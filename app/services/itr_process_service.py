"""
Serviço para processamento de ITRs (download XML, parse e persistência)
Pacote 04: Processamento do ITR (Download XML, Parse e Persistência)
"""
import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
import requests

from ..db.repositories.importacao.itr_controle_repo import ItrControleRepository
from ..db.repositories.itr_dados_repo import ItrDadosRepository
from ..db.connection import get_conn
from ..core.utils import ValidationError, parse_date


class ItrProcessService:
	
	def __init__(self):
		self.controle_repo = ItrControleRepository()
		self.dados_repo = ItrDadosRepository()
		self.namespace = {}
	
	def processar_itr(self, itr_id: int, consolidado: str) -> Dict[str, Any]:
		"""
		Processa um ITR específico baixando o XML e extraindo os dados.
		Retorna resumo do processamento.
		"""
		# Buscar dados do ITR
		itr_controle = self.controle_repo.get_by_id(itr_id)
		if not itr_controle:
			raise ValidationError(f"ITR com ID {itr_id} não encontrado")
		
		if itr_controle['processado'] == 1:
			raise ValidationError("ITR já foi processado anteriormente")
		
		# Verificar versionamento
		max_versao = self.controle_repo.get_max_version_for_period(
			itr_controle['cnpj'], 
			itr_controle['data_referencia']
		)
		
		if itr_controle['versao'] <= max_versao:
			# Verificar se já existe processado para esta versão
			if self.dados_repo.exists_for_context(
				itr_controle['cnpj'], 
				itr_controle['data_referencia'], 
				itr_controle['versao']
			):
				raise ValidationError("ITR desta versão já foi processado")
		
		# Iniciar transação global
		conn = get_conn()
		try:
			conn.execute("BEGIN TRANSACTION")
			
			# Baixar e processar XML
			print(f"Baixando XML do ITR: {itr_controle['razao_social']} - {itr_controle['data_referencia']}")
			xml_content = self._download_and_extract_xml(
				itr_controle['link_documento'], 
				itr_controle['codigo_cvm']
			)
			
			print("Parseando XML e extraindo dados...")
			dados_extraidos = self._parse_xml_itr(xml_content, itr_controle, consolidado)
			
			# Se versão maior, remover versões anteriores
			if itr_controle['versao'] > max_versao:
				deleted = self.dados_repo.delete_previous_versions(
					itr_controle['cnpj'],
					itr_controle['data_referencia'],
					itr_controle['versao']
				)
				print(f"Removidas {deleted} linhas de versões anteriores")
			
			# Inserir novos dados
			print(f"Inserindo {len(dados_extraidos)} registros...")
			inserted = self.dados_repo.insert_batch(dados_extraidos)
			# Marcar como processado
			self.controle_repo.mark_as_processed(itr_id)
			
			conn.commit()
			
			resumo = {
				'status': 'sucesso',
				'empresa': itr_controle['razao_social'],
				'cnpj': itr_controle['cnpj'],
				'data_referencia': itr_controle['data_referencia'],
				'versao': itr_controle['versao'],
				'registros_inseridos': inserted,
				'versoes_removidas': itr_controle['versao'] > max_versao
			}
			
			print("ITR processado com sucesso!")
			return resumo
			
		except Exception as e:
			conn.rollback()
			raise ValidationError(f"Erro no processamento do ITR: {str(e)}")
		finally:
			conn.close()

	def _download_and_extract_xml(self, link_documento: str, codigo_cvm: str) -> str:
		"""
		Baixa o ZIP do link_documento e extrai o XML com prefixo codigo_cvm
		"""
		with tempfile.TemporaryDirectory() as temp_dir:
			zip_path = os.path.join(temp_dir, "itr.zip")
			
			# Download do ZIP com tratamento robusto
			try:
				print(f"Baixando arquivo: {link_documento}")
				response = requests.get(link_documento, timeout=120, stream=True)
				response.raise_for_status()
				
				# Verificar tamanho se disponível
				content_length = response.headers.get('content-length')
				if content_length:
					size_mb = int(content_length) / (1024 * 1024)
					print(f"Tamanho do arquivo: {size_mb:.1f} MB")
				
				# Download por chunks para arquivos grandes
				with open(zip_path, 'wb') as f:
					for chunk in response.iter_content(chunk_size=8192):
						if chunk:
							f.write(chunk)
				
				print(f"Download concluído: {os.path.getsize(zip_path):,} bytes")
				
			except requests.RequestException as e:
				raise ValidationError(f"Erro no download do XML: {str(e)}")
			
			# Extrair XML correto
			try:
				with zipfile.ZipFile(zip_path, 'r') as zip_file:
					xml_files = [f for f in zip_file.namelist() if f.startswith(codigo_cvm) and f.endswith('.xml')]
					
					if not xml_files:
						available = ', '.join(zip_file.namelist()[:10])  # Limitar listagem
						if len(zip_file.namelist()) > 10:
							available += f" ... e mais {len(zip_file.namelist()) - 10} arquivos"
						raise ValidationError(f"XML com prefixo '{codigo_cvm}' não encontrado. Arquivos: {available}")
					
					if len(xml_files) > 1:
						print(f"Aviso: Múltiplos XMLs encontrados, usando o primeiro: {xml_files[0]}")
					
					xml_filename = xml_files[0]
					print(f"Extraindo XML: {xml_filename}")
					
					try:
						xml_content = zip_file.read(xml_filename).decode('utf-8')
					except UnicodeDecodeError:
						# Tentar outros encodings
						try:
							xml_content = zip_file.read(xml_filename).decode('latin1')
							print("Aviso: XML lido com encoding latin1")
						except UnicodeDecodeError:
							xml_content = zip_file.read(xml_filename).decode('utf-8', errors='ignore')
							print("Aviso: XML lido com erro de encoding ignorado")
					
					print(f"XML extraído com sucesso: {len(xml_content):,} caracteres")
					return xml_content
			
			except zipfile.BadZipFile:
				raise ValidationError("Arquivo ZIP inválido ou corrompido")

	def _parse_xml_itr(self, xml_content: str, itr_controle: Dict[str, Any], consolidado: str) -> List[Dict[str, Any]]:
		"""
		Parse do XML extraindo os dados das demonstrações
		"""
		try:
			root = ET.fromstring(xml_content)
		except ET.ParseError as e:
			raise ValidationError(f"XML inválido: {str(e)}")
		
		# Definir namespace se existir
		self.namespace = {}
		if root.tag.startswith('{'):
			ns_uri = root.tag.split('}')[0][1:]
			self.namespace = {'ns': ns_uri}
		
		# Extrair contexto base
		contexto = self._extrair_contexto_xml(root, itr_controle)
		
		# Determinar se usar Consolidadas ou Individuais
		usar_consolidadas = True if consolidado == 'c' else False
		tipo_df = "DfConsolidadas" if usar_consolidadas else "DfIndividuais"
		
		print(f"Usando demonstrações: {tipo_df}")
		
		dados_extraidos = []
		
		# Extrair demonstrações financeiras
		demos_node = self._find_element(root, f".//{tipo_df}")
		
		if demos_node is not None:
			# Grupos de demonstrações a extrair
			grupos_demo = [
				'BalancoPatrimonialAtivo',
				'BalancoPatrimonialPassivo', 
				'DemonstracaoResultado'
			]
			
			for grupo in grupos_demo:
				dados_grupo = self._extrair_grupo_demonstracao(demos_node, grupo, contexto)
				dados_extraidos.extend(dados_grupo)
		
		# Extrair Capital Integralizado
		capital_dados = self._extrair_capital_integralizado(root, contexto)
		dados_extraidos.extend(capital_dados)
		
		if not dados_extraidos:
			raise ValidationError("Nenhum dado válido extraído do XML")
		
		return dados_extraidos
	
	def _extrair_contexto_xml(self, root: ET.Element, itr_controle: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Extrai informações de contexto do XML
		"""
		contexto = {
			'cnpj': itr_controle['cnpj'],
			'data_referencia': itr_controle['data_referencia'],
			'versao': itr_controle['versao'],
			'razao_social': itr_controle['razao_social'],
			'codigo_cvm': itr_controle['codigo_cvm'],
			'moeda': 1,  # Default
			'escala_moeda': 1,  # Default
			'data_inicio_exercicio': '',
			'data_fim_exercicio': ''
		}
		
		# Buscar informações de contexto no XML
		try:
			# Informações de período
			exercicio_node = self._find_element(root, ".//DadosITR")
			if exercicio_node is not None:
				inicio = self._find_element(exercicio_node, "DtInicioTrimestreAtual")
				fim = self._find_element(exercicio_node, "DtFimTrimestreAtual")
				
				if inicio is not None and inicio.text:
					contexto['data_inicio_exercicio'] = parse_date(inicio.text.strip())
				if fim is not None and fim.text:
					contexto['data_fim_exercicio'] = parse_date(fim.text.strip())
			
			# Informações de moeda e escala (pode variar por demonstração)
			moeda_node = self._find_element(root, ".//Moeda")
			if moeda_node is not None and moeda_node.text:
				try:
					contexto['moeda'] = int(moeda_node.text.strip())
				except ValueError:
					pass
			
			escala_node = self._find_element(root, ".//EscalaMoeda")
			if escala_node is not None and escala_node.text:
				try:
					contexto['escala_moeda'] = int(escala_node.text.strip())
				except ValueError:
					pass
		
		except Exception as e:
			print(f"Aviso: Erro ao extrair contexto do XML: {str(e)}")
		
		return contexto
	
	def _deve_usar_consolidadas(self, root: ET.Element) -> bool:
		"""
		Determina se deve usar DfConsolidadas baseado na regra:
		Se DfConsolidadas possuir qualquer TrimestreAtual válido nos grupos exigidos
		"""
		consolidadas_node = self._find_element(root, ".//DfConsolidadas")
		
		if consolidadas_node is None:
			return False
		
		grupos_para_verificar = [
			'BalancoPatrimonialAtivo',
			'BalancoPatrimonialPassivo',
			'DemonstracaoResultado'
		]
		
		for grupo in grupos_para_verificar:
			grupo_node = self._find_element(consolidadas_node, f".//{grupo}")
			if grupo_node is not None:
				# Verificar se há pelo menos uma conta com TrimestreAtual válido
				for conta in self._findall_elements(grupo_node, ".//Conta"):
					trimestre_atual = self._find_element(conta, "TrimestreAtual")
					if trimestre_atual is not None and trimestre_atual.text and trimestre_atual.text.strip():
						return True
		
		return False
	
	def _extrair_grupo_demonstracao(self, demos_node: ET.Element, grupo: str, contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""
		Extrai dados de um grupo de demonstração (BalancoPatrimonialAtivo, etc.)
		"""
		dados = []
		
		grupo_node = self._find_element(demos_node, f".//{grupo}")
		if grupo_node is None:
			return dados
		
		# Buscar todas as contas
		for conta_node in self._findall_elements(grupo_node, ".//Conta"):
			# Verificar ContaFixa
			conta_fixa_node = self._find_element(conta_node, "ContaFixa")
			#if conta_fixa_node is None or not self._is_conta_fixa_true(conta_fixa_node.text):
			#	continue
			
			# Extrair dados da conta
			conta_fixa = self._get_element_text(conta_node, "ContaFixa")
			codigo_conta = self._get_element_text(conta_node, "CodigoConta")
			descricao_conta = self._get_element_text(conta_node, "DescricaoConta")
			valor_conta = self._get_element_text(conta_node, "TrimestreAtual")
			
			if codigo_conta and descricao_conta and valor_conta:
				registro = contexto.copy()
				registro.update({
					'grupo_itr': grupo,
					'codigo_conta': codigo_conta,
					'descricao_conta': descricao_conta,
					'valor_conta': valor_conta,
					'conta_fixa' : 1 if conta_fixa.lower() == "true" else 0
				})
				dados.append(registro)
		
		return dados
	
	def _extrair_capital_integralizado(self, root: ET.Element, contexto: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""
		Extrai dados do Capital Integralizado
		"""
		dados = []
		
		# O caminho correto para a tag CapitalIntegralizado (corrigido do exemplo: "CaptalIntegralizado" parece typo)
		capital_node = self._find_element(
			root,
			'.//DadosITR/Formulario/DadosEmpresa/ComposicaoCapital/CaptalIntegralizado'
		)
		
		if capital_node is None:
			return dados
		
		# Mapeamento fixo conforme especificação
		mapeamento_capital = [
			("Ordinarias", "1", "Ordinarias"),
			("Preferenciais", "2", "Preferenciais"),
			("QtdeTotalAcoes", "3", "QtdeTotalAcoes")
		]
		
		for xml_field, codigo_conta, descricao_conta in mapeamento_capital:
			valor_node = self._find_element(capital_node, xml_field)
			if valor_node is not None and valor_node.text and valor_node.text.strip():
				registro = contexto.copy()
				registro.update({
					'grupo_itr': 'CapitalIntegralizado',
					'codigo_conta': codigo_conta,
					'descricao_conta': descricao_conta,
					'valor_conta': valor_node.text.strip(),
					'conta_fixa' : 1
				})
				dados.append(registro)
		
		return dados
	
	def _is_conta_fixa_true(self, value: str) -> bool:
		"""
		Verifica se ContaFixa é True (case-insensitive, aceita True/true/TRUE/1)
		"""
		if not value:
			return False
		return value.strip().lower() in {'true', '1'}
	
	def _find_element(self, parent: ET.Element, path: str) -> Optional[ET.Element]:
		"""
		Busca elemento considerando namespace se existir
		"""
		if self.namespace:
			# Adicionar namespace aos tags no path
			path_parts = path.split('//')
			ns_path_parts = []
			for part in path_parts:
				if part and not part.startswith('.'):
					ns_path_parts.append(f"ns:{part}")
				else:
					ns_path_parts.append(part)
			ns_path = '//'.join(ns_path_parts)
			return parent.find(ns_path, self.namespace)
		else:
			return parent.find(path)
	
	def _findall_elements(self, parent: ET.Element, path: str) -> List[ET.Element]:
		"""
		Busca todos os elementos considerando namespace se existir
		"""
		if self.namespace:
			# Adicionar namespace aos tags no path
			path_parts = path.split('//')
			ns_path_parts = []
			for part in path_parts:
				if part and not part.startswith('.'):
					ns_path_parts.append(f"ns:{part}")
				else:
					ns_path_parts.append(part)
			ns_path = '//'.join(ns_path_parts)
			return parent.findall(ns_path, self.namespace)
		else:
			return parent.findall(path)
	
	def _get_element_text(self, parent: ET.Element, tag: str) -> str:
		"""
		Extrai texto de um elemento filho, retornando string vazia se não encontrado
		"""
		element = self._find_element(parent, tag)
		if element is not None and element.text:
			return element.text.strip()
		return ""