from typing import Optional, List
from ..connection import get_conn

def count(texto: str = "", apenas_ativos: bool = True) -> int:
    conn = get_conn()
    where, params = "WHERE 1=1 ", []
    if texto:
        txt = f"%{texto.strip().lower()}%"
        # embora aqui não tenha JOIN, já deixo os aliases para consistência
        where += "AND (lower(a.ticker) LIKE ? OR lower(a.nome) LIKE ?) "
        params += [txt, txt]
    if apenas_ativos:
        where += "AND a.ativo = 1 "
    # use alias a para manter coerência
    total = conn.execute(f"SELECT COUNT(*) c FROM ativos a {where};", params).fetchone()["c"]
    conn.close(); return int(total)

def list(texto: str = "", apenas_ativos: bool = True, offset: int = 0, limit: int = 20) -> List[dict]:
    conn = get_conn()
    where, params = "WHERE 1=1 ", []
    if texto:
        txt = f"%{texto.strip().lower()}%"
        where += "AND (lower(a.ticker) LIKE ? OR lower(a.nome) LIKE ?) "
        params += [txt, txt]
    if apenas_ativos:
        where += "AND a.ativo = 1 "  # <— aqui estava sem alias

    rows = conn.execute(
        f"""
        SELECT a.id, a.ticker, a.nome, a.classe, a.ativo,
               e.razao_social AS empresa, e.id AS empresa_id
        FROM ativos a
        LEFT JOIN empresas e ON e.id = a.empresa_id
        {where}
        ORDER BY a.ticker ASC
        LIMIT ? OFFSET ?;
        """,
        (*params, limit, offset)
    ).fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_by_ticker(ticker: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM ativos WHERE lower(ticker)=lower(?);", (ticker.strip(),)).fetchone()
    conn.close(); return dict(row) if row else None

def get_by_id(aid: int) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM ativos WHERE id=?;", (aid,)).fetchone()
    conn.close(); return dict(row) if row else None

def create(ticker: str, nome: str, classe: str, empresa_id: int | None) -> int:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO ativos(ticker, nome, classe, empresa_id, ativo) VALUES (?, ?, ?, ?, 1);",
                (ticker.strip().upper(), nome.strip(), classe, empresa_id))
    conn.commit(); nid = cur.lastrowid; conn.close(); return nid

def update(aid: int, ticker: str, nome: str, classe: str, empresa_id: int | None) -> None:
    conn = get_conn()
    conn.execute("UPDATE ativos SET ticker=?, nome=?, classe=?, empresa_id=? WHERE id=?;",
                 (ticker.strip().upper(), nome.strip(), classe, empresa_id, aid))
    conn.commit(); conn.close()

def inativar(aid: int) -> None:
    conn = get_conn()
    conn.execute("UPDATE ativos SET ativo=0 WHERE id=?;", (aid,))
    conn.commit(); conn.close()

def reativar(aid: int) -> None:
    conn = get_conn()
    conn.execute("UPDATE ativos SET ativo=1 WHERE id=?;", (aid,))
    conn.commit(); conn.close()
