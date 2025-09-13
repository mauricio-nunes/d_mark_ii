from typing import Optional, List


def get_by_nome(nome: str, conn=None) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM corretoras WHERE lower(nome)=lower(?);", (nome.strip(),)
    ).fetchone()
    return dict(row) if row else None


def get_by_id(cid: int, conn=None) -> Optional[dict]:
    row = conn.execute("SELECT * FROM corretoras WHERE id=?;", (cid,)).fetchone()
    return dict(row) if row else None


def criar(nome: str, descricao: str = "", conn=None) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO corretoras(nome, descricao, ativo) VALUES (?, ?, 1);",
        (nome.strip(), descricao.strip()),
    )
    new_id = cur.lastrowid
    return new_id


def update(cid: int, nome: str, descricao: str = "", conn=None) -> None:
    conn.execute(
        "UPDATE corretoras SET nome=?, descricao=?, atualizado_em=datetime('now') WHERE id=?;",
        (nome.strip(), descricao.strip(), cid),
    )


def inativar(cid: int, conn=None) -> None:
    conn.execute(
        "UPDATE corretoras SET ativo=0, atualizado_em=datetime('now') WHERE id=?;",
        (cid,),
    )


def reativar(cid: int, conn=None) -> None:
    conn.execute(
        "UPDATE corretoras SET ativo=1, atualizado_em=datetime('now') WHERE id=?;",
        (cid,),
    )


def contar_corretoras(texto: str = "", apenas_ativas: bool = True, conn=None) -> int:
    txt = f"%{texto.strip().lower()}%"
    where = "WHERE 1=1 "
    params = []
    if texto:
        where += "AND (lower(nome) LIKE ? OR lower(coalesce(descricao,'')) LIKE ?) "
        params += [txt, txt]
    if apenas_ativas:
        where += "AND ativo = 1 "
    total = conn.execute(
        f"SELECT COUNT(*) AS c FROM corretoras {where};", params
    ).fetchone()["c"]
    return int(total)


def listar_corretoras(
    texto: str = "",
    apenas_ativas: bool = True,
    offset: int = 0,
    limit: int = 20,
    conn=None,
) -> List[dict]:

    txt = f"%{texto.strip().lower()}%"
    where = "WHERE 1=1 "
    params = []
    if texto:
        where += "AND (lower(nome) LIKE ? OR lower(coalesce(descricao,'')) LIKE ?) "
        params += [txt, txt]
    if apenas_ativas:
        where += "AND ativo = 1 "
    rows = conn.execute(
        f"""SELECT id, nome, descricao, ativo, criado_em, atualizado_em
            FROM corretoras {where}
            ORDER BY nome ASC
            LIMIT ? OFFSET ?;""",
        (*params, limit, offset),
    ).fetchall()
    return [dict(r) for r in rows]
