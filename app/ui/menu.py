from colorama import Fore, Style
from .widgets import title, divider, pause
from .prompts import prompt_menu_choice
from ..core.utils import clear_screen
from .cadastros.menu import cadastros_loop 
from .transacoes.menu import transacoes_loop
from .eventos.menu import eventos_loop
from .importacao.menu import importacao_loop
from .consultas.menu import consultas_loop
from .backup.menu import backup_loop      
from .config.menu import config_loop   
from .processamento.menu import processamento_loop

MAIN_ITEMS = [
    "Cadastros",
    "Transações & Proventos",
    "Eventos Corporativos",
    "Importação",
    "Consultas",
    "Backup/Restore",
    "Configurações",
    "Consolidação & Processamento",
    "Sair"
]

def show_main_menu():
    title("Menu Principal")
    for i, item in enumerate(MAIN_ITEMS, start=1):
        if item == "Sair":
            num = 0
        else:
            num = i
        print(Fore.WHITE + f"{num}. {item}" + Style.RESET_ALL)
    divider()

def handle_main_choice(choice: str) -> bool:
    """
    Retorna True para continuar no app, False para sair.
    """
    match choice.lower():
        case "1":
            cadastros_loop()
        case "2":
            transacoes_loop()
            pause()
        case "3":
            eventos_loop()
            pause()
        case "4":
            importacao_loop()
            pause()
        case "5":
            consultas_loop()
            pause()
        case "6":
            backup_loop()
            pause()
        case "7":
            config_loop()
            pause()
        case "8":
            processamento_loop()
            pause()
        case "0" | "q" | "sair" | "exit":
            return False
        case _:
            print("Opção inválida.")
            pause()
    return True

def main_loop():
    keep = True
    while keep:
        clear_screen()
        show_main_menu()
        choice = prompt_menu_choice()
        keep = handle_main_choice(choice)
