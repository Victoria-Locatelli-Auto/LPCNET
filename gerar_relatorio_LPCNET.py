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
SENHA_EMAIL = "zxcc lqby cvsa pchf"
EMAIL_DESTINATARIO = ["joao.antunes@mcmtocantins.com", "natalia.sobral@mcmtocantins.com","daniel@teddi.com.br"]
SMTP_SERVIDOR = "smtp.gmail.com"
SMTP_PORTA = 587

FILIAIS = ["137", "254", "255", "394", "395", "396", "480"]

PASTA_RELATORIOS = "relatorios"
os.makedirs(PASTA_RELATORIOS, exist_ok=True)

# ==================== FUNÇÕES ==========================

def gerar_relatorio(filial_numero, context, dsm_valores):
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

        options = page.query_selector_all("#selectPedidoDsm option")
        todos_valores = [opt.get_attribute("value") for opt in options if opt.get_attribute("value")]

        if not todos_valores:
            print(f"⚠️ Nenhum pedido DSM disponível para a filial {filial_numero}")
            return None

        opcoes_dsm = [todos_valores[i] for i in dsm_valores if i < len(todos_valores)]
        print(f"📄 DSMs selecionados para a filial {filial_numero}: {opcoes_dsm}")

        relatorios_filial = []

        for valor in opcoes_dsm:
            page.select_option("#selectPedidoDsm", valor)
            print(f"✅ Pedido DSM selecionado (valor={valor})")

            page.wait_for_timeout(1000)

            with page.expect_navigation():
                page.click('text=Consulta')

            print(f"➡️ Navegou para {page.url}")
            page.wait_for_selector("div.table-responsive > table", timeout=90000)

            tabelas = page.query_selector_all("div.table-responsive > table")

            if len(tabelas) < 3:
                print(f"❌ Menos de 3 tabelas para o pedido {valor} da filial {filial_numero}")
                continue

            print(f"✅ {len(tabelas)} tabelas encontradas para pedido {valor}")

            workbook = openpyxl.Workbook()
            sheet_pedido = workbook.active
            sheet_pedido.title = f"Pedido {filial_numero} - DSM {valor}"

            for t_idx, tabela in enumerate(tabelas):
                salvar_tabela(sheet_pedido, tabela, t_idx)
                sheet_pedido.append([])

            nome_arquivo = f"{filial_numero}_DSM{valor}_{obter_data_formatada()}.xlsx"
            caminho_arquivo = os.path.join(PASTA_RELATORIOS, nome_arquivo)

            workbook.save(caminho_arquivo)
            print(f"✅ Relatório salvo como {caminho_arquivo}")
            relatorios_filial.append(caminho_arquivo)

        return relatorios_filial if relatorios_filial else None

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
                    nome_coluna = f"Coluna {col + 1}"
            else:
                if nome_coluna.lower().startswith("peça") and col in [0, 1]:
                    nome_coluna = "Peça"

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
    msg['To'] = ", ".join(EMAIL_DESTINATARIO)
    msg['Subject'] = f"Relatórios - {obter_data_formatada()}"

    corpo = MIMEText("Segue em anexo os relatórios gerados automaticamente do dia de hoje.", 'plain')
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
        hoje = datetime.today()
        segunda_feira = hoje.weekday() == 0

        print("📊 Etapa 1: Gerando relatórios DSM 0...")
        for filial in FILIAIS:
            arquivos = gerar_relatorio(filial, context, dsm_valores=[0])
            if arquivos:
                arquivos_gerados.extend(arquivos)

        if segunda_feira:
            print("📊 Etapa 2: Segunda-feira detectada. Gerando relatórios DSM 1...")
            for filial in FILIAIS:
                arquivos = gerar_relatorio(filial, context, dsm_valores=[1])
                if arquivos:
                    arquivos_gerados.extend(arquivos)
        else:
            print("📅 Hoje não é segunda-feira. Pulando relatórios DSM 1.")

        browser.close()

        if arquivos_gerados:
            enviar_email(arquivos_gerados)
        else:
            print("⚠️ Nenhum relatório foi gerado para enviar.")

