#!/usr/bin/env python3
"""Gathering cycles against the two stall counters attributed to it.

Data: fbfull_xeon.csv -- 2D type-1 double precision, M = 33,554,432 on a
5793^2 grid, tol = 1e-6, sigma = 2, spreadinterponly=1, all 40 threads of the
Xeon E5-2698 v4.

  gathering cycles      from the timers inside the parallel region
  l1d_pend_miss.fb_full cycles in which a demand request was blocked because no
                        line-fill buffer was available
  cycle_activity.stalls_l2_miss
                        execution stalls while a demand load that missed L2 is
                        outstanding

All three are cycle counts summed over the threads, so they share one axis. The
vertical lines mark where the staging buffer of S_max points, at 32 bytes each,
fills a thread's share of the 256 KiB L2 (4096 points) and a whole core's
(8192 points).

Writes maxsp_fbfull_xeon.{pdf,png} next to this script.
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
GATHER, FB, L2 = "#2a78d6", "#e34948", "#f0a202"


def main():
    rows = sorted(csv.DictReader(open(HERE / "fbfull_xeon.csv")),
                  key=lambda r: int(r["max_sp"]))
    x = [int(r["max_sp"]) for r in rows]
    col = lambda k: [float(r[k]) / 1e9 for r in rows]

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    for key, c, lab in (("gather_cyc", GATHER, "gathering cycles"),
                        ("stalls_l2_gather", L2,
                         "cycle_activity.stalls_l2_miss"),
                        ("fb_full_gather", FB,
                         "l1d_pend_miss.fb_full")):
        ax.plot(x, col(key), "-o", lw=1.8, ms=4, color=c, label=lab)

    top = max(col("stalls_l2_gather"))
    for pts, lab in ((4096, "L2 share of a thread"),
                     (8192, "L2 of a core")):
        ax.axvline(pts, color="0.45", ls="--", lw=1.1, zorder=1)
        ax.annotate(lab, (pts, top * 0.55), rotation=90,
                    textcoords="offset points", xytext=(-5, 0), ha="center",
                    va="center", fontsize=8, color="0.35")

    ax.set_xscale("log")
    ax.set_xlabel(r"$S_{\max}$")
    ax.set_ylabel(r"cycles [$10^9$], attributed to gathering")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=9, loc="upper left", framealpha=0.95,
              prop={"family": "monospace", "size": 8.5})
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(HERE / "maxsp_fbfull_xeon.pdf", bbox_inches="tight")
    fig.savefig(HERE / "maxsp_fbfull_xeon.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "maxsp_fbfull_xeon.pdf", "and .png")


if __name__ == "__main__":
    main()
