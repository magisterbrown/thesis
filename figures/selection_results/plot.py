#!/usr/bin/env python3
"""The three selection tables of Chapter 6 drawn as grouped bars.

Data: data.csv, transcribed from the tables. Each row is a class of transform,
each bar one column of the table: three thread counts with uniformly
distributed points, and twenty threads with exponentially distributed ones.
Values are ratios against the library defaults, so the line at one separates a
gain from a loss, and the aggregate over all 54 transforms is set apart at the
bottom.

Writes selection_{speedup,work,sp_work}.{pdf,png} next to this script.
"""
import csv
import pathlib
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).parent
COLS = (("uniform_20", "#2a78d6", "uniform, 20 threads"),
        ("uniform_10", "#6fa8e8", "uniform, 10 threads"),
        ("uniform_1", "#b9d4f5", "uniform, 1 thread"),
        ("exponential_20", "#f0a202", "exponential, 20 threads"))
TITLES = {
    "speedup": ("Wall-clock speed-up of the bin sort and spreading stage",
                "speed-up over the library defaults"),
    "work": ("Throughput of the spreading stage improvement",
             "improvement over the library defaults"),
    "sp_work": (r"Throughput of the spreading stage improvement, $S_{\max}$ only",
                "improvement over the library defaults"),
    "sp": (r"Wall-clock speed-up of the bin sort and spreading stage, $S_{\max}$ only",
           "speed-up over the library defaults"),
}


def main():
    tables = defaultdict(list)
    for r in csv.DictReader(open(HERE / "data.csv")):
        tables[r["table"]].append(r)

    for name, rows in tables.items():
        labels = [r["row"] for r in rows]
        y = np.arange(len(rows), dtype=float)
        y[-1] += 0.55                       # set the aggregate apart
        h = 0.19
        fig, ax = plt.subplots(figsize=(7.6, 4.4))
        for k, (key, colour, lab) in enumerate(COLS):
            vals = [float(r[key]) for r in rows]
            off = (1.5 - k) * h
            bars = ax.barh(y + off, vals, height=h, color=colour, label=lab,
                           zorder=3)
            for rect, v in zip(bars, vals):
                ax.annotate(f"{v:.2f}", (v, rect.get_y() + rect.get_height() / 2),
                            textcoords="offset points", xytext=(3, 0),
                            va="center", fontsize=6.5, color="0.25")
        ax.axvline(1.0, color="0.3", lw=1.2, zorder=4)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=9)
        ax.invert_yaxis()
        lo = min(float(r[k]) for r in rows for k, _, _ in COLS)
        hi = max(float(r[k]) for r in rows for k, _, _ in COLS)
        ax.set_xlim(min(0.85, lo - 0.05), hi * 1.08)
        title, xlabel = TITLES[name]
        ax.set_xlabel(xlabel)
        ax.set_title(title, loc="left", fontsize=10.5)
        ax.axhline(y[-1] - 0.42, color="0.6", lw=0.8, ls="--", zorder=2)
        ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.13),
                  ncol=4, frameon=False, handlelength=1.6, columnspacing=1.6)
        ax.grid(True, axis="x", ls=":", lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)
        fig.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(HERE / f"selection_{name}.{ext}", dpi=200,
                        bbox_inches="tight")
        plt.close(fig)
        print("wrote", HERE / f"selection_{name}.pdf", "and .png")


if __name__ == "__main__":
    main()
