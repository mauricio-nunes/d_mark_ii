from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...db.repositories import transacoes_repo as repo, ativos_repo, carteiras_repo, corretoras_repo
from ...services.transacoes_service import incluir, editar, excluir, ValidationError
from ...services.posicao_service import posicao_e_pm_ate

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def _header():
    title("Transações")
    print("Tipos: COMPRA | VENDA | BONIFICACAO | SUBSCRICAO | AMORTIZACAO | TRANSFERENCIA")
    print("Comandos: [N] Próx.  [P] Ant.  [G] Ir pág.  [F] Filtrar  [I] Incluir  [E] Editar  [D] Excluir  [Q] Voltar")
    divider()

def _render(rows, page, pages, total):
    print(Fore.CYAN + f"{'ID':<5} {'DATA':<10} {'TIPO':<14} {'TICKER':<8} {'CART':<10} {'QTD':>12} {'PU':>12} {'TAXAS':>10}" + Style.RESET_ALL)
    print("-"*90)
    for r in rows:
        print(f"{r['id']:<5} {r['data']:<10} {r['tipo']:<14} {r['ticker_str']:<8} {r['carteira_str']:<10} "
              f"{r['quantidade']:>12} {r.get('preco_unitario',''):>12} {r.get('taxas',''):>10}")

def _coleta_campos(reg=None):
    data = _input(f"Data (YYYY-MM-DD)* [{reg['data']}]:" if reg else "Data (YYYY-MM-DD)*: ").strip() or (reg['data'] if reg else "")
    tipo = _input(f"Tipo* [{reg['tipo']}]:" if reg else "Tipo*: ").strip().upper() or (reg['tipo'] if reg else "")
    # listar alguns ids
    if not reg:
        print(Fore.MAGENTA + "Alguns ativos:" + Style.RESET_ALL)
        for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']} - {a['nome']}")
        print(Fore.MAGENTA + "Algumas carteiras:" + Style.RESET_ALL)
        for c in carteiras_repo.list("", True, 0, 10): print(f"  {c['id']:>3} - {c['nome']}")
        print(Fore.MAGENTA + "Algumas corretoras:" + Style.RESET_ALL)
        for co in corretoras_repo.list_corretoras("", True, 0, 10): print(f"  {co['id']:>3} - {co['nome']}")
    ticker = int(_input(f"Ticker (ID)* [{reg['ticker']}]:" if reg else "Ticker (ID)*: ") or (reg['ticker'] if reg else 0))
    cart = int(_input(f"Carteira (ID)* [{reg['carteira_id']}]:" if reg else "Carteira (ID)*: ") or (reg['carteira_id'] if reg else 0))
    qtd = _input(f"Quantidade* [{reg['quantidade']}]: " if reg else "Quantidade*: ").strip() or (reg['quantidade'] if reg else "")
    pu  = _input(f"Preço unitário [{reg.get('preco_unitario','')}]: " if reg else "Preço unitário: ").strip() or (reg.get('preco_unitario','') if reg else None)
    tx  = _input(f"Taxas [{reg.get('taxas','0')}]: " if reg else "Taxas: ").strip() or (reg.get('taxas','0') if reg else "0")
    obs = _input(f"Observações [{reg.get('observacoes','')}]: " if reg else "Observações: ").strip() or (reg.get('observacoes','') if reg else "")
    return {"data": data, "tipo": tipo, "ticker": ticker, "carteira_id": cart,
            "quantidade": qtd, "preco_unitario": pu, "taxas": tx, "observacoes": obs}

def tela_transacoes():
    filtro = ""; ticker_id = None; carteira_id = None
    total = repo.count(texto=filtro, ticker_id=ticker_id, carteira_id=carteira_id); pager = Paginator(total)

    while True:
        clear_screen(); _header()
        start, _ = pager.range()
        rows = repo.list(texto=filtro, ticker_id=ticker_id, carteira_id=carteira_id, offset=start, limit=pager.page_size, apenas_ativas=True)
        _render(rows, pager.page, pager.pages, pager.total)

        ch = prompt_menu_choice("Selecione: ").strip().lower()
        if ch in ("q","voltar"): break
        elif ch=="n": pager.next()
        elif ch=="p": pager.prev()
        elif ch=="g":
            try: pager.goto(int(input("Ir para página: ")))
            except: print("Inválido."); pause()
        elif ch=="f":
            filtro = input("Filtro em observações [ENTER limpa]: ").strip()
            # filtros rápidos
            ti = input("Ticker (ID) [ENTER ignora]: ").strip(); ticker_id = int(ti) if ti else None
            ca = input("Carteira (ID) [ENTER ignora]: ").strip(); carteira_id = int(ca) if ca else None
            total = repo.count(texto=filtro, ticker_id=ticker_id, carteira_id=carteira_id); pager = Paginator(total)
        elif ch=="i":
            try:
                data = _coleta_campos()
                if confirm("Confirmar inclusão? (S/N) "):
                    incluir(data); print("Incluída.")
                    total = repo.count(texto=filtro, ticker_id=ticker_id, carteira_id=carteira_id); pager = Paginator(total)
            except ValidationError as e:
                print(f"Erro: {e}")
            pause()
        elif ch=="e":
            try: tid = int(input("ID da transação: "))
            except: print("ID inválido."); pause(); continue
            reg = repo.get_by_id(tid)
            if not reg: print("Não encontrada."); pause(); continue
            try:
                data = _coleta_campos(reg)
                if confirm("Confirmar alteração? (S/N) "):
                    editar(tid, data); print("Atualizada.")
            except ValidationError as e:
                print(f"Erro: {e}")
            pause()
        elif ch=="d":
            try: tid = int(input("ID da transação: "))
            except: print("ID inválido."); pause(); continue
            if confirm("Excluir (soft delete)? (S/N) "):
                excluir(tid); print("Excluída.")
                total = repo.count(texto=filtro, ticker_id=ticker_id, carteira_id=carteira_id); pager = Paginator(total)
            pause()
        else:
            print("Comando inválido."); pause()
