from datetime import datetime
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
    rich_input,
)
from ...core.utils import clear_screen, ValidationError
from app.services.balanco.balanco_service import BalancoService


MENU_ITENS = [
    "Exportar Balanço ",
    "Voltar",
]


def handle_menu_choice(choice: str) -> bool:
    match choice.lower():
        case "1":
            processar_balanco_flow()
        case "0" | "q" | "voltar" | "sair" | "exit":
            return False
        case _:
            rich_label_error("Opção inválida.")
            pause()
    return True


def balanco_menu():
    keep = True
    while keep:
        clear_screen()
        divider()
        title("Balanços")
        divider()
        show_menu_options(MENU_ITENS)
        divider()
        choice = prompt_menu_choice()
        keep = handle_menu_choice(choice)


# * PROCESSAMENTO DE BALANÇO
def processar_balanco_flow():
    clear_screen()
    divider()
    title("CVM - DFP | Processar Balanço")
    divider()

    current_year = datetime.now().year

    header_dfp_text = {
        "Fonte": "CVM - Formulário de Demonstrações Financeiras Padronizadas (DFP) - Companhias Abertas",
        "Período Disponível": f"Período disponível: últimos 5 anos + Últimos 12 meses(TTM)",
    }
    print_dict(header_dfp_text)

    codigo_empresa = rich_edit_input("Informe o código da empresa (ex: PETR):")
    if not codigo_empresa:
        rich_label_error("O código da empresa é obrigatório")
        pause()
        return

    rich_label_info(
        f"🚀 Iniciando o processamento dos balanços da empresa {codigo_empresa} ..."
    )
    rich_label_info("   Este processo pode levar alguns minutos...")
    try:

        service = BalancoService()
        xlsx_path = service.calcular_balanco_por_codigo(codigo_empresa)

        rich_label_success("✅ Processamento de indicadores concluído com sucesso!")
        rich_label_info(f"   Arquivo gerado: {xlsx_path}")
        pause()
    except ValidationError as ve:
        rich_label_error(f"Erro: {str(ve)}")
        pause()
    except Exception as e:
        rich_label_error(f"Erro: {str(e)}")
        pause()
