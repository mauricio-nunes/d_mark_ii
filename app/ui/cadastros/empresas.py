from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...db.repositories import empresas_repo as repo
from ...services.cadastros.empresas_service import ValidationError, criar, editar, inativar, reativar
from ...core.utils import normalize_cnpj

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

def _header():
    title("Cadastro de Empresas")
    print("Comandos: [N] Próx.  [P] Ant.  [G] Ir pág.  [F] Filtrar  [I] Incluir  [E] Editar  [X] Inativar  [R] Reativar  [Q] Voltar")
    divider()

def _render(rows, page, pages, total, filtro, apenas_ativas):
    status = "Ativas" if apenas_ativas else "Todas"
    print(Fore.YELLOW + f"Filtro: '{filtro}' | {status} | Página {page}/{pages} | Registros: {total}" + Style.RESET_ALL)
    print(Fore.CYAN + f"{'ID':<5} {'CNPJ':<16} {'RAZÃO SOCIAL':<40} {'TIPO':<10} {'ATIVO':<6}" + Style.RESET_ALL)
    print("-"*90)
    for r in rows:
        cnpj = r['cnpj']
        print(f"{r['id']:<5} {cnpj:<16} {r['razao_social']:<40} {r['tipo_empresa']:<10} {'Sim' if r['ativo'] else 'Não':<6}")

def _coleta_campos(reg=None):
    cnpj = _input(f"CNPJ* [{reg['cnpj']}]:" if reg else "CNPJ*: ").strip() or (reg['cnpj'] if reg else "")
    rz = _input(f"Razão social* [{reg['razao_social']}]: " if reg else "Razão social*: ").strip() or (reg['razao_social'] if reg else "")
    cvm = _input(f"Código CVM* [{reg['codigo_cvm']}]: " if reg else "Código CVM*: ").strip() or (reg['codigo_cvm'] if reg else "")
    data_const = _input(f"Data constituição (YYYY-MM-DD) [{reg.get('data_constituicao','')}]:" if reg else "Data constituição (YYYY-MM-DD): ").strip() or (reg.get('data_constituicao','') if reg else None)
    setor = _input(f"Setor [{reg.get('setor_atividade','')}]: " if reg else "Setor: ").strip() or (reg.get('setor_atividade','') if reg else "")
    situ = _input(f"Situação [{reg.get('situacao','')}]: " if reg else "Situação: ").strip() or (reg.get('situacao','') if reg else "")
    ctrl = _input(f"Controle acionário [{reg.get('controle_acionario','')}]: " if reg else "Controle acionário: ").strip() or (reg.get('controle_acionario','') if reg else "")
    tipo = _input(f"Tipo* (Fundo|CiaAberta) [{reg.get('tipo_empresa','')}]: " if reg else "Tipo* (Fundo|CiaAberta): ").strip() or (reg.get('tipo_empresa','') if reg else "")
    return {
        "cnpj": normalize_cnpj(cnpj),
        "razao_social": rz,
        "codigo_cvm": cvm,
        "data_constituicao": data_const or None,
        "setor_atividade": setor,
        "situacao": situ,
        "controle_acionario": ctrl,
        "tipo_empresa": tipo
    }

def tela_empresas():
    filtro, apenas_ativas = "", True
    total = repo.count(filtro, apenas_ativas); pager = Paginator(total)
    while True:
        clear_screen(); _header()
        start, _ = pager.range()
        rows = repo.list(filtro, apenas_ativas, start, pager.page_size)
        _render(rows, pager.page, pager.pages, pager.total, filtro, apenas_ativas)
        ch = prompt_menu_choice("Selecione: ").strip().lower()
        if ch in ("q","voltar"): break
        elif ch=="n": pager.next()
        elif ch=="p": pager.prev()
        elif ch=="g":
            try: pager.goto(int(_input("Ir para página: ")))
            except: print("Inválido."); pause()
        elif ch=="f":
            filtro = _input("Texto (razão/cnpj) [ENTER limpa]: ")
            ap = _input("Só ativas? (S/N) [S]: ").lower()
            apenas_ativas = False if ap in ("n","nao","não") else True
            total = repo.count(filtro,apenas_ativas); pager = Paginator(total)
        elif ch=="i":
            data = _coleta_campos()
            try:
                if confirm("Confirmar inclusão? (S/N) "):
                    criar(**data); print("Incluída.")
                    total = repo.count(filtro,apenas_ativas); pager = Paginator(total)
            except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="e":
            try: eid = int(_input("ID: "))
            except: print("ID inválido."); pause(); continue
            reg = repo.get_by_id(eid)
            if not reg: print("Não encontrada."); pause(); continue
            data = _coleta_campos(reg)
            try:
                if confirm("Confirmar alteração? (S/N) "):
                    editar(eid, **data); print("Atualizada.")
            except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="x":
            try: eid = int(_input("ID p/ inativar: "))
            except: print("ID inválido."); pause(); continue
            if confirm("Inativar? (S/N) "):
                try: inativar(eid); print("Inativada.")
                except ValidationError as e: print(f"Erro: {e}")
            pause()
        elif ch=="r":
            try: eid = int(_input("ID p/ reativar: "))
            except: print("ID inválido."); pause(); continue
            if confirm("Reativar? (S/N) "):
                try: reativar(eid); print("Reativada.")
                except ValidationError as e: print(f"Erro: {e}")
            pause()
        else:
            print("Comando inválido."); pause()
