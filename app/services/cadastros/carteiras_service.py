from ...db.repositories import carteiras_repo as repo

class ValidationError(Exception): ...

def _unique(nome: str, ignore_id: int | None = None):
    if not nome or not nome.strip():
        raise ValidationError("Nome é obrigatório.")
    found = repo.get_by_nome(nome)
    if found and (ignore_id is None or found["id"] != ignore_id):
        raise ValidationError("Já existe uma carteira com esse nome.")

def criar(nome: str, descricao: str = "") -> int:
    _unique(nome); return repo.create(nome, descricao)

def editar(cid: int, nome: str, descricao: str = ""):
    if not repo.get_by_id(cid): raise ValidationError("Carteira não encontrada.")
    _unique(nome, ignore_id=cid); repo.update(cid, nome, descricao)

def inativar(cid: int): 
    if not repo.get_by_id(cid): raise ValidationError("Carteira não encontrada.")
    repo.inativar(cid)

def reativar(cid: int): 
    if not repo.get_by_id(cid): raise ValidationError("Carteira não encontrada.")
    repo.reativar(cid)
