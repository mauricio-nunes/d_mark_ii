from ...db.repositories import ativos_repo as repo
from ...db.repositories import empresas_repo
class ValidationError(Exception): ...

CLASSES = ("Acao","FII","Tesouro","BDR","ETF")

def _unique_ticker(ticker: str, ignore_id: int | None = None):
    if not ticker or not ticker.strip(): raise ValidationError("Ticker é obrigatório.")
    found = repo.get_by_ticker(ticker)
    if found and (ignore_id is None or found["id"] != ignore_id):
        raise ValidationError("Já existe ativo com esse ticker.")

def _empresa_optional(empresa_id):
    if empresa_id in (None, "", 0): return None
    emp = empresas_repo.get_by_id(int(empresa_id))
    if not emp: raise ValidationError("Empresa vinculada não encontrada.")
    return int(empresa_id)

def criar(ticker: str, nome: str, classe: str, empresa_id):
    _unique_ticker(ticker)
    if classe not in CLASSES: raise ValidationError(f"Classe inválida. Use uma de {CLASSES}.")
    if not nome or not nome.strip(): raise ValidationError("Nome é obrigatório.")
    emp_id = _empresa_optional(empresa_id)
    return repo.create(ticker, nome, classe, emp_id)

def editar(aid: int, ticker: str, nome: str, classe: str, empresa_id):
    if not repo.get_by_id(aid): raise ValidationError("Ativo não encontrado.")
    _unique_ticker(ticker, ignore_id=aid)
    if classe not in CLASSES: raise ValidationError(f"Classe inválida. Use uma de {CLASSES}.")
    if not nome or not nome.strip(): raise ValidationError("Nome é obrigatório.")
    emp_id = _empresa_optional(empresa_id)
    repo.update(aid, ticker, nome, classe, emp_id)

def inativar(aid: int):
    if not repo.get_by_id(aid): raise ValidationError("Ativo não encontrado.")
    repo.inativar(aid)

def reativar(aid: int):
    if not repo.get_by_id(aid): raise ValidationError("Ativo não encontrado.")
    repo.reativar(aid)
