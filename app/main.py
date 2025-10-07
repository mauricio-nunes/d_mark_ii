import os
from colorama import init as colorama_init
from app.ui.splash import splash
from app.db.bootstrap import apply_migrations
from app.core.utils import ensure_dirs
from app.ui.menu import main_loop
from app.services.auth_service import login_flow


def main():
	# Transição simples
	os.system("cls" if os.name == "nt" else "clear")

	colorama_init()
	ensure_dirs()
	splash()
	apply_migrations()

	# Fluxo de login
	user = None
	while not user:
		user = login_flow()

	# Transição simples
	os.system("cls" if os.name == "nt" else "clear")

	# Loop principal
	main_loop()


if __name__ == "__main__":
	main()
