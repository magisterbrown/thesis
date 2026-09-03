#!/usr/bin/env python3
"""Plot gathering and add_wrapped_subgrid cost vs. max_sp_size (S_max).

Data: 2D type-1 double-precision transform, 1 GiB of nonuniform-point data
(N1=N2=1448, M=33,554,432, density 16), bin sizes 16x4, 64 threads on an
Ice Lake node, spreading phase isolated (--spreadinterponly). Symbol costs
attributed with `perf record -e cycles`; each point is the mean of three
runs with different point-generation seeds.

This is the sweep behind Table 5.3, whose three columns are marked.
"""
import csv
import pathlib

import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, FuncFormatter

HERE = pathlib.Path(__file__).parent
GATHER, ADDWR, TOTAL, MARK = "#2a78d6", "#eb6834", "#4a3aa7", "#52514e"
TABLE_VALUES = {1024: "1{,}024", 2078: "2{,}078", 100000: "100{,}000"}

cols = {k: [] for k in ("max_sp", "spread_ms", "spread_sd", "gather_ms",
                        "gather_sd", "add_wrapped_ms", "add_wrapped_sd")}
with open(HERE / "gather_vs_add.csv") as f:
    for row in csv.DictReader(f):
        for k in cols:
            cols[k].append(float(row[k]))
S = cols["max_sp"]
best = S[min(range(len(S)), key=lambda i: cols["spread_ms"][i])]

fig, ax = plt.subplots(1, 1, figsize=(10.5, 4.0))

ax.plot(S, cols["gather_ms"], color=GATHER, lw=1.6, marker="o", ms=4.5,
        zorder=3, label="gathering")
ax.plot(S, cols["add_wrapped_ms"], color=ADDWR, lw=1.6, marker="o", ms=4.5,
        zorder=3, label="add_wrapped_subgrid")
ax.set_ylabel("ms per spreading call")
ax.set_title("Per-step cost", loc="left", fontsize=11)
ax.legend(frameon=False, fontsize=9.5, loc="upper left",
          bbox_to_anchor=(0.02, 0.97))

top = max(cols["spread_ms"]) * 1.16
ax.set_ylim(0, top)
ax.set_ylabel("ms per spreading call")
ax.set_title("Total spreading time", loc="left", fontsize=11)

ax.set_xscale("log")
ax.set_xlabel(r"$S_{\max}$ (max subproblem size)")
ax.grid(True, which="major", linestyle=":", linewidth=0.6, alpha=0.7)
ax.set_axisbelow(True)
ax.xaxis.set_major_locator(LogLocator(base=10))
ax.xaxis.set_major_formatter(FuncFormatter(
        lambda v, _: f"{int(v/1000)}k" if v >= 1000 else str(int(v))))
ax.set_ylim(bottom=0)


fig.tight_layout()
fig.savefig(HERE / "gather_vs_add.pdf")
fig.savefig(HERE / "gather_vs_add.png", dpi=200)
print("wrote", HERE / "gather_vs_add.pdf", "and .png")
