from typing import Tuple
from ..db.repositories import transacoes_repo
from ..core.decimal_ctx import D
from .pm_service import iter_effects

def posicao_e_pm_ate(ticker_id: int, carteira_id: int, data_ref: str | None = None) -> Tuple[str, str]:
    txs = transacoes_repo.list(
        texto="", ticker_id=ticker_id, carteira_id=carteira_id,
        corretora_id=None, data_ini=None, data_fim=data_ref,
        offset=0, limit=10_000_000, apenas_ativas=True
    )
    q, pm = iter_effects(txs)
    return (f"{q:f}", f"{pm:f}")
