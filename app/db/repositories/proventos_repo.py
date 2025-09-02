from typing import List, Optional
from ..connection import get_conn

def create(data: dict) -> int:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO proventos(data_referencia, ticker, descricao, data_pagamento, tipo_evento,
                              instituicao, quantidade, preco_unitario, valor_total,
                              observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (data["data_referencia"], data["ticker"], data.get("descricao",""), data["data_pagamento"],
          data["tipo_evento"], data.get("instituicao"),
          data.get("quantidade"), data.get("preco_unitario"),
          data.get("valor_total"), data.get("observacoes")))
    conn.commit(); nid = cur.lastrowid; conn.close(); return nid
    

def delete_by_competencia(data_referencia: str) -> int:
	"""Remove todos os registros de uma competência (mês/ano)"""
	conn = get_conn()
	# Extrair ano-mês da data_referencia (YYYY-MM-DD -> YYYY-MM)
	ano_mes = data_referencia[:7]  # YYYY-MM
	
	# Contar registros que serão removidos
	count = conn.execute(
		"SELECT COUNT(*) as c FROM proventos WHERE substr(data_referencia, 1, 7) = ?",
		(ano_mes,)
	).fetchone()['c']
	
	# Remover registros
	conn.execute(
		"DELETE FROM proventos WHERE substr(data_referencia, 1, 7) = ?",
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
		"SELECT COUNT(*) as c FROM proventos WHERE substr(data_referencia, 1, 7) = ?",
		(ano_mes,)
	).fetchone()['c']
	conn.close()
	return count > 0

# def update(pid: int, data: dict) -> None:
#     conn = get_conn()
#     conn.execute("""
#         UPDATE proventos
#            SET ticker=?, descricao=?, data_pagamento=?, tipo_evento=?, corretora_id=?,
#                quantidade=?, preco_unitario=?, valor_total=?, observacoes=?
#          WHERE id=?;
#     """, (data["ticker"], data.get("descricao",""), data["data_pagamento"],
#           data["tipo_evento"], data.get("corretora_id"),
#           data.get("quantidade"), data.get("preco_unitario"),
#           data.get("valor_total"), data.get("observacoes",""), pid))
#     conn.commit(); conn.close()

# def soft_delete(pid: int) -> None:
#     conn = get_conn()
#     conn.execute("UPDATE proventos SET ativo=0 WHERE id=?;", (pid,))
#     conn.commit(); conn.close()

# def get_by_id(pid: int) -> Optional[dict]:
#     conn = get_conn(); r = conn.execute("SELECT * FROM proventos WHERE id=?;", (pid,)).fetchone()
#     conn.close(); return dict(r) if r else None

# def list(texto: str="", ticker_id: int|None=None, tipo: str|None=None,
#          data_ini: str|None=None, data_fim: str|None=None,
#          offset: int=0, limit: int=20, apenas_ativos: bool=True) -> list:
#     conn = get_conn()
#     where, p = ["1=1"], []
#     if apenas_ativos: where.append("p.ativo=1")
#     if texto:
#         where.append("(lower(coalesce(p.descricao,'')) LIKE ? OR lower(coalesce(p.observacoes,'')) LIKE ?)")
#         t = f"%{texto.strip().lower()}%"; p += [t, t]
#     if ticker_id: where.append("p.ticker=?"); p.append(ticker_id)
#     if tipo: where.append("p.tipo_evento=?"); p.append(tipo)
#     if data_ini: where.append("p.data_pagamento>=?"); p.append(data_ini)
#     if data_fim: where.append("p.data_pagamento<=?"); p.append(data_fim)

#     rows = conn.execute(f"""
#         SELECT p.id, p.data_pagamento, p.tipo_evento, p.valor_total, p.quantidade, p.preco_unitario,
#                a.ticker AS ticker_str, p.ticker, coalesce(p.descricao,'') AS descricao, coalesce(p.observacoes,'') AS observacoes
#           FROM proventos p
#           JOIN ativos a ON a.id=p.ticker
#          WHERE {' AND '.join(where)}
#          ORDER BY p.data_pagamento ASC, p.id ASC
#          LIMIT ? OFFSET ?;
#     """, (*p, limit, offset)).fetchall()
#     conn.close(); return [dict(r) for r in rows]

# def count(**kwargs) -> int:
#     conn = get_conn()
#     where, p = ["1=1"], []
#     if kwargs.get("apenas_ativos", True): where.append("ativo=1")
#     if kwargs.get("texto"):
#         t = f"%{kwargs['texto'].strip().lower()}%"
#         where.append("(lower(coalesce(descricao,'')) LIKE ? OR lower(coalesce(observacoes,'')) LIKE ?)")
#         p += [t, t]
#     if kwargs.get("ticker_id"): where.append("ticker=?"); p.append(kwargs["ticker_id"])
#     if kwargs.get("tipo"): where.append("tipo_evento=?"); p.append(kwargs["tipo"])
#     if kwargs.get("data_ini"): where.append("data_pagamento>=?"); p.append(kwargs["data_ini"])
#     if kwargs.get("data_fim"): where.append("data_pagamento<=?"); p.append(kwargs["data_fim"])
#     r = conn.execute(f"SELECT COUNT(*) c FROM proventos WHERE {' AND '.join(where)};", p).fetchone()
#     conn.close(); return int(r["c"])
