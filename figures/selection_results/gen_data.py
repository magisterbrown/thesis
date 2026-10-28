#!/usr/bin/env python3
"""Reduce the raw selection-sweep logs in raw/ to data.csv and the appendix values.

Each log line is one timer record of one run of one test transform, tagged with
the dimension, precision, density, repetition, and which configuration was used:
the library defaults (dflt), the full selection of bin dimensions and S_max
(best), or the selection of S_max alone with the bins left at the default
(sponly). The timers are the bin sort ([sort_phase] wall, [sort_busy] CPU) and
the spreading stage ([phase] wall, [busy] CPU).

Two details of the logs matter. The bin sort runs single-threaded whenever the
library chooses that path, and then emits no [sort_phase] record; its wall time
is the [sort_busy] CPU time, since one thread was working. And in three
dimensions no bin larger than the default fits in L1d, so the full selection
keeps the default bins and sponly would repeat best; those runs were skipped and
best is read in their place.

Writes data.csv (the chapter tables) and appendix.csv (every transform).
"""
import csv
import pathlib
import statistics as st
from collections import defaultdict

HERE = pathlib.Path(__file__).parent
SEGMENTS = (("uniform_20", "sw_uni20.txt"), ("uniform_10", "sw_uni10.txt"),
            ("uniform_1", "sw_uni1.txt"), ("exponential_20", "sw_exp20.txt"))
DENSITIES = (0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32)
PRECISIONS = (("double", "d"), ("single", "f"))
GROUPS = tuple(f"{d}D {p}" for d in (1, 2, 3) for p, _ in PRECISIONS)
# table name -> (metric, numerator variant, denominator variant)
TABLES = (("speedup", "wall", "best", "dflt"),
          ("work", "cpu", "best", "dflt"),
          ("sp", "wall", "sponly", "dflt"),
          ("sp_work", "cpu", "sponly", "dflt"),
          ("bins_work", "cpu", "best", "sponly"))


def load(path):
    """raw log -> {(dim, prec, density, variant): {timer: [values]}}"""
    recs = defaultdict(lambda: defaultdict(list))
    for line in open(path):
        p = line.split()
        if len(p) < 9 or not p[8].startswith("["):
            continue
        key = (int(p[0][1:]), p[1][4:], float(p[2][4:]), p[4])
        kv = dict(x.split("=", 1) for x in p if "=" in x and "imbalance" not in x)
        tag = p[8].strip("[]")
        if tag == "sort_phase":
            recs[key]["sort_wall"].append(float(kv["wall"]))
        elif tag == "sort_busy":
            recs[key]["sort_cpu"].append(float(kv["work"]))
        elif tag == "phase":
            recs[key]["sp_wall"].append(float(kv["wall"]))
        elif tag == "busy":
            recs[key]["sp_cpu"].append(float(kv["work"]))
    return recs


def time_of(recs, dim, prec, dens, variant, metric):
    """Sort plus spreading, as wall or CPU time; the best of the repetitions."""
    if dim == 3 and variant == "sponly":
        variant = "best"                    # same configuration, not rerun
    r = recs[(dim, prec, dens, variant)]
    if not r["sp_cpu"]:
        raise KeyError(f"no records for {dim}D {prec} {dens} {variant}")
    if metric == "cpu":
        return min(r["sort_cpu"]) + min(r["sp_cpu"])
    # the single-threaded sort path emits no wall record; its CPU time is its wall time
    sort = min(r["sort_wall"]) if r["sort_wall"] else min(r["sort_cpu"])
    return sort + min(r["sp_wall"])


def main():
    data = {seg: load(HERE / "raw" / f) for seg, f in SEGMENTS}
    rows, appendix = [], []
    for name, metric, num, den in TABLES:
        ratios = defaultdict(lambda: defaultdict(list))
        for seg, recs in data.items():
            for dim, (prec, code) in ((d, p) for d in (1, 2, 3) for p in PRECISIONS):
                for dens in DENSITIES:
                    args = (recs, dim, code, dens)
                    r = time_of(*args, den, metric) / time_of(*args, num, metric)
                    ratios[f"{dim}D {prec}"][seg].append(r)
                    ratios["all 54"][seg].append(r)
                    appendix.append({"table": name, "segment": seg,
                                     "row": f"{dim}D {prec}", "density": dens,
                                     "ratio": f"{r:.3f}"})
        for group in GROUPS + ("all 54",):
            row = {"table": name, "row": group}
            for seg, _ in SEGMENTS:
                row[seg] = f"{st.geometric_mean(ratios[group][seg]):.2f}"
            rows.append(row)

    with open(HERE / "data.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["table", "row"] + [s for s, _ in SEGMENTS])
        w.writeheader()
        w.writerows(rows)
    with open(HERE / "appendix.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["table", "segment", "row", "density", "ratio"])
        w.writeheader()
        w.writerows(appendix)
    print("wrote", HERE / "data.csv", "and", HERE / "appendix.csv")


if __name__ == "__main__":
    main()
