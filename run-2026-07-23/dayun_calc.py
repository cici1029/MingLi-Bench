# -*- coding: utf-8 -*-
"""大运/起运 确定性计算 — v2 rebuild 2026-08-12.

起运 = 距节天数 ÷ 3（年），阳男阴女顺排、阴男阳女逆排。
节气用 bazi-cli (ephem 天文计算)；须用其 venv 运行：
  ~/Developer/openclaw-projects/bazi/venv/bin/python dayun_calc.py 1991-02-21T09:00 女

Regression anchors (calibration_data.DAYUN_CASES):
  susu 4.35 岁顺 / 叶恒 7.5 岁逆 / 散兵 4.99 岁顺
"""
import argparse
import os
import sys
from datetime import datetime

BAZI_DIR = os.path.expanduser("~/Developer/openclaw-projects/bazi")
sys.path.insert(0, BAZI_DIR)
try:
    import bazi_core
except ImportError as e:
    raise SystemExit(f"需要 bazi-cli + ephem（{e}）。请用 bazi venv 运行：\n"
                     f"  {BAZI_DIR}/venv/bin/python {' '.join(sys.argv)}")

from bazi_tables import STEMS, BRANCHES


def sixty(idx):
    return STEMS[idx % 10] + BRANCHES[idx % 12]


def gz_index(gz):
    s, b = STEMS.index(gz[0]), BRANCHES.index(gz[1])
    for i in range(60):
        if i % 10 == s and i % 12 == b:
            return i
    raise ValueError(gz)


def calc(birth: datetime, gender: str, n_yun: int = 8):
    bz = bazi_core.calculate_bazi(birth)
    pillars = [bz["year_pillar"], bz["month_pillar"], bz["day_pillar"], bz["hour_pillar"]]
    year_stem = pillars[0][0]
    yang_year = STEMS.index(year_stem) % 2 == 0
    forward = (yang_year and gender == "男") or (not yang_year and gender == "女")

    # 距节: 顺排=到下一个节, 逆排=回上一个节 (节 only, 不含中气)
    jie_name, jie_time, _ = bazi_core.get_current_jie(birth)
    if forward:
        # next 节: scan year terms
        terms = bazi_core.get_year_solar_terms(birth.year) + bazi_core.get_year_solar_terms(birth.year + 1)
        jies = sorted(t for name, t in terms if name in bazi_core.MONTH_JIE and t > birth)
        target = jies[0]
        delta_days = (target - birth).total_seconds() / 86400
    else:
        target = jie_time
        delta_days = (birth - target).total_seconds() / 86400
    qiyun_years = delta_days / 3

    month_idx = gz_index(pillars[1])
    dayun = []
    # 起运时刻 = 出生时刻 + 起运年数
    from datetime import timedelta
    qiyun_date = birth + timedelta(days=qiyun_years * 365.2425)
    for i in range(1, n_yun + 1):
        idx = (month_idx + i) % 60 if forward else (month_idx - i) % 60
        dayun.append((sixty(idx), qiyun_date.year + (i - 1) * 10))
    return {"pillars": pillars, "forward": forward, "qiyun_years": qiyun_years,
            "qiyun_date": qiyun_date, "jie_ref": target, "dayun": dayun}


def main():
    ap = argparse.ArgumentParser(description="确定性大运/起运计算 (v2)")
    ap.add_argument("birth", help="ISO 出生时刻，如 1991-02-21T09:00（视为当地标准时/北京时）")
    ap.add_argument("gender", choices=["男", "女"])
    ap.add_argument("--n", type=int, default=8, help="大运数")
    args = ap.parse_args()
    birth = datetime.fromisoformat(args.birth)
    r = calc(birth, args.gender, args.n)
    print("四柱:", " ".join(r["pillars"]))
    print(f"{'顺排' if r['forward'] else '逆排'}（{'阳' if STEMS.index(r['pillars'][0][0]) % 2 == 0 else '阴'}年{args.gender}）"
          f"| 起运 {r['qiyun_years']:.2f} 岁（{r['qiyun_date'].date()}），参照节 {r['jie_ref'].date()}")
    print("大运:", ", ".join(f"{gz}:{y}" for gz, y in r["dayun"]))
    print("     （sweep --dayun 参数可直接粘贴上行）")


if __name__ == "__main__":
    main()
