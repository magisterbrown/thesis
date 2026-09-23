#!/usr/bin/env python3
"""Busy time of each thread at one subproblem size.

Data: thread_busy_524288.csv -- 2D type-1 double precision, M = 33,554,432 on
a 5793^2 grid (unit density), tol = 1e-6, sigma = 2, spreadinterponly=1, on all
40 threads. S_max = 524,288 divides the points into 64 subproblems, so 24
threads receive two and 16 receive one.

Each thread stops its own clock after its last subproblem (the omp for is
nowait), so the bars are busy time and exclude waiting at the barrier. The
phase cannot end before the tallest bar, so everything above a bar is idle.

Writes thread_busy.{pdf,png} next to this script.
"""
import csv
import pathlib
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
ONE, TWO, LINE = "#2a78d6", "#f0a202", "#c3423f"


def main(tag="524288"):
    rows = sorted(csv.DictReader(open(HERE / f"thread_busy_{tag}.csv")),
                  key=lambda r: int(r["thread"]))
    busy = [float(r["busy_ms"]) for r in rows]
    nsub = [int(r["nsub"]) for r in rows]
    mx, mean = max(busy), st.mean(busy)

    fig, ax = plt.subplots(1, 1, figsize=(7.6, 3.9))
    ax.bar(range(len(busy)), busy, width=0.82,
           color=[ONE if n == 1 else TWO for n in nsub], zorder=3)
    ax.axhline(mx, color=LINE, ls="--", lw=1.4, zorder=4)
    ax.axhline(mean, color="0.25", ls=":", lw=1.4, zorder=4)
    ax.annotate(f"slowest thread, {mx:.0f} ms", (len(busy) - 0.4, mx),
                textcoords="offset points", xytext=(0, 4), ha="right",
                fontsize=8.5, color=LINE)
    ax.annotate(f"mean {mean:.0f} ms", (len(busy) - 0.4, mean),
                textcoords="offset points", xytext=(0, -12), ha="right",
                fontsize=8.5, color="0.25")

    handles, labels = [], []
    for k, c, name in ((1, ONE, "one subproblem"), (2, TWO, "two subproblems")):
        if any(n == k for n in nsub):
            handles.append(plt.Rectangle((0, 0), 1, 1, color=c))
            labels.append(name)
    ax.legend(handles, labels, fontsize=9, loc="lower right", framealpha=0.95)
    ax.set_xlabel("thread")
    ax.set_ylabel("busy time [ms]")
    ax.set_xlim(-0.8, len(busy) - 0.2)
    ax.set_ylim(0, mx * 1.16)
    ax.grid(True, axis="y", ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(HERE / f"thread_busy_{tag}.pdf", bbox_inches="tight")
    fig.savefig(HERE / f"thread_busy_{tag}.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / f"thread_busy_{tag}.pdf", "and .png")
    print(f"  max {mx:.1f}  mean {mean:.1f}  min {min(busy):.1f}  "
          f"imbalance {1 - mean / mx:.3f}")


if __name__ == "__main__":
    main("524288")
    main("838861")
