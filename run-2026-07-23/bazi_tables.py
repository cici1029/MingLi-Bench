# -*- coding: utf-8 -*-
"""Shared 干支 tables for MingLi-Bench engines (v2 rebuild 2026-08-12).

v1 (2026-07-23/24) was lost with no git remote; this rebuild follows the spec
preserved in skill xuanxue-consult SKILL.md + recorded engine outputs in
notes/玄学/wiki/people/*.md (see calibration_data.py).
"""

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

STEM_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
               "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
STEM_YANG = {s: i % 2 == 0 for i, s in enumerate(STEMS)}
BRANCH_WUXING = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
                 "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}

# 藏干: branch -> [(stem, 档)] 档 in {"本", "中", "余"}
HIDDEN = {
    "子": [("癸", "本")],
    "丑": [("己", "本"), ("癸", "中"), ("辛", "余")],
    "寅": [("甲", "本"), ("丙", "中"), ("戊", "余")],
    "卯": [("乙", "本")],
    "辰": [("戊", "本"), ("乙", "中"), ("癸", "余")],
    "巳": [("丙", "本"), ("庚", "中"), ("戊", "余")],
    "午": [("丁", "本"), ("己", "中")],
    "未": [("己", "本"), ("丁", "中"), ("乙", "余")],
    "申": [("庚", "本"), ("壬", "中"), ("戊", "余")],
    "酉": [("辛", "本")],
    "戌": [("戊", "本"), ("辛", "中"), ("丁", "余")],
    "亥": [("壬", "本"), ("甲", "中")],
}

# 十二长生: 阳干顺行 阴干逆行; anchor = 长生 branch
CHANGSHENG_START = {"甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申",
                    "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯"}
STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]


def changsheng(stem, branch):
    start = BRANCHES.index(CHANGSHENG_START[stem])
    cur = BRANCHES.index(branch)
    step = (cur - start) % 12 if STEM_YANG[stem] else (start - cur) % 12
    return STAGES[step]


# 生克
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def ten_god(dm, other):
    """十神 of stem `other` relative to day master `dm`."""
    w1, w2 = STEM_WUXING[dm], STEM_WUXING[other]
    same_pol = STEM_YANG[dm] == STEM_YANG[other]
    if w1 == w2:
        return "比肩" if same_pol else "劫财"
    if SHENG[w1] == w2:
        return "食神" if same_pol else "伤官"
    if KE[w1] == w2:
        return "偏财" if same_pol else "正财"
    if KE[w2] == w1:
        return "七杀" if same_pol else "正官"
    return "偏印" if same_pol else "正印"


def is_helper(dm, other):
    """帮扶党(印+比劫+日主) vs 克泄耗党(财官杀食伤)."""
    w1, w2 = STEM_WUXING[dm], STEM_WUXING[other]
    return w1 == w2 or SHENG[w2] == w1


# 支冲/六合/三合/三会/刑
CHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
         "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
LIUHE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
         "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
SANHE = [set("申子辰"), set("寅午戌"), set("巳酉丑"), set("亥卯未")]
SANHUI = [set("寅卯辰"), set("巳午未"), set("申酉戌"), set("亥子丑")]
SANXING = [set("寅巳申"), set("丑戌未")]
XING_PAIR = [{"子", "卯"}]
ZIXING = {"辰", "午", "酉", "亥"}

# 天干五合
WUHE = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙", "丙": "辛", "辛": "丙",
        "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊"}


def stem_ke(a, b):
    return KE[STEM_WUXING[a]] == STEM_WUXING[b]


def year_ganzhi(year):
    """流年干支 (立春界, caller aligns year)."""
    return STEMS[(year - 4) % 10] + BRANCHES[(year - 4) % 12]
