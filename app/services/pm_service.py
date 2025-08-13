from typing import Iterable, Tuple
from decimal import Decimal
from ..core.decimal_ctx import D, money, qty, HALF_UP

# Tipos que AUMENTAM posição
IN_TYPES = {"COMPRA", "SUBSCRICAO", "BONIFICACAO", "TRANSFERENCIA"}
# Tipos que REDUZEM posição
OUT_TYPES = {"VENDA", "TRANSFERENCIA"}

def iter_effects(transacoes: Iterable[dict]) -> Tuple[Decimal, Decimal]:
    """
    Retorna (qtde_final, pm_final). Percorre em ORDEM CRONOLÓGICA.
    Regras:
      - COMPRA/SUBSCRICAO: custo = q * p + taxas -> entra no PM
      - BONIFICACAO: entra com preco_unit=0 -> dilui PM
      - VENDA: reduz quantidade (sem alterar PM)
      - TRANSFERENCIA: se for 'entrada' usa preco_unit como PM de origem; se 'saida', reduz qtde
        (notamos pelo campo 'preco_unitario': para saída ele pode vir vazio; não altera PM).
    Observação: se a posição zera, o PM deve zerar.
    """
    q = D("0")
    pm = D("0")
    for t in transacoes:
        tipo = (t["tipo"] or "").upper()
        qt = qty(t["quantidade"])
        pu = money(t.get("preco_unitario") or "0")
        taxas = money(t.get("taxas") or "0")

        if tipo in ("COMPRA", "SUBSCRICAO"):
            custo = qt * pu + taxas
            new_q = q + qt
            pm = ( (pm * q) + custo ) / new_q if new_q != 0 else D("0")
            q = new_q

        elif tipo == "BONIFICACAO":
            # preco_unitario = 0; aumenta q, dilui pm
            new_q = q + qt
            pm = (pm * q) / new_q if new_q != 0 else D("0")
            q = new_q

        elif tipo == "VENDA":
            # não altera PM, apenas reduz q (bloqueio de vender > posição ocorre no service)
            q = q - qt
            if q <= 0:
                q = D("0"); pm = D("0")

        elif tipo == "TRANSFERENCIA":
            # regra: se for ENTRADA, virá com preco_unitário = PM de origem
            # se for SAÍDA, geralmente preco_unit=null/0 e apenas reduz qtd
            if pu > 0:
                # ENTRADA
                custo = qt * pu  # sem taxas
                new_q = q + qt
                pm = ( (pm * q) + custo ) / new_q if new_q != 0 else D("0")
                q = new_q
            else:
                # SAÍDA
                q = q - qt
                if q <= 0:
                    q = D("0"); pm = D("0")
        else:
            # outros tipos: AMORTIZACAO etc. não afetam PM aqui (poderá ser tratado depois)
            pass

    # arredondar para exibição/persistência padrão
    return (qty(q), money(pm))
