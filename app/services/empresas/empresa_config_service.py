from typing import Optional, List, Dict, Any
from app.core.utils import normalize_cnpj, valid_cnpj, ValidationError
from app.db.repositories.empresas.empresa_config_repo import EmpresaConfigRepo


class EmpresaConfigService:
	"""Service para gerenciamento de configurações de empresas."""
	
	def __init__(self, repo: EmpresaConfigRepo):
		self.repo = repo
	
	def listar(self) -> List[Dict[str, Any]]:
		"""Lista todas as configurações de empresas."""
		return self.repo.listar_todas()
	
	def obter_por_id(self, id: int) -> Optional[Dict[str, Any]]:
		"""Obtém configuração por ID."""
		if not isinstance(id, int) or id <= 0:
			raise ValidationError("ID deve ser um número inteiro positivo")
		
		return self.repo.obter_por_id(id)
	
	def criar(self, dados: Dict[str, Any]) -> Dict[str, Any]:
		"""Cria nova configuração de empresa com validações."""
		# Validações obrigatórias
		if not dados.get('cnpj'):
			raise ValidationError("CNPJ é obrigatório")
		
		if not dados.get('codigo_negociacao'):
			raise ValidationError("Código de negociação é obrigatório")
		
		# Validar CNPJ
		cnpj_normalizado = normalize_cnpj(dados['cnpj'])
		if not valid_cnpj(cnpj_normalizado):
			raise ValidationError("CNPJ inválido")
		
		# Verificar se CNPJ já existe
		if self.repo.obter_por_cnpj(cnpj_normalizado):
			raise ValidationError("CNPJ já cadastrado")
		
		# Verificar se código de negociação já existe
		codigo_upper = dados['codigo_negociacao'].upper().strip()
		if not codigo_upper:
			raise ValidationError("Código de negociação não pode estar vazio")
		
		if self.repo.obter_por_codigo(codigo_upper):
			raise ValidationError("Código de negociação já cadastrado")
		
		# Validar tipo_dfp se fornecido
		if dados.get('tipo_dfp') and dados['tipo_dfp'] not in ['individual', 'consolidado']:
			raise ValidationError("Tipo DFP deve ser 'individual' ou 'consolidado'")
		
		# Validar modo_analise se fornecido
		if dados.get('modo_analise') and dados['modo_analise'] not in ['padrao', 'banco', 'seguradora']:
			raise ValidationError("Modo de análise deve ser 'padrao', 'banco' ou 'seguradora'")
		
		# Preparar dados para inserção
		dados_criacao = {
			'cnpj': cnpj_normalizado,
			'codigo_negociacao': codigo_upper,
			'classificacao': dados.get('classificacao', '').strip() or None,
			'tipo_dfp': dados.get('tipo_dfp'),
			'modo_analise': dados.get('modo_analise')
		}
		
		return self.repo.criar(dados_criacao)
	
	def atualizar(self, id: int, dados: Dict[str, Any]) -> Dict[str, Any]:
		"""Atualiza configuração existente com validações."""
		if not isinstance(id, int) or id <= 0:
			raise ValidationError("ID deve ser um número inteiro positivo")
		
		# Verificar se registro existe
		registro_atual = self.repo.obter_por_id(id)
		if not registro_atual:
			raise ValidationError("Configuração de empresa não encontrada")
		
		dados_atualizacao = {}
		
		# Validar CNPJ se fornecido
		if 'cnpj' in dados:
			if not dados['cnpj']:
				raise ValidationError("CNPJ é obrigatório")
			
			cnpj_normalizado = normalize_cnpj(dados['cnpj'])
			if not valid_cnpj(cnpj_normalizado):
				raise ValidationError("CNPJ inválido")
			
			# Verificar se CNPJ já existe em outro registro
			empresa_existente = self.repo.obter_por_cnpj(cnpj_normalizado)
			if empresa_existente and empresa_existente['id'] != id:
				raise ValidationError("CNPJ já cadastrado em outra empresa")
			
			dados_atualizacao['cnpj'] = cnpj_normalizado
		
		# Validar código de negociação se fornecido
		if 'codigo_negociacao' in dados:
			if not dados['codigo_negociacao']:
				raise ValidationError("Código de negociação é obrigatório")
			
			codigo_upper = dados['codigo_negociacao'].upper().strip()
			if not codigo_upper:
				raise ValidationError("Código de negociação não pode estar vazio")
			
			# Verificar se código já existe em outro registro
			empresa_existente = self.repo.obter_por_codigo(codigo_upper)
			if empresa_existente and empresa_existente['id'] != id:
				raise ValidationError("Código de negociação já cadastrado em outra empresa")
			
			dados_atualizacao['codigo_negociacao'] = codigo_upper
		
		# Validar classificação se fornecida
		if 'classificacao' in dados:
			dados_atualizacao['classificacao'] = dados['classificacao'].strip() if dados['classificacao'] else None
		
		# Validar tipo_dfp se fornecido
		if 'tipo_dfp' in dados:
			if dados['tipo_dfp'] and dados['tipo_dfp'] not in ['individual', 'consolidado']:
				raise ValidationError("Tipo DFP deve ser 'individual' ou 'consolidado'")
			dados_atualizacao['tipo_dfp'] = dados['tipo_dfp']
		
		# Validar modo_analise se fornecido
		if 'modo_analise' in dados:
			if dados['modo_analise'] and dados['modo_analise'] not in ['padrao', 'banco', 'seguradora']:
				raise ValidationError("Modo de análise deve ser 'padrao', 'banco' ou 'seguradora'")
			dados_atualizacao['modo_analise'] = dados['modo_analise']
		
		if not dados_atualizacao:
			return registro_atual
		
		return self.repo.atualizar(id, dados_atualizacao)
	
	def excluir(self, id: int) -> bool:
		"""Exclui configuração de empresa."""
		if not isinstance(id, int) or id <= 0:
			raise ValidationError("ID deve ser um número inteiro positivo")
		
		# Verificar se registro existe
		if not self.repo.obter_por_id(id):
			raise ValidationError("Configuração de empresa não encontrada")
		
		return self.repo.excluir(id)
	
	def buscar(self, termo: str) -> List[Dict[str, Any]]:
		"""Busca empresas por termo."""
		if not termo or not termo.strip():
			return self.listar()
		
		return self.repo.buscar(termo.strip())
	
	def obter_por_cnpj(self, cnpj: str) -> Optional[Dict[str, Any]]:
		"""Obtém configuração por CNPJ."""
		if not cnpj:
			raise ValidationError("CNPJ é obrigatório")
		
		cnpj_normalizado = normalize_cnpj(cnpj)
		if not valid_cnpj(cnpj_normalizado):
			raise ValidationError("CNPJ inválido")
		
		return self.repo.obter_por_cnpj(cnpj_normalizado)
	
	def obter_por_codigo(self, codigo_negociacao: str) -> Optional[Dict[str, Any]]:
		"""Obtém configuração por código de negociação."""
		if not codigo_negociacao:
			raise ValidationError("Código de negociação é obrigatório")
		
		return self.repo.obter_por_codigo(codigo_negociacao.upper().strip())