"""
Shell interativo principal do CLI Typer.
"""
import typer
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich import print as rprint

from app.ui.cli.commands.empresas import empresas_app

console = Console()

class InteractiveShell:
	def __init__(self):
		self.app = typer.Typer(
			name="D Mark II CLI",
			help="Terminal interativo para gerenciamento do sistema",
			no_args_is_help=True
		)
		self._setup_commands()
		self._running = True

	def _setup_commands(self):
		"""Registra todos os grupos de comandos disponíveis."""
		self.app.add_typer(empresas_app, name="empresas")
		
		# Comando especial para sair
		self.app.command()(self.sair)
		self.app.command()(self.help)

	def sair(self):
		"""Sair do terminal interativo."""
		if Confirm.ask("Deseja realmente sair do terminal interativo?"):
			self._running = False
			rprint("[green]Voltando ao menu principal...[/green]")
			raise typer.Exit()

	def help(self):
		"""Mostra comandos disponíveis."""
		self._show_available_commands()

	def _show_available_commands(self):
		"""Exibe lista formatada de comandos disponíveis."""
		table = Table(title="Comandos Disponíveis", show_header=True, header_style="bold blue")
		table.add_column("Comando", style="cyan", no_wrap=True)
		table.add_column("Descrição", style="white")
		
		table.add_row("/empresas", "CRUD de configuração de empresas")
		table.add_row("/help", "Mostra esta lista de comandos")
		table.add_row("/sair", "Volta ao menu principal")
		
		console.print(table)
		console.print("\n[yellow]Digite um comando precedido de '/' para continuar[/yellow]")
		console.print("[dim]Exemplo: /empresas buscar PETR4[/dim]")

	def run(self):
		"""Executa o shell interativo."""
		# Resetar estado ao iniciar nova sessão
		self._running = True
		
		console.print(Panel.fit(
			"[bold green]Terminal Interativo D Mark II[/bold green]\n"
			"Digite '/help' para ver comandos disponíveis",
			title="CLI Interativo"
		))
		
		while self._running:
			try:
				command = Prompt.ask(
					"[bold blue]dmarkii[/bold blue]",
					default="/help"
				).strip()
				
				if not command.startswith('/'):
					console.print("[red]Comando deve começar com '/'[/red]")
					continue
					
				# Remove a barra e processa o comando
				cmd_parts = command[1:].split()
				if not cmd_parts:
					continue
				
				# Verificar se é só o nome do comando principal (ex: /empresas)
				if len(cmd_parts) == 1 and cmd_parts[0] == "empresas":
					self._show_empresas_commands()
					continue
					
				# Executa o comando via Typer
				try:
					self.app(cmd_parts, standalone_mode=False)
				except typer.Exit:
					break
				except Exception as e:
					console.print(f"[red]Erro ao executar comando: {e}[/red]")
					
			except KeyboardInterrupt:
				if Confirm.ask("\nDeseja sair do terminal interativo?"):
					break
			except EOFError:
				break
				
		console.print("[green]Terminal interativo finalizado.[/green]")

	def _show_empresas_commands(self):
		"""Mostra comandos específicos do módulo empresas (versão especializada sem listar/visualizar)."""
		table = Table(title="Comandos do Módulo Empresas", show_header=True, header_style="bold green")
		table.add_column("Comando", style="cyan", no_wrap=True)
		table.add_column("Descrição", style="white")
		
		table.add_row("/empresas criar", "Cria nova empresa")
		table.add_row("/empresas buscar CODIGO", "Mostra detalhes da empresa pelo código")
		table.add_row("/empresas editar CODIGO", "Edita empresa pelo código")
		table.add_row("/empresas excluir CODIGO", "Exclui empresa pelo código (confirmação)")
		
		console.print(table)

# Instância global para uso no menu principal
interactive_shell = InteractiveShell()