from ..widgets import (
    pause,
    divider,
    title,
    show_menu_options,
    prompt_menu_choice,
    print_dict,
)
from ..forms import (
    rich_label_error,
    rich_label_warning,
    rich_label_info,
    rich_label,
    rich_label_success,
)
from ...core.paths import BACKUP_DIR
from ...services.backup_service import list_backups, make_backup, restore_from
from ...core.utils import clear_screen


MENU_ITENS = ["Fazer Backup agora", "Restaurar de um Backup", "Voltar"]


def tela_backup():
    clear_screen()
    divider()
    title("Backup do Banco")
    divider()
    try:
        dst = make_backup()
        print_dict({"Backup criado": str(dst)})
    except Exception as e:
        rich_label_error(f"Erro no backup: {e}")
    pause()


def tela_restore():
    clear_screen()
    divider()
    title("Restore do Banco")
    divider()
    print_dict({"Diretório de Backups": str(BACKUP_DIR)})
    divider()
    bks = list_backups()

    if not bks:
        rich_label_warning("Nenhum backup encontrado.")
        pause()
        return
    rich_label_info("Backups (mais recentes primeiro):")
    for i, p in enumerate(bks, start=1):
        rich_label(f" {i:>2}. {p.name}")
    ch = prompt_menu_choice(
        "\nNúmero do backup para restaurar (ou ENTER p/ cancelar): "
    ).strip()
    if not ch:
        return
    try:
        idx = int(ch) - 1
        sel = bks[idx]
    except Exception:
        rich_label_error("Opção inválida.")
        pause()
        return

    rich_label_warning(
        f"\nATENÇÃO: isso vai sobrescrever o banco atual por {sel.name}!"
    )
    conf = prompt_menu_choice("Digite 'RESTAURAR' para confirmar: ").strip().upper()
    if conf != "RESTAURAR":
        rich_label_info("Cancelado.")
        pause()
        return

    try:
        restore_from(sel)
        rich_label_success("Restore concluído com sucesso.")
    except Exception as e:
        rich_label_error(f"Erro no restore: {e}")
    pause()


def handle_main_choice(choice: str) -> bool:
    match choice.lower():
        case "1":
            tela_backup()
        case "2":
            tela_restore()
        case "0" | "q" | "sair" | "exit":
            return False
        case _:
            rich_label_error("Opção inválida.")
            pause()
    return True


def backup_loop():

    keep = True
    while keep:
        clear_screen()
        divider()
        title("Backup/Restore")
        divider()
        show_menu_options(MENU_ITENS)
        divider()
        choice = prompt_menu_choice()
        keep = handle_main_choice(choice)
