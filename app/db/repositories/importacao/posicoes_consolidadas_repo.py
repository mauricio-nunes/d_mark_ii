from typing import List

class PosicoesConsolidadasRepo:
    def __init__(self, conn):
        self.conn = conn
  

    def criar(self, data: dict) -> int:
        """Cria novo registro de posição consolidada"""

        cur = self.conn.cursor()
        cur.execute('''
            INSERT INTO posicao_consolidada(
                data_referencia, produto, instituicao, conta, ativo_id, corretora_id, codigo_negociacao,cnpj_empresa,codigo_isin,tipo_indexador,adm_escriturador_emissor,quantidade,
                quantidade_disponivel, quantidade_indisponivel, motivo, preco_fechamento,data_vencimento, valor_aplicado, valor_liquido, valor_atualizado, tipo_ativo,tipo_regime,data_emissao,contraparte
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['data_referencia'],data['produto'], data['instituicao'], data['conta'],data['ativo_id'], data['corretora_id'],
            data['codigo_negociacao'],data['cnpj_empresa'],data['codigo_isin'],data['tipo_indexador'],data['adm_escriturador_emissor'],data['quantidade'],
            data['quantidade_disponivel'], data['quantidade_indisponivel'],data['motivo'],data['preco_fechamento'],data['data_vencimento'], data['valor_aplicado'],
            data['valor_liquido'], data['valor_atualizado'], data['tipo_ativo'], data['tipo_regime'],
            data['data_emissao'], data['contraparte']
        ))
    
        new_id = cur.lastrowid
        return new_id

    def excluir_por_competencia(self, data_referencia: str) -> int:
        """Remove todos os registros de uma competência (mês/ano)"""
    
        # Extrair ano-mês da data_referencia (YYYY-MM-DD -> YYYY-MM)
        ano_mes = data_referencia[:7]  # YYYY-MM
        
        # Contar registros que serão removidos
        count = self.conn.execute(
            "SELECT COUNT(*) as c FROM posicao_consolidada WHERE substr(data_referencia, 1, 7) = ?",
            (ano_mes,)
        ).fetchone()['c']
        
        # Remover registros
        self.conn.execute(
            "DELETE FROM posicao_consolidada WHERE substr(data_referencia, 1, 7) = ?",
            (ano_mes,)
        )

        return count

    def existe_por_competencia(self, data_referencia: str) -> bool:
        """Verifica se já existem dados para a competência"""
        
        ano_mes = data_referencia[:7]  # YYYY-MM
        count = self.conn.execute(
            "SELECT COUNT(*) as c FROM posicao_consolidada WHERE substr(data_referencia, 1, 7) = ?",
            (ano_mes,)
        ).fetchone()['c']
        return count > 0

    def listar_por_data(self, data_referencia: str, offset: int = 0, limit: int = 50) -> List[dict]:
        """Lista registros por data de referência"""
       
        rows = self.conn.execute('''
            SELECT * FROM posicao_consolidada 
            WHERE data_referencia = ? 
            ORDER BY instituicao, conta, codigo_negociacao
            LIMIT ? OFFSET ?
        ''', (data_referencia, limit, offset)).fetchall()

        return [dict(row) for row in rows]

    def contar_por_data(self, data_referencia: str) -> int:
        """Conta registros por data de referência"""
        
        count = self.conn.execute(
            "SELECT COUNT(*) as c FROM posicao_consolidada WHERE data_referencia = ?",
            (data_referencia,)
        ).fetchone()['c']
        
        return count

    def get_competencias_unicas(self) -> List[str]:
        """Retorna lista de competências (YYYY-MM) únicas no banco"""
        
        rows = self.conn.execute('''
            SELECT DISTINCT substr(data_referencia, 1, 7) as competencia 
            FROM posicao_consolidada 
            ORDER BY competencia DESC
        ''').fetchall()

        return [row['competencia'] for row in rows]