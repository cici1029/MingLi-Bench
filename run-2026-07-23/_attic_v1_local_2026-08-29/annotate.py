# Deterministic bazi fact-layer engine. LLM judges; tables compute.
import json, itertools

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
WUXING_G = dict(zip(GAN, "木木火火土土金金水水"))
YINYANG_G = {g: i % 2 == 0 for i, g in enumerate(GAN)}  # True=阳
WUXING_Z = dict(zip(ZHI, "水土木木土火火土金金土水"))
SHENG = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
KE = {"木":"土","土":"水","水":"火","火":"金","金":"木"}

CANGGAN = {"子":["癸"],"丑":["己","癸","辛"],"寅":["甲","丙","戊"],"卯":["乙"],
"辰":["戊","乙","癸"],"巳":["丙","庚","戊"],"午":["丁","己"],"未":["己","丁","乙"],
"申":["庚","壬","戊"],"酉":["辛"],"戌":["戊","辛","丁"],"亥":["壬","甲"]}

def shishen(day, other):
    dw, ow = WUXING_G[day], WUXING_G[other]
    same_yy = YINYANG_G[day] == YINYANG_G[other]
    if dw == ow: return "比肩" if same_yy else "劫财"
    if SHENG[dw] == ow: return "食神" if same_yy else "伤官"
    if SHENG[ow] == dw: return "偏印" if same_yy else "正印"
    if KE[dw] == ow: return "偏财" if same_yy else "正财"
    if KE[ow] == dw: return "七杀" if same_yy else "正官"

# 十二长生: 阳干顺行, 阴干逆行
CHANGSHENG_START = {"甲":"亥","丙":"寅","戊":"寅","庚":"巳","壬":"申","乙":"午","丁":"酉","己":"酉","辛":"子","癸":"卯"}
STAGES = ["长生","沐浴","冠带","临官","帝旺","衰","病","死","墓","绝","胎","养"]
def changsheng(day, branch):
    start = ZHI.index(CHANGSHENG_START[day])
    step = 1 if YINYANG_G[day] else -1
    off = (ZHI.index(branch) - start) * step % 12
    return STAGES[off]

LIUCHONG = [set(p) for p in ["子午","丑未","寅申","卯酉","辰戌","巳亥"]]
LIUHE = {frozenset(p): w for p, w in [("子丑","土"),("寅亥","木"),("卯戌","火"),("辰酉","金"),("巳申","水"),("午未","火")]}
SANHE = {frozenset("申子辰"):"水",frozenset("寅午戌"):"火",frozenset("巳酉丑"):"金",frozenset("亥卯未"):"木"}
SANHUI = {frozenset("寅卯辰"):"木",frozenset("巳午未"):"火",frozenset("申酉戌"):"金",frozenset("亥子丑"):"水"}
XING_GROUPS = [set("寅巳申"), set("丑戌未")]
XING_PAIRS = [set("子卯")]
ZIXING = set("辰午酉亥")
CHUAN = [set(p) for p in ["子未","丑午","寅巳","卯辰","申亥","酉戌"]]
WUHE_G = {frozenset(p): w for p, w in [("甲己","土"),("乙庚","金"),("丙辛","水"),("丁壬","木"),("戊癸","火")]}

def xunkong(day_gz):
    gi, zi = GAN.index(day_gz[0]), ZHI.index(day_gz[1])
    xun_start_zhi = (zi - gi) % 12
    return ZHI[(xun_start_zhi + 10) % 12] + ZHI[(xun_start_zhi + 11) % 12]


# ===== v4 additions (2026-07-24): A层规则实装批次2 =====
# 纳音（六十甲子五行，袁树珊常用：纳音叠算/纳音助化）
def jiazi(idx):
    return GAN[idx % 10] + ZHI[idx % 12]
NAYIN = {}
_ny_names = ["海中金","炉中火","大林木","路旁土","剑锋金","山头火","涧下水","城头土","白蜡金","杨柳木",
"泉中水","屋上土","霹雳火","松柏木","长流水","砂石金","山下火","平地木","壁上土","金箔金",
"覆灯火","天河水","大驿土","钗钏金","桑柘木","大溪水","沙中土","天上火","石榴木","大海水"]
for _i in range(30):
    NAYIN[jiazi(_i*2)] = _ny_names[_i]
    NAYIN[jiazi(_i*2+1)] = _ny_names[_i]
NY_WX = {n: n[-1].replace("金","金").replace("木","木").replace("水","水").replace("火","火").replace("土","土") for n in _ny_names}

def nayin_line(sizhu):
    parts=[f"{gz}={NAYIN[gz]}" for gz in sizhu]
    from collections import Counter
    wx=Counter(NAYIN[gz][-1] for gz in sizhu)
    dom=[f"{w}x{c}" for w,c in wx.most_common() if c>=2]
    return "纳音: " + " ".join(parts) + ("；纳音党势: " + " ".join(dom) if dom else "")

# 天干五合化气成败（A层：合而能化需化神秉令/得势，否则以合绊论）
def wuhe_verdict(sizhu):
    stems=[gz[0] for gz in sizhu]; mz=sizhu[1][1]
    ml_wx = WUXING_Z[mz]
    out=[]
    import itertools as _it
    for (i,a),(j,b) in _it.combinations(list(enumerate(stems)),2):
        fs=frozenset({a,b})
        if fs in WUHE_G and a!=b:
            hua=WUHE_G[fs]
            adjacent = abs(i-j)==1
            deling = (ml_wx==hua)
            if deling and adjacent: verdict=f"化{hua}候选（化神秉令且紧贴，真化再查争合与根）"
            elif deling: verdict=f"化{hua}倾向（化神秉令但隔位，化力减）"
            else: verdict=f"合绊论（化神{hua}不秉令，两字互绊减力）"
            out.append(f"{'年月日时'[i]}{a}+{'年月日时'[j]}{b}: {verdict}")
    return ("天干五合化气判: " + "；".join(out)) if out else ""

def annotate(sizhu, tiaohou=None):
    yz, mz, dz, hz = sizhu
    day = dz[0]
    pillars = list(zip("年月日时", sizhu))
    L = []
    # 1 十神 + 藏干 + 长生
    rows = []
    for pos, gz in pillars:
        g, z = gz[0], gz[1]
        ss = "日主" if pos == "日" else shishen(day, g)
        cg = " ".join(f"{c}({shishen(day,c)})" for c in CANGGAN[z])
        rows.append(f"  {pos}柱 {gz}: 天干{g}={ss} | 支藏 {cg} | 日主{day}在{z}={changsheng(day,z)}")
    L.append("十神与十二长生表:")
    L += rows
    # 2 得令与通根
    stage_m = changsheng(day, mz[1])
    ml = CANGGAN[mz[1]][0]
    mlss = shishen(day, ml)
    deling = mlss in ("比肩","劫财","正印","偏印")
    L.append(f"月令: 本气{ml}({mlss}) → 日主{'得令' if deling else '失令'}（长生态={stage_m}）")
    branches = [gz[1] for gz in sizhu]
    tg_report = []
    for pos, gz in pillars:
        g = gz[0]
        roots = []
        for i, b in enumerate(branches):
            cg = CANGGAN[b]
            for k, c in enumerate(cg):
                if WUXING_G[c] == WUXING_G[g]:
                    tier = ["本气","中气","余气"][k]
                    tag = "" if c == g else f"(同气{c})"
                    roots.append(f"{'年月日时'[i]}支{b}{tier}{tag}")
                    break
        tg_report.append(f"  {g}({'日主' if pos=='日' else shishen(day,g)}): {'通根 ' + '、'.join(roots) if roots else '无根'}")
    L.append("天干通根盘点:")
    L += tg_report
    # 3 支间关系
    rel = []
    idx = list(enumerate(branches))
    for (i, a), (j, b) in itertools.combinations(idx, 2):
        pa, pb = "年月日时"[i], "年月日时"[j]
        pair = {a, b}
        if a == b and a in ZIXING: rel.append(f"{pa}{a}-{pb}{b} 自刑")
        if pair in LIUCHONG: rel.append(f"{pa}{a}-{pb}{b} 六冲" + ("（冲提纲!）" if 1 in (i, j) else ""))
        if frozenset(pair) in LIUHE: rel.append(f"{pa}{a}-{pb}{b} 六合化{LIUHE[frozenset(pair)]}")
        if pair in CHUAN: rel.append(f"{pa}{a}-{pb}{b} 相穿(害)")
        if pair in XING_PAIRS: rel.append(f"{pa}{a}-{pb}{b} 相刑")
    bs = set(branches)
    for grp, w in SANHE.items():
        inter = grp & bs
        if len(inter) == 3: rel.append(f"三合{w}局全({''.join(sorted(grp, key=ZHI.index))})——强弱以局论优先检查!")
        elif len(inter) == 2 and sorted(grp - inter)[0] not in bs:
            g2 = sorted(inter, key=ZHI.index)
            mid = [z for z in grp if changsheng({"水":"壬","火":"丙","金":"庚","木":"甲"}[w], z) == "帝旺"][0]
            if mid in inter: rel.append(f"半合{w}局({g2[0]}{g2[1]})")
    for grp, w in SANHUI.items():
        if len(grp & bs) == 3: rel.append(f"三会{w}方全——强弱以方论优先检查!")
    for grp in XING_GROUPS:
        inter = grp & bs
        if len(inter) == 3: rel.append(f"三刑全({''.join(sorted(grp, key=ZHI.index))})")
        elif len(inter) == 2: rel.append(f"三刑二字({''.join(sorted(inter, key=ZHI.index))}，逢{''.join(grp-inter)}岁运补全触发)")
    stems = [gz[0] for gz in sizhu]
    for (i, a), (j, b) in itertools.combinations(list(enumerate(stems)), 2):
        if frozenset({a, b}) in WUHE_G and a != b:
            rel.append(f"天干{a}{b}合(化{WUHE_G[frozenset({a,b})]}，成化需月令支持)")
    L.append("干支关系（合冲刑穿会，判强弱与应期的机械事实）:")
    L += ["  " + r for r in rel] if rel else ["  （无显著关系）"]
    # 3b 纳音 + 五合化气判 (v4) + 计数/神煞 (v5)
    L.append(nayin_line(sizhu))
    L.append(counts_line(sizhu))
    sl=shensha_line(sizhu, day)
    if sl: L.append(sl)
    for ln in v6_lines(sizhu, day): L.append(ln)
    for ln in a16_huaqi(sizhu): L.append(ln)
    wv=wuhe_verdict(sizhu)
    if wv: L.append(wv)
    # 4 空亡（含 A层规则: 空亡逢冲则实）
    xk=xunkong(dz)
    xk_notes=[]
    for i,b in enumerate(branches):
        if b in xk:
            hit_chong=any({b,b2} in LIUCHONG for j,b2 in enumerate(branches) if j!=i)
            xk_notes.append(f"{'年月日时'[i]}支{b}落空亡" + ("（逢冲则实，空解）" if hit_chong else "（真空，力量折半再折；A22 格局涉此支者降级为驳杂不废）"))
    L.append(f"旬空（以日柱{dz}起）: {xk}" + ("；" + "；".join(xk_notes) if xk_notes else ""))
    # 4b 盖头截脚（A层规则: 干支同柱克战）
    gj=[]
    for i,(pos,gz) in enumerate(pillars):
        g,z=gz[0],gz[1]; zg=CANGGAN[z][0]
        if KE[WUXING_G[g]]==WUXING_G[zg]: gj.append(f"{pos}柱{gz} 盖头（干克支，支用力损）")
        elif KE[WUXING_G[zg]]==WUXING_G[g]: gj.append(f"{pos}柱{gz} 截脚（支克干，干虚浮）")
    if gj: L.append("盖头截脚: " + "；".join(gj))
    # 5 墓库提示 (Chao 衰养例的一般化: 长生态弱位提示)
    mub = [f"{'年月日时'[i]}支{b}({changsheng(day,b)})" for i, b in enumerate(branches) if changsheng(day, b) in ("衰","病","死","墓","绝","养","胎")]
    if mub: L.append("日主弱态支位（衰病死墓绝胎养，若坐用神/忌神其力量按此折减）: " + "、".join(mub))
    # 6 调候
    if tiaohou:
        t = tiaohou.get(day, {}).get(mz[1])
        if t:
            L.append(f"调候用神（穷通宝鉴查表）: 主={''.join(t['primary'])} 次={''.join(t.get('secondary',[]))}" + (f" | {t['note']}" if t.get('note') else ""))
    return "\n".join(L)

# （self-test 块移至文件末尾——原在此处时，v4-v7 追加于其后的 counts_line 等
#  函数在脚本模式执行到自测时尚未定义，python3 annotate.py 会 NameError。）

# ===== 力量定级引擎 v2 (2026-07-24) =====
# Chao 提出的 codify 层：衰/养等十二长生态对根力的折减 + 冲合修正，全部查表计算。
# 输出的是"分级事实"不是结论；强弱定调仍由 LLM 综合（防只看一两个字）。
STAGE_MULT = {"帝旺":1.3,"临官":1.2,"长生":1.0,"冠带":1.0,"沐浴":0.8,
              "衰":0.6,"养":0.6,"胎":0.45,"病":0.5,"死":0.4,"墓":0.55,"绝":0.3}
POS_W = [1.0, 1.5, 1.2, 1.0]  # 年月日时：月令根x1.5，日支x1.2
TIER_PTS = [30, 15, 8]        # 本气/中气/余气

def strength_table(sizhu):
    yz, mz, dz, hz = sizhu
    day = dz[0]
    branches = [gz[1] for gz in sizhu]
    stems = [gz[0] for gz in sizhu]
    # 支间状态: 冲/合绊/会局
    chong=set(); ban=set(); hui={}
    import itertools as _it
    for (i,a),(j,b) in _it.combinations(list(enumerate(branches)),2):
        if {a,b} in LIUCHONG: chong.add(i); chong.add(j)
        if frozenset({a,b}) in LIUHE: ban.add(i); ban.add(j)
    bs=set(branches)
    for grp,w in list(SANHE.items())+list(SANHUI.items()):
        if len(grp & bs)>=3:
            for i,b in enumerate(branches):
                if b in grp: hui[i]=w
    rows=[]
    for si,(pos,g) in enumerate(zip("年月日时",stems)):
        total=10.0; detail=[f"透干10"]
        for bi,b in enumerate(branches):
            cg=CANGGAN[b]
            for k,c in enumerate(cg):
                if WUXING_G[c]==WUXING_G[g]:
                    stage=changsheng(g,b)
                    pts=TIER_PTS[k]*STAGE_MULT[stage]*POS_W[bi]
                    mods=[]
                    if bi in chong: pts*=0.5; mods.append("被冲x0.5")
                    if bi in ban: pts*=0.7; mods.append("合绊x0.7")
                    if bi in hui:
                        if hui[bi]==WUXING_G[g]: pts*=1.3; mods.append("会局同气x1.3")
                        else: pts*=0.7; mods.append("会局异气x0.7")
                    total+=pts
                    detail.append(f"{'年月日时'[bi]}支{b}{['本','中','余'][k]}气·{stage}({STAGE_MULT[stage]}){'·'+ '·'.join(mods) if mods else ''}={pts:.0f}")
                    break
        role="日主" if pos=="日" and g==day else shishen(day,g)
        rows.append((pos,g,role,total,detail))
    # 党势汇总（五行为单位，含未透藏干主气）
    party={}
    for pos,g,role,total,_ in rows:
        party[WUXING_G[g]]=party.get(WUXING_G[g],0)+total
    lines=["力量定级表（机械计算，供综合判断——强弱定调仍须整体裁量）:"]
    for pos,g,role,total,detail in rows:
        lines.append(f"  {pos}干{g}({role}): {total:.0f}分 [{'; '.join(detail)}]")
    dm=[r for r in rows if r[0]=="日"][0][3]
    helpers=sum(t for _,g,r,t,_ in rows if WUXING_G[g]==WUXING_G[day] or SHENG[WUXING_G[g]]==WUXING_G[day])
    drainers=sum(t for _,g,r,t,_ in rows if WUXING_G[g]!=WUXING_G[day] and SHENG[WUXING_G[g]]!=WUXING_G[day])
    # 未透主气党势（藏干司令也是力量，防"当令杀不透=隐形"误导）
    hidden={}
    for bi,b in enumerate(branches):
        c=CANGGAN[b][0]
        if c in stems: continue
        stage=changsheng(c,b)
        pts=TIER_PTS[0]*STAGE_MULT[stage]*POS_W[bi]
        if bi in chong: pts*=0.5
        if bi in ban: pts*=0.7
        if bi in hui: pts*=(1.3 if hui[bi]==WUXING_G[c] else 0.7)
        hidden[c]=hidden.get(c,0)+pts
    if hidden:
        lines.append("  未透主气党势: " + " ".join(f"{c}({shishen(day,c)}){v:.0f}" for c,v in sorted(hidden.items(), key=lambda x:-x[1])))
    hb=sum(v for c,v in hidden.items() if WUXING_G[c]==WUXING_G[day] or SHENG[WUXING_G[c]]==WUXING_G[day])
    hd=sum(v for c,v in hidden.items() if WUXING_G[c]!=WUXING_G[day] and SHENG[WUXING_G[c]]!=WUXING_G[day])
    lines.append(f"  合计: 帮扶党 {helpers+hb:.0f}（透{helpers:.0f}+藏{hb:.0f}） vs 克泄耗党 {drainers+hd:.0f}（透{drainers:.0f}+藏{hd:.0f}）")
    return "\n".join(lines)

# ===== v5 additions (2026-07-24): A层规则实装批次3 =====
TIANYI = {"甲":"丑未","戊":"丑未","庚":"丑未","乙":"子申","己":"子申","丙":"亥酉","丁":"亥酉","壬":"卯巳","癸":"卯巳","辛":"午寅"}
TIANSHE = {"寅卯辰":"戊寅","巳午未":"甲午","申酉戌":"戊申","亥子丑":"甲子"}

def taiyuan(sizhu):
    # 胎元 = 月干进一、月支进三
    mg, mz = sizhu[1][0], sizhu[1][1]
    return GAN[(GAN.index(mg)+1)%10] + ZHI[(ZHI.index(mz)+3)%12]

def counts_line(sizhu):
    # A01 藏干逐位计数（透干+全部藏干逐位入账）+ A03 偏枯门槛 + A04 反克方向 + A06 失令仍衰
    from collections import Counter
    cnt=Counter()
    for gz in sizhu:
        cnt[WUXING_G[gz[0]]]+=1
        for c in CANGGAN[gz[1]]:
            cnt[WUXING_G[c]]+=1
    names={1:"",2:"炎",3:"盛",4:"极",5:"极",6:"极"}
    parts=[f"{w}x{cnt.get(w,0)}" for w in "木火土金水"]
    L=["藏干逐位计数（A01，透+藏全口径）: " + " ".join(parts)]
    ml=WUXING_Z[sizhu[1][1]]
    for w in "木火土金水":
        n=cnt.get(w,0)
        if n>=4:
            foes=[v for v in "木火土金水" if KE[v]==w]
            foe_n=sum(cnt.get(v,0) for v in foes)
            if foe_n<=1: L.append(f"  偏枯警（A03）: {w}计{n}而克之者仅{foe_n}点，偏枯之造判据触发")
    for a in "木火土金水":
        b=KE[a]
        if cnt.get(a,0)>0 and cnt.get(b,0)>=3*max(cnt.get(a,0),1) and cnt.get(a,0)<=1:
            L.append(f"  反克警（A04）: {a}仅{cnt.get(a,0)}点克{b}{cnt.get(b,0)}点，寡不敌众反为{b}所伤（{b}强{a}折）")
    for w in "木火土金水":
        if cnt.get(w,0)>=4 and ml!=w and SHENG.get(ml)!=w:
            L.append(f"  失令注（A06）: {w}数多（{cnt[w]}）而不得月令，数多犹藏形，作衰减看")
    return "\n".join(L)

def shensha_line(sizhu, day):
    L=[]
    branches=[gz[1] for gz in sizhu]
    # 天乙贵人矩阵（A26/A27/A28）
    hits=[]
    for pos,gz in zip("年月日时",sizhu):
        g=gz[0]; ty=TIANYI[g]
        inchart=[f"{'年月日时'[i]}支{b}" for i,b in enumerate(branches) if b in ty]
        if inchart: hits.append(f"{pos}干{g}贵人({ty})在盘: {','.join(inchart)}")
    if hits: L.append("天乙贵人矩阵: " + "；".join(hits))
    mutual=all(any(b in TIANYI[gz[0]] for b in branches) for gz in sizhu)
    if mutual: L.append("  四柱互贵判定（A28）: 各干贵人皆在盘中，前引后从左右逢源")
    # 天赦（A25）
    for season,day_gz in TIANSHE.items():
        if sizhu[1][1] in season and sizhu[2]==day_gz:
            L.append(f"天赦日（A25）: {season}月逢{day_gz}日，处事无忧逢凶化吉")
    # 胎元 + 五行俱足（A30）
    ty_gz=taiyuan(sizhu)
    wx=set(NAYIN[gz][-1] for gz in sizhu) | {NAYIN[ty_gz][-1]}
    L.append(f"胎元: {ty_gz}（纳音{NAYIN[ty_gz]}）" + ("；五行俱足格判据（A30）: 四柱+胎元纳音凑齐五行 ✓" if len(wx)==5 else ""))
    # 四大空亡（A23）: 日柱旬内纳音五行不见年柱纳音之行
    di=None
    for i in range(60):
        if jiazi(i)==sizhu[2]: di=i; break
    xun=[jiazi((di//10)*10+k) for k in range(10)]
    xun_wx=set(NAYIN[gz][-1] for gz in xun)
    ny_year=NAYIN[sizhu[0]][-1]
    if ny_year not in xun_wx:
        L.append(f"四大空亡（A23）: 日旬纳音不见年命{ny_year}，主蹇滞，救应须专查")
    return "\n".join(L)

# ===== v6 additions (2026-07-24): A层批次4 =====
YANGREN = {"甲":"卯","丙":"午","戊":"午","庚":"酉","壬":"子"}  # 阳干羊刃
YINREN  = {"乙":"寅","丁":"巳","己":"巳","辛":"申","癸":"亥"}  # 阴刃(一说)
JINSHEN = {"甲子","己卯","甲午","己酉"}  # 四进神日
YUEDE  = {"寅":"丙","午":"丙","戌":"丙","申":"壬","子":"壬","辰":"壬","亥":"甲","卯":"甲","未":"甲","巳":"庚","酉":"庚","丑":"庚"}

def v6_lines(sizhu, day):
    L=[]
    branches=[gz[1] for gz in sizhu]; stems=[gz[0] for gz in sizhu]; mz=sizhu[1][1]
    # A09/A10 刃
    ren = YANGREN.get(day)
    if ren and ren in branches:
        deling = (mz == ren)
        L.append(f"A09 阳刃在盘（{ren}）" + ("且当月令=得生气，加权计力" if deling else "，不当令按常权"))
    yren = YINREN.get(day)
    if yren and yren in branches:
        L.append(f"A10 阴刃在盘（{yren}）：只稍助权威，刃之力弱于用神之力（上限注）")
    # A29 进神+月德
    if sizhu[2] in JINSHEN:
        yd = YUEDE[mz]
        has_yd = yd in stems
        L.append(f"A29 日柱{sizhu[2]}为四进神日" + (f"，且{yd}月德透干：格局力量上修" if has_yd else f"（月德{yd}不透，加成减半）"))
    # A02 生克通道计数与配平
    from collections import Counter
    cnt=Counter()
    for gz in sizhu:
        cnt[WUXING_G[gz[0]]]+=1
        for c in CANGGAN[gz[1]]: cnt[WUXING_G[c]]+=1
    pairs=[]
    for a in "木火土金水":
        b=KE[a]
        na,nb=cnt.get(a,0),cnt.get(b,0)
        if na and nb:
            tag = "配平（交，制化成立判据）" if na==nb else ("克方占优" if na>nb else "被克方众")
            pairs.append(f"{a}{na}克{b}{nb}:{tag}")
    if pairs: L.append("A02 生克通道计数: " + "；".join(pairs))
    return L

def a16_huaqi(sizhu):
    # A16 化气禄旺换算：五合化候选存在时，按化神阳干查其在各支的长生/禄/旺
    import itertools as _it
    stems=[gz[0] for gz in sizhu]; branches=[gz[1] for gz in sizhu]; mlwx=WUXING_Z[sizhu[1][1]]
    YANG_OF={"木":"甲","火":"丙","土":"戊","金":"庚","水":"壬"}
    out=[]
    for (i,a),(j,b) in _it.combinations(list(enumerate(stems)),2):
        fs=frozenset({a,b})
        if fs in WUHE_G and a!=b and WUHE_G[fs]==mlwx:
            hy=YANG_OF[mlwx]
            states=[f"{'年月日时'[k]}支{z}={changsheng(hy,z)}" for k,z in enumerate(branches)]
            out.append(f"A16 化气禄旺换算（化{mlwx}以{hy}取禄旺）: " + " ".join(states) + "；化成禄旺者生、禄绝者死")
    return list(dict.fromkeys(out))

# ===== v7 additions (2026-07-24): A层收口批次（参数化接缝规则）=====
WUHUDUN = {"甲":"丙","己":"丙","乙":"戊","庚":"戊","丙":"庚","辛":"庚","丁":"壬","壬":"壬","戊":"甲","癸":"甲"}  # 年干→寅月起干

def mingong_ganzhi(year_gan, mingong_zhi):
    # A21 完整化: 五虎遁得命宫干（从寅起，顺数至命宫支）
    start = WUHUDUN[year_gan]
    offset = (ZHI.index(mingong_zhi) - ZHI.index("寅")) % 12
    g = GAN[(GAN.index(start) + offset) % 10]
    return g + mingong_zhi

def a12_yongshen_houbo(sizhu, yongshen_elems):
    # A12 用神数量定量级（参数: 用神五行列表）: 数对，一对薄、三对厚
    from collections import Counter
    cnt=Counter()
    for gz in sizhu:
        cnt[WUXING_G[gz[0]]]+=1
        for c in CANGGAN[gz[1]]: cnt[WUXING_G[c]]+=1
    pairs=min(cnt.get(e,0) for e in yongshen_elems) if yongshen_elems else 0
    grade="厚" if pairs>=3 else ("中" if pairs==2 else "薄")
    return f"A12 用神{'/'.join(yongshen_elems)}调剂力: 约{pairs}对（{grade}）——量级随厚薄分层"

def a18_nayin_backup(sizhu, needed_elem):
    # A18 纳音替补用神（参数: 正五行所缺之药）
    for pos,gz in [("日",sizhu[2]),("月",sizhu[1])]:
        if NAYIN[gz][-1]==needed_elem:
            return f"A18 纳音替补: 正五行乏{needed_elem}，{pos}柱纳音{NAYIN[gz]}可为正式用神（无中生有救弊）"
    return f"A18 纳音替补: 日/月柱纳音均无{needed_elem}，此路不通"

def a19_dayun_nayin(dayun_gz, key_elem):
    # A19 运岁纳音入结算（参数: 化神或用神五行）
    ny=NAYIN[dayun_gz]; wx=ny[-1]
    rel = "生助" if SHENG.get(wx)==key_elem or wx==key_elem else ("克伐" if KE.get(wx)==key_elem else "无涉")
    return f"A19 {dayun_gz}运纳音{ny}对{key_elem}: {rel}" + ("（运本气非喜时以此定吉凶）" if rel!="无涉" else "")

def a02_peace(sizhu, ji_elems, yu_elems):
    # A02 完整版（参数: 济方/御方五行）: 双通道同时够数
    from collections import Counter
    cnt=Counter()
    for gz in sizhu:
        cnt[WUXING_G[gz[0]]]+=1
        for c in CANGGAN[gz[1]]: cnt[WUXING_G[c]]+=1
    j=sum(cnt.get(e,0) for e in ji_elems); y=sum(cnt.get(e,0) for e in yu_elems)
    ok = j>0 and y>0 and abs(j-y)<=1
    return f"A02 济方{''.join(ji_elems)}={j} vs 御方{''.join(yu_elems)}={y}: " + ("配平成立（交）" if ok else "未配平")

def a31_mingong_fill(mingong_zhi, kongwang_str, dayun_zhi):
    # A31 大运填实命宫空亡 → 发端应期
    if mingong_zhi in kongwang_str and dayun_zhi==mingong_zhi:
        return f"A31 应期: 大运{dayun_zhi}填实命宫空亡之支，发端之运（填实而登第）"
    return ""

if __name__ == "__main__":
    import os
    th = json.load(open("tiaohou.json")) if os.path.exists("tiaohou.json") else None
    # self-test: case_1 甲寅 戊辰 己亥 壬申
    demo = annotate(["甲寅","戊辰","己亥","壬申"], th)
    print(demo)
    # regression asserts
    assert shishen("己","甲")=="正官" and shishen("己","壬")=="正财" and shishen("己","戊")=="劫财"
    assert changsheng("甲","亥")=="长生" and changsheng("甲","午")=="死" and changsheng("乙","午")=="长生"
    assert changsheng("戊","辰")=="冠带"
    assert xunkong("己亥")=="辰巳"
    print("\nREGRESSION OK")
