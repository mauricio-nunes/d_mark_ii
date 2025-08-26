from typing import List, Optional, Tuple
from ..connection import get_conn

def create(data: dict) -> int:
	"""Cria novo registro de posição consolidada"""
	conn = get_conn()
	cur = conn.cursor()
	cur.execute('''
		INSERT INTO b3_posicao_consolidada(
			data_referencia, instituicao, conta, cnpj_empresa, codigo_negociacao,
			nome_ativo, quantidade_disponivel, quantidade_indisponivel,
			valor_atualizado, preco_unitario, percentual_carteira, observacoes
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	''', (
		data['data_referencia'], data['instituicao'], data['conta'],
		data['cnpj_empresa'], data['codigo_negociacao'], data['nome_ativo'],
		data['quantidade_disponivel'], data['quantidade_indisponivel'],
		data['valor_atualizado'], data.get('preco_unitario'),
		data.get('percentual_carteira'), data.get('observacoes', '')
	))
	conn.commit()
	new_id = cur.lastrowid
	conn.close()
	return new_id

def delete_by_competencia(data_referencia: str) -> int:
	"""Remove todos os registros de uma competência (mês/ano)"""
	conn = get_conn()
	# Extrair ano-mês da data_referencia (YYYY-MM-DD -> YYYY-MM)
	ano_mes = data_referencia[:7]  # YYYY-MM
	
	# Contar registros que serão removidos
	count = conn.execute(
		"SELECT COUNT(*) as c FROM b3_posicao_consolidada WHERE substr(data_referencia, 1, 7) = ?",
		(ano_mes,)
	).fetchone()['c']
	
	# Remover registros
	conn.execute(
		"DELETE FROM b3_posicao_consolidada WHERE substr(data_referencia, 1, 7) = ?",
		(ano_mes,)
	)
	conn.commit()
	conn.close()
	return count

def exists_by_competencia(data_referencia: str) -> bool:
	"""Verifica se já existem dados para a competência"""
	conn = get_conn()
	ano_mes = data_referencia[:7]  # YYYY-MM
	count = conn.execute(
		"SELECT COUNT(*) as c FROM b3_posicao_consolidada WHERE substr(data_referencia, 1, 7) = ?",
		(ano_mes,)
	).fetchone()['c']
	conn.close()
	return count > 0

def list_by_data(data_referencia: str, offset: int = 0, limit: int = 50) -> List[dict]:
	"""Lista registros por data de referência"""
	conn = get_conn()
	rows = conn.execute('''
		SELECT * FROM b3_posicao_consolidada 
		WHERE data_referencia = ? 
		ORDER BY instituicao, conta, codigo_negociacao
		LIMIT ? OFFSET ?
	''', (data_referencia, limit, offset)).fetchall()
	conn.close()
	return [dict(row) for row in rows]

def count_by_data(data_referencia: str) -> int:
	"""Conta registros por data de referência"""
	conn = get_conn()
	count = conn.execute(
		"SELECT COUNT(*) as c FROM b3_posicao_consolidada WHERE data_referencia = ?",
		(data_referencia,)
	).fetchone()['c']
	conn.close()
	return count

def get_unique_competencias() -> List[str]:
	"""Retorna lista de competências (YYYY-MM) únicas no banco"""
	conn = get_conn()
	rows = conn.execute('''
		SELECT DISTINCT substr(data_referencia, 1, 7) as competencia 
		FROM b3_posicao_consolidada 
		ORDER BY competencia DESC
	''').fetchall()
	conn.close()
	return [row['competencia'] for row in rows]