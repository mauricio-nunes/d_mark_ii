from typing import Optional
from ..connection import get_conn

def upsert(hash_linha: str, conn=None, **kwargs) -> tuple[int, bool]:
	"""
	Insert or update movimentação by hash_linha.
	Returns (id, was_inserted) where was_inserted is True for new records, False for updates.
	"""
	if conn is None:
		conn = get_conn()
		should_close = True
	else:
		should_close = False
	cur = conn.cursor()
	
	# Try to insert first
	try:
		cur.execute("""
			INSERT INTO movimentacao(hash_linha, entrada_saida,data, movimentacao, produto, 
									codigo, codigo_negociacao, instituicao, quantidade,
									preco_unitario, valor_total_operacao)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
		""", (hash_linha, kwargs["entrada_saida"], kwargs["data"], kwargs["movimentacao"], kwargs["produto"],
			  kwargs["codigo"], kwargs.get("codigo_negociacao"), kwargs["instituicao"],
			  kwargs["quantidade"], kwargs["preco_unitario"], kwargs.get("valor_total_operacao")))
		if should_close:
			conn.commit()
			nid = cur.lastrowid
			conn.close()
			
		else:
			nid = cur.lastrowid

			return nid, True

	except Exception as e:
		# Hash already exists, update instead
  

		#conn.rollback()
		cur.execute("""
			UPDATE movimentacao SET entrada_saida=?,data=?, movimentacao=?, produto=?, 
									codigo=?, codigo_negociacao=?, instituicao=?, quantidade=?,
									preco_unitario=?, valor_total_operacao=?, atualizado_em=datetime('now')
			WHERE hash_linha=?;
		""", (kwargs["entrada_saida"], kwargs["data"], kwargs["movimentacao"], kwargs["produto"],
			  kwargs["codigo"], kwargs.get("codigo_negociacao"), kwargs["instituicao"],
			  kwargs["quantidade"], kwargs["preco_unitario"], kwargs.get("valor_total_operacao"),
			  hash_linha))

		# Get the ID of the updated record
		row = conn.execute("SELECT id FROM movimentacao WHERE hash_linha=?;", (hash_linha,)).fetchone()
		if should_close:
			conn.commit()
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

def ticker_exists(ticker: str) -> bool:
	"""Verifica se o ticker existe em movimentacao"""
	conn = get_conn()
	row = conn.execute("SELECT 1 FROM movimentacao WHERE codigo_negociacao = ? LIMIT 1;", (ticker,)).fetchone()
	conn.close()
	return row is not None

def list_by_codigo(codigo: str, consolidado: bool = False) -> list[dict]:
	"""Lista movimentações por codigo"""
	conn = get_conn()
	rows = conn.execute("""
		SELECT * FROM movimentacao 
		WHERE codigo = ? AND (consolidado = ? OR consolidado IS NULL)
		ORDER BY date(data) ASC , movimentacao DESC;
	""", (codigo, int(consolidado))).fetchall()
	conn.close()
	return [dict(row) for row in rows]

def list_by_codigo_negociacao(codigo: str, consolidado: bool = False) -> list[dict]:
	"""Lista movimentações por codigo"""
	conn = get_conn()
	rows = conn.execute("""
		SELECT * FROM movimentacao 
		WHERE codigo_negociacao = ? AND (consolidado = ? OR consolidado IS NULL)
		ORDER BY date(data) ASC , movimentacao DESC;
	""", (codigo, int(consolidado))).fetchall()
	conn.close()
	return [dict(row) for row in rows]