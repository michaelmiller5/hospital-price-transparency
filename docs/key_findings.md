# Key findings (locked Nov 2, 2026)

Scope: hospital facility prices (not physician fees) for 10 shoppable services, commercial insurance unless stated, at five hospitals: Crouse, St. Joseph's and Upstate (Syracuse); Strong Memorial and Highland (Rochester). Source: each hospital's 2026 machine-readable price file. Every number below is reproduced by `scripts/analysis_stats.py` and the table named in brackets.

Each "contract" is one insurer plan's published price. Contracts are counted equally, not weighted by how many people each plan covers, because the files do not include enrollment.

## 1. Which hospital is cheapest depends on the insurer contract, not just the hospital.

For the same procedure, commercial prices ranged up to 25 to 28 times from the lowest to the highest contract for MRI and CT head. For the five CT and MRI services, how the contract is set explains about 75% of the price variation; which hospital explains about 50% (the two overlap). [01_variance_sources]

## 2. Percent-of-charges contracts produce the extreme prices.

Some contracts pay a percentage of the hospital's list price instead of a fixed fee. Among commercial contracts that publish a dollar amount, these appear only at Upstate and St. Joseph's. Where a hospital had both kinds for the same procedure, the percent-of-charges contracts were higher in 11 of 12 comparisons, by 1.9 to 7.5 times. The exception was upper GI endoscopy at Upstate (0.4 times). [02_pct_of_charges_gap]

Example, MRI brain at Upstate: fixed-fee contracts (Excellus, MVP) were $625 to $839. Percent-of-charges contracts (UnitedHealthcare, UMR, Aetna, CDPHP, EmblemHealth, MultiPlan, First Health) were $2,639 to $7,957, against a list price of $8,841. [contract_prices view]

Limit: all 12 comparisons come from two hospitals, so this is a pattern in this data, not a general rate.

## 3. On fixed-fee contracts alone, hospital differences are modest.

With only fixed-fee and case-rate contracts, the most expensive hospital was 1.3 to 1.5 times the cheapest for 8 of the 10 services. Exceptions: screening mammograms (Strong and Highland about 2.5 times Crouse) and inpatient joint replacement (Upstate 2.1 times Highland, based on only 2 to 6 contracts per hospital). Crouse had the lowest median for all six imaging services; Highland had the lowest for colonoscopy, endoscopy and both joint replacement items. Upstate had the highest fixed-fee median for all nine services where it has fixed-fee contracts. [05_fixed_fee_comparison]

Sensitivity: Strong and Highland publish two facility price lists for some services (APC-tagged lines and chargemaster lines), and the main analysis uses the median across both (judgment call L4). Using only one list, the gap for those 8 services is 1.5 to 1.9 times instead of 1.3 to 1.5, and the rankings shift: with APC lines only, Highland is lowest on all eight; with chargemaster lines only, Strong is highest on seven. The conclusion that fixed-fee gaps are far smaller than percent-of-charges gaps holds under every version. [06_rate_list_sensitivity]

## 4. The same insurer pays different hospitals different prices, by a steady margin.

- MVP: the most expensive hospital was 1.27 to 1.65 times the cheapest across eight services, with Upstate highest on all eight and Crouse lowest on seven. Screening mammograms were the exception at 2.6 times (Highland highest, Crouse lowest). [03b_same_insurer_spread]
- Excellus: St. Joseph's was 1.55 times Highland for all eight outpatient services where Excellus prices were published at all five hospitals, with the same ratio on every service. Excellus's ratios between Crouse, St. Joseph's, Strong and Highland are constant across services; Upstate's are not (1.45 to 1.53 times Highland). Caveat: Strong and Highland each list a second, higher Excellus rate for imaging (MRI brain: Highland $555.23 vs $420.18, Strong $814.53 vs $524.91). Using Highland's higher line, St. Joseph's is about 1.17 times Highland for imaging instead of 1.55. [03b_same_insurer_spread]

## 5. Commercial plans pay about double Medicare Advantage.

At the three hospitals that use fixed-fee commercial contracts (Crouse, Highland, Strong), commercial prices were 1.55 to 2.3 times the Medicare Advantage price for most services. Mammograms (about 5 times at Highland and Strong) and inpatient joint replacement at Highland and Strong (1.1 to 1.3 times) were outside that range. Highland's inpatient joint replacement figure rests on two commercial contracts, one of which (POMCO, $20,399.98) equals its Medicare Advantage case rate. Upstate's fixed-fee contracts are higher than this range (about 2.4 times). [04_commercial_vs_medicare_advantage]

## 6. Transparency gap: Rochester General's file is hard to use for price shopping.

For the 9 outpatient services, Rochester General's 2026 file gives an insurer dollar price from one insurer (Aetna) for six imaging services, and from none for colonoscopy, upper GI endoscopy or outpatient knee replacement. The other payers' prices appear as formulas (for example, a percent of billed charges or of Medicare) on separate rows grouped by APC procedure group rather than by service code. Inpatient joint replacement (DRG 470) has dollar prices from five payer contracts (four commercial, one Medicare Advantage). [rates table, hospital_key = rochester_general]

## What this data does not show

- Actual amounts paid on claims, or patient out-of-pocket costs.
- How many people each contract covers, so contract counts are not market share.
- For percent-of-charges contracts, the dollar figure is the hospital's own published estimate.
- Quality of care.
- Strong and Highland figures depend partly on how their two facility price lists are combined (see finding 3 sensitivity).
