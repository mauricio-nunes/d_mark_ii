from typing import Optional, List, Dict, Any
from ...connection import get_conn


class UsuarioRepo:
    """Repository para a tabela de usuários."""

    def __init__(self, conn):
        self.conn = conn 

    def reset_tentativas(self, user_id: int):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE users
            SET tentativas = 0,
                bloqueado = 0
            WHERE id = ?;
        """, (user_id,))
       

    def get_user_by_username(self, username: str):
        cur = self.conn.cursor()
        row = cur.execute("SELECT * FROM users WHERE username = ?;", (username,)).fetchone()
        
        return row

    def update_login_attempts(self, user_id: int, tentativas: int, bloqueado: int):
        cur = self.conn.cursor()
        cur.execute("UPDATE users SET tentativas = ?, bloqueado = ? WHERE id = ?;",
                    (tentativas, bloqueado, user_id))
        
    def update_password(self, user_id: int, password_hash: bytes, must_change: bool = False):
        cur = self.conn.cursor()
        cur.execute("UPDATE users SET password_hash = ?, must_change_password = ?, tentativas = 0, bloqueado = 0 WHERE id = ?;",
                    (password_hash, 1 if must_change else 0, user_id))
        
    def create_user(self, username: str, password_hash: bytes, must_change_password: bool = True):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users(username, password_hash, must_change_password) VALUES (?, ?, ?);",
            (username, password_hash, 1 if must_change_password else 0)
        )
        