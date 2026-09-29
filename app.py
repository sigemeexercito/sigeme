from flask import Flask, request, redirect, url_for, render_template, flash, make_response, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_migrate import Migrate
from datetime import datetime
import io
import pandas as pd
import pdfkit
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from relatorios import gerar_relatorio_pdf
from werkzeug.utils import secure_filename
import os
import re
from sqlalchemy import func

from datetime import datetime

def validar_data(valor, campo_nome="Data"):
    if not valor:
        return None, f"{campo_nome} não pode estar vazia"
    try:
        data = datetime.strptime(valor, "%Y-%m-%d").date()
        return data, None
    except ValueError:
        return None, f"{campo_nome} inválida"


# 🔹 Configuração principal
app = Flask(__name__)
app.secret_key = "segredo"

# Base de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///militares.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Upload de fotos
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 🔹 Inicializar DB corretamente
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Militar(db.Model):
    __tablename__ = 'militares'
    id = db.Column(db.Integer, primary_key=True)
    foto = db.Column(db.String(200))

    # Relações
    familiares = db.relationship("Familiar", back_populates="militar", cascade="all, delete-orphan")
    formacoes = db.relationship("Formacao", back_populates="militar", cascade="all, delete-orphan")
    lista_funcoes = db.relationship("Funcao", back_populates="militar", cascade="all, delete-orphan")
    promocoes = db.relationship("Promocao", back_populates="militar", cascade="all, delete-orphan")
    linguas = db.relationship("Lingua", back_populates="militar", cascade="all, delete-orphan")
     

    # Step 1: Dados Pessoais
    nome_completo = db.Column(db.String, nullable=False)
    sexo = db.Column(db.String)
    data_nascimento = db.Column(db.Date)
    idade = db.Column(db.Integer)
    altura = db.Column(db.Integer)
    numero_calcado = db.Column(db.Integer)
    nacionalidade = db.Column(db.String)
    email = db.Column(db.String)
    contacto1 = db.Column(db.String)
    contacto2 = db.Column(db.String)

    # Step 2: Identificação
    patente = db.Column(db.String)
    cargo_funcao = db.Column(db.String)
    regime = db.Column(db.String)
    nuit = db.Column(db.String)
    numero_bi = db.Column(db.String)
    data_emissao_bi = db.Column(db.Date)
    numero_bi_militar = db.Column(db.String)
    validade_bi_militar = db.Column(db.Date)
    numero_passaporte = db.Column(db.String)
    data_emissao_passaporte = db.Column(db.Date)

    # Step 3: Dados de Nascimento
    pais_nascimento = db.Column(db.String)
    provincia_nascimento = db.Column(db.String)
    distrito_nascimento = db.Column(db.String)
    posto_administrativo = db.Column(db.String)
    localidade = db.Column(db.String)
    estado_civil = db.Column(db.String)
    conjuge = db.Column(db.String)

    # Step 6: Incorporação
    data_incorporacao = db.Column(db.Date)
    tempo_servico = db.Column(db.Integer)

    # Step 7: Carreira
    situacao = db.Column(db.String)
    ordem_servico = db.Column(db.String)

    # Step 9: Promoções
    data_ultima_promocao = db.Column(db.Date)
    numero_os_ultima_promocao = db.Column(db.String)

    # Step 10: Acadêmico
    nivel_academico = db.Column(db.String)

    # Step 11: Emergência
    contacto_emergencia = db.Column(db.String)
    parentesco_emergencia = db.Column(db.String)
    nome_emergencia = db.Column(db.String(100))
    morada_emergencia = db.Column(db.String(200))

    # Step 15: Observações
    observacoes = db.Column(db.Text)

    # Unidade e Especialidade (texto)
    especialidade = db.Column(db.String)
    unidade = db.Column(db.String)   # ✔ corrigido: é String, não unidade_id
    provincia = db.Column(db.String)
    distrito = db.Column(db.String)

    # Campos Bancários
    conta_bancaria = db.Column(db.String)
    banco = db.Column(db.String)

    # Campos de Condução
    tipo_conducao = db.Column(db.String)
    tempo_experiencia_conducao = db.Column(db.Integer)
    tipo_carta = db.Column(db.String)
    numero_carta = db.Column(db.String)
    validade_carta = db.Column(db.Date)
    
    # Situacao
    situacao = db.Column(db.String(50))
    data_obito = db.Column(db.Date, nullable=True)
    causa_obito = db.Column(db.String(100), nullable=True)
    obs_obito = db.Column(db.Text, nullable=True)

    # Auditoria interna
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    criado_por = db.Column(db.String(50))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_por = db.Column(db.String(50))
    atualizado_em = db.Column(db.DateTime, onupdate=datetime.utcnow)



# -----------------------------
# Modelo Auditoria
# -----------------------------
class Auditoria(db.Model):
    __tablename__ = 'auditorias'

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), nullable=False)
    acao = db.Column(db.Enum(
        'Criar', 'Editar', 'Eliminar', 'Login', 'Logout', 'Exportar',
        name='acao_enum'
    ), nullable=False)
    detalhes = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Auditoria {self.id} - {self.usuario} - {self.acao}>"
def registrar_auditoria(usuario, acao, detalhes=None):
    log = Auditoria(
        usuario=usuario,
        acao=acao,
        detalhes=detalhes
    )
    db.session.add(log)
    db.session.commit()


class Formacao(db.Model):
    __tablename__ = 'formacoes'
    id = db.Column(db.Integer, primary_key=True)

    # Dados da formação
    curso = db.Column(db.String, nullable=False)
    estabelecimento = db.Column(db.String)
    tipo_curso = db.Column(db.String)     # ✔ acrescentado
    nivel = db.Column(db.String)          # ✔ acrescentado
    duracao = db.Column(db.String)        # ✔ acrescentado
    pais = db.Column(db.String)           # ✔ acrescentado
    data_inicio = db.Column(db.Date)
    data_final = db.Column(db.Date)
    observacoes = db.Column(db.Text)

    # Relação com Militar
    militar_id = db.Column(db.Integer, db.ForeignKey('militares.id'), nullable=False)
    militar = db.relationship("Militar", back_populates="formacoes")


class Funcao(db.Model):
    __tablename__ = 'funcoes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    ordem_servico = db.Column(db.String, nullable=True)
    data_ordem = db.Column(db.Date, nullable=True)
    unidade = db.Column(db.String, nullable=True)  # texto simples
    inicio = db.Column(db.Date, nullable=True)
    termino = db.Column(db.Date, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    militar_id = db.Column(db.Integer, db.ForeignKey('militares.id'))
    militar = db.relationship("Militar", back_populates="lista_funcoes")

    # 👉 método de validação
    def validar_periodo(self):
        if self.inicio and self.termino and self.termino < self.inicio:
            raise ValueError("Data de término não pode ser anterior à data de início")




class Familiar(db.Model):
    __tablename__ = 'familiares'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    grau_parentesco = db.Column(db.String)
    data_nasc = db.Column(db.Date)
    provincia = db.Column(db.String)
    morada = db.Column(db.String)
    telefone = db.Column(db.String)
    observacoes = db.Column(db.Text)

    militar_id = db.Column(db.Integer, db.ForeignKey('militares.id'))
    militar = db.relationship("Militar", back_populates="familiares")
class Especialidade(db.Model):
    __tablename__ = 'Especialidades'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<Especialidade {self.nome}>"


class Unidade(db.Model):
    __tablename__ = 'Unidades'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    prevista = db.Column(db.Boolean, default=True)


class Usuario(db.Model, UserMixin):
    __tablename__ = 'Usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    perfil = db.Column(db.String(50), nullable=False)  # admin, operador, visualizador

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# 🔹 Decorators para perfis
from functools import wraps
from flask import abort
from flask_login import current_user

def perfis_requeridos(*perfis):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.perfil.lower() not in [p.lower() for p in perfis]:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def operador_allowed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.perfil.lower() != "operador":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def visualizador_allowed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.perfil.lower() != "visualizador":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


class Promocao(db.Model):
    __tablename__ = 'promocoes'
    id = db.Column(db.Integer, primary_key=True)

    patente = db.Column(db.String)
    data = db.Column(db.Date)
    numero_os = db.Column(db.String)
    observacoes = db.Column(db.Text)

    militar_id = db.Column(db.Integer, db.ForeignKey('militares.id'), nullable=False)

    # Relação inversa
    militar = db.relationship("Militar", back_populates="promocoes")
    militar_ref = db.relationship("Militar", overlaps="militar")



class Lingua(db.Model):
    __tablename__ = "linguas"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    fala = db.Column(db.String(50))
    leitura = db.Column(db.String(50))
    escrita = db.Column(db.String(50))
    compreensao = db.Column(db.String(50))
    materna = db.Column(db.Boolean)

    militar_id = db.Column(db.Integer, db.ForeignKey("militares.id"))
    militar = db.relationship("Militar", back_populates="linguas")
# Criar tabelas
# with app.app_context():
#     db.create_all()


# 🔑 Função auxiliar para carregar listas
def carregar_listas():
    # Patentes previstas
    PATENTES_PREVISTAS = [
        "Major General","Brigadeiro","Coronel","Tenente Coronel","Major",
        "Capitão","Tenente","Alferes","Intendente","Subintendente",
        "1º Sargento","2º Sargento","3º Sargento","Furriel",
        "1º Cabo","2º Cabo","Soldado",
    ]
    # 🔑 Mapeamento de patentes para categorias
PATENTE_CATEGORIA = {
    # Oficiais
    "Major General": "Oficial",
    "Brigadeiro": "Oficial",
    "Coronel": "Oficial",
    "Tenente Coronel": "Oficial",
    "Major": "Oficial",
    "Capitão": "Oficial",
    "Tenente": "Oficial",
    "Alferes": "Oficial",

    # Sargentos
    "Intendente": "Sargento",
    "Subintendente": "Sargento",
    "1º Sargento": "Sargento",
    "2º Sargento": "Sargento",
    "3º Sargento": "Sargento",
    "Furriel": "Sargento",
    "1º Cabo": "Sargento",
    "2º Cabo": "Sargento",

    # Praças
    "Soldado": "Praça"
}


# 🔑 Função auxiliar para carregar listas
def carregar_listas():
    # Patentes previstas
    PATENTES_PREVISTAS = list(PATENTE_CATEGORIA.keys())

    # Níveis académicos previstos
    NIVEIS_PREVISTOS = [
        "PhD","Mestre","Licenciado","Bacharel","12ª Classe",
        "Técnico Médio Profissional","10ª Classe","9ª Classe",
        "8ª Classe","7ª Classe","6ª Classe","5ª Classe"
    ]

    # Regimes previstos
    REGIMES_PREVISTOS = ["QP","RV","SEN"]

    # Bancos previstos
    BANCOS_PREVISTOS = ["BIM","BCI","STDBANK"]

    # Dicionário completo de províncias e distritos
    PROVINCIAS_E_DISTRITOS = {
        "Maputo Cidade": ["KaMpfumo", "Nhlamankulu", "KaMaxaquene", "KaMavota", "KaTembe", "KaNyaka"],
        "Maputo Província": ["Matola", "Boane", "Marracuene", "Manhiça", "Magude", "Moamba", "Namaacha", "Matutuíne"],
        "Gaza": ["Xai-Xai", "Bilene", "Chibuto", "Chókwè", "Mandlakazi", "Mabalane", "Massingir", "Guijá", "Chicualacuala", "Chigubo"],
        "Inhambane": ["Inhambane", "Maxixe", "Vilankulo", "Massinga", "Jangamo", "Morrumbene", "Panda", "Funhalouro", "Govuro", "Homoíne", "Inharrime", "Inhassoro", "Mabote", "Zavala"],
        "Sofala": ["Beira", "Dondo", "Nhamatanda", "Buzi", "Caia", "Cheringoma", "Chibabava", "Gorongosa", "Marromeu", "Muanza"],
        "Manica": ["Chimoio", "Gondola", "Sussundenga", "Barue", "Mossurize", "Machaze", "Macossa", "Tambara", "Guro", "Vanduzi"],
        "Tete": ["Tete", "Moatize", "Angónia", "Changara", "Zumbo", "Cahora-Bassa", "Chifunde", "Chiuta", "Macanga", "Marávia", "Mutarara", "Tsangano"],
        "Zambézia": ["Quelimane", "Mocuba", "Milange", "Maganja da Costa", "Gilé", "Alto Molócuè", "Chinde", "Gurué", "Ile", "Inhassunge", "Lugela", "Namacurra", "Nicoadala", "Pebane", "Morrumbala", "Mopeia"],
        "Nampula": ["Nampula", "Nacala Porto", "Nacala-a-Velha", "Monapo", "Mecuburi", "Meconta", "Mogovolas", "Moma", "Mossuril", "Muecate", "Murrupula", "Rapale", "Ribaue", "Angoche", "Eráti", "Lalaua", "Malema"],
        "Cabo Delgado": ["Pemba", "Montepuez", "Mueda", "Macomia", "Quissanga", "Ancuabe", "Balama", "Chiúre", "Ibo", "Mecúfi", "Meluco", "Metuge", "Mocímboa da Praia", "Muidumbe", "Namuno", "Nangade", "Palma"],
        "Niassa": ["Lichinga", "Cuamba", "Mandimba", "Ngauma", "Marrupa", "Lago", "Majune", "Maúa", "Mecula", "Metarica", "Muembe", "Nipepe", "Sanga"]
    }

    return {
        "patentes": PATENTES_PREVISTAS,
        "niveis_academicos": NIVEIS_PREVISTOS,
        "regimes": REGIMES_PREVISTOS,
        "bancos": BANCOS_PREVISTOS,
        "provincias": list(PROVINCIAS_E_DISTRITOS.keys()),
        "distritos_por_provincia": PROVINCIAS_E_DISTRITOS,
        "especialidades": [e.nome for e in Especialidade.query.all()]
    }


@app.route('/distritos/<provincia>')
def distritos_por_provincia(provincia):
    listas = carregar_listas()
    distritos = listas["distritos_por_provincia"].get(provincia, [])
    return jsonify(distritos)



    # Unidades previstas
    UNIDADES_PREVISTAS = [
        "Comando do Exército","Regimento de Protecção da Cidade Maputo","Brigada 107","Brigada 110",
        "Batalhão de Forças Especiais","Batalhão de Infantaria de Quelimane","Batalhão de Infantaria de Tete",
        "Batalhão de Infantaria de Chimoio/ Acampamento de Dongo","Batalhão de Infantaria de Chókwè",
        "Batalhão de Tanques","Batalhão de Proteção de Objectos Económicos de Songo","Batalhão de Protecção de Paióis",
        "Batalhão de Artilharia Anti-Aerea AZP-37mm","Grupo de Artilharia Terrestre D-30","Grupo de Artilharia Reactiva de BM-21",
        "Escola Prática do Exército","Escola de Formação de Forças Especiais","Centro de Formação de Artilharia do Exército",
        "Centro de Formação de Engenharia e Defesa Química","Centro de Formação de Operações de Apoio à Paz",
        "1ª Companhia de Comandos","2ª Companhia de Comandos","Companhia de Paraquedistas"
    ]

    # Unidades não previstas
    UNIDADES_NAO_PREVISTAS = [
        "Força Tarefa Conjunta de Protec. Obj. Petroliferos-Afungi","Batalhão Trovoada","Militares Em Novas Ordens",
        "Batalhão de Operações Especiais Tanzania","Batalhão de Operações Especiais Rinoceronte","Candidatos ao Curso na Argélia",
        "Companhia do Aeroporto-Nampula","Finalistas do 16° Curso de Formação de Sargentos","Finalistas do 54° Curso de Instrução Básica Militar",
        "Finalistas do 18° Curso de Academia Militar","Companhia de Macarara Formada em Nampula"
    ]

    # Especialidades previstas (lista completa)
    ESPECIALIDADES_PREVISTAS = [
        "Administração Militar","Artilharia","Artilharia Anti-Aérea","Blindados","Comunicações",
        "Engenharia","Forças Especiais","Infantaria","Polícia Militar","Saúde Militar","Técnica","Paraquedistas"
    ]

    # Valores já existentes na BD
    patentes_existentes = [p[0] for p in db.session.query(Militar.patente.distinct()).filter(Militar.patente != None, Militar.patente != '').all()]
    niveis_existentes = [n[0] for n in db.session.query(Militar.nivel_academico.distinct()).filter(Militar.nivel_academico != None, Militar.nivel_academico != '').all()]
    regimes_existentes = [r[0] for r in db.session.query(Militar.regime.distinct()).filter(Militar.regime != None, Militar.regime != '').all()]
    bancos_existentes = [b[0] for b in db.session.query(Militar.banco.distinct()).filter(Militar.banco != None, Militar.banco != '').all()]
    provincias_existentes = [p[0] for p in db.session.query(Militar.provincia.distinct()).filter(Militar.provincia != None, Militar.provincia != '').all()]
    unidades_existentes = [u[0] for u in db.session.query(Militar.unidade.distinct()).filter(Militar.unidade != None, Militar.unidade != '').all()]
    #especialidades_existentes = [e[0] for e in db.session.query(Militar.especialidade.distinct()).filter(Militar.especialidade != None, Militar.especialidade != '').all()]
    especialidades_existentes = [e.nome for e in Especialidade.query.all()]

    return {
        "patentes": sorted(set(PATENTES_PREVISTAS + patentes_existentes)),
        "niveis": sorted(set(NIVEIS_PREVISTOS + niveis_existentes)),
        "regimes": sorted(set(REGIMES_PREVISTOS + regimes_existentes)),
        "bancos": sorted(set(BANCOS_PREVISTOS + bancos_existentes)),
        "provincias": sorted(set(PROVINCIAS_PREVISTAS + provincias_existentes)),
        "distritos_por_provincia": DISTRITOS_POR_PROVINCIA,
        "unidades_previstas": sorted(set(UNIDADES_PREVISTAS + unidades_existentes)),
        "unidades_nao_previstas": sorted(set(UNIDADES_NAO_PREVISTAS + unidades_existentes)),
        "especialidades": sorted(set(ESPECIALIDADES_PREVISTAS + especialidades_existentes))
    }
   
    
@app.route('/relatorios/filtro', methods=['GET'])
def relatorio_filtro():
    patente = request.args.get("patente")
    unidade = request.args.get("unidade")
    especialidade = request.args.get("especialidade")
    nivel_academico = request.args.get("nivel_academico")
    regime = request.args.get("regime")
    tempo_servico = request.args.get("tempo_servico")
    nome = request.args.get("nome")
    sexo = request.args.get("sexo")
    situacao = request.args.get("situacao")   # <-- Novo filtro

    # Lista fixa de níveis acadêmicos
    niveis_fixos = [
        "PhD", "Mestre", "Licenciado", "Bacharel",
        "Tecnico Medio", "12 Classe", "10 Classe",
        "7 Classe", "5 Classe"
    ]

    # Dropdowns
    patentes = [p[0] for p in db.session.query(Militar.patente.distinct()).filter(Militar.patente != None, Militar.patente != '').all()]
    unidades = [u[0] for u in db.session.query(Militar.unidade.distinct()).filter(Militar.unidade != None, Militar.unidade != '').all()]
    especialidades = [e[0] for e in db.session.query(Militar.especialidade.distinct()).filter(Militar.especialidade != None, Militar.especialidade != '').all()]
    niveis_db = [n[0] for n in db.session.query(Militar.nivel_academico.distinct()).filter(Militar.nivel_academico != None, Militar.nivel_academico != '').all()]
    regimes = [r[0] for r in db.session.query(Militar.regime.distinct()).filter(Militar.regime != None, Militar.regime != '').all()]
    tempos = [t[0] for t in db.session.query(Militar.tempo_servico.distinct()).filter(Militar.tempo_servico != None, Militar.tempo_servico != '').all()]
    situacoes = [s[0] for s in db.session.query(Militar.situacao.distinct()).filter(Militar.situacao != None, Militar.situacao != '').all()]  # <-- lista de situações

    # Junta lista fixa com valores do banco (sem duplicados)
    niveis = sorted(set(niveis_fixos + niveis_db))

    # Query detalhada
    query = db.session.query(Militar)

    if patente: query = query.filter(Militar.patente == patente)
    if unidade: query = query.filter(Militar.unidade == unidade)
    if especialidade: query = query.filter(Militar.especialidade == especialidade)
    if nivel_academico: query = query.filter(Militar.nivel_academico == nivel_academico)
    if regime: query = query.filter(Militar.regime == regime)
    if tempo_servico: query = query.filter(Militar.tempo_servico == tempo_servico)
    if nome: query = query.filter(Militar.nome_completo.ilike(f"%{nome}%"))
    if sexo: query = query.filter(Militar.sexo == sexo)
    if situacao: query = query.filter(Militar.situacao == situacao)   # <-- aplica filtro

    dados = query.all()

    return render_template(
        "relatorio_filtro.html",
        patentes=patentes,
        unidades=unidades,
        especialidades=especialidades,
        niveis=niveis,
        regimes=regimes,
        tempos=tempos,
        situacoes=situacoes,   # <-- passa lista para o template
        patente=patente,
        unidade=unidade,
        especialidade=especialidade,
        nivel_academico=nivel_academico,
        regime=regime,
        tempo_servico=tempo_servico,
        nome=nome,
        sexo=sexo,
        situacao=situacao,     # <-- passa valor selecionado
        dados=dados
    )

from datetime import datetime

def str_to_date(data_str):
    """Converte string 'YYYY-MM-DD' em objeto date, ou None se vazio."""
    if not data_str:
        return None
    return datetime.strptime(data_str, "%Y-%m-%d").date()


from datetime import datetime

@app.route('/novo', methods=['GET', 'POST'])
@login_required
@perfis_requeridos('admin', 'operador')
def novo():
    if request.method == 'POST':
        # --- Validação de NUIT duplicado ---
        nuit = request.form.get("nuit")
        if nuit and Militar.query.filter_by(nuit=nuit).first():
            flash("⚠️ Este NUIT já existe no SIGEME.", "danger")
            return redirect(url_for("novo"))

        # --- Validações obrigatórias ---
        data_nascimento, erro = validar_data(request.form.get("data_nascimento"), "Data de Nascimento")
        if erro: 
            flash(erro, "danger"); return redirect(url_for("novo"))

        data_incorporacao, erro = validar_data(request.form.get("data_incorporacao"), "Data de Incorporação")
        if erro: 
            flash(erro, "danger"); return redirect(url_for("novo"))

        # --- Validações opcionais ---
        data_emissao_bi = None
        if request.form.get("data_emissao_bi"):
            data_emissao_bi, erro = validar_data(request.form.get("data_emissao_bi"), "Data de Emissão BI")
            if erro: 
                flash(erro, "danger"); return redirect(url_for("novo"))

        validade_bi_militar = None
        if request.form.get("validade_bi_militar"):
            validade_bi_militar, erro = validar_data(request.form.get("validade_bi_militar"), "Validade BI Militar")
            if erro: 
                flash(erro, "danger"); return redirect(url_for("novo"))

        data_emissao_passaporte = None
        if request.form.get("data_emissao_passaporte"):
            data_emissao_passaporte, erro = validar_data(request.form.get("data_emissao_passaporte"), "Data de Emissão Passaporte")
            if erro: 
                flash(erro, "danger"); return redirect(url_for("novo"))

        data_ultima_promocao = None
        if request.form.get("data_ultima_promocao"):
            data_ultima_promocao, erro = validar_data(request.form.get("data_ultima_promocao"), "Data da Última Promoção")
            if erro: 
                flash(erro, "danger"); return redirect(url_for("novo"))

        validade_carta = None
        if request.form.get("validade_carta"):
            validade_carta, erro = validar_data(request.form.get("validade_carta"), "Validade da Carta de Condução")
            if erro: 
                flash(erro, "danger"); return redirect(url_for("novo"))

        # --- Criar Militar ---
        militar = Militar(
            nome_completo=request.form['nome_completo'],
            sexo=request.form.get('sexo'),
            data_nascimento=data_nascimento,
            idade=int(request.form['idade']) if request.form.get('idade') else None,
            altura=int(request.form.get('altura')) if request.form.get('altura') else None,
            numero_calcado=int(request.form.get('numero_calcado')) if request.form.get('numero_calcado') else None,
            nacionalidade=request.form.get('nacionalidade'),
            email=request.form.get('email'),
            contacto1=request.form.get('contacto1'),
            contacto2=request.form.get('contacto2'),
            patente=request.form.get('patente'),
            cargo_funcao=request.form.get('cargo_funcao'),
            regime=request.form.get('regime'),
            nuit=request.form.get('nuit'),
            numero_bi=request.form.get('numero_bi'),
            data_emissao_bi=data_emissao_bi,
            numero_bi_militar=request.form.get('numero_bi_militar'),
            validade_bi_militar=validade_bi_militar,
            numero_passaporte=request.form.get('numero_passaporte'),
            data_emissao_passaporte=data_emissao_passaporte,
            data_incorporacao=data_incorporacao,
            tempo_servico=int(request.form['tempo_servico']) if request.form.get('tempo_servico') else None,
            situacao=request.form.get('situacao'),
            ordem_servico=request.form.get('ordem_servico'),
            data_ultima_promocao=data_ultima_promocao,
            numero_os_ultima_promocao=request.form.get('numero_os_ultima_promocao'),
            nivel_academico=request.form.get('nivel_academico') or 'Não definido',
            especialidade=request.form.get('especialidade'),
            unidade=request.form.get('unidade'),
            provincia_nascimento=request.form.get('provincia_nascimento'),
            distrito_nascimento=request.form.get('distrito_nascimento'),
            posto_administrativo=request.form.get('posto_administrativo'),
            localidade=request.form.get('localidade'),
            estado_civil=request.form.get('estado_civil'),
            conjuge=request.form.get('conjuge'),
            conta_bancaria=request.form.get('conta_bancaria'),
            banco=request.form.get('banco'),
            tipo_conducao=request.form.get('tipo_conducao'),
            tempo_experiencia_conducao=int(request.form.get('tempo_experiencia_conducao')) if request.form.get('tempo_experiencia_conducao') else None,
            tipo_carta=request.form.get('tipo_carta'),
            numero_carta=request.form.get('numero_carta'),
            validade_carta=validade_carta,
            contacto_emergencia=request.form.get('contacto_emergencia'),
            parentesco_emergencia=request.form.get('parentesco_emergencia'),
            nome_emergencia=request.form.get('nome_emergencia'),
            morada_emergencia=request.form.get('morada_emergencia'),
            observacoes=request.form.get('observacoes'),
            data_obito=request.form.get('data_obito') if request.form.get('situacao') == 'Falecido' else None,
            causa_obito=request.form.get('causa_obito') if request.form.get('situacao') == 'Falecido' else None,
            obs_obito=request.form.get('obs_obito') if request.form.get('situacao') == 'Falecido' else None
        )

        # --- Upload da Foto ---
        foto = request.files.get('foto')
        if foto and foto.filename != '':
            filename = secure_filename(foto.filename)
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(caminho)
            militar.foto = filename

        db.session.add(militar)
        db.session.flush()  # gera ID antes de relacionar    

        # --- Familiares ---
        ids_familiares = request.form.getlist("familiar_id[]")
        nomes_familiares = request.form.getlist("nome_familiar[]")
        graus = request.form.getlist("grau_parentesco[]")
        datas_familiares = request.form.getlist("data_nasc_familiar[]")
        provincias = request.form.getlist("prov_familiar[]")
        moradas = request.form.getlist("morada_familiar[]")
        telefones = request.form.getlist("telefone_familiar[]")
        obs_familiares = request.form.getlist("obs_familiar[]")

        remover_ids = request.form.getlist("remover_familiar[]")
        for fid in remover_ids:
            familiar = Familiar.query.get(int(fid))
            if familiar and familiar.militar_id == militar.id:
                db.session.delete(familiar)

        for i in range(len(nomes_familiares)):
            fid = ids_familiares[i] if i < len(ids_familiares) else None
            if fid and fid not in remover_ids:
                familiar = Familiar.query.get(int(fid))
                if familiar and familiar.militar_id == militar.id:
                    familiar.nome = nomes_familiares[i]
                    familiar.grau_parentesco = graus[i]
                    familiar.data_nasc = datetime.strptime(datas_familiares[i], "%Y-%m-%d").date() if datas_familiares[i] else None
                    familiar.provincia = provincias[i]
                    familiar.morada = moradas[i]
                    familiar.telefone = telefones[i]
                    familiar.observacoes = obs_familiares[i]
            elif not fid:
                if nomes_familiares[i]:
                    novo_fam = Familiar(
                        nome=nomes_familiares[i],
                        grau_parentesco=graus[i],
                        data_nasc=datetime.strptime(datas_familiares[i], "%Y-%m-%d").date() if datas_familiares[i] else None,
                        provincia=provincias[i],
                        morada=moradas[i],
                        telefone=telefones[i],
                        observacoes=obs_familiares[i],
                        militar=militar
                    )
                    db.session.add(novo_fam)

        db.session.commit()

                # --- Funções ---
        nomes_funcoes = request.form.getlist("funcao_nome[]")
        os_funcoes = request.form.getlist("funcao_os[]")
        datas_ordem = request.form.getlist("funcao_data[]")
        unidades = request.form.getlist("funcao_unidade[]")
        inicios = request.form.getlist("funcao_inicio[]")
        terminos = request.form.getlist("funcao_termino[]")
        obs_funcoes = request.form.getlist("funcao_obs[]")

        for i in range(len(nomes_funcoes)):
            inicio_date = datetime.strptime(inicios[i], "%Y-%m-%d").date() if inicios[i] else None
            termino_date = datetime.strptime(terminos[i], "%Y-%m-%d").date() if terminos[i] else None

            funcao = Funcao(
                nome=nomes_funcoes[i],
                ordem_servico=os_funcoes[i],
                data_ordem=datetime.strptime(datas_ordem[i], "%Y-%m-%d").date() if datas_ordem[i] else None,
                unidade=unidades[i],
                inicio=inicio_date,
                termino=termino_date,
                observacoes=obs_funcoes[i],
                militar=militar
            )

            try:
                funcao.validar_periodo()
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("novo"))

            db.session.add(funcao)

        # --- Promoções ---
        patentes = request.form.getlist("promocao_patente[]")
        datas_promocoes = request.form.getlist("promocao_data[]")
        os_promocoes = request.form.getlist("promocao_os[]")
        obs_promocoes = request.form.getlist("promocao_obs[]")

        for i in range(len(patentes)):
            data_promocao = datetime.strptime(datas_promocoes[i], "%Y-%m-%d").date() if datas_promocoes[i] else None
            numero_os = os_promocoes[i].strip() if os_promocoes[i] else None

            promocao = Promocao(
                patente=patentes[i],
                data=data_promocao,
                numero_os=numero_os,
                observacoes=obs_promocoes[i],
                militar=militar
            )

            if data_promocao and data_promocao > datetime.today().date():
                flash("Data da promoção não pode ser futura.", "danger")
                return redirect(url_for("novo"))

            db.session.add(promocao)

        # --- Línguas ---
        linguas = request.form.getlist("lingua_nome[]")
        outras = request.form.getlist("outra_lingua[]")
        fala = request.form.getlist("lingua_fala[]")
        leitura = request.form.getlist("lingua_leitura[]")
        escrita = request.form.getlist("lingua_escrita[]")
        compreensao = request.form.getlist("lingua_compreensao[]")
        materna = request.form.getlist("lingua_materna[]")

        for i in range(len(linguas)):
            nome = linguas[i]
            if nome == "Outra" and outras[i]:
                nome = outras[i]

            lingua = Lingua(
                nome=nome,
                fala=fala[i],
                leitura=leitura[i],
                escrita=escrita[i],
                compreensao=compreensao[i],
                materna=(materna[i] == "Sim"),
                militar=militar
            )
            db.session.add(lingua)

        # --- Formações ---
        cursos = request.form.getlist("curso[]")
        estabelecimentos = request.form.getlist("estabelecimento[]")
        tipos = request.form.getlist("tipo_curso[]")
        niveis = request.form.getlist("nivel[]")
        duracoes = request.form.getlist("duracao[]")
        paises = request.form.getlist("pais[]")
        paises_outro = request.form.getlist("pais_outro[]")
        inicios_formacao = request.form.getlist("data_inicio[]")
        finais_formacao = request.form.getlist("data_final[]")
        obs_formacoes = request.form.getlist("observacoes[]")

        for tipo, curso, estab, nivel, duracao, pais, pais_outro, inicio, fim, obs in zip(
            tipos, cursos, estabelecimentos, niveis, duracoes, paises, paises_outro,
            inicios_formacao, finais_formacao, obs_formacoes
        ):
            if tipo == "Militar":
                nivel = "ADEQUAÇÃO"
            if pais == "Outro":
                pais = pais_outro

            formacao = Formacao(
                tipo_curso=tipo,
                curso=curso,
                estabelecimento=estab,
                nivel=nivel,
                duracao=duracao,
                pais=pais,
                data_inicio=datetime.strptime(inicio, "%Y-%m-%d").date() if inicio else None,
                data_final=datetime.strptime(fim, "%Y-%m-%d").date() if fim else None,
                observacoes=obs,
                militar=militar
            )
            db.session.add(formacao)

        # --- Commit final (POST) ---
        db.session.commit()
        flash('Militar cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_militares'))

    # --- GET: carregar listas para o form ---
    listas = carregar_listas()
    listas['unidades_previstas'] = [u.nome for u in Unidade.query.filter_by(prevista=True).all()]
    listas['unidades_nao_previstas'] = [u.nome for u in Unidade.query.filter_by(prevista=False).all()]
    listas['unidades'] = Unidade.query.all()
    listas['niveis'] = [
        "PhD", "Mestre", "Licenciado", "Bacharel",
        "Tecnico Medio", "12 Classe", "10 Classe",
        "7 Classe", "5 Classe"
    ]

    return render_template('form.html', militar=None, **listas)

    


    # --- GET: carregar listas para o form ---
# --- Formulário principal ---

@app.route('/form')
def carregar_form():
    listas = carregar_listas()

    # Unidades previstas e não previstas
    listas['unidades_previstas'] = [
        u.nome for u in Unidade.query.filter_by(prevista=True).all()
    ]
    listas['unidades_nao_previstas'] = [
        u.nome for u in Unidade.query.filter_by(prevista=False).all()
    ]

    # Lista completa de unidades (objetos com id e nome)
    listas['unidades'] = Unidade.query.all()

    # Lista fixa de níveis académicos
    listas['niveis'] = [
        "PhD", "Mestre", "Licenciado", "Bacharel",
        "Tecnico Medio", "12 Classe", "10 Classe",
        "7 Classe", "5 Classe"
    ]

    return render_template('form.html', militar=None, **listas)


# --- Listar todas as especialidades ---
@app.route('/especialidades')
def listar_especialidades():
    especialidades = Especialidade.query.all()
    return render_template('especialidades.html', especialidades=especialidades)


# --- Adicionar nova especialidade ---
@app.route('/nova_especialidade', methods=['GET', 'POST'])
def nova_especialidade():
    if request.method == 'POST':
        nome = request.form['nome']
        if nome:
            nova = Especialidade(nome=nome)
            db.session.add(nova)
            db.session.commit()
            return redirect(url_for('listar_especialidades'))
    return render_template('nova_especialidade.html')


# --- Editar especialidade ---
@app.route('/editar_especialidade/<int:id>', methods=['GET', 'POST'])
def editar_especialidade(id):
    especialidade = Especialidade.query.get_or_404(id)
    if request.method == 'POST':
        especialidade.nome = request.form['nome']
        db.session.commit()
        return redirect(url_for('listar_especialidades'))
    return render_template('editar_especialidade.html', especialidade=especialidade)


# --- Apagar especialidade ---
@app.route('/apagar_especialidade/<int:id>', methods=['POST'])
def apagar_especialidade(id):
    especialidade = Especialidade.query.get_or_404(id)
    db.session.delete(especialidade)
    db.session.commit()
    return redirect(url_for('listar_especialidades'))


# Rota para listar militares
@app.route('/')
@app.route('/militares')
def listar_militares():
    militares = Militar.query.all()
    return render_template('list.html', militares=militares)
    
@app.route('/relatorios/filtro_agregado', methods=['GET'])
def relatorio_filtro_agregado():
    patente = request.args.get("patente")
    unidade = request.args.get("unidade")
    especialidade = request.args.get("especialidade")
    nivel_academico = request.args.get("nivel_academico")
    regime = request.args.get("regime")
    tempo_servico = request.args.get("tempo_servico")
    sexo = request.args.get("sexo")

    # Dropdowns
    patentes = [p[0] for p in db.session.query(Militar.patente.distinct()).filter(Militar.patente != None, Militar.patente != '').all()]
    unidades = [u[0] for u in db.session.query(Militar.unidade.distinct()).filter(Militar.unidade != None, Militar.unidade != '').all()]
    especialidades = [e[0] for e in db.session.query(Militar.especialidade.distinct()).filter(Militar.especialidade != None, Militar.especialidade != '').all()]
    niveis = [n[0] for n in db.session.query(Militar.nivel_academico.distinct()).filter(Militar.nivel_academico != None, Militar.nivel_academico != '').all()]
    regimes = [r[0] for r in db.session.query(Militar.regime.distinct()).filter(Militar.regime != None, Militar.regime != '').all()]
    tempos = [t[0] for t in db.session.query(Militar.tempo_servico.distinct()).filter(Militar.tempo_servico != None, Militar.tempo_servico != '').all()]

    # Query agregada
    query = db.session.query(
        Militar.sexo,
        Militar.patente,
        Militar.unidade,
        Militar.especialidade,
        Militar.nivel_academico,
        Militar.regime,
        Militar.tempo_servico,
        db.func.count(Militar.id).label("total")
    )

    # Aplicar filtros
    if patente: query = query.filter(Militar.patente == patente)
    if unidade: query = query.filter(Militar.unidade == unidade)
    if especialidade: query = query.filter(Militar.especialidade == especialidade)
    if nivel_academico: query = query.filter(Militar.nivel_academico == nivel_academico)
    if regime: query = query.filter(Militar.regime == regime)
    if tempo_servico: query = query.filter(Militar.tempo_servico == tempo_servico)
    if sexo: query = query.filter(Militar.sexo == sexo)

    query = query.group_by(
        Militar.sexo,
        Militar.patente,
        Militar.unidade,
        Militar.especialidade,
        Militar.nivel_academico,
        Militar.regime,
        Militar.tempo_servico
    )

    dados = query.all()

    return render_template(
        "relatorio_filtro_agregado.html",
        patentes=patentes,
        unidades=unidades,
        especialidades=especialidades,
        niveis=niveis,
        regimes=regimes,
        tempos=tempos,
        patente=patente,
        unidade=unidade,
        especialidade=especialidade,
        nivel_academico=nivel_academico,
        regime=regime,
        tempo_servico=tempo_servico,
        sexo=sexo,
        dados=dados
    )

from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import os
from datetime import datetime

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@perfis_requeridos('admin', 'operador')
def edit_militar(id):
    militar = Militar.query.options(
        joinedload(Militar.familiares),
        joinedload(Militar.lista_funcoes),
        joinedload(Militar.promocoes),
        joinedload(Militar.linguas),
        joinedload(Militar.formacoes)
    ).get_or_404(id)

    if request.method == 'POST':
        # --- Validação de NUIT duplicado ---
        nuit = request.form.get('nuit')
        duplicado = Militar.query.filter(Militar.nuit == nuit, Militar.id != id).first()
        if nuit and duplicado:
            flash("⚠️ Este NUIT já existe no SIGEME.", "danger")
            return redirect(url_for('edit_militar', id=id))

        # --- Campos simples (só atualiza se vier valor) ---
        valor = request.form.get('nome_completo')
        if valor: militar.nome_completo = valor


        valor = request.form.get('patente')
        if valor: militar.patente = valor

        valor = request.form.get('cargo_funcao')
        if valor: militar.cargo_funcao = valor

        valor = request.form.get('data_nascimento')
        if valor: militar.data_nascimento = str_to_date(valor)

        valor = request.form.get('data_incorporacao')
        if valor: militar.data_incorporacao = str_to_date(valor)

        valor = request.form.get('data_ultima_promocao')
        if valor: militar.data_ultima_promocao = str_to_date(valor)

        valor = request.form.get('nivel_academico')
        if valor: militar.nivel_academico = valor

        valor = request.form.get('regime')
        if valor: militar.regime = valor

        valor = request.form.get('sexo')
        if valor: militar.sexo = valor

        valor = request.form.get('idade')
        if valor: militar.idade = int(valor)

        valor = request.form.get('tempo_servico')
        if valor: militar.tempo_servico = int(valor)

        valor = request.form.get('especialidade')
        if valor: militar.especialidade = valor

        valor = request.form.get('unidade')
        if valor: militar.unidade = valor

        valor = request.form.get('provincia')
        if valor: militar.provincia = valor

        valor = request.form.get('distrito')
        if valor: militar.distrito = valor

        valor = request.form.get('nuit')
        if valor: militar.nuit = valor

        valor = request.form.get('conta_bancaria')
        if valor: militar.conta_bancaria = valor

        valor = request.form.get('banco')
        if valor: militar.banco = valor

        valor = request.form.get('numero_os_ultima_promocao')
        if valor: militar.numero_os_ultima_promocao = valor

        valor = request.form.get('situacao')
        if valor: militar.situacao = valor

        # --- Tratamento especial para falecidos ---
        if militar.situacao == "Falecido":
            valor = request.form.get('data_obito')
            if valor:
                militar.data_obito = str_to_date(valor)
            else:
                flash("⚠️ É obrigatório indicar a Data de Óbito.", "danger")
                return redirect(url_for("edit_militar", id=militar.id))

            valor = request.form.get('causa_obito')
            if valor:
                militar.causa_obito = valor
            else:
                flash("⚠️ É obrigatório indicar a Causa do Óbito.", "danger")
                return redirect(url_for("edit_militar", id=militar.id))

        valor = request.form.get('obs_obito')
        if valor:
            militar.obs_obito = valor

        valor = request.form.get('ordem_servico')
        if valor: militar.ordem_servico = valor

        # --- Upload da Foto ---
        foto = request.files.get('foto')
        if foto and foto.filename != '':
            filename = secure_filename(foto.filename)
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(caminho)
            militar.foto = filename

        # --- Familiares (append sem apagar os antigos) ---
        nomes_familiares = request.form.getlist("nome_familiar[]")
        graus = request.form.getlist("grau_parentesco[]")
        datas_familiares = request.form.getlist("data_nasc_familiar[]")
        provincias = request.form.getlist("prov_familiar[]")
        moradas = request.form.getlist("morada_familiar[]")
        telefones = request.form.getlist("telefone_familiar[]")
        obs_familiares = request.form.getlist("obs_familiar[]")

        for i in range(len(nomes_familiares)):
            if nomes_familiares[i]:
                familiar = Familiar(
                    nome=nomes_familiares[i],
                    grau_parentesco=graus[i],
                    data_nasc=datetime.strptime(datas_familiares[i], "%Y-%m-%d").date() if datas_familiares[i] else None,
                    provincia=provincias[i],
                    morada=moradas[i],
                    telefone=telefones[i],
                    observacoes=obs_familiares[i],
                    militar=militar
                )
                db.session.add(familiar)

        # --- Funções (append) ---
        nomes_funcoes = request.form.getlist("funcao_nome[]")
        os_funcoes = request.form.getlist("funcao_os[]")
        datas_ordem = request.form.getlist("funcao_data[]")
        unidades = request.form.getlist("funcao_unidade[]")
        inicios = request.form.getlist("funcao_inicio[]")
        terminos = request.form.getlist("funcao_termino[]")
        obs_funcoes = request.form.getlist("funcao_obs[]")

        for i in range(len(nomes_funcoes)):
            inicio_date = datetime.strptime(inicios[i], "%Y-%m-%d").date() if inicios[i] else None
            termino_date = datetime.strptime(terminos[i], "%Y-%m-%d").date() if terminos[i] else None

            funcao = Funcao(
                nome=nomes_funcoes[i],
                ordem_servico=os_funcoes[i],
                data_ordem=datetime.strptime(datas_ordem[i], "%Y-%m-%d").date() if datas_ordem[i] else None,
                unidade=unidades[i],
                inicio=inicio_date,
                termino=termino_date,
                observacoes=obs_funcoes[i],
                militar=militar
            )

            try:
                funcao.validar_periodo()
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("edit_militar", id=id))

            db.session.add(funcao)

        # --- Promoções (append) ---
        patentes = request.form.getlist("promocao_patente[]")
        datas_promocoes = request.form.getlist("promocao_data[]")
        os_promocoes = request.form.getlist("promocao_os[]")
        obs_promocoes = request.form.getlist("promocao_obs[]")

        for i in range(len(patentes)):
            data_promocao = datetime.strptime(datas_promocoes[i], "%Y-%m-%d").date() if datas_promocoes[i] else None
            numero_os = os_promocoes[i].strip() if os_promocoes[i] else None

            promocao = Promocao(
                patente=patentes[i],
                data=data_promocao,
                numero_os=numero_os,
                observacoes=obs_promocoes[i],
                militar=militar
            )

            if data_promocao and data_promocao > datetime.today().date():
                flash("Data da promoção não pode ser futura.", "danger")
                return redirect(url_for("edit_militar", id=id))

            db.session.add(promocao)

        # --- Línguas (append) ---
        linguas = request.form.getlist("lingua_nome[]")
        outras = request.form.getlist("outra_lingua[]")
        fala = request.form.getlist("lingua_fala[]")
        leitura = request.form.getlist("lingua_leitura[]")
        escrita = request.form.getlist("lingua_escrita[]")
        compreensao = request.form.getlist("lingua_compreensao[]")
        materna = request.form.getlist("lingua_materna[]")

        for i in range(len(linguas)):
            nome = linguas[i]
            if nome == "Outra" and outras[i]:
                nome = outras[i]

            lingua = Lingua(
                nome=nome,
                fala=fala[i],
                leitura=leitura[i],
                escrita=escrita[i],
                compreensao=compreensao[i],
                materna=(materna[i] == "Sim"),
                militar=militar
            )
            db.session.add(lingua)

                        # --- Formações (append) ---
        cursos = request.form.getlist("curso[]")
        estabelecimentos = request.form.getlist("estabelecimento[]")
        tipos = request.form.getlist("tipo_curso[]")
        niveis = request.form.getlist("nivel[]")  # cuidado: no HTML é "nivel[]"
        duracoes = request.form.getlist("duracao[]")
        paises = request.form.getlist("pais[]")
        paises_outro = request.form.getlist("pais_outro[]")
        inicios_formacao = request.form.getlist("data_inicio[]")
        finais_formacao = request.form.getlist("data_final[]")
        obs_formacoes = request.form.getlist("observacoes[]")

        # Limpa formações antigas antes de recriar
        Formacao.query.filter_by(militar_id=militar.id).delete()

        for tipo, curso, estab, nivel, duracao, pais, pais_outro, inicio, fim, obs in zip(
            tipos, cursos, estabelecimentos, niveis, duracoes, paises, paises_outro,
            inicios_formacao, finais_formacao, obs_formacoes
        ):
            if not curso:  # só grava se tiver curso
                continue

            # Ajusta nível militar
            if tipo == "Militar":
                nivel = "ADEQUAÇÃO"
            # Ajusta país "Outro"
            if pais == "Outro":
                pais = pais_outro

            formacao = Formacao(
                tipo_curso=tipo,
                curso=curso,
                estabelecimento=estab,
                nivel=nivel,
                duracao=duracao,
                pais=pais,
                data_inicio=datetime.strptime(inicio, "%Y-%m-%d").date() if inicio else None,
                data_final=datetime.strptime(fim, "%Y-%m-%d").date() if fim else None,
                observacoes=obs,
                militar=militar
            )
            db.session.add(formacao)

        # --- Commit final ---
        db.session.commit()
        flash('Registro atualizado com sucesso!', 'success')
        return redirect(url_for('listar_militares'))

    # --- GET ---
    listas = carregar_listas()
    listas['unidades_previstas'] = [u.nome for u in Unidade.query.filter_by(prevista=True).all()]
    listas['unidades_nao_previstas'] = [u.nome for u in Unidade.query.filter_by(prevista=False).all()]
    listas['unidades'] = Unidade.query.all()
    listas['niveis'] = [
        "PhD", "Mestre", "Licenciado", "Bacharel",
        "Tecnico Medio", "12 Classe", "10 Classe",
        "7 Classe", "5 Classe"
    ]

    #return render_template('form.html', militar=militar, **listas)
    return render_template('form.html', militar=militar, editar=True, **listas)


# 🔑 Todas as tuas rotas de relatórios (relatorio_filtro, relatorio_filtro_excel, relatorio_filtro_pdf,
# relatorio_patente, relatorio_unidade, relatorio_provincia, relatorio_tempo_servico) permanecem iguais
# às que já tinhas no teu código original
from flask import send_file

from flask_login import current_user
from flask import send_file

@app.route('/relatorios/filtro/excel')
def relatorio_filtro_excel():
    patente = request.args.get("patente")
    unidade = request.args.get("unidade")
    especialidade = request.args.get("especialidade")
    nivel_academico = request.args.get("nivel_academico")
    regime = request.args.get("regime")
    tempo_servico = request.args.get("tempo_servico")
    nome = request.args.get("nome")
    sexo = request.args.get("sexo")
    situacao = request.args.get("situacao")   # <-- incluir também no Excel

    query = db.session.query(Militar)

    if patente and patente.strip() != "" and patente != "-- Todas --":
        query = query.filter(Militar.patente == patente)
    if unidade and unidade.strip() != "" and unidade != "-- Todas --":
        query = query.filter(Militar.unidade == unidade)
    if especialidade and especialidade.strip() != "" and especialidade != "-- Todas --":
        query = query.filter(Militar.especialidade == especialidade)
    if nivel_academico and nivel_academico.strip() != "" and nivel_academico != "-- Todas --":
        query = query.filter(Militar.nivel_academico == nivel_academico)
    if regime and regime.strip() != "" and regime != "-- Todas --":
        query = query.filter(Militar.regime == regime)
    if tempo_servico and tempo_servico.strip() != "" and tempo_servico != "-- Todos --":
        query = query.filter(Militar.tempo_servico == tempo_servico)
    if nome and nome.strip() != "":
        query = query.filter(Militar.nome_completo.ilike(f"%{nome}%"))
    if sexo and sexo.strip() != "":
        query = query.filter(Militar.sexo == sexo)
    if situacao and situacao.strip() != "" and situacao != "-- Todas --":
        query = query.filter(Militar.situacao == situacao)

    militares = query.all()

    # 👉 aqui usas a tua função gerar_relatorio_excel
    filename = gerar_relatorio_excel("Operador Zuba", militares)

    return send_file(
        filename,
        as_attachment=True,
        download_name="relatorio.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

from sqlalchemy import func
#from models import Militar

# 🔹 Blueprint
estatisticas_bp = Blueprint("estatisticas", __name__)

@estatisticas_bp.route("/estatisticas")
def estatisticas():
    totais_situacao = (
        db.session.query(Militar.situacao, func.count(Militar.id))
        .group_by(Militar.situacao)
        .all()
    )

    totais_por_patente = (
        db.session.query(Militar.situacao, Militar.patente, func.count(Militar.id))
        .group_by(Militar.situacao, Militar.patente)
        .all()
    )

    falecidos_por_causa = (
        db.session.query(Militar.causa_obito, func.count(Militar.id))
        .filter(Militar.situacao == "Falecido")
        .group_by(Militar.causa_obito)
        .all()
    )

    return render_template(
        "relator_estatistico.html",
        totais_situacao=totais_situacao,
        totais_por_patente=[
            {"situacao": s, "patente": p, "total": t}
            for s, p, t in totais_por_patente
        ],
        falecidos_por_causa=falecidos_por_causa
    )

# 🔹 Registrar blueprint
app.register_blueprint(estatisticas_bp)


@app.route('/relatorios/filtro/pdf')
def relatorio_filtro_pdf():
    patente = request.args.get("patente")
    unidade = request.args.get("unidade")
    especialidade = request.args.get("especialidade")
    nivel_academico = request.args.get("nivel_academico")
    regime = request.args.get("regime")
    tempo_servico = request.args.get("tempo_servico")
    nome = request.args.get("nome")
    sexo = request.args.get("sexo")
    situacao = request.args.get("situacao")

    query = db.session.query(Militar)

    if patente: query = query.filter(Militar.patente == patente)
    if unidade: query = query.filter(Militar.unidade == unidade)
    if especialidade: query = query.filter(Militar.especialidade == especialidade)
    if nivel_academico: query = query.filter(Militar.nivel_academico == nivel_academico)
    if regime: query = query.filter(Militar.regime == regime)
    if tempo_servico: query = query.filter(Militar.tempo_servico == tempo_servico)
    if nome: query = query.filter(Militar.nome_completo.ilike(f"%{nome}%"))
    if sexo: query = query.filter(Militar.sexo == sexo)
    if situacao: query = query.filter(Militar.situacao == situacao)

    militares = query.all()

    # Converter militares em lista de listas para tabela PDF
    dados = [["ID", "Nome", "Patente", "Unidade", "Situação"]]
    for m in militares:
        dados.append([m.id, m.nome_completo, m.patente, m.unidade, m.situacao])  # <-- corrigido para m.id

    # Nome do operador autenticado
    operador_nome = current_user.nome if current_user.is_authenticated else "Operador desconhecido"

    # Dicionário de filtros aplicados
    filtros = {
        "Patente": patente,
        "Unidade": unidade,
        "Especialidade": especialidade,
        "Nível Académico": nivel_academico,
        "Regime": regime,
        "Tempo de Serviço": tempo_servico,
        "Nome": nome,
        "Sexo": sexo,
        "Situação": situacao
    }

    # Gerar PDF com filtros
    filename = gerar_relatorio_pdf(operador_nome, dados, filtros)

    return send_file(
        filename,
        as_attachment=True,
        download_name="relatorio.pdf",
        mimetype="application/pdf"
    )

  

@app.route('/militar/<int:id>')
def ficha_militar(id):
    # Busca o militar pelo ID
    militar = Militar.query.get_or_404(id)

    # Renderiza a ficha completa com todos os dados e relacionamentos
    return render_template("ficha_militar.html", militar=militar)


    
@app.route('/formacao')
def listar_formacao():
    nome = request.args.get("nome")
    unidade = request.args.get("unidade")

    query = db.session.query(Formacao).join(Militar)

    if nome:
        query = query.filter(Militar.nome_completo == nome)
    if unidade:
        query = query.filter(Militar.unidade == unidade)

    dados = query.all()

    # Listas únicas para os selects (evita duplicação)
    militares = db.session.query(Militar.nome_completo).distinct().all()
    unidades = db.session.query(Militar.unidade).distinct().all()

    # Flatten para listas simples
    militares = [m[0] for m in militares]
    unidades = [u[0] for u in unidades]

    return render_template(
        "listar_formacao.html",
        dados=dados,
        militares=militares,
        unidades=unidades
    )


@app.route('/formacao/apagar/<int:id>', methods=['POST'])
def apagar_formacao(id):
    formacao = Formacao.query.get_or_404(id)
    db.session.delete(formacao)
    db.session.commit()
    flash("Formação apagada com sucesso!", "danger")
    return redirect(url_for('listar_formacao'))
    
@app.route('/formacao/editar/<int:id>', methods=['GET', 'POST'])
def editar_formacao(id):
    formacao = Formacao.query.get_or_404(id)

    if request.method == 'POST':
        formacao.militar_id = int(request.form['id_militar'])
        formacao.curso = request.form['curso']
        formacao.estabelecimento = request.form['estabelecimento']
        formacao.data_inicio = datetime.strptime(request.form['data_inicio'], "%Y-%m-%d").date()

        data_final = request.form['data_final']
        formacao.data_final = datetime.strptime(data_final, "%Y-%m-%d").date() if data_final else None

        formacao.observacoes = request.form.get('observacoes')

        db.session.commit()
        flash("Formação atualizada com sucesso!", "success")
        return redirect(url_for('listar_formacao'))

    militares = Militar.query.all()
    return render_template('formacao_editar.html', formacao=formacao, militares=militares)


    
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash

@app.route('/formacao/novo', methods=['GET', 'POST'])
def nova_formacao():
    if request.method == 'POST':
        try:
            militar_id = request.form.get("militar_id")
            if not militar_id:
                flash("Selecione um militar antes de salvar a formação.", "danger")
                return redirect(url_for("nova_formacao"))

            curso = request.form["curso"]
            estabelecimento = request.form["estabelecimento"]

            # Converter datas para objetos date
            data_inicio = datetime.strptime(request.form["data_inicio"], "%Y-%m-%d").date()
            data_final = request.form["data_final"]
            data_final = datetime.strptime(data_final, "%Y-%m-%d").date() if data_final else None

            # Criar objeto Formacao
            nova = Formacao(
                militar_id=int(militar_id),
                curso=curso,
                estabelecimento=estabelecimento,
                data_inicio=data_inicio,
                data_final=data_final
            )

            db.session.add(nova)
            db.session.commit()
            flash("Formação cadastrada com sucesso!", "success")
            return redirect(url_for("listar_formacao"))

        except Exception as e:
            flash(f"Erro ao cadastrar formação: {e}", "danger")
            return redirect(url_for("nova_formacao"))

    militares = Militar.query.all()
    return render_template("formacao_novo.html", militares=militares)

@app.route('/relatorios/formacoes/pdf')
def relatorio_formacoes_pdf():
    nome = request.args.get("nome")
    unidade = request.args.get("unidade")

    query = db.session.query(Formacao).join(Militar)

    if nome:
        query = query.filter(Militar.nome_completo.ilike(f"%{nome}%"))
    if unidade:
        query = query.filter(Militar.unidade.ilike(f"%{unidade}%"))

    formacoes = query.all()

    # Converter formações em lista de listas para tabela PDF
    dados = [["Nome", "Unidade", "Curso", "Estabelecimento", "Data Início", "Data Final"]]
    for f in formacoes:
        dados.append([
            f.militar.nome_completo,
            f.militar.unidade,
            f.curso,
            f.estabelecimento,
            f.data_inicio.strftime("%d/%m/%Y"),
            f.data_final.strftime("%d/%m/%Y") if f.data_final else "-"
        ])

    # Nome do operador autenticado
    operador_nome = current_user.nome if current_user.is_authenticated else "Operador desconhecido"

    # Filtros aplicados
    filtros = {
        "Nome": nome,
        "Unidade": unidade
    }

    # Gerar PDF
    filename = gerar_relatorio_pdf(operador_nome, dados, filtros)

    return send_file(
        filename,
        as_attachment=True,
        download_name="formacoes.pdf",
        mimetype="application/pdf"
    )

  
@app.route('/unidades/nova', methods=['GET', 'POST'])
def nova_unidade():
    if request.method == 'POST':
        nome = request.form['nome']
        prevista = request.form['prevista'] == 'true'
        nova = Unidade(nome=nome, prevista=prevista)
        db.session.add(nova)
        db.session.commit()
        return redirect(url_for('unidades'))
    return render_template('nova_unidade.html')
    
    
@app.route('/unidades/editar/<int:id>', methods=['GET', 'POST'])
def editar_unidade(id):
    unidade = Unidade.query.get_or_404(id)

    if request.method == 'POST':
        unidade.nome = request.form['nome']
        unidade.prevista = request.form['prevista'] == 'true'
        db.session.commit()
        return redirect(url_for('unidades'))

    return render_template('editar_unidade.html', unidade=unidade)

@app.route('/unidades/apagar/<int:id>', methods=['POST', 'GET'])
def apagar_unidade(id):
    unidade = Unidade.query.get_or_404(id)
    db.session.delete(unidade)
    db.session.commit()
    return redirect(url_for('unidades'))
    
@app.route('/relatorios/contagem', methods=['GET'])
def relatorio_contagem():
    patente = request.args.get("patente")
    unidade = request.args.get("unidade")
    especialidade = request.args.get("especialidade")
    regime = request.args.get("regime")
    situacao = request.args.get("situacao")   # <-- Novo filtro

    # Corrigido: usa Militar.id
    query = db.session.query(db.func.count(Militar.id).label("total"))

    if patente:
        query = query.filter(Militar.patente == patente)
    if unidade:
        query = query.filter(Militar.unidade == unidade)
    if especialidade:
        query = query.filter(Militar.especialidade == especialidade)
    if regime:
        query = query.filter(Militar.regime == regime)
    if situacao:
        query = query.filter(Militar.situacao == situacao)

    total = query.scalar()

    # Dropdowns
    patentes = [p[0] for p in db.session.query(Militar.patente.distinct()).filter(Militar.patente != None, Militar.patente != '').all()]
    unidades = [u[0] for u in db.session.query(Militar.unidade.distinct()).filter(Militar.unidade != None, Militar.unidade != '').all()]
    especialidades = [e[0] for e in db.session.query(Militar.especialidade.distinct()).filter(Militar.especialidade != None, Militar.especialidade != '').all()]
    regimes = [r[0] for r in db.session.query(Militar.regime.distinct()).filter(Militar.regime != None, Militar.regime != '').all()]
    situacoes = [s[0] for s in db.session.query(Militar.situacao.distinct()).filter(Militar.situacao != None, Militar.situacao != '').all()]

    return render_template(
        "relatorio_contagem.html",
        patente=patente,
        unidade=unidade,
        especialidade=especialidade,
        regime=regime,
        situacao=situacao,
        total=total,
        patentes=patentes,
        unidades=unidades,
        especialidades=especialidades,
        regimes=regimes,
        situacoes=situacoes
    )

from flask import session

@app.route('/logout')
@login_required
def logout():
    # Auditoria
    registrar_auditoria(current_user.username, "Logout", "Saiu do sistema")

    logout_user()  # encerra sessão do Flask-Login
    flash("Sessão encerrada com sucesso!", "info")
    return redirect(url_for('login'))

    
@app.route('/dashboard')
@login_required
def dashboard():
    # Totais já existentes
    total_usuarios = Usuario.query.count()
    total_unidades = Unidade.query.count()
    unidades_previstas = Unidade.query.filter_by(prevista=True).count()
    unidades_nao_previstas = Unidade.query.filter_by(prevista=False).count()

    # Contagem por categoria de patente
    militares = Militar.query.all()
    oficiais_count = sum(1 for m in militares if PATENTE_CATEGORIA.get(m.patente) == "Oficial")
    sargentos_count = sum(1 for m in militares if PATENTE_CATEGORIA.get(m.patente) == "Sargento")
    pracas_count = sum(1 for m in militares if PATENTE_CATEGORIA.get(m.patente) == "Praça")

    return render_template(
        "dashboard.html",
        total_usuarios=total_usuarios,
        total_unidades=total_unidades,
        unidades_previstas=unidades_previstas,
        unidades_nao_previstas=unidades_nao_previstas,
        oficiais_count=oficiais_count,
        sargentos_count=sargentos_count,
        pracas_count=pracas_count
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = Usuario.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login efetuado com sucesso!", "success")

            # Auditoria
            registrar_auditoria(user.username, "Login", "Entrou no sistema")

            return redirect(url_for("dashboard"))
        else:
            flash("Usuário ou senha inválidos", "danger")

    return render_template("login.html")


def add_usuario():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        perfil = request.form.get("perfil")

        # Verifica duplicados
        if Usuario.query.filter_by(username=username).first():
            flash("Usuário já existe!", "warning")
        elif Usuario.query.filter_by(email=email).first():
            flash("Email já cadastrado!", "warning")
        else:
            novo_usuario = Usuario(
                nome=nome,
                email=email,
                username=username,
                perfil=perfil
            )
            novo_usuario.set_password(password)  # usa werkzeug para hash
            db.session.add(novo_usuario)
            db.session.commit()
            flash("Usuário criado com sucesso!", "success")
            return redirect(url_for("usuarios"))

    # GET ou falha → mostra formulário
    return render_template("add_usuario.html")
 
@app.route("/teste")
@login_required
def teste():
    return f"Perfil atual: {current_user.perfil}"


@app.route("/admin/usuarios")
@login_required
@perfis_requeridos('admin')   # <-- só Admin pode criar usuários
def usuarios():
    lista_usuarios = Usuario.query.all()
    return render_template("usuarios.html", usuarios=lista_usuarios)


@app.route("/admin/usuarios/add", methods=["GET", "POST"])
@login_required
@perfis_requeridos('admin')   # só Admin pode adicionar usuários
def add_usuario():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        perfil = request.form.get("perfil").lower()  # padroniza em minúsculas
        

        # Verifica duplicados
        if Usuario.query.filter_by(username=username).first():
            flash("Usuário já existe!", "warning")
        elif Usuario.query.filter_by(email=email).first():
            flash("Email já cadastrado!", "warning")
        else:
            novo_usuario = Usuario(
                nome=nome,
                email=email,
                username=username,
                perfil=perfil
            )
            novo_usuario.set_password(password)  # usa werkzeug para hash
            db.session.add(novo_usuario)
            db.session.commit()
            flash("Usuário criado com sucesso!", "success")
            return redirect(url_for("usuarios"))  # volta para listagem

    # GET ou falha → mostra formulário
    return render_template("add_usuario.html")


# Rota para editar usuário
@app.route("/usuarios/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == "POST":
        usuario.nome = request.form.get("nome")
        usuario.email = request.form.get("email")
        usuario.username = request.form.get("username")
        usuario.perfil = request.form.get("perfil")

        nova_senha = request.form.get("password")
        if nova_senha:
            usuario.set_password(nova_senha)

        db.session.commit()
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("usuarios"))

    return render_template("editar_usuario.html", usuario=usuario)


# Rota para apagar usuário
@app.route("/usuarios/<int:id>/apagar", methods=["GET", "POST"])
@login_required
def apagar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == "POST":
        db.session.delete(usuario)
        db.session.commit()
        flash("Usuário apagado com sucesso!", "success")
        return redirect(url_for("usuarios"))
    return render_template("apagar_usuario.html", usuario=usuario)
    

from sqlalchemy import func, cast
from sqlalchemy.types import String

@app.route('/filtro_militar', methods=['GET', 'POST'])
@login_required
@perfis_requeridos('admin', 'operador')
def filtro_militar():
    nuit = request.form.get("nuit") or request.args.get("nuit")
    if nuit:
        nuit = nuit.strip()

    # Remove espaços e tabs invisíveis antes de comparar
    militar = Militar.query.filter(
        func.replace(func.trim(cast(Militar.nuit, String)), '\t', '') == nuit
    ).first()

    if militar:
        # Corrigido: chama a função ficha_militar_detalhe
        return redirect(url_for('ficha_militar_detalhe', id=militar.id))
    else:
        return render_template("filtro_militar.html", erro=True)




from sqlalchemy.orm import joinedload

@app.route('/ficha_militar/<int:id>')
@login_required
@perfis_requeridos('admin', 'operador')
def ficha_militar_detalhe(id):
    militar = Militar.query.options(
        joinedload(Militar.familiares),
        joinedload(Militar.lista_funcoes),
        joinedload(Militar.promocoes),
        joinedload(Militar.linguas),
        joinedload(Militar.formacoes)
    ).get_or_404(id)

    return render_template("ficha_militar.html", militar=militar)

    
import pdfkit
from flask import Flask, render_template, make_response

@app.route('/militar/<int:id>/pdf')
def militar_pdf(id):
    militar = Militar.query.get_or_404(id)
    html = render_template("ficha_militar.html", militar=militar)

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    options = {
        'enable-local-file-access': None
    }

    pdf = pdfkit.from_string(html, False, configuration=config, options=options)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=ficha_militar_{id}.pdf'
    return response


@app.route("/unidades")
@login_required
def unidades():
    lista_unidades = Unidade.query.all()
    return render_template("listar_unidades.html", unidades=lista_unidades)

    
@app.route("/usuarios")
@login_required
@perfis_requeridos('admin')
def listar_usuarios():   # <-- nome diferente
    lista_usuarios = Usuario.query.all()
    return render_template("usuarios.html", usuarios=lista_usuarios)

from flask import send_file

@app.route('/relatorio')
def relatorio():
    dados = ["Militar 1 - Formação X", "Militar 2 - Formação Y"]
    gerar_relatorio_pdf("Operador Zuba", dados)
    return send_file("relatorio.pdf", as_attachment=True)

@app.route("/apagar_familiar/<int:id>", methods=["POST"])
@login_required
def apagar_familiar(id):
    familiar = Familiar.query.get_or_404(id)
    militar_id = familiar.militar_id
    db.session.delete(familiar)
    db.session.commit()
    flash("Familiar removido com sucesso!", "danger")
    return redirect(url_for("editar_militar", id=militar_id))  # garante que o nome bate certo

@app.route("/check_nuit/<nuit>")
def check_nuit(nuit):
    # limpa espaços e garante tipo
    nuit = nuit.strip()

    existente = Militar.query.filter_by(nuit=nuit).first()
    print("NUIT recebido:", nuit)
    print("Encontrado:", existente)

    return jsonify({"exists": bool(existente)})


# Remover Função
@app.route("/apagar_funcao/<int:id>", methods=["POST"])
@login_required
def apagar_funcao(id):
    # Buscar a função pelo ID
    funcao = Funcao.query.get_or_404(id)

    # Guardar o ID do militar associado
    militar_id = funcao.militar_id

    # Remover a função
    db.session.delete(funcao)
    db.session.commit()

    # Mensagem de feedback
    flash("Função removida com sucesso!", "danger")

    # Redirecionar para edição do militar
    return redirect(url_for("edit_militar", id=militar_id))


# Remover Promoção
@app.route("/apagar_promocao/<int:id>", methods=["POST"])
@login_required
def apagar_promocao(id):
    # Buscar a promoção pelo ID
    promocao = Promocao.query.get_or_404(id)

    # Guardar o ID do militar associado
    militar_id = promocao.militar_id

    # Remover a promoção
    db.session.delete(promocao)
    db.session.commit()

    # Mensagem de feedback
    flash("Promoção removida com sucesso!", "danger")

    # Redirecionar para edição do militar
    return redirect(url_for("edit_militar", id=militar_id))


# Remover Língua
@app.route("/apagar_lingua/<int:id>", methods=["POST"])
@login_required
def apagar_lingua(id):
    # Buscar a língua pelo ID
    lingua = Lingua.query.get_or_404(id)

    # Guardar o ID do militar associado
    militar_id = lingua.militar_id

    # Remover a língua
    db.session.delete(lingua)
    db.session.commit()

    # Mensagem de feedback
    flash("Língua removida com sucesso!", "danger")

    # Redirecionar para edição do militar
    return redirect(url_for("edit_militar", id=militar_id))


   
# Delete militar
@app.route('/delete/<int:id>', methods=['POST'])
def delete_militar(id):
    militar = Militar.query.get_or_404(id)
    db.session.delete(militar)
    db.session.commit()
    flash('Registro excluído com sucesso!', 'danger')
    return redirect(url_for('listar_militares'))

with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(username="admin").first():
        u = Usuario(
            nome="Admin",
            email="admin@example.com",
            username="admin",
            perfil="Admin"
        )
        u.set_password("1234")
        db.session.add(u)
        db.session.commit()
        
from datetime import datetime

@app.route('/auditorias')
@login_required
def listar_auditorias():
    usuario = request.args.get('usuario')
    acao = request.args.get('acao')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    query = Auditoria.query

    if usuario and usuario.strip():
        query = query.filter(Auditoria.usuario == usuario)

    if acao and acao.strip():
        query = query.filter(Auditoria.acao == acao)

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(Auditoria.data_hora >= dt_inicio)
        except ValueError:
            flash("Data inicial inválida", "danger")

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, "%Y-%m-%d")
            dt_fim = dt_fim.replace(hour=23, minute=59, second=59)
            query = query.filter(Auditoria.data_hora <= dt_fim)
        except ValueError:
            flash("Data final inválida", "danger")

    logs = query.order_by(Auditoria.data_hora.desc()).all()

    # 🔹 lista de usuários distintos já registados em auditorias
    usuarios = [u[0] for u in db.session.query(Auditoria.usuario).distinct().all()]
    # 🔹 lista fixa de ações
    acoes = ['Criar', 'Editar', 'Eliminar', 'Login', 'Logout', 'Exportar']

    return render_template("auditorias.html", logs=logs, usuarios=usuarios, acoes=acoes)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # cria admin se não existir (verifica username OU email)
        admin = Usuario.query.filter(
            (Usuario.username == "admin") | (Usuario.email == "admin@example.com")
        ).first()

        if not admin:
            admin = Usuario(
                nome="Admin",
                email="admin@example.com",
                username="admin",
                perfil="Admin"
            )
            admin.set_password("1234")
            db.session.add(admin)
            db.session.commit()
            print("Usuário admin criado com sucesso!")

    app.run(debug=True)




