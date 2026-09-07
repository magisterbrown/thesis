#!/usr/bin/env python3
"""Cost of the three spreading steps against the maximum subproblem size.

Data: maxsp_steps.csv, measured on one exclusive Ice Lake node (Xeon Platinum
8362, 64 threads) with spreadinterponly=1, so no FFT is involved. 2D type-1
double precision, M = 33,554,432 nonuniform points on a 5793 x 5793 grid at
unit density -- 1 GiB of point data. Each row is the mean of three runs.

Step costs are attributed with perf: the spreading phase is timed by FINUFFT's
own counter and split in proportion to each step's sampled cycles. Gathering is
inlined into the OpenMP body of spreadSorted rather than being a function of
its own, so its bucket also carries the subproblem loop and the subgrid
zeroing, and is an upper bound on gathering alone.

Writes two figures next to this script:

  maxsp_steps.pdf   wall-clock cost of each of the three steps against S_max
  maxsp_cycles.pdf  the same three steps in cycles rather than time. Cycles
                    count work actually done, summed over threads, so the two
                    figures separate real slowdown from wall time inflated by
                    load imbalance: past the middle of the range the subproblem
                    count per thread approaches one, and time keeps rising
                    while cycles do not.
  maxsp_fbfull.pdf  the cycles gathering consumes, against the stall counters
  maxsp_addvol.pdf  adding time and the write volume the subgrid model
                    predicts, A(S_max) times the number of subproblems, both
                    against S_max. They carry different units and so sit on
                    twin axes; the figure is for whether the two fall together,
                    not for their relative height.
  maxsp_8thr.pdf    gathering time and gathering cycles on 8 threads, each
                    normalised to its own value at the smallest S_max. Both are
                    plotted on one axis because normalising removes the units;
                    on twin axes any two curves can be made to look parallel.
                    On 64 threads the two diverge (time rises 3.8x while cycles
                    rise 1.7x); with 8 threads there are eight times as many
                    subproblems per thread, and the divergence disappears.: cycles a
                    demand request was blocked for want of a line-fill buffer
                    (l1d_pend_miss.fb_full) and cycles stalled on an L3 miss
                    (cycle_activity.stalls_l3_miss). stalls_l2_miss is in the
                    CSV but not drawn: nearly every L2 miss also misses L3, so
                    the two curves coincide and only one is informative. All
                    quantities are attributed to the gathering symbol. The
                    counters share the right axis because all three are cycle
                    counts; time is on the left because it is not. What the
                    figure is for is whether the counters rise the way the time
                    does -- they do not past the middle of the range, where the
                    subproblem count per thread approaches one and wall time is
                    increasingly set by load imbalance rather than by work.
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent

# Xeon Platinum 8362: 1.25 MiB L2 per core, 48 MiB L3 shared by 32 cores.
# A thread's working set is its staging buffers plus its subgrid,
#   B(S) = 32*S + 16*A2(S)   bytes
# (kx0 and ky0 at 8 B a point, dd0 at 16, and the subgrid at 16 B a cell),
# so each cache size maps to the S_max at which the buffers stop fitting.
L2_BYTES = 1280 * 1024
L3_BYTES = 49152 * 1024 / 32
M_PTS, N_GRID, BX, BY, W = 33554432, 5793, 16, 4, 7


def subgrid_cells(S):
    rho = M_PTS / (N_GRID * N_GRID)
    x_ext = S / (rho * BY)
    r = x_ext / N_GRID
    f = min(1.0, r)
    return ((1 - f) * (x_ext + BX + W) * (BY + W)
            + f * (N_GRID + W) * ((max(1.0, r) + 1) * BY + W))


def smax_at(cache_bytes):
    """S_max whose per-thread working set just fills this much cache."""
    lo, hi = 100.0, 5e6
    for _ in range(200):
        mid = (lo + hi) / 2
        if 32 * mid + 16 * subgrid_cells(mid) < cache_bytes:
            lo = mid
        else:
            hi = mid
    return lo

# categorical slots 1-3, the set that stays separable for colour-blind readers
GATHER, SPREAD, ADD = "#2a78d6", "#eb6834", "#1baf7a"
TIME_C, FB_C = "#1f77b4", "#ff7f0e"   # matches the twin-axis figures elsewhere
L2_C, L3_C = "#1baf7a", "#4a3aa7"     # the two stall counters
CYC_C = "#e34948"                     # gathering cycles: work, not stalls


def main():
    rows = list(csv.DictReader(open(HERE / "maxsp_steps.csv")))
    x = [int(r["max_sp"]) for r in rows]

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))

    for key, sd, c, lab in (("gather_ms", "gather_sd", GATHER, "gathering"),
                            ("spread_ms", "spread_sd", SPREAD, "spreading"),
                            ("add_ms", "add_sd", ADD, "adding")):
        y = [float(r[key]) for r in rows]
        e = [float(r[sd]) for r in rows]
        ax.fill_between(x, [a - b for a, b in zip(y, e)],
                        [a + b for a, b in zip(y, e)], color=c, alpha=0.18, lw=0)
        ax.plot(x, y, "-o", color=c, lw=1.8, ms=4, label=lab)
    ax.set_xscale("log")
    ax.set_xlabel(r"$S_{\max}$")
    ax.set_ylabel("time per spreading call [ms]")
    ax.set_ylim(bottom=0)
    ax.set_title("Cost of each step", loc="left", fontsize=11)
    ax.legend(fontsize=9, loc="upper left", framealpha=0.95)
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(HERE / "maxsp_steps.pdf", bbox_inches="tight")
    fig.savefig(HERE / "maxsp_steps.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "maxsp_steps.pdf", "and .png")

    # --- gathering cycles against the stall counters -----------------------
    # every quantity here is a cycle count, so they share one axis; no twin
    # axis is needed and none of the height comparisons are scaling artefacts
    fig2, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    for key, c, lab in (("gather_cycles", GATHER, "gathering cycles"),
                        ("fb_full_gather", FB_C, "l1d_pend_miss.fb_full"),
                        ("stalls_l3_gather", L3_C, "cycle_activity.stalls_l3_miss")):
        xs = [xi for xi, r in zip(x, rows) if r.get(key)]
        ys = [float(r[key]) for r in rows if r.get(key)]
        ax.plot(xs, ys, "-s", lw=1.8, ms=4, color=c, label=lab)

    ax.set_xscale("log")
    ax.set_xlabel(r"$S_{\max}$")
    ax.set_ylabel("cycles, attributed to gathering")
    ax.set_ylim(bottom=0)
    ax.set_title("64 threads", loc="left", fontsize=11)
    ax.legend(fontsize=9, loc="lower right", framealpha=0.95)
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    fig2.tight_layout()
    fig2.savefig(HERE / "maxsp_fbfull.pdf", bbox_inches="tight")
    fig2.savefig(HERE / "maxsp_fbfull.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "maxsp_fbfull.pdf", "and .png")

    # --- the same pair on 8 threads ----------------------------------------
    r8 = list(csv.DictReader(open(HERE / "maxsp_8thr.csv")))
    x8 = [int(r["max_sp"]) for r in r8]
    fig5, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    for key, c, lab in (("gather_cycles", GATHER, "gathering cycles"),
                        ("fb_full_gather", FB_C, "l1d_pend_miss.fb_full")):
        ax.plot(x8, [float(r[key]) for r in r8], "-s", lw=1.8, ms=4,
                color=c, label=lab)
    ax.set_xscale("log")
    ax.set_xlabel(r"$S_{\max}$")
    ax.set_ylabel("cycles, attributed to gathering")
    # cropped rather than zero-based: both series sit in a narrow band and the
    # shapes are invisible against a 0 baseline
    ax.set_ylim(bottom=3e9)
    ax.set_title("8 threads", loc="left", fontsize=11)
    ax.legend(fontsize=9, loc="lower right", framealpha=0.95)
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    fig5.tight_layout()
    fig5.savefig(HERE / "maxsp_fbfull_8thr.pdf", bbox_inches="tight")
    fig5.savefig(HERE / "maxsp_fbfull_8thr.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "maxsp_fbfull_8thr.pdf", "and .png")

    # --- the same three steps, in cycles rather than wall time --------------
    fig3, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    for key, c, lab in (("gather_cycles", GATHER, "gathering"),
                        ("spread_cycles", SPREAD, "spreading"),
                        ("add_cycles", ADD, "adding")):
        ax.plot(x, [float(r[key]) for r in rows], "-o", lw=1.8, ms=4,
                color=c, label=lab)
    ax.set_xscale("log")
    ax.set_xlabel(r"$S_{\max}$")
    ax.set_ylabel("cycles, summed over threads")
    ax.set_ylim(bottom=0)
    ax.set_title("Cycles per step", loc="left", fontsize=11)
    ax.legend(fontsize=9, loc="upper left", framealpha=0.95)
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    fig3.tight_layout()
    fig3.savefig(HERE / "maxsp_cycles.pdf", bbox_inches="tight")
    fig3.savefig(HERE / "maxsp_cycles.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "maxsp_cycles.pdf", "and .png")

    # --- 8 threads: does gathering time still outrun gathering cycles? ------
    r8 = list(csv.DictReader(open(HERE / "maxsp_8thr.csv")))
    x8 = [int(r["max_sp"]) for r in r8]
    fig4, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    for key, c, lab in (("gather_ms", GATHER, "gathering time"),
                        ("gather_cycles", CYC_C, "gathering cycles")):
        y = [float(r[key]) for r in r8]
        ax.plot(x8, [v / y[0] for v in y], "-o", lw=1.8, ms=4, color=c, label=lab)
    ax.axhline(1.0, color="0.6", lw=0.8, ls=":", zorder=1)
    ax.set_xscale("log")
    ax.set_xlabel(r"$S_{\max}$")
    ax.set_ylabel(r"relative to $S_{\max}=10^4$")
    ax.set_title("8 threads", loc="left", fontsize=11)
    ax.legend(fontsize=9, loc="upper left", framealpha=0.95)
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    fig4.tight_layout()
    fig4.savefig(HERE / "maxsp_8thr.pdf", bbox_inches="tight")
    fig4.savefig(HERE / "maxsp_8thr.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "maxsp_8thr.pdf", "and .png")

    # --- adding time and the cells it writes, both against S_max -----------
    fig6, ax = plt.subplots(1, 1, figsize=(7.5, 4.4))
    l1, = ax.plot(x, [float(r["add_ms"]) for r in rows], "-o", lw=1.8, ms=4,
                  color=ADD, label="adding time")
    ax.set_xscale("log")
    ax.set_xlabel(r"$S_{\max}$")
    ax.set_ylabel("adding time [ms]", color=ADD)
    ax.tick_params(axis="y", colors=ADD)
    ax.set_ylim(bottom=0)

    # cells written is a count, not a time, so it needs its own axis; only the
    # shapes are comparable, not the heights
    rax = ax.twinx()
    l2, = rax.plot(x, [float(r["cells_written"]) for r in rows], "-s", lw=1.8,
                   ms=4, color=CYC_C, label=r"cells written, $A \cdot n_{sub}$")
    rax.set_ylabel("cells written", color=CYC_C)
    rax.tick_params(axis="y", colors=CYC_C)
    rax.set_ylim(bottom=0)

    ax.legend(handles=[l1, l2], fontsize=9, loc="upper right", framealpha=0.95)
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    fig6.tight_layout()
    fig6.savefig(HERE / "maxsp_addvol.pdf", bbox_inches="tight")
    fig6.savefig(HERE / "maxsp_addvol.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "maxsp_addvol.pdf", "and .png")


if __name__ == "__main__":
    main()
