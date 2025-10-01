import shutil
from datetime import datetime
from pathlib import Path
from typing import List
from ..core.paths import BACKUP_DIR, DEFAULT_DB_PATH, ensure_dirs


CFG_DB_PATH = "db_path"  # opcional, se quiser armazenar caminho custom

def _db_path() -> Path:
    # usa valor do config, se existir; senão, DEFAULT_DB_PATH
    return DEFAULT_DB_PATH

def list_backups() -> List[Path]:
    ensure_dirs()
    return sorted(BACKUP_DIR.glob("dmarki_*.db"), reverse=True)

def make_backup() -> Path:
    ensure_dirs()
    src = _db_path()
    if not src.exists():
        raise FileNotFoundError(f"Banco não encontrado: {src}")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"dmarki_{stamp}.db"
    shutil.copy2(src, dst)
    return dst

def restore_from(path: Path) -> None:
    ensure_dirs()
    if not path.exists():
        raise FileNotFoundError(f"Backup não encontrado: {path}")
    dst = _db_path()
    # cópia "por cima"
    shutil.copy2(path, dst)
