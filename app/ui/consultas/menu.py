from colorama import Fore, Style
from ..widgets import title, divider, pause
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from .posicao import tela_posicao
from .extrato import tela_extrato
from .proventos import tela_proventos
from .historico import tela_historico
from .pm_detalhado import tela_pm_detalhado

ITEMS = [
    "Posição por Carteira",
    "Extrato de Transações",
    "Proventos por Período",
    "Histórico Mensal",
    "PM detalhado por Ativo",
    "Voltar"
]

def consultas_loop():
    keep = True
    while keep:
        clear_screen(); title("Consultas")
        for i, it in enumerate(ITEMS, start=1): print(Fore.WHITE + f"{i}. {it}" + Style.RESET_ALL)
        divider()
        ch = prompt_menu_choice("Selecione: ").strip().lower()
        match ch:
            case "1": tela_posicao()
            case "2": tela_extrato()
            case "3": tela_proventos()
            case "4": tela_historico()
            case "5": tela_pm_detalhado()
            case "6" | "q" | "voltar": keep = False
            case _: print("Opção inválida."); pause()
