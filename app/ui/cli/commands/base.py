"""
Classe base para comandos CRUD com padrões comuns.
"""
import typer
from typing import Protocol, List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich import print as rprint
from abc import ABC, abstractmethod

console = Console()

class CrudService(Protocol):
	"""Interface que os services devem implementar para CRUD."""
	
	def listar(self) -> List[Dict[str, Any]]:
		"""Lista todos os registros."""
		...
	
	def obter_por_id(self, id: int) -> Optional[Dict[str, Any]]:
		"""Obtém registro por ID."""
		...
	
	def criar(self, dados: Dict[str, Any]) -> Dict[str, Any]:
		"""Cria novo registro."""
		...
	
	def atualizar(self, id: int, dados: Dict[str, Any]) -> Dict[str, Any]:
		"""Atualiza registro existente."""
		...
	
	def excluir(self, id: int) -> bool:
		"""Exclui registro."""
		...

class BaseCrudCommand(ABC):
	"""Classe base para comandos CRUD."""
	
	def __init__(self, service: CrudService, entity_name: str, entity_name_plural: str):
		self.service = service
		self.entity_name = entity_name
		self.entity_name_plural = entity_name_plural
		self.app = typer.Typer(name=entity_name_plural)
		self._setup_commands()
	
	def _setup_commands(self):
		"""Registra os comandos CRUD padrão."""
		self.app.command(name="listar")(self.listar)
		self.app.command(name="criar")(self.criar)
		self.app.command(name="editar")(self.editar)
		self.app.command(name="excluir")(self.excluir)
		self.app.command(name="visualizar")(self.visualizar)
	
	def listar(self):
		"""Lista todos os registros."""
		try:
			registros = self.service.listar()
			if not registros:
				rprint(f"[yellow]Nenhum {self.entity_name} encontrado.[/yellow]")
				return
			
			self._render_list(registros)
			
		except Exception as e:
			console.print(f"[red]Erro ao listar {self.entity_name_plural}: {e}[/red]")
	
	def criar(self):
		"""Cria novo registro interativamente."""
		console.print(f"[bold green]Criar novo {self.entity_name}[/bold green]")
		
		while True:
			try:
				dados = self._collect_create_data()
				if dados is None:  # Usuário cancelou
					return
				
				resultado = self.service.criar(dados)
				console.print(f"[green]{self.entity_name} criado com sucesso![/green]")
				self._render_single(resultado)
				break
				
			except Exception as e:
				console.print(f"[red]Erro: {e}[/red]")
				if not Confirm.ask("Deseja tentar novamente?"):
					break
	
	def editar(self):
		"""Edita registro existente."""
		# Primeiro lista para o usuário escolher
		try:
			registros = self.service.listar()
			if not registros:
				rprint(f"[yellow]Nenhum {self.entity_name} encontrado para editar.[/yellow]")
				return
			
			self._render_list(registros)
			
			id_registro = IntPrompt.ask(f"ID do {self.entity_name} para editar")
			registro = self.service.obter_por_id(id_registro)
			
			if not registro:
				console.print(f"[red]{self.entity_name} não encontrado.[/red]")
				return
			
			console.print(f"[bold blue]Editando {self.entity_name}[/bold blue]")
			self._render_single(registro)
			
			while True:
				try:
					dados = self._collect_update_data(registro)
					if dados is None:  # Usuário cancelou
						return
					
					resultado = self.service.atualizar(id_registro, dados)
					console.print(f"[green]{self.entity_name} atualizado com sucesso![/green]")
					self._render_single(resultado)
					break
					
				except Exception as e:
					console.print(f"[red]Erro: {e}[/red]")
					if not Confirm.ask("Deseja tentar novamente?"):
						break
			
		except Exception as e:
			console.print(f"[red]Erro ao editar {self.entity_name}: {e}[/red]")
	
	def visualizar(self):
		"""Visualiza registro específico."""
		try:
			registros = self.service.listar()
			if not registros:
				rprint(f"[yellow]Nenhum {self.entity_name} encontrado.[/yellow]")
				return
			
			self._render_list(registros)
			
			id_registro = IntPrompt.ask(f"ID do {self.entity_name} para visualizar")
			registro = self.service.obter_por_id(id_registro)
			
			if not registro:
				console.print(f"[red]{self.entity_name} não encontrado.[/red]")
				return
			
			self._render_detail(registro)
			
		except Exception as e:
			console.print(f"[red]Erro ao visualizar {self.entity_name}: {e}[/red]")
	
	def excluir(self):
		"""Exclui registro."""
		try:
			registros = self.service.listar()
			if not registros:
				rprint(f"[yellow]Nenhum {self.entity_name} encontrado para excluir.[/yellow]")
				return
			
			self._render_list(registros)
			
			id_registro = IntPrompt.ask(f"ID do {self.entity_name} para excluir")
			registro = self.service.obter_por_id(id_registro)
			
			if not registro:
				console.print(f"[red]{self.entity_name} não encontrado.[/red]")
				return
			
			console.print(f"[bold red]Confirmação de exclusão[/bold red]")
			self._render_single(registro)
			
			if Confirm.ask(f"Tem certeza que deseja excluir este {self.entity_name}?"):
				self.service.excluir(id_registro)
				console.print(f"[green]{self.entity_name} excluído com sucesso![/green]")
			else:
				console.print("[yellow]Exclusão cancelada.[/yellow]")
				
		except Exception as e:
			console.print(f"[red]Erro ao excluir {self.entity_name}: {e}[/red]")
	
	# Métodos abstratos que devem ser implementados pelas classes filhas
	@abstractmethod
	def _render_list(self, registros: List[Dict[str, Any]]):
		"""Renderiza lista de registros."""
		pass
	
	@abstractmethod
	def _render_single(self, registro: Dict[str, Any]):
		"""Renderiza registro único (resumo)."""
		pass
	
	@abstractmethod
	def _render_detail(self, registro: Dict[str, Any]):
		"""Renderiza detalhes completos do registro."""
		pass
	
	@abstractmethod
	def _collect_create_data(self) -> Optional[Dict[str, Any]]:
		"""Coleta dados para criação. Retorna None se cancelado."""
		pass
	
	@abstractmethod
	def _collect_update_data(self, registro_atual: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		"""Coleta dados para atualização. Retorna None se cancelado."""
		pass