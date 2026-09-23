#!/usr/bin/env python3
"""Total cycles of the three steps against S_max -- a scratch plot.

Sums the gathering, spreading and adding cycles of maxsp_steps.csv, the data
behind the cycles panel of the S_max figure, to show how much work the
spreading phase does in total as S_max changes. Not referenced by the thesis.

Writes maxsp_cycles_total.{pdf,png} next to this script.
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
TOTAL = "#6a3d9a"
KEYS = ("gather_cycles", "spread_cycles", "add_cycles")


def main():
    rows = list(csv.DictReader(open(HERE / "maxsp_steps.csv")))
    rows.sort(key=lambda r: int(r["max_sp"]))
    x = [int(r["max_sp"]) for r in rows]
    tot = [sum(float(r[k]) for k in KEYS) / 1e9 for r in rows]

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    ax.plot(x, tot, "-o", lw=1.8, ms=4, color=TOTAL,
            label="gathering + spreading + adding")
    for (xi, yi), dy, ha in (((x[0], tot[0]), -14, "left"),
                             ((x[-1], tot[-1]), 8, "right")):
        ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points",
                    xytext=(4 if ha == "left" else -4, dy), ha=ha, fontsize=9,
                    color=TOTAL)
    ax.set_xscale("log")
    ax.set_xlabel(r"$S_{\max}$")
    ax.set_ylabel(r"cycles [$10^9$], summed over threads")
    ax.set_ylim(bottom=0)
    ax.set_title("Total cycles of the spreading phase", loc="left", fontsize=11)
    ax.legend(fontsize=9, framealpha=0.95)
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(HERE / "maxsp_cycles_total.pdf", bbox_inches="tight")
    fig.savefig(HERE / "maxsp_cycles_total.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "maxsp_cycles_total.pdf", "and .png")
    for xi, yi in zip(x, tot):
        print(f"  S_max={xi:>7}  total={yi:7.2f} Gcyc")


if __name__ == "__main__":
    main()
