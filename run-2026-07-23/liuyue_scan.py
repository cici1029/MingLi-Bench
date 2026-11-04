# liuyue_scan.py: month-level scan, bazi flow-month pillar + ziwei flow-month palace (2026-11-04)
# Bazi side: month pillars from astronomical 节 times (bazi_core), scored with the liunian_sweep v2
#   features against natal + current dayun (weights were fit on YEARS: read month scores as relative only),
#   plus explicit hits on chosen target branches (冲/刑/穿/合绊/伏吟) and 丁透+刑 (丑未刑戌) fuse flags.
# Ziwei side: iztro horoscope() 斗君 flow month: which natal palace, and where the month's 四化 land.
#   Ziwei months are LUNAR; rows pair by the 15th of each Gregorian month (expect up to ~3 weeks skew).
# Run with the bazi venv (needs its ephemeris deps):
#   ~/Developer/openclaw-projects/bazi/venv/bin/python liuyue_scan.py '丙寅 戊戌 丙午 丙申' --dayun 甲午 \
#       --date 1986-10-29 --time-index 8 --gender 女 --targets 申,午 --from 2026-11 --to 2028-12 [--tz-offset -16]
import argparse, datetime, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.expanduser("~/Developer/openclaw-projects/bazi"))
import sweep_features as sf, liunian_sweep as ls
from bazi_core import get_year_months, calculate_bazi

ZHI = "子丑寅卯辰巳午未申酉戌亥"
CHONG = {a: ZHI[(i + 6) % 12] for i, a in enumerate(ZHI)}
CHUAN = {"子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "巳", "巳": "寅", "卯": "辰", "辰": "卯", "申": "亥", "亥": "申", "酉": "戌", "戌": "酉"}
LIUHE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯", "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
XING = {("寅", "巳"), ("巳", "申"), ("申", "寅"), ("丑", "戌"), ("戌", "未"), ("未", "丑"), ("子", "卯"), ("卯", "子")}

def month_score(pillars, dayun, gz):
    orig = sf.year_ganzhi; sf.year_ganzhi = lambda y: gz
    try: f = sf.featurize(pillars, dayun, 0, ls.FLAGS)
    finally: sf.year_ganzhi = orig
    sc = sum(ls.WEIGHTS.get(k, 0) * v for k, v in f.items())
    mech = [ls.FEAT_LABEL[k] for k, v in sorted(f.items(), key=lambda kv: -ls.WEIGHTS.get(kv[0], 0) * kv[1]) if v and ls.WEIGHTS.get(k, 0) > 0]
    return round(sc, 1), mech

def target_hits(b, targets, natal_branches, year_branch):
    out = []
    for t in targets:
        if CHONG[b] == t: out.append(f"{b}冲{t}")
        if CHUAN.get(b) == t: out.append(f"{b}穿{t}")
        if LIUHE.get(b) == t: out.append(f"{b}合绊{t}")
        if (b, t) in XING or (t, b) in XING: out.append(f"{b}刑{t}")
        if b == t: out.append(f"{t}伏吟")
        if year_branch == t and CHONG[b] == t: out.append(f"岁月冲({t})")
    # 刑 that shakes a target via a third natal branch (e.g. 未刑戌 with 申 as the brittle target)
    for nb in natal_branches:
        if nb not in targets and ((b, nb) in XING or (nb, b) in XING): out.append(f"{b}刑{nb}")
    return out

def ziwei_months(date, ti, gender, ym_from, ym_to):
    js = r"""
const { astro } = require(process.argv[1]);
const [date, ti, g, y0, m0, y1, m1] = process.argv.slice(2);
const a = astro.bySolar(date, +ti, g, true, 'zh-CN');
const nm = n => n === '事业' ? '官禄' : n === '交友' ? '仆役' : n;
const natal = a.palaces.map(p => ({ name: nm(p.name), branch: p.earthlyBranch, stars: [...p.majorStars, ...p.minorStars].map(s => s.name) }));
const find = s => (natal.find(p => p.stars.includes(s)) || {}).name || '-';
const Z = '子丑寅卯辰巳午未申酉戌亥';
const opp = n => { const p = natal.find(x => x.name === n); if (!p) return '-'; return natal.find(x => x.branch === Z[(Z.indexOf(p.branch) + 6) % 12]).name; };
const out = [];
for (let y = +y0, m = +m0; y < +y1 || (y === +y1 && m <= +m1); m === 12 ? (y++, m = 1) : m++) {
  const h = a.horoscope(`${y}-${m}-15`, +ti), mo = h.monthly; const [lu, qu, ke, ji] = mo.mutagen;
  out.push({ ym: `${y}-${String(m).padStart(2, '0')}`, lunar: h.lunarDate, palace: natal[mo.index].name,
    lu: `${lu}>${find(lu)}`, quan: `${qu}>${find(qu)}`, ke: `${ke}>${find(ke)}`, ji: `${ji}>${find(ji)}`, ji_chong: opp(find(ji)) });
}
console.log(JSON.stringify(out));
"""
    mod = os.path.join(HERE, "node_modules", "iztro")
    y0, m0 = map(int, ym_from.split("-")); y1, m1 = map(int, ym_to.split("-"))
    r = subprocess.run(["node", "-e", js, mod, date, str(ti), gender, str(y0), str(m0), str(y1), str(m1)],
                       capture_output=True, text=True, check=True)
    return {x["ym"]: x for x in json.loads(r.stdout)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pillars"); ap.add_argument("--dayun", required=True, help="current dayun 干支, e.g. 甲午")
    ap.add_argument("--date"); ap.add_argument("--time-index", type=int); ap.add_argument("--gender")
    ap.add_argument("--targets", default="", help="target branches, e.g. 申,午")
    ap.add_argument("--from", dest="f", required=True); ap.add_argument("--to", dest="t", required=True)
    ap.add_argument("--tz-offset", type=float, default=-16, help="hours added to Beijing 节 time (PST -16, PDT -15)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    # anchor self-check (consult GATE 1)
    assert calculate_bazi(datetime.datetime(1949, 10, 1, 12))["day_pillar"] == "甲子"
    assert calculate_bazi(datetime.datetime(2000, 1, 1, 12))["day_pillar"] == "戊午"
    P = a.pillars.split(); natal_b = [p[1] for p in P]; T = [t for t in a.targets.split(",") if t]
    y0, m0 = map(int, a.f.split("-")); y1, m1 = map(int, a.t.split("-"))
    lo, hi = datetime.datetime(y0, m0, 1) - datetime.timedelta(days=10), datetime.datetime(y1, m1, 28)
    rows = []
    for y in range(y0 - 1, y1 + 1):
        for m in get_year_months(y):
            st = m["start_time"] if isinstance(m["start_time"], datetime.datetime) else datetime.datetime.fromisoformat(str(m["start_time"]))
            st_local = st + datetime.timedelta(hours=a.tz_offset)
            if not (lo <= st_local <= hi) or any(r["start"] == st_local.strftime("%Y-%m-%d") for r in rows): continue
            ygz = calculate_bazi(st + datetime.timedelta(hours=2))["year_pillar"]  # just after 节, so 寅月 gets the new year
            gz = m["pillar"]; sc, mech = month_score(P, a.dayun, gz)
            hits = target_hits(gz[1], T, natal_b, ygz[1])
            fuse = "丁透+刑" if ("丁" in (gz[0], ygz[0]) and (gz[1] in "丑未" or ygz[1] in "丑未")) else ""
            fuse2 = "加倍" if fuse and gz[1] in "丑未" and ygz[0] == "丁" else ""
            rows.append({"start": st_local.strftime("%Y-%m-%d"), "ygz": ygz, "mgz": gz, "score": sc, "mech": mech,
                         "hits": hits, "fuse": fuse + fuse2})
    rows.sort(key=lambda r: r["start"])
    zw = ziwei_months(a.date, a.time_index, a.gender, a.f, a.t) if a.date else {}
    for r in rows:
        ym = r["start"][:7]
        d = datetime.date.fromisoformat(r["start"]) + datetime.timedelta(days=10)  # pair with the Gregorian month the 节-month mostly covers
        r["ziwei"] = zw.get(f"{d.year}-{d.month:02d}")
    if a.json: print(json.dumps(rows, ensure_ascii=False)); return
    for r in rows:
        z = r["ziwei"]
        zs = f" | 紫微流月={z['palace']} 禄{z['lu']} 忌{z['ji']}冲{z['ji_chong']}" if z else ""
        print(f"{r['start']} {r['ygz']}年 {r['mgz']}月 [{r['score']:5}] {'+'.join(r['mech'][:3])} | {' '.join(r['hits'])} {r['fuse']}{zs}")

if __name__ == "__main__":
    main()
