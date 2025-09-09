from decimal import Decimal
from tabulate import tabulate
from colorama import Fore, Style
from ..widgets import title, divider, pause
from ...core.utils import clear_screen
from ...db.repositories import carteiras_repo
from ...services.consultas_service import posicao_simples
from ...core.formatters import fmt_qty, fmt_money, fmt_price

def _input(t): 
	return input(Fore.WHITE + t + Style.RESET_ALL)

def _carteira_nome(cid: int) -> str:
	c = carteiras_repo.get_by_id(cid)
	return c["nome"] if c else f"#{cid}"

def tela_posicao_simples():
	clear_screen(); title("Posição Atual da Carteira")
	print("Algumas carteiras:")
	for c in carteiras_repo.list("", True, 0, 10):
		print(f"  {c['id']:>3} - {c['nome']}")
	try:
		cid = int(_input("Carteira (ID)*: ") or "0")
	except:
		print("ID inválido."); pause(); return

	data = _input("Data de referência (YYYY-MM-DD) [ENTER = hoje]: ").strip() or None

	rows = posicao_simples(cid, data)
	clear_screen()
	title(f"Posição — Carteira: { _carteira_nome(cid) }   Data Ref: {data or 'hoje'}")
	divider()

	if not rows:
		print("Nenhuma posição encontrada."); pause(); return

	table = []
	total_qtd = Decimal("0")
	total_valor_investido = Decimal("0")

	# Monta linhas
	for r in rows:
		q = r["quantidade_atual"]
		pm = r["preco_medio"]
		valor_inv = r["valor_investido"]

		# Totais
		total_qtd += q
		total_valor_investido += valor_inv

		table.append([
			r["codigo_negociacao"],
			fmt_qty(q),
			fmt_money(valor_inv),
			fmt_price(pm)
		])

	# Linha de totais
	table.append([
		Fore.CYAN + "**TOTAL**" + Style.RESET_ALL,
		Fore.CYAN + fmt_qty(total_qtd) + Style.RESET_ALL,
		Fore.CYAN + fmt_money(total_valor_investido) + Style.RESET_ALL,
		""
	])

	headers = [
		Fore.YELLOW + "Código de Negociação" + Style.RESET_ALL,
		Fore.YELLOW + "Quantidade Atual" + Style.RESET_ALL,
		Fore.YELLOW + "Valor Investido (R$)" + Style.RESET_ALL,
		Fore.YELLOW + "Preço Médio (R$)" + Style.RESET_ALL
	]
	
	print(tabulate(table, headers=headers, tablefmt="fancy_grid", stralign="right", numalign="right"))
	print()
	pause()