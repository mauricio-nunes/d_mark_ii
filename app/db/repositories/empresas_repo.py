from typing import Optional, List
from ..connection import get_conn

def count(texto: str = "", apenas_ativas: bool = True) -> int:
    conn = get_conn()
    where, params = "WHERE 1=1 ", []
    if texto:
        txt = f"%{texto.strip().lower()}%"
        where += "AND (lower(razao_social) LIKE ? OR cnpj LIKE ?) "
        params += [txt, f"%{texto.strip().replace('.','').replace('/','').replace('-','')}%"]
    if apenas_ativas:
        where += "AND ativo = 1 "
    total = conn.execute(f"SELECT COUNT(*) c FROM empresas {where};", params).fetchone()["c"]
    conn.close(); return int(total)

def list(texto: str = "", apenas_ativas: bool = True, offset: int = 0, limit: int = 20) -> List[dict]:
    conn = get_conn()
    where, params = "WHERE 1=1 ", []
    if texto:
        txt = f"%{texto.strip().lower()}%"
        where += "AND (lower(razao_social) LIKE ? OR cnpj LIKE ?) "
        params += [txt, f"%{texto.strip().replace('.','').replace('/','').replace('-','')}%"]
    if apenas_ativas:
        where += "AND ativo = 1 "
    rows = conn.execute(
        f"""SELECT id, cnpj, razao_social, tipo_empresa, setor_atividade, ativo
            FROM empresas {where} ORDER BY razao_social ASC LIMIT ? OFFSET ?;""",
        (*params, limit, offset)
    ).fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_by_cnpj(cnpj: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM empresas WHERE cnpj = ?;", (cnpj,)).fetchone()
    conn.close(); return dict(row) if row else None

def get_by_codigo_cvm(codigo_cvm: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM empresas WHERE codigo_cvm = ?;", (codigo_cvm,)).fetchone()
    conn.close(); return dict(row) if row else None

def get_by_id(eid: int) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM empresas WHERE id=?;", (eid,)).fetchone()
    conn.close(); return dict(row) if row else None

def create(**kwargs) -> int:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO empresas(cnpj, razao_social, codigo_cvm, data_constituicao, setor_atividade, situacao,
                             controle_acionario, tipo_empresa, ativo)
        VALUES (?, ?, ?,? , ?, ?, ?, ?, 1);
    """, (kwargs["cnpj"], kwargs["razao_social"], kwargs["codigo_cvm"], kwargs.get("data_constituicao"),
          kwargs.get("setor_atividade"), kwargs.get("situacao"),
          kwargs.get("controle_acionario"), kwargs["tipo_empresa"]))
    conn.commit(); nid = cur.lastrowid; conn.close(); return nid

def update(eid: int, **kwargs) -> None:
    conn = get_conn()
    conn.execute("""
        UPDATE empresas SET razao_social=?, codigo_cvm=?, data_constituicao=?, setor_atividade=?,
            situacao=?, controle_acionario=?, tipo_empresa=? WHERE id=?;
    """, (kwargs["razao_social"], kwargs["codigo_cvm"], kwargs.get("data_constituicao"),
          kwargs.get("setor_atividade"), kwargs.get("situacao"),
          kwargs.get("controle_acionario"), kwargs["tipo_empresa"], eid))
    conn.commit(); conn.close()

def inativar(eid: int) -> None:
    conn = get_conn()
    conn.execute("UPDATE empresas SET ativo=0 WHERE id=?;", (eid,))
    conn.commit(); conn.close()

def reativar(eid: int) -> None:
    conn = get_conn()
    conn.execute("UPDATE empresas SET ativo=1 WHERE id=?;", (eid,))
    conn.commit(); conn.close()

def upsert_by_cnpj(**kwargs) -> tuple[int, bool]:
    """
    Insert or update empresa by CNPJ. 
    Returns (id, was_inserted) where was_inserted is True for new records, False for updates.
    """
    conn = get_conn(); cur = conn.cursor()
    
    # Try to insert first
        
    # Get the ID and controle_id of the updated record
    row = conn.execute("SELECT id,controle_id FROM empresas WHERE cnpj=?;", (kwargs["cnpj"],)).fetchone()
    
    # Insert if not exists
    if row is None:
        cur.execute("""
            INSERT INTO empresas(cnpj, razao_social, codigo_cvm, data_constituicao, setor_atividade,
                                    situacao, controle_acionario, tipo_empresa,categoria_registro, controle_id,
                                    pais_origem, pais_custodia, situacao_emissor, dia_encerramento_fiscal,
                                    mes_encerramento_fiscal, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (kwargs["cnpj"], kwargs["razao_social"], kwargs["codigo_cvm"], kwargs.get("data_constituicao"),
                kwargs.get("setor_atividade"), kwargs.get("situacao"),
                kwargs.get("controle_acionario"), kwargs["tipo_empresa"], kwargs["categoria_registro"], kwargs.get("controle_id"),
                kwargs.get("pais_origem"), kwargs.get("pais_custodia"), kwargs.get("situacao_emissor"),
                kwargs.get("dia_encerramento_fiscal"), kwargs.get("mes_encerramento_fiscal"), kwargs.get("ativo", 1)))
        conn.commit()
        nid = cur.lastrowid
        conn.close()
        return nid, 1

    # Update if controle_id is older
    if int(row['controle_id']) < int(kwargs.get("controle_id", 0)):

        cur.execute("""
            UPDATE empresas SET razao_social=?, codigo_cvm=?, data_constituicao=?, setor_atividade=?,
                situacao=?, controle_acionario=?, tipo_empresa=?, categoria_registro=?, controle_id=?,
                pais_origem=?, pais_custodia=?, situacao_emissor=?, dia_encerramento_fiscal=?,
                mes_encerramento_fiscal=?, ativo=?, atualizado_em=datetime('now')
                WHERE cnpj=?;
            """, (kwargs["razao_social"], kwargs["codigo_cvm"], kwargs.get("data_constituicao"),
                    kwargs.get("setor_atividade"), kwargs.get("situacao"),
                    kwargs.get("controle_acionario"), kwargs["tipo_empresa"], kwargs.get("categoria_registro"),
                    kwargs.get("controle_id"), kwargs.get("pais_origem"), kwargs.get("pais_custodia"),
                    kwargs.get("situacao_emissor"), kwargs.get("dia_encerramento_fiscal"),
                    kwargs.get("mes_encerramento_fiscal"), kwargs.get("ativo", 1),
                    kwargs["cnpj"]))
        conn.commit()
        return row['id'], 2

    # If controle_id is not older, do nothing
    return 0, 0

