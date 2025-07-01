import schedule
import time
from salvar_sessao_LPCNET import salvar_sessao_com_login
from gerar_relatorio_LPCNET import executar_rotina  # importar a função completa
from Gerar_relatorio_1 import executar_rotina_1  # importar a função completa
from datetime import datetime


def executar_automacao():
    print(f"🚀 Iniciando automação em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("🔐 Autenticando e salvando sessão...")
    salvar_sessao_com_login()  # Login completo com 2FA
    print("📊 Gerando relatórios...")
    executar_rotina()          # chama a rotina que gera relatórios para todas as filiais
    print("✅ Automação concluída.\n")
    executar_rotina_1()          # chama a rotina que gera relatórios para todas as filiais
    print("✅ Automação de ontem concluída .\n")

# Agendamento para rodar todos os dias às 08:30 (ajuste o horário conforme precisar)
schedule.every().day.at("16:32").do(executar_automacao)

print("⏰ Agendamento configurado para rodar todos os dias às 08:30.")
print("🌀 Mantendo o programa em execução...")

while True:
    schedule.run_pending()
    time.sleep(60)
