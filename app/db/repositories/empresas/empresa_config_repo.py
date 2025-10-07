from typing import Optional, List, Dict, Any
import sqlite3
from app.core.utils import normalize_cnpj, valid_cnpj, ValidationError


class EmpresaConfigRepo:
	"""Repository para a tabela de configuração de empresas."""

	def __init__(self, conn: sqlite3.Connection):
		self.conn = conn
		self.conn.row_factory = sqlite3.Row

	def listar_todas(self) -> List[Dict[str, Any]]:
		"""Lista todas as configurações de empresas."""
		cur = self.conn.cursor()
		rows = cur.execute("""
			SELECT id, cnpj, codigo_negociacao, classificacao, tipo_dfp, modo_analise,
				   criado_em, atualizado_em
			FROM empresas_config 
			ORDER BY codigo_negociacao
		""").fetchall()
		
		return [dict(row) for row in rows]

	def obter_por_id(self, id: int) -> Optional[Dict[str, Any]]:
		"""Obtém configuração de empresa por ID."""
		cur = self.conn.cursor()
		row = cur.execute("""
			SELECT id, cnpj, codigo_negociacao, classificacao, tipo_dfp, modo_analise,
				   criado_em, atualizado_em
			FROM empresas_config 
			WHERE id = ?
		""", (id,)).fetchone()
		
		return dict(row) if row else None

	def obter_por_cnpj(self, cnpj: str) -> Optional[Dict[str, Any]]:
		"""Obtém configuração de empresa por CNPJ."""
		cnpj_normalizado = normalize_cnpj(cnpj)
		cur = self.conn.cursor()
		row = cur.execute("""
			SELECT id, cnpj, codigo_negociacao, classificacao, tipo_dfp, modo_analise,
				   criado_em, atualizado_em
			FROM empresas_config 
			WHERE cnpj = ?
		""", (cnpj_normalizado,)).fetchone()
		
		return dict(row) if row else None

	def obter_por_codigo(self, codigo_negociacao: str) -> Optional[Dict[str, Any]]:
		"""Obtém configuração de empresa por código de negociação."""
		cur = self.conn.cursor()
		row = cur.execute("""
			SELECT id, cnpj, codigo_negociacao, classificacao, tipo_dfp, modo_analise,
				   criado_em, atualizado_em
			FROM empresas_config 
			WHERE codigo_negociacao = ?
		""", (codigo_negociacao.upper(),)).fetchone()
		
		return dict(row) if row else None

	def criar(self, dados: Dict[str, Any]) -> Dict[str, Any]:
		"""Cria nova configuração de empresa."""
		cnpj_normalizado = normalize_cnpj(dados['cnpj'])
		codigo_upper = dados['codigo_negociacao'].upper()
		
		cur = self.conn.cursor()
		cur.execute("""
			INSERT INTO empresas_config (cnpj, codigo_negociacao, classificacao, tipo_dfp, modo_analise)
			VALUES (?, ?, ?, ?, ?)
		""", (
			cnpj_normalizado,
			codigo_upper,
			dados.get('classificacao'),
			dados.get('tipo_dfp'),
			dados.get('modo_analise')
		))
		
		id_criado = cur.lastrowid
		self.conn.commit()
		
		return self.obter_por_id(id_criado)

	def atualizar(self, id: int, dados: Dict[str, Any]) -> Dict[str, Any]:
		"""Atualiza configuração de empresa existente."""
		campos_para_atualizar = []
		valores = []
		
		if 'cnpj' in dados:
			campos_para_atualizar.append('cnpj = ?')
			valores.append(normalize_cnpj(dados['cnpj']))
		
		if 'codigo_negociacao' in dados:
			campos_para_atualizar.append('codigo_negociacao = ?')
			valores.append(dados['codigo_negociacao'].upper())
		
		if 'classificacao' in dados:
			campos_para_atualizar.append('classificacao = ?')
			valores.append(dados['classificacao'])
		
		if 'tipo_dfp' in dados:
			campos_para_atualizar.append('tipo_dfp = ?')
			valores.append(dados['tipo_dfp'])
		
		if 'modo_analise' in dados:
			campos_para_atualizar.append('modo_analise = ?')
			valores.append(dados['modo_analise'])

		if not campos_para_atualizar:
			return self.obter_por_id(id)
		
		valores.append(id)
		
		cur = self.conn.cursor()
		cur.execute(f"""
			UPDATE empresas_config 
			SET {', '.join(campos_para_atualizar)}
			WHERE id = ?
		""", valores)
		
		self.conn.commit()
		
		return self.obter_por_id(id)

	def excluir(self, id: int) -> bool:
		"""Exclui configuração de empresa."""
		cur = self.conn.cursor()
		cur.execute("DELETE FROM empresas_config WHERE id = ?", (id,))
		linhas_afetadas = cur.rowcount
		self.conn.commit()
		
		return linhas_afetadas > 0

	def buscar(self, termo: str) -> List[Dict[str, Any]]:
		"""Busca empresas por termo (código de negociação, CNPJ ou classificação)."""
		termo_busca = f"%{termo}%"
		cnpj_normalizado = normalize_cnpj(termo) if termo else ""
		
		cur = self.conn.cursor()
		rows = cur.execute("""
			SELECT id, cnpj, codigo_negociacao, classificacao, tipo_dfp, modo_analise,
				   criado_em, atualizado_em
			FROM empresas_config 
			WHERE codigo_negociacao LIKE ? 
			   OR cnpj LIKE ?
			   OR classificacao LIKE ?
			   OR cnpj = ?
			ORDER BY codigo_negociacao
		""", (termo_busca, termo_busca, termo_busca, cnpj_normalizado)).fetchall()
		
		return [dict(row) for row in rows]