import os
from colorama import Fore, Style
from ..widgets import title, pause, confirm
from ...core.utils import clear_screen
from ...core.xlsx import list_sheets
from ...services.importacao_service import (
    import_cvm_companies,
    import_cvm_valores_mobiliarios,
    find_movimentacao_files,
    preview_movimentacao,
    importar_movimentacao,
    find_b3_posicao_files,
    validar_competencia,
    importar_b3_posicao,
    parse_data_referencia_from_filename,
    ValidationError,
)
from ...core.xlsx import list_sheets


def _input(t):
    return input(Fore.WHITE + t + Style.RESET_ALL)

def importar_empresas_cvm_flow():
    """Import CVM companies with year selection."""
    clear_screen()
    title("Importar Cadastro Empresas CVM")

    from datetime import datetime

    current_year = datetime.now().year

    year_input = _input(f"Ano [{current_year}]: ").strip()

    if year_input:
        try:
            year = int(year_input)
            if year < 2010:
                print("Erro: Ano deve ser ≥ 2010")
                pause()
                return
        except ValueError:
            print("Erro: Ano inválido")
            pause()
            return
    else:
        year = current_year

    print(f"Iniciando importação de empresas CVM para o ano {year}...")
    print("Isso pode levar alguns minutos...")

    try:
        inserted, updated, ignored, errors = import_cvm_companies(year)

        clear_screen()
        title("Importação CVM Concluída")
        print(f"Ano: {year}")
        print(f"Empresas incluídas: {inserted}")
        print(f"Empresas atualizadas: {updated}")
        print(f"Empresas ignoradas: {ignored}")
        print(f"Erros: {errors}")
        print(f"Total processado: {inserted + updated + ignored + errors}")

    except Exception as e:
        print(f"Erro durante importação: {e}")

    pause()

def importar_valores_mobiliarios_flow():
    """Import CVM valores mobiliarios with year selection."""
    clear_screen()
    title("Importar Cadastro Valores Mobiliarios CVM")

    from datetime import datetime

    current_year = datetime.now().year

    year_input = _input(f"Ano [{current_year}]: ").strip()

    if year_input:
        try:
            year = int(year_input)
            if year < 2010:
                print("Erro: Ano deve ser ≥ 2010")
                pause()
                return
        except ValueError:
            print("Erro: Ano inválido")
            pause()
            return
    else:
        year = current_year

    print(f"Iniciando importação de valores mobiliarios CVM para o ano {year}...")
    print("Isso pode levar alguns minutos...")

    try:
        inserted, updated, ignored, errors = import_cvm_valores_mobiliarios(year)

        clear_screen()
        title("Importação valores mobiliarios CVM Concluída")
        print(f"Ano: {year}")
        print(f"Valores Mobiliarios incluídos: {inserted}")
        print(f"Valores Mobiliarios atualizados: {updated}")
        print(f"Valores Mobiliarios ignorados: {ignored}")
        print(f"Erros: {errors}")
        print(f"Total processado: {inserted + updated + ignored + errors}")

    except Exception as e:
        print(f"Erro durante importação: {e}")

    pause()


def importar_b3_posicao_flow():
    """Import Planilha Posição Consolidada B3."""
    clear_screen()
    title("Importar [B3] Posição Consolidada")

    # Encontrar arquivos na pasta imports
    files = find_b3_posicao_files()

    if not files:
        print("Nenhum arquivo de posição consolidada encontrado na pasta 'imports'.")
        print(
            "Procurando arquivos no padrão: relatorio-consolidado-mensal-{ano}-{mes}.xlsx"
        )
        pause()
        return

    # Se múltiplos arquivos, deixar usuário escolher
    if len(files) == 1:
        selected_file = files[0]
        print(f"Arquivo encontrado: {os.path.basename(selected_file)}")
    else:
        print("Arquivos encontrados (até 10, ordenados por data de modificação):")
        for i, file in enumerate(files, 1):
            mtime = os.path.getmtime(file)
            import datetime

            mtime_str = datetime.datetime.fromtimestamp(mtime).strftime(
                "%d/%m/%Y %H:%M"
            )
            print(f"{i}. {os.path.basename(file)} ({mtime_str})")

        try:
            choice = int(_input("Escolha o arquivo (número): ").strip())
            if 1 <= choice <= len(files):
                selected_file = files[choice - 1]
            else:
                print("Opção inválida.")
                pause()
                return
        except ValueError:
            print("Entrada inválida.")
            pause()
            return

    print(f"\nProcessando arquivo: {os.path.basename(selected_file)}")

    try:
        # Verificar a data de referência no nome do arquivo
        data_ref = parse_data_referencia_from_filename(selected_file)

        sheets = list_sheets(selected_file)

        sheet_names = ["Posição - Ações", "Posição - Fundos", "Posição - Tesouro Direto", "Posição - Renda Fixa"]
        if not any(sheet in sheets for sheet in sheet_names):
            print("Arquivo não contém abas válidas para importação de posição consolidada.")
            pause()
            return

        print("-" * 100)

        if validar_competencia(data_ref):
            competencia = data_ref[:7]  # YYYY-MM
            print(f"Já existem dados para a competência {competencia}.")
            if not confirm("Sobrescrever dados existentes? (S/N) "):
                print("Importação cancelada.")
                pause()
                return

        # Confirmar importação
        if confirm("Confirmar importação? (S/N) "):

            inseridas, removidas, erros = importar_b3_posicao(selected_file, data_ref, sheets)

            # Relatório final
            clear_screen()
            title("Importação de Posição Consolidada Concluída")
            print(f"Arquivo: {os.path.basename(selected_file)}")
            print(f"Linhas inseridas: {inseridas}")
            if removidas > 0:
                print(f"Linhas removidas (sobrescrita): {removidas}")
            print(f"Erros: {erros}")
            print(f"Total processado: {inseridas + erros}")

            if erros > 0:
                print(f"{erros} linhas com erro foram ignoradas.")

            print(f"Arquivo movido para 'imports/processed'")

    except ValidationError as e:
        print(f"Erro: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

    pause()


def importar_movimentacao_b3_flow():
    clear_screen()
    title("Importar Movimentação da B3")

    # Encontrar arquivos na pasta imports
    files = find_movimentacao_files()

    if not files:
        print("Nenhum arquivo de movimentação encontrado na pasta 'imports'.")
        print(
            "Procure por arquivos no padrão: movimentacao_MM_AAAA.xlsx ou movimentacao_AAAA.xlsx"
        )
        pause()
        return

    # Se múltiplos arquivos, deixar usuário escolher
    if len(files) == 1:
        selected_file = files[0]
        print(f"Arquivo encontrado: {os.path.basename(selected_file)}")
    else:
        print("Múltiplos arquivos encontrados:")
        for i, file in enumerate(files, 1):
            print(f"{i}. {os.path.basename(file)}")

        try:
            choice = int(_input("Escolha o arquivo (número): ").strip())
            if 1 <= choice <= len(files):
                selected_file = files[choice - 1]
            else:
                print("Opção inválida.")
                pause()
                return
        except ValueError:
            print("Entrada inválida.")
            pause()
            return

    print(f"\nProcessando arquivo: {os.path.basename(selected_file)}")

    try:
        # Preview dos dados
        preview_data = preview_movimentacao(selected_file)

        if not preview_data:
            print("Arquivo não contém dados válidos para importação.")
            pause()
            return

        print(f"\nPreview das primeiras linhas:")
        print("-" * 80)
        for i, row in enumerate(preview_data[:5], 1):
            print(f"Linha {i}:")
            print(f"  Data: {row.get('data', 'N/A')}")
            print(f"  Movimentação: {row.get('movimentacao', 'N/A')}")
            print(f"  Código: {row.get('codigo', 'N/A')}")
            print(f"  Ativo: {row.get('ativo_descricao', 'N/A')}")
            print(f"  Quantidade: {row.get('quantidade', 'N/A')}")
            print(f"  Preço Unit.: {row.get('preco_unitario', 'N/A')}")
            print()

        if len(preview_data) > 5:
            print(f"... e mais {len(preview_data) - 5} linhas")

        print("-" * 80)

        # Confirmar importação
        if confirm("Confirmar importação? (S/N) "):
            inseridas, atualizadas, ignoradas, erros = importar_movimentacao(
                selected_file
            )

            # Relatório final
            clear_screen()
            title("Importação de Movimentação Concluída")
            print(f"Arquivo: {os.path.basename(selected_file)}")
            print(f"Linhas inseridas: {inseridas}")
            print(f"Linhas atualizadas: {atualizadas}")
            print(f"Linhas ignoradas: {ignoradas}")
            print(f"Erros: {erros}")
            print(f"Total processado: {inseridas + atualizadas + ignoradas + erros}")

            if erros > 0:
                print(f"\n⚠️  {erros} linhas com erro foram ignoradas.")

            if atualizadas > 0:
                print(f"ℹ️  {atualizadas} linhas já existiam e foram atualizadas.")

    except ValidationError as e:
        print(f"Erro: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

    pause()


def importacao_loop():
    while True:
        clear_screen()
        title("Importação")
        print("1. [CVM] Cadastro Empresas")
        print("2. [CVM] Valores Mobiliários")
        print("3. [B3] Posição consolidada")
        print("4. Importar Movimentação da B3")
        print("8. Voltar")
        ch = _input("> ").strip()
        if ch == "1":
            importar_empresas_cvm_flow()
        elif ch == "2":
            importar_valores_mobiliarios_flow()
        elif ch == "3":
            importar_b3_posicao_flow()
        elif ch == "4":
            importar_movimentacao_b3_flow()
        else:
            break
