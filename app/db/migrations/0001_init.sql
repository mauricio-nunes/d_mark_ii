PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash BLOB NOT NULL,
  tentativas INTEGER NOT NULL DEFAULT 0,
  bloqueado INTEGER NOT NULL DEFAULT 0, -- 0=false, 1=true
  must_change_password INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS corretoras (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT UNIQUE NOT NULL,
  descricao TEXT,
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  inativado_em TEXT
);

CREATE TABLE IF NOT EXISTS carteiras (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT UNIQUE NOT NULL,
  descricao TEXT,
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  inativado_em TEXT
);

CREATE TABLE IF NOT EXISTS empresas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cnpj TEXT UNIQUE NOT NULL, -- somente dígitos
  razao_social TEXT NOT NULL,
  codigo_cvm TEXT UNIQUE NOT NULL,
  data_constituicao TEXT, -- ISO date
  setor_atividade TEXT,
  situacao TEXT,
  controle_acionario TEXT,
  tipo_empresa TEXT NOT NULL, -- 'Fundo' | 'CiaAberta'
  categoria_registro TEXT NOT NULL,
  controle_id INTEGER NOT NULL, -- numero de controle para upsert caso a empresa já exista
  pais_origem TEXT NOT NULL,
  pais_custodia TEXT NOT NULL,
  situacao_emissor TEXT NOT NULL, 
  dia_encerramento_fiscal INTEGER NOT NULL,
  mes_encerramento_fiscal INTEGER NOT NULL,
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);


CREATE TABLE IF NOT EXISTS ativos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT UNIQUE NOT NULL,
  nome TEXT NOT NULL,
  classe TEXT NOT NULL, -- 'Acao' | 'FII' | 'Tesouro' | 'BDR' | 'ETF'
  empresa_id INTEGER,
  controle_id INTEGER NOT NULL,
  valor_mobiliario TEXT NOT NULL,
  sigla_classe_acao TEXT  NULL,
  classe_acao TEXT  NULL,
  composicao TEXT NULL,
  mercado TEXT NOT NULL, -- 'B3' | 'OTC' | 'NYSE' | 'NASDAQ' | 'ARCA' | 'AMEX' | 'OTHER'
  data_inicio_negociacao TEXT NOT NULL, -- ISO date
  data_fim_negociacao TEXT NULL, -- ISO date
  segmento TEXT NOT NULL DEFAULT 0,
  importado INTEGER NOT NULL DEFAULT 0, -- 0=manual, 1=importado
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

CREATE TABLE IF NOT EXISTS transacoes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data TEXT NOT NULL, -- ISO date
  tipo TEXT NOT NULL, -- COMPRA|VENDA|BONIFICACAO|SUBSCRICAO|AMORTIZACAO|TRANSFERENCIA|EVENTO
  corretora_id INTEGER,
  quantidade TEXT NOT NULL, -- Decimal string (6 casas)
  ticker INTEGER NOT NULL,  -- FK para ativos.id
  carteira_id INTEGER NOT NULL,
  preco_unitario TEXT,      -- Decimal string (4 casas)
  taxas TEXT DEFAULT '0',   -- Decimal string (4 casas)
  observacoes TEXT,
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (corretora_id) REFERENCES corretoras(id),
  FOREIGN KEY (ticker) REFERENCES ativos(id),
  FOREIGN KEY (carteira_id) REFERENCES carteiras(id)
);

CREATE INDEX IF NOT EXISTS idx_transacoes_ticker_data ON transacoes(ticker, data);
CREATE INDEX IF NOT EXISTS idx_transacoes_carteira ON transacoes(carteira_id);

CREATE TABLE IF NOT EXISTS proventos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data_referencia TEXT NOT NULL,  -- YYYY-MM-DD (último dia do mês)
  ticker INTEGER NOT NULL,
  descricao TEXT,
  data_pagamento TEXT NOT NULL, -- ISO date
  tipo_evento TEXT NOT NULL, -- DIVIDENDO|JCP|RENDIMENTO FII|AMORTIZACAO|OUTROS
  instituicao TEXT NOT NULL,
  quantidade TEXT,       -- opcional
  preco_unitario TEXT,   -- opcional
  valor_total TEXT,      -- opcional
  observacoes TEXT,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);



CREATE INDEX IF NOT EXISTS idx_proventos_ticker_data ON proventos(ticker, data_pagamento);

CREATE TABLE IF NOT EXISTS eventos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tipo TEXT NOT NULL, -- Split|Inplit|Bonificacao|TrocaTicker
  ticker_antigo INTEGER,
  ticker_novo INTEGER,
  data_ex TEXT NOT NULL, -- ISO date
  num INTEGER DEFAULT 0,
  --den INTEGER DEFAULT 0,
  observacoes TEXT,
  ativo INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (ticker_antigo) REFERENCES ativos(id),
  FOREIGN KEY (ticker_novo) REFERENCES ativos(id)
);

CREATE INDEX IF NOT EXISTS idx_eventos_data ON eventos(data_ex);
CREATE INDEX IF NOT EXISTS idx_eventos_ticker ON eventos(ticker_antigo, ticker_novo);


CREATE TABLE IF NOT EXISTS ticker_mapping (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker_antigo TEXT NOT NULL,
  ticker_novo TEXT NOT NULL,
  data_vigencia DATE NOT NULL -- ISO date
);

CREATE INDEX IF NOT EXISTS idx_mapping_data ON ticker_mapping(data_vigencia);

CREATE TABLE IF NOT EXISTS fechamentos_mensais (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker INTEGER NOT NULL,
  data_ref TEXT NOT NULL,         -- último dia do mês (conforme regra)
  preco_fechamento TEXT NOT NULL, -- Decimal string (4)
  quantidade TEXT,                -- posição consolidada
  FOREIGN KEY (ticker) REFERENCES ativos(id)
);

CREATE INDEX IF NOT EXISTS idx_fechamentos_ticker_data ON fechamentos_mensais(ticker, data_ref);

CREATE TABLE IF NOT EXISTS config (
  chave TEXT PRIMARY KEY,
  valor TEXT
);
