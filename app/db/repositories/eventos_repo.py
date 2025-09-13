from typing import List, Optional
from ..connection import get_conn

def criar(data: dict , conn=None) -> int:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO eventos(tipo,entidade_id,evento,nome, ticker_antigo, ticker_novo, data_ex, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (data["tipo"], data.get("entidade_id"), data.get("evento"), data.get("nome"), data.get("ticker_antigo"), data.get("ticker_novo"),
          data["data_ex"], data.get("observacoes","")))
    
    nid = cur.lastrowid
    return nid

def update(eid: int, data: dict) -> None:
    conn = get_conn()
    conn.execute("""
        UPDATE eventos SET tipo=?, ticker_antigo=?, ticker_novo=?, data_ex=?, num=?, den=?, observacoes=?
        WHERE id=?;
    """, (data["tipo"], data.get("ticker_antigo"), data.get("ticker_novo"), data["data_ex"],
          data.get("num"), data.get("den"), data.get("observacoes",""), eid))
    conn.commit(); conn.close()

def soft_delete(eid: int) -> None:
    conn = get_conn(); conn.execute("UPDATE eventos SET ativo=0 WHERE id=?;", (eid,))
    conn.commit(); conn.close()

def get_by_id(eid: int) -> Optional[dict]:
    conn = get_conn(); r = conn.execute("SELECT * FROM eventos WHERE id=?;", (eid,)).fetchone()
    conn.close(); return dict(r) if r else None

def list(ticker_id: int | None = None, tipo: str | None = None,
         data_ini: str | None = None, data_fim: str | None = None,
         offset: int = 0, limit: int = 50, apenas_ativos: bool = True) -> List[dict]:
    conn = get_conn()
    where, p = ["1=1"], []
    if apenas_ativos: where.append("e.ativo=1")
    if ticker_id: where.append("(e.ticker_antigo=? OR e.ticker_novo=?)"); p += [ticker_id, ticker_id]
    if tipo: where.append("e.tipo=?"); p.append(tipo)
    if data_ini: where.append("e.data_ex>=?"); p.append(data_ini)
    if data_fim: where.append("e.data_ex<=?"); p.append(data_fim)
    rows = conn.execute(f"""
        SELECT e.*,
               a1.ticker AS ticker_antigo_str, a2.ticker AS ticker_novo_str
          FROM eventos e
          LEFT JOIN ativos a1 ON a1.id = e.ticker_antigo
          LEFT JOIN ativos a2 ON a2.id = e.ticker_novo
         WHERE {' AND '.join(where)}
         ORDER BY e.data_ex ASC, e.id ASC
         LIMIT ? OFFSET ?;
    """, (*p, limit, offset)).fetchall()
    conn.close(); return [dict(r) for r in rows]
