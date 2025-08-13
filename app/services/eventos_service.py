from datetime import datetime
from decimal import Decimal
from typing import Iterable, Tuple, List
from ..core.decimal_ctx import D, qty, money
from ..db.repositories import (eventos_repo, ticker_mapping_repo,
                               transacoes_repo, proventos_repo,
                               ativos_repo, carteiras_repo)
from .pm_service import iter_effects

class ValidationError(Exception): ...

# Tipos: Split | Inplit | Bonificacao | TrocaTicker
VALID_TYPES = ("Split","Inplit","Bonificacao","TrocaTicker")

def _parse_date(s: str):
    try: datetime.strptime(s, "%Y-%m-%d")
    except: raise ValidationError("Data inválida (use YYYY-MM-DD).")

def incluir_evento(data: dict) -> int:
    """
    data: {tipo, ticker_antigo?, ticker_novo?, data_ex, num?, den?, observacoes?}
    - Split/Inplit/Bonificacao: exige (ticker_antigo, num, den)
    - TrocaTicker: exige (ticker_antigo, ticker_novo)
    """
    tipo = (data["tipo"] or "").strip()
    if tipo not in VALID_TYPES: raise ValidationError(f"Tipo inválido. Use {VALID_TYPES}.")
    _parse_date(data["data_ex"])

    if tipo in ("Split","Inplit","Bonificacao"):
        if not data.get("ticker_antigo"): raise ValidationError("ticker_antigo é obrigatório.")
        if not data.get("num") or not data.get("den"): raise ValidationError("num/den são obrigatórios.")
    if tipo == "TrocaTicker":
        if not data.get("ticker_antigo") or not data.get("ticker_novo"):
            raise ValidationError("ticker_antigo e ticker_novo são obrigatórios.")

    return eventos_repo.create(data)

def editar_evento(eid: int, data: dict) -> None:
    if not eventos_repo.get_by_id(eid): raise ValidationError("Evento não encontrado.")
    incluir_evento  # só para validar os campos (reutilize regras)
    data["tipo"] = (data["tipo"] or "").strip()
    _parse_date(data["data_ex"])
    eventos_repo.update(eid, data)

def excluir_evento(eid: int) -> None:
    eventos_repo.soft_delete(eid)

# ------------------- Fator acumulado on-the-fly -------------------

def _event_factor_for_ticker_between(ticker_id: int, start_date: str, end_date: str) -> Decimal:
    """
    Retorna Π(num/den) de todos os eventos de Split/Inplit/Bonificacao do ticker
    com data_ex no intervalo (start_date, end_date]  (aplicação para frente).
    Bonificação usa fator (1 + bonus) = num/den.
    """
    if not end_date: return D("1")
    evs = eventos_repo.list(ticker_id=ticker_id, tipo=None, data_ini=start_date, data_fim=end_date, offset=0, limit=10_000)
    f = D("1")
    for e in evs:
        if e["tipo"] in ("Split","Inplit","Bonificacao"):
            num = D(str(e["num"] or "1")); den = D(str(e["den"] or "1"))
            if den == 0: continue
            f *= (num/den)
    return f

def ajustar_tranche(qtd: Decimal, pm: Decimal, fator: Decimal) -> Tuple[Decimal, Decimal]:
    """
    Aplica o fator a uma tranche: qtd' = qtd * fator ; pm' = pm / fator
    """
    if fator == 0: return D("0"), D("0")
    return qty(qtd * fator), money(pm / fator)

def posicao_ajustada_on_the_fly(ticker_id: int, carteira_id: int, data_ref: str | None) -> Tuple[str, str]:
    """
    Recalcula posição/PM ajustando cada transação com o fator entre sua data e data_ref,
    sem regravar histórico.
    """
    txs = transacoes_repo.list(texto="", ticker_id=ticker_id, carteira_id=carteira_id,
                               data_ini=None, data_fim=data_ref, offset=0, limit=10_000_000, apenas_ativas=True)
    # Re-empilha transações aplicando fator forward por transação
    tranches: List[Tuple[Decimal, Decimal]] = []  # lista de (qtd_ajustada, pm_ajustado) acumulada
    for t in txs:
        tipo = (t["tipo"] or "").upper()
        q = qty(t["quantidade"])
        pu = money(t.get("preco_unitario") or "0")
        fator = _event_factor_for_ticker_between(ticker_id, t["data"], data_ref)
        if tipo in ("COMPRA","SUBSCRICAO"):
            q2, pm2 = ajustar_tranche(q, pu, fator)
            # merge com posição atual
            # custo total atual = sum(qi * pmi)
            qt_atual = sum(qi for qi, _ in tranches)
            custo_atual = sum(qi*pmi for qi, pmi in tranches)
            novo_q = qt_atual + q2
            novo_pm = (custo_atual + (q2*pm2)) / novo_q if novo_q != 0 else D("0")
            tranches = [(novo_q, money(novo_pm))]
        elif tipo == "BONIFICACAO":
            q2, _ = ajustar_tranche(q, D("0"), fator)
            # dilui pm: só aumenta quantidade
            if tranches:
                qt_atual, pm_atual = tranches[0]
                novo_q = qt_atual + q2
                novo_pm = (pm_atual * qt_atual) / novo_q if novo_q != 0 else D("0")
                tranches = [(qty(novo_q), money(novo_pm))]
            else:
                tranches = [(q2, D("0"))]
        elif tipo == "VENDA":
            # reduz quantidade ajustada
            if tranches:
                qt_atual, pm_atual = tranches[0]
                qt_venda = ajustar_tranche(q, D("0"), fator)[0]
                novo_q = qt_atual - qt_venda
                if novo_q <= 0: tranches = [(D("0"), D("0"))]
                else: tranches = [(qty(novo_q), pm_atual)]
        elif tipo == "TRANSFERENCIA":
            # entrada com PU>0 (mantém PM) / saída com PU=0
            if pu > 0:
                q2, pm2 = ajustar_tranche(q, pu, fator)
                if tranches:
                    qt_atual, pm_atual = tranches[0]
                    novo_q = qt_atual + q2
                    novo_pm = (pm_atual*qt_atual + pm2*q2) / novo_q if novo_q != 0 else D("0")
                    tranches = [(qty(novo_q), money(novo_pm))]
                else:
                    tranches = [(q2, pm2)]
            else:
                if tranches:
                    qt_atual, pm_atual = tranches[0]
                    qt_saida = ajustar_tranche(q, D("0"), fator)[0]
                    novo_q = qt_atual - qt_saida
                    if novo_q <= 0: tranches = [(D("0"), D("0"))]
                    else: tranches = [(qty(novo_q), pm_atual)]
        else:
            # AMORTIZACAO/EVENTO: ignorados no PM (por enquanto)
            pass

    if not tranches: return ("0", "0")
    qf, pmf = tranches[0]
    if qf <= 0: return ("0", "0")
    return (f"{qf:f}", f"{pmf:f}")

# ------------------- Aplicadores (opcionais) -------------------

def aplicar_bonificacao_gerando_transacoes(eid: int) -> int:
    """
    Para BONIFICACAO: cria transações tipo BONIFICACAO (PU=0) em cada carteira que
    tiver posição na data_ex. Quantidade bônus = q * (num/den - 1).
    Retorna quantidade de lançamentos criados.
    """
    e = eventos_repo.get_by_id(eid)
    if not e or e["tipo"] != "Bonificacao": raise ValidationError("Evento não é Bonificacao.")
    num = D(str(e["num"])); den = D(str(e["den"])); data_ex = e["data_ex"]; ticker_id = e["ticker_antigo"]
    fator_bonus = (num/den) - D("1")
    if fator_bonus <= 0: return 0

    # percorre carteiras existentes
    carters = carteiras_repo.list("", True, 0, 1000)
    from ..services.posicao_service import posicao_e_pm_ate
    created = 0
    for c in carters:
        qtd_str, _ = posicao_e_pm_ate(ticker_id, c["id"], data_ex)
        q = qty(qtd_str)
        if q > 0:
            bonus = qty(q * fator_bonus)
            if bonus > 0:
                from ..db.repositories import transacoes_repo
                data = {
                    "data": data_ex, "tipo": "BONIFICACAO", "corretora_id": None,
                    "quantidade": f"{bonus:f}", "ticker": ticker_id, "carteira_id": c["id"],
                    "preco_unitario": "0", "taxas": "0", "observacoes": f"BONUS auto do evento #{eid}"
                }
                transacoes_repo.create(data); created += 1
    return created

def aplicar_inplit_liquidacao_fracoes(eid: int, preco_liquidacao: str) -> int:
    """
    Para INPLIT: frações são liquidadas em dinheiro.
    Cria PROVENTO tipo OUTROS por carteira: valor = (frac * preco_liquidacao).
    """
    e = eventos_repo.get_by_id(eid)
    if not e or e["tipo"] != "Inplit": raise ValidationError("Evento não é Inplit.")
    num = D(str(e["num"])); den = D(str(e["den"])); data_ex = e["data_ex"]; ticker_id = e["ticker_antigo"]
    fator = num/den
    px = money(preco_liquidacao)

    carters = carteiras_repo.list("", True, 0, 1000)
    from ..services.posicao_service import posicao_e_pm_ate
    created = 0
    for c in carters:
        qtd_str, _ = posicao_e_pm_ate(ticker_id, c["id"], data_ex)
        q = qty(qtd_str)
        if q > 0:
            q_aj = q * fator
            inteira = q_aj.to_integral_value(rounding=0)  # round down
            fracao = q_aj - inteira
            if fracao > 0:
                val = money(fracao * px)
                from ..db.repositories import proventos_repo
                prov = {
                    "ticker": ticker_id, "descricao": f"Liquidação frações INPLIT evento #{eid}",
                    "data_pagamento": data_ex, "tipo_evento": "OUTROS", "corretora_id": None,
                    "quantidade": None, "preco_unitario": None, "valor_total": f"{val:f}",
                    "observacoes": f"fração={fracao}"
                }
                proventos_repo.create(prov); created += 1
    return created
