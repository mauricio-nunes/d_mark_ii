from datetime import datetime
from rich.console import Console
from ..forms import (
    rich_label_error,
    rich_label_info,
    rich_label_warning,
    rich_edit_input,
    rich_label,
    rich_input
)
from ..widgets import (
    title,
    pause,
    divider,
    show_menu_options,
    prompt_menu_choice,
    print_dict,
    render_table,
)
from ...core.utils import clear_screen
from ...services.importacao.fca_import_service import FcaImportService, ValidationError
from ...services.importacao.itr_import_service import ItrImportService
from ...services.importacao.dfp_import_service import DfpImportService

console = Console()

MENU_ITENS = [
    "CVM - FCA | Cadastro de Empresas",
    "CVM - ITR | Informações Trimestrais",
    "CVM - DFP | Informações Anuais",
    "B3 | Posição consolidada",
    "B3 | Movimentação",
    "Voltar",
]


def handle_menu_choice(choice: str) -> bool:
    match choice.lower():
        case "1":
            importar_fca_cadastro_empresas_flow()
        case "2":
            importar_itr_flow()
        case "3":
            importar_dfp_flow()
        case "4":
            rich_label_info("Em desenvolvimento...")
            pause()
        case "5":
            rich_label_info("Em desenvolvimento...")
            pause()
        case "0" | "q" | "voltar" | "sair" | "exit" | "6":
            return False
        case _:
            rich_label_error("Opção inválida.")
            pause()
    return True





# * IMPORTACAO DFP - INFORMAÇÕES ANUAIS
def importar_dfp_flow():
    """Importação DFP - Informações anuais de Empresas CVM com formatação tabular."""
    clear_screen()
    divider()
    title("CVM - DFP | Importar Demontrações Financeiras Padronizadas")
    divider()

    current_year = datetime.now().year

    header_dfp_text = {
        "Fonte": "CVM - Formulário de Demonstrações Financeiras Padronizadas (DFP) - Companhias Abertas",
        "Período Disponível": f"Período disponível: 2011 a {current_year}",
    }
    print_dict(header_dfp_text)

    year_input = rich_input(f"Informe o ano para importação [{current_year}]: ").strip()

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

    rich_label_info(f"🚀 Iniciando importação DFP para o ano {year}...")
    rich_label_info("   Este processo pode levar alguns minutos...")

    try:
        dfp_service = DfpImportService()
        resumo = dfp_service.importar_por_ano(year)

        # Relatório final com tabela
        clear_screen()
        title(f"Importação DFP - Relatório Final - Ano {year}")

        # Tabela de resultados
        headers = [
            "Arquivo",
            "Total Registros",
            "Inseridos",
            "Atualizados",
            "Ignorados",
            "Erros",
        ]
        rows = resumo

        # sum totals for resumo list
        processados = sum(r[1] for r in resumo)
        render_table("Resumo da Importação DFP", processados, 1, 1, headers, rows)
        rich_label_info("✅ Importação concluída com sucesso!")

    except ValidationError as e:
        clear_screen()
        rich_label_error("Erro na Importação ITR")
        rich_label_error(f"❌ {str(e)}")
        rich_label_error("Verifique os parâmetros e tente novamente.")

    except Exception as e:
        clear_screen()
        rich_label_error("Erro Inesperado")
        rich_label_error(f"❌ Erro durante importação: {str(e)}")
        rich_label_error("Verifique sua conexão de internet e tente novamente.")

    pause()


# * IMPORTACAO ITR - INFORMAÇÕES TRIMESTRAIS
def importar_itr_flow():
    """Importação ITR - Informações trimestrais de Empresas CVM com formatação tabular."""
    clear_screen()
    divider()
    title("CVM - ITR | Importar Informações Trimestrais")
    divider()

    current_year = datetime.now().year
    header_itr_text = {
        "Fonte": "CVM - Formulário de Informações Trimestrais (ITR) - Companhias Abertas",
        "Período Disponível": f"Período disponível: 2011 a {current_year}",
    }
    print_dict(header_itr_text)

    year_input = rich_input(f"Informe o ano para importação [{current_year}]: ").strip()

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

    rich_label_info(f"🚀 Iniciando importação ITR para o ano {year}...")
    rich_label_info("   Este processo pode levar alguns minutos...")

    try:
        itr_service = ItrImportService()
        resumo = itr_service.importar_por_ano(year)

        # Relatório final com tabela
        clear_screen()
        title(f"Importação ITR - Relatório Final - Ano {year}")

        # Tabela de resultados
        headers = [
            "Arquivo",
            "Total Registros",
            "Inseridos",
            "Atualizados",
            "Ignorados",
            "Erros",
        ]
        rows = resumo

        # sum totals for resumo list
        processados = sum(r[1] for r in resumo)

        render_table("Resumo da Importação ITR", processados, 1, 1, headers, rows)

        rich_label_info("✅ Importação concluída com sucesso!")

    except ValidationError as e:
        clear_screen()
        rich_label_error("Erro na Importação ITR")
        rich_label_error(f"❌ {str(e)}")
        rich_label_error("Verifique os parâmetros e tente novamente.")

    except Exception as e:
        clear_screen()
        rich_label_error("Erro Inesperado")
        rich_label_error(f"❌ Erro durante importação: {str(e)}")
        rich_label_error("Verifique sua conexão de internet e tente novamente.")

    pause()


# * IMPORTACAO FCA - CADASTRO DE EMPRESAS CVM
def importar_fca_cadastro_empresas_flow():
    """Importação FCA - Cadastro de Empresas CVM com formatação tabular."""
    clear_screen()
    divider()
    title("CVM - FCA | Importar Cadastro de Empresas")
    divider()

    current_year = datetime.now().year

    header_fca_text = {
        "Fonte": "CVM - Formulário Cadastral (FCA) - Companhias Abertas",
        "Período Disponível": f"Período disponível: 2011 a {current_year}",
    }
    print_dict(header_fca_text)

    year_input = rich_edit_input(
        f"Informe o ano para importação: ", str(current_year)
    ).strip()

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

    rich_label_info(f"🚀 Iniciando importação FCA para o ano {year}...")
    rich_label_info("   Este processo pode levar alguns minutos...")

    try:
        fca_service = FcaImportService()
        inseridos, atualizados, ignorados, erros, lista_erros = (
            fca_service.importar_fca_por_ano(year)
        )

        # Relatório final com tabela
        clear_screen()
        title(f"Importação FCA - Relatório Final - Ano {year}")

        # Tabela de resultados
        headers = ["Operação", "Quantidade", "Descrição"]
        rows = [
            ["Inseridas", inseridos, "Novas empresas cadastradas"],
            ["Atualizadas", atualizados, "Empresas com dados atualizados"],
            ["Ignoradas", ignorados, "Empresas com dados iguais/antigos"],
            ["Erros", erros, "Linhas com problemas de validação"],
        ]

        render_table(
            "Resumo da Importação FCA",
            inseridos + atualizados + ignorados + erros,
            1,
            1,
            headers,
            rows,
        )

        # Mostrar erros se houver
        if erros > 0 and lista_erros:

            rich_label_warning("⚠️  Detalhes dos erros:")
            # Mostrar apenas os primeiros 10 erros para não poluir a tela
            for erro in lista_erros[:10]:
                rich_label(f"   • {erro}")
            if len(lista_erros) > 10:
                rich_label(f"   • ... e mais {len(lista_erros) - 10} erros")

        if inseridos > 0 or atualizados > 0:
            rich_label_info("✅ Importação concluída com sucesso!")

    except ValidationError as e:
        clear_screen()
        rich_label_error("Erro na Importação FCA")
        rich_label_error(f"❌ {str(e)}")
        rich_label_error("Verifique os parâmetros e tente novamente.")

    except Exception as e:
        clear_screen()
        rich_label_error("Erro Inesperado")
        rich_label_error(f"❌ Erro durante importação: {str(e)}")
        rich_label_error("Verifique sua conexão de internet e tente novamente.")

    pause()


# * MENU DE IMPORTAÇÃO
def importacao_loop():
    keep = True
    while keep:
        clear_screen()
        divider()
        title("Importação de Dados")
        divider()
        show_menu_options(MENU_ITENS)
        divider()
        choice = prompt_menu_choice().strip()
        keep = handle_menu_choice(choice)
