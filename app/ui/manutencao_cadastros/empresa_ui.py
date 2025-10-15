from app.services.empresas.empresa_service import EmpresaService
from ..widgets import (
    title,
    divider,
    pause,
    show_menu_options,
    prompt_menu_choice,
    render_table,
    print_dict,
)
from ..forms import (
    rich_label_error,
    rich_input,
    rich_label_info,
    rich_edit_input,
    rich_label_success,
    rich_label,
)
from ...core.utils import clear_screen, parse_cnpj


service = EmpresaService()

TABLE_COLUMNS = ["CNPJ", "Nome", "Código", "Classificação", "Tipo DFP", "Modo Análise"]

MENU_ITENS = [
    "Listar empresas",
    "Buscar empresa (CNPJ ou código)",
    "Adicionar nova empresa",
    "Exportar cadastro para CSV",
    "Voltar",
]

DFP_TYPES = ["individual", "consolidado"]
ANALYSIS_MODES = ["banco", "seguradora", "padrao"]


def handle_menu_choice(choice: str) -> bool:
    match choice.lower():
        case "1":
            listar_empresas()
        case "2":
            buscar_empresa()
        case "3":
            adicionar_empresa()
        case "4":
            exportar_csv()
        case "0" | "q" | "voltar" | "sair" | "exit":
            return False
        case _:
            rich_label_error("Opção inválida.")
            pause()
    return True


def empresa_menu():
    keep = True
    while keep:
        clear_screen()
        divider()
        title("Cadastro de Empresas")
        divider()
        show_menu_options(MENU_ITENS)
        divider()
        choice = prompt_menu_choice()
        keep = handle_menu_choice(choice)


def listar_empresas():
    page = 1
    while True:
        clear_screen()
        divider()
        title("Listagem de Empresas")
        divider()
        emp, total = service.listar_empresas(page)
        total_pages = (total // 20) + (1 if total % 20 > 0 else 0)
        emp = [
            (
                parse_cnpj(e["cnpj"]),
                str(e["nome_pregao"]),
                e["codigo_negociacao"],
                str(e["classificacao"] or ""),
                str(e["tipo_dfp"] or ""),
                str(e["modo_analise"] or ""),
            )
            for e in emp
        ]
        render_table("Empresas", total, total_pages, page, TABLE_COLUMNS, emp)
        op = (
            prompt_menu_choice("\n[N] Próxima | [P] Anterior | [Q] Sair: ")
            .strip()
            .lower()
        )
        if op == "n":
            page += 1
        elif op == "p" and page > 1:
            page -= 1
        elif op == "q":
            break


def buscar_empresa():
    query = rich_input("\nDigite o CNPJ ou código de negociação: ").strip()
    empresa = service.buscar_empresa(query)
    if empresa:
        clear_screen()
        divider()
        title("Buscar Empresa - Resultado")
        divider()
        render_table(
            "Empresa Encontrada",
            1,
            1,
            1,
            TABLE_COLUMNS,
            [
                (
                    parse_cnpj(empresa["cnpj"]),
                    empresa["nome_pregao"],
                    empresa["codigo_negociacao"],
                    str(empresa["classificacao"] or ""),
                    str(empresa["tipo_dfp"] or ""),
                    str(empresa["modo_analise"] or ""),
                )
            ],
        )
        op = prompt_menu_choice("[E] Editar | [V] Voltar: ").strip().lower()
        if op == "e":
            editar_empresa(empresa["cnpj"])
    else:
        rich_label_info("Empresa não encontrada.")
        pause()


def adicionar_empresa():
    clear_screen()
    divider()
    title("Adicionar Nova Empresa")
    divider()
    cnpj = rich_edit_input("CNPJ: ")
    nome_pregao = rich_edit_input("Nome: ")
    codigo = rich_edit_input("Código de negociação: ")
    classificacao = rich_edit_input("Classificação: ")
    tipo_dfp = rich_edit_input("Tipo DFP (opcional): ", choices=DFP_TYPES)
    modo_analise = rich_edit_input("Modo análise (opcional): ", choices=ANALYSIS_MODES)
    try:
        service.adicionar_empresa(
            cnpj, nome_pregao, codigo, classificacao, tipo_dfp, modo_analise
        )
        rich_label_success("Empresa adicionada com sucesso!")
    except Exception as e:
        rich_label_error(e)
    pause()


def editar_empresa(cnpj=None):
    if not cnpj:
        cnpj = rich_edit_input("Digite o CNPJ da empresa para editar: ").strip()
    empresa = service.buscar_empresa(cnpj)
    if not empresa:
        rich_label_error("Empresa não encontrada.")
        pause()

    clear_screen()
    divider()
    title("Editar Empresa")
    divider()

    rich_label(f'CNPJ: {parse_cnpj(empresa["cnpj"])}')
    nome_pregao = rich_edit_input(f"Nome: ", empresa["nome_pregao"])
    codigo = rich_edit_input(f"Código: ", empresa["codigo_negociacao"])
    classificacao = rich_edit_input(f"Classificação: ", empresa["classificacao"])
    tipo_dfp = rich_edit_input(f"Tipo DFP: ", empresa["tipo_dfp"], choices=DFP_TYPES)
    modo_analise = rich_edit_input(
        f"Modo análise: ", empresa["modo_analise"], choices=ANALYSIS_MODES
    )
    try:
        service.editar_empresa(
            empresa["cnpj"], nome_pregao, codigo, classificacao, tipo_dfp, modo_analise
        )
        rich_label_success("Empresa atualizada com sucesso!")
    except Exception as e:
        rich_label_error(e)
    pause()


def exportar_csv():
    try:
        clear_screen()
        divider()
        title("Exportar Empresas para CSV")
        divider()
        path = service.exportar_csv()
        print_dict({"Arquivo exportado": str(path)})
    except Exception as e:
        rich_label_error(e)
    pause()
