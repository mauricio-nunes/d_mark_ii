"""
Repositório para a tabela itr_dados
Gerencia os dados extraídos dos XMLs dos ITRs
"""
from typing import List, Dict, Any
from ..connection import get_conn
from ...core.utils import normalize_cnpj


class ItrDadosRepository:
	
	def delete_previous_versions(self, cnpj: str, data_referencia: str, versao_atual: int) -> int:
		"""
		Remove todas as versões anteriores para o mesmo CNPJ e período.
		Retorna o número de registros removidos.
		"""
		conn = get_conn()
		cur = conn.cursor()
		
		cur.execute("""
			DELETE FROM itr_dados 
			WHERE cnpj = ? AND data_referencia = ? AND versao < ?
		""", (normalize_cnpj(cnpj), data_referencia, versao_atual))
		
		deleted_count = cur.rowcount
		conn.commit()
		conn.close()
		
		return deleted_count
	
	def insert_batch(self, registros: List[Dict[str, Any]]) -> int:
		"""
		Insere em lote os dados extraídos do XML.
		Retorna o número de registros inseridos.
		"""
		conn = get_conn()
		cur = conn.cursor()
		
		inserted_count = 0
		for reg in registros:
			cur.execute("""
				INSERT INTO itr_dados (
					cnpj, data_referencia, versao, razao_social, codigo_cvm, grupo_itr,
					moeda, escala_moeda, data_inicio_exercicio, data_fim_exercicio,
					codigo_conta, descricao_conta, valor_conta, conta_fixa
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""", (
				normalize_cnpj(reg['cnpj']),
				reg['data_referencia'],
				reg['versao'],
				reg['razao_social'],
				reg['codigo_cvm'],
				reg['grupo_itr'],
				reg['moeda'],
				reg['escala_moeda'],
				reg['data_inicio_exercicio'],
				reg['data_fim_exercicio'],
				reg['codigo_conta'],
				reg['descricao_conta'],
				reg['valor_conta'],
				reg['conta_fixa']
			))
			inserted_count += 1
		
		conn.commit()
		conn.close()
		
		return inserted_count
	
	def get_by_context(self, cnpj: str, data_referencia: str, versao: int) -> List[Dict[str, Any]]:
		"""
		Busca todos os dados de um contexto específico (CNPJ, período, versão)
		"""
		conn = get_conn()
		cur = conn.cursor()
		
		result = cur.execute("""
			SELECT id, cnpj, data_referencia, versao, razao_social, codigo_cvm, grupo_itr,
				   moeda, escala_moeda, data_inicio_exercicio, data_fim_exercicio,
				   codigo_conta, descricao_conta, valor_conta
			FROM itr_dados 
			WHERE cnpj = ? AND data_referencia = ? AND versao = ?
			ORDER BY grupo_itr, codigo_conta
		""", (normalize_cnpj(cnpj), data_referencia, versao)).fetchall()
		
		conn.close()
		
		return [dict(row) for row in result]
	
	def exists_for_context(self, cnpj: str, data_referencia: str, versao: int) -> bool:
		"""
		Verifica se já existem dados para um contexto específico
		"""
		conn = get_conn()
		cur = conn.cursor()
		
		result = cur.execute("""
			SELECT COUNT(*) FROM itr_dados 
			WHERE cnpj = ? AND data_referencia = ? AND versao = ?
		""", (normalize_cnpj(cnpj), data_referencia, versao)).fetchone()
		
		conn.close()
		
		return result[0] > 0 if result else False