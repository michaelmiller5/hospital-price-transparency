"""Build the DuckDB database from the cleaned CSVs and the SQL files.

Run from the repository root:  python scripts/build_database.py
Creates data/processed/hospital_prices.duckdb (rebuilt from scratch each run).
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "hospital_prices.duckdb"


def main():
    if DB.exists():
        DB.unlink()
    con = duckdb.connect(str(DB))
    con.execute(f"SET file_search_path = '{ROOT.as_posix()}'")
    for sql_file in sorted((ROOT / "sql").glob("*.sql")):
        con.execute(sql_file.read_text())
        print(f"ran {sql_file.name}")

    # Sanity checks: fail loudly if the load does not match the cleaning output.
    total, usable = con.execute(
        "SELECT COUNT(*), COUNT(*) FILTER (WHERE exclusion_reason = '') FROM rates").fetchone()
    assert total > 0 and usable > 0, "rates table is empty"
    bad = con.execute(
        "SELECT COUNT(*) FROM usable_rates WHERE negotiated_dollar IS NULL OR negotiated_dollar <= 0").fetchone()[0]
    assert bad == 0, f"{bad} usable rows have a missing or non-positive price"
    print(f"rates: {total:,} rows, {usable:,} usable")
    con.close()


if __name__ == "__main__":
    main()
