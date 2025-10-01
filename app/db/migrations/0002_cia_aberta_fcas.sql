-- Migration: CVM FCA - Cadastro de Empresas
-- Tabela para armazenar dados do Formulário Cadastral (FCA) da CVM

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cia_aberta_fca_geral (
	cnpj TEXT NOT NULL UNIQUE,
	data_referencia TEXT,
	documento_id INTEGER,
	razao_social TEXT,
	data_constituicao TEXT,
	codigo_cvm TEXT,
	data_registro_cvm TEXT,
	categoria_registro TEXT,
	situacao_registro_cvm TEXT,
	pais_origem TEXT,
	pais_custodia_valores_mobiliarios TEXT,
	setor_atividade TEXT,
	descricao_atividade TEXT,
	situacao_emissor TEXT,
	controle_acionario TEXT,
	dia_encerramento_exercicio_social INTEGER,
	mes_encerramento_exercicio_social INTEGER,
	pagina_web TEXT,
	criado_em TEXT NOT NULL DEFAULT (datetime('now')),
	atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_cia_fca_documento_id ON cia_aberta_fca_geral (documento_id);
CREATE INDEX IF NOT EXISTS idx_cia_fca_codigo_cvm ON cia_aberta_fca_geral (codigo_cvm);
CREATE INDEX IF NOT EXISTS idx_cia_fca_data_referencia ON cia_aberta_fca_geral (data_referencia);
CREATE INDEX IF NOT EXISTS idx_cia_fca_situacao_registro ON cia_aberta_fca_geral (situacao_registro_cvm);