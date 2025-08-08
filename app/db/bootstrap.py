import os
from .connection import get_conn

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
        conn.commit()

    # seed admin se não existir
    from ..db.repositories.users_repo import get_user_by_username, create_user
    from ..core.security import hash_password
    if get_user_by_username("admin") is None:
        create_user("admin", hash_password("admin"), must_change_password=True)

    conn.close()
