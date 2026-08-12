# -*- coding: utf-8 -*-
"""力量定级引擎 (strength engine) — v2 rebuild 2026-08-12.

v1 (2026-07-23, lost) parameters recovered by fitting against 12 recorded
per-字 score breakdowns in notes/玄学/wiki/people/*.md. See calibration_data.py
and test_regression.py. Recovered scheme:

  每字力量分 = 透干10 + Σ根 [ 档基础分(本35/中20/余10)
                             × 十二长生态系数(透干自身在该支的长生位)
                             × 宫位权重(年0.9/月1.3/日1.0/时0.85)
                             × 冲0.5 × 六合绊0.7 ]
  未透主气党势 = 该支本气藏干(其字未透时) 按同公式记党(无透干10分项)

  根 = 任何地支藏干中与透干同五行者(不限同字, 本/中/余皆算)。
  十二长生态系数: 长生1.0 沐浴0.7 冠带0.9 临官1.2 帝旺1.3 衰0.6
                  病0.5 死0.4 墓0.5 绝0.3 胎0.4 养0.6
  (帝旺1.3/衰养0.6/绝0.3 为 SKILL 记载锚点; 沐浴/病/胎 为 v2 拟合值)
  刑不修正力量(v1 实测行为: susu 未戌刑不减未党)。会局修正未见于校准数据, v2 未实现。

Usage:
  from annotate import strength_table, annotate
  print(strength_table(['辛未','庚寅','壬戌','甲辰']))
"""

from bazi_tables import (STEMS, HIDDEN, STEM_WUXING, changsheng, ten_god,
                         is_helper, CHONG, LIUHE)

STAGE_COEF = {"长生": 1.0, "沐浴": 0.7, "冠带": 0.9, "临官": 1.2, "帝旺": 1.3,
              "衰": 0.6, "病": 0.5, "死": 0.4, "墓": 0.5, "绝": 0.3, "胎": 0.4, "养": 0.6}
BASE = {"本": 35, "中": 20, "余": 10}
PALACE = {0: 0.9, 1: 1.3, 2: 1.0, 3: 0.85}   # 年月日时
POS_NAME = ["年", "月", "日", "时"]
TOU = 10
CHONG_MOD = 0.5
HE_MOD = 0.7


def _branch_mods(branches):
    """Per-position multiplier from 支冲/六合 among the four branches."""
    mods = [1.0] * 4
    for i in range(4):
        for j in range(4):
            if i == j:
                continue
            if CHONG.get(branches[i]) == branches[j]:
                mods[i] *= CHONG_MOD
                break  # 冲只记一次
    for i in range(4):
        for j in range(4):
            if i != j and LIUHE.get(branches[i]) == branches[j]:
                mods[i] *= HE_MOD
                break
    return mods


def _root_score(stem, branches, mods, dang_only=None):
    """Σ roots of `stem` across branches. dang_only: restrict to 档 (for 党势=本)."""
    total, detail = 0.0, []
    for pos, br in enumerate(branches):
        for hid, dang in HIDDEN[br]:
            if dang_only and dang != dang_only:
                continue
            if dang_only is None and STEM_WUXING[hid] != STEM_WUXING[stem]:
                continue
            if dang_only and hid != stem:
                continue
            stage = changsheng(stem, br)
            pts = BASE[dang] * STAGE_COEF[stage] * PALACE[pos] * mods[pos]
            total += pts
            detail.append(f"{POS_NAME[pos]}支{br}{hid}({dang}气·{stage}·{pts:.1f})")
    return total, detail


def strength_table(pillars):
    """pillars: ['辛未','庚寅','壬戌','甲辰'] (年月日时). Returns printable table."""
    rows = compute(pillars)
    dm = pillars[2][0]
    lines = [f"日主 {dm} | 帮扶党 {rows['help_total']} vs 克泄耗党 {rows['drain_total']}"
             f" | {'身弱倾向' if rows['help_total'] < rows['drain_total'] else '身强倾向'}（定调仍需会合局/从格综合裁量）"]
    for r in rows["items"]:
        side = "帮" if r["helper"] else "耗"
        lines.append(f"  [{side}] {r['label']} {r['stem']}({r['tengod']}) = {r['score']}"
                     + (f"  根: {'; '.join(r['detail'])}" if r["detail"] else "  (无根裸透)" if r["kind"] == "透" else ""))
    return "\n".join(lines)


def compute(pillars):
    stems = [p[0] for p in pillars]
    branches = [p[1] for p in pillars]
    dm = stems[2]
    mods = _branch_mods(branches)
    items = []
    # 透干 (含日主)
    for pos, st in enumerate(stems):
        root, detail = _root_score(st, branches, mods)
        items.append({"kind": "透", "label": f"{POS_NAME[pos]}干", "stem": st,
                      "tengod": "日主" if pos == 2 else ten_god(dm, st),
                      "helper": is_helper(dm, st),
                      "score": int(round(TOU + root)), "detail": detail})
    # 未透主气党势: 本气藏干其字未透
    tou_set = set(stems)
    party = {}
    for pos, br in enumerate(branches):
        hid, dang = HIDDEN[br][0]
        if hid in tou_set:
            continue
        stage = changsheng(hid, br)
        pts = BASE["本"] * STAGE_COEF[stage] * PALACE[pos] * mods[pos]
        party.setdefault(hid, [0.0, []])
        party[hid][0] += pts
        party[hid][1].append(f"{POS_NAME[pos]}支{br}({stage}·{pts:.1f})")
    for hid, (pts, detail) in party.items():
        items.append({"kind": "党", "label": "藏党", "stem": hid,
                      "tengod": ten_god(dm, hid), "helper": is_helper(dm, hid),
                      "score": int(round(pts)), "detail": detail})
    help_total = sum(r["score"] for r in items if r["helper"])
    drain_total = sum(r["score"] for r in items if not r["helper"])
    return {"items": items, "help_total": help_total, "drain_total": drain_total}


def annotate(pillars):
    """Full annotation: strength + 十神 + 长生 per pillar."""
    out = [strength_table(pillars)]
    dm = pillars[2][0]
    for pos, p in enumerate(pillars):
        st, br = p[0], p[1]
        hids = "、".join(f"{h}{ten_god(dm, h)}" for h, _ in HIDDEN[br])
        out.append(f"{POS_NAME[pos]}柱 {p}: {ten_god(dm, st) if pos != 2 else '日主'} | "
                   f"日主{changsheng(dm, br)}于{br} | 藏干 {hids}")
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    args = sys.argv[1:] or ["辛未", "庚寅", "壬戌", "甲辰"]
    if len(args) == 1:
        args = args[0].split()
    print(annotate(args))
