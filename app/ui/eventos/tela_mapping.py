from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ...core.utils import clear_screen
from ...services import ticker_mapping_service

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def _render(rows):
    print(Fore.CYAN + f"{'ID':<4} {'DATA_VIG':<10} {'ANTIGO':<10} {'NOVO':<10}" + Style.RESET_ALL)
    for r in rows:
        print(f"{r['id']:<4} {r['data_vigencia']:<10} {r.get('ticker_antigo') or '-':<10} {r.get('ticker_novo') or '-':<10}")

def tela_mapping():
    while True:
        clear_screen(); title("Ticker Mapping")
        rows = ticker_mapping_service.list_mappings(0, 200)
        _render(rows)
        print("\nComandos: [I] Incluir  [E] Editar  [D] Excluir  [Q] Voltar")
        ch = input("> ").strip().lower()
        if ch in ("q","voltar"): break
        elif ch=="i":
            #print("Alguns ativos:"); 
            #for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']}")
            ant = _input("Ticker antigo*: ").strip()
            nov = _input("Ticker novo*: ").strip()
            data = _input("Data de vigência (YYYY-MM-DD)*: ").strip()
            ticker_mapping_service.create_mapping({"ticker_antigo": ant, "ticker_novo": nov, "data_vigencia": data})
            print("Incluído."); pause()
        elif ch=="e":
            try: mid = int(_input("ID: ") or "0")
            except: print("ID inválido."); pause(); continue
            ant = _input("Ticker antigo: ").strip()
            nov = _input("Ticker novo: ").strip()
            data = _input("Data de vigência (YYYY-MM-DD)*: ").strip()
            ticker_mapping_service.update_mapping(mid, {"ticker_antigo": ant, "ticker_novo": nov, "data_vigencia": data})
            print("Atualizado."); pause()
        elif ch=="d":
            try: mid = int(_input("ID: ") or "0")
            except: print("ID inválido."); pause(); continue
            if confirm("Excluir? (S/N) "): ticker_mapping_service.delete_mapping(mid); print("Excluído.")
            pause()
        else:
            print("Comando inválido."); pause()
