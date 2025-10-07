from colorama import Fore, Style
from .widgets import title, divider, pause
from .prompts import prompt_menu_choice
from ..core.utils import clear_screen

from .importacao.menu import importacao_loop
from .backup.menu import backup_loop


MAIN_ITEMS = [
    "Importação",
    "Database - Backup/Restore",
    "Manutenção de Cadastros",
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
            importacao_loop()
            pause()
        case "2":
            backup_loop()
            pause()
        case "3":
            from .empresas.menu import manutencao_cadastros_menu
            manutencao_cadastros_menu()
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
