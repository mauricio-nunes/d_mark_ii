from colorama import Fore, Style
from ..core.utils import clear_screen

def divider():
    print(Fore.BLUE + "-" * 70 + Style.RESET_ALL)

def title(text: str):
    divider()
    print(Fore.CYAN + f"{text}".upper() + Style.RESET_ALL)
    divider()

def confirm(prompt="Confirmar (S/N)? ")->bool:
    ans = input(Fore.YELLOW + prompt + Style.RESET_ALL).strip().lower()
    return ans in ("s", "sim", "y", "yes")

def pause(msg="Pressione ENTER para continuar..."):
    input(Fore.MAGENTA + msg + Style.RESET_ALL)
    clear_screen()  # <- aqui a mágica
