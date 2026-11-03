"""Build dashboard/index.html: a single self-contained page (no external libraries).

Reads contract prices from data/processed/hospital_prices.duckdb, embeds them as JSON
into dashboard/template.html, and writes dashboard/index.html for GitHub Pages.

Run from the repository root:  python scripts/build_dashboard.py
"""
import json
import re
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent

# File dates come from each hospital file's last_updated_on field; URLs from each
# hospital's cms-hpt.txt (checked Nov 2, 2026).
SOURCES = {
    "crouse": ("2026-05-19", "https://www.crouse.org/wp-content/uploads/2026/05/16-0960470_Crouse-Hospital_standardcharges.csv"),
    "st_josephs": ("2026-03-31", "https://hpt.trinity-health.org/150532254_st-josephs-hospital-health-center_standardcharges.zip"),
    "upstate": ("2026-09-05", "https://www.upstate.edu/hospital/files/161469571_upstate-university-hospital_standardcharges.csv"),
    "strong": ("2026-07-01", "https://www.urmc.rochester.edu/getmedia/b1fa98a4-bf2c-4b54-883d-edbc50653e7a/161029490-STRONG-MEMORIAL-HOSPITAL-standardcharges.csv"),
    "highland": ("2026-07-01", "https://www.urmc.rochester.edu/getmedia/5479e418-958b-4a8a-b3ab-610f5962d661/160743037-HIGHLAND-HOSPITAL-OF-ROCHESTER-standardcharges.csv"),
    "rochester_general": ("2026-04-01", "https://msc.rochesterregional.org/practitionerPortal/docs/MRF2026/160743134_rochester-general-hospital_standardcharges.csv"),
}


def plan_label(contract_key):
    """Readable plan name: drop internal bracket codes and repeated whitespace."""
    s = re.sub(r"\s*\[\d+\]", "", contract_key)
    s = re.sub(r"\s+", " ", s).strip(" ,|")
    return s[:120]


def main():
    con = duckdb.connect(str(ROOT / "data" / "processed" / "hospital_prices.duckdb"), read_only=True)
    hospitals = con.execute(
        "SELECT hospital_key, hospital_name, city, health_system, role FROM hospitals").fetchall()
    procedures = con.execute(
        "SELECT procedure_code, label, category FROM procedures").fetchall()
    rows = con.execute("""
        SELECT hospital_key, procedure_code, plan_type, insurer, contract_key,
               ROUND(price, 2), pct_of_charges, n_rate_lines
        FROM contract_prices ORDER BY hospital_key, procedure_code, price, plan_type, insurer, contract_key""").fetchall()
    data = {
        "hospitals": [{"key": k, "name": n, "city": c, "system": s, "role": r,
                       "updated": SOURCES[k][0], "url": SOURCES[k][1]} for k, n, c, s, r in hospitals],
        "procedures": [{"code": c, "label": l, "category": g} for c, l, g in procedures],
        "contracts": [[h, p, t, i, plan_label(k), v, int(bool(m)), n]
                      for h, p, t, i, k, v, m, n in rows],
    }
    template = (ROOT / "dashboard" / "template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace("/*__DATA__*/null", payload)
    assert html != template, "data placeholder not found in template"
    (ROOT / "dashboard" / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote dashboard/index.html with {len(rows):,} contract prices")


if __name__ == "__main__":
    main()
