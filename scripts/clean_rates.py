"""Turn the six filtered hospital extracts into one standardized long table.

Every source row (or, for the wide Crouse file, every payer/plan cell) becomes
one row in data/processed/rates_long.csv. Nothing is silently dropped: rows that
should not be used in the price comparison get an exclusion reason instead.

Usage (from the repository root):
    python scripts/clean_rates.py data/filtered data/processed
"""
import csv
import re
import sys
from pathlib import Path

import pandas as pd

csv.field_size_limit(1 << 30)

HOSPITALS = {
    # key: (filtered file, display name, city, health system, role)
    "crouse": ("crouse_filtered.csv", "Crouse Hospital", "Syracuse", "Crouse Health", "comparison"),
    "st_josephs": ("st_josephs_filtered.csv", "St. Joseph's Hospital Health Center", "Syracuse", "Trinity Health", "comparison"),
    "upstate": ("upstate_filtered.csv", "Upstate University Hospital", "Syracuse", "SUNY Upstate", "comparison"),
    "strong": ("strong_memorial_filtered.csv", "Strong Memorial Hospital", "Rochester", "URMC", "comparison"),
    "highland": ("highland_filtered.csv", "Highland Hospital", "Rochester", "URMC", "comparison"),
    "rochester_general": ("rochester_general_filtered.csv", "Rochester General Hospital", "Rochester", "Rochester Regional Health", "transparency_finding"),
}

PROCEDURES = {
    # code: (label, category, code type)
    "70551": ("MRI brain, no contrast", "Imaging", "CPT"),
    "73721": ("MRI knee/leg joint, no contrast", "Imaging", "CPT"),
    "72148": ("MRI lower back, no contrast", "Imaging", "CPT"),
    "70450": ("CT head, no contrast", "Imaging", "CPT"),
    "74177": ("CT abdomen and pelvis, with contrast", "Imaging", "CPT"),
    "77067": ("Screening mammogram", "Imaging", "CPT"),
    "45378": ("Colonoscopy, diagnostic", "Procedure", "CPT"),
    "43239": ("Upper GI endoscopy with biopsy", "Procedure", "CPT"),
    "27447": ("Knee replacement, outpatient", "Surgery", "CPT"),
    "DRG470": ("Hip or knee replacement, inpatient stay (MS-DRG 470)", "Surgery", "MS-DRG"),
}

# ---------------------------------------------------------------- helpers

def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("﻿", "")).strip()


def to_float(s):
    s = clean(s).replace("$", "").replace(",", "")
    try:
        return float(s) if s else None
    except ValueError:
        return None


def procedure_code(row, idx):
    """First CPT/HCPCS code in our list, or MS-DRG 470, across code|1..code|9."""
    for n in range(1, 10):
        c, t = f"code|{n}", f"code|{n}|type"
        if c not in idx or t not in idx:
            continue
        val, typ = clean(row[idx[c]]), clean(row[idx[t]]).upper()
        if typ in ("CPT", "HCPCS") and val in PROCEDURES:
            return val
        if typ == "MS-DRG" and val.lstrip("0") == "470":
            return "DRG470"
    return None


def read_filtered(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        next(r); next(r)
        header = [clean(h) for h in next(r)]
        rows = list(r)
    return header, rows


# ---------------------------------------------------------------- billing class

def billing_class(hosp, row, g):
    bc = g(row, "billing_class").lower()
    if bc:
        return bc
    if hosp in ("strong", "highland"):
        desc, notes = g(row, "description"), g(row, "additional_generic_notes")
        # URMC files mix physician fees into the hospital file. "PR" and "CHG"
        # lines carry physician/advanced-practice-provider tier notes.
        if desc.startswith(("PR ", "CHG ")) or re.search(r"\b(Physician|APP)\b", notes):
            return "professional"
        return "facility"
    if hosp == "crouse":
        return "facility"  # Crouse lists hospital (facility) charges only
    return "unknown"


# ---------------------------------------------------------------- payer normalization

INSURERS = [
    (r"\bMVP\b", "MVP Health Care"),
    (r"EXCELLUS|UNIVERA|MEDICARE BLUE CHOICE|HOSPITAL BLUE", "Excellus BCBS"),
    (r"AETNA", "Aetna"),
    (r"UNITED ?HEALTH|\bUHC\b|\bUMR\b", "UnitedHealthcare"),
    (r"CIGNA|EVERNORTH", "Cigna"),
    (r"FIDELIS", "Fidelis Care"),
    (r"HIGHMARK|BC/BS OF WESTERN NY|BCBS WNY", "Highmark BCBS"),
    (r"AMERIGROUP", "Amerigroup"),
    (r"INDEPENDENT HEALTH", "Independent Health"),
    (r"CDPHP|CAPITAL DISTRICT", "CDPHP"),
    (r"HUMANA", "Humana"),
    (r"MOLINA", "Molina"),
    (r"EMBLEM|\bGHI\b", "EmblemHealth"),
    (r"HEALTHFIRST", "Healthfirst"),
    (r"WELLCARE", "WellCare"),
    (r"MARTIN'?S POINT", "Martin's Point"),
    (r"BRIGHTON", "Brighton Health Plan"),
    (r"MYCOMPASS", "MyCompass"),
    (r"NASCENTIA", "Nascentia"),
    (r"MULTIPLAN", "MultiPlan"),
    (r"MAGNACARE", "MagnaCare"),
    (r"POMCO", "POMCO"),
    (r"FIRST HEALTH|COVENTRY", "First Health network"),
    (r"ICIRCLE", "iCircle"),
    (r"ELDERPLAN", "Elderplan"),
    (r"MEDIGOLD", "MediGold"),
    (r"TRICARE|CHAMPUS", "TRICARE"),
    (r"OPTUM", "Optum"),
]

PLAN_TYPES = [
    # Order matters: the first pattern that matches wins.
    (r"TRICARE|CHAMPUS|US FAMILY PLAN|^MARTINS POINT$", "Military (TRICARE)"),  # St. Joseph's bare plan: payer is US Family Health Plan
    (r"WORKERS COMP|NO.?FAULT|CORRECTIONAL", "Other"),
    (r"MEDICARE|MEDIGOLD|DSNP|ELDERPLAN", "Medicare Advantage"),
    (r"MEDICAID|CHILD HEALTH|\bHARP\b|\bCHP\b|ESSENTIAL|\bESS\b|OPTION|GOVT PROGRAMS|AMERIGROUP",
     "Medicaid / Essential Plan"),
    (r"METAL|\bQHP\b|\bEPP\b|HEALTH BENEFIT EXCHANGE", "Individual / Exchange"),
    (r"GROUP", "Commercial"),
    (r"EXCHANGE|INDIVIDUAL|STUDENT", "Individual / Exchange"),
]

BEHAVIORAL = r"BEHAVIORAL|EVERNORTH|^MH |\bMH CARELON|CARELON|BEACON"


def contract_text(hosp, payer, plan):
    # St. Joseph's lists every out-of-area Blue plan as the payer while the
    # contract that sets the rate is in plan_name (e.g. payer "BLUE CROSS - ND",
    # plan "EXCELLUS BCBS"). Use plan_name there; payer + plan elsewhere.
    if hosp == "st_josephs" and plan:
        return plan.upper()
    return f"{payer} | {plan}".upper()


def insurer_of(text, payer, hosp):
    # Match on the payer name first (a Cigna payer can list an MVP plan in the
    # MVP-Cigna partnership), then on the full contract text.
    first = text if hosp == "st_josephs" else clean(payer).upper()
    for candidate in (first, text):
        for pat, name in INSURERS:
            if re.search(pat, candidate):
                return name
    return clean(payer).title() or "Unknown"


def plan_type_of(text):
    for pat, name in PLAN_TYPES:
        if re.search(pat, text):
            return name
    return "Commercial"


# ---------------------------------------------------------------- main

def long_rows(hosp, header, rows):
    idx = {h: i for i, h in enumerate(header)}
    g = lambda row, k: clean(row[idx[k]]) if k in idx and idx[k] < len(row) else ""
    tall = "payer_name" in idx
    if not tall:  # wide: one column group per payer|plan
        pairs = []
        for h in header:
            p = h.split("|")
            if h.startswith("standard_charge|") and len(p) == 4 and p[3] == "negotiated_dollar":
                pairs.append((p[1], p[2]))
    for i, row in enumerate(rows, start=4):  # line 4 = first data line in filtered file
        code = procedure_code(row, idx)
        if code is None:
            continue
        desc = g(row, "description")
        modifiers = g(row, "modifiers")
        if hosp == "st_josephs" and "|" in desc:  # St. Joseph's appends modifier text to the description
            modifiers = modifiers or desc.split("|", 1)[1]
        base = {
            "hospital_key": hosp, "procedure_code": code, "description": desc,
            "setting": g(row, "setting").lower(), "billing_class": billing_class(hosp, row, g),
            "modifiers": modifiers, "gross_charge": to_float(g(row, "standard_charge|gross")),
            "cash_price": to_float(g(row, "standard_charge|discounted_cash")),
            "source_file": HOSPITALS[hosp][0], "source_line": i,
            # Strong and Highland publish two facility rate lists for some services:
            # CPT lines tagged with an APC group note, and chargemaster lines.
            "rate_layer": ("apc_line" if g(row, "additional_generic_notes").startswith("APC") else "chargemaster_line")
                          if hosp in ("strong", "highland") else "single",
        }
        if tall:
            items = [(g(row, "payer_name"), g(row, "plan_name"),
                      g(row, "standard_charge|negotiated_dollar"), g(row, "standard_charge|negotiated_percentage"),
                      g(row, "standard_charge|negotiated_algorithm"), g(row, "standard_charge|methodology"),
                      g(row, "additional_generic_notes"))]
        else:
            items = []
            for payer, plan in pairs:
                k = lambda f: g(row, f"standard_charge|{payer}|{plan}|{f}")
                items.append((clean(payer), clean(plan), k("negotiated_dollar"), k("negotiated_percentage"),
                              k("negotiated_algorithm"), k("methodology"),
                              g(row, f"additional_payer_notes|{payer}|{plan}")))
        for payer, plan, dollar, pct, algo, meth, notes in items:
            if not tall and not (dollar or pct or algo):
                continue  # empty wide cell: this payer has no rate on this line
            text = contract_text(hosp, payer, plan)
            yield {**base, "payer_raw": payer, "plan_raw": plan,
                   "insurer": insurer_of(text, payer, hosp) if payer else "",
                   "plan_type": plan_type_of(text) if payer else "",
                   "negotiated_dollar": to_float(dollar), "negotiated_percentage": to_float(pct),
                   "has_algorithm": bool(algo), "methodology": meth.lower(), "notes": notes,
                   "behavioral_contract": bool(re.search(BEHAVIORAL, f"{payer} | {plan}".upper()))}


def exclusion_reason(r):
    """First reason a row is not usable in the head-to-head comparison ('' = usable)."""
    if HOSPITALS[r["hospital_key"]][4] != "comparison":
        return "hospital is the transparency-gap finding, not in head-to-head"
    if not r["payer_raw"]:
        return "no payer (gross or cash price line)"
    if r["billing_class"] != "facility":
        return "professional (physician) fee, not hospital facility fee"
    if r["modifiers"]:
        return "billing modifier variant, not the base service"
    want = ("inpatient", "both") if r["procedure_code"] == "DRG470" else ("outpatient", "both")
    if r["setting"] not in want:
        return "care setting does not match the procedure definition"
    if r["behavioral_contract"]:
        return "behavioral-health carve-out contract"
    if pd.isna(r["negotiated_dollar"]):
        return "no dollar amount (percentage or formula only)"
    return ""


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    recs = []
    for hosp, (fname, *_rest) in HOSPITALS.items():
        header, rows = read_filtered(src / fname)
        recs.extend(long_rows(hosp, header, rows))
    df = pd.DataFrame(recs)
    df["exclusion_reason"] = df.apply(exclusion_reason, axis=1)

    # Exact duplicates of a usable rate (same hospital, procedure, contract and dollar
    # amount listed on several lines) are marked so each contract price counts once.
    usable = df["exclusion_reason"] == ""
    # St. Joseph's: payer_raw varies across out-of-area Blue plans that share one
    # contract, so the contract is identified by plan_name there.
    sj = df["hospital_key"] == "st_josephs"
    df["contract_key"] = (df["payer_raw"] + " | " + df["plan_raw"]).where(~sj, df["plan_raw"])
    keys = ["hospital_key", "procedure_code", "contract_key", "negotiated_dollar"]
    dup_idx = df[usable].index[df[usable].duplicated(subset=keys, keep="first")]
    df.loc[dup_idx, "exclusion_reason"] = "duplicate of a rate already counted"

    hosp_df = pd.DataFrame([{"hospital_key": k, "hospital_name": v[1], "city": v[2], "health_system": v[3],
                             "role": v[4], "source_file": v[0]} for k, v in HOSPITALS.items()])
    proc_df = pd.DataFrame([{"procedure_code": k, "label": v[0], "category": v[1], "code_type": v[2]}
                            for k, v in PROCEDURES.items()])
    df.to_csv(out / "rates_long.csv", index=False)
    hosp_df.to_csv(out / "hospitals.csv", index=False)
    proc_df.to_csv(out / "procedures.csv", index=False)
    log = df.groupby(["hospital_key", "exclusion_reason"]).size().rename("rows").reset_index()
    log.to_csv(out / "cleaning_log.csv", index=False)
    print(log.to_string())


if __name__ == "__main__":
    main()
