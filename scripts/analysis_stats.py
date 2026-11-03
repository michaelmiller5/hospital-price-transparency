"""Statistics for the commercial price comparison.

Reads the contract_prices view from data/processed/hospital_prices.duckdb and writes
result tables to data/processed/analysis/. All statistics use commercial contracts
for the five comparison hospitals. Prices are compared on a log scale because
price differences are multiplicative (2x, 3x), not additive.

Run from the repository root:  python scripts/analysis_stats.py
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed" / "analysis"
RNG = np.random.default_rng(2026)


def eta_squared(values, groups):
    """Share of total variance in `values` explained by `groups` (0 to 1)."""
    values = np.asarray(values, float)
    grand = values.mean()
    total = ((values - grand) ** 2).sum()
    if total == 0:
        return np.nan
    between = sum(len(v) * (v.mean() - grand) ** 2
                  for _, v in pd.Series(values).groupby(np.asarray(groups)))
    return between / total


def bootstrap_ci(x, stat=np.median, n=10_000, level=0.95):
    x = np.asarray(x, float)
    boots = stat(RNG.choice(x, size=(n, len(x)), replace=True), axis=1)
    lo, hi = np.quantile(boots, [(1 - level) / 2, 1 - (1 - level) / 2])
    return lo, hi


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ROOT / "data" / "processed" / "hospital_prices.duckdb"), read_only=True)
    cp = con.execute("SELECT * FROM contract_prices").df()
    com = cp[cp.plan_type == "Commercial"].copy()
    com["log_price"] = np.log(com["price"])
    com["method"] = np.where(com["pct_of_charges"], "percent of charges", "fixed fee / case rate")

    # 1. Where does the variation come from? Hospital vs contract method, per procedure.
    rows = []
    for (code, label), g in com.groupby(["procedure_code", "procedure_label"]):
        rows.append({
            "procedure_code": code, "procedure_label": label,
            "n_contracts": len(g), "n_hospitals": g.hospital_key.nunique(),
            "share_pct_of_charges": round(g.pct_of_charges.mean(), 2),
            "variance_explained_by_hospital": round(eta_squared(g.log_price, g.hospital_key), 2),
            "variance_explained_by_method": round(eta_squared(g.log_price, g.method), 2)
                if g.method.nunique() > 1 else np.nan,
            "highest_to_lowest_contract": round(g.price.max() / g.price.min(), 1),
        })
    var = pd.DataFrame(rows)
    var.to_csv(OUT / "01_variance_sources.csv", index=False)

    # 2. Percent-of-charges vs fixed-fee contracts inside the same hospital and procedure.
    rows = []
    for (h, code), g in com.groupby(["hospital_name", "procedure_code"]):
        if g.method.nunique() < 2:
            continue
        pct, fixed = g[g.pct_of_charges], g[~g.pct_of_charges]
        rows.append({"hospital_name": h, "procedure_code": code,
                     "n_pct": len(pct), "n_fixed": len(fixed),
                     "median_pct": round(pct.price.median(), 2),
                     "median_fixed": round(fixed.price.median(), 2),
                     "ratio": round(pct.price.median() / fixed.price.median(), 2)})
    gap = pd.DataFrame(rows)
    gap.to_csv(OUT / "02_pct_of_charges_gap.csv", index=False)
    if len(gap):
        lo, hi = bootstrap_ci(gap.ratio)
        gap_summary = {"pairs": len(gap), "median_ratio": round(gap.ratio.median(), 2),
                       "ci95_low": round(lo, 2), "ci95_high": round(hi, 2),
                       "pairs_where_pct_higher": int((gap.ratio > 1).sum())}
    else:
        gap_summary = {}
    pd.DataFrame([gap_summary]).to_csv(OUT / "02b_pct_of_charges_gap_summary.csv", index=False)

    # 3. Same insurer across hospitals (apples to apples): Excellus and MVP commercial.
    same = (com[com.insurer.isin(["Excellus BCBS", "MVP Health Care"])]
            .groupby(["insurer", "procedure_code", "procedure_label", "hospital_name"])
            .price.median().reset_index())
    spread = (same.groupby(["insurer", "procedure_code", "procedure_label"])
              .agg(n_hospitals=("hospital_name", "nunique"),
                   lowest=("price", "min"), highest=("price", "max"))
              .reset_index())
    spread["highest_to_lowest"] = (spread.highest / spread.lowest).round(2)
    lo_h = same.loc[same.groupby(["insurer", "procedure_code"]).price.idxmin(), ["insurer", "procedure_code", "hospital_name"]]
    hi_h = same.loc[same.groupby(["insurer", "procedure_code"]).price.idxmax(), ["insurer", "procedure_code", "hospital_name"]]
    spread = (spread.merge(lo_h.rename(columns={"hospital_name": "lowest_hospital"}), on=["insurer", "procedure_code"])
                    .merge(hi_h.rename(columns={"hospital_name": "highest_hospital"}), on=["insurer", "procedure_code"]))
    same.round(2).to_csv(OUT / "03a_same_insurer_prices.csv", index=False)
    spread.round(2).to_csv(OUT / "03b_same_insurer_spread.csv", index=False)

    # 4. Commercial vs Medicare Advantage at each hospital (median contract price ratio).
    ma = cp[cp.plan_type == "Medicare Advantage"].groupby(["hospital_name", "procedure_code"]).price.median()
    cm = com.groupby(["hospital_name", "procedure_code"]).price.median()
    vs = pd.concat([cm.rename("commercial_median"), ma.rename("medicare_adv_median")], axis=1).dropna().reset_index()
    vs["commercial_to_ma"] = (vs.commercial_median / vs.medicare_adv_median).round(2)
    vs.round(2).to_csv(OUT / "04_commercial_vs_medicare_advantage.csv", index=False)

    # 5. Fixed-fee-only hospital comparison (removes the percent-of-charges effect).
    fixed = (com[~com.pct_of_charges].groupby(["procedure_code", "procedure_label", "hospital_name"])
             .agg(n_contracts=("price", "size"), median_price=("price", "median")).reset_index())
    fixed["x_lowest"] = (fixed.median_price /
                         fixed.groupby("procedure_code").median_price.transform("min")).round(2)
    fixed.round(2).to_csv(OUT / "05_fixed_fee_comparison.csv", index=False)

    # 6. Sensitivity: Strong and Highland publish two facility rate lists. The main
    #    analysis takes the median across both (judgment call L4). Re-run the
    #    fixed-fee comparison using only one list at a time, where both exist.
    ur = con.execute("SELECT * FROM usable_rates WHERE plan_type = 'Commercial'").df()
    variants = {"both lists (main)": ["single", "apc_line", "chargemaster_line"],
                "APC lines only": ["single", "apc_line"],
                "chargemaster lines only": ["single", "chargemaster_line"]}
    # Where a hospital publishes only one list for a procedure, that list is kept in every variant.
    n_layers = ur.groupby(["hospital_name", "procedure_code"]).rate_layer.transform("nunique")
    rows = []
    for name, layers in variants.items():
        sub = ur[ur.rate_layer.isin(layers) | (n_layers == 1)]
        cp_v = (sub.groupby(["hospital_name", "procedure_code", "contract_key"])
                .agg(price=("negotiated_dollar", "median"),
                     pct=("methodology", lambda m: (m == "percent of total billed charges").any()))
                .reset_index())
        f = cp_v[~cp_v.pct].groupby(["procedure_code", "hospital_name"]).price.median().reset_index()
        for code, g in f.groupby("procedure_code"):
            rows.append({"variant": name, "procedure_code": code,
                         "highest_to_lowest": round(g.price.max() / g.price.min(), 2),
                         "lowest_hospital": g.loc[g.price.idxmin(), "hospital_name"],
                         "highest_hospital": g.loc[g.price.idxmax(), "hospital_name"]})
    sens = pd.DataFrame(rows)
    sens.to_csv(OUT / "06_rate_list_sensitivity.csv", index=False)

    pd.set_option("display.width", 250)
    for name, df in [("VARIANCE SOURCES", var), ("PCT-OF-CHARGES GAP", gap),
                     ("GAP SUMMARY", pd.DataFrame([gap_summary])), ("SAME INSURER SPREAD", spread),
                     ("COMMERCIAL VS MA", vs), ("FIXED-FEE ONLY", fixed), ("RATE LIST SENSITIVITY", sens)]:
        print(f"\n== {name}\n{df.round(2).to_string(index=False)}")


if __name__ == "__main__":
    main()
