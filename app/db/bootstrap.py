import os
from .connection import get_conn
from ..db.repositories.usuarios.usuario_repo import UsuarioRepo 
from ..core.security import hash_password

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")

def apply_migrations():
    conn = get_conn()
    cur = conn.cursor()
    # controle simples de versões
    cur.execute("CREATE TABLE IF NOT EXISTS _migrations (name TEXT PRIMARY KEY);")
    applied = {row["name"] for row in cur.execute("SELECT name FROM _migrations;").fetchall()}

    for fname in sorted(os.listdir(MIGRATIONS_DIR)):
        if not fname.endswith(".sql"):
            continue
        if fname in applied:
            continue
        path = os.path.join(MIGRATIONS_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
        cur.executescript(sql)
        cur.execute("INSERT INTO _migrations(name) VALUES (?);", (fname,))
        

    # seed admin se não existir
    user_repo = UsuarioRepo(conn=conn)
    if user_repo.get_user_by_username("admin") is None:
        user_repo.create_user("admin", hash_password("admin"), must_change_password=True)
    conn.commit()
    conn.close()
