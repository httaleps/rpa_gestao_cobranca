import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os
from segredos import EMAIL_REMETENTE, SENHA_APP

# ── 1. LER PLANILHA ──────────────────────────────────────────────────────────
df = pd.read_excel('../dados/clientes.xlsx')
logs = []

# ── 2. CONECTAR AO SERVIDOR SMTP ─────────────────────────────────────────────
try:
    servidor = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    servidor.login(EMAIL_REMETENTE, SENHA_APP)
    print("✅ Conexão SMTP estabelecida!")
except Exception as e:
    print(f"❌ Falha na conexão SMTP: {e}")
    exit()

# ── 3. ENVIAR E-MAIL PARA CADA CLIENTE ───────────────────────────────────────
for index, row in df.iterrows():
    nome       = row['nome']
    email      = row['email']
    valor      = row.get('valor', 0)
    vencimento = row.get('vencimento', 'N/A')
    pdf_path   = f'../boletos/boleto_cliente{index+1:03d}.pdf'

    try:
        # Monta o e-mail
        msg = MIMEMultipart()
        msg['From']    = EMAIL_REMETENTE
        msg['To']      = email
        msg['Subject'] = f"Fatura TechSolutions - Vencimento {vencimento}"

        # Corpo do e-mail
        corpo = f"""
        <html><body>
        <p>Olá, <strong>{nome}</strong>!</p>
        <p>Segue sua fatura da <strong>TechSolutions Ltda</strong>:</p>
        <ul>
            <li>Valor: <strong>R$ {valor:.2f}</strong></li>
            <li>Vencimento: <strong>{vencimento}</strong></li>
        </ul>
        <p>O boleto com QR Code está em anexo.</p>
        <p>Qualquer dúvida, estamos à disposição!</p>
        <p>Atenciosamente,<br>Equipe TechSolutions</p>
        </body></html>
        """
        msg.attach(MIMEText(corpo, 'html'))

        # Anexa o PDF do boleto (se existir)
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="boleto_{nome}.pdf"')
            msg.attach(part)

        # Envia
        servidor.sendmail(EMAIL_REMETENTE, email, msg.as_string())
        print(f"✅ E-mail enviado para {nome} ({email})")
        logs.append({'cliente': nome, 'email': email, 'status': 'Enviado', 'hora': datetime.now()})

    except Exception as e:
        print(f"❌ Erro ao enviar para {nome}: {e}")
        logs.append({'cliente': nome, 'email': email, 'status': f'Falhou: {e}', 'hora': datetime.now()})

servidor.quit()

# ── 4. SALVAR LOGS ────────────────────────────────────────────────────────────
import csv
with open('../dados/log_emails.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['cliente', 'email', 'status', 'hora'])
    writer.writeheader()
    writer.writerows(logs)

print(f"\n✅ {sum(1 for l in logs if l['status']=='Enviado')} e-mails enviados com sucesso!")