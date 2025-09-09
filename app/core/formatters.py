from decimal import Decimal
from colorama import Fore, Style

def fmt_money(v: Decimal | None) -> str:
    if v is None:
        return "N/D"
    s = f"{v:,.2f}"
    # converte 12,345.67 -> 12.345,67
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_qty(v: Decimal | None) -> str:
    if v is None:
        return "N/D"
    return f"{v:,.6f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_price(v: Decimal | None) -> str:
    """Formato para preço médio com 3 casas decimais."""
    if v is None:
        return "N/D"
    s = f"{v:,.3f}"
    # converte 12,345.678 -> 12.345,678
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_pct(v: Decimal | None) -> str:
    if v is None:
        return "N/D"
    s = f"{v:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.replace("X", ".")

def fmt_profit(v: Decimal | None) -> str:
    """Valor com cor: verde positivo, vermelho negativo."""
    if v is None:
        return "N/D"
    s = fmt_money(v)
    if v > 0:
        return Fore.GREEN + s + Style.RESET_ALL
    if v < 0:
        return Fore.RED + s + Style.RESET_ALL
    return s

def fmt_profit_pct(v: Decimal | None) -> str:
    """Percentual com cor: verde positivo, vermelho negativo."""
    if v is None:
        return "N/D"
    s = fmt_pct(v)
    if v > 0:
        return Fore.GREEN + s + Style.RESET_ALL
    if v < 0:
        return Fore.RED + s + Style.RESET_ALL
    return s
