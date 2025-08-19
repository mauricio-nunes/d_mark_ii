from colorama import Fore, Style
from ..widgets import header, pause
from ...services.config_service import get_prefs, set_prefs
from ...db.repositories import users_repo

def _input(t):
    return input(Fore.WHITE + t + Style.RESET_ALL)

def tela_prefs():
    pf = get_prefs()
    header("Preferências Atuais", {
        "Fonte (pyfiglet)": pf.get("figlet_font"),
        "Tema": pf.get("theme"),
        "Paginações": pf.get("page_size"),
        "DB Path": pf.get("db_path", "padrão ./data/dmarki.db"),
    })
    print("\nAlterar valores (ENTER mantém):")
    ff = _input(f"Fonte pyfiglet [{pf.get('figlet_font')}]: ").strip() or pf.get("figlet_font")
    th = _input(f"Tema (dark|light) [{pf.get('theme')}]: ").strip() or pf.get("theme")
    try:
        ps = int(_input(f"Page size padrão [{pf.get('page_size')}]: ").strip() or pf.get("page_size"))
    except Exception:
        ps = pf.get("page_size", 20)
    dbp = _input(f"Caminho do DB (opcional) [{pf.get('db_path','')}]: ").strip() or pf.get("db_path","")

    set_prefs({"figlet_font": ff, "theme": th, "page_size": ps, "db_path": dbp})
    print("\nPreferências salvas.")
    pause()

def tela_desbloqueio():
    header("Desbloquear Login")
    usr = users_repo.get_user_by_username("admin")
    if not usr:
        print("Usuário admin não encontrado."); pause(); return
    print(f"Status atual — tentativas: {usr['tentativas']} | bloqueado: {usr['bloqueado']}")
    conf = _input("Digite 'DESBLOQUEAR' para resetar tentativas/bloqueio: ").strip().upper()
    if conf != "DESBLOQUEAR":
        print("Cancelado."); pause(); return
    try:
        users_repo.reset_tentativas(usr["id"])  # ver patch abaixo se não existir
        print("Usuário desbloqueado.")
    except Exception as e:
        print(f"Erro: {e}")
    pause()

def config_loop():
    keep = True
    while keep:
        header("Configurações")
        print("1. Preferências (fonte/tema/paginação/DB path)")
        print("2. Desbloquear Login (admin)")
        print("3. Voltar")
        ch = _input("> ").strip()
        match ch:
            case "1": tela_prefs()
            case "2": tela_desbloqueio()
            case _: keep = False
