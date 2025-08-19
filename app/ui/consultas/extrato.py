from decimal import Decimal
from tabulate import tabulate
from colorama import Fore, Style
from ..widgets import title, divider, pause
from ...core.utils import clear_screen
from ...core.pagination import Paginator
from ...core.decimal_ctx import money, qty, D
from ...db.repositories import ativos_repo, carteiras_repo
from ...services.consultas_service import extrato

def _input(t): 
    return input(Fore.WHITE + t + Style.RESET_ALL)

def _ticker_disp(r: dict) -> str:
    # tenta usar o display com mapping; fallback para ticker_str
    return r.get("ticker_disp") or r.get("ticker_str") or str(r.get("ticker"))

def _cashflow(r: dict) -> Decimal | None:
    """
    Fluxo de caixa por linha:
    - COMPRA/SUBSCRICAO:    -(q*pu + taxas)
    - VENDA:                +(q*pu - taxas)
    - TRANSFERENCIA/BONIFICACAO/AMORTIZACAO/EVENTO: 0 (não consideramos caixa aqui)
    Retorna Decimal (pode ser 0) ou None se não der para calcular.
    """
    tipo = (r.get("tipo") or "").upper()
    q = qty(r.get("quantidade"))
    pu = money(r.get("preco_unitario"))
    tx = money(r.get("taxas"))
    if tipo in ("COMPRA", "SUBSCRICAO"):
        return -(q * pu + tx)
    if tipo == "VENDA":
        return (q * pu - tx)
    # Transferência e outros eventos não são caixa
    return D("0")

def _delta_q(r: dict) -> Decimal:
    tipo = (r.get("tipo") or "").upper()
    q = qty(r.get("quantidade"))
    if tipo in ("COMPRA", "SUBSCRICAO", "BONIFICACAO"):
        return q
    if tipo in ("VENDA",):
        return -q
    # TRANSFERENCIA e demais: zero (não altera posição líquida da carteira? No nosso modelo, sim, já há saída/entrada separadas)
    return D("0")

def _fmt_money_color(v: Decimal | None) -> str:
    from ...core.formatters import fmt_money
    if v is None:
        return "N/D"
    s = fmt_money(v)
    if v > 0:
        return Fore.GREEN + s + Style.RESET_ALL
    if v < 0:
        return Fore.RED + s + Style.RESET_ALL
    return s

def _fmt_qty(v: Decimal | None) -> str:
    from ...core.formatters import fmt_qty
    return fmt_qty(v)

def _render_page(rows):
    headers = ["ID", "Data", "Tipo", "Ticker", "Carteira", "Qtd", "PU", "Taxas", "Qtd(Aj)", "Fluxo Caixa"]
    table = []
    for r in rows:
        cf = _cashflow(r)
        table.append([
            r.get("id"),
            r.get("data"),
            r.get("tipo"),
            _ticker_disp(r),
            r.get("carteira_str"),
            _fmt_qty(qty(r.get("quantidade"))),
            _fmt_money_color(money(r.get("preco_unitario")) if r.get("preco_unitario") not in (None, "") else D("0")),
            _fmt_money_color(money(r.get("taxas")) if r.get("taxas") not in (None, "") else D("0")),
            _fmt_qty(qty(r.get("qtd_ajustada")) if r.get("qtd_ajustada") else None),
            _fmt_money_color(cf),
        ])
    print(tabulate(table, headers=headers, tablefmt="grid", stralign="right", numalign="right"))

def tela_extrato():
    clear_screen(); title("Extrato de Transações")
    print("Alguns ativos:"); 
    for a in ativos_repo.list("", True, 0, 10): print(f"  {a['id']:>3} - {a['ticker']}")
    print("Algumas carteiras:"); 
    for c in carteiras_repo.list("", True, 0, 10): print(f"  {c['id']:>3} - {c['nome']}")

    t_id = _input("Ticker (ID) [ENTER ignora]: ").strip()
    c_id = _input("Carteira (ID) [ENTER ignora]: ").strip()
    di = _input("Data inicial [YYYY-MM-DD / ENTER ignora]: ").strip() or None
    df = _input("Data final   [YYYY-MM-DD / ENTER ignora]: ").strip() or None
    ticker_id = int(t_id) if t_id else None
    carteira_id = int(c_id) if c_id else None

    rows_all = extrato(carteira_id, ticker_id, di, df, incluir_ajuste=True)

    # Totais do filtro (sobre todas as linhas)
    total_q = D("0")
    total_cf = D("0")
    for r in rows_all:
        total_q += _delta_q(r)
        cf = _cashflow(r)
        if cf is not None:
            total_cf += cf

    pager = Paginator(len(rows_all))
    while True:
        clear_screen(); title("Extrato de Transações"); divider()
        print(f"Período: {di or 'N/D'} a {df or 'N/D'}  |  Linhas: {len(rows_all)}")
        start, end = pager.range()
        _render_page(rows_all[start:end])

        # Totais consolidados (do filtro completo)
        from ...core.formatters import fmt_money, fmt_qty
        print()
        print(tabulate(
            [[fmt_qty(total_q), _fmt_money_color(total_cf)]],
            headers=["Δ Quantidade (sinal)", "Fluxo Caixa Líquido"],
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
            path = _input("Caminho CSV: ").strip() or "./extrato.csv"
            import csv
            headers_csv = ["id","data","tipo","ticker","carteira","quantidade","preco_unitario","taxas","qtd_ajustada","fluxo_caixa"]
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(headers_csv)
                for r in rows_all:
                    cf = _cashflow(r)
                    w.writerow([
                        r.get("id"), r.get("data"), r.get("tipo"), _ticker_disp(r), r.get("carteira_str"),
                        r.get("quantidade"), r.get("preco_unitario"), r.get("taxas"),
                        r.get("qtd_ajustada"), f"{cf:f}" if cf is not None else ""
                    ])
            print(f"CSV salvo em {path}."); pause()
