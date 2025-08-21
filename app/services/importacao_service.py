from typing import Dict, List, Tuple
import os
import csv
import zipfile
import requests
import tempfile
import hashlib
import re
import glob
from datetime import datetime
from tqdm import tqdm
from ..core.xlsx import read_xlsx_rows, list_sheets
from ..core.decimal_ctx import D, money, qty
from ..core.daterules import parse_year_month_from_sheet, last_business_day
from ..core.utils import normalize_cnpj
from ..db.repositories import ativos_repo, proventos_repo, fechamentos_repo, empresas_repo
from ..db.repositories import movimentacao_repo
from ..db.repositories import users_repo  # só para garantir conexão se precisar

class ValidationError(Exception): ...

# chaves do config
CFG_PROV_MAP = "xlsx_map_proventos"     # json str
CFG_FECH_MAP = "xlsx_map_fechamentos"   # json str

# --------- helpers de mapeamento ---------

def _normalize(s: str | None) -> str:
    return (s or "").strip()

def _get_or_create_ativo_by_ticker_str(ticker_str: str) -> int | None:
    a = ativos_repo.get_by_ticker(ticker_str)
    if a: return a["id"]
    # cria on-the-fly com nome=ticker, classe=Acao por padrão
    return ativos_repo.create(ticker_str, ticker_str, "Acao", None)

# --------- PROVENTOS ---------

def preview_proventos(path: str, sheet: str, colmap: dict) -> List[dict]:
    rows = read_xlsx_rows(path, sheet)
    out = []
    for r in rows:
        try:
            ticker = _normalize(str(r.get(colmap["ticker"])))
            tipo   = _normalize(str(r.get(colmap["tipo"]))).upper()
            data   = _normalize(str(r.get(colmap["data_pagamento"])))
            desc   = _normalize(str(r.get(colmap.get("descricao",""))))
            qtd    = _normalize(str(r.get(colmap.get("quantidade","") ))) or None
            pu     = _normalize(str(r.get(colmap.get("preco_unitario","") ))) or None
            valor  = _normalize(str(r.get(colmap.get("valor_total","") ))) or None
            out.append({
                "ticker": ticker, "tipo_evento": tipo, "data_pagamento": data,
                "descricao": desc, "quantidade": qtd, "preco_unitario": pu, "valor_total": valor
            })
        except Exception:
            continue
    return out[:50]

def importar_proventos(path: str, sheet: str, colmap: dict) -> Tuple[int,int]:
    rows = read_xlsx_rows(path, sheet)
    ok = 0; skip = 0
    for r in rows:
        ticker = _normalize(str(r.get(colmap["ticker"])))
        if not ticker: skip += 1; continue
        tipo   = _normalize(str(r.get(colmap["tipo"]))).upper()
        data   = _normalize(str(r.get(colmap["data_pagamento"])))
        desc   = _normalize(str(r.get(colmap.get("descricao",""))))
        qtd    = _normalize(str(r.get(colmap.get("quantidade","") ))) or None
        pu     = _normalize(str(r.get(colmap.get("preco_unitario","") ))) or None
        valor  = _normalize(str(r.get(colmap.get("valor_total","") ))) or None

        try:
            aid = _get_or_create_ativo_by_ticker_str(ticker)
            proventos_repo.create({
                "ticker": aid, "descricao": desc, "data_pagamento": data,
                "tipo_evento": tipo, "corretora_id": None,
                "quantidade": qtd, "preco_unitario": pu, "valor_total": valor,
                "observacoes": "import XLSX"
            })
            ok += 1
        except Exception:
            skip += 1
    return ok, skip

# --------- FECHAMENTOS MENSAIS ---------

def preview_fechamentos(path: str, sheet: str, colmap: dict) -> List[dict]:
    rows = read_xlsx_rows(path, sheet)
    # calcular data_ref a partir do nome da planilha
    ym = parse_year_month_from_sheet(sheet)
    data_ref = last_business_day(*ym) if ym else None
    out = []
    for r in rows:
        try:
            ticker = _normalize(str(r.get(colmap["ticker"])))
            preco  = _normalize(str(r.get(colmap["preco_fechamento"])))
            qtde   = _normalize(str(r.get(colmap.get("quantidade","")))) or None
            out.append({"ticker": ticker, "data_ref": data_ref, "preco_fechamento": preco, "quantidade": qtde})
        except Exception:
            continue
    return out[:50]

def importar_fechamentos(path: str, sheet: str, colmap: dict) -> Tuple[int,int]:
    rows = read_xlsx_rows(path, sheet)
    ym = parse_year_month_from_sheet(sheet)
    if not ym: raise ValidationError("Não consegui inferir AAAA-MM pelo nome da planilha. Renomeie a aba (ex.: 2024-07, 202407, Jul/2024).")
    data_ref = last_business_day(*ym)

    ok = 0; skip = 0
    for r in rows:
        ticker = _normalize(str(r.get(colmap["ticker"])))
        if not ticker: skip += 1; continue
        preco  = _normalize(str(r.get(colmap["preco_fechamento"])))
        qtde   = _normalize(str(r.get(colmap.get("quantidade","")))) or None
        try:
            aid = _get_or_create_ativo_by_ticker_str(ticker)
            fechamentos_repo.create(aid, data_ref, preco, qtde)
            ok += 1
        except Exception:
            skip += 1
    return ok, skip

# --------- CVM COMPANIES IMPORT ---------

def _parse_cvm_date(date_str: str) -> str | None:
    """Parse CVM date format to ISO date (YYYY-MM-DD) or return None if invalid."""
    if not date_str or date_str.strip() == "":
        return None
    
    try:
        # Try DD/MM/YYYY format first (common in Brazilian data)
        if "/" in date_str:
            day, month, year = date_str.strip().split("/")
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        # Try YYYY-MM-DD format
        elif "-" in date_str and len(date_str.split("-")[0]) == 4:
            return date_str.strip()
        else:
            return None
    except:
        return None

def download_cvm_file(year: int) -> str:
    """
    Download CVM file for the given year and return path to extracted CSV.
    Raises Exception if download or extraction fails.
    """
    url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{year}.zip"
    
    # Create temp directory for download
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"fca_cia_aberta_{year}.zip")
    csv_path = os.path.join(temp_dir, f"fca_cia_aberta_geral_{year}.csv")
    
    try:
        # Download file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        with open(zip_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Baixando") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        # Extract CSV from ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Look for the expected CSV file
            expected_csv = f"fca_cia_aberta_geral_{year}.csv"
            if expected_csv not in zip_ref.namelist():
                raise Exception(f"Arquivo {expected_csv} não encontrado no ZIP")
            
            zip_ref.extract(expected_csv, temp_dir)
        
        return csv_path
        
    except requests.RequestException as e:
        raise Exception(f"Erro ao baixar arquivo da CVM: {e}")
    except zipfile.BadZipFile:
        raise Exception("Arquivo ZIP corrompido")
    except Exception as e:
        raise Exception(f"Erro no processamento: {e}")

def import_cvm_companies(year: int | None = None) -> tuple[int, int, int]:
    """
    Import CVM companies for the given year (default: current year).
    Returns (inserted_count, updated_count, error_count).
    """
    if year is None:
        year = datetime.now().year
    
    if year < 2010:
        raise ValidationError("Ano deve ser maior ou igual a 2010")
    
    # Download and extract file
    csv_path = download_cvm_file(year)
    
    try:
        inserted, updated, errors = 0, 0, 0
        
        # Count total rows for progress bar
        with open(csv_path, 'r', encoding='latin1') as f:
            total_rows = sum(1 for _ in csv.DictReader(f, delimiter=';')) - 1  # Subtract header
        
        # Process CSV file
        with open(csv_path, 'r', encoding='latin1') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            with tqdm(total=total_rows, desc="Processando empresas", unit="empresas") as pbar:
                for row in reader:
                    try:
                        # Extract and normalize data
                        cnpj = normalize_cnpj(row.get("CNPJ_Companhia", ""))
                        if not cnpj:
                            errors += 1
                            pbar.update(1)
                            continue
                        
                        razao_social = row.get("Nome_Empresarial", "").strip()
                        if not razao_social:
                            errors += 1
                            pbar.update(1)
                            continue
                        
                        codigo_cvm = row.get("Codigo_CVM", "").strip()
                        data_constituicao = _parse_cvm_date(row.get("Data_Constituicao", ""))
                        setor_atividade = row.get("Setor_Atividade", "").strip() or None
                        situacao = row.get("Situacao_Registro_CVM", "").strip() or None
                        controle_acionario = row.get("Especie_Controle_Acionario", "").strip() or None
                        
                        # Set ativo based on situacao
                        ativo = 1 if situacao == "Ativo" else 0
                        
                        # Upsert company
                        empresa_id, was_inserted = empresas_repo.upsert_by_cnpj(
                            cnpj=cnpj,
                            razao_social=razao_social,
                            codigo_cvm=codigo_cvm,
                            data_constituicao=data_constituicao,
                            setor_atividade=setor_atividade,
                            situacao=situacao,
                            controle_acionario=controle_acionario,
                            tipo_empresa="CiaAberta",
                            ativo=ativo
                        )
                        
                        if was_inserted:
                            inserted += 1
                        else:
                            updated += 1
                            
                    except Exception as e:
                        errors += 1
                    
                    pbar.update(1)
        
        return inserted, updated, errors
        
    finally:
        # Cleanup temp files
        try:
            if os.path.exists(csv_path):
                os.remove(csv_path)
            if os.path.exists(os.path.dirname(csv_path)):
                os.rmdir(os.path.dirname(csv_path))
        except:
            pass  # Ignore cleanup errors

# --------- MOVIMENTAÇÃO B3 ---------

def _normalize_string(s: str) -> str:
	"""Normaliza string para minúsculas sem acentos"""
	if not s:
		return ""
	# Remove acentos básicos
	replacements = {
		'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
		'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
		'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
		'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
		'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
		'ç': 'c', 'ñ': 'n'
	}
	normalized = s.lower()
	for old, new in replacements.items():
		normalized = normalized.replace(old, new)
	return normalized.strip()

def _parse_date(date_str: str) -> str:
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

def _normalize_decimal(value_str: str) -> str:
	"""Normaliza valores decimais removendo separadores de milhares e convertendo vírgula para ponto"""
	if not value_str:
		return "0"
	
	# Remove espaços e caracteres extras
	clean = str(value_str).strip().replace(' ', '')
	
	# Se contém vírgula como decimal (padrão brasileiro)
	if ',' in clean:
		# Se tem ponto E vírgula, ponto é separador de milhares
		if '.' in clean and clean.rindex('.') < clean.rindex(','):
			clean = clean.replace('.', '')  # Remove separador de milhares
		clean = clean.replace(',', '.')  # Vírgula vira decimal
	
	# Remove separadores de milhares restantes (se houver mais de um ponto)
	parts = clean.split('.')
	if len(parts) > 2:
		# Mantém apenas o último ponto como decimal
		decimal_part = parts[-1]
		integer_part = ''.join(parts[:-1])
		clean = f"{integer_part}.{decimal_part}"
	
	return clean

def _parse_produto(produto_str: str) -> tuple[str, str, str]:
	"""
	Decompõe o campo Produto em código, código_negociacao e ativo_descricao
	Exemplo: "PETR4 - PETROBRAS PN N2" -> ("PETR4", "PETR4", "PETROBRAS PN N2")
	"""
	if not produto_str:
		return "", "", ""
	
	# Padrão: CODIGO - DESCRICAO ou CODIGO DESCRICAO
	parts = produto_str.split(' - ', 1)
	if len(parts) == 2:
		codigo = parts[0].strip()
		descricao = parts[1].strip()
		return codigo, codigo, descricao
	
	# Se não tem separador, pega primeira palavra como código
	words = produto_str.split()
	if words:
		codigo = words[0]
		descricao = produto_str
		return codigo, codigo, descricao
	
	return "", "", produto_str

def _calculate_hash(row_data: dict) -> str:
	"""Calcula SHA-256 da linha normalizada para idempotência"""
	# Criar string normalizada dos campos principais
	hash_string = f"{row_data['data']}|{row_data['movimentacao']}|{row_data['tipo_movimentacao']}|{row_data['codigo']}|{row_data['quantidade']}|{row_data['preco_unitario']}|{row_data.get('valor_total_operacao', '')}"
	return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()

def find_movimentacao_files(imports_dir: str = "imports") -> list[str]:
	"""Encontra arquivos de movimentação na pasta imports"""
	pattern = os.path.join(imports_dir, "movimentacao_*.xlsx")
	files = glob.glob(pattern)
	
	# Filtrar apenas arquivos com padrão válido
	valid_files = []
	for file in files:
		basename = os.path.basename(file)
		# Padrão: movimentacao_{mes}_{ano}.xlsx ou movimentacao_{ano}.xlsx
		if re.match(r'movimentacao_(\d{1,2}_)?\d{4}\.xlsx$', basename):
			valid_files.append(file)
	
	return sorted(valid_files)

def preview_movimentacao(path: str, sheet: str = None) -> List[dict]:
	"""Preview das primeiras linhas do arquivo de movimentação"""
	# Usar primeira aba se não especificada
	if not sheet:
		sheets = list_sheets(path)
		sheet = sheets[0] if sheets else None
	
	rows = read_xlsx_rows(path, sheet)
	
	# Mapear colunas esperadas (assumindo padrão B3)
	expected_columns = {
		"Data": "data",
		"Movimentação": "movimentacao", 
		"Produto": "produto",
		"Quantidade": "quantidade",
		"Preço unitário": "preco_unitario",
		"Valor da Operação": "valor_total_operacao"
	}
	
	preview_data = []
	for i, row in enumerate(rows[:10]):  # Apenas 10 primeiras linhas
		try:
			# Mapear campos
			mapped_row = {}
			for excel_col, field_name in expected_columns.items():
				value = row.get(excel_col, "")
				mapped_row[field_name] = value
			
			# Processar campos básicos para preview
			if mapped_row.get("data"):
				try:
					mapped_row["data"] = _parse_date(str(mapped_row["data"]))
				except:
					pass
			
			if mapped_row.get("produto"):
				codigo, codigo_neg, descricao = _parse_produto(str(mapped_row["produto"]))
				mapped_row["codigo"] = codigo
				mapped_row["ativo_descricao"] = descricao
			
			preview_data.append(mapped_row)
		except Exception:
			continue
	
	return preview_data

def importar_movimentacao(path: str, sheet: str = None) -> tuple[int, int, int, int]:
	"""
	Importa arquivo de movimentação da B3
	Returns (inseridas, atualizadas, ignoradas, erros)
	"""
	# Usar primeira aba se não especificada
	if not sheet:
		sheets = list_sheets(path)
		sheet = sheets[0] if sheets else None
		if not sheet:
			raise ValidationError("Arquivo não possui abas válidas")
	
	rows = read_xlsx_rows(path, sheet)
	
	# Mapear colunas esperadas
	expected_columns = {
		"Data": "data",
		"Movimentação": "movimentacao",
		"Produto": "produto", 
		"Quantidade": "quantidade",
		"Preço unitário": "preco_unitario",
		"Valor da Operação": "valor_total_operacao"
	}
	
	inseridas = 0
	atualizadas = 0
	ignoradas = 0
	erros = 0
	
	# Processa em transação única
	from ..db.connection import get_conn
	conn = get_conn()
	
	try:
		conn.execute("BEGIN TRANSACTION;")
		
		for row in rows:
			try:
				# Mapear campos do Excel
				data_raw = str(row.get("Data", "")).strip()
				movimentacao_raw = str(row.get("Movimentação", "")).strip()
				produto_raw = str(row.get("Produto", "")).strip()
				quantidade_raw = str(row.get("Quantidade", "")).strip()
				preco_raw = str(row.get("Preço unitário", "")).strip()
				valor_raw = str(row.get("Valor da Operação", "")).strip()
				
				# Ignorar linhas vazias
				if not data_raw or not movimentacao_raw or not produto_raw:
					ignoradas += 1
					continue
				
				# Transformar dados
				data = _parse_date(data_raw)
				movimentacao = _normalize_string(movimentacao_raw)
				
				# Determinar tipo de movimentação
				if "credito" in movimentacao or "entrada" in movimentacao:
					tipo_movimentacao = "credito"
				elif "debito" in movimentacao or "saida" in movimentacao:
					tipo_movimentacao = "debito"
				else:
					# Assumir crédito por padrão
					tipo_movimentacao = "credito"
				
				# Processar produto
				codigo, codigo_negociacao, ativo_descricao = _parse_produto(produto_raw)
				
				# Processar valores numéricos
				quantidade_decimal = _normalize_decimal(quantidade_raw)
				quantidade = str(abs(qty(quantidade_decimal)))  # Sempre positivo
				
				preco_unitario_decimal = _normalize_decimal(preco_raw)
				preco_unitario = str(money(preco_unitario_decimal).quantize(D("0.001")))  # 3 casas decimais
				
				# Valor total (pode ser NULL para subscrições)
				valor_total_operacao = None
				if valor_raw and valor_raw.lower() not in ("", "0", "null", "none"):
					valor_decimal = _normalize_decimal(valor_raw)
					valor_total = abs(money(valor_decimal))
					if valor_total > 0:
						valor_total_operacao = str(valor_total)
				
				# Preparar dados para inserção
				row_data = {
					"data": data,
					"movimentacao": movimentacao,
					"tipo_movimentacao": tipo_movimentacao,
					"codigo": codigo,
					"codigo_negociacao": codigo_negociacao if codigo_negociacao != codigo else None,
					"ativo_descricao": ativo_descricao,
					"quantidade": quantidade,
					"preco_unitario": preco_unitario,
					"valor_total_operacao": valor_total_operacao
				}
				
				# Calcular hash
				hash_linha = _calculate_hash(row_data)
				
				# Fazer upsert
				_, was_inserted = movimentacao_repo.upsert(hash_linha, **row_data)
				
				if was_inserted:
					inseridas += 1
				else:
					atualizadas += 1
					
			except Exception as e:
				erros += 1
				print(f"Erro ao processar linha: {e}")
				continue
		
		conn.execute("COMMIT;")
		
	except Exception as e:
		conn.execute("ROLLBACK;")
		raise ValidationError(f"Erro na importação: {e}")
	finally:
		conn.close()
	
	return inseridas, atualizadas, ignoradas, erros
