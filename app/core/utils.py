import os
import re
from dotenv import load_dotenv
from .decimal_ctx import money, qty, D
from datetime import datetime

class ValidationError(Exception): ...

load_dotenv()

def normalize_cnpj(cnpj: str) -> str:
    cnpj_num = re.sub(r"\D", "", cnpj or "")
    return cnpj_num.zfill(14) 


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
    
def normalize_b3_decimal(value) -> str:
        """Normaliza valores decimais da B3 (vírgula para ponto, trata '-' como zero)"""
        if not value or value == '-' or str(value).strip() == '':
            return '0'
        
        str_value = str(value).strip()
        
        # Remove pontos de milhares e substitui vírgula decimal por ponto
        # Ex: "1.500,25" -> "1500.25"
        if ',' in str_value and '.' in str_value:
            # Formato brasileiro: pontos para milhares, vírgula para decimal
            str_value = str_value.replace('.', '').replace(',', '.')
        elif ',' in str_value:
            # Apenas vírgula decimal
            str_value = str_value.replace(',', '.')
        
        try:
            decimal_value = D(str_value)
            return str(decimal_value)
        except:
            return '0'

def parse_date(date_str: str) -> str:
    """Converte data de dd/mm/aaaa para YYYY-MM-DD"""
    if not date_str:
        return ""
    try:
        # Tentar formato dd/mm/aaaa primeiro
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Se já estiver em formato ISO, retornar como está
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str
            
        # Tentar parse com datetime
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        raise ValidationError(f"Data inválida: {date_str}. Use formato dd/mm/aaaa")
