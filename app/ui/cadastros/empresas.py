from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...services.cadastros.empresas_service import (
    EmpresasService as empresas_service,
    ValidationError,
)


def _input(t):
    return input(Fore.WHITE + t + Style.RESET_ALL)


def _header():
    title("Cadastro de Empresas")
    print("Comandos:  [I] Incluir [E] Editar [X] Inativar   [R] Reativar [F] Filtrar")
    print("Navegação: [N] Próx.   [P] Ant.   [G] Ir p/ pág. [Q] Voltar")
    divider()


def _render_table(rows, page, pages, total, filtro, apenas_ativas):
    status = "Ativas" if apenas_ativas else "Todas"
    print(
        Fore.YELLOW
        + f"Filtro: '{filtro}' | {status} | Página {page}/{pages} | Registros: {total}"
        + Style.RESET_ALL
    )
    print(
        Fore.CYAN
        + f"{'ID':<5} {'CNPJ':<16} {'RAZÃO SOCIAL':<40} {'TIPO':<10} {'ATIVO':<6}"
        + Style.RESET_ALL
    )
    print("-" * 90)
    for r in rows:
        cnpj = r["cnpj"]
        print(
            f"{r['id']:<5} {cnpj:<16} {r['razao_social']:<40} {r['tipo_empresa']:<10} {'Sim' if r['ativo'] else 'Não':<6}"
        )


def _coleta_campos(reg=None):
    cnpj = _input(f"CNPJ* [{reg['cnpj']}]:" if reg else "CNPJ*: ").strip() or (
        reg["cnpj"] if reg else ""
    )
    rz = _input(
        f"Razão social* [{reg['razao_social']}]: " if reg else "Razão social*: "
    ).strip() or (reg["razao_social"] if reg else "")
    setor = _input(
        f"Setor [{reg.get('setor_atividade','')}]: " if reg else "Setor: "
    ).strip() or (reg.get("setor_atividade", "") if reg else "")
    tipo = _input(
        f"Tipo* (Fundo|CiaAberta) [{reg.get('tipo_empresa','')}]: "
        if reg
        else "Tipo* (Fundo|CiaAberta): "
    ).strip() or (reg.get("tipo_empresa", "") if reg else "")
    return {
        "cnpj": cnpj,
        "razao_social": rz,
        "setor_atividade": setor,
        "tipo_empresa": tipo,
    }


def tela_empresas():
    filtro, apenas_ativas = "", True
    total = empresas_service().contar_empresas(filtro, apenas_ativas)
    pager = Paginator(total)

    while True:
        clear_screen()
        _header()
        start, _ = pager.range()
        rows = empresas_service().listar_empresas(
            filtro, apenas_ativas, start, pager.page_size
        )
        _render_table(rows, pager.page, pager.pages, pager.total, filtro, apenas_ativas)

        ch = prompt_menu_choice("Selecione: ").strip().lower()
        if ch in ("q", "voltar"):
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
            filtro = _input("Texto (razão/cnpj) [ENTER p/ limpar]: ").strip()
            show = _input("Só ativas? (S/N) [S]: ").strip().lower()
            apenas_ativas = False if show in ("n", "nao", "não") else True
            # recalcula paginação
            total = empresas_service().contar_empresas(filtro, apenas_ativas)
            pager = Paginator(total)
        elif ch == "i":
            data = _coleta_campos()
            try:
                if confirm("Confirmar inclusão? (S/N) "):
                    new_id = empresas_service().criar_empresa(**data)
                    print(f"Empresa incluída com id {new_id}.")
                    total = empresas_service().contar_empresas(filtro, apenas_ativas)
                    pager = Paginator(total)
                else:
                    print("Operação Cancelada.")
            except ValidationError as e:
                print(f"Erro: {e}")
            pause()
        elif ch == "e":
            try:
                eid = int(_input("ID da empresa: "))
            except ValueError:
                print("ID inválido.")
                pause()
                continue
            reg = empresas_service().get_empresa_por_id(eid)
            if not reg:
                print(" Empresa não encontrada.")
                pause()
                continue
            data = _coleta_campos(reg)
            try:
                if confirm("Confirmar alteração? (S/N) "):
                    empresas_service().editar_empresa(eid, **data)
                    print("Empresa Atualizada.")
                else:
                    print("Operação Cancelada.")
            except ValidationError as e:
                print(f"Erro: {e}")
            pause()
        elif ch == "x":
            try:
                eid = int(_input("ID da Empresa  p/ inativar: "))
            except ValueError:
                print("ID inválido.")
                pause()
                continue
            if confirm("Tem certeza que deseja INATIVAR? (S/N) "):
                try:
                    empresas_service().inativar_empresa(eid)
                    print("Inativada.")
                except ValidationError as e:
                    print(f"Erro: {e}")
            else:
                print("Cancelado.")
            pause()
        elif ch == "r":
            try:
                eid = int(_input("ID da Empresa p/ reativar: "))
            except ValueError:
                print("ID inválido.")
                pause()
                continue
            if confirm("Reativar? (S/N) "):
                try:
                    empresas_service().reativar_empresa(eid)
                    print("Reativada.")
                except ValidationError as e:
                    print(f"Erro: {e}")
            pause()
        else:
            print("Comando inválido.")
            pause()
