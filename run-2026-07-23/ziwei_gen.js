// ziwei_gen.js — iztro 排盘 → ziwei_sweep.py 可食用 JSON (2026-08-29)
// 用法:
//   node ziwei_gen.js --date 1990-5-4 --time 14:30 --gender 男
//   node ziwei_gen.js --date 2000-8-16 --time-index 2 --gender 女
// 输出 JSON: { year_stem, palaces:[{name,stem,branch,stars}], decadal:[{palace,branch,stem,range}], meta }
// 注: iztro chineseDate 年干按农历界年 (非立春), 生年四化以此为准 (紫微系内自洽, 与八字节气界分歧属正常, 见 2026-07-30 小多多案)
const { astro } = require("iztro");

function arg(name, def) {
  const i = process.argv.indexOf("--" + name);
  return i > 0 ? process.argv[i + 1] : def;
}

const date = arg("date");
const gender = arg("gender");
let timeIndex = arg("time-index", null);
const time = arg("time", null);
if (!date || !gender || (timeIndex === null && time === null)) {
  console.error("usage: node ziwei_gen.js --date YYYY-M-D (--time HH:MM | --time-index 0-12) --gender 男|女");
  process.exit(2);
}
if (timeIndex === null) {
  const h = parseInt(time.split(":")[0], 10);
  timeIndex = h >= 23 ? 12 : Math.floor((h + 1) / 2); // 0=早子(00-01), 12=晚子(23-24)
} else {
  timeIndex = parseInt(timeIndex, 10);
}

const h = astro.bySolar(date, timeIndex, gender, true, "zh-CN");
const palaces = h.palaces.map((p) => ({
  name: p.name === "事业" ? "官禄" : p.name === "交友" ? "仆役" : p.name,
  stem: p.heavenlyStem,
  branch: p.earthlyBranch,
  stars: [...p.majorStars, ...p.minorStars].map((s) => s.name),
  adj: p.adjectiveStars.map((s) => s.name), // 杂曜 (红鸾/天喜/天马/天姚等, 婚期/迁移应期要用)
}));
const decadal = h.palaces.map((p) => ({
  palace: p.name === "事业" ? "官禄" : p.name === "交友" ? "仆役" : p.name,
  branch: p.earthlyBranch,
  stem: p.decadal.heavenlyStem,
  range: p.decadal.range, // 虚岁
}));

console.log(JSON.stringify({
  year_stem: h.chineseDate[0],
  year_branch: h.chineseDate[1],
  palaces,
  decadal,
  meta: {
    solar: h.solarDate, lunar: h.lunarDate, chineseDate: h.chineseDate,
    timeIndex, gender, soul: h.soul, body: h.body, fiveElementsClass: h.fiveElementsClass,
  },
}, null, 1));
