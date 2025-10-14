
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
    rich_input
)
from ...core.utils import clear_screen, parse_cnpj
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
        "Período Disponível": f"Período disponível: 2011 a {current_year}",
    }
    print_dict(header_dfp_text)

    codigo_empresa = rich_edit_input("Informe o código da empresa (ex: PETR):")
    if not codigo_empresa:
        rich_label_error("O código da empresa é obrigatório")
        pause()
        return

    year_input = rich_edit_input(f"Informe o ano para processar:", current_year)

    if year_input:
        try:
            year = int(year_input)
            if year <= 2010:
                rich_label_error("O Ano deve ser maior que 2010")
                pause()
                return
            if year > current_year:
                rich_label_error(f"O Ano deve ser menor ou igual a {current_year}")
                pause()
                return
        except ValueError:
            rich_label_error("O Ano deve ser um número válido")
            pause()
            return
    else:
        year = current_year

    rich_label_info(f"🚀 Iniciando o processamento do balanço da empresa {codigo_empresa} com DFP para o ano {year}...")
    rich_label_info("   Este processo pode levar alguns minutos...")
    try:
        
        service = BalancoService()
        indicadores = service.calcular_balanco_por_codigo(codigo_empresa, year)
        if indicadores:
            table_data = []
            for key, value in indicadores.items():
                table_data.append([key, value])
            render_table(table_data, headers=["Indicador", "Valor"], title=f"Indicadores Financeiros - {codigo_empresa} - {year}")
            rich_label_success("✅ Processamento de indicadores concluído com sucesso!")
        else:
            rich_label_info("Nenhum indicador calculado.")
    except Exception as e:
        rich_label_error(f"Erro ao processar indicadores: {str(e)}")