from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ...core.utils import clear_screen
from ...db.repositories import ticker_mapping_repo, ativos_repo

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def _render(rows):
    print(Fore.CYAN + f"{'ID':<4} {'DATA_VIG':<10} {'ANTIGO':<10} {'NOVO':<10}" + Style.RESET_ALL)
    for r in rows:
        print(f"{r['id']:<4} {r['data_vigencia']:<10} {r.get('ticker_antigo_str') or '-':<10} {r.get('ticker_novo_str') or '-':<10}")

def tela_mapping():
    while True:
        clear_screen(); title("Ticker Mapping")
        rows = ticker_mapping_repo.list(0, 200)
        _render(rows)
        print("\nComandos: [I] Incluir  [E] Editar  [D] Excluir  [Q] Voltar")
        ch = input("> ").strip().lower()
        if ch in ("q","voltar"): break
        elif ch=="i":
            print("Alguns ativos:"); 
            for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']}")
            ant = int(_input("Ticker antigo (ID)*: ") or "0")
            nov = int(_input("Ticker novo (ID)*: ") or "0")
            data = _input("Data de vigência (YYYY-MM-DD)*: ").strip()
            ticker_mapping_repo.create({"ticker_antigo": ant, "ticker_novo": nov, "data_vigencia": data})
            print("Incluído."); pause()
        elif ch=="e":
            try: mid = int(_input("ID: ") or "0")
            except: print("ID inválido."); pause(); continue
            ant = int(_input("Ticker antigo (ID)*: ") or "0")
            nov = int(_input("Ticker novo (ID)*: ") or "0")
            data = _input("Data de vigência (YYYY-MM-DD)*: ").strip()
            ticker_mapping_repo.update(mid, {"ticker_antigo": ant, "ticker_novo": nov, "data_vigencia": data})
            print("Atualizado."); pause()
        elif ch=="d":
            try: mid = int(_input("ID: ") or "0")
            except: print("ID inválido."); pause(); continue
            if confirm("Excluir? (S/N) "): ticker_mapping_repo.delete(mid); print("Excluído.")
            pause()
        else:
            print("Comando inválido."); pause()
