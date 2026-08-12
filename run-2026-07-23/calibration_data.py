# -*- coding: utf-8 -*-
"""Recorded v1 engine outputs, recovered from notes/玄学/wiki/people/*.md.

These are the regression targets for the v2 rebuild (2026-08-12).
STRENGTH: chart -> (帮扶 total, 克泄耗 total, {字: score} where known)
SWEEP: chart + dayun + window -> {year: recorded score}
"""

# ---- strength engine targets ----------------------------------------------
# stems keyed by (position, stem) pos in 年干/月干/日干/时干; parties keyed by wuxing stem.
STRENGTH_CASES = {
    "susu": {
        "pillars": ["辛未", "庚寅", "壬戌", "甲辰"],
        "help_total": 47, "drain_total": 128,
        "stems": {("年干", "辛"): 19, ("月干", "庚"): 15, ("日干", "壬"): 12, ("时干", "甲"): 73},
        "parties": {"己": 30, "戊": 25},
    },
    "yeheng": {
        "pillars": ["己巳", "辛未", "庚寅", "乙酉"],
        "help_total": 185, "drain_total": 143,
        "stems": {("年干", "己"): 69, ("月干", "辛"): 52, ("日干", "庚"): 64, ("时干", "乙"): 64},
        "parties": {"甲": 43, "丙": 36},
    },
    "bpjia": {
        "pillars": ["辛未", "丙申", "甲子", "癸酉"],
        "help_total": 77, "drain_total": 208,
        "stems": {("年干", "辛"): 104, ("月干", "丙"): 19, ("日干", "甲"): 14, ("时干", "癸"): 62},
        "parties": {"庚": 54, "己": 30},
    },
    "hryi": {
        "pillars": ["壬申", "庚戌", "乙亥", "辛巳"],
        "help_total": 56, "drain_total": 153,
        "stems": {("年干", "壬"): 42, ("月干", "庚"): 54, ("日干", "乙"): 14, ("时干", "辛"): 62},
        "parties": {},
    },
    "wangshuang": {
        "pillars": ["乙丑", "壬午", "壬辰", "庚戌"],
        "help_total": 62, "drain_total": 116,
        "stems": {("年干", "乙"): 19, ("月干", "壬"): 22, ("日干", "壬"): 22, ("时干", "庚"): 19},
        "parties": {"丁": 54, "戊": 26, "己": 16},
    },
    "summersu": {
        "pillars": ["壬戌", "己酉", "己酉", "乙亥"],
        "help_total": 72, "drain_total": 159,
        "stems": {("年干", "壬"): 46, ("月干", "己"): 28, ("日干", "己"): 28, ("时干", "乙"): 16},
        "parties": {"辛": 97, "戊": 16},
    },
    "susu_husband": {
        "pillars": ["辛未", "辛卯", "庚辰", "己卯"],
        "help_total": 128, "drain_total": 90,
        "stems": {("时干", "己"): 62},  # 己印62; 三金裸透 30 (辛+辛+庚 各10); 戊藏36
        "parties": {"戊": 36, "乙": 90},
    },
    "ceo": {
        "pillars": ["甲子", "丙子", "己卯", "丁卯"],
        "help_total": 30, "drain_total": 265,
        "stems": {("月干", "丙"): 10, ("时干", "丁"): 10, ("日干", "己"): 10, ("年干", "甲"): 96},
        "parties": {"癸": 90, "乙": 79},
    },
    "hrbp": {
        "pillars": ["乙丑", "戊子", "庚辰", "丁亥"],
        "help_total": 75, "drain_total": 138,
        "stems": {("月干", "戊"): 55, ("年干", "乙"): 32, ("时干", "丁"): 10, ("日干", "庚"): 12},
        "parties": {"癸": 49, "壬": 47, "己": 8},
    },
    "lucky": {
        "pillars": ["壬申", "乙巳", "乙未", "乙酉"],
        "help_total": 68, "drain_total": 135,
        "stems": {("年干", "壬"): 20, ("月干", "乙"): 16, ("日干", "乙"): 16, ("时干", "乙"): 16},
        "parties": {"丙": 38, "己": 36, "辛": 36, "庚": 25},
    },
    "lucian": {
        "pillars": ["癸卯", "甲寅", "己酉", "辛未"],
        "help_total": 45, "drain_total": 148,
        "stems": {}, "parties": {},
    },
    "zoujia": {
        # 戌时对照盘 (canonical 亥时): 帮扶 73 vs 克泄 146 was for 庚戌时 variant
        "pillars": ["癸亥", "乙丑", "丁巳", "庚戌"],
        "help_total": 73, "drain_total": 146,
        "stems": {}, "parties": {},
    },
}

# directions: True = 身弱 (help < drain)
STRENGTH_DIRECTIONS = {k: v["help_total"] < v["drain_total"] for k, v in STRENGTH_CASES.items()}

# ---- liunian_sweep targets --------------------------------------------------
SWEEP_CASES = {
    "chao": {
        "pillars": "丙寅 戊戌 丙午 丙申",
        "dayun": "丁酉:1993,丙申:2003,乙未:2013,甲午:2023,癸巳:2033,壬辰:2043,辛卯:2053,庚寅:2063,己丑:2073",
        "window": (2026, 2045),
        "recorded": {2026: 41, 2034: 39, 2037: 34, 2040: 30, 2041: 29, 2032: 28, 2027: 15},
        "top_order": [2026, 2034, 2037, 2040, 2041, 2032],
    },
    "zoujia": {
        "pillars": "癸亥 乙丑 丁巳 辛亥",
        "dayun": "甲子:1990,癸亥:2000,壬戌:2010,辛酉:2020,庚申:2030,己未:2040,戊午:2050",
        "window": (2026, 2045),
        "recorded": {2037: 51, 2043: 51, 2031: 39, 2034: 36, 2045: 29, 2027: 27},
        "top_order": [2037, 2043, 2031, 2034, 2045, 2027],
    },
    "wujiaoyang": {
        "pillars": "辛未 乙未 甲申 乙亥",
        "dayun": "丙申:2000,丁酉:2010,戊戌:2020,己亥:2030,庚子:2040",
        "window": (1994, 2036),
        "recorded": {2021: 58, 1997: 49, 2009: 44, 2033: 40, 2010: 37},
        "top_order": [2021, 1997, 2009, 2033, 2010],
    },
    "liuchang": {
        "pillars": "壬申 丙午 己巳 壬申",
        "dayun": "乙巳:1998,甲辰:2008,癸卯:2018,壬寅:2028,辛丑:2038",
        "window": (1995, 2036),
        "recorded": {1998: 67, 2034: 57, 2010: 49, 2022: 49, 2028: 39},
        "top_order": [1998, 2034, [2010, 2022], 2028],
    },
    "lucky": {
        "pillars": "壬申 乙巳 乙未 乙酉",
        "dayun": "丙午:1998,丁未:2008,戊申:2018,己酉:2028,庚戌:2038,辛亥:2048",
        "window": (1995, 2036),
        "recorded": {1998: 45, 2010: 45, 2021: 39, 2022: 39, 2009: 36, 2025: 36, 2034: 36,
                     2030: 34, 2029: 32},
        "top_order": [[1998, 2010], [2021, 2022], [2009, 2025, 2034], 2030, 2029],
    },
    "wangshuang": {
        "pillars": "乙丑 壬午 壬辰 庚戌",
        "dayun": "癸未:1990,甲申:2000,乙酉:2010,丙戌:2020,丁亥:2030,戊子:2040",
        "window": (1990, 2035),
        "recorded": {2030: 40},
        "notes": "2030 rank #2 overall in 1990-2035; 2012 壬辰 must be Top4 (selftest)",
    },
}

# ---- dayun_calc anchors -----------------------------------------------------
DAYUN_CASES = [
    # (birth iso, gender, expected qiyun years ±0.05, direction, first few dayun)
    ("1991-02-21T09:00", "女", 4.35, "顺", ["辛卯", "壬辰", "癸巳", "甲午"]),
    ("1989-07-29T18:50", "男", 7.45, "逆", ["庚午", "己巳", "戊辰", "丁卯"]),  # 页面记 ~7.5 (约数)
    ("1992-04-20T22:00", "男", 4.89, "顺", ["乙巳", "丙午", "丁未", "戊申"]),  # App 4.9; 首算 4.99 系手敲立夏时刻之误
]
