#!/usr/bin/env python3
"""Rewrite the appendix tables of selected configurations (tab:app_selection_picks,
tab:app_sp_picks) from raw/picks_thesis_{full,sp}_t{20,10,1}.txt, the configurations
chosen by traffic_model_thesis.py and measured in raw/l2/. Run after that script."""
import pathlib
from make_tables import splice, TEX

HERE = pathlib.Path(__file__).parent
DENS = ("0.125", "0.25", "0.5", "1", "2", "4", "8", "16", "32")
ROWS = [(d, p) for d in (1, 2, 3) for p in ("d", "f")]
NAME = {"d": "double", "f": "single"}


def sp_fmt(s):
    return f"${s / 1e6:.1f}$M" if s >= 1e6 else f"${s / 1e3:.0f}$k"


def load(kind, t):
    out = {}
    for line in open(HERE / "raw" / f"picks_thesis_{kind}_t{t}.txt"):
        x = line.split()
        d = int(x[0])
        out[(d, x[1], x[2])] = (x[4:4 + d], int(x[7]))
    return out


def body(kind):
    lines = []
    for i, t in enumerate((20, 10, 1)):
        if i:
            lines.append("        \\midrule")
        lines.append(f"        \\multicolumn{{10}}{{l}}{{\\emph{{${t}$ thread{'s' if t > 1 else ''}}}}} \\\\")
        P = load(kind, t)
        for d, p in ROWS:
            cells = []
            for de in DENS:
                b, s = P[(d, p, de)]
                cells.append(f"${'{\\times}'.join(b)}$ / {sp_fmt(s)}" if kind == "full" else sp_fmt(s))
            lines.append(f"        {d}D {NAME[p]} & " + " & ".join(cells) + " \\\\")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    path = TEX / "07_appendix_selection.tex"
    text = path.read_text()
    text = splice(text, "tab:app_selection_picks", body("full"))
    text = splice(text, "tab:app_sp_picks", body("sp"))
    path.write_text(text)
    print("rewrote the two tables of selected configurations in", path)
