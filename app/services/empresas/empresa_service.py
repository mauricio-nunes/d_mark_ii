from app.db.repositories.empresas.empresa_repo import EmpresaRepo
from app.core.utils import normalize_cnpj, valid_cnpj, ValidationError
import csv
import os

class EmpresaService:
	def __init__(self, repo=None):
		self.repo = repo or EmpresaRepo()

	def listar_empresas(self, page=1, page_size=20):
		return self.repo.listar_empresas(page, page_size)

	def buscar_empresa(self, query):
		if valid_cnpj(query):
			return self.repo.buscar_por_cnpj(normalize_cnpj(query))
		return self.repo.buscar_por_codigo(query)

	def adicionar_empresa(self, cnpj, codigo, classificacao, tipo_dfp, modo_analise):
		cnpj = normalize_cnpj(cnpj)
		if not valid_cnpj(cnpj):
			raise ValidationError('CNPJ inválido.')
		if self.repo.buscar_por_cnpj(cnpj):
			raise ValidationError('CNPJ já cadastrado.')
		if self.repo.buscar_por_codigo(codigo):
			raise ValidationError('Código de negociação já cadastrado.')
		self.repo.inserir_empresa(cnpj, codigo, classificacao, tipo_dfp, modo_analise)

	def editar_empresa(self, cnpj, codigo, classificacao, tipo_dfp, modo_analise):
		cnpj = normalize_cnpj(cnpj)
		empresa = self.repo.buscar_por_cnpj(cnpj)
		if not empresa:
			raise ValidationError('Empresa não encontrada.')
		if codigo != empresa['codigo_negociacao'] and self.repo.buscar_por_codigo(codigo):
			raise ValidationError('Código de negociação já cadastrado.')
		self.repo.atualizar_empresa(cnpj, codigo, classificacao, tipo_dfp, modo_analise)

	def exportar_csv(self):
		empresas, _ = self.repo.listar_empresas(page=1, page_size=10000)
		os.makedirs('./exports', exist_ok=True)
		path = './exports/empresas.csv'
		with open(path, 'w', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow(['CNPJ', 'Código', 'Classificação', 'Tipo DFP', 'Modo Análise'])
			for e in empresas:
				writer.writerow([e['cnpj'], e['codigo_negociacao'], e['classificacao'], e['tipo_dfp'], e['modo_analise']])
		return path
