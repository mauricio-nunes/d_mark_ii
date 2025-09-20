from typing import Optional, List


class EmpresasRepo:
    def __init__(self, conn=None):
        self.conn = conn

    def contar(self, texto: str = "", apenas_ativas: bool = True) -> int:
        where, params = "WHERE 1=1 ", []
        if texto:
            txt = f"%{texto.strip().lower()}%"
            where += "AND (lower(razao_social) LIKE ? OR cnpj LIKE ?) "
            params += [
                txt,
                f"%{texto.strip().replace('.','').replace('/','').replace('-','')}%",
            ]
        if apenas_ativas:
            where += "AND ativo = 1 "
        total = self.conn.execute(
            f"SELECT COUNT(*) c FROM empresas {where};", params
        ).fetchone()["c"]
        return int(total)

    def listar(
        self,
        texto: str = "",
        apenas_ativas: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> List[dict]:
        where, params = "WHERE 1=1 ", []
        if texto:
            txt = f"%{texto.strip().lower()}%"
            where += "AND (lower(razao_social) LIKE ? OR cnpj LIKE ?) "
            params += [
                txt,
                f"%{texto.strip().replace('.','').replace('/','').replace('-','')}%",
            ]
        if apenas_ativas:
            where += "AND ativo = 1 "

        rows = self.conn.execute(
            f"""SELECT id, cnpj, razao_social, tipo_empresa, setor_atividade, ativo
                FROM empresas {where} ORDER BY razao_social ASC LIMIT ? OFFSET ?;""",
            (*params, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_by_cnpj(self, cnpj: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM empresas WHERE cnpj = ?;", (cnpj,)
        ).fetchone()
        return dict(row) if row else None

    def get_by_codigo_cvm(self, codigo_cvm: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM empresas WHERE codigo_cvm = ?;", (codigo_cvm,)
        ).fetchone()
        return dict(row) if row else None

    def get_by_id(self, eid: int) -> Optional[dict]:

        row = self.conn.execute("SELECT * FROM empresas WHERE id=?;", (eid,)).fetchone()
        return dict(row) if row else None

    def criar(self, **kwargs) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO empresas(cnpj, razao_social, setor_atividade,
                                tipo_empresa, ativo)
            VALUES (?, ?, ?, ?, 1);
        """,
            (
                kwargs["cnpj"],
                kwargs["razao_social"],
                kwargs["setor_atividade"],
                kwargs["tipo_empresa"],
            ),
        )
        nid = cur.lastrowid
        return nid

    def editar(self, eid: int, **kwargs) -> None:

        self.conn.execute(
            """
            UPDATE empresas SET cnpj=?,razao_social=?, setor_atividade=?, tipo_empresa=?, atualizado_em=datetime('now') WHERE id=?;
        """,
            (
                kwargs["cnpj"],
                kwargs["razao_social"],
                kwargs["setor_atividade"],
                kwargs["tipo_empresa"],
                eid,
            ),
        )

    def inativar(self, eid: int) -> None:
        self.conn.execute(
            "UPDATE empresas SET ativo=0, atualizado_em=datetime('now') WHERE id=?;",
            (eid,),
        )

    def reativar(self, eid: int) -> None:
        self.conn.execute(
            "UPDATE empresas SET ativo=1, atualizado_em=datetime('now') WHERE id=?;",
            (eid,),
        )
        
    def upsert_por_cnpj(self, **kwargs) -> tuple[int, int]:
        
        cur = self.conn.cursor()
        
        cur.execute(
            """
            INSERT INTO empresas(cnpj, razao_social, setor_atividade,
                                tipo_empresa, ativo)
            VALUES (?, ?, ?, ?, ?) ON CONFLICT(cnpj) DO UPDATE SET
                razao_social=excluded.razao_social,
                setor_atividade=excluded.setor_atividade,
                tipo_empresa=excluded.tipo_empresa,
                ativo=excluded.ativo,
                atualizado_em=datetime('now');
        """,
            (
                kwargs["cnpj"],
                kwargs["razao_social"],
                kwargs["setor_atividade"],
                kwargs["tipo_empresa"],
                kwargs["situacao"]
            ),
        )
        nid = cur.lastrowid
        return nid
        

