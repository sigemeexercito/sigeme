import pandas as pd
import sqlite3
import os

# Caminho absoluto para garantir que o ficheiro é encontrado
excel_path = r"C:\Users\DELL\Documents\Projectos\"

# Verificação extra: listar ficheiros na pasta
print("Ficheiros na pasta:", os.listdir(r"C:\Users\DELL\Documents\Projectos\mapa_principal.xlsx"))

# 1. Ler a planilha Excel
df = pd.read_excel(excel_path, engine="openpyxl")
print("Primeiras linhas da planilha:")
print(df.head())
print("Nomes das colunas:")
print(df.columns)

# 2. Renomear colunas para bater com a tabela Militares
df = df.rename(columns={
    "NOME COMPLETO": "nome_completo",
    "PATENTE": "patente",
    "CARGO/FUNÇÃO ORGÂNICA": "cargo_funcao",
    "NASC": "data_nascimento",
    "INCORP": "data_incorporacao",
    "ULT-PRO": "data_ultima_promocao",
    "NÍVEL ACADÉMICO": "nivel_academico",
    "SEXO": "sexo",
    "IDADE": "idade",
    "TEMPO": "tempo_servico",
    "ESPECIALIDADE": "especialidade",
    "UNIDADE": "unidade",
    "PROVÍNCIA": "provincia",
    "DISTRITO": "distrito",
    "NUIT": "nuit",
    "Nº CONTA BANCÁRIA": "conta_bancaria",
    "BANCO": "banco",
    "Nº DA OS DA ÚLTIMA PROMOÇÃO": "numero_os_ultima_promocao"
})

# 3. Conectar ao banco SQLite
conn = sqlite3.connect("militares.db")

# 4. Inserir os dados na tabela Militares
df.to_sql("Militares", conn, if_exists="append", index=False)

conn.close()
print("Importação concluída com sucesso!")
