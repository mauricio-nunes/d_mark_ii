"""
Menu Processamento - Funcionalidades de processamento de dados
"""
from colorama import Fore, Style
from ..widgets import title, divider, pause
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...core.formatters import paint_header
from .processar_itrs import processar_itrs_flow

def _input(t):
    return input(Fore.WHITE + t + Style.RESET_ALL)


    
    


def _input(t):
    return input(Fore.WHITE + t + Style.RESET_ALL)

#* MENU PROCESSAMENTO
def processamento_loop():
    while True:
        clear_screen()
        title("Processamento & Consolidação")
        print("1. Processar ITRs")
        print("9. Voltar")
        ch = _input("> ").strip()
        if ch in ("9", "voltar", "v"):
            break
        elif ch == "1":
            processar_itrs_flow()
            pause()
        else:
            print("Opção inválida.")
            pause()

