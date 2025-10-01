"""
Serviço para importação de ITRs da CVM
Pacote 02: CLI: Importar ITR (Menu 8.CVM → 1.Importar ITR)
"""
import csv
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Any, Dict, Tuple , List
import requests


from tqdm import tqdm

from ...db.repositories.importacao.cia_aberta_itr_repo import CiaAbertaItrRepo
from ...core.utils import normalize_cnpj, valid_cnpj,parse_date,parse_int,get_utc_timestamp, ValidationError


class ItrImportService:
	
	def __init__(self):
		self.repo = CiaAbertaItrRepo()
	
	def importar_por_ano(self, ano: int) -> Tuple[int, int, int, int, List[str]]:
		"""
		Importa ITRs de um ano específico.
		Retorna (novos_incluidos, duplicados, erros)
		"""
		# Validar ano
		current_year = datetime.now().year
		if ano <= 2010:
			raise ValidationError("Ano deve ser maior que 2010")
		if ano > current_year:
			raise ValidationError(f"Ano deve ser menor ou igual ao ano corrente ({current_year})")
		
		# Download e extração
		csv_paths = self._download_and_extract(ano)
		lista_erros = []
		resumo = []
		try:
			for csv_path in csv_paths:
				file_name = os.path.basename(csv_path).lower()
				if file_name.startswith('itr_cia_aberta_bpa'):
					total_registros, inseridos, atualizados, ignorados, erros = self._processar_csv_balanco_patrimonial_ativo(csv_path)
					resumo.append([file_name, total_registros, inseridos, atualizados, ignorados, erros])
				elif file_name.startswith('itr_cia_aberta_bpp'):
					total_registros, inseridos, atualizados, ignorados, erros = self._processar_csv_balanco_patrimonial_passivo(csv_path)
					resumo.append([file_name, total_registros, inseridos, atualizados, ignorados, erros])
				elif file_name.startswith('itr_cia_aberta_dre'):
					total_registros, inseridos, atualizados, ignorados, erros  = self._processar_csv_demonstracao_resultado(csv_path)
					resumo.append([file_name, total_registros, inseridos, atualizados, ignorados, erros])
				elif file_name.startswith('itr_cia_aberta_composicao_capital'):
					total_registros, inseridos, atualizados, ignorados, erros = self._processar_csv_composicao_capital(csv_path)
					resumo.append([file_name, total_registros, inseridos, atualizados, ignorados, erros])
				elif file_name.startswith(f'itr_cia_aberta_{ano}'):
					total_registros ,inseridos, atualizados, ignorados, erros = self._processar_csv_itr_controle(csv_path)
					resumo.append([file_name, total_registros, inseridos, atualizados, ignorados, erros])

			return resumo
			# Somar resultados
		finally:
			# Limpeza obrigatória
			for csv_path in csv_paths:
				self._cleanup_temp_files(csv_path)
				break

	def _download_and_extract(self, ano: int) -> List[str]:
		"""
		Baixa ZIP da CVM e extrai todos os arquivos CSV.
		
		Returns:
			Lista de paths para os arquivos CSV extraídos
		
		Raises:
			ValidationError: Para problemas de download/extração
		"""
		url = f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_{ano}.zip'
		
		# Criar diretório temporário
		temp_dir = tempfile.mkdtemp()
		zip_path = os.path.join(temp_dir, f'itr_cia_aberta_{ano}.zip')
		
		try:
			# Download do ZIP
			print(f'Baixando arquivo de {ano}...')
			response = requests.get(url, timeout=30)
			
			if response.status_code == 404:
				raise ValidationError(f'Arquivo não encontrado na CVM para o ano {ano}')
			elif response.status_code != 200:
				raise ValidationError(f'Erro no download: HTTP {response.status_code}')
			
			# Salvar ZIP
			with open(zip_path, 'wb') as f:
				f.write(response.content)
			
			# Extrair ZIP
			print('Extraindo arquivos CSV...')
			csv_paths = []
			with zipfile.ZipFile(zip_path, 'r') as zip_ref:
				csv_files = [name for name in zip_ref.namelist() if name.lower().endswith('.csv')]
				if not csv_files:
					raise ValidationError('Nenhum arquivo CSV encontrado no ZIP')
				for csv_file in csv_files:
					zip_ref.extract(csv_file, temp_dir)
					csv_paths.append(os.path.join(temp_dir, csv_file))
			
			return csv_paths
			
		except Exception as e:
			# Limpar diretório em caso de erro
			try:
				shutil.rmtree(temp_dir)
			except:
				pass
			
			if isinstance(e, ValidationError):
				raise
			else:
				raise ValidationError(f"Erro no download/extração: {str(e)}")
	
	#* ITR CONTROLE
 
	def _processar_csv_itr_controle(self, csv_path: str) -> Tuple[int, int, int, int, List[str]]:
		"""
		Processa o CSV e persiste no banco
		"""
		inseridos = atualizados = ignorados = erros = total_registros = 0
		lista_erros = []
  
		print("Analisando arquivo...")

		consolidated_data = {}

		with open(csv_path, 'r', encoding='latin1') as f:
			reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
   
   
			for row_num, row in enumerate(reader, start=2):
				try:
					# Mapear dados do CSV para o formato esperado
					data = self._extract_and_validate_itr_controle_row(row, row_num)
					if data is None:
						erros += 1
						continue
  
					codigo_documento = data['codigo_documento']
					consolidated_data[codigo_documento] = data  
						
				except Exception as e:
					erros += 1
					lista_erros.append(f"Linha {row_num}: {str(e)}")


		# Processamento das linhas consolidadas
		total_registros = len(consolidated_data)
		print(f"Processando {total_registros} ITRs...")

		with tqdm(total=total_registros, desc="Importando ITRs", unit="ITRs") as pbar:
			for codigo_documento, data in consolidated_data.items():
				try:
					
					_, action = self.repo.insert_itr_controle(**data)
					
					if action == 'inserted':
						inseridos += 1
					else: #ignored
						ignorados += 1

				except Exception as e:
					erros += 1
					lista_erros.append(f"ITR - documento {codigo_documento}: Erro no insert - {str(e)}")
				
				pbar.update(1)
    
		self.repo.conn.commit()
		return total_registros, inseridos, atualizados, ignorados, erros

	def _extract_and_validate_itr_controle_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
		"""
		Extrai e valida dados de uma linha do CSV.
		
		Returns:
			Dict com dados normalizados ou None se linha inválida
		
		Raises:
			ValidationError: Para erros de validação
		"""
		# CNPJ obrigatório e válido
		cnpj_raw = row.get('CNPJ_CIA', '').strip()
		if not cnpj_raw:
			raise ValidationError("CNPJ vazio")
		
		cnpj = normalize_cnpj(cnpj_raw)
		if not valid_cnpj(cnpj):
			raise ValidationError(f"CNPJ inválido: {cnpj_raw}")
		
		# Razão social obrigatória
		razao_social = row.get('DENOM_CIA', '').strip()
		if not razao_social:
			raise ValidationError("Razão social vazia")
		
		
		# Extrair e normalizar todos os campos
		now_utc = get_utc_timestamp()
		
		data = {
			'cnpj': cnpj,
			'data_referencia': parse_date(row.get('DT_REFER', '')),
			'versao': parse_int(row.get('VERSAO', '0').strip()),
   			'razao_social': row.get('DENOM_CIA', '').strip(),
			'codigo_cvm': row.get('CD_CVM', '').strip(),
			'categoria_documento': row.get('CATEG_DOC', '').strip(),
			'codigo_documento': parse_int(row.get('ID_DOC', '').strip()),
   			'data_recebimento': parse_date(row.get('DT_RECEB', '').strip()),
      		'link_documento': row.get('LINK_DOC', '').strip(),
        	'criado_em': now_utc
		}
		
		return data

	#* ITR COMPOSIÇÃO DE CAPITAL
	def _processar_csv_composicao_capital(self, csv_path: str) -> Tuple[int, int, int, int, List[str]]:
		"""
		Processa o CSV e persiste no banco
		"""
		inseridos = atualizados = ignorados = erros = total_registros = 0
		lista_erros = []
  
		print("Analisando arquivo (Composicção de Capital)...")

		consolidated_data = {}

		with open(csv_path, 'r', encoding='latin1') as f:
			reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
   
			 
			for row_num, row in enumerate(reader, start=2):
				try:
					# Mapear dados do CSV para o formato esperado
					data = self._extract_and_validate_composicao_capital_row(row, row_num)
					if data is None:
						erros += 1
						continue
  
					codigo_documento = data['row_num']
					consolidated_data[codigo_documento] = data

				except Exception as e:
					erros += 1
					lista_erros.append(f"Linha {row_num}: {str(e)}")


		# Processamento das linhas consolidadas
		total_registros = len(consolidated_data)
		print(f"Processando {total_registros} Composição de Capital ITRs...")

		with tqdm(total=total_registros, desc="Importando Composição de Capital", unit="ITRs") as pbar:
			for codigo_documento, data in consolidated_data.items():
				try:
					
					_, action = self.repo.insert_itr_composicao_capital(**data)
					
					if action == 'inserted':
						inseridos += 1
					else:  # ignored
						ignorados += 1


				except Exception as e:
					erros += 1
					lista_erros.append(f"ITR - Composição de Capital documento {codigo_documento}: Erro no insert - {str(e)}")
				
				pbar.update(1)
		self.repo.conn.commit()
		return total_registros, inseridos, atualizados, ignorados, erros

	def _extract_and_validate_composicao_capital_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
		"""
		Extrai e valida dados de uma linha do CSV.
		
		Returns:
			Dict com dados normalizados ou None se linha inválida
		
		Raises:
			ValidationError: Para erros de validação
		"""
		
		# CNPJ obrigatório e válido
		cnpj_raw = row.get('CNPJ_CIA', '').strip()
		if not cnpj_raw:
			raise ValidationError("CNPJ vazio")
		
		cnpj = normalize_cnpj(cnpj_raw)
		if not valid_cnpj(cnpj):
			raise ValidationError(f"CNPJ inválido: {cnpj_raw}")
		
		# Razão social obrigatória
		razao_social = row.get('DENOM_CIA', '').strip()
		if not razao_social:
			raise ValidationError("Razão social vazia")
		
		
		# Extrair e normalizar todos os campos
		now_utc = get_utc_timestamp()
		
		data = {
			'row_num' : row_num,
			'cnpj': cnpj,
			'data_referencia': parse_date(row.get('DT_REFER', '')),
			'versao': parse_int(row.get('VERSAO', '0').strip()),
   			'razao_social': row.get('DENOM_CIA', '').strip(),
			'qtde_acao_ordinaria' : parse_int(row.get('QT_ACAO_ORDIN_CAP_INTEGR',0)),
			'qtde_acao_preferencial' : parse_int(row.get('QT_ACAO_PREF_CAP_INTEGR',0)),
   			'qtde_acao_total' : parse_int(row.get('QT_ACAO_TOTAL_CAP_INTEGR',0)),
   			'qtde_acao_ordinaria_tesouraria' : parse_int(row.get('QT_ACAO_ORDIN_TESOURO',0)),
   			'qtde_acao_preferencial_tesouraria' : parse_int(row.get('QT_ACAO_PREF_TESOURO',0)),
   			'qtde_acao_total_tesouraria' : parse_int(row.get('QT_ACAO_TOTAL_TESOURO',0)),
        	'criado_em': now_utc
		}
		
		return data
 
	#* ITR Balanço Patrimonial
	def _processar_csv_balanco_patrimonial_ativo(self, csv_path: str) -> Tuple[int, int, int, int, List[str]]:
		"""
		Processa o CSV e persiste no banco
		"""
		inseridos = atualizados = ignorados = erros = total_registros =  0
		lista_erros = []
  
		print("Analisando arquivo (Balanço Patrimonial)...")

		consolidated_data = {}

		with open(csv_path, 'r', encoding='latin1') as f:
			reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
    
			for row_num, row in enumerate(reader, start=2):
				try:
					# Mapear dados do CSV para o formato esperado
					data = self._extract_and_validate_balanco_row(row, row_num)
					if data is None:
						erros += 1
						continue
					
					if data['exercicio'] != 'ÚLTIMO':
						#ignorados += 1
						continue
					
					codigo_documento = data['row_num']
					consolidated_data[codigo_documento] = data  
						
				except Exception as e:
					erros += 1
					lista_erros.append(f"Linha {row_num}: {str(e)}")


		# Processamento das linhas consolidadas
		total_registros = len(consolidated_data)
		print(f"Processando {total_registros} Balanço Patrimonial ITRs...")

		with tqdm(total=total_registros, desc="Importando Balanço Patrimonial", unit="ITRs") as pbar:
			for codigo_documento, data in consolidated_data.items():
				try:
					
					_, action = self.repo.insert_itr_dre_bal('cia_aberta_itr_bpa', **data)
					
					if action == 'inserted':
						inseridos += 1
					else:  # ignored
						ignorados += 1

					

				except Exception as e:
					erros += 1
					lista_erros.append(f"ITR - Balanço Patrimonial documento {codigo_documento}: Erro no insert - {str(e)}")
				
				pbar.update(1)

		self.repo.conn.commit()
		return total_registros, inseridos, atualizados, ignorados, erros

	def _processar_csv_balanco_patrimonial_passivo(self, csv_path: str) -> Tuple[int, int, int, int, List[str]]:
		"""
		Processa o CSV e persiste no banco
		"""
		inseridos = atualizados = ignorados = erros = total_registros =  0
		lista_erros = []
  
		print("Analisando arquivo (Balanço Patrimonial Passivo)...")

		consolidated_data = {}

		with open(csv_path, 'r', encoding='latin1') as f:
			reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
   
			 
			for row_num, row in enumerate(reader, start=2):
				try:
					# Mapear dados do CSV para o formato esperado
					data = self._extract_and_validate_balanco_row(row, row_num)
					if data is None:
						erros += 1
						continue
  
					if data['exercicio'] != 'ÚLTIMO':
						#ignorados += 1
						continue
  
					codigo_documento = data['row_num']
					consolidated_data[codigo_documento] = data  
						
				except Exception as e:
					erros += 1
					lista_erros.append(f"Linha {row_num}: {str(e)}")


		# Processamento das linhas consolidadas
		total_registros = len(consolidated_data)
		print(f"Processando {total_registros} Balanço Patrimonial ITRs...")

		with tqdm(total=total_registros, desc="Importando Balanço Patrimonial", unit="ITRs") as pbar:
			for codigo_documento, data in consolidated_data.items():
				try:
					
					_, action = self.repo.insert_itr_dre_bal('cia_aberta_itr_bpp', **data)
					
					if action == 'inserted':
						inseridos += 1
					else:  # ignored
						ignorados += 1

					

				except Exception as e:
					erros += 1
					lista_erros.append(f"ITR - Balanço Patrimonial documento {codigo_documento}: Erro no insert - {str(e)}")
				
				pbar.update(1)
    
		self.repo.conn.commit()
		return total_registros, inseridos, atualizados, ignorados, erros

	def _extract_and_validate_balanco_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
		"""
		Extrai e valida dados de uma linha do CSV.
		
		Returns:
			Dict com dados normalizados ou None se linha inválida
		
		Raises:
			ValidationError: Para erros de validação
		"""


		# CNPJ obrigatório e válido
		cnpj_raw = row.get('CNPJ_CIA', '').strip()
		if not cnpj_raw:
			raise ValidationError("CNPJ vazio")
		
		cnpj = normalize_cnpj(cnpj_raw)
		if not valid_cnpj(cnpj):
			raise ValidationError(f"CNPJ inválido: {cnpj_raw}")
		
		# Razão social obrigatória
		razao_social = row.get('DENOM_CIA', '').strip()
		if not razao_social:
			raise ValidationError("Razão social vazia")

		#grupo
		grupo = row.get('GRUPO_DFP', '').split('-')[0]
  
		#conta fixa
		if row.get('ST_CONTA_FIXA', '').strip() == 'S':
			conta_fixa = 1
		else :
			conta_fixa = 0 
		
		
		# Extrair e normalizar todos os campos
		now_utc = get_utc_timestamp()
  
		data = {
			'row_num' : row_num,
			'cnpj': cnpj,
			'data_referencia': parse_date(row.get('DT_REFER', '')),
			'versao': parse_int(row.get('VERSAO', '0').strip()),
   			'razao_social': row.get('DENOM_CIA', '').strip(),
			'codigo_cvm': row.get('CD_CVM', '').strip(),
			'grupo': grupo.strip(), 
			'moeda' : row.get('MOEDA', '').strip(),
			'escala_moeda' : row.get('ESCALA_MOEDA', '').strip(),
			'data_inicio_exercicio' : parse_date(row.get('DT_FIM_EXERC', '').strip()),
			'data_fim_exercicio' : parse_date(row.get('DT_FIM_EXERC', '').strip()),
			'codigo_conta' : row.get('CD_CONTA', '').strip(),
			'descricao_conta' : row.get('DS_CONTA', '').strip(),
			'valor_conta' : row.get('VL_CONTA', '').strip(),
			'conta_fixa' : conta_fixa,
        	'criado_em': now_utc,
			'exercicio' : row.get('ORDEM_EXERC','').strip()
		}
		
		return data

	#* ITR Demonstração do Resultado
	def _processar_csv_demonstracao_resultado(self, csv_path: str) -> Tuple[int, int, int, int, List[str]]:
		"""
		Processa o CSV e persiste no banco
		"""
		inseridos = atualizados = ignorados = erros = total_registros = 0
		lista_erros = []
  
		print("Analisando arquivo (Demontrativo de Resultado)...")

		consolidated_data = {}

		with open(csv_path, 'r', encoding='latin1') as f:
			reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
   

			for row_num, row in enumerate(reader, start=2):
				try:
					# Mapear dados do CSV para o formato esperado
					data = self._extract_and_validate_dre_row(row, row_num)
					if data is None:
						erros += 1
						continue
					
					if data['exercicio'] != 'ÚLTIMO':
						#ignorados += 1
						continue
					
					codigo_documento = data['row_num']
					consolidated_data[codigo_documento] = data  
						
				except Exception as e:
					erros += 1
					lista_erros.append(f"Linha {row_num}: {str(e)}")


		# Processamento das linhas consolidadas
		total_registros = len(consolidated_data)
		print(f"Processando {total_registros} Demontrativo de Resultado ITRs...")

		with tqdm(total=total_registros, desc="Importando DRE", unit="DREs") as pbar:
			for codigo_documento, data in consolidated_data.items():
				try:
					
					_, action = self.repo.insert_itr_dre_bal('cia_aberta_itr_dre', **data)
					
					if action == 'inserted':
						inseridos += 1
					else:  # ignored
						ignorados += 1

					

				except Exception as e:
					erros += 1
					lista_erros.append(f"ITR - Demonstrativo de Resultado {codigo_documento}: Erro no insert - {str(e)}")
				
				pbar.update(1)
    
		self.repo.conn.commit()
		return total_registros, inseridos, atualizados, ignorados, erros

	def _extract_and_validate_dre_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
		"""
		Extrai e valida dados de uma linha do CSV.
		
		Returns:
			Dict com dados normalizados ou None se linha inválida
		
		Raises:
			ValidationError: Para erros de validação
		"""
		
		# CNPJ obrigatório e válido
		cnpj_raw = row.get('CNPJ_CIA', '').strip()
		if not cnpj_raw:
			raise ValidationError("CNPJ vazio")
		
		cnpj = normalize_cnpj(cnpj_raw)
		if not valid_cnpj(cnpj):
			raise ValidationError(f"CNPJ inválido: {cnpj_raw}")
		
		# Razão social obrigatória
		razao_social = row.get('DENOM_CIA', '').strip()
		if not razao_social:
			raise ValidationError("Razão social vazia")

		#grupo
		grupo = row.get('GRUPO_DFP', '').strip().split('-')[0]
  
		#conta fixa
		if row.get('ST_CONTA_FIXA', '').strip() == 'S':
			conta_fixa = 1
		else :
			conta_fixa = 0 
		
		
		# Extrair e normalizar todos os campos
		now_utc = get_utc_timestamp()
  
		data = {
			'row_num' : row_num,
			'cnpj': cnpj,
			'data_referencia': parse_date(row.get('DT_REFER', '')),
			'versao': parse_int(row.get('VERSAO', '0').strip()),
   			'razao_social': row.get('DENOM_CIA', '').strip(),
			'codigo_cvm': row.get('CD_CVM', '').strip(),
			'grupo': grupo.strip(), 
			'moeda' : row.get('MOEDA', '').strip(),
			'escala_moeda' : row.get('ESCALA_MOEDA', '').strip(),
			'data_inicio_exercicio' : parse_date(row.get('DT_FIM_EXERC', '').strip()),
			'data_fim_exercicio' : parse_date(row.get('DT_FIM_EXERC', '').strip()),
			'codigo_conta' : row.get('CD_CONTA', '').strip(),
			'descricao_conta' : row.get('DS_CONTA', '').strip(),
			'valor_conta' : row.get('VL_CONTA', '').strip(),
			'conta_fixa' : conta_fixa,
        	'criado_em': now_utc,
			'exercicio' : row.get('ORDEM_EXERC','').strip()
		}
		
		return data
 
 
	def _cleanup_temp_files(self, csv_path: str):
		"""Remove arquivos temporários."""
		try:
			temp_dir = os.path.dirname(csv_path)
			if temp_dir and os.path.exists(temp_dir):
				shutil.rmtree(temp_dir)
		except Exception:
			# Ignorar erros de limpeza
			pass