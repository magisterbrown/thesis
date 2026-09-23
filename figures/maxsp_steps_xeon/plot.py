#!/usr/bin/env python3
"""The four steps of a subproblem against S_max, in time and in cycles.

Data: maxsp_steps_xeon.csv -- 2D type-1 double precision, M = 33,554,432 on a
5793^2 grid (unit density), tol = 1e-6, sigma = 2, spreadinterponly=1 so no FFT
is involved, on all 40 threads of the Xeon E5-2698 v4. Two repetitions per
point; the plotted value is their mean.

Unlike the earlier figures, neither panel is derived from a sampled symbol
distribution. Both come from timers placed inside the parallel region around
each step, read once per subproblem by the thread running it:

  gathering  the resizes and the copy of one subproblem's points out of the
             sorted arrays into the thread's buffers
  spreading  the spread_subproblem_Nd call
  adding     the add_wrapped_subgrid call
  freeing    the destruction of the thread's buffers when the parallel region
             closes, which releases up to 41 MB per thread

The time plot is the wall-clock time of the whole spreading phase, taken from
FINUFFT's own t1 fancy spread timer. The cycle plot breaks that phase into the
four steps above, in reference (TSC) cycles summed over all threads; cycles
count work performed and so exclude the idle time that imbalance creates.

Writes maxsp_steps_xeon_time.{pdf,png} and maxsp_steps_xeon_cycles.{pdf,png}.
"""
import collections
import csv
import pathlib
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
GATHER, SPREAD, ADD, FREE = "#2a78d6", "#f0a202", "#1baf7a", "#8e44ad"
TOTAL = "#4a4a4a"
PHASE = "#c3423f"
STEPS = (("gather", GATHER, "gathering"), ("spread", SPREAD, "spreading"),
         ("add", ADD, "adding"), ("free", FREE, "freeing buffers"))


def load():
    by = collections.defaultdict(list)
    for r in csv.DictReader(open(HERE / "maxsp_steps_xeon.csv")):
        by[int(r["max_sp"])].append(r)
    x = sorted(by)
    mean = lambda sp, k: st.mean(float(r[k]) for r in by[sp])
    return x, by, mean


def sd(by, sp, k):
    v = [float(r[k]) for r in by[sp]]
    return st.pstdev(v)


def main():
    x, by, mean = load()

    # --- the two panels of the earlier figure, on this machine -------------
    # (a) the whole cost of a spreading call, with a band over the repetitions
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    y = [mean(sp, "phase_ms") for sp in x]
    e = [sd(by, sp, "phase_ms") for sp in x]
    ax.fill_between(x, [a - b for a, b in zip(y, e)],
                    [a + b for a, b in zip(y, e)], color=PHASE, alpha=0.18, lw=0)
    ax.plot(x, y, "-o", lw=1.8, ms=4, color=PHASE,
            label="gathering + spreading + adding")
    ax.set_ylabel("time per spreading call [ms]")
    ax.set_title("Total cost of a subproblem", loc="left", fontsize=11)
    ax.legend(fontsize=9, loc="upper left", framealpha=0.95)
    finish(ax)
    save(fig, "maxsp_xeon_total")

    # (b) the three steps in cycles, with their sum, and no buffer-freeing
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    total = [sum(mean(sp, k + "_cyc") for k, _, _ in STEPS[:3]) / 1e9 for sp in x]
    ax.plot(x, total, "--s", lw=1.6, ms=4, color=TOTAL, label="all three steps")
    for key, c, lab in STEPS[:3]:
        ax.plot(x, [mean(sp, key + "_cyc") / 1e9 for sp in x], "-o", lw=1.8,
                ms=4, color=c, label=lab)
    ax.set_ylabel(r"cycles [$10^9$], summed over threads")
    ax.set_title("Cycles per step", loc="left", fontsize=11)
    ax.legend(fontsize=9, loc="center left", framealpha=0.95)
    finish(ax)
    save(fig, "maxsp_xeon_steps_cycles")

    # --- wall time of the spreading phase, from FINUFFT's own timer --------
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    wall = [mean(sp, "phase_ms") for sp in x]
    ax.plot(x, wall, "-o", lw=1.8, ms=4, color=PHASE, label="wall time")
    for xi, yi in ((x[0], wall[0]), (x[-1], wall[-1])):
        ax.annotate(f"{yi:.0f} ms", (xi, yi), textcoords="offset points",
                    xytext=(6 if xi == x[0] else -6, 8),
                    ha="left" if xi == x[0] else "right", fontsize=9, color=PHASE)
    ax.set_ylabel("wall-clock time of the spreading phase [ms]")
    ax.set_title("Wall time", loc="left", fontsize=11)
    ax.legend(fontsize=9, loc="lower right", framealpha=0.95)
    finish(ax)
    save(fig, "maxsp_steps_xeon_time")

    # --- the same steps in cycles ------------------------------------------
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    for key, c, lab in STEPS:
        ax.plot(x, [mean(sp, key + "_cyc") / 1e9 for sp in x], "-o", lw=1.8,
                ms=4, color=c, label=lab)
    ax.set_ylabel(r"cycles [$10^9$], summed over threads")
    ax.set_title("Cycles per step", loc="left", fontsize=11)
    ax.legend(fontsize=9, loc="center left", framealpha=0.95)
    finish(ax)
    save(fig, "maxsp_steps_xeon_cycles")


def finish(ax):
    ax.set_xscale("log")
    ax.set_xlabel(r"$S_{\max}$")
    ax.set_ylim(bottom=0)
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def save(fig, stem):
    fig.tight_layout()
    fig.savefig(HERE / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(HERE / f"{stem}.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / f"{stem}.pdf", "and .png")


if __name__ == "__main__":
    main()
