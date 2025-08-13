from colorama import Fore, Style
from ..widgets import title, pause, confirm
from ...core.utils import clear_screen
from ...db.repositories import ativos_repo, carteiras_repo
from ...services.transacoes_service import transferir, ValidationError

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def tela_transferencia():
    clear_screen(); title("Transferência entre Carteiras")
    print(Fore.MAGENTA + "Alguns ativos:" + Style.RESET_ALL)
    for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']} - {a['nome']}")
    print(Fore.MAGENTA + "Algumas carteiras:" + Style.RESET_ALL)
    for c in carteiras_repo.list("", True, 0, 10): print(f"  {c['id']:>3} - {c['nome']}")

    data = _input("Data (YYYY-MM-DD)*: ").strip()
    ticker_id = int(_input("Ticker (ID)*: ") or "0")
    origem = int(_input("Carteira ORIGEM (ID)*: ") or "0")
    destino = int(_input("Carteira DESTINO (ID)*: ") or "0")
    qtd = _input("Quantidade*: ").strip()

    try:
        if confirm("Confirmar transferência? (S/N) "):
            tid_out, tid_in = transferir(data, ticker_id, origem, destino, qtd)
            print(f"Transferência criada. Saída #{tid_out}, Entrada #{tid_in}.")
    except ValidationError as e:
        print(f"Erro: {e}")
    pause()
