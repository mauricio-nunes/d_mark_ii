from typing import Dict, List, Tuple
import os
import csv
import zipfile
import requests
import tempfile
from datetime import datetime
from tqdm import tqdm
from ..core.xlsx import read_xlsx_rows, list_sheets
from ..core.decimal_ctx import D
from ..core.daterules import parse_year_month_from_sheet, last_business_day
from ..core.utils import normalize_cnpj
from ..db.repositories import ativos_repo, proventos_repo, fechamentos_repo, empresas_repo
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
