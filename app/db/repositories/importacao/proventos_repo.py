from typing import List

class ProventosRepo:
    def __init__(self, conn):
        self.conn = conn

    def criar(self, data: dict, conn=None) -> int:
        
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO proventos(data_referencia, ativo, ativo_id, corretora_id, descricao, data_pagamento, tipo_evento,
                                instituicao, quantidade, preco_unitario, valor_total,
                                observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (data["data_referencia"], data["ticker"], data["ativo_id"], data["corretora_id"], data.get("descricao",""), data["data_pagamento"],
            data["tipo_evento"], data.get("instituicao"),
            data.get("quantidade"), data.get("preco_unitario"),
            data.get("valor_total"), data.get("observacoes")))

        nid = cur.lastrowid;

        return nid
        

    def excluir_por_competencia(self, data_referencia: str, conn=None) -> int:
        """Remove todos os registros de uma competência (mês/ano)"""
        

        # Extrair ano-mês da data_referencia (YYYY-MM-DD -> YYYY-MM)
        ano_mes = data_referencia[:7]  # YYYY-MM
        
        # Contar registros que serão removidos
        count = self.conn.execute(
            "SELECT COUNT(*) as c FROM proventos WHERE substr(data_referencia, 1, 7) = ?",
            (ano_mes,)
        ).fetchone()['c']
        
        # Remover registros
        self.conn.execute(
            "DELETE FROM proventos WHERE substr(data_referencia, 1, 7) = ?",
            (ano_mes,)
        )
    
        return count

    def existe_por_competencia(self, data_referencia: str) -> bool:
        """Verifica se já existem dados para a competência"""

        ano_mes = data_referencia[:7]  # YYYY-MM
        count = self.conn.execute(
            "SELECT COUNT(*) as c FROM proventos WHERE substr(data_referencia, 1, 7) = ?",
            (ano_mes,)
        ).fetchone()['c']
        return count > 0