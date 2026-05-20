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
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS (Ver 15.0 원본 100% 사수)
# ==============================================================================
st.set_page_config(page_title="초연 시공명리 사주풀이 Ver 21.0", layout="wide")

st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");
    
    body, .stApp { background-color: #FFF8E1; }
    
    .report-page { 
        width: 210mm; 
        max-width: 100%;
        margin: 30px auto; 
        background-color: #FFFFFF !important; 
        padding: 15mm 10mm; 
        box-shadow: 0 0 20px rgba(0,0,0,0.15); 
        border-radius: 20px; 
        box-sizing: border-box; 
    }
    
    .report-page, .report-page * { 
        font-family: 'Noto Serif KR', serif !important; 
        color: #000000;
    }
    
    .vip-inset-frame { 
        border: 2px solid #1A237E; 
        border-radius: 15px; 
        padding: 20px; 
        background: transparent; 
        -webkit-box-decoration-break: clone;
        box-decoration-break: clone;
    }
    
    .report-page h1 { font-size: 26px !important; margin-bottom: 15px !important; color: #1A237E !important; font-weight: 900 !important; }
    .report-page h2 { font-size: 22px !important; margin-bottom: 15px !important; font-weight: 900 !important; }
    .report-page h3 { font-size: 19px !important; margin-top: 25px !important; margin-bottom: 10px !important; border-bottom: 2px solid #1A237E; padding-bottom: 5px; color: #1A237E !important; font-weight: 900 !important; }
    .report-page h4 { font-size: 17px !important; margin-top: 15px !important; margin-bottom: 8px !important; font-weight: 900 !important; }
    
    .result-table { width: 100%; border-collapse: collapse; border: 3px solid #3E2723; margin-bottom: 15px; table-layout: fixed; }
    .result-table td { border: 1px solid #444; padding: 1px; text-align: center; vertical-align: middle; font-weight: 900; font-size: 13px; line-height: 1.2; word-wrap: break-word; }
    
    .no-border-row td { border-top: none !important; border-bottom: none !important; }
    .no-border-row:last-of-type td { border-bottom: 1px solid #444 !important; }
    
    .header-cell-main { background-color: #E8EAF6 !important; color: #1A237E !important; font-weight: 900 !important; font-size: 12px !important; height: 22px !important; }
    
    .top-header-cell { background-color: #1A237E !important; height: 30px !important; }
    .top-header-cell td, .top-header-cell span { color: #FFFFFF !important; font-weight: 900 !important; font-size: 16px !important; }
    
    .color-목 { background-color: #2E7D32 !important; color: white !important; }
    .color-화 { background-color: #C62828 !important; color: white !important; }
    .color-토 { background-color: #F9A825 !important; color: black !important; }
    .color-금 { background-color: #9E9E9E !important; color: white !important; }
    .color-수 { background-color: #212121 !important; color: white !important; }
    
    /* 🎯 1~12번 대제목 크기/밑줄/마진 완벽 통일 */
    .report-page h3 { font-size: 22px !important; margin-top: 35px !important; margin-bottom: 15px !important; border-bottom: 2px solid #1A237E; padding-bottom: 8px; color: #1A237E !important; font-weight: 900 !important; width: 100%; display: block; }
    
    /* 🎯 특수기호(▶, •, ◈) 소제목 및 일반 본문 제어 구역 */
    .content-box-loose { line-height: 1.8; font-size: 15px; color: #111; text-align: justify; word-break: keep-all; font-family: 'Noto Serif KR', 'Nanum Myeongjo', serif !important; padding: 0 !important; }
    
    /* 소목차(▶, •, ◈, 1), 2) 등)는 들여쓰기 0, 마진 칼각, 그리고 '무조건 강력한 굵은 글씨' 강제 */
    .content-box-loose .sub-title { text-indent: 0px !important; margin-top: 25px !important; margin-bottom: 10px !important; font-weight: 900 !important; display: block; color: #111 !important; }
    
    /* 사이드바 버튼 색상 */    
    div[data-testid="stSidebar"] div.stButton > button:first-child { background-color: #D50000; color: white; border: none; font-weight: 900; height: 45px; }
    div[data-testid="stSidebar"] .navy-btn button { background-color: #1A237E !important; color: white !important; border: none !important; font-weight: 900 !important; height: 45px; }
    
    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; }
        .report-page { 
            box-shadow: none; margin: 0 auto; padding: 0; 
            page-break-after: always; 
            border-radius: 0; width: 100%; max-width: 100%;
        }
        .report-page:last-of-type { page-break-after: auto; }
        .page-break-before { page-break-before: always; }
        .vip-inset-frame { border: 2px solid #000; border-radius: 20px; padding: 15px; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. 시스템 변수 세팅 및 써머타임 엔진
# ==============================================================================
if 's_y' not in st.session_state: st.session_state.s_y = 1964
if 's_m' not in st.session_state: st.session_state.s_m = 1
if 's_d' not in st.session_state: st.session_state.s_d = 15
if 's_t' not in st.session_state: st.session_state.s_t = "07:30 ~ 09:29 (辰)시"

def get_total_time_adjustment(dt):
    adj = -30
    if dt_mod.datetime(1954, 3, 21) <= dt <= dt_mod.datetime(1961, 8, 9, 23, 59): adj = 0
    si = [(dt_mod.datetime(1948,5,31), dt_mod.datetime(1948,9,22)), (dt_mod.datetime(1949,3,31), dt_mod.datetime(1949,9,30)), (dt_mod.datetime(1950,4,1), dt_mod.datetime(1950,9,10)), (dt_mod.datetime(1951,5,6), dt_mod.datetime(1951,9,9)), (dt_mod.datetime(1954,3,21), dt_mod.datetime(1954,5,5)), (dt_mod.datetime(1955,4,6), dt_mod.datetime(1955,9,22)), (dt_mod.datetime(1956,5,20), dt_mod.datetime(1956,9,30)), (dt_mod.datetime(1957,5,5), dt_mod.datetime(1957,9,22)), (dt_mod.datetime(1958,5,4), dt_mod.datetime(1958,9,21)), (dt_mod.datetime(1959,5,4), dt_mod.datetime(1959,9,20)), (dt_mod.datetime(1960,5,1), dt_mod.datetime(1960,9,18)), (dt_mod.datetime(1987,5,10,2), dt_mod.datetime(1987,10,11,3)), (dt_mod.datetime(1988,5,8,2), dt_mod.datetime(1988,10,9,3))]
    for s, e in si:
        if s <= dt <= e: adj -= 60; break
    return adj

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
# 2. AI 및 명리 연산 엔진
# ==============================================================================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-pro') 
except: pass

GAN, JI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"

JIJANGGAN = {
    '子': ['壬', '-', '癸'], 
    '丑': ['癸', '辛', '己'], 
    '寅': ['戊', '丙', '甲'], 
    '卯': ['甲', '-', '乙'], 
    '辰': ['乙', '癸', '戊'], 
    '巳': ['戊', '庚', '丙'], 
    '午': ['丙', '己', '丁'], 
    '未': ['丁', '乙', '己'], 
    '申': ['戊', '壬', '庚'], 
    '酉': ['庚', '-', '辛'], 
    '戌': ['辛', '丁', '戊'], 
    '亥': ['戊', '甲', '壬']
}

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
    if cur_j in {'甲':'亥','乙':'子','丙':'寅','戊':'寅','丁':'卯','己':'卯','庚':'巳','辛':'午','壬':'申','癸':'酉'}.get(dc,""): noble.append("문곡귀인")
    if cur_j in {'甲':'子午','乙':'子午','丙':'卯酉','丁':'卯酉','戊':'辰戌丑未','己':'辰戌丑未','庚':'寅亥','辛':'寅亥','壬':'巳申','癸':'巳申'}.get(dc,""): noble.append("태극귀인")
    if cur_j in {'甲':'巳','乙':'午','丙':'巳','丁':'午','戊':'申','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}.get(dc,""): noble.append("천주귀인")
    if cur_j == mj: noble.append("월덕귀인")
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): noble.append("천록귀인")
    if cur_j in {'甲':'亥','乙':'午','丙':'寅','戊':'寅','丁':'酉','己':'酉','庚':'巳','辛':'子','壬':'申','癸':'卯'}.get(dc,""): noble.append("학당귀인")
    if cur_j in {'甲':'亥','乙':'戌','丙':'申','戊':'申','丁':'未','己':'未','庚':'巳','辛':'辰','壬':'寅','癸':'丑'}.get(dc,""): noble.append("암록")
    
    if gj in ["甲寅", "乙丑", "丙子", "丁酉", "戊申", "己未", "庚午", "辛巳", "壬辰", "癸卯"]: noble.append("복성귀인")
    
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): ausp.append("건록")
    if cur_j in {'甲':'辰','乙':'巳','丙':'未','戊':'未','丁':'申','己':'申','庚':'戌','辛':'亥','壬':'丑','癸':'寅'}.get(dc,""): ausp.append("금여록")
    if gj in ["甲辰", "乙巳", "庚戌", "辛亥"]: ausp.append("금여록")
    if gj in ["甲寅", "丙辰", "戊辰", "庚辰", "壬戌"]: ausp.append("일덕")
    if gj in ["乙丑", "己巳", "癸酉"] and idx in [0, 1]: ausp.append("금신")
    
    if gj in ["甲辰","乙未","丙戌","丁丑","戊辰","壬戌","癸丑"]: evil.append("백호대살")
    if gj in ["庚辰","庚戌","壬辰","壬戌","戊戌"]: evil.append("괴강살")
    if cur_j in {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子'}.get(dc,""): evil.append("양인살")
    
    if cur_j in {'甲':'酉','丙':'子','戊':'子','庚':'卯','壬':'午'}.get(dc,""): evil.append("비인살")
    if gj in ["丙子", "丁丑", "戊子", "己丑", "壬午", "癸未"]: evil.append("비인살")
    
    if dj == '寅' and cur_j in ['寅', '巳', '申']: evil.append("탕화살")
    if dj == '午' and cur_j in ['辰', '午', '丑']: evil.append("탕화살")
    if dj == '丑' and cur_j in ['午', '未', '戌']: evil.append("탕화살")
    
    if cur_g in ['甲', '辛'] or cur_j in ['卯', '午', '申', '未']: evil.append("현침살")
    if cur_j in ['卯','酉','戌'] and (jjis.count('卯') + jjis.count('酉') + jjis.count('戌')) >= 2: 
        evil.append("철쇄개금")
        
    if cur_g == cur_j: evil.append("간여지동")
    
    dohwa_map = {'寅':'卯', '午':'卯', '戌':'卯', '申':'酉', '子':'酉', '辰':'酉', '巳':'午', '酉':'午', '丑':'午', '亥':'子', '卯':'子', '未':'子'}
    if cur_j == dohwa_map.get(yj, "") or cur_j == dohwa_map.get(dj, ""): evil.append("도화살")
    if gj in ["甲午","丙寅","丁未","戊辰","庚戌","辛酉","壬子"]: evil.append("홍염살")
    if gj in ["甲寅","乙巳","丁巳","戊申","辛亥"]: evil.append("고란살")
    if cur_g in ['乙', '己'] or cur_j in ['巳', '丑']: evil.append("곡각살")
    if gj in ["丙子","丁丑","戊寅","辛卯","壬辰","癸巳","丙午","丁未","戊申","辛酉","壬戌","癸亥"]: evil.append("음양차착")
    if cur_j in ['子','午','卯','酉']: evil.append("교신성")
    if cur_j in ['辰','戌']: evil.append("평두")
    if cur_j in ['寅','申','巳','亥']: evil.append("효신살")
    if gj in ["甲辰","乙巳","丙申","丁亥","戊戌","己丑","庚辰","辛巳","壬申","癸亥"]: evil.append("퇴신")
    
    if idx == 1 and gj in ["丙子", "戊戌", "庚寅", "癸亥"]: evil.append("타뇌관살")
    if idx == 1 and gj in ["丙午", "丁未", "戊午", "戊子", "己未", "己丑"]: evil.append("육수살")
    if gj in ["甲寅", "甲申", "丁丑", "戊申", "己丑", "辛未", "壬寅", "癸未"]: evil.append("남연살")
    if gj in ["乙丑", "丙申", "丁丑", "己未", "庚寅", "辛未", "壬寅", "壬申"]: evil.append("여연살")
    if gj in ["甲寅", "乙卯", "丁未", "戊戌", "己未", "庚申", "辛酉", "癸丑"]: evil.append("음욕살")
    if gj in ["甲午", "丙戌", "戊辰", "庚辰", "壬戌", "乙巳", "丁亥", "己亥", "辛巳", "癸亥"]: evil.append("의처의부")

    result = []
    for n in list(dict.fromkeys(noble)): result.append(f"<span style='color:#0D47A1;'>{n}</span>")
    for a in list(dict.fromkeys(ausp)): result.append(f"<span style='color:#2E7D32;'>{a}</span>")
    for e in list(dict.fromkeys(evil)): result.append(f"<span style='color:#C62828;'>{e}</span>")
    return result

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
        else: 
            res += "<div style='flex-grow:1; display:flex; align-items:center; justify-content:center; background:#f9f9f9; width:95%; margin:0 auto; color:#bbb; border-radius:3px; border:1px dashed #ddd;'>-</div>"
    return res + "</div>"

def get_gyukgook_detailed(ds, ys, ms, hs, mb):
    if mb in ["子", "午", "卯", "酉"]:
        core_ss = get_ss(ds, mb)
        return core_ss + "격", f"월지 {mb}의 순수한 기운인 {core_ss}을 그대로 격으로 삼습니다."
    
    jg = JIJANGGAN.get(mb, [])
    if not jg: return "알수없음격", "지장간 정보가 없습니다."

    target_gans = [ys, ms, hs] 
    main_qi = jg[-1]
    
    if main_qi in target_gans:
        return get_ss(ds, main_qi) + "격", f"월지 {mb}의 정기(본기)인 {main_qi}이 천간에 투출하여 {get_ss(ds, main_qi)}격이 되었습니다."
    if len(jg) == 3 and jg[1] in target_gans:
        return get_ss(ds, jg[1]) + "격", f"월지 {mb}의 중기인 {jg[1]}이 천간에 투출하여 {get_ss(ds, jg[1])}격이 되었습니다."
    if jg[0] in target_gans:
        return get_ss(ds, jg[0]) + "격", f"월지 {mb}의 여기인 {jg[0]}이 천간에 투출하여 {get_ss(ds, jg[0])}격이 되었습니다."
    return get_ss(ds, main_qi) + "격", f"월지 {mb}의 지장간이 천간에 투출하지 않아, 정기(본기)인 {main_qi}를 기준으로 {get_ss(ds, main_qi)}격으로 정합니다."

def calculate_gongmang(ilgan, ilji):
    if ilgan in ["?"," ","-"] or ilji in ["?"," ","-"]: return "-"
    try:
        base = (list(JI).index(ilji) - list(GAN).index(ilgan) - 2) % 12
        return list(JI)[base] + "," + list(JI)[(base+1)%12]
    except: return "-"

def get_time_ganji(day_gan, time_str, dt_obj=None):
    if "시간 모름" in time_str: return "?", "?"
    if dt_obj:
        adj_mins = get_total_time_adjustment(dt_obj)
        dt_obj += dt_mod.timedelta(minutes=adj_mins)
    
    target_ji, t_idx = "子", 0
    if "朝子" in time_str or "夜子" in time_str: target_ji, t_idx = "子", 0
    else:
        for j in list(JI):
            if j in time_str: target_ji, t_idx = j, list(JI).index(j); break
    start_gan_idx = {"甲":0,"己":0,"乙":2,"庚":2,"丙":4,"辛":4,"丁":6,"壬":6,"戊":8,"癸":8}.get(day_gan, 0)
    return list(GAN)[(start_gan_idx + t_idx) % 10], target_ji

def get_daeun_su_accurate(utc_dt, order):
    try:
        sun = ephem.Sun()
        sun.compute(utc_dt)
        eq = ephem.Equatorial(sun.a_ra, sun.a_dec, epoch=utc_dt)
        lon = math.degrees(ephem.Ecliptic(eq).lon) % 360.0
        
        jeol_lons = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]
        
        if order == 1: 
            targets = [l for l in jeol_lons if l > lon] + [l + 360 for l in jeol_lons if l <= lon]
            t_lon = min(targets) % 360
        else: 
            targets = [l for l in jeol_lons if l <= lon] + [l - 360 for l in jeol_lons if l > lon]
            t_lon = max(targets) % 360
            
        search_dt = utc_dt
        step = dt_mod.timedelta(minutes=10) if order == 1 else dt_mod.timedelta(minutes=-10)
        
        for _ in range(6000):
            sun.compute(search_dt)
            eq_s = ephem.Equatorial(sun.a_ra, sun.a_dec, epoch=search_dt)
            l = math.degrees(ephem.Ecliptic(eq_s).lon) % 360.0
            if (order==1 and l>=t_lon and l-t_lon<180) or (order==-1 and l<=t_lon and t_lon-l<180): 
                break
            search_dt += step
            
        total_seconds = abs((search_dt - utc_dt).total_seconds())
        days_diff = total_seconds / 86400.0
        
        d_su = int(days_diff / 3)
        rem_days = days_diff % 3
        if rem_days >= 1.5:
            d_su += 1
            
        if d_su <= 0: d_su = 1
        if d_su > 10: d_su = 10
        return d_su
    except: 
        return 1

# ==============================================================================
# 3. [Ver 509.0 이식] 프리미엄 궁합 분석 엔진 클래스
# ==============================================================================
def get_group_ss(ss_str):
    return {'비견':'비겁', '겁재':'비겁', '식신':'식상', '상관':'식상', '편재':'재성', '정재':'재성', '편관':'관성', '정관':'관성', '편인':'인성', '정인':'인성'}.get(ss_str, '비겁')

class UniversalPrintableGunghap:
    def __init__(self, applicant, partner_name, male, female, daeun_score=10):
        self.app, self.p_name, self.daeun_score = applicant, partner_name, daeun_score
        male = [m if m and len(m) >= 2 else "  " for m in (list(male) + ["  ", "  ", "  ", "  "])][:4]
        female = [f if f and len(f) >= 2 else "  " for f in (list(female) + ["  ", "  ", "  ", "  "])][:4]
        self.m_g = [male[3][0], male[2][0], male[1][0], male[0][0]]
        self.m_j = [male[3][1], male[2][1], male[1][1], male[0][1]]
        self.f_g = [female[3][0], female[2][0], female[1][0], female[0][0]]
        self.f_j = [female[3][1], female[2][1], female[1][1], female[0][1]]
        self.logic_flags, self.details = {}, []

    def get_ji_rel(self, j1, j2):
        if not j1 or not j2 or j1=="?" or j2=="?": return "무"
        s = {j1, j2}
        if s in [{'子','丑'}, {'寅','亥'}, {'卯','戌'}, {'辰','酉'}, {'巳','申'}, {'午','未'}]: return "육합"
        if s in [{'寅','卯'}, {'卯','辰'}, {'寅','辰'}, {'巳','午'}, {'午','未'}, {'巳','未'}, {'申','酉'}, {'酉','戌'}, {'申','戌'}, {'亥','子'}, {'子','丑'}, {'亥','丑'}]: return "방합"
        if s in [{'申','子'}, {'子','辰'}, {'申','辰'}, {'寅','午'}, {'午','戌'}, {'寅','戌'}, {'亥','卯'}, {'卯','未'}, {'亥','未'}, {'巳','酉'}, {'酉','丑'}, {'巳','丑'}]: return "반합"
        if s in [{'子','午'}, {'丑','未'}, {'寅','申'}, {'卯','酉'}, {'辰','戌'}, {'巳','亥'}]: return "충"
        if s in [{'子','未'}, {'丑','午'}, {'寅','酉'}, {'卯','申'}, {'辰','亥'}, {'巳','戌'}]: return "원진"
        if s in [{'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}, {'子','卯'}]: return "형"
        if s in [{'子','酉'}, {'丑','辰'}, {'寅','亥'}, {'卯','午'}, {'巳','申'}, {'未','戌'}]: return "파"
        if s in [{'子','未'}, {'丑','午'}, {'寅','巳'}, {'卯','辰'}, {'申','亥'}, {'酉','戌'}]: return "해"
        return "무"

    def count_elements(self, gans, jjis):
        counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
        for c in gans + jjis:
            if c in "甲乙寅卯": counts['목'] += 1
            elif c in "丙丁巳午": counts['화'] += 1
            elif c in "戊己辰戌丑未": counts['토'] += 1
            elif c in "庚辛申酉": counts['금'] += 1
            elif c in "壬癸亥子": counts['수'] += 1
        return counts

    def run_universal_logic(self):
        m_g, m_j, f_g, f_j = self.m_g, self.m_j, self.f_g, self.f_j
        il_rel = self.get_ji_rel(m_j[1], f_j[1])
        
        if il_rel == "육합": s1 = 25
        elif il_rel in ["방합", "반합"]: s1 = 21
        elif il_rel == "무": s1 = 17
        elif il_rel in ["파", "해"]: s1 = 12
        elif il_rel in ["형", "원진"]: s1 = 8
        elif il_rel == "충": s1 = 5
        else: s1 = 17
        p1 = int((s1 / 25) * 100)

        s2 = 5 
        n_rel, w_rel, si_rel = self.get_ji_rel(m_j[3], f_j[3]), self.get_ji_rel(m_j[2], f_j[2]), self.get_ji_rel(m_j[0], f_j[0]) 
        if n_rel in ["육합", "방합", "반합"]: s2 += 2
        elif n_rel == "충": s2 -= 1
        if w_rel in ["육합", "방합", "반합"]: s2 += 2
        elif w_rel == "충": s2 -= 1
        if si_rel in ["육합", "방합", "반합"]: s2 += 1
        s2 = max(0, min(10, s2))
        p2 = int((s2 / 10) * 100)

        m_ec, f_ec = self.count_elements(m_g, m_j), self.count_elements(f_g, f_j)
        s3 = 5
        for e in ['목','화','토','금','수']:
            if m_ec[e] == 0 and f_ec[e] >= 2: s3 += 2 
            if f_ec[e] == 0 and m_ec[e] >= 2: s3 += 2 
            if m_ec[e] >= 4 and f_ec[e] >= 4: s3 -= 2 
        s3 = max(0, min(10, s3))
        p3 = int((s3 / 10) * 100)

        s4 = 5
        bad_iljus, goran, nache = ["甲寅", "乙卯", "庚申", "辛酉", "戊辰", "戊戌"], ["甲寅", "乙巳", "丁巳", "戊申", "辛亥"], ["甲子", "乙巳", "丁卯", "庚午", "辛亥", "癸酉"] 
        m_ilju, f_ilju = m_g[1] + m_j[1], f_g[1] + f_j[1]
        if m_ilju in bad_iljus or m_ilju in goran or m_ilju in nache: s4 -= 1
        if f_ilju in bad_iljus or f_ilju in goran or f_ilju in nache: s4 -= 1
        s4 = max(0, min(5, s4))
        p4 = int((s4 / 5) * 100)

        s5 = min(10, self.daeun_score)
        p5 = int((s5 / 10) * 100)

        risk = 0.0
        if il_rel == "충": risk += 0.10 
        elif il_rel in ["형", "원진"]: risk += 0.05 
        
        def count_ss_groups(dc, chars):
            res = {'비겁':0, '식상':0, '재성':0, '관성':0, '인성':0}
            for c in chars:
                if c and c not in ["?", " ", "-"]:
                    try:
                        ss = get_group_ss(get_ss(dc, c))
                        if ss in res: res[ss] += 1
                    except: pass
            return res
        
        m_ss, f_ss = count_ss_groups(m_g[1], m_g + m_j), count_ss_groups(f_g[1], f_g + f_j)
        if m_ss['비겁'] >= 4: risk += 0.05 
        if m_ss['재성'] == 0: risk += 0.05 
        if f_ss['식상'] >= 4: risk += 0.05 
        if f_ss['관성'] >= 4 or f_ss['관성'] == 0: risk += 0.05 

        risk = min(0.20, risk) 
        p6_safety = int((1.0 - risk) * 100)

        base_bonus = 40 
        sub_total = base_bonus + s1 + s2 + s3 + s4 + s5
        self.final_score = max(40, min(100, int(sub_total * (1.0 - risk))))

        if self.final_score >= 90: self.grade = "천생연분 (최고의 인연)"
        elif self.final_score >= 85: self.grade = "상생연분 (함께하면 좋은 인연)"
        elif self.final_score >= 80: self.grade = "동행연분 (편안하고 안정적인 인연)"
        elif self.final_score >= 70: self.grade = "보완연분 (서로를 채워주는 인연)"
        elif self.final_score >= 60: self.grade = "성장연분 (이해하며 맞춰가는 인연)"
        else: self.grade = "조율연분 (인내와 배려가 필요한 인연)"

        self.details = [
            {"label": "내면의 유대감", "pct": p1, "color": "#9b59b6"},
            {"label": "환경 조화", "pct": p2, "color": "#2ecc71"},
            {"label": "기운 상호보완", "pct": p3, "color": "#3498db"},
            {"label": "특수 기운", "pct": p4, "color": "#f1c40f"},
            {"label": "대운 조화", "pct": p5, "color": "#8e44ad"},
            {"label": "리스크 방어력", "pct": p6_safety, "color": "#e74c3c"}]

    def generate_ai_report(self, m_ctx, f_ctx):
        m_ec, f_ec = self.count_elements(self.m_g, self.m_j), self.count_elements(self.f_g, self.f_j)

        def get_patho(ec):
            w = []
            if ec['목'] >= 3: w.append("목다화식/토붕")
            if ec['화'] >= 3: w.append("화다토조/금용")
            if ec['토'] >= 3: w.append("토다금매/수색")
            if ec['금'] >= 3: w.append("금다수탁/목절")
            if ec['수'] >= 3: w.append("수다목표/화멸")
            return ", ".join(w) if w else "오행구족(조화)"

        m_patho, f_patho = get_patho(m_ec), get_patho(f_ec)
        f_map = {'甲':'본능','乙':'본능','丙':'감성','丁':'감성','戊':'수렴','己':'수렴','庚':'자율','辛':'자율','壬':'사고','癸':'사고'}
        m_psy, f_psy = f_map.get(m_ctx['dc'], '미상'), f_map.get(f_ctx['dc'], '미상')

        detail_scores_text = "\n".join([f"  * {d['label']}: {d['pct']}점" for d in self.details])

        prompt = f"""[SYSTEM ROLE: CHOYEON SIGONG MASTER]
당신은 명리심리상담사 '초연 박사'입니다. 아래 데이터를 바탕으로 교차 분석 궁합 에세이를 작성하십시오.

[🚨 중요 시스템 지시: 알고리즘 최종 점수 동기화]
시스템 로직이 엄격하게 산출한 두 사람의 '최종 궁합 점수는 {self.final_score}점'이며, 세부 항목은 다음과 같습니다.
{detail_scores_text}

당신이 작성하는 모든 분석(사주구조, 대운, 상생/조화 등)은 반드시 위 점수의 결과를 논리적으로 뒷받침해야 합니다.
- {self.final_score}점이 80점 이상이면: 극복 가능한 긍정적 인연임을 강조하십시오.
- {self.final_score}점이 60~79점이면: 장단점이 공존하여 뼈깎는 노력이 필요함을 객관적으로 서술하십시오.
- {self.final_score}점이 60점 미만이면: 가치관 충돌이나 시공의 부조화, 대운의 엇갈림을 명확히 지적하고, 매우 현실적이고 엄중한 처방을 내리십시오.
(※ 주의: 점수 숫자 자체는 본문에 절대 노출하지 마십시오.)

[남성({m_ctx['u_name']})]: 오행{m_ec}, 병리({m_patho}), 심리({m_psy}인자)
[여성({f_ctx['u_name']})]: 오행{f_ec}, 병리({f_patho}), 심리({f_psy}인자)

<div class='choyeon-premium-report' style='line-height:1.9;'>
  <h3 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 24px; font-weight: bold; color: #1B5E20; border-bottom: 3px double #1B5E20; padding-bottom: 10px; margin-top: 10px;'>🍀 두 사람의 운명적 만남에 대하여</h3>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(총평 서술)</p>
  
  <h4 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 20px; font-weight: bold; color: #1A237E; margin-top: 35px;'>🗝️ 커플의 사주팔자 비교 분석</h4>
  <div style='margin-top: 15px; margin-bottom: 10px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>▶ 음양오행과 사주구조</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(비교 분석 서술)</p>
  
  <div style='margin-top: 20px; margin-bottom: 10px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>▶ 자기 성향과 사회적 관계</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(성향 궁합 서술)</p>
  
  <div style='margin-top: 20px; margin-bottom: 10px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>▶ 시공의 충돌에 따른 삶의 변화</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(시공 변화 서술)</p>

  <h4 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 20px; font-weight: bold; color: #1A237E; margin-top: 40px;'>🌈 커플의 인생 기상도 분석</h4>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(심층 조언)</p>

  <h4 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 20px; font-weight: bold; color: #1A237E; margin-top: 40px;'>💞 커플의 상생과 조화 궁합 분석</h4>
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>[내면의 유대감] - 속 궁합</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(심도 있는 서술)</p>
  
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>[사회적 환경 조화] - 겉 궁합</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(호흡과 시너지 서술)</p>
  
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>[기운의 상호 보완] - 오행 궁합</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(상생 상극 서술)</p>

  <h4 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 20px; font-weight: bold; color: #1A237E; margin-top: 40px;'>⚓ 더 깊은 인연을 위한 조율의 지혜</h4>
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>[환경의 차이와 포용]</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(처방 서술)</p>
  
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>[에너지의 균형]</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(처방 서술)</p>
</div>
※ 엄격한 주의사항: 본문(<p>) 작성 시 'font-family' 속성을 임의로 추가하지 마십시오. 전체 글꼴이 파괴됩니다.
"""
        global model 
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"<div style='color:red;'>🚨 AI 서버 통신 장애가 발생했습니다.</div>"

    def get_graphic_html(self, ai_text):
        c = "#3498db" if self.final_score >= 70 else ("#f39c12" if self.final_score >= 60 else "#e74c3c")
        
        bars_html = ""
        for item in self.details:
            bars_html += f"""
            <div style='display:flex; align-items:center; margin-bottom:12px;'>
                <div style='width:130px; font-size:13px; font-weight:bold; color:#555;'>{item['label']}</div>
                <div style='flex:1; height:12px; margin:0 10px;'>
                    <svg width='100%' height='12' style='display:block;'>
                        <rect width='100%' height='12' rx='6' ry='6' fill='#eeeeee' />
                        <rect width='{item['pct']}%' height='12' rx='6' ry='6' fill='{item['color']}' />
                    </svg>
                </div>
                <div style='width:35px; font-size:12px; font-weight:bold;'>{item['pct']}%</div>
            </div>"""
        
        gunghap_closing = f"""
        <div style='margin-top: 40px; padding-top: 30px; page-break-inside: avoid;'>
            <p style='font-size: 15px; line-height: 1.8; color: #333; font-family: "Noto Serif KR", serif;'>
                &nbsp;&nbsp;&nbsp;&nbsp;두 분의 <b style='color:#1A237E;'>'만남'</b>은 결코 우연이 아닌, <b style='color:#1A237E;'>'셀 수 없이 많은 시간 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 
                사주팔자는 각자의 바코드지만, <b style='color:#1A237E;'>'궁합(宮合)'</b>은 두 바코드가 만나 그려내는 새로운 <b style='color:#1A237E;'>'하모니(harmonie)'</b>입니다.
            </p>
            <p style='font-size: 15px; line-height: 1.8; color: #333; margin-top: 10px; font-family: "Noto Serif KR", serif;'>
                &nbsp;&nbsp;&nbsp;&nbsp;서로의 다름을 이해하고 채워주는 든든한 <b style='color:#1A237E;'>'동반자'</b>가 되시기를 진심으로 기원하며, 
                두 분의 앞날에 늘 시공간의 축복이 가득하시길 소망합니다. 
            </p>
            <div style='text-align: right; margin-top: 25px;'>
                <span style='font-weight: 900; font-size: 16px; color: #1A237E; font-family: "Noto Serif KR", serif;'>- 초연 시공명리 연구소 드림 -</span>
            </div>
        </div>
        """

        return f"""
        <div class='report-page' style='padding:40px; background:#fff;'>
            <div style='text-align:center; border-bottom:4px double #3E2723; padding-bottom:15px; margin-bottom:30px;'>
                <h1 style='margin:0; color:#3E2723; font-family: "Malgun Gothic", sans-serif; font-weight: 900;'>💞 초연 시공명리 종합 궁합풀이</h1>
            </div>
            <div style='background-color: #FAFAFA; padding: 40px; border: 2px solid #1A237E; border-radius: 15px; margin-bottom: 40px; -webkit-box-decoration-break: clone; box-decoration-break: clone;'>
                <div class='content-box-loose' style='margin-bottom: 50px;'>
                    {ai_text}
                </div>
                <h2 style='text-align:center; margin-top:0; color:#333; font-family: "Malgun Gothic", sans-serif; font-weight: 900; font-size: 22px; margin-bottom: 25px;'>📊 최종 궁합 점수</h2>
                <div style='display:flex; justify-content:center; align-items:center; margin-bottom:20px;'>
                    <div style='width:130px; height:130px; border-radius:50%; background:conic-gradient({c} {self.final_score}%, #f0f0f0 0); display:flex; justify-content:center; align-items:center; -webkit-print-color-adjust: exact;'>
                        <div style='width:98px; height:98px; background:#fff; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
                            <span style='font-size:32px; font-weight:900; color:{c};'>{self.final_score}</span>
                            <span style='font-size:10px; color:#888; font-weight:bold;'>SCORE</span>
                        </div>
                    </div>
                </div>
                <div style='text-align:center; margin-bottom:25px;'>
                    <span style='font-size:16px; font-weight:bold; color:#fff; background:{c}; padding:8px 32px; border-radius:30px; display: inline-block; -webkit-print-color-adjust: exact;'>{self.grade}</span>
                </div>
                <div style='max-width:500px; margin:0 auto; margin-bottom: 20px;'>
                    {bars_html}
                </div>
                {gunghap_closing}
            </div>
        </div>"""

# ==============================================================================
# 4. 사이드바 UI
# ==============================================================================
with st.sidebar:
    st.title("🏮초연 시공명리 연구소")
    st.caption("Ver 16.0 Master (15.0 Base + 509 Gunghap)")
    
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
                klc_find = KoreanLunarCalendar(); found = False
                for y in range(2026, 1899, -1):
                    klc_find.setSolarDate(y, 7, 1); gj_y = klc_find.getChineseGapJaString().split()
                    if gj_y and gj_y[0][:2] == ry_h:
                        curr_dt = dt_mod.date(y+1, 2, 28)
                        while curr_dt >= dt_mod.date(y, 1, 1):
                            klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                            gj = klc_find.getChineseGapJaString().split()
                            if len(gj) >= 3 and gj[0][:2] == ry_h and gj[1][:2] == rm_h and gj[2][:2] == rd_h:
                                st.session_state.s_y, st.session_state.s_m, st.session_state.s_d = curr_dt.year, curr_dt.month, curr_dt.day
                                time_map_rev = {'子':'00:30 ~ 01:29 (朝子)시','丑':'01:30 ~ 03:29 (丑)시','寅':'03:30 ~ 05:29 (寅)시','卯':'05:30 ~ 07:29 (卯)시','辰':'07:30 ~ 09:29 (辰)시','巳':'09:30 ~ 11:29 (巳)시','午':'11:30 ~ 13:29 (午)시','未':'13:30 ~ 15:29 (未)시','申':'15:30 ~ 17:29 (申)시','酉':'17:30 ~ 19:29 (酉)시','戌':'19:30 ~ 21:29 (戌)시','亥':'21:30 ~ 23:29 (亥)시'}
                                if rt:
                                    ji_char = rt.replace("시","").replace(" ","")[-1]
                                    rt_h = K2H_JI.get(ji_char, ji_char)
                                    if rt_h in time_map_rev: st.session_state.s_t = time_map_rev[rt_h]
                                found = True
                                is_leap = getattr(klc_find, 'isIntercalary', False)
                                leap_str = "윤달" if is_leap else "평달"
                                st.success(f"✅ [양력] {curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일 / [음력] {klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일 ({leap_str}) 입력완료!")
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                        if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

    st.markdown("---")
    u_product = st.selectbox("📋 분석 상품 선택", ["개인사주", "궁합"])
    
    st.markdown("<div style='font-weight:900; color:#1A237E; margin-bottom:5px;'>👤 신청인 정보 (공통)</div>", unsafe_allow_html=True)
    u_name = st.text_input("이름", value="", placeholder="홍길동", key="u_n")
    u_gender = st.selectbox("성별", ["남성", "여성"], key="u_g")
    u_marital = st.selectbox("혼인여부", ["미혼", "기혼", "돌싱"], key="u_m_stat")
    u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")
    
    col1, col2, col3 = st.columns(3)
    u_y = col1.number_input("년", 1900, 2050, key="s_y")
    u_m = col2.number_input("월", 1, 12, key="s_m")
    u_d = col3.number_input("일", 1, 31, key="s_d")
    
    idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]
    u_t = st.selectbox("태어난 시간", idx_list, key="s_t")
    
    p_name, p_gender, p_marital, p_cal, p_y, p_m, p_d, p_t = "", "여성", "미혼", "양력", 1967, 9, 24, "시간 모름"
    if u_product == "궁합":
        st.markdown("---")
        st.markdown("<div style='font-weight:900; color:#C62828; margin-bottom:5px;'>💕 상대방 정보</div>", unsafe_allow_html=True)
        p_name = st.text_input("이름", value="", placeholder="이영희", key="p_n")
        p_gender_default = "여성" if u_gender == "남성" else "남성"
        p_gender = st.selectbox("성별", ["남성", "여성"], index=["남성", "여성"].index(p_gender_default), key="p_g")
        p_marital = st.selectbox("혼인여부", ["미혼", "기혼", "돌싱"], key="p_m_stat")
        p_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="p_c")
        
        p_col1, p_col2, p_col3 = st.columns(3)
        p_y = p_col1.number_input("년", 1900, 2050, value=1967, key="p_y_in")
        p_m = p_col2.number_input("월", 1, 12, value=9, key="p_m_in")
        p_d = p_col3.number_input("일", 1, 31, value=24, key="p_d_in")
        p_t = st.selectbox("태어난 시간", idx_list, key="p_t_key")
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_single = st.button("🚀 초연 시공명리 사주풀이 가동", use_container_width=True, type="primary")

# ==============================================================================
# 5. 분석 가동 및 출력 (스위치 분기)
# ==============================================================================
if btn_single:
    if not u_name.strip(): st.warning("⚠️ 신청인의 이름을 입력해 주세요.")
    elif u_product == "궁합" and not p_name.strip(): st.warning("⚠️ 상대방의 이름을 입력해 주세요.")
    else:
        spinner_msg = "초연 시공명리 사주풀이 분석 중..." if u_product == "개인사주" else "💕 두 분의 시공간을 교차하여 궁합을 분석 중입니다..."
        
        try:
            with open("/content/drive/MyDrive/choyeon-spacetime/choyeon_db.json", 'r', encoding='utf-8') as f:
                choyeon_db = json.load(f)
        except Exception as e:
            choyeon_db = {"wolryeong": {}, "ilju": {}}

        with st.spinner(spinner_msg):
            # ------------------------------------------------------------------
            # [공통 연산 - 신청인]
            # ------------------------------------------------------------------
            klc = KoreanLunarCalendar()
            if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
            elif u_cal == "음력(평달)": klc.setLunarDate(u_y, u_m, u_d, False)
            else: klc.setLunarDate(u_y, u_m, u_d, True)
            
            is_leap = getattr(klc, 'isIntercalary', False)
            leap_str = "윤달" if is_leap else "평달"
            
            sol_str = f"{klc.solarYear}년 {klc.solarMonth:02d}월 {klc.solarDay:02d}일"
            lun_str = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({leap_str})"
            
            curr_dt_sys = dt_mod.datetime.now()
            curr_y = curr_dt_sys.year
            curr_m = curr_dt_sys.month
            u_age = curr_y - u_y + 1
            
            base_y_idx = (curr_y - 1984) % 60
            curr_y_ganji = GAN[base_y_idx % 10] + JI[base_y_idx % 12]            
            gj = klc.getChineseGapJaString().split()
            ys, yb, ms, mb, ds, db = gj[0][0], gj[0][1], gj[1][0], gj[1][1], gj[2][0], gj[2][1]
            
            base_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0)
            hs, hb = get_time_ganji(ds, u_t, base_dt)
            gans, jjis = [hs, ds, ms, ys], [hb, db, mb, yb]
            
            time_str = f" {u_t.split('(')[0].strip()} ({hb})시" if u_t != "시간 모름" else ""
            
            def td(c, size="18px"): return f"<td class='color-{get_color(c)}' style='font-size:{size}; font-weight:900; border:1px solid #444 !important;'>{('?' if c in ['?',' ','-'] else c)}</td>"
            
            # ------------------------------------------------------------------
            # [모드 1] 개인사주 분석
            # ------------------------------------------------------------------
            if u_product == "개인사주":
                components.html(f"<div style='text-align:right;'><button style='background:#2E7D32; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-family:\"Noto Serif KR\", serif;' onclick='window.parent.print()'>🖨️ 초연 사주풀이 인쇄/PDF</button></div>", height=50)
                
                ji_rel_rows = ""
                for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                    b_bot = "1px solid #444 !important" if l_idx == 3 else "none !important"
                    cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:none !important; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                    lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top:none !important;'>합충형파해</td>" if l_idx==0 else ""
                    ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

                disp_name = u_name if u_name.strip() else "홍길동"
                info_h = f"<div style='text-align:center; margin-bottom:20px;'><span style='font-size:20px; font-weight:900; color:#1A237E;'>🏮 {disp_name}님 ({u_gender}, {u_marital}, {u_age}세)</span><br><span style='font-size:16px; color:#333; font-weight:900;'>[양력: {sol_str} | 음력: {lun_str}{time_str}]</span></div>"

                table_html = f"""<table class='result-table'>
                <tr class='top-header-cell'>
                <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>구분</span></td>
                <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>시주</span></td>
                <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>일주</span></td>
                <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>월주</span></td>
                <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>년주</span></td>
                </tr>
                <tr><td class='header-cell-main' style='border:1px solid #444;'>천간합충</td>{"".join([f"<td style='border:1px solid #444;'>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])}</tr>
                <tr><td class='header-cell-main' style='border:1px solid #444;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#D50000;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(ds,ms)}</td><td style='border:1px solid #444;'>{get_ss(ds,ys)}</td></tr>
                <tr><td class='header-cell-main' style='border:1px solid #444;'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
                <tr><td class='header-cell-main' style='border:1px solid #444;'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
                <tr><td class='header-cell-main' style='border:1px solid #444;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(ds,hb)}</td><td style='border:1px solid #444;'>{get_ss(ds,db)}</td><td style='border:1px solid #444;'>{get_ss(ds,mb)}</td><td style='border:1px solid #444;'>{get_ss(ds,yb)}</td></tr>
                <tr><td class='header-cell-main' style='padding:0; border:1px solid #444;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
                {ji_rel_rows}
                <tr><td class='header-cell-main' style='border:1px solid #444 !important;'>십이운성</td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
                <tr><td class='header-cell-main' style='border:1px solid #444 !important;'>십이신살</td>{"".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
                <tr><td class='header-cell-main' style='border:1px solid #444 !important;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis)) if get_general_shinsal_filtered(i, gans, jjis) else '-'}</td>" for i in range(4)])}</tr>
                </table>"""
                
                calc_gyukgook, gyukgook_detail = get_gyukgook_detailed(ds, ys, ms, hs, mb)

                gen_shinsal_list = []
                for i in range(4):
                    raw_tags = get_general_shinsal_filtered(i, gans, jjis)
                    for tag in raw_tags:
                        if ">" in tag and "<" in tag: gen_shinsal_list.append(tag.split('>')[1].split('<')[0])
                shinsal_str = ", ".join(list(dict.fromkeys(gen_shinsal_list))) if gen_shinsal_list else "특이 신살 없음"
                
                s12_list = [get_12_shinsal(yb, j) for j in jjis if get_12_shinsal(yb, j) != "-"]
                s12_str = ", ".join(list(dict.fromkeys(s12_list))) if s12_list else "특이 12신살 없음"
          
                samhyung_warn = ""
                has_in, has_sa, has_shin = '寅' in jjis, '巳' in jjis, '申' in jjis
                if sum([has_in, has_sa, has_shin]) == 2:
                    missing = [x for x, has in zip(['寅','巳','申'], [has_in, has_sa, has_shin]) if not has][0]
                    samhyung_warn += f"원국에 인사신 중 2글자가 있어 가형 상태입니다. 운에서 '{missing}'이 들어올 때 삼형살이 완성되니 주의 요망. "
                has_chuk, has_sul, has_mi = '丑' in jjis, '戌' in jjis, '未' in jjis
                if sum([has_chuk, has_sul, has_mi]) == 2:
                    missing = [x for x, has in zip(['丑','戌','未'], [has_chuk, has_sul, has_mi]) if not has][0]
                    samhyung_warn += f"원국에 축술미 중 2글자가 있어 가형 상태입니다. 운에서 '{missing}'이 들어올 때 삼형살이 완성되니 주의 요망. "
                if not samhyung_warn: samhyung_warn = "해당 없음"

                counts = {"목":0,"화":0,"토":0,"금":0,"수":0}
                for char in gans + jjis:
                    if char != "?": counts[get_color(char)] += 1
                
                guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
                guiin_str = guiin_map.get(ds, '없음')
                    
                adj_mins = get_total_time_adjustment(base_dt)
                utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
                order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
                direction_str = "순행" if order == 1 else "역행"
                calc_d = get_daeun_su_accurate(utc_dt, order)
                
                n_gong = calculate_gongmang(ys, yb)
                i_gong = calculate_gongmang(ds, db)
                
                master_bar_html = f"<div style='border:2px solid #3E2723; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap;'><div>⏳ 대운수: {calc_d}</div><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin_str}</div><div>🎯 공망: [년] {n_gong} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; [일] {i_gong}</div></div>"
                
                daewun_info = []
                un_html = f"<h3 style='color:#1A237E; margin-top:40px;'>11. 운의 흐름</h3><div style='margin-bottom:10px; font-weight:bold;'>[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(10):
                    val, c, j = i*10+calc_d, GAN[(GAN.index(ms)+(i+1)*order)%10] if ms in GAN else "-", JI[(JI.index(mb)+(i+1)*order)%12] if mb in JI else "-"
                    daewun_info.append(f"{val}세:{c}{j}")
                    is_active = val <= u_age < val+10
                    bg_col = "#FFF9C4" if is_active else "transparent"
                    b_left = "1px solid #ccc" if i != 9 else "none"
                    un_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{val}세</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,c)}</div><div class='color-{get_color(c)}' style='font-size:16px; font-weight:900;'>{c}</div><div class='color-{get_color(j)}' style='font-size:16px; font-weight:900;'>{j}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,j)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,j)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, j)}</div></div>"
                un_html += "</div>"
                daewun_info_str = ", ".join(daewun_info)

                cur_dw_idx = max(0, (u_age - calc_d) // 10)
                dw_g_cur = GAN[(GAN.index(ms) + (cur_dw_idx+1)*order)%10] if ms in GAN else "-"
                dw_j_cur = JI[(JI.index(mb) + (cur_dw_idx+1)*order)%12] if mb in JI else "-"
                current_daewun_age = cur_dw_idx * 10 + calc_d
                
                start_year = u_y + current_daewun_age - 1
                
                sewun_info = []
                se_html = f"<div style='margin-top:20px; margin-bottom:10px; font-weight:bold;'>[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(10):
                    ty = start_year + i
                    tage = current_daewun_age + i
                    base = (ty - 1984) % 60
                    tc, tj = GAN[base % 10], JI[base % 12]
                    sewun_info.append(f"{ty}년({tc}{tj})")
                    is_cur_yr = (ty == curr_y)
                    bg_col = "#E1F5FE" if is_cur_yr else "transparent"
                    b_left = "1px solid #ccc" if i != 9 else "none"
                    se_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; line-height:1.2; border-bottom:1px solid #ccc;'>{ty}년<br>({tage}세)</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div></div>"
                se_html += "</div>"
                sewun_info_str = ", ".join(sewun_info)

                wol_gans = ["己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚"]
                wol_jis = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]
                cur_wol_g = wol_gans[curr_m - 1]
                cur_wol_j = wol_jis[curr_m - 1]
                
                wol_html = f"<div style='margin-top:20px; margin-bottom:10px; font-weight:bold;'>[ 월운의 흐름 ({curr_y}년도 양력기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(12):
                    tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
                    is_cur_m = (tm == curr_m)
                    bg_col = "#E8F5E9" if is_cur_m else "transparent"
                    b_left = "1px solid #ccc" if i != 11 else "none"
                    wol_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{tm}월</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div></div>"
                wol_html += "</div>"
                
                closing_html = f"""<div style='margin-top: 30px;'>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드와 같지만, 우리가 살아가며 마주하는 스캐너인 운은 늘 변화하며 흐릅니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 초연 전통명리와의 인연이 <b>{disp_name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 나침반이 되기를 진심으로 기원합니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 전통명리의 지혜와 궁금증이 있으시면 언제든 초연 전통명리 연구소의 문을 두드려 주십시오.</p>
<p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
<div style='text-align: right; margin-top: 30px;'>
<span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
</div>
</div>"""

                age_prompt = ""
                if u_age < 20:
                    age_prompt = "내담자는 청소년기(10대)입니다. 학업 진학운과 부모 형제운을 최우선으로 상세히 분석하고 재물 사업운은 축소하십시오."
                elif 20 <= u_age < 40:
                    age_prompt = "내담자는 청년기(20~30대)입니다. 적성 직업운과 결혼 자녀운 등 사회적 자립과 혼인 과정을 상세히 통변하십시오."
                elif 40 <= u_age < 60:
                    age_prompt = "내담자는 중장년기(40~50대)입니다. 재성운과 관직 명예운에 집중하여 상세하게 서술하십시오."
                else:
                    age_prompt = "내담자는 노년기(60대 이상)입니다. 건강운 및 대운 세운 통변 시 건강 관리를 최우선으로 깊이 다루십시오."

                gender_prompt = ""
                if u_gender == "남성":
                    gender_prompt = "남성 내담자입니다. 배우자운(재성)과 자식운(관성)을 남명 이론에 입각하여 해석하십시오."
                else:
                    gender_prompt = "여성 내담자입니다. 배우자운(관성)과 자식운(식상)을 여명 이론에 입각하여 해석하십시오."

                # ==============================================================================
                # 🎯 [김집사 긴급 특단 조치] 외부 파일 로드를 폐기하고, 데이터를 코드 내부에 직접 이식
                # ==============================================================================
                choyeon_db = {
                  "wolryeong": {
                    "갑자(甲子)월": "천둥번개 우뢰(甲)가 꽁꽁 얼어붙은 검은 연못(子)의 정적을 거세게 깨우는 완연한 한겨울(甲子월)",
                    "을축(乙丑)월": "찬 바람(乙)이 꽁꽁 얼어붙은 버드나무 언덕(丑)을 매섭게 휘감아 도는 가장 추운 겨울(乙丑월)",
                    "병인(丙寅)월": "태양(丙)이 넓은 들판(寅)의 찬 기운을 녹이며 환히 비추는, 추위가 남아 있는 이른 봄(丙寅월)",
                    "정묘(丁卯)월": "영롱한 별빛(丁)이 옥 같이 아름다운 숲(卯)의 어둠을 밝히는 완연한 봄(丁卯월)",
                    "무진(戊辰)월": "노을(戊)이 풀이 우거진 늪지(辰) 위로 내려앉아 수분이 차오르는 봄과 여름의 환절기(戊辰월)",
                    "기사(己巳)월": "구름(己)이 큰 역(巳) 위로 머무르며 열기를 품기 시작하는 이른 여름(己巳월)",
                    "경오(庚午)월": "달빛(庚)이 횟불 신호대(午)의 정적 속에 고고하게 빛을 쏟아내는 완연한 여름(庚午월)",
                    "신미(辛未)월": "서리(辛)가 화원(未)의 열기를 식히지만 가장 무더운 여름(辛未월)",
                    "임신(壬申)월": "이슬(壬)이 대도시(申)의 마른 풀끝을 적시는 서늘한 가을의 시작(壬申월)",
                    "계유(癸酉)월": "봄비(癸)가 사찰의 종(酉)을 적시며 결실을 거두는 완연한 가을(癸酉월)",
                    "갑술(甲戌)월": "우뢰(甲)가 불태운 들판(戌)에 진동하며 결실을 저장하는 가을과 겨울의 환절기(甲戌월)",
                    "을해(乙亥)월": "바람(乙)이 쏟아지는 강물(亥) 위를 스치며 추위가 스며드는 이른 겨울(乙亥월)",
                    "병자(丙子)월": "태양(丙)이 검은 연못(子)을 비추는 깊어지는 한겨울(丙子월)",
                    "정축(丁丑)월": "별(丁)이 버드나무 언덕(丑)의 시린 어둠을 밝히는 가장 추운 겨울(丁丑월)",
                    "무인(戊寅)월": "노을(戊)이 들판(寅)을 온화하게 감싸 안는 이른 봄(戊寅월)",
                    "기묘(己卯)월": "구름(己)이 아름다운 숲(卯) 위를 감싸는 완연한 봄(己卯월)",
                    "경진(庚辰)월": "달빛(庚)이 우거진 늪지(辰) 위로 쏟아지는 봄과 여름의 환절기(庚辰월)",
                    "신사(辛巳)월": "서리(辛)가 큰 역(巳) 위로 내려앉는 이른 여름(辛巳월)",
                    "임오(壬午)월": "이슬(壬)이 횃불 신호대(午) 위로 맺히는 완연한 여름(壬午월)",
                    "계미(癸未)월": "봄비(癸)가 화원(未)을 적시는 가장 무더운 여름(癸未월)",
                    "갑신(甲申)월": "우뢰(甲)가 대도시(申)를 진동시키는 이른 가을(甲申월)",
                    "을유(乙酉)월": "바람(乙)이 사찰의 종(酉)을 울리는 완연한 가을(乙酉월)",
                    "병술(丙戌)월": "태양(丙)이 불태운 들판(戌)을 비추는 가을과 겨울의 환절기(丙戌월)",
                    "정해(丁亥)월": "별(丁)이 쏟아지는 강물(亥) 위를 밝히는 이른 겨울(丁亥월)",
                    "무자(戊子)월": "노을(戊)이 검은 연못(子)의 정적을 비추는 한겨울(戊子월)",
                    "기축(己丑)월": "구름(己)이 버드나무 언덕(丑)을 덮어주는 가장 추운 겨울(己丑월)",
                    "경인(庚寅)월": "달빛(庚)이 넓은 들판(寅)의 정적을 비추는 이른 봄(庚寅월)",
                    "신묘(辛卯)월": "서리(辛)가 아름다운 숲(卯)에 내리는 완연한 봄(辛卯월)",
                    "임진(壬辰)월": "이슬(壬)이 늪지(辰)를 적시는 봄과 여름의 환절기(壬辰월)",
                    "계사(癸巳)월": "봄비(癸)가 큰 역(巳) 위로 내리는 이른 여름(癸巳월)",
                    "갑오(甲午)월": "우뢰(甲)가 횃불 신호대(午)를 진동시키는 완연한 여름(甲午월)",
                    "을미(乙未)월": "바람(乙)이 화원(未) 위를 스치는 가장 무더운 여름(乙未월)",
                    "병신(丙申)월": "태양(丙)이 대도시(申)를 환히 비추는 이른 가을(丙申월)",
                    "정유(丁酉)월": "별(丁)이 사찰의 종(酉)을 은은히 비추는 완연한 가을(丁酉월)",
                    "무술(戊戌)월": "노을(戊)이 불태운 들판(戌)을 덮는 가을과 겨울의 환절기(戊戌월)",
                    "기해(己亥)월": "구름(己)이 쏟아지는 강물(亥) 위에 머무는 이른 겨울(己亥월)",
                    "경자(庚子)월": "달빛(庚)이 검은 연못(子)을 비추는 한겨울(庚子월)",
                    "신축(辛丑)월": "서리(辛)가 버드나무 언덕(丑)에 내리는 가장 추운 겨울(辛丑월)",
                    "임인(壬寅)월": "이슬(壬)이 들판(寅)을 적시는 이른 봄(壬寅월)",
                    "계묘(癸卯)월": "봄비(癸)가 아름다운 숲(卯)을 적시는 완연한 봄(癸卯월)",
                    "갑진(甲辰)월": "우뢰(甲)가 늪지(辰)를 진동시키는 봄과 여름의 환절기(甲辰월)",
                    "을사(乙巳)월": "바람(乙)이 큰 역(巳) 위를 스치는 이른 여름(乙巳월)",
                    "병오(丙午)월": "태양(丙)이 횟불 신호대(午)를 비추는 완연한 여름(丙午월)",
                    "정미(丁未)월": "영롱한 별빛(丁)이 화원(未)을 비추는 가장 무더운 여름(丁未월)",
                    "무신(戊申)월": "붉은 노을(戊)이 유명한 대도시(申)를 감싸는 이른 가을(戊申월)",
                    "기유(己酉)월": "포근한 구름(己)이 사찰의 종(酉) 위에 머무는 완연한 가을(己酉월)",
                    "경술(庚戌)월": "서늘한 달빛(庚)이 불태우는 근원(戌)을 비추는 가을과 겨울의 환절기(庚戌월)",
                    "신해(辛亥)월": "하얀 서리(辛)가 쏟아지는 강물(亥) 위에 내리는 이른 겨울(辛亥월)",
                    "임자(壬子)월": "가을이슬(壬)이 검은 연못(子)을 비추는 한겨울(壬子월)",
                    "계축(癸丑)월": "봄비(癸)가 버드나무 언덕(丑)을 적시는 가장 추운 겨울(癸丑월)",
                    "갑인(甲寅)월": "천둥번개 우뢰(甲)가 넓은 들판(寅)을 진동시키는 이른 봄(甲寅월)",
                    "을묘(乙卯)월": "바람(乙)이 옥 같이 아름다운 숲(卯)을 스치는 완연한 봄(乙卯월)",
                    "병진(丙辰)월": "태양(丙)이 풀이 우거진 늪지(辰)를 비추는 봄과 여름의 환절기(丙辰월)",
                    "정사(丁巳)월": "영롱한 별빛(丁)이 큰 역(巳)을 밝히는 이른 여름(丁巳월)",
                    "무오(戊午)월": "붉은 노을(戊)이 횟불 신호대(午)를 덮는 완연한 여름(戊午월)",
                    "기미(己未)월": "포근한 구름(己)이 화원(未) 위에 머무는 가장 무더운 여름(己未월)",
                    "경신(庚申)월": "서늘한 달빛(庚)이 유명한 대도시(申)를 비추는 이른 가을(庚申월)",
                    "신유(辛酉)월": "하얀 서리(辛)가 사찰의 종(酉) 위에 내리는 완연한 가을(辛酉월)",
                    "임술(壬戌)월": "가을이슬(壬)이 불태우는 근원(戌) 위에 맺히는 가을과 겨울의 환절기(壬戌월)",
                    "계해(癸亥)월": "봄비(癸)가 쏟아지는 강물(亥)을 적시는 이른 겨울(癸亥월)"
                  },
                  "ilju": {
                    "갑자(甲子)": "검은 연못(子) 위에 울려 퍼지는 우레(甲)의 형상",
                    "을축(乙丑)": "버드나무 언덕(丑)에 불어오는 바람(乙)의 형상",
                    "병인(丙寅)": "넓은 들판(寅)을 비추는 태양(丙)의 형상",
                    "정묘(丁卯)": "옥 같이 아름다운 숲(卯) 위에 떠있는 밤하늘 별(丁)의 형상",
                    "무진(戊辰)": "우거진 늪지(辰)에 드리워진 노을(戊)의 형상",
                    "기사(己巳)": "커다란 역(巳) 위에 떠도는 구름(己)의 형상",
                    "경오(庚午)": "봉화대(午) 위에 떠있는 밤하늘 달(庚)의 형상",
                    "신미(辛未)": "아름다운 화원(未) 위에 내려앉은 서리(辛)의 형상",
                    "임신(壬申)": "대도시(申)를 적시는 가을이슬(壬)의 형상",
                    "계유(癸酉)": "사찰의 종(酉) 위에 내리는 봄비(癸)의 형상",
                    "갑술(甲戌)": "불 태우는 근원(戌) 위에 울려 퍼지는 우레(甲)의 형상",
                    "을해(乙亥)": "거대한 강물(亥)에 불어오는 바람(乙)의 형상",
                    "병자(丙子)": "검은 연못(子)을 비추는 태양(丙)의 형상",
                    "정축(丁丑)": "버드나무 언덕(丑) 위에 떠있는 밤하늘 별(丁)의 형상",
                    "무인(戊寅)": "넓은 들판(寅) 위에 드리워진 노을(戊)의 형상",
                    "기묘(己卯)": "옥 같이 아름다운 숲(卯)에 떠도는 구름(己)의 형상",
                    "경진(庚辰)": "우거진 늪지(辰) 위에 떠있는 밤하늘 달(庚)의 형상",
                    "신사(辛巳)": "대도시(巳)에 내려앉은 서리(辛)의 형상",
                    "임오(壬午)": "봉화대(午)에 맺혀진 가을이슬(壬)의 형상",
                    "계미(癸未)": "아름다운 화원(未)을 적셔주는 봄비(癸)의 형상",
                    "갑신(甲申)": "대도시(申)에 울려 퍼지는 우레(甲)의 형상",
                    "을유(乙酉)": "사찰의 종(酉)을 스치는 바람(乙)의 형상",
                    "병술(丙戌)": "불 태우는 근원(戌)를 비추는 태양(丙)의 형상",
                    "정해(丁亥)": "거대한 강물(亥)를 비치는 밤하늘 별(丁)의 형상",
                    "무자(戊子)": "검은 연못(子) 위에 드리워진 노을(戊)의 형상",
                    "기축(己丑)": "버드나무 언덕(丑) 위에 떠도는 구름(己)의 형상",
                    "경인(庚寅)": "넓은 들판(寅)을 비추는 밤하늘 달(庚)의 형상",
                    "신묘(辛卯)": "옥 같이 아름다운 숲(卯) 위에 내려앉은 서리(辛)의 형상",
                    "임진(壬辰)": "우거진 늪지(辰) 위에 맺혀진 가을이슬(壬)의 형상",
                    "계사(癸巳)": "커다란 역(巳)을 적시는 봄비(癸)의 형상",
                    "갑오(甲午)": "봉화대(午) 위에 울려 퍼지는 우레(甲)의 형상",
                    "을미(乙未)": "아름다운 화원(未)에 불어오는 바람(乙)의 형상",
                    "병신(丙申)": "대도시(申)를 비추는 태양(丙)의 형상",
                    "정유(丁酉)": "사찰의 종(酉)을 비추는 밤하늘 별(丁)의 형상",
                    "무술(戊戌)": "불태우는 근원(戌) 위에 드리워진 노을(戊)의 형상",
                    "기해(己亥)": "거대한 강물(亥) 위를 떠도는 구름(己)의 형상",
                    "경자(庚子)": "검은 연못(子) 위에 떠있는 밤하늘 달(庚)의 형상",
                    "신축(辛丑)": "버드나무 언덕(丑) 위에 내리앉은 서리(辛)의 형상",
                    "임인(壬寅)": "넓은 들판(寅) 위에 맺혀진 가을이슬(壬)의 형상",
                    "계묘(癸卯)": "옥 같이 아름다운 숲(卯)을 적셔주는 봄비(癸)의 형상",
                    "갑진(甲辰)": "우거진 늪지(辰) 위에 울려 퍼지는 우레(甲)의 형상",
                    "을사(乙巳)": "커다란 역(巳)으로 불어오는 바람(乙)의 형상",
                    "병오(丙午)": "봉화대(午) 위에 떠있는 태양(丙)의 형상",
                    "정미(丁未)": "아름다운 화원(未)를 비추는 밤하늘 별(丁)의 형상",
                    "무신(戊申)": "대도시(申) 위에 드리워진 노을(戊)의 형상",
                    "기유(己酉)": "사찰의 종(酉) 위를 떠도는 구름(己)의 형상",
                    "경술(庚戌)": "불태우는 근원(戌) 위에 떠있는 밤하늘 달(庚)의 형상",
                    "신해(辛亥)": "거대한 강물(亥)에 내려앉은 서리(辛)의 형상",
                    "임자(壬子)": "검은 연못(子) 위로 맺혀진 가을이슬(壬)의 형상",
                    "계축(癸丑)": "버드나무 언덕(丑) 위에 내리는 진눈개비(癸)의 형상",
                    "갑인(甲寅)": "넓은 들판(寅) 위에 울려 퍼지는 우레(甲)의 형상",
                    "을묘(乙卯)": "옥 같이 아름다운 숲(卯)에 불어오는 바람(乙)의 형상",
                    "병진(丙辰)": "갯벌(辰) 위를 비추는 태양(丙)의 형상",
                    "정사(丁巳)": "커다란 역(巳)을 비추는 밤하늘 별(丁)의 형상",
                    "무오(戊午)": "봉화대(午)에 드리워진 노을(戊)의 형상",
                    "기미(己未)": "아름다운 화원(未) 위를 떠도는 구름(己)의 형상",
                    "경신(庚申)": "대도시(申) 위에 떠있는 밤하늘 달(庚)의 형상",
                    "신유(辛酉)": "사찰의 종(酉) 위에 내려 앉은 서리(辛)의 형상",
                    "임술(壬戌)": "불태우는 근원(戌) 위에 맺혀진 가을이슬(壬)의 형상",
                    "계해(癸亥)": "거대한 강물(亥) 위에 새차게 내리는 봄비(癸)의 형상"
                  }
                }

                # 2. 박사님의 변수(한자든 한글이든)를 오직 '한글'로만 통일하여 절대 실패하지 않게 만듭니다.
                C2H_MAP = {'甲':'갑','乙':'을','丙':'병','丁':'정','戊':'무','己':'기','庚':'경','辛':'신','壬':'임','癸':'계',
                           '子':'자','丑':'축','寅':'인','卯':'묘','辰':'진','巳':'사','午':'오','未':'미','申':'신','酉':'유','戌':'술','亥':'해'}

                # ms, mb, ds, db 변수 안전하게 한글로 통일
                w_gan_han = C2H_MAP.get(ms, ms)
                w_ji_han  = C2H_MAP.get(mb, mb)
                i_gan_han = C2H_MAP.get(ds, ds)
                i_ji_han  = C2H_MAP.get(db, db)

                # 3. 데이터 강제 추출
                w_core = "시공간 데이터를 찾지 못했습니다"
                for key, val in choyeon_db["wolryeong"].items():
                    if w_gan_han in key and w_ji_han in key:
                        w_core = val
                        break

                i_core = "데이터를 찾지 못했습니다"
                for key, val in choyeon_db["ilju"].items():
                    if i_gan_han in key and i_ji_han in key:
                        i_core = val
                        break

                # 4. 결과 출력용 황금 텍스트 조립
                choyeon_golden_text = f"""
<div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 16px; line-height: 1.8; color: #000000; margin-bottom: 20px;'>
    <p style='text-indent: 15px; margin-bottom: 0;'>
        <b>{disp_name}님</b>은 '{w_core}'의 시공간에서, '{i_core}'의 성품을 가지고 태어나셨습니다.
    </p>
</div>
"""

                # 🎯 5. 프롬프트 헤더 및 강력한 통제 명령 세팅
                db_header = (
                    f"[시스템 강제 시간 인식: 현재 시점은 {curr_y}년 {curr_m}월 입니다.]\n"
                    "당신은 명리심리상담사 1급 자격을 갖춘 초연 박사입니다. \n"
                    f"- 내담자 성함: {disp_name}\n"
                    f"- 나이 / 성별: {u_age}세 / {u_gender}\n"
                    f"- 혼인 여부: {u_marital}\n"
                    f"- 공망 팩트: [년주] {n_gong}, [일주] {i_gong}\n"
                )

                # 🚨 [김집사 긴급 방패] 대운 나이 변수가 없어서 발생하는 치명적 에러 원천 차단
                dw_start_age = locals().get('dw_start_age', 'OO')
                dw_mid_age   = locals().get('dw_mid_age', 'OO')
                dw_mid2_age  = locals().get('dw_mid2_age', 'OO')
                dw_end_age   = locals().get('dw_end_age', 'OO')

                prompt = f"""
{db_header}

[문단 통제 명령]
1. 모든 통변 에세이 문장은 반드시 p 태그로 감싸십시오.
2. 적절한 지점에서는 반드시 단락 나누기를 집행하십시오.
3. 🚨 모든 소목차(1), 2), ▶, •, ◈)에는 가독성을 위해 아래와 같이 폰트 크기(22px)를 강제하는 태그를 토씨 하나 틀리지 말고 적용하십시오!
   <span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>1) 겉으로 드러난 성격</span>
   <span class='sub-title' style='font-size: 22px; font-weight: 900; color: #111;'>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</span>
   <span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>• {dw_start_age}세~{dw_mid_age}세 대운:</span>
   <span class='sub-title' style='font-size: 22px; font-weight: 900; color: #111;'>◈ 나를 돕는 에너지와 색상:</span>
4. 별표 2개를 사용하여 글씨를 굵게 만드는 행위를 금지합니다.
5. 🚨 호칭 강제: 내담자를 지칭할 때는 오직 '{disp_name}님'만 사용하십시오. ('선생님', '당신' 절대 사용 금지)
6. 🚨 인사말 철저 금지: "안녕하십니까", "반갑습니다", "초연입니다" 등 쓸데없는 인사말이나 오지랖 멘트를 절대 작성하지 마십시오. 시작부터 바로 본론(사주 분석)으로 진입하십시오.
7. 🚨 전통명리 이론 기반 통변: AI가 임의로 지어내는 문학적 비유(예: 넓은 들판 등)를 철저히 금지합니다. 오직 사주 원국 간지의 물상 형상(예: 언 땅 위의 새싹 등) 등 정통 명리학 이론에 입각하여 이해하기 쉬운 구어체로 설명하십시오.

[내담자 맞춤형 정밀 타겟팅]
- {age_prompt}
- {gender_prompt}

[통변 지시]
- 모든 명리 용어는 대중이 이해하기 쉬운 현대적 구어체 표현 뒤에 괄호 형태로 병기하십시오.
- 간지 표기 시 반드시 한자로 표기하십시오.
- 격국 팩트: {gyukgook_detail}
- 공망 팩트: 년주 {n_gong}, 일주 {i_gong}
- 일반신살: {shinsal_str} / 12신살: {s12_str}

[출력 템플릿 - 절대 명령]
(※ 주의: [CHOYEON_GOLDEN_TEXT_HERE] 치환자는 절대 수정/삭제하지 말고 그대로 출력하십시오. 파이썬이 데이터를 강제 주입합니다.)
(※ 주의: 괄호로 묶인 '(※ AI 지시: ...)' 부분은 당신이 실제 분석 에세이로 교체하여 출력해야 하는 영역입니다.)
"""
                try:
                    res = model.generate_content(prompt)
                    ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                    
                    # 🎯 [핵심] 여기서 박사님의 원본 문장을 AI가 출력한 마커 위치에 강제 주입합니다!
                    ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)
                    
                    ai_text = ai_text.replace("[DAEWUN_TABLE_HERE]", un_html).replace("[SEWUN_TABLE_HERE]", se_html).replace("[WOLWUN_TABLE_HERE]", wol_html)
                    
                    if un_html not in ai_text:
                        ai_text = un_html + se_html + wol_html + "<div style='color:red;'>⚠️ 표 마커가 누락되었습니다.</div>" + ai_text

                    report_1_full_html = f"""<div class='report-page'>

<div class='vip-inset-frame' style='border-color:#1A237E;'>
<h1 style='text-align:center;'>🎯[초연 시공명리 사주풀이]</h1>
{info_h}
{table_html}
{master_bar_html}
<div style='margin-top:20px;'>
{ai_text}
{closing_html}
</div>
</div>
</div>"""
                    st.markdown(report_1_full_html, unsafe_allow_html=True)
                    
                except Exception as e: 
                    st.error(f"AI 연산 오류: {e}")

            # ------------------------------------------------------------------
            # [모드 2] 궁합 분석
            # ------------------------------------------------------------------
            elif u_product == "궁합":
                p_klc = KoreanLunarCalendar()
                if p_cal == "양력": p_klc.setSolarDate(p_y, p_m, p_d)
                elif p_cal == "음력(평달)": p_klc.setLunarDate(p_y, p_m, p_d, False)
                else: p_klc.setLunarDate(p_y, p_m, p_d, True)
                
                p_in_dt = dt_mod.datetime(p_klc.solarYear, p_klc.solarMonth, p_klc.solarDay, 12, 30)
                p_gj = p_klc.getChineseGapJaString().split()
                p_ys, p_yb, p_ms, p_mb, p_ds, p_db = p_gj[0][0], p_gj[0][1], p_gj[1][0], p_gj[1][1], p_gj[2][0], p_gj[2][1]
                try: p_hs, p_hb = get_time_ganji(p_ds, p_t, p_in_dt)
                except: p_hs, p_hb = "?", "?"
                
                m_pillars, f_pillars = ([hs, ds, ms, ys], [hb, db, mb, yb]), ([p_hs, p_ds, p_ms, p_ys], [p_hb, p_db, p_mb, p_yb])
                
                m_ctx = {'u_name': u_name, 'dc': ds}
                f_ctx = {'u_name': p_name, 'dc': p_ds}
                
                if u_gender == "여성":
                    m_pillars, f_pillars = f_pillars, m_pillars
                    m_ctx, f_ctx = f_ctx, m_ctx
                
                gh_engine = UniversalPrintableGunghap(u_name, p_name, m_pillars, f_pillars)
                gh_engine.run_universal_logic()
                
                def draw_saju_table(gans, jjis, name_str, title_str):
                    c_gans = "".join([f"<td class='color-{get_color(g)}' style='font-size:20px; font-weight:900;'>{g}</td>" for g in gans])
                    c_jjis = "".join([f"<td class='color-{get_color(j)}' style='font-size:20px; font-weight:900;'>{j}</td>" for j in jjis])
                    return f"""
                    <div style='margin-bottom: 20px;'>
                        <div style='font-size: 18px; font-weight: 900; color: #1A237E; margin-bottom: 5px;'>🏮 {title_str} : {name_str}님</div>
                        <table class='result-table' style='width: 100%;'>
                            <tr class='top-header-cell'><td>시주</td><td>일주</td><td>월주</td><td>년주</td></tr>
                            <tr>{c_gans}</tr>
                            <tr>{c_jjis}</tr>
                        </table>
                    </div>
                    """
                
                tables_html = "<div class='report-page'><div class='vip-inset-frame'>"
                tables_html += f"<div style='text-align:center; border-bottom:4px double #3E2723; padding-bottom:15px; margin-bottom:20px;'><h1 style='margin:0; color:#3E2723; font-weight: 900;'>🗝️ 두 사람의 사주 명조</h1></div>"
                if u_gender == '남성':
                    tables_html += draw_saju_table(gh_engine.m_g, gh_engine.m_j, u_name, "남명 원국")
                    tables_html += draw_saju_table(gh_engine.f_g, gh_engine.f_j, p_name, "여명 원국")
                else:
                    tables_html += draw_saju_table(gh_engine.m_g, gh_engine.m_j, p_name, "남명 원국")
                    tables_html += draw_saju_table(gh_engine.f_g, gh_engine.f_j, u_name, "여명 원국")
                tables_html += "</div></div>"
                
                try:
                    ai_text = gh_engine.generate_ai_report(m_ctx, f_ctx)
                    gunghap_html = gh_engine.get_graphic_html(ai_text)
                    
                    st.markdown(tables_html, unsafe_allow_html=True)
                    st.markdown(gunghap_html, unsafe_allow_html=True)
                    
                    print_btn_html = "<div class='no-print' style='text-align: center; margin: 40px 0;'><button onclick='window.focus(); window.print()' style='padding: 12px 35px; background-color: #3E2723; color: white; font-weight: 900; border-radius: 5px; cursor: pointer;'>궁합 감명서 인쇄 / PDF 저장</button></div>"
                    components.html(print_btn_html, height=100)
                except Exception as e:
                    st.error(f"궁합 AI 구동 실패 오류: {e}")
