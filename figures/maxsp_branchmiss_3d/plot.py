#!/usr/bin/env python3
import pathlib

import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent

DATA = [
    (100000, 16565009, 18.58e6),
    (200000, 14415661, 20.40e6),
    (350000, 13953232, 20.46e6),
    (500000, 13109364, 20.49e6),
    (650000, 10099818, 21.18e6),
    (843909, 9440831, 22.17e6),
]

x = [row[0] for row in DATA]
misses = [row[1] / 1e6 for row in DATA]  # millions
nupts = [row[2] / 1e6 for row in DATA]  # millions

fig, ax1 = plt.subplots(figsize=(6.5, 4.2))

color1 = "#c9622a"
ax1.set_xlabel(r"$S_{\max}$ (max subproblem size)")
ax1.set_ylabel("branch-misses (millions)", color=color1)
l1, = ax1.plot(x, misses, marker="o", color=color1, linewidth=1.5, markersize=5,
                label="branch-misses")
ax1.tick_params(axis="y", labelcolor=color1)
ax1.grid(True, linestyle=":", linewidth=0.6, alpha=0.7)

ax2 = ax1.twinx()
color2 = "#1f6f8b"
ax2.set_ylabel("amortized throughput (M nupts/s)", color=color2)
l2, = ax2.plot(x, nupts, marker="s", color=color2, linewidth=1.5, markersize=5,
                label="throughput")
ax2.tick_params(axis="y", labelcolor=color2)

ax1.set_title(r"$S_{\max}$ vs. branch-misses and throughput (illustrative trend)")
ax1.legend(handles=[l1, l2], loc="upper center")

fig.tight_layout()
fig.savefig(HERE / "branchmiss_throughput.pdf")
fig.savefig(HERE / "branchmiss_throughput.png", dpi=200)
print("wrote", HERE / "branchmiss_throughput.pdf", "and .png")
