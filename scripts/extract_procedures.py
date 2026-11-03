"""Pull the 10 study procedures out of one raw hospital price file.

Reads a CMS v3 hospital price transparency CSV (tall or wide layout, plain or
zipped), keeps every row whose code columns hold one of the study's CPT codes
or MS-DRG 470, writes those rows unchanged (plus the 3 header lines) to an
output CSV, and prints a JSON coverage summary.

Usage (from the repository root), once per hospital file in data/raw/:
    python scripts/extract_procedures.py data/raw/<hospital file> data/filtered/<name>_filtered.csv
"""
import csv, io, json, sys, zipfile, collections

# Final procedure list (locked Nov 2, 2026): 9 CPT codes plus MS-DRG 470.
CODES = {"70551", "73721", "72148", "70450", "74177", "77067", "45378", "43239", "27447"}
DRGS = {"470"}
csv.field_size_limit(1 << 30)


def open_text(path):
    if path.lower().endswith(".zip"):
        zf = zipfile.ZipFile(path)
        name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
        return io.TextIOWrapper(zf.open(name), encoding="utf-8-sig", newline="")
    return open(path, encoding="utf-8-sig", newline="")


def main():
    src, out = sys.argv[1], sys.argv[2]
    f = open_text(src)
    r = csv.reader(f)
    meta_h, meta_v, header = next(r), next(r), next(r)
    while not any(c.strip() for c in header):  # skip blank line(s) before header
        header = next(r)
    idx = {h.strip(): i for i, h in enumerate(header)}
    code_cols = [(idx[f"code|{n}"], idx[f"code|{n}|type"]) for n in range(1, 10)
                 if f"code|{n}" in idx and f"code|{n}|type" in idx]
    tall = "payer_name" in idx

    stats = collections.defaultdict(lambda: {"rows": 0, "rows_with_payer": 0, "neg_dollar": 0,
                                             "neg_pct_or_algo_only": 0, "payers": set(),
                                             "settings": collections.Counter(),
                                             "billing_class": collections.Counter(),
                                             "code_types": collections.Counter()})
    if not tall:
        neg_cols = [i for h, i in idx.items() if h.startswith("standard_charge|") and h.endswith("|negotiated_dollar")]

    w = csv.writer(open(out, "w", newline="", encoding="utf-8"))
    w.writerow(meta_h); w.writerow(meta_v); w.writerow(header)
    g = lambda row, k: row[idx[k]].strip() if k in idx and idx[k] < len(row) else ""
    total = 0
    for row in r:
        total += 1
        hit = None
        for ci, ti in code_cols:
            if ci >= len(row):
                continue
            val, t = row[ci].strip(), row[ti].strip().upper()
            if val in CODES and t in ("CPT", "HCPCS"):
                hit, typ = val, t; break
            if t == "MS-DRG" and val.lstrip("0") in DRGS:
                hit, typ = "DRG" + val.lstrip("0"), t; break
        if not hit:
            continue
        w.writerow(row)
        s = stats[hit]
        s["rows"] += 1
        s["code_types"][typ] += 1
        s["settings"][g(row, "setting")] += 1
        s["billing_class"][g(row, "billing_class")] += 1
        if tall:
            payer = g(row, "payer_name")
            if payer:
                s["rows_with_payer"] += 1
                s["payers"].add(payer)
                if g(row, "standard_charge|negotiated_dollar"):
                    s["neg_dollar"] += 1
                elif g(row, "standard_charge|negotiated_percentage") or g(row, "standard_charge|negotiated_algorithm"):
                    s["neg_pct_or_algo_only"] += 1
        else:
            for i in neg_cols:
                if i < len(row) and row[i].strip():
                    s["neg_dollar"] += 1
                    s["payers"].add(header[i].split("|")[1].strip())
            s["rows_with_payer"] = s["neg_dollar"]

    res = {"file": src, "format": "tall" if tall else "wide", "hospital": meta_v[0].strip(),
           "data_rows": total, "codes": {}}
    for c in sorted(CODES) + ["DRG" + d for d in sorted(DRGS)]:
        s = stats.get(c)
        if not s:
            res["codes"][c] = None; continue
        res["codes"][c] = {"rows": s["rows"], "rows_with_payer": s["rows_with_payer"],
                           "neg_dollar": s["neg_dollar"], "neg_pct_or_algo_only": s["neg_pct_or_algo_only"],
                           "n_payers": len(s["payers"]), "settings": dict(s["settings"]),
                           "billing_class": dict(s["billing_class"]), "code_types": dict(s["code_types"])}
    print(json.dumps(res))


if __name__ == "__main__":
    main()
