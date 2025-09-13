-- Migração para tabela de movimentação da B3
PRAGMA foreign_keys = ON;

-- CREATE TABLE IF NOT EXISTS movimentacao (
--   id INTEGER PRIMARY KEY AUTOINCREMENT,
--   hash_linha TEXT UNIQUE NOT NULL,  -- SHA-256 para idempotência
--   entrada_saida TEXT NOT NULL,      -- normalizada (minúsculas sem acentos credito / debito)
--   data TEXT NOT NULL,               -- YYYY-MM-DD
--   movimentacao TEXT NOT NULL,       -- normalizada (minúsculas sem acentos)
--   produto TEXT NOT NULL,    -- descrição do ativo
--   codigo TEXT NOT NULL,             -- código do ativo
--   codigo_negociacao TEXT,           -- código de negociação (pode ser NULL)
--   instituicao TEXT NOT NULL,        -- nome da instituição financeira
--   quantidade TEXT NOT NULL,         -- Decimal string positivo
--   preco_unitario TEXT NOT NULL,     -- Decimal string com 3 casas decimais
--   valor_total_operacao TEXT,        -- Decimal string ou NULL para subscrições sem valor
--   criado_em TEXT NOT NULL DEFAULT (datetime('now')),
--   atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
-- );

-- -- Índice único para garantir idempotência
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_movimentacao_hash ON movimentacao(hash_linha);

-- -- Índices para consultas comuns
-- CREATE INDEX IF NOT EXISTS idx_movimentacao_data ON movimentacao(data);
-- CREATE INDEX IF NOT EXISTS idx_movimentacao_codigo ON movimentacao(codigo);
