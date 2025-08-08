from ...db.repositories import corretoras_repo as repo

class ValidationError(Exception): ...

def _validate_nome_unique(nome: str, ignore_id: int | None = None):
    if not nome or not nome.strip():
        raise ValidationError("Nome é obrigatório.")
    found = repo.get_by_nome(nome)
    if found and (ignore_id is None or found["id"] != ignore_id):
        raise ValidationError("Já existe uma corretora com esse nome.")

def criar_corretora(nome: str, descricao: str = "") -> int:
    _validate_nome_unique(nome)
    return repo.create(nome, descricao)

def editar_corretora(cid: int, nome: str, descricao: str = "") -> None:
    if not repo.get_by_id(cid):
        raise ValidationError("Corretora não encontrada.")
    _validate_nome_unique(nome, ignore_id=cid)
    repo.update(cid, nome, descricao)

def inativar_corretora(cid: int) -> None:
    if not repo.get_by_id(cid):
        raise ValidationError("Corretora não encontrada.")
    repo.inativar(cid)

def reativar_corretora(cid: int) -> None:
    if not repo.get_by_id(cid):
        raise ValidationError("Corretora não encontrada.")
    repo.reativar(cid)
