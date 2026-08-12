# -*- coding: utf-8 -*-
"""Stage-2 fitter: optimize weights for RANK fidelity + selftest gates + SSE."""
import random
import numpy as np
from calibration_data import SWEEP_CASES
from sweep_features import featurize, parse_dayun, dayun_at

FEATS = ["zhu_fuyin", "tkdc", "suiyun_binglin", "stem_fuyin", "stem_he",
         "stem_ke_out", "stem_ke_in", "branch_fuyin", "branch_chong",
         "branch_liuhe", "branch_hai", "xing_pair", "zixing", "san_zi_tong",
         "banhe", "banhui", "sanxing_full", "sanhe_full", "sanhui_full"]

FLAGS = {"zhu_excl_components": True, "tkdc_excl_chong": True,
         "triple_use_dayun": True, "dayun_factor": 0.5, "use_palace": True}

# precompute feature vectors for every window year of every case
CASES = {}
for name, c in SWEEP_CASES.items():
    dy = parse_dayun(c["dayun"])
    pillars = c["pillars"].split()
    lo, hi = c["window"]
    feats = {y: featurize(pillars, dayun_at(dy, y), y, FLAGS) for y in range(lo, hi + 1)}
    X = {y: np.array([f.get(k, 0) for k in FEATS], float) for y, f in feats.items()}
    CASES[name] = (X, c["recorded"])
# wangshuang full window for selftest
_ws = SWEEP_CASES["wangshuang"]
_dy = parse_dayun(_ws["dayun"])
WS_X = {y: np.array([featurize(_ws["pillars"].split(), dayun_at(_dy, y), y, FLAGS).get(k, 0)
                     for k in FEATS], float) for y in range(1990, 2036)}


def objective(w):
    w = np.array(w)
    sse = 0.0
    inv = 0
    for name, (X, rec) in CASES.items():
        scores = {y: float(X[y] @ w) for y in X}
        for y, r in rec.items():
            sse += (scores[y] - r) ** 2
        years = list(rec)
        for i in range(len(years)):
            for j in range(i + 1, len(years)):
                a, b = years[i], years[j]
                if rec[a] == rec[b]:
                    continue
                hi_y, lo_y = (a, b) if rec[a] > rec[b] else (b, a)
                if scores[hi_y] < scores[lo_y] - 1e-9 and rec[hi_y] - rec[lo_y] >= 3:
                    inv += 1
    # gates
    gate_pen = 0
    ws_scores = {y: float(WS_X[y] @ w) for y in WS_X}
    ws_rank = sorted(ws_scores, key=lambda y: -ws_scores[y])
    if ws_rank.index(2012) + 1 > 4:
        gate_pen += 1
    if ws_rank.index(2030) + 1 > 3:
        gate_pen += 1
    chao_X, chao_rec = CASES["chao"]
    ch_scores = {y: float(chao_X[y] @ w) for y in chao_X}
    ch_rank = sorted(ch_scores, key=lambda y: -ch_scores[y])
    if ch_rank[0] != 2026:
        gate_pen += 1
    if ch_rank.index(2027) + 1 <= 6:
        gate_pen += 1
    return sse + 25 * inv + 400 * gate_pen, sse, inv, gate_pen


def anneal(seed, iters=20000):
    rnd = random.Random(seed)
    w = [25 if f == "zhu_fuyin" else 13 if f == "tkdc" else rnd.choice([2, 5, 8]) for f in FEATS]
    cur, *_ = objective(w)
    best_w, best = list(w), cur
    temp = 30.0
    for it in range(iters):
        temp *= 0.9997
        i = rnd.randrange(len(FEATS))
        w2 = list(w)
        w2[i] = max(0.0, w2[i] + rnd.choice([-3, -2, -1, -0.5, 0.5, 1, 2, 3]))
        e, *_ = objective(w2)
        if e < cur or rnd.random() < np.exp((cur - e) / max(temp, 0.5)):
            cur, w = e, w2
            if e < best:
                best, best_w = e, list(w)
    return best, best_w


if __name__ == "__main__":
    results = [anneal(s) for s in range(8)]
    results.sort()
    best, w = results[0]
    obj, sse, inv, gates = objective(w)
    print(f"obj={obj:.1f} sse={sse:.1f} inversions={inv} gate_pen={gates}")
    for k, v in zip(FEATS, w):
        if v:
            print(f"  {k:<16}= {v}")
    print("WEIGHTS =", {k: v for k, v in zip(FEATS, w) if v})
