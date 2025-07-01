from playwright.sync_api import sync_playwright, TimeoutError

def salvar_sessao():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://lpcnet.slapl.prod.aws.scania.com/login")

        print("⚠️ Faça login manualmente e pressione ENTER para continuar.")
        input()

        context.storage_state(path="estado_autenticado_LPCNET.json")
        print("✅ Sessão salva em 'estado_autenticado_LPCNET.json'.")
        browser.close()

def verificar_autenticacao():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="estado_autenticado_LPCNET.json")
        page = context.new_page()

        page.goto("https://lpcnet.slapl.prod.aws.scania.com")

        if "login" in page.url.lower():
            print("⚠️ Sessão expirada, tentando login automático...")

            try:
                seletor = 'button.btn-primary:has-text("Login")'
                page.wait_for_selector(seletor, timeout=10000)
                page.click(seletor, force=True)
                print("✅ Clique no botão Login realizado.")

                page.wait_for_timeout(9000)

                if "login" not in page.url.lower():
                    context.storage_state(path="estado_autenticado_LPCNET.json")
                    print("✅ Sessão revalidada e salva novamente.")
                else:
                    print("❌ Login não efetuado, verifique o site ou credenciais.")

            except TimeoutError:
                print("❌ Botão Login não encontrado. Verifique o seletor ou a página.")

        else:
            print("✅ Sessão ativa, nada a fazer.")

        browser.close()

if __name__ == "__main__":
    salvar_sessao()
    verificar_autenticacao()
