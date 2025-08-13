from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...db.repositories import eventos_repo, ativos_repo
from ...services.eventos_service import incluir_evento, editar_evento, excluir_evento, ValidationError

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def _header():
    title("Eventos")
    print("Tipos: Split | Inplit | Bonificacao | TrocaTicker")
    print("Comandos: [N] Próx. [P] Ant. [G] Ir pág. [F] Filtro [I] Incluir [E] Editar [D] Excluir [Q] Voltar")
    divider()

def _render(rows, page, pages, total):
    print(Fore.CYAN + f"{'ID':<4} {'DATA':<10} {'TIPO':<12} {'TICKER_ANT':<10} {'TICKER_NOV':<10} {'NUM':>6} {'DEN':>6} {'ATV':<3}" + Style.RESET_ALL)
    for r in rows:
        print(f"{r['id']:<4} {r['data_ex']:<10} {r['tipo']:<12} {r.get('ticker_antigo_str') or '-':<10} {r.get('ticker_novo_str') or '-':<10} "
              f"{str(r.get('num') or ''):>6} {str(r.get('den') or ''):>6} {('S' if r.get('ativo') else 'N'):>3}")

def _form(reg=None):
    if not reg:
        print(Fore.MAGENTA + "Alguns ativos:" + Style.RESET_ALL)
        for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']} - {a['nome']}")
    tipo = _input(f"Tipo* [{reg['tipo']}]:" if reg else "Tipo*: ").strip() or (reg['tipo'] if reg else "")
    data_ex = _input(f"Data-ex* (YYYY-MM-DD) [{reg['data_ex']}]:" if reg else "Data-ex* (YYYY-MM-DD): ").strip() or (reg['data_ex'] if reg else "")
    ta = _input(f"Ticker antigo (ID) [{reg.get('ticker_antigo') or ''}]: " if reg else "Ticker antigo (ID): ").strip() or (reg.get('ticker_antigo') if reg else None)
    tn = _input(f"Ticker novo (ID) [{reg.get('ticker_novo') or ''}]: " if reg else "Ticker novo (ID): ").strip() or (reg.get('ticker_novo') if reg else None)
    num = _input(f"num [{reg.get('num') or ''}]: " if reg else "num: ").strip() or (reg.get('num') if reg else None)
    den = _input(f"den [{reg.get('den') or ''}]: " if reg else "den: ").strip() or (reg.get('den') if reg else None)
    obs = _input(f"Obs [{reg.get('observacoes','')}]: " if reg else "Obs: ").strip() or (reg.get('observacoes','') if reg else "")
    return {
        "tipo": tipo, "data_ex": data_ex,
        "ticker_antigo": int(ta) if ta else None,
        "ticker_novo": int(tn) if tn else None,
        "num": int(num) if num else None,
        "den": int(den) if den else None,
        "observacoes": obs
    }

def tela_eventos():
    filtro_tipo = None
    total = len(eventos_repo.list(tipo=filtro_tipo))
    pager = Paginator(total)

    while True:
        clear_screen(); _header()
        start, _ = pager.range()
        rows = eventos_repo.list(tipo=filtro_tipo, offset=start, limit=pager.page_size)
        _render(rows, pager.page, pager.pages, pager.total)
        ch = prompt_menu_choice("Selecione: ").strip().lower()
        if ch in ("q","voltar"): break
        elif ch=="n": pager.next()
        elif ch=="p": pager.prev()
        elif ch=="g":
            try: pager.goto(int(input("Ir para página: ")))
            except: print("Inválido."); pause()
        elif ch=="f":
            tp = input("Tipo (Split/Inplit/Bonificacao/TrocaTicker) [ENTER limpa]: ").strip()
            filtro_tipo = tp or None
            total = len(eventos_repo.list(tipo=filtro_tipo)); pager = Paginator(total)
        elif ch=="i":
            try:
                data = _form()
                if confirm("Confirmar inclusão? (S/N) "):
                    incluir_evento(data); print("Incluído.")
                    total = len(eventos_repo.list(tipo=filtro_tipo)); pager = Paginator(total)
            except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="e":
            try: eid = int(input("ID: "))
            except: print("ID inválido."); pause(); continue
            reg = eventos_repo.get_by_id(eid)
            if not reg: print("Não encontrado."); pause(); continue
            try:
                data = _form(reg)
                if confirm("Confirmar alteração? (S/N) "):
                    editar_evento(eid, data); print("Atualizado.")
            except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="d":
            try: eid = int(input("ID: "))
            except: print("ID inválido."); pause(); continue
            if confirm("Excluir (soft delete)? (S/N) "):
                excluir_evento(eid); print("Excluído.")
                total = len(eventos_repo.list(tipo=filtro_tipo)); pager = Paginator(total)
            pause()
        else:
            print("Comando inválido."); pause()
