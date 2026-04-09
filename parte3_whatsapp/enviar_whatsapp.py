import pandas as pd
import urllib.parse
import sqlite3
import pyautogui
import time
import csv
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── 1. LER PLANILHA ──────────────────────────────────────────
# Lê direto do banco unindo clientes + faturas
conn = sqlite3.connect('../parte1_cadastro/instance/techsolutions.db')

df = pd.read_sql_query('''
    SELECT 
        c.nome        AS Nome,
        c.telefone    AS Telefone,
        f.valor       AS Valor,
        f.data_vencimento AS Vencimento,
        f.id          AS fatura_id
    FROM fatura f
    JOIN cliente c ON f.cliente_id = c.id
    WHERE f.status = 'pendente'
''', conn)

erros = []

conn.close()

conn_update = sqlite3.connect('../parte1_cadastro/instance/techsolutions.db')
cursor_update = conn_update.cursor()

# Gera o link do boleto automaticamente pelo id da fatura
df['Link'] = df['fatura_id'].apply(
    lambda fid: f"http://localhost:5000/boletos/boleto_cliente{fid:03d}.pdf"
)

# Cria colunas de controle se não existirem
if 'Status' not in df.columns:
    df['Status'] = 'Pendente'
if 'DataEnvio' not in df.columns:
    df['DataEnvio'] = ''

print(f"✅ {len(df)} faturas pendentes carregadas do banco.")

# # ── 1. LER PLANILHA ──────────────────────────────────────────
# df = pd.read_excel('../dados/clientes_whatsapp.xlsx')
#
# # criar colunas se não existirem
# if 'Status' not in df.columns:
#     df['Status'] = 'Pendente'
#
# if 'DataEnvio' not in df.columns:
#     df['DataEnvio'] = ''
#
# erros = []

# ── 2. VALIDAR TELEFONE ──────────────────────────────────────
def validar_telefone(tel):
    tel = str(tel)
    tel = tel.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    return tel if len(tel) in [10, 11] else None


# ── 3. ABRIR WHATSAPP WEB ────────────────────────────────────
driver = webdriver.Chrome()
driver.get('https://web.whatsapp.com')

print("⏳ Escaneie o QR Code do WhatsApp Web (30s)...")
time.sleep(30)


# ── 4. ENVIAR MENSAGENS ──────────────────────────────────────
for index, row in df.iterrows():

    # só envia se não foi enviado ainda
    if str(row['Status']).lower() == 'enviado':
        continue

    nome = row['Nome']
    telefone = validar_telefone(row['Telefone'])
    valor = row['Valor']
    vencimento = row['Vencimento']
    link_boleto = row['Link']

    if not telefone:
        print(f"❌ Telefone inválido: {nome}")
        df.at[index, 'Status'] = 'Falhou'

        erros.append({
            'cliente': nome,
            'erro': 'Telefone inválido',
            'data': datetime.now()
        })
        continue

    try:
        mensagem = (
            f"Olá {nome}! 👋\n\n"
            f"Sua fatura de R$ {valor} vence em {vencimento}.\n\n"
            f"Acesse seu boleto com QR Code:\n"
            f"{link_boleto}\n\n"
            f"TechSolutions"
        )

        msg = urllib.parse.quote(mensagem)

        url = f"https://web.whatsapp.com/send?phone=55{telefone}&text={msg}"
        driver.get(url)

        wait = WebDriverWait(driver, 30)

        # Selenium localiza e foca a caixa
        caixa = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@contenteditable="true"][@role="textbox"]')
            )
        )
        time.sleep(2)

        # PyAutoGUI clica no botão enviar (como pedido no enunciado)
        pyautogui.hotkey('enter')

        print(f"✅ Mensagem enviada para {nome}")

        df.at[index, 'Status'] = 'Enviado'
        df.at[index, 'DataEnvio'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor_update.execute(
            "UPDATE fatura SET status = 'enviado' WHERE id = ?",
            (int(row['fatura_id']),)
        )
        conn_update.commit()

        time.sleep(4)

    except Exception as e:
        print(f"❌ Erro ao enviar para {nome}: {e}")

        df.at[index, 'Status'] = 'Falhou'

        cursor_update.execute(
            "UPDATE fatura SET status = 'falhou' WHERE id = ?",
            (int(row['fatura_id']),)
        )
        conn_update.commit()

        erros.append({
            'cliente': nome,
            'erro': str(e),
            'data': datetime.now()
        })


# ── 5. SALVAR ERROS ──────────────────────────────────────────
if erros:
    with open('../dados/erros.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['cliente', 'erro', 'data']
        )
        writer.writeheader()
        writer.writerows(erros)

    print(f"⚠️ {len(erros)} erros salvos em erros.csv")


# ── 6. SALVAR PLANILHA (COM TRATAMENTO DE ERRO) ──────────────
try:
    df.to_excel('../dados/clientes_whatsapp.xlsx', index=False)
except:
    df.to_excel('../dados/clientes_whatsapp_atualizado.xlsx', index=False)
    print("⚠️ Planilha original aberta. Salvo como clientes_whatsapp_atualizado.xlsx")

conn_update.close()
driver.quit()

subprocess.run(['python', '../parte5_relatorio/relatorio.py'])
print("✅ Relatório atualizado automaticamente!")

print("✅ Processo finalizado!")