from typing import Optional
from ..connection import get_conn

def upsert(hash_linha: str, **kwargs) -> tuple[int, bool]:
	"""
	Insert or update movimentação by hash_linha.
	Returns (id, was_inserted) where was_inserted is True for new records, False for updates.
	"""
	conn = get_conn()
	cur = conn.cursor()
	
	# Try to insert first
	try:
		cur.execute("""
			INSERT INTO movimentacao(hash_linha, data, movimentacao, tipo_movimentacao, 
									codigo, codigo_negociacao, ativo_descricao, quantidade,
									preco_unitario, valor_total_operacao)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
		""", (hash_linha, kwargs["data"], kwargs["movimentacao"], kwargs["tipo_movimentacao"],
			  kwargs["codigo"], kwargs.get("codigo_negociacao"), kwargs["ativo_descricao"],
			  kwargs["quantidade"], kwargs["preco_unitario"], kwargs.get("valor_total_operacao")))
		conn.commit()
		nid = cur.lastrowid
		conn.close()
		return nid, True
	except:
		# Hash already exists, update instead
		conn.rollback()
		cur.execute("""
			UPDATE movimentacao SET data=?, movimentacao=?, tipo_movimentacao=?, 
									codigo=?, codigo_negociacao=?, ativo_descricao=?, quantidade=?,
									preco_unitario=?, valor_total_operacao=?, atualizado_em=datetime('now')
			WHERE hash_linha=?;
		""", (kwargs["data"], kwargs["movimentacao"], kwargs["tipo_movimentacao"],
			  kwargs["codigo"], kwargs.get("codigo_negociacao"), kwargs["ativo_descricao"],
			  kwargs["quantidade"], kwargs["preco_unitario"], kwargs.get("valor_total_operacao"),
			  hash_linha))
		conn.commit()
		
		# Get the ID of the updated record
		row = conn.execute("SELECT id FROM movimentacao WHERE hash_linha=?;", (hash_linha,)).fetchone()
		conn.close()
		return row["id"] if row else None, False

def get_by_id(mid: int) -> Optional[dict]:
	"""Get movimentação by ID"""
	conn = get_conn()
	row = conn.execute("SELECT * FROM movimentacao WHERE id=?;", (mid,)).fetchone()
	conn.close()
	return dict(row) if row else None

def list_all(limit: int = 100, offset: int = 0) -> list[dict]:
	"""List all movimentações with pagination"""
	conn = get_conn()
	rows = conn.execute("""
		SELECT * FROM movimentacao 
		ORDER BY data DESC, criado_em DESC 
		LIMIT ? OFFSET ?;
	""", (limit, offset)).fetchall()
	conn.close()
	return [dict(row) for row in rows]

def count() -> int:
	"""Count total movimentações"""
	conn = get_conn()
	row = conn.execute("SELECT COUNT(*) as total FROM movimentacao;").fetchone()
	conn.close()
	return row["total"] if row else 0