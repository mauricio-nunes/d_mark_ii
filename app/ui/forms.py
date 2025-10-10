from typing import List
from rich.console import Console
from getpass import getpass
from rich.prompt import Prompt

_console = Console()


def rich_input(prompt: str) -> str:
    """Input com prompt colorido."""
    colored_prompt = f"[bold white]{prompt}[/bold white] "
    return _console.input(colored_prompt)


def rich_label_error(text: str) -> str:
    """Rótulo de erro em vermelho."""
    return _console.print(f"[bold red]{text}[/]")


def rich_getpass(prompt: str) -> str:
    """Input de senha com prompt colorido."""
    return getpass(prompt)


def rich_label_success(text: str) -> str:
    """Rótulo de sucesso em verde."""
    return _console.print(f"[green]{text}[/green]")


def rich_label_warning(text: str) -> str:
    """Rótulo de aviso em amarelo."""
    return _console.print(f"[bold yellow]{text}[/]")


def rich_label_info(text: str) -> str:
    """Rótulo de informação em azul."""
    return _console.print(f"[blue]{text}[/blue]")


def rich_label(text: str) -> str:
    """Rótulo padrão em branco."""
    return _console.print(text)


def rich_edit_input(prompt: str, default: str = None, choices: List[str] = None) -> str:
    """Input com valor padrão e prompt colorido."""
    resp = Prompt.ask(
        f"[bold white]{prompt}[/bold white]", default=default, choices=choices
    )
    return resp
