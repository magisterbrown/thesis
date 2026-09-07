#!/usr/bin/env python3
"""Show how the spreading kernel shrinks as the upsampling factor sigma rises.

One curve per sigma, all on the same axis: the kernel's value against offset
from the nonuniform point, measured in fine-grid spacings. Raising sigma
relaxes the accuracy demanded of the kernel, so the width ns falls and each
point touches fewer grid cells -- which is what spreading actually pays for.

Both quantities sigma drives are taken from the formulas FINUFFT uses
(src/common/kernel.cpp):

    ns   = ceil( log(tolfac/tol) / (pi*sqrt(1 - 1/sigma)) + 1 )   [:90]
    beta = pi * ns * (1 - 1/(2*sigma))                            [:105]

with tolfac = 0.18 * 1.4^(dim-1) for type 1/2. ns is a ceil, so it falls in
steps: several of the sigmas below share a width and differ only through beta,
which is why their curves nearly coincide.

The kernel drawn is the "exp-sqrt" (ES) kernel of the FINUFFT paper,
phi(z) = exp(beta*(sqrt(1-z^2)-1)) on |z| <= 1. Current FINUFFT actually ships
a PSWF kernel (kerformula 7-9) and uses the beta expression above only as its
starting point, so this illustrates the classic ES kernel rather than the exact
function the library now evaluates.

Writes kernel_vs_sigma.{pdf,png} next to this script.
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).parent

TOL = 1e-6     # requested tolerance
DIM = 1        # tolfac depends on dimension
TYPE = 1       # type 1/2 (type 3 carries an extra factor)
SIGMAS = [1.25, 1.4, 1.5, 1.6, 1.75, 2.0]


def tolfac(dim=DIM, type_=TYPE):
    """kernel_tolfac: 0.18 * 1.4^(dim-1), times 1.4 again for type 3."""
    return 0.18 * 1.4 ** (dim - 1) * (1.4 if type_ == 3 else 1.0)


def kernel_ns(sigma, tol=TOL):
    """theoretical_kernel_ns: the width in grid cells needed for this tol."""
    return int(np.ceil(np.log(tolfac() / tol) / (np.pi * np.sqrt(1.0 - 1.0 / sigma)) + 1.0))


def kernel_beta(ns, sigma):
    """beta_cutoff from set_kernel_shape_given_ns."""
    return np.pi * ns * (1.0 - 1.0 / (2.0 * sigma))


def es_kernel(z, beta):
    """ES kernel phi(z) = exp(beta*(sqrt(1-z^2)-1)) on |z| <= 1, else 0."""
    inside = np.abs(z) <= 1.0
    out = np.zeros_like(z)
    out[inside] = np.exp(beta * (np.sqrt(1.0 - z[inside] ** 2) - 1.0))
    return out


def main():
    # squarer than a standalone plot would be, so that beside the taller
    # spreading figure the two subfigures come out near the same height
    fig, ax = plt.subplots(1, 1, figsize=(5.0, 4.4))

    z = np.linspace(-1.0, 1.0, 600)
    for sigma in SIGMAS:
        ns = kernel_ns(sigma)
        half = ns / 2.0                       # half-width in grid spacings
        ax.plot(z * half, es_kernel(z, kernel_beta(ns, sigma)),
                label=f"sigma={sigma} (ns={ns})")

    ax.set_title(f"ES spreading kernel shrinks as sigma increases\n(tol={TOL:.0e})",
                 fontsize=10)
    ax.set_xlabel("offset from NU point (grid spacings)")
    ax.set_ylabel("kernel value")
    ax.legend(fontsize=7.5)
    ax.tick_params(labelsize=8)
    ax.grid(True, ls=":", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(HERE / "kernel_vs_sigma.pdf", bbox_inches="tight")
    fig.savefig(HERE / "kernel_vs_sigma.png", dpi=200, bbox_inches="tight")
    print("wrote", HERE / "kernel_vs_sigma.pdf", "and .png")


if __name__ == "__main__":
    main()
