-- Analysis views. Each layer builds on the one before it.

-- 1. Usable rates: facility fee, base service, right setting, dollar amount, not a duplicate.
CREATE OR REPLACE VIEW usable_rates AS
SELECT r.*, h.hospital_name, h.city, h.health_system, p.label AS procedure_label, p.category
FROM rates r
JOIN hospitals h USING (hospital_key)
JOIN procedures p USING (procedure_code)
WHERE r.exclusion_reason = '';

-- 2. One price per insurer contract. A contract that lists several usable rates
--    for the same procedure gets the median of them (see judgment call L4).
CREATE OR REPLACE VIEW contract_prices AS
SELECT
    hospital_key, hospital_name, city, health_system,
    procedure_code, procedure_label, category,
    plan_type, insurer, contract_key,
    MEDIAN(negotiated_dollar)                          AS price,
    COUNT(*)                                           AS n_rate_lines,
    MIN(negotiated_dollar)                             AS min_line_price,
    MAX(negotiated_dollar)                             AS max_line_price,
    BOOL_OR(methodology = 'percent of total billed charges') AS pct_of_charges
FROM usable_rates
GROUP BY ALL;

-- 3. Hospital x procedure x plan type summary across contracts.
CREATE OR REPLACE VIEW price_summary AS
SELECT
    hospital_key, hospital_name, city,
    procedure_code, procedure_label, category, plan_type,
    COUNT(*)                         AS n_contracts,
    COUNT(DISTINCT insurer)          AS n_insurers,
    MEDIAN(price)                    AS median_price,
    QUANTILE_CONT(price, 0.25)       AS p25_price,
    QUANTILE_CONT(price, 0.75)       AS p75_price,
    MIN(price)                       AS min_price,
    MAX(price)                       AS max_price,
    AVG(CASE WHEN pct_of_charges THEN 1 ELSE 0 END) AS share_pct_of_charges
FROM contract_prices
GROUP BY ALL;

-- 4. Commercial prices side by side, with each hospital compared to the
--    lowest-priced hospital for that procedure.
CREATE OR REPLACE VIEW commercial_comparison AS
SELECT
    procedure_code, procedure_label, hospital_name, city,
    n_contracts, n_insurers,
    ROUND(median_price, 2)                                            AS median_price,
    ROUND(min_price, 2)                                               AS min_price,
    ROUND(max_price, 2)                                               AS max_price,
    ROUND(median_price / MIN(median_price) OVER (PARTITION BY procedure_code), 2) AS x_lowest_hospital,
    RANK() OVER (PARTITION BY procedure_code ORDER BY median_price)  AS rank_low_to_high,
    ROUND(share_pct_of_charges, 2)                                    AS share_pct_of_charges
FROM price_summary
WHERE plan_type = 'Commercial';

-- 5. Spread across insurers inside the same hospital (commercial contracts).
CREATE OR REPLACE VIEW insurer_spread AS
SELECT
    hospital_name, procedure_code, procedure_label,
    n_contracts,
    ROUND(min_price, 2)               AS lowest_contract,
    ROUND(max_price, 2)               AS highest_contract,
    ROUND(max_price / min_price, 2)   AS high_to_low_ratio
FROM price_summary
WHERE plan_type = 'Commercial' AND n_contracts >= 2;

-- 6. Commercial prices split by how the contract is set (fixed fee vs percent of charges).
CREATE OR REPLACE VIEW commercial_by_method AS
SELECT
    hospital_name, procedure_code, procedure_label,
    CASE WHEN pct_of_charges THEN 'percent of charges' ELSE 'fixed fee / case rate' END AS contract_method,
    COUNT(*)                     AS n_contracts,
    ROUND(MEDIAN(price), 2)      AS median_price
FROM contract_prices
WHERE plan_type = 'Commercial'
GROUP BY ALL;

-- 7. Same insurer, same procedure, different hospitals (commercial): who pays the most where.
CREATE OR REPLACE VIEW insurer_across_hospitals AS
SELECT
    insurer, procedure_code, procedure_label, hospital_name,
    ROUND(MEDIAN(price), 2) AS median_price
FROM contract_prices
WHERE plan_type = 'Commercial'
GROUP BY ALL;

-- 8. Audit trail: how many rows each exclusion rule removed, per hospital.
CREATE OR REPLACE VIEW cleaning_audit AS
SELECT hospital_key,
       CASE WHEN exclusion_reason = '' THEN 'usable' ELSE exclusion_reason END AS outcome,
       COUNT(*) AS n_rows
FROM rates
GROUP BY ALL
ORDER BY hospital_key, n_rows DESC;
