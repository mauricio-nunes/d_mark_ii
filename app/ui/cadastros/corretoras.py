from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...services.cadastros.corretoras_service import (
    criar_corretora, editar_corretora, inativar_corretora, reativar_corretora,contar_corretoras,listar_corretoras, get_corretora_por_id, ValidationError
)

def _input(text): return input(Fore.WHITE + text + Style.RESET_ALL)

def _header():
    title("Cadastro de Corretoras")
    print("Comandos:  [I] Incluir [E] Editar [X] Inativar   [R] Reativar [F] Filtrar")
    print("Navegação: [N] Próx.   [P] Ant.   [G] Ir p/ pág. [Q] Voltar")
    divider()

def _render_table(rows, page, pages, total, filtro, apenas_ativas):
    status = "Ativas" if apenas_ativas else "Todas"
    print(Fore.YELLOW + f"Filtro: '{filtro}' | Exibindo: {status} | Página {page}/{pages} | Registros: {total}" + Style.RESET_ALL)
    print(Fore.BLUE + "-" * 70 + Style.RESET_ALL)
    print(Fore.CYAN + f"{'ID':<5} {'DESCRIÇÃO':<15} {'ATIVO':<6} {'NOME'}" + Style.RESET_ALL)
    print(Fore.BLUE + "-" * 70 + Style.RESET_ALL)
    for r in rows:
        ativo = "Sim" if r["ativo"] else "Não"
        print(f"{r['id']:<5} {r['descricao']:<15} {ativo:<6} {r['nome']}")
    print(Fore.BLUE + "-" * 70 + Style.RESET_ALL)

def tela_corretoras():
    filtro = ""
    apenas_ativas = True
    # paginação
    total = contar_corretoras(filtro, apenas_ativas)
    pager = Paginator(total)

    while True:
        clear_screen()
        _header()
        start, end = pager.range()
        rows = listar_corretoras(filtro, apenas_ativas, offset=start, limit=pager.page_size)
        _render_table(rows, pager.page, pager.pages, pager.total, filtro, apenas_ativas)

        choice = prompt_menu_choice("Selecione: ").strip().lower()
        if choice in ("q", "voltar", "5"):
            break
        elif choice == "n":
            pager.next()
        elif choice == "p":
            pager.prev()
        elif choice == "g":
            try:
                p = int(_input("Ir para a página: "))
                pager.goto(p)
            except ValueError:
                print("Número inválido."); pause()
        elif choice == "f":
            filtro = _input("Texto (nome/descrição) [ENTER p/ limpar]: ").strip()
            show = _input("Exibir só ativas? (S/N) [S]: ").strip().lower()
            apenas_ativas = False if show in ("n","nao","não") else True
            # recalcula paginação
            total = contar_corretoras(filtro, apenas_ativas)
            pager = Paginator(total)
        elif choice == "i":
            nome = _input("Nome*: ").strip()
            desc = _input("Descrição: ").strip()
            try:
                if confirm("Confirmar inclusão (S/N)? "):
                    new_id = criar_corretora(nome, desc)
                    print(f"Incluída com id {new_id}.")
                    # recarrega total
                    total = contar_corretoras(filtro, apenas_ativas); pager = Paginator(total)
                else:
                    print("Operação cancelada.")
            except ValidationError as e:
                print(f"Erro: {e}")
            pause()
        elif choice == "e":
            try:
                cid = int(_input("ID da corretora: "))
            except ValueError:
                print("ID inválido."); pause(); continue
            reg = get_corretora_por_id(cid)
            if not reg:
                print("Não encontrada."); pause(); continue
            nome = _input(f"Nome* [{reg['nome']}]: ").strip() or reg["nome"]
            desc = _input(f"Descrição [{reg.get('descricao','')}] : ").strip() or (reg.get("descricao","") or "")
            try:
                if confirm("Confirmar alteração (S/N)? "):
                    editar_corretora(cid, nome, desc)
                    print("Atualizado.")
                else:
                    print("Operação cancelada.")
            except ValidationError as e:
                print(f"Erro: {e}")
            pause()
        elif choice == "x":
            try:
                cid = int(_input("ID da corretora p/ inativar: "))
            except ValueError:
                print("ID inválido."); pause(); continue
            if confirm("Tem certeza que deseja INATIVAR? (S/N) "):
                try:
                    inativar_corretora(cid); print("Inativada.")
                except ValidationError as e:
                    print(f"Erro: {e}")
            else:
                print("Cancelado.")
            pause()
        elif choice == "r":
            try:
                cid = int(_input("ID da corretora p/ reativar: "))
            except ValueError:
                print("ID inválido."); pause(); continue
            if confirm("Reativar? (S/N) "):
                try:
                    reativar_corretora(cid); print("Reativada.")
                except ValidationError as e:
                    print(f"Erro: {e}")
            else:
                print("Cancelado.")
            pause()
        else:
            print("Comando inválido."); pause()
