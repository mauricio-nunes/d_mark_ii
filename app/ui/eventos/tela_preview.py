from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ...core.utils import clear_screen
from ...db.repositories import ativos_repo, carteiras_repo, eventos_repo
from ...services.eventos_service import posicao_ajustada_on_the_fly, aplicar_bonificacao_gerando_transacoes, aplicar_inplit_liquidacao_fracoes, ValidationError

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def tela_preview():
    clear_screen(); title("Prévia / Aplicação de Eventos")
    print("1) Pré‑visualizar posição ajustada (on‑the‑fly)")
    print("2) Aplicar BONIFICAÇÃO (gerar transações PU=0)")
    print("3) Aplicar INPLIT (liquidar frações → provento OUTROS)")
    print("4) Voltar")
    ch = _input("Selecione: ").strip()
    if ch == "1":
        print("Alguns ativos:"); 
        for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']} - {a['nome']}")
        print("Algumas carteiras:"); 
        for c in carteiras_repo.list("", True, 0, 10): print(f"  {c['id']:>3} - {c['nome']}")
        tid = int(_input("Ticker (ID)*: ") or "0")
        cid = int(_input("Carteira (ID)*: ") or "0")
        data = _input("Data de referência (YYYY-MM-DD)*: ").strip()
        q, pm = posicao_ajustada_on_the_fly(tid, cid, data)
        print(Fore.CYAN + f"\nPosição ajustada em {data}: QTD={q}  PM={pm}" + Style.RESET_ALL)
        pause()
    elif ch == "2":
        print("Eventos de BONIFICAÇÃO recentes:")
        for e in eventos_repo.list(tipo="Bonificacao", data_ini=None, data_fim=None, limit=50):
            print(f"  {e['id']:>3} - {e['data_ex']} {e.get('ticker_antigo_str')}  num/den={e.get('num')}/{e.get('den')}")
        try:
            eid = int(_input("ID do evento Bonificação*: ") or "0")
            if confirm("Gerar transações de bônus (PU=0) por carteira? (S/N) "):
                n = aplicar_bonificacao_gerando_transacoes(eid)
                print(f"Criadas {n} transações de bonificação.")
        except ValidationError as e: print(f"Erro: {e}")
        pause()
    elif ch == "3":
        print("Eventos de INPLIT recentes:")
        for e in eventos_repo.list(tipo="Inplit", data_ini=None, data_fim=None, limit=50):
            print(f"  {e['id']:>3} - {e['data_ex']} {e.get('ticker_antigo_str')}  num/den={e.get('num')}/{e.get('den')}")
        try:
            eid = int(_input("ID do evento Inplit*: ") or "0")
            px = _input("Preço por fração liquidada (R$)*: ").strip()
            if confirm("Gerar proventos OUTROS de frações por carteira? (S/N) "):
                n = aplicar_inplit_liquidacao_fracoes(eid, px)
                print(f"Criados {n} proventos de liquidação de frações.")
        except ValidationError as e: print(f"Erro: {e}")
        pause()
    else:
        return
