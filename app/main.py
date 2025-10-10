import os
from app.ui.splash import splash
from app.db.bootstrap import apply_migrations
from app.core.utils import ensure_dirs
from app.ui.menu import main_loop
from app.services.auth_service import login_flow


def main():
    # Transição simples
    os.system("cls" if os.name == "nt" else "clear")

    ensure_dirs()
    splash()
    apply_migrations()

    # Fluxo de login
    user = None
    while not user:
        user = login_flow()

    # Loop principal
    main_loop()


if __name__ == "__main__":
    main()
