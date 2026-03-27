import pandas as pd
import urllib.parse
import pyautogui
import time
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ── 1. LER PLANILHA ──────────────────────────────────────────────────────────
df = pd.read_excel('../dados/clientes_whatsapp.xlsx')
df['Status'] = ''
erros = []

def validar_telefone(tel):
    tel_limpo = str(tel).replace(' ','').replace('-','').replace('(','').replace(')','')
    return tel_limpo if len(tel_limpo) in [10, 11] else None

# ── 2. ABRIR WHATSAPP WEB ────────────────────────────────────────────────────
driver = webdriver.Chrome()
driver.get('https://web.whatsapp.com')

print("⏳ Escaneie o QR Code do WhatsApp Web. Aguardando 30 segundos...")
time.sleep(30)

# ── 3. ENVIAR MENSAGEM PARA CADA CLIENTE ─────────────────────────────────────
for index, row in df.iterrows():
    nome       = row['nome']
    telefone   = validar_telefone(row['telefone'])
    valor      = row.get('valor', 0)
    vencimento = row.get('vencimento', 'N/A')
    fatura_num = index + 1

    if not telefone:
        print(f"❌ Telefone inválido: {nome}")
        erros.append({'cliente': nome, 'erro': 'Telefone inválido', 'data': datetime.now()})
        df.at[index, 'Status'] = 'Falhou'
        continue

    try:
        mensagem = (
            f"Olá {nome}! 👋\n"
            f"Aqui é da *TechSolutions Ltda*.\n\n"
            f"Sua fatura de *R$ {valor:.2f}* vence em *{vencimento}*.\n"
            f"Segue em anexo seu boleto com QR Code PIX.\n\n"
            f"Qualquer dúvida estamos à disposição! 😊"
        )

        msg_codificada = urllib.parse.quote(mensagem)
        url = f"https://web.whatsapp.com/send?phone=55{telefone}&text={msg_codificada}"

        driver.get(url)
        time.sleep(6)

        # Clica no botão enviar
        botao = pyautogui.locateOnScreen('btn_enviar.png', confidence=0.7)
        if botao:
            pyautogui.click(botao)
            print(f"✅ Mensagem enviada para {nome}")
            df.at[index, 'Status'] = 'Enviado'
        else:
            raise Exception("Botão enviar não encontrado na tela")

        time.sleep(3)

    except Exception as e:
        print(f"❌ Erro ao enviar para {nome}: {e}")
        erros.append({'cliente': nome, 'erro': str(e), 'data': datetime.now()})
        df.at[index, 'Status'] = 'Falhou'

driver.quit()

# ── 4. SALVAR ERROS E ATUALIZAR PLANILHA ─────────────────────────────────────
if erros:
    with open('../dados/erros.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['cliente', 'erro', 'data'])
        writer.writeheader()
        writer.writerows(erros)
    print(f"⚠️ {len(erros)} erros salvos em erros.csv")

df.to_excel('../dados/clientes_whatsapp.xlsx', index=False)
print("✅ Planilha atualizada com status!")