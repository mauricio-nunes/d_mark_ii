"""
Repositório para a tabela itr_controle
Gerencia os metadados dos ITRs importados do CSV da CVM
"""
from typing import List, Optional, Dict, Any
from ...connection import get_conn
from ....core.utils import normalize_cnpj, parse_date


class ItrControleRepository:
	
	def __init__(self, conn=None):
		self.conn = conn or get_conn()
	
	def insert(self, **kwargs) -> tuple[int, str]:
		"""
		Faz upsert baseado em CNPJ, data_referencia e versao.
		Retorna (affected_rows, action) onde action = 'inserted'|'updated'|'ignored'
		"""
		cur = self.conn.cursor()
		
		try:
			cur.execute("""
					INSERT INTO itr_controle (
						cnpj, data_referencia, versao, razao_social, codigo_cvm,
						categoria_documento, codigo_documento, data_recebimento,
						link_documento, criado_em, processado
					) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
				""", (
					kwargs['cnpj'], kwargs['data_referencia'], kwargs['versao'],
					kwargs.get('razao_social'), kwargs.get('codigo_cvm'),
					kwargs.get('categoria_documento'), kwargs.get('codigo_documento'),
					kwargs.get('data_recebimento'), kwargs.get('link_documento'),
					kwargs['criado_em']
				))
			return cur.rowcount, 'inserted'

		except Exception as e:
				# Violação de UNIQUE constraint - duplicado
				if 'UNIQUE constraint failed' in str(e):
					return 0, 'ignored'
				else:
					raise e







	def insert_batch(self, registros: List[Dict[str, Any]]) -> tuple[int, int]:
		"""
		Insere em lote os registros do CSV, ignorando duplicados.
		Retorna (novos_inseridos, duplicados_ignorados)
		"""
		conn = get_conn()
		cur = conn.cursor()
		
		novos = 0
		duplicados = 0
		
		for reg in registros:
			try:
				cur.execute("""
					INSERT INTO itr_controle (
						cnpj, data_referencia, versao, razao_social, codigo_cvm,
						categoria_documento, codigo_documento, data_recebimento,
						link_documento, criado_em, processado
					) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
				""", (
					normalize_cnpj(reg['cnpj']),
					parse_date(reg['data_referencia']),
					int(reg['versao']),
					reg['razao_social'],
					reg['codigo_cvm'],
					reg['categoria_documento'],
					reg['codigo_documento'],
					parse_date(reg['data_recebimento']),
					reg['link_documento'],
					reg['criado_em']
				))
				novos += 1
			except Exception as e:
				# Violação de UNIQUE constraint - duplicado
				if 'UNIQUE constraint failed' in str(e):
					duplicados += 1
				else:
					raise e
		
		conn.commit()
		conn.close()
		return novos, duplicados
	
	def list_not_processed(self, razao_social_filter: str = None, cnpj_filter: str = None, 
						  limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
		"""
		Lista ITRs não processados com filtros opcionais
		"""
		conn = get_conn()
		cur = conn.cursor()
		
		sql = """
			SELECT id, cnpj, data_referencia, versao, razao_social, codigo_cvm,
				   categoria_documento, codigo_documento, data_recebimento, link_documento
			FROM itr_controle 
			WHERE processado = 0
		"""
		params = []
		
		if razao_social_filter:
			sql += " AND razao_social LIKE ?"
			params.append(f"%{razao_social_filter}%")
		
		if cnpj_filter:
			sql += " AND cnpj = ?"
			params.append(normalize_cnpj(cnpj_filter))
		
		sql += " ORDER BY data_referencia DESC, razao_social LIMIT ? OFFSET ?"
		params.extend([limit, offset])
		
		result = cur.execute(sql, params).fetchall()
		conn.close()
		
		return [dict(row) for row in result]
	
	def count_not_processed(self, razao_social_filter: str = None, cnpj_filter: str = None) -> int:
		"""
		Conta ITRs não processados com filtros opcionais
		"""
		conn = get_conn()
		cur = conn.cursor()
		
		sql = "SELECT COUNT(*) FROM itr_controle WHERE processado = 0"
		params = []
		
		if razao_social_filter:
			sql += " AND razao_social LIKE ?"
			params.append(f"%{razao_social_filter}%")
		
		if cnpj_filter:
			sql += " AND cnpj = ?"
			params.append(normalize_cnpj(cnpj_filter))
		
		result = cur.execute(sql, params).fetchone()
		conn.close()
		
		return result[0] if result else 0
	
	def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
		"""
		Busca um ITR por ID
		"""
		conn = get_conn()
		cur = conn.cursor()
		
		result = cur.execute("""
			SELECT id, cnpj, data_referencia, versao, razao_social, codigo_cvm,
				   categoria_documento, codigo_documento, data_recebimento, 
				   link_documento, processado
			FROM itr_controle WHERE id = ?
		""", (id,)).fetchone()
		
		conn.close()
		
		return dict(result) if result else None
	
	def mark_as_processed(self, id: int) -> None:
		"""
		Marca um ITR como processado
		"""
		conn = get_conn()
		cur = conn.cursor()
		
		cur.execute("UPDATE itr_controle SET processado = 1 WHERE id = ?", (id,))
		conn.commit()
		conn.close()
	
	def get_max_version_for_period(self, cnpj: str, data_referencia: str) -> Optional[int]:
		"""
		Retorna a versão máxima já processada para um CNPJ e período
		"""
		conn = get_conn()
		cur = conn.cursor()
		
		result = cur.execute("""
			SELECT MAX(d.versao)
			FROM itr_dados d
			WHERE d.cnpj = ? AND d.data_referencia = ?
		""", (normalize_cnpj(cnpj), data_referencia)).fetchone()
		
		conn.close()
		
		return result[0] if result and result[0] is not None else 0