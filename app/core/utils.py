import os
import re
from dotenv import load_dotenv
from .decimal_ctx import money, qty, D

load_dotenv()

def normalize_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj or "")

def valid_cnpj(cnpj: str) -> bool:
    # Algoritmo de validação de CNPJ (DV)
    c = normalize_cnpj(cnpj)
    if len(c) != 14 or c == c[0]*14: return False
    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    pesos2 = [6] + pesos1
    soma = sum(int(d)*p for d,p in zip(c[:12], pesos1))
    dv1 = (soma % 11); dv1 = 0 if dv1 < 2 else 11 - dv1
    soma = sum(int(d)*p for d,p in zip(c[:13], pesos2))
    dv2 = (soma % 11); dv2 = 0 if dv2 < 2 else 11 - dv2
    return c[-2:] == f"{dv1}{dv2}"

def ensure_dirs():
    for d in ("./data", "./backup", "./export", "./imports"):
        os.makedirs(d, exist_ok=True)

def half_up_money_str(x) -> str:
    return f"{money(x):f}"

def half_up_qty_str(x) -> str:
    return f"{qty(x):f}"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")
