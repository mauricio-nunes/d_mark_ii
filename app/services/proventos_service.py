from ..db.repositories import proventos_repo, ativos_repo
from datetime import datetime

class ValidationError(Exception): ...

TIPOS = ("DIVIDENDO","JCP","RENDIMENTO FII","AMORTIZACAO","OUTROS")

def _parse_date(s: str):
    try: datetime.strptime(s, "%Y-%m-%d")
    except: raise ValidationError("Data inválida. Use YYYY-MM-DD.")

def incluir(data: dict) -> int:
    _parse_date(data["data_pagamento"])
    if (data.get("tipo_evento") or "").upper() not in TIPOS:
        raise ValidationError(f"Tipo inválido. Use um de {TIPOS}.")
    if not ativos_repo.get_by_id(data["ticker"]):
        raise ValidationError("Ativo não encontrado.")
    return proventos_repo.create(data)

def editar(pid: int, data: dict) -> None:
    _parse_date(data["data_pagamento"])
    if (data.get("tipo_evento") or "").upper() not in TIPOS:
        raise ValidationError(f"Tipo inválido. Use um de {TIPOS}.")
    if not ativos_repo.get_by_id(data["ticker"]):
        raise ValidationError("Ativo não encontrado.")
    proventos_repo.update(pid, data)

def excluir(pid: int) -> None:
    proventos_repo.soft_delete(pid)
