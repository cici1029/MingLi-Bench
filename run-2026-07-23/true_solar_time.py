# true_solar_time.py: clock time + longitude -> true solar time + 时辰 branch (2026-11-04)
# Ported from Renhuai123/ziwei-doushu lib/ziwei/true-solar-time.ts (MIT). Formula: NOAA
# solar equations (Spencer series), accuracy about +-0.5 min, enough for 时辰 boundaries.
# Does NOT handle DST: convert a DST clock reading to standard time first (China 1986-1991 summers,
# US/EU summers). utc_offset_min = standard offset of the birth place (Beijing 480, PST -480).
# Usage:
#   python3 true_solar_time.py 1990-07-15 12:00 --lon 116.4            # Beijing time, Beijing
#   python3 true_solar_time.py 1997-05-21 14:10 --lon -122.4 --utc-offset -480
#   python3 true_solar_time.py --selftest
import argparse, datetime, math

ZHI = "子丑寅卯辰巳午未申酉戌亥"

def equation_of_time(y, m, d, hh=12, mm=0):
    """minutes; positive = sundial ahead of mean time"""
    n = (datetime.date(y, m, d) - datetime.date(y, 1, 1)).days + 1
    days = 366 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 365
    g = 2 * math.pi / days * (n - 1 + (hh + mm / 60 - 12) / 24)
    return 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                     - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))

def branch_index(minute_of_day):
    """0=子 .. 11=亥; 子 spans 23:00-00:59"""
    if minute_of_day >= 1380 or minute_of_day < 60: return 0
    return int((minute_of_day - 60) // 120) + 1

def true_solar(y, m, d, hh, mm, lon, utc_offset_min=480):
    meridian = utc_offset_min / 4
    lon_corr = (lon - meridian) * 4
    eot = equation_of_time(y, m, d, hh, mm)
    raw = hh * 60 + mm + lon_corr + eot
    secs = round(raw * 60)
    day_offset = secs // 86400
    sod = secs % 86400
    return {"lon_corr_min": lon_corr, "eot_min": eot, "total_corr_min": lon_corr + eot,
            "day_offset": day_offset, "clock": f"{sod // 3600:02d}:{sod % 3600 // 60:02d}:{sod % 60:02d}",
            "branch": branch_index(sod / 60)}

def selftest():
    # reference values produced by the upstream TS implementation (calculateTrueSolarTime)
    cases = [((1990, 7, 15, 12, 0, 116.4, 480), "11:39:49", 6, 0),
             ((1986, 2, 11, 23, 30, 87.6, 480), "21:06:11", 11, 0),
             ((2000, 11, 3, 0, 20, 126.6, 480), "01:02:46", 1, 0),
             ((1997, 5, 21, 14, 10, -122.4, -480), "14:04:08", 7, 0),
             ((2010, 12, 31, 23, 55, 135.0, 480), "00:52:19", 0, 1)]
    for args, clock, br, off in cases:
        r = true_solar(*args)
        assert (r["clock"], r["branch"], r["day_offset"]) == (clock, br, off), (args, r)
    assert abs(equation_of_time(2026, 11, 3) - 16.4) < 0.6  # NOAA table: about +16.4 min
    assert abs(equation_of_time(2026, 2, 11) + 14.2) < 0.6  # about -14.2 min
    print("selftest OK")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("date", nargs="?"); ap.add_argument("time", nargs="?")
    ap.add_argument("--lon", type=float); ap.add_argument("--utc-offset", type=int, default=480)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest()
    else:
        y, m, d = map(int, a.date.split("-")); hh, mm = map(int, a.time.split(":"))
        r = true_solar(y, m, d, hh, mm, a.lon, a.utc_offset)
        print(f"真太阳时 {r['clock']} ({ZHI[r['branch']]}时, time-index {r['branch']}) day_offset={r['day_offset']} "
              f"| 经度差 {r['lon_corr_min']:+.1f} 均时差 {r['eot_min']:+.1f} 合计 {r['total_corr_min']:+.1f} 分钟")
