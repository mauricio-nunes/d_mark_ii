-- banco do Brasil : 00000000000191
-- sanepar : 76484013000145

WITH ult AS (
    /* pega a última versão disponível por CNPJ + data + grupo */
    SELECT 
        cnpj, 
        data_referencia, 
        grupo, 
        MAX(versao) AS versao
    FROM cia_aberta_itr_dre
    WHERE cnpj = '76484013000145'
      AND grupo = 'DF Individual'
    GROUP BY cnpj, data_referencia, grupo
),
base AS (
    /* traz os valores já na escala correta */
    SELECT
        d.codigo_conta,
        d.descricao_conta,
        d.data_referencia,
        CAST(d.valor_conta AS REAL) *
          CASE
            WHEN UPPER(d.escala_moeda) IN ('MIL','MILHAR') THEN 1000.0
            WHEN UPPER(d.escala_moeda) IN ('MILHÃO','MILHAO','MILHÕES','MILHOES') THEN 1000000.0
            ELSE 1.0
          END AS valor_ajust
    FROM cia_aberta_itr_dre d
    INNER JOIN ult u
      ON d.cnpj = u.cnpj
     AND d.data_referencia = u.data_referencia
     AND d.grupo = u.grupo
     AND d.versao = u.versao
),
agg AS (
    /* faz o pivot acumulado */
    SELECT
        codigo_conta,
        descricao_conta,
        MAX(CASE WHEN data_referencia = '2024-03-31' THEN valor_ajust END) AS cum_03,
        MAX(CASE WHEN data_referencia = '2024-06-30' THEN valor_ajust END) AS cum_06,
        MAX(CASE WHEN data_referencia = '2024-09-30' THEN valor_ajust END) AS cum_09,
        MAX(CASE WHEN data_referencia = '2024-12-31' THEN valor_ajust END) AS cum_12
    FROM base
    GROUP BY codigo_conta, descricao_conta
)
SELECT
    codigo_conta,
    descricao_conta,

    /* acumulados (como vêm na DRE) */
    ROUND(cum_03, 2) AS acumulado_03,
    ROUND(cum_06, 2) AS acumulado_06,
    ROUND(cum_09, 2) AS acumulado_09,
    ROUND(cum_12, 2) AS acumulado_12,

    /* valores trimestrais (diferenças) */
    ROUND(cum_03, 2) AS tri_1,
    ROUND(COALESCE(cum_06, 0) - COALESCE(cum_03, 0), 2) AS tri_2,
    ROUND(COALESCE(cum_09, 0) - COALESCE(cum_06, 0), 2) AS tri_3,
    ROUND(COALESCE(cum_12, 0) - COALESCE(cum_09, 0), 2) AS tri_4

FROM agg
ORDER BY codigo_conta;

