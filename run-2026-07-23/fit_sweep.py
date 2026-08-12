# -*- coding: utf-8 -*-
"""Fit liunian_sweep weights against recorded v1 scores (dev tool).

Least-squares per design-flag combo, then integer/half rounding + local polish.
"""
import itertools
import numpy as np
from calibration_data import SWEEP_CASES
from sweep_features import featurize, parse_dayun, dayun_at

FEATS = ["zhu_fuyin", "tkdc", "suiyun_binglin", "stem_fuyin", "stem_he",
         "stem_ke_out", "stem_ke_in", "branch_fuyin", "branch_chong",
         "branch_liuhe", "branch_hai", "xing_pair", "zixing", "san_zi_tong", "banhe", "banhui",
         "sanxing_full", "sanhe_full", "sanhui_full"]


def build_rows(flags):
    rows = []
    for name, c in SWEEP_CASES.items():
        dy = parse_dayun(c["dayun"])
        pillars = c["pillars"].split()
        for year, score in c["recorded"].items():
            f = featurize(pillars, dayun_at(dy, year), year, flags)
            rows.append((name, year, [f.get(k, 0) for k in FEATS], score))
    return rows


def polish(X, y, w, grid, iters=6):
    best = float(np.sum((X @ w - y) ** 2))
    for _ in range(iters):
        improved = False
        for i in range(len(w)):
            for v in grid:
                w2 = w.copy()
                w2[i] = v
                e = float(np.sum((X @ w2 - y) ** 2))
                if e < best - 1e-9:
                    best, w = e, w2
                    improved = True
        if not improved:
            break
    return w, best


def main():
    flag_space = {
        "zhu_excl_components": [True, False],
        "tkdc_excl_chong": [True, False],
        "triple_use_dayun": [True, False],
        "dayun_factor": [1.0, 0.8, 0.5],
        "use_palace": [True, False],
    }
    keys = list(flag_space)
    results = []
    for combo in itertools.product(*flag_space.values()):
        flags = dict(zip(keys, combo))
        rows = build_rows(flags)
        X = np.array([r[2] for r in rows], dtype=float)
        y = np.array([r[3] for r in rows], dtype=float)
        w, *_ = np.linalg.lstsq(X, y, rcond=None)
        w = np.clip(w, 0, None)
        sse_f = float(np.sum((X @ w - y) ** 2))
        # round to nearest 0.5 then polish on 0.5 grid 0..30
        w_r = np.round(w * 2) / 2
        grid = [g / 2 for g in range(0, 61)]
        w_p, sse_p = polish(X, y, w_r, grid)
        results.append((sse_p, sse_f, flags, w_p, rows))
    results.sort(key=lambda r: r[0])
    for sse_p, sse_f, flags, w, rows in results[:5]:
        print(f"SSE(poly)={sse_p:7.1f}  SSE(float)={sse_f:7.1f}  {flags}")
    sse_p, sse_f, flags, w, rows = results[0]
    print("\n=== BEST ===", flags)
    for k, v in zip(FEATS, w):
        if v:
            print(f"  {k:<16}= {v}")
    X = np.array([r[2] for r in rows], dtype=float)
    y = np.array([r[3] for r in rows], dtype=float)
    pred = X @ np.array(w)
    print("\nresiduals:")
    for (name, year, _, rec), p in zip(rows, pred):
        mark = "" if abs(p - rec) < 2.5 else "  <-- off"
        print(f"  {name:<12}{year}: rec {rec:>3}  pred {p:6.1f}{mark}")


if __name__ == "__main__":
    main()
