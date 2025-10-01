-- Migration: CVM ITR - Informações Trimestrais
-- Tabela para armazenar dados de Informações Trimestrais (ITR) da CVM
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cia_aberta_itr_bpa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj TEXT NOT NULL,
    data_referencia TEXT NOT NULL,
    versao INTEGER NOT NULL,
    razao_social TEXT NOT NULL,
    codigo_cvm TEXT NOT NULL,
    grupo TEXT NOT NULL,
    moeda TEXT NOT NULL,
    escala_moeda TEXT NOT NULL,
    data_inicio_exercicio TEXT NOT NULL,
    data_fim_exercicio TEXT NOT NULL,
    codigo_conta TEXT NOT NULL,
    descricao_conta TEXT NOT NULL,
    valor_conta TEXT NOT NULL,
    conta_fixa INTEGER NOT NULL ,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (cnpj, data_referencia, versao, grupo, codigo_conta)
);



CREATE TABLE IF NOT EXISTS cia_aberta_itr_bpp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj TEXT NOT NULL,
    data_referencia TEXT NOT NULL,
    versao INTEGER NOT NULL,
    razao_social TEXT NOT NULL,
    codigo_cvm TEXT NOT NULL,
    grupo TEXT NOT NULL,
    moeda TEXT NOT NULL,
    escala_moeda TEXT NOT NULL,
    data_inicio_exercicio TEXT NOT NULL,
    data_fim_exercicio TEXT NOT NULL,
    codigo_conta TEXT NOT NULL,
    descricao_conta TEXT NOT NULL,
    valor_conta TEXT NOT NULL,
    conta_fixa INTEGER NOT NULL ,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (cnpj, data_referencia, versao, grupo, codigo_conta)
);


CREATE TABLE IF NOT EXISTS cia_aberta_itr_dre (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj TEXT NOT NULL,
    data_referencia TEXT NOT NULL,
    versao INTEGER NOT NULL,
    razao_social TEXT NOT NULL,
    codigo_cvm TEXT NOT NULL,
    grupo TEXT NOT NULL,
    moeda TEXT NOT NULL,
    escala_moeda TEXT NOT NULL,
    data_inicio_exercicio TEXT NOT NULL,
    data_fim_exercicio TEXT NOT NULL,
    codigo_conta TEXT NOT NULL,
    descricao_conta TEXT NOT NULL,
    valor_conta TEXT NOT NULL,
    conta_fixa INTEGER NOT NULL ,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (cnpj, data_referencia, versao, grupo, codigo_conta)
);



CREATE TABLE IF NOT EXISTS cia_aberta_itr_composicao_capital (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj TEXT NOT NULL,
    data_referencia TEXT NOT NULL,
    versao INTEGER NOT NULL,
    razao_social TEXT NOT NULL,
    qtde_acao_ordinaria TEXT NOT NULL DEFAULT '0',
    qtde_acao_preferencial TEXT NOT NULL DEFAULT '0',
    qtde_acao_total TEXT NOT NULL DEFAULT '0',
    qtde_acao_ordinaria_tesouraria TEXT NOT NULL DEFAULT '0',
    qtde_acao_preferencial_tesouraria TEXT NOT NULL DEFAULT '0',
    qtde_acao_total_tesouraria TEXT NOT NULL DEFAULT '0',
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (cnpj, data_referencia, versao)
);

-- Tabela de controle dos metadados dos ITRs importados do CSV
CREATE TABLE IF NOT EXISTS cia_aberta_itr_controle (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	cnpj TEXT NOT NULL,
	data_referencia TEXT NOT NULL,
	versao INTEGER NOT NULL,
	razao_social TEXT NOT NULL,
	codigo_cvm TEXT NOT NULL,
	categoria_documento TEXT NOT NULL,
	codigo_documento TEXT NOT NULL,
	data_recebimento TEXT NOT NULL,
	link_documento TEXT NOT NULL,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
	UNIQUE (cnpj, data_referencia, versao, codigo_documento)
);