from ...db.connection import get_conn
from ...db.repositories.ativos_repo import AtivosRepo as ativos_repo
from ...db.repositories.empresas_repo import  EmpresasRepo as empresas_repo
class ValidationError(Exception): ...

CLASSES = ("Acao","FII","Tesouro","BDR","ETF")

class AtivosService:
    def __init__(self):
        conn = get_conn()
        self.ativo_repo = ativos_repo(conn)
        self.empresa_repo = empresas_repo(conn)




    def _unique_ticker(self, ticker: str, ignore_id: int | None = None):
        if not ticker or not ticker.strip(): raise ValidationError("Ticker é obrigatório.")
        found = self.ativo_repo.get_by_ticker(ticker)
        if found and (ignore_id is None or found["id"] != ignore_id):
            raise ValidationError("Já existe ativo com esse ticker.")

    def _empresa_optional(self, empresa_id):
        if empresa_id in (None, "", 0): return None
        emp = self.empresa_repo.get_by_id(int(empresa_id))
        if not emp: raise ValidationError("Empresa vinculada não encontrada.")
        return int(empresa_id)

    def contar_ativos(self, texto: str = "", apenas_ativas: bool = True) -> int:
        total = self.ativo_repo.contar(texto, apenas_ativas)
        self.close()
        return total

    def listar_ativos(self, texto: str = "", apenas_ativas: bool = True, offset: int = 0, limit: int = 20) -> list[dict]:
        rows = self.ativo_repo.listar(texto, apenas_ativas, offset, limit)
        self.close()
        return rows

    def criar_ativo(self, ticker: str, nome: str, classe: str, empresa_id):
        self._unique_ticker(ticker)
        if classe not in CLASSES: raise ValidationError(f"Classe inválida. Use uma de {CLASSES}.")
        if not nome or not nome.strip(): raise ValidationError("Nome é obrigatório.")
        emp_id = self._empresa_optional(empresa_id)
        ativo =  self.ativo_repo.criar(ticker, nome, classe, emp_id)
        self.dispose()
        return ativo

    def editar_ativo(self, aid: int, ticker: str, nome: str, classe: str, empresa_id):
        if not self.ativo_repo.get_by_id(aid): 
            raise ValidationError("Ativo não encontrado.")
        self._unique_ticker(ticker, ignore_id=aid)
        if classe not in CLASSES: raise ValidationError(f"Classe inválida. Use uma de {CLASSES}.")
        if not nome or not nome.strip(): raise ValidationError("Nome é obrigatório.")
        emp_id = self._empresa_optional(empresa_id)
        self.ativo_repo.editar(aid, ticker, nome, classe, emp_id)
        self.dispose()
        
    def get_ativo_por_id(self, aid: int) -> dict | None:
        ativo = self.ativo_repo.get_by_id(aid)
        self.close()
        return ativo

    def inativar_ativo(self, aid: int):
        if not self.ativo_repo.get_by_id(aid): 
            raise ValidationError("Ativo não encontrado.")
        self.ativo_repo.inativar(aid)
        self.dispose()

    def reativar_ativo(self, aid: int):
        if not self.ativo_repo.get_by_id(aid): 
            raise ValidationError("Ativo não encontrado.")
        self.ativo_repo.reativar(aid)
        self.dispose()

    def close(self):
            self.ativo_repo.conn.close()

    def dispose(self):
        self.ativo_repo.conn.commit()
        self.close()