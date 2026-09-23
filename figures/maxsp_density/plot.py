#!/usr/bin/env python3
"""Gathering against adding at low and high point density.

Data: maxsp_density.csv, a slice of the density sweep -- 3D type-1 double
precision, 1 GiB of nonuniform points, every thread of an Ice Lake node, with
S_max swept from 10^4 up to M/nthr. Three cases are shown: two densities at the far ends of the sweep on every
thread of the node, and a single-threaded run at unit density. The last isolates
the effect of S_max from thread contention, which is what makes gathering rise
in the first two.

The panels have independent y axes on purpose: adding costs two orders of
magnitude more cycles at the low density than at the high one, so a shared scale would flatten the right
panel entirely. What the figure is for is which of the two steps dominates and
whether they cross, not the absolute heights.

Writes maxsp_density.{pdf,png} next to this script.
"""
import csv
import pathlib
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
GATHER, ADD = "#2a78d6", "#1baf7a"


def main():
    rows = list(csv.DictReader(open(HERE / "maxsp_density.csv")))
    by = defaultdict(list)
    for r in rows:
        by[(float(r["density"]), r["nthreads"])].append(r)
    for v in by.values():
        v.sort(key=lambda r: int(r["max_sp"]))

    # keep the order the CSV was written in, which is the order of the argument
    seen, cases = set(), []
    for r in rows:
        k = (float(r["density"]), r["nthreads"])
        if k not in seen:
            seen.add(k); cases.append(k)

    fig, axes = plt.subplots(1, len(cases), figsize=(4.8 * len(cases), 4.0),
                             squeeze=False)

    for ax, (rho, thr) in zip(axes[0], cases):
        v = by[(rho, thr)]
        x = [int(r["max_sp"]) for r in v]
        ax.plot(x, [float(r["gather_cycles"]) / 1e9 for r in v], "-o", lw=1.8,
                ms=4, color=GATHER, label="gathering")
        ax.plot(x, [float(r["add_cycles"]) / 1e9 for r in v], "-o", lw=1.8, ms=4,
                color=ADD, label="adding")
        ax.set_xscale("log")
        ax.set_ylim(bottom=0)
        ax.set_xlabel(r"$S_{\max}$")
        ax.set_ylabel(r"cycles [$10^9$]")
        nthr = "all threads" if thr == "all" else f"{thr} thread"
        ax.set_title(rf"$\rho$ = {rho:g}, {nthr}", loc="left", fontsize=11)
        ax.legend(fontsize=9, framealpha=0.95)
        ax.grid(True, ls=":", lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(HERE / "maxsp_density.pdf", bbox_inches="tight")
    fig.savefig(HERE / "maxsp_density.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "maxsp_density.pdf", "and .png")


if __name__ == "__main__":
    main()
