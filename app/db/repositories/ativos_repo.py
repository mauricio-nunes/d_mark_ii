from typing import Optional, List

class AtivosRepo:
    def __init__(self, conn=None):
        self.conn = conn

    def contar(self, texto: str = "", apenas_ativos: bool = True) -> int:

        where, params = "WHERE 1=1 ", []
        if texto:
            txt = f"%{texto.strip().lower()}%"
            # embora aqui não tenha JOIN, já deixo os aliases para consistência
            where += "AND (lower(a.ticker) LIKE ? OR lower(a.nome) LIKE ?) "
            params += [txt, txt]
        if apenas_ativos:
            where += "AND a.ativo = 1 "
        # use alias a para manter coerência
        total = self.conn.execute(f"SELECT COUNT(*) c FROM ativos a {where};", params).fetchone()["c"]
        return int(total)

    def listar(self, texto: str = "", apenas_ativos: bool = True, offset: int = 0, limit: int = 20) -> List[dict]:
        
        where, params = "WHERE 1=1 ", []
        if texto:
            txt = f"%{texto.strip().lower()}%"
            where += "AND (lower(a.ticker) LIKE ? OR lower(a.nome) LIKE ?) "
            params += [txt, txt]
        if apenas_ativos:
            where += "AND a.ativo = 1 "  # <— aqui estava sem alias

        rows = self.conn.execute(
            f"""
            SELECT a.id, a.ticker, a.nome, a.classe, a.ativo,
                e.razao_social AS empresa, e.id AS empresa_id
            FROM ativos a
            LEFT JOIN empresas e ON e.id = a.empresa_id
            {where}
            ORDER BY a.ticker ASC
            LIMIT ? OFFSET ?;
            """,
            (*params, limit, offset)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_by_ticker(self, ticker: str) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM ativos WHERE lower(ticker)=lower(?);", (ticker.strip(),)).fetchone()
        return dict(row) if row else None

    def get_by_id(self, aid: int) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM ativos WHERE id=?;", (aid,)).fetchone()
        return dict(row) if row else None

    def criar(self, ticker: str, nome: str, classe: str, empresa_id: int | None) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO ativos(ticker, nome, classe, empresa_id, ativo) VALUES (?, ?, ?, ?, 1);",
                    (ticker.strip().upper(), nome.strip(), classe, empresa_id))
        nid = cur.lastrowid
        return nid

    def editar(self, aid: int, ticker: str, nome: str, classe: str, empresa_id: int | None) -> None:
       
        self.conn.execute("UPDATE ativos SET ticker=?, nome=?, classe=?, empresa_id=? WHERE id=?;",
                    (ticker.strip().upper(), nome.strip(), classe, empresa_id, aid))
        

    def inativar(self, aid: int) -> None:
        self.conn.execute("UPDATE ativos SET ativo=0, atualizado_em=datetime('now') WHERE id=?;", (aid,))
        

    def reativar(self, aid: int) -> None:
        self.conn.execute("UPDATE ativos SET ativo=1, atualizado_em=datetime('now') WHERE id=?;", (aid,))
