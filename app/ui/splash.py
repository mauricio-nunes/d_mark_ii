import os
import time
from colorama import Fore, Style, init as colorama_init
from pyfiglet import Figlet

colorama_init()

def _normalize_figlet_font(name: str) -> str:
	# aceita "ANSI Shadow", "ansi shadow", "ANSI_Shadow"...
	return (name or "ansi_shadow").strip().lower().replace(" ", "_")

def splash():
	env_font = os.getenv("DMARKI_FIGLET_FONT", "ansi_shadow")
	font = _normalize_figlet_font(env_font)
	try:
		f = Figlet(font=font)
	except Exception:
		f = Figlet(font="ansi_shadow")  # fallback seguro

	print(Fore.CYAN + f.renderText("D-MARK I") + Style.RESET_ALL)
	print(Fore.WHITE + "Inicializando", end="", flush=True)
	for _ in range(20):
		print(Fore.GREEN + ".", end="", flush=True)
		time.sleep(0.04)
	print(Style.RESET_ALL)
