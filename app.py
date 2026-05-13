import streamlit as st
import pandas as pd
import json
import os
import math
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import ephem
import google.generativeai as genai

# ==============================================================================
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS
# ==============================================================================
st.set_page_config(page_title="초연 시공명리 Ver 8.7", layout="wide")

st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&family=Malgun+Gothic&display=swap");
    .stApp { background-color: #FFF8E1; font-family: 'Malgun Gothic', sans-serif; }
    .report-page { max-width: 950px; margin: 20px auto; background: white; padding: 25px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }
    .vip-inset-frame { border: 3px solid #1A237E; border-radius: 20px; padding: 40px; background: white; }
    .result-table { width: 100%; border-collapse: collapse; border: 3px solid #3E2723; margin-bottom: 15px; table-layout: fixed; }
    .result-table td { border: 1px solid #444; padding: 5px; text-align: center; vertical-align: middle; font-weight: 900; font-size: 14px; }
    .header-cell-main { background-color: #E8EAF6 !important; color: #1A237E !important; font-weight: 900 !important; }
    .top-header-cell { background-color: #1A237E !important; color: white !important; font-size: 16px !important; padding: 8px 0 !important; }
    .color-목 { background-color: #2E7D32 !important; color: white !important; }
    .color-화 { background-color: #C62828 !important; color: white !important; }
    .color-토 { background-color: #F9A825 !important; color: black !important; }
    .color-금 { background-color: #9E9E9E !important; color: white !important; }
    .color-수 { background-color: #212121 !important; color: white !important; }
    .content-box-loose { line-height: 1.8; font-size: 16px; font-family: 'Noto Serif KR', serif; text-align: justify; text-indent: 15px; margin-bottom: 12px; }
    .un-title { font-weight: 900; font-size: 20px; color: #3E2723; border-bottom: 2px solid #3E2723; margin-top: 30px; margin-bottom: 10px; }
    .rtl-scroll { display: flex; flex-direction: row-reverse; width: 100%; border: 2px solid #3E2723; overflow-x: auto; background: white; }
    .dw-age-head { background: #3E2723; color: white; font-weight: 900; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. AI 엔진 및 DB 설정
# ==============================================================================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro')
except:
    pass

@st.cache_data
def load_db():
    db_path = "choyeon_db.json"
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f: return json.load(f)
    return {"wolryeong": {}, "ilju": {}}

CHOYEON_DB = load_db()

# ==============================================================================
# 2. 명리 연산 엔진 (코랩 원본 100% 복구: 신살, 지장간, 합충 등)
# ==============================================================================
GAN = "甲乙丙丁戊己庚辛壬癸"
JI = "子丑寅卯辰巳午未申酉戌亥"

def split_hanja(v):
    v = v.strip()
    if len(v) >= 2: return v[0], v[1]
    return "?", "?"

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
    if target_ji in ["?", " ", "-"] or not year_ji: return "-"
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
    s = {me, target}; r = []
    if s in [{'寅','卯'}, {'卯','辰'}, {'寅','辰'}, {'巳','午'}, {'午','未'}, {'巳','未'}, {'申','酉'}, {'酉','戌'}, {'申','戌'}, {'亥','子'}, {'子','丑'}, {'亥','丑'}]: r.append("방합")
    if s in [{'申','子'}, {'子','辰'}, {'申','辰'}, {'寅','午'}, {'午','戌'}, {'寅','戌'}, {'亥','卯'}, {'卯','未'}, {'亥','未'}, {'巳','酉'}, {'酉','丑'}, {'巳','丑'}]: r.append("반합")
    if s in [{'子','丑'}, {'寅','亥'}, {'卯','戌'}, {'辰','酉'}, {'巳','申'}, {'午','未'}]: r.append("육합")
    if s in [{'午','亥'}, {'子','戌'}, {'丑','寅'}, {'寅','未'}, {'卯','申'}]: r.append("암합")
    if s in [{'子','午'}, {'丑','未'}, {'寅','申'}, {'卯','酉'}, {'辰','戌'}, {'巳','亥'}]: r.append("충")
    if s in [{'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}, {'子','卯'}]: r.append("형")
    if s in [{'子','未'}, {'丑','午'}, {'寅','巳'}, {'卯','辰'}, {'申','亥'}, {'酉','戌'}]: r.append("해")
    if s in [{'子','酉'}, {'丑','辰'}, {'寅','亥'}, {'卯','午'}, {'巳','申'}, {'未','戌'}]: r.append("파")
    if s == {'戌','亥'}: r.append("천라")
    if s == {'辰','巳'}: r.append("지망")
    if s in [{'丑','午'}, {'卯','申'}, {'辰','亥'}, {'巳','戌'}]: r.extend(["원진", "귀문"])
    elif s in [{'子','酉'}, {'寅','未'}]: r.append("귀문")
    elif s in [{'寅','酉'}, {'子','未'}]: r.append("원진")
    return ", ".join(list(dict.fromkeys(r))) if r else "-"

def get_general_shinsal(idx, gans, jjis):
    sc, dc, mc, yc = gans; sj, dj, mj, yj = jjis; cur_g, cur_j = gans[idx], jjis[idx]
    if cur_g in ["?", "-", " "] or cur_j in ["?", "-", " "]: return [], [], []
    gj = cur_g + cur_j; noble, ausp, evil = [], [] , []
    if cur_j in {'甲':'未丑','乙':'申子','丙':'酉亥','丁':'酉亥','戊':'未丑','己':'申子','庚':'未丑','辛':'午寅','壬':'卯巳','癸':'卯巳'}.get(dc,""): noble.append("천을귀인")
    if cur_j == mj: noble.append("월덕귀인")
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): ausp.append("건록")
    if gj in ["甲辰","乙未","丙戌","丁丑","戊辰","壬戌","癸丑"]: evil.append("백호살")
    if gj in ["庚辰","庚戌","壬辰","壬戌","戊戌"]: evil.append("괴강살")
    if cur_j in {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子'}.get(dc,""): evil.append("양인살")
    if cur_j in ['午','寅','丑']: evil.append("탕화살")
    if cur_g == cur_j: evil.append("간여지동")
    dohwa_map = {'寅':'卯', '午':'卯', '戌':'卯', '申':'酉', '子':'酉', '辰':'酉', '巳':'午', '酉':'午', '丑':'午', '亥':'子', '卯':'子', '未':'子'}
    if cur_j == dohwa_map.get(yj, "") or cur_j == dohwa_map.get(dj, ""): evil.append("도화살")
    return list(dict.fromkeys(noble)), list(dict.fromkeys(ausp)), list(dict.fromkeys(evil))

def get_jijanggan_full(dg, ji):
    if ji in ["?", "-", " "]: return "-"
    raw = {'子':['壬','-','癸'],'丑':['癸','辛','己'],'寅':['戊','丙','甲'],'卯':['甲','-','乙'],'辰':['乙','癸','戊'],'巳':['戊','庚','丙'],'午':['丙','己','丁'],'未':['丁','乙','己'],'申':['戊','壬','庚'],'酉':['庚','-','辛'],'戌':['辛','丁','戊'],'亥':['戊','甲','壬']}.get(ji, ['-','-','-'])
    res = "<div style='display:flex; flex-direction:column; height:100%; min-height:65px; gap:2px; padding:2px 0; margin:0;'>"
    for j in raw:
        if j != '-':
            ss_label = get_ss(dg, j)[:2]; color_key = get_color(j)
            bg = {'목':'#2E7D32','화':'#C62828','토':'#F9A825','금':'#9E9E9E','수':'#212121'}.get(color_key, '#888')
            tc = 'white' if color_key != '토' else 'black'
            res += f"<div style='flex-grow:1; display:flex; align-items:center; justify-content:center; background:{bg}; color:{tc}; width:95%; margin:0 auto; font-size:12px; font-weight:900; border-radius:3px;'>{j} ({ss_label})</div>"
        else: res += "<div style='flex-grow:1; display:flex; align-items:center; justify-content:center; background:#f9f9f9; width:95%; margin:0 auto; color:#bbb; border-radius:3px; border:1px dashed #ddd;'>-</div>"
    return res + "</div>"

def calculate_gongmang(ilgan, ilji):
    if ilgan in ["?"," ","-"] or ilji in ["?"," ","-"]: return "모름"
    try:
        base = (list(JI).index(ilji) - list(GAN).index(ilgan) - 2) % 12
        return list(JI)[base] + "," + list(JI)[(base+1)%12]
    except: return "모름"

def get_time_ganji(day_gan, time_str):
    if "시간 모름" in time_str: return "?", "?"
    time_idx_map = {"子":0,"丑":1,"寅":2,"卯":3,"辰":4,"巳":5,"午":6,"未":7,"申":8,"酉":9,"戌":10,"亥":11}
    target_ji = "?"
    for j in list(JI):
        if j in time_str: target_ji = j; break
    if target_ji == "?": return "?", "?"
    start_gan_idx = {"甲":0,"己":0,"乙":2,"庚":2,"丙":4,"辛":4,"丁":6,"壬":6,"戊":8,"癸":8}.get(day_gan, 0)
    target_gan = list(GAN)[(start_gan_idx + time_idx_map[target_ji]) % 10]
    return target_gan, target_ji

def get_daeun_su_accurate(utc_dt, order):
    try:
        sun = ephem.Sun(); jeol_lons = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]
        sun.compute(utc_dt); lon = math.degrees(ephem.Ecliptic(sun).lon) % 360.0
        if order == 1: targets = [l for l in jeol_lons if l > lon] + [l + 360 for l in jeol_lons if l <= lon]; t_lon = min(targets) % 360
        else: targets = [l for l in jeol_lons if l <= lon] + [l - 360 for l in jeol_lons if l > lon]; t_lon = max(targets) % 360
        search_dt = utc_dt; step = dt_mod.timedelta(hours=6) if order == 1 else dt_mod.timedelta(hours=-6)
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
    st.caption("Ver 8.7 Masterpiece (Full Version)")
    u_name = st.text_input("성함", "내담자")
    u_gender = st.selectbox("성별", ["남성", "여성"])
    u_cal = st.selectbox("달력", ["양력", "음력"])
    col1, col2, col3 = st.columns(3)
    with col1: u_y = st.number_input("년", 1900, 2030, 1963)
    with col2: u_m = st.number_input("월", 1, 12, 5)
    with col3: u_d = st.number_input("일", 1, 31, 22)
    u_t = st.selectbox("태어난 시간", [
        "시간 모름", "23:30 ~ 01:29 (子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", 
        "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", 
        "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", 
        "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시"
    ])
    st.markdown("---")
    st.markdown("### ⚖️ 타 감명지 비교용")
    comp_text = st.text_area("비교할 타 술사 감명서", height=150)

# ==============================================================================
# 4. 분석 가동 및 레이아웃 (수직 통합형 원상복구 - 코랩 100%)
# ==============================================================================
if st.button("🚀 초연 시공명리 풀버전 가동", use_container_width=True):
    klc = KoreanLunarCalendar()
    if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
    else: klc.setLunarDate(u_y, u_m, u_d, False)
    
    gj = klc.getChineseGapJaString().split()
    ys, yb = gj[0][0], gj[0][1]; ms, mb = gj[1][0], gj[1][1]; ds, db = gj[2][0], gj[2][1]
    hs, hb = get_time_ganji(ds, u_t)
    
    # --- 1. 정밀 원국 표 렌더링 ---
    gans = [hs, ds, ms, ys]
    jjis = [hb, db, mb, yb]
    
    def d_str(v): return v if v not in ["?", " ", "-", "모름"] else "-"
    def td(c, size="22px"): return f"<td class='color-{get_color(c)}' style='font-size:{size};'>{d_str(c)}</td>"
    def ss_td(tc): return f"<td class='sub-header'>{get_ss(ds, tc)}</td>"
    
    # 합충형해파 행 생성
    ji_rel_rows = ""
    for loop_idx, r_idx in enumerate([1, 2, 0, 3]):
        border_css = "border-bottom: 1px solid #444 !important;" if loop_idx == 3 else "border-top: none !important; border-bottom: none !important;"
        if loop_idx == 0: border_css = "border-bottom: none !important;"
        cells = "".join([f"<td style='color:{('#D50000' if c_idx==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[c_idx])!='-' else '#BBB'))}; font-weight:900; {border_css}'>{('←('+d_str(jjis[r_idx])+')→' if c_idx==r_idx else get_ji_rel_set(jjis[r_idx], jjis[c_idx]))}</td>" for c_idx in range(4)])
        lbl = f"<td rowspan='4' class='header-cell-main' style='border-bottom: 1px solid #444 !important;'>합충형파해</td>" if r_idx==1 else ""
        ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

    hch_tds = "".join([f"<td>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])
    jg_tds = "".join([f"<td style='padding:0;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])
    un_tds = "".join([f"<td style='color:#0D47A1 !important;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])
    s12_tds = "".join([f"<td style='color:#C62828 !important;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])
    
    shinsal_tds = ""
    for i in range(4):
        noble, ausp, evil = get_general_shinsal(i, gans, jjis)
        cmb = [f"<span style='color:#0D47A1;'>{x}</span>" for x in noble + ausp] + [f"<span style='color:#C62828;'>{x}</span>" for x in evil]
        shinsal_tds += f"<td style='vertical-align: top; font-size:12px; line-height:1.4;'>{'<br>'.join(cmb[:6]) if cmb else '-'}</td>"

    html_table = f"""
    <table class='result-table'>
        <tr><td class='top-header-cell'>구분</td><td class='top-header-cell'>시주</td><td class='top-header-cell'>일주</td><td class='top-header-cell'>월주</td><td class='top-header-cell'>년주</td></tr>
        <tr><td class='header-cell-main'>천간합충</td>{hch_tds}</tr>
        <tr><td class='header-cell-main'>천간십성</td>{ss_td(hs)}<td><span style='color:#D50000'>日元</span></td>{ss_td(ms)}{ss_td(ys)}</tr>
        <tr><td class='header-cell-main'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
        <tr><td class='header-cell-main'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
        <tr><td class='header-cell-main'>지지십성</td>{ss_td(hb)}{ss_td(db)}{ss_td(mb)}{ss_td(yb)}</tr>
        <tr><td class='header-cell-main' style='padding:0;'>지장간</td>{jg_tds}</tr>
        {ji_rel_rows}
        <tr><td class='header-cell-main'>십이운성</td>{un_tds}</tr>
        <tr><td class='header-cell-main'>십이신살</td>{s12_tds}</tr>
        <tr><td class='header-cell-main'>일반신살</td>{shinsal_tds}</tr>
    </table>
    """
    
    st.markdown(f"### 🏮 {u_name}님 정밀 사주 원국")
    st.markdown(html_table, unsafe_allow_html=True)
    
    # --- 2. 마스터 바 ---
    counts = {"목":0,"화":0,"토":0,"금":0,"수":0}
    for char in [hs, ds, ms, ys, hb, db, mb, yb]:
        if char != "?": counts[get_color(char)] += 1
    
    utc_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0) - dt_mod.timedelta(hours=9)
    order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
    calc_d = get_daeun_su_accurate(utc_dt, order)
    
    st.markdown(f"""
    <div style='border: 2px solid #3E2723; background-color: #FFF8E1; padding: 10px; display: flex; justify-content: space-around; font-size: 15px; font-weight: 900; border-radius: 8px;'>
        <div>⏳ 대운수: <b>{calc_d}</b></div>
        <div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div>
        <div>🎯 공망: [일] {calculate_gongmang(ds, db)}</div>
    </div>
    """, unsafe_allow_html=True)

    # --- 3. 대운 흐름표 (RTL) ---
    st.markdown("<div class='un-title'>◈ 대운의 흐름</div>", unsafe_allow_html=True)
    un_html = "<div class='rtl-scroll'>"
    for i in range(10):
        val = i*10 + calc_d
        c = GAN[(GAN.index(ms)+(i+1)*order)%10] if ms in GAN else "-"
        j = JI[(JI.index(mb)+(i+1)*order)%12] if mb in JI else "-"
        un_html += f"""
        <div style='flex: 1; min-width: 80px; border-left: 1px solid #ccc; text-align: center; padding-bottom:5px;'>
            <div class='dw-age-head'>{val}세</div>
            <div style='padding: 5px;'>{get_ss(ds, c)}</div>
            <div class='color-{get_color(c)}' style='font-size:18px;'>{c}</div>
            <div class='color-{get_color(j)}' style='font-size:18px;'>{j}</div>
            <div style='padding: 5px;'>{get_ss(ds, j)}</div>
            <div style='font-size:12px;'>{get_unsung(ds, j)}</div>
            <div style='font-size:12px; color:#C62828;'>{get_12_shinsal(yb, j)}</div>
        </div>
        """
    st.markdown(un_html + "</div>", unsafe_allow_html=True)

    # --- 4. 11단계 정밀 감명 & 비교 리포트 ---
    st.markdown("---")
    with st.spinner("초연 509 시스템: 합충형해파 동적 물리엔진 가동 중..."):
        prompt = f"""
        당신은 최고의 명리학 마스터 '초연 박사'입니다.
        내담자: {u_name} ({u_gender}, {u_y}년 {u_m}월 {u_d}일생)
        사주: {ys}{yb} {ms}{mb} {ds}{db} {hs}{hb} / 공망: {calculate_gongmang(ds, db)}
        
        [지시사항]
        1. 11단계(성격, 부모, 학업, 직업, 결혼, 사업, 재산, 건강, 대운, 세운 등)로 정밀 분석하시오.
        2. {f'3. 아래 타 술사의 감명서와 1:1 비교하여 초연 시스템의 우위를 증명하시오: {comp_text}' if comp_text else ''}
        3. HTML 구조를 활용하여 VIP 인셋 프레임 형식으로 화려하고 깊이 있게 서술하십시오.
        """
        try:
            if "GOOGLE_API_KEY" not in st.secrets:
                st.error("API 키가 없습니다.")
            else:
                res = model.generate_content(prompt)
                st.markdown(f"<div class='report-page'><div class='vip-inset-frame'>{res.text}</div></div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"AI 연산 오류: {e}")
