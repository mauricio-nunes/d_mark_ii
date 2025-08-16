from colorama import Fore, Style
from ..widgets import title, divider, pause, confirm
from ..prompts import prompt_menu_choice
from ...core.utils import clear_screen
from ...db.repositories import config_repo  # assumindo que você tem um config_repo simples
from ...services.importacao_service import (
    preview_proventos, importar_proventos,
    preview_fechamentos, importar_fechamentos,
    CFG_PROV_MAP, CFG_FECH_MAP, ValidationError
)
from ...core.xlsx import list_sheets

def _input(t): return input(Fore.WHITE + t + Style.RESET_ALL)

DEFAULT_MAP_PROV = {"ticker":"Ticker","tipo":"Tipo","data_pagamento":"DataPagamento",
                    "descricao":"Descricao","quantidade":"Quantidade","preco_unitario":"PrecoUnitario","valor_total":"ValorTotal"}

DEFAULT_MAP_FECH = {"ticker":"Ticker","preco_fechamento":"PrecoFechamento","quantidade":"Qtde"}

def _get_map(key:str, default:dict) -> dict:
    import json
    val = config_repo.get_value(key)
    if not val:
        config_repo.set_value(key, json.dumps(default))
        return default
    try:
        return json.loads(val)
    except Exception:
        return default

def _set_map(key:str, m:dict):
    import json
    config_repo.set_value(key, json.dumps(m))

def _editar_mapeamento(key:str, default:dict):
    clear_screen(); title("Configurar Mapeamento de Colunas")
    m = _get_map(key, default)
    for k,v in m.items():
        nv = _input(f"{k} [{v}]: ").strip() or v
        m[k] = nv
    _set_map(key, m)
    print("Mapeamento salvo."); pause()

def _escolher_aba(path: str) -> str | None:
    sheets = list_sheets(path)
    print("Abas encontradas:")
    for i, s in enumerate(sheets, start=1): print(f"  {i}. {s}")
    ch = _input("Escolha a aba (número): ").strip()
    try:
        idx = int(ch)-1
        return sheets[idx]
    except:
        return None

def _preview(rows: list[dict], cols: list[str]):
    print(Fore.CYAN + "Pré-visualização (até 50 linhas):" + Style.RESET_ALL)
    print("-"*100)
    for r in rows[:50]:
        print(" | ".join(f"{c}={r.get(c)}" for c in cols))
    print("-"*100)

def importar_proventos_flow():
    clear_screen(); title("Importar Proventos (XLSX)")
    path = _input("Caminho do arquivo XLSX: ").strip()
    sheet = _escolher_aba(path)
    if not sheet: print("Aba inválida."); pause(); return
    mapa = _get_map(CFG_PROV_MAP, DEFAULT_MAP_PROV)
    prev = preview_proventos(path, sheet, mapa)
    _preview(prev, ["ticker","tipo_evento","data_pagamento","descricao","quantidade","preco_unitario","valor_total"])
    if confirm("Confirmar importação? (S/N) "):
        ok, skip = importar_proventos(path, sheet, mapa)
        print(f"Importação concluída. OK={ok}, Ignorados={skip}")
    pause()

def importar_fechamentos_flow():
    clear_screen(); title("Importar Fechamento Mensal (XLSX)")
    path = _input("Caminho do arquivo XLSX: ").strip()
    sheet = _escolher_aba(path)
    if not sheet: print("Aba inválida."); pause(); return
    mapa = _get_map(CFG_FECH_MAP, DEFAULT_MAP_FECH)
    try:
        prev = preview_fechamentos(path, sheet, mapa)
    except ValidationError as e:
        print(f"Erro: {e}"); pause(); return
    _preview(prev, ["ticker","data_ref","preco_fechamento","quantidade"])
    if confirm("Confirmar importação? (S/N) "):
        ok, skip = importar_fechamentos(path, sheet, mapa)
        print(f"Importação concluída. OK={ok}, Ignorados={skip}")
    pause()

def configurar_mapeamento_flow():
    while True:
        clear_screen(); title("Mapeamento de Colunas")
        print("1. Proventos")
        print("2. Fechamento Mensal")
        print("3. Voltar")
        ch = _input("> ").strip()
        if ch == "1": _editar_mapeamento(CFG_PROV_MAP, DEFAULT_MAP_PROV)
        elif ch == "2": _editar_mapeamento(CFG_FECH_MAP, DEFAULT_MAP_FECH)
        else: break

def importacao_loop():
    while True:
        clear_screen(); title("Importação (XLSX)")
        print("1. Proventos (XLSX)")
        print("2. Fechamento Mensal (XLSX)")
        print("3. Configurar Mapeamento de Colunas")
        print("4. Voltar")
        ch = _input("> ").strip()
        if ch == "1": importar_proventos_flow()
        elif ch == "2": importar_fechamentos_flow()
        elif ch == "3": configurar_mapeamento_flow()
        else: break
