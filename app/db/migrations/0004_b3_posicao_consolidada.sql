-- Migração para tabela de posição consolidada da B3
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS b3_posicao_consolidada (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	data_referencia TEXT NOT NULL,                    -- YYYY-MM-DD (último dia do mês)
	produto TEXT NOT NULL,                             -- Nome do produto
	instituicao TEXT NOT NULL,                        -- Nome da corretora
	conta TEXT NOT NULL,                              -- Número da conta
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
	atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Índice único para evitar duplicações por competência/conta/ticker
CREATE UNIQUE INDEX IF NOT EXISTS idx_b3_posicao_unique 
	ON b3_posicao_consolidada(data_referencia, instituicao, codigo_isin);

-- Índices para consultas comuns
CREATE INDEX IF NOT EXISTS idx_b3_posicao_data ON b3_posicao_consolidada(data_referencia);
CREATE INDEX IF NOT EXISTS idx_b3_posicao_instituicao ON b3_posicao_consolidada(instituicao);
CREATE INDEX IF NOT EXISTS idx_b3_posicao_ticker ON b3_posicao_consolidada(codigo_negociacao);
CREATE INDEX IF NOT EXISTS idx_b3_posicao_cnpj ON b3_posicao_consolidada(cnpj_empresa);