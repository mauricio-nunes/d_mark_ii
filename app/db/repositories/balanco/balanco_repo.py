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
                    WHERE c.categoria_documento = 'DFP'
                        AND c.cnpj = ?
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
                        d.data_referencia,
                        /* aplica escala */
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
                    WHERE d.cnpj = ? AND d.grupo = ?
                    )
                    SELECT
                    b.codigo_conta,
                    /* JSON com chaves = datas e valores = somatórios */
                    JSON_OBJECT(
                        /* agrupa e transforma cada (data, valor) em par chave/valor */
                        
                        /* D5 */
                        (SELECT u5.data_referencia FROM ult5 u5 ORDER BY u5.data_referencia DESC LIMIT 1 OFFSET 4),
                        (SELECT IFNULL(SUM(b6.valor_ajust),0.0) FROM base b6
                        WHERE b6.codigo_conta = b.codigo_conta
                            AND b6.data_referencia = (SELECT u5.data_referencia FROM ult5 u5 ORDER BY u5.data_referencia DESC LIMIT 1 OFFSET 4)),
                        
                        /* D4 */
                        (SELECT u4.data_referencia FROM ult5 u4 ORDER BY u4.data_referencia DESC LIMIT 1 OFFSET 3),
                        (SELECT IFNULL(SUM(b5.valor_ajust),0.0) FROM base b5
                        WHERE b5.codigo_conta = b.codigo_conta
                            AND b5.data_referencia = (SELECT u4.data_referencia FROM ult5 u4 ORDER BY u4.data_referencia DESC LIMIT 1 OFFSET 3)),
                        
                        /* D3 */
                        (SELECT u3.data_referencia FROM ult5 u3 ORDER BY u3.data_referencia DESC LIMIT 1 OFFSET 2),
                        (SELECT IFNULL(SUM(b4.valor_ajust),0.0) FROM base b4
                        WHERE b4.codigo_conta = b.codigo_conta
                            AND b4.data_referencia = (SELECT u3.data_referencia FROM ult5 u3 ORDER BY u3.data_referencia DESC LIMIT 1 OFFSET 2)),
                        
                        /* D2 */
                        (SELECT u2.data_referencia FROM ult5 u2 ORDER BY u2.data_referencia DESC LIMIT 1 OFFSET 1),
                        (SELECT IFNULL(SUM(b3.valor_ajust),0.0) FROM base b3
                        WHERE b3.codigo_conta = b.codigo_conta
                            AND b3.data_referencia = (SELECT u2.data_referencia FROM ult5 u2 ORDER BY u2.data_referencia DESC LIMIT 1 OFFSET 1)),
                            
                            
                        /* D1 */
                        (SELECT u1.data_referencia FROM ult5 u1 ORDER BY u1.data_referencia DESC LIMIT 1 OFFSET 0),
                        (SELECT IFNULL(SUM(b2.valor_ajust),0.0) FROM base b2
                        WHERE b2.codigo_conta = b.codigo_conta
                            AND b2.data_referencia = (SELECT u1.data_referencia FROM ult5 u1 ORDER BY u1.data_referencia DESC LIMIT 1 OFFSET 0))
                       
                    ) AS valores_por_data
                    FROM base b
                    GROUP BY b.codigo_conta
                    ORDER BY b.codigo_conta;

            """,
            (cnpj,cnpj,grupo)
        ).fetchall()
        # converte para List[Dict]
        flattened: List[Dict[str, Any]] = []
        for r in rows:
            payload = json.loads(r["valores_por_data"]) if r["valores_por_data"] else {}
            item = {"codigo_conta": r["codigo_conta"]}
            item.update(payload)  # datas viram campos do dict
            flattened.append(item)
        return flattened

    def get_last_twelve_months_dres_by_cnpj(self, cnpj: str, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            WITH
                ultima AS (
                SELECT
                    cnpj,
                    grupo,
                    MAX(date(data_referencia)) AS data_ref
                FROM cia_aberta_itr_dre
                WHERE cnpj = ?            -- 1) CNPJ
                    AND grupo = ?           -- 2) Grupo (ex.: 'DF Individual')
                ),
                ult_vers AS (
                SELECT d.cnpj, d.grupo, d.data_referencia, MAX(d.versao) AS versao
                FROM cia_aberta_itr_dre d
                JOIN ultima u
                    ON u.cnpj = d.cnpj
                AND u.grupo = d.grupo
                AND date(d.data_referencia) = u.data_ref
                GROUP BY d.cnpj, d.grupo, d.data_referencia
                ),
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
                prev_tri_vers AS (
                SELECT d.cnpj, d.grupo, d.data_referencia, MAX(d.versao) AS versao
                FROM cia_aberta_itr_dre d
                JOIN datas_ref r
                    ON r.cnpj = d.cnpj
                AND r.grupo = d.grupo
                AND date(d.data_referencia) = r.data_ref_prev_tri
                GROUP BY d.cnpj, d.grupo, d.data_referencia
                ),
                prev_ano_vers AS (
                SELECT d.cnpj, d.grupo, d.data_referencia, MAX(d.versao) AS versao
                FROM cia_aberta_itr_dre d
                JOIN datas_ref r
                    ON r.cnpj = d.cnpj
                AND r.grupo = d.grupo
                AND date(d.data_referencia) = r.data_ref_prev_ano
                GROUP BY d.cnpj, d.grupo, d.data_referencia
                ),
                ytd_atual AS (
                SELECT
                    d.cnpj,
                    d.codigo_conta,
                    CAST(d.valor_conta AS REAL) *
                    CASE
                        WHEN UPPER(d.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                        WHEN UPPER(d.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                        WHEN UPPER(d.escala_moeda) LIKE 'BILH%' THEN 1000000000.0
                        ELSE 1.0
                    END AS val
                FROM cia_aberta_itr_dre d
                JOIN ult_vers u
                    ON u.cnpj = d.cnpj
                AND u.grupo = d.grupo
                AND d.data_referencia = u.data_referencia
                AND d.versao = u.versao
                ),
                ytd_prev_tri AS (
                SELECT
                    d.cnpj,
                    d.codigo_conta,
                    CAST(d.valor_conta AS REAL) *
                    CASE
                        WHEN UPPER(d.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                        WHEN UPPER(d.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                        WHEN UPPER(d.escala_moeda) LIKE 'BILH%' THEN 1000000000.0
                        ELSE 1.0
                    END AS val
                FROM cia_aberta_itr_dre d
                JOIN prev_tri_vers p
                    ON p.cnpj = d.cnpj
                AND p.grupo = d.grupo
                AND d.data_referencia = p.data_referencia
                AND d.versao = p.versao
                ),
                ano_prev AS (
                SELECT
                    d.cnpj,
                    d.codigo_conta,
                    CAST(d.valor_conta AS REAL) *
                    CASE
                        WHEN UPPER(d.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                        WHEN UPPER(d.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                        WHEN UPPER(d.escala_moeda) LIKE 'BILH%' THEN 1000000000.0
                        ELSE 1.0
                    END AS val
                FROM cia_aberta_itr_dre d
                JOIN prev_ano_vers p
                    ON p.cnpj = d.cnpj
                AND p.grupo = d.grupo
                AND d.data_referencia = p.data_referencia
                AND d.versao = p.versao
                ),
                final AS (
                SELECT
                    a.cnpj,
                    a.codigo_conta,
                    /* data de referência mais recente (a mesma para todos de 'final') */
                    (SELECT data_ref FROM ultima) AS data_ref,
                    CASE
                    WHEN strftime('%m', (SELECT data_ref FROM ultima)) = '12'
                        THEN SUM(a.val)
                    ELSE
                        SUM(a.val) + COALESCE(SUM(ap.val), 0) - COALESCE(SUM(pt.val), 0)
                    END AS valor_12_meses
                FROM ytd_atual a
                LEFT JOIN ytd_prev_tri pt
                    ON pt.cnpj = a.cnpj AND pt.codigo_conta = a.codigo_conta
                LEFT JOIN ano_prev ap
                    ON ap.cnpj = a.cnpj AND ap.codigo_conta = a.codigo_conta
                GROUP BY a.cnpj, a.codigo_conta
                )
                SELECT
                f.cnpj,
                f.codigo_conta,
                f.data_ref,            -- opcional: útil para debug
                f.valor_12_meses,      -- opcional: valor em coluna
                JSON_OBJECT(f.data_ref, f.valor_12_meses) AS json_flat
                FROM final f
                ORDER BY f.codigo_conta;

            """ , (cnpj,grupo)
        ).fetchall()
        
        flattened: List[Dict[str, Any]] = []
        for r in rows:
            # r é um sqlite3.Row -> acessar por nome de coluna
            codigo = r["codigo_conta"]
            jf = r["json_flat"]               # ex.: '{"2024-12-31": 123.45}'
            data_val = json.loads(jf) if jf else {}   # dict com UMA chave (a data_ref mais recente)
            # monta um dict com codigo_conta + a(s) data(s) como coluna(s)
            item = {"codigo_conta": codigo}
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
                    WHERE c.categoria_documento = 'DFP'
                        AND c.cnpj = ?
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
                        d.data_referencia,
                        /* aplica escala */
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
                    WHERE d.cnpj = ? AND d.grupo = ?
                    )
                    SELECT
                    b.codigo_conta,
                    /* JSON com chaves = datas e valores = somatórios */
                    JSON_OBJECT(
                        /* agrupa e transforma cada (data, valor) em par chave/valor */
                        
                        /* D5 */
                        (SELECT u5.data_referencia FROM ult5 u5 ORDER BY u5.data_referencia DESC LIMIT 1 OFFSET 4),
                        (SELECT IFNULL(SUM(b6.valor_ajust),0.0) FROM base b6
                        WHERE b6.codigo_conta = b.codigo_conta
                            AND b6.data_referencia = (SELECT u5.data_referencia FROM ult5 u5 ORDER BY u5.data_referencia DESC LIMIT 1 OFFSET 4)),
                        
                        /* D4 */
                        (SELECT u4.data_referencia FROM ult5 u4 ORDER BY u4.data_referencia DESC LIMIT 1 OFFSET 3),
                        (SELECT IFNULL(SUM(b5.valor_ajust),0.0) FROM base b5
                        WHERE b5.codigo_conta = b.codigo_conta
                            AND b5.data_referencia = (SELECT u4.data_referencia FROM ult5 u4 ORDER BY u4.data_referencia DESC LIMIT 1 OFFSET 3)),
                        
                        /* D3 */
                        (SELECT u3.data_referencia FROM ult5 u3 ORDER BY u3.data_referencia DESC LIMIT 1 OFFSET 2),
                        (SELECT IFNULL(SUM(b4.valor_ajust),0.0) FROM base b4
                        WHERE b4.codigo_conta = b.codigo_conta
                            AND b4.data_referencia = (SELECT u3.data_referencia FROM ult5 u3 ORDER BY u3.data_referencia DESC LIMIT 1 OFFSET 2)),
                        
                        /* D2 */
                        (SELECT u2.data_referencia FROM ult5 u2 ORDER BY u2.data_referencia DESC LIMIT 1 OFFSET 1),
                        (SELECT IFNULL(SUM(b3.valor_ajust),0.0) FROM base b3
                        WHERE b3.codigo_conta = b.codigo_conta
                            AND b3.data_referencia = (SELECT u2.data_referencia FROM ult5 u2 ORDER BY u2.data_referencia DESC LIMIT 1 OFFSET 1)),
                            
                            
                        /* D1 */
                        (SELECT u1.data_referencia FROM ult5 u1 ORDER BY u1.data_referencia DESC LIMIT 1 OFFSET 0),
                        (SELECT IFNULL(SUM(b2.valor_ajust),0.0) FROM base b2
                        WHERE b2.codigo_conta = b.codigo_conta
                            AND b2.data_referencia = (SELECT u1.data_referencia FROM ult5 u1 ORDER BY u1.data_referencia DESC LIMIT 1 OFFSET 0))
                       
                    ) AS valores_por_data
                    FROM base b
                    GROUP BY b.codigo_conta
                    ORDER BY b.codigo_conta;

            """,
            (cnpj,cnpj,grupo)
        ).fetchall()
        # converte para List[Dict]
        flattened: List[Dict[str, Any]] = []
        for r in rows:
            payload = json.loads(r["valores_por_data"]) if r["valores_por_data"] else {}
            item = {"codigo_conta": r["codigo_conta"]}
            item.update(payload)  # datas viram campos do dict
            flattened.append(item)
        return flattened
    
    def get_last_five_bpps_by_cnpj(self, cnpj: str, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            WITH dfp_versoes AS (
                    SELECT c.cnpj, c.data_referencia, MAX(c.versao) AS versao
                    FROM cia_aberta_itr_controle c
                    WHERE c.categoria_documento = 'DFP'
                        AND c.cnpj = ?
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
                        d.data_referencia,
                        /* aplica escala */
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
                    WHERE d.cnpj = ? AND d.grupo = ?
                    )
                    SELECT
                    b.codigo_conta,
                    /* JSON com chaves = datas e valores = somatórios */
                    JSON_OBJECT(
                        /* agrupa e transforma cada (data, valor) em par chave/valor */
                        
                        /* D5 */
                        (SELECT u5.data_referencia FROM ult5 u5 ORDER BY u5.data_referencia DESC LIMIT 1 OFFSET 4),
                        (SELECT IFNULL(SUM(b6.valor_ajust),0.0) FROM base b6
                        WHERE b6.codigo_conta = b.codigo_conta
                            AND b6.data_referencia = (SELECT u5.data_referencia FROM ult5 u5 ORDER BY u5.data_referencia DESC LIMIT 1 OFFSET 4)),
                        
                        /* D4 */
                        (SELECT u4.data_referencia FROM ult5 u4 ORDER BY u4.data_referencia DESC LIMIT 1 OFFSET 3),
                        (SELECT IFNULL(SUM(b5.valor_ajust),0.0) FROM base b5
                        WHERE b5.codigo_conta = b.codigo_conta
                            AND b5.data_referencia = (SELECT u4.data_referencia FROM ult5 u4 ORDER BY u4.data_referencia DESC LIMIT 1 OFFSET 3)),
                        
                        /* D3 */
                        (SELECT u3.data_referencia FROM ult5 u3 ORDER BY u3.data_referencia DESC LIMIT 1 OFFSET 2),
                        (SELECT IFNULL(SUM(b4.valor_ajust),0.0) FROM base b4
                        WHERE b4.codigo_conta = b.codigo_conta
                            AND b4.data_referencia = (SELECT u3.data_referencia FROM ult5 u3 ORDER BY u3.data_referencia DESC LIMIT 1 OFFSET 2)),
                        
                        /* D2 */
                        (SELECT u2.data_referencia FROM ult5 u2 ORDER BY u2.data_referencia DESC LIMIT 1 OFFSET 1),
                        (SELECT IFNULL(SUM(b3.valor_ajust),0.0) FROM base b3
                        WHERE b3.codigo_conta = b.codigo_conta
                            AND b3.data_referencia = (SELECT u2.data_referencia FROM ult5 u2 ORDER BY u2.data_referencia DESC LIMIT 1 OFFSET 1)),
                            
                            
                        /* D1 */
                        (SELECT u1.data_referencia FROM ult5 u1 ORDER BY u1.data_referencia DESC LIMIT 1 OFFSET 0),
                        (SELECT IFNULL(SUM(b2.valor_ajust),0.0) FROM base b2
                        WHERE b2.codigo_conta = b.codigo_conta
                            AND b2.data_referencia = (SELECT u1.data_referencia FROM ult5 u1 ORDER BY u1.data_referencia DESC LIMIT 1 OFFSET 0))
                       
                    ) AS valores_por_data
                    FROM base b
                    GROUP BY b.codigo_conta
                    ORDER BY b.codigo_conta;

            """,
            (cnpj,cnpj,grupo)
        ).fetchall()
        # converte para List[Dict]
        flattened: List[Dict[str, Any]] = []
        for r in rows:
            payload = json.loads(r["valores_por_data"]) if r["valores_por_data"] else {}
            item = {"codigo_conta": r["codigo_conta"]}
            item.update(payload)  # datas viram campos do dict
            flattened.append(item)
        return flattened
    
    def get_last_bpp_by_cnpj(self, cnpj: str, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            WITH
            ult AS (
            /* Última data de ITR no controle para o CNPJ */
            SELECT c.cnpj, MAX(date(c.data_referencia)) AS data_ref
            FROM cia_aberta_itr_controle c
            WHERE c.categoria_documento = 'ITR'
                AND c.cnpj = ?
            ),
            vers AS (
            /* Maior versão do ITR nessa data */
            SELECT c.cnpj,
                    date(c.data_referencia) AS data_referencia,
                    MAX(c.versao) AS versao
            FROM cia_aberta_itr_controle c
            JOIN ult u
                ON u.cnpj = c.cnpj
            AND date(c.data_referencia) = u.data_ref
            WHERE c.categoria_documento = 'ITR'
                AND c.cnpj = ?
            GROUP BY c.cnpj, date(c.data_referencia)
            ),
            base AS (
            SELECT
                p.cnpj,
                p.grupo,
                p.codigo_conta,
                date(p.data_referencia) AS data_ref,
                CAST(p.valor_conta AS REAL) *
                CASE
                    WHEN UPPER(p.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                    WHEN UPPER(p.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                    WHEN UPPER(p.escala_moeda) LIKE 'BILH%'      THEN 1000000000.0
                    ELSE 1.0
                END AS val
            FROM cia_aberta_itr_bpp p
            JOIN ult  u ON u.cnpj = p.cnpj AND date(p.data_referencia) = u.data_ref
            JOIN vers v ON v.cnpj = p.cnpj AND date(p.data_referencia) = v.data_referencia AND p.versao = v.versao
            WHERE p.grupo = ?
            ),
            agg AS (
            SELECT
                codigo_conta,
                data_ref,
                SUM(val) AS valor
            FROM base
            GROUP BY codigo_conta, data_ref
            )
            SELECT
            a.codigo_conta,
            a.data_ref,                 -- opcional (debug)
            a.valor,                    -- opcional (coluna numérica)
            JSON_OBJECT(a.data_ref, a.valor) AS json_flat
            FROM agg a
            ORDER BY a.codigo_conta;

            """,
            (cnpj,cnpj,grupo)
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            payload = json.loads(r["json_flat"]) if r["json_flat"] else {}
            item = {"codigo_conta": r["codigo_conta"]}
            for k, v in payload.items():
                item[k] = float(v) if v is not None else None
            out.append(item)
        return out
    
    def get_last_bpa_by_cnpj(self, cnpj: str, grupo: str) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            WITH
            ult AS (
            /* Última data de ITR no controle para o CNPJ */
            SELECT c.cnpj, MAX(date(c.data_referencia)) AS data_ref
            FROM cia_aberta_itr_controle c
            WHERE c.categoria_documento = 'ITR'
                AND c.cnpj = ?
            ),
            vers AS (
            /* Maior versão do ITR nessa data */
            SELECT c.cnpj,
                    date(c.data_referencia) AS data_referencia,
                    MAX(c.versao) AS versao
            FROM cia_aberta_itr_controle c
            JOIN ult u
                ON u.cnpj = c.cnpj
            AND date(c.data_referencia) = u.data_ref
            WHERE c.categoria_documento = 'ITR'
                AND c.cnpj = ?
            GROUP BY c.cnpj, date(c.data_referencia)
            ),
            base AS (
            SELECT
                b.cnpj,
                b.grupo,
                b.codigo_conta,
                date(b.data_referencia) AS data_ref,
                CAST(b.valor_conta AS REAL) *
                CASE
                    WHEN UPPER(b.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
                    WHEN UPPER(b.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
                    WHEN UPPER(b.escala_moeda) LIKE 'BILH%'      THEN 1000000000.0
                    ELSE 1.0
                END AS val
            FROM cia_aberta_itr_bpa b
            JOIN ult  u ON u.cnpj = b.cnpj AND date(b.data_referencia) = u.data_ref
            JOIN vers v ON v.cnpj = b.cnpj AND date(b.data_referencia) = v.data_referencia AND b.versao = v.versao
            WHERE b.grupo = ?
            ),
            agg AS (
            SELECT
                codigo_conta,
                data_ref,
                SUM(val) AS valor
            FROM base
            GROUP BY codigo_conta, data_ref
            )
            SELECT
            a.codigo_conta,
            a.data_ref,                 -- opcional (debug)
            a.valor,                    -- opcional (coluna numérica)
            JSON_OBJECT(a.data_ref, a.valor) AS json_flat
            FROM agg a
            ORDER BY a.codigo_conta;

            """,
            (cnpj,cnpj,grupo)
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            payload = json.loads(r["json_flat"]) if r["json_flat"] else {}
            item = {"codigo_conta": r["codigo_conta"]}
            for k, v in payload.items():
                item[k] = float(v) if v is not None else None
            out.append(item)
        return out    