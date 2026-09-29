import sqlite3

# Criar conexão com banco SQLite (arquivo local)
conn = sqlite3.connect("militares.db")
cursor = conn.cursor()

# Criar tabela principal
cursor.execute("""
CREATE TABLE IF NOT EXISTS Militares (
    id_militar INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_completo TEXT NOT NULL,
    patente TEXT,
    cargo_funcao TEXT,
    data_nascimento TEXT,
    data_incorporacao TEXT,
    data_ultima_promocao TEXT,
    nivel_academico TEXT,
    regime TEXT,
    sexo TEXT,
    idade INTEGER,
    tempo_servico INTEGER,
    especialidade TEXT,
    unidade TEXT,
    provincia TEXT,
    distrito TEXT,
    nuit TEXT,
    conta_bancaria TEXT,
    banco TEXT,
    numero_os_ultima_promocao TEXT
)
""")

conn.commit()
conn.close()
