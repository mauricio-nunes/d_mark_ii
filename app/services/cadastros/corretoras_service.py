from ...db.connection import get_conn
from ...db.repositories import corretoras_repo
from ...db.repositories import eventos_repo
from datetime import datetime


class ValidationError(Exception): ...


def _validate_nome_unique(nome: str, ignore_id: int | None = None, conn=None):
    if not nome or not nome.strip():
        raise ValidationError("Nome é obrigatório.")
    found = corretoras_repo.get_by_nome(nome, conn=conn)
    if found and (ignore_id is None or found["id"] != ignore_id):
        raise ValidationError("Já existe uma corretora com esse nome.")


def criar_corretora(nome: str, descricao: str = "") -> int:
    conn = get_conn()
    _validate_nome_unique(nome, conn=conn)
    corretora_id = corretoras_repo.criar(nome, descricao, conn=conn)
    now = datetime.now().strftime("%Y-%m-%d")

    eventos_repo.criar(
        {
            "tipo": "corretora",
            "entidade_id": corretora_id,
            "evento": "criacao",
            "nome": nome,
            "data_ex": now,
            "observacoes": f"Corretora '{descricao}' criada.",
        },
        conn=conn,
    )
    conn.commit()
    conn.close()
    return corretora_id


def inativar_corretora(cid: int) -> None:
    conn = get_conn()
    if not corretoras_repo.get_by_id(cid, conn=conn):
        raise ValidationError("Corretora não encontrada.")
    corretoras_repo.inativar(cid, conn=conn)
    conn.commit()
    conn.close()


def reativar_corretora(cid: int) -> None:
    conn = get_conn()
    if not corretoras_repo.get_by_id(cid, conn=conn):
        raise ValidationError("Corretora não encontrada.")
    corretoras_repo.reativar(cid, conn=conn)
    conn.commit()
    conn.close()


def get_corretora_por_id(cid: int) -> dict | None:
    return corretoras_repo.get_by_id(cid, conn=get_conn())


def listar_corretoras(
    texto: str = "", apenas_ativas: bool = True, offset: int = 0, limit: int = 20
) -> list[dict]:
    return corretoras_repo.listar_corretoras(
        texto, apenas_ativas, offset, limit, conn=get_conn()
    )


def contar_corretoras(texto: str = "", apenas_ativas: bool = True) -> int:
    return corretoras_repo.contar_corretoras(texto, apenas_ativas, conn=get_conn())


def editar_corretora(cid: int, nome: str, descricao: str = "") -> None:
    conn = get_conn()
    if not corretoras_repo.get_by_id(cid, conn=conn):
        raise ValidationError("Corretora não encontrada.")
    _validate_nome_unique(nome, ignore_id=cid, conn=conn)
    corretoras_repo.update(cid, nome, descricao, conn=conn)
    
    now = datetime.now().strftime("%Y-%m-%d")
    eventos_repo.criar(
        {
            "tipo": "corretora",
            "entidade_id": cid,
            "evento": "alteracao",
            "nome": nome,
            "data_ex": now,
            "observacoes": f"Corretora '{descricao}' alterada.",
        },
        conn=conn,
    )
    
    conn.commit()
    conn.close()
