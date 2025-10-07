from colorama import Fore, Style
from .widgets import title, divider, pause
from .prompts import prompt_menu_choice
from ..core.utils import clear_screen

from .importacao.menu import importacao_loop
from .backup.menu import backup_loop


def iniciar_terminal_interativo():
	"""Inicia o CLI interativo com Typer."""
	from .cli.interactive_shell import interactive_shell
	
	clear_screen()
	title("Terminal Interativo")
	
	try:
		interactive_shell.run()
	except KeyboardInterrupt:
		print("\nTerminal interativo interrompido.")
	except Exception as e:
		print(f"Erro no terminal interativo: {e}")


MAIN_ITEMS = [
    "Importação",
    "Terminal Interativo",
    "Database - Backup/Restore",
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
            iniciar_terminal_interativo()
            pause()
        case "3":
            backup_loop()
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
