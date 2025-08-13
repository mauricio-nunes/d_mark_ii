from datetime import datetime
from ..core.decimal_ctx import qty
from ..db.repositories import transacoes_repo, ativos_repo, carteiras_repo
from .posicao_service import posicao_e_pm_ate

class ValidationError(Exception): ...

TIPOS = ("COMPRA","VENDA","BONIFICACAO","SUBSCRICAO","AMORTIZACAO","TRANSFERENCIA","EVENTO")

def _exists(repo, _id, label):
    if not repo.get_by_id(_id): raise ValidationError(f"{label} não encontrada(o).")

def _parse_date(s: str):
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        raise ValidationError("Data inválida. Use YYYY-MM-DD.")

def _can_sell_or_transfer(ticker_id: int, carteira_id: int, data_ref: str, quantidade: str):
    q_str, _ = posicao_e_pm_ate(ticker_id, carteira_id, data_ref)
    pos = qty(q_str)
    if qty(quantidade) > pos:
        raise ValidationError(f"Quantidade indisponível para VENDA/TRANSFERÊNCIA. Disponível em {data_ref}: {pos}")

def incluir(data: dict) -> int:
    _parse_date(data["data"])
    tipo = (data["tipo"] or "").upper()
    if tipo not in TIPOS: raise ValidationError(f"Tipo inválido. Use um de {TIPOS}.")
    _exists(ativos_repo, data["ticker"], "Ativo")
    _exists(carteiras_repo, data["carteira_id"], "Carteira")

    if tipo in ("VENDA","TRANSFERENCIA"):
        _can_sell_or_transfer(data["ticker"], data["carteira_id"], data["data"], data["quantidade"])

    if tipo == "BONIFICACAO":
        data["preco_unitario"] = "0"; data["taxas"] = "0"
    return transacoes_repo.create(data)

def editar(tid: int, data: dict) -> None:
    data["tipo"] = (data["tipo"] or "").upper()
    _parse_date(data["data"])
    _exists(ativos_repo, data["ticker"], "Ativo")
    _exists(carteiras_repo, data["carteira_id"], "Carteira")

    if data["tipo"] in ("VENDA","TRANSFERENCIA"):
        _can_sell_or_transfer(data["ticker"], data["carteira_id"], data["data"], data["quantidade"])

    if data["tipo"] == "BONIFICACAO":
        data["preco_unitario"] = "0"; data["taxas"] = "0"

    transacoes_repo.update(tid, data)

def excluir(tid: int) -> None:
    transacoes_repo.soft_delete(tid)

def transferir(data_base: str, ticker_id: int, origem_id: int, destino_id: int, quantidade: str) -> tuple[int,int]:
    if origem_id == destino_id: raise ValidationError("Origem e destino não podem ser a mesma carteira.")
    _parse_date(data_base)
    _exists(ativos_repo, ticker_id, "Ativo")
    _exists(carteiras_repo, origem_id, "Carteira origem")
    _exists(carteiras_repo, destino_id, "Carteira destino")
    _can_sell_or_transfer(ticker_id, origem_id, data_base, quantidade)

    _, pm_str = posicao_e_pm_ate(ticker_id, origem_id, data_base)

    saida = {
        "data": data_base, "tipo": "TRANSFERENCIA", "corretora_id": None,
        "quantidade": quantidade, "ticker": ticker_id, "carteira_id": origem_id,
        "preco_unitario": "0", "taxas": "0", "observacoes": "Transferência (saída)"
    }
    entrada = {
        "data": data_base, "tipo": "TRANSFERENCIA", "corretora_id": None,
        "quantidade": quantidade, "ticker": ticker_id, "carteira_id": destino_id,
        "preco_unitario": pm_str, "taxas": "0", "observacoes": "Transferência (entrada)"
    }
    tid_out = transacoes_repo.create(saida)
    tid_in = transacoes_repo.create(entrada)
    return tid_out, tid_in
