#!/usr/bin/env python3
"""Plot add_wrapped_subgrid cycle count vs. max_sp_size (S_max).

Data: 2D type-1 double-precision transform, ~500 MiB of nonuniform-point
data (N1=N2=4048, M=16,386,304, density~1), multithreaded, measured with
`perf record -e cycles` on the host machine. Each point is a single run.
"""
import csv
import pathlib

import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent

x, y = [], []
with open(HERE / "wrapped_cycles.csv") as f:
    for row in csv.DictReader(f):
        x.append(int(row["max_sp_size"]))
        y.append(float(row["wrapped_cycles"]) / 1e9)  # billions of cycles

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(x, y, marker="o", color="#1f6f8b", linewidth=1.5, markersize=5)
ax.set_xscale("log")
ax.set_xlabel(r"$S_{\max}$ (max subproblem size)")
ax.set_ylabel("add_wrapped_subgrid cycles (billions)")
ax.grid(True, which="both", linestyle=":", linewidth=0.6, alpha=0.7)

fig.tight_layout()
fig.savefig(HERE / "wrapped_cycles.pdf")
fig.savefig(HERE / "wrapped_cycles.png", dpi=200)
print("wrote", HERE / "wrapped_cycles.pdf", "and .png")
