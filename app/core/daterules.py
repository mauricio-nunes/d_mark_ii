import re
from datetime import date, timedelta

def parse_year_month_from_sheet(sheet_name: str) -> tuple[int,int] | None:
    """
    Tenta extrair AAAA-MM, AAAAMM, AAAA_MM, 'Jul/2024', '2024 Jul' etc.
    """
    s = sheet_name.strip()
    # 1) AAAA-MM ou AAAA_MM
    m = re.search(r'(\d{4})[ _\-\/](\d{1,2})', s)
    if m:
        y = int(m.group(1)); mm = int(m.group(2))
        if 1 <= mm <= 12: return (y, mm)
    # 2) AAAAMM
    m = re.search(r'(\d{6})', s)
    if m:
        n = int(m.group(1)); y = n // 100; mm = n % 100
        if 1 <= mm <= 12: return (y, mm)
    # 3) Nome do mês
    meses = {
        'jan':1,'fev':2,'mar':3,'abr':4,'mai':5,'jun':6,
        'jul':7,'ago':8,'set':9,'out':10,'nov':11,'dez':12
    }
    m = re.search(r'(?i)(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[^\d]*([12]\d{3})', s)
    if m:
        mm = meses[m.group(1).lower()]; y = int(m.group(2))
        return (y, mm)
    return None

def last_business_day(year: int, month: int) -> str:
    """
    Último dia útil do mês (sem feriados): retorna YYYY-MM-DD
    """
    if month == 12:
        d = date(year+1,1,1) - timedelta(days=1)
    else:
        d = date(year, month+1,1) - timedelta(days=1)
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d -= timedelta(days=1)
    return d.strftime("%Y-%m-%d")
