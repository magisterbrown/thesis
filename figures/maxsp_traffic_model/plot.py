#!/usr/bin/env python3
"""Spreading time against S_max next to the traffic model, both relative to the default S_max.

Data: traffic.csv -- the reference transform (2D type-1 double precision, M = 33,554,432,
5793^2 modes, tol = 1e-6, library defaults except S_max, bins 16x4) on 1, 10 and 20 threads
(one per core); built by perf/binsweep/make_traffic_csv.py. "time" is the measured wall time of
the spreading loop; "model" is the sum of Equations spread_reads and spread_writes (fitted ramp ends:
h_sub from C3/2 to 2 C3, h_buf from C2 to 1.5 C3) at the run's own fine grid and kernel width.
Both are divided by their value at the default S_max = min(1e5, M/n_thr).

Writes traffic.{pdf,png} next to this script.
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
    R = list(csv.DictReader(open(HERE / "traffic.csv")))
    fig, axes = plt.subplots(1, 3, figsize=(8.6, 3.2), sharey=True)
    for ax, t in zip(axes, THREADS):
        rs = [r for r in R if int(r["threads"]) == t]
        sp = [int(r["s_max"]) for r in rs]
        dflt = sp.index(min(100000, 33554432 // t))
        time = [float(r["spread_ms"]) for r in rs]
        model = [float(r["model_reads"]) + float(r["model_writes"]) for r in rs]
        ax.plot(sp, [m / model[dflt] for m in model], "--s", color=MODEL, lw=2, ms=4, label="model traffic", zorder=3)
        ax.plot(sp, [x / time[dflt] for x in time], "-o", color=TIME, lw=2, ms=4, label="spreading time", zorder=4)
        ax.axvline(sp[dflt], color="0.35", ls=":", lw=1.1, zorder=1)
        ax.axhline(1, color="0.6", lw=0.8, zorder=1)
        ax.set_title(f"{t} thread{'s' if t > 1 else ''}", fontsize=9.5)
        ax.set_xscale("log")
        ax.set_xlabel(r"$S_{\max}$")
        ax.grid(True, ls=":", lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)
    axes[0].set_ylim(0, 2)
    axes[0].set_ylabel("relative to default $S_{\\max}$")
    axes[0].legend(fontsize=8.5, loc="upper right", framealpha=0.95)
    fig.tight_layout()
    fig.savefig(HERE / "traffic.pdf", bbox_inches="tight")
    fig.savefig(HERE / "traffic.png", dpi=200, bbox_inches="tight")

if __name__ == "__main__":
    main()
