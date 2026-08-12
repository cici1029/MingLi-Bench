# -*- coding: utf-8 -*-
"""应期枚举 liunian_sweep — v2 rebuild 2026-08-12.

流年 × (原局四柱 + 大运) 作用强度枚举。表只管作用强度（结构层），
喜忌量级仍由 GATE 2 定调裁量（skill xuanxue-consult GATE 4 纪律）。

v1 (2026-08-07 首跑, lost) 的分数不可精确复刻；v2 权重按 6 盘 33 个记录分
拟合 + 排名保真度约束（见 fit_sweep2.py / test_regression.py）。
⚠️ v2 分数与 person 页记录的 v1 分数存在 ±7 偏差；Top 集合与序经回归验证。

Usage (与 person 页存的命令行兼容):
  python3 liunian_sweep.py '丙寅 戊戌 丙午 丙申' \
      --dayun '丁酉:1993,丙申:2003,乙未:2013,甲午:2023' --from 2026 --to 2045
  python3 liunian_sweep.py --selftest
"""
import argparse
from sweep_features import featurize, parse_dayun, dayun_at, DEFAULT_FLAGS
from bazi_tables import year_ganzhi

WEIGHTS = {
    "zhu_fuyin": 16.0,     # 柱级伏吟（干支全同某柱）
    "tkdc": 15.0,          # 天克地冲
    "suiyun_binglin": 0.0, # 岁运并临（并入柱级伏吟对大运柱的命中）
    "stem_fuyin": 0.0,
    "stem_he": 1.0,        # 天干五合
    "stem_ke_out": 3.0,    # 流年干克柱干
    "stem_ke_in": 0.0,
    "branch_fuyin": 5.5,   # 支伏吟
    "branch_chong": 12.5,  # 支冲
    "branch_liuhe": 5.5,   # 六合绊
    "branch_hai": 8.5,     # 相害
    "xing_pair": 5.5,      # 刑（两字）
    "zixing": 8.0,         # 自刑（辰午酉亥，命中记一次）
    "san_zi_tong": 6.5,    # 流年支=运支=原局支 三字同
    "banhe": 2.0,          # 半合
    "banhui": 0.0,
    "sanxing_full": 0.5,   # 三刑全（流年补第三字）
    "sanhe_full": 4.0,     # 三合全（拱填实）
    "sanhui_full": 5.5,    # 三会全
}
FLAGS = {"zhu_excl_components": True, "tkdc_excl_chong": True,
         "triple_use_dayun": True, "dayun_factor": 0.5, "use_palace": True}

FEAT_LABEL = {
    "zhu_fuyin": "柱级伏吟", "tkdc": "天克地冲", "suiyun_binglin": "岁运并临",
    "stem_fuyin": "干伏吟", "stem_he": "干合", "stem_ke_out": "干克出",
    "stem_ke_in": "干被克", "branch_fuyin": "支伏吟", "branch_chong": "支冲",
    "branch_liuhe": "六合", "branch_hai": "相害", "xing_pair": "刑",
    "zixing": "自刑", "san_zi_tong": "三字同", "banhe": "半合", "banhui": "半会",
    "sanxing_full": "三刑全", "sanhe_full": "三合全/拱填", "sanhui_full": "三会全",
}


def sweep(pillars, dayun_list, y_from, y_to):
    rows = []
    for year in range(y_from, y_to + 1):
        dy = dayun_at(dayun_list, year)
        f = featurize(pillars, dy, year, FLAGS)
        score = sum(WEIGHTS.get(k, 0) * v for k, v in f.items())
        mechs = [FEAT_LABEL[k] for k, v in sorted(f.items(), key=lambda kv: -WEIGHTS.get(kv[0], 0) * kv[1])
                 if v and WEIGHTS.get(k, 0) > 0]
        rows.append({"year": year, "gz": year_ganzhi(year), "dayun": dy,
                     "score": round(score, 1), "_raw": score, "mechs": mechs})
    rows.sort(key=lambda r: -r["_raw"])
    return rows


def main():
    ap = argparse.ArgumentParser(description="流年应期枚举 (v2)")
    ap.add_argument("pillars", nargs="?", help="'年柱 月柱 日柱 时柱'")
    ap.add_argument("--dayun", help="'干支:起年,干支:起年,...'")
    ap.add_argument("--from", dest="y_from", type=int)
    ap.add_argument("--to", dest="y_to", type=int)
    ap.add_argument("--top", type=int, default=0, help="只显示前 N 行")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        import test_regression
        raise SystemExit(test_regression.run_sweep_selftest())

    if not (args.pillars and args.dayun and args.y_from and args.y_to):
        ap.error("需要 pillars --dayun --from --to（或 --selftest）。原局+大运双输入缺一不可。")
    pillars = args.pillars.split()
    if len(pillars) != 4:
        ap.error("四柱须为空格分隔的 4 组干支")
    rows = sweep(pillars, parse_dayun(args.dayun), args.y_from, args.y_to)
    shown = rows[:args.top] if args.top else rows
    print(f"{'流年':<6}{'干支':<4}{'大运':<4}{'强度':<7}机制")
    for r in shown:
        print(f"{r['year']:<6}{r['gz']:<4}{r['dayun'] or '--':<4}[{r['score']:>5.1f}] {'+'.join(r['mechs']) or '--'}")
    print("\n⚠️ 表只管作用强度；喜忌量级由定盘裁量。v2 rebuild：分数与 2026-08-07 前记录的 v1 分数不可比，序已回归验证。")


if __name__ == "__main__":
    main()
