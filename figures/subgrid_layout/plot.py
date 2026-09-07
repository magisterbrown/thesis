#!/usr/bin/env python3
"""Draw the first N subgrids of a 2D spread, separating the ones that span the
whole fast axis from the ones that do not.

Reads a CSV from collect_subgrid_sizes.py and plots each subproblem's subgrid
as a rectangle at its recorded offset. A subgrid is classed as spanning when
its x extent reaches the full grid width: that happens when the subproblem's
run of bin-sorted points crosses a bin-row boundary, so the run holds a suffix
of one row and a prefix of the next. Those two pieces sit at opposite ends of
the x axis, so the bounding box has to cover everything between them, however
few points the run actually holds.

The fills are translucent, so where rectangles overlap the colour darkens --
that overlap is the redundant write traffic the subgrid size controls.

Data: subgrid_2d_smax2500.csv, logged from perftest/spreadtestnd with
spread_debug=2 at S_max=2500, unit density, 3162x3162 grid.

Writes subgrid_layout.{pdf,png} next to this script.
"""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

COMPACT, SPANNING = "#2a78d6", "#eb6834"
# darker shades of the same two hues, for the rectangle borders: the fills are
# faint enough to stack many deep, so the edges are what delimit each subgrid
COMPACT_EDGE, SPANNING_EDGE = "#17456f", "#8f3a15"
INK, MUTED = "#0b0b0b", "#52514e"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path,
                    default=Path(__file__).resolve().parent / "subgrid_2d_smax2500.csv")
    ap.add_argument("--n", type=int, default=20, help="subproblems to draw")
    ap.add_argument("--max-sp", type=int, default=None,
                    help="if the CSV holds several sweeps, keep only this one")
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parent / "subgrid_layout.pdf")
    args = ap.parse_args()

    rows = [r for r in csv.DictReader(open(args.csv)) if r["dim"] == "2"]
    if args.max_sp is not None:
        rows = [r for r in rows if int(r["max_sp"]) == args.max_sp]
    rows = rows[:args.n]
    if not rows:
        raise SystemExit(f"no 2D rows in {args.csv}")
    N = int(rows[0]["N_per_dim"])
    smax = int(rows[0]["max_sp"])

    fig, ax = plt.subplots(figsize=(11.0, 4.2))

    # spanning subgrids underneath, compact ones on top: the spanning ones cover
    # the full width and would otherwise hide the structure they overlap
    spans = [r for r in rows if int(r["size1"]) >= N]
    compact = [r for r in rows if int(r["size1"]) < N]
    n_span = len(spans)
    # the spanning subgrids get a heavier border: they sit underneath and are
    # otherwise easy to lose under the compact ones stacked on top
    for group, c, ec, z, lw in ((spans, SPANNING, SPANNING_EDGE, 2, 2.0),
                                (compact, COMPACT, COMPACT_EDGE, 3, 1.2)):
        for r in group:
            ax.add_patch(Rectangle((int(r["off1"]), int(r["off2"])),
                                   int(r["size1"]), int(r["size2"]),
                                   facecolor=c, alpha=0.12, lw=0, zorder=z))
            ax.add_patch(Rectangle((int(r["off1"]), int(r["off2"])),
                                   int(r["size1"]), int(r["size2"]),
                                   facecolor="none", edgecolor=ec, lw=lw,
                                   alpha=0.9, zorder=z + 2))

    # the periodic grid itself
    ymax = max(int(r["off2"]) + int(r["size2"]) for r in rows)
    ax.axvline(0, color=MUTED, lw=1.0, ls="--", zorder=1)
    ax.axvline(N, color=MUTED, lw=1.0, ls="--", zorder=1)
    ax.annotate("grid edge", (0, ymax), textcoords="offset points", xytext=(4, -10),
                fontsize=8, color=MUTED)
    ax.annotate("grid edge", (N, ymax), textcoords="offset points", xytext=(-4, -10),
                ha="right", fontsize=8, color=MUTED)

    ax.set_xlim(-0.04 * N, 1.04 * N)
    ax.set_ylim(min(int(r["off2"]) for r in rows) - 2, ymax + 3)
    ax.set_xlabel("x (fine-grid cells)")
    ax.set_ylabel("y (fine-grid cells)")
    ax.set_title(f"First {len(rows)} subgrids, 2D, $S_{{\\max}}$={smax}, "
                 f"grid {N}$\\times${N}", fontsize=11)

    handles = [
        Patch(facecolor=COMPACT, alpha=0.12, edgecolor=COMPACT_EDGE, lw=1.2,
              label=f"within one bin-row ({len(rows) - n_span})"),
        Patch(facecolor=SPANNING, alpha=0.12, edgecolor=SPANNING_EDGE, lw=2.0,
              label=f"crosses a bin-row boundary, spans full width ({n_span})"),
    ]
    ax.legend(handles=handles, fontsize=9, loc="upper left", framealpha=0.95)
    ax.grid(True, ls=":", lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(args.out, bbox_inches="tight")
    fig.savefig(args.out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    print(f"wrote {args.out}  ({n_span} of {len(rows)} span the full width)")


if __name__ == "__main__":
    main()
