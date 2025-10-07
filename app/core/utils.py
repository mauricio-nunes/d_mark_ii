import os
import re
from dotenv import load_dotenv
from .decimal_ctx import money, qty, D
from datetime import datetime ,timezone
import unicodedata

class ValidationError(Exception): ...

load_dotenv()

def parse_url(url_str: str) -> str:
	#ajustar se iniciar com / remover a barra do inicio
	if url_str.startswith('/'):
		url_str = url_str[1:]
		
	if url_str.startswith('www:'):
		url_str = url_str.replace('www:', 'www.')
	
	if url_str.startswith('www.https://'):
		url_str = url_str.replace('www.https://', 'https://')
	
	if url_str.startswith('https:/') and not url_str.startswith('https://'):
		url_str = url_str.replace('https:/', 'https://')

	# se terminar com / remover a barra do final
	if url_str.endswith('/'):
		url_str = url_str[:-1]

		
	first_part = url_str.split(' ')
	if len(first_part) > 1:
		url_str = first_part[0]

	# Remover acentos e cedilha
	try:
		url_str = unicodedata.normalize('NFKD', url_str)
		url_str = ''.join([c for c in url_str if not unicodedata.combining(c)])
		url_str = url_str.replace('ç', 'c').replace('Ç', 'C')
	except:
		pass
	
	return url_str.strip()
	

def validate_url(url_str: str) -> bool:
	"""Valida se string é uma URL válida (com ou sem http/https). Remove acentos e cedilha antes de validar."""
	if not url_str or str(url_str).strip() == '':
		return True  # URL vazia é válida (campo opcional)
	
	url_str = str(url_str).strip()
	
	# Regex para validar URL com ou sem http/https
	url_pattern = re.compile(
		r'^(https?://)?'  # http:// ou https:// (opcional)
		r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63}\.?|'  # domínio
		r'localhost|'  # localhost
		r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
		r'(?::\d+)?'  # porta opcional
		r'(?:/?|[/?]\S+)?$', re.IGNORECASE)
	
	return bool(url_pattern.match(url_str))

def get_utc_timestamp() -> str:
	"""Retorna timestamp atual em UTC no formato ISO com Z."""
	return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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

def parse_int(value_str: str) -> int:
	"""Converte string para inteiro. Retorna None se vazio/inválido."""
	if not value_str or str(value_str).strip() == '':
		return None
	
	try:
		return int(str(value_str).strip())
	except:
		return None



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
