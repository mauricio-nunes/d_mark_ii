# from typing import List, Optional
# from ..connection import get_conn

# def create(ticker_id: int, data_ref: str, preco: str, qtde: str | None) -> int:
#     conn = get_conn(); cur = conn.cursor()
#     # idempotência: checa existência por (ticker, data_ref)
#     r = conn.execute("""
#         SELECT id FROM fechamentos_mensais
#          WHERE ticker=? AND data_ref=?;
#     """, (ticker_id, data_ref)).fetchone()
#     if r:
#         conn.execute("""
#             UPDATE fechamentos_mensais SET preco_fechamento=?, quantidade=?
#              WHERE id=?;
#         """, (preco, qtde, r["id"]))
#         conn.commit(); nid = r["id"]; conn.close(); return nid

#     cur.execute("""
#         INSERT INTO fechamentos_mensais(ticker, data_ref, preco_fechamento, quantidade)
#         VALUES (?, ?, ?, ?);
#     """, (ticker_id, data_ref, preco, qtde))
#     conn.commit(); nid = cur.lastrowid; conn.close(); return nid

# def list(ticker_id: int | None = None, data_ini: str | None = None, data_fim: str | None = None,
#          offset: int = 0, limit: int = 200) -> List[dict]:
#     conn = get_conn()
#     where, p = ["1=1"], []
#     if ticker_id: where.append("f.ticker=?"); p.append(ticker_id)
#     if data_ini: where.append("f.data_ref>=?"); p.append(data_ini)
#     if data_fim: where.append("f.data_ref<=?"); p.append(data_fim)

#     rows = conn.execute(f"""
#         SELECT f.id, f.data_ref, f.preco_fechamento, f.quantidade,
#                a.ticker AS ticker_str, f.ticker
#           FROM fechamentos_mensais f
#           JOIN ativos a ON a.id = f.ticker
#          WHERE {' AND '.join(where)}
#          ORDER BY f.data_ref DESC, a.ticker ASC
#          LIMIT ? OFFSET ?;
#     """, (*p, limit, offset)).fetchall()
#     conn.close(); return [dict(r) for r in rows]
