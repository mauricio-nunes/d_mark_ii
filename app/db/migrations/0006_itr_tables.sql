-- Migração 0006: Tabelas para importação e processamento de ITRs da CVM
-- EPIC: Importação e Processamento de ITRs da CVM no DMARK

-- Tabela de controle dos metadados dos ITRs importados do CSV
CREATE TABLE IF NOT EXISTS itr_controle (
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
	criado_em TEXT NOT NULL,
	processado INTEGER NOT NULL DEFAULT 0,
	UNIQUE (cnpj, data_referencia, versao, codigo_documento)
);

-- Índice para consultas por status de processamento e filtros
CREATE INDEX IF NOT EXISTS idx_itr_controle_proc 
ON itr_controle (processado, cnpj, razao_social);

-- Tabela de dados extraídos dos XMLs dos ITRs 
CREATE TABLE IF NOT EXISTS itr_dados (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	cnpj TEXT NOT NULL,
	data_referencia TEXT NOT NULL,
	versao INTEGER NOT NULL,
	razao_social TEXT NOT NULL,
	codigo_cvm TEXT NOT NULL,
	grupo_itr TEXT NOT NULL,
	moeda INTEGER NOT NULL,
	escala_moeda INTEGER NOT NULL,
	data_inicio_exercicio TEXT NOT NULL,
	data_fim_exercicio TEXT NOT NULL,
	codigo_conta TEXT NOT NULL,
	descricao_conta TEXT NOT NULL,
	valor_conta TEXT NOT NULL,
	conta_fixa INTEGER NOT NULL ,
	UNIQUE (cnpj, data_referencia, versao, grupo_itr, codigo_conta)
);

-- Índice para consultas por contexto (CNPJ, data, versão)
CREATE INDEX IF NOT EXISTS idx_itr_dados_ctx 
ON itr_dados (cnpj, data_referencia, versao);