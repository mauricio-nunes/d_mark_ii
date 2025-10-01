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

def render_table(rows, headers, tablefmt='fancy_grid'):
    """Renderiza tabela usando tabulate ou fallback simples."""
    try:
        from tabulate import tabulate
        return tabulate(rows, headers=headers, tablefmt=tablefmt)
    except ImportError:
        # Fallback simples sem tabulate
        lines = []
        
        # Calcular larguras das colunas
        if not rows:
            return ""
        
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(str(header))
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width + 2)
        
        # Linha de cabeçalho
        header_line = "|".join(str(h).center(w) for h, w in zip(headers, col_widths))
        lines.append(header_line)
        lines.append("-" * len(header_line))
        
        # Linhas de dados
        for row in rows:
            row_line = "|".join(str(row[i] if i < len(row) else "").center(col_widths[i]) 
                               for i in range(len(headers)))
            lines.append(row_line)
        
        return "\n".join(lines)

def paint_gain_loss(value):
    """Pinta valor positivo em verde, negativo em vermelho."""
    if value is None:
        return "N/D"
    
    if isinstance(value, (int, float)) and value > 0:
        return Fore.GREEN + str(value) + Style.RESET_ALL
    elif isinstance(value, (int, float)) and value < 0:
        return Fore.RED + str(value) + Style.RESET_ALL
    else:
        return str(value)

def paint_header(text):
    """Pinta header com cor destacada."""
    return Fore.CYAN + Style.BRIGHT + str(text) + Style.RESET_ALL

def paint_success(text):
    """Pinta texto de sucesso em verde."""
    return Fore.GREEN + str(text) + Style.RESET_ALL

def paint_warning(text):
    """Pinta texto de aviso em amarelo."""
    return Fore.YELLOW + str(text) + Style.RESET_ALL

def paint_error(text):
    """Pinta texto de erro em vermelho."""
    return Fore.RED + str(text) + Style.RESET_ALL
