import streamlit as st
import pandas as pd
import json
import os
import math
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import ephem
import google.generativeai as genai
import streamlit.components.v1 as components

# ==============================================================================
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS (A4 완벽 핏, 명조체 통일)
# ==============================================================================
st.set_page_config(page_title="초연 시공명리 Ver 12.5", layout="wide")

st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");
    .stApp, p, h1, h2, h3, h4, h5, h6, div, span, td { font-family: 'Noto Serif KR', serif !important; }
    
    body { background-color: #FFF8E1; }
    
    .report-page { max-width: 210mm; margin: 10px auto; background: white; padding: 15mm 10mm; box-shadow: 0 0 15px rgba(0,0,0,0.1); border-radius: 20px; box-sizing: border-box; }
    .vip-inset-frame { border: 2px solid #1A237E; border-radius: 15px; padding: 20px; background: transparent; }
    
    .result-table { width: 100%; border-collapse: collapse; border: 3px solid #3E2723; margin-bottom: 15px; table-layout: fixed; }
    .result-table td { border: 1px solid #444; padding: 1px; text-align: center; vertical-align: middle; font-weight: 900; font-size: 13px; line-height: 1.2; word-wrap: break-word; }
    
    .no-border-row td { border-top: none !important; border-bottom: none !important; }
    .no-border-row:last-of-type td { border-bottom: 1px solid #444 !important; }
    
    .header-cell-main { background-color: #E8EAF6 !important; color: #1A237E !important; font-weight: 900 !important; font-size: 12px !important; height: 22px !important; }
    .top-header-cell { background-color: #1A237E !important; color: white !important; font-size: 13px !important; height: 26px !important; padding: 0 !important; }
    
    .color-목 { background-color: #2E7D32 !important; color: white !important; }
    .color-화 { background-color: #C62828 !important; color: white !important; }
    .color-토 { background-color: #F9A825 !important; color: black !important; }
    .color-금 { background-color: #9E9E9E !important; color: white !important; }
    .color-수 { background-color: #212121 !important; color: white !important; }
    
    .content-box-loose { line-height: 1.8; font-size: 15px; text-align: justify; text-indent: 15px; margin-bottom: 12px; }
    
    /* 대운/세운/월운 흐름표 (좌->우 LTR 정렬) */
    .flow-flex { display: flex; flex-direction: row; width: 100%; border: 2px solid #3E2723; background: white; margin-bottom: 5px; }
    .flow-col { flex: 1; border-right: 1px solid #ccc; text-align: center; padding-bottom: 3px; }
    .flow-col:last-child { border-right: none; }
    .dw-age-head { background: #3E2723; color: white; font-weight: 900; padding: 3px; font-size: 12px; }
    
    div.stButton > button:first-child { background-color: #D50000; color: white; border: none; font-weight: 900; } 
    div[data-testid="stSidebar"] div.stButton > button { height: 45px; }
    .navy-btn button { background-color: #1A237E !important; color: white !important; border: none !important; font-weight: 900 !important; }
    
    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        .stApp { background-color: white !important; }
        .report-page { max-width: 100%; width: 100%; box-shadow: none; margin: 0; padding: 0; page-break-after: always; border: none; min-height: auto; }
        .vip-inset-frame { border: 2px solid #000; border-radius: 20px; padding: 15px; }
        .no-bg-print { background-color: transparent !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. 자동 커서 이동(JS) 및 시스템 변수 세팅
# ==============================================================================
if 's_y' not in st.session_state: st.session_state.s_y = 2000
if 's_m' not in st.session_state: st.session_state.s_m = 1
if 's_d' not in st.session_state: st.session_state.s_d = 1
if 's_t' not in st.session_state: st.session_state.s_t = "시간 모름"

components.html("""
<script>
    const doc = window.parent.document;
    doc.addEventListener('keyup', function(e) {
        if (e.target.tagName !== 'INPUT' || e.target.type !== 'text') return;
        let label = e.target.getAttribute('aria-label') || "";
        if (label.includes('년주') || label.includes('월주') || label.includes('일주')) {
            if (e.key === ' ' || e.target.value.includes('년') || e.target.value.includes('월') || e.target.value.includes('일') || e.target.value.includes('시')) {
                let inputs = Array.from(doc.querySelectorAll('input[type="text"]'));
                let idx = inputs.indexOf(e.target);
                if (idx > -1 && idx < inputs.length - 1) inputs[idx + 1].focus();
            }
        }
    });
</script>
""", height=0, width=0)

# ==============================================================================
# 2. AI 엔진 및 명리 연산 엔진
# ==============================================================================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-pro') 
except: pass

GAN, JI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"

def get_color(c):
    if c in "甲乙寅卯": return "목"
    if c in "丙丁巳午": return "화"
    if c in "戊己辰戌丑未": return "토"
    if c in "庚辛申酉": return "금"
    if c in "壬癸亥子": return "수"
    return "토"

def get_ss(dg, tc):
    if tc in ["?", " ", "-"]: return "-"
    rels = {
        '甲':{'甲':'비견','乙':'겁재','丙':'식신','丁':'상관','戊':'편재','己':'정재','庚':'편관','辛':'정관','壬':'편인','癸':'정인','寅':'비견','卯':'겁재','巳':'식신','午':'상관','辰':'편재','戌':'편재','丑':'정재','未':'정재','申':'편관','酉':'정관','亥':'편인','子':'정인'},
        '乙':{'乙':'비견','甲':'겁재','丁':'식신','丙':'상관','己':'편재','戊':'정재','辛':'편관','庚':'정관','癸':'편인','壬':'정인','卯':'비견','寅':'겁재','午':'식신','巳':'상관','丑':'편재','未':'편재','辰':'정재','戌':'정재','酉':'편관','申':'정관','子':'편인','亥':'정인'},
        '丙':{'丙':'비견','丁':'겁재','戊':'식신','己':'상관','庚':'편재','辛':'정재','壬':'편관','癸':'정관','甲':'편인','乙':'정인','巳':'비견','午':'겁재','辰':'식신','戌':'식신','未':'상관','丑':'상관','申':'편재','酉':'정재','亥':'편관','子':'정관','寅':'편인','卯':'정인'},
        '丁':{'丁':'비견','丙':'겁재','己':'식신','戊':'상관','辛':'편재','庚':'정재','癸':'편관','壬':'정관','乙':'편인','甲':'정인','午':'비견','巳':'겁재','未':'식신','丑':'식신','辰':'상관','戌':'상관','酉':'편재','申':'정재','子':'편관','亥':'정관','卯':'편인','寅':'정인'},
        '戊':{'戊':'비견','己':'겁재','庚':'식신','辛':'상관','壬':'편재','癸':'정재','甲':'편관','乙':'정관','丙':'편인','丁':'정인','辰':'비견','戌':'비견','丑':'겁재','未':'겁재','申':'식신','酉':'상관','亥':'편재','子':'정재','寅':'편관','卯':'정관','巳':'편인','午':'정인'},
        '己':{'己':'비견','戊':'겁재','辛':'식신','庚':'상관','癸':'편재','壬':'정재','乙':'편관','甲':'정관','丁':'편인','丙':'정인','丑':'비견','未':'비견','辰':'겁재','戌':'겁재','酉':'식신','申':'상관','子':'편재','亥':'정재','卯':'편관','寅':'정관','午':'편인','巳':'정인'},
        '庚':{'庚':'비견','辛':'겁재','壬':'식신','癸':'상관','甲':'편재','乙':'정재','丙':'편관','丁':'정관','戊':'편인','己':'정인','申':'비견','酉':'겁재','亥':'식신','子':'상관','寅':'편재','卯':'정재','巳':'편관','午':'정관','辰':'편인','戌':'편인','丑':'정인','未':'정인'},
        '辛':{'辛':'비견','庚':'겁재','癸':'식신','壬':'상관','乙':'편재','甲':'정재','丁':'편관','丙':'정관','己':'편인','戊':'정인','酉':'비견','申':'겁재','子':'식신','亥':'상관','卯':'편재','寅':'정재','午':'편관','巳':'정관','未':'편인','丑':'편인','辰':'정인','戌':'정인'},
        '壬':{'壬':'비견','癸':'겁재','甲':'식신','乙':'상관','丙':'편재','丁':'정재','戊':'편관','己':'정관','庚':'편인','辛':'정인','亥':'비견','子':'겁재','寅':'식신','卯':'상관','巳':'편재','午':'정재','辰':'편관','戌':'편관','丑':'정관','未':'정관','申':'편인','酉':'정인'},
        '癸':{'癸':'비견','壬':'겁재','乙':'식신','甲':'상관','丁':'편재','丙':'정재','己':'편관','戊':'정관','辛':'편인','庚':'정인','子':'비견','亥':'겁재','卯':'식신','寅':'상관','午':'편재','巳':'정재','未':'편관','丑':'편관','戌':'정관','辰':'정관','酉':'편인','申':'정인'}
    }
    return rels.get(dg, {}).get(tc, "-")

def get_unsung(dg, ji):
    if ji in ["?", " ", "-"]: return "-"
    table = {'甲':"亥子丑寅卯辰巳午未申酉戌",'丙':"寅卯辰巳午未申酉戌亥子丑",'戊':"寅卯辰巳午未申酉戌亥子丑",'庚':"巳午未申酉戌亥子丑寅卯辰",'壬':"申酉戌亥子丑寅卯辰巳午未",'乙':"午巳辰卯寅丑子亥戌酉申未",'丁':"酉申未午巳辰卯寅丑子亥戌",'己':"酉申未午巳辰卯寅丑子亥戌",'辛':"子亥戌酉申未午巳辰卯寅丑",'癸':"卯寅丑子亥戌酉申未午巳辰"}
    idx = table.get(dg, "").find(ji)
    return ["장생","목욕","관대","건록","제왕","쇠","병","사","묘","절","태","양"][idx] if idx != -1 else "-"

def get_12_shinsal(year_ji, target_ji):
    if target_ji in ["?", " ", "-"] or not year_ji or year_ji == "?": return "-"
    s_map = {"申":"巳","子":"巳","辰":"巳", "寅":"亥","午":"亥","戌":"亥", "巳":"寅","酉":"寅","丑":"寅", "亥":"申","卯":"申","未":"申"}
    s_idx = (list(JI).index(target_ji) - list(JI).index(s_map.get(year_ji, "巳")) + 12) % 12
    return ["겁살","재살","천살","지살","년살","월살","망신살","장성살","반안살","역마살","육해살","화개살"][s_idx]

def get_gan_rel_all(idx, gans):
    me = gans[idx]; res = []
    if me in ["-", "?", " "]: return "-"
    for i, other in enumerate(gans):
        if i == idx or other in ["-", "?", " "]: continue
        s = {me, other}
        if s in [{'甲','己'}, {'乙','庚'}, {'丙','辛'}, {'丁','壬'}, {'戊','癸'}]: res.append("합")
        if s in [{'甲','庚'}, {'乙','辛'}, {'丙','壬'}, {'丁','癸'}, {'戊','甲'}, {'己','乙'}]: res.append("충")
    return "".join(list(set(res))) if res else "-"

def get_ji_rel_set(me, target):
    if not me or not target or me == "?" or target == "?" or me == target: return "자형" if me == target and me in "辰午酉亥" else "-"
    s, r = {me, target}, []
    if s in [{'寅','卯'}, {'卯','辰'}, {'寅','辰'}, {'巳','午'}, {'午','未'}, {'巳','未'}, {'申','酉'}, {'酉','戌'}, {'申','戌'}, {'亥','子'}, {'子','丑'}, {'亥','丑'}]: r.append("방합")
    if s in [{'申','子'}, {'子','辰'}, {'申','辰'}, {'寅','午'}, {'午','戌'}, {'寅','戌'}, {'亥','卯'}, {'卯','未'}, {'亥','未'}, {'巳','酉'}, {'酉','丑'}, {'巳','丑'}]: r.append("반합")
    if s in [{'子','丑'}, {'寅','亥'}, {'卯','戌'}, {'辰','酉'}, {'巳','申'}, {'午','未'}]: r.append("육합")
    if s in [{'午','亥'}, {'子','戌'}, {'丑','寅'}, {'寅','未'}, {'卯','申'}]: r.append("암합")
    if s in [{'子','午'}, {'丑','未'}, {'寅','申'}, {'卯','酉'}, {'辰','戌'}, {'巳','亥'}]: r.append("충")
    if s in [{'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}, {'子','卯'}]: r.append("형")
    if s in [{'子','未'}, {'丑','午'}, {'寅','巳'}, {'卯','辰'}, {'申','亥'}, {'酉','戌'}]: r.append("해")
    if s in [{'子','酉'}, {'丑','辰'}, {'寅','亥'}, {'卯','午'}, {'巳','申'}, {'未','戌'}]: r.append("파")
    if s in [{'丑','午'}, {'卯','申'}, {'辰','亥'}, {'巳','戌'}]: r.extend(["원진", "귀문"])
    elif s in [{'子','酉'}, {'寅','未'}]: r.append("귀문")
    elif s in [{'寅','酉'}, {'子','未'}]: r.append("원진")
    if s == {'戌','亥'}: r.append("천라")
    if s == {'辰','巳'}: r.append("지망")
    return ", ".join(list(dict.fromkeys(r))) if r else "-"

def get_general_shinsal_filtered(idx, gans, jjis):
    dc, mc, yc = gans[1], gans[2], gans[3]
    dj, mj, yj = jjis[1], jjis[2], jjis[3]
    cur_g, cur_j = gans[idx], jjis[idx]
    
    if cur_g in ["?", "-", " "] or cur_j in ["?", "-", " "]: return []
    gj = cur_g + cur_j
    noble, ausp, evil = [], [], []
    
    if cur_j in {'甲':'未丑','乙':'申子','丙':'酉亥','丁':'酉亥','戊':'未丑','己':'申子','庚':'未丑','辛':'午寅','壬':'卯巳','癸':'卯巳'}.get(dc,""): noble.append("천을귀인")
    if cur_j in {'甲':'巳','乙':'午','丙':'申','戊':'申','丁':'酉','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}.get(dc,""): noble.append("문창귀인")
    if cur_j in {'甲':'子午','乙':'子午','丙':'卯酉','丁':'卯酉','戊':'辰戌丑未','己':'辰戌丑未','庚':'寅亥','辛':'寅亥','壬':'巳申','癸':'巳申'}.get(dc,""): noble.append("태극귀인")
    if cur_j in {'甲':'巳','乙':'午','丙':'巳','丁':'午','戊':'申','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}.get(dc,""): noble.append("천주귀인")
    if cur_j in {'甲':'亥','乙':'戌','丙':'申','戊':'申','丁':'未','己':'未','庚':'巳','辛':'辰','壬':'寅','癸':'丑'}.get(dc,""): noble.append("암록")
    if cur_j == mj: noble.append("월덕귀인")
    
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): ausp.append("건록")
    if cur_j in {'甲':'亥','乙':'午','丙':'寅','戊':'寅','丁':'酉','己':'酉','庚':'巳','辛':'子','壬':'申','癸':'卯'}.get(dc,""): ausp.append("학당귀인")
    if cur_j in {'甲':'辰','乙':'巳','丙':'未','戊':'未','丁':'申','己':'申','庚':'戌','辛':'亥','壬':'丑','癸':'寅'}.get(dc,""): ausp.append("금여록")
    
    if gj in ["甲辰","乙未","丙戌","丁丑","戊辰","壬戌","癸丑"]: evil.append("백호대살")
    if gj in ["庚辰","庚戌","壬辰","壬戌","戊戌"]: evil.append("괴강살")
    if cur_j in {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子'}.get(dc,""): evil.append("양인살")
    if cur_j in ['午','寅','丑']: evil.append("탕화살")
    if cur_g in ['甲','辛'] or cur_j in ['卯','午','申']: evil.append("현침살")
    if cur_j in ['卯','酉','戌']: evil.append("철쇄개금")
    if cur_g == cur_j: evil.append("간여지동")
    dohwa_map = {'寅':'卯', '午':'卯', '戌':'卯', '申':'酉', '子':'酉', '辰':'酉', '巳':'午', '酉':'午', '丑':'午', '亥':'子', '卯':'子', '未':'子'}
    if cur_j == dohwa_map.get(yj, "") or cur_j == dohwa_map.get(dj, ""): evil.append("도화살")
    
    result = []
    for n in list(dict.fromkeys(noble)): result.append(f"<span style='color:#0D47A1;'>{n}</span>")
    for a in list(dict.fromkeys(ausp)): result.append(f"<span style='color:#2E7D32;'>{a}</span>")
    for e in list(dict.fromkeys(evil)): result.append(f"<span style='color:#C62828;'>{e}</span>")
    return result[:6]

def get_jijanggan_full(dg, ji):
    if ji in ["?", "-", " "]: return "-"
    raw = {'子':['壬','-','癸'],'丑':['癸','辛','己'],'寅':['戊','丙','甲'],'卯':['甲','-','乙'],'辰':['乙','癸','戊'],'巳':['戊','庚','丙'],'午':['丙','-','丁'],'未':['丁','乙','己'],'申':['戊','壬','庚'],'酉':['庚','-','辛'],'戌':['辛','丁','戊'],'亥':['戊','甲','壬']}.get(ji, ['-','-','-'])
    res = "<div style='display:flex; flex-direction:column; height:100%; min-height:40px; gap:1px; padding:1px 0;'>"
    for j in raw:
        if j != '-':
            ss_label = get_ss(dg, j)[:2]; ck = get_color(j)
            bg = {'목':'#2E7D32','화':'#C62828','토':'#F9A825','금':'#9E9E9E','수':'#212121'}.get(ck, '#888')
            res += f"<div style='flex-grow:1; display:flex; align-items:center; justify-content:center; background:{bg}; color:{('black' if ck=='토' else 'white')}; font-size:11px; font-weight:900; border-radius:2px;'>{j}({ss_label})</div>"
        else:
            res += "<div style='flex-grow:1; background:#f9f9f9; border:1px dashed #ddd; border-radius:2px;'></div>"
    return res + "</div>"

def calculate_gongmang(ilgan, ilji):
    if ilgan in ["?"," ","-"] or ilji in ["?"," ","-"]: return "-"
    try:
        base = (list(JI).index(ilji) - list(GAN).index(ilgan) - 2) % 12
        return list(JI)[base] + "," + list(JI)[(base+1)%12]
    except: return "-"

def get_time_ganji(day_gan, time_str):
    if "시간 모름" in time_str: return "?", "?"
    target_ji, t_idx = "子", 0
    if "朝子" in time_str or "夜子" in time_str: target_ji, t_idx = "子", 0
    else:
        for j in list(JI):
            if j in time_str: target_ji, t_idx = j, list(JI).index(j); break
    start_gan_idx = {"甲":0,"己":0,"乙":2,"庚":2,"丙":4,"辛":4,"丁":6,"壬":6,"戊":8,"癸":8}.get(day_gan, 0)
    return list(GAN)[(start_gan_idx + t_idx) % 10], target_ji

def get_daeun_su_accurate(utc_dt, order):
    try:
        sun = ephem.Sun(); jeol_lons = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]
        sun.compute(utc_dt); lon = math.degrees(ephem.Ecliptic(sun).lon) % 360.0
        if order == 1: targets = [l for l in jeol_lons if l > lon] + [l + 360 for l in jeol_lons if l <= lon]; t_lon = min(targets) % 360
        else: targets = [l for l in jeol_lons if l <= lon] + [l - 360 for l in jeol_lons if l > lon]; t_lon = max(targets) % 360
        search_dt, step = utc_dt, dt_mod.timedelta(hours=6) if order == 1 else dt_mod.timedelta(hours=-6)
        for _ in range(150):
            sun.compute(search_dt); l = math.degrees(ephem.Ecliptic(sun).lon) % 360.0
            if (order==1 and l>=t_lon and l-t_lon<180) or (order==-1 and l<=t_lon and t_lon-l<180): break
            search_dt += step
        return max(1, min(10, round(abs((search_dt - utc_dt).total_seconds()) / 86400.0 / 3)))
    except: return 1

# ==============================================================================
# 3. 사이드바 UI
# ==============================================================================
with st.sidebar:
    st.title("🧪 초연 임상 연구소")
    st.caption("Ver 12.5 Masterpiece (Ultimate)")
    
    with st.expander("🔍 사주팔자 역산 검색", expanded=False):
        col_g1, col_g2 = st.columns(2)
        with col_g1: ry = st.text_input("년주", value="")
        with col_g2: rm = st.text_input("월주", value="")
        col_g3, col_g4 = st.columns(2)
        with col_g3: rd = st.text_input("일주", value="")
        with col_g4: rt = st.text_input("시주", value="")
        
        K2H_GAN = {'갑':'甲','을':'乙','병':'丙','정':'丁','무':'戊','기':'己','경':'庚','신':'辛','임':'壬','계':'癸'}
        K2H_JI = {'자':'子','축':'丑','인':'寅','묘':'卯','진':'辰','사':'巳','오':'午','미':'未','신':'申','유':'酉','술':'戌','해':'亥'}
        
        if st.button("🔍 생년월일 자동입력", use_container_width=True):
            _ry, _rm, _rd = ry.replace("년","").replace(" ","")[:2], rm.replace("월","").replace(" ","")[:2], rd.replace("일","").replace(" ","")[:2]
            if len(_ry)==2 and len(_rm)==2 and len(_rd)==2:
                ry_h = K2H_GAN.get(_ry[0], _ry[0]) + K2H_JI.get(_ry[1], _ry[1])
                rm_h = K2H_GAN.get(_rm[0], _rm[0]) + K2H_JI.get(_rm[1], _rm[1])
                rd_h = K2H_GAN.get(_rd[0], _rd[0]) + K2H_JI.get(_rd[1], _rd[1])
                klc = KoreanLunarCalendar(); found = False
                for y in range(2026, 1899, -1):
                    klc.setSolarDate(y, 7, 1); gj_y = klc.getChineseGapJaString().split()
                    if gj_y and gj_y[0][:2] == ry_h:
                        curr_dt = dt_mod.date(y+1, 2, 28)
                        while curr_dt >= dt_mod.date(y, 1, 1):
                            klc.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                            gj = klc.getChineseGapJaString().split()
                            if len(gj) >= 3 and gj[0][:2] == ry_h and gj[1][:2] == rm_h and gj[2][:2] == rd_h:
                                st.session_state.s_y, st.session_state.s_m, st.session_state.s_d = curr_dt.year, curr_dt.month, curr_dt.day
                                time_map_rev = {'子':'00:30 ~ 01:29 (朝子)시','丑':'01:30 ~ 03:29 (丑)시','寅':'03:30 ~ 05:29 (寅)시','卯':'05:30 ~ 07:29 (卯)시','辰':'07:30 ~ 09:29 (辰)시','巳':'09:30 ~ 11:29 (巳)시','午':'11:30 ~ 13:29 (午)시','未':'13:30 ~ 15:29 (未)시','申':'15:30 ~ 17:29 (申)시','酉':'17:30 ~ 19:29 (酉)시','戌':'19:30 ~ 21:29 (戌)시','亥':'21:30 ~ 23:29 (亥)시'}
                                if rt:
                                    ji_char = rt.replace("시","").replace(" ","")[-1]
                                    rt_h = K2H_JI.get(ji_char, ji_char)
                                    if rt_h in time_map_rev: st.session_state.s_t = time_map_rev[rt_h]
                                found = True
                                is_leap = getattr(klc, 'isIntercalary', False)
                                leap_str = "윤달" if is_leap else "평달"
                                st.success(f"✅ [양력] {curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일 / [음력] {klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({leap_str}) 입력완료!")
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                        if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

    st.markdown("---")
    u_name = st.text_input("이름", value="", placeholder="정홍일")
    u_gender = st.selectbox("성별", ["남성", "여성", "돌싱"])
    u_cal = st.selectbox("달력", ["양력", "음력"])
    col1, col2, col3 = st.columns(3)
    u_y = col1.number_input("년", 1900, 2030, key="s_y")
    u_m = col2.number_input("월", 1, 12, key="s_m")
    u_d = col3.number_input("일", 1, 31, key="s_d")
    idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]
    u_t = st.selectbox("태어난 시간", idx_list, key="s_t")
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_single = st.button("🚀 초연 시공명리 사주풀이", use_container_width=True, type="primary")
    
    st.markdown("---")
    comp_text = st.text_area("비교할 타 술사 감명서 (선택)", height=150)
    st.markdown("<div class='navy-btn'>", unsafe_allow_html=True)
    btn_compare = st.button("⚖️ 두 감명서의 상세 비교", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# 4. 분석 가동 및 출력
# ==============================================================================
if btn_single or btn_compare:
    if btn_compare and not comp_text.strip(): st.warning("⚠️ 타 술사 감명서를 입력하세요.")
    else:
        klc = KoreanLunarCalendar()
        if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
        else: klc.setLunarDate(u_y, u_m, u_d, False)
        
        sol_str = f"{klc.solarYear}년 {klc.solarMonth:02d}월 {klc.solarDay:02d}일"
        lun_str = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일"
        
        curr_y = 2026
        curr_m = dt_mod.datetime.now().month
        u_age = curr_y - u_y + 1
        
        gj = klc.getChineseGapJaString().split()
        ys, yb, ms, mb, ds, db = gj[0][0], gj[0][1], gj[1][0], gj[1][1], gj[2][0], gj[2][1]
        hs, hb = get_time_ganji(ds, u_t); gans, jjis = [hs, ds, ms, ys], [hb, db, mb, yb]
        
        time_str = f" {u_t.split('(')[0].strip()} ({hb})시" if u_t != "시간 모름" else ""
        
        components.html(f"<div style='text-align:right;'><button style='background:#2E7D32; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; font-weight:bold;' onclick='window.parent.print()'>🖨️ {'3대 리포트 통합' if btn_compare else '초연 사주풀이'} 인쇄/PDF</button></div>", height=50)
        
        def td(c, size="18px"): return f"<td class='color-{get_color(c)}' style='font-size:{size}; font-weight:900;'>{('?' if c in ['?',' ','-'] else c)}</td>"
        
        ji_rel_rows = ""
        for l_idx, r_idx in enumerate([1, 2, 0, 3]):
            cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
            lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important;'>합충형파해</td>" if r_idx==1 else ""
            ji_rel_rows += f"<tr class='no-border-row'>{lbl}{cells}</tr>"

        disp_name = u_name if u_name.strip() else "정홍일"
        
        info_h = f"<div style='text-align:center; margin-bottom:20px;'><span style='font-size:20px; font-weight:900; color:#1A237E;'>🏮 {disp_name}님 ({u_gender}, {u_age}세)</span><br><span style='font-size:16px; color:#333; font-weight:900;'>[양력: {sol_str} | 음력: {lun_str}{time_str}]</span></div>"

        html_table = f"""
        <div class='report-page'><div class='vip-inset-frame'>
        <h1 style='text-align:center; color:#1A237E; font-size:28px; margin:0 0 10px 0;'>🔬 [초연 시공명리 사주풀이]</h1>
        {info_h}
        <table class='result-table'>
            <tr class='top-header-cell'><td>구분</td><td>시주</td><td>일주</td><td>월주</td><td>년주</td></tr>
            <tr><td class='header-cell-main'>천간합충</td>{"".join([f"<td>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])}</tr>
            <tr><td class='header-cell-main'>천간십성</td><td>{get_ss(ds,hs)}</td><td><span style='color:#D50000;'>日元</span></td><td>{get_ss(ds,ms)}</td><td>{get_ss(ds,ys)}</td></tr>
            <tr><td class='header-cell-main'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
            <tr><td class='header-cell-main'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
            <tr><td class='header-cell-main'>지지십성</td><td>{get_ss(ds,hb)}</td><td>{get_ss(ds,db)}</td><td>{get_ss(ds,mb)}</td><td>{get_ss(ds,yb)}</td></tr>
            <tr><td class='header-cell-main' style='padding:0;'>지장간</td>{"".join([f"<td style='padding:0;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
            {ji_rel_rows}
            <tr><td class='header-cell-main'>십이운성</td>{"".join([f"<td style='color:#0D47A1;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
            <tr><td class='header-cell-main'>십이신살</td>{"".join([f"<td style='color:#C62828;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
            <tr><td class='header-cell-main'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis)) if get_general_shinsal_filtered(i, gans, jjis) else '-'}</td>" for i in range(4)])}</tr>
        </table>
        """
        
        counts = {"목":0,"화":0,"토":0,"금":0,"수":0}
        for char in gans + jjis:
            if char != "?": counts[get_color(char)] += 1
        
        guiins = []
        for i in range(4):
            for res in get_general_shinsal_filtered(i, gans, jjis):
                if "귀인" in res: guiins.append(res.replace("<span style='color:#0D47A1;'>", "").replace("</span>", ""))
        guiin_str = ", ".join(list(set(guiins))) if guiins else "없음"
            
        utc_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0) - dt_mod.timedelta(hours=9)
        order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
        calc_d = get_daeun_su_accurate(utc_dt, order)
        n_gong = calculate_gongmang(ys, yb)
        i_gong = calculate_gongmang(ds, db)
        
        st.markdown(html_table + f"<div style='border:2px solid #3E2723; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap;'><div>⏳ 대운수: {calc_d}</div><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin_str}</div><div>🎯 공망: [년] {n_gong}, [일] {i_gong}</div></div>", unsafe_allow_html=True)
        
        # [핵심] 대운/세운/월운 흐름표 생성 (좌->우 LTR 정렬)
        un_html = f"<h4 style='color:#1A237E; margin-top:20px;'>1) 대운의 흐름 (대운수: {calc_d})</h4><div class='flow-flex'>"
        for i in range(10):
            val, c, j = i*10+calc_d, GAN[(GAN.index(ms)+(i+1)*order)%10] if ms in GAN else "-", JI[(JI.index(mb)+(i+1)*order)%12] if mb in JI else "-"
            is_active = val <= u_age < val+10
            bg_col = "#FFF9C4" if is_active else "transparent"
            un_html += f"<div class='flow-col' style='background-color:{bg_col};'><div class='dw-age-head'>{val}세</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,c)}</div><div class='color-{get_color(c)}' style='font-size:16px; font-weight:900;'>{c}</div><div class='color-{get_color(j)}' style='font-size:16px; font-weight:900;'>{j}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,j)}</div><div style='font-size:11px;'>{get_unsung(ds,j)}</div><div style='font-size:11px; color:#C62828;'>{get_12_shinsal(yb, j)}</div></div>"
        un_html += "</div>"

        cur_dw_idx = max(0, (u_age - calc_d) // 10)
        dw_g_cur = GAN[(GAN.index(ms) + (cur_dw_idx+1)*order)%10] if ms in GAN else "-"
        dw_j_cur = JI[(JI.index(mb) + (cur_dw_idx+1)*order)%12] if mb in JI else "-"
        se_html = f"<h4 style='color:#1A237E; margin-top:20px;'>2) 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준)</h4><div class='flow-flex'>"
        for i in range(10):
            ty, tage = 2026 + i, u_age + i
            base = (ty - 1984) % 60
            tc, tj = GAN[base % 10], JI[base % 12]
            is_cur_yr = (ty == 2026)
            bg_col = "#E1F5FE" if is_cur_yr else "transparent"
            se_html += f"<div class='flow-col' style='background-color:{bg_col};'><div class='dw-age-head'>{ty}년({tage}세)</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828;'>{get_12_shinsal(yb, tj)}</div></div>"
        se_html += "</div>"

        wol_gans = ["己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚"]
        wol_jis = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]
        wol_html = f"<h4 style='color:#1A237E; margin-top:20px;'>3) 월운의 흐름 (2026년도 양력기준)</h4><div class='flow-flex'>"
        for i in range(12):
            tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
            is_cur_m = (tm == curr_m)
            bg_col = "#E8F5E9" if is_cur_m else "transparent"
            wol_html += f"<div class='flow-col' style='background-color:{bg_col};'><div class='dw-age-head'>{tm}월</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828;'>{get_12_shinsal(yb, tj)}</div></div>"
        wol_html += "</div>"
        
        # [핵심] 박사님 작성 하드코딩 맺음말
        closing_html = f"""
        <div style='margin-top: 30px;'>
            <p style='text-indent: 15px; text-align: justify; word-break: keep-all; line-height: 1.8; margin-bottom: 8px; color: #333;'>'사주팔자(命)'는 태어날 때 부여받은 변하지 않는 '바코드(bar-code)'와 같지만, 우리가 살아가며 마주하는 '스캐너(scanner)'인 '운(運)'은 늘 변화하며 흐릅니다.</p>
            <p style='text-indent: 15px; text-align: justify; word-break: keep-all; line-height: 1.8; margin-bottom: 8px; color: #333;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{disp_name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
            <p style='text-indent: 15px; text-align: justify; word-break: keep-all; line-height: 1.8; margin-bottom: 15px; color: #333;'>앞으로 미래에 대한 더 깊은 시공간의 지혜와 궁금증이 있으시면 언제든 '초연 시공명리 연구소의 문'을 두드려 주십시오.</p>
            <p style='text-indent: 15px; font-size: 16px; line-height: 1.8; color: #333; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
            <div style='text-align: right; margin-top: 30px;'>
                <span style='font-weight: 900; font-size: 20px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
            </div>
        </div>
        """

        # [AI 프롬프트: 12단계 및 운세분석 강제 족쇄]
        with st.spinner("초연 509 시스템: 체용(體用) 실행분석 및 12.5 마스터피스 가동 중..."):
            prompt = f"""
            [절대 규칙: 표(Table)는 파이썬(만세력)이 자동 생성하여 삽입하므로, AI는 절대 표나 그리드를 직접 마크다운으로 그리지 마십시오. 오직 텍스트 분석만 작성하십시오. 모든 문장은 명조체 폰트를 사용.]
            당신은 최고의 명리학 마스터 '초연 박사'입니다.
            내담자: {disp_name} ({u_gender}, {sol_str}생)
            사주: {ys}{yb}년 {ms}{mb}월 {ds}{db}일 {hs}{hb}시 / 공망: {i_gong}
            
            [🚨 제5장 운세분석 비급 (필수 반영 사항)]
            1. 대운은 체운(시기, 환경), 세운/월운은 용운(실행, 사건격발)으로 접근.
            2. 사고(四庫) 진술축미의 왕자입고(旺者入庫), 암신개고(暗神開庫) 타이밍 정밀 분석.
            3. 천라지망 및 원진/귀문, 동착살 흉화 가중 심층 스캔.
            4. 월운 분석 시 반드시 전반기(5~19일)와 후반기(20일~익월 4일)로 절기를 나누어 작성.

            [출력 템플릿] 아래 1~12단계 목차(HTML)를 무조건 동일하게 출력하십시오. 1. 2. 3. 넘버링 필수.
            <h3 style='color:#1A237E;'>1) 분석</h3><div class='content-box-loose'><p>1. (격국 및 무대 분석)</p></div>
            <h3 style='color:#1A237E;'>2) 성격</h3><div class='content-box-loose'><p>1. (지장간 좌법/인종법 분석)</p></div>
            <h3 style='color:#1A237E;'>3) 부모·형제운</h3><div class='content-box-loose'></div>
            <h3 style='color:#1A237E;'>4) 학업·진학운</h3><div class='content-box-loose'></div>
            <h3 style='color:#1A237E;'>5) 적성·직업운</h3><div class='content-box-loose'></div>
            <h3 style='color:#1A237E;'>6) 결혼·자녀운</h3><div class='content-box-loose'></div>
            <h3 style='color:#1A237E;'>7) 사업운</h3><div class='content-box-loose'></div>
            <h3 style='color:#1A237E;'>8) 관직·명예운</h3><div class='content-box-loose'></div>
            <h3 style='color:#1A237E;'>9) 재성운</h3><div class='content-box-loose'></div>
            <h3 style='color:#1A237E;'>10) 건강운</h3><div class='content-box-loose'></div>
            
            <h3 style='color:#1A237E;'>11) 운의 흐름</h3>
            [DAEWUN_TABLE_HERE]
            <div class='content-box-loose'>
                <p>▶ 과거 대운 요약 (3줄 이상)</p>
                <p>▶ 현재 대운 상세 (5줄 이상, 체운의 환경 변화 및 십성 충돌 분석)</p>
            </div>
            [SEWUN_TABLE_HERE]
            <div class='content-box-loose'>
                <p>▶ 과거 세운 요약 (3줄 이상)</p>
                <p>▶ 올해 세운 상세 (5줄 이상, 용운의 사건 실행 및 합충 분석)</p>
            </div>
            [WOLWUN_TABLE_HERE]
            <div class='content-box-loose'>
                <p>▶ 과거 월운 요약 (3줄 이상)</p>
                <p>▶ 이번 달({curr_m}월) 전반기 (양력 5일~19일): (해당 시기의 구체적 사건 및 심리 촉발 상세 서술)</p>
                <p>▶ 이번 달({curr_m}월) 후반기 (양력 20일~익월 4일): (해당 시기의 구체적 사건 및 심리 촉발 상세 서술)</p>
            </div>

            <h3 style='color:#1A237E; margin-top:30px;'>12) 삶을 바꾸는 지혜로운 조언</h3>
            <div class='content-box-loose' style='background-color:#fdfdfd; padding:15px; border:1px solid #eee; border-radius:8px;'>
                <p><b>◈ 나를 돕는 에너지와 색상:</b> (색상 및 기운 팁)</p>
                <p><b>◈ 신체 밸런스와 에너지 관리:</b> (건강 조언)</p>
                <p><b>◈ 공간의 흐름과 방위의 지혜:</b> (귀인의 방위)</p>
                <p><b>◈ 재능 효율을 높이는 직업적 지혜:</b> (적성 팁)</p>
                <p><b>◈ 더 나은 내일을 위한 절제의 미학:</b> (수성 원칙)</p>
                <div style='margin-top:20px;'><span style='color:#1A237E; font-weight:900;'>[초연 시공명리 특별 개운 비법]</span></div>
                <p><b>◈ 수호 천사의 기운:</b> (천을귀인 활용법)</p>
                <p><b>◈ 백년해로의 기운:</b> (부부 관계 조언)</p>
                <p><b>◈ 행운에 따른 기운:</b> (도/망/역 등 수성 전략)</p>
            </div>
            """
            try:
                res = model.generate_content(prompt)
                
                # 표 삽입 치환 및 맺음말(closing_html) 직접 결합
                final_report = res.text.replace("[DAEWUN_TABLE_HERE]", un_html).replace("[SEWUN_TABLE_HERE]", se_html).replace("[WOLWUN_TABLE_HERE]", wol_html)
                final_report += closing_html
                
                st.markdown(f"<div style='margin-top:20px;'>{final_report}</div></div></div>", unsafe_allow_html=True)
                
                if btn_compare:
                    st.markdown(f"<div class='page-break'></div><div class='report-page no-bg-print'><div class='vip-inset-frame' style='border-color:#3E2723;'><h2 style='text-align:center; color:#3E2723; margin-bottom:20px;'>📜 타 술사 감명서 원본 내역</h2><div class='content-box-loose'>{comp_text.replace('\\n','<br>')}</div></div></div>", unsafe_allow_html=True)
                    
                    with st.spinner("1:1 교차 대조 중..."):
                        comp_prompt = f"""
[시스템: 1:1 비교]
타 술사 감명서를 1~11단계 목차에 맞춰 교차 대조.
타 술사의 '정적인 구조' 파악의 한계를 지적하고, 초연의 '동적 시뮬레이션(시기에 따른 실행분석)' 우위를 입증.
12번은 [12) 종합 의견]으로 총평.

대상 데이터: {comp_text}
"""
                        c_res = model.generate_content(comp_prompt)
                        st.markdown(f"<div class='page-break'></div><div class='report-page no-bg-print'><div class='vip-inset-frame' style='border-color:#D50000;'><h2 style='text-align:center; color:#D50000; margin-bottom:20px;'>⚖️ 두 감명서 1:1 상세비교 리포트</h2><div class='content-box-loose'>{c_res.text}</div><div style='text-align:center; margin-top:50px; font-size:20px; font-weight:900;'>- 초연 임상 연구소 -</div></div></div>", unsafe_allow_html=True)
                        
            except Exception as e: 
                st.error(f"AI 연산 오류: {e}")
