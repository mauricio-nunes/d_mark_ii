from ...db.connection import get_conn
from ...db.repositories.corretoras_repo import CorretorasRepo as corretoras_repo
from ...db.repositories.eventos_repo import EventosRepo as eventos_repo
from datetime import datetime


class ValidationError(Exception): ...


class CorretorasService:
    def __init__(self):
        conn = get_conn()
        self.corretora_repo = corretoras_repo(conn)
        self.evento_repo = eventos_repo(conn)

    def _validate_nome_unique(self, nome: str, ignore_id: int | None = None):
        if not nome or not nome.strip():
            raise ValidationError("Nome é obrigatório.")
        found = self.corretora_repo.get_by_nome(nome)
        if found and (ignore_id is None or found["id"] != ignore_id):
            raise ValidationError("Já existe uma corretora com esse nome.")

    def criar_corretora(self, nome: str, descricao: str = "") -> int:

        self._validate_nome_unique(nome)
        corretora_id = self.corretora_repo.criar(nome, descricao)
        now = datetime.now().strftime("%Y-%m-%d")

        self.evento_repo.criar(
            {
                "tipo": "corretora",
                "entidade_id": corretora_id,
                "evento": "criacao",
                "nome": nome,
                "data_ex": now,
                "observacoes": f"Corretora '{descricao}' criada.",
            }
        )
        self.dispose()
        return corretora_id

    def inativar_corretora(self, eid: int) -> None:

        if not self.corretora_repo.get_by_id(eid):
            raise ValidationError("Corretora não encontrada.")
        self.corretora_repo.inativar(eid)
        self.dispose()

    def reativar_corretora(self, eid: int) -> None:
        if not self.corretora_repo.get_by_id(eid):
            raise ValidationError("Corretora não encontrada.")
        self.corretora_repo.reativar(eid)
        self.dispose()

    def get_corretora_por_id(self, eid: int) -> dict | None:
        corretora = self.corretora_repo.get_by_id(eid)
        self.close()
        return corretora

    def listar_corretoras(
        self,
        texto: str = "",
        apenas_ativas: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        rows = self.corretora_repo.listar(texto, apenas_ativas, offset, limit)
        self.close()
        return rows

    def contar_corretoras(self, texto: str = "", apenas_ativas: bool = True) -> int:
        count = self.corretora_repo.contar(texto, apenas_ativas)
        self.close()
        return count

    def editar_corretora(self, cid: int, nome: str, descricao: str = "") -> None:
        if not self.corretora_repo.get_by_id(cid):
            raise ValidationError("Corretora não encontrada.")
        self._validate_nome_unique(nome, ignore_id=cid)
        self.corretora_repo.editar(cid, nome, descricao)

        now = datetime.now().strftime("%Y-%m-%d")
        self.evento_repo.criar(
            {
                "tipo": "corretora",
                "entidade_id": cid,
                "evento": "alteracao",
                "nome": nome,
                "data_ex": now,
                "observacoes": f"Corretora '{descricao}' alterada.",
            }
        )

        self.dispose()

    def close(self):
        self.corretora_repo.conn.close()

    def dispose(self):
        self.corretora_repo.conn.commit()
        self.close()
