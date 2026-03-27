import sqlite3
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os

os.makedirs('../boletos', exist_ok=True)

# ── LER FATURAS DO BANCO ─────────────────────────────────────────────────────
conn = sqlite3.connect('../parte1_cadastro/instance/techsolutions.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas = cursor.fetchall()
print("Tabelas no banco:", tabelas)

cursor.execute('''
    SELECT f.id, c.nome, c.email, f.valor, f.data_vencimento
    FROM fatura f
    JOIN cliente c ON f.cliente_id = c.id
''')
faturas = cursor.fetchall()
conn.close()

print(f"Faturas encontradas: {len(faturas)}")

# ── GERAR UM PDF POR FATURA ──────────────────────────────────────────────────
def gerar_boleto(fatura_id, nome, email, valor, vencimento):
    # Gera o QR Code
    dados_pix = f"PIX|TechSolutions|R${valor:.2f}|Fatura#{fatura_id}|Venc:{vencimento}"
    img_qr = qrcode.make(dados_pix)
    qr_path = f'../boletos/qr_{fatura_id}.png'
    img_qr.save(qr_path)

    # Cria o PDF
    arquivo = f'../boletos/boleto_cliente{fatura_id:03d}.pdf'
    c = canvas.Canvas(arquivo, pagesize=A4)
    largura, altura = A4

    # Cabeçalho azul
    c.setFillColorRGB(0, 0.4, 0.8)
    c.rect(0, altura - 80, largura, 80, fill=True, stroke=False)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(2*cm, altura - 50, "TechSolutions Ltda")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, altura - 68, "BOLETO / FATURA")

    # Dados do cliente
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(2*cm, altura - 120, f"Cliente: {nome}")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, altura - 145, f"E-mail: {email}")
    c.drawString(2*cm, altura - 165, f"Nº da Fatura: {fatura_id:03d}")

    # Valor e vencimento
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(1.5*cm, altura - 230, largura - 3*cm, 50, fill=True, stroke=False)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, altura - 200, f"Valor: R$ {valor:.2f}")
    c.drawString(10*cm, altura - 200, f"Vencimento: {vencimento}")

    # Código de barras simulado
    c.setFont("Helvetica", 8)
    codigo = f"0001.{fatura_id:04d} 0002.{int(valor*100):06d} 0003.{str(vencimento).replace('-','')}"
    c.drawString(2*cm, altura - 280, f"Código: {codigo}")

    # QR Code
    c.drawImage(qr_path, largura - 6*cm, altura - 380, width=4*cm, height=4*cm)
    c.setFont("Helvetica", 9)
    c.drawString(largura - 6*cm, altura - 390, "Pague com PIX")

    # Rodapé
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(2*cm, 1.5*cm, "TechSolutions Ltda | contato@techsolutions.com.br")

    c.save()
    print(f"✅ PDF gerado: {arquivo}")

# ── RODAR PARA TODAS AS FATURAS ──────────────────────────────────────────────
for fatura in faturas:
    gerar_boleto(*fatura)

print(f"\n🎉 {len(faturas)} boletos gerados na pasta /boletos!")