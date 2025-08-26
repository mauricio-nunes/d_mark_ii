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
from ..db.repositories import movimentacao_repo , valor_mobiliario_repo
from ..db.repositories import b3_posicao_consolidada_repo, corretoras_repo
from ..db.repositories import users_repo  # só para garantir conexão se precisar

class ValidationError(Exception): ...

# chaves do config
CFG_PROV_MAP = "xlsx_map_proventos"     # json str
CFG_FECH_MAP = "xlsx_map_fechamentos"   # json str

# --------- helpers de mapeamento ---------

def _normalize(s: str | None) -> str:
    return (s or "").strip()

TICKER_REGEX = re.compile(r'^[A-Z]{3,4}[0-9]{1,2}$')
def validar_ticker_b3(ticker: str) -> bool:
    """
    Valida se uma string é um possível código de negociação da B3.
    """
    if bool(TICKER_REGEX.match(ticker.upper())):
        return ticker.upper()
    
    return False

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

# --------- CVM IMPORT ---------

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

def download_cvm_valor_mobiliario_file(year: int) -> str:
    """
    Download CVM file for the given year and return path to extracted CSV.
    Raises Exception if download or extraction fails.
    """
    url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{year}.zip"
    
    # Create temp directory for download
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"fca_cia_aberta_{year}.zip")
    csv_path = os.path.join(temp_dir, f"fca_cia_aberta_valor_mobiliario_{year}.csv")

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
            expected_csv = f"fca_cia_aberta_valor_mobiliario_{year}.csv"
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

def import_cvm_companies(year: int | None = None) -> tuple[int, int, int, int]:
    """
    Import CVM companies for the given year (default: current year).
    Returns (inserted_count, updated_count, ignored_count, error_count).
    """
    if year is None:
        year = datetime.now().year
    
    if year < 2010:
        raise ValidationError("Ano deve ser maior ou igual a 2010")
    
    # Download and extract file
    csv_path = download_cvm_file(year)
    
    try:
        inserted, updated, ignored, errors = 0, 0, 0, 0

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
                        categoria_registro = row.get("Categoria_Registro_CVM", "").strip() or None
                        controle_id = row.get("ID_Documento", "").strip() or None
                        pais_origem = row.get("Pais_Origem", "").strip() or None
                        pais_custodia = row.get("Pais_Custodia_Valores_Mobiliarios", "").strip() or None
                        situacao_emissor = row.get("Situacao_Emissor", "").strip() or None
                        dia_encerramento_fiscal = row.get("Dia_Encerramento_Exercicio_Social", "").strip() or None
                        mes_encerramento_fiscal = row.get("Mes_Encerramento_Exercicio_Social", "").strip() or None

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
                            ativo=ativo,
                            categoria_registro=categoria_registro,
                            controle_id=controle_id,
                            pais_origem=pais_origem,
                            pais_custodia=pais_custodia,
                            situacao_emissor=situacao_emissor,
                            dia_encerramento_fiscal=dia_encerramento_fiscal,
                            mes_encerramento_fiscal=mes_encerramento_fiscal
                        )

                        if was_inserted == 1:
                            inserted += 1
                        elif was_inserted == 2:
                            updated += 1
                        else:
                            ignored += 1

                    except Exception as e:
                        errors += 1
                    
                    pbar.update(1)
        
        return inserted, updated, ignored, errors
        
    finally:
        # Cleanup temp files
        try:
            if os.path.exists(csv_path):
                os.remove(csv_path)
            if os.path.exists(os.path.dirname(csv_path)):
                os.rmdir(os.path.dirname(csv_path))
        except:
            pass  # Ignore cleanup errors

def import_cvm_valores_mobiliarios(year: int | None = None) -> tuple[int, int, int, int]:
    """
    Import CVM Valores Mobiliarios for the given year (default: current year).
    Returns (inserted_count, updated_count,ignored_count, error_count).
    """
    if year is None:
        year = datetime.now().year
    
    if year < 2010:
        raise ValidationError("Ano deve ser maior ou igual a 2010")
    
    # Download and extract file
    csv_path = download_cvm_valor_mobiliario_file(year)
    
    try:
        inserted, updated, ignored, errors = 0, 0, 0, 0

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

                        empresa = empresas_repo.get_by_cnpj(cnpj)
                        empresa_id = empresa["id"]
                        if not empresa_id:
                            errors += 1
                            pbar.update(1)
                            continue

                        mercado = row.get("Mercado", "").strip() or None
                        if mercado != "Bolsa":
                            ignored += 1
                            pbar.update(1)
                            continue

                        valor_mobiliario = row.get("Valor_Mobiliario", "").strip() or None
                        if valor_mobiliario != "Ações Ordinárias" and valor_mobiliario != "Ações Preferenciais" and valor_mobiliario != "Units":
                            ignored += 1
                            pbar.update(1)
                            continue

                        codigo_negociacao = validar_ticker_b3(row.get("Codigo_Negociacao", "").strip())
                        if not codigo_negociacao:
                            errors += 1
                            pbar.update(1)
                            continue

                        nome = row.get("Nome_Empresarial", "").strip()
                        classe = "Acao"
                        controle_id = row.get("ID_Documento", "").strip() or None
                        sigla_classe_acao = row.get("Sigla_Classe_Acao_Preferencial", "").strip() or None
                        classe_acao = row.get("Classe_Acao_Preferencial", "").strip() or None
                        composicao = row.get("Composicao_BDR_Unit", "").strip() or None
                        data_inicio_negociacao = _parse_cvm_date(row.get("Data_Inicio_Negociacao", ""))
                        data_fim_negociacao = _parse_cvm_date(row.get("Data_Fim_Negociacao", ""))
                        segmento = row.get("Segmento", "").strip() or None
                        importado = 1

						# Set ativo based on situacao
                        ativo = 1
                        
                        # Upsert company
                        empresa_id, was_inserted = valor_mobiliario_repo.upsert_by_ticker(
                            ticker=codigo_negociacao,
                            nome=nome,
                            classe=classe,
                            empresa_id=empresa_id,
                            controle_id = controle_id,
                            valor_mobiliario=valor_mobiliario,
                            sigla_classe_acao=sigla_classe_acao,
                            classe_acao=classe_acao,
                            composicao=composicao,
                            mercado=mercado,
                            data_inicio_negociacao=data_inicio_negociacao,
                            data_fim_negociacao=data_fim_negociacao,
                            segmento=segmento,
                            importado=importado,
                            ativo=ativo
                        )

                        if was_inserted == 1:
                            inserted += 1
                        elif was_inserted == 2:
                            updated += 1
                        else:
                            ignored += 1

                    except Exception as e:
                        errors += 1
                    
                    pbar.update(1)
        
        return inserted, updated, ignored, errors
        
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

# --------- B3 POSIÇÃO CONSOLIDADA ---------

def find_b3_posicao_files(imports_dir: str = "imports") -> list[str]:
	"""Encontra arquivos de posição consolidada da B3 na pasta imports"""
	import calendar
	
	meses = [
		'janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho',
		'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
	]
	
	pattern = os.path.join(imports_dir, "relatorio-consolidado-mensal-*.xlsx")
	files = glob.glob(pattern)
	
	# Filtrar apenas arquivos com padrão válido
	valid_files = []
	for file in files:
		basename = os.path.basename(file)
		# Padrão: relatorio-consolidado-mensal-YYYY-{mes}.xlsx
		match = re.match(r'^relatorio-consolidado-mensal-(\d{4})-(janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\.xlsx$', basename.lower())
		if match:
			valid_files.append(file)
	
	# Ordenar por mtime (mais recente primeiro) e limitar a 10
	valid_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
	return valid_files[:10]

def _parse_data_referencia_from_filename(filename: str) -> str:
	"""Extrai a data de referência do nome do arquivo"""
	import calendar
	from datetime import date
	
	meses_map = {
		'janeiro': 1, 'fevereiro': 2, 'marco': 3, 'abril': 4,
		'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
		'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
	}
	
	basename = os.path.basename(filename).lower()
	match = re.match(r'^relatorio-consolidado-mensal-(\d{4})-(janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\.xlsx$', basename)
	
	if not match:
		raise ValidationError(f"Nome de arquivo inválido: {filename}")
	
	ano = int(match.group(1))
	mes_nome = match.group(2)
	mes = meses_map[mes_nome]
	
	# Último dia do mês (fevereiro sempre 28 conforme requisito)
	if mes == 2:
		ultimo_dia = 28
	else:
		ultimo_dia = calendar.monthrange(ano, mes)[1]
	
	return f"{ano:04d}-{mes:02d}-{ultimo_dia:02d}"

def _validate_b3_posicao_cadastros(rows: List[dict]) -> List[str]:
	"""Valida se instituições, CNPJs e tickers existem nos cadastros"""
	from ..db.connection import get_conn
	
	errors = []
	
	# Obter listas de cadastros existentes
	conn = get_conn()
	
	# Corretoras (descricao)
	corretoras_existentes = {
		row['descricao'].strip().lower() for row in 
		conn.execute("SELECT descricao FROM corretoras WHERE ativo=1 AND descricao IS NOT NULL").fetchall()
	}
	
	# Empresas (CNPJ)
	empresas_existentes = {
		row['cnpj'].strip() for row in 
		conn.execute("SELECT cnpj FROM empresas WHERE ativo=1").fetchall()
	}
	
	# Ativos (ticker)
	ativos_existentes = {
		row['ticker'].strip().upper() for row in 
		conn.execute("SELECT ticker FROM ativos WHERE ativo=1").fetchall()
	}
	
	conn.close()
	
	# Verificar dados do arquivo
	instituicoes_faltantes = set()
	cnpjs_faltantes = set()
	tickers_faltantes = set()
	
	for row in rows:
		instituicao = row.get('instituicao', '').strip().lower()
		cnpj = row.get('cnpj_empresa', '').strip()
		ticker = row.get('codigo_negociacao', '').strip().upper()
		
		if instituicao and instituicao not in corretoras_existentes:
			instituicoes_faltantes.add(row.get('instituicao', '').strip())
		
		if cnpj and cnpj not in empresas_existentes:
			cnpjs_faltantes.add(cnpj)
		
		if ticker and ticker not in ativos_existentes:
			tickers_faltantes.add(ticker)
	
	# Montar lista de erros
	if instituicoes_faltantes:
		errors.append(f"Instituições não cadastradas: {', '.join(sorted(instituicoes_faltantes))}")
	
	if cnpjs_faltantes:
		errors.append(f"CNPJs não cadastrados: {', '.join(sorted(cnpjs_faltantes))}")
	
	if tickers_faltantes:
		errors.append(f"Tickers não cadastrados: {', '.join(sorted(tickers_faltantes))}")
	
	return errors

def _normalize_b3_decimal(value) -> str:
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

def preview_b3_posicao(path: str) -> List[dict]:
	"""Gera preview dos dados de posição consolidada"""
	# Verificar se a aba existe
	sheets = list_sheets(path)
	sheet_target = "Posição - Ações"
	
	if sheet_target not in sheets:
		raise ValidationError(f"Aba '{sheet_target}' não encontrada. Abas disponíveis: {', '.join(sheets)}")
	
	rows = read_xlsx_rows(path, sheet_target)
	data_referencia = _parse_data_referencia_from_filename(path)
	
	preview_data = []
	for row in rows[:50]:  # Limitar preview a 50 linhas
		# Ignorar linhas de totalização
		valor_atualizado = str(row.get('Valor Atualizado', '')).strip()
		if 'total' in valor_atualizado.lower():
			continue
		
		preview_data.append({
			'data_referencia': data_referencia,
			'instituicao': str(row.get('Instituição', '')).strip(),
			'conta': str(row.get('Conta', '')).strip(),
			'cnpj_empresa': str(row.get('CNPJ da Empresa', '')).strip(),
			'codigo_negociacao': str(row.get('Código de Negociação', '')).strip(),
			'nome_ativo': str(row.get('Ativo', '')).strip(),
			'quantidade_disponivel': _normalize_b3_decimal(row.get('Quantidade Disponível', 0)),
			'quantidade_indisponivel': _normalize_b3_decimal(row.get('Quantidade Indisponível', 0)),
			'valor_atualizado': _normalize_b3_decimal(row.get('Valor Atualizado', 0))
		})
	
	return preview_data

def importar_b3_posicao(path: str) -> Tuple[int, int, int]:
	"""
	Importa posição consolidada da B3
	Returns (inseridas, removidas, erros)
	"""
	from ..db.connection import get_conn
	
	# Verificar se a aba existe
	sheets = list_sheets(path)
	sheet_target = "Posição - Ações"
	
	if sheet_target not in sheets:
		raise ValidationError(f"Aba '{sheet_target}' não encontrada. Abas disponíveis: {', '.join(sheets)}")
	
	rows = read_xlsx_rows(path, sheet_target)
	data_referencia = _parse_data_referencia_from_filename(path)
	
	# Mapear colunas esperadas
	expected_columns = [
		'Instituição', 'Conta', 'CNPJ da Empresa', 'Código de Negociação',
		'Ativo', 'Quantidade Disponível', 'Quantidade Indisponível', 'Valor Atualizado'
	]
	
	# Verificar cabeçalhos (primeira linha não vazia)
	if not rows:
		raise ValidationError("Arquivo não contém dados")
	
	first_row = rows[0] if rows else {}
	missing_columns = [col for col in expected_columns if col not in first_row]
	
	if missing_columns:
		raise ValidationError(f"Colunas faltantes: {', '.join(missing_columns)}")
	
	# Processar dados e filtrar linhas válidas
	processed_data = []
	for row in rows:
		# Ignorar linhas de totalização
		valor_atualizado = str(row.get('Valor Atualizado', '')).strip()
		if 'total' in valor_atualizado.lower():
			continue
		
		# Verificar se linha tem dados essenciais
		codigo_negociacao = str(row.get('Código de Negociação', '')).strip()
		if not codigo_negociacao:
			continue
		
		processed_data.append({
			'data_referencia': data_referencia,
			'instituicao': str(row.get('Instituição', '')).strip(),
			'conta': str(row.get('Conta', '')).strip(),
			'cnpj_empresa': str(row.get('CNPJ da Empresa', '')).strip(),
			'codigo_negociacao': codigo_negociacao.upper(),
			'nome_ativo': str(row.get('Ativo', '')).strip(),
			'quantidade_disponivel': _normalize_b3_decimal(row.get('Quantidade Disponível', 0)),
			'quantidade_indisponivel': _normalize_b3_decimal(row.get('Quantidade Indisponível', 0)),
			'valor_atualizado': _normalize_b3_decimal(row.get('Valor Atualizado', 0))
		})
	
	if not processed_data:
		raise ValidationError("Nenhuma linha válida encontrada para importação")
	
	# Validações bloqueantes
	validation_errors = _validate_b3_posicao_cadastros(processed_data)
	if validation_errors:
		raise ValidationError("\n".join(validation_errors))
	
	# Verificar duplicidade por competência
	removidas = 0
	if b3_posicao_consolidada_repo.exists_by_competencia(data_referencia):
		removidas = b3_posicao_consolidada_repo.delete_by_competencia(data_referencia)
	
	# Importação transacional com progresso
	conn = get_conn()
	inseridas = 0
	erros = 0
	
	try:
		conn.execute("BEGIN;")
		
		# Barra de progresso
		for row_data in tqdm(processed_data, desc="Importando posições"):
			try:
				b3_posicao_consolidada_repo.create(row_data)
				inseridas += 1
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
	
	# Mover arquivo para processed
	_move_to_processed(path)
	
	return inseridas, removidas, erros

def _move_to_processed(file_path: str):
	"""Move arquivo processado para imports/processed"""
	import shutil
	
	processed_dir = os.path.join(os.path.dirname(file_path), "processed")
	os.makedirs(processed_dir, exist_ok=True)
	
	filename = os.path.basename(file_path)
	destination = os.path.join(processed_dir, filename)
	
	# Resolver colisão de nome se necessário
	if os.path.exists(destination):
		from datetime import datetime
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		name, ext = os.path.splitext(filename)
		filename = f"{name}_{timestamp}{ext}"
		destination = os.path.join(processed_dir, filename)
	
	shutil.move(file_path, destination)
