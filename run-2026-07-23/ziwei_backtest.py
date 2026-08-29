# ziwei_backtest.py — 紫微 sweep 对已验锚点的回测 harness (2026-08-29)
# 通用工具, 不含个人数据; 数据集 JSON 由 vault 侧提供 (勿入本 repo):
# [{"slug","date","time_index","gender","birth_year","anchors":[{"year","domain","desc","note"?}]}]
# 指标:
#   定域 hit@k — 锚点年份的真实域在该年 12 域分里排前 k (k=2,3)。这是"八字定年、紫微定域"分工的直接检验。
#   应期 rank — 锚点年在全窗口按该域分排序的名次 (top5/top8)。检验紫微独立选年能力。
# 用法: python3 ziwei_backtest.py dataset.json [--window-start-age 15] [--to 2026] [-v]
import argparse, json, subprocess, sys, os

from ziwei_sweep import Chart, sweep

HERE = os.path.dirname(os.path.abspath(__file__))
# 锚点域 → 可接受的 sweep 域集合 (学业=官禄主+父母文书; 官非=是非缠身/自身)
ACCEPT = {"婚恋": {"婚恋"}, "事业": {"事业"}, "学业": {"事业", "六亲"}, "生育": {"子女"},
          "六亲": {"六亲"}, "家宅": {"家宅"}, "财务": {"财务"}, "健康": {"健康"},
          "官非": {"官非", "事业", "自身"}, "迁徙": {"迁徙"}, "人际": {"人际"}}

def gen_chart(date, time_index, gender):
    out = subprocess.run(["node", os.path.join(HERE, "ziwei_gen.js"), "--date", date,
                          "--time-index", str(time_index), "--gender", gender],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)

def domain_rank(row, accept):
    best = max((row["domains"].get(d, 0.0) for d in accept), default=0.0)
    if best <= 0: return 99
    return 1 + sum(1 for v in row["domains"].values() if v > best)

def year_rank(rows, y, accept):
    best_rank = 99
    for d in accept:
        scores = [(r["domains"].get(d, 0.0), r["year"]) for r in rows]
        target = next(s for s, yy in scores if yy == y)
        rank = 1 + sum(1 for s, yy in scores if s > target)
        best_rank = min(best_rank, rank)
    return best_rank

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--window-start-age", type=int, default=15)
    ap.add_argument("--to", type=int, default=2026)
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--career-move", action="store_true",
                    help="事业锚点兼收迁移宫 (教义: 跳槽/转业/离乡属迁移宫事; post-hoc 变体, 与 strict 并报)")
    a = ap.parse_args()
    if a.career_move:
        ACCEPT["事业"] = {"事业", "迁徙"}
    ds = json.load(open(a.dataset))
    if isinstance(ds, dict): ds = ds["people"]
    agg = {"n": 0, "dom2": 0, "dom3": 0, "yr5": 0, "yr8": 0}
    per_domain = {}
    for person in ds:
        ch = Chart(gen_chart(person["date"], person["time_index"], person["gender"]))
        by = person["birth_year"]
        y_from = min([by + a.window_start_age] + [an["year"] for an in person["anchors"]])
        rows = sweep(ch, by, y_from, a.to)
        rowmap = {r["year"]: r for r in rows}
        n_win = len(rows)
        print(f"\n== {person['slug']} (窗口 {y_from}-{a.to}, {n_win} 年) ==")
        for an in person["anchors"]:
            acc = ACCEPT[an["domain"]]
            row = rowmap[an["year"]]
            dr = domain_rank(row, acc)
            yr = year_rank(rows, an["year"], acc)
            top = sorted(row["domains"].items(), key=lambda kv: -kv[1])[:3]
            tops = " ".join(f"{d}{s:.1f}" for d, s in top)
            print(f"  {an['year']} {an['domain']:<3} {an['desc']:<14} 定域rank={dr:<2} 应期rank={yr}/{n_win} | 当年top3: {tops}")
            if a.verbose:
                print("      " + "；".join(e[0] for e in sorted(row["events"], key=lambda e: -e[1])[:8]))
            agg["n"] += 1
            agg["dom2"] += dr <= 2; agg["dom3"] += dr <= 3
            agg["yr5"] += yr <= 5; agg["yr8"] += yr <= 8
            pd = per_domain.setdefault(an["domain"], [0, 0, 0])
            pd[0] += 1; pd[1] += dr <= 2; pd[2] += yr <= 5
    n = agg["n"]
    print(f"\n==== 汇总 (n={n}) ====")
    print(f"定域 hit@2: {agg['dom2']}/{n} = {agg['dom2']/n:.0%}   (随机基线 ~{2/12:.0%}-{2/8:.0%})")
    print(f"定域 hit@3: {agg['dom3']}/{n} = {agg['dom3']/n:.0%}")
    print(f"应期 top5:  {agg['yr5']}/{n} = {agg['yr5']/n:.0%}   (随机基线 ~5/35≈14%)")
    print(f"应期 top8:  {agg['yr8']}/{n} = {agg['yr8']/n:.0%}")
    print("\n按域分解 (n / 定域hit@2 / 应期top5):")
    for d, (cnt, d2, y5) in sorted(per_domain.items(), key=lambda kv: -kv[1][0]):
        print(f"  {d}: {cnt} / {d2} / {y5}")

if __name__ == "__main__":
    main()
