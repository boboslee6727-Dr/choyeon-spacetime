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
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS 
# ==============================================================================
st.set_page_config(page_title="초연 전통명리 사주풀이 Ver 15.0", layout="wide")

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
    
    .content-box-loose { line-height: 1.8; font-size: 15px; text-align: justify; margin-bottom: 12px; }
    .content-box-loose p { margin-bottom: 12px; text-indent: 10px; } 
    
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
if 's_y' not in st.session_state: st.session_state.s_y = 2000
if 's_m' not in st.session_state: st.session_state.s_m = 1
if 's_d' not in st.session_state: st.session_state.s_d = 1
if 's_t' not in st.session_state: st.session_state.s_t = "시간 모름"

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
    
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): ausp.append("건록")
    if cur_j in {'甲':'辰','乙':'巳','丙':'未','戊':'未','丁':'申','己':'申','庚':'戌','辛':'亥','壬':'丑','癸':'寅'}.get(dc,""): ausp.append("금여록")
    if gj in ["甲寅", "丙辰", "戊辰", "庚辰", "壬戌"]: ausp.append("일덕")
    if gj in ["乙丑", "己巳", "癸酉"]: ausp.append("금신")
    
    if gj in ["甲辰","乙未","丙戌","丁丑","戊辰","壬戌","癸丑"]: evil.append("백호대살")
    if gj in ["庚辰","庚戌","壬辰","壬戌","戊戌"]: evil.append("괴강살")
    if cur_j in {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子'}.get(dc,""): evil.append("양인살")
    if cur_j in {'甲':'酉','丙':'子','戊':'子','庚':'卯','壬':'午'}.get(dc,""): evil.append("비인살")
    if cur_j in ['午','寅','丑']: evil.append("탕화살")
    if cur_g in ['甲','辛'] or cur_j in ['卯','午','申']: evil.append("현침살")
    if cur_j in ['卯','酉','戌']: evil.append("철쇄개금")
    if cur_g == cur_j: evil.append("간여지동")
    dohwa_map = {'寅':'卯', '午':'卯', '戌':'卯', '申':'酉', '子':'酉', '辰':'酉', '巳':'午', '酉':'午', '丑':'午', '亥':'子', '卯':'子', '未':'子'}
    if cur_j == dohwa_map.get(yj, "") or cur_j == dohwa_map.get(dj, ""): evil.append("도화살")
    if gj in ["甲午","丙寅","丁未","戊辰","庚戌","辛酉","壬子"]: evil.append("홍염살")
    if gj in ["甲寅","乙巳","丁巳","戊申","辛亥"]: evil.append("고란살")
    if cur_g in ['乙','己'] or cur_j in ['巳','丑']: evil.append("곡각살")
    if gj in ["丙子","丁丑","戊寅","辛卯","壬辰","癸巳","丙午","丁未","戊申","辛酉","壬戌","癸亥"]: evil.append("음양차착")
    if cur_j in ['子','午','卯','酉']: evil.append("교신성")
    if cur_j in ['辰','戌']: evil.append("평두")
    if cur_j in ['寅','申','巳','亥']: evil.append("효신살")
    if gj in ["甲辰","乙巳","丙申","丁亥","戊戌","己丑","庚辰","辛巳","壬申","癸亥"]: evil.append("퇴신")

    result = []
    for n in list(dict.fromkeys(noble)): result.append(f"<span style='color:#0D47A1;'>{n}</span>")
    for a in list(dict.fromkeys(ausp)): result.append(f"<span style='color:#2E7D32;'>{a}</span>")
    for e in list(dict.fromkeys(evil)): result.append(f"<span style='color:#C62828;'>{e}</span>")
    return result[:6]

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
    if mb in ["?", "-", " "]: return "알 수 없음", "월지를 알 수 없어 격국을 산출할 수 없습니다."
    raw = {'子':['壬','-','癸'],'丑':['癸','辛','己'],'寅':['戊','丙','甲'],'卯':['甲','-','乙'],'辰':['乙','癸','戊'],'巳':['戊','庚','丙'],'午':['丙','己','丁'],'未':['丁','乙','己'],'申':['戊','壬','庚'],'酉':['庚','-','辛'],'戌':['辛','丁','戊'],'亥':['戊','甲','壬']}.get(mb, ['-','-','-'])
    
    for idx in [2, 1, 0]:
        stem = raw[idx]
        if stem != '-' and stem in [ys, ms, hs]:
            gyuk = get_ss(ds, stem) + "격"
            detail = f"월지 {mb}의 지장간 중 {stem}({get_ss(ds, stem)})이 천간에 투출하여 성립된 {gyuk}"
            return gyuk, detail
    
    bon_stem = raw[2]
    gyuk = get_ss(ds, mb) + "격"
    detail = f"천간에 투출된 지장간이 없어 월지 본기(本氣)인 {bon_stem}를 그대로 취하여 성립된 {gyuk}"
    return gyuk, detail

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

# [Ver 15.0 수술] 대운수 계산 공식 완벽 수정 (ver 509.0과 일치 확인)
def get_daeun_su_accurate(utc_dt, order):
    try:
        sun = ephem.Sun()
        sun.compute(utc_dt)
        # [수술] 과거 날짜의 세차운동 오류를 잡기 위해 당해 연도(epoch of date) 기준 apparent 좌표로 정밀 변환
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
        
        # 정통 명리학 대운수 사사오입 규칙 엄격 적용
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
# 3. 사이드바 UI
# ==============================================================================
with st.sidebar:
    st.title("🧪 초연 임상 연구소")
    st.caption("Ver 15.0 Masterpiece")
    
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
    u_name = st.text_input("이름", value="", placeholder="홍길동")
    u_gender = st.selectbox("성별", ["남성", "여성"])
    u_marital = st.selectbox("혼인여부", ["미혼", "기혼", "돌싱"])
    
    u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"])
    col1, col2, col3 = st.columns(3)
    u_y = col1.number_input("년", 1900, 2030, key="s_y")
    u_m = col2.number_input("월", 1, 12, key="s_m")
    u_d = col3.number_input("일", 1, 31, key="s_d")
    idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]
    u_t = st.selectbox("태어난 시간", idx_list, key="s_t")
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_single = st.button("🚀 초연 전통명리 사주풀이", use_container_width=True, type="primary")
    
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
        spinner_msg = "두 감명서를 1:1 상세 비교 분석 중...." if btn_compare else "초연 전통명리 사주풀이(Ver 15.0) 분석 중..."
        
        with st.spinner(spinner_msg):
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
            
            # 올해의 간지 동적 계산 (1984년 甲子년 기준)
            base_y_idx = (curr_y - 1984) % 60
            curr_y_ganji = GAN[base_y_idx % 10] + JI[base_y_idx % 12]            
            gj = klc.getChineseGapJaString().split()
            ys, yb, ms, mb, ds, db = gj[0][0], gj[0][1], gj[1][0], gj[1][1], gj[2][0], gj[2][1]
            
            base_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0)
            hs, hb = get_time_ganji(ds, u_t, base_dt)
            gans, jjis = [hs, ds, ms, ys], [hb, db, mb, yb]
            
            time_str = f" {u_t.split('(')[0].strip()} ({hb})시" if u_t != "시간 모름" else ""
            
            components.html(f"<div style='text-align:right;'><button style='background:#2E7D32; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-family:\"Noto Serif KR\", serif;' onclick='window.parent.print()'>🖨️ {'3대 리포트 통합' if btn_compare else '초연 사주풀이'} 인쇄/PDF</button></div>", height=50)
            
            def td(c, size="18px"): return f"<td class='color-{get_color(c)}' style='font-size:{size}; font-weight:900; border:1px solid #444 !important;'>{('?' if c in ['?',' ','-'] else c)}</td>"
            
            ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444" if l_idx == 3 else "none"
                cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:none !important; border-bottom:{b_bot} !important; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important;'>합충형파해</td>" if l_idx==0 else ""
                ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

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
                samhyung_warn += f"원국에 인사신(寅巳申) 중 2글자가 있어 가형(假刑) 상태입니다. 운에서 '{missing}'이/가 들어올 때 삼형살이 완성되니 관재구설/수술수/배신에 강력히 주의 요망. "
            has_chuk, has_sul, has_mi = '丑' in jjis, '戌' in jjis, '未' in jjis
            if sum([has_chuk, has_sul, has_mi]) == 2:
                missing = [x for x, has in zip(['丑','戌','未'], [has_chuk, has_sul, has_mi]) if not has][0]
                samhyung_warn += f"원국에 축술미(丑戌未) 중 2글자가 있어 가형(假刑) 상태입니다. 운에서 '{missing}'이/가 들어올 때 삼형살이 완성되니 관재구설/수술수/배신에 강력히 주의 요망. "
            if not samhyung_warn: samhyung_warn = "해당 없음"

            counts = {"목":0,"화":0,"토":0,"금":0,"수":0}
            for char in gans + jjis:
                if char != "?": counts[get_color(char)] += 1
            
            guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
            guiin_str = guiin_map.get(ds, '없음')
                
            b_hr, b_mn = 12, 0
            if u_t != "시간 모름":
                try: 
                    b_hr = int(u_t.split(':')[0])
                    b_mn = 30 # 해당 시(時)의 중간값으로 정밀 보정
                except: pass
            
            # [사고모델 최종 수술] 음력 입력 시에도 천문 계산 기점은 변환된 실제 양력 날짜(klc.solarYear/Month/Day)로 완벽 동기화
            utc_dt = dt_mod.datetime(klc.solarYear, klc.solarMonth, klc.solarDay, b_hr, b_mn) - dt_mod.timedelta(hours=9)
            order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
            direction_str = "순행" if order == 1 else "역행"
            calc_d = get_daeun_su_accurate(utc_dt, order)
            
            n_gong = calculate_gongmang(ys, yb)
            i_gong = calculate_gongmang(ds, db)
            
            master_bar_html = f"<div style='border:2px solid #3E2723; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap;'><div>⏳ 대운수: {calc_d}</div><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin_str}</div><div>🎯 공망: [년] {n_gong} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; [일] {i_gong}</div></div>"
            
            daewun_info = []
            un_html = f"<h4 style='color:#1A237E; margin-top:20px;'>11. 운의 흐름</h4><div style='margin-bottom:10px; font-weight:bold;'>[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
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
            current_daewun_fact = f"{current_daewun_age}세 {dw_g_cur}{dw_j_cur}대운"
            
            start_year = u_y + current_daewun_age - 1
            
            sewun_info = []
            se_html = f"<div style='margin-top:20px; margin-bottom:10px; font-weight:bold;'>[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
            for i in range(10):
                ty = start_year + i
                tage = current_daewun_age + i
                base = (ty - 1984) % 60
                tc, tj = GAN[base % 10], JI[base % 12]
                sewun_info.append(f"{ty}년({tc}{tj})")
                is_cur_yr = (ty == 2026)
                bg_col = "#E1F5FE" if is_cur_yr else "transparent"
                b_left = "1px solid #ccc" if i != 9 else "none"
                se_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; line-height:1.2; border-bottom:1px solid #ccc;'>{ty}년<br>({tage}세)</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div></div>"
            se_html += "</div>"
            sewun_info_str = ", ".join(sewun_info)

            wol_gans = ["己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚"]
            wol_jis = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]
            cur_wol_g = wol_gans[curr_m - 1]
            cur_wol_j = wol_jis[curr_m - 1]
            
            wol_html = f"<div style='margin-top:20px; margin-bottom:10px; font-weight:bold;'>[ 월운의 흐름 (2026년도 양력기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
            for i in range(12):
                tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
                is_cur_m = (tm == curr_m)
                bg_col = "#E8F5E9" if is_cur_m else "transparent"
                b_left = "1px solid #ccc" if i != 11 else "none"
                wol_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{tm}월</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div></div>"
            wol_html += "</div>"
            
            closing_html = f"""<div style='margin-top: 30px;'>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자(命)'는 태어날 때 부여받은 변하지 않는 '바코드(bar-code)'와 같지만, 우리가 살아가며 마주하는 '스캐너(scanner)'인 '운(運)'은 늘 변화하며 흐릅니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 전통명리와의 인연'이 <b>{disp_name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 전통명리의 지혜와 궁금증이 있으시면 언제든 '초연 전통명리 연구소의 문'을 두드려 주십시오.</p>
<p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
<div style='text-align: right; margin-top: 30px;'>
<span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 전통명리 연구소 드림 -</span>
</div>
</div>"""

            age_prompt = ""
            if u_age < 20:
                age_prompt = "내담자는 [청소년기(10대)]입니다. '4. 학업·진학운'과 '3. 부모·형제운'을 최우선으로 가장 상세히 분석하고, 재성운(재물)/사업운은 간략히 축소하십시오."
            elif 20 <= u_age < 40:
                age_prompt = "내담자는 [청년기(20~30대)]입니다. '5. 적성·직업운'과 '6. 결혼·자녀운' 등 사회적 자립과 연애/혼인 과정을 상세히 통변하십시오."
            elif 40 <= u_age < 60:
                age_prompt = "내담자는 [중장년기(40~50대)]입니다. 인생의 황금기이므로 '9. 재성운(재물)'과 '8. 관직·명예운(사업/승진)'에 통변의 화력을 집중하여 가장 길고 상세하게 서술하십시오."
            else:
                age_prompt = "내담자는 [노년기(60대 이상 시니어)]입니다. '10. 건강운' 및 대운/세운 통변 시 노인성 질환, 관절, 혈관 예방 등 건강 관리를 최우선으로 깊이 다루고, 재산의 안정적 유지에 대해 상세히 통변하십시오."

            gender_prompt = ""
            if u_gender == "남성":
                gender_prompt = "내담자는 [남성]입니다. 육친 해석 시 재성(아내/재물)과 관성(자녀/사회적 명예)의 동태를 남성의 생애 주기와 가장의 역할에 맞춰 현실적으로 통변하십시오."
            else:
                gender_prompt = "내담자는 [여성]입니다. 육친 해석 시 식상(자녀/표현력)과 관성(남편/직장)의 조화를 중심으로 풀되, 현대 사회 여성의 독립적 사회 활동과 성취를 비중 있게 강조하십시오."

            dw_start_age = current_daewun_age
            dw_mid_age = current_daewun_age + 4
            dw_mid2_age = current_daewun_age + 5
            dw_end_age = current_daewun_age + 9
            
            past_months_html = "<p>▶ 지나온 각 과거 월운 요약</p>\n"
            for m in range(1, curr_m):
                g = wol_gans[m-1]
                j = wol_jis[m-1]
                if m == 1:
                    past_months_html += f"<p><b>- {curr_y}년 1월 ({g}{j}월: 작년도 하반기 연장선):</b> </p>\n"
                elif m == 2:
                    past_months_html += f"<p><b>- {curr_y}년 2월 ({g}{j}월: 새로운 시작):</b> </p>\n"
                else:
                    past_months_html += f"<p><b>- {curr_y}년 {m}월 ({g}{j}월):</b> </p>\n"

            # [Ver 13.32 수술] 환각 차단 및 정밀 룰 탑재 프롬프트
            prompt = f"""
[절대 규칙]
1. 현재 시스템 시간: {curr_y}년({curr_y_ganji}년) {curr_m}월({cur_wol_g}{cur_wol_j}월)
2. 응답의 첫 글자는 무조건 <h3 style='color:#1A237E;'>1. 사주팔자 구조 분석</h3> 으로 시작하십시오. (인사말 절대 금지)
3. 절대 들여쓰기를 하지 마십시오. 표(Table)는 절대 직접 그리지 마십시오.
4. [DAEWUN_TABLE_HERE] 등 마커는 파이썬 치환용이므로 절대 지우지 마십시오.
5. [강제] 응답의 모든 문장에서 '내담자'라는 단어 사용 절대 금지. 반드시 [{disp_name}님]을 사용하여 서술하십시오.

[🚨 3D 입체 통변 및 육친 강제 지시]
1번~11번 모든 항목은 평면적 해석을 금지하며, 반드시 [관계, 심리적 내면, 사회적 영역(직업/재물)] 3차원 관점을 융합하여 풀이하십시오.
현재 혼인 상태: '{u_marital}'. 절대 '육친적'이라는 단어를 쓰지 말고 "인간관계 측면에서 살펴보면" 등으로 순화하십시오.

[🔥 내담자 맞춤형 정밀 타겟팅 룰 (반드시 엄수)]
- {age_prompt}
- {gender_prompt}

[🌟 대중 친화적 하이브리드 통변 강제 지시]
- [천간 합/충 짝짓기 오류(환각) 절대 금지] 천간의 합(合)은 '甲己, 乙庚, 丙辛, 丁壬, 戊癸' 이고, 천간의 충(沖)은 '甲庚, 乙辛, 丙壬, 丁癸' 뿐입니다. 절대 '갑경합', '을기충' 등 글자 짝을 잘못 지어 명리학에 없는 거짓 용어를 지어내지 마십시오. 충(갈등/변화)의 상황에 합(合)이라는 단어를 쓰는 실수를 엄금합니다.
- 모든 명리 용어(십성, 신살, 묘유충 등)는 절대로 단독으로 쓰지 마십시오.
- 반드시 [대중이 이해하기 쉬운 현대적 구어체 표현] + (명리용어) 형태로 병기하십시오.
  예시) "가을의 서늘함과 봄의 생동감이 부딪히는 현상(卯酉충)"
- [한자 100% 표기 규칙] '甲목', '己토' ❌ -> 반드시 '甲木', '己土', '亥水', '甲庚충' 등 100% 한자(漢字)로 표기하십시오.
- [궁성 스토리텔링 강제] 합형충파해 설명 시 각 지지(자리)가 상징하는 육친과 의미를 엮어 풀이하십시오.
- [십이운성 3D 결합 강제] 십성(육친) 통변 시, 반드시 해당 기둥의 십이운성(十二運星)이 부여하는 에너지의 강약과 상태를 결합하여 입체적으로 통변하십시오. (예: 건록을 깔고 앉아 매우 왕성함)

[🚨 핵심 팩트 강제 지시]
- 격국(格局) 팩트: [{gyukgook_detail}] 
- 공망(空亡) 팩트: [년주: {n_gong}, 일주: {i_gong}] -> 년공망은 사회적/초년 결핍, 일공망은 개인적/배우자 결핍으로 나누어 설명하십시오.
- 부모운 특수 지시: 사주 원국에서 부모를 상징하는 기운이 약하거나 극을 받는다면, 이를 '초년 시절의 뼈아픈 상실이나 짊어져야 했던 삶의 무게' 등으로 통변에 깊이 녹여내십시오. (특정 나이는 언급 금지)
- 건강운 시작 전 지시: '10. 건강운'을 시작하기 전, 일반인이 이해하기 쉽게 오행(목화토금수)의 생극제화 원리(예: 나무는 간, 불은 심장 등)를 1~2줄로 비유적으로 먼저 설명하십시오.
- 일반신살: [{shinsal_str}] / 12신살: [{s12_str}]
  -> [환각 절대 금지] 오직 위 목록에 명시된 신살만 100% 팩트로 인정하여 통변에 활용하십시오. 사주 표에 없는 신살은 절대 언급하거나 지어내지 마시고, 신살의 '위치' 또한 임의로 꾸며내지 마십시오.
- [경계령] 분석 순서는 [합 ➡️ 형 ➡️ 충 ➡️ 파 ➡️ 해] 순서를 엄수.
- [과거 대운/세운/월운 전수 분석 및 3줄 요약 규칙] 과거 운을 분석할 때는 첫 번째 대운(1대운)부터 현재 직전 대운까지 단 하나의 시기도 임의로 건너뛰거나 누락하지 말고 반드시 모든 시기를 순서대로 전부 출력하십시오. 단, 출력 용량 초과로 인한 글 끊김 및 누락을 방지하기 위해, 각 시기별 풀이는 핵심 명리 작용(십성, 합형충파해)과 현실적 영향(직업, 건강, 심리 등)을 압축하여 '반드시 정확히 3줄(3문장)'로 명쾌하게 요약하여 서술하십시오.
- [과거 대운/세운/월운 전수 분석 및 3줄 요약 규칙] 과거 운을 분석할 때는 첫 번째 대운(1대운)부터 현재 직전 대운까지 단 하나의 시기도 임의로 건너뛰거나 누락하지 말고 반드시 모든 시기를 순서대로 전부 출력하십시오. 단, 출력 용량 초과로 인한 글 끊김 및 누락을 방지하기 위해, 각 시기별 풀이는 핵심 명리 작용(십성, 합형충파해)과 현실적 영향(직업, 건강, 심리 등)을 압축하여 '반드시 정확히 3줄(3문장)'로 명쾌하게 요약하여 서술하십시오.
★ [도트(•) 양식 및 문단 여백 엄수]: 웹 화면 깨짐 방지를 위해 아스테리스크(*, **) 기호를 절대 사용하지 마십시오. 줄 맨 첫 칸에 특수문자 도트(•)를 사용하고 한 칸 띄워 출력하되, **글자가 다닥다닥 붙어 출력되는 것을 막기 위해 반드시 하나의 대운 분석이 끝날 때마다 '엔터 두 번(빈 줄 한 칸)'을 입력하여 다음 대운과의 문단 간격을 여유 있게 띄워 출력하십시오.**
(출력 양식 예시)
• [시작나이]세~[종료나이]세 ([대운간지] 대운): [해당 시기의 명리 작용과 현실적 영향에 대한 3줄 요약 내용]
• [다음 시작나이]세~[다음 종료나이]세 ([다음 대운간지] 대운): [해당 시기의 명리 작용과 현실적 영향에 대한 3줄 요약 내용]
- [조언 및 개운비법 논리성 강제] '12. 삶을 바꾸는 지혜로운 조언'과 '개운 비법' 파트는 행운의 색상, 방위, 에너지(수호천사, 기운)를 추천할 때 반드시 '2) 조후/억부 용신'에서 분석된 나를 돕는 오행(용신)을 논리적 근거로 삼아 서술하십시오. 없는 기운을 임의로 지어내지 마십시오.
- 통변 시 가장 강조할 명리적 단어나 문구는 반드시 ' ' (작은따옴표)로 묶어 시각적으로 강조하십시오.
- [결혼 및 자녀운 신살 환각 절대 금지]: '6. 결혼·자녀운' 목차를 서술할 때, 앞서 제공된 사주 표의 신살 목록([{shinsal_str}], [{s12_str}])에 '백호대살'이 명시되어 있지 않다면 일지 未土 등의 글자만 보고 임의로 백호대살이나 괴강살이 자리하고 있다고 지어내어 소설 쓰는 것을 절대 금지합니다. 오직 제공된 진짜 팩트 데이터만 배우자궁 분석에 연결하십시오.

실제 대운 흐름: {daewun_info_str}
실제 세운 흐름: {sewun_info_str}
사주: {ys}{yb}년 {ms}{mb}월 {ds}{db}일 {hs}{hb}시

[출력 템플릿 - 이 목차명과 구조를 100% 동일하게 복사하여 출력할 것]
<h3 style='color:#1A237E;'>1. 사주팔자 구조 분석</h3>
<div class='content-box-loose'>
<p>1) 타고난 삶의 무대와 기본 성향 (격국)</p>
<p>2) 내 삶의 온도와 에너지 균형 (조후/억부/용신)</p>
<p>3) 사주팔자의 역동적 관계 분석 (합형충파해/진술축미)</p>
</div>
<h3 style='color:#1A237E;'>2. 성격</h3>
<div class='content-box-loose'>
<p>1) 겉으로 드러난 성격</p>
<p>2) 감추어진 진짜 속마음</p>
</div>
<h3 style='color:#1A237E;'>3. 부모·형제운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>4. 학업·진학운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>5. 적성·직업운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>6. 결혼·자녀운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>7. 사업운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>8. 관직·명예운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>9. 재성운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>10. 건강운</h3><div class='content-box-loose'></div>

[DAEWUN_TABLE_HERE]
<div class='content-box-loose'>
<p>▶ 지나온 각 과거 대운 분석</p>
<p>▶ 현재 대운 전반기 상세 분석 ({dw_start_age}세~{dw_mid_age}세)</p>
<p>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</p>
</div>
[SEWUN_TABLE_HERE]
<div class='content-box-loose'>
<p>▶ 지나온 각 과거 세운 분석</p>
<p>▶ 올해({curr_y}년 {curr_y_ganji}년) 세운 전반기(양력 2월~7월 말) 상세 분석</p>
<p>▶ 올해({curr_y}년 {curr_y_ganji}년) 세운 후반기(양력 8월~내년 1월 말) 상세 분석</p>
</div>
[WOLWUN_TABLE_HERE]
<div class='content-box-loose'>
{past_months_html}
<p>▶ 이번 달({curr_m}월 {cur_wol_g}{cur_wol_j}월) 전반기 (양력 5일~19일) 상세 분석</p>
<p>▶ 이번 달({curr_m}월 {cur_wol_g}{cur_wol_j}월) 후반기 (양력 20일~익월 4일) 상세 분석</p>
</div>

<h3 style='color:#1A237E; margin-top:30px;'>12. 삶을 바꾸는 지혜로운 조언</h3>
<div class='content-box-loose'>
<p><b>◈ 나를 돕는 에너지와 색상:</b></p>
<p><b>◈ 신체 밸런스와 에너지 관리:</b></p>
<p><b>◈ 공간의 흐름과 방위의 지혜:</b></p>
<p><b>◈ 재능 효율을 높이는 직업적 지혜:</b></p>
<p><b>◈ 더 나은 내일을 위한 절제의 미학:</b></p>
<div style='margin-top:20px; margin-bottom:10px;'><span style='color:#1A237E; font-weight:900;'>[초연 전통명리 특별 개운 비법]</span></div>
<p><b>◈ 수호 천사의 기운:</b></p>
<p><b>◈ 백년해로의 기운:</b></p>
<p><b>◈ 행운에 따른 기운:</b></p>
</div>
"""
            
            try:
                res = model.generate_content(prompt)
                ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                
                ai_text = ai_text.replace("[DAEWUN_TABLE_HERE]", un_html).replace("[SEWUN_TABLE_HERE]", se_html).replace("[WOLWUN_TABLE_HERE]", wol_html)
                
                if un_html not in ai_text:
                    ai_text = un_html + se_html + wol_html + "<div style='color:red;'>⚠️ AI가 템플릿 마커를 누락하여 표가 최상단에 출력되었습니다.</div>" + ai_text

                report_1_full_html = f"""<div class='report-page'>
<div class='vip-inset-frame' style='border-color:#1A237E;'>
<h1 style='text-align:center;'>🔬 [초연 전통명리 사주풀이]</h1>
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
                
                if btn_compare:
                    st.markdown(f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#3E2723;'><h2 style='text-align:center; color:#3E2723;'>📜 타 술사 감명서 원본 내역</h2><div class='content-box-loose' style='margin-top:20px;'>{comp_text.replace('\\n','<br>')}</div></div></div>", unsafe_allow_html=True)
                    
                    comp_prompt = f"""
[시스템 절대 규칙: 첫 글자는 무조건 대제목 <h3>로 시작. 들여쓰기 금지. 마크다운 기호 금지.]
타 술사 감명서를 1~11단계 목차에 맞춰 교차 대조.
타 술사의 '정적인 구조' 파악의 한계를 지적하고, 초연의 '동적 시뮬레이션(시기에 따른 실행분석)' 우위를 입증.
12번은 [12. 종합 의견]으로 총평.

대상 데이터: {comp_text}
"""
                    c_res = model.generate_content(comp_prompt)
                    c_ai_text = "\n".join([line.lstrip() for line in c_res.text.split("\n")])
                    st.markdown(f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#D50000;'><h2 style='text-align:center; color:#D50000;'>⚖️ 두 감명서 1:1 상세비교 리포트</h2><div class='content-box-loose' style='margin-top:20px;'>{c_ai_text}</div><div style='text-align:center; margin-top:50px; font-size:20px; font-weight:900;'>- 초연 임상 연구소 -</div></div></div>", unsafe_allow_html=True)
                        
            except Exception as e: 
                st.error(f"AI 연산 오류: {e}")
