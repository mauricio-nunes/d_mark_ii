from colorama import Fore, Style
from .widgets import title, divider, pause
from .prompts import prompt_menu_choice
from ..core.utils import clear_screen
from .cadastros.menu import cadastros_loop 
from .transacoes.menu import transacoes_loop

MAIN_ITEMS = [
    "Cadastros",
    "Transações & Proventos",
    "Eventos Corporativos",
    "Importação",
    "Consultas",
    "Backup/Restore",
    "Configurações",
    "Sair"
]

def show_main_menu():
    title("Menu Principal")
    for i, item in enumerate(MAIN_ITEMS, start=1):
        num = 9 if item == "Sair" else i
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
            print("▶ Eventos Corporativos (em construção).")
            pause()
        case "4":
            print("▶ Importação (em construção).")
            pause()
        case "5":
            print("▶ Consultas (em construção).")
            pause()
        case "6":
            print("▶ Backup/Restore (em construção).")
            pause()
        case "7":
            print("▶ Configurações (em construção).")
            pause()
        case "9" | "q" | "sair" | "exit":
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
