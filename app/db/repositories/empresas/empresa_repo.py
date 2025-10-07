import sqlite3
from app.core.utils import normalize_cnpj

class EmpresaRepo:
	def __init__(self, db_path=None):
		self.db_path = db_path or 'data/dmarki.db'

	def _conn(self):
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		return conn

	def listar_empresas(self, page=1, page_size=20):
		offset = (page - 1) * page_size
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute('SELECT COUNT(*) FROM empresa')
			total = cur.fetchone()[0]
			cur.execute('SELECT * FROM empresa ORDER BY codigo_negociacao LIMIT ? OFFSET ?', (page_size, offset))
			rows = [dict(row) for row in cur.fetchall()]
		return rows, total

	def buscar_por_cnpj(self, cnpj):
		cnpj = normalize_cnpj(cnpj)
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute('SELECT * FROM empresa WHERE cnpj = ?', (cnpj,))
			row = cur.fetchone()
			return dict(row) if row else None

	def buscar_por_codigo(self, codigo):
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute('SELECT * FROM empresa WHERE codigo_negociacao = ?', (codigo,))
			row = cur.fetchone()
			return dict(row) if row else None

	def inserir_empresa(self, cnpj, codigo, classificacao, tipo_dfp, modo_analise):
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute(
				'INSERT INTO empresa (cnpj, codigo_negociacao, classificacao, tipo_dfp, modo_analise) VALUES (?, ?, ?, ?, ?)',
				(cnpj, codigo, classificacao, tipo_dfp, modo_analise)
			)
			conn.commit()

	def atualizar_empresa(self, cnpj, codigo, classificacao, tipo_dfp, modo_analise):
		with self._conn() as conn:
			cur = conn.cursor()
			cur.execute(
				'UPDATE empresa SET codigo_negociacao = ?, classificacao = ?, tipo_dfp = ?, modo_analise = ? WHERE cnpj = ?',
				(codigo, classificacao, tipo_dfp, modo_analise, cnpj)
			)
			conn.commit()
