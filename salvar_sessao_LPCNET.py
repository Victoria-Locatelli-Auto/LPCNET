from playwright.sync_api import sync_playwright, TimeoutError

# CONFIGURAÇÕES
URL_LOGIN_SCANIA = "https://lpcnet.slapl.prod.aws.scania.com/login"
STORAGE_PATH = "estado_autenticado_LPCNET.json"
EMAIL_SCANIA = "nnap08@scaniaweb.com"
SENHA_SCANIA = "2714@Mcmalemanha"
EMAIL_GOOGLE = "natalia.sobral@mcmtocantins.com"
SENHA_GOOGLE = "2714@Mcm"

def login_conta_google(context, email, senha):
    print("\n🔐 Iniciando login na Conta Google...")
    page = context.new_page()
    page.goto("https://accounts.google.com/", timeout=60000)

    page.wait_for_selector('input[type="email"]', timeout=15000)
    page.fill('input[type="email"]', email)
    page.click('span.VfPpkd-vQzf8d:has-text("Avançar")', timeout=30000)

    page.wait_for_selector('input[type="password"]', timeout=15000)
    page.fill('input[type="password"]', senha)
    page.click('span.VfPpkd-vQzf8d:has-text("Avançar")', timeout=30000)

    try:
        page.wait_for_url("https://myaccount.google.com/*", timeout=15000)
        print("✅ Login Google bem-sucedido!")
    except TimeoutError:
        print("⚠️ Login Google pode estar incompleto. Verifique se há confirmação extra.")

    page.close()

def salvar_sessao_com_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        # Login Google
        login_conta_google(context, EMAIL_GOOGLE, SENHA_GOOGLE)

        page = context.new_page()
        print("\n🌐 Acessando página de login Scania...")
        page.goto(URL_LOGIN_SCANIA, timeout=60000)
        page.wait_for_timeout(2000)

        try:
            print("🔵 Clicando no botão de Login...")
            page.click('button:has-text("Login")', timeout=10000)

            page.wait_for_selector('input[type="email"]', timeout=10000)
            print("✍️ Preenchendo e-mail Scania...")
            page.fill('input[type="email"]', EMAIL_SCANIA)
            page.click('#idSIButton9', timeout=10000)

            print("🔐 Aguardando campo de senha...")
            page.wait_for_selector('input[type="password"]', timeout=15000)
            page.fill('input[type="password"]', SENHA_SCANIA)
            page.click('#idSIButton9', timeout=10000)

            print("📱 Selecionando opção de autenticação via SMS...")
            page.wait_for_selector('div.table-row >> text=Texto', timeout=20000)
            page.click('div.table-row >> text=Texto')

            print("⌛ Aguardando campo de código 2FA...")
            campo_codigo = page.wait_for_selector('input[type="tel"], input[name="otc"]', timeout=60000)

            # Entrada manual do código 2FA
            codigo_2fa = input("📲 Insira manualmente o código 2FA recebido por SMS: ").strip()
            print("✍️ Preenchendo campo de código...")
            campo_codigo.fill(codigo_2fa)

            botao_confirmar = page.query_selector('button:has-text("Verificar"), button:has-text("Confirmar"), #idSIButton9')
            if botao_confirmar:
                botao_confirmar.click()

            print("✅ Aguardando botão 'Verificar' final após autenticação...")
            page.wait_for_selector('input[type="submit"][value="Verificar"]', timeout=20000)
            page.click('input[type="submit"][value="Verificar"]')

            print("✅ Aguardando tela principal...")
            page.wait_for_selector('text=LOGÍSTICA', timeout=60000)

            context.storage_state(path=STORAGE_PATH)
            print(f"💾 Sessão salva com sucesso em '{STORAGE_PATH}'")

        except TimeoutError as e:
            print("❌ Timeout durante o login Scania.", str(e))
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    salvar_sessao_com_login()
