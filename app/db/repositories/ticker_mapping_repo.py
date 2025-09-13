from typing import List, Optional
from ..connection import get_conn

def create(data: dict) -> int:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO ticker_mapping(ticker_antigo, ticker_novo, data_vigencia)
        VALUES (?, ?, ?);
    """, (data["ticker_antigo"], data["ticker_novo"], data["data_vigencia"]))
    conn.commit(); nid = cur.lastrowid; conn.close(); return nid

def update(mid: int, data: dict) -> None:
    conn = get_conn()
    conn.execute("""
        UPDATE ticker_mapping SET ticker_antigo=?, ticker_novo=?, data_vigencia=? WHERE id=?;
    """, (data["ticker_antigo"], data["ticker_novo"], data["data_vigencia"], mid))
    conn.commit(); conn.close()

def delete(mid: int) -> None:
    conn = get_conn(); conn.execute("DELETE FROM ticker_mapping WHERE id=?;", (mid,))
    conn.commit(); conn.close()

def list(offset: int = 0, limit: int = 100) -> List[dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, ticker_antigo, ticker_novo, data_vigencia
          FROM ticker_mapping 
         ORDER BY data_vigencia ASC, id ASC
         LIMIT ? OFFSET ?;
    """, (limit, offset)).fetchall()
    conn.close(); return [dict(r) for r in rows]
