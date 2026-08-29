# ziwei_annotate.py — 紫微事实层 v1 (2026-07-24) + v2 飞星派演算 (2026-07-25)
# 输入: palaces = [{"name":宫名,"stem":干,"branch":支,"stars":[星名,...]}] (含辅星)
# 输出: 三方四正 / 生年四化定位 / 自化 / 飞化矩阵 / 忌冲 / 叠加 flags —— 全确定性
# v2 追加: 交禄交忌 / 禄随忌走 / 禄转忌链 / 照与冲 / 命盘六线 / 共宗六位破 (规则源: 玄学 wiki ziwei 蒸馏页)
ZHI = "子丑寅卯辰巳午未申酉戌亥"
# 飞星派十干四化（梁若瑜系统：戊右弼科、壬左辅科）
SIHUA = {
"甲":("廉贞","破军","武曲","太阳"), "乙":("天机","天梁","紫微","太阴"),
"丙":("天同","天机","文昌","廉贞"), "丁":("太阴","天同","天机","巨门"),
"戊":("贪狼","太阴","右弼","天机"), "己":("武曲","贪狼","天梁","文曲"),
"庚":("太阳","武曲","太阴","天同"), "辛":("巨门","太阳","文曲","文昌"),
"壬":("天梁","紫微","左辅","武曲"), "癸":("破军","巨门","太阴","贪狼")}
HUA_NAMES = ["禄","权","科","忌"]

def _find_star(palaces, star):
    for p in palaces:
        if star in p["stars"]: return p
    return None

def sanfang(palaces, name):
    me=[p for p in palaces if p["name"]==name][0]
    bi=ZHI.index(me["branch"])
    targets={"对宫":ZHI[(bi+6)%12], "三合1":ZHI[(bi+4)%12], "三合2":ZHI[(bi+8)%12]}
    out={}
    for k,b in targets.items():
        tp=[p for p in palaces if p["branch"]==b][0]
        out[k]=(tp["name"], tp["branch"], tp["stars"])
    return me, out

def annotate_ziwei(palaces, year_stem):
    L=[]
    # 1 生年四化定位
    ss=SIHUA[year_stem]
    L.append(f"生年四化（{year_stem}年: {ss[0]}禄 {ss[1]}权 {ss[2]}科 {ss[3]}忌）定位:")
    ji_palace=None
    for star,hua in zip(ss,HUA_NAMES):
        p=_find_star(palaces,star)
        if p:
            L.append(f"  生年{hua}（{star}）在 {p['name']}宫{p['branch']}")
            if hua=="忌": ji_palace=p
        else:
            L.append(f"  生年{hua}（{star}）不在盘面星表中（借星/缺录待查）")
    if ji_palace:
        opp=ZHI[(ZHI.index(ji_palace["branch"])+6)%12]
        op=[p for p in palaces if p["branch"]==opp][0]
        L.append(f"  生年忌冲: {ji_palace['name']}忌 冲 {op['name']}宫{opp}")
    # 2 自化
    zh=[]
    for p in palaces:
        ss_p=SIHUA[p["stem"]]
        for star,hua in zip(ss_p,HUA_NAMES):
            if star in p["stars"]: zh.append(f"{p['name']}宫{p['stem']}{p['branch']} 自化{hua}（{star}）")
    if zh: L.append("自化: " + "；".join(zh))
    # 3 飞化矩阵（各宫干飞四化落宫）
    L.append("飞化矩阵（宫干四化落宫，飞星派核心）:")
    ji_in={}
    for p in palaces:
        ss_p=SIHUA[p["stem"]]
        cells=[]
        for star,hua in zip(ss_p,HUA_NAMES):
            t=_find_star(palaces,star)
            if t and t["name"]!=p["name"]:
                cells.append(f"{hua}入{t['name']}")
                if hua=="忌": ji_in.setdefault(t["name"],[]).append(p["name"])
        if cells: L.append(f"  {p['name']}({p['stem']}{p['branch']}): " + " ".join(cells))
    # 4 叠忌 flags
    dup=[f"{k}宫收{len(v)}忌（{'、'.join(v)}）" for k,v in ji_in.items() if len(v)>=2]
    if dup: L.append("叠忌警: " + "；".join(dup))
    return "\n".join(L)

# ============================================================================
# v2 — 飞星派可码化演算（规则源：玄学 wiki ziwei/ concepts+techniques 蒸馏页）
# ============================================================================

LU_STARS = {v[0] for v in SIHUA.values()}   # 可化禄之星（文昌文曲左右弼无禄，交禄不成之判据）
ORDER = ["命宫","兄弟","夫妻","子女","财帛","疾厄","迁移","仆役","官禄","田宅","福德","父母"]
# 命盘六线（[[命盘六线]]：对宫两两成线，坐宫与对宫一体论）
LINES = [("命迁线","命宫","迁移","个性与待人处世的态度"),
         ("兄友线","兄弟","仆役","创业、成就与人际"),
         ("夫官线","夫妻","官禄","工作与异性的关系"),
         ("子田线","子女","田宅","家庭、经济、亲属、下一代"),
         ("福财线","福德","财帛","享福与花钱、赚钱的态度"),
         ("父疾线","父母","疾厄","长辈、思考、身体健康")]

def _pal(palaces, name):
    for p in palaces:
        if p["name"]==name: return p
    return None

def _opp(palaces, p):
    b=ZHI[(ZHI.index(p["branch"])+6)%12]
    return [q for q in palaces if q["branch"]==b][0]

def _self_hua(p, hua_idx):
    return SIHUA[p["stem"]][hua_idx] in p["stars"]

def _incoming(palaces, hua_idx):
    """外来飞化落宫: {target_name: [(src_name, star), ...]}（不含自化）"""
    book={}
    for p in palaces:
        star=SIHUA[p["stem"]][hua_idx]
        t=_find_star(palaces, star)
        if t is not None and t["name"]!=p["name"]:
            book.setdefault(t["name"],[]).append((p["name"], star))
    return book

def _ji_load(palaces, name, year_stem=None):
    """一宫的忌总量: 外来飞忌 + 自化忌 + 生年忌坐（共宗破/多忌判据）"""
    n=len(_incoming(palaces,3).get(name,[]))
    p=_pal(palaces,name)
    if _self_hua(p,3): n+=1
    if year_stem and SIHUA[year_stem][3] in p["stars"]: n+=1
    return n

def jiaolu_jiaoji(palaces, year_stem=None):
    """交禄/交忌判定（[[交禄]][[交忌]]）。
    交禄: 两宫互飞禄=相辅相成；两宫禄会于同一宫=交禄（落点宫变强）；同星禄+权会=交禄权（相辅相成）。
    交忌: 两宫忌入同宫=冷战型；两宫忌入对宫（破在该线）=打架型，媒介线两端只是媒介不算不合；
          忌入生年忌所在宫=与生年忌交忌。"""
    lu_in=_incoming(palaces,0); ji_in=_incoming(palaces,3)
    out={"jiaolu_mutual":[], "jiaolu_converge":[], "jiaoluquan":[], "jiaoji":[]}
    # 互飞禄（A禄入B 且 B禄入A）= 相辅相成
    seen=set()
    for tgt,srcs in lu_in.items():
        for src,_ in srcs:
            if any(s==tgt for s,_ in lu_in.get(src,[])):
                key=frozenset((src,tgt))
                if key not in seen:
                    seen.add(key); out["jiaolu_mutual"].append((src,tgt))
    # 两宫禄会于同一宫（落点宫提升等级；透过的宫不变强）
    for tgt,srcs in lu_in.items():
        if len(srcs)>=2:
            out["jiaolu_converge"].append({"at":tgt,"sources":srcs})
    # 交禄权: 同星曜 禄+权 来会（我禄有情 + 对方权大助力 = 相辅相成）
    quan_in=_incoming(palaces,1)
    for tgt,lsrcs in lu_in.items():
        for lsrc,lstar in lsrcs:
            for qsrc,qstar in quan_in.get(tgt,[]):
                if qstar==lstar and qsrc!=lsrc:
                    out["jiaoluquan"].append({"star":lstar,"at":tgt,"lu_src":lsrc,"quan_src":qsrc})
    # 交忌·冷战型: 两宫忌入同宫
    for tgt,srcs in ji_in.items():
        names=[s for s,_ in srcs]
        for i in range(len(names)):
            for j in range(i+1,len(names)):
                out["jiaoji"].append({"type":"冷战型","pair":(names[i],names[j]),"at":tgt})
    # 交忌·打架型: 两宫忌入对宫（破在媒介线上；线两端只是媒介）
    done=set()
    for tgt in list(ji_in):
        tp=_pal(palaces,tgt); op=_opp(palaces,tp)
        key=frozenset((tgt,op["name"]))
        if op["name"] in ji_in and key not in done:
            done.add(key)
            line=next((l for l in LINES if {l[1],l[2]}=={tgt,op["name"]}), None)
            for a,_ in ji_in[tgt]:
                for b,_ in ji_in[op["name"]]:
                    if a!=b:
                        out["jiaoji"].append({"type":"打架型","pair":(a,b),
                            "line":(tgt,op["name"]),
                            "line_name":line[0] if line else f"{tgt}-{op['name']}线"})
    # 与生年忌同宫交忌
    if year_stem:
        nj=_find_star(palaces, SIHUA[year_stem][3])
        if nj:
            for src,star in ji_in.get(nj["name"],[]):
                out["jiaoji"].append({"type":"与生年忌同宫","pair":(src,"生年忌"),"at":nj["name"]})
    return out

def lu_sui_ji(palaces):
    """禄随忌走（[[禄随忌走]]）: 同星曜他宫化忌 + 他宫化禄 → 禄被忌带到该星所在宫。
    排除: 落点宫自化忌时，他宫禄入是填补/擦屁股，不叫禄随忌走。"""
    out=[]
    stars={s for p in palaces for s in p["stars"]}
    for star in sorted(stars):
        tgt=_find_star(palaces, star)
        ji_src=[p["name"] for p in palaces if SIHUA[p["stem"]][3]==star and p["name"]!=tgt["name"]]
        lu_src=[p["name"] for p in palaces if SIHUA[p["stem"]][0]==star and p["name"]!=tgt["name"]]
        if ji_src and lu_src:
            kind="填补（禄入逢自化忌，非禄随忌走）" if _self_hua(tgt,3) else "禄随忌走"
            out.append({"star":star,"at":tgt["name"],"ji_src":ji_src,"lu_src":lu_src,"kind":kind})
    return out

def lu_zhuan_ji(palaces, start):
    """禄转忌链（[[禄转忌与忌转忌]]）: start 宫干化禄入 A，A 宫干再化忌入 B = 禄的最终归宿。
    三重解释: ①start禄入A ②A禄入B ③start禄入B（透过A）。
    逢禄来会（[[交禄]]）: 他宫同星（转忌之星）化禄入 B → 交禄成；转忌之星无禄可化则交禄不成。"""
    s=_pal(palaces,start)
    r={"start":start,"lu_star":SIHUA[s["stem"]][0],"A":None,"ji_star":None,"B":None,
       "feng_lu":[],"jiaolu_ok":False,"explanations":[],"notes":[]}
    A=_find_star(palaces, r["lu_star"])
    if A is None:
        r["notes"].append(f"化禄星{r['lu_star']}不在盘面星表，链中断"); return r
    r["A"]=A["name"]
    if A["name"]==start:
        r["notes"].append(f"{start}自化禄（{r['lu_star']}），只有一条解释（本宫自化），不转忌"); return r
    r["ji_star"]=SIHUA[A["stem"]][3]
    B=_find_star(palaces, r["ji_star"])
    if B is None:
        r["explanations"]=[f"{start}禄入{A['name']}"]
        r["notes"].append(f"转忌星{r['ji_star']}不在盘面星表，链止于{A['name']}"); return r
    r["B"]=B["name"]
    if B["name"]==A["name"]:
        r["explanations"]=[f"{start}禄入{A['name']}", f"{A['name']}自化忌（{r['ji_star']}），气收于本宫且自我消散"]
        r["notes"].append("转忌逢自化忌")
    else:
        r["explanations"]=[f"{start}禄入{A['name']}", f"{A['name']}禄入{B['name']}",
                           f"{start}禄入{B['name']}（透过{A['name']}，透过之宫不变强）"]
    # 逢禄来会
    if r["ji_star"] not in LU_STARS:
        r["notes"].append(f"转忌之星{r['ji_star']}无禄可化，逢不了、交禄不成")
    else:
        r["feng_lu"]=[p["name"] for p in palaces
                      if SIHUA[p["stem"]][0]==r["ji_star"] and p["name"] not in (start,A["name"],B["name"])]
        r["jiaolu_ok"]=bool(r["feng_lu"])
    return r

def zhao_chong(palaces, year_stem):
    """照与冲（[[照与冲]]）: 生年禄权科坐宫→照对宫（吉）；忌坐宫→冲对宫（动荡、过后即愈）。"""
    out=[]
    for star,hua in zip(SIHUA[year_stem],HUA_NAMES):
        p=_find_star(palaces,star)
        if p is None: continue
        op=_opp(palaces,p)
        out.append({"hua":hua,"star":star,"at":p["name"],"opp":op["name"],
                    "mode":"冲" if hua=="忌" else "照"})
    return out

def liuxian(palaces, year_stem=None):
    """命盘六线逐线体检（[[命盘六线]]）: 线上生年四化 / 自化 / 忌总量，输出线级 flag。"""
    ji_in=_incoming(palaces,3)
    out=[]
    for lname,a,b,meaning in LINES:
        pa,pb=_pal(palaces,a),_pal(palaces,b)
        if pa is None or pb is None: continue
        rec={"line":lname,"palaces":(a,b),"meaning":meaning,"nianhua":[],"zihua":[],"flags":[]}
        for p in (pa,pb):
            if year_stem:
                for star,hua in zip(SIHUA[year_stem],HUA_NAMES):
                    if star in p["stars"]: rec["nianhua"].append(f"生年{hua}（{star}）坐{p['name']}")
            for star,hua in zip(SIHUA[p["stem"]],HUA_NAMES):
                if star in p["stars"]: rec["zihua"].append(f"{p['name']}自化{hua}（{star}）")
        fly_ji=len(ji_in.get(a,[]))+len(ji_in.get(b,[]))
        total_ji=_ji_load(palaces,a,year_stem)+_ji_load(palaces,b,year_stem)
        rec["ji_in"]=fly_ji; rec["ji_total"]=total_ji
        if rec["nianhua"]: rec["flags"].append("有生年四化")
        if rec["zihua"]: rec["flags"].append("有自化")
        if total_ji>=2: rec["flags"].append("多忌")
        out.append(rec)
    return out

def gongzong_po(palaces, year_stem=None):
    """共宗六位破（[[共宗六位]]）: 某宫顺数第六宫为其'身'；共宗位忌总量≥2（双忌以上）即破。"""
    out=[]
    for name in ORDER:
        if _pal(palaces,name) is None: continue
        six=ORDER[(ORDER.index(name)+5)%12]
        if _pal(palaces,six) is None: continue
        load=_ji_load(palaces,six,year_stem)
        if load>=2:
            out.append({"palace":name,"six":six,"ji":load})
    return out

def annotate_ziwei_v2(palaces, year_stem):
    """v2 汇总入口 = v1 输出 + 交禄交忌 + 禄随忌走 + 禄转忌链（命/田宅/福德）+ 照冲 + 六线 + 共宗破。"""
    L=[annotate_ziwei(palaces, year_stem), "", "=== v2 飞星派演算 ==="]
    # 1 交禄 / 交忌
    jj=jiaolu_jiaoji(palaces, year_stem)
    L.append("交禄/交忌:")
    for a,b in jj["jiaolu_mutual"]:
        L.append(f"  交禄（互飞禄）: {a}⇄{b} ＝相辅相成")
    for e in jj["jiaolu_converge"]:
        src=", ".join(f"{s}({st}禄)" for s,st in e["sources"])
        L.append(f"  会禄: {src} 会于{e['at']} → {e['at']}提升等级（透过之宫不变强）")
    for e in jj["jiaoluquan"]:
        L.append(f"  交禄权: {e['lu_src']}{e['star']}禄 + {e['quan_src']}{e['star']}权 会于{e['at']} ＝相辅相成")
    for e in jj["jiaoji"]:
        if e["type"]=="冷战型":
            L.append(f"  交忌·冷战型: {e['pair'][0]}×{e['pair'][1]} 忌入同宫{e['at']} ＝八字不合（冷战）")
        elif e["type"]=="打架型":
            L.append(f"  交忌·打架型: {e['pair'][0]}×{e['pair'][1]} 忌入对宫，破在{e['line_name']}"
                     f"（{e['line'][0]}/{e['line'][1]}只是媒介，不算不合）")
        else:
            L.append(f"  交忌·与生年忌同宫: {e['pair'][0]} 忌入{e['at']}（坐生年忌）＝与生年忌不合")
    # 2 禄随忌走
    ls=lu_sui_ji(palaces)
    if ls:
        L.append("禄随忌走:")
        for d in ls:
            L.append(f"  {d['star']}@{d['at']}: {'、'.join(d['ji_src'])}忌 + {'、'.join(d['lu_src'])}禄 → {d['kind']}")
    # 3 禄转忌链（三要宫各追一层）
    L.append("禄转忌链（命宫/田宅/福德）:")
    for start in ("命宫","田宅","福德"):
        if _pal(palaces,start) is None: continue
        r=lu_zhuan_ji(palaces,start)
        chain=f"  {start}--{r['lu_star']}禄-->{r['A'] or '?'}"
        if r["B"]: chain+=f"--{r['ji_star']}忌-->{r['B']}"
        L.append(chain)
        for ex in r["explanations"]: L.append(f"    解: {ex}")
        for n in r["notes"]: L.append(f"    注: {n}")
        if r["jiaolu_ok"]:
            L.append(f"    逢{'、'.join(r['feng_lu'])}{r['ji_star']}禄来会 ＝交禄成，{r['B']}变好")
    # 4 照与冲
    L.append("照与冲（生年四化隔空作用）:")
    for e in zhao_chong(palaces,year_stem):
        note="动荡、过了冲即愈" if e["mode"]=="冲" else "吉"
        L.append(f"  生年{e['hua']}（{e['star']}）坐{e['at']} {e['mode']}{e['opp']}（{note}）")
    # 5 命盘六线
    L.append("命盘六线体检:")
    for rec in liuxian(palaces,year_stem):
        det="；".join(rec["nianhua"]+rec["zihua"]) or "无生年四化/自化"
        fl=" ".join(f"[{f}]" for f in rec["flags"]) or "[平]"
        L.append(f"  {rec['line']}（{rec['meaning']}）: {det}；飞忌入线{rec['ji_in']}、忌总量{rec['ji_total']} {fl}")
    # 6 共宗六位破
    po=gongzong_po(palaces,year_stem)
    if po:
        L.append("共宗六位破（共宗位双忌以上即破）:")
        for e in po:
            L.append(f"  {e['palace']}之共宗（{e['six']}）忌总量{e['ji']} ＝{e['six']}破，改写{e['palace']}之事")
    return "\n".join(L)

if __name__ == "__main__":
    # 单元测试 1: Lucian（癸年）12 宫（自 people/lucian.md 表转录）
    P=[{"name":"命宫","stem":"庚","branch":"申","stars":["廉贞"]},
       {"name":"父母","stem":"辛","branch":"酉","stars":["右弼"]},
       {"name":"福德","stem":"壬","branch":"戌","stars":["破军"]},
       {"name":"田宅","stem":"癸","branch":"亥","stars":["天同","文曲"]},
       {"name":"官禄","stem":"甲","branch":"子","stars":["武曲","天府"]},
       {"name":"仆役","stem":"乙","branch":"丑","stars":["太阳","太阴"]},
       {"name":"迁移","stem":"甲","branch":"寅","stars":["贪狼"]},
       {"name":"疾厄","stem":"乙","branch":"卯","stars":["天机","巨门","文昌"]},
       {"name":"财帛","stem":"丙","branch":"辰","stars":["紫微","天相"]},
       {"name":"子女","stem":"丁","branch":"巳","stars":["天梁","左辅"]},
       {"name":"夫妻","stem":"戊","branch":"午","stars":["七杀"]},
       {"name":"兄弟","stem":"己","branch":"未","stars":[]}]
    out=annotate_ziwei(P,"癸")
    assert "生年禄（破军）在 福德宫戌" in out, "破军禄定位应在福德[身]"
    assert "生年忌（贪狼）在 迁移宫寅" in out, "贪狼忌应在迁移"
    me,sf=sanfang(P,"命宫")
    assert sf["对宫"][0]=="迁移" and {sf["三合1"][0],sf["三合2"][0]}=={"官禄","财帛"}
    print(annotate_ziwei_v2(P,"癸"))

    # v2 断言（机制规则自洽性验证）
    jj=jiaolu_jiaoji(P,"癸")
    # A1 交忌打架型: 田宅忌入迁移 + 财帛忌入命宫（迁移对宫）→ 田宅×财帛 打架，破在命迁线
    assert any(e["type"]=="打架型" and set(e["pair"])=={"田宅","财帛"} and e["line_name"]=="命迁线"
               for e in jj["jiaoji"]), "田宅×财帛应为打架型交忌破在命迁线"
    # A2 交忌冷战型: 父母/子女同忌入疾厄
    assert any(e["type"]=="冷战型" and set(e["pair"])=={"父母","子女"} and e["at"]=="疾厄"
               for e in jj["jiaoji"]), "父母×子女应为冷战型交忌于疾厄"
    # A3 机制自洽: 交忌类型判定与忌入方向一致（冷战=同落点；打架=落点互为对宫）
    for e in jj["jiaoji"]:
        if e["type"]=="冷战型":
            lands={_find_star(P,SIHUA[_pal(P,s)["stem"]][3])["name"] for s in e["pair"]}
            assert lands=={e["at"]}, "冷战型两宫忌应落同一宫"
        elif e["type"]=="打架型":
            x,y=e["line"]
            assert (ZHI.index(_pal(P,x)["branch"])-ZHI.index(_pal(P,y)["branch"]))%12==6, \
                "打架型两落点应互为对宫"
    # A4 禄随忌走: 命宫天同忌入田宅 + 财帛天同禄 → 财帛之禄随命宫之忌到田宅
    ls=lu_sui_ji(P)
    assert any(d["star"]=="天同" and d["at"]=="田宅" and "命宫" in d["ji_src"]
               and "财帛" in d["lu_src"] and d["kind"]=="禄随忌走" for d in ls), \
        "财帛天同禄应随命宫天同忌走到田宅"
    # A5 机制自洽: 落点宫自化忌 ⟺ 判为填补（非禄随忌走）
    for d in ls:
        assert _self_hua(_pal(P,d["at"]),3)==d["kind"].startswith("填补"), \
            "自化忌落点必须判填补，非自化忌落点必须判禄随忌走"
    # A6 禄转忌链: 田宅破军禄入福德，福德壬武曲忌入官禄；逢兄弟己武曲禄来会=交禄成
    lz=lu_zhuan_ji(P,"田宅")
    assert lz["A"]=="福德" and lz["B"]=="官禄" and "兄弟" in lz["feng_lu"] and lz["jiaolu_ok"], \
        "田宅禄转忌链应为 田宅→福德→官禄，逢兄弟武曲禄交禄成"
    # A7 照冲: 生年忌坐迁移冲命宫，且与 v1 忌冲行同向；禄权科皆为照
    zc=zhao_chong(P,"癸")
    ji_e=[e for e in zc if e["hua"]=="忌"][0]
    assert ji_e["at"]=="迁移" and ji_e["opp"]=="命宫" and ji_e["mode"]=="冲"
    assert f"生年忌冲: 迁移忌 冲 命宫宫申" in out, "v2 冲向应与 v1 忌冲一致"
    assert all(e["mode"]=="照" for e in zc if e["hua"]!="忌"), "禄权科应为照非冲"
    # A8 六线: 命迁线坐生年忌 + 忌总量≥2 → 多忌 flag
    mq=[l for l in liuxian(P,"癸") if l["line"]=="命迁线"][0]
    assert "多忌" in mq["flags"] and any("生年忌" in s for s in mq["nianhua"]), \
        "命迁线应有生年忌 + 多忌 flag"
    print("\n单元测试 Lucian ✓: v1 四化/三方 + v2 交忌两型自洽/禄随忌走/禄转忌交禄/照冲/六线 8 断言全过")

    # 单元测试 2: 邹嘉（癸年）12 宫（自 people/zoujia.md 主星表转录）
    Z=[{"name":"命宫","stem":"甲","branch":"寅","stars":["破军"]},
       {"name":"父母","stem":"乙","branch":"卯","stars":[]},
       {"name":"福德","stem":"丙","branch":"辰","stars":["廉贞","天府"]},
       {"name":"田宅","stem":"丁","branch":"巳","stars":["太阴"]},
       {"name":"官禄","stem":"戊","branch":"午","stars":["贪狼"]},
       {"name":"仆役","stem":"己","branch":"未","stars":["天同","巨门"]},
       {"name":"迁移","stem":"庚","branch":"申","stars":["武曲","天相"]},
       {"name":"疾厄","stem":"辛","branch":"酉","stars":["太阳","天梁"]},
       {"name":"财帛","stem":"壬","branch":"戌","stars":["七杀"]},
       {"name":"子女","stem":"癸","branch":"亥","stars":["天机"]},
       {"name":"夫妻","stem":"甲","branch":"子","stars":["紫微"]},
       {"name":"兄弟","stem":"乙","branch":"丑","stars":[]}]
    print("\n" + "="*30 + " 邹嘉盘（癸年） " + "="*30)
    out_z=annotate_ziwei_v2(Z,"癸")
    print(out_z)
    assert "生年禄（破军）在 命宫宫寅" in out_z, "邹嘉: 破军禄应在命宫"
    assert "生年忌（贪狼）在 官禄宫午" in out_z, "邹嘉: 贪狼忌应在官禄"
    print("\n单元测试 邹嘉 ✓: v2 全流程跑通不抛错；生年四化定位与 people/zoujia.md 一致（破军禄在命宫、贪狼忌在官禄）")

# ===== v3 (2026-07-25): 动盘——大限/流年飞星 =====
def flow_ziwei(palaces, year_stem_birth, xian_name, liunian_stem, liunian_branch):
    """动盘：大限宫干四化 + 流年干四化 + 流年叠宫。静动分开解释（飞星派纪律）。"""
    L=[]
    # 大限四化（大限宫干飞）
    xp=[p for p in palaces if p["name"]==xian_name][0]
    ss=SIHUA[xp["stem"]]
    cells=[]
    for star,hua in zip(ss,HUA_NAMES):
        t=_find_star(palaces,star)
        if t: cells.append(f"限{hua}（{star}）入{t['name']}" + ("=限自化" if t["name"]==xian_name else ""))
    L.append(f"大限（{xian_name}宫{xp['stem']}{xp['branch']}限）四化: " + "；".join(cells))
    # 流年叠宫
    lp=[p for p in palaces if p["branch"]==liunian_branch][0]
    L.append(f"流年叠宫: 流年命宫坐本命{lp['name']}宫（{liunian_branch}）——该宫十二事被引动为当年主轴")
    # 生年忌冲之宫被流年踏上
    birth_ji=_find_star(palaces, SIHUA[year_stem_birth][3])
    if birth_ji:
        chong=ZHI[(ZHI.index(birth_ji["branch"])+6)%12]
        if liunian_branch==chong:
            L.append(f"  ⚠ 流年命宫恰坐生年忌（{SIHUA[year_stem_birth][3]}@{birth_ji['name']}）所冲之宫——冲起应年")
    # 流年四化
    ss2=SIHUA[liunian_stem]
    cells2=[]
    for star,hua in zip(ss2,HUA_NAMES):
        t=_find_star(palaces,star)
        if t:
            tag=""
            if star==SIHUA[year_stem_birth][HUA_NAMES.index(hua)] : tag="（与生年同化=重引叠加）"
            cells2.append(f"年{hua}（{star}）入{t['name']}{tag}")
    L.append(f"流年（{liunian_stem}{liunian_branch}）四化: " + "；".join(cells2))
    ji_star=ss2[3]; t=_find_star(palaces,ji_star)
    if t:
        chong=ZHI[(ZHI.index(t["branch"])+6)%12]
        op=[p for p in palaces if p["branch"]==chong][0]
        L.append(f"  流年忌冲: {t['name']}忌 冲 {op['name']}宫{chong}")
    return L
