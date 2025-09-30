from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...services.cadastros.carteiras_service import(CarteirasService as carteiras_service, ValidationError)

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def _header():
    title("Cadastro de Carteiras")
    print("Comandos:  [I] Incluir [E] Editar [X] Inativar   [R] Reativar [F] Filtrar")
    print("Navegação: [N] Próx.   [P] Ant.   [G] Ir p/ pág. [Q] Voltar")
    divider()

def _render(rows, page, pages, total, filtro, apenas_ativas):
    status = "Ativas" if apenas_ativas else "Todas"
    print(Fore.YELLOW + f"Filtro: '{filtro}' | {status} | Página {page}/{pages} | Registros: {total}" + Style.RESET_ALL)
    print(Fore.CYAN + f"{'ID':<5} {'NOME':<30} {'ATIVO':<6} {'DESCRIÇÃO'}" + Style.RESET_ALL)
    print("-"*70)
    for r in rows:
        print(f"{r['id']:<5} {r['nome']:<30} {'Sim' if r['ativo'] else 'Não':<6} {r.get('descricao','')}")

def tela_carteiras():
    filtro, apenas_ativas = "", True
    
    total = carteiras_service().contar_carteiras(filtro, apenas_ativas); pager = Paginator(total)
    while True:
        clear_screen(); _header()
        start, end = pager.range()
        rows =  carteiras_service().listar_carteiras(filtro, apenas_ativas, start, pager.page_size)
        _render(rows, pager.page, pager.pages, pager.total, filtro, apenas_ativas)
        ch = prompt_menu_choice("Selecione: ").strip().lower()
        if ch in ("q","voltar"): break
        elif ch=="n": pager.next()
        elif ch=="p": pager.prev()
        elif ch=="g":
            try: pager.goto(int(_input("Ir para página: ")))
            except: print("Inválido."); pause()
        elif ch=="f":
            filtro = _input("Texto (nome/descrição) [ENTER limpa]: "); ap = _input("Só ativas? (S/N) [S]: ").lower()
            apenas_ativas = False if ap in ("n","nao","não") else True
            total = carteiras_service().contar_carteiras(filtro,apenas_ativas); pager = Paginator(total)
        elif ch=="i":
            nome = _input("Nome*: "); desc = _input("Descrição: ")
            try:
                if confirm("Confirmar inclusão? (S/N) "):
                    carteiras_service().criar_carteira(nome, desc); print("Incluída.")
                    total = carteiras_service().contar_carteiras(filtro,apenas_ativas); pager = Paginator(total)
            except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="e":
            try: cid = int(_input("ID: "))
            except: print("ID inválido."); pause(); continue
            reg = carteiras_service().get_carteira_por_id(cid)
            if not reg: print("Não encontrada."); pause(); continue
            nome = _input(f"Nome* [{reg['nome']}]: ") or reg['nome']
            desc = _input(f"Descrição [{reg.get('descricao','')}]: ") or (reg.get('descricao','') or "")
            try:
                if confirm("Confirmar alteração? (S/N) "): 
                    carteiras_service().editar_carteira(cid, nome, desc); print("Atualizada.")
            except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="x":
            try: cid = int(_input("ID p/ inativar: "))
            except: print("ID inválido."); pause(); continue
            if confirm("Inativar? (S/N) "):
                try: 
                    carteiras_service().inativar_carteira(cid); print("Inativada.")
                except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="r":
            try: cid = int(_input("ID p/ reativar: "))
            except: print("ID inválido."); pause(); continue
            if confirm("Reativar? (S/N) "):
                try: 
                    carteiras_service().reativar_carteira(cid); print("Reativada.")
                except ValidationError as e: print(f"Erro: {e}")
            pause()
        else:
            print("Comando inválido."); pause()
