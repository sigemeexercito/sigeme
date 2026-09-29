from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from datetime import datetime
import os
from collections import Counter

def gerar_relatorio_pdf(nome_operador, dados, filtros, filename="relatorio.pdf"):
    c = canvas.Canvas(filename, pagesize=A4)
    largura, altura = A4

    # Emblema nacional (logo)
    caminho_emblema = os.path.join("static", "images", "emblema.png")
    if os.path.exists(caminho_emblema):
        c.drawImage(caminho_emblema, largura/2 - 40, altura - 100, width=80, height=80)

    # Textos oficiais
    c.setFont("Helvetica-Bold", 12)
    linhas = [
        "REPÚBLICA DE MOÇAMBIQUE",
        "MINISTÉRIO DA DEFESA NACIONAL",
        "ESTADO MAIOR GENERAL",
        "RAMO DO COMANDO DO EXÉRCITO",
        "REPARTIÇÃO DO PESSOAL",
        "SISTEMA DE GESTÃO DO MILITAR DO EXÉRCITO",
    ]
    y = altura - 120
    for linha in linhas:
        c.drawCentredString(largura/2, y, linha)
        y -= 15

    # SIGEME centralizado
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(largura/2, y - 20, "SIGEME")

    # Identificação do relatório
    c.setFont("Helvetica", 9)
    c.drawString(40, altura - 80, f"Operador: {nome_operador}")
    c.drawString(40, altura - 95, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Filtros aplicados
    y -= 60
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Filtros aplicados:")
    c.setFont("Helvetica", 9)
    y -= 15
    for chave, valor in filtros.items():
        if valor:  # só mostra filtros usados
            c.drawString(60, y, f"{chave}: {valor}")
            y -= 12

    # Corpo do relatório - tabela formatada
    tabela = Table(dados, colWidths=[3*cm, 4*cm, 3*cm, 4*cm, 3*cm, 3*cm])

    estilo = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ])
    tabela.setStyle(estilo)

    # Renderizar tabela no PDF (margem esquerda ajustada)
    tabela.wrapOn(c, largura, altura)
    tabela.drawOn(c, 20, y - 120)   # margem esquerda reduzida

    # Totais por Unidade
    unidades = [linha[1] for linha in dados[1:]]  # coluna Unidade
    contagem = Counter(unidades)

    y_resumo = y - 140 - (len(dados) * 12)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y_resumo, "Totais por Unidade:")
    y_resumo -= 15
    c.setFont("Helvetica", 9)
    for unidade, total in contagem.items():
        c.drawString(60, y_resumo, f"{unidade}: {total}")
        y_resumo -= 12

    c.showPage()
    c.save()
    return filename
