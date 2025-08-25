from typing import Optional, List
from ..connection import get_conn

def upsert_by_ticker(**kwargs) -> tuple[int, bool]:
    """
    Insert Valor Mobiliario. 
    Returns (id, was_inserted) where was_inserted.
    """
    conn = get_conn(); cur = conn.cursor()
    
    # Try to insert first
        
    # Get the ID and controle_id of the updated record
    row = conn.execute("SELECT id,controle_id FROM ativos WHERE ticker=?;", (kwargs["ticker"],)).fetchone()

    # Insert if not exists
    if row is None:
        try:
            cur.execute("""
                INSERT INTO ativos(ticker, nome, classe, empresa_id, controle_id,
                                valor_mobiliario, sigla_classe_acao, classe_acao,
                                composicao, mercado, data_inicio_negociacao,
                                data_fim_negociacao, segmento, importado, ativo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (kwargs["ticker"], kwargs["nome"], kwargs["classe"], kwargs.get("empresa_id"),
                    kwargs.get("controle_id"), kwargs["valor_mobiliario"], kwargs["sigla_classe_acao"],
                    kwargs["classe_acao"], kwargs["composicao"], kwargs["mercado"],
                    kwargs["data_inicio_negociacao"], kwargs["data_fim_negociacao"],
                    kwargs["segmento"], kwargs["importado"], kwargs["ativo"]))
            conn.commit()
            nid = cur.lastrowid
            conn.close()
            return nid, 1
        except Exception as e:
            conn.close()
            raise Exception(f"Error inserting ativo: {e}")
    

    # Update if controle_id is older
    if int(row['controle_id']) < int(kwargs.get("controle_id", 0)):
        try: 
            cur.execute("""
                UPDATE ativos SET nome=?, classe=?, empresa_id=?, controle_id=?,
                    valor_mobiliario=?, sigla_classe_acao=?, classe_acao=?, composicao=?, mercado=?,
                    data_inicio_negociacao=?, data_fim_negociacao=?, segmento=?, importado=?, ativo=?,
                    atualizado_em=datetime('now')
                    WHERE ticker=?;
                """, (kwargs["nome"], kwargs["classe"], kwargs.get("empresa_id"),
                        kwargs.get("controle_id"), kwargs["valor_mobiliario"], kwargs["sigla_classe_acao"],
                        kwargs["classe_acao"], kwargs["composicao"], kwargs["mercado"],
                        kwargs["data_inicio_negociacao"], kwargs["data_fim_negociacao"],
                        kwargs["segmento"], kwargs["importado"], kwargs["ativo"],
                        kwargs["ticker"]))
            conn.commit()
            return row['id'], 2
        except Exception as e:
            conn.close()
            raise Exception(f"Error updating ativo: {e}")

    # If controle_id is not older, do nothing
    return 0, 0