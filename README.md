# MingLi-Bench

命理判读的确定性引擎 + benchmark 工装。被 `xuanxue-consult` / `xuanxue-calibrate` skill 作为硬 gate 依赖。

## ⚠️ v2 rebuild (2026-08-12)

v1（2026-07-23/24 建，2026-08-07 扩展 liunian_sweep）**无 git remote，两机本地目录先后丢失**，
原始代码不可恢复。v2 按以下材料重建：

- skill `xuanxue-consult` SKILL.md 中的公式规格（力量表公式、sweep 接口、selftest 案例）
- `notes/玄学/wiki/people/*.md` 中记录的 v1 输出：12 张盘的力量表逐字分数 +
  6 张盘的 sweep 命令行与 Top 分数表 + 3 个起运锚点

**教训（已入 KB log）：被 skill 当强制 gate 引用的脚本必须有 git remote。**

## 布局

```
run-2026-07-23/          # 保持 v1 路径（person 页存的命令行直接可用）
  bazi_tables.py         # 干支基础表（藏干/长生/冲合刑会/十神）
  annotate.py            # 力量定级引擎 strength_table()/annotate()，纯 python
  liunian_sweep.py       # 应期枚举 CLI（--selftest），纯 python
  dayun_calc.py          # 大运/起运确定性计算（需 bazi-cli venv 的 ephem）
  calibration_data.py    # 从 vault 恢复的 v1 输出（回归目标）
  test_regression.py     # 回归 gate 全套
  fit_sweep.py / fit_sweep2.py  # 权重拟合工装（dev only，需 numpy）
```

## 与 v1 的差异（使用者必读）

- **力量引擎**：参数几乎完整复原（透干 10 / 根档 本35 中20 余10 / 宫位 年0.9 月1.3 日1.0 时0.85 /
  长生态系数含 SKILL 锚点 帝旺1.3 衰养0.6 绝0.3 / 冲0.5 六合绊0.7）。12 张校准盘方向 12/12，
  总分偏差 ≤15%（惟 hrbp 盘藏党 -14%：v1 疑对亥子丑三会有会局加成，v2 未复原该项）。
  沐浴0.7/病0.5/胎0.4 为 v2 拟合值（校准数据未覆盖）。刑不修正力量（v1 实测行为）。
- **liunian_sweep**：v1 权重不可精确反推。v2 权重按 33 个记录分拟合 + 排名保真约束。
  **分数与 person 页记录的 v1 分数不可比（±7 偏差）；Top 集合/序经回归验证**
  （chao top2 精确、liuchang 5/5 全序、王双 2012/2030 Top4、lucky 8/9、zoujia 5/6、wujiaoyang 4/5）。
  person 页「存命令不存全表」纪律不变，重生的表以 v2 分数为准，老记录当历史对照。
- **dayun_calc**：与 v1 记录精确一致（susu 4.35 岁完全吻合；节气用 bazi-cli 的 ephem 天文计算）。

## 用法

```bash
# 力量表（纯 python，无依赖）
python3 -c "import sys;sys.path.insert(0,'$HOME/Developer/openclaw-projects/MingLi-Bench/run-2026-07-23');from annotate import strength_table;print(strength_table(['辛未','庚寅','壬戌','甲辰']))"

# 应期枚举（纯 python）
python3 run-2026-07-23/liunian_sweep.py '丙寅 戊戌 丙午 丙申' \
  --dayun '丁酉:1993,丙申:2003,乙未:2013,甲午:2023' --from 2026 --to 2045 --top 10

# 起运/大运（需 bazi venv）
~/Developer/openclaw-projects/bazi/venv/bin/python run-2026-07-23/dayun_calc.py 1991-02-21T09:00 女

# 回归全套
~/Developer/openclaw-projects/bazi/venv/bin/python run-2026-07-23/test_regression.py
```

## Benchmark 语料（未恢复）

v1 的 2025 大赛题材料 + 五轮 A/B/D 配置结果（45±3% 平台、RESULTS.md）随目录丢失，
结论已蒸馏在 SKILL「Benchmark 回归」节。如需复测，需重新收集题库。
