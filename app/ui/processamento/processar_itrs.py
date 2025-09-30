"""
Fluxo de processamento de ITRs
Pacote 03: CLI: Listar e Selecionar ITRs para Processamento
"""
from typing import Optional
from colorama import Fore, Style
from tabulate import tabulate
from ..widgets import title, divider, pause
from ...core.utils import clear_screen, ValidationError
from ...core.pagination import paginate
from ...core.formatters import paint_header
from ...db.repositories.importacao.itr_controle_repo import ItrControleRepository
from ...services.itr_process_service import ItrProcessService


def _input(prompt: str) -> str:
	"""Input com formatação padrão"""
	return input(Fore.WHITE + prompt + Style.RESET_ALL)


def processar_itrs_flow():
	"""
	Fluxo principal de listagem e processamento de ITRs
	"""
	clear_screen()
	title("Processar ITRs - Via Download do XML Informado na CVM")
    
	print("📋 " + paint_header("Formulário de Informações Trimestrais (ITR) - Companhias Abertas"))
	print(f"   Fonte: CVM - Comissão de Valores Mobiliários")
	print()
	
	# Filtros opcionais
	filtros = _obter_filtros()
	
	# Listar e selecionar ITR
	itr_selecionado = _listar_e_selecionar_itr(filtros)
	
	if itr_selecionado:
		_processar_itr_selecionado(itr_selecionado, filtros['consolidado'])


def _obter_filtros() -> dict:
	"""
	Obtém filtros opcionais do usuário
	"""
	print("Filtros (opcional - pressione Enter para pular):")
	print()
	
	razao_social = _input("Filtrar por razão social (contém): ").strip()
	cnpj = _input("Filtrar por CNPJ: ").strip()
	consolidado = _input("Consolidado ou Individual? (c/i): ").strip().lower()
	
	filtros = {}
	if razao_social:
		filtros['razao_social'] = razao_social
	if cnpj:
		filtros['cnpj'] = cnpj

	if not consolidado in ('c', 'i', ''):
		print(f"{Fore.YELLOW}Aviso: Considerando Individual por padrão.{Style.RESET_ALL}")
		filtros['consolidado'] = "i"
	else:
		filtros['consolidado'] = consolidado

	return filtros


def _listar_e_selecionar_itr(filtros: dict) -> Optional[dict]:
	"""
	Lista ITRs com paginação e permite seleção
	"""
	repo = ItrControleRepository()
	
	def fetch_data(limit: int, offset: int):
		return repo.list_not_processed(
			razao_social_filter=filtros.get('razao_social'),
			cnpj_filter=filtros.get('cnpj'),
			limit=limit,
			offset=offset
		)
	
	def count_data():
		return repo.count_not_processed(
			razao_social_filter=filtros.get('razao_social'),
			cnpj_filter=filtros.get('cnpj')
		)
	
	def render_item(item: dict, index: int):
		return [
			item['id'],
			item['cnpj'],
			item['razao_social'][:40] + "..." if len(item['razao_social']) > 40 else item['razao_social'],
			item['data_referencia'],
			item['versao'],
			item['categoria_documento']
		]
	
	headers = ['ID', 'CNPJ', 'Razão Social', 'Data Ref.', 'Versão', 'Categoria']
	
	# Mostrar filtros aplicados
	if filtros:
		print()
		print("Filtros aplicados:")
		for key, value in filtros.items():
			print(f"  {key}: {value}")
		print()
	
	selected_item = paginate(
		fetch_func=fetch_data,
		count_func=count_data,
		render_func=render_item,
		headers=headers,
		title="ITRs Não Processados",
		items_per_page=20
	)
	
	return selected_item


def _processar_itr_selecionado(itr: dict, consolidado: str):
	"""
	Processa o ITR selecionado
	"""
	clear_screen()
	title("Processamento de ITR")
	
	print("ITR selecionado:")
	print()
	
	# Exibir detalhes do ITR em tabela
	detalhes = [
		["ID", itr['id']],
		["CNPJ", itr['cnpj']],
		["Razão Social", itr['razao_social']],
		["Data Referência", itr['data_referencia']],
		["Versão", itr['versao']],
		["Código CVM", itr['codigo_cvm']],
		["Categoria", itr['categoria_documento']],
		["Data Recebimento", itr['data_recebimento']]
	]
	
	print(tabulate(detalhes, headers=["Campo", "Valor"], tablefmt="fancy_grid"))
	print()
	
	# Confirmar processamento
	confirmar = _input("Deseja processar este ITR? (s/N): ").strip().lower()
	
	if confirmar not in ['s', 'sim', 'y', 'yes']:
		print("Processamento cancelado.")
		return
	
	# Executar processamento
	try:
		print()
		print("Iniciando processamento...")
		print("Este processo pode levar alguns minutos.")
		print()
		
		service = ItrProcessService()
		resumo = service.processar_itr(itr['id'], consolidado=consolidado)
		
		# Exibir resultado do processamento
		_exibir_resultado_processamento(resumo)
	
	except ValidationError as e:
		clear_screen()
		title("Erro no Processamento")
		print(f"{Fore.RED}Erro: {str(e)}{Style.RESET_ALL}")
		print()
		print("Possíveis causas:")
		print("• ITR já foi processado anteriormente")
		print("• Arquivo XML não encontrado ou inválido")
		print("• Problemas de conexão com a internet")
		print("• Formato do XML não suportado")
	
	except Exception as e:
		clear_screen()
		title("Erro Inesperado")
		print(f"{Fore.RED}Erro inesperado: {str(e)}{Style.RESET_ALL}")
		print()
		print("Tente novamente ou contate o suporte técnico.")
	
	print()
	divider()


def _exibir_resultado_processamento(resumo: dict):
	"""
	Exibe o resultado do processamento
	"""
	clear_screen()
	title("Processamento Concluído")
	
	print(f"Empresa: {Fore.CYAN}{resumo['empresa']}{Style.RESET_ALL}")
	print(f"CNPJ: {resumo['cnpj']}")
	print(f"Período: {resumo['data_referencia']} (Versão {resumo['versao']})")
	print()
	
	# Resultado em tabela
	resultado = [
		["Status", f"{Fore.GREEN}✅ Sucesso{Style.RESET_ALL}"],
		["Registros Inseridos", f"{Fore.CYAN}{resumo['registros_inseridos']:,}{Style.RESET_ALL}"],
		["Versões Removidas", f"{Fore.YELLOW}Sim{Style.RESET_ALL}" if resumo['versoes_removidas'] else "Não"]
	]
	
	print(tabulate(resultado, headers=["Campo", "Valor"], tablefmt="fancy_grid"))
	print()
	
	print(f"{Fore.GREEN}🎉 ITR processado com sucesso!{Style.RESET_ALL}")
	print()
	print("Os dados extraídos incluem:")
	print("• Balanço Patrimonial (Ativo e Passivo)")
	print("• Demonstração do Resultado do Exercício (DRE)")
	print("• Informações de Capital Integralizado")
	print()
	print("Dados disponíveis para consultas e análises.")
	print()
	divider()