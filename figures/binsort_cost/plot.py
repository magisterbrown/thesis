#!/usr/bin/env python3
"""Bin sort cost against the size of the count array it histograms into.

Reads binsort_cost.csv: one row per bin shape from a 2D, 1 GiB, unit-density
transform on 64 threads, with FINUFFT's own `sorted` timer for the type-1
setpts and the cycles perf attributes to bin_sort.

The sort makes two passes over the points and touches nothing else but a
per-thread array of nbins counters, so its cost is set by whether that array
stays in cache rather than by how many points there are. Plotting time against
the array size puts the cache levels on the x axis, where the L1d line marks
where the curve reaches its floor.

Shapes of very different aspect ratio are drawn as open markers. They land on
the same curve as the 4:1 family, which is the evidence that only the number of
bins matters and not how the bins are shaped.

Usage:
    python3 plot.py
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
SORT, MUTED = "#7b3fb5", "#52514e"
L1D, L2 = 48 * 1024, 1.25 * 2**20      # Ice Lake SP, per core
FAMILY = {(4,1),(8,2),(16,4),(32,8),(48,12),(64,16),(96,24),(128,32),
          (192,48),(256,64),(384,96),(512,128),(768,192),(1024,256)}
# label offsets are per point: the curve is steep at one end and flat at
# the other, so a single offset would collide somewhere
LABEL = {(4,1): (-8, 4, "right"), (16,4): (8, -2, "left"),
         (64,16): (8, -2, "left"), (96,24): (6, 6, "left"),
         (1024,256): (0, -14, "center")}


def main():
    rows = list(csv.DictReader(open(HERE / "binsort_cost.csv")))
    for r in rows:
        r["k"] = (int(r["bin_x"]), int(r["bin_y"]))
        r["x"] = int(r["count_bytes_per_thread"])
        r["y"] = float(r["sort_ms"])
    fam = sorted((r for r in rows if r["k"] in FAMILY), key=lambda r: r["x"])
    other = [r for r in rows if r["k"] not in FAMILY]

    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    for x, c, lab in ((L1D, "#c2410c", "L1d, 48 KB"), (L2, "#0e7490", "L2, 1.25 MiB")):
        ax.axvline(x, color=c, lw=1.2, ls="--", zorder=1)
        ax.annotate(lab, (x, 1.0), xycoords=("data", "axes fraction"),
                    textcoords="offset points", xytext=(4, -12),
                    fontsize=9, color=c)
    ax.plot([r["x"] for r in fam], [r["y"] for r in fam], "-o", lw=1.8, ms=5,
            color=SORT, zorder=4, label=r"bins $16n\times4n$")
    ax.plot([r["x"] for r in other], [r["y"] for r in other], "o", ms=6,
            mfc="none", mew=1.3, color=MUTED, zorder=3,
            label="other aspect ratios")
    for r in fam:
        if r["k"] in LABEL:
            dx, dy, ha = LABEL[r["k"]]
            ax.annotate(rf'${r["k"][0]}\times{r["k"][1]}$', (r["x"], r["y"]),
                        textcoords="offset points", xytext=(dx, dy), ha=ha,
                        fontsize=8.5, color=SORT, zorder=6)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(3.5e2, 9e7)          # room for the end labels
    ax.set_ylim(12, 460)
    ax.set_xlabel("count array per thread [bytes]")
    ax.set_ylabel("sort time [ms]")
    ax.legend(fontsize=9, framealpha=0.95, loc="upper left")
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(HERE / "binsort_cost.pdf", bbox_inches="tight")
    fig.savefig(HERE / "binsort_cost.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "binsort_cost.pdf", "and .png")


if __name__ == "__main__":
    main()
