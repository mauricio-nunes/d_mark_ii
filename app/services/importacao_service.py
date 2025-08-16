from typing import Dict, List, Tuple
from ..core.xlsx import read_xlsx_rows, list_sheets
from ..core.decimal_ctx import D
from ..core.daterules import parse_year_month_from_sheet, last_business_day
from ..db.repositories import ativos_repo, proventos_repo, fechamentos_repo
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
