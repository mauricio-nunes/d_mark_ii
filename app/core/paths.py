from pathlib import Path

# Diretórios padrão
BASE_DIR = Path(".").resolve()
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backup"

# Caminho padrão do DB (pode ser sobrescrito via config_repo se existir)
DEFAULT_DB_PATH = DATA_DIR / "dmarki.db"

def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
