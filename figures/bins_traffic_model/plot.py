#!/usr/bin/env python3
"""Sort + spread time against the bin size next to the traffic model, both relative to the default bins.

Data: bins.csv -- the reference transform (2D type-1 double precision, M = 33,554,432,
5793^2 modes, tol = 1e-6, library defaults except the bins, S_max = min(1e5, M/n_thr)) on 1, 10 and
20 threads (one per core), bins in the 4:1 family 4x1 ... 512x128; built by
perf/binsweep/make_bins_csv.py. "time" is the measured wall time of the bin sort plus the spreading
loop; "model" is the sum of Equations sort_reads, sort_writes, spread_reads and spread_writes at the
run's own fine grid and kernel width. Both are divided by their value at the default 16x4 bins.

Writes bins.{pdf,png} next to this script.
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
TIME, MODEL = "#2a78d6", "#f0a202"
THREADS = (1, 10, 20)


def main():
    R = list(csv.DictReader(open(HERE / "bins.csv")))
    fig, axes = plt.subplots(1, 3, figsize=(8.6, 3.2), sharey=True)
    for ax, t in zip(axes, THREADS):
        rs = [r for r in R if int(r["threads"]) == t]
        area = [int(r["bx"]) * int(r["by"]) for r in rs]
        labels = [f"{r['bx']}×{r['by']}" for r in rs]
        dflt = labels.index("16×4")
        time = [float(r["sort_ms"]) + float(r["spread_ms"]) for r in rs]
        model = [float(r["model_sort_lines"]) + float(r["model_spread_lines"]) for r in rs]
        ax.plot(area, [m / model[dflt] for m in model], "--s", color=MODEL, lw=2, ms=4, label="model traffic", zorder=3)
        ax.plot(area, [x / time[dflt] for x in time], "-o", color=TIME, lw=2, ms=4, label="sort + spreading time", zorder=4)
        ax.axvline(area[dflt], color="0.35", ls=":", lw=1.1, zorder=1)
        ax.axhline(1, color="0.6", lw=0.8, zorder=1)
        ax.set_title(f"{t} thread{'s' if t > 1 else ''}", fontsize=9.5)
        ax.set_xscale("log")
        ax.set_xticks(area[::2], labels[::2], fontsize=7.5, rotation=30)
        ax.minorticks_off()
        ax.set_xlabel(r"bin size $b_x \times b_y$")
        ax.grid(True, ls=":", lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)
    axes[0].set_ylim(bottom=0)
    axes[0].set_ylabel("relative to default bins")
    axes[0].legend(fontsize=8.5, loc="upper center", framealpha=0.95)
    fig.tight_layout()
    fig.savefig(HERE / "bins.pdf", bbox_inches="tight")
    fig.savefig(HERE / "bins.png", dpi=200, bbox_inches="tight")


if __name__ == "__main__":
    main()
