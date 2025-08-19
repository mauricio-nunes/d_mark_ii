from decimal import Decimal
from tabulate import tabulate
from colorama import Fore, Style
from ..widgets import title, divider, pause
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...core.decimal_ctx import money, qty, D
from ...core.formatters import fmt_money, fmt_qty
from ...db.repositories import ativos_repo
from ...services.consultas_service import historico_mensal

def _input(t): 
    return input(Fore.WHITE + t + Style.RESET_ALL)

def _valor(px, qt) -> Decimal | None:
    if px in (None, "", "N/D") or qt in (None, "", "N/D"):
        return None
    try:
        return money(px) * qty(qt)
    except Exception:
        return None

def _render_page(rows):
    headers = ["Ticker", "Data Ref", "Preço Fech.", "Qtde", "Valor"]
    table = []
    for r in rows:
        px = r.get("preco_fechamento")
        qt = r.get("quantidade")
        val = _valor(px, qt)
        table.append([
            r.get("ticker"),
            r.get("data_ref"),
            fmt_money(money(px)) if px not in (None, "", "N/D") else "N/D",
            fmt_qty(qty(qt)) if qt not in (None, "", "N/D") else "N/D",
            fmt_money(val) if val is not None else "N/D"
        ])
    print(tabulate(table, headers=headers, tablefmt="grid", stralign="right", numalign="right"))

def tela_historico():
    clear_screen(); title("Histórico Mensal (Fechamentos)")
    print("Alguns ativos:"); 
    for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']}")
    t_id = _input("Ticker (ID) [ENTER ignora]: ").strip()
    di = _input("Data inicial [YYYY-MM-DD / ENTER ignora]: ").strip() or None
    df = _input("Data final   [YYYY-MM-DD / ENTER ignora]: ").strip() or None
    ticker_id = int(t_id) if t_id else None

    rows_all = historico_mensal(ticker_id, di, df)

    # Totais do filtro
    total_val = D("0")
    count_val = 0
    for r in rows_all:
        val = _valor(r.get("preco_fechamento"), r.get("quantidade"))
        if val is not None:
            total_val += val
            count_val += 1

    pager = Paginator(len(rows_all))
    while True:
        clear_screen(); title("Histórico Mensal"); divider()
        print(f"Período: {di or 'N/D'} a {df or 'N/D'}  |  Linhas: {len(rows_all)}")
        start, end = pager.range()
        _render_page(rows_all[start:end])

        print()
        print(tabulate(
            [[count_val, fmt_money(total_val)]],
            headers=["# Meses com Valor", "Soma dos Valores (R$)"],
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
            path = _input("Caminho CSV: ").strip() or "./historico.csv"
            import csv
            headers_csv = ["ticker","data_ref","preco_fechamento","quantidade","valor_calc"]
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(headers_csv)
                for r in rows_all:
                    val = _valor(r.get("preco_fechamento"), r.get("quantidade"))
                    w.writerow([
                        r.get("ticker"), r.get("data_ref"), r.get("preco_fechamento"),
                        r.get("quantidade"), f"{val:f}" if val is not None else ""
                    ])
            print(f"CSV salvo em {path}."); pause()
