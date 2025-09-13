-- Migration: Add 'consolidado' column to movimentacao table
ALTER TABLE movimentacao ADD COLUMN consolidado BOOLEAN DEFAULT 0;
