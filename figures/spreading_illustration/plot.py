#!/usr/bin/env python3
"""Illustrate the spreading step of a type-1 NUFFT in three stages.

Top:    the nonuniform input -- ten points at arbitrary locations, each
        carrying a signed strength.
Middle: the spreading kernel centred on each point and scaled by that point's
        strength. This is the quantity that actually gets accumulated; the
        kernel has compact support, so each point touches only ns grid cells.
Bottom: the result on the regular grid -- the sum of the middle panel sampled
        at the grid points. This array is what the FFT then consumes.

The kernel is the "exp-sqrt" (ES) kernel of the FINUFFT paper,

    phi(z) = exp(beta * (sqrt(1 - z^2) - 1)),   |z| <= 1,

supported on ns/2 grid spacings either side of the point. beta is the standard
cutoff shape parameter pi*ns*(1 - 1/(2*sigma)) computed the same way as
beta_cutoff in src/common/kernel.cpp; note that current FINUFFT actually ships
a PSWF kernel (kerformula 7-9) and uses that expression only as its starting
point, so this figure illustrates the classic ES kernel rather than the exact
function the library now evaluates.

Nothing here is measured -- it is a schematic drawn from a fixed random seed,
so the picture is reproducible.

Writes spreading_illustration.{pdf,png} next to this script.
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).parent

M = 10        # nonuniform points
N = 64        # uniform grid points
NS = 7        # kernel width in grid cells
SIGMA = 2.0   # upsampling factor the shape parameter is chosen for
SEED = 3

INK, RULE = "#0b0b0b", "#52514e"


def es_kernel(z, beta):
    """ES kernel on |z| <= 1, zero outside. z is the distance from the point
    centre in units of the kernel half-width."""
    inside = np.abs(z) <= 1.0
    out = np.zeros_like(z)
    out[inside] = np.exp(beta * (np.sqrt(1.0 - z[inside] ** 2) - 1.0))
    return out


def main():
    rng = np.random.default_rng(SEED)

    # Uniform grid over the periodic domain, and the nonuniform input.
    h = 2 * np.pi / N
    grid = -np.pi + h * np.arange(N)
    x = np.sort(rng.uniform(-np.pi, np.pi, M))        # locations
    c = rng.uniform(-2.0, 2.4, M)                     # strengths

    beta = np.pi * NS * (1.0 - 1.0 / (2.0 * SIGMA))
    half = (NS / 2.0) * h                             # kernel half-width in x

    colors = plt.cm.tab10(np.arange(M) % 10)

    # sized for a half-textwidth subfigure: a wider figure would be scaled down
    # further by LaTeX and take the label text with it
    fig, axes = plt.subplots(3, 1, figsize=(5.0, 6.4), sharex=True)

    # --- 1. the nonuniform points -------------------------------------------
    ax = axes[0]
    ax.vlines(x, 0, c, color=RULE, lw=1.2, zorder=2)
    ax.plot(x, c, "o", ms=5, color="#2a78d6", zorder=3)
    ax.set_ylabel("strength", fontsize=9)
    ax.set_title(f"{M} nonuniform points: location and strength", fontsize=9)

    # --- 2. one scaled kernel per point -------------------------------------
    ax = axes[1]
    zz = np.linspace(-1.0, 1.0, 400)
    for xj, cj, col in zip(x, c, colors):
        ax.plot(xj + zz * half, cj * es_kernel(zz, beta), lw=1.4, color=col,
                zorder=2)
    ax.set_ylabel("kernel $\\times$ strength", fontsize=9)
    ax.set_title(f"spreading kernel (ES, ns={NS}) scaled and centred on each point",
                 fontsize=9)

    # --- 3. the accumulated regular grid ------------------------------------
    # Each point contributes to the grid cells inside its support; the periodic
    # wrap is what FINUFFT's spreader does at the domain edges.
    spread = np.zeros(N)
    for xj, cj in zip(x, c):
        d = grid - xj
        d -= 2 * np.pi * np.round(d / (2 * np.pi))   # nearest periodic image
        spread += cj * es_kernel(d / half, beta)

    ax = axes[2]
    ax.vlines(grid, 0, spread, color=RULE, lw=0.9, zorder=2)
    ax.plot(grid, spread, "o", ms=3.5, color="#2a78d6", zorder=3)
    ax.set_ylabel("value on grid", fontsize=9)
    ax.set_title(f"spread onto the uniform grid (N={N})", fontsize=9)
    ax.set_xlabel("location $x$", fontsize=9)

    for ax in axes:
        ax.axhline(0, color=INK, lw=0.9, zorder=1)
        ax.set_xlim(-np.pi, np.pi)
        ax.grid(True, ls=":", lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=8)

    fig.tight_layout()
    # bbox_inches: the y labels sit outside the tight_layout box on this
    # tall-and-narrow figure and are otherwise clipped at the left edge
    fig.savefig(HERE / "spreading_illustration.pdf", bbox_inches="tight")
    fig.savefig(HERE / "spreading_illustration.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "spreading_illustration.pdf", "and .png")


if __name__ == "__main__":
    main()
