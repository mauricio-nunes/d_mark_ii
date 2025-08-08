from colorama import Fore, Style
from ..widgets import title, divider, pause
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from .corretoras import tela_corretoras
from .carteiras import tela_carteiras
from .empresas import tela_empresas
from .ativos import tela_ativos

ITEMS = [
    "Corretoras",
    "Carteiras",
    "Empresas",
    "Ativos",
    "Voltar"
]

def show_cadastros_menu():
    title("Cadastros")
    for i, item in enumerate(ITEMS, start=1):
        print(Fore.WHITE + f"{i}. {item}" + Style.RESET_ALL)
    divider()

def handle_cadastros_choice(choice: str) -> bool:
    match choice:
        case "1": tela_corretoras()
        case "2": tela_carteiras()
        case "3": tela_empresas()
        case "4": tela_ativos()
        case "5" | "q" | "voltar": return False
        case _: print("Opção inválida."); pause()
    return True

def cadastros_loop():
    keep = True
    while keep:
        clear_screen()
        show_cadastros_menu()
        choice = prompt_menu_choice()
        keep = handle_cadastros_choice(choice)
