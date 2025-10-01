from colorama import Fore, Style
from datetime import datetime
from ..widgets import title, pause
from ...core.utils import clear_screen
from ...core.formatters import render_table, paint_header, paint_success, paint_warning, paint_error
from ...services.importacao.fca_import_service import FcaImportService , ValidationError
from ...services.importacao.itr_import_service import ItrImportService
from ...services.importacao.dfp_import_service import DfpImportService


def _input(t):
    return input(Fore.WHITE + t + Style.RESET_ALL)

#* IMPORTACAO DFP - INFORMAÇÕES ANUAIS
def importar_dfp_flow():
    """Importação DFP - Informações anuais de Empresas CVM com formatação tabular."""
    clear_screen()
    title("CVM - DFP | Importar Demontrações Financeiras Padronizadas")

    current_year = datetime.now().year

    print("📋 " + paint_header("Formulário de Demontrações Finaneiras Padronizadas (DFP) - Companhias Abertas"))
    print(f"   Fonte: CVM - Comissão de Valores Mobiliários")
    print(f"   Período disponível: 2011 a {current_year}")
    print()

    year_input = _input(f"Informe o ano para importação [{current_year}]: ").strip()

    if year_input:
        try:
            year = int(year_input)
            if year <= 2010:
                print()
                print(paint_error("❌ Erro: Ano deve ser maior que 2010"))
                pause()
                return
            if year > current_year:
                print()
                print(paint_error(f"❌ Erro: Ano deve ser menor ou igual a {current_year}"))
                pause()
                return
        except ValueError:
            print()
            print(paint_error("❌ Erro: Ano inválido"))
            pause()
            return
    else:
        year = current_year

    print()
    print(f"🚀 Iniciando importação DFP para o ano {paint_header(year)}...")
    print("   Este processo pode levar alguns minutos...")
    print()

    try:
        dfp_service = DfpImportService()
        resumo = dfp_service.importar_por_ano(year)

        # Relatório final com tabela
        clear_screen()
        title("Importação DFP - Relatório Final")
        
        print(f"📊 {paint_header('Ano:')} {year}")
        print()
        
        # Tabela de resultados
        headers = ["Arquivo", "Total Registros", "Inseridos", "Atualizados", "Ignorados", "Erros" ]
        rows = resumo
        
        print(render_table(rows, headers, tablefmt='fancy_grid'))
        print()
        
        #sum totals for resumo list
        processados = sum(r[1] for r in resumo)
        
        print(f"📈 {paint_header('Total processado:')} {processados} registros")
        
        # Mostrar erros se houver
        # if erros > 0 and lista_erros:
        #     print()
        #     print(paint_warning("⚠️  Detalhes dos erros:"))
        #     # Mostrar apenas os primeiros 10 erros para não poluir a tela
        #     for erro in lista_erros[:10]:
        #         print(f"   • {erro}")
        #     if len(lista_erros) > 10:
        #         print(f"   • ... e mais {len(lista_erros) - 10} erros")
        
        print()
        print(paint_success("✅ Importação concluída com sucesso!"))

    except ValidationError as e:
        clear_screen()
        title(paint_error("Erro na Importação ITR"))
        print()
        print(paint_error(f"❌ {str(e)}"))
        print()
        print("Verifique os parâmetros e tente novamente.")
        
    except Exception as e:
        clear_screen()
        title(paint_error("Erro Inesperado"))
        print()
        print(paint_error(f"❌ Erro durante importação: {str(e)}"))
        print()
        print("Verifique sua conexão de internet e tente novamente.")

    print()
    pause()

#* IMPORTACAO ITR - INFORMAÇÕES TRIMESTRAIS
def importar_itr_flow():
    """Importação ITR - Informações trimestrais de Empresas CVM com formatação tabular."""
    clear_screen()
    title("CVM - ITR | Importar Informações Trimestrais")

    current_year = datetime.now().year

    print("📋 " + paint_header("Formulário de Informações Trimestrais (ITR) - Companhias Abertas"))
    print(f"   Fonte: CVM - Comissão de Valores Mobiliários")
    print(f"   Período disponível: 2011 a {current_year}")
    print()

    year_input = _input(f"Informe o ano para importação [{current_year}]: ").strip()

    if year_input:
        try:
            year = int(year_input)
            if year <= 2010:
                print()
                print(paint_error("❌ Erro: Ano deve ser maior que 2010"))
                pause()
                return
            if year > current_year:
                print()
                print(paint_error(f"❌ Erro: Ano deve ser menor ou igual a {current_year}"))
                pause()
                return
        except ValueError:
            print()
            print(paint_error("❌ Erro: Ano inválido"))
            pause()
            return
    else:
        year = current_year

    print()
    print(f"🚀 Iniciando importação ITR para o ano {paint_header(year)}...")
    print("   Este processo pode levar alguns minutos...")
    print()

    try:
        itr_service = ItrImportService()
        resumo = itr_service.importar_por_ano(year)

        # Relatório final com tabela
        clear_screen()
        title("Importação ITR - Relatório Final")
        
        print(f"📊 {paint_header('Ano:')} {year}")
        print()
        
        # Tabela de resultados
        headers = ["Arquivo", "Total Registros", "Inseridos", "Atualizados", "Ignorados", "Erros" ]
        rows = resumo
        
        print(render_table(rows, headers, tablefmt='fancy_grid'))
        print()
        
        #sum totals for resumo list
        processados = sum(r[1] for r in resumo)
        
        print(f"📈 {paint_header('Total processado:')} {processados} registros")
        
        # Mostrar erros se houver
        # if erros > 0 and lista_erros:
        #     print()
        #     print(paint_warning("⚠️  Detalhes dos erros:"))
        #     # Mostrar apenas os primeiros 10 erros para não poluir a tela
        #     for erro in lista_erros[:10]:
        #         print(f"   • {erro}")
        #     if len(lista_erros) > 10:
        #         print(f"   • ... e mais {len(lista_erros) - 10} erros")
        
        print()
        print(paint_success("✅ Importação concluída com sucesso!"))

    except ValidationError as e:
        clear_screen()
        title(paint_error("Erro na Importação ITR"))
        print()
        print(paint_error(f"❌ {str(e)}"))
        print()
        print("Verifique os parâmetros e tente novamente.")
        
    except Exception as e:
        clear_screen()
        title(paint_error("Erro Inesperado"))
        print()
        print(paint_error(f"❌ Erro durante importação: {str(e)}"))
        print()
        print("Verifique sua conexão de internet e tente novamente.")

    print()
    pause()
    
#* IMPORTACAO FCA - CADASTRO DE EMPRESAS CVM
def importar_fca_cadastro_empresas_flow():
    """Importação FCA - Cadastro de Empresas CVM com formatação tabular."""
    clear_screen()
    title("CVM - FCA | Importar Cadastro de Empresas")

    current_year = datetime.now().year

    print("📋 " + paint_header("Formulário Cadastral (FCA) - Companhias Abertas"))
    print(f"   Fonte: CVM - Comissão de Valores Mobiliários")
    print(f"   Período disponível: 2011 a {current_year}")
    print()

    year_input = _input(f"Informe o ano para importação [{current_year}]: ").strip()

    if year_input:
        try:
            year = int(year_input)
            if year <= 2010:
                print()
                print(paint_error("❌ Erro: Ano deve ser maior que 2010"))
                pause()
                return
            if year > current_year:
                print()
                print(paint_error(f"❌ Erro: Ano deve ser menor ou igual a {current_year}"))
                pause()
                return
        except ValueError:
            print()
            print(paint_error("❌ Erro: Ano inválido"))
            pause()
            return
    else:
        year = current_year

    print()
    print(f"🚀 Iniciando importação FCA para o ano {paint_header(year)}...")
    print("   Este processo pode levar alguns minutos...")
    print()

    try:
        fca_service = FcaImportService()
        inseridos, atualizados, ignorados, erros, lista_erros = fca_service.importar_fca_por_ano(year)

        # Relatório final com tabela
        clear_screen()
        title("Importação FCA - Relatório Final")
        
        print(f"📊 {paint_header('Ano:')} {year}")
        print()
        
        # Tabela de resultados
        headers = ["Operação", "Quantidade", "Descrição"]
        rows = [
            ["Inseridas", paint_success(inseridos), "Novas empresas cadastradas"],
            ["Atualizadas", paint_warning(atualizados), "Empresas com dados atualizados"],  
            ["Ignoradas", ignorados, "Empresas com dados iguais/antigos"],
            ["Erros", paint_error(erros), "Linhas com problemas de validação"]
        ]
        
        print(render_table(rows, headers, tablefmt='fancy_grid'))
        print()
        
        total_processado = inseridos + atualizados + ignorados + erros
        print(f"📈 {paint_header('Total processado:')} {total_processado} registros")
        
        # Mostrar erros se houver
        if erros > 0 and lista_erros:
            print()
            print(paint_warning("⚠️  Detalhes dos erros:"))
            # Mostrar apenas os primeiros 10 erros para não poluir a tela
            for erro in lista_erros[:10]:
                print(f"   • {erro}")
            if len(lista_erros) > 10:
                print(f"   • ... e mais {len(lista_erros) - 10} erros")
        
        if inseridos > 0 or atualizados > 0:
            print()
            print(paint_success("✅ Importação concluída com sucesso!"))

    except ValidationError as e:
        clear_screen()
        title(paint_error("Erro na Importação FCA"))
        print()
        print(paint_error(f"❌ {str(e)}"))
        print()
        print("Verifique os parâmetros e tente novamente.")
        
    except Exception as e:
        clear_screen()
        title(paint_error("Erro Inesperado"))
        print()
        print(paint_error(f"❌ Erro durante importação: {str(e)}"))
        print()
        print("Verifique sua conexão de internet e tente novamente.")

    print()
    pause()

#* MENU DE IMPORTAÇÃO
def importacao_loop():
    while True:
        clear_screen()
        title("Importação")
        print("1. [CVM - FCA] Cadastro Empresas")
        print("2. [CVM - ITR] Informações Trimestrais")
        print("3. [CVM - DFP] Informações Anuais")
        print("4. [B3] Posição consolidada")
        print("5. [B3] Movimentação")
        print("6. [CVM] Cadastro de Fundos e Empresas")
        print("8. Voltar")
        ch = _input("> ").strip()
        if ch == "1":
            importar_fca_cadastro_empresas_flow()
        elif ch == "2":
            importar_itr_flow()
            pause()
        elif ch == "3":
            importar_dfp_flow()
            pause()
        elif ch == "4":
            #importar_movimentacao_b3_flow()
            print("Em desenvolvimento...")
            pause()
        elif ch == "5":
            #importar_fundos_empresas_flow()
            print("Em desenvolvimento...")
            pause()
        else:
            break
