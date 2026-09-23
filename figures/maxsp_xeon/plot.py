#!/usr/bin/env python3
"""The three steps, the phase time and the load imbalance against S_max.

Data: maxsp_xeon.csv, 2D type-1 double precision, M = 33,554,432 on a
5793^2 grid (unit density), tol = 1e-6, sigma = 2, all 40 threads of the
Xeon E5-2698 v4, spreadinterponly=1 so no FFT is involved.

  cycles      attributed to gathering, spreading and adding by perf, summed
              over threads. The gathering bucket is the body of the OpenMP
              region, so it also holds the subproblem loop and the subgrid
              allocation.
  busy time   measured inside the parallel region: each thread stops its own
              clock after its last subproblem (the omp for is nowait), so
              waiting at the barrier is excluded. The band is min..max over
              the 40 threads, the line is the mean, and the dashed line is
              the wall time of the whole phase.
  imbalance   1 - mean/max, the fraction of the phase an average thread
              spends idle. It peaks where the subproblems do not divide
              evenly over the threads (64 over 40) and collapses again at
              exactly one subproblem per thread.

Writes maxsp_xeon.{pdf,png} next to this script.
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
GATHER, SPREAD, ADD = "#2a78d6", "#f0a202", "#1baf7a"
TIME, IMB = "#444444", "#c3423f"


def main():
    rows = list(csv.DictReader(open(HERE / "maxsp_xeon.csv")))
    x = [int(r["max_sp"]) for r in rows]
    col = lambda k: [float(r[k]) for r in rows]

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.9))

    ax = axes[0]
    for k, c, lab in (("gather_gcyc", GATHER, "gathering"),
                      ("spread_gcyc", SPREAD, "spreading"),
                      ("add_gcyc", ADD, "adding")):
        ax.plot(x, col(k), "-o", lw=1.8, ms=4, color=c, label=lab)
    ax.set_ylabel(r"cycles [$10^9$], all threads")
    ax.set_title("cost of the three steps", loc="left", fontsize=11)
    ax.legend(fontsize=9, framealpha=0.95)

    ax = axes[1]
    ax.fill_between(x, col("min_ms"), col("max_ms"), color=TIME, alpha=0.18,
                    lw=0, label="per-thread min..max")
    ax.plot(x, col("mean_ms"), "-o", lw=1.8, ms=4, color=TIME,
            label="mean busy time")
    ax.plot(x, col("phase_ms"), "--s", lw=1.6, ms=4, color=IMB,
            label="phase wall time")
    ax.set_ylabel("time [ms]")
    ax.set_title("busy time per thread", loc="left", fontsize=11)
    ax.legend(fontsize=9, framealpha=0.95, loc="upper left")

    ax = axes[2]
    ax.plot(x, [100 * v for v in col("imbalance")], "-o", lw=1.8, ms=4, color=IMB)
    for xi, r in zip(x, rows):
        if int(r["nsub"]) in (64, 40):
            ax.annotate(f"{r['nsub']} subprobs\non 40 threads", (xi, 100 * float(r["imbalance"])),
                        textcoords="offset points", xytext=(-6, 10 if int(r["nsub"]) == 40 else 4),
                        ha="right", fontsize=8, color=IMB)
    ax.set_ylabel(r"idle share $1-\bar{t}/\max t$  [\%]".replace("\\%", "%"))
    ax.set_title("load imbalance", loc="left", fontsize=11)
    ax.set_ylim(bottom=0)

    for ax in axes:
        ax.set_xscale("log")
        ax.set_xlabel(r"$S_{\max}$")
        ax.grid(True, ls=":", lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(HERE / "maxsp_xeon.pdf", bbox_inches="tight")
    fig.savefig(HERE / "maxsp_xeon.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "maxsp_xeon.pdf", "and .png")


if __name__ == "__main__":
    main()
