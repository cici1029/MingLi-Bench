# ziwei_sweep.py — 紫微流年应期枚举器 (2026-08-29, sunny-wang 2021 婚期 sweep 漏捕催生)
# 逐年机械枚举: 太岁入宫/冲宫 + 流年干四化落宫 + 生年忌伏起/冲起 + 叠忌 + 大限四化 + 流年宫位旋转
# → 按宫域打分排序。与 liunian_sweep.py (八字侧) 双列候选: 八字管强度, 紫微管"哪个域"。
# 事实层工具: 只枚举与打分, 不判吉凶——喜忌量级仍在 GATE 2 定调裁量。
# 用法:
#   node ziwei_gen.js --date 1991-2-21 --time-index 4 --gender 女 > /tmp/chart.json
#   python3 ziwei_sweep.py /tmp/chart.json --birth-year 1991 --from 2005 --to 2035 [--domain 婚恋] [--top 12]
#   python3 ziwei_sweep.py --selftest
# ⚠️ 界年 caveat: 紫微按农历界年 (非立春); 公历 1 月至农历新年前的事件属前一年的行, 对表时人工归位。
import argparse, json, sys

from ziwei_annotate import SIHUA, HUA_NAMES

ZHI = "子丑寅卯辰巳午未申酉戌亥"
GAN = "甲乙丙丁戊己庚辛壬癸"
ORDER = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "仆役", "官禄", "田宅", "福德", "父母"]
# 宫 → 域标签 (回测/出题用; 学业类锚点在回测层映射 官禄+父母 双宫)
DOMAIN = {"命宫": "自身", "兄弟": "六亲", "夫妻": "婚恋", "子女": "子女", "财帛": "财务", "疾厄": "健康",
          "迁移": "迁徙", "仆役": "人际", "官禄": "事业", "田宅": "家宅", "福德": "心境", "父母": "六亲"}

def jiazi(i): return GAN[i % 10] + ZHI[i % 12]
def liunian_gz(year): return jiazi((year - 1984) % 60)

class Chart:
    def __init__(self, d):
        self.palaces = d["palaces"]
        self.year_stem = d["year_stem"]
        self.decadal = d["decadal"]
        self.by_branch = {p["branch"]: p for p in self.palaces}
        self.by_name = {p["name"]: p for p in self.palaces}

    def star_palace(self, star):
        for p in self.palaces:
            if star in p["stars"]: return p
        return None

    def adj_palace(self, star):  # 杂曜定位 (红鸾/天喜/天马等)
        for p in self.palaces:
            if star in p.get("adj", []): return p
        return None

    def sanfang_branches(self, branch):  # 三方四正: 本/对/两三合
        i = ZHI.index(branch)
        return {ZHI[i], ZHI[(i + 6) % 12], ZHI[(i + 4) % 12], ZHI[(i + 8) % 12]}

    def opp(self, p):
        return self.by_branch[ZHI[(ZHI.index(p["branch"]) + 6) % 12]]

    def self_ji(self, p):  # 宫干自化忌
        return SIHUA[p["stem"]][3] in p["stars"]

    def decadal_at(self, xusui):
        for dc in self.decadal:
            a, b = dc["range"]
            if a <= xusui <= b: return dc
        return None

def sweep_year(ch, y, birth_year):
    """返回 events: [(desc, weight, palace_name)]"""
    gz = liunian_gz(y); fg, fz = gz[0], gz[1]
    ev = []
    ss = SIHUA[fg]
    # 1 太岁入宫 (流年命宫叠本命某宫: 该宫十二事成年度主轴)
    p0 = ch.by_branch[fz]
    ev.append((f"太岁入{p0['name']}", 4.0, p0["name"]))
    # 2 太岁冲宫
    p1 = ch.opp(p0)
    ev.append((f"太岁冲{p1['name']}", 4.0, p1["name"]))
    # 3 流年干四化落宫 (忌重 > 禄 > 权科); 忌兼冲对宫
    W_HUA = {"禄": 3.0, "权": 1.5, "科": 1.0, "忌": 5.0}
    ji_p = None
    for star, hua in zip(ss, HUA_NAMES):
        tp = ch.star_palace(star)
        if not tp: continue
        ev.append((f"流{hua}({star})入{tp['name']}", W_HUA[hua], tp["name"]))
        if hua == "忌":
            ji_p = tp
            op = ch.opp(tp)
            ev.append((f"流忌冲{op['name']}", 3.5, op["name"]))
    # 4 生年忌: 伏起/冲起/叠忌
    birth_ji_star = SIHUA[ch.year_stem][3]
    bj = ch.star_palace(birth_ji_star)
    if bj:
        if p0["name"] == bj["name"]:
            ev.append((f"太岁踏生年忌宫{bj['name']}(伏起)", 3.0, bj["name"]))
        if p0["name"] == ch.opp(bj)["name"]:
            ev.append((f"太岁踏生年忌所冲之宫(冲起{bj['name']})", 4.0, bj["name"]))
        if ji_p and ji_p["name"] == bj["name"]:
            ev.append((f"流忌叠生年忌于{bj['name']}(双忌)", 4.0, bj["name"]))
    # 5 自化忌宫被太岁引动
    if ch.self_ji(p0):
        ev.append((f"太岁引动{p0['name']}自化忌", 2.0, p0["name"]))
    # 6 大限四化 (限忌/限禄入宫; 限流双忌叠)
    xusui = y - birth_year + 1
    dc = ch.decadal_at(xusui)
    if dc:
        ds = SIHUA[dc["stem"]]
        for star, hua, w in ((ds[3], "忌", 2.0), (ds[0], "禄", 1.5)):
            tp = ch.star_palace(star)
            if not tp: continue
            ev.append((f"限{hua}({star})入{tp['name']}[{dc['palace']}限]", w, tp["name"]))
            if hua == "忌" and ji_p and ji_p["name"] == tp["name"]:
                ev.append((f"限流双忌叠于{tp['name']}", 4.0, tp["name"]))
    # 6b 大限宫域引动 (大限行X宫 = 该域十年被引动, 教义标配)
    if dc:
        ev.append((f"大限行{dc['palace']}", 2.0, dc["palace"]))
    # 6c 红鸾/天喜会流年命宫 (三方四正) → 婚庆应期 (教义第一婚期机制)
    sf = ch.sanfang_branches(fz)
    for hs in ("红鸾", "天喜"):
        hp = ch.adj_palace(hs)
        if hp and hp["branch"] in sf:
            w = 3.0 if hp["branch"] == fz else 2.0  # 坐命重于会照
            ev.append((f"流命会{hs}({hp['name']})", w, "夫妻"))
    # 6d 天马被太岁入/冲 → 驿马动 (迁移应期)
    mp = ch.adj_palace("天马")
    if mp and (mp["branch"] == fz or mp["branch"] == p1["branch"]):
        ev.append((f"太岁动天马({mp['name']})", 2.0, "迁移"))
    # 7 流年宫位旋转: 流X宫落在持生年忌/流忌的本命宫 → 该域被压
    fi = ZHI.index(fz)
    for pn in ch.palaces:
        flow_name = ORDER[(fi - ZHI.index(pn["branch"])) % 12]
        hot = (bj and pn["name"] == bj["name"]) or (ji_p and pn["name"] == ji_p["name"])
        if hot and flow_name != "命宫":  # 命宫情形已由 1/4/5 覆盖
            ev.append((f"流{flow_name}叠本命{pn['name']}(忌坐)", 3.0, flow_name))
    return gz, ev

def sweep(ch, birth_year, y_from, y_to):
    rows = []
    for y in range(y_from, y_to + 1):
        gz, ev = sweep_year(ch, y, birth_year)
        dom = {}
        for desc, w, pal in ev:
            d = DOMAIN.get(pal, pal)
            dom[d] = dom.get(d, 0.0) + w
        total = sum(w for _, w, _ in ev)
        rows.append({"year": y, "gz": gz, "total": total, "domains": dom, "events": ev})
    return rows

def fmt_row(r, domain=None):
    top = sorted(r["domains"].items(), key=lambda kv: -kv[1])[:3]
    doms = " ".join(f"{d}{s:.1f}" for d, s in top)
    evs = "；".join(e[0] for e in sorted(r["events"], key=lambda e: -e[1])[:6])
    lead = f"{r['year']} {r['gz']}"
    if domain:
        lead += f" [{domain}={r['domains'].get(domain, 0.0):.1f}]"
    return f"{lead} 总{r['total']:.1f} | {doms} | {evs}"

def selftest():
    # 案A (盘面去名化; 已验对照: person 页 2026-07-28 动盘判读)
    # 期望: 2026 丙午 = 太岁入财帛(身宫) + 流忌(廉贞)入命宫 + 流官叠本命命宫
    # 盘面 = ziwei_gen.js --date 1991-2-21 --time-index 4 --gender 女 实际输出 (勿手编星曜)
    chart_a = {
        "year_stem": "辛",
        "palaces": [
            {"name": "官禄", "stem": "庚", "branch": "寅", "stars": ["武曲", "天相", "天钺", "铃星"]},
            {"name": "仆役", "stem": "辛", "branch": "卯", "stars": ["太阳", "天梁", "地劫"]},
            {"name": "迁移", "stem": "壬", "branch": "辰", "stars": ["七杀", "左辅"]},
            {"name": "疾厄", "stem": "癸", "branch": "巳", "stars": ["天机", "天马"]},
            {"name": "财帛", "stem": "甲", "branch": "午", "stars": ["紫微", "文昌", "天魁"]},
            {"name": "子女", "stem": "乙", "branch": "未", "stars": ["地空"]},
            {"name": "夫妻", "stem": "丙", "branch": "申", "stars": ["破军", "文曲", "陀罗"]},
            {"name": "兄弟", "stem": "丁", "branch": "酉", "stars": ["禄存"]},
            {"name": "命宫", "stem": "戊", "branch": "戌", "stars": ["廉贞", "天府", "右弼", "擎羊"]},
            {"name": "父母", "stem": "己", "branch": "亥", "stars": ["太阴"]},
            {"name": "福德", "stem": "庚", "branch": "子", "stars": ["贪狼"]},
            {"name": "田宅", "stem": "辛", "branch": "丑", "stars": ["天同", "巨门", "火星"]},
        ],
        "decadal": [
            {"palace": "命宫", "branch": "戌", "stem": "戊", "range": [3, 12]},
            {"palace": "父母", "branch": "亥", "stem": "己", "range": [13, 22]},
            {"palace": "福德", "branch": "子", "stem": "庚", "range": [23, 32]},
            {"palace": "田宅", "branch": "丑", "stem": "辛", "range": [33, 42]},
            {"palace": "官禄", "branch": "寅", "stem": "庚", "range": [43, 52]},
        ],
    }
    ch = Chart(chart_a)
    gz, ev = sweep_year(ch, 2026, 1991)
    descs = [e[0] for e in ev]
    assert gz == "丙午", gz
    # person 页 2026-07-28 动盘判读三点回归: 流年命叠本命财帛 / 廉贞年忌入本命命宫 / 流官叠本命命宫
    assert "太岁入财帛" in descs, descs
    assert any("流忌(廉贞)入命宫" in d for d in descs), descs
    assert any("流官禄叠本命命宫" in d for d in descs), descs
    assert any("流忌冲迁移" in d for d in descs), descs
    # 旋转公式回归: 太岁午, 本命命宫戌 → (午6-戌10)%12=8=官禄
    assert ORDER[(ZHI.index("午") - ZHI.index("戌")) % 12] == "官禄"
    # 宫叠机制 (2026-08-26 delta 原型): 太岁支=夫妻宫支之年, 婚恋域必在该年被点亮
    gz28, ev28 = sweep_year(ch, 2028, 1991)  # 戊申年, 申=案A夫妻宫
    assert gz28 == "戊申", gz28
    assert any("太岁入夫妻" in e[0] for e in ev28), ev28
    print("selftest OK")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chart", nargs="?", help="ziwei_gen.js 输出的 JSON 路径 (- 为 stdin)")
    ap.add_argument("--birth-year", type=int)
    ap.add_argument("--from", dest="y_from", type=int)
    ap.add_argument("--to", dest="y_to", type=int)
    ap.add_argument("--domain", help="按单域排序 (婚恋/事业/财务/健康/家宅/子女/六亲/人际/迁徙)")
    ap.add_argument("--top", type=int, default=0, help="只显示按分排序的前 N 行")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest(); return
    if not (a.chart and a.birth_year and a.y_from and a.y_to):
        ap.error("需要 chart + --birth-year + --from + --to")
    d = json.load(sys.stdin if a.chart == "-" else open(a.chart))
    ch = Chart(d)
    rows = sweep(ch, a.birth_year, a.y_from, a.y_to)
    if a.domain:
        rows.sort(key=lambda r: -r["domains"].get(a.domain, 0.0))
    elif a.top:
        rows.sort(key=lambda r: -r["total"])
    if a.top: rows = rows[:a.top]
    for r in rows:
        print(fmt_row(r, a.domain))

if __name__ == "__main__":
    main()
