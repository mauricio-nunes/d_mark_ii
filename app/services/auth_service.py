from ..db.repositories.usuarios.usuario_repo import UsuarioRepo
from ..core.security import check_password, hash_password
from ..ui.widgets import title
from ..db.connection import get_conn
from getpass import getpass

MAX_ATTEMPTS = 5

def login_flow() -> dict | None:
    """
    Retorna o registro do usuário logado (dict-like Row) ou None.
    """
    title("Login")
    conn = get_conn()
    user_repo = UsuarioRepo(conn)
    username = input("Usuário: ").strip()
    user = user_repo.get_user_by_username(username)
    if not user:
        print("Usuário ou senha inválidos.")
        conn.close()
        return None
    if user["bloqueado"]:
        print("Usuário bloqueado. Use Configurações > Desbloquear login.")
        conn.close()
        return None


    raw = getpass("Senha: ")

    if check_password(raw, user["password_hash"]):
        # reset tentativas
        user_repo.update_login_attempts(user["id"], 0, 0)
        if user["must_change_password"]:
            print("\nÉ necessário trocar a senha no primeiro acesso.")
            new1 = getpass("Nova senha: ")
            new2 = getpass("Confirme a nova senha: ")
            if new1 != new2 or not new1:
                print("Senhas não conferem.")
                conn.close()
                return None
            user_repo.update_password(user["id"], hash_password(new1), must_change=False)
            print("Senha alterada com sucesso.\n")
        conn.commit()
        conn.close()
        return dict(user)
    else:
        tentativas = user["tentativas"] + 1
        bloqueado = 1 if tentativas >= MAX_ATTEMPTS else 0
        user_repo.update_login_attempts(user["id"], tentativas, bloqueado)
        if bloqueado:
            print("Senha incorreta. Usuário foi BLOQUEADO por excesso de tentativas.")
        else:
            print(f"Senha incorreta. Tentativas: {tentativas}/{MAX_ATTEMPTS}.")
        conn.commit()
        conn.close()
        return None
