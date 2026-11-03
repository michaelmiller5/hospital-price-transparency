"""Rebuild everything downstream of the filtered extracts, in order.

Run from the repository root:  python scripts/run_all.py
(The first step, scripts/extract_procedures.py, needs the raw hospital files in
data/raw/ and is run separately; see the README.)
"""
import subprocess
import sys

STEPS = [
    ["scripts/clean_rates.py", "data/filtered", "data/processed"],
    ["scripts/build_database.py"],
    ["scripts/analysis_stats.py"],
    ["scripts/build_dashboard.py"],
]

for step in STEPS:
    print(f"\n>> python {' '.join(step)}")
    subprocess.run([sys.executable, *step], check=True)
