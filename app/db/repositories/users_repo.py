from ..connection import get_conn

def get_user_by_username(username: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username = ?;", (username,)).fetchone()
    conn.close()
    return row

def update_login_attempts(user_id: int, tentativas: int, bloqueado: int):
    conn = get_conn()
    conn.execute("UPDATE users SET tentativas = ?, bloqueado = ? WHERE id = ?;",
                 (tentativas, bloqueado, user_id))
    conn.commit()
    conn.close()

def update_password(user_id: int, password_hash: bytes, must_change: bool = False):
    conn = get_conn()
    conn.execute("UPDATE users SET password_hash = ?, must_change_password = ?, tentativas = 0, bloqueado = 0 WHERE id = ?;",
                 (password_hash, 1 if must_change else 0, user_id))
    conn.commit()
    conn.close()

def create_user(username: str, password_hash: bytes, must_change_password: bool = True):
    conn = get_conn()
    conn.execute(
        "INSERT INTO users(username, password_hash, must_change_password) VALUES (?, ?, ?);",
        (username, password_hash, 1 if must_change_password else 0)
    )
    conn.commit()
    conn.close()
