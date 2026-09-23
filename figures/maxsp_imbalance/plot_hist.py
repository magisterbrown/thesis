#!/usr/bin/env python3
"""Distribution of per-thread busy times at one value of S_max.

Same run as thread_busy.csv: 2D type-1 double precision, M = 33,554,432 on a
5793^2 grid, tol = 1e-6, sigma = 2, spreadinterponly=1, all 40 threads of the
Xeon E5-2698 v4. The points split into 64 subproblems, so 24 threads take two
and 16 take one, and the busy times fall into two groups rather than scattering
around a mean.

Writes thread_busy_hist.{pdf,png} next to this script.
"""
import csv
import pathlib
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).parent
ONE, TWO, LINE = "#2a78d6", "#f0a202", "#c3423f"


def main(tag="524288", title="64 subproblems over 40 threads"):
    rows = list(csv.DictReader(open(HERE / f"thread_busy_{tag}.csv")))
    busy = np.array([float(r["busy_ms"]) for r in rows])
    nsub = np.array([int(r["nsub"]) for r in rows])
    mx, mean = busy.max(), busy.mean()

    lo = 10 * np.floor(busy.min() / 10) - 10
    hi = 10 * np.ceil(busy.max() / 10) + 20
    bins = np.arange(lo, hi, 10)
    fig, ax = plt.subplots(1, 1, figsize=(7.4, 3.9))
    groups, colors, labels = [], [], []
    for k, c, name in ((1, ONE, "one subproblem"), (2, TWO, "two subproblems")):
        if (nsub == k).any():
            groups.append(busy[nsub == k])
            colors.append(c)
            labels.append(f"{name} ({(nsub == k).sum()} threads)")
    ax.hist(groups, bins=bins, stacked=True, color=colors, edgecolor="white",
            linewidth=0.5, zorder=3, label=labels)
    ax.axvline(mean, color="0.25", ls=":", lw=1.4, zorder=4)
    ax.axvline(mx, color=LINE, ls="--", lw=1.4, zorder=4)
    ax.annotate(f"mean {mean:.0f} ms", (mean, ax.get_ylim()[1] * 0.92),
                textcoords="offset points", xytext=(-5, 0), ha="right",
                fontsize=8.5, color="0.25")
    ax.annotate(f"slowest {mx:.0f} ms", (mx, ax.get_ylim()[1] * 0.92),
                textcoords="offset points", xytext=(-5, 0), ha="right",
                fontsize=8.5, color=LINE)
    ax.set_xlabel("busy time of a thread [ms]")
    ax.set_ylabel("threads")
    pretty = f"{int(tag):,}".replace(",", "{,}")
    ax.set_title(rf"$S_{{\max}} = {pretty}$: {title}", loc="left", fontsize=11)
    ax.legend(fontsize=9, loc="upper left", framealpha=0.95)
    ax.grid(True, axis="y", ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(HERE / f"thread_busy_hist_{tag}.pdf", bbox_inches="tight")
    fig.savefig(HERE / f"thread_busy_hist_{tag}.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / f"thread_busy_hist_{tag}.pdf", "and .png")
    if (nsub == 1).any():
        print(f"  one subproblem : n={int((nsub == 1).sum())} "
              f"mean={busy[nsub == 1].mean():.1f} ms")
    if (nsub == 2).any():
        print(f"  two subproblems: n={int((nsub == 2).sum())} "
              f"mean={busy[nsub == 2].mean():.1f} ms")
    print(f"  overall mean={mean:.1f}  max={mx:.1f}  "
          f"imbalance={1 - mean / mx:.3f}")


if __name__ == "__main__":
    main("524288", "64 subproblems over 40 threads")
    main("838861", "40 subproblems over 40 threads")
