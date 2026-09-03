#!/usr/bin/env python3
"""Plot gathering and add_wrapped_subgrid cost vs. max_sp_size (S_max),
at low density.

Same transform as figures/maxsp_gather_vs_add (2D type-1 double-precision,
M=33,554,432, bin sizes 16x4, 64 threads on an Ice Lake node, spreading phase
isolated) but on a 16384^2 grid, giving density 0.125 instead of 16. Symbol
costs attributed with `perf record -e cycles`; each point is the mean of three
runs with different point-generation seeds.
"""
import csv
import pathlib

import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, FuncFormatter

HERE = pathlib.Path(__file__).parent
GATHER, ADDWR = "#2a78d6", "#eb6834"

cols = {k: [] for k in ("max_sp", "spread_ms", "gather_ms", "add_wrapped_ms")}
with open(HERE / "gather_vs_add_lowdensity.csv") as f:
    for row in csv.DictReader(f):
        for k in cols:
            cols[k].append(float(row[k]))
S = cols["max_sp"]

fig, ax = plt.subplots(1, 1, figsize=(10.5, 4.0))

ax.plot(S, cols["gather_ms"], color=GATHER, lw=1.6, marker="o", ms=4.5,
        zorder=3, label="gathering")
ax.plot(S, cols["add_wrapped_ms"], color=ADDWR, lw=1.6, marker="o", ms=4.5,
        zorder=3, label="add_wrapped_subgrid")
ax.set_ylabel("ms per spreading call")
ax.set_title("Per-step cost, density 0.125", loc="left", fontsize=11)
ax.legend(frameon=False, fontsize=9.5, loc="upper right",
          bbox_to_anchor=(0.98, 0.97))

ax.set_xscale("log")
ax.set_xlabel(r"$S_{\max}$ (max subproblem size)")
ax.grid(True, which="major", linestyle=":", linewidth=0.6, alpha=0.7)
ax.set_axisbelow(True)
ax.xaxis.set_major_locator(LogLocator(base=10))
ax.xaxis.set_major_formatter(FuncFormatter(
        lambda v, _: f"{int(v/1000)}k" if v >= 1000 else str(int(v))))
ax.set_ylim(bottom=0)

fig.tight_layout()
fig.savefig(HERE / "gather_vs_add_lowdensity.pdf")
fig.savefig(HERE / "gather_vs_add_lowdensity.png", dpi=200)
print("wrote", HERE / "gather_vs_add_lowdensity.pdf", "and .png")
