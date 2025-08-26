-- Migração para tabela de posição consolidada da B3
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS b3_posicao_consolidada (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	data_referencia TEXT NOT NULL,                    -- YYYY-MM-DD (último dia do mês)
	instituicao TEXT NOT NULL,                        -- Nome da corretora
	conta TEXT NOT NULL,                              -- Número da conta
	cnpj_empresa TEXT NOT NULL,                       -- CNPJ da empresa emissora
	codigo_negociacao TEXT NOT NULL,                  -- Ticker/código de negociação
	nome_ativo TEXT NOT NULL,                         -- Nome do ativo
	quantidade_disponivel TEXT NOT NULL DEFAULT '0',  -- Decimal string
	quantidade_indisponivel TEXT NOT NULL DEFAULT '0', -- Decimal string  
	valor_atualizado TEXT NOT NULL DEFAULT '0',       -- Decimal string
	preco_unitario TEXT,                              -- Decimal string (opcional)
	percentual_carteira TEXT,                         -- Decimal string (opcional)
	observacoes TEXT,                                 -- Campo adicional para outras informações
	criado_em TEXT NOT NULL DEFAULT (datetime('now')),
	atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Índice único para evitar duplicações por competência/conta/ticker
CREATE UNIQUE INDEX IF NOT EXISTS idx_b3_posicao_unique 
	ON b3_posicao_consolidada(data_referencia, instituicao, conta, codigo_negociacao);

-- Índices para consultas comuns
CREATE INDEX IF NOT EXISTS idx_b3_posicao_data ON b3_posicao_consolidada(data_referencia);
CREATE INDEX IF NOT EXISTS idx_b3_posicao_instituicao ON b3_posicao_consolidada(instituicao);
CREATE INDEX IF NOT EXISTS idx_b3_posicao_ticker ON b3_posicao_consolidada(codigo_negociacao);
CREATE INDEX IF NOT EXISTS idx_b3_posicao_cnpj ON b3_posicao_consolidada(cnpj_empresa);