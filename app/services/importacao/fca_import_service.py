"""
Serviço para importação de dados do Formulário Cadastral (FCA) da CVM.
Segue as regras de negócio definidas no EPIC.
"""
import os
import csv
import zipfile
import requests
import tempfile
import shutil
from datetime import datetime
from typing import Tuple, Dict, List, Any
from tqdm import tqdm
from ...db.repositories.importacao.cia_aberta_fca_repo import CiaAbertaFcaRepo
from ...core.utils import normalize_cnpj, valid_cnpj,parse_date,parse_int,validate_url,get_utc_timestamp,parse_url, ValidationError


class FcaImportService:
	"""Serviço de importação de dados FCA da CVM."""
	
	def __init__(self):
		self.repo = CiaAbertaFcaRepo()
	
	def importar_fca_por_ano(self, ano: int) -> Tuple[int, int, int, int, List[str]]:
		"""
		Importa dados FCA da CVM para o ano especificado.
		
		Args:
			ano: Ano para importação (deve ser > 2010 e <= ano corrente)
		
		Returns:
			Tuple[inseridos, atualizados, ignorados, erros, lista_erros]
		
		Raises:
			ValidationError: Para ano inválido ou problemas de validação
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
			return self._processar_csv(csv_path, ano)
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
		url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{ano}.zip"
		
		# Criar diretório temporário
		temp_dir = tempfile.mkdtemp()
		zip_path = os.path.join(temp_dir, f"fca_cia_aberta_{ano}.zip")
		csv_filename = f"fca_cia_aberta_geral_{ano}.csv"
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
	
	def _processar_csv(self, csv_path: str, ano: int) -> Tuple[int, int, int, int, List[str]]:
		"""
		Processa o CSV extraído aplicando as regras de negócio.
		
		Returns:
			Tuple[inseridos, atualizados, ignorados, erros, lista_erros]
		"""
		inseridos = atualizados = ignorados = erros = 0
		lista_erros = []
		
		# Contar linhas para progress bar
		print("Analisando arquivo...")
		# with open(csv_path, 'r', encoding='latin1') as f:
		# 	total_rows = sum(1 for _ in csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')) - 1
		
		# Consolidação prévia por CNPJ (para tratar duplicatas no mesmo CSV)
		print("Consolidando dados por CNPJ...")
		consolidated_data = {}
		
		with open(csv_path, 'r', encoding='latin1') as f:
			reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
			
			for row_num, row in enumerate(reader, start=2):  # linha 2 = primeira linha de dados
				try:
					# Extrair e validar dados básicos
					data = self._extract_and_validate_row(row, row_num)
					if data is None:
						erros += 1
						continue
					
					cnpj = data['cnpj']
					documento_id = data.get('documento_id', 0) or 0
					
					# Consolidação: manter apenas o de maior documento_id por CNPJ
					if cnpj not in consolidated_data or documento_id > (consolidated_data[cnpj].get('documento_id', 0) or 0):
						consolidated_data[cnpj] = data
				
				except Exception as e:
					erros += 1
					lista_erros.append(f"Linha {row_num}: {str(e)}")
		
		# Processamento das linhas consolidadas
		print(f"Processando {len(consolidated_data)} empresas únicas...")
		
		with tqdm(total=len(consolidated_data), desc="Importando empresas", unit="empresas") as pbar:
			for cnpj, data in consolidated_data.items():
				try:
					# Upsert na base
					_, action = self.repo.upsert_by_cnpj(**data)
					
					if action == 'inserted':
						inseridos += 1
					elif action == 'updated':
						atualizados += 1
					else:  # ignored
						ignorados += 1

					self.repo.conn.commit()

				except Exception as e:
					erros += 1
					lista_erros.append(f"CNPJ {cnpj}: Erro no upsert - {str(e)}")
				
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
		cnpj_raw = row.get('CNPJ_Companhia', '').strip()
		if not cnpj_raw:
			raise ValidationError("CNPJ vazio")
		
		cnpj = normalize_cnpj(cnpj_raw)
		if not valid_cnpj(cnpj):
			raise ValidationError(f"CNPJ inválido: {cnpj_raw}")
		
		# Razão social obrigatória
		razao_social = row.get('Nome_Empresarial', '').strip()
		if not razao_social:
			raise ValidationError("Razão social vazia")
		
		# Validar URL se fornecida
		pagina_web = parse_url(row.get('Pagina_Web', '').strip())
		if pagina_web and not validate_url(pagina_web):
			raise ValidationError(f"URL inválida: {pagina_web}")
		
		# Extrair e normalizar todos os campos
		now_utc = get_utc_timestamp()
		
		data = {
			'cnpj': cnpj,
			'data_referencia': parse_date(row.get('Data_Referencia', '')),
			'documento_id': parse_int(row.get('ID_Documento', '')),
			'razao_social': razao_social,
			'data_constituicao': parse_date(row.get('Data_Constituicao', '')),
			'codigo_cvm': row.get('Codigo_CVM', '').strip(),
			'data_registro_cvm': parse_date(row.get('Data_Registro_CVM', '')),
			'categoria_registro': row.get('Categoria_Registro_CVM', '').strip(),
			'situacao_registro_cvm': row.get('Situacao_Registro_CVM', '').strip(),
			'pais_origem': row.get('Pais_Origem', '').strip(),
			'pais_custodia_valores_mobiliarios': row.get('Pais_Custodia_Valores_Mobiliarios', '').strip(),
			'setor_atividade': row.get('Setor_Atividade', '').strip(),
			'descricao_atividade': row.get('Descricao_Atividade', '').strip(),
			'situacao_emissor': row.get('Situacao_Emissor', '').strip(),
			'controle_acionario': row.get('Especie_Controle_Acionario', '').strip(),
			'dia_encerramento_exercicio_social': parse_int(row.get('Dia_Encerramento_Exercicio_Social', '')),
			'mes_encerramento_exercicio_social': parse_int(row.get('Mes_Encerramento_Exercicio_Social', '')),
			'pagina_web': pagina_web,
			'criado_em': now_utc,
			'atualizado_em': now_utc
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