# hkjfma 2026 第十七屆全球算命師大賽（干净 held-out 语料）

抓取 2026-08-13，源 = hkjfma.org（香港青年術數家協會）2026-06 赛题公告页。
公司机 FortiClient 封锁该站，经 mini 中转下载（http 需升 https，中文文件名需 percent-encode）。

## 为什么这份语料珍贵

- 答案 2026-08-08 才公布（得奖名单 08-10），**几乎不可能进任何 LLM 训练数据** = 无污染 held-out
- 上游 DestinyLinker/MingLi-Bench 只覆盖到 2025（160 题）；本目录是 2026 当届 40 题
- vault _meta/2026-07-23 blindspot 文档预判过：公开旧题有背题风险，「真正干净的 held-out 是 2026 当届」

## 文件

- `raw/q_01-05.jpg … q_36-40.jpg`：40 题原图（8 命例 × 5 题，每张含命例生辰 + 提供者 + 术数流派）
- `raw/q_signup.jpg / q_rules.jpg`：报名表 + 报名须知
- `raw/answers-20260808.jpg`：官方手写正确答案表
- `raw/winners-20260810.jpeg`：得奖名单
- `answers.json`：答案表机读转录（vision 转录，已对图抽验）

## 待办

- [ ] 40 题 vision 转录成 upstream data.json 同构格式（birth_info + question + options + answer），入 `data.json`
- [ ] 用 v2 引擎 + 判读工序跑一轮盲测，与 2022-2025 旧题分数对照（背题程度检测）
- [ ] 2027 第十八届报名：每年 6 月开赛、立秋截止（2026 届 8/8 出答案）；dida 已设 2027-06 提醒

## 时间线（2026 届，供 2027 报名参考）

- 2026-06：赛题 + 报名公告上线（40 题公开，线上免费，allcounted.com 表单提交答案）
- 截止：立秋（约 08-07）
- 2026-08-08：公布答案；2026-08-10：公布得奖名单
