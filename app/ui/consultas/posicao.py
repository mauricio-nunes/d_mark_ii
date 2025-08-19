from decimal import Decimal
from tabulate import tabulate
from colorama import Fore, Style
from ..widgets import title, divider, pause
from ...core.utils import clear_screen
from ...db.repositories import carteiras_repo
from ...services.consultas_service import posicao_por_carteira
from ...core.formatters import fmt_money, fmt_qty, fmt_profit, fmt_profit_pct

def _input(t): 
    return input(Fore.WHITE + t + Style.RESET_ALL)

def _carteira_nome(cid: int) -> str:
    c = carteiras_repo.get_by_id(cid)
    return c["nome"] if c else f"#{cid}"

def tela_posicao():
    clear_screen(); title("Posição por Carteira")
    print("Algumas carteiras:")
    for c in carteiras_repo.list("", True, 0, 10):
        print(f"  {c['id']:>3} - {c['nome']}")
    try:
        cid = int(_input("Carteira (ID)*: ") or "0")
    except:
        print("ID inválido."); pause(); return

    data = _input("Data de referência (YYYY-MM-DD) [ENTER = hoje / todas]: ").strip() or None

    rows = posicao_por_carteira(cid, data)
    clear_screen()
    title(f"Posição — Carteira: { _carteira_nome(cid) }   Data Ref: {data or 'N/D'}")
    divider()

    if not rows:
        print("Nenhuma posição encontrada."); pause(); return

    table = []
    total_qtd = Decimal("0")
    total_bruto = Decimal("0")
    total_atual = Decimal("0")

    # Monta linhas
    for r in rows:
        q = r["quantidade"]              # Decimal
        pm = r["pm"]                     # Decimal
        px = r["fech_preco"]             # Decimal | None

        valor_bruto = q * pm
        valor_atual = (q * px) if px is not None else None
        lucro = (valor_atual - valor_bruto) if (valor_atual is not None) else None
        lucro_pct = ((lucro / valor_bruto) * 100) if (lucro is not None and valor_bruto != 0) else None

        # Totais: somamos apenas quando há preço de fechamento
        total_qtd += q
        total_bruto += valor_bruto
        if valor_atual is not None:
            total_atual += valor_atual

        table.append([
            r["ticker"],
            fmt_qty(q),
            fmt_money(pm),
            fmt_money(valor_bruto),
            fmt_money(valor_atual),
            fmt_profit(luco=lucro) if False else fmt_profit(lucro),   # mypy silence :)
            fmt_profit_pct(lucro_pct),
            r["fech_data"]
        ])

    # Totais consolidados
    total_lucro = (total_atual - total_bruto) if total_atual != 0 else Decimal("0")
    total_pct = ((total_lucro / total_bruto) * 100) if total_bruto != 0 else Decimal("0")

    table.append([
        "**TOTAL**",
        fmt_qty(total_qtd),
        "",
        fmt_money(total_bruto),
        fmt_money(total_atual if total_atual != 0 else None),
        fmt_profit(total_lucro if total_atual != 0 else None),
        fmt_profit_pct(total_pct if total_atual != 0 else None),
        ""
    ])

    headers = ["Ticker", "Quantidade", "PM (R$)", "Valor Bruto", "Valor Atual", "Lucro/Prej R$", "Lucro/Prej %", "Fechamento de"]
    print(tabulate(table, headers=headers, tablefmt="grid", stralign="right", numalign="right"))
    print()
    pause()
