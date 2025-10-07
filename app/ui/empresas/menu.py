from rich.console import Console
from rich.panel import Panel
from app.ui.empresas.empresa_ui import empresa_menu

console = Console()

def manutencao_cadastros_menu():
	while True:
		console.clear()
		console.print(Panel('[bold cyan]Manutenção de Cadastros[/bold cyan]', expand=False))
		console.print('[1] Empresas')
		console.print('[0] Voltar')
		op = console.input('\nEscolha uma opção: ').strip()
		if op == '1':
			empresa_menu()
		elif op == '0':
			break
