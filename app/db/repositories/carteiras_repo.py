from typing import Optional, List


class CarteirasRepo:
    def __init__(self, conn=None):
        self.conn = conn

    def contar(self, texto: str = "", apenas_ativas: bool = True) -> int:
        
        where, params = "WHERE 1=1 ", []
        if texto:
            txt = f"%{texto.strip().lower()}%"
            where += "AND (lower(nome) LIKE ? OR lower(coalesce(descricao,'')) LIKE ?) "
            params += [txt, txt]
        if apenas_ativas:
            where += "AND ativo = 1 "
        total = self.conn.execute(f"SELECT COUNT(*) c FROM carteiras {where};", params).fetchone()["c"]
        return int(total)

    def listar(self, texto: str = "", apenas_ativas: bool = True, offset: int = 0, limit: int = 20) -> List[dict]:
        where, params = "WHERE 1=1 ", []
        if texto:
            txt = f"%{texto.strip().lower()}%"
            where += "AND (lower(nome) LIKE ? OR lower(coalesce(descricao,'')) LIKE ?) "
            params += [txt, txt]
        if apenas_ativas:
            where += "AND ativo = 1 "
        rows = self.conn.execute(
            f"""SELECT id, nome, descricao, ativo, criado_em, atualizado_em
                FROM carteiras {where} ORDER BY nome ASC LIMIT ? OFFSET ?;""",
            (*params, limit, offset)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_by_nome(self, nome: str) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM carteiras WHERE lower(nome)=lower(?);", (nome.strip(),)).fetchone()
        return dict(row) if row else None

    def get_by_id(self, cid: int) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM carteiras WHERE id=?;", (cid,)).fetchone()
        return dict(row) if row else None

    def criar(self, nome: str, descricao: str = "") -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO carteiras(nome, descricao, ativo) VALUES (?, ?, 1);", (nome.strip(), descricao.strip()))
        new_id = cur.lastrowid
        return new_id

    def editar(self, cid: int, nome: str, descricao: str = "") -> None:        
        self.conn.execute("UPDATE carteiras SET nome=?, descricao=? WHERE id=?;", (nome.strip(), descricao.strip(), cid))


    def inativar(self, cid: int) -> None:
        self.conn.execute("UPDATE carteiras SET ativo=0, atualizado_em=datetime('now') WHERE id=?;", (cid,))

    def reativar(self, cid: int) -> None:
        self.conn.execute("UPDATE carteiras SET ativo=1, atualizado_em=datetime('now') WHERE id=?;", (cid,))

