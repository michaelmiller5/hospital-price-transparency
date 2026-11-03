-- Base tables, loaded from the CSVs that scripts/clean_rates.py produces.
-- Paths are relative to the repository root.

CREATE OR REPLACE TABLE hospitals AS
SELECT * FROM read_csv('data/processed/hospitals.csv', header = true, all_varchar = true);

CREATE OR REPLACE TABLE procedures AS
SELECT * FROM read_csv('data/processed/procedures.csv', header = true, all_varchar = true);

-- One row per published price line (or per payer/plan cell for wide files).
-- exclusion_reason = '' means the row is usable in the comparison.
CREATE OR REPLACE TABLE rates AS
SELECT
    hospital_key,
    procedure_code,
    description,
    setting,
    billing_class,
    modifiers,
    TRY_CAST(NULLIF(gross_charge, '') AS DOUBLE)          AS gross_charge,
    TRY_CAST(NULLIF(cash_price, '') AS DOUBLE)            AS cash_price,
    payer_raw,
    plan_raw,
    insurer,
    plan_type,
    TRY_CAST(NULLIF(negotiated_dollar, '') AS DOUBLE)     AS negotiated_dollar,
    TRY_CAST(NULLIF(negotiated_percentage, '') AS DOUBLE) AS negotiated_percentage,
    has_algorithm = 'True'                                AS has_algorithm,
    methodology,
    notes,
    behavioral_contract = 'True'                          AS behavioral_contract,
    contract_key,
    COALESCE(exclusion_reason, '')                        AS exclusion_reason,
    source_file,
    CAST(source_line AS INTEGER)                          AS source_line,
    rate_layer
FROM read_csv('data/processed/rates_long.csv', header = true, all_varchar = true);
