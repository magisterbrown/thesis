#!/usr/bin/env python3
"""Plot DUCC FFT throughput against the ideal 1/log2(N) shape.

Styled after perftest/plot_ducc_fft_bench.py in the finufft repo, which is the
script that produced the exploratory version of this figure; this is the
thesis-figure copy, with paths resolved next to the CSV and no CLI.

Data: complex-to-complex out-of-place DUCC FFTs in one, two and three
dimensions, single and double precision, on 1 and 16 threads. The sweep sizes
each dimension so the TOTAL element count (N^dim) follows a common ladder,
capped by a 1 GiB budget, so the dimensions are compared at matched problem
sizes rather than matched per-axis N. Each point is a Google Benchmark mean
over eight repetitions.

Throughput is N^dim points per unit cpu time, so higher is better and the
curves stay comparable across sizes. Each panel carries a dashed C/log2(N)
reference on the SAME axis: an FFT costs O(N log N), so at a fixed cost per
butterfly the point rate should fall off as 1/log2(N). C is fitted (median of
throughput * log2(N) over the panel's busiest thread count), so the reference
is a shape to compare against rather than an absolute prediction -- where the
measured curve drops away from it, something other than butterfly count is
paying: cache, bandwidth, or radix.

Vertical lines mark where the working set (N^dim complex elements) crosses the
L2 and L3 sizes recorded in the CSV's own columns, which is usually where the
throughput curve visibly bends.

Writes ducc_fft_scaling.{pdf,png} next to this script.
"""
import csv
import math
import pathlib
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent

BYTES_PER_ELEMENT = {"f": 8, "d": 16}  # complex<float>, complex<double>
PREC_NAME = {"f": "float", "d": "double"}
IDEAL_STYLE = dict(color="#3f3f46", ls="-.", lw=1.5)  # neutral reference


def load_rows(csv_path: pathlib.Path) -> list:
    with open(csv_path, newline="") as f:
        rows = []
        for r in csv.DictReader(f):
            r["dim"]            = int(r["dim"])
            r["nthreads"]       = int(r["nthreads"])
            r["N"]              = float(r["N"])
            r["cpu_time_ns"]    = float(r["cpu_time_ns"])
            r["l2_cache_bytes"] = float(r["l2_cache_bytes"]) if r["l2_cache_bytes"] else None
            r["l3_cache_bytes"] = float(r["l3_cache_bytes"]) if r["l3_cache_bytes"] else None
            rows.append(r)
        return rows


def cache_boundary_n(cache_bytes, dim: int, prec: str):
    """Per-axis N at which an N^dim array of this precision fills cache_bytes."""
    if not cache_bytes:
        return None
    return (cache_bytes / BYTES_PER_ELEMENT[prec]) ** (1.0 / dim)


def main():
    rows = load_rows(HERE / "ducc_fft_bench_results.csv")
    if not rows:
        raise SystemExit("No rows read from ducc_fft_bench_results.csv")

    dims = sorted({r["dim"] for r in rows})
    precs = sorted({r["prec"] for r in rows})  # 'd' before 'f'
    nthreads_vals = sorted({r["nthreads"] for r in rows})
    colors = plt.cm.viridis([i / max(1, len(nthreads_vals) - 1)
                             for i in range(len(nthreads_vals))])
    color_of = dict(zip(nthreads_vals, colors))

    fig, axes = plt.subplots(len(dims), len(precs),
                             figsize=(6.0 * len(precs), 3.9 * len(dims)),
                             squeeze=False)

    for i, dim in enumerate(dims):
        for j, prec in enumerate(precs):
            ax = axes[i][j]
            subset = [r for r in rows if r["dim"] == dim and r["prec"] == prec]
            by_threads = defaultdict(list)
            for r in subset:
                by_threads[r["nthreads"]].append(r)

            for nthreads in nthreads_vals:
                pts = sorted(by_threads.get(nthreads, []), key=lambda r: r["N"])
                if not pts:
                    continue
                xs = [r["N"] for r in pts]
                # Throughput in Mpoint/s: N^dim points over the cpu time.
                ys = [(r["N"] ** dim) * 1e3 / r["cpu_time_ns"] for r in pts]
                ax.plot(xs, ys, marker="o", label=f"{nthreads} thr",
                        color=color_of[nthreads])

            ns = sorted({r["N"] for r in subset})

            # Ideal O(N log N) shape on the throughput axis, fitted to the
            # busiest thread count so it sits on that curve's own level.
            if ns:
                ref_threads = max(by_threads) if by_threads else None
                ref_pts = by_threads.get(ref_threads, [])
                scales = sorted((r["N"] ** dim) * 1e3 / r["cpu_time_ns"] * math.log2(r["N"])
                                for r in ref_pts if r["N"] > 1)
                if scales:
                    c = scales[len(scales) // 2]  # median: robust to the cache cliffs
                    ax.plot(ns, [c / math.log2(n) for n in ns],
                            label=f"C / log$_2$ N ({ref_threads} thr fit)",
                            **IDEAL_STYLE)

            ax.set_xscale("log")
            # Linear throughput: the values span well under a decade, and a log
            # y-axis flattens exactly the differences (the multi-thread hump,
            # the fall past L3) this plot is about.
            ax.set_ylim(bottom=0)

            # Cache boundaries, drawn after the ylim is fixed so the labels land
            # at the top of the panel rather than wherever autoscaling left it.
            l2 = cache_boundary_n(subset[0]["l2_cache_bytes"], dim, prec) if subset else None
            l3 = cache_boundary_n(subset[0]["l3_cache_bytes"], dim, prec) if subset else None
            for val, label, style in ((l2, "L2", ":"), (l3, "L3", "--")):
                if val is not None:
                    ax.axvline(val, color="grey", linestyle=style, linewidth=1)
                    ax.text(val, 0.98, label, transform=ax.get_xaxis_transform(),
                            rotation=90, va="top", ha="right", color="grey", fontsize=8)

            ax.set_title(f"dim={dim}, prec={PREC_NAME.get(prec, prec)}")
            ax.set_xlabel("N (per-axis size)")
            ax.set_ylabel("throughput (Mpoint/s)")
            ax.grid(True, which="both", linestyle=":", linewidth=0.5)
            # One legend for the whole figure: every panel draws the same
            # series, so repeating it five more times only eats plot area.
            if i == 0 and j == 0:
                ax.legend(fontsize=8, loc="lower left", framealpha=0.9)

    fig.tight_layout()
    fig.savefig(HERE / "ducc_fft_scaling.pdf")
    fig.savefig(HERE / "ducc_fft_scaling.png", dpi=200)
    print("wrote", HERE / "ducc_fft_scaling.pdf", "and .png")


if __name__ == "__main__":
    main()
