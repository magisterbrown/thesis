#!/usr/bin/env python3
"""What bin sorting does to the order points are stored in.

Three levels of sorting applied to the same 2D point set, each panel coloured
by the point's position in the array the spreader reads: none, coarse bins, and
the default bins. A subproblem is a contiguous run of that array, so the colour
shows directly how much of the grid one subproblem has to reach into -- smooth
colour means a run of points is spatially compact, mottled colour means it is
scattered.

The three are one knob, not three algorithms: shrinking the bin tightens the
ordering, and FINUFFT's default is a coarse setting of it rather than a sort in
its own right.

The sort reproduced here is FINUFFT's bin_sort_singlethread: bins are indexed
x fastest, points are placed into their bin's slot in input order, and the
indices are read back one bin at a time. Nothing orders points that share a
bin, which is why each band in the coarse panel is a flat colour rather than a
gradient.

No CSV: the point set is generated from a fixed seed, so the figure is
reproducible without a measurement to accompany it.

Usage:
    python3 plot.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
N = 128           # fine-grid cells per axis
M = 5000          # points; density below 1 so the panels stay legible
SEED = 0


def bin_sort(pts, bx, by):
    """Indices in FINUFFT's bin order: by bin, x fastest, input order within."""
    nbx = int(N / bx) + 1
    b = (pts[:, 0] / bx).astype(int) + nbx * (pts[:, 1] / by).astype(int)
    return np.argsort(b, kind="stable")     # stable: no order inside a bin


def main():
    rng = np.random.default_rng(SEED)
    pts = rng.uniform(0, N, size=(M, 2))

    panels = [(None, "not sorted"),
              ((16, 32), r"coarse bins, $16\times32$"),
              ((16, 4), r"default bins, $16\times4$")]

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.3))
    for ax, (bins, title) in zip(axes, panels):
        order = np.arange(M) if bins is None else bin_sort(pts, *bins)
        rank = np.empty(M)
        rank[order] = np.arange(M)          # where each point lands in the array
        s = ax.scatter(pts[:, 0], pts[:, 1], c=rank, s=9, cmap="viridis",
                       linewidths=0)
        # the bin rows are the structure the middle panel is about
        # only worth drawing where the rows are far enough apart to be seen
        if bins is not None and bins[1] >= 8:
            for y in range(0, N + 1, bins[1]):
                ax.axhline(y, color="white", lw=0.4, alpha=0.55, zorder=3)
        ax.set_xlim(0, N)
        ax.set_ylim(0, N)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("$x$ [grid cells]")
        ax.set_xticks([0, N // 2, N])
        ax.set_yticks([0, N // 2, N])
    axes[0].set_ylabel("$y$ [grid cells]")

    cb = fig.colorbar(s, ax=axes, fraction=0.02, pad=0.015)
    cb.set_label("position in the sorted point array")

    fig.savefig(HERE / "binsort_locality.pdf", bbox_inches="tight")
    fig.savefig(HERE / "binsort_locality.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "binsort_locality.pdf", "and .png")


if __name__ == "__main__":
    main()
