#!/usr/bin/env python3
"""DRAM bandwidth and aggregate instruction throughput of the spreading stage vs thread count.

Data: scaling.csv -- the reference transform (2D type-1 double precision, M = 33,554,432,
5793^2 modes, tol = 1e-6, library defaults of the instrumented build: sigma = 1.15, ns = 12,
bins 16x4, S_max = 1e5), median of three runs per thread count. Bandwidth is the DRAM read +
write traffic counted by the memory controllers (uncore IMC CAS counts, 64 B each) over the
wall time of the spreading loop; IPC x threads is the per-thread instructions / cycles of the
gather, spread and add steps (core counters read inside each thread), times the thread count.

Writes scaling.{pdf,png} next to this script.
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
BW, IPC, MARK = "#2a78d6", "#f0a202", "0.35"


def main():
    rows = list(csv.DictReader(open(HERE / "scaling.csv")))
    t = [int(r["threads"]) for r in rows]
    bw = [float(r["bandwidth_GBs"]) for r in rows]
    agg = [float(r["ipc_x_threads"]) for r in rows]
    core = [x for x in t if x <= 20]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 5.4), sharex=True)
    a1.plot(t, bw, "-o", color=BW, lw=2, ms=6, zorder=3)
    a1.set_ylabel("DRAM bandwidth [GB/s]")
    a1.set_ylim(0, 35)

    a2.plot(t, agg, "-o", color=IPC, lw=2, ms=6, zorder=3)
    a2.plot(core, [agg[0] * x for x in core], ls=":", color="0.45", lw=1.2, zorder=2)
    a2.text(5.2, 10.6, "linear scaling\nof one thread", ha="center", fontsize=8.5, color="0.35")
    a2.set_ylabel("IPC × threads")
    a2.set_ylim(0, 13)
    a2.set_xlabel("threads")

    for ax in (a1, a2):
        ax.axvline(10, color=MARK, ls="--", lw=1.1, zorder=1)
        ax.axvspan(20, 41, color="0.92", zorder=0)
        ax.grid(True, ls=":", lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)
        ax.set_xlim(0, 41)
    a1.annotate("bandwidth saturates", (10, 26), textcoords="offset points", xytext=(6, -14),
                fontsize=8.5, color=MARK)
    a1.annotate("2 threads per core", (30.5, 4), ha="center", fontsize=8.5, color="0.35")
    a2.set_xticks([1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 40])
    fig.tight_layout()
    fig.savefig(HERE / "scaling.pdf", bbox_inches="tight")
    fig.savefig(HERE / "scaling.png", dpi=200, bbox_inches="tight")


if __name__ == "__main__":
    main()
