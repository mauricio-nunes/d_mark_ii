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

from ...db.repositories.importacao.itr_controle_repo import ItrControleRepository
from ...core.utils import normalize_cnpj, valid_cnpj,parse_date,parse_int,validate_url,get_utc_timestamp,parse_url, ValidationError


class ItrImportService:
	
	def __init__(self):
		self.repo = ItrControleRepository()
		#self.base_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"
		#self.chunk_size = 50000  # Linhas por chunk
	
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
		csv_path = self._download_and_extract(ano)
		
		try:
			return self._processar_csv(csv_path)
		finally:
			# Limpeza obrigatória
			self._cleanup_temp_files(csv_path)
   
	def _download_and_extract(self, ano: int) -> str:
		"""
		Baixa ZIP da CVM e extrai CSV.
		
		Returns:
			Path para o arquivo CSV extraído
		
		Raises:
			ValidationError: Para problemas de download/extração
		"""
		url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_{ano}.zip"
		
		# Criar diretório temporário
		temp_dir = tempfile.mkdtemp()
		zip_path = os.path.join(temp_dir, f"itr_cia_aberta_{ano}.zip")
		csv_filename = f"itr_cia_aberta_{ano}.csv"
		csv_path = os.path.join(temp_dir, csv_filename)
		
		try:
			# Download do ZIP
			print(f"Baixando arquivo de {ano}...")
			response = requests.get(url, timeout=30)
			
			if response.status_code == 404:
				raise ValidationError(f"Arquivo não encontrado na CVM para o ano {ano}")
			elif response.status_code != 200:
				raise ValidationError(f"Erro no download: HTTP {response.status_code}")
			
			# Salvar ZIP
			with open(zip_path, 'wb') as f:
				f.write(response.content)
			
			# Extrair ZIP
			print("Extraindo arquivo...")
			with zipfile.ZipFile(zip_path, 'r') as zip_ref:
				# Verificar se CSV existe no ZIP
				if csv_filename not in zip_ref.namelist():
					raise ValidationError(f"Arquivo {csv_filename} não encontrado no ZIP")
				
				# Extrair apenas o CSV necessário
				zip_ref.extract(csv_filename, temp_dir)
			
			return csv_path
			
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
	
	# def _download_file(self, url: str, dest_path: str) -> None:
	# 	"""
	# 	Baixa um arquivo da URL para o destino
	# 	"""
	# 	try:
	# 		response = requests.get(url, stream=True, timeout=60)
	# 		response.raise_for_status()
			
	# 		# Verificar content-type se disponível
	# 		content_type = response.headers.get('content-type', '')
	# 		if content_type and 'zip' not in content_type.lower() and 'octet-stream' not in content_type.lower():
	# 			print(f"Aviso: Content-Type inesperado: {content_type}")
			
	# 		# Salvar arquivo
	# 		with open(dest_path, 'wb') as f:
	# 			for chunk in response.iter_content(chunk_size=8192):
	# 				if chunk:
	# 					f.write(chunk)
			
	# 		# Verificar tamanho
	# 		file_size = os.path.getsize(dest_path)
	# 		if file_size == 0:
	# 			raise ValidationError("Arquivo baixado está vazio")
			
	# 		print(f"Arquivo baixado: {file_size:,} bytes")
			
	# 	except requests.RequestException as e:
	# 		raise ValidationError(f"Erro no download: {str(e)}")
	
	# def _extract_csv_from_zip(self, zip_path: str, csv_filename: str, csv_dest: str) -> None:
	# 	"""
	# 	Extrai o CSV específico do ZIP
	# 	"""
	# 	try:
	# 		with zipfile.ZipFile(zip_path, 'r') as zip_file:
	# 			# Verificar se o CSV está no ZIP
	# 			if csv_filename not in zip_file.namelist():
	# 				available_files = ', '.join(zip_file.namelist())
	# 				raise ValidationError(f"Arquivo {csv_filename} não encontrado no ZIP. Arquivos disponíveis: {available_files}")
				
	# 			# Extrair CSV
	# 			zip_file.extract(csv_filename, os.path.dirname(csv_dest))
				
	# 			# Verificar se foi extraído
	# 			if not os.path.exists(csv_dest):
	# 				raise ValidationError(f"Erro na extração do arquivo {csv_filename}")
				
	# 			print(f"CSV extraído: {os.path.getsize(csv_dest):,} bytes")
				
	# 	except zipfile.BadZipFile:
	# 		raise ValidationError("Arquivo ZIP inválido ou corrompido")
	
	def _processar_csv(self, csv_path: str) -> Tuple[int, int, int, int, List[str]]:
		"""
		Processa o CSV em chunks e persiste no banco
		"""
		inseridos = atualizados = ignorados = erros = 0
		lista_erros = []
  
		print("Analisando arquivo...")

		consolidated_data = {}

		with open(csv_path, 'r', encoding='latin1') as f:
			reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
   
   
			for row_num, row in enumerate(reader, start=2):
				try:
					# Mapear dados do CSV para o formato esperado
					data = self._extract_and_validate_row(row, row_num)
					if data is None:
						erros += 1
						continue
  
					codigo_documento = data['codigo_documento']
					consolidated_data[codigo_documento] = data  
						
				except Exception as e:
					erros += 1
					lista_erros.append(f"Linha {row_num}: {str(e)}")


		# Processamento das linhas consolidadas
		print(f"Processando {len(consolidated_data)} ITRs...")
  
		with tqdm(total=len(consolidated_data), desc="Importando ITRs", unit="ITRs") as pbar:
			for codigo_documento, data in consolidated_data.items():
				try:
					#! AJUSTAR O REPOSITORY PARA RETORNAR A AÇÃO REALIZADA
					_, action = self.repo.insert(**data)
					
					if action == 'inserted':
						inseridos += 1
					elif action == 'updated':
						atualizados += 1
					else:  # ignored
						ignorados += 1

					self.repo.conn.commit()

				except Exception as e:
					erros += 1
					lista_erros.append(f"ITR - documento {codigo_documento}: Erro no insert - {str(e)}")
				
				pbar.update(1)
		
		return inseridos, atualizados, ignorados, erros, lista_erros


	def _extract_and_validate_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
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

	def _cleanup_temp_files(self, csv_path: str):
		"""Remove arquivos temporários."""
		try:
			temp_dir = os.path.dirname(csv_path)
			if temp_dir and os.path.exists(temp_dir):
				shutil.rmtree(temp_dir)
		except Exception:
			# Ignorar erros de limpeza
			pass