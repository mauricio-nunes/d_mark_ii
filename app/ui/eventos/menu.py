from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from .tela_eventos import tela_eventos
from .tela_mapping import tela_mapping
from .tela_preview import tela_preview

ITEMS = ["Incluir/Editar Eventos", "Ticker Mapping", "Revisar/Aplicação (prévia)", "Voltar"]

def show_menu():
    title("Eventos Corporativos")
    for i, it in enumerate(ITEMS, start=1):
        print(Fore.WHITE + f"{i}. {it}" + Style.RESET_ALL)
    divider()

def eventos_loop():
    keep = True
    while keep:
        clear_screen(); show_menu()
        ch = prompt_menu_choice().strip().lower()
        match ch:
            case "1": tela_eventos()
            case "2": tela_mapping()
            case "3": tela_preview()
            case "4" | "q" | "voltar": keep = False
            case _: print("Opção inválida."); pause()
