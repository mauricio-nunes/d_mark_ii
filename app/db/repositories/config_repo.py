from ..connection import get_conn

def get_value(key: str) -> str | None:
    conn = get_conn()
    r = conn.execute("SELECT valor FROM config WHERE chave=?;", (key,)).fetchone()
    conn.close(); return r["valor"] if r else None

def set_value(key: str, value: str) -> None:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO config(chave, valor) VALUES(?, ?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor;", (key, value))
    conn.commit(); conn.close()
