# Data judgment calls

Every decision that changes which rows count, or how a row is labeled, is recorded here. Row counts come from `data/processed/cleaning_log.csv`, which `scripts/clean_rates.py` regenerates on every run.

## Source files

| # | Decision | Why |
|---|---|---|
| S1 | Each file's URL was taken from the hospital's own `cms-hpt.txt` index (the CMS-required pointer file), not third-party trackers. | Primary source. This caught Rochester General moving its file to a 2026 path. |
| S2 | Every file header was checked for hospital name, street address and license number before use. | A same-named St. Joseph's in Park Rapids, Minnesota (chisjh.org) was downloaded by mistake and caught here. It was deleted and never used. The Syracuse St. Joseph's file comes from sjhsyr.org (Trinity Health). |
| S3 | All files follow CMS template version 3.0.0. Crouse uses the "wide" layout (one column group per payer and plan); the others use "tall" (one row per payer and plan). | The cleaning script handles both layouts and outputs one common long table. |
| S4 | Crouse's file covers Crouse Hospital and its Commonwealth Division. Upstate's file covers its downtown and Community campuses. Each is treated as one hospital. | The files do not split prices by campus. |

## Procedure list

| # | Decision | Why |
|---|---|---|
| P1 | 10 items: CPT 70551, 73721, 72148, 70450, 74177, 77067, 45378, 43239, 27447, and MS-DRG 470. | All are on the CMS shoppable services list (DRG 470 covers the inpatient joint replacement stay). Every code was confirmed to have insurer dollar prices at each comparison hospital before the list was locked. |
| P2 | Knee replacement is split into outpatient (CPT 27447) and inpatient stay (MS-DRG 470). | Hospitals price these as different products. Mixing them would be wrong. DRG 470 includes hip and knee replacements and is labeled that way. |
| P3 | A row matches a procedure if any of its code columns holds the CPT code (type CPT or HCPCS) or MS-DRG 470. | Hospitals put the CPT code in different columns (some list an internal chargemaster code first). |

## Hospitals in the comparison

| # | Decision | Why |
|---|---|---|
| H1 | Rochester General is kept out of the head-to-head comparison and reported as a separate transparency finding. | For the 9 outpatient services it gives an insurer dollar price from Aetna only (six imaging services) or from no insurer (colonoscopy, endoscopy, outpatient knee replacement). Inpatient joint replacement (DRG 470) has dollar prices from five payer contracts (four commercial, one Medicare Advantage), but the outpatient gap is why it is excluded from the head-to-head. Other insurers are listed as formulas (percent of charges, percent of Medicare) and priced by APC procedure groups rather than by code. Its "median allowed amount" fields measure a different thing (historical payments for a whole group) and are not comparable to negotiated rates. |
| H2 | Highland Hospital (URMC, Rochester) was added to the comparison. | Keeps two Rochester hospitals in the head-to-head. Caveat: Highland and Strong are in the same health system. |

## Row exclusions (in the order they are applied)

A row gets the first reason that applies. Excluded rows stay in `rates_long.csv` with their reason, so every count can be audited.

| # | Exclusion | Why |
|---|---|---|
| E1 | No payer (gross charge or cash price line) | Not a negotiated insurer rate. Gross and cash prices are kept in their own columns. |
| E2 | Professional (physician) fee | The comparison is the hospital facility fee. Strong, Highland and St. Joseph's mix physician fees into the hospital file. Detection: St. Joseph's and Upstate have a `billing_class` column. Strong and Highland do not; there, lines starting with "PR" or "CHG", or with a "Physician" or "APP" tier note, are physician fees. Crouse lists facility charges only. |
| E3 | Billing modifier variant | Modifiers (for example, discontinued procedure, bilateral, technical component) change the price of the service. Only the base service is compared. St. Joseph's puts modifier text after a "\|" in the description instead of the modifiers column; both are checked. |
| E4 | Care setting does not match | CPT procedures must be outpatient (or "both"). DRG 470 must be inpatient (or "both"). |
| E5 | Behavioral-health carve-out contract | Plans such as United Behavioral Health, Evernorth Behavioral and Carelon are mental-health contracts that also appear on surgical and imaging lines. Their rates (as low as $9.47 for a knee replacement) are not real prices for these services. |
| E6 | No dollar amount | Some contracts are published only as a percentage or formula. They are counted in the cleaning log but not used as prices. |
| E7 | Duplicate of a rate already counted | The same contract and dollar amount listed on several lines (for example, Crouse lists each code with and without a revenue code; St. Joseph's repeats left, right and bilateral MRI lines). Each contract price is counted once. |

## Insurer and plan labels

| # | Decision | Why |
|---|---|---|
| L1 | Insurer names are standardized with ordered pattern rules in `clean_rates.py` (for example, "EXCELLUS BC/BS [2201]" and "Excellus" both become Excellus BCBS; Medicare Blue Choice is Excellus's Medicare Advantage product). The payer name is matched first, then the plan name. | Each hospital spells insurers differently. Matching the payer first keeps a Cigna contract that lists an MVP plan (the MVP-Cigna partnership) labeled as Cigna. |
| L2 | St. Joseph's contracts are identified by `plan_name`, not `payer_name`. | St. Joseph's lists hundreds of out-of-area Blue plans as payers (for example "BLUE CROSS - ND") that all map to one Excellus BCBS contract and rate. Using the payer name would count one contract hundreds of times. Side effect: St. Joseph's "MVP COMMERCIAL" plan, whose payers are Cigna and Cigna EAP (the MVP-Cigna partnership), is labeled MVP. No reported number changes. |
| L3 | Plan types: Commercial, Medicare Advantage, Medicaid / Essential Plan, Individual / Exchange, Military (TRICARE), Other. Assigned by ordered pattern rules on payer and plan text. | Needed to compare like with like. Notable calls: Amerigroup is Medicaid managed care; "Healthy NY" alone does not make a plan Medicaid; Upstate's "Commercial/Small Group and Individual Exchange" Excellus contract is labeled Commercial; student health plans (Crouse "MVP Student", Upstate "Individual Commercial/Student Health") are labeled Individual / Exchange because they are individual-market products, not employer group plans; St. Joseph's bare "MARTINS POINT" plan is labeled Military because its payer is US Family Health Plan (a TRICARE program). |
| L4 | When one contract lists more than one usable dollar rate for the same procedure, the contract's rate is the median of those rates. | Strong and Highland publish two facility price lists for some services (APC-tagged CPT lines and chargemaster lines) that can differ a lot (Strong MVP MRI brain: $559.46 on one line, $1,005.14 on another). Neither is clearly the one that applies, so the main analysis uses the median. 137 of 1,568 contracts have more than one rate. Because this choice moves the Rochester numbers, the fixed-fee hospital comparison is re-run with each list alone in `data/processed/analysis/06_rate_list_sensitivity.csv`, and the findings state the range. |

## Verification

| # | Check | Result |
|---|---|---|
| V1 | Extracts compared to the hospital files by checksum after transfer. | All matched. |
| V2 | 8 random usable rates per hospital traced back to the exact line in the hospital's original file, with the dollar amount confirmed (`scripts/verify_against_raw.py`). | 40 of 40 passed. |

## Open items

- Some contracts (notably several at Upstate) are "percent of total billed charges," and the hospital's file shows a computed dollar figure. These are kept, but the methodology is stored so its effect can be checked before any finding is stated.
