"""Spot-check: confirm sampled cleaned rates trace back, unchanged, to the hospital's raw file.

For each sampled row in rates_long.csv, take its line from the filtered extract,
check that exact line exists in the original hospital file, and check that the
cleaned dollar amount appears in that line.

Usage (from the repository root):
    python scripts/verify_against_raw.py data/processed/rates_long.csv data/filtered data/raw/<hospital file> <hospital_key> [N]
"""
import csv, io, random, sys, zipfile

import pandas as pd

csv.field_size_limit(1 << 30)


def raw_lines(path):
    if path.endswith(".zip"):
        zf = zipfile.ZipFile(path)
        f = io.TextIOWrapper(zf.open(zf.namelist()[0]), encoding="utf-8-sig", newline="")
    else:
        f = open(path, encoding="utf-8-sig", newline="")
    for rec in csv.reader(f):
        yield tuple(c.strip() for c in rec)


def main():
    rates, fdir, raw, hosp = sys.argv[1:5]
    n = int(sys.argv[5]) if len(sys.argv) > 5 else 8
    df = pd.read_csv(rates, keep_default_na=False)
    usable = df[(df.hospital_key == hosp) & (df.exclusion_reason == "")]
    sample = usable.sample(min(n, len(usable)), random_state=7)
    fname = sample.source_file.iloc[0]
    with open(f"{fdir}/{fname}", encoding="utf-8-sig", newline="") as f:
        frows = [tuple(c.strip() for c in r) for r in csv.reader(f)]
    targets = {int(r.source_line): frows[int(r.source_line) - 1] for r in sample.itertuples()}
    found = set()
    want = set(targets.values())
    for rec in raw_lines(raw):
        if rec in want:
            found.add(rec)
            if len(found) == len(want):
                break
    ok = 0
    for r in sample.itertuples():
        line = targets[int(r.source_line)]
        in_raw = line in found
        amount_ok = any(abs(float(c) - float(r.negotiated_dollar)) < 0.005
                        for c in line if c.replace(".", "", 1).isdigit())
        ok += in_raw and amount_ok
        print(f"{'PASS' if in_raw and amount_ok else 'FAIL'}  line {r.source_line}  {r.procedure_code}  "
              f"{r.insurer} / {r.plan_type}  ${float(r.negotiated_dollar):,.2f}")
    print(f"{hosp}: {ok}/{len(sample)} sampled rates traced to the raw file")


if __name__ == "__main__":
    main()
