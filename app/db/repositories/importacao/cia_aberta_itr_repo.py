from typing import Optional, List, Dict, Any
from ...connection import get_conn


class CiaAbertaItrRepo:
    """Repository para as tabelas de Itr."""

    def __init__(self, conn=None):
        self.conn = conn or get_conn()


    def get_max_version_for_period(self, cnpj: str, data_referencia: str, categoria_documento: str) -> Optional[int]:
        row = self.conn.execute(
            "SELECT max(versao) as versao FROM cia_aberta_itr_controle WHERE cnpj = ? AND data_referencia = ? AND categoria_documento = ?",
            (cnpj, data_referencia, categoria_documento)
        ).fetchone()
        # Retorna o valor do campo 'versao' ou None se não houver resultado
        return row["versao"] if row is not None else None
    
    def get_last_version_from_cnpj(self, cnpj: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            """
            SELECT max(data_referencia) as data_referencia, max(versao) as versao
            FROM cia_aberta_itr_controle
            WHERE cnpj = ?
            """,
            (cnpj,)
        ).fetchone()
        return dict(row) if row else None

    def insert_itr_controle(self, **kwargs) -> tuple[int, str]:
        """
        Retorna (affected_rows, action) onde action = 'inserted'|'updated'|'ignored'
        """
        cur = self.conn.cursor()

        try:
            cur.execute(
                """
				INSERT OR IGNORE INTO cia_aberta_itr_controle (
					cnpj, data_referencia, versao, razao_social, codigo_cvm,
					categoria_documento, codigo_documento, data_recebimento,
					link_documento, criado_em
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""",
                (
                    kwargs["cnpj"],
                    kwargs["data_referencia"],
                    kwargs["versao"],
                    kwargs.get("razao_social"),
                    kwargs.get("codigo_cvm"),
                    kwargs.get("categoria_documento"),
                    kwargs.get("codigo_documento"),
                    kwargs.get("data_recebimento"),
                    kwargs.get("link_documento"),
                    kwargs["criado_em"],
                ),
            )
            return (cur.rowcount or 0), ("inserted" if cur.rowcount == 1 else "ignored")

        except Exception as e:

            raise e

    def insert_itr_composicao_capital(self, **kwargs) -> tuple[int, str]:
        """
        Retorna (affected_rows, action) onde action = 'inserted'|'updated'|'ignored'
        """
        cur = self.conn.cursor()

        try:
            cur.execute(
                """
                INSERT OR IGNORE INTO cia_aberta_itr_composicao_capital (
                    cnpj, data_referencia, versao, razao_social,
                    qtde_acao_ordinaria, qtde_acao_preferencial, qtde_acao_total,
                    qtde_acao_ordinaria_tesouraria, qtde_acao_preferencial_tesouraria, qtde_acao_total_tesouraria
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    kwargs["cnpj"],
                    kwargs["data_referencia"],
                    kwargs["versao"],
                    kwargs["razao_social"],
                    kwargs["qtde_acao_ordinaria"],
                    kwargs["qtde_acao_preferencial"],
                    kwargs["qtde_acao_total"],
                    kwargs["qtde_acao_ordinaria_tesouraria"],
                    kwargs["qtde_acao_preferencial_tesouraria"],
                    kwargs["qtde_acao_total_tesouraria"],
                ),
            )
            return (cur.rowcount or 0), ("inserted" if cur.rowcount == 1 else "ignored")

        except Exception as e:
            raise e

    def insert_itr_dre_bal(self, table_name: str, **kwargs) -> tuple[int, str]:
        """
        Retorna (affected_rows, action) onde action = 'inserted'|'updated'|'ignored'
        """
        cur = self.conn.cursor()

        try:
            cur.execute(
                f"""
                INSERT OR IGNORE INTO {table_name} (
                    cnpj, data_referencia, versao, razao_social,
                    codigo_cvm, grupo, moeda, escala_moeda,
                    data_inicio_exercicio, data_fim_exercicio,
                    codigo_conta, descricao_conta, valor_conta,
                    conta_fixa, criado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    kwargs["cnpj"],
                    kwargs["data_referencia"],
                    kwargs["versao"],
                    kwargs["razao_social"],
                    kwargs["codigo_cvm"],
                    kwargs["grupo"],
                    kwargs["moeda"],
                    kwargs["escala_moeda"],
                    kwargs["data_inicio_exercicio"],
                    kwargs["data_fim_exercicio"],
                    kwargs["codigo_conta"],
                    kwargs["descricao_conta"],
                    kwargs["valor_conta"],
                    kwargs["conta_fixa"],
                    kwargs["criado_em"],
                ),
            )
            return (cur.rowcount or 0), ("inserted" if cur.rowcount == 1 else "ignored")

        except Exception as e:

            raise e
        
    def get_BPA_records(self, cnpj: str, data_referencia: str, versao: int, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT * FROM cia_aberta_itr_bpa
            WHERE cnpj = ? AND data_referencia = ? AND versao = ? AND grupo = ?
            """,
            (cnpj, data_referencia, versao, grupo)
        ).fetchall()
        return [dict(row) for row in rows] if rows else None
    
    def get_DRE_records(self, cnpj: str, data_referencia: str, versao: int, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT * FROM cia_aberta_itr_dre
            WHERE cnpj = ? AND data_referencia = ? AND versao = ? AND grupo = ?
            """,
            (cnpj, data_referencia, versao, grupo)
        ).fetchall()
        return [dict(row) for row in rows] if rows else None
    
    def get_BPP_records(self, cnpj: str, data_referencia: str, versao: int, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT * FROM cia_aberta_itr_bpp
            WHERE cnpj = ? AND data_referencia = ? AND versao = ? AND grupo = ?
            """,
            (cnpj, data_referencia, versao, grupo)
        ).fetchall()
        return [dict(row) for row in rows] if rows else None
    
    def get_composicao_capital_records(self, cnpj: str, data_referencia: str, versao: int) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT * FROM cia_aberta_itr_composicao_capital
            WHERE cnpj = ? AND data_referencia = ? AND versao = ?
            """,
            (cnpj, data_referencia, versao)
        ).fetchall()
        return [dict(row) for row in rows] if rows else None