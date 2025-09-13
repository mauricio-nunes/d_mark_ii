from ..widgets import title, pause
from ...core.utils import clear_screen
from ...services.consolidacao_service import listar_carteiras, consolidar_movimentacao, ValidationError
from colorama import Fore, Style
from tabulate import tabulate
from ...core.formatters import fmt_money, fmt_qty

def tela_consolidar_movimentacao():
    clear_screen()
    title("Consolidar Movimentação")

    # Verificar carteiras
    wallets = listar_carteiras()
    if not wallets:
        print("Nenhuma carteira cadastrada. Você deve cadastrar uma carteira primeiro.")
        pause()
        return

    print("Carteiras disponíveis:")
    for w in wallets:
        print(f"  {w['id']:>3} - {w['nome']}")

    try:
        carteira_id = int(input("Digite o ID da carteira: "))
    except ValueError:
        print("ID inválido.")
        pause()
        return

    if not any(w['id'] == carteira_id for w in wallets):
        print("Carteira não encontrada.")
        pause()
        return

    ticker = input("Digite o ticker do ativo a consolidar: ").strip().upper()
    if not ticker:
        print("Ticker obrigatório.")
        pause()
        return

    dry_run_input = input("Dry run? (S/N): ").strip().upper()
    dry_run = dry_run_input == "S"

    try:
        transacoes = consolidar_movimentacao(carteira_id, ticker, dry_run)
        if dry_run:
            print("Modo Dry Run - Simulação:")
            
            headers = ['Data', 'Tipo', 'Quantidade', 'Ticker', 'Preço Unitário', 'Quantidade Total', 'Valor Investido', 'Preço Médio']
            rows = [
                [
                        tx['data'],
                        tx['tipo'],
                        tx['quantidade'],
                        tx['ticker'],
                        f"R$ {fmt_money(tx['preco_unitario'])}",
                        tx['quantidade_total'],
                        fmt_money(tx['valor_investido']),
                        fmt_money(tx['preco_medio'])
                ]
                for tx in transacoes
            ]

            print(f'{Fore.CYAN}{Style.BRIGHT}Movimentações simuladas:{Style.RESET_ALL}')
            print(tabulate(rows, headers, tablefmt='fancy_grid'))
        
    except ValidationError as e:
        print(f"Erro: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

    pause()
