from app import db

class Militar(db.Model):
    __tablename__ = 'militares'
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(120), nullable=False)
    patente = db.Column(db.String(50), nullable=False)
    cargo_funcao = db.Column(db.String(100))
    data_nascimento = db.Column(db.Date)
    data_incorporacao = db.Column(db.Date)
    data_ultima_promocao = db.Column(db.Date)
    nivel_academico = db.Column(db.String(100))
    regime = db.Column(db.String(50))
    sexo = db.Column(db.String(1))
    idade = db.Column(db.Integer)
    tempo_servico = db.Column(db.Integer)
    especialidade = db.Column(db.String(100))
    unidade = db.Column(db.String(100))
    provincia = db.Column(db.String(100))
    distrito = db.Column(db.String(100))
    nuit = db.Column(db.String(50))
    conta_bancaria = db.Column(db.String(50))
    banco = db.Column(db.String(50))
    numero_os_ultima_promocao = db.Column(db.String(50))
