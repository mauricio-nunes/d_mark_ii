from typing import Optional, List, Dict, Any
from ...connection import get_conn


class CiaAbertaItrRepo:
	"""Repository para as tabelas de Itr."""
	
	def __init__(self, conn=None):
		self.conn = conn or get_conn()
	
	def insert_itr_controle(self, **kwargs) -> tuple[int, str]:
		"""
		Retorna (affected_rows, action) onde action = 'inserted'|'updated'|'ignored'
		"""
		cur = self.conn.cursor()
		
		try:
			cur.execute("""
				INSERT OR IGNORE INTO cia_aberta_itr_controle (
					cnpj, data_referencia, versao, razao_social, codigo_cvm,
					categoria_documento, codigo_documento, data_recebimento,
					link_documento, criado_em
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""", (
				kwargs['cnpj'], kwargs['data_referencia'], kwargs['versao'],
				kwargs.get('razao_social'), kwargs.get('codigo_cvm'),
				kwargs.get('categoria_documento'), kwargs.get('codigo_documento'),
				kwargs.get('data_recebimento'), kwargs.get('link_documento'),
				kwargs['criado_em']
			))
			return (cur.rowcount or 0), ('inserted' if cur.rowcount == 1 else 'ignored')
		
		except Exception as e:
			
			raise e
	
	def insert_itr_composicao_capital(self, **kwargs) -> tuple[int, str]:
		"""
		Retorna (affected_rows, action) onde action = 'inserted'|'updated'|'ignored'
		"""
		cur = self.conn.cursor()
		
		try:
			cur.execute("""
				INSERT OR IGNORE INTO cia_aberta_itr_composicao_capital (
					cnpj, data_referencia, versao, razao_social,
					qtde_acao_ordinaria, qtde_acao_preferencial, qtde_acao_total,
					qtde_acao_ordinaria_tesouraria, qtde_acao_preferencial_tesouraria, qtde_acao_total_tesouraria
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""", (
				kwargs['cnpj'],
				kwargs['data_referencia'],
				kwargs['versao'],
				kwargs['razao_social'],
				kwargs['qtde_acao_ordinaria'],
				kwargs['qtde_acao_preferencial'],
				kwargs['qtde_acao_total'],
				kwargs['qtde_acao_ordinaria_tesouraria'],
				kwargs['qtde_acao_preferencial_tesouraria'],
				kwargs['qtde_acao_total_tesouraria']
			))
			return (cur.rowcount or 0), ('inserted' if cur.rowcount == 1 else 'ignored')
		
		except Exception as e:
			raise e

	def insert_itr_dre_bal(self, table_name: str, **kwargs) -> tuple[int, str]:
		"""
		Retorna (affected_rows, action) onde action = 'inserted'|'updated'|'ignored'
		"""
		cur = self.conn.cursor()

		try:
			cur.execute(f"""
				INSERT OR IGNORE INTO {table_name} (
					cnpj, data_referencia, versao, razao_social,
					codigo_cvm, grupo, moeda, escala_moeda,
					data_inicio_exercicio, data_fim_exercicio,
					codigo_conta, descricao_conta, valor_conta,
					conta_fixa, criado_em
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""", (
				kwargs['cnpj'],
				kwargs['data_referencia'],
				kwargs['versao'],
				kwargs['razao_social'],
				kwargs['codigo_cvm'],
				kwargs['grupo'],
				kwargs['moeda'],
				kwargs['escala_moeda'],
				kwargs['data_inicio_exercicio'],
				kwargs['data_fim_exercicio'],
				kwargs['codigo_conta'],
				kwargs['descricao_conta'],
				kwargs['valor_conta'],
				kwargs['conta_fixa'],
				kwargs['criado_em']
			))
			return (cur.rowcount or 0), ('inserted' if cur.rowcount == 1 else 'ignored')

		except Exception as e:
			
			raise e
		
#         WITH ult AS (
#     /* pega a última versão disponível por CNPJ + data + grupo */
#     SELECT 
#         cnpj, 
#         data_referencia, 
#         grupo, 
#         MAX(versao) AS versao
#     FROM cia_aberta_itr_dre
#     WHERE cnpj = '00000000000191'
#       AND grupo = 'DF Individual'
#     GROUP BY cnpj, data_referencia, grupo
# ),
# base AS (
#     /* traz os valores já na escala correta */
#     SELECT
#         d.codigo_conta,
#         d.descricao_conta,
#         d.data_referencia,
#         CAST(d.valor_conta AS REAL) *
#           CASE
#             WHEN UPPER(d.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
#             WHEN UPPER(d.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
#             ELSE 1.0
#           END AS valor_ajust
#     FROM cia_aberta_itr_dre d
#     INNER JOIN ult u
#       ON d.cnpj = u.cnpj
#      AND d.data_referencia = u.data_referencia
#      AND d.grupo = u.grupo
#      AND d.versao = u.versao
# ),
# agg AS (
#     /* faz o pivot acumulado */
#     SELECT
#         codigo_conta,
#         descricao_conta,
#         MAX(CASE WHEN data_referencia = '2024-03-31' THEN valor_ajust END) AS cum_03,
#         MAX(CASE WHEN data_referencia = '2024-06-30' THEN valor_ajust END) AS cum_06,
#         MAX(CASE WHEN data_referencia = '2024-09-30' THEN valor_ajust END) AS cum_09
#     FROM base
#     GROUP BY codigo_conta, descricao_conta
# )
# SELECT
#     codigo_conta,
#     descricao_conta,

#     /* acumulados (como vêm na DRE) */
#     ROUND(cum_03, 2) AS acumulado_03,
#     ROUND(cum_06, 2) AS acumulado_06,
#     ROUND(cum_09, 2) AS acumulado_09,

#     /* valores trimestrais (diferenças) */
#     ROUND(cum_03, 2) AS tri_1,
#     ROUND(COALESCE(cum_06, 0) - COALESCE(cum_03, 0), 2) AS tri_2,
#     ROUND(COALESCE(cum_09, 0) - COALESCE(cum_06, 0), 2) AS tri_3

# FROM agg
# ORDER BY codigo_conta;
