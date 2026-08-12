# -*- coding: utf-8 -*-
"""Feature extraction for liunian_sweep scoring (v2 rebuild).

featurize(pillars, dayun_gz, year) -> {mechanism: count}
Design flags let the fitter explore v1's exact counting conventions.
"""
from itertools import combinations
from bazi_tables import (CHONG, LIUHE, SANHE, SANHUI, SANXING, XING_PAIR, ZIXING,
                         WUHE, stem_ke, year_ganzhi)

HAI = {"子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "巳", "巳": "寅",
       "卯": "辰", "辰": "卯", "申": "亥", "亥": "申", "酉": "戌", "戌": "酉"}

XING_PAIRS = [{"寅", "巳"}, {"巳", "申"}, {"申", "寅"}, {"丑", "戌"}, {"戌", "未"}, {"未", "丑"},
              {"子", "卯"}]

DEFAULT_FLAGS = {
    "zhu_excl_components": True,   # 柱级伏吟命中时不再叠加该柱的干/支伏吟
    "tkdc_excl_chong": False,      # 天克地冲命中时不再叠加支冲
    "triple_use_dayun": True,      # 三刑/三合/三会 允许用大运支补第三字
    "dayun_factor": 1.0,           # 大运柱各机制权重系数
    "use_palace": False,           # 按宫位加权 (年0.9/月1.3/日1.0/时0.85, 大运=dayun_factor)
}
PALACE_W = [0.9, 1.3, 1.0, 0.85]


def _pair_feats(feats, ys, yb, ps, pb, prefix=""):
    if ys == ps and yb == pb:
        feats[prefix + "zhu_fuyin"] = feats.get(prefix + "zhu_fuyin", 0) + 1
        zhu = True
    else:
        zhu = False
    tkdc = (stem_ke(ys, ps) or stem_ke(ps, ys)) and CHONG.get(yb) == pb
    if tkdc:
        feats[prefix + "tkdc"] = feats.get(prefix + "tkdc", 0) + 1
    return zhu, tkdc


def featurize(pillars, dayun_gz, year, flags=None):
    """pillars: ['丙寅','戊戌','丙午','丙申']; dayun_gz: '甲午' or None."""
    fl = dict(DEFAULT_FLAGS)
    if flags:
        fl.update(flags)
    ygz = year_ganzhi(year)
    ys, yb = ygz[0], ygz[1]
    feats = {}

    def add(k, n=1.0):
        feats[k] = feats.get(k, 0) + n

    if fl["use_palace"]:
        targets = [(p[0], p[1], PALACE_W[i]) for i, p in enumerate(pillars)]
    else:
        targets = [(p[0], p[1], 1.0) for p in pillars]
    if dayun_gz:
        targets.append((dayun_gz[0], dayun_gz[1], fl["dayun_factor"]))
        if ygz == dayun_gz:
            add("suiyun_binglin")

    for ps, pb, w in targets:
        zhu = ys == ps and yb == pb
        if zhu:
            add("zhu_fuyin", w)
        tkdc = (stem_ke(ys, ps) or stem_ke(ps, ys)) and CHONG.get(yb) == pb
        if tkdc:
            add("tkdc", w)
        skip_comp = zhu and fl["zhu_excl_components"]
        # stem features
        if not skip_comp:
            if ys == ps:
                add("stem_fuyin", w)
            if WUHE.get(ys) == ps:
                add("stem_he", w)
            if stem_ke(ys, ps):
                add("stem_ke_out", w)
            elif stem_ke(ps, ys):
                add("stem_ke_in", w)
        # branch features
        if not skip_comp:
            if yb == pb:
                add("branch_fuyin", w)
        if CHONG.get(yb) == pb and not (tkdc and fl["tkdc_excl_chong"]):
            add("branch_chong", w)
        if LIUHE.get(yb) == pb:
            add("branch_liuhe", w)
        if HAI.get(yb) == pb:
            add("branch_hai", w)
        if {yb, pb} in XING_PAIRS:
            add("xing_pair", w)
        for trio in SANHE:
            if yb in trio and pb in trio and yb != pb:
                add("banhe", w)
        for trio in SANHUI:
            if yb in trio and pb in trio and yb != pb:
                add("banhui", w)

    # 自刑: year branch in 辰午酉亥 and present in chart/dayun -> once
    zix_hits = [pb for _, pb, _ in targets if pb == yb]
    if yb in ZIXING and zix_hits:
        add("zixing", 1.0)
    # 三字同: 流年支 == 大运支 == 某原局支
    if dayun_gz and dayun_gz[1] == yb and any(p[1] == yb for p in pillars):
        add("san_zi_tong", 1.0)

    # triples: year branch + two distinct-position branches completing a set;
    # dayun may supply one leg (weight = dayun_factor for that combination)
    trip = [(p[1], 1.0) for p in pillars]
    if dayun_gz and fl["triple_use_dayun"]:
        trip.append((dayun_gz[1], fl["dayun_factor"]))
    n = len(trip)
    for sets, feat in ((SANXING, "sanxing_full"), (SANHE, "sanhe_full"),
                       (SANHUI, "sanhui_full")):
        for i, j in combinations(range(n), 2):
            (a, wa), (b, wb) = trip[i], trip[j]
            for trio in sets:
                if {yb, a, b} == trio:
                    add(feat, min(wa, wb))
    return feats


def parse_dayun(spec):
    """'甲午:2023,癸巳:2033' -> [(start_year, gz)] sorted."""
    out = []
    for part in spec.split(","):
        gz, y = part.strip().split(":")
        out.append((int(y), gz))
    return sorted(out)


def dayun_at(dayun_list, year):
    cur = None
    for start, gz in dayun_list:
        if year >= start:
            cur = gz
    return cur
