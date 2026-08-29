import json, re, subprocess, datetime

BAZI = "/Users/chao.ruan/Developer/openclaw-projects/bazi/venv/bin/python"
BAZIPY = "/Users/chao.ruan/Developer/openclaw-projects/bazi/bazi.py"
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
JIE = {"立春","惊蛰","清明","立夏","芒种","小暑","立秋","白露","寒露","立冬","大雪","小寒"}
YANG = set("甲丙戊庚壬")

def jiazi(idx):
    return GAN[idx % 10] + ZHI[idx % 12]

def jiazi_index(gz):
    for i in range(60):
        if jiazi(i) == gz: return i
    raise ValueError(gz)

def run(args):
    return subprocess.run([BAZI, BAZIPY] + args, capture_output=True, text=True).stdout

def sizhu(y, m, d, h):
    out = run(["date", f"{y:04d}-{m:02d}-{d:02d}", str(h)])
    return re.search(r"八字: (\S+) (\S+) (\S+) (\S+)", out).groups()

def jie_times(year):
    out = run(["jieqi", str(year)])
    ts = []
    for name, t in re.findall(r"(\S+): (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", out):
        if name in JIE:
            ts.append(datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S"))
    return ts

def liunian(year):
    return jiazi((year - 1984) % 60)

def case_block(binfo):
    y, m, d, h = binfo["year"], binfo["month"], binfo["day"], binfo["hour"]
    gender = binfo["gender"]
    yz, mz, dz, hz = sizhu(y, m, d, h)
    birth = datetime.datetime(y, m, d, h, binfo.get("minute", 0))
    jies = sorted(jie_times(y - 1) + jie_times(y) + jie_times(y + 1))
    forward = (yz[0] in YANG) == (gender == "男")
    if forward:
        target = min(t for t in jies if t > birth); days = (target - birth).total_seconds() / 86400
    else:
        target = max(t for t in jies if t < birth); days = (birth - target).total_seconds() / 86400
    qiyun = days / 3
    mi = jiazi_index(mz)
    luck = [(jiazi(mi + (i + 1) * (1 if forward else -1)), round(qiyun + i * 10, 1)) for i in range(8)]
    lines = [
        f"确定性排盘（天文计算，非估算）: 四柱 {yz} {mz} {dz} {hz}",
        f"大运: {'顺排' if forward else '逆排'}（年干{'阳' if yz[0] in YANG else '阴'}{gender}），起运 {qiyun:.1f} 岁（虚岁约 {qiyun+1:.0f} 岁起运）",
        "大运序列(起运实岁): " + " / ".join(f"{g}({a}岁起)" for g, a in luck),
        "流年干支速查: " + " ".join(f"{yy}{liunian(yy)}" for yy in range(y, min(y + 76, 2027)) if yy % 2 == 0),
        "  （奇数年请按六十甲子顺推一位；2026=丙午 已核）",
    ]
    return "\n".join(lines)

qs = json.load(open("../data/data.json"))["questions"]
cases = {}
for q in qs:
    cid = int(q["case_id"].split("_")[1])
    if cid >= 25 and q["case_id"] not in cases:
        cases[q["case_id"]] = q["birth_info"]

src = open("configA_batch4.md").read()
sections = re.split(r"(?=^## case_)", src, flags=re.M)
out = []
for sec in sections:
    m = re.match(r"## (case_\d+)", sec)
    if m and m.group(1) in cases:
        pos = sec.find("### ")
        appendix = "\n" + case_block(cases[m.group(1)]) + "\n\n"
        sec = sec[:pos] + appendix + sec[pos:]
    out.append(sec)
open("configD_batch4.md", "w").write("".join(out))

# regression gates
assert sizhu(1974, 4, 28, 16) == ("甲寅", "戊辰", "己亥", "壬申"), "case_1 regression failed"
assert liunian(2026) == "丙午" and liunian(1984) == "甲子", "liunian failed"
print("OK: configD_batch4.md generated,", len(cases), "cases;", "regression gates passed")
