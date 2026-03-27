import sqlite3
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime

# ── 1. IMPORTAR DO BANCO ──────────────────────────────────────────────────────
conn = sqlite3.connect('../parte1_cadastro/techsolutions.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT c.nome, c.telefone, c.email, f.valor, f.data_vencimento, f.status
    FROM fatura f
    JOIN cliente c ON f.cliente_id = c.id
''')
dados = cursor.fetchall()
conn.close()

# ── 2. CRIAR O EXCEL FORMATADO ────────────────────────────────────────────────
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Relatório de Faturas"

# Estilo do cabeçalho
cabecalho_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
cabecalho_font = Font(color="FFFFFF", bold=True, size=12)
borda = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

# Cabeçalhos
colunas = ['Nome', 'Telefone', 'E-mail', 'Valor (R$)', 'Vencimento', 'Status']
for col, titulo in enumerate(colunas, start=1):
    cell = ws.cell(row=1, column=col, value=titulo)
    cell.fill  = cabecalho_fill
    cell.font  = cabecalho_font
    cell.border = borda
    cell.alignment = Alignment(horizontal='center')

# ── 3. PREENCHER OS DADOS ─────────────────────────────────────────────────────
verde   = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
amarelo = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
vermelho = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

for row_idx, linha in enumerate(dados, start=2):
    for col_idx, valor in enumerate(linha, start=1):
        cell = ws.cell(row=row_idx, column=col_idx, value=valor)
        cell.border = borda
        cell.alignment = Alignment(horizontal='center')

    # Colorir linha pelo status
    status = linha[5]
    cor = verde if status == 'enviado' else (vermelho if status == 'falhou' else amarelo)
    for col in range(1, 7):
        ws.cell(row=row_idx, column=col).fill = cor

# Ajusta largura das colunas
for col in ws.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    ws.column_dimensions[col[0].column_letter].width = max_len + 4

# ── 4. SALVAR ─────────────────────────────────────────────────────────────────
arquivo = '../dados/faturas_relatorio.xlsx'
wb.save(arquivo)
print(f"✅ Relatório salvo em: {arquivo}")