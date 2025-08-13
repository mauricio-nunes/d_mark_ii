from typing import List, Optional
from ..connection import get_conn

def create(data: dict) -> int:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO transacoes(data, tipo, corretora_id, quantidade, ticker, carteira_id,
                               preco_unitario, taxas, observacoes, ativo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
    """, (data["data"], data["tipo"], data.get("corretora_id"),
          data["quantidade"], data["ticker"], data["carteira_id"],
          data.get("preco_unitario"), data.get("taxas","0"), data.get("observacoes","")))
    conn.commit(); nid = cur.lastrowid; conn.close(); return nid

def update(tid: int, data: dict) -> None:
    conn = get_conn()
    conn.execute("""
        UPDATE transacoes
           SET data=?, tipo=?, corretora_id=?, quantidade=?, ticker=?, carteira_id=?,
               preco_unitario=?, taxas=?, observacoes=?
         WHERE id=?;
    """, (data["data"], data["tipo"], data.get("corretora_id"),
          data["quantidade"], data["ticker"], data["carteira_id"],
          data.get("preco_unitario"), data.get("taxas","0"), data.get("observacoes",""), tid))
    conn.commit(); conn.close()

def soft_delete(tid: int) -> None:
    conn = get_conn()
    conn.execute("UPDATE transacoes SET ativo=0 WHERE id=?;", (tid,))
    conn.commit(); conn.close()

def get_by_id(tid: int) -> Optional[dict]:
    conn = get_conn()
    r = conn.execute("SELECT * FROM transacoes WHERE id=?;", (tid,)).fetchone()
    conn.close(); return dict(r) if r else None

def list(texto: str="", ticker_id: int|None=None, carteira_id: int|None=None,
         corretora_id: int|None=None, data_ini: str|None=None, data_fim: str|None=None,
         offset: int=0, limit: int=20, apenas_ativas: bool=True) -> List[dict]:
    conn = get_conn()
    where, p = ["1=1"], []
    if apenas_ativas: where.append("t.ativo=1")
    if texto:
        where.append("(lower(coalesce(t.observacoes,'')) LIKE ?)")
        p.append(f"%{texto.strip().lower()}%")
    if ticker_id: where.append("t.ticker=?"); p.append(ticker_id)
    if carteira_id: where.append("t.carteira_id=?"); p.append(carteira_id)
    if corretora_id: where.append("t.corretora_id=?"); p.append(corretora_id)
    if data_ini: where.append("t.data>=?"); p.append(data_ini)
    if data_fim: where.append("t.data<=?"); p.append(data_fim)

    rows = conn.execute(f"""
        SELECT t.id, t.data, t.tipo, t.quantidade, t.preco_unitario, t.taxas, t.observacoes,
               a.ticker AS ticker_str, t.ticker, t.carteira_id,
               c.nome AS carteira_str, co.nome AS corretora_str
          FROM transacoes t
          JOIN ativos a ON a.id=t.ticker
          JOIN carteiras c ON c.id=t.carteira_id
          LEFT JOIN corretoras co ON co.id=t.corretora_id
         WHERE {' AND '.join(where)}
         ORDER BY t.data ASC, t.id ASC
         LIMIT ? OFFSET ?;
    """, (*p, limit, offset)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def count(**kwargs) -> int:
    conn = get_conn()
    where, p = ["1=1"], []
    if kwargs.get("apenas_ativas", True): where.append("ativo=1")
    if kwargs.get("texto"):
        where.append("(lower(coalesce(observacoes,'')) LIKE ?)")
        p.append(f"%{kwargs['texto'].strip().lower()}%")
    if kwargs.get("ticker_id"): where.append("ticker=?"); p.append(kwargs["ticker_id"])
    if kwargs.get("carteira_id"): where.append("carteira_id=?"); p.append(kwargs["carteira_id"])
    if kwargs.get("corretora_id"): where.append("corretora_id=?"); p.append(kwargs["corretora_id"])
    if kwargs.get("data_ini"): where.append("data>=?"); p.append(kwargs["data_ini"])
    if kwargs.get("data_fim"): where.append("data<=?"); p.append(kwargs["data_fim"])
    r = conn.execute(f"SELECT COUNT(*) c FROM transacoes WHERE {' AND '.join(where)};", p).fetchone()
    conn.close(); return int(r["c"])
