PRAGMA foreign_keys = ON;


-------------- USUARIOS ------------
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash BLOB NOT NULL,
  tentativas INTEGER NOT NULL DEFAULT 0,
  bloqueado INTEGER NOT NULL DEFAULT 0, -- 0=false, 1=true
  must_change_password INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);


-------------- EMPRESAS ------------
CREATE TABLE IF NOT EXISTS empresas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cnpj TEXT UNIQUE NOT NULL, -- somente dígitos
  razao_social TEXT NOT NULL,
  setor_atividade TEXT,
  tipo_empresa TEXT NOT NULL, -- 'Fundo' | 'CiaAberta'
  codigo_cvm INT, -- código CVM
  situacao_emissor TEXT,
  controle_acionario TEXT,
  data_constituicao TEXT, -- ISO date
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);


-------------- ATIVOS  ------------

CREATE TABLE IF NOT EXISTS ativos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT UNIQUE NOT NULL,
  nome TEXT NOT NULL,
  classe TEXT NOT NULL, -- 'Acao' | 'FII' | 'Tesouro' | 'BDR' | 'ETF'
  empresa_id INTEGER,
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

-------------- CORRETORAS  ------------
CREATE TABLE IF NOT EXISTS corretoras (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT UNIQUE NOT NULL,
  descricao TEXT NOT NULL,
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);



-------------- PROVENTOS ------------
CREATE TABLE IF NOT EXISTS proventos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data_referencia TEXT NOT NULL,  -- YYYY-MM-DD (último dia do mês)
  ativo TEXT NOT NULL,
  ativo_id INTEGER NOT NULL,
  corretora_id INTEGER NOT NULL,
  descricao TEXT,
  data_pagamento TEXT NOT NULL, -- ISO date
  tipo_evento TEXT NOT NULL, -- DIVIDENDO|JCP|RENDIMENTO FII|AMORTIZACAO|OUTROS
  instituicao TEXT NOT NULL,
  quantidade TEXT,       -- opcional
  preco_unitario TEXT,   -- opcional
  valor_total TEXT,      -- opcional
  observacoes TEXT,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (ativo_id) REFERENCES ativos(id),
  FOREIGN KEY (corretora_id) REFERENCES corretoras(id)
);




CREATE TABLE IF NOT EXISTS eventos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tipo TEXT NOT NULL, --- corretora|ativo
  entidade_id INTEGER NOT NULL, -- id da corretora ou do ativo
  evento TEXT NOT NULL, 
  nome TEXT, -- nome da corretora ou do ativo
  ticker_antigo TEXT,
  ticker_novo TEXT,
  data_ex TEXT NOT NULL, -- ISO date
  observacoes TEXT,
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-------------- CARTEIRAS  ------------
CREATE TABLE IF NOT EXISTS carteiras (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT UNIQUE NOT NULL,
  descricao TEXT,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now')),
  ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS carteiras_ativos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  carteira_id INTEGER NOT NULL,
  ativo_id INTEGER NOT NULL,
  percentual_requerido TEXT NOT NULL DEFAULT '100.00', -- Decimal string (2 casas)
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (carteira_id) REFERENCES carteiras(id),
  FOREIGN KEY (ativo_id) REFERENCES ativos(id)
);

---------------- POSICAO CONSOLIDADA B3 ------------
  CREATE TABLE IF NOT EXISTS posicao_consolidada (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	data_referencia TEXT NOT NULL,                    -- YYYY-MM-DD (último dia do mês)
	produto TEXT NOT NULL,                             -- Nome do produto
	instituicao TEXT NOT NULL,                        -- Nome da corretora
	conta TEXT NOT NULL,                              -- Número da conta
	ativo_id INTEGER NOT NULL,
  corretora_id INTEGER NOT NULL,
	codigo_negociacao TEXT NOT NULL,                  -- Ticker/código de negociação
	cnpj_empresa TEXT NOT NULL,                       -- CNPJ da empresa emissora
	codigo_isin TEXT NOT NULL,                        -- Código ISIN
	tipo_indexador TEXT NOT NULL,
	adm_escriturador_emissor TEXT NOT NULL,          -- Nome do administrador/escriturador
	quantidade TEXT NOT NULL DEFAULT '0',            -- Decimal string
	quantidade_disponivel TEXT NOT NULL DEFAULT '0',  -- Decimal string
	quantidade_indisponivel TEXT NOT NULL DEFAULT '0', -- Decimal string
	motivo TEXT,
	preco_fechamento TEXT NOT NULL,
	data_vencimento TEXT,
	valor_aplicado TEXT NOT NULL DEFAULT '0',            -- Decimal string
	valor_liquido TEXT NOT NULL DEFAULT '0',            -- Decimal string
	valor_atualizado TEXT NOT NULL DEFAULT '0',       -- Decimal string
	tipo_ativo TEXT NOT NULL,
	tipo_regime TEXT,
	data_emissao TEXT,
	contraparte TEXT,
	preco_atualizado_mtm TEXT NOT NULL DEFAULT '0',  -- Decimal string
	valor_atualizado_mtm TEXT NOT NULL DEFAULT '0',  -- Decimal string
	criado_em TEXT NOT NULL DEFAULT (datetime('now')),
	atualizado_em TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (ativo_id) REFERENCES ativos(id),
  FOREIGN KEY (corretora_id) REFERENCES corretoras(id)
);

-- Índice único para evitar duplicações por competência/conta/ticker
CREATE UNIQUE INDEX IF NOT EXISTS idx_b3_posicao_unique 
	ON posicao_consolidada(data_referencia, instituicao, codigo_isin);

-------------- MOVIMENTAÇÃO B3 ------------
CREATE TABLE IF NOT EXISTS movimentacao (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hash_linha TEXT UNIQUE NOT NULL,  -- SHA-256 para idempotência
  entrada_saida TEXT NOT NULL,      -- normalizada (minúsculas sem acentos credito / debito)
  data TEXT NOT NULL,               -- YYYY-MM-DD
  movimentacao TEXT NOT NULL,       -- normalizada (minúsculas sem acentos)
  produto TEXT NOT NULL,    -- descrição do ativo
  codigo TEXT NOT NULL,             -- código do ativo
  codigo_negociacao TEXT,           -- código de negociação (pode ser NULL)
  ativo_id INTEGER NOT NULL,
  instituicao TEXT NOT NULL,        -- nome da instituição financeira
  quantidade TEXT NOT NULL,         -- Decimal string positivo
  preco_unitario TEXT NOT NULL,     -- Decimal string com 3 casas decimais
  valor_total_operacao TEXT,        -- Decimal string ou NULL para subscrições sem valor
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (ativo_id) REFERENCES ativos(id)
);

-- Índice único para garantir idempotência
CREATE UNIQUE INDEX IF NOT EXISTS idx_movimentacao_hash ON movimentacao(hash_linha);

-- Índices para consultas comuns
CREATE INDEX IF NOT EXISTS idx_movimentacao_data ON movimentacao(data);
CREATE INDEX IF NOT EXISTS idx_movimentacao_codigo ON movimentacao(codigo);


