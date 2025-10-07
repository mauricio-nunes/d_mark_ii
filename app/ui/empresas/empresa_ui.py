from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from app.services.empresas.empresa_service import EmpresaService

console = Console()
service = EmpresaService()

def empresa_menu():
	while True:
		console.clear()
		console.print(Panel('[bold cyan]Cadastro de Empresas[/bold cyan]', expand=False))
		console.print('[1] Listar empresas')
		console.print('[2] Buscar empresa (CNPJ ou código)')
		console.print('[3] Adicionar nova empresa')
		console.print('[4] Editar empresa existente')
		console.print('[5] Exportar cadastro para CSV')
		console.print('[0] Voltar')
		op = console.input('\nEscolha uma opção: ').strip()
		if op == '1':
			listar_empresas()
		elif op == '2':
			buscar_empresa()
		elif op == '3':
			adicionar_empresa()
		elif op == '4':
			editar_empresa()
		elif op == '5':
			exportar_csv()
		elif op == '0':
			break

def listar_empresas():
	page = 1
	while True:
		empresas, total = service.listar_empresas(page)
		table = Table(title=f'Empresas - Página {page}')
		table.add_column('CNPJ')
		table.add_column('Código')
		table.add_column('Classificação')
		table.add_column('Tipo DFP')
		table.add_column('Modo Análise')
		for e in empresas:
			table.add_row(e['cnpj'], e['codigo_negociacao'], str(e['classificacao'] or ''), str(e['tipo_dfp'] or ''), str(e['modo_analise'] or ''))
		console.print(table)
		console.print(f'[bold]Total:[/bold] {total}')
		op = console.input('[N] Próxima | [P] Anterior | [Q] Sair: ').strip().lower()
		if op == 'n':
			page += 1
		elif op == 'p' and page > 1:
			page -= 1
		elif op == 'q':
			break

def buscar_empresa():
	query = console.input('Digite o CNPJ ou código de negociação: ').strip()
	empresa = service.buscar_empresa(query)
	if empresa:
		console.print(Panel(str(empresa), title='Empresa encontrada'))
		op = console.input('[E] Editar | [V] Voltar: ').strip().lower()
		if op == 'e':
			editar_empresa(empresa['cnpj'])
	else:
		console.print('[red]Empresa não encontrada.[/red]')
		console.input('Pressione ENTER para voltar.')

def adicionar_empresa():
	console.print('[bold]Adicionar nova empresa[/bold]')
	cnpj = console.input('CNPJ: ').strip()
	codigo = console.input('Código de negociação: ').strip()
	classificacao = console.input('Classificação (opcional): ').strip()
	tipo_dfp = console.input('Tipo DFP (opcional): ').strip()
	modo_analise = console.input('Modo análise (opcional): ').strip()
	try:
		service.adicionar_empresa(cnpj, codigo, classificacao, tipo_dfp, modo_analise)
		console.print('[green]Empresa adicionada com sucesso![/green]')
	except Exception as e:
		console.print(f'[red]{e}[/red]')
	console.input('Pressione ENTER para voltar.')

def editar_empresa(cnpj=None):
	if not cnpj:
		cnpj = console.input('Digite o CNPJ da empresa para editar: ').strip()
	empresa = service.buscar_empresa(cnpj)
	if not empresa:
		console.print('[red]Empresa não encontrada.[/red]')
		console.input('Pressione ENTER para voltar.')
		return
	console.print('[bold]Editar empresa[/bold]')
	console.print(f'CNPJ: {empresa["cnpj"]} (não editável)')
	codigo = console.input(f'Código [{empresa["codigo_negociacao"]}]: ').strip() or empresa['codigo_negociacao']
	classificacao = console.input(f'Classificação [{empresa["classificacao"] or ""}]: ').strip() or empresa['classificacao']
	tipo_dfp = console.input(f'Tipo DFP [{empresa["tipo_dfp"] or ""}]: ').strip() or empresa['tipo_dfp']
	modo_analise = console.input(f'Modo análise [{empresa["modo_analise"] or ""}]: ').strip() or empresa['modo_analise']
	try:
		service.editar_empresa(empresa['cnpj'], codigo, classificacao, tipo_dfp, modo_analise)
		console.print('[green]Empresa atualizada com sucesso![/green]')
	except Exception as e:
		console.print(f'[red]{e}[/red]')
	console.input('Pressione ENTER para voltar.')

def exportar_csv():
	try:
		path = service.exportar_csv()
		console.print(f'[green]Exportação concluída: {path}[/green]')
	except Exception as e:
		console.print(f'[red]{e}[/red]')
	console.input('Pressione ENTER para voltar.')
