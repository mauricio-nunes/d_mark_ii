from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...db.repositories import proventos_repo as repo, ativos_repo
from ...services.proventos_service import incluir, editar, excluir, ValidationError

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def _header():
    title("Proventos")
    print("Tipos: DIVIDENDO | JCP | RENDIMENTO FII | AMORTIZACAO | OUTROS")
    print("Comandos: [N] Próx. [P] Ant. [G] Ir pág. [F] Filtros [I] Incluir [E] Editar [D] Excluir [Q] Voltar")
    divider()

def _render(rows, page, pages, total):
    print(Fore.CYAN + f"{'ID':<5} {'DATA':<10} {'TIPO':<14} {'TICKER':<8} {'VALOR':>14} {'QTD':>12} {'PU':>12} {'DESC'}" + Style.RESET_ALL)
    print("-"*110)
    for r in rows:
        print(f"{r['id']:<5} {r['data_pagamento']:<10} {r['tipo_evento']:<14} {r['ticker_str']:<8} "
              f"{str(r.get('valor_total') or ''):>14} {str(r.get('quantidade') or ''):>12} {str(r.get('preco_unitario') or ''):>12} {r.get('descricao','')}")

def _coleta_campos(reg=None):
    if not reg:
        print(Fore.MAGENTA + "Alguns ativos:" + Style.RESET_ALL)
        for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']} - {a['nome']}")
    data = _input(f"Data pagamento (YYYY-MM-DD)* [{reg['data_pagamento']}]:" if reg else "Data pagamento (YYYY-MM-DD)*: ").strip() or (reg['data_pagamento'] if reg else "")
    tipo = _input(f"Tipo* [{reg['tipo_evento']}]:" if reg else "Tipo*: ").strip().upper() or (reg['tipo_evento'] if reg else "")
    ticker = int(_input(f"Ticker (ID)* [{reg['ticker']}]: " if reg else "Ticker (ID)*: ").strip() or (reg['ticker'] if reg else 0))
    desc = _input(f"Descrição [{reg.get('descricao','')}]: " if reg else "Descrição: ").strip() or (reg.get('descricao','') if reg else "")
    qtd  = _input(f"Quantidade [{reg.get('quantidade','')}]: " if reg else "Quantidade: ").strip() or (reg.get('quantidade','') if reg else None)
    pu   = _input(f"Preço unitário [{reg.get('preco_unitario','')}]: " if reg else "Preço unitário: ").strip() or (reg.get('preco_unitario','') if reg else None)
    val  = _input(f"Valor total [{reg.get('valor_total','')}]: " if reg else "Valor total: ").strip() or (reg.get('valor_total','') if reg else None)
    obs  = _input(f"Observações [{reg.get('observacoes','')}]: " if reg else "Observações: ").strip() or (reg.get('observacoes','') if reg else "")
    return {"data_pagamento": data, "tipo_evento": tipo, "ticker": ticker, "descricao": desc,
            "quantidade": qtd, "preco_unitario": pu, "valor_total": val, "observacoes": obs}

def tela_proventos():
    filtro = ""; ticker_id = None; tipo = None
    total = repo.count(texto=filtro, ticker_id=ticker_id, tipo=tipo); pager = Paginator(total)
    while True:
        clear_screen(); _header()
        start, _ = pager.range()
        rows = repo.list(texto=filtro, ticker_id=ticker_id, tipo=tipo, offset=start, limit=pager.page_size, apenas_ativos=True)
        _render(rows, pager.page, pager.pages, pager.total)
        ch = prompt_menu_choice("Selecione: ").strip().lower()
        if ch in ("q","voltar"): break
        elif ch=="n": pager.next()
        elif ch=="p": pager.prev()
        elif ch=="g":
            try: pager.goto(int(input("Ir para página: ")))
            except: print("Inválido."); pause()
        elif ch=="f":
            filtro = input("Filtro (descrição/obs) [ENTER limpa]: ").strip()
            ti = input("Ticker (ID) [ENTER ignora]: ").strip(); ticker_id = int(ti) if ti else None
            tp = input("Tipo (DIVIDENDO/JCP/RENDIMENTO FII/AMORTIZACAO/OUTROS) [ENTER ignora]: ").strip().upper()
            tipo = tp or None
            total = repo.count(texto=filtro, ticker_id=ticker_id, tipo=tipo); pager = Paginator(total)
        elif ch=="i":
            try:
                data = _coleta_campos()
                if confirm("Confirmar inclusão? (S/N) "):
                    incluir(data); print("Incluído.")
                    total = repo.count(texto=filtro, ticker_id=ticker_id, tipo=tipo); pager = Paginator(total)
            except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="e":
            try: pid = int(input("ID do provento: "))
            except: print("ID inválido."); pause(); continue
            reg = repo.get_by_id(pid)
            if not reg: print("Não encontrado."); pause(); continue
            try:
                data = _coleta_campos(reg)
                if confirm("Confirmar alteração? (S/N) "):
                    editar(pid, data); print("Atualizado.")
            except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="d":
            try: pid = int(input("ID do provento: "))
            except: print("ID inválido."); pause(); continue
            if confirm("Excluir (soft delete)? (S/N) "):
                excluir(pid); print("Excluído.")
                total = repo.count(texto=filtro, ticker_id=ticker_id, tipo=tipo); pager = Paginator(total)
            pause()
        else:
            print("Comando inválido."); pause()
