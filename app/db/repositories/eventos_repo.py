from typing import List, Optional


class EventosRepo:
    def __init__(self, conn=None):
        self.conn = conn

    def criar(self, data: dict) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO eventos(tipo,entidade_id,evento,nome, ticker_antigo, ticker_novo, data_ex, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
            (
                data["tipo"],
                data.get("entidade_id"),
                data.get("evento"),
                data.get("nome"),
                data.get("ticker_antigo"),
                data.get("ticker_novo"),
                data["data_ex"],
                data.get("observacoes", ""),
            ),
        )

        nid = cur.lastrowid
        return nid

    def update(self, eid: int, data: dict) -> None:

        self.conn.execute(
            """
            UPDATE eventos SET tipo=?, ticker_antigo=?, ticker_novo=?, data_ex=?, num=?, den=?, observacoes=?
            WHERE id=?;
        """,
            (
                data["tipo"],
                data.get("ticker_antigo"),
                data.get("ticker_novo"),
                data["data_ex"],
                data.get("num"),
                data.get("den"),
                data.get("observacoes", ""),
                eid,
            ),
        )

    def soft_delete(self, eid: int) -> None:
        self.conn.execute("UPDATE eventos SET ativo=0 WHERE id=?;", (eid,))

    def get_by_id(self, eid: int) -> Optional[dict]:
        r = self.conn.execute("SELECT * FROM eventos WHERE id=?;", (eid,)).fetchone()
        return dict(r) if r else None

    def list(
        self,
        ticker_id: int | None = None,
        tipo: str | None = None,
        data_ini: str | None = None,
        data_fim: str | None = None,
        offset: int = 0,
        limit: int = 50,
        apenas_ativos: bool = True,
    ) -> List[dict]:

        where, p = ["1=1"], []
        if apenas_ativos:
            where.append("e.ativo=1")
        if ticker_id:
            where.append("(e.ticker_antigo=? OR e.ticker_novo=?)")
            p += [ticker_id, ticker_id]
        if tipo:
            where.append("e.tipo=?")
            p.append(tipo)
        if data_ini:
            where.append("e.data_ex>=?")
            p.append(data_ini)
        if data_fim:
            where.append("e.data_ex<=?")
            p.append(data_fim)
        rows = self.conn.execute(
            f"""
            SELECT e.*,
                a1.ticker AS ticker_antigo_str, a2.ticker AS ticker_novo_str
            FROM eventos e
            LEFT JOIN ativos a1 ON a1.id = e.ticker_antigo
            LEFT JOIN ativos a2 ON a2.id = e.ticker_novo
            WHERE {' AND '.join(where)}
            ORDER BY e.data_ex ASC, e.id ASC
            LIMIT ? OFFSET ?;
        """,
            (*p, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def listar_eventos_por_tipo(self, tipo: str) -> List[dict]:
        rows = self.conn.execute(
            """
            SELECT * FROM eventos
            WHERE tipo=? AND ativo=1 
            ORDER BY data_ex ASC, id ASC;
        """,
            (tipo,),
        ).fetchall()
        return [dict(r) for r in rows]