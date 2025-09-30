from ...db.connection import get_conn
from ...db.repositories.empresas_repo import EmpresasRepo as empresas_repo
from ...core.utils import normalize_cnpj, valid_cnpj


class ValidationError(Exception): ...


class EmpresasService:
    def __init__(self):
        self.empresa_repo = empresas_repo(get_conn())

    def _check_unique_cnpj(self, cnpj: str, ignore_id: int | None = None):
        c = normalize_cnpj(cnpj)
        if not valid_cnpj(c):
            raise ValidationError("CNPJ inválido.")
        found = self.empresa_repo.get_by_cnpj(c)
        if found and (ignore_id is None or found["id"] != ignore_id):
            raise ValidationError("Já existe empresa com este CNPJ.")
        return c

    # def _check_unique_codigo_cvm(codigo_cvm: str, ignore_id: int | None = None):
    #     found = empresas_repo.get_by_codigo_cvm(codigo_cvm)
    #     if found and (ignore_id is None or found["id"] != ignore_id):
    #         raise ValidationError("Já existe uma empresa com este Código CVM.")
    #     return codigo_cvm

    def criar_empresa(self, **data) -> int:

        if not data.get("cnpj"):
            raise ValidationError("CNPJ é obrigatório.")
        if not data.get("razao_social"):
            raise ValidationError("Razão social é obrigatória.")
        tipo = (data.get("tipo_empresa") or "").strip()
        if tipo not in ("Fundo", "CiaAberta"):
            raise ValidationError("tipo_empresa deve ser Fundo ou CiaAberta.")

        cnpj = self._check_unique_cnpj(data.get("cnpj", ""))
        data["cnpj"] = cnpj
        eid = self.empresa_repo.criar(**data)
        self.dispose()
        return eid

    def editar_empresa(self, eid: int, **data):

        reg = self.empresa_repo.get_by_id(eid)
        if not reg:
            raise ValidationError("Empresa não encontrada.")
        cnpj = self._check_unique_cnpj(
            data.get("cnpj", reg["cnpj"]), ignore_id=eid
        )  # mantém CNPJ se vier igual
        tipo = (data.get("tipo_empresa") or reg["tipo_empresa"]).strip()
        if tipo not in ("Fundo", "CiaAberta"):
            raise ValidationError("tipo_empresa deve ser Fundo ou CiaAberta.")
        data["cnpj"] = cnpj
        data["tipo_empresa"] = tipo
        self.empresa_repo.editar(eid, **data)
        self.dispose()

    def inativar_empresa(self, eid: int):

        if not self.empresa_repo.get_by_id(eid):
            raise ValidationError("Empresa não encontrada.")

        self.empresa_repo.inativar(eid)
        self.dispose()

    def reativar_empresa(self, eid: int):
        if not self.empresa_repo.get_by_id(eid):
            raise ValidationError("Empresa não encontrada.")

        self.empresa_repo.reativar(eid)
        self.dispose()

    def contar_empresas(self, filtro: str = "", apenas_ativas: bool = True) -> int:
        count = self.empresa_repo.contar(filtro, apenas_ativas)
        self.close()
        return count

    def listar_empresas(
        self,
        filtro: str = "",
        apenas_ativas: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        rows = self.empresa_repo.listar(filtro, apenas_ativas, offset, limit)
        self.close()
        return rows

    def get_empresa_por_id(self, eid: int) -> dict | None:
        empresa = self.empresa_repo.get_by_id(eid)
        self.close()
        return empresa

    def close(self):
        self.empresa_repo.conn.close()

    def dispose(self):
        self.empresa_repo.conn.commit()
        self.close()
