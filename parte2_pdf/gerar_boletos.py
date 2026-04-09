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

# ── GERAR  QR CODE ──────────────────────────────────────────────────
def gerar_payload_pix(valor, fatura_id):
    chave_pix = "48991183497"  # substitua pela chave PIX real
    nome_beneficiario = "Tales Henrique Silveira de Sousa"
    cidade = "Palhoça"
    txid = f"FATURA{fatura_id:03d}"

    def campo(id, valor):
        return f"{id}{len(valor):02d}{valor}"

    merchant_account = campo("00", "BR.GOV.BCB.PIX") + campo("01", chave_pix)
    payload = (
        campo("00", "01") +
        campo("26", merchant_account) +
        campo("52", "0000") +
        campo("53", "986") +
        campo("54", f"{valor:.2f}") +
        campo("58", "BR") +
        campo("59", nome_beneficiario[:25]) +
        campo("60", cidade[:15]) +
        campo("62", campo("05", txid[:25]))
    )

    # CRC16 obrigatório no padrão PIX
    def crc16(data):
        crc = 0xFFFF
        for byte in data.encode('utf-8'):
            crc ^= byte << 8
            for _ in range(8):
                crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
        return crc & 0xFFFF

    payload += "6304"
    payload += f"{crc16(payload):04X}"
    return payload

# ── GERAR UM PDF POR FATURA ──────────────────────────────────────────────────
def gerar_boleto(fatura_id, nome, email, valor, vencimento):
    # Gera o QR Code
    dados_pix = gerar_payload_pix(valor, fatura_id)
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