#!/usr/bin/env python3
"""Grid of S_max sweeps: one axes per case, three step curves in each.

Reads smax_sweep.csv, produced by perftest/density_sweep.py on four exclusive
Ice Lake nodes. Every configuration is a 1 GiB transform, so M depends on the
dimension (44.7M in 1D, 33.6M in 2D, 26.8M in 3D) and the grid follows from the
density as N = M / rho. Runs use spreadinterponly, and the cycles spent in each
step are separated by symbol with perf. A "case" is one combination of
dimension, point density and thread count; within a case the subproblem size is
swept from 10^4 up to M/nthr, and the cycles spent gathering, spreading and
adding are recorded separately.

Rows of the grid are densities, columns are (dimension, thread count), so
reading down a column shows how density changes the balance at fixed geometry
and reading across a row shows how dimension and thread count change it at
fixed density.

Every panel shares a log x axis. The y axis is per-panel, because cycle counts
differ by two orders of magnitude between the single-threaded and all-thread
cases and a shared scale would flatten most of the grid; the point of the
figure is the shape of each curve and where its minimum falls, not the
magnitudes across panels.

Usage:
    python3 plot_smax_sweep.py [--csv smax_sweep.csv] [--out smax_sweep.png]
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

GATHER, SPREAD, ADD = "#2a78d6", "#eb6834", "#1baf7a"
STEPS = (("gather_cycles", GATHER, "gathering"),
         ("spread_cycles", SPREAD, "spreading"),
         ("add_cycles", ADD, "adding"))
# 8-thread runs are in the CSV but not drawn: they sit between the two limits
# and add a column without adding an argument
THR_ORDER = {"1": 0, "all": 1}
SKIP_THREADS = {"8"}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path,
                    default=Path(__file__).resolve().parent / "smax_sweep.csv")
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parent / "smax_sweep.pdf")
    args = ap.parse_args()

    rows = [r for r in csv.DictReader(open(args.csv))
            if r["nthreads"] not in SKIP_THREADS]
    cases = defaultdict(list)
    for r in rows:
        cases[(int(r["dim"]), r["nthreads"], float(r["density"]))].append(r)
    for v in cases.values():
        v.sort(key=lambda r: int(r["max_sp"]))

    densities = sorted({k[2] for k in cases})
    cols = sorted({(k[0], k[1]) for k in cases}, key=lambda t: (t[0], THR_ORDER[t[1]]))

    fig, axes = plt.subplots(len(densities), len(cols),
                             figsize=(2.5 * len(cols), 2.1 * len(densities)),
                             squeeze=False)

    for i, rho in enumerate(densities):
        for j, (dim, thr) in enumerate(cols):
            ax = axes[i][j]
            pts = cases.get((dim, thr, rho), [])
            for key, c, _ in STEPS:
                if not pts:
                    continue
                ax.plot([int(p["max_sp"]) for p in pts],
                        [float(p[key]) for p in pts],
                        "-o", ms=2.5, lw=1.3, color=c)
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.tick_params(labelsize=6)
            ax.grid(True, ls=":", lw=0.5, alpha=0.6)
            ax.set_axisbelow(True)
            # every panel names all three parameters: with 81 axes a reader
            # should not have to count rows and columns to place one
            ax.set_title(f"{dim}D  $\\rho$={rho:g}  {thr} thr", fontsize=7.5)
            if j == 0:
                ax.set_ylabel("cycles", fontsize=7)
            if i == len(densities) - 1:
                ax.set_xlabel(r"$S_{\max}$", fontsize=7)

    # framed and oversized: against a grid of 81 panels a thin unframed legend
    # at the top reads as part of the title and gets missed
    handles = [Line2D([], [], color=c, lw=4, marker="o", ms=6, label=lab)
               for _, c, lab in STEPS]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=True,
               fancybox=False, edgecolor="0.3", framealpha=1.0,
               fontsize=13, handlelength=2.5, borderpad=0.8, columnspacing=2.5,
               bbox_to_anchor=(0.5, 1.002))
    fig.suptitle("Cycles per spreading step against $S_{\\max}$, "
                 "1 GiB transforms", fontsize=12, y=1.013)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(args.out, bbox_inches="tight")
    fig.savefig(args.out.with_suffix(".png"), dpi=150, bbox_inches="tight")
    print(f"wrote {args.out} and .png  ({len(cases)} cases)")


if __name__ == "__main__":
    main()
