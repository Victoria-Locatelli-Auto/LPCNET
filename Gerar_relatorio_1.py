from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime, timedelta
import openpyxl
import time
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText


# ==================== CONFIGURAÇÕES E-MAIL ==========================


EMAIL_REMETENTE = "victoria.santos@mcmtocantins.com"
SENHA_EMAIL = "zxcc lqby cvsa pchf"  # ⚠️ Substitua pela senha de aplicativo gerada no Google!
EMAIL_DESTINATARIO = ["joao.antunes@mcmtocantins.com", "natalia.sobral@mcmtocantins.com","daniel@teddi.com.br"]
SMTP_SERVIDOR = "smtp.gmail.com"
SMTP_PORTA = 587


FILIAIS = ["137", "254", "255", "394", "395","396", "480"]

PASTA_RELATORIOS = "relatorios"
os.makedirs(PASTA_RELATORIOS, exist_ok=True)

# ==================== FUNÇÕES ==========================

def gerar_relatorio(filial_numero, context):
    page = context.new_page()

    try:
        page.goto("https://lpcnet.slapl.prod.aws.scania.com")
        print(f"➡️ Gerando relatório para a filial {filial_numero}")

        page.click('text=LOGÍSTICA')
        page.click('text=Posição do Pedido')
        page.wait_for_timeout(2000)

        page.fill("#clientesearch", filial_numero)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)

        mensagem_erro = page.query_selector("text=M.U")
        if mensagem_erro:
            print(f"❌ Filial {filial_numero} não encontrada. Pulando...")
            return None

        print(f"✅ Filial {filial_numero} selecionada")

        page.select_option("#selectPedidoDsm", "1")
        print("✅ Pedido DSM mais recente selecionado")

        page.wait_for_timeout(1000)

        with page.expect_navigation():
            page.click('text=Consulta')

        print(f"➡️ Navegou para {page.url}")

        page.wait_for_selector("div.table-responsive > table", timeout=90000)

        tabelas = page.query_selector_all("div.table-responsive > table")

        if len(tabelas) < 3:
            print(f"❌ Menos de 3 tabelas para a filial {filial_numero}")
            return None

        print(f"✅ {len(tabelas)} tabelas encontradas")

        workbook = openpyxl.Workbook()
        sheet_pedido = workbook.active
        sheet_pedido.title = f"Pedido {filial_numero}"

        # Salvar as três tabelas
        for idx, tabela in enumerate(tabelas):
            salvar_tabela(sheet_pedido, tabela, idx)
            sheet_pedido.append([])  # Linha em branco para separar

        nome_arquivo = f"{filial_numero}-{obter_data_formatada()}.xlsx"
        caminho_arquivo = os.path.join(PASTA_RELATORIOS, nome_arquivo)

        workbook.save(caminho_arquivo)
        print(f"✅ Relatório salvo como {caminho_arquivo}")

        return caminho_arquivo

    except Exception as e:
        print(f"❌ Erro na filial {filial_numero}: {e}")
        return None


def salvar_tabela(sheet, tabela, tabela_index):
    thead = tabela.query_selector("thead")
    tbody = tabela.query_selector("tbody")

    if thead:
        linhas_cabecalho = thead.query_selector_all("tr")

        headers_matrix = []
        for linha in linhas_cabecalho:
            row = []
            for th in linha.query_selector_all("th"):
                texto = th.inner_text().strip()
                colspan = int(th.get_attribute("colspan") or 1)
                for _ in range(colspan):
                    row.append(texto)
            headers_matrix.append(row)

        max_len = max(len(r) for r in headers_matrix)
        for r in headers_matrix:
            while len(r) < max_len:
                r.append("")

        cabecalhos = []
        for col in range(max_len):
            partes = []
            for row in headers_matrix:
                if row[col] and row[col] not in partes:
                    partes.append(row[col])

            nome_coluna = " - ".join(partes).strip()

            # 🔧 Correção específica para a Tabela 3
            if tabela_index == 2:
                if col == 5:
                    nome_coluna = "Quantidade - Solicitada"
                elif col == 6:
                    nome_coluna = "Quantidade - Atendida"
                elif col == 7:
                    nome_coluna = "Quantidade - Separada"
                elif col == 8:
                    nome_coluna = "Quantidade - Faturada"
                elif col in [0, 1]:
                    nome_coluna = "Peça"
                elif not nome_coluna:
                    nome_coluna = f"Coluna {col + 1}"  # Nome genérico se vier vazio

            else:
                if nome_coluna.lower().startswith("peça") and col in [0, 1]:
                    nome_coluna = "Peça"

            # 🔥 Aplicação das regras de renomeação:
            if nome_coluna == "ID - Separada":
                nome_coluna = "ID"
            elif nome_coluna == "Situação - Faturada":
                nome_coluna = "Situação"
            elif nome_coluna == "Pendência - (desdobrado)":
                nome_coluna = "Pendência"
            elif nome_coluna == "Pedido/Ano":
                nome_coluna = "Pedido/Ano - (desdobrado)"

            cabecalhos.append(nome_coluna)

        sheet.append(cabecalhos)

    for row in tbody.query_selector_all("tr"):
        dados = [td.inner_text().strip() for td in row.query_selector_all("td")]
        if dados:
            sheet.append(dados)


def obter_data_formatada():
    return datetime.now().strftime("%d-%m-%Y")

def enviar_email(anexos):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = ", ".join(EMAIL_DESTINATARIO)  # 🔹 Correção aqui! Transformando lista em string
    msg['Subject'] = f"Relatórios - {obter_data_formatada()}"

    corpo = MIMEText("Segue em anexo os relatórios gerados automaticamente do dia de ontem.", 'plain')
    msg.attach(corpo)

    for arquivo in anexos:
        with open(arquivo, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(arquivo))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(arquivo)}"'
            msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA) as server:
            server.starttls()
            server.login(EMAIL_REMETENTE, SENHA_EMAIL)
            server.send_message(msg)

        print("📧 Email enviado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")

def executar_rotina():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="estado_autenticado_LPCNET.json")

        arquivos_gerados = []

        for filial in FILIAIS:
            arquivo = gerar_relatorio(filial, context)
            if arquivo:
                arquivos_gerados.append(arquivo)

        browser.close()

        if arquivos_gerados:
                enviar_email(arquivos_gerados)
        else:
                print("⚠️ Nenhum relatório foi gerado para enviar.")

    
