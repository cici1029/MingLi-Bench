// liuyue_flags.js: ziwei flow-month overlay flags (2026-11-19). For each lunar month: flow-month palace, month 四化 landing,
// and overlaps of the month 忌/禄 with natal 忌, flow-year 忌, decadal 忌 and the month palace itself.
// Usage: node liuyue_flags.js <label>:<YYYY-MM-DD>:<timeIndex>:<男|女> [more people...] [--from 2026-11] [--to 2028-01]
const { astro } = require('iztro');
const argv = process.argv.slice(2); const opt = n => { const i = argv.indexOf('--'+n); return i >= 0 ? argv[i+1] : null; };
const [Y0, M0] = (opt('from') || '2026-11').split('-').map(Number), [Y1, M1] = (opt('to') || '2028-01').split('-').map(Number);
const people = {}; argv.filter(a => a.includes(':')).forEach(a => { const [k, d, t, g] = a.split(':'); people[k] = [d, +t, g]; });
const Z='子丑寅卯辰巳午未申酉戌亥';
const nm = n => n==='事业'?'官禄':n==='交友'?'仆役':n;
for (const [k,[date,ti,g]] of Object.entries(people)) {
  const a = astro.bySolar(date, ti, g, true, 'zh-CN');
  const natal = a.palaces.map(p=>({name:nm(p.name),branch:p.earthlyBranch,stars:[...p.majorStars,...p.minorStars]}));
  const find = s => { const p = natal.find(p=>p.stars.some(x=>x.name===s)); return p?p.name:'-'; };
  const opp = n => { const p=natal.find(x=>x.name===n); return p?natal.find(x=>x.branch===Z[(Z.indexOf(p.branch)+6)%12]).name:'-'; };
  const birthHua = {}; natal.forEach(p=>p.stars.forEach(s=>{ if(s.mutagen) birthHua[s.mutagen]=`${s.name}@${p.name}`; }));
  console.log(`\n#### ${k} 生年四化 ${JSON.stringify(birthHua)}`);
  let lastY='';
  for (let y=Y0,m=M0; y<Y1||(y===Y1&&m<=M1); m===12?(y++,m=1):m++) {
    const h=a.horoscope(`${y}-${m}-15`, ti);
    const yk = h.yearly.heavenlyStem+h.yearly.earthlyBranch;
    if (yk!==lastY) { lastY=yk;
      const d=h.decadal, yr=h.yearly;
      console.log(`  [${yk}] 虚岁${h.age.nominalAge} 大限命=${natal[d.index].name}(${d.heavenlyStem}${d.earthlyBranch}) 限四化 ${d.mutagen.map(s=>s+'>'+find(s)).join(' ')} | 流年命=${natal[yr.index].name} 年四化 ${yr.mutagen.map(s=>s+'>'+find(s)).join(' ')} | 小限=${natal[h.age.index].name}`);
    }
    const mo=h.monthly; const [lu,qu,ke,ji]=mo.mutagen;
    const mp=natal[mo.index].name, jp=find(ji), lp=find(lu);
    const yji=find(h.yearly.mutagen[3]), dji=find(h.decadal.mutagen[3]), bji=(birthHua['忌']||'').split('@')[1];
    const fl=[];
    if(jp===mp) fl.push('忌坐月命'); if(opp(jp)===mp) fl.push('忌冲月命');
    if(jp===yji) fl.push('叠流年忌'); if(jp===dji) fl.push('叠限忌'); if(jp===bji) fl.push('叠生年忌');
    if(jp==='命宫') fl.push('忌入本命'); if(opp(jp)==='命宫') fl.push('忌冲本命');
    if(lp===mp) fl.push('禄坐月命'); if(opp(lp)===mp) fl.push('禄照月命'); if(lp==='命宫') fl.push('禄入本命');
    if(mp===yji) fl.push('月命踩流年忌'); if(mp===bji) fl.push('月命踩生年忌'); if(mp===opp(yji)) fl.push('月命受流年忌冲');
    // relative-to-liunian palace of the month
    const rel = ['命宫','兄弟','夫妻','子女','财帛','疾厄','迁移','仆役','官禄','田宅','福德','父母'];
    const yb=Z.indexOf(natal[h.yearly.index].branch), mb=Z.indexOf(natal[mo.index].branch);
    const relName = rel[((yb-mb)%12+12)%12];
    console.log(`  ${y}-${String(m).padStart(2,'0')} 农${h.lunarDate.slice(5)} ${mo.heavenlyStem}${mo.earthlyBranch} 月命=${mp}(流年${relName}) 禄${lu}>${lp} 权${qu}>${find(qu)} 科${ke}>${find(ke)} 忌${ji}>${jp}冲${opp(jp)} ${fl.length?'【'+fl.join(',')+'】':''}`);
  }
}
