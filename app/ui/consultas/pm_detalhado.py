from colorama import Fore, Style
from ..widgets import title, divider, pause
from ...core.utils import clear_screen
from ...db.repositories import ativos_repo, carteiras_repo
from ...services.consultas_service import pm_detalhado_por_ativo

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def _render(rows):
    print(Fore.CYAN + f"{'DATA':<10} {'TIPO':<14} {'QTD_ORIG':>12} {'PU_ORIG':>12} {'TAXAS':>10} {'FATOR':>10} {'QTD_AJ':>12} {'PU_AJ':>12} {'Q_ACUM':>12} {'PM_ACUM':>12}" + Style.RESET_ALL)
    print("-"*132)
    for r in rows:
        print(f"{r['data']:<10} {r['tipo']:<14} {r['qtd_orig']:>12} {str(r['pu_orig'] or ''):>12} {str(r['taxas'] or ''):>10} "
              f"{r['fator']:>10} {r['qtd_aj']:>12} {str(r['pu_aj'] or ''):>12} {r['qtd_acum']:>12} {r['pm_acum']:>12}")

def tela_pm_detalhado():
    clear_screen(); title("PM detalhado por Ativo")
    print("Alguns ativos:"); 
    for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']}")
    print("Algumas carteiras:"); 
    for c in carteiras_repo.list("", True, 0, 10): print(f"  {c['id']:>3} - {c['nome']}")
    tid = int(_input("Ticker (ID)*: ") or "0")
    cid = int(_input("Carteira (ID)*: ") or "0")
    data = _input("Data de referência (YYYY-MM-DD) [ENTER = todas]: ").strip() or None

    rows = pm_detalhado_por_ativo(tid, cid, data)
    clear_screen(); title("PM detalhado"); divider()
    _render(rows)
    pause()
