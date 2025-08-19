from decimal import Decimal
from tabulate import tabulate
from colorama import Fore, Style
from ..widgets import title, divider, pause
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...core.decimal_ctx import money, qty, D
from ...db.repositories import ativos_repo
from ...services.consultas_service import proventos_por_periodo
from ...core.formatters import fmt_money, fmt_qty

def _input(t): 
    return input(Fore.WHITE + t + Style.RESET_ALL)

def _valor_total_row(r: dict) -> Decimal | None:
    """
    Usa valor_total quando houver; senão, tenta quantidade*preco_unitario; senão None.
    """
    v = r.get("valor_total")
    if v not in (None, ""):
        return money(v)
    q = r.get("quantidade")
    pu = r.get("preco_unitario")
    if q not in (None, "") and pu not in (None, ""):
        return qty(q) * money(pu)
    return None

def _render_page(rows):
    headers = ["ID", "Data", "Tipo", "Ticker", "Valor Total", "Qtd", "PU", "Descrição"]
    table = []
    for r in rows:
        val = _valor_total_row(r)
        table.append([
            r.get("id"),
            r.get("data_pagamento"),
            r.get("tipo_evento"),
            r.get("ticker_str"),
            fmt_money(val) if val is not None else "N/D",
            fmt_qty(qty(r.get("quantidade"))) if r.get("quantidade") not in (None, "") else "",
            fmt_money(money(r.get("preco_unitario"))) if r.get("preco_unitario") not in (None, "") else "",
            r.get("descricao","")
        ])
    print(tabulate(table, headers=headers, tablefmt="grid", stralign="right", numalign="right"))

def tela_proventos():
    clear_screen(); title("Proventos por Período")
    print("Alguns ativos:"); 
    for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']}")
    t_id = _input("Ticker (ID) [ENTER ignora]: ").strip()
    di = _input("Data inicial [YYYY-MM-DD / ENTER ignora]: ").strip() or None
    df = _input("Data final   [YYYY-MM-DD / ENTER ignora]: ").strip() or None
    ticker_id = int(t_id) if t_id else None

    rows_all = proventos_por_periodo(ticker_id, di, df)

    # Totais do filtro
    total_val = D("0")
    count = 0
    for r in rows_all:
        val = _valor_total_row(r)
        if val is not None:
            total_val += val
            count += 1

    pager = Paginator(len(rows_all))
    while True:
        clear_screen(); title("Proventos por Período"); divider()
        print(f"Período: {di or 'N/D'} a {df or 'N/D'}  |  Linhas: {len(rows_all)}")
        start, end = pager.range()
        _render_page(rows_all[start:end])

        # Totais consolidados (do filtro completo)
        print()
        print(tabulate(
            [[count, fmt_money(total_val)]],
            headers=["# Lançamentos com Valor", "Total (R$)"],
            tablefmt="grid", stralign="right", numalign="right"
        ))
        print(f"\nPág {pager.page}/{pager.pages} — [N] Próx  [P] Ant  [G] Ir pág  [CSV] Exportar  [Q] Voltar")
        ch = input("> ").strip().lower()
        if ch in ("q","voltar"): break
        elif ch=="n": pager.next()
        elif ch=="p": pager.prev()
        elif ch=="g":
            try: pager.goto(int(input("Pág: ")))
            except: pass
        elif ch=="csv":
            path = _input("Caminho CSV: ").strip() or "./proventos.csv"
            import csv
            headers_csv = ["id","data_pagamento","tipo_evento","ticker","valor_total_calc","quantidade","preco_unitario","descricao"]
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(headers_csv)
                for r in rows_all:
                    val = _valor_total_row(r)
                    w.writerow([
                        r.get("id"), r.get("data_pagamento"), r.get("tipo_evento"), r.get("ticker_str"),
                        f"{val:f}" if val is not None else "",
                        r.get("quantidade"), r.get("preco_unitario"), r.get("descricao","")
                    ])
            print(f"CSV salvo em {path}."); pause()
