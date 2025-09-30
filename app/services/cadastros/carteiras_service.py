from ...db.connection import get_conn
from ...db.repositories.carteiras_repo import CarteirasRepo as carteiras_repo

class ValidationError(Exception): ...

class CarteirasService:
    
    def __init__(self):
        conn = get_conn()
        self.carteira_repo = carteiras_repo(conn)

    def _unique(self, nome: str, ignore_id: int | None = None):
        if not nome or not nome.strip():
            raise ValidationError("Nome é obrigatório.")
        found = self.carteira_repo.get_by_nome(nome)
        if found and (ignore_id is None or found["id"] != ignore_id):
            raise ValidationError("Já existe uma carteira com esse nome.")
        
    def contar_carteiras(self, texto: str = "", apenas_ativas: bool = True) -> int:
        count =  self.carteira_repo.contar(texto, apenas_ativas)
        self.close()
        return count

    def criar_carteira(self, nome: str, descricao: str = "") -> int:
        self._unique(nome)
        carteira_id =  self.carteira_repo.criar(nome, descricao)
        self.dispose()
        return carteira_id

    def editar_carteira(self, cid: int, nome: str, descricao: str = ""):
        if not self.carteira_repo.get_by_id(cid):
            raise ValidationError("Carteira não encontrada.")
        self._unique(nome, ignore_id=cid)
        self.carteira_repo.editar(cid, nome, descricao)
        self.dispose()

    def inativar_carteira(self, cid: int):
        if not self.carteira_repo.get_by_id(cid):
            raise ValidationError("Carteira não encontrada.")
        self.carteira_repo.inativar(cid)
        self.dispose()

    def reativar_carteira(self, cid: int):
        if not self.carteira_repo.get_by_id(cid):
            raise ValidationError("Carteira não encontrada.")
        self.carteira_repo.reativar(cid)
        self.dispose()
    
    def listar_carteiras(
        self,
        texto: str = "",
        apenas_ativas: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        rows = self.carteira_repo.listar(texto, apenas_ativas, offset, limit)
        self.close()
        return rows
    
    def get_carteira_por_id(self, eid: int) -> dict | None:
        carteira = self.carteira_repo.get_by_id(eid)
        self.close()
        return carteira

    def close(self):
        self.carteira_repo.conn.close()

    def dispose(self):
        self.carteira_repo.conn.commit()
        self.close()
