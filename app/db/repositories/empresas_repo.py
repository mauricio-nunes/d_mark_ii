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


# def upsert_by_cnpj(**kwargs) -> tuple[int, bool]:
#     """
#     Insert or update empresa by CNPJ.
#     Returns (id, was_inserted) where was_inserted is True for new records, False for updates.
#     """
#     cur = conn.cursor()

#     # Try to insert first

#     # Get the ID and controle_id of the updated record
#     row = conn.execute("SELECT id,controle_id FROM empresas WHERE cnpj=?;", (kwargs["cnpj"],)).fetchone()

#     # Insert if not exists
#     if row is None:
#         cur.execute("""
#             INSERT INTO empresas(cnpj, razao_social, codigo_cvm, data_constituicao, setor_atividade,
#                                     situacao, controle_acionario, tipo_empresa,categoria_registro, controle_id,
#                                     pais_origem, pais_custodia, situacao_emissor, dia_encerramento_fiscal,
#                                     mes_encerramento_fiscal, ativo)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
#         """, (kwargs["cnpj"], kwargs["razao_social"], kwargs["codigo_cvm"], kwargs.get("data_constituicao"),
#                 kwargs.get("setor_atividade"), kwargs.get("situacao"),
#                 kwargs.get("controle_acionario"), kwargs["tipo_empresa"], kwargs["categoria_registro"], kwargs.get("controle_id"),
#                 kwargs.get("pais_origem"), kwargs.get("pais_custodia"), kwargs.get("situacao_emissor"),
#                 kwargs.get("dia_encerramento_fiscal"), kwargs.get("mes_encerramento_fiscal"), kwargs.get("ativo", 1)))
#         conn.commit()
#         nid = cur.lastrowid
#         conn.close()
#         return nid, 1

#     # Update if controle_id is older
#     if int(row['controle_id']) < int(kwargs.get("controle_id", 0)):

#         cur.execute("""
#             UPDATE empresas SET razao_social=?, codigo_cvm=?, data_constituicao=?, setor_atividade=?,
#                 situacao=?, controle_acionario=?, tipo_empresa=?, categoria_registro=?, controle_id=?,
#                 pais_origem=?, pais_custodia=?, situacao_emissor=?, dia_encerramento_fiscal=?,
#                 mes_encerramento_fiscal=?, ativo=?, atualizado_em=datetime('now')
#                 WHERE cnpj=?;
#             """, (kwargs["razao_social"], kwargs["codigo_cvm"], kwargs.get("data_constituicao"),
#                     kwargs.get("setor_atividade"), kwargs.get("situacao"),
#                     kwargs.get("controle_acionario"), kwargs["tipo_empresa"], kwargs.get("categoria_registro"),
#                     kwargs.get("controle_id"), kwargs.get("pais_origem"), kwargs.get("pais_custodia"),
#                     kwargs.get("situacao_emissor"), kwargs.get("dia_encerramento_fiscal"),
#                     kwargs.get("mes_encerramento_fiscal"), kwargs.get("ativo", 1),
#                     kwargs["cnpj"]))
#         conn.commit()
#         return row['id'], 2

#     # If controle_id is not older, do nothing
#     return 0, 0
