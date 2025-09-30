from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...services.cadastros.corretoras_service import (
    CorretorasService as corretoras_service,
    ValidationError,
)


def _input(text):
    return input(Fore.WHITE + text + Style.RESET_ALL)


def _header():
    title("Cadastro de Corretoras")
    print("Comandos:  [I] Incluir [E] Editar [X] Inativar   [R] Reativar [F] Filtrar")
    print("Navegação: [N] Próx.   [P] Ant.   [G] Ir p/ pág. [Q] Voltar")
    divider()


def _render_table(rows, page, pages, total, filtro, apenas_ativas):
    status = "Ativas" if apenas_ativas else "Todas"
    print(
        Fore.YELLOW
        + f"Filtro: '{filtro}' | Exibindo: {status} | Página {page}/{pages} | Registros: {total}"
        + Style.RESET_ALL
    )
    print(Fore.BLUE + "-" * 70 + Style.RESET_ALL)
    print(
        Fore.CYAN
        + f"{'ID':<5} {'DESCRIÇÃO':<15} {'ATIVO':<6} {'NOME'}"
        + Style.RESET_ALL
    )
    print(Fore.BLUE + "-" * 70 + Style.RESET_ALL)
    for r in rows:
        ativo = "Sim" if r["ativo"] else "Não"
        print(f"{r['id']:<5} {r['descricao']:<15} {ativo:<6} {r['nome']}")
    print(Fore.BLUE + "-" * 70 + Style.RESET_ALL)


def _coleta_campos(reg=None):
    nome = _input(f"Nome* [{reg['nome']}]: " if reg else "Nome*: ").strip() or (
        reg["nome"] if reg else ""
    )
    desc = _input(
        f"Descrição [{reg.get('descricao','')}]: " if reg else "Descrição: "
    ).strip() or (reg.get("descricao", "") if reg else "")
    return {"nome": nome, "descricao": desc}


def tela_corretoras():
    filtro, apenas_ativas = "", True

    total = corretoras_service().contar_corretoras(filtro, apenas_ativas)
    pager = Paginator(total)

    while True:
        clear_screen()
        _header()
        start, _ = pager.range()
        rows = corretoras_service().listar_corretoras(
            filtro, apenas_ativas, offset=start, limit=pager.page_size
        )
        _render_table(rows, pager.page, pager.pages, pager.total, filtro, apenas_ativas)

        ch = prompt_menu_choice("Selecione: ").strip().lower()
        if ch in ("q", "voltar", "5"):
            break
        elif ch == "n":
            pager.next()
        elif ch == "p":
            pager.prev()
        elif ch == "g":
            try:
                pager.goto(int(_input("Ir para página: ")))
            except ValueError:
                print("Inválido.")
                pause()
        elif ch == "f":
            filtro = _input("Texto (nome/descrição) [ENTER p/ limpar]: ").strip()
            show = _input("Exibir só ativas? (S/N) [S]: ").strip().lower()
            apenas_ativas = False if show in ("n", "nao", "não") else True
            # recalcula paginação
            total = corretoras_service().contar_corretoras(filtro, apenas_ativas)
            pager = Paginator(total)
        elif ch == "i":
            data = _coleta_campos()
            try:
                if confirm("Confirmar inclusão (S/N)? "):
                    new_id = corretoras_service().criar_corretora(**data)
                    print(f"Corretora incluída com id {new_id}.")
                    # recarrega total
                    total = corretoras_service().contar_corretoras(
                        filtro, apenas_ativas
                    )
                    pager = Paginator(total)
                else:
                    print("Operação cancelada.")
            except ValidationError as e:
                print(f"Erro: {e}")
            pause()
        elif ch == "e":
            try:
                eid = int(_input("ID da corretora: "))
            except ValueError:
                print("ID inválido.")
                pause()
                continue
            reg = corretoras_service().get_corretora_por_id(eid)
            if not reg:
                print("Corretora não encontrada.")
                pause()
                continue
            data = _coleta_campos(reg)
            try:
                if confirm("Confirmar alteração (S/N)? "):
                    corretoras_service().editar_corretora(eid, **data)
                    print("Corretora Atualizada.")
                else:
                    print("Operação Cancelada.")
            except ValidationError as e:
                print(f"Erro: {e}")
            pause()
        elif ch == "x":
            try:
                eid = int(_input("ID da corretora p/ inativar: "))
            except ValueError:
                print("ID inválido.")
                pause()
                continue
            if confirm("Tem certeza que deseja INATIVAR? (S/N) "):
                try:
                    corretoras_service().inativar_corretora(eid)
                    print("Inativada.")
                except ValidationError as e:
                    print(f"Erro: {e}")
            else:
                print("Cancelado.")
            pause()
        elif ch == "r":
            try:
                eid = int(_input("ID da corretora p/ reativar: "))
            except ValueError:
                print("ID inválido.")
                pause()
                continue
            if confirm("Reativar? (S/N) "):
                try:
                    corretoras_service().reativar_corretora(eid)
                    print("Reativada.")
                except ValidationError as e:
                    print(f"Erro: {e}")
            else:
                print("Cancelado.")
            pause()
        else:
            print("Comando inválido.")
            pause()
