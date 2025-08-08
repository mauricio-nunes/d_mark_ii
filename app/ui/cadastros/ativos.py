from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...db.repositories import ativos_repo as repo
from ...db.repositories import empresas_repo
from ...services.cadastros.ativos_service import ValidationError, CLASSES, criar, editar, inativar, reativar

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def _header():
    title("Cadastro de Ativos")
    print(f"Classes válidas: {', '.join(CLASSES)}")
    print("Comandos: [N] Próx.  [P] Ant.  [G] Ir pág.  [F] Filtrar  [I] Incluir  [E] Editar  [X] Inativar  [R] Reativar  [Q] Voltar")
    divider()

def _render(rows, page, pages, total, filtro, apenas_ativos):
    status = "Ativos" if apenas_ativos else "Todos"
    print(Fore.YELLOW + f"Filtro: '{filtro}' | {status} | Página {page}/{pages} | Registros: {total}" + Style.RESET_ALL)
    print(Fore.CYAN + f"{'ID':<5} {'TICKER':<10} {'NOME':<30} {'CLASSE':<10} {'EMPRESA'}" + Style.RESET_ALL)
    print("-"*90)
    for r in rows:
        emp = r['empresa'] or "-"
        print(f"{r['id']:<5} {r['ticker']:<10} {r['nome']:<30} {r['classe']:<10} {emp}")

def _coleta_campos(reg=None):
    ticker = _input(f"Ticker* [{reg['ticker']}]: " if reg else "Ticker*: ").strip() or (reg['ticker'] if reg else "")
    nome = _input(f"Nome* [{reg['nome']}]: " if reg else "Nome*: ").strip() or (reg['nome'] if reg else "")
    classe = _input(f"Classe* ({'/'.join(CLASSES)}) [{reg['classe']}]: " if reg else f"Classe* ({'/'.join(CLASSES)}): ").strip() or (reg['classe'] if reg else "")
    empresa_id = _input(f"Empresa (ID) [{reg.get('empresa_id') if reg else ''}] - ENTER p/ nenhum: ").strip() or (reg.get('empresa_id') if reg else "")
    if empresa_id: 
        try: empresa_id = int(empresa_id)
        except: empresa_id = None
    return {"ticker": ticker, "nome": nome, "classe": classe, "empresa_id": empresa_id}

def _listar_empresas_pequeno():
    rows = empresas_repo.list("", True, 0, 10)
    print(Fore.MAGENTA + "Algumas empresas (use o ID):" + Style.RESET_ALL)
    for r in rows:
        print(f"  {r['id']:>3} - {r['razao_social']} ({r['cnpj']})")

def tela_ativos():
    filtro, apenas_ativos = "", True
    total = repo.count(filtro, apenas_ativos); pager = Paginator(total)
    while True:
        clear_screen(); _header()
        start, _ = pager.range()
        rows = repo.list(filtro, apenas_ativos, start, pager.page_size)
        _render(rows, pager.page, pager.pages, pager.total, filtro, apenas_ativos)
        ch = prompt_menu_choice("Selecione: ").strip().lower()
        if ch in ("q","voltar"): break
        elif ch=="n": pager.next()
        elif ch=="p": pager.prev()
        elif ch=="g":
            try: pager.goto(int(_input("Ir para página: ")))
            except: print("Inválido."); pause()
        elif ch=="f":
            filtro = _input("Texto (ticker/nome) [ENTER limpa]: ")
            ap = _input("Somente ativos? (S/N) [S]: ").lower()
            apenas_ativos = False if ap in ("n","nao","não") else True
            total = repo.count(filtro,apenas_ativos); pager = Paginator(total)
        elif ch=="i":
            _listar_empresas_pequeno()
            data = _coleta_campos()
            try:
                if confirm("Confirmar inclusão? (S/N) "):
                    criar(**data); print("Incluído.")
                    total = repo.count(filtro,apenas_ativos); pager = Paginator(total)
            except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="e":
            try: aid = int(_input("ID: "))
            except: print("ID inválido."); pause(); continue
            reg = repo.get_by_id(aid)
            if not reg: print("Não encontrado."); pause(); continue
            _listar_empresas_pequeno()
            data = _coleta_campos(reg)
            try:
                if confirm("Confirmar alteração? (S/N) "): editar(aid, **data); print("Atualizado.")
            except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="x":
            try: aid = int(_input("ID p/ inativar: "))
            except: print("ID inválido."); pause(); continue
            if confirm("Inativar? (S/N) "):
                try: inativar(aid); print("Inativado.")
                except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="r":
            try: aid = int(_input("ID p/ reativar: "))
            except: print("ID inválido."); pause(); continue
            if confirm("Reativar? (S/N) "):
                try: reativar(aid); print("Reativado.")
                except ValidationError as e: print(f"Erro: {e}")
            pause()
        else:
            print("Comando inválido."); pause()
