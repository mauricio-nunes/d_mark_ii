from typing import List, Dict, Any, Optional, Tuple
from openpyxl import load_workbook , Workbook
import warnings
from openpyxl.styles import Font, Alignment, PatternFill, numbers
from openpyxl.utils import get_column_letter

warnings.simplefilter("ignore", UserWarning)  # Suppress openpyxl warnings about data


def read_xlsx_rows(path: str, sheet_name: str | None = None) -> List[Dict[str, Any]]:
    wb = load_workbook(filename=path, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = [str(h).strip() if h is not None else "" for h in rows[0]]
    data = []
    for r in rows[1:]:
        row_dict = {}
        for k, v in zip(header, r):
            row_dict[k] = v
        data.append(row_dict)
    return data


def list_sheets(path: str) -> list[str]:
    wb = load_workbook(filename=path, read_only=True)
    return wb.sheetnames


def _collect_date_cols(rows: List[Dict[str, Any]], key_col: str = "codigo_conta") -> List[str]:
    dates = set()
    for r in rows or []:
        for k in r.keys():
            if k != key_col:
                dates.add(k)

    return sorted(dates, reverse=False)

def _coerce_number(val: Any) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except Exception:
        return None

def _infer_single_date_col(rows_extra: List[Dict[str, Any]], key_col: str = "codigo_conta") -> Optional[str]:
    """
    Descobre o rótulo da coluna 'extra' (TTM/Última data) olhando as chaves das linhas extra.
    Se houver múltiplas datas nos 'extras', escolhe a mais recente.
    """
    dates = set()
    for r in rows_extra or []:
        for k in r.keys():
            if k != key_col:
                dates.add(k)
    if not dates:
        return None
    # pega a mais recente
    return sorted(dates, reverse=True)[0]

def _index_rows_by_key(rows: List[Dict[str, Any]], key_col: str = "codigo_conta") -> Dict[str, Dict[str, Any]]:
    """
    Produz um índice: codigo_conta -> dict com as colunas de data/valores (último vence se repetido).
    """
    idx: Dict[str, Dict[str, Any]] = {}
    for r in rows or []:
        key = r.get(key_col)
        if key is None:
            continue
        d = idx.setdefault(key, {})
        for k, v in r.items():
            if k == key_col:
                continue
            d[k] = v
    return idx

def _merge_5y_plus_extra(
    rows_5y: List[Dict[str, Any]],
    rows_extra: List[Dict[str, Any]],
    key_col: str = "codigo_conta",
    fill_missing_with_zero: bool = True
) -> Tuple[List[str], List[List[Optional[float]]]]:
    """
    Retorna (header, data_rows) combinando:
      - colunas do 5y (datas desc)
      - + 1 coluna 'extra' (rótulo = data inferida em rows_extra) ao fim
    """
    base_dates = _collect_date_cols(rows_5y, key_col=key_col)
    extra_col = _infer_single_date_col(rows_extra, key_col=key_col)

    # Índices por conta
    idx_5y = _index_rows_by_key(rows_5y, key_col=key_col)
    idx_extra = _index_rows_by_key(rows_extra, key_col=key_col)

    # universo de contas
    contas = sorted(set(idx_5y.keys()) | set(idx_extra.keys()))

    # Header
    header = [key_col] + base_dates
    if extra_col:
        header.append(extra_col)

    # Linhas
    data_rows: List[List[Optional[float]]] = []
    for conta in contas:
        row: List[Optional[float]] = [conta]
        # valores das datas 5y
        base_vals = idx_5y.get(conta, {})
        for d in base_dates:
            val = base_vals.get(d, None)
            if val is None and fill_missing_with_zero:
                val = 0.0
            row.append(_coerce_number(val))
        # valor extra (TTM/Última data)
        if extra_col:
            extra_val = idx_extra.get(conta, {}).get(extra_col, None)
            if extra_val is None and fill_missing_with_zero:
                extra_val = 0.0
            row.append(_coerce_number(extra_val))
        data_rows.append(row)

    return header, data_rows

def _write_table(ws, title: str, header: List[str], rows: List[List[Optional[float]]], start_row: int) -> int:
    """
    Escreve (título + tabela) e retorna a próxima linha livre.
    """
    # título
    ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=max(1, len(header)))
    c = ws.cell(row=start_row, column=1, value=title)
    c.font = Font(bold=True, size=12)
    c.alignment = Alignment(horizontal="left", vertical="center")
    c.fill = PatternFill("solid", fgColor="F2F2F2")
    r = start_row + 1

    # cabeçalho
    for j, h in enumerate(header, start=1):
        ch = ws.cell(row=r, column=j, value=h)
        ch.font = Font(bold=True)
        ch.alignment = Alignment(horizontal="center")
        ch.fill = PatternFill("solid", fgColor="E8F0FE")

    # dados
    for row in rows:
        r += 1
        for j, v in enumerate(row, start=1):
            ws.cell(row=r, column=j, value=v)

    # formato numérico nas colunas de data (2..N)
    for col_idx in range(2, len(header) + 1):
        for row_idx in range(start_row + 2, r + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            if isinstance(cell.value, (int, float)):
                cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

    # congelar topo se ainda não houver
    ws.freeze_panes = ws.freeze_panes or "A2"

    # linha em branco
    r += 2
    return r

def _autosize(ws):
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            txt = "" if cell.value is None else str(cell.value)
            if len(txt) > max_len:
                max_len = len(txt)
        ws.column_dimensions[letter].width = min(max(12, max_len + 2), 50)

def build_excel_balanco_dre_side_by_side(
    dre_5y: List[Dict[str, Any]],
    dre_12m: List[Dict[str, Any]],
    bpp_5y: List[Dict[str, Any]],
    bpa_5y: List[Dict[str, Any]],
    bpa: List[Dict[str, Any]],
    bpp: List[Dict[str, Any]],
    xlsx_path: str = "balanco_dre.xlsx",
    sheet_balanco: str = "Balanço Patrimonial",
    sheet_dre: str = "DRE",
    fill_missing_with_zero: bool = True
) -> str:
    """
    DRE:       [dre_5y] + [dre_12m como última coluna]
    Balanço:   BPA: [bpa_5y] + [bpa como última coluna]
               BPP: [bpp_5y] + [bpp como última coluna]  (em um bloco abaixo do BPA)
    """
    wb = Workbook()

    # --- DRE (uma tabela: 5y + TTM à direita) ---
    ws_dre = wb.active
    ws_dre.title = sheet_dre
    dre_header, dre_rows = _merge_5y_plus_extra(
        rows_5y=dre_5y,
        rows_extra=dre_12m,
        key_col="codigo_conta",
        fill_missing_with_zero=fill_missing_with_zero
    )
    r = 1
    r = _write_table(ws_dre, "DRE (5 anos + Últimos 12 meses)", dre_header, dre_rows, r)
    _autosize(ws_dre)

    # --- Balanço Patrimonial ---
    ws_bal = wb.create_sheet(title=sheet_balanco)
    # BPA bloco
    bpa_header, bpa_rows = _merge_5y_plus_extra(
        rows_5y=bpa_5y,
        rows_extra=bpa,
        key_col="codigo_conta",
        fill_missing_with_zero=fill_missing_with_zero
    )
    rb = 1
    rb = _write_table(ws_bal, "BPA - Ativo (5 anos + Última data)", bpa_header, bpa_rows, rb)

    # BPP bloco (abaixo, como “union”)
    bpp_header, bpp_rows = _merge_5y_plus_extra(
        rows_5y=bpp_5y,
        rows_extra=bpp,
        key_col="codigo_conta",
        fill_missing_with_zero=fill_missing_with_zero
    )
    rb = _write_table(ws_bal, "BPP - Passivo (5 anos + Última data)", bpp_header, bpp_rows, rb)

    _autosize(ws_bal)

    wb.save(xlsx_path)
    return xlsx_path

