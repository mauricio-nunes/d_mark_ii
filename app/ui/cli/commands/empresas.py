"""
Comandos CRUD para configuração de empresas.
"""
from typing import List, Dict, Any, Optional
import typer
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import print as rprint

from app.ui.cli.commands.base import BaseCrudCommand, console
from app.services.empresas.empresa_config_service import EmpresaConfigService
from app.db.repositories.empresas.empresa_config_repo import EmpresaConfigRepo
from app.db.connection import get_conn


class EmpresasConfigCrudCommand(BaseCrudCommand):
	"""Comandos para manutenção de empresas.

	Este CRUD especializado usa apenas:
	- criar: /empresas criar
	- buscar: /empresas buscar CODIGO
	- editar: /empresas editar CODIGO
	- excluir: /empresas excluir CODIGO

	Comandos padrão 'listar' e 'visualizar' foram intencionalmente removidos para acesso direto por código de negociação.
	"""

	def __init__(self):
		conn = get_conn()
		repo = EmpresaConfigRepo(conn)
		service = EmpresaConfigService(repo)
		super().__init__(service, "empresa", "empresas")
		# Atualiza help após construção da base
		self.app.help = (
			"Gerencia empresas por código de negociação.\n\n"
			"Comandos:\n"
			"  criar                Cria uma nova empresa\n"
			"  buscar CODIGO        Exibe detalhes da empresa\n"
			"  editar CODIGO        Edita a empresa\n"
			"  excluir CODIGO       Exclui a empresa (confirmação necessária)\n\n"
			"Exemplos:\n"
			"  /empresas criar\n"
			"  /empresas buscar PETR4\n"
			"  /empresas editar VALE3\n"
			"  /empresas excluir ITUB4"
		)

	def _setup_commands(self):  # override: registra apenas comandos permitidos
		self.app.command(name="criar")(self.criar)
		self.app.command(name="buscar")(self.buscar)
		self.app.command(name="editar")(self.editar)
		self.app.command(name="excluir")(self.excluir)
	
	
	def _render_single(self, registro: Dict[str, Any]):
		"""Renderiza empresa única (resumo)."""
		cnpj = registro.get('cnpj', '')
		cnpj_formatado = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}" if len(cnpj) == 14 else cnpj
		
		console.print(Panel(
			f"[bold]Código:[/bold] {registro.get('codigo_negociacao', '')}\n"
			f"[bold]CNPJ:[/bold] {cnpj_formatado}\n"
			f"[bold]Classificação:[/bold] {registro.get('classificacao', '') or 'Não definida'}\n"
			f"[bold]ID:[/bold] {registro.get('id', '')}",
			title=f"Empresa #{registro.get('id', '')}"
		))
	
	def _render_detail(self, registro: Dict[str, Any]):
		"""Renderiza detalhes completos da empresa."""
		cnpj = registro.get('cnpj', '')
		cnpj_formatado = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}" if len(cnpj) == 14 else cnpj
		
		detalhes = f"""
[bold]ID:[/bold] {registro.get('id', '')}
[bold]Código de Negociação:[/bold] {registro.get('codigo_negociacao', '')}
[bold]CNPJ:[/bold] {cnpj_formatado}
[bold]Classificação:[/bold] {registro.get('classificacao', '') or 'Não definida'}
[bold]Tipo DFP:[/bold] {registro.get('tipo_dfp', '') or 'Não definido'}
[bold]Modo de Análise:[/bold] {registro.get('modo_analise', '') or 'Não definido'}
[bold]Criado em:[/bold] {registro.get('criado_em', 'N/A')}
[bold]Atualizado em:[/bold] {registro.get('atualizado_em', 'N/A')}
		""".strip()
		
		console.print(Panel(detalhes, title="Detalhes da Empresa", expand=False))
	
	def _collect_create_data(self) -> Optional[Dict[str, Any]]:
		"""Coleta dados para criação de empresa."""
		
		
		cnpj = Prompt.ask("CNPJ (com ou sem formatação)")
		codigo_negociacao = Prompt.ask("Código de negociação")
		classificacao = Prompt.ask("Classificação", default="")
		
		# Tipo DFP
		tipo_dfp_opcoes = ["", "individual", "consolidado"]
		console.print("\nOpções para Tipo DFP:")
		for i, opcao in enumerate(tipo_dfp_opcoes):
			display = "Não definido" if opcao == "" else opcao
			console.print(f"  {i}. {display}")
		
		tipo_dfp_idx = IntPrompt.ask("Escolha o tipo DFP", default=0)
		tipo_dfp = tipo_dfp_opcoes[tipo_dfp_idx] if 0 <= tipo_dfp_idx < len(tipo_dfp_opcoes) else None
		
		# Modo de análise
		modo_analise_opcoes = ["", "padrao", "banco", "seguradora"]
		console.print("\nOpções para Modo de Análise:")
		for i, opcao in enumerate(modo_analise_opcoes):
			display = "Não definido" if opcao == "" else opcao
			console.print(f"  {i}. {display}")
		
		modo_analise_idx = IntPrompt.ask("Escolha o modo de análise", default=0)
		modo_analise = modo_analise_opcoes[modo_analise_idx] if 0 <= modo_analise_idx < len(modo_analise_opcoes) else None
		
		return {
			'cnpj': cnpj,
			'codigo_negociacao': codigo_negociacao,
			'classificacao': classificacao if classificacao else None,
			'tipo_dfp': tipo_dfp if tipo_dfp else None,
			'modo_analise': modo_analise if modo_analise else None
		}
	
	def _collect_update_data(self, registro_atual: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		"""Coleta dados para atualização de empresa."""
		if not Confirm.ask("Deseja editar esta empresa?"):
			return None
		
		dados = {}
		
		# CNPJ
		cnpj_atual = registro_atual.get('cnpj', '')
		cnpj_formatado = f"{cnpj_atual[:2]}.{cnpj_atual[2:5]}.{cnpj_atual[5:8]}/{cnpj_atual[8:12]}-{cnpj_atual[12:]}" if len(cnpj_atual) == 14 else cnpj_atual
		novo_cnpj = Prompt.ask("CNPJ", default=cnpj_formatado)
		if novo_cnpj != cnpj_formatado:
			dados['cnpj'] = novo_cnpj
		
		# Código de negociação
		novo_codigo = Prompt.ask(
			"Código de negociação", 
			default=registro_atual.get('codigo_negociacao', '')
		)
		if novo_codigo != registro_atual.get('codigo_negociacao', ''):
			dados['codigo_negociacao'] = novo_codigo
		
		# Classificação
		nova_classificacao = Prompt.ask(
			"Classificação", 
			default=registro_atual.get('classificacao', '') or ""
		)
		if nova_classificacao != (registro_atual.get('classificacao', '') or ""):
			dados['classificacao'] = nova_classificacao if nova_classificacao else None
		
		# Tipo DFP
		if Confirm.ask("Deseja alterar o tipo DFP?", default=False):
			tipo_dfp_opcoes = [None, "individual", "consolidado"]
			console.print("\nOpções para Tipo DFP:")
			for i, opcao in enumerate(tipo_dfp_opcoes):
				display = "Não definido" if opcao is None else opcao
				atual = " (atual)" if opcao == registro_atual.get('tipo_dfp') else ""
				console.print(f"  {i}. {display}{atual}")
			
			tipo_dfp_idx = IntPrompt.ask("Escolha o tipo DFP")
			if 0 <= tipo_dfp_idx < len(tipo_dfp_opcoes):
				novo_tipo_dfp = tipo_dfp_opcoes[tipo_dfp_idx]
				if novo_tipo_dfp != registro_atual.get('tipo_dfp'):
					dados['tipo_dfp'] = novo_tipo_dfp
		
		# Modo de análise
		if Confirm.ask("Deseja alterar o modo de análise?", default=False):
			modo_analise_opcoes = [None, "padrao", "banco", "seguradora"]
			console.print("\nOpções para Modo de Análise:")
			for i, opcao in enumerate(modo_analise_opcoes):
				display = "Não definido" if opcao is None else opcao
				atual = " (atual)" if opcao == registro_atual.get('modo_analise') else ""
				console.print(f"  {i}. {display}{atual}")
			
			modo_analise_idx = IntPrompt.ask("Escolha o modo de análise")
			if 0 <= modo_analise_idx < len(modo_analise_opcoes):
				novo_modo_analise = modo_analise_opcoes[modo_analise_idx]
				if novo_modo_analise != registro_atual.get('modo_analise'):
					dados['modo_analise'] = novo_modo_analise
		
		return dados if dados else None
	
	# ==== Comandos customizados (sem listar/visualizar) ====

	def buscar(self, codigo_negociacao: str = typer.Argument(..., help="Código exato de negociação")):
		"""Busca empresa por código de negociação (exato, case-insensitive) e exibe detalhes."""
		try:
			codigo = codigo_negociacao.strip().upper()
			registro = self.service.obter_por_codigo(codigo)
			if not registro:
				rprint(f"[yellow]Empresa não encontrada com código '{codigo_negociacao}'.[/yellow]")
				return
			self._render_detail(registro)
		except Exception as e:
			console.print(f"[red]Erro ao buscar empresa: {e}[/red]")

	def editar(self, codigo_negociacao: str = typer.Argument(..., help="Código exato de negociação")):
		"""Edita empresa identificada pelo código de negociação (fluxo de edição permanece o mesmo)."""
		try:
			codigo = codigo_negociacao.strip().upper()
			registro = self.service.obter_por_codigo(codigo)
			if not registro:
				rprint(f"[yellow]Empresa não encontrada com código '{codigo_negociacao}'.[/yellow]")
				return
			console.print(f"[bold blue]Editando empresa[/bold blue]")
			self._render_single(registro)
			while True:
				try:
					dados = self._collect_update_data(registro)
					if dados is None:
						return
					resultado = self.service.atualizar(registro['id'], dados)
					console.print(f"[green]Empresa atualizada com sucesso![/green]")
					self._render_single(resultado)
					break
				except Exception as e:
					console.print(f"[red]Erro: {e}[/red]")
					if not Confirm.ask("Deseja tentar novamente?"):
						break
		except Exception as e:
			console.print(f"[red]Erro ao editar empresa: {e}[/red]")

	def excluir(self, codigo_negociacao: str = typer.Argument(..., help="Código exato de negociação")):
		"""Exclui empresa identificada pelo código de negociação após confirmação."""
		try:
			codigo = codigo_negociacao.strip().upper()
			registro = self.service.obter_por_codigo(codigo)
			if not registro:
				rprint(f"[yellow]Empresa não encontrada com código '{codigo_negociacao}'.[/yellow]")
				return
			console.print(f"[bold red]Confirmação de exclusão[/bold red]")
			self._render_detail(registro)
			if Confirm.ask("Tem certeza que deseja excluir esta empresa?"):
				self.service.excluir(registro['id'])
				console.print("[green]Empresa excluída com sucesso![/green]")
			else:
				console.print("[yellow]Exclusão cancelada.[/yellow]")
		except Exception as e:
			console.print(f"[red]Erro ao excluir empresa: {e}[/red]")


# Instância do comando para registro no shell
empresas_command = EmpresasConfigCrudCommand()
empresas_app = empresas_command.app