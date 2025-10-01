from typing import Optional, List, Dict, Any
from ...connection import get_conn


class CiaAbertaFcaRepo:
	"""Repository para tabela cia_aberta_fca_geral."""
	
	def __init__(self, conn=None):
		self.conn = conn or get_conn()
	
	def get_by_cnpj(self, cnpj: str) -> Optional[Dict[str, Any]]:
		"""Busca empresa por CNPJ."""
		row = self.conn.execute(
			"SELECT * FROM cia_aberta_fca_geral WHERE cnpj = ?",
			(cnpj,)
		).fetchone()
		return dict(row) if row else None
	
	def upsert_by_cnpj(self, **kwargs) -> tuple[int, str]:
		"""
		Faz upsert baseado em CNPJ e documento_id.
		Retorna (affected_rows, action) onde action = 'inserted'|'updated'|'ignored'
		"""
		cur = self.conn.cursor()
		
		# Verificar se já existe
		existing = cur.execute(
			"SELECT documento_id FROM cia_aberta_fca_geral WHERE cnpj = ?",
			(kwargs['cnpj'],)
		).fetchone()
		
		if existing is None:
			# INSERT - não existe
			cur.execute("""
				INSERT INTO cia_aberta_fca_geral (
					cnpj, data_referencia, documento_id, razao_social, data_constituicao,
					codigo_cvm, data_registro_cvm, categoria_registro, situacao_registro_cvm,
					pais_origem, pais_custodia_valores_mobiliarios, setor_atividade,
					descricao_atividade, situacao_emissor, controle_acionario,
					dia_encerramento_exercicio_social, mes_encerramento_exercicio_social,
					pagina_web, criado_em, atualizado_em
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			""", (
				kwargs['cnpj'], kwargs.get('data_referencia'), kwargs.get('documento_id'),
				kwargs.get('razao_social'), kwargs.get('data_constituicao'),
				kwargs.get('codigo_cvm'), kwargs.get('data_registro_cvm'),
				kwargs.get('categoria_registro'), kwargs.get('situacao_registro_cvm'),
				kwargs.get('pais_origem'), kwargs.get('pais_custodia_valores_mobiliarios'),
				kwargs.get('setor_atividade'), kwargs.get('descricao_atividade'),
				kwargs.get('situacao_emissor'), kwargs.get('controle_acionario'),
				kwargs.get('dia_encerramento_exercicio_social'),
				kwargs.get('mes_encerramento_exercicio_social'),
				kwargs.get('pagina_web'), kwargs['criado_em'], kwargs['atualizado_em']
			))
			return cur.rowcount, 'inserted'
		
		# Comparar documento_id
		existing_doc_id = existing['documento_id'] or 0
		new_doc_id = kwargs.get('documento_id') or 0
		
		if new_doc_id > existing_doc_id:
			# UPDATE - documento mais recente
			cur.execute("""
				UPDATE cia_aberta_fca_geral SET
					data_referencia = ?, documento_id = ?, razao_social = ?,
					data_constituicao = ?, codigo_cvm = ?, data_registro_cvm = ?,
					categoria_registro = ?, situacao_registro_cvm = ?, pais_origem = ?,
					pais_custodia_valores_mobiliarios = ?, setor_atividade = ?,
					descricao_atividade = ?, situacao_emissor = ?, controle_acionario = ?,
					dia_encerramento_exercicio_social = ?, mes_encerramento_exercicio_social = ?,
					pagina_web = ?, atualizado_em = ?
				WHERE cnpj = ?
			""", (
				kwargs.get('data_referencia'), kwargs.get('documento_id'),
				kwargs.get('razao_social'), kwargs.get('data_constituicao'),
				kwargs.get('codigo_cvm'), kwargs.get('data_registro_cvm'),
				kwargs.get('categoria_registro'), kwargs.get('situacao_registro_cvm'),
				kwargs.get('pais_origem'), kwargs.get('pais_custodia_valores_mobiliarios'),
				kwargs.get('setor_atividade'), kwargs.get('descricao_atividade'),
				kwargs.get('situacao_emissor'), kwargs.get('controle_acionario'),
				kwargs.get('dia_encerramento_exercicio_social'),
				kwargs.get('mes_encerramento_exercicio_social'),
				kwargs.get('pagina_web'), kwargs['atualizado_em'], kwargs['cnpj']
			))
			return cur.rowcount, 'updated'
		else:
			# IGNORAR - documento igual ou mais antigo
			return 0, 'ignored'
	
	def count_all(self) -> int:
		"""Conta total de empresas."""
		result = self.conn.execute("SELECT COUNT(*) as count FROM cia_aberta_fca_geral").fetchone()
		return result['count']
	
	def listar_paginado(self, offset: int = 0, limit: int = 20, filtro: str = "") -> List[Dict[str, Any]]:
		"""Lista empresas com paginação e filtro opcional."""
		where_clause = ""
		params = []
		
		if filtro:
			where_clause = "WHERE razao_social LIKE ? OR cnpj LIKE ? OR codigo_cvm LIKE ?"
			filtro_like = f"%{filtro}%"
			params = [filtro_like, filtro_like, filtro_like]
		
		query = f"""
			SELECT cnpj, razao_social, codigo_cvm, situacao_registro_cvm, 
				   setor_atividade, data_referencia, documento_id
			FROM cia_aberta_fca_geral 
			{where_clause}
			ORDER BY razao_social 
			LIMIT ? OFFSET ?
		"""
		params.extend([limit, offset])
		
		rows = self.conn.execute(query, params).fetchall()
		return [dict(row) for row in rows]