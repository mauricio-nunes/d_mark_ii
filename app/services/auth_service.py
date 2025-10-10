from app.core.utils import clear_screen
from app.ui.forms import (
    rich_input,
    rich_label_error,
    rich_getpass,
    rich_label_success,
    rich_label_warning,
)
from ..db.repositories.usuarios.usuario_repo import UsuarioRepo
from ..core.security import check_password, hash_password
from ..ui.widgets import title, divider
from ..db.connection import get_conn

import time

MAX_ATTEMPTS = 5


def login_flow() -> dict | None:
    """
    Retorna o registro do usuário logado (dict-like Row) ou None.
    """
    clear_screen()
    divider()
    title("Login")
    divider()
    conn = get_conn()
    user_repo = UsuarioRepo(conn)
    username = rich_input("Usuário:").strip()
    user = user_repo.get_user_by_username(username)
    if not user:
        rich_label_error("Usuário ou senha inválidos.")
        conn.close()
        time.sleep(1)
        clear_screen()
        return None
    if user["bloqueado"]:
        rich_label_error("Usuário bloqueado.")
        conn.close()
        time.sleep(1)
        clear_screen()
        return None

    raw = rich_getpass("Senha:").strip()

    if check_password(raw, user["password_hash"]):
        # reset tentativas
        user_repo.update_login_attempts(user["id"], 0, 0)
        if user["must_change_password"]:
            rich_label_warning("É necessário trocar a senha no primeiro acesso.")
            new1 = rich_getpass("Nova senha: ")
            new2 = rich_getpass("Confirme a nova senha: ")
            if new1 != new2 or not new1:
                rich_label_error("Senhas não conferem.")
                time.sleep(1)
                clear_screen()
                conn.close()
                return None
            user_repo.update_password(
                user["id"], hash_password(new1), must_change=False
            )
            rich_label_success("Senha alterada com sucesso.")
            time.sleep(1)
            clear_screen()
        conn.commit()
        conn.close()
        return dict(user)
    else:
        tentativas = user["tentativas"] + 1
        bloqueado = 1 if tentativas >= MAX_ATTEMPTS else 0
        user_repo.update_login_attempts(user["id"], tentativas, bloqueado)
        if bloqueado:
            rich_label_error(
                "Senha incorreta. Usuário foi BLOQUEADO por excesso de tentativas."
            )
            time.sleep(1)
            clear_screen()
        else:
            rich_label_error(
                f"Senha incorreta. Tentativas: {tentativas}/{MAX_ATTEMPTS}."
            )
            time.sleep(1)
            clear_screen()
        conn.commit()
        conn.close()
        return None
