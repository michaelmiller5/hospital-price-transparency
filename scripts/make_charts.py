"""Static charts for the README (images/*.png).

Run from the repository root:  python scripts/make_charts.py
"""
from pathlib import Path

import duckdb
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"
FIXED, PCT = "#2a78d6", "#eb6834"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
ORDER = ["crouse", "st_josephs", "upstate", "strong", "highland"]
SHORT = {"crouse": "Crouse\nSyracuse", "st_josephs": "St. Joseph's\nSyracuse", "upstate": "Upstate\nSyracuse",
         "strong": "Strong Memorial\nRochester", "highland": "Highland\nRochester"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": INK, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
})


def money(v, _=None):
    return f"${v/1000:,.0f}K" if v >= 1000 else f"${v:,.0f}"


def style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, linewidth=1)
    ax.set_axisbelow(True)


def mri_strip(con):
    df = con.execute("""SELECT hospital_key, price, pct_of_charges FROM contract_prices
                        WHERE procedure_code = '70551' AND plan_type = 'Commercial'""").df()
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
    offs = np.array([0, -0.12, 0.12, -0.24, 0.24, -0.06, 0.06, -0.18, 0.18])
    for i, h in enumerate(ORDER):
        g = df[df.hospital_key == h].sort_values("price").reset_index(drop=True)
        y = len(ORDER) - 1 - i + offs[np.arange(len(g)) % len(offs)]
        ax.scatter(g.price, y, s=46, c=np.where(g.pct_of_charges, PCT, FIXED),
                   edgecolors=SURFACE, linewidths=1.5, zorder=3)
        med = g.price.median()
        ax.plot([med, med], [len(ORDER) - 1 - i - 0.32, len(ORDER) - 1 - i + 0.32], color=INK, lw=2, zorder=4)
        ax.text(9800, len(ORDER) - 1 - i, f"median ${med:,.0f}",
                va="center", ha="left", color=INK2, fontsize=10)
    ax.set_xscale("log")
    ax.set_xlim(250, 9500)
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    ax.xaxis.set_major_formatter(FuncFormatter(money))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_yticks(range(len(ORDER)))
    ax.set_yticklabels([SHORT[h] for h in reversed(ORDER)])
    style(ax)
    ax.scatter([], [], s=46, c=FIXED, label="Fixed fee or case rate")
    ax.scatter([], [], s=46, c=PCT, label="Percent of hospital list price")
    ax.plot([], [], color=INK, lw=2, label="Hospital median")
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, -0.28), ncol=3, frameon=False, fontsize=10, labelcolor=INK2)
    fig.text(0.02, 0.95, "MRI brain without contrast: every commercial contract price, by hospital",
             color=INK, fontsize=13, fontweight="bold")
    fig.text(0.02, 0.895, "Each dot is one insurer plan. Log scale: equal spacing means equal multiples.",
             color=MUTED, fontsize=10)
    fig.subplots_adjust(left=0.17, right=0.86, top=0.83, bottom=0.2)
    fig.savefig(IMG / "mri_brain_commercial.png")
    plt.close(fig)


def pct_vs_fixed():
    gap = pd.read_csv(ROOT / "data" / "processed" / "analysis" / "02_pct_of_charges_gap.csv", dtype={"procedure_code": str})
    labels = {"70450": "CT head", "70551": "MRI brain", "72148": "MRI lower back", "73721": "MRI knee",
              "74177": "CT abdomen/pelvis", "77067": "Screening mammogram", "43239": "Upper GI endoscopy"}
    gap["name"] = gap.procedure_code.map(labels) + np.where(gap.hospital_name.str.startswith("Upstate"),
                                                           " (Upstate)", " (St. Joseph's)")
    gap = gap.sort_values("ratio").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
    for i, r in gap.iterrows():
        ax.plot([r.median_fixed, r.median_pct], [i, i], color=GRID, lw=3, zorder=1, solid_capstyle="round")
        ax.scatter(r.median_fixed, i, s=50, c=FIXED, edgecolors=SURFACE, linewidths=1.5, zorder=3)
        ax.scatter(r.median_pct, i, s=50, c=PCT, edgecolors=SURFACE, linewidths=1.5, zorder=3)
        ax.text(max(r.median_fixed, r.median_pct) * 1.12, i, f"{r.ratio:.1f}x", va="center", color=INK2, fontsize=10)
    ax.set_xscale("log")
    ax.set_xlim(120, 12000)
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    ax.xaxis.set_major_formatter(FuncFormatter(money))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_yticks(range(len(gap)))
    ax.set_yticklabels(gap.name, fontsize=10)
    style(ax)
    ax.scatter([], [], s=50, c=FIXED, label="Median fixed-fee contract")
    ax.scatter([], [], s=50, c=PCT, label="Median percent-of-list-price contract")
    ax.legend(loc="lower center", bbox_to_anchor=(0.42, -0.2), ncol=2, frameon=False, fontsize=10, labelcolor=INK2)
    fig.text(0.02, 0.95, "Same hospital, same procedure: percent-of-list-price vs fixed-fee contracts",
             color=INK, fontsize=13, fontweight="bold")
    fig.text(0.02, 0.905, "Commercial insurance. Percent-of-list-price was higher in 11 of 12 comparisons. Log scale.",
             color=MUTED, fontsize=10)
    fig.subplots_adjust(left=0.29, right=0.95, top=0.85, bottom=0.15)
    fig.savefig(IMG / "pct_vs_fixed.png")
    plt.close(fig)


def main():
    IMG.mkdir(exist_ok=True)
    con = duckdb.connect(str(ROOT / "data" / "processed" / "hospital_prices.duckdb"), read_only=True)
    mri_strip(con)
    pct_vs_fixed()
    print("wrote images/mri_brain_commercial.png and images/pct_vs_fixed.png")


if __name__ == "__main__":
    main()
