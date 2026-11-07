#!/usr/bin/env python3
"""Convert the Google Benchmark JSON files of the Broadwell re-run of the sigma
sweep into the CSV layout plot.py reads (same columns as sigma_sweep_1thread.csv).

Data: produced on the Xeon E5-2698 v4 of Section 3.1 (Table 3.1) by
perftest/sigma_sweep (built natively there, DUCC FFT), run on ONE thread
(--nthreads 1, OMP_NUM_THREADS=1) pinned to one core with taskset, 8 iterations
per point. Same configurations, densities and tolerances as the earlier Ice Lake
run, except that every configuration is now single-threaded (the earlier 3D and
one 2D configuration had used all threads).

Usage: python3 json_to_csv.py JSON_DIR OUT.csv
"""
import csv
import json
import pathlib
import re
import sys

FIELDS = ["configuration", "prec", "dim", "size", "density", "tol",
          "upsampfac", "complexity", "cpu_time_ns", "real_time_ns", "time_unit"]

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
rows = []
for js in sorted(src.glob("json_*.json")):
    m = re.match(r"json_(.+)_([0-9.e+-]+)\.json$", js.name)
    label, tol = m.group(1), float(m.group(2))
    size_part, prec_part = label.split("-")[0], label.split("-")[1]
    dims = [int(v) for v in size_part.split("x")]
    dim = sum(1 for v in dims if v > 1)
    try:
        data = json.loads(js.read_text())
    except json.JSONDecodeError:
        print(f"skipping {js.name}: incomplete (run still in progress?)")
        continue
    for bm in data.get("benchmarks", []):
        rows.append({
            "configuration": label,
            "prec": prec_part[-1],
            "dim": dim,
            "size": dims[0],
            "density": bm["density"],
            "tol": tol,
            "upsampfac": bm["upsampfac"],
            "complexity": bm["complexity"],
            "cpu_time_ns": bm["cpu_time"],
            "real_time_ns": bm["real_time"],
            "time_unit": bm["time_unit"],
        })

with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
print(f"wrote {out}: {len(rows)} rows from {len(list(src.glob('json_*.json')))} files")
