from decimal import Decimal, getcontext, ROUND_HALF_UP

# Precisão ampla p/ cálculo intermediário
getcontext().prec = 28
HALF_UP = ROUND_HALF_UP

def D(value) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))

def money(x) -> Decimal:
    """Monetário com 4 casas, half-up."""
    return D(x).quantize(Decimal("0.0001"), rounding=HALF_UP)

def qty(x) -> Decimal:
    """Quantidade com 6 casas, half-up."""
    return D(x).quantize(Decimal("0.000001"), rounding=HALF_UP)
