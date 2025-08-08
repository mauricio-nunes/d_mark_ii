import os
import re
from dotenv import load_dotenv
from .decimal_ctx import money, qty, D

load_dotenv()

def normalize_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj or "")

def ensure_dirs():
    for d in ("./data", "./backup", "./export", "./imports"):
        os.makedirs(d, exist_ok=True)

def half_up_money_str(x) -> str:
    return f"{money(x):f}"

def half_up_qty_str(x) -> str:
    return f"{qty(x):f}"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")
