#!/usr/bin/env python3
"""The two figures for the 2D, 1 GiB parameter search.

optuna_histogram_2d  distribution of measured times over the search trials,
                     with the library default marked.
importance_2d        functional ANOVA importance, in two panels: over all
                     trials, and over the trials with sorting enabled.

The second panel exists because spread_sort's own variance is so large that it
leaves every other parameter looking negligible; conditioning on sort=1 shows
how the remaining five rank against each other, which is the question the rest
of the thesis actually acts on.

Reads trials.csv (one row per trial), importance.csv and importance_sorted.csv,
all produced by perftest/optuna_binsize_2d_1gib.py.

Usage:
    python3 plot.py
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
BAR, BAR2, DEFAULT, BEST = "#2a78d6", "#7b3fb5", "#c2410c", "#1baf7a"
DEFAULT_S = 0.5087         # sigma=1.25, sort=1, bins 16x4, max_sp=100k;
                           # median of 5 runs on the same node
TIMEOUT_S = 8.0            # trials at the cap are censored, not measured
def label(p):
    # the shared "spread_" prefix costs width and says nothing
    return p.replace("spread_", "")


def read(name):
    return list(csv.DictReader(open(HERE / name)))


def histogram(ax, times):
    lo, hi = min(times), max(times)
    bins = np.logspace(np.log10(lo * 0.9), np.log10(hi * 1.1), 34)
    ax.hist(times, bins=bins, color=BAR, edgecolor="white", linewidth=0.5)
    # the two markers sit within 7% of each other, so the labels are stacked and
    # pushed to opposite sides rather than both hung off the line
    for x, c, lab, yf, dx, ha in (
            (min(times), BEST, f"best {min(times):.3f} s", 0.96, -5, "right"),
            (DEFAULT_S, DEFAULT, f"default {DEFAULT_S:.3f} s", 0.86, 5, "left")):
        ax.axvline(x, color=c, lw=1.6, ls="--", zorder=5)
        ax.annotate(lab, (x, yf), xycoords=("data", "axes fraction"),
                    textcoords="offset points", xytext=(dx, 0), ha=ha,
                    va="center", fontsize=8.5, color=c)
    ax.set_xscale("log")
    ax.set_xlabel("setpts + execute time [s]")
    ax.set_ylabel("trials")
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def bars(ax, rows, color, title):
    rows = sorted(rows, key=lambda r: float(r["importance"]))
    y = np.arange(len(rows))
    v = [100 * float(r["importance"]) for r in rows]
    ax.barh(y, v, color=color, height=0.68)
    ax.set_yticks(y)
    ax.set_yticklabels([label(r["param"]) for r in rows], fontsize=9)
    for i, val in enumerate(v):
        ax.annotate(f"{val:.1f}%", (val, i), textcoords="offset points",
                    xytext=(4, 0), va="center", fontsize=8.5)
    ax.set_xlim(0, max(v) * 1.18)
    ax.set_xlabel("share of variance [%]")
    ax.set_title(title, fontsize=10)
    ax.grid(True, axis="x", ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def main():
    plt.rcParams["text.usetex"] = False
    trials = read("trials.csv")
    times = [float(r["time_s"]) for r in trials]

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    histogram(ax, times)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(HERE / f"optuna_histogram_2d.{ext}",
                    dpi=200, bbox_inches="tight")

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.4))
    bars(axes[0], read("importance.csv"), BAR, "all trials")
    bars(axes[1], read("importance_sorted.csv"), BAR2,
         "trials with spread_sort = 1")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(HERE / f"importance_2d.{ext}", dpi=200, bbox_inches="tight")
    print(f"wrote optuna_histogram_2d and importance_2d ({len(trials)} trials)")


if __name__ == "__main__":
    main()
