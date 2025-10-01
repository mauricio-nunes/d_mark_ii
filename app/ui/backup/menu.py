from colorama import Fore, Style
from ..widgets import header, pause
from ...core.paths import BACKUP_DIR
from ...services.backup_service import list_backups, make_backup, restore_from

def _input(t): 
    return input(Fore.WHITE + t + Style.RESET_ALL)

def tela_backup():
    header("Backup do Banco")
    try:
        dst = make_backup()
        print(f"Backup criado: {dst}")
    except Exception as e:
        print(f"Erro no backup: {e}")
    pause()

def tela_restore():
    header("Restore do Banco", {"Diretório": str(BACKUP_DIR)})
    bks = list_backups()
    if not bks:
        print("Nenhum backup encontrado."); pause(); return
    print("Backups (mais recentes primeiro):")
    for i, p in enumerate(bks, start=1):
        print(f" {i:>2}. {p.name}")
    ch = _input("Número do backup para restaurar (ou ENTER p/ cancelar): ").strip()
    if not ch: return
    try:
        idx = int(ch)-1
        sel = bks[idx]
    except Exception:
        print("Opção inválida."); pause(); return

    print(f"\nATENÇÃO: isso vai sobrescrever o banco atual por {sel.name}!")
    conf = _input("Digite 'RESTAURAR' para confirmar: ").strip().upper()
    if conf != "RESTAURAR":
        print("Cancelado."); pause(); return

    try:
        restore_from(sel)
        print("Restore concluído com sucesso.")
    except Exception as e:
        print(f"Erro no restore: {e}")
    pause()

def backup_loop():
    keep = True
    while keep:
        header("Backup/Restore")
        print("1. Fazer Backup agora")
        print("2. Restaurar de um Backup")
        print("3. Voltar")
        ch = _input("> ").strip()
        match ch:
            case "1": tela_backup()
            case "2": tela_restore()
            case _: keep = False
