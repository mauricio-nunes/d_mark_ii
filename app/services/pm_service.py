from typing import Iterable, Tuple
from decimal import Decimal
from ..core.decimal_ctx import D, money, qty

def iter_effects(transacoes: Iterable[dict]) -> Tuple[Decimal, Decimal]:
    """
    Caminha cronologicamente (já vem ordenado no repo.list) e calcula (qtde, pm).
    Regras:
      - COMPRA/SUBSCRICAO: custo = q*pu + taxas -> entra no PM
      - BONIFICACAO: pu=0 -> dilui PM
      - VENDA: reduz quantidade; não altera PM; se zerar, PM=0
      - TRANSFERENCIA: entrada (pu>0) agrega ao PM; saída (pu=0) só reduz qtde; se zerar, PM=0
    """
    q = D("0"); pm = D("0")
    for t in transacoes:
        tipo = (t["tipo"] or "").upper()
        qt = qty(t["quantidade"])
        pu = money(t.get("preco_unitario") or "0")
        taxas = money(t.get("taxas") or "0")

        if tipo in ("COMPRA","SUBSCRICAO"):
            custo = qt * pu + taxas
            new_q = q + qt
            pm = ((pm*q) + custo) / new_q if new_q != 0 else D("0")
            q = new_q

        elif tipo == "BONIFICACAO":
            new_q = q + qt
            pm = ((pm*q) / new_q) if new_q != 0 else D("0")
            q = new_q

        elif tipo == "VENDA":
            q = q - qt
            if q <= 0: q = D("0"); pm = D("0")

        elif tipo == "TRANSFERENCIA":
            if pu > 0:
                custo = qt * pu  # sem taxas
                new_q = q + qt
                pm = ((pm*q) + custo) / new_q if new_q != 0 else D("0")
                q = new_q
            else:
                q = q - qt
                if q <= 0: q = D("0"); pm = D("0")
        else:
            # AMORTIZACAO/EVENTO: sem efeito no PM neste pacote
            pass

    return (qty(q), money(pm))
