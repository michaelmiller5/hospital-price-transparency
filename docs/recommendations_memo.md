# Memo: Where hospital prices differ in Syracuse and Rochester, and what to do about it

**To:** Benefits and network leaders at self-funded employers and health plans in Central and Western New York
**From:** Michael Miller, data analyst
**Date:** November 2026
**Data:** 2026 price transparency files published by Crouse, St. Joseph's and Upstate (Syracuse), Strong Memorial and Highland (Rochester), and Rochester General (Rochester). Hospital facility prices for 10 common shoppable services. Methods and every cleaning decision are documented in this repository.

## Bottom line

1. The biggest price risk is not a particular hospital. It is contracts that pay a **percentage of the hospital's list price**. At Upstate and St. Joseph's, those contracts priced imaging at 1.9 to 7.5 times the same hospital's fixed-fee contracts.
2. Even for the same insurer, the higher-priced hospital in the same city charged **17% to 34% more** for the same service (Excellus and MVP, all services except mammograms; up to 47% in Rochester depending on which of Strong and Highland's two price lists is used). For outpatient knee replacement that is $4,500 to $10,000 per case. That is enough to steer.
3. Rochester General's file does not show code-level dollar prices for most insurers, so buyers cannot compare it on the same terms.

## What the data shows

**Percent-of-charges contracts drive the extreme prices.** For an MRI brain at Upstate, fixed-fee commercial contracts (Excellus, MVP) were $625 to $839. Percent-of-list-price contracts (UnitedHealthcare, UMR, Aetna, CDPHP, EmblemHealth, MultiPlan, First Health) were $2,639 to $7,957, against a list price of $8,841. Across the hospital and procedure pairs that had both contract types, percent-of-charges contracts were higher in 11 of 12.

**Same insurer, same city, different price.** Examples from fixed-fee commercial contracts:

| Service | Insurer | Lower-priced hospital | Higher-priced hospital | Difference |
|---|---|---|---|---|
| MRI brain | MVP (Syracuse) | Crouse $624.52 | Upstate $818.94 | $194.42 (24% less at Crouse) |
| MRI brain | Excellus (Syracuse) | Crouse $534.90 | St. Joseph's $650.28 | $115.38 (18% less at Crouse) |
| MRI brain | Excellus (Rochester) | Highland $420.18 | Strong $524.91 | $104.73 (20% less at Highland) |
| Knee replacement, outpatient | MVP (Syracuse) | Crouse $33,603.99 | Upstate $43,593.03 | $9,989.04 |
| Knee replacement, outpatient | Excellus (Syracuse) | Crouse $28,781.67 | St. Joseph's $34,990.26 | $6,208.59 |
| Knee replacement, outpatient | MVP (Rochester) | Highland $26,425.28 | Strong $30,924.34 | $4,499.06 |

Strong and Highland publish two facility price lists for some services. Rochester figures use the median of both. Using only the higher chargemaster list, Highland is still lower than Strong and the MRI gap is larger (Excellus: $555.23 vs $814.53).

Excellus prices at Crouse, St. Joseph's, Strong and Highland move in lockstep: the ratio between any two of them is the same on every service (for example, St. Joseph's is 1.55 times Highland on all eight outpatient services, using Highland's APC-line prices). That pattern suggests each hospital is paid a set multiple of one shared fee schedule. Upstate does not follow it.

**Commercial plans pay about double Medicare Advantage** on fixed-fee contracts (1.55 to 2.3 times at Crouse, Highland and Strong for most services).

## Recommendations

1. **Find out how your plan pays Upstate and St. Joseph's.** Ask your carrier or TPA whether your contracts with these hospitals are fixed fee or percent of charges, service by service. If imaging is paid as a percent of charges, push for a fixed fee schedule or a cap tied to Medicare rates. Of the five recommendations, this one has the most money at stake per scan.
2. **Steer shoppable imaging within each city, by insurer.** In Syracuse, Crouse had the lowest Excellus and MVP prices for MRI, CT and colonoscopy. In Rochester, Highland was lower than Strong for both Excellus and MVP on every service where both hospitals list a price, under either of their price lists, except MVP mammograms (the same price at both). Use lower copays, a preferred tier, or care navigation for scheduled imaging.
3. **Prioritize outpatient knee replacement.** It carries the largest dollar gap per case (about $4,500 to $10,000 between hospitals in the same city for the same insurer). It is a good fit for a bundled price or a preferred-provider arrangement, alongside quality data that this analysis does not include.
4. **Use Medicare rates as the yardstick in negotiations.** At Crouse, Highland and Strong, commercial prices sit at roughly 1.55 to 2.3 times Medicare Advantage for most services (Upstate's fixed-fee contracts run about 2.4 times). At Upstate, the median commercial MRI brain price is about 11 times its Medicare Advantage price because of percent-of-charges contracts. That is far outside the fixed-fee range and worth challenging.
5. **Ask Rochester Regional for code-level rates directly.** Its 2026 file gives an insurer dollar price for these outpatient services from one insurer at most, so a buyer cannot compare it with the other hospitals from the public file alone.

## Limits of this analysis

- These are published negotiated rates, not claims. They do not show what was actually paid or what patients owed.
- Contracts are counted equally. The files do not say how many people each plan covers, so a small network counts the same as Excellus.
- For percent-of-charges contracts, the dollar figure is the hospital's own estimate.
- Quality, access and wait times are not included. Price alone should not decide where care is steered.
- Inpatient joint replacement rests on only 2 to 6 commercial contracts per hospital.
- Strong and Highland numbers depend partly on how their two facility price lists are combined; the repository includes the comparison under each list.

## With more data, next steps would be

- Weight prices by claims volume to estimate actual dollars at stake for a given employer.
- Add Medicare fee-for-service rates as a fixed benchmark.
- Extend to the other hospitals in the URMC and Rochester Regional systems and to more services.
