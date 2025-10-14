from .widgets import title, divider, pause, show_menu_options, prompt_menu_choice
from .forms import rich_label_error
from .manutencao_cadastros.menu import manutencao_loop
from .importacao.menu import importacao_loop
from .balanco.menu import balanco_menu
from .backup.menu import backup_loop
from ..core.utils import clear_screen

MAIN_ITEMS = [
    "Importação",
    "Database - Backup/Restore",
    "Manutenção de Cadastros",
    "Balanços",
    "Sair",
]

def handle_main_choice(choice: str) -> bool:
    """
    Retorna True para continuar no app, False para sair.
    """
    match choice.lower():
        case "1":
            importacao_loop()
        case "2":
            backup_loop()
        case "3":
            manutencao_loop()
        case "4":
            balanco_menu()
        case "0" | "q" | "sair" | "exit":
            return False
        case _:
            rich_label_error("Opção inválida.")
            pause()
    return True


def main_loop():

    keep = True
    while keep:
        clear_screen()
        divider()
        title("Menu Principal")
        divider()
        show_menu_options(MAIN_ITEMS)
        divider()
        choice = prompt_menu_choice()
        keep = handle_main_choice(choice)
