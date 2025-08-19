from typing import List, Dict, Optional
from decimal import Decimal
from ..db.repositories import transacoes_repo, proventos_repo, fechamentos_repo, ativos_repo, ticker_mapping_repo
from ..services.eventos_service import posicao_ajustada_on_the_fly, _event_factor_for_ticker_between
from ..core.decimal_ctx import D, qty, money

# ---------- helpers ----------

def _unique_tickers_in_carteira(carteira_id: int, ate_data: str | None) -> List[int]:
    txs = transacoes_repo.list(texto="", ticker_id=None, carteira_id=carteira_id,
                               corretora_id=None, data_ini=None, data_fim=ate_data,
                               offset=0, limit=1_000_000, apenas_ativas=True)
    seen = set()
    for t in txs:
        seen.add(t["ticker"])
    return sorted(seen)

def _ultimo_fechamento(ticker_id: int, ate_data: str | None) -> tuple[str|None, str|None]:
    # retorna (data_ref, preco); se não houver, (None, None)
    rows = fechamentos_repo.list(ticker_id=ticker_id, data_ini=None, data_fim=ate_data, offset=0, limit=1_000_000)
    if not rows: return None, None
    # já vem ordenado desc por data_ref
    r = rows[0]
    return r["data_ref"], str(r["preco_fechamento"])

def _apply_ticker_mapping_display(ticker_id: int, data_ref: str | None) -> str:
    # por simplicidade: se houver mapping com data_vigencia <= data_ref, mostrar ticker_novo
    a = ativos_repo.get_by_id(ticker_id)
    if not a: return "N/D"
    if not data_ref:
        return a["ticker"]
    maps = ticker_mapping_repo.list(0, 1000)
    novo = a["ticker"]
    for m in maps:
        if m["ticker_antigo"] == ticker_id and m["data_vigencia"] <= data_ref:
            # troca para o novo
            a2 = ativos_repo.get_by_id(m["ticker_novo"])
            if a2: novo = a2["ticker"]
    return novo

# ---------- 5.1 Posição por Carteira ----------
def _last_fechamento_price_decimal(ticker_id: int, ref_date: Optional[str]) -> Optional[Decimal]:
    rows = fechamentos_repo.list(ticker_id=ticker_id, data_ini=None, data_fim=ref_date, offset=0, limit=10_000)
    if not rows:
        return None
    try:
        return money(rows[0].get("preco_fechamento"))
    except Exception:
        return None

def posicao_por_carteira(carteira_id: int, data_ref: Optional[str]) -> List[Dict]:
    """
    Retorna lista de dicts com:
      - ticker (string já mapeada por data_ref)
      - ticker_id (int)
      - quantidade (Decimal)
      - pm (Decimal)
      - fech_data (str | 'N/D')
      - fech_preco (Decimal | None)
    OBS: Não formata — isso é feito na UI. Também não calcula lucro/valores aqui;
         a UI calcula (valor_bruto, valor_atual, lucro, lucro_pct) para poder somar totais facilmente.
    """
    # descobrir tickers com transações na carteira até a data_ref
    txs = transacoes_repo.list(texto="", ticker_id=None, carteira_id=carteira_id, data_ini=None, data_fim=data_ref,
                               offset=0, limit=1_000_000, apenas_ativas=True)
    tickers = sorted(set(t["ticker"] for t in txs))
    out: List[Dict] = []

    # helper local (reutiliza função de display existente)
    def ticker_display_at(ticker_id: int, ref_date: Optional[str]) -> str:
        atv = ativos_repo.get_by_id(ticker_id)
        if not atv:
            return f"#{ticker_id}"
        disp = atv["ticker"]
        if not ref_date:
            return disp
        maps = ticker_mapping_repo.list(0, 1000)
        chosen = None
        for m in maps:
            if m["ticker_antigo"] == ticker_id and m["data_vigencia"] <= ref_date:
                chosen = m
        if chosen:
            atv2 = ativos_repo.get_by_id(chosen["ticker_novo"])
            if atv2:
                disp = atv2["ticker"]
        return disp

    for tid in tickers:
        q_str, pm_str = posicao_ajustada_on_the_fly(tid, carteira_id, data_ref)
        q = qty(q_str)
        if q <= 0:
            continue
        pm = money(pm_str)

        px = _last_fechamento_price_decimal(tid, data_ref)
        data_fe = None
        if px is not None:
            # pegar a data ref do último fechamento também
            rows = fechamentos_repo.list(ticker_id=tid, data_ini=None, data_fim=data_ref, offset=0, limit=1)
            if rows:
                data_fe = rows[0].get("data_ref")

        out.append({
            "ticker": ticker_display_at(tid, data_ref),
            "ticker_id": tid,
            "quantidade": q,             # Decimal
            "pm": pm,                    # Decimal
            "fech_data": data_fe or "N/D",
            "fech_preco": px             # Decimal | None
        })

    # ordenar por ticker
    out.sort(key=lambda r: r["ticker"])
    return out

# ---------- 5.2 Extrato (com quantidade ajustada na data_ref) ----------

def extrato(carteira_id: int | None, ticker_id: int | None,
            data_ini: str | None, data_fim: str | None, incluir_ajuste: bool = True) -> List[dict]:
    rows = transacoes_repo.list(texto="", ticker_id=ticker_id, carteira_id=carteira_id,
                                corretora_id=None, data_ini=data_ini, data_fim=data_fim,
                                offset=0, limit=200_000, apenas_ativas=True)
    if not incluir_ajuste:
        return rows
    # acrescenta coluna 'qtd_ajustada' (para data_fim; se None, usa hoje? deixamos None = sem ajuste)
    out = []
    for r in rows:
        if data_fim:
            f = _event_factor_for_ticker_between(r["ticker"], r["data"], data_fim)
            qaj = qty(qty(r["quantidade"]) * f)
            r = dict(r); r["qtd_ajustada"] = f"{qaj:f}"
        else:
            r = dict(r); r["qtd_ajustada"] = ""
        out.append(r)
    return out

# ---------- 5.3 Proventos por período ----------

def proventos_por_periodo(ticker_id: int | None, data_ini: str | None, data_fim: str | None) -> List[dict]:
    rows = proventos_repo.list(texto="", ticker_id=ticker_id, tipo=None,
                               data_ini=data_ini, data_fim=data_fim,
                               offset=0, limit=100_000, apenas_ativos=True)
    return rows

# ---------- 5.4 Histórico mensal ----------

def historico_mensal(ticker_id: int | None, data_ini: str | None, data_fim: str | None) -> List[dict]:
    rows = fechamentos_repo.list(ticker_id=ticker_id, data_ini=data_ini, data_fim=data_fim, offset=0, limit=200_000)
    # já vem por data desc; vamos normalizar saída
    out = []
    for r in rows:
        out.append({
            "ticker": r["ticker_str"], "ticker_id": r["ticker"],
            "data_ref": r["data_ref"], "preco_fechamento": r["preco_fechamento"],
            "quantidade": r.get("quantidade")
        })
    return out

# ---------- 5.5 PM detalhado por ativo ----------

def pm_detalhado_por_ativo(ticker_id: int, carteira_id: int, data_ref: str | None) -> List[dict]:
    """
    Retorna timeline com (data, tipo, qtd, pu, taxas, fator_aplicado, qtd_acum, pm_acum) já considerando eventos.
    """
    txs = transacoes_repo.list(texto="", ticker_id=ticker_id, carteira_id=carteira_id,
                               corretora_id=None, data_ini=None, data_fim=data_ref,
                               offset=0, limit=200_000, apenas_ativas=True)
    timeline = []
    q = D("0"); pm = D("0")
    for t in txs:
        f = _event_factor_for_ticker_between(ticker_id, t["data"], data_ref)
        qt = qty(t["quantidade"])
        pu = money(t.get("preco_unitario") or "0")
        tx = money(t.get("taxas") or "0")
        tipo = (t["tipo"] or "").upper()
        # aplicar efeito como no on-the-fly (mesma regra do pm_service, mas ajustando por f)
        if tipo in ("COMPRA","SUBSCRICAO"):
            q2 = qty(qt * f); pm2 = money(pu / f)  # ajustar tranche
            custo = q2 * pm2 + tx
            new_q = q + q2
            pm = ((pm*q) + custo) / new_q if new_q != 0 else D("0")
            q = new_q
        elif tipo == "BONIFICACAO":
            q2 = qty(qt * f)
            new_q = q + q2
            pm = ((pm*q) / new_q) if new_q != 0 else D("0")
            q = new_q
        elif tipo == "VENDA":
            q2 = qty(qt * f)
            q = q - q2
            if q <= 0: q = D("0"); pm = D("0")
        elif tipo == "TRANSFERENCIA":
            if pu > 0:
                q2 = qty(qt * f); pm2 = money(pu / f)
                new_q = q + q2
                pm = ((pm*q) + (q2*pm2)) / new_q if new_q != 0 else D("0")
                q = new_q
            else:
                q2 = qty(qt * f)
                q = q - q2
                if q <= 0: q = D("0"); pm = D("0")
        else:
            pass
        timeline.append({
            "data": t["data"], "tipo": t["tipo"],
            "qtd_orig": t["quantidade"], "pu_orig": t.get("preco_unitario"), "taxas": t.get("taxas"),
            "fator": f"{f:f}", "qtd_aj": f"{(qty(qt * f)):f}", "pu_aj": f"{(money(pu / f)):f}" if pu > 0 else "",
            "qtd_acum": f"{q:f}", "pm_acum": f"{pm:f}"
        })
    return timeline
