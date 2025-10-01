from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

HALF_UP = ROUND_HALF_UP

def D(value, default: str = "0") -> Decimal:
    """
    Parser decimal tolerante:
    - aceita None, '', 'None', 'NaN'
    - aceita vírgula decimal (10,50 -> 10.50)
    - em caso de erro, retorna Decimal(default)
    """
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal(default)
    s = str(value).strip()
    if s == "" or s.lower() in ("none", "nan"):
        return Decimal(default)
    # vírgula decimal -> ponto
    s = s.replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        # última tentativa: filtra apenas dígitos, ponto e sinal
        s2 = "".join(ch for ch in s if ch.isdigit() or ch in ".-")
        if s2 in ("", "-"):
            return Decimal(default)
        try:
            return Decimal(s2)
        except InvalidOperation:
            return Decimal(default)

def money(x) -> Decimal:
    return D(x).quantize(Decimal("0.0001"), rounding=HALF_UP)

def qty(x) -> Decimal:
    return D(x).quantize(Decimal("0.000001"), rounding=HALF_UP)