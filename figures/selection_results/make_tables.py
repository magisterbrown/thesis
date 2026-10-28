#!/usr/bin/env python3
"""Rewrite the selection tables of Chapter 6 and the appendix from the CSVs.

The numbers in data.csv and appendix.csv come from the same raw logs as the
figures, so this keeps the two in step: run gen_data.py, then this.

Each table is a grid of ratios of the default configuration against a selected
one, so every cell is replaced and only the surrounding LaTeX is left alone.
"""
import csv
import pathlib
import re
from collections import defaultdict

HERE = pathlib.Path(__file__).parent
TEX = HERE.parent.parent / "chapters"
SEGMENTS = (("uniform_20", r"uniform distribution, $20$ threads"),
            ("uniform_10", r"uniform distribution, $10$ threads"),
            ("uniform_1", r"uniform distribution, $1$ thread"),
            ("exponential_20", r"exponential distribution, $20$ threads"))
GROUPS = tuple(f"{d}D {p}" for d in (1, 2, 3) for p in ("double", "single"))
DENSITIES = ("0.125", "0.25", "0.5", "1", "2", "4", "8", "16", "32")
# label -> table name in the CSVs
CHAPTER = {"tab:selection_results": "speedup",
           "tab:selection_work": "work",
           "tab:selection_sp_work": "sp_work"}
APPENDIX = {"tab:app_selection_speedup": "speedup",
            "tab:app_selection_work": "work",
            "tab:app_sp_speedup": "sp",
            "tab:app_sp_work": "sp_work"}


def row(label, values, pad):
    cells = " & ".join(f"${v}$" for v in values)
    return f"        {label:<{pad}} & {cells} \\\\"


def splice(text, label, body):
    """Replace a table's rows, between the column headings and \\bottomrule."""
    end = text.index(f"\\label{{{label}}}")
    start = text.rindex(r"\begin{table}", 0, end)
    block = text[start:end]
    head = block.index("\\midrule\n") + len("\\midrule\n")
    tail = block.index("        \\bottomrule")
    return text[:start] + block[:head] + body + block[tail:] + text[end:]


def main():
    chapter = defaultdict(dict)
    for r in csv.DictReader(open(HERE / "data.csv")):
        chapter[r["table"]][r["row"]] = [r[s] for s, _ in SEGMENTS]
    appendix = defaultdict(dict)
    for r in csv.DictReader(open(HERE / "appendix.csv")):
        appendix[r["table"]][(r["segment"], r["row"], r["density"])] = \
            f'{float(r["ratio"]):.2f}'

    for path, labels, builder in (
            (TEX / "05_parameter_tuning.tex", CHAPTER, "chapter"),
            (TEX / "07_appendix_selection.tex", APPENDIX, "appendix")):
        text = path.read_text()
        for label, name in labels.items():
            if builder == "chapter":
                lines = [row(g, chapter[name][g], 9) for g in GROUPS]
                lines += ["        \\midrule",
                          row(r"all $54$", chapter[name]["all 54"], 0)]
            else:
                lines = []
                for i, (seg, caption) in enumerate(SEGMENTS):
                    if i:
                        lines.append("        \\midrule")
                    lines.append(f"        \\multicolumn{{10}}{{l}}{{\\emph{{{caption}}}}} \\\\")
                    lines += [row(g, [appendix[name][(seg, g, d)] for d in DENSITIES], 9)
                              for g in GROUPS]
            text = splice(text, label, "\n".join(lines) + "\n")
        path.write_text(text)
        print("rewrote", len(labels), "tables in", path)


if __name__ == "__main__":
    main()
