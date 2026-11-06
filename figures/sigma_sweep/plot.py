#!/usr/bin/env python3
"""Plot the sigma sweep: measured cpu time against the modelled spreading cost.

Data: sigma_sweep_xeon_1thread.csv, produced by perftest/sigma_sweep on the Xeon
E5-2698 v4 of Section 3.1 (built there with -march=native, AVX2), SINGLE-THREADED
(--nthreads 1, OMP_NUM_THREADS=1, pinned to one core), 8 iterations per point,
re-run 2026-11-06. Five configurations (1D 16000 and 2D 400x400 in single and
double, 3D 96x96x64 in double) x that precision's tolerances x 16 upsampling
factors from 1.25 to 2.00. json_to_csv.py converts the benchmark's JSON output.
Tolerance 1e-12 is left out of the figures: the 3D configuration was not run at
it, and the appendix grid keeps four tolerances per row.

The earlier sweep, sigma_sweep_1thread.csv, was taken on an Ice Lake node and,
despite its name, ran the 3D and one 2D configuration on all threads; it is
kept for reference only.

The `complexity` column is finufft's own modelled spreading cost,
nj * (2*nspread + padding) * (2*nspread)^(dim-1), taken from the benchmark's
counters (see FINUFFT_PLAN_T::get_complexity). It counts spreading only and has
no FFT term, so it is plotted on its own axis against measured time rather than
converted into one: the two are in different units, and what the comparison is
good for is whether the model STEPS at the same sigma the measurement does, not
whether the two sit at the same height.

Writes two figures:

  sigma_sweep_1e6.pdf   one panel per dimension at tol 1e-6, double precision.
                        The main-text figure.
  sigma_sweep_all.pdf   every (configuration, tolerance) pair, one panel each,
                        configurations down the page and tolerances across.
                        The appendix figure.
"""
import csv
import pathlib
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = pathlib.Path(__file__).parent
CSV = HERE / "sigma_sweep_xeon_1thread.csv"

PREC_NAME = {"f": "single", "d": "double"}
TIME_COLOR, CPLX_COLOR = "#1f77b4", "#ff7f0e"

MAIN_TOL = 1e-6      # the tolerance the main-text figure shows
DROP_TOLS = {1e-12}  # excluded: not run for 3D; keeps four tolerances per row
MAIN_PREC = "d"      # ... and at which precision


def load_rows(path=CSV) -> list:
    with open(path, newline="") as f:
        rows = []
        for r in csv.DictReader(f):
            r["dim"] = int(r["dim"])
            r["size"] = int(r["size"])
            r["density"] = float(r["density"])
            r["tol"] = float(r["tol"])
            if r["tol"] in DROP_TOLS:
                continue
            r["upsampfac"] = float(r["upsampfac"])
            r["complexity"] = float(r["complexity"])
            r["cpu_time_ns"] = float(r["cpu_time_ns"])
            rows.append(r)
        return rows


def grid_label(config: str, dim: int) -> str:
    """N1xN2xN3 from the configuration string, trimmed to the active axes;
    `size` alone would mislabel the anisotropic 96x96x64 grid."""
    return r"$\times$".join(config.split("-", 1)[0].split("x")[:dim])


def twin_panel(ax, pts: list, title: str, legend: bool = False):
    """Measured cpu time on the left axis, modelled complexity on a twin axis
    at the right, each axis labelled in its series' colour."""
    xs = [p["upsampfac"] for p in pts]

    l1, = ax.plot(xs, [p["cpu_time_ns"] / 1e6 for p in pts], "-o", lw=1.6,
                  ms=3.5, color=TIME_COLOR, label="CPU time", zorder=3)
    ax.set_ylabel("CPU time [ms]", color=TIME_COLOR, fontsize=9)
    ax.tick_params(axis="y", colors=TIME_COLOR, labelsize=8)
    ax.tick_params(axis="x", labelsize=8)

    rax = ax.twinx()
    l2, = rax.plot(xs, [p["complexity"] for p in pts], "-s", lw=1.6, ms=3.5,
                   color=CPLX_COLOR, label="Complexity", zorder=2)
    rax.set_ylabel("Modelled complexity [ops]", color=CPLX_COLOR, fontsize=9)
    rax.tick_params(axis="y", colors=CPLX_COLOR, labelsize=8)

    ax.set_title(title, fontsize=9)
    ax.set_xlabel(r"upsampling factor $\sigma$", fontsize=9)
    # one legend serves the figure: every panel draws the same two series
    if legend:
        ax.legend(handles=[l1, l2], fontsize=8, loc="upper right",
                  framealpha=0.95)
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    return rax


def by_config_and_tol(rows: list):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["configuration"], r["tol"])].append(r)
    for k in groups:
        groups[k].sort(key=lambda r: r["upsampfac"])
    return groups


def main_figure(rows: list):
    """One panel per dimension at a single tolerance and precision."""
    sel = [r for r in rows if r["tol"] == MAIN_TOL and r["prec"] == MAIN_PREC]
    by_dim = defaultdict(list)
    for r in sel:
        by_dim[r["dim"]].append(r)
    dims = sorted(by_dim)

    fig, axes = plt.subplots(1, len(dims), figsize=(4.3 * len(dims), 3.6),
                             squeeze=False)
    for i, dim in enumerate(dims):
        pts = sorted(by_dim[dim], key=lambda r: r["upsampfac"])
        cfg = pts[0]["configuration"]
        twin_panel(axes[0][i], pts,
                   f"{dim}D, {grid_label(cfg, dim)}", legend=(i == 0))
    fig.tight_layout()
    return fig


def appendix_figure(rows: list):
    """Every (configuration, tolerance) pair: configurations down, tolerances
    across, so a row shows how the model's agreement changes with tolerance."""
    groups = by_config_and_tol(rows)
    configs = sorted({c for c, _ in groups},
                     key=lambda c: (groups[[k for k in groups if k[0] == c][0]][0]["dim"],
                                    groups[[k for k in groups if k[0] == c][0]][0]["size"],
                                    groups[[k for k in groups if k[0] == c][0]][0]["prec"],
                                    c))
    tols_of = {c: sorted({t for cc, t in groups if cc == c}, reverse=True)
               for c in configs}

    nrows, ncols = len(configs), max(len(t) for t in tols_of.values())
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.0 * ncols, 3.1 * nrows),
                             squeeze=False)

    for i, cfg in enumerate(configs):
        for j, tol in enumerate(tols_of[cfg]):
            pts = groups[(cfg, tol)]
            r = pts[0]
            title = (f"{r['dim']}D {grid_label(cfg, r['dim'])}, "
                     f"{PREC_NAME[r['prec']]}, tol={tol:.0e}")
            twin_panel(axes[i][j], pts, title, legend=(i == 0 and j == 0))
        for j in range(len(tols_of[cfg]), ncols):
            axes[i][j].axis("off")

    fig.tight_layout()
    return fig


def main():
    rows = load_rows()
    if not rows:
        raise SystemExit(f"no rows read from {CSV}")

    for fig, name in ((main_figure(rows), "sigma_sweep_1e6"),
                      (appendix_figure(rows), "sigma_sweep_all")):
        fig.savefig(HERE / f"{name}.pdf", bbox_inches="tight")
        fig.savefig(HERE / f"{name}.png", dpi=200, bbox_inches="tight")
        print("wrote", HERE / f"{name}.pdf", "and .png")


if __name__ == "__main__":
    main()
