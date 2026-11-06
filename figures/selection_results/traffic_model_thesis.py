#!/usr/bin/env python3
"""The traffic model and selection procedure exactly as printed in Chapter 6.

Spreading: Equations eq:traffic_terms, eq:traffic_ramps, eq:spread_reads/writes
  lambda = A_d(S)/S * 2*sz/64,  beta = (d+2)*sz/64,  u = w^d/(1+rho*w^d) * 2*sz/64
  h_sub = ramp(2*sz*A_d(S); C3/2, 2*C3),  h_buf = ramp((d+2)*sz*S; L2, 2*C3)
  reads  = (d+1) + 2*beta*h_buf + (2*lambda+u)*h_sub + lambda
  writes =          beta*h_buf  + (2*lambda+u)*h_sub + lambda
Bin sort: Equations eq:sort_counts_miss, eq:sort_reads/writes
  P_count = max(0, 1 - C3/(4*nbins)),  P_place = max(0, 1 - C3/(64*min(nbins, M/(8*n_t)) + 4*nbins))
  (P_place differs from the printed form 8*M/n_t, which keeps the whole share of ret open; see sort_rw)
  reads = writes = P_count + 2*P_place + n_t*nbins/(8*M)
Selection (Section 6.7): bins from bins_for() (padded bin <= 0.9 L1d, b_x >= b_y >= b_z,
16x4x4 minimum), 40 log-spaced S_max up to M/n_thr keeping S_max >= 2500, minimise
sort + spread traffic.

C3 is the L3 cache divided by the number of threads that share it. The subgrid size
A_d is the formula of Section 6.2, taken from the analysis code (traffic_model.A).
Usage: python3 traffic_model_thesis.py  -> writes picks_thesis_{full,sp}_t{20,10,1}.txt
"""
import math
import pathlib
import sys

import numpy as np

BINSWEEP = pathlib.Path(__file__).resolve().parents[3] / "valgrind/perf/binsweep"
sys.path.insert(0, str(BINSWEEP))
import traffic_model as old  # noqa: E402  (only A() and halo() are used)

B = 64
L1 = 32 * 1024
L2 = 256 * 1024  # private per core; one thread per core up to 20 threads
L3 = 50 * 2**20
NS = 8  # kernel width of the test transforms


def ramp(x, a, c):
    return min(1.0, max(0.0, math.log(max(x, 1e-300) / a) / math.log(c / a)))


def spread_rw(d, sz, N, M, S, b, nthr, ns=NS):
    C3 = L3 / nthr
    rho = M / math.prod(N)
    s = M / max(nthr, math.ceil(M / S))  # points per subproblem, as in the library
    A = old.A(d, N, rho, old.halo(ns), s, b)
    lam = A / s * 2 * sz / B
    beta = (d + 2) * sz / B
    u = ns**d / (1 + rho * ns**d) * 2 * sz / B
    hs = ramp(2 * sz * A, C3 / 2, 2 * C3)
    hb = ramp((d + 2) * sz * s, L2, 2 * C3)  # staging buffer is reused at once: costs once it leaves L2
    reads = (d + 1) + 2 * beta * hb + (2 * lam + u) * hs + lam
    writes = beta * hb + (2 * lam + u) * hs + lam
    return reads, writes


def sort_threads(N, M, nthr):
    return nthr if 10 * M > math.prod(N) else 1  # library: single-threaded sort when sparse


def sort_rw(d, sz, N, M, b, nthr):
    nt = sort_threads(N, M, nthr)
    C3 = L3 / nt
    nbins = math.prod(N[i] // b[i] + 1 for i in range(d))
    pc = max(0.0, 1 - C3 / (4 * nbins))
    # open ret lines: one per bin, at most the thread's share of ret (M/(8 n_t) lines). The printed
    # form 8*M/n_t (whole share always open) overestimates sort traffic up to 10x for few large bins.
    pp = max(0.0, 1 - C3 / (64 * min(nbins, M / (8 * nt)) + 4 * nbins))
    t = pc + 2 * pp + nt * nbins / (8 * M)
    return t, t


BX = [16, 32, 64, 128, 256, 512, 1024, 2048]
BYZ = [4, 8, 16, 32, 64]


def bins_for(d, sz, w=NS):
    c = {1: [(x, 1, 1) for x in BX], 2: [(x, y, 1) for x in BX for y in BYZ],
         3: [(x, y, z) for x in BX for y in BYZ for z in BYZ]}[d]
    fit = [b for b in c if b[0] >= b[1] >= b[2] and
           (b[0] + w) * ((b[1] + w) if d > 1 else 1) * ((b[2] + w) if d > 2 else 1) * 2 * sz <= 0.9 * L1]
    return fit or [(16, 4, 4)[:d] + (1,) * (3 - d)]


def sps_for(M, nthr):
    one = math.ceil(M / nthr)
    return [int(s) for s in np.unique(np.round(np.logspace(math.log10(200), math.log10(one), 40)).astype(int))
            if s >= 2500]


def total(d, sz, N, M, S, b, nthr):
    return sum(sort_rw(d, sz, N, M, b, nthr)) + sum(spread_rw(d, sz, N, M, S, b, nthr))


def pick(d, sz, N, M, nthr, bins=None):
    cands = bins or bins_for(d, sz)
    return min(((total(d, sz, N, M, s, b, nthr), b, s) for b in cands for s in sps_for(M, nthr)),
               key=lambda x: x[0])


def cases():
    """The 54 test transforms: (d, prec, density, n, M) from the measured pick files."""
    raw = pathlib.Path(__file__).parent / "raw" / "picks_full_uni20.txt"
    for line in open(raw):
        f = line.split()
        d, p, de, n = int(f[0]), f[1], float(f[2]), int(f[3])
        yield d, p, de, n, int(round(de * n**d))


if __name__ == "__main__":
    out = pathlib.Path(__file__).parent / "raw"
    for nthr in (20, 10, 1):
        with open(out / f"picks_thesis_full_t{nthr}.txt", "w") as ff, \
             open(out / f"picks_thesis_sp_t{nthr}.txt", "w") as fs:
            for d, p, de, n, M in cases():
                sz = 8 if p == "d" else 4
                N = (2 * n,) * d
                _, b, s = pick(d, sz, N, M, nthr)
                default = (16, 4, 4)[:d] + (1,) * (3 - d)
                _, _, s_sp = pick(d, sz, N, M, nthr, bins=[default])
                fmt = lambda bb, ss: " ".join(map(str, [d, p, f"{de:g}", n, *bb[:d], *[0] * (3 - d), ss]))
                print(fmt(b, s), *["0"] * 4, file=ff)
                print(fmt((0, 0, 0), s_sp), *["0"] * 4, file=fs)
        print(f"wrote picks_thesis_full_t{nthr}.txt and picks_thesis_sp_t{nthr}.txt")
