# liunian_sweep.py — 应期枚举器 (2026-08-07, 王双 Y2 婚期失手催生)
# 逐年机械枚举: 流年干支 x (原局四柱 + 当值大运) 的全部作用 → 打分排序。
# 目的: 盲断轮/前瞻从完整候选表里挑, 不从记忆里捞 (pattern-match 漏 2012 壬辰伏吟日柱案)。
# 用法:
#   python3 liunian_sweep.py '乙丑 壬午 壬辰 庚戌' \
#     --dayun '癸未:1990,甲申:2000,乙酉:2010,丙戌:2020,丁亥:2030,戊子:2040' \
#     --from 1990 --to 2035 [--top 12]
# 事实层工具: 只枚举与打分, 不判吉凶——喜忌定调仍在 GATE 2 人工裁量。
# ⚠️ 立春界 caveat: 表按公历年映射干支((y-1984)%60), 1月至2月初立春前的事件干支上属【前一年】的行
#   (例: 2010-01-31 事件属己丑年行, 不属庚寅行)。对表核事件时人工归位, 尤其冬季事件。
import argparse, sys

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
PALACE = ["年柱(祖上/父母/早年)", "月柱(父母/兄弟/提纲)", "日柱(自身/配偶宫)", "时柱(子女/晚运)"]

WUHE = {frozenset("甲己"), frozenset("乙庚"), frozenset("丙辛"), frozenset("丁壬"), frozenset("戊癸")}
CHONG = {frozenset("子午"), frozenset("丑未"), frozenset("寅申"), frozenset("卯酉"), frozenset("辰戌"), frozenset("巳亥")}
LIUHE = {frozenset("子丑"), frozenset("寅亥"), frozenset("卯戌"), frozenset("辰酉"), frozenset("巳申"), frozenset("午未")}
HAI = {frozenset("子未"), frozenset("丑午"), frozenset("寅巳"), frozenset("卯辰"), frozenset("申亥"), frozenset("酉戌")}
SANHE = {"水": set("申子辰"), "金": set("巳酉丑"), "火": set("寅午戌"), "木": set("亥卯未")}
SANHUI = {"北方水": set("亥子丑"), "东方木": set("寅卯辰"), "南方火": set("巳午未"), "西方金": set("申酉戌")}
XING3 = [set("寅巳申"), set("丑未戌")]
XING2 = {frozenset("子卯")}
ZIXING = set("辰午酉亥")
# 天干五行+阴阳 → 十神
WX = {"甲": ("木", 0), "乙": ("木", 1), "丙": ("火", 0), "丁": ("火", 1), "戊": ("土", 0),
      "己": ("土", 1), "庚": ("金", 0), "辛": ("金", 1), "壬": ("水", 0), "癸": ("水", 1)}
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
ZHI_MAIN = {"子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙",
            "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬"}

def shishen(day_gan, other_gan):
    dw, dy = WX[day_gan]; ow, oy = WX[other_gan]
    same = (dy == oy)
    if ow == dw: return "比肩" if same else "劫财"
    if SHENG[dw] == ow: return "食神" if same else "伤官"
    if KE[dw] == ow: return "偏财" if same else "正财"
    if KE[ow] == dw: return "七杀" if same else "正官"
    if SHENG[ow] == dw: return "偏印" if same else "正印"
    raise ValueError

def jiazi(i): return GAN[i % 10] + ZHI[i % 12]

def liunian_gz(year): return jiazi((year - 1984) % 60)

def branch_events(fz, targets, tag_of):
    """流年支 fz 对一组支 targets [(支, 标签)] 的两两作用。"""
    ev = []
    KU = set("辰戌丑未")
    for tz, tag in targets:
        pair = frozenset((fz, tz))
        if fz == tz: ev.append((f"伏吟{tag}{tz}", 6))
        if pair in CHONG:
            ev.append((f"冲{tag}{tz}", 8))
            if tz in KU: ev.append((f"冲开{tag}{tz}库", 3))
        if pair in LIUHE: ev.append((f"合{tag}{tz}", 5))
        if pair in HAI: ev.append((f"害{tag}{tz}", 4))
        if pair in XING2 or (len(pair) == 2 and any(pair <= s for s in XING3)):
            ev.append((f"刑{tag}{tz}", 5))
            if tz in KU: ev.append((f"刑开{tag}{tz}库", 3))
    return ev

def sweep(pillars, dayun, y_from, y_to):
    day_gan = pillars[2][0]
    gans = [p[0] for p in pillars]; zhis = [p[1] for p in pillars]
    rows = []
    for y in range(y_from, y_to + 1):
        gz = liunian_gz(y); fg, fz = gz[0], gz[1]
        # 当值大运
        yun = None
        for gzr, start in dayun:
            if y >= start: yun = (gzr, start)
        yun_gz = yun[0] if yun else None
        ev = []
        ss = shishen(day_gan, fg)
        ev.append((f"年干{fg}={ss}透", 2))
        ssz = shishen(day_gan, ZHI_MAIN[fz])
        # 柱级伏吟/并临 (干支全同, 权重最高)
        for i, p in enumerate(pillars):
            if gz == p:
                ev.append((f"流年{gz}=伏吟{PALACE[i]}·柱级", 12))
            elif fz == p[1] and frozenset((fg, p[0])) in WUHE:
                ev.append((f"天合地同{PALACE[i]}", 6))
            elif frozenset((fg, p[0])) in WUHE and frozenset((fz, p[1])) in CHONG:
                ev.append((f"天合地冲{PALACE[i]}", 7))
            elif KE.get(WX[fg][0]) == WX[p[0]][0] and frozenset((fz, p[1])) in CHONG:
                ev.append((f"天克地冲{PALACE[i]}(反吟)", 9))
        if yun_gz:
            if gz == yun_gz: ev.append((f"岁运并临({yun_gz}运)", 12))
            if fz == yun_gz[1]: ev.append((f"伏吟运支{yun_gz[1]}", 4))
            if frozenset((fz, yun_gz[1])) in CHONG: ev.append((f"冲运支{yun_gz[1]}", 6))
        # 干层: 合原局干 / 合运干 / 伏吟干
        for i, g in enumerate(gans):
            if frozenset((fg, g)) in WUHE: ev.append((f"年干{fg}合{PALACE[i][:2]}{g}", 4))
        if fg == day_gan: ev.append((f"年干伏吟日主{day_gan}", 3))
        if yun_gz and frozenset((fg, yun_gz[0])) in WUHE: ev.append((f"年干{fg}合运干{yun_gz[0]}", 3))
        # 支层: 对原局四支 + 运支
        tgt = [(zhis[i], PALACE[i][:2]) for i in range(4)]
        ev += branch_events(fz, tgt, None)
        # 自刑
        if fz in ZIXING and fz in zhis: ev.append((f"{fz}{fz}自刑", 5))
        # 三合局成/半合: 流年支 + (原局支+运支) 凑局
        pool = zhis + ([yun_gz[1]] if yun_gz else [])
        for wux, s in SANHE.items():
            if fz in s:
                others = s - {fz}
                have = others & set(pool)
                if len(have) == 2: ev.append((f"三合{wux}局成({fz}+{'+'.join(sorted(have))})", 9))
                elif len(have) == 1: ev.append((f"半合{wux}({fz}+{list(have)[0]})", 3))
        for name, s in SANHUI.items():
            if fz in s and len((s - {fz}) & set(pool)) == 2:
                ev.append((f"三会{name}({fz})", 8))
        # 三刑齐 (流年补全)
        for s in XING3:
            if fz in s and len((s - {fz}) & set(pool)) == 2:
                ev.append((f"三刑齐({'+'.join(sorted(s))})", 9))
        score = sum(w for _, w in ev)
        rows.append((y, gz, ss, ssz, yun_gz, ev, score))
    return rows

def selftest():
    """回归 gate: 王双 2012 伏吟夫宫必在 2010-2032 top5; Chao 2015 并临/2016/2018 柱级伏吟必现。"""
    ws = sweep("乙丑 壬午 壬辰 庚戌".split(),
               [("癸未",1990),("甲申",2000),("乙酉",2010),("丙戌",2020),("丁亥",2030),("戊子",2040)], 2010, 2032)
    top5 = [r[0] for r in sorted(ws, key=lambda r: -r[6])[:5]]
    assert 2012 in top5, f"FAIL: 王双 2012 不在 top5 {top5}"
    assert any("伏吟日柱" in e for e, _ in [x for r in ws if r[0]==2012 for x in r[5]]), "FAIL: 2012 缺伏吟日柱标签"
    ch = sweep("丙寅 戊戌 丙午 丙申".split(),
               [("丁酉",1993),("丙申",2003),("乙未",2013),("甲午",2023)], 2013, 2028)
    def evs(y): return [e for r in ch if r[0]==y for e,_ in r[5]]
    assert any("岁运并临" in e for e in evs(2015)), "FAIL: chao 2015 并临"
    assert any("伏吟时柱" in e and "柱级" in e for e in evs(2016)), "FAIL: chao 2016 柱级伏吟时柱"
    assert any("伏吟月柱" in e and "柱级" in e for e in evs(2018)), "FAIL: chao 2018 柱级伏吟月柱"
    print("selftest OK: 王双 2012 top5 + chao 2015/2016/2018 全命中")

def main():
    ap = argparse.ArgumentParser()
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest(); return
    ap.add_argument("pillars", help="'年柱 月柱 日柱 时柱'")
    ap.add_argument("--dayun", required=True, help="'干支:起年,干支:起年,...'")
    ap.add_argument("--from", dest="y_from", type=int, required=True)
    ap.add_argument("--to", dest="y_to", type=int, required=True)
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()
    pillars = a.pillars.split()
    assert len(pillars) == 4, "需要四柱"
    dayun = []
    for item in a.dayun.split(","):
        gz, yr = item.split(":"); dayun.append((gz, int(yr)))
    rows = sweep(pillars, dayun, a.y_from, a.y_to)
    print(f"# 应期全量枚举: {' '.join(pillars)} (日主{pillars[2][0]})  {a.y_from}-{a.y_to}")
    print(f"{'年':<6}{'干支':<4}{'年干十神':<5}{'支主气':<5}{'运':<4}{'分':>3}  事件")
    for y, gz, ss, ssz, yun, ev, sc in rows:
        evs = "; ".join(e for e, _ in ev if not e.startswith("年干") or "合" in e or "伏吟" in e)
        print(f"{y:<6}{gz:<4}{ss:<5}{ssz:<5}{(yun[0] if yun else '--'):<4}{sc:>3}  {evs}")
    print("\n# Top 应期候选 (按作用强度排序, 喜忌与量级由 GATE 2 定调裁量):")
    for y, gz, ss, ssz, yun, ev, sc in sorted(rows, key=lambda r: -r[6])[:a.top]:
        evs = "; ".join(e for e, w in sorted(ev, key=lambda x: -x[1])[:4])
        print(f"  {y} {gz} [{sc}] {evs}")

if __name__ == "__main__":
    main()
