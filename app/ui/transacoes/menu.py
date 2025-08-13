from colorama import Fore, Style
from ..widgets import title, divider, pause
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from .transacoes import tela_transacoes
from .proventos import tela_proventos
from .transferencia import tela_transferencia

ITEMS = [
    "Lançar/Editar Transação",
    "Lançar/Editar Provento",
    "Transferência entre Carteiras",
    "Voltar",
]

def show_menu():
    title("Transações & Proventos")
    for i, it in enumerate(ITEMS, start=1):
        print(Fore.WHITE + f"{i}. {it}" + Style.RESET_ALL)
    divider()

def transacoes_loop():
    keep = True
    while keep:
        clear_screen(); show_menu()
        ch = prompt_menu_choice().strip().lower()
        match ch:
            case "1": tela_transacoes()
            case "2": tela_proventos()
            case "3": tela_transferencia()
            case "4" | "q" | "voltar": keep = False
            case _: print("Opção inválida."); pause()
