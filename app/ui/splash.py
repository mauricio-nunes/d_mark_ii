import os
import time
from rich.console import Console
from pyfiglet import Figlet

console = Console()


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

    title_text = f.renderText("D-MARK I")
    console.print(title_text, style="cyan")

    console.print("Inicializando", style="white", end="")
    for _ in range(30):
        console.print(".", style="green", end="")
        time.sleep(0.04)
    console.print()  # quebra de linha final
