from ...core.utils import clear_screen
from ..forms import rich_label_error
from ..widgets import title, divider, pause, show_menu_options, prompt_menu_choice
from app.ui.manutencao_cadastros.empresa_ui import empresa_menu

MENU_ITENS = ["Empresas", "Voltar"]


def handle_menu_choice(choice: str) -> bool:
    match choice.lower():
        case "1":
            empresa_menu()
        case "0" | "q" | "voltar" | "sair" | "exit":
            return False
        case _:
            rich_label_error("Opção inválida.")
            pause()
    return True


def manutencao_loop():
    keep = True
    while keep:
        clear_screen()
        divider()
        title("Manutenção de Cadastros")
        divider()
        show_menu_options(MENU_ITENS)
        divider()
        choice = prompt_menu_choice().strip()
        keep = handle_menu_choice(choice)
