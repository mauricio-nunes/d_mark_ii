from ..db.repositories import carteiras_repo, transacoes_repo, movimentacao_repo
from datetime import date
from ..core.decimal_ctx import D, money, qty

class ValidationError(Exception):
    pass

def listar_carteiras():
    """Lista carteiras ativas"""
    return carteiras_repo.list("", True, 0, 1000)

def ticker_existe_em_movimentacao(ticker: str) -> bool:
    """Verifica se o ticker existe em movimentacao"""
    return movimentacao_repo.ticker_exists(ticker)

def listar_movimentacoes_nao_consolidadas(codigo: str):
    """Lista posições não consolidadas para o ticker"""
    return movimentacao_repo.list_by_codigo(codigo, consolidado=False)

def consolidar_movimentacao(carteira_id: int, ticker: str, dry_run: bool = False):
    """Consolida movimentações para o ticker na carteira especificada"""
    # Verificar carteira
    carteira = carteiras_repo.get_by_id(carteira_id)
    if not carteira:
        raise ValidationError("Carteira não encontrada.")

    #listar as movimentações não consolidadas
    
    codigo = ticker[:4] 

    movimentacoes = listar_movimentacoes_nao_consolidadas(codigo)
    if not movimentacoes:
        raise ValidationError(f"Nenhuma posição não consolidada encontrada para {ticker}.")
    transacoes = []
    qtde_acumulada = D('0.0')
    valor_acumulado = D('0.0')
    for movimentacao in movimentacoes:
        #verificar se o codigo de negociacao é igual ao ticker informado se for diferente pode ser uma subscrição
        if movimentacao['codigo_negociacao'] != ticker:
            #verificar se o c codigo de negociacao termina com 11 para units 
            if movimentacao['codigo_negociacao'].strip().endswith('11'):
                continue
            
            if movimentacao['movimentacao'] == "direitos de subscricao - exercido" and movimentacao['entrada_saida'] == "debito":
                valor_acumulado += money(movimentacao['valor_total_operacao'])
                qtde_acumulada += qty(movimentacao['quantidade'])
                transacoes.append({
                    "data": movimentacao['data'],
                    "tipo": "SUBSCRIÇÃO",
                    "corretora": movimentacao['instituicao'],
                    "ticker": ticker,
                    "quantidade": qty(movimentacao['quantidade']),
                    "preco_unitario": money(movimentacao['preco_unitario']),
                    "cartera_id": carteira_id,
                    "taxas": 0.0,
                    "valor_total_operacao": money(movimentacao['valor_total_operacao']),
                    "valor_investido": valor_acumulado,
                    "preco_medio": valor_acumulado / qtde_acumulada if qtde_acumulada != D('0.0') else D('0.0'),
                    "quantidade_total": qtde_acumulada,
                    "observacoes": f"Subscrição - de {movimentacao['codigo_negociacao']}"
                })
                
            
            
            continue  #pular para a próxima movimentação
        else:
            
        
            if movimentacao['movimentacao'] == "transferencia - liquidacao" and movimentacao['entrada_saida'] == "credito":
                
                valor_acumulado += money(movimentacao['valor_total_operacao'])
                qtde_acumulada += qty(movimentacao['quantidade'])
                transacoes.append({
                    "data": movimentacao['data'],
                    "tipo": "COMPRA",
                    "corretora": movimentacao['instituicao'],
                    "ticker": movimentacao['codigo_negociacao'],
                    "quantidade": qty(movimentacao['quantidade']),
                    "preco_unitario": money(movimentacao['preco_unitario']),
                    "cartera_id": carteira_id,
                    "taxas": 0.0,
                    "valor_total_operacao": money(movimentacao['valor_total_operacao']),
                    "valor_investido": valor_acumulado,
                    "preco_medio": valor_acumulado / qtde_acumulada if qtde_acumulada != D('0.0') else D('0.0'),
                    "quantidade_total": qtde_acumulada,
                    "observacoes": f"Consolidação de transferência - liquidação para {ticker}"
                })
                
            elif movimentacao['movimentacao'] == "transferencia - liquidacao" and movimentacao['entrada_saida'] == "debito":
                valor_acumulado += (money(movimentacao['valor_total_operacao']) * -1)
                qtde_acumulada += (qty(movimentacao['quantidade']) * -1)
                if qtde_acumulada ==0:
                    valor_acumulado = 0
                transacoes.append({
                    "data": movimentacao['data'],
                    "tipo": "VENDA",
                    "corretora": movimentacao['instituicao'],
                    "ticker": movimentacao['codigo_negociacao'],
                    "quantidade": qty(movimentacao['quantidade']),
                    "preco_unitario": money(movimentacao['preco_unitario']),
                    "cartera_id": carteira_id,
                    "taxas": 0.0,
                    "valor_total_operacao": money(movimentacao['valor_total_operacao']),
                    "valor_investido": valor_acumulado,
                    "preco_medio": valor_acumulado / qtde_acumulada if qtde_acumulada != D('0.0') else D('0.0'),
                    "quantidade_total": qtde_acumulada,
                    "observacoes": f"Consolidação de transferência - liquidação para {ticker}"
                })
            elif movimentacao['movimentacao'] == "grupamento" and movimentacao['entrada_saida'] == "credito":
                #valor_acumulado = (money(movimentacao['valor_total_operacao']))
                qtde_acumulada = (qty(movimentacao['quantidade']))
                transacoes.append({
                    "data": movimentacao['data'],
                    "tipo": "AGRUPAMENTO",
                    "corretora": movimentacao['instituicao'],
                    "ticker": movimentacao['codigo_negociacao'],
                    "quantidade": qty(movimentacao['quantidade']),
                    "preco_unitario": money(movimentacao['preco_unitario']),
                    "cartera_id": carteira_id,
                    "taxas": 0.0,
                    "valor_total_operacao": money(movimentacao['valor_total_operacao']),
                    "valor_investido": valor_acumulado,
                    "preco_medio": valor_acumulado / qtde_acumulada if qtde_acumulada != D('0.0') else D('0.0'),
                    "quantidade_total": qtde_acumulada,
                    "observacoes": f"Grupamento {ticker}"
                })
            elif movimentacao['movimentacao'] == "desdobro" and movimentacao['entrada_saida'] == "credito":
                #valor_acumulado = (money(movimentacao['valor_total_operacao']))
                qtde_acumulada += (qty(movimentacao['quantidade']))
                transacoes.append({
                    "data": movimentacao['data'],
                    "tipo": "DESDOBRAMENTO",
                    "corretora": movimentacao['instituicao'],
                    "ticker": movimentacao['codigo_negociacao'],
                    "quantidade": qty(movimentacao['quantidade']),
                    "preco_unitario": money(movimentacao['preco_unitario']),
                    "cartera_id": carteira_id,
                    "taxas": 0.0,
                    "valor_total_operacao": money(movimentacao['valor_total_operacao']),
                    "valor_investido": valor_acumulado,
                    "preco_medio": valor_acumulado / qtde_acumulada if qtde_acumulada != D('0.0') else D('0.0'),
                    "quantidade_total": qtde_acumulada,
                    "observacoes": f"Desdobramento {ticker}"
                })
            elif movimentacao['movimentacao'] == "bonificacao em ativos" and movimentacao['entrada_saida'] == "credito":
                #valor_acumulado = (money(movimentacao['valor_total_operacao']))
                qtde_acumulada += (qty(movimentacao['quantidade']))
                transacoes.append({
                    "data": movimentacao['data'],
                    "tipo": "BONFICAÇÃO",
                    "corretora": movimentacao['instituicao'],
                    "ticker": movimentacao['codigo_negociacao'],
                    "quantidade": qty(movimentacao['quantidade']),
                    "preco_unitario": money(movimentacao['preco_unitario']),
                    "cartera_id": carteira_id,
                    "taxas": 0.0,
                    "valor_total_operacao": money(movimentacao['valor_total_operacao']),
                    "valor_investido": valor_acumulado ,
                    "preco_medio" : 0.0,
                    "quantidade_total" : qtde_acumulada,
                    "observacoes": f"Desdobramento {ticker}"
                })
            elif movimentacao['movimentacao'] == "leilao de fracao" and movimentacao['entrada_saida'] == "credito":
                valor_acumulado += (money(movimentacao['valor_total_operacao']) *-1)
                qtde_acumulada += (qty(movimentacao['quantidade']) *-1)
                transacoes.append({
                    "data": movimentacao['data'],
                    "tipo": "VENDA FRAÇÃO",
                    "corretora": movimentacao['instituicao'],
                    "ticker": movimentacao['codigo_negociacao'],
                    "quantidade": qty(movimentacao['quantidade']),
                    "preco_unitario": money(movimentacao['preco_unitario']),
                    "cartera_id": carteira_id,
                    "taxas": 0.0,
                    "valor_total_operacao": money(movimentacao['valor_total_operacao']),
                    "valor_investido": valor_acumulado,
                    "preco_medio": valor_acumulado / qtde_acumulada if qtde_acumulada != D('0.0') else D('0.0'),
                    "quantidade_total" : qtde_acumulada,
                    "observacoes": f"Desdobramento {ticker}"
                })
        
    return transacoes
        #verificar se teve SUBSCRICAO
        
        
        
        #VERIFICAR SE FOI FEITO BONIFICAÇÃO
        

        
        

    # # Calcular totais
    # total_quantidade = sum(p['quantidade_disponivel'] for p in positions)
    # total_valor = sum(p['valor_atualizado'] for p in positions)

    # if total_quantidade <= 0:
    #     raise ValidationError("Quantidade total deve ser positiva.")

    # preco_medio = total_valor / total_quantidade

    # Simular transação
    # data_tx = date.today().isoformat()
    # tx_data = {
    #     "data": data_tx,
    #     "tipo": "COMPRA",
    #     "corretora_id": None,
    #     "quantidade": str(total_quantidade),
    #     "ticker": asset['id'],
    #     "carteira_id": carteira_id,
    #     "preco_unitario": str(preco_medio),
    #     "taxas": "0",
    #     "observacoes": f"Consolidação de posições B3 para {ticker}"
    # }

    # if dry_run:
    #     # Apenas simular, não alterar banco
    #     return None, total_quantidade, preco_medio, tx_data

    # # Criar transação
    # tx_id = transacoes_repo.create(tx_data)

    # # Marcar como consolidado
    # ids = [p['id'] for p in positions]
    # b3_posicao_consolidada_repo.update_consolidado(ids, True)

    # return tx_id, total_quantidade, preco_medio, tx_data
    return None, 0, 0.0, {}
