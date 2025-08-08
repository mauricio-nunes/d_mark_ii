from ...db.repositories import empresas_repo as repo
from ...core.utils import normalize_cnpj

class ValidationError(Exception): ...

def _valid_cnpj(cnpj: str) -> bool:
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

def _check_unique_cnpj(cnpj: str, ignore_id: int | None = None):
    c = normalize_cnpj(cnpj)
    if not _valid_cnpj(c): raise ValidationError("CNPJ inválido.")
    found = repo.get_by_cnpj(c)
    if found and (ignore_id is None or found["id"] != ignore_id):
        raise ValidationError("Já existe empresa com este CNPJ.")
    return c

def criar(**data) -> int:
    cnpj = _check_unique_cnpj(data.get("cnpj",""))
    if not data.get("razao_social"): raise ValidationError("Razão social é obrigatória.")
    tipo = (data.get("tipo_empresa") or "").strip()
    if tipo not in ("Fundo","CiaAberta"): raise ValidationError("tipo_empresa deve ser Fundo ou CiaAberta.")
    data["cnpj"] = cnpj
    return repo.create(**data)

def editar(eid: int, **data):
    reg = repo.get_by_id(eid)
    if not reg: raise ValidationError("Empresa não encontrada.")
    cnpj = _check_unique_cnpj(data.get("cnpj", reg["cnpj"]), ignore_id=eid)  # mantém CNPJ se vier igual
    tipo = (data.get("tipo_empresa") or reg["tipo_empresa"]).strip()
    if tipo not in ("Fundo","CiaAberta"): raise ValidationError("tipo_empresa deve ser Fundo ou CiaAberta.")
    data["cnpj"] = cnpj; data["tipo_empresa"] = tipo
    repo.update(eid, **data)

def inativar(eid: int):
    if not repo.get_by_id(eid): raise ValidationError("Empresa não encontrada.")
    repo.inativar(eid)

def reativar(eid: int):
    if not repo.get_by_id(eid): raise ValidationError("Empresa não encontrada.")
    repo.reativar(eid)
