from typing import TypedDict, Optional
from ..db.repositories import config_repo

# chaves
CFG_FIGLET_FONT = "ui.figlet_font"
CFG_THEME = "ui.theme"             # "dark"|"light"
CFG_PAGE_SIZE = "ui.page_size"     # inteiro
CFG_DB_PATH = "db_path"            # opcional

class Prefs(TypedDict, total=False):
    figlet_font: str
    theme: str
    page_size: int
    db_path: str

def get_prefs() -> Prefs:
    def _g(k, d=None):
        v = config_repo.get_value(k)
        return v if v is not None else d
    pf: Prefs = {}
    ff = _g(CFG_FIGLET_FONT, "ansi_shadow")
    th = _g(CFG_THEME, "dark")
    ps = _g(CFG_PAGE_SIZE, "20")
    pf["figlet_font"] = ff
    pf["theme"] = th
    try:
        pf["page_size"] = int(ps)
    except Exception:
        pf["page_size"] = 20
    dbp = _g(CFG_DB_PATH, None)
    if dbp: pf["db_path"] = dbp
    return pf

def set_prefs(p: Prefs) -> None:
    if "figlet_font" in p and p["figlet_font"]:
        config_repo.set_value(CFG_FIGLET_FONT, p["figlet_font"])
    if "theme" in p and p["theme"]:
        config_repo.set_value(CFG_THEME, p["theme"])
    if "page_size" in p and p["page_size"]:
        config_repo.set_value(CFG_PAGE_SIZE, str(p["page_size"]))
    if "db_path" in p and p["db_path"]:
        config_repo.set_value(CFG_DB_PATH, p["db_path"])
