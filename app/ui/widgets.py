from rich.console import Console
from ..core.utils import clear_screen
from rich.table import Table
from rich import box


_console = Console()


def divider():
    return _console.print("-" * 70, style="blue")


def title(text: str):
    _console.print(f"{text}".upper(), style="cyan")


def confirm(prompt="Confirmar (S/N)? ") -> bool:
    ans = _console.input(f"[yellow]{prompt}[/yellow]").strip().lower()
    return ans in ("s", "sim", "y", "yes")


def pause(msg="Pressione ENTER para continuar..."):
    _console.input(f"\n[magenta]{msg}[/magenta]")
    clear_screen()


def render_table(
    title: str,
    total: int,
    total_pages: int,
    page: int,
    columns: list[str],
    rows: list[tuple],
):
    table = Table(
        title=title,
        box=box.ASCII,
        caption=f"Total de registros: {total} - Página {page}/{total_pages}",
        caption_justify="center",
        header_style="bold magenta",
        show_lines=False,
    )
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*map(str, row))
    _console.print(table)


def show_menu_options(options: list[str]):
    """
    Exibe opções numeradas a partir de 1.
    """
    for i, option in enumerate(options, start=1):
        if option.lower() == "sair" or option.lower() == "voltar":
            _console.print(f"0. {option}", style="white")
        else:
            _console.print(f"{i}. {option}", style="white")


def prompt_menu_choice(label="Selecione a opção: ") -> str:
    return _console.input(f"[yellow]{label}[/yellow]").strip()


def print_dict(meta: dict):
    """Imprime dicionário chave:valor formatado."""
    kv = [f"{k}: {v}" for k, v in meta.items() if v not in (None, "", "N/D")]
    if kv:
        _console.print("\n".join(kv), style="white")
