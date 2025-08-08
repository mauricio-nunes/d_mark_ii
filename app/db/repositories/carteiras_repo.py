from typing import Optional, List
from ..connection import get_conn

def count(texto: str = "", apenas_ativas: bool = True) -> int:
    conn = get_conn()
    where, params = "WHERE 1=1 ", []
    if texto:
        txt = f"%{texto.strip().lower()}%"
        where += "AND (lower(nome) LIKE ? OR lower(coalesce(descricao,'')) LIKE ?) "
        params += [txt, txt]
    if apenas_ativas:
        where += "AND ativo = 1 "
    total = conn.execute(f"SELECT COUNT(*) c FROM carteiras {where};", params).fetchone()["c"]
    conn.close()
    return int(total)

def list(texto: str = "", apenas_ativas: bool = True, offset: int = 0, limit: int = 20) -> List[dict]:
    conn = get_conn()
    where, params = "WHERE 1=1 ", []
    if texto:
        txt = f"%{texto.strip().lower()}%"
        where += "AND (lower(nome) LIKE ? OR lower(coalesce(descricao,'')) LIKE ?) "
        params += [txt, txt]
    if apenas_ativas:
        where += "AND ativo = 1 "
    rows = conn.execute(
        f"""SELECT id, nome, descricao, ativo, criado_em, inativado_em
            FROM carteiras {where} ORDER BY nome ASC LIMIT ? OFFSET ?;""",
        (*params, limit, offset)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_by_nome(nome: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM carteiras WHERE lower(nome)=lower(?);", (nome.strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_by_id(cid: int) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM carteiras WHERE id=?;", (cid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create(nome: str, descricao: str = "") -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO carteiras(nome, descricao, ativo) VALUES (?, ?, 1);", (nome.strip(), descricao.strip()))
    conn.commit(); new_id = cur.lastrowid; conn.close(); return new_id

def update(cid: int, nome: str, descricao: str = "") -> None:
    conn = get_conn()
    conn.execute("UPDATE carteiras SET nome=?, descricao=? WHERE id=?;", (nome.strip(), descricao.strip(), cid))
    conn.commit(); conn.close()

def inativar(cid: int) -> None:
    conn = get_conn()
    conn.execute("UPDATE carteiras SET ativo=0, inativado_em=datetime('now') WHERE id=?;", (cid,))
    conn.commit(); conn.close()

def reativar(cid: int) -> None:
    conn = get_conn()
    conn.execute("UPDATE carteiras SET ativo=1, inativado_em=NULL WHERE id=?;", (cid,))
    conn.commit(); conn.close()
