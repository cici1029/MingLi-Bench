# -*- coding: utf-8 -*-
"""Regression gates for the v2 rebuild. Run: python3 test_regression.py"""
import subprocess
import sys
import os


def run_strength():
    from calibration_data import STRENGTH_CASES
    from annotate import compute
    fails = []
    print("== strength engine ==")
    for name, c in STRENGTH_CASES.items():
        r = compute(c["pillars"])
        dir_ok = (r["help_total"] < r["drain_total"]) == (c["help_total"] < c["drain_total"])
        h_dev = abs(r["help_total"] - c["help_total"]) / max(c["help_total"], 1)
        d_dev = abs(r["drain_total"] - c["drain_total"]) / max(c["drain_total"], 1)
        status = "✓" if dir_ok and h_dev <= 0.15 and d_dev <= 0.15 else "✗"
        if status == "✗":
            fails.append(name)
        print(f"  {status} {name:<14} rec {c['help_total']}/{c['drain_total']}  "
              f"v2 {r['help_total']}/{r['drain_total']}  方向{'✓' if dir_ok else '✗'}")
    return fails


def run_sweep_selftest():
    from calibration_data import SWEEP_CASES
    from sweep_features import parse_dayun
    from liunian_sweep import sweep
    fails = []
    print("== liunian_sweep selftest ==")

    def ranks(case):
        c = SWEEP_CASES[case]
        rows = sweep(c["pillars"].split(), parse_dayun(c["dayun"]), *c["window"])
        return [r["year"] for r in rows]

    # 王双 2012 壬辰 (柱级伏吟夫宫) 必须 Top4；2030 庚戌 Top3 (rec #2)
    ws = ranks("wangshuang")
    _gate(fails, "王双 2012 in Top4", ws.index(2012) + 1 <= 4, f"rank={ws.index(2012)+1}")
    _gate(fails, "王双 2030 in Top4", ws.index(2030) + 1 <= 4, f"rank={ws.index(2030)+1}")
    # chao: 2026 全窗最高、2027 分低 (「分低险高」示范例)
    ch = ranks("chao")
    _gate(fails, "chao 2026 = #1 (2026-2045)", ch[0] == 2026, f"top={ch[0]}")
    _gate(fails, "chao 2027 outside Top6", ch.index(2027) + 1 > 6, f"rank={ch.index(2027)+1}")
    # Top-set overlap thresholds vs recorded v1 tables
    thresholds = {"chao": 5, "zoujia": 5, "wujiaoyang": 4, "liuchang": 5, "lucky": 8}
    for case, need in thresholds.items():
        c = SWEEP_CASES[case]
        rec = sorted(c["recorded"], key=lambda y: -c["recorded"][y])
        top = ranks(case)[:len(rec)]
        got = len(set(top) & set(rec))
        _gate(fails, f"{case} Top{len(rec)} overlap ≥{need}", got >= need, f"got {got}")
    return 1 if fails else 0


def _gate(fails, name, ok, detail=""):
    print(f"  {'✓' if ok else '✗'} {name} {detail}")
    if not ok:
        fails.append(name)


def run_dayun():
    from calibration_data import DAYUN_CASES
    print("== dayun_calc ==")
    try:
        import ephem  # noqa: F401
        direct = True
    except ImportError:
        direct = False
    fails = []
    for birth, gender, exp_qiyun, exp_dir, exp_yun in DAYUN_CASES:
        if direct:
            from datetime import datetime
            from dayun_calc import calc
            r = calc(datetime.fromisoformat(birth), gender)
            qiyun = r["qiyun_years"]
            direction = "顺" if r["forward"] else "逆"
            yun = [gz for gz, _ in r["dayun"][:len(exp_yun)]]
        else:
            venv = os.path.expanduser("~/Developer/openclaw-projects/bazi/venv/bin/python")
            out = subprocess.run([venv, os.path.join(os.path.dirname(__file__), "dayun_calc.py"),
                                  birth, gender], capture_output=True, text=True).stdout
            qiyun = float(out.split("起运 ")[1].split(" 岁")[0])
            direction = "顺" if "顺排" in out else "逆"
            yun = [x.split(":")[0] for x in out.split("大运: ")[1].split("\n")[0].split(", ")][:len(exp_yun)]
        ok = abs(qiyun - exp_qiyun) <= 0.1 and direction == exp_dir and yun == exp_yun
        print(f"  {'✓' if ok else '✗'} {birth} {gender}: 起运 {qiyun:.2f} (期望 {exp_qiyun}) {direction} {yun}")
        if not ok:
            fails.append(birth)
    return fails


if __name__ == "__main__":
    f1 = run_strength()
    f2 = run_sweep_selftest()
    f3 = run_dayun()
    total = len(f1) + (f2 if isinstance(f2, int) else 0) + len(f3)
    print(f"\n{'ALL GATES PASS' if not total else f'FAILURES: {total}'}")
    sys.exit(1 if total else 0)
