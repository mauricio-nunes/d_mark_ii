from getpass import getpass
from colorama import Fore, Style

def prompt_username() -> str:
    return input(Fore.WHITE + "Usuário: " + Style.RESET_ALL).strip()

def prompt_password(label="Senha: ") -> str:
    return getpass(Fore.WHITE + label + Style.RESET_ALL)

def prompt_menu_choice(label="Selecione a opção: ") -> str:
    return input(Fore.YELLOW + label + Style.RESET_ALL).strip()
