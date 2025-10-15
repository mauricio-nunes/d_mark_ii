from ...connection import get_conn
from typing import Optional, List, Dict, Any
import json


class BalancoRepo:

    def __init__(self, conn=None):
        self.conn = conn or get_conn()

    def get_last_five_dres_by_cnpj(self, cnpj: str, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            WITH dfp_versoes AS (
                SELECT c.cnpj, c.data_referencia, MAX(c.versao) AS versao
                FROM cia_aberta_itr_controle c
                WHERE c.categoria_documento = 'DFP' AND c.cnpj = ?
                GROUP BY c.cnpj, c.data_referencia
                ),
                ult5 AS (
                SELECT dv.cnpj, dv.data_referencia, dv.versao
                FROM dfp_versoes dv
                ORDER BY dv.data_referencia DESC
                LIMIT 5
                ),
                base AS (
                SELECT
                    d.codigo_conta,
                    d.descricao_conta,
                    d.data_referencia,
                    CAST(d.valor_conta AS REAL) *
                    CASE
                        WHEN UPPER(d.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                        WHEN UPPER(d.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                        WHEN UPPER(d.escala_moeda) LIKE 'BILH%' THEN 1000000000.0
                        ELSE 1.0
                    END AS valor_ajust
                FROM cia_aberta_itr_dre d
                JOIN ult5 u
                    ON u.cnpj = d.cnpj
                AND u.data_referencia = d.data_referencia
                AND u.versao = d.versao
                WHERE d.cnpj = ? AND d.grupo = ? AND d.conta_fixa = 1
                ),
                ag AS (
                SELECT
                    codigo_conta,
                    MIN(descricao_conta) AS descricao_conta,
                    data_referencia,
                    SUM(valor_ajust) AS valor
                FROM base
                GROUP BY codigo_conta, data_referencia
                )
                SELECT
                a.codigo_conta,
                a.descricao_conta,
                JSON_GROUP_OBJECT(a.data_referencia, a.valor) AS valores_por_data
                FROM ag a
                GROUP BY a.codigo_conta
                ORDER BY a.codigo_conta;


            """,
            (cnpj, cnpj, grupo),
        ).fetchall()
        # converte para List[Dict]
        flattened: List[Dict[str, Any]] = []
        for r in rows:
            payload = json.loads(r["valores_por_data"]) if r["valores_por_data"] else {}
            item = {
                "codigo_conta": r["codigo_conta"],
                "descricao_conta": r["descricao_conta"],
            }
            item.update(payload)  # datas viram campos do dict
            flattened.append(item)
        return flattened

    def get_last_twelve_months_dres_by_cnpj(
        self, cnpj: str, grupo: str
    ) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            WITH
                -- última data do cnpj+grupo
                ultima AS (
                SELECT
                    cnpj,
                    grupo,
                    MAX(date(data_referencia)) AS data_ref
                FROM cia_aberta_itr_dre
                WHERE cnpj = ? AND grupo = ?
                ),

                -- datas alvo: atual, tri anterior (corrigido), e 31/dez do ano anterior
                datas_ref AS (
                SELECT
                    u.cnpj,
                    u.grupo,
                    u.data_ref  AS data_ref_atual,
                    CASE strftime('%m', u.data_ref)
                    WHEN '03' THEN date(strftime('%Y', u.data_ref, '-1 years') || '-03-31')
                    WHEN '06' THEN date(strftime('%Y', u.data_ref, '-1 years') || '-06-30')
                    WHEN '09' THEN date(strftime('%Y', u.data_ref, '-1 years') || '-09-30')
                    ELSE           date(strftime('%Y', u.data_ref, '-1 years') || '-12-31')
                    END AS data_ref_prev_tri,
                    date(strftime('%Y', u.data_ref, '-1 years') || '-12-31') AS data_ref_prev_ano
                FROM ultima u
                ),

                -- lista única das 3 datas-alvo
                targets AS (
                SELECT cnpj, grupo, data_ref_atual      AS data_referencia FROM datas_ref
                UNION ALL
                SELECT cnpj, grupo, data_ref_prev_tri   FROM datas_ref
                UNION ALL
                SELECT cnpj, grupo, data_ref_prev_ano   FROM datas_ref
                ),

                -- escolhe a MAIOR versão disponível para cada (cnpj, grupo, data_referencia)
                vers AS (
                SELECT
                    d.cnpj, d.grupo, d.data_referencia, MAX(d.versao) AS versao
                FROM cia_aberta_itr_dre d
                JOIN targets t
                    ON t.cnpj = d.cnpj
                AND t.grupo = d.grupo
                AND date(d.data_referencia) = t.data_referencia
                GROUP BY d.cnpj, d.grupo, d.data_referencia
                ),

                -- aplica escala só uma vez e restringe a contas fixas
                base AS (
                SELECT
                    d.cnpj,
                    d.codigo_conta,
                    d.descricao_conta,
                    d.data_referencia,
                    CAST(d.valor_conta AS REAL) *
                    CASE
                        WHEN UPPER(d.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                        WHEN UPPER(d.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                        WHEN UPPER(d.escala_moeda) LIKE 'BILH%' THEN 1000000000.0
                        ELSE 1.0
                    END AS val
                FROM cia_aberta_itr_dre d
                JOIN vers v
                    ON v.cnpj = d.cnpj
                AND v.grupo = d.grupo
                AND v.data_referencia = d.data_referencia
                AND v.versao = d.versao
                WHERE d.conta_fixa = 1
                ),

                -- agrega por conta e separa valores por data alvo
                ag AS (
                SELECT
                    b.codigo_conta,
                    MIN(b.descricao_conta) AS descricao_conta,
                    SUM(CASE WHEN b.data_referencia = (SELECT data_ref_atual FROM datas_ref)   THEN b.val END) AS val_atual,
                    SUM(CASE WHEN b.data_referencia = (SELECT data_ref_prev_tri FROM datas_ref) THEN b.val END) AS val_prev_tri,
                    SUM(CASE WHEN b.data_referencia = (SELECT data_ref_prev_ano FROM datas_ref) THEN b.val END) AS val_prev_ano
                FROM base b
                GROUP BY b.codigo_conta
                )

                SELECT
                (SELECT cnpj FROM ultima) AS cnpj,
                a.codigo_conta,
                a.descricao_conta,
                (SELECT data_ref FROM ultima) AS data_ref,
                CASE
                    WHEN strftime('%m', (SELECT data_ref FROM ultima)) = '12'
                    THEN COALESCE(a.val_atual, 0)
                    ELSE
                    COALESCE(a.val_atual, 0) + COALESCE(a.val_prev_ano, 0) - COALESCE(a.val_prev_tri, 0)
                END AS valor_12_meses,
                JSON_OBJECT(
                    (SELECT data_ref FROM ultima),
                    CASE
                    WHEN strftime('%m', (SELECT data_ref FROM ultima)) = '12'
                        THEN COALESCE(a.val_atual, 0)
                    ELSE
                        COALESCE(a.val_atual, 0) + COALESCE(a.val_prev_ano, 0) - COALESCE(a.val_prev_tri, 0)
                    END
                ) AS json_flat
                FROM ag a
                ORDER BY a.codigo_conta;

            """,
            (cnpj, grupo),
        ).fetchall()

        flattened: List[Dict[str, Any]] = []
        for r in rows:
            # r é um sqlite3.Row -> acessar por nome de coluna
            codigo = r["codigo_conta"]
            jf = r["json_flat"]  # ex.: '{"2024-12-31": 123.45}'
            data_val = (
                json.loads(jf) if jf else {}
            )  # dict com UMA chave (a data_ref mais recente)
            # monta um dict com codigo_conta + a(s) data(s) como coluna(s)
            item = {"codigo_conta": codigo, "descricao_conta": r["descricao_conta"]}
            # garante tipo float nos valores
            for k, v in data_val.items():
                item[k] = float(v) if v is not None else None
            flattened.append(item)

        return flattened

    def get_last_five_bpas_by_cnpj(self, cnpj: str, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            WITH dfp_versoes AS (
                SELECT c.cnpj, c.data_referencia, MAX(c.versao) AS versao
                FROM cia_aberta_itr_controle c
                WHERE c.categoria_documento = 'DFP' AND c.cnpj = ?
                GROUP BY c.cnpj, c.data_referencia
                ),
                ult5 AS (
                SELECT dv.cnpj, dv.data_referencia, dv.versao
                FROM dfp_versoes dv
                ORDER BY dv.data_referencia DESC
                LIMIT 5
                ),
                base AS (
                SELECT
                    d.codigo_conta,
                    d.descricao_conta,
                    d.data_referencia,
                    CAST(d.valor_conta AS REAL) *
                    CASE
                        WHEN UPPER(d.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                        WHEN UPPER(d.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                        WHEN UPPER(d.escala_moeda) LIKE 'BILH%' THEN 1000000000.0
                        ELSE 1.0
                    END AS valor_ajust
                FROM cia_aberta_itr_bpa d
                JOIN ult5 u
                    ON u.cnpj = d.cnpj
                AND u.data_referencia = d.data_referencia
                AND u.versao = d.versao
                WHERE d.cnpj = ? AND d.grupo = ? AND d.conta_fixa = 1
                ),
                ag AS (
                SELECT
                    codigo_conta,
                    MIN(descricao_conta) AS descricao_conta,
                    data_referencia,
                    SUM(valor_ajust) AS valor
                FROM base
                GROUP BY codigo_conta, data_referencia
                )
                SELECT
                a.codigo_conta,
                a.descricao_conta,
                JSON_GROUP_OBJECT(a.data_referencia, a.valor) AS valores_por_data
                FROM ag a
                GROUP BY a.codigo_conta
                ORDER BY a.codigo_conta;

            """,
            (cnpj, cnpj, grupo),
        ).fetchall()
        # converte para List[Dict]
        flattened: List[Dict[str, Any]] = []
        for r in rows:
            payload = json.loads(r["valores_por_data"]) if r["valores_por_data"] else {}
            item = {
                "codigo_conta": r["codigo_conta"],
                "descricao_conta": r["descricao_conta"],
            }
            item.update(payload)  # datas viram campos do dict
            flattened.append(item)
        return flattened

    def get_last_five_bpps_by_cnpj(self, cnpj: str, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            WITH dfp_versoes AS (
                SELECT c.cnpj, c.data_referencia, MAX(c.versao) AS versao
                FROM cia_aberta_itr_controle c
                WHERE c.categoria_documento = 'DFP' AND c.cnpj = ?
                GROUP BY c.cnpj, c.data_referencia
                ),
                ult5 AS (
                SELECT dv.cnpj, dv.data_referencia, dv.versao
                FROM dfp_versoes dv
                ORDER BY dv.data_referencia DESC
                LIMIT 5
                ),
                base AS (
                SELECT
                    d.codigo_conta,
                    d.descricao_conta,
                    d.data_referencia,
                    CAST(d.valor_conta AS REAL) *
                    CASE
                        WHEN UPPER(d.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                        WHEN UPPER(d.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                        WHEN UPPER(d.escala_moeda) LIKE 'BILH%' THEN 1000000000.0
                        ELSE 1.0
                    END AS valor_ajust
                FROM cia_aberta_itr_bpp d
                JOIN ult5 u
                    ON u.cnpj = d.cnpj
                AND u.data_referencia = d.data_referencia
                AND u.versao = d.versao
                WHERE d.cnpj = ? AND d.grupo = ? AND d.conta_fixa = 1
                ),
                ag AS (
                SELECT
                    codigo_conta,
                    MIN(descricao_conta) AS descricao_conta,
                    data_referencia,
                    SUM(valor_ajust) AS valor
                FROM base
                GROUP BY codigo_conta, data_referencia
                )
                SELECT
                a.codigo_conta,
                a.descricao_conta,
                JSON_GROUP_OBJECT(a.data_referencia, a.valor) AS valores_por_data
                FROM ag a
                GROUP BY a.codigo_conta
                ORDER BY a.codigo_conta;

            """,
            (cnpj, cnpj, grupo),
        ).fetchall()
        # converte para List[Dict]
        flattened: List[Dict[str, Any]] = []
        for r in rows:
            payload = json.loads(r["valores_por_data"]) if r["valores_por_data"] else {}
            item = {
                "codigo_conta": r["codigo_conta"],
                "descricao_conta": r["descricao_conta"],
            }
            item.update(payload)  # datas viram campos do dict
            flattened.append(item)
        return flattened

    def get_last_bpp_by_cnpj(self, cnpj: str, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            WITH latest AS (
                /* Última data do ITR para o CNPJ e maior versão nessa data */
                SELECT
                    c.cnpj,
                    date(c.data_referencia) AS data_ref,
                    MAX(c.versao)           AS versao
                FROM cia_aberta_itr_controle c
                WHERE c.categoria_documento = 'ITR'
                    AND c.cnpj = ?
                    AND date(c.data_referencia) = (
                    SELECT MAX(date(c2.data_referencia))
                    FROM cia_aberta_itr_controle c2
                    WHERE c2.categoria_documento = 'ITR'
                        AND c2.cnpj = c.cnpj
                    )
                GROUP BY c.cnpj, date(c.data_referencia)
                ),
                base AS (
                SELECT
                    p.cnpj,
                    p.grupo,
                    p.codigo_conta,
                    p.descricao_conta,
                    date(p.data_referencia) AS data_ref,
                    CAST(p.valor_conta AS REAL) *
                    CASE
                        WHEN UPPER(p.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                        WHEN UPPER(p.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                        WHEN UPPER(p.escala_moeda) LIKE 'BILH%'      THEN 1000000000.0
                        ELSE 1.0
                    END AS val
                FROM cia_aberta_itr_bpp p
                JOIN latest l
                    ON l.cnpj = p.cnpj
                AND date(p.data_referencia) = l.data_ref
                AND p.versao = l.versao
                WHERE p.grupo = ?
                    AND p.conta_fixa = 1
                ),
                agg AS (
                SELECT
                    codigo_conta,
                    /* se houver variações pontuais de texto por versão, fixamos uma canônica */
                    MIN(descricao_conta) AS descricao_conta,
                    data_ref,
                    SUM(val) AS valor
                FROM base
                GROUP BY codigo_conta, data_ref
                )
                SELECT
                a.codigo_conta,
                a.descricao_conta,
                a.data_ref,
                a.valor,
                JSON_OBJECT(a.data_ref, a.valor) AS json_flat
                FROM agg a
                ORDER BY a.codigo_conta;


            """,
            (cnpj, grupo),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            payload = json.loads(r["json_flat"]) if r["json_flat"] else {}
            item = {
                "codigo_conta": r["codigo_conta"],
                "descricao_conta": r["descricao_conta"],
            }
            for k, v in payload.items():
                item[k] = float(v) if v is not None else None
            out.append(item)
        return out

    def get_last_bpa_by_cnpj(self, cnpj: str, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
             WITH latest AS (
                /* Última data do ITR para o CNPJ e maior versão nessa data */
                SELECT
                    c.cnpj,
                    date(c.data_referencia) AS data_ref,
                    MAX(c.versao)           AS versao
                FROM cia_aberta_itr_controle c
                WHERE c.categoria_documento = 'ITR'
                    AND c.cnpj = ?
                    AND date(c.data_referencia) = (
                    SELECT MAX(date(c2.data_referencia))
                    FROM cia_aberta_itr_controle c2
                    WHERE c2.categoria_documento = 'ITR'
                        AND c2.cnpj = c.cnpj
                    )
                GROUP BY c.cnpj, date(c.data_referencia)
                ),
                base AS (
                SELECT
                    p.cnpj,
                    p.grupo,
                    p.codigo_conta,
                    p.descricao_conta,
                    date(p.data_referencia) AS data_ref,
                    CAST(p.valor_conta AS REAL) *
                    CASE
                        WHEN UPPER(p.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                        WHEN UPPER(p.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                        WHEN UPPER(p.escala_moeda) LIKE 'BILH%'      THEN 1000000000.0
                        ELSE 1.0
                    END AS val
                FROM cia_aberta_itr_bpa p
                JOIN latest l
                    ON l.cnpj = p.cnpj
                AND date(p.data_referencia) = l.data_ref
                AND p.versao = l.versao
                WHERE p.grupo = ?
                    AND p.conta_fixa = 1
                ),
                agg AS (
                SELECT
                    codigo_conta,
                    /* se houver variações pontuais de texto por versão, fixamos uma canônica */
                    MIN(descricao_conta) AS descricao_conta,
                    data_ref,
                    SUM(val) AS valor
                FROM base
                GROUP BY codigo_conta, data_ref
                )
                SELECT
                a.codigo_conta,
                a.descricao_conta,
                a.data_ref,
                a.valor,
                JSON_OBJECT(a.data_ref, a.valor) AS json_flat
                FROM agg a
                ORDER BY a.codigo_conta;

            """,
            (cnpj, grupo),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            payload = json.loads(r["json_flat"]) if r["json_flat"] else {}
            item = {
                "codigo_conta": r["codigo_conta"],
                "descricao_conta": r["descricao_conta"],
            }
            for k, v in payload.items():
                item[k] = float(v) if v is not None else None
            out.append(item)
        return out
