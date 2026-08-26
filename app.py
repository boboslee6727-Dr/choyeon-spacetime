import streamlit as st
import pandas as pd
import json
import os
import math
import calendar
import datetime as dt_mod
from datetime import datetime
from korean_lunar_calendar import KoreanLunarCalendar
import ephem
from google import genai
import pytz
import streamlit.components.v1 as components
import re

# 🎯 [버전 컨트롤 타워]
APP_VERSION = "Ver 48.3"

# ==============================================================================
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS (ver 48.0 + ver 72.1/7.3 스타일 응용 통합 - 연녹색 유지)
# ==============================================================================
st.set_page_config(page_title=f"초연 전통 명리 {APP_VERSION}", layout="wide")

st.markdown("""<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800;900&display=swap');

    .stApp { background-color: #E8F5E9 !important; } /* 현재 연녹색 유지 */
    
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span[data-testid="stMarkdownContainer"] { 
        font-family: 'Nanum Gothic', sans-serif !important; 
    }

    div[data-testid="stSidebar"] * { font-size: 14px !important; }
    div[data-testid="stRadio"] label p { font-size: 14px !important; }
    div[data-testid="stCheckbox"] label p { font-size: 14px !important; }

    .report-page, .report-page *, .cover-page, div.cover-page *, .choyeon-premium-report, .result-table td { 
        font-family: 'Noto Serif KR', serif !important; 
    }

    .b-text { font-weight: 900 !important; color: #000000 !important; display: inline-block; }
    .b-text-red { font-weight: 900 !important; color: #D50000 !important; display: inline-block; }

    div.stButton > button { 
        font-family: 'Nanum Gothic', sans-serif !important; 
        font-weight: 900 !important; 
        font-size: 16px !important;
        border-radius: 8px !important;
        width: 100% !important;
    }

    /* Primary 버튼 (빨간색) */
    div.stButton > button[kind="primary"] { 
        background-color: #D50000 !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        height: 50px !important; 
        font-weight: 900 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #B71C1C !important;
        color: #FFFFFF !important;
    }

    /* Secondary 버튼 (인쇄/저장 - ver 7.3 원본 초록색 #00A843) */
    div.stButton > button[kind="secondary"] { 
        background-color: #00A843 !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        height: 50px !important;
        font-weight: 900 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08) !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #008937 !important;
        color: #FFFFFF !important;
    }

    .ai-title-l1 { font-size: 22px !important; font-weight: 900 !important; color: #000000 !important; margin-top: 35px !important; margin-bottom: 15px !important; border-bottom: 2px solid #000000 !important; padding-bottom: 5px !important; line-height: 1.4 !important; font-family: sans-serif !important; display: block !important; }
    .ai-title-l2 { font-size: 18px !important; font-weight: 900 !important; color: #000000 !important; margin-top: 22px !important; margin-bottom: 10px !important; line-height: 1.4 !important; font-family: sans-serif !important; display: block !important; }
    .vip-inset-frame { border: 2px solid #3E2723 !important; border-radius: 12px !important; padding: 30px 25px !important; background-color: #FFFFFF !important; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .ai-body-p { font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-justify: inter-character !important; text-indent: 1.0em !important; margin-bottom: 12px !important; word-break: break-all !important; }

    .color-목 { background: #2E7D32 !important; color: #FFF !important; }
    .color-화 { background: #C62828 !important; color: #FFF !important; }
    .color-토 { background: #F9A825 !important; color: #000 !important; }
    .color-금 { background: #9E9E9E !important; color: #FFF !important; }
    .color-수 { background: #212121 !important; color: #FFF !important; }

    .result-table { width: 100%; border-collapse: collapse !important; border: 3px solid #3E2723 !important; margin-bottom: 15px; table-layout: fixed; }
    .result-table td { border: 1px solid #444 !important; padding: 1px 0 !important; text-align: center; vertical-align: middle; font-weight: 900 !important; font-size: 13px; line-height: 1.2 !important; }
    .ganji-cell-24 { font-size: 24px !important; font-weight: 900 !important; }

    .top-header-cell { background-color: #1A237E !important; height: 30px !important; }
    .top-header-cell td { background-color: #1A237E !important; color: #FFFFFF !important; font-weight: 900 !important; font-size: 16px !important; border: 1px solid #444 !important; }
    .header-cell-main, .header-cell-sub { background-color: #E8EAF6 !important; color: #000000 !important; font-weight: 900 !important; font-size: 14px !important; }

    .report-page { width: 210mm; max-width: 100%; margin: 20px auto; background-color: #FFF !important; padding: 12mm 10mm; box-sizing: border-box; color: #000; }

    @media print { 
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; -webkit-print-color-adjust: exact !important; }
        .report-page { box-shadow: none; margin: 0 auto; page-break-after: always; width: 100%; padding: 0; }
    }
</style>""", unsafe_allow_html=True)

# ==============================================================================
# 0.5 [외부 choyeon_db.json 완벽 동적 연계]
# ==============================================================================
@st.cache_data
def load_choyeon_db():
    file_path = 'choyeon_db.json'
    if not os.path.exists(file_path):
        return {"wolryeong": {}, "ilju": {}, "ilju_structure": {}, "ilju_secret": {}, "ilju_full_master": {}}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"🚨 choyeon_db.json 파일 로드 오류: {e}")
        return {"wolryeong": {}, "ilju": {}, "ilju_structure": {}, "ilju_secret": {}, "ilju_full_master": {}}

choyeon_db = load_choyeon_db()

# ==============================================================================
# 1. 시스템 변수 세팅 및 써머타임 엔진
# ==============================================================================
def get_total_time_adjustment(dt):
    adj = -30
    if dt_mod.datetime(1954, 3, 21) <= dt <= dt_mod.datetime(1961, 8, 9, 23, 59): adj = 0
    si = [(dt_mod.datetime(1948,5,31), dt_mod.datetime(1948,9,22)), (dt_mod.datetime(1949,3,31), dt_mod.datetime(1949,9,30)), (dt_mod.datetime(1950,4,1), dt_mod.datetime(1950,9,10)), (dt_mod.datetime(1951,5,6), dt_mod.datetime(1951,9,9)), (dt_mod.datetime(1954,3,21), dt_mod.datetime(1954,5,5)), (dt_mod.datetime(1955,4,6), dt_mod.datetime(1955,9,22)), (dt_mod.datetime(1956,5,20), dt_mod.datetime(1956,9,30)), (dt_mod.datetime(1957,5,5), dt_mod.datetime(1957,9,22)), (dt_mod.datetime(1958,5,4), dt_mod.datetime(1958,9,21)), (dt_mod.datetime(1959,5,4), dt_mod.datetime(1959,9,20)), (dt_mod.datetime(1960,5,1), dt_mod.datetime(1960,9,18)), (dt_mod.datetime(1987,5,10,2), dt_mod.datetime(1987,10,11,3)), (dt_mod.datetime(1988,5,8,2), dt_mod.datetime(1988,10,9,3))]
    for s, e in si:
        if s <= dt <= e: adj -= 60; break
    return adj

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

def get_true_year_month_pillar(year, month, day, hour, minute):
    kst = pytz.timezone('Asia/Seoul')
    dt_kst = kst.localize(datetime(year, month, day, hour, minute))
    dt_utc = dt_kst.astimezone(pytz.utc)
    
    sun = ephem.Sun()
    sun.compute(dt_utc)
    lon = math.degrees(ephem.Ecliptic(sun).lon) % 360.0
    
    actual_year = year
    if month <= 2 and lon < 315.0:
        actual_year -= 1
        
    year_idx = (actual_year - 1984) % 60
    y_gan = GAN[year_idx % 10]
    y_ji = JI[year_idx % 12]
    
    if 315 <= lon < 345: m_ji_idx = 2
    elif 345 <= lon or lon < 15: m_ji_idx = 3
    elif 15 <= lon < 45: m_ji_idx = 4
    elif 45 <= lon < 75: m_ji_idx = 5
    elif 75 <= lon < 105: m_ji_idx = 6
    elif 105 <= lon < 135: m_ji_idx = 7
    elif 135 <= lon < 165: m_ji_idx = 8
    elif 165 <= lon < 195: m_ji_idx = 9
    elif 195 <= lon < 225: m_ji_idx = 10
    elif 225 <= lon < 255: m_ji_idx = 11
    elif 255 <= lon < 285: m_ji_idx = 0
    elif 285 <= lon < 315: m_ji_idx = 1
    
    y_gan_idx = year_idx % 10
    start_month_gan_idx = ((y_gan_idx % 5) * 2 + 2) % 10
    m_offset = (m_ji_idx - 2) % 12
    m_gan = GAN[(start_month_gan_idx + m_offset) % 10]
    
    return f"{y_gan}{y_ji}", f"{m_gan}{JI[m_ji_idx]}", lon

components.html("""
<script>
    const doc = window.parent.document;
    doc.addEventListener('keyup', function(e) {
        if (e.target.tagName !== 'INPUT' || e.target.type !== 'text') return;
        let label = e.target.getAttribute('aria-label') || "";
        if (label.includes('년주') || label.includes('월주') || label.includes('일주')) {
            if (e.isComposing) return;
            let val = e.target.value.trim();
            if (e.key === ' ' || e.key === 'Enter' || val.length >= 2) {
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
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    
    class GeminiModelCompat:
        def __init__(self, genai_client):
            self.client = genai_client
            
        def generate_content(self, contents, **kwargs):
            res = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents
            )
            return res

    model = GeminiModelCompat(client)

except Exception as _api_e:
    st.error(f"🚨 Gemini API 키 오류: {_api_e}")
    client = None
    model = None

def call_claude_api(prompt_text, max_tokens=8000):
    if client is None:
        return "<div style='color:red;'>🚨 Gemini 모델이 초기화되지 않았습니다. API 키를 확인하세요.</div>"
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_text
        )
        return response.text.strip()
    except Exception as e:
        return f"<div style='color:red;'>🚨 Gemini AI 서버 통신 장애: {e}</div>"

JIJANGGAN = {'子': ['壬', '-', '癸'], '丑': ['癸', '辛', '己'], '寅': ['戊', '丙', '甲'], '卯': ['甲', '-', '乙'], '辰': ['乙', '癸', '戊'], '巳': ['戊', '庚', '丙'], '午': ['丙', '己', '丁'], '未': ['丁', '乙', '己'], '申': ['戊', '壬', '庚'], '酉': ['庚', '-', '辛'], '戌': ['辛', '丁', '戊'], '亥': ['戊', '甲', '壬'] }

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

def get_samjae(year_ji, target_ji):
    if year_ji in ["?", " ", "-"] or target_ji in ["?", " ", "-"]: return "해당 없음"
    s_map = {
        '申': ['寅','卯','辰'], '子': ['寅','卯','辰'], '辰': ['寅','卯','辰'],
        '亥': ['巳','午','未'], '卯': ['巳','午','未'], '未': ['巳','午','未'],
        '寅': ['申','酉','戌'], '午': ['申','酉','戌'], '戌': ['申','酉','戌'],
        '巳': ['亥','子','丑'], '酉': ['亥','子','丑'], '丑': ['亥','子','丑']
    }
    sj_list = s_map.get(year_ji, [])
    if not sj_list: return "해당 없음"
    if target_ji == sj_list[0]: return "들삼재"
    elif target_ji == sj_list[1]: return "눌삼재"
    elif target_ji == sj_list[2]: return "날삼재"
    return "해당 없음"

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

def get_general_shinsal_filtered(idx, gans, jjis, gender="남성"):
    dc, mc, yc = gans[1], gans[2], gans[3]
    dj, mj, yj = jjis[1], jjis[2], jjis[3]
    cur_g, cur_j = gans[idx], jjis[idx]
    
    if cur_g in ["?", "-", " "] or cur_j in ["?", "-", " "]: return []
    gj = cur_g + cur_j
    noble, ausp, evil = [], [], []
    
    if cur_j in {'甲':'未丑','乙':'申子','丙':'酉亥','丁':'酉亥','戊':'未丑','己':'申子','庚':'未丑','辛':'午寅','壬':'卯巳','癸':'卯巳'}.get(dc,""): noble.append("천을귀인") 
    if cur_j == mj: noble.append("월덕귀인") 
    if cur_j in {'甲':'子午','乙':'子午','丙':'卯酉','丁':'卯酉','戊':'辰戌丑未','己':'辰戌丑未','庚':'寅亥','辛':'寅亥','壬':'巳申','癸':'巳申'}.get(dc,""): noble.append("태극귀인") 
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): noble.append("천록귀인") 
    if cur_j in {'甲':'巳','乙':'午','丙':'申','戊':'申','丁':'酉','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}.get(dc,""): noble.append("문창귀인")
    if cur_j in {'甲':'亥','乙':'子','丙':'寅','戊':'寅','丁':'卯','己':'卯','庚':'巳','辛':'午','壬':'申','癸':'酉'}.get(dc,""): noble.append("문곡귀인")
    if cur_j in {'甲':'亥','乙':'午','丙':'寅','戊':'寅','丁':'酉','己':'酉','庚':'巳','辛':'子','壬':'申','癸':'卯'}.get(dc,""): noble.append("학당귀인")
    if gj in ["甲寅", "乙丑", "丙子", "丁酉", "戊申", "己未", "庚午", "辛巳", "壬辰", "癸卯"]: noble.append("복성귀인")
    if cur_j in {'甲':'巳','乙':'午','丙':'巳','丁':'午','戊':'申','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}.get(dc,""): noble.append("천주귀인")
    
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): ausp.append("건록")
    if cur_j in {'甲':'亥','乙':'戌','丙':'申','戊':'申','丁':'未','己':'未','庚':'巳','辛':'辰','壬':'寅','癸':'丑'}.get(dc,""): noble.append("암록")
    if cur_j in {'甲':'辰','乙':'巳','丙':'未','戊':'未','丁':'申','己':'申','庚':'戌','辛':'亥','壬':'丑','癸':'寅'}.get(dc,""): ausp.append("금여록")
    if gj in ["甲寅", "丙辰", "戊辰", "庚辰", "壬戌"]: ausp.append("일덕")
    if gj in ["乙丑", "己巳", "癸酉"] and idx in [0, 1]: ausp.append("금신")
    hyeop_map = {'甲':['丑','卯'], '乙':['寅','辰'], '丙':['辰','午'], '戊':['辰','午'], '丁':['巳','未'], '己':['巳','未'], '庚':['未','酉'], '辛':['申','戌'], '壬':['戌','子'], '癸':['亥','丑']}
    if cur_j in hyeop_map.get(dc, []): ausp.append("협록")  
    
    if gj in ["甲辰","乙未","丙戌","丁丑","戊辰","壬戌","癸丑"]: evil.append("백호대살")
    if gj in ["庚辰","庚戌","壬辰","壬戌","戊戌"]: evil.append("괴강살")
    if cur_j in {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子'}.get(dc,""): evil.append("양인살")

    if cur_j in {'甲':'酉','乙':'戌','丙':'子','丁':'丑','戊':'子','己':'丑','庚':'卯','辛':'辰','壬':'午','癸':'未'}.get(dc,""): evil.append("비인살")
    if dj == '寅' and cur_j in ['寅', '巳', '申']: evil.append("탕화살")
    if dj == '午' and cur_j in ['辰', '午', '丑']: evil.append("탕화살")
    if dj == '丑' and cur_j in ['午', '未', '戌']: evil.append("탕화살")
    if cur_g in ['乙', '己'] or cur_j in ['巳', '丑']: evil.append("곡각살")
    if cur_g in ['甲', '辛'] or cur_j in ['卯', '午', '申', '未']: evil.append("현침살")

    if gj in ["甲寅", "乙卯", "丙午", "丁巳", "戊辰", "戊戌", "己未", "己丑", "庚申", "辛酉", "壬子", "癸亥"]: evil.append("간여지동")
    if gj in ["甲寅","乙巳","丁巳","戊申","辛亥"]: evil.append("고란살")
    if gj in ["丙子","丁丑","戊寅","辛卯","壬辰","癸巳","丙午","丁未","戊申","辛酉","壬戌","癸亥"]: evil.append("음양차착")
    if gj in ["甲午", "丙戌", "戊辰", "庚辰", "壬戌", "乙巳", "丁亥", "己亥", "辛巳", "癸亥"]: evil.append("의처의부")
    if cur_j in ['寅','申','巳','亥']: evil.append("효신살")

    dohwa_map = {'寅':'卯', '午':'卯', '戌':'卯', '申':'酉', '子':'酉', '辰':'酉', '巳':'午', '酉':'午', '丑':'午', '亥':'子', '卯':'子', '未':'子'}
    if cur_j == dohwa_map.get(yj, "") or cur_j == dohwa_map.get(dj, ""): evil.append("도화살")
    if gj in ["甲子", "乙巳", "丁卯", "庚午", "辛亥", "癸酉"]: evil.append("나체도화")
    if gj in ["甲午","丙寅","丁未","戊辰","庚戌","辛酉","壬子"]: evil.append("홍염살")
    if gj in ["甲寅", "乙卯", "丁未", "戊戌", "己未", "庚申", "辛酉", "癸丑"]: evil.append("음욕살")
    if gender == "여성" and gj in ["甲寅", "甲申", "丁丑", "戊申", "己丑", "辛未", "壬寅", "癸未"]: evil.append("남연살")
    if gender == "남성" and gj in ["乙丑", "丙申", "丁丑", "己未", "庚寅", "辛未", "壬寅", "壬申"]: evil.append("여연살")

    if cur_j in ['卯','酉','戌'] and (jjis.count('卯') + jjis.count('酉') + jjis.count('戌')) >= 2: evil.append("철쇄개금")
    if cur_j in ['子','午','卯','酉']: evil.append("교신성")
    if idx == 1 and gj in ["丙午", "丁未", "戊午", "戊子", "己未", "己丑"]: evil.append("육수살")
    if gj in ["甲辰","乙巳","丙申","丁亥","戊戌","己丑","庚辰","辛巳","壬申","癸亥"]: evil.append("십악대패살")
    if cur_g in ['甲', '丙', '壬'] and cur_j in ['子', '辰']: evil.append("평두살")
    cheolsa_map = {'甲':'辰', '乙':'寅', '丙':'戌', '丁':'申', '戊':'午', '己':'辰', '庚':'寅', '辛':'戌', '壬':'申', '癸':'午'}
    if cur_j == cheolsa_map.get(dc, ""): evil.append("철사관")

    if gj in ["甲子", "甲午", "己卯", "己酉"]: ausp.append("진신") 
    if gj in ["丙子", "丙午", "辛卯", "辛酉"]: evil.append("교신") 
    if gj in ["丁丑", "丁未", "壬辰", "壬戌"]: evil.append("퇴신") 
    if gj in ["戊寅", "戊申", "癸巳", "癸亥"]: ausp.append("복신") 

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

def check_vault_status(base_gans, base_jjis, attacker_ji):
    vaults = ['辰', '戌', '丑', '未']
    clash_map = {'辰':'戌', '戌':'辰', '丑':'未', '未':'丑'}
    hyung_sets = [{'丑','戌'}, {'戌','未'}, {'丑','未'}]
    core_gans = {'辰':['壬','癸'], '戌':['丙','丁'], '丑':['庚','辛'], '未':['甲','乙']}
    
    results = []
    for i, ji in enumerate(base_jjis):
        if ji in vaults:
            if clash_map.get(ji) == attacker_ji or {ji, attacker_ji} in hyung_sets:
                targets = core_gans.get(ji, [])
                is_trapped = any(g in targets for g in base_gans)
                if is_trapped:
                    trapped_chars = [g for g in targets if g in base_gans]
                    results.append(f"🚨 <b style='color:#C62828;'>[입고(入庫) 주의]</b> {ji} 무덤이 열려 천간의 {','.join(trapped_chars)} 기운이 빨려 들어갑니다.")
                else:
                    results.append(f"💎 <b style='color:#2E7D32;'>[개고(開庫) 발현]</b> {ji} 금고가 열려 지장간의 숨은 보물이 세상에 드러납니다.")
    return results

def get_gyukgook_detailed(ds, ys, ms, hs, mb):
    jg = JIJANGGAN.get(mb, [])
    if not jg: return "알수없음격", "지장간 정보가 없습니다."

    def safe_get_ss(day_gan, target_char):
        if not target_char or target_char == "?": return "무명"
        return get_ss(day_gan, target_char)

    if ds in ['甲', '丙', '戊', '庚', '壬']:
        if mb == '卯' and ds == '甲': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == '午' and ds == '丙': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == '酉' and ds == '庚': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == '子' and ds == '壬': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == {'甲':'寅', '丙':'巳', '戊':'巳', '庚':'申', '壬':'亥'}.get(ds, ""):
            return "건록격", f"월지 {mb}가 일간 {ds}의 건록(建祿)에 해당하여 건록격으로 정합니다."

    if mb in ["子", "午", "卯", "酉"]:
        core_ss = safe_get_ss(ds, mb)
        if core_ss in ["비견", "겁재"]:
            return "건록(월겁)격", f"월지 {mb}가 일간 {ds}와 같은 기운이므로 건록(월겁)격으로 삼습니다."
        return core_ss + "격", f"월지 {mb}의 순수한 기운인 {core_ss}을 그대로 격으로 삼습니다."
    
    target_gans = [ys, ms, hs] 
    main_qi = jg[-1] 
    
    def is_valid_gyuk(char):
        return safe_get_ss(ds, char) not in ["비견", "겁재"]
    
    if main_qi in target_gans and is_valid_gyuk(main_qi):
        return safe_get_ss(ds, main_qi) + "격", f"월지 {mb}의 정기(본기)인 {main_qi}이 천간에 투출하여 {safe_get_ss(ds, main_qi)}격이 되었습니다."
    if len(jg) >= 2 and jg[1] in target_gans and is_valid_gyuk(jg[1]):
        return safe_get_ss(ds, jg[1]) + "격", f"월지 {mb}의 중기인 {jg[1]}이 천간에 투출하여 {safe_get_ss(ds, jg[1])}격이 되었습니다."
    if len(jg) >= 1 and jg[0] in target_gans and is_valid_gyuk(jg[0]):
        return safe_get_ss(ds, jg[0]) + "격", f"월지 {mb}의 여기인 {jg[0]}이 천간에 투출하여 {safe_get_ss(ds, jg[0])}격이 되었습니다."
        
    fallback_ss = safe_get_ss(ds, main_qi)
    if fallback_ss in ["비견", "겁재"]:
        return "건록(월겁)격", f"월지 {mb}의 본기가 {fallback_ss}이므로 건록(월겁)격으로 정합니다."
    
    return fallback_ss + "격", f"월지 {mb}의 지장간이 투출하지 않아 정기(본기)인 {main_qi}를 기준으로 {fallback_ss}격으로 정합니다."

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
        def get_lon(dt):
            sun.compute(dt)
            return math.degrees(ephem.Ecliptic(sun).lon) % 360.0

        start_lon = get_lon(utc_dt)
        jeol_lons = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]
        
        if order == 1:
            t_lon_unwrapped = min([l for l in jeol_lons if l > start_lon] + [l + 360 for l in jeol_lons if l <= start_lon])
        else:
            t_lon_unwrapped = max([l for l in jeol_lons if l <= start_lon] + [l - 360 for l in jeol_lons if l > start_lon])
            
        search_dt = utc_dt
        step = dt_mod.timedelta(minutes=10) if order == 1 else dt_mod.timedelta(minutes=-10)
        
        for _ in range(6000):
            search_dt += step
            curr_lon = get_lon(search_dt)
            
            if order == 1 and curr_lon < start_lon and (start_lon - curr_lon) > 180:
                curr_lon += 360
            elif order == -1 and curr_lon > start_lon and (curr_lon - start_lon) > 180:
                curr_lon -= 360
                
            if (order == 1 and curr_lon >= t_lon_unwrapped) or (order == -1 and curr_lon <= t_lon_unwrapped):
                break
                
        total_days = abs((search_dt - utc_dt).total_seconds()) / 86400.0
        d_su = int(round(total_days / 3.0))
        
        if d_su == 0: d_su = 1
        elif d_su > 10: d_su = 10
        
        return d_su
    except Exception as e: 
        return 1

def get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, forbidden_list):
    results = []
    curr_date = start_date
    while curr_date <= end_date:
        score = 80 
        results.append({'date': curr_date.strftime('%Y-%m-%d'), 'score': score})
        curr_date += dt_mod.timedelta(days=1)
        
    return sorted(results, key=lambda x: x['score'], reverse=True)[:5]

# ==============================================================================
# 3. 프리미엄 궁합 분석 엔진 클래스
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

    def get_vault_harmony(self, base_gans, base_jjis, partner_jjis):
        results = []
        for p_ji in partner_jjis:
            results.extend(check_vault_status(base_gans, base_jjis, p_ji))
        return results

    def get_johoo_harmony(self, m_ilgan, m_ec, f_ec):
        score = 0
        if m_ilgan in "丙丁":
            if f_ec['수'] >= 2: score += 5
        elif m_ilgan in "壬癸":
            if f_ec['화'] >= 2: score += 5
        return score

    def run_universal_logic(self):
        m_g, m_j, f_g, f_j = self.m_g, self.m_j, self.f_g, self.f_j
        il_rel = self.get_ji_rel(m_j[2], f_j[2])
        
        if il_rel == "육합": s1 = 25
        elif il_rel in ["방합", "반합"]: s1 = 21
        elif il_rel == "무": s1 = 17
        elif il_rel in ["파", "해"]: s1 = 12
        elif il_rel in ["형", "원진"]: s1 = 8
        elif il_rel == "충": s1 = 5
        else: s1 = 17
        p1 = int((s1 / 25) * 100)

        s2 = 5 
        n_rel, w_rel, si_rel = self.get_ji_rel(m_j[0], f_j[0]), self.get_ji_rel(m_j[1], f_j[1]), self.get_ji_rel(m_j[3], f_j[3]) 
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
        m_ilju, f_ilju = m_g[2] + m_j[2], f_g[2] + f_j[2]
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
        
        m_ss, f_ss = count_ss_groups(m_g[2], m_g + m_j), count_ss_groups(f_g[2], f_g + f_j)
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
            {"label": "대운 기상도 조화", "pct": p5, "color": "#8e44ad"},
            {"label": "리스크 방어력", "pct": p6_safety, "color": "#e74c3c"}
        ]

# ==============================================================================
# 4. 사이드바 UI (상담 분야 선택 최상단 재배열 버전)
# ==============================================================================
with st.sidebar:
    st.title("🏮초연 전통명리 연구소")
    st.caption(f"{APP_VERSION}")
    st.markdown("---")

    # ==============================================================
    # 1. 📋 상담 분야 선택 (최상단 배치)
    # ==============================================================
    main_category = st.selectbox(
        "📋 상담 분야 선택", 
        [
            "1. 개인 사주팔자 풀이 (종합)", 
            "2. 테마별 특성화 상담", 
            "3. 커플 연애/결혼운 (궁합) 풀이", 
            "4. 타 감명서 비교"
        ], 
        key="main_category"
    )

    u_product = "1-1. 사주팔자 및 대운 분석"

    if main_category == "1. 개인 사주팔자 풀이 (종합)":
        u_product = st.radio(
            "상세 분석 항목:", 
            [
                "1-1. 사주팔자 및 대운 분석", 
                "1-2. 올해 및 특정연도 운세 상세분석", 
                "1-3. 이번달 및 특정월 운세 상세분석", 
                "1-4. 특정 주간 및 특정일운 상세분석"
            ], 
            key="sub_category_1"
        )
    elif main_category == "2. 테마별 특성화 상담":
        u_product = st.radio(
            "특성화 상품 선택:", 
            [
                "2-1. 재물운 특화 분석", 
                "2-2. 직업/진학운 특화 분석", 
                "2-3. 연애/결혼운 특화 분석", 
                "2-4. 건강운 특화 분석", 
                "2-5. 이사 및 방위 특화 분석"
            ], 
            key="sub_category_2"
        )
    elif main_category == "3. 커플 연애/결혼운 (궁합) 풀이":
        u_product = st.radio(
            "상세 분석 항목:", 
            [
                "3-1. 연애/결혼운 (궁합) 풀이", 
                "3-2. 결혼 택일", 
                "3-3. 출산 택일"
            ], 
            key="sub_category_3"
        )
    else:
        u_product = st.radio(
            "비교 분석 대상:", 
            [
                "4-1. 타 감명서 비교 (사주)", 
                "4-2. 타 감명서 비교 (궁합)"
            ], 
            key="sub_category_4"
        )

    st.markdown("---")

    # ==============================================================
    # 2. 🔍 신청인 사주팔자 역산 검색
    # ==============================================================
    with st.expander("🔍 사주팔자 역산 검색", expanded=False):
        col_g1, col_g2 = st.columns(2)
        with col_g1: ry = st.text_input("년주", value="", key="u_ry_rev")
        with col_g2: rm = st.text_input("월주", value="", key="u_rm_rev")
        col_g3, col_g4 = st.columns(2)
        with col_g3: rd = st.text_input("일주", value="", key="u_rd_rev")
        with col_g4: rt = st.text_input("시주", value="", key="u_rt_rev")
        
        K2H_GAN = {'갑':'甲','을':'乙','병':'丙','정':'丁','무':'戊','기':'己','경':'庚','신':'辛','임':'壬','계':'癸'}
        K2H_JI = {'자':'子','축':'丑','인':'寅','묘':'卯','진':'辰','사':'巳','오':'午','미':'未','신':'申','유':'酉','술':'戌','해':'亥'}
        
        if st.button("🔍 생년월일 자동입력", use_container_width=True, key="btn_user_rev"):
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
                                st.success(f"✅ 양력{curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일 음력{klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일 ({leap_str})")
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                        if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

    st.markdown("---")
    
    # ==============================================================
    # 3. 👤 신청인 기본 정보
    # ==============================================================
    st.markdown("<div style='font-weight:900; color:#1A237E; margin-bottom:5px;'>👤 신청인 기본 정보</div>", unsafe_allow_html=True)
    u_name = st.text_input("이름", value="", placeholder="홍길동", key="u_n")
    u_gender = st.selectbox("성별", ["남성", "여성"], index=0, key="u_g")
    u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], index=1, key="u_m_stat")
    u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], index=0, key="u_c")
    
    col1, col2, col3 = st.columns(3)
    u_y = col1.number_input("년", 1900, 2050, value=2010, key="s_y")
    u_m = col2.number_input("월", 1, 12, value=1, key="s_m")
    u_d = col3.number_input("일", 1, 31, value=1, key="s_d")
    
    idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]
    u_t = st.selectbox("태어난 시간", idx_list, index=0, key="s_t")
    
    p_name, p_gender, p_marital, p_cal, p_y, p_m, p_d, p_t = "", "여성", "미혼", "양력", 0, 0, 0, "시간 모름"
    other_reading_text = ""
    run_delivery_calc = False  
    start_date, end_date = None, None
    baby_gender = "미정"
    compare_mode = "자동대조"
    run_iljin_calc = False
    
    # --------------------------------------------------------------
    # 조건 분기 세부 설정 (일운, 타 감명서, 궁합/택일)
    # --------------------------------------------------------------
    if main_category in ["1. 개인 사주팔자 풀이 (종합)", "2. 테마별 특성화 상담"]:
        if u_product in ["1-1. 사주팔자 및 대운 분석", "1-4. 특정 주간 및 특정일운 상세분석"]:
            st.markdown("<hr style='border:1px dashed #1A237E; margin:15px 0;'>", unsafe_allow_html=True)
            run_iljin_calc = st.checkbox("🔮 일운 운세 분석 가동 (선택)", value=False)
            
            if run_iljin_calc:
                if 'target_date' not in st.session_state:
                    kst = pytz.timezone('Asia/Seoul')
                    st.session_state['target_date'] = dt_mod.datetime.now(kst).date()
                target_iljin_date = st.date_input("분석할 일자 선택", value=st.session_state['target_date'])
                st.session_state['target_date'] = target_iljin_date

    elif main_category == "4. 타 감명서 비교":
        st.markdown("<hr style='border:1px dashed #2E7D32; margin:15px 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-weight:900; color:#2E7D32; margin-bottom:5px;'>📜 타 감명서 원문 대조 설정</div>", unsafe_allow_html=True)
        compare_mode = st.radio("대조 분석 모드", ["전통 명리학과 1:1 자동 대조", "외부 타 감명서 원문 대조"], index=0, key="comp_mode_select")
        
        if compare_mode == "외부 타 감명서 원문 대조":
            other_reading_text = st.text_area("타 감명서 원문 텍스트 입력", value="", height=180, placeholder="타 철학관이나 프로그램에서 제공받은 감명서 원문을 이곳에 붙여넣으세요.", key="other_txt_in")

    if main_category == "3. 커플 연애/결혼운 (궁합) 풀이" or u_product == "4-2. 타 감명서 비교 (궁합)":
        st.markdown("<hr style='border:1px dashed #C62828; margin:15px 0;'>", unsafe_allow_html=True)
        
        # 🔍 상대방 사주팔자 역산 검색
        with st.expander("🔍 상대방 사주팔자 역산 검색", expanded=False):
            p_col_g1, p_col_g2 = st.columns(2)
            with p_col_g1: p_ry = st.text_input("상대방 년주", value="", key="p_ry_rev")
            with p_col_g2: p_rm = st.text_input("상대방 월주", value="", key="p_rm_rev")
            p_col_g3, p_col_g4 = st.columns(2)
            with p_col_g3: p_rd = st.text_input("상대방 일주", value="", key="p_rd_rev")
            with p_col_g4: p_rt = st.text_input("상대방 시주", value="", key="p_rt_rev")
            
            if st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="btn_partner_rev"):
                _p_ry = p_ry.replace("년","").replace(" ","")[:2]
                _p_rm = p_rm.replace("월","").replace(" ","")[:2]
                _p_rd = p_rd.replace("일","").replace(" ","")[:2]
                if len(_p_ry)==2 and len(_p_rm)==2 and len(_p_rd)==2:
                    p_ry_h = K2H_GAN.get(_p_ry[0], _p_ry[0]) + K2H_JI.get(_p_ry[1], _p_ry[1])
                    p_rm_h = K2H_GAN.get(_p_rm[0], _p_rm[0]) + K2H_JI.get(_p_rm[1], _p_rm[1])
                    p_rd_h = K2H_GAN.get(_p_rd[0], _p_rd[0]) + K2H_JI.get(_p_rd[1], _p_rd[1])
                    klc_find_p = KoreanLunarCalendar(); found_p = False
                    for y in range(2026, 1899, -1):
                        klc_find_p.setSolarDate(y, 7, 1); gj_y = klc_find_p.getChineseGapJaString().split()
                        if gj_y and gj_y[0][:2] == p_ry_h:
                            curr_dt_p = dt_mod.date(y+1, 2, 28)
                            while curr_dt_p >= dt_mod.date(y, 1, 1):
                                klc_find_p.setSolarDate(curr_dt_p.year, curr_dt_p.month, curr_dt_p.day)
                                gj = klc_find_p.getChineseGapJaString().split()
                                if len(gj) >= 3 and gj[0][:2] == p_ry_h and gj[1][:2] == p_rm_h and gj[2][:2] == p_rd_h:
                                    st.session_state.p_y_in = curr_dt_p.year
                                    st.session_state.p_m_in = curr_dt_p.month
                                    st.session_state.p_d_in = curr_dt_p.day
                                    
                                    time_map_rev_p = {'子':'00:30 ~ 01:29 (朝子)시','丑':'01:30 ~ 03:29 (丑)시','寅':'03:30 ~ 05:29 (寅)시','卯':'05:30 ~ 07:29 (卯)시','辰':'07:30 ~ 09:29 (辰)시','巳':'09:30 ~ 11:29 (巳)시','午':'11:30 ~ 13:29 (午)시','未':'13:30 ~ 15:29 (未)시','申':'15:30 ~ 17:29 (申)시','酉':'17:30 ~ 19:29 (酉)시','戌':'19:30 ~ 21:29 (戌)시','亥':'21:30 ~ 23:29 (亥)시'}
                                    if p_rt:
                                        ji_char_p = p_rt.replace("시","").replace(" ","")[-1]
                                        p_rt_h = K2H_JI.get(ji_char_p, ji_char_p)
                                        if p_rt_h in time_map_rev_p:
                                            matched_time = time_map_rev_p[p_rt_h]
                                            st.session_state.p_t_key = matched_time
                                            st.session_state.p_t_select_key = matched_time
                                    
                                    found_p = True
                                    is_leap_p = getattr(klc_find_p, 'isIntercalary', False)
                                    leap_str_p = "윤달" if is_leap_p else "평달"
                                    st.success(f"✅양력{curr_dt_p.year}년 {curr_dt_p.month:02d}월 {curr_dt_p.day:02d}일 음력{klc_find_p.lunarYear}년 {klc_find_p.lunarMonth:02d}월 {klc_find_p.lunarDay:02d}일 ({leap_str_p})")
                                    break
                                curr_dt_p -= dt_mod.timedelta(days=1)
                            if found_p: break
                    if not found_p: st.error("일치하는 날짜가 없습니다.")
                else: st.warning("간지를 2글자씩 정확히 입력하세요.")

        st.markdown("<div style='font-weight:900; color:#C62828; margin-bottom:5px;'>💕 상대방 기본 정보</div>", unsafe_allow_html=True)
        p_name = st.text_input("이름", value="", placeholder="이영희", key="p_n")
        p_gender_default = "여성" if u_gender == "남성" else "남성"
        p_gender = st.selectbox("성별", ["남성", "여성"], index=["남성", "여성"].index(p_gender_default), key="p_g")
        p_marital = st.selectbox("혼인여부", ["미혼", "기혼", "돌싱"], index=0, key="p_m_stat")
        p_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], index=0, key="p_c")
        
        if 'p_y_in' not in st.session_state: st.session_state['p_y_in'] = 2010
        if 'p_m_in' not in st.session_state: st.session_state['p_m_in'] = 1
        if 'p_d_in' not in st.session_state: st.session_state['p_d_in'] = 1
        if 'p_t_key' not in st.session_state: st.session_state['p_t_key'] = idx_list[0]
        if 'p_t_select_key' not in st.session_state: st.session_state['p_t_select_key'] = st.session_state['p_t_key']

        p_col1, p_col2, p_col3 = st.columns(3)
        p_y = p_col1.number_input("년", 1900, 2050, key="p_y_in")
        p_m = p_col2.number_input("월", 1, 12, key="p_m_in")
        p_d = p_col3.number_input("일", 1, 31, key="p_d_in")
        
        p_t_idx = idx_list.index(st.session_state['p_t_select_key']) if st.session_state['p_t_select_key'] in idx_list else 0
        p_t = st.selectbox("태어난 시간", idx_list, index=p_t_idx, key="p_t_select_key")
        st.session_state['p_t_key'] = p_t
        
        current_year = dt_mod.datetime.now().year 
        f_year = u_y if u_gender == "여성" else p_y

        if u_product == "3-3. 출산 택일" or ((current_year - f_year + 1) <= 49 and main_category == "3. 커플 연애/결혼운 (궁합) 풀이"):
            st.markdown("<hr style='border:1px solid #ddd; margin:15px 0;'>", unsafe_allow_html=True)
            
            with st.expander("👶 출산택일 달력 선택", expanded=(u_product == "3-3. 출산 택일")):
                baby_gender = st.radio("태아 성별", ["미정", "남아", "여아"], index=0)
                start_date = st.date_input("탐색 시작일")
                end_date = st.date_input("탐색 종료일")
                
                st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
                run_delivery_calc = st.checkbox("✅ 출산택일 확정 (체크 후 하단 메인 가동버튼 클릭)", value=(u_product == "3-3. 출산 택일"))

    # ✅ [공통 영역]
    st.markdown("---")
    
    # 🚀 사주풀이 가동 버튼 (Primary - 빨간색)
    btn_single = st.button("🚀 초연 전통명리 사주풀이 가동", key="btn_run", use_container_width=True, type="primary")

    # 🖨️ 인쇄 / PDF 저장 버튼
    if st.button("🖨️ 풀이 결과 인쇄 / PDF 저장", key="btn_print", use_container_width=True, type="secondary"):
        components.html("<script>window.parent.print();</script>", height=0)

    if btn_single:
        is_gunghap_type = (main_category == "3. 커플 연애/결혼운 (궁합) 풀이") or (u_product == "4-2. 타 감명서 비교 (궁합)")
        is_compare_type = (main_category == "4. 타 감명서 비교")

        if not u_name.strip(): 
            st.warning("⚠️ 신청인의 이름을 입력해 주세요.")
        elif is_compare_type and compare_mode == "외부 타 감명서 원문 대조" and not other_reading_text.strip():
            st.warning("⚠️ 타 감명서 원문을 입력해 주세요.")
        elif is_gunghap_type and not p_name.strip(): 
            st.warning("⚠️ 상대방의 이름을 입력해 주세요.")
        else:
            st.session_state['app_running'] = True
            
            # 이전 세션 출력물 말끔히 초기화
            for key in ['saved_report_html', 'saved_report_2', 'saved_report_gh_cover', 'saved_report_gh_m', 'saved_report_gh_f', 'saved_report_gh_g', 'saved_report_del', 'saved_report_iljin']:
                if key in st.session_state: del st.session_state[key]

            if main_category in ["1. 개인 사주팔자 풀이 (종합)", "2. 테마별 특성화 상담"] and run_iljin_calc:
                st.session_state['need_calc'] = True
                st.session_state['run_waterfall'] = True
            elif is_gunghap_type and run_delivery_calc:
                st.session_state['need_calc'] = True
                st.session_state['run_delivery_only'] = True
            else:
                st.session_state['need_calc'] = True
                st.session_state['run_waterfall'] = False
                st.session_state['run_delivery_only'] = False
            
            st.rerun()

# ==============================================================================
# 5. 분석 가동 로직 (need_calc 상태일 때만 무거운 연산 실행)
# ==============================================================================
if st.session_state.get('need_calc', False):
    spinner_msg = f"⏳ [초연 전통명리 개인 사주풀이 분석({APP_VERSION}) 중....]"
    with st.spinner(spinner_msg):
        try:
            name = u_name if u_name.strip() else "홍길동"
            disp_name = name

            kst = pytz.timezone('Asia/Seoul')
            curr_dt_sys = dt_mod.datetime.now(kst)
            curr_y = curr_dt_sys.year
            curr_m = curr_dt_sys.month
            u_age = curr_y - u_y + 1
            base_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0)
            
            klc = KoreanLunarCalendar()
            if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
            elif u_cal == "음력(평달)": klc.setLunarDate(u_y, u_m, u_d, False)
            else: klc.setLunarDate(u_y, u_m, u_d, True)
            
            is_leap = getattr(klc, 'isIntercalary', False)
            leap_str = "윤달" if is_leap else "평달"
            sol_str = f"{klc.solarYear}년 {klc.solarMonth:02d}월 {klc.solarDay:02d}일"
            lun_str = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({leap_str})"
            
            true_ym, true_mm, _ = get_true_year_month_pillar(u_y, u_m, u_d, 12, 0)
            ys, yb = true_ym[0], true_ym[1]
            ms, mb = true_mm[0], true_mm[1]
            
            gj = klc.getChineseGapJaString().split()
            ds, db = gj[2][0], gj[2][1]
            hs, hb = get_time_ganji(ds, u_t, base_dt)
            
            gans, jjis = [hs, ds, ms, ys], [hb, db, mb, yb]
            applicant_bazi = [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"]

            st.session_state['global_gans'] = gans
            st.session_state['global_jjis'] = jjis
            st.session_state['global_ds'] = ds
            st.session_state['global_db'] = db

            adj_mins = get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
            calc_d = get_daeun_su_accurate(utc_dt, order)
            current_daewun_age = ((u_age - calc_d) // 10) * 10 + calc_d
            
            base_y_idx = (curr_y - 1984) % 60
            curr_y_ganji = GAN[base_y_idx % 10] + JI[base_y_idx % 12]
            time_str = f" {u_t.split('(')[0].strip()} ({hb})시" if u_t != "시간 모름" else ""
            
            def td(c, size="18px"): return f"<td class='color-{get_color(c)}' style='font-size:{size}; font-weight:900; border:1px solid #444 !important;'><span style='color:inherit !important;'>{('?' if c in ['?',' ','-'] else c)}</span></td>"
            
            p_icon = "♂️" if u_gender == "남성" else "♀️"
            p_color = "#1A237E" if u_gender == "남성" else "#D50000"
            today_str = (dt_mod.datetime.utcnow() + dt_mod.timedelta(hours=9)).strftime("%Y년 %m월 %d일")

            user_ilju_key = f"{ds}{db}"
            ilju_full_db = choyeon_db.get("ilju_full_master", {})
            ilju_master_data = ilju_full_db.get(user_ilju_key, {})
            ilju_summary_text = ilju_master_data.get('summary', f"{user_ilju_key}의 고유한 본성")

            intro_html = """
    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
    <div style="margin: 0; padding: 0;">
        <p class="ai-body-p" style="margin-top: 0; margin-bottom: 6px; font-weight: 600; text-align: justify; text-indent: 0; color: #000000;">
            <b>"초연 전통 명리학"</b>은 태어난 연·월·일·시의 정통 <b>사주팔자 원국과 격국, 십성, 12운성 및 신살</b>을 바탕으로 내담자의 타고난 천성과 삶의 궤적을 맑고 깊이 있게 통변합니다.
        </p> 
        <p class="ai-body-p" style="margin-top: 0; margin-bottom: 0; font-weight: 600; text-align: justify; text-indent: 0; color: #000000;">
            따라서, 본 감명서는 고전 명리의 이치에 철저히 입각하여 인생의 길흉화복과 시기별 흐름을 가장 정교하고 품격 있게 제시합니다.
        </p>
    </div>
    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
"""

            hap_chung_hyoung_pa_hae = (
                f"일-월지:{get_ji_rel_set(db, mb)}, 일-년지:{get_ji_rel_set(db, yb)}, "
                f"일-시지:{get_ji_rel_set(db, hb)}, 월-년지:{get_ji_rel_set(mb, yb)}"
            )

            # ==============================================================
            # [A] 개인 사주팔자 및 특성화 상품 분석 분기
            # ==============================================================
            if main_category in ["1. 개인 사주팔자 풀이 (종합)", "2. 테마별 특성화 상담"]:
                past_months_html = ""

                cover_html = (
                        f"<div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>\n"
                        f"    <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>\n"
                        f"        <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>\n"
                        f"            <h1 class='title-gothic' style='font-size: 36px !important; margin:0 !important;'>초연 전통 명리사주 풀이</h1>\n"
                        f"            <div style='text-align: right; margin-top: 10px;'>\n"
                        f"                <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px;'>{APP_VERSION}</span>\n"
                        f"            </div>\n"
                        f"        </div>\n"
                        f"        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>\n"
                        f"            <h2 style='font-size: 24px; font-weight: 800; color: {p_color}; margin-bottom: 20px;'>{p_icon} 신청인 : {u_name} 님</h2>\n"
                        f"            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>\n"
                        f"                <p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p>\n"
                        f"                <p style='margin: 5px 0 0 0; color: #D50000; white-space: nowrap;'>{time_str}</p>\n"
                        f"            </div>\n"
                        f"        </div>\n"
                        f"        <p style='font-size: 18px; margin-top: 50px; font-weight: 800;'>{today_str}</p>\n"
                        f"        <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 20px;'>초연 전통명리 연구소</p>\n"
                        f"    </div>\n"
                        f"</div>"
                    )
                st.session_state['saved_report_cover'] = cover_html

                ji_rel_rows = ""
                for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                    b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                    b_top = "0px solid transparent !important"
                    cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'><span style='color:inherit !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</span></td>" for ci in range(4)])
                    lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'><span style='color:inherit !important;'>합충형파해</span></td>" if l_idx==0 else ""
                    ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

                info_h = f"<div style='text-align:center; font-family:\"Malgun Gothic\", sans-serif; margin-bottom:15px; line-height:1.5;'><span style='font-size:18px; font-weight:900; color:{p_color}; white-space:nowrap;'>{p_icon} {disp_name}님 ({u_gender}, {u_marital}, {u_age}세)</span><br><span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span></div>"

                table_html = f"""<div style='text-align:center; margin-bottom:10px;'>{info_h}</div>
<table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
<tr class='top-header-cell'>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'><span style='color:#FFFFFF !important;'>구분</span></td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'><span style='color:#FFFFFF !important;'>시주</span></td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'><span style='color:#FFFFFF !important;'>일주</span></td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'><span style='color:#FFFFFF !important;'>월주</span></td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'><span style='color:#FFFFFF !important;'>년주</span></td>
</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>천간합충</span></td>{"".join([f"<td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_gan_rel_all(i, gans)}</span></td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>천간십성</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(ds,hs)}</span></td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(ds,ms)}</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(ds,ys)}</span></td></tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>천간</span></td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>지지</span></td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>지지십성</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(ds,hb)}</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(ds,db)}</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(ds,mb)}</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(ds,yb)}</span></td></tr>
<tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>지장간</span></td>{"".join([f"<td style='padding:0; border:1px solid #444;'><span style='color:inherit !important;'>{get_jijanggan_full(ds, jjis[i])}</span></td>" for i in range(4)])}</tr>
{ji_rel_rows}
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>십이운성</span></td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'><span style='color:inherit !important;'>{get_unsung(ds, jjis[i])}</span></td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>십이신살</span></td>{"".join([f"<td style='color:#C62828; border:1px solid #444 !important;'><span style='color:inherit !important;'>{get_12_shinsal(yb, jjis[i])}</span></td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>일반신살</span></td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'><span style='color:inherit !important;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis, u_gender)) if get_general_shinsal_filtered(i, gans, jjis, u_gender) else '-'}</span></td>" for i in range(4)])}</tr>
</table>
"""
                calc_gyukgook, gyukgook_detail = get_gyukgook_detailed(ds, ys, ms, hs, mb)

                SEASON_SOLAR_TERMS = {
                    '寅': '입춘과 경칩 사이의 이른 봄(寅月)',
                    '卯': '경칩과 청명 사이의 완연한 봄(卯月)',
                    '辰': '청명과 입하 사이의 봄과 여름의 환절기(辰月)',
                    '巳': '입하와 망종 사이의 이른 여름(巳月)',
                    '午': '망종과 소서 사이의 완연한 여름(午月)',
                    '未': '소서와 입추 사이의 가장 무더운 여름(未月)',
                    '申': '입추와 백로 사이의 이른 가을(申月)',
                    '酉': '백로와 한로 사이의 완연한 가을(酉月)',
                    '戌': '한로와 입동 사이의 가을과 겨울의 환절기(戌月)',
                    '亥': '입동과 대설 사이의 이른 겨울(亥月)',
                    '子': '대설과 소한 사이의 완연한 한겨울(子月)',
                    '丑': '소한과 입춘 사이의 가장 추운 겨울(丑月)'
                }

                wol_korean_str = SEASON_SOLAR_TERMS.get(mb, f"{mb}월")
                gyuk_name = calc_gyukgook

                user_ilju_key = f"{ds}{db}"
                ilju_struct_db = choyeon_db.get("ilju_structure", {})
                struct_data = ilju_struct_db.get(user_ilju_key, [])

                if len(struct_data) >= 3:
                    action_type = struct_data[1]    # (2) 유형 (예: "자기몰입형")
                    main_tendency = struct_data[2]  # (3) 성격 (예: "자의식 발달하여 발상의 전환이 빠르고 임사즉결")
                else:
                    action_type = "자율활동형"
                    main_tendency = "독자적인 삶의 무대를 개척하는"

                ilju_full_db = choyeon_db.get("ilju_full_master", {})
                ilju_master_data = ilju_full_db.get(user_ilju_key, {})
                ilju_summary_text = ilju_master_data.get('summary', '고유의 역량을 품은')

                choyeon_golden_text = f"""
<div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000; margin-bottom: 20px;'>
    <p style='text-indent: 15px; margin-bottom: 5px;'>
        정통 명리학적으로 풀이하면 <b>{disp_name}님</b>은 <b>{wol_korean_str}</b>에 <b>'{gyuk_name}'</b>의 그릇을 갖추고 태어나셨으며, 성격은 <b>'{action_type}'</b>으로 <b>'{main_tendency}'</b> 성향이 있습니다.
    </p>
</div>
<hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
"""

                gen_shinsal_list = []
                for i in range(4):
                    raw_tags = get_general_shinsal_filtered(i, gans, jjis, u_gender)
                    for tag in raw_tags:
                        if ">" in tag and "<" in tag: gen_shinsal_list.append(tag.split('>')[1].split('<')[0])
                shinsal_str = ", ".join(list(dict.fromkeys(gen_shinsal_list))) if gen_shinsal_list else "특이 신살 없음"
                
                s12_list = [get_12_shinsal(yb, j) for j in jjis if get_12_shinsal(yb, j) != "-"]
                s12_str = ", ".join(list(dict.fromkeys(s12_list))) if s12_list else "특이 12신살 없음"
          
                samhyung_warn_list = []
                jjis_set = set(jjis)
                if len({'寅', '巳', '申'}.intersection(jjis_set)) == 3:
                    samhyung_warn_list.append("원국 인사신(寅巳申) 삼형살 전면 성립")
                elif len({'寅', '巳', '申'}.intersection(jjis_set)) == 2:
                    missing = list({'寅', '巳', '申'} - jjis_set)[0]
                    samhyung_warn_list.append(f"원국 인사신(寅巳申) 가형 상태 (운에서 '{missing}' 도래 시 삼형 완성)")

                if len({'丑', '戌', '未'}.intersection(jjis_set)) == 3:
                    samhyung_warn_list.append("원국 축술미(丑戌未) 삼형살 전면 성립")
                elif len({'丑', '戌', '未'}.intersection(jjis_set)) == 2:
                    missing = list({'丑', '戌', '未'} - jjis_set)[0]
                    samhyung_warn_list.append(f"원국 축술미(丑戌未) 가형 상태 (운에서 '{missing}' 도래 시 삼형 완성)")

                samhyung_warn = " / ".join(samhyung_warn_list) if samhyung_warn_list else "해당 없음"

                counts = {"목":0,"화":0,"토":0,"금":0,"수":0}
                for char in gans + jjis:
                    if char != "?": counts[get_color(char)] += 1
                
                guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
                guiin_str = guiin_map.get(ds, '없음')
                    
                direction_str = "순행" if order == 1 else "역행"
                n_gong = calculate_gongmang(ys, yb)
                i_gong = calculate_gongmang(ds, db)
                
                gongmang_targets = n_gong.split(',') + i_gong.split(',')
                gongmang_hits = []
                if yb in gongmang_targets: gongmang_hits.append(f"년지({yb})")
                if mb in gongmang_targets: gongmang_hits.append(f"월지({mb})")
                if db in gongmang_targets: gongmang_hits.append(f"일지({db})")
                if hb in gongmang_targets: gongmang_hits.append(f"시지({hb})")
                
                gongmang_actual = ", ".join(gongmang_hits) + "에 공망 작용함" if gongmang_hits else "사주 원국 내 공망 작용 없음"
                
                cur_samjae = get_samjae(yb, curr_y_ganji[1])
                samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"
                
                master_bar_html = f"<div style='border:2px solid #3E2723; margin-top:20px; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap;'><div>🔢 대운수: {calc_d}</div><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin_str}</div><div>🎯 공망: [일] {i_gong}</div><div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div></div>"               

                daewun_info = []
                un_html = f"<div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(10):
                    val, c, j = i*10+calc_d, GAN[(GAN.index(ms)+(i+1)*order)%10] if ms in GAN else "-", JI[(JI.index(mb)+(i+1)*order)%12] if mb in JI else "-"
                    daewun_info.append(f"{val}세:{c}{j}")
                    is_active = val <= u_age < val+10
                    bg_col = "#FFF9C4" if is_active else "transparent"
                    b_left = "1px solid #ccc" if i != 9 else "none"
                    un_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{val}세</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,c)}</div><div class='color-{get_color(c)}' style='font-size:16px; font-weight:900;'>{c}</div><div class='color-{get_color(j)}' style='font-size:16px; font-weight:900;'>{j}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,j)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,j)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, j)}</div></div>"
                un_html += "</div>"

                cur_dw_idx = max(0, (u_age - calc_d) // 10)
                dw_g_cur = GAN[(GAN.index(ms) + (cur_dw_idx+1)*order)%10] if ms in GAN else "-"
                dw_j_cur = JI[(JI.index(mb) + (cur_dw_idx+1)*order)%12] if mb in JI else "-"
                current_daewun_age = cur_dw_idx * 10 + calc_d
                
                dw_start_age = current_daewun_age
                dw_mid_age   = current_daewun_age + 4
                dw_mid2_age  = current_daewun_age + 5
                dw_end_age   = current_daewun_age + 9

                start_year = u_y + current_daewun_age - 1
                sewun_info = []
                se_html = f"<div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
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

                wol_gans = ["己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚"]
                wol_jis = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]
                cur_wol_g = wol_gans[curr_m - 1]
                cur_wol_j = wol_jis[curr_m - 1]
                
                wol_html = f"<div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 월운의 흐름 ({curr_y}년도 양력기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(12):
                    tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
                    is_cur_m = (tm == curr_m)
                    bg_col = "#E8F5E9" if is_cur_m else "transparent"
                    b_left = "1px solid #ccc" if i != 11 else "none"
                    wol_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{tm}월</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div></div>"
                wol_html += "</div>"
                
                past_daewun_list = []
                for idx in range(cur_dw_idx):
                    val = idx * 10 + calc_d
                    d_gan = GAN[(GAN.index(ms) + (idx + 1) * order) % 10] if ms in GAN else "-"
                    d_ji = JI[(JI.index(mb) + (idx + 1) * order) % 12] if mb in JI else "-"
                    past_daewun_list.append(f"• {val}세~{val+9}세 ({d_gan}{d_ji}대운): ")
                past_daewun_html = "\n".join(past_daewun_list) if past_daewun_list else "• (첫 대운 시기이므로 이전 대운 생략)"

                curr_dw_start_year = u_y + current_daewun_age - 1
                sewun_start_calc = min(curr_dw_start_year, curr_y - 3)
                past_sewun_list = []
                for py in range(sewun_start_calc, curr_y):
                    base = (py - 1984) % 60
                    past_sewun_list.append(f"• {py}년({GAN[base%10]}{JI[base%12]}년): ")
                past_sewun_html = "\n".join(past_sewun_list) if past_sewun_list else "• (분석할 과거 세운 없음)"

                terms_name = {1:"소한", 2:"입춘", 3:"경칩", 4:"청명", 5:"입하", 6:"망종", 7:"소서", 8:"입추", 9:"백로", 10:"한로", 11:"입동", 12:"대설"}
                
                def get_term_day(y, m):
                    _, p1, _ = get_true_year_month_pillar(y, m, 1, 12, 0)
                    for d in range(2, 12):
                        _, pd, _ = get_true_year_month_pillar(y, m, d, 12, 0)
                        if pd != p1: return d, pd
                    return 5, p1

                past_wol_list = []
                prev_y_idx = (curr_y - 1 - 1984) % 60
                prev_y_ganji = GAN[prev_y_idx % 10] + JI[prev_y_idx % 12]
                
                for pm in range(1, curr_m):
                    tc, tj = wol_gans[pm-1], wol_jis[pm-1]
                    s_day, _ = get_term_day(curr_y, pm)
                    next_m = pm + 1 if pm < 12 else 1
                    next_y = curr_y if pm < 12 else curr_y + 1
                    e_day, _ = get_term_day(next_y, next_m)
                    t_start = terms_name[pm]
                    t_end = terms_name[next_m]
                    
                    year_prefix = f"{prev_y_ganji}년 " if pm == 1 else ""
                    past_wol_list.append(f"• {pm}월({tc}{tj}월): ({year_prefix}{pm}월 {s_day}일 {t_start} ~ {next_m}월 {e_day-1}일 {t_end} 전)")
                
                past_months_html = "\n".join(past_wol_list) if past_wol_list else "• (올해 첫 달이므로 작년 하반기 요약): "

                curr_term_day, curr_wol_pillar = get_term_day(curr_y, curr_m)
                next_m = curr_m + 1 if curr_m < 12 else 1
                next_y = curr_y if curr_m < 12 else curr_y + 1
                next_term_day, _ = get_term_day(next_y, next_m)
                
                curr_t_name = terms_name[curr_m]
                next_t_name = terms_name[next_m]

                if curr_m == 6:
                    sun = ephem.Sun()
                    haji_day = 21
                    for d in range(20, 24):
                        dt_utc = dt_mod.datetime(curr_y, 6, d, 12, 0).astimezone(pytz.utc)
                        sun.compute(dt_utc)
                        if math.degrees(ephem.Ecliptic(sun).lon) % 360.0 >= 90.0:
                            haji_day = d
                            break
                    
                    prompt_first_half = f"▶ 이번 달 전반기 ({curr_m}월 {curr_term_day}일 {curr_t_name} ~ {curr_m}월 {haji_day-1}일 하지 전: {curr_wol_pillar})"
                    prompt_second_half = f"▶ 이번 달 후반기 ({curr_m}월 {haji_day}일 하지 ~ {next_m}월 {next_term_day-1}일 {next_t_name} 전: {curr_wol_pillar})"
                else:
                    mid_day = curr_term_day + 15
                    prompt_first_half = f"▶ 이번 달 전반기 ({curr_m}월 {curr_term_day}일 {curr_t_name} ~ {curr_m}월 {mid_day-1}일: {curr_wol_pillar})"
                    prompt_second_half = f"▶ 이번 달 후반기 ({curr_m}월 {mid_day}일 ~ {next_m}월 {next_term_day-1}일 {next_t_name} 전: {curr_wol_pillar})"

                closing_html = f"""<div style='margin-top: 30px;'>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 정통 명식의 바코드와 같지만, 우리가 살아가며 마주하는 '운'은 늘 변화하며 흐릅니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 전통명리와의 인연'이 <b>{disp_name}님</b>의 삶이라는 긴 여정에서 올바른 방향을 잡는 든든한 '나침반'이 되기를 진심으로 기원합니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 인생의 길흉화복과 명리에 대한 더 깊은 지혜가 필요하실 때 언제든 <b>'초연 전통명리 연구소'</b>를 찾아 주십시오.</p>
<p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 깊이 감사드립니다.</p>
<div style='text-align: right; margin-top: 30px;'>
<span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 전통명리 연구소 드림 -</span>
</div>
</div>"""

                report_1_full_html = f"""{cover_html}
<div class='report-page' style='page-break-before: avoid;'>
<div class='vip-inset-frame' style='border:2px solid #1A237E; box-sizing: border-box; padding: 20px; border-radius:15px; margin-top: 0;'>

<h1 style='text-align:center;'>🎯[초연 전통 명리사주 풀이 ({u_product})]</h1>
{table_html}
{master_bar_html}
<div style='margin-top:20px;'>
{{full_content_clean_placeholder}}
</div>
</div>
</div>"""

                base_gans_list = [hs, ds, ms, ys]
                base_jjis_list = [hb, db, mb, yb]

                won_guk_vaults = []
                for attacker in base_jjis_list:
                    won_guk_vaults.extend(check_vault_status(base_gans_list, base_jjis_list, attacker))
                won_guk_vaults = list(dict.fromkeys(won_guk_vaults)) 
                won_guk_vaults_str = ", ".join(won_guk_vaults) if won_guk_vaults else "해당 없음"

                daewun_vaults = check_vault_status(base_gans_list, base_jjis_list, dw_j_cur)
                sewun_vaults = check_vault_status(base_gans_list, base_jjis_list, curr_y_ganji[1])
                wolwun_vaults = check_vault_status(base_gans_list, base_jjis_list, cur_wol_j)

                hang_un_vaults = list(dict.fromkeys(daewun_vaults + sewun_vaults + wolwun_vaults))
                hang_un_vaults_str = ", ".join(hang_un_vaults) if hang_un_vaults else "해당 없음"

                disp_first_name = disp_name[1:] if len(disp_name) > 2 else disp_name
                
                age_prompt = ""
                if u_age < 20:
                    age_prompt = "내담자는 청소년기(10대)입니다. 학업 진학운과 부모 형제운을 최우선으로 상세히 분석하고 재물 사업운은 축소하십시오."
                elif 20 <= u_age < 40:
                    age_prompt = "내담자는 청년기(20~30대) MZ세대입니다. 고리타분한 명리 용어를 버리고 직업은 '스타트업, 프리랜서, 워라밸, 퍼스널 브랜딩', 연애는 '소개팅, 썸, 연인 간의 소통' 등 2030 청년들이 100% 공감할 수 있는 세련되고 트렌디한 어휘로 통변하십시오."
                elif 40 <= u_age < 60:
                    age_prompt = "내담자는 중장년기(40~50대)입니다. 재성운과 관직 명예운에 집중하여 현실적인 자산 관리와 사회적 성취를 중심으로 서술하십시오."
                else:
                    age_prompt = "내담자는 노년기(60대 이상)입니다. 건강운 및 심리적 평안, 노후 자산 안정을 최우선으로 깊이 다루십시오."

                gender_prompt = ""
                if u_gender == "남성":
                    gender_prompt = "남성 내담자입니다. 배우자운(재성)과 자식운(관성)을 남명 이론에 입각하여 해석하십시오."
                else:
                    gender_prompt = "여성 내담자입니다. 배우자운(관성)과 자식운(식상)을 여명 이론에 입각하여 해석하십시오."

                if ilju_master_data:
                    ilju_master_prompt_context = f"""
🎯 [초연 전통명리의 뼈때리는 팩트폭격 - {user_ilju_key}일주 전용 마스터 비기]
- 물상 및 성향 요약: {ilju_master_data.get('summary', '')}
- 심리적 관점: {ilju_master_data.get('psychology', '')}
- 육친적 관점: {ilju_master_data.get('family', '')}
- 사회적 관점: {ilju_master_data.get('society', '')}
- 지장간 좌법(座法) 분석: {ilju_master_data.get('jijanggan_zaBeob', '')}
- 인종법(引從法) 숨겨진 내면: {ilju_master_data.get('injong_beob', '')}
- 신살, 변곡점, 건강, 과숙/고신, 도망역: {ilju_master_data.get('shinsal_warnings', '')}
- 💥 뼈때리는 팩트폭격 핵심 비기: {ilju_master_data.get('choyeon_secret', '')}

🚨 [통변 절대 규칙]: 위 박사님의 '초연 전통명리의 뼈때리는 팩트폭격'에 담긴 문장과 임상적 통찰을 사주풀이 에세이(성격 분석, 사주구조분석, 운의 흐름) 전반에 100% 녹여내어 깊이 있게 풀이하십시오.
"""
                else:
                    ilju_master_prompt_context = ""
                                
                db_header = (
                    f"[시스템 강제 시간 인식: 현재 시점은 {curr_y}년 {curr_m}월 입니다.]\n"
                    "당신은 정통 명리심리상담사 1급 자격을 갖춘 초연 박사입니다. \n"
                    f"- 내담자 성함: {disp_name}\n"
                    f"- 나이 / 성별: {u_age}세 / {u_gender}\n"
                    f"- marital_status: {u_marital}\n"
                    f"- 선택 상품: {u_product}\n"
                    f"- 격국 팩트: {gyukgook_detail}\n"
                    f"- 실제 타격받는 공망 궁위 팩트: {gongmang_actual}\n"
                    f"- 올해({curr_y}년) 삼재 여부: {cur_samjae}\n" 
                    f"- 원국 삼형살(인사신/축술미) 팩트: {samhyung_warn}\n"
                    f"- 원국 내부 묘고(입고/개고) 작용: {won_guk_vaults_str}\n"
                    f"- 현재 행운(대/세/월운) 외부 충격에 의한 묘고 작용: {hang_un_vaults_str}\n"
                    f"🚨 [AI 환각 및 UI 파괴 원천 차단 절대 규칙]\n"
                    f"1. 서론 철저 금지: '안녕하십니까', '기쁩니다' 등의 인사말이나 감성적인 도입부를 절대로 작성하지 마십시오.\n"
                    f"2. 호칭 절대 규칙: 각 대목차의 첫 문장은 반드시 '{disp_name}님은~'으로 격식있게 시작하고, 그 이후 본문에서는 친근하게 '{disp_first_name}님은~'으로 부르십시오.\n"
                    f"3. 🚨 공망 소설 금지: 위 '실제 타격받는 공망 궁위 팩트'에 명시된 자리만 공망으로 해석하십시오.\n"
                    f"4. 괄호 병기 금지: 에세이 작성 시 전문 용어나 한자를 괄호 안에 병기하는 행위를 금지합니다.\n"
                    f"5. HTML 훼손 금지: </div> 태그를 임의로 닫거나 마크다운 기호를 남발하지 마십시오.\n"
                )

                if u_gender == '남성':
                    yukchin_rule = f"""
🚨 [육친 통변 특수부대 절대 규칙 (남성용)]: 
- 본 내담자는 남성(현재 상태: {u_marital})입니다. 아래의 명리학적 육친 생극제화 및 대체 규칙을 100% 엄수하십시오.
1. 👨‍👩‍👦 [핵심 가족]: 
   - 아내(부인) = 정재 (정재가 없으면 편재로 대체)
   - 애인(여친) = 편재 (편재가 없으면 정재로 대체)
   - 자녀 = 관성(정관/편관) 🚨(경고: 남명에서 '식상'을 자녀로 풀이하는 즉시 치명적 오류로 간주함!)
2. 👵👴 [부모 및 조부모]: 
   - 아버지 = 편재 (없으면 정재) / 어머니 = 정인 (없으면 편인)
   - 조부(할아버지) = 편인 / 조모(할머니) = 상관
3. 🏠 [처가 및 형제]: 
   - 장모(처가) = 식상 (아내를 생하는 기운)
   - 동성 형제(형/남동생) = 비견 / 이성 형제(누나/여동생) = 겁재
4. 🚨 [상태별 호칭 맞춤형 타겟팅]: 내담자의 현재 혼인 상태({u_marital})를 반드시 반영하십시오. 
   - 기혼: '현재 아내/배우자'로 칭할 것.
   - 미혼: '미래의 인연'으로 칭할 것.
   - 🚨돌싱(이혼/사별): '과거의 인연(전처)'에 대한 성찰이나 '새로운 인연(재혼운)'으로 변환하여 카운슬링할 것.
"""
                else:
                    yukchin_rule = f"""
🚨 [육친 통변 특수부대 절대 규칙 (여성용)]: 
- 본 내담자는 여성(현재 상태: {u_marital})입니다. 아래의 명리학적 육친 생극제화 및 대체 규칙을 100% 엄수하십시오.
1. 👩‍❤️‍👨 [핵심 가족]: 
   - 남편 = 정관 (정관이 없으면 편관으로 대체)
   - 애인(남친) = 편관 (편관이 없으면 정관으로 대체)
   - 자녀 = 식상(식신/상관) 🚨(경고: 여명에서 '관성'을 자녀로 풀이하는 즉시 치명적 오류로 간주함!)
2. 👵👴 [부모 및 조부모]: 
   - 아버지 = 편재 (없으면 정재) / 어머니 = 정인 (없으면 편인)
   - 조부(외할아버지) = 편인 / 조모(외할머니) = 상관
3. 🏠 [시댁 및 자매]: 
   - 시어머니(시댁) = 재성 (남편을 생하는 기운)
   - 동성 형제(언니/여동생) = 비견 / 이성 형제(오빠/남동생) = 겁재
4. 🚨 [상태별 호칭 맞춤형 타겟팅]: 내담자의 현재 혼인 상태({u_marital})를 반드시 반영하십시오. 
   - 기혼: '현재 남편/배우자'로 칭할 것.
   - 미혼: '미래의 인연'으로 칭할 것.
   - 🚨돌싱(이혼/사별): '과거의 인연(전 남편)'에 대한 성찰이나 '새로운 인연(재혼운)'으로 변환하여 카운슬링할 것.
"""

                prompt = f"""
{db_header}
{ilju_master_prompt_context}

[ 🚨종합 특별지시 사항 : 대중을 위한 정통 명리 통변 원칙]
1. 🚨명리 용어의 전략적 노출 및 해제: 딱딱한 한자어 전문 용어의 단순 남발을 금지하고, 쉬운 비유와 현대적 구어체로 설명하십시오.
2. 따뜻한 상담가 마인드: 내담자의 삶을 깊이 이해하고 어루만져 주는 친절한 카운슬러 어조를 유지하십시오.
3. 정통 사주 명리의 십성, 격국, 12운성, 신살의 이치를 유기적으로 융합하여 심도 있게 풀이하십시오.
4. 🚨[요약 금지 절대 규칙]: 축약, 요약, 압축 서술을 엄금합니다. 선택된 상품 [{u_product}]의 주 분석 대상 팩트를 풍부하고 상세하게 풀이하십시오.

[문단 통제 명령]
1. 모든 통변 에세이 문장은 반드시 <p style='text-indent: 1em;'> 태그로 감싸하십시오.
2. 🚨 [계층별 글자 크기 및 상하 간격 강제 규격화]
   [대목차] <h3 style='color:#1A237E; font-size: 24px; font-weight: 900; margin-top: 30px; margin-bottom: 15px;'>1. 성격 분석</h3>
   [부목차] <span class='sub-title' style='display: block; font-size: 20px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 35px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
   [세부 소목차] <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 25px; margin-bottom: 5px;'>▶ 현재 대운 전반기 상세 분석</span>
3. 표(Table) 생성 절대 금지. 운의 흐름 연도별 분석은 반드시 도트 기호(•)를 사용한 텍스트로 작성하십시오.

[내담자 맞춤형 정밀 타겟팅]
- {age_prompt}
- {gender_prompt}
- {yukchin_rule}

[통변 지시 및 팩트 통제]
- 간지 표기 시 반드시 한자로 표기하십시오.
- 격국 팩트: {gyukgook_detail}
- 공망 팩트: {gongmang_actual}
- 일반신살: {shinsal_str} / 12신살: {s12_str}
- 삼형살 팩트: {samhyung_warn}
- 입고/개고 팩트: {won_guk_vaults_str}

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>1. 성격 분석</h3>
<div class='content-box-loose'>
{choyeon_golden_text}

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>1) 겉으로 드러난 성격</span>
- 일주({ds}{db}), 일간 십성, 일지 십이운성 봉법/좌법 에너지를 분석하십시오.
- 위 박사님 마스터 비기의 성향 및 물상 팩트를 직접 인용하여 표면적 행동 방식과 사회적 대인관계 스타일을 상세히 서술하십시오.
- 12신살 통변 시 년지 기준 신살(사회적 환경)과 일지 기준 신살(내면 파동)을 명확히 구분하여 설명하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>2) 감추어진 내 속마음</span>
- 일지 지장간 인종법(引從法)과 좌법, 일지 공망의 양가적 심리 작용을 정밀 분석하십시오.
- 마스터 비기의 내면 심리 분석(psychology)을 바탕으로 남들에게 말하지 못하는 속마음, 정신적 고독감, 내면의 공허함을 서술하십시오.
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>2. 사주팔자 구조분석</h3>
<div class='content-box-loose'>
🚨 [원국 분석 엄밀성 지시]: 본 파트는 '사주원국 자체의 고정 구조'만을 분석하는 파트입니다. 동적 운(대/세/월/일운)의 팩트는 절대 개입시키지 마십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>1) 내 삶의 무대와 타고난 기본 성향</span>
- 원국의 오행 분포(木:{counts['목']}, 火:{counts['화']}, 土:{counts['토']}, 金:{counts['금']}, 水:{counts['수']})의 편중 및 발달 상태를 분석하십시오.
- 십성의 생극제화 및 격국({gyukgook_detail})의 그릇과 품격, 원국의 조후(調候) 상태를 정밀 서술하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>2) 내 삶의 역동성과 상호작용</span>
- 🚨 [해석 절대 원칙]: 원국 내의 합충형해파는 사건 발생이 아니라, 일간과 7궁성(년·월·일·시) 간의 '육친적 거리감, 심리적 갈등, 사회적 관계성'으로 정밀 통변하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>3) 내 삶의 숨겨진 능력과 특별한 행운의 요소</span>
- 4주 궁위별 12운성의 에너지 세기와 주요 신살(천을귀인: {guiin_str}, 일반신살: {shinsal_str}, 12신살: {s12_str})의 배치가 삶에 미치는 영향을 풀이하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>4) 내 삶의 변곡점과 주의해야 할 시련</span>
- 진술축미 묘고의 원국 내 상태(원국 입고/개고 팩트: {won_guk_vaults_str})와 삼형살(팩트: {samhyung_warn}), 복음, 격각 등의 원국 내 정적 구조를 분석하십시오.
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>3. 특정 운의 분석</h3>
<div class='content-box-loose'>

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>1) 부모·형제운</span>
- 🚨 [JSON family 연동]: 마스터 데이터의 육친 관점("family")과 년주(조상/부모)·월주(부모/형제)의 십성, 인성·비겁의 동태를 바탕으로 정서적 유대감과 현실적 환경 작용을 서술하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>2) 학업·진학운</span>
- 인성(학문/이해력)과 식상(표현력), 관성(조직/자제력)의 세력을 분석하십시오.
- 문창, 문곡, 학당, 화개 등 학문 관련 핵심 신살을 자연스럽게 융합하여 공부 스타일, 시험운, 전공 선택 방향성을 서술하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>3) 적성·직업운</span>
- 🚨 [JSON society 및 지장간 구조 연동]: 마스터 데이터의 사회적 관점("society")과 지장간 구조를 연동하십시오.
  ① 진로 유형 판별: '직장 조직형' vs '자율 사업형' vs '전문 자유직형' 중 어디에 적합한지 명확히 분기하여 제안하십시오.
  ② 추천 업상: JSON "society"에 정의된 적성 분야 및 추천 업상(業象) 물상 예시를 정확히 짚어주십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>4) 연애운</span>
- 일간/일지 십성 및 지장간 구조를 바탕으로 본인의 이상형 스타일과 연애 성향을 풀이하십시오.
- 원국 내 배우자성(남:재성, 여:관성)의 위치, 충, 원진, 공망 파동을 분석하여 조혼/만혼 권장 가이드 및 연애 시 유의점을 조언하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>5) 결혼·자녀운</span>
- 🚨 [JSON family 연동]: 배우자궁(일지)의 안점 여부 및 배우자성, 자식성(남:관성, 여:식상)의 동태와 인연의 깊이를 따뜻한 어조로 서술하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>6) 재물운</span>
- 재성(정재/편재)의 유무, 지장간 재고(財庫) 여부, 식상생재/재생관 흐름을 정밀 분석하여 돈과 물질을 대하는 가치관과 재물 축적 스타일을 서술하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>7) 관직·명예운</span>
- 관성과 인성의 상생 구조, 조직 내 승진, 감투운, 책임감의 크기 및 사회적 명예 발전 가능성을 정밀 풀이하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>8) 건강운</span>
- 🚨 [JSON shinsal_warnings 연동]: 마스터 데이터의 건강 경고("shinsal_warnings") 취약 장기 팩트 및 원국 오행의 편중/편고를 분석하여 실질적인 건강 관리법을 제시하십시오.
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>4. 운의 흐름 분석</h3>
<div class='content-box-loose'>
🚨 [동적 운 통변 절대 원칙]: 외부 운(대운, 세운, 월운)이 원국을 타격할 때 일어나는 '현실적 팩트(언제, 어떤 사건/사고/발복이 일어나는가)'를 정밀 구분하여 통변하십시오.

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>1) 대운의 흐름</span>
[DAEWUN_TABLE_HERE]
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>(1) 지나온 과거 각 대운 분석</span>
🚨 [대운 줄바꿈 절대 규칙]: 각 대운 항목(• ... :)의 쌍점(:) 뒤 해설은 절대로 통글로 뭉쳐 쓰지 마시고, 각 불릿 항목마다 독립된 <p style='text-indent: 1em; margin-bottom: 12px;'> 태그로 감싸 반드시 줄바꿈하여 서술하십시오.
{past_daewun_html}

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>(2) 현재 대운 분석</span>
▶ 현재 대운 전반기 상세 분석 ({dw_start_age}세~{dw_mid_age}세):
▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세):

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>2) 세운의 흐름</span>
[SEWUN_TABLE_HERE]
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>(1) 지나온 과거 각 세운 분석</span>
🚨 [세운 줄바꿈 절대 규칙]: 각 세운 항목(• ... :)의 쌍점(:) 뒤 해설은 반드시 독립된 <p style='text-indent: 1em; margin-bottom: 12px;'> 태그로 감싸 한 줄씩 완전히 줄바꿈하여 작성하십시오.
{past_sewun_html}

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>(2) 현재 세운 분석</span>
▶ 현재 세운 전반기 상세 분석:
▶ 현재 세운 후반기 상세 분석:

<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>3) 월운의 흐름</span>
[WOLWUN_TABLE_HERE]
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>(1) 지나온 과거 각 월운 분석</span>
🚨 [월운 줄바꿈 절대 규칙]: 각 월운 항목(• ... :)의 쌍점(:) 뒤 해설은 반드시 독립된 <p style='text-indent: 1em; margin-bottom: 12px;'> 태그로 감싸 한 줄씩 완전히 줄바꿈하여 작성하십시오.
{past_months_html}

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>(2) 현재 월운 분석</span>
{prompt_first_half}
{prompt_second_half}
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>5. 삶을 바꾸는 지혜로운 조언</h3>
<div class='content-box-loose'>
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 나를 돕는 에너지와 색상:</span>
(용신/희신 오행에 부합하는 개운 색상, 숫자를 제시하십시오)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 재물을 부르는 이재(理財)와 절제의 지혜:</span> 
(사주 구조상 손재수를 막고 실질적인 부를 축적할 재태크/지출 절제/투자 가이드를 명쾌하게 제시하십시오)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 재능 효율을 높이는 직업적 지혜:</span> 
(강점 오행과 십성을 극대화할 직업적 처세술을 조언하십시오)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>4) 신체 밸런스와 에너지 관리:</span> 
(취약 오행 수련법 및 건강 습관을 제시하십시오)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>5) 공간의 흐름과 방위의 지혜:</span> 
(길한 방향, 공간 정돈 및 개운 인테리어를 제시하십시오)

<div style='margin-top: 25px; padding-top: 15px; border-top: 1.5px dashed #1A237E;'>
<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #1A237E; display: block; margin-bottom: 10px;'>🎯 전통명리 특별 개운 비법</span>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 수호 천사의 기운 조언:</span>
(원국의 천을귀인·암록·학당귀인 등 나를 돕는 귀인 성분과 귀인 조력자를 활용하는 개운법을 제시하십시오)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 백년해로의 기운 조언:</span>
(배우자궁 일지 및 지장간 합/육친의 동태를 바탕으로 부부·연인 간 갈등을 피하고 인연을 지키는 백년해로 지혜를 조언하십시오)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 행운에 따른 기운 조언:</span>
(현재 대운 및 세운의 길한 파동을 타고 흉한 변곡점(충/형/묘고)을 우회하는 실질적인 행운 처세술을 조언하십시오)
</div>
"""
                try:
                    res = model.generate_content(prompt)
                    ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                    
                    if "[CHOYEON_GOLDEN_TEXT_HERE]" in ai_text:
                        ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)

                    un_html_clean = un_html.replace("\n", " ").replace("\r", "")
                    se_html_clean = se_html.replace("\n", " ").replace("\r", "")
                    wol_html_clean = wol_html.replace("\n", " ").replace("\r", "")

                    clean_ai_text = ai_text

                    daeoun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{un_html_clean}</div>"
                    sewun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{se_html_clean}</div>"
                    wolwun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{wol_html_clean}</div>"

                    # 운의 흐름 표 강제 삽입 처리
                    clean_ai_text, count_d = re.subn(r'[\#\*\_\s]*\[\s*DAEWUN_TABLE_HERE\s*\][\#\*\_\s]*', daeoun_target, clean_ai_text, flags=re.IGNORECASE)
                    clean_ai_text, count_s = re.subn(r'[\#\*\_\s]*\[\s*SEWUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                    clean_ai_text, count_w = re.subn(r'[\#\*\_\s]*\[\s*WOLWUN_TABLE_HERE\s*\][\#\*\_\s]*', wolwun_target, clean_ai_text, flags=re.IGNORECASE)

                    if count_d == 0:
                        clean_ai_text = re.sub(r'(<span[^>]*>1\) 대운의 흐름</span>)', r'\1\n' + daeoun_target, clean_ai_text, flags=re.IGNORECASE)
                    if count_s == 0:
                        clean_ai_text = re.sub(r'(<span[^>]*>2\) 세운의 흐름</span>)', r'\1\n' + sewun_target, clean_ai_text, flags=re.IGNORECASE)
                    if count_w == 0:
                        clean_ai_text = re.sub(r'(<span[^>]*>3\) 월운의 흐름</span>)', r'\1\n' + wolwun_target, clean_ai_text, flags=re.IGNORECASE)

                    full_content_clean = f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000;'>{clean_ai_text}<br><br>{closing_html}</div>"

                    report_1_full_html = report_1_full_html.replace("{full_content_clean_placeholder}", full_content_clean)
                    
                    st.session_state['saved_report_html'] = report_1_full_html
                    
                except Exception as e: 
                    st.error(f"AI 연산 오류: {e}")

            # ==============================================================
            # [B] 타 감명서 비교 (사주 / 궁합) 연산 분기
            # ==============================================================
            elif main_category == "4. 타 감명서 비교":
                try:
                    if u_product == "4-1. 타 감명서 비교 (사주)":
                        base_essay_text = clean_ai_text if 'clean_ai_text' in locals() else ""
                        
                        if compare_mode == "전통 명리학과 1:1 자동 대조":
                            comp_prompt = f"""
[SYSTEM ROLE: CHOYEON TRADITIONAL MASTER]
당신은 정통 명리심리상담사 '초연 박사'입니다.
아래 제공된 [{disp_name}님의 초연 전통명리 감명서 실제 본문]을 바탕으로, 일반 시중의 [A. 전통 명리 단식 풀이]와 [B. 초연 전통명리 정밀 풀이]의 깊이 차이를 항목별로 칼같이 1:1 대조 분석하십시오.

🚨 [대조 통변 절대 규칙]
0. 🚨 [인사말 원천 차단]: 출력의 첫 글자는 반드시 <h3 style=...> 태그로 시작해야 합니다. "안녕하십니까" 등의 서론을 엄금합니다.
1. [B. 초연 전통명리 정밀 풀이] 부분은 반드시 아래 제공된 [초연 전통명리 감명서 실제 본문]의 실제 분석 팩트와 논리를 직접 인용하여 정교하게 대조하십시오.
2. [A. 전통 명리 단식 풀이] 부분은 시중 철학관의 단순 오행/십성 표면적 해석의 한계를 명쾌히 짚어주십시오.
3. 모든 본문 문단은 HTML 태그인 <p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000000; text-indent: 1em; text-align: justify; margin-top: 4px; margin-bottom: 12px;'> 로 감싸하십시오.

[출력 목차 서식 정의]
<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 25px; margin-bottom: 8px; display:block;'>1. 타고난 성격 및 오행·조후 구조 대조</h3>
<p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000000; text-indent: 1em; text-align: justify; margin-top: 4px; margin-bottom: 12px;'><b>[A. 전통 명리 단식 풀이]</b> 일간 {ds} 중심의 단순 표면 성격 및 오행 개수(木:{counts['목']}, 火:{counts['화']}, 土:{counts['토']}, 金:{counts['금']}, 水:{counts['수']}) 단식 해석...</p>
<p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000000; text-indent: 1em; text-align: justify; margin-top: 4px; margin-bottom: 12px;'><b>[B. 초연 전통명리 정밀 풀이]</b> (위 실제 감명서의 월령 계절감({wol_korean_str}), 조후, 격국({gyukgook_detail}) 분석 팩트를 인용하여 정밀 대조)...</p>

<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 25px; margin-bottom: 8px; display:block;'>2. 원국 합충형해파·신살 및 공망 작용 대조</h3>
<p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000000; text-indent: 1em; text-align: justify; margin-top: 4px; margin-bottom: 12px;'><b>[A. 전통 명리 단식 풀이]</b> 합과 충의 단순 길흉 판단 및 일반적 신살 표면 해석...</p>
<p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000000; text-indent: 1em; text-align: justify; margin-top: 4px; margin-bottom: 12px;'><b>[B. 초연 전통명리 정밀 풀이]</b> (위 실제 감명서의 합충형해파({hap_chung_hyoung_pa_hae}) 육친 거리감, 공망 타격 궁위({gongmang_actual}), 신살({shinsal_str}) 팩트를 인용하여 정밀 대조)...</p>

<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 25px; margin-bottom: 8px; display:block;'>3. 동적 운(대운 및 세운)의 흐름과 변곡점 대조</h3>
<p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000000; text-indent: 1em; text-align: justify; margin-top: 4px; margin-bottom: 12px;'><b>[A. 전통 명리 단식 풀이]</b> 대운({dw_g_cur}{dw_j_cur})과 세운({curr_y_ganji}) 글자의 단순 길흉 및 십성 단식 예측...</p>
<p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000000; text-indent: 1em; text-align: justify; margin-top: 4px; margin-bottom: 12px;'><b>[B. 초연 전통명리 정밀 풀이]</b> (위 실제 감명서의 묘고 반응({hang_un_vaults_str})과 삼형살 변곡점({samhyung_warn}) 발복 팩트를 인용하여 정밀 대조)...</p>

<h3 style='color:#2E7D32; font-size: 20px; font-weight: 900; border-bottom: 2px solid #2E7D32; padding-bottom: 4px; margin-top: 25px; margin-bottom: 10px; display:block;'>4. 수석보좌관 종합 검증 및 앱 업데이트 제안 총평</h3>
<p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000000; text-indent: 1em; text-align: justify; margin-top: 4px; margin-bottom: 12px;'>
🚨 [수석보좌관 총평 절대 작성 규칙]
1. 정통 명리 논리 위배 검증: 제출된 타 감명서가 정통 명리학 이치(격국, 십성, 궁위, 신살)에 위배되거나 오류를 범한 핵심 요소를 객관적으로 지적하십시오.
2. 수용 및 타산지석 분석: 그럼에도 타 감명서에서 돋보이는 세련된 어휘, 현대적 카운슬링 어조, 내담자 공감 기법 등 우리가 수용하고 배워야 할 장점을 짚어내십시오.
3. 초연시공명리 앱 진화 제안: 타 감명서의 장점을 적극 흡수하여 박사님의 '초연시공명리' 시스템과 통변 엔진을 한 단계 더 진화시키기 위한 개발/업데이트 시사점을 결론으로 제시하십시오.
</p>

[초연 전통명리 감명서 실제 본문 팩트]
{base_essay_text[:3500]}
"""
                            c_res = call_claude_api(comp_prompt, max_tokens=10000)
                            
                            other_cover_html = (
                                f"<div class='page-break-before'></div>\n"
                                f"<div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>\n"
                                f"    <div style='border: 4px solid #2E7D32; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>\n"
                                f"        <div style='border-bottom:4px double #2E7D32; padding-bottom:20px; margin-bottom:40px;'>\n"
                                f"            <h1 class='title-gothic' style='font-size: 38px !important; margin:0 !important;'>전통 명리 학술 대조 리포트</h1>\n"
                                f"            <div style='text-align: right; margin-top: 10px;'>\n"
                                f"                <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px;'>{APP_VERSION}</span>\n"
                                f"            </div>\n"
                                f"        </div>\n"
                                f"        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>\n"
                                f"            <h2 style='font-size: 24px; font-weight: 800; color: #2E7D32; margin-bottom: 20px;'>👤 신청인 : {u_name} 님</h2>\n"
                                f"            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>\n"
                                f"                <p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p>\n"
                                f"            </div>\n"
                                f"        </div>\n"
                                f"        <p style='font-size: 18px; margin-top: 50px; font-weight: 800;'>{today_str}</p>\n"
                                f"        <p style='font-size: 22px; font-weight: 800; color: #2E7D32; margin-top: 20px;'>초연 전통명리 연구소</p>\n"
                                f"    </div>\n"
                                f"</div>"
                            )
                            st.session_state['saved_report_2'] = other_cover_html + f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#2E7D32;'><h1 style='text-align:center; color:#2E7D32; font-size: 26px; font-weight: 800; border-bottom:2px solid #2E7D32; padding-bottom:15px;'>⚖️ 전통 명리 학술 대조 리포트</h1><div style='margin-top:20px;'>{c_res}</div></div></div>"
                        else:
                            base_essay_text = clean_ai_text if 'clean_ai_text' in locals() else ""
                            
                            comp_prompt = f"""
[SYSTEM ROLE: CHOYEON SYSTEM CHIEF CHANCELLOR (초연시공명리 수석보좌관)]
당신은 '초연 박사님'을 보좌하는 수석보좌관 AI입니다.
제출된 {disp_name}님의 [외부 타 감명서 원문]을 박사님의 [초연시공명리 정밀 통변 팩트]와 1:1로 엄밀히 비교 대조하여 학술 검증 리포트를 작성하십시오.

🚨 [1:1 원문 대조 및 학술 검증 지시]
1. **타 감명서 목차/항목 구조 완벽 재현**: 제출된 타 감명서의 제목, 소목차, 분석 순서(예: 성격, 직업, 대운 등)를 그대로 가져와 동일한 순서로 목차를 구성하십시오.
2. **항목별 1:1 교차 검증**:
   - **[타 감명서 원문 분석]**: 원문의 주장과 통변 논리를 요약하십시오.
   - **[정통 명리 이치 검증 및 초연시공명리 재해석]**: 원문의 서술이 정통 명리 이치(격국: {gyukgook_detail}, 공망: {gongmang_actual}, 신살: {shinsal_str}, 묘고: {won_guk_vaults_str})에 위배되는지 검증하고, 오류를 정교하게 교정하십시오.
3. **학술적 수용 및 앱 진화 총평 작성**:
   - 마지막 목차인 **[4. 수석보좌관 종합 검증 및 앱 업데이트 제안 총평]**에서는 타 감명서의 논리적 오류를 검증함과 동시에, 타 감명서가 가진 우수한 카운슬링 어조나 배울 점을 수용하여 **'초연시공명리 앱 고도화 및 업데이트 방향'**을 종합적으로 제안하십시오.
4. **서식 통제**: 목차 제목은 <h3 style='color:#2E7D32; font-size: 20px; font-weight: 900; border-bottom: 2px solid #2E7D32; padding-bottom: 4px; margin-top: 25px; margin-bottom: 10px; display:block;'> 태그로, 문단은 <p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000000; text-indent: 1em; text-align: justify; margin-top: 4px; margin-bottom: 12px;'> 태그로 출력하십시오.

[제출된 타 감명서 원문 (목차 구조 및 분석 순서 기준점)]
{other_reading_text}

[초연시공명리 정밀 검증 근거 및 실제 감명서 팩트]
{base_essay_text[:3500]}
"""
                            c_res = call_claude_api(comp_prompt, max_tokens=10000)
                            
                            report_2_html = (
                                f"<div class='page-break-before'></div>\n"
                                f"<div class='report-page'>\n"
                                f"<div class='vip-inset-frame' style='border-color:#2E7D32; padding:20px;'>\n"
                                f"<h1 style='text-align:center; color:#2E7D32; font-size: 26px; font-weight: 900; border-bottom:2px solid #2E7D32; padding-bottom:15px; margin-bottom:20px;'>⚖️ 타 감명서 학술 검증 및 1:1 대조 리포트</h1>\n"
                                f"<div style='margin-top:20px;'>{c_res}</div>\n"
                                f"<hr style='border:1px dashed #2E7D32; margin:30px 0;'>\n"
                                f"<h3 style='color:#555; font-size:18px; font-weight:900; margin-bottom:10px;'>📜 [제출된 타 감명서 원문]</h3>\n"
                                f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 14px; line-height: 1.8; color: #444; background:#F9F9F9; padding:15px; border-radius:8px;'>{other_reading_text.replace(chr(10), '<br>')}</div>\n"
                                f"</div>\n"
                                f"</div>"
                            )
                            st.session_state['saved_report_2'] = report_2_html

                    elif u_product == "4-2. 타 감명서 비교 (궁합)":
                        m_name_val = u_name if u_gender == "남성" else p_name
                        f_name_val = p_name if u_gender == "남성" else u_name
                        
                        male_data_pack = applicant_bazi if u_gender == "남성" else partner_bazi
                        female_data_pack = partner_bazi if u_gender == "남성" else applicant_bazi

                        gh_engine = UniversalPrintableGunghap(m_name_val, f_name_val, male_data_pack, female_data_pack, 10)
                        gh_engine.run_universal_logic()

                        comp_prompt = f"""
[SYSTEM ROLE: CHOYEON SYSTEM CHANCELLOR (초연시공명리 수석보좌관)]
당신은 '초연 박사님'을 보좌하는 수석보좌관 AI입니다.
제출된 [{m_name_val}님과 {f_name_val}님의 외부 궁합 감명서 원문]을 박사님의 [초연시공명리 궁합 정밀 통변 팩트]와 1:1로 엄밀히 비교 대조하여 학술 검증 리포트를 작성하십시오.

🚨 [궁합 1:1 원문 대조 및 학술 검증 지시]
1. **타 궁합 감명서 목차/항목 구조 완벽 재현**: 제출된 타 감명서의 제목, 소목차, 분석 순서(예: 겉궁합, 속궁합, 오행보완, 운세교차 등)를 그대로 가져와 동일한 순서로 목차를 구성하십시오.
2. **항목별 1:1 교차 검증**:
   - **[타 궁합 감명서 원문 분석]**: 원문의 주장과 궁합 통변 논리를 요약하십시오.
   - **[정통 명리 이치 검증 및 초연시공명리 재해석]**: 원문의 궁합 판단이 정통 명리 이치 및 초연 정밀 궁합 점수({gh_engine.final_score}점)에 위배되는지 검증하고 오류를 교정하십시오.
3. **학술적 수용 및 앱 진화 총평 작성**:
   - 마지막 목차인 **[4. 수석보좌관 종합 검증 및 궁합 엔진 업데이트 제안 총평]**에서는 타 궁합 감명서의 논리적 오류를 검증함과 동시에, 타 감명서에서 배울 점을 수용하여 **'초연시공명리 궁합 엔진 고도화 방향'**을 종합적으로 제안하십시오.
4. 모든 본문 문단은 <p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000000; text-indent: 1em; text-align: justify; margin-top: 4px; margin-bottom: 12px;'> 태그로 출력하십시오.

[제출된 타 궁합 감명서 원문 (목차 구조 및 분석 순서 기준점)]
{other_reading_text}

[초연시공명리 정밀 궁합 팩트]
- 남성({m_name_val}) / 여성({f_name_val})
- 초연 궁합 정밀 점수: {gh_engine.final_score}점 ({gh_engine.grade})
"""
                        c_res = call_claude_api(comp_prompt, max_tokens=10000)
                        report_2_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#C62828; padding:20px;'><h1 style='text-align:center; color:#C62828; font-size: 26px; font-weight: 900; border-bottom:2px solid #C62828; padding-bottom:15px; margin-bottom:20px;'>⚖️ 타 궁합 감명서 학술 검증 및 1:1 대조 리포트</h1><div style='margin-top:20px;'>{c_res}</div></div></div>"
                        st.session_state['saved_report_2'] = report_2_html

                except Exception as e:
                    st.error(f"2단계 비교 분석 중 오류 발생: {e}")

            # ==============================================================
            # [C] 커플 연애/결혼운 (궁합) 풀이 연산 분기
            # ==============================================================
            elif main_category == "3. 커플 연애/결혼운 (궁합) 풀이":
                try:
                    p_klc = KoreanLunarCalendar()
                    if p_cal == "양력": p_klc.setSolarDate(p_y, p_m, p_d)
                    elif p_cal == "음력(평달)": p_klc.setLunarDate(p_y, p_m, p_d, False)
                    else: p_klc.setLunarDate(p_y, p_m, p_d, True)
                    
                    p_is_leap = getattr(p_klc, 'isIntercalary', False)
                    p_leap_str = "윤달" if p_is_leap else "평달"
                    p_sol_str = f"{p_klc.solarYear}년 {p_klc.solarMonth:02d}월 {p_klc.solarDay:02d}일"
                    p_lun_str = f"{p_klc.lunarYear}년 {p_klc.lunarMonth:02d}월 {p_klc.lunarDay:02d}일 ({p_leap_str})"
                    p_age = curr_y - p_y + 1
                    
                    p_base_dt = dt_mod.datetime(p_y, p_m, p_d, 12, 0)
                    p_gj = p_klc.getChineseGapJaString().split()
                    p_ys, p_yb, p_ms, p_mb, p_ds, p_db = p_gj[0][0], p_gj[0][1], p_gj[1][0], p_gj[1][1], p_gj[2][0], p_gj[2][1]
                    p_hs, p_hb = get_time_ganji(p_ds, p_t, p_base_dt)
                    partner_bazi = [f"{p_hs}{p_hb}", f"{p_ds}{p_db}", f"{p_ms}{p_mb}", f"{p_ys}{p_yb}"]

                    if u_gender == "남성":
                        m_name, m_sol, m_lun, m_time, m_age = u_name, sol_str, lun_str, time_str, u_age
                        m_gans, m_jjis = gans, jjis
                        m_ys, m_yb, m_ms, m_mb, m_ds, m_db, m_hs, m_hb = ys, yb, ms, mb, ds, db, hs, hb
                        m_calc_d, m_order = calc_d, order
                        
                        f_name, f_sol, f_lun, f_time, f_age = p_name, p_sol_str, p_lun_str, f" {p_t.split('(')[0].strip()} ({p_hb})시" if p_t != "시간 모름" else "", p_age
                        f_gans, f_jjis = [p_hs, p_ds, p_ms, p_ys], [p_hb, p_db, p_mb, p_yb]
                        f_ys, f_yb, f_ms, f_mb, f_ds, f_db, f_hs, f_hb = p_ys, p_yb, p_ms, p_mb, p_ds, p_db, p_hs, p_hb
                        p_utc_dt = p_base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=get_total_time_adjustment(p_base_dt))
                        p_order = 1 if (GAN.index(p_ys)%2==0) == (p_gender=='남성') else -1
                        f_calc_d, f_order = get_daeun_su_accurate(p_utc_dt, p_order), p_order
                        
                        male_data_pack, female_data_pack = applicant_bazi, partner_bazi
                    else:
                        m_name, m_sol, m_lun, m_time, m_age = p_name, p_sol_str, p_lun_str, f" {p_t.split('(')[0].strip()} ({p_hb})시" if p_t != "시간 모름" else "", p_age
                        m_gans, m_jjis = [p_hs, p_ds, p_ms, p_ys], [p_hb, p_db, p_mb, p_yb]
                        m_ys, m_yb, m_ms, m_mb, m_ds, m_db, m_hs, m_hb = p_ys, p_yb, p_ms, p_mb, p_ds, p_db, p_hs, p_hb
                        p_utc_dt = p_base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=get_total_time_adjustment(p_base_dt))
                        p_order = 1 if (GAN.index(p_ys)%2==0) == (p_gender=='남성') else -1
                        m_calc_d, m_order = get_daeun_su_accurate(p_utc_dt, p_order), p_order
                        
                        f_name, f_sol, f_lun, f_time, f_age = u_name, sol_str, lun_str, time_str, u_age
                        f_gans, f_jjis = gans, jjis
                        f_ys, f_yb, f_ms, f_mb, f_ds, f_db, f_hs, f_hb = ys, yb, ms, mb, ds, db, hs, hb
                        f_calc_d, f_order = calc_d, order
                        
                        male_data_pack, female_data_pack = partner_bazi, applicant_bazi

                    curr_j = JI[((curr_y - 1984) % 60) % 12]

                    def get_counts(t_gans, t_jjis):
                        c = {"목":0,"화":0,"토":0,"금":0,"수":0}
                        for x in t_gans + t_jjis:
                            if x != "?": c[get_color(x)] += 1
                        return c

                    m_cnt, f_cnt = get_counts(m_gans, m_jjis), get_counts(f_gans, f_jjis)

                    m_name = m_name.replace("+", "").strip()
                    f_name = f_name.replace("+", "").strip()

                    def build_bazi_table(gender_icon, name, gender_str, marital_str, age, sol, lun, time, t_gans, t_jjis, t_ds, t_yb, counts, guiin, y_gong, d_gong, samjae, daeun_su, color):
                        ji_rel_rows = ""
                        for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                            b_bot = "1px solid #444 !important" if l_idx == 3 else "none !important"
                            cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(t_jjis[r_idx], t_jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:none !important; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'><span style='color:inherit !important;'>{('←('+t_jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(t_jjis[r_idx], t_jjis[ci]))}</span></td>" for ci in range(4)])
                            lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important;'><span style='color:inherit !important;'>합충형파해</span></td>" if l_idx==0 else ""
                            ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

                        info_str = f"<div style='text-align:center; margin-bottom:15px; font-family:\"Malgun Gothic\", sans-serif;'><span style='font-size:18px; font-weight:900; color:{color};'>{gender_icon} {name}님 ({gender_str}, {marital_str}, {age}세)</span><br><span style='font-size:14px; font-weight:900; color:#222;'>[양력] {sol} | [음력] {lun}{time}</span></div>"
                        
                        def td(c): return f"<td class='color-{get_color(c)}' style='font-size:20px; font-weight:900; border:1px solid #444 !important;'><span style='color:inherit !important;'>{('?' if c in ['?',' ','-'] else c)}</span></td>"
                            
                        return (
                            f"{info_str}\n"
                            f"<table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>\n"
                            f"<tr class='top-header-cell'>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:#FFFFFF !important;'>구분</span></td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:#FFFFFF !important;'>시주</span></td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:#FFFFFF !important;'>일주</span></td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:#FFFFFF !important;'>월주</span></td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:#FFFFFF !important;'>년주</span></td>\n"
                            f"</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:inherit !important;'>천간십성</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(t_ds,t_gans[0])}</span></td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(t_ds,t_gans[2])}</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(t_ds,t_gans[3])}</span></td></tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:inherit !important;'>천간</span></td>{td(t_gans[0])}{td(t_gans[1])}{td(t_gans[2])}{td(t_gans[3])}</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:inherit !important;'>지지</span></td>{td(t_jjis[0])}{td(t_jjis[1])}{td(t_jjis[2])}{td(t_jjis[3])}</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:inherit !important;'>지지십성</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(t_ds,t_jjis[0])}</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(t_ds,t_jjis[1])}</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(t_ds,t_jjis[2])}</span></td><td style='border:1px solid #444;'><span style='color:inherit !important;'>{get_ss(t_ds,t_jjis[3])}</span></td></tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; padding:0; font-size:15px !important; white-space:nowrap;'><span style='color:inherit !important;'>지장간</span></td>{''.join([f'<td style=\"border:1px solid #444; padding:0;\"><span style=\"color:inherit !important;\">{get_jijanggan_full(t_ds, t_jjis[i])}</span></td>' for i in range(4)])}</tr>\n"
                            f"{ji_rel_rows}\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:inherit !important;'>십이운성</span></td>{''.join([f'<td style=\"border:1px solid #444; color:#0D47A1; font-weight:bold;\"><span style=\"color:inherit !important;\">{get_unsung(t_ds, t_jjis[i])}</span></td>' for i in range(4)])}</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:inherit !important;'>십이신살</span></td>{''.join([f'<td style=\"border:1px solid #444; color:#C62828; font-weight:bold;\"><span style=\"color:inherit !important;\">{get_12_shinsal(t_yb, t_jjis[i])}</span></td>' for i in range(4)])}</tr>\n"
                            f"</table>\n"
                            f"<div style='border:2px solid {color}; margin-top:10px; margin-bottom:20px; padding:6px 8px; display:flex; justify-content:space-between; align-items:center; font-weight:900; font-size:11px; letter-spacing:-0.5px; border-radius:8px; background-color:#FAFAFA;'><div style='white-space:nowrap;'>🔢 대운수: {daeun_su}</div><div style='white-space:nowrap;'>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div style='white-space:nowrap;'>🌟 천을귀인: <span style='color:{color};'>{guiin}</span></div><div style='white-space:nowrap;'>🎯 공망: [년] <span style='color:#C62828;'>{y_gong}</span> [일] <span style='color:#C62828;'>{d_gong}</span></div><div style='white-space:nowrap;'>🌪️ 삼재: {samjae}</div></div>"
                        )

                    m_marital = u_marital if u_gender == "남성" else p_marital
                    f_marital = p_marital if u_gender == "남성" else u_marital
                    
                    guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
                    
                    m_tbl = build_bazi_table("♂️", m_name, "남명", m_marital, m_age, m_sol, m_lun, m_time, m_gans, m_jjis, m_ds, m_yb, m_cnt, guiin_map.get(m_ds, '-'), calculate_gongmang(m_ys, m_yb), calculate_gongmang(m_ds, m_db), get_samjae(m_yb, curr_j), m_calc_d, "#1A237E")
                    f_tbl = build_bazi_table("♀️", f_name, "여명", f_marital, f_age, f_sol, f_lun, f_time, f_gans, f_jjis, f_ds, f_yb, f_cnt, guiin_map.get(f_ds, '-'), calculate_gongmang(f_ys, f_yb), calculate_gongmang(f_ds, f_db), get_samjae(f_yb, curr_j), f_calc_d, "#2E7D32")
                    
                    def build_daewun_html(name, t_ds, t_ms, t_mb, t_yb, t_calc_d, t_order, age, color):
                        d_str = "순행" if t_order == 1 else "역행"
                        html = f"<div style='margin-bottom:10px;'><div style='font-size:15px; font-weight:900; color:{color}; margin-bottom:5px;'>[ {name}님 대운 흐름표 (대운수: {t_calc_d}), {d_str} ]</div>"
                        html += f"<div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white;'>"
                        for i in range(10):
                            val = i*10 + t_calc_d
                            tc = GAN[(GAN.index(t_ms)+(i+1)*t_order)%10]
                            tj = JI[(JI.index(t_mb)+(i+1)*t_order)%12]
                            bg = "#FFF9C4" if val <= age < val+10 else "transparent"
                            brd = "1px solid #ccc" if i != 9 else "none"
                            html += f"<div style='flex:1; border-left:{brd}; text-align:center; padding-bottom:3px; background-color:{bg};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:11px; border-bottom:1px solid #ccc;'>{val}세</div><div style='padding:2px; font-size:11px;'>{get_ss(t_ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:15px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:15px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:11px;'>{get_ss(t_ds,tj)}</div><div style='font-size:10px; border-top:1px solid #eee;'>{get_unsung(t_ds,tj)}</div><div style='font-size:10px; color:#C62828; border-top:1px solid #eee;'>{get_12_shinsal(t_yb, tj)}</div></div>"
                        return html + "</div></div>"

                    m_page_un_html = build_daewun_html(m_name, m_ds, m_ms, m_mb, m_yb, m_calc_d, m_order, m_age, "#1A237E")
                    f_page_un_html = build_daewun_html(f_name, f_ds, f_ms, f_mb, f_yb, f_calc_d, f_order, f_age, "#2E7D32")
                    
                    couple_daewun_tables = f"<div style='margin-bottom: 25px;'>{m_page_un_html}<div style='height:20px;'></div>{f_page_un_html}</div>"

                    ilju_struct_db = choyeon_db.get("ilju_structure", {})

                    m_ilju_key = f"{m_ds}{m_db}"
                    m_struct_data = ilju_struct_db.get(m_ilju_key, [])
                    m_action_type = m_struct_data[1] if len(m_struct_data) >= 3 else "자율활동형"
                    m_main_tendency = m_struct_data[2] if len(m_struct_data) >= 3 else "독자적인 삶의 무대를 개척하는"
                    m_gy_name, m_gy_desc = get_gyukgook_detailed(m_ds, m_ys, m_ms, m_hs, m_mb)

                    m_traditional_text_html = f"""
                    <div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000; margin-bottom: 20px;'>
                        <p style='text-indent: 15px; margin-bottom: 5px;'>
                            정통 명리학적으로 풀이하면 <b>{m_name}님</b>은 <b>{m_mb}월</b>에 <b>'{m_gy_name}'</b>의 그릇을 갖추고 태어나셨으며, 성격은 <b>'{m_action_type}'</b>으로 <b>'{m_main_tendency}'</b> 성향이 있습니다.
                        </p>
                    </div>
                    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
                    """

                    f_ilju_key = f"{f_ds}{f_db}"
                    f_struct_data = ilju_struct_db.get(f_ilju_key, [])
                    f_action_type = f_struct_data[1] if len(f_struct_data) >= 3 else "자율활동형"
                    f_main_tendency = f_struct_data[2] if len(f_struct_data) >= 3 else "독자적인 삶의 무대를 개척하는"
                    f_gy_name, f_gy_desc = get_gyukgook_detailed(f_ds, f_ys, f_ms, f_hs, f_mb)

                    f_traditional_text_html = f"""
                    <div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000; margin-bottom: 20px;'>
                        <p style='text-indent: 15px; margin-bottom: 5px;'>
                            정통 명리학적으로 풀이하면 <b>{f_name}님</b>은 <b>{f_mb}월</b>에 <b>'{f_gy_name}'</b>의 그릇을 갖추고 태어나셨으며, 성격은 <b>'{f_action_type}'</b>으로 <b>'{f_main_tendency}'</b> 성향이 있습니다.
                        </p>
                    </div>
                    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
                    """

                    gh_engine = UniversalPrintableGunghap(u_name, p_name, male_data_pack, female_data_pack, 10)
                    gh_engine.run_universal_logic()
                    
                    essay_prompt = f"""[SYSTEM ROLE: CHOYEON TRADITIONAL MASTER]
당신은 정통 명리심리상담사 '초연 박사'입니다.

🚨 [출력 절대 형식 및 내용 생성 규칙]
1. 각 소제목 아래에 절대로 안내 문구를 그대로 복사해서 출력하지 마십시오!
2. 반드시 내담자의 명리적 특징을 분석하여 3~4문장 분량의 실제 통변 내용을 직접 작성해야 합니다.
3. 모든 통변 문장은 HTML 태그 <p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'> 로 감싸하십시오.

[MALE_START]
<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; margin-top: 15px;'>1. 성격 및 가치관</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
(이곳에 남성의 사회적 표면 성격을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>
(이곳에 남성의 내면과 무의식을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>3) 무의식이 갈망하는 반려자의 상</span>
(남성의 연애 및 결혼관을 실제 에세이로 작성)

<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; margin-top: 15px;'>2. 사주팔자의 요약</h3>
{m_traditional_text_html}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(이곳에 남성의 정통 명리적 성향을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>
(이곳에 남성의 오행 및 조후 에너지를 분석한 실제 에세이 작성)
[MALE_END]

[FEMALE_START]
<h3 style='color:#D50000; font-size: 22px; font-weight: 900; margin-top: 15px;'>1. 성격 및 가치관</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
(이곳에 여성의 사회적 표면 성격을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>
(이곳에 여성의 내면과 무의식을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>3) 무의식이 갈망하는 반려자의 상</span>
(여성의 연애 및 결혼관을 실제 에세이로 작성)

<h3 style='color:#D50000; font-size: 22px; font-weight: 900; margin-top: 15px;'>2. 사주팔자의 요약</h3>
{f_traditional_text_html}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(이곳에 여성의 정통 명리적 성향을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>
(이곳에 여성의 오행 및 조후 에너지를 분석한 실제 에세이 작성)
[FEMALE_END]

[GUNGHAP_START]
<h3 style='color: #1B5E20; font-size: 22px; font-weight: 900; margin-top: 10px;'>🍀 두 사람의 운명적 만남에 대하여</h3>
(이곳에 두 사람의 인연 총평을 깊이 있게 통변한 실제 에세이 작성)

<h3 style='color: #1A237E; font-size: 22px; font-weight: 900; margin-top: 25px;'>🌈 커플의 인생 기상도 분석</h3>
[COUPLE_DAEWUN_TABLES_HERE]
(이곳에 상하 대운 교차점에 따른 상생/보완을 분석한 실제 에세이 작성)

<h4 style='color: #1A237E; font-size: 18px; font-weight: 900; margin-top: 25px;'>💞 커플의 상생과 조화 궁합 분석</h4>
(이곳에 속궁합, 겉궁합, 오행 궁합을 통합 분석한 실제 에세이 작성)

<h4 style='color: #1A237E; font-size: 18px; font-weight: 900; margin-top: 25px;'>⚓ 조율의 지혜</h4>
(이곳에 갈등 극복 및 개운 처방을 담은 실제 에세이 작성)
[GUNGHAP_END]
"""
                    res_text = call_claude_api(essay_prompt, max_tokens=12000)
                    ai_clean = "\n".join([line.lstrip() for line in res_text.split("\n")])
                    
                    import re
                    m_ess, f_ess, g_ess = "", "", ai_clean
                    
                    m_match = re.search(r'\[MALE_START\](.*?)\[MALE_END\]', ai_clean, re.DOTALL)
                    if m_match: m_ess = m_match.group(1).strip()
                    
                    f_match = re.search(r'\[FEMALE_START\](.*?)\[FEMALE_END\]', ai_clean, re.DOTALL)
                    if f_match: f_ess = f_match.group(1).strip()
                    
                    g_match = re.search(r'\[GUNGHAP_START\](.*?)\[GUNGHAP_END\]', ai_clean, re.DOTALL)
                    if g_match: 
                        g_ess = g_match.group(1).strip()
                    else:
                        g_ess = ai_clean.replace(m_ess, "").replace(f_ess, "").replace("[MALE_START]", "").replace("[MALE_END]", "").replace("[FEMALE_START]", "").replace("[FEMALE_END]", "")
                    
                    import re
                    g_ess, count = re.subn(r'\[\s*COUPLE_DAEWUN_TABLES_HERE\s*\]', couple_daewun_tables, g_ess, flags=re.IGNORECASE)
                    if count == 0:
                        g_ess = re.sub(r'(<h3[^>]*>🌈 커플의 인생 기상도 분석</h3>)', r'\1\n<div style="margin-top:15px;">' + couple_daewun_tables + '</div>', g_ess)

                    def wrap_a4(content, title_color="#1A237E", title="[ 초연 전통 명리사주 풀이 ]"):
                        return (
                            f"<div class='report-page'>\n"
                            f"<div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'>\n"
                            f"<h1 style='text-align:center; color:{title_color}; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; border-bottom:2px solid {title_color}; padding-bottom:15px; margin-bottom:30px;'>{title}</h1>\n"
                            f"{content}\n"
                            f"</div>\n"
                            f"</div>"
                        )

                    t_col = "#3498db" if gh_engine.final_score >= 70 else ("#f39c12" if gh_engine.final_score >= 60 else "#e74c3c")
                    bars = "".join([f"<div style='display:flex; align-items:center; margin-bottom:12px;'><div style='width:130px; font-size:13px; font-weight:bold; color:#555;'>{d['label']}</div><div style='flex:1; height:12px; margin:0 10px;'><svg width='100%' height='12'><rect width='100%' height='12' rx='6' ry='6' fill='#eee' /><rect width='{d['pct']}%' height='12' rx='6' ry='6' fill='{d['color']}' /></svg></div><div style='width:35px; font-size:12px; font-weight:bold;'>{d['pct']}%</div></div>" for d in gh_engine.details])
                    
                    closing_original = (
                        f"<div style='margin-top: 40px; padding-top: 30px; page-break-inside: avoid;'>\n"
                        f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333;'>&nbsp;&nbsp;&nbsp;&nbsp;두 분의 <b style='color:#1A237E;'>'만남'</b>은 결코 우연이 아닌, <b style='color:#1A237E;'>'수많은 인연의 이치 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 명식이지만, <b style='color:#1A237E;'>'궁합(宮合)'</b>은 두 명식이 만나 그려내는 새로운 <b style='color:#1A237E;'>'조화와 상생'</b>입니다.</p>\n"
                        f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333; margin-top: 10px;'>&nbsp;&nbsp;&nbsp;&nbsp;서로의 기운을 보완하고 다독여주는 든든한 <b style='color:#1A237E;'>'반려자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 전통 명리의 축복이 가득하시길 소망합니다.</p>\n"
                        f"<div style='text-align: right; margin-top: 25px;'><span style='font-weight: 900; font-size: 16px; color: #1A237E; font-family: \"Nanum Myeongjo\", serif;'>- 초연 전통명리 연구소 드림 -</span></div>\n"
                        f"</div>"
                    )

                    g_full_content = (
                        f"<div class='choyeon-premium-report'>\n{g_ess}\n</div>\n"
                        f"<h2 style='text-align:center; margin-top:40px; font-size:22px; font-weight:900;'>📊 최종 궁합 점수</h2>\n"
                        f"<div style='display:flex; justify-content:center; align-items:center; margin:20px 0;'>\n"
                        f"<div style='width:130px; height:130px; border-radius:50%; background:conic-gradient({t_col} {gh_engine.final_score}%, #eee 0); display:flex; justify-content:center; align-items:center; -webkit-print-color-adjust: exact;'>\n"
                        f"<div style='width:98px; height:98px; background:#fff; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center;'>\n"
                        f"<span style='font-size:32px; font-weight:900; color:{t_col};'>{gh_engine.final_score}</span>\n"
                        f"<span style='font-size:10px; color:#888; font-weight:bold;'>SCORE</span>\n"
                        f"</div>\n"
                        f"</div>\n"
                        f"</div>\n"
                        f"<div style='text-align:center; margin-bottom:20px;'><span style='font-size:16px; font-weight:bold; color:#fff; background:{t_col}; padding:8px 32px; border-radius:30px; -webkit-print-color-adjust: exact;'>{gh_engine.grade}</span></div>\n"
                        f"<div style='max-width:500px; margin:0 auto;'>\n{bars}\n</div>\n"
                        f"{closing_original}"
                    )

                    cover_html = (
                        f"<div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>\n"
                        f"    <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>\n"
                        f"        <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>\n"
                        f"            <h1 class='title-gothic' style='font-size: 36px !important; margin:0 !important;'>초연 전통 명리궁합 풀이</h1>\n"
                        f"            <div style='text-align: right; margin-top: 10px;'>\n"
                        f"                <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px;'>{APP_VERSION}</span>\n"
                        f"            </div>\n"
                        f"        </div>\n"
                        f"        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 15px; margin-bottom: 20px;'>\n"
                        f"            <h2 style='font-size: 24px; font-weight: 800; color: #1A237E; margin-bottom: 15px;'>♂️ 남명 : {m_name} 님 <span style='font-size:16px; color:#555;'>( {m_age}세 )</span></h2>\n"
                        f"            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>\n"
                        f"                <p style='margin: 0; white-space: nowrap;'>[양력] {m_sol} | [음력] {m_lun}</p>\n"
                        f"            </div>\n"
                        f"        </div>\n"
                        f"        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 15px;'>\n"
                        f"            <h2 style='font-size: 24px; font-weight: 800; color: #D50000; margin-bottom: 15px;'>♀️ 여명 : {f_name} 님 <span style='font-size:16px; color:#555;'>( {f_age}세 )</span></h2>\n"
                        f"            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>\n"
                        f"                <p style='margin: 0; white-space: nowrap;'>[양력] {f_sol} | [음력] {f_lun}</p>\n"
                        f"            </div>\n"
                        f"        </div>\n"
                        f"        <p style='font-size: 18px; margin-top: 40px; font-weight: 800;'>{today_str}</p>\n"
                        f"        <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 전통명리 연구소</p>\n"
                        f"    </div>\n"
                        f"</div>"
                    )
                    st.session_state['saved_report_gh_cover'] = cover_html

                    m_page_content = f"{m_tbl}\n<div class='choyeon-premium-report' style='margin-top:20px;'>\n{m_ess}\n</div>"
                    f_page_content = f"{f_tbl}\n<div class='choyeon-premium-report' style='margin-top:20px;'>\n{f_ess}\n</div>"
                    
                    st.session_state['saved_report_gh_m'] = wrap_a4(m_page_content, "#1A237E", "[ 남명 사주팔자표 및 요약 ]")
                    st.session_state['saved_report_gh_f'] = wrap_a4(f_page_content, "#D50000", "[ 여명 사주팔자표 및 요약 ]")
                    st.session_state['saved_report_gh_g'] = wrap_a4(g_full_content, "#1B5E20", "[ 초연 전통명리 종합 궁합풀이 ]")
                    
                except Exception as e:
                    st.error(f"3단계 궁합 종합 분석 가동 장애: {e}")

            st.session_state['need_calc'] = False

        except Exception as e: 
            st.error(f"시스템 연산 중 치명적 오류 발생: {e}")
            st.session_state['need_calc'] = False
            st.stop()

# ==============================================================================
# 🌊 7. [독립 모듈] 일진 분석 (결과 출력부)
# ==============================================================================
if st.session_state.get('app_running', False) and st.session_state.get('run_waterfall', False) and 'global_gans' in st.session_state:
    
    if not st.session_state.get('saved_report_iljin'):
        
        if st.session_state.get('saved_report_html'):
            st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
            
        t_date = st.session_state['target_date']
        
        gans_list = st.session_state['global_gans']
        jjis_list = st.session_state['global_jjis']
        m_ilgan = st.session_state['global_ds']
        m_ilji = st.session_state['global_db']
            
        def get_execution_yong(upper_group, lower_group):
            matrix = {'비겁': {'비겁':'비겁', '식상':'식상', '재성':'재성', '관성':'관성', '인성':'인성'}, '식상': {'비겁':'인성', '식상':'비겁', '재성':'식상', '관성':'재성', '인성':'관성'}, '재성': {'비겁':'관성', '식상':'인성', '재성':'비겁', '관성':'식상', '인성':'재성'}, '관성': {'비겁':'재성', '식상':'관성', '재성':'인성', '관성':'비겁', '인성':'식상'}, '인성': {'비겁':'식상', '식상':'재성', '재성':'관성', '관성':'인성', '인성':'비겁'} }
            return matrix.get(upper_group, {}).get(lower_group, '비겁')

        def get_gan_rel_simple(g1, g2):
            if not g1 or not g2 or g1=="?" or g2=="?": return "-"
            s = {g1, g2}
            if s in [{'甲','己'}, {'乙','庚'}, {'丙','辛'}, {'丁','壬'}, {'戊','癸'}]: return "합(合)"
            if s in [{'甲','庚'}, {'乙','辛'}, {'丙','壬'}, {'丁','癸'}]: return "충(沖)"
            극_dict = {'甲':'戊', '乙':'己', '丙':'庚', '丁':'辛', '戊':'壬', '己':'癸', '庚':'甲', '辛':'乙', '壬':'丙', '癸':'丁'}
            if 극_dict.get(g1) == g2 or 극_dict.get(g2) == g1: return "극(剋)"
            return "-"
            
        def get_ji_rel_set_simple(j1, j2):
            if not j1 or not j2 or j1 == "?" or j2 == "?": return "-"
            s = {j1, j2}
            if s in [{'子','丑'}, {'寅','亥'}, {'卯','戌'}, {'辰','酉'}, {'巳','申'}, {'午','未'}]: return "육합"
            if s in [{'子','午'}, {'丑','未'}, {'寅','申'}, {'卯','酉'}, {'辰','戌'}, {'巳','亥'}]: return "충"
            if s in [{'子','未'}, {'丑','午'}, {'寅','酉'}, {'卯','申'}, {'辰','亥'}, {'巳','戌'}]: return "원진"
            if s in [{'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}, {'子','卯'}]: return "형"
            return "-"

        dklc = KoreanLunarCalendar()
        dklc.setSolarDate(t_date.year, t_date.month, t_date.day)
        gj_str = dklc.getChineseGapJaString()
        
        if gj_str:
            parts = gj_str.split()
            target_year = parts[0][:2]
            target_wol = parts[1][:2]
            target_il = parts[2][:2]
            
            gan_res = []
            labels_gan = ["년간", "월간", "일간", "시간"]
            for idx, label in enumerate(labels_gan):
                rel = get_gan_rel_simple(gans_list[idx], target_il[0])
                if rel != "-":
                    gan_res.append(f"☁️ <b>{label}({gans_list[idx]})</b> → <span style='color:#1976D2; font-weight:bold;'>천간 {rel}</span>")
            gan_res_html = '<br>'.join(gan_res) if gan_res else '특이 천간 파동 없음'

            r_res = []
            labels_ji = ["년지", "월지", "일지", "시지"]
            for idx, label in enumerate(labels_ji):
                rel_full = get_ji_rel_set_simple(jjis_list[idx], target_il[1])
                if rel_full != "-":
                    r_res.append(f"🌊 <b>{label}({jjis_list[idx]})</b> → <span style='color:#D50000; font-weight:bold;'>{rel_full}</span>")

            r_res_html = '<br>'.join(r_res) if r_res else '특이 지지 파동 없음'

            iljin_prompt = f"""
당신은 정통 명리심리상담사 초연 박사입니다. 아래의 정밀 연산된 팩트를 바탕으로 오늘 하루(일진)의 흐름을 날카롭게 분석하십시오.
- 내담자 일주: {m_ilgan}{m_ilji}
- 일진 날짜: {t_date.year}년 {t_date.month}월 {t_date.day}일 ({target_year}년 {target_wol}월 {target_il}일)
- 천간 파동: {gan_res_html}
- 지지 형충파해: {r_res_html}

[출력 템플릿]
<br><b>🌅 전반부 (자시~오시):</b> (내용 상세 작성)
<br><b>🌃 후반부 (미시~야자시):</b> (내용 상세 작성)
"""
            with st.spinner("⏳ 메인 사주풀이 보존 완료! 하단에 [일진 정밀 분석] 추가 가동 중..."):
                try:
                    res = model.generate_content(iljin_prompt)
                    ai_iljin_html = res.text.strip().replace("\n", "<br>")
                except Exception as e:
                    ai_iljin_html = f"<div style='color:red;'>🚨 AI 일진 분석 장애: {e}</div>"

            html_output = (
                f"<div class='page-break-before'></div>\n"
                f"<div class='report-page'>\n"
                f"<div class='vip-inset-frame' style='border: 3px solid #1A237E;'>\n"
                f"<h1 style='text-align: center; color: #1A237E;'>🔮 일진 정밀 분석서 {APP_VERSION}</h1>\n"
                f"<div style='text-align: center; font-size: 16px; font-weight: bold; color: #555; margin-bottom: 20px;'>대상일자: {t_date}</div>\n"
                f"<div class='content-box-loose' style='font-size: 15px; line-height: 1.8;'>{ai_iljin_html}</div>\n"
                f"</div>\n"
                f"</div>"
            )
            st.session_state['saved_report_iljin'] = html_output
            st.rerun()

# ==============================================================================
# 👶 8. [독립 모듈] 출산택일 정밀 분석
# ==============================================================================
if st.session_state.get('app_running', False) and st.session_state.get('run_delivery_only', False) and 'global_gans' in st.session_state:
    with st.spinner("⏳ [출산택일 분석실] 최적의 길일 연산 및 AI 통변 중..."):
        try:
            gans = st.session_state['global_gans']
            jjis = st.session_state['global_jjis']
            p_bazi_context = st.session_state.get('partner_bazi', ["?", "?", "?", "?"])
            
            if u_gender == "남성":
                m_jjis = jjis
                f_jjis = [b[1] if len(b)>1 else "?" for b in p_bazi_context]
            else:
                m_jjis = [b[1] if len(b)>1 else "?" for b in p_bazi_context]
                f_jjis = jjis

            FORBIDDEN_LIST = ['병오', '임자', '계해', '신유', '경신']
            delivery_days = get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, FORBIDDEN_LIST)
            
            del_content = f"<h2 style='text-align:center;'>👶 새 생명 마중 길일 추천</h2>\n<p>부모님의 사주와 조화를 이루는 길일입니다.</p>\n"
            for day_info in delivery_days:
                del_content += f"<div>✅ {day_info['date']} (합 점수: {day_info['score']})</div>\n"
            
            delivery_prompt = f"""
당신은 정통 명리심리상담사 초연 박사입니다. 부모의 사주 기운을 바탕으로 최고의 프리미엄 출산 희망일을 선정하여 전통 명리 에세이로 풀어내십시오.
- 부모 원국: {gans}{jjis} / {p_bazi_context}
- 탐색 기간: {start_date} ~ {end_date} / 태아 성별: {baby_gender}
"""
            del_res = model.generate_content(delivery_prompt)
            ai_delivery_html = del_res.text.strip().replace("\n", "<br>")
            del_content += f"<div class='content-box-loose' style='font-size:15px; line-height:1.8; margin-top:20px;'>\n{ai_delivery_html}\n</div>"

            def wrap_a4(content, title_color="#1A237E", title="[ 초연 전통 명리사주 풀이 ]"):
                return f"<div class='report-page'>\n<div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'>\n<h1 style='text-align:center; color:{title_color}; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; border-bottom:2px solid {title_color}; padding-bottom:15px; margin-bottom:30px;'>{title}</h1>\n{content}\n</div>\n</div>"

            st.session_state['saved_report_del'] = wrap_a4(del_content, "#4A148C", "[ 초연 전통명리 출산택일 ]")
            st.session_state['run_delivery_only'] = False
        except Exception as e:
            st.error(f"출산택일 연산 장애: {e}")
            st.session_state['run_delivery_only'] = False

# ==============================================================================
# 9. 화면 출력부 (세분화 카테고리 대응 수정 완결)
# ==============================================================================
if st.session_state.get('app_running', False):
    
    # 1. 개인 사주 및 특성화 상품 출력
    if main_category in ["1. 개인 사주팔자 풀이 (종합)", "2. 테마별 특성화 상담"]:
        if st.session_state.get('saved_report_html'):
            st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
        if st.session_state.get('saved_report_iljin'):
            st.markdown(st.session_state.get('saved_report_iljin', ''), unsafe_allow_html=True)
    
    # 2. 타 감명서 대조 출력
    if main_category == "4. 타 감명서 비교":
        if st.session_state.get('saved_report_html'):
            st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
        if st.session_state.get('saved_report_2'):
            st.markdown(st.session_state.get('saved_report_2', ''), unsafe_allow_html=True)
        
    # 3. 궁합 및 택일 출력
    if main_category == "3. 커플 연애/결혼운 (궁합) 풀이":
        if st.session_state.get('saved_report_gh_cover'):
            st.markdown(st.session_state.get('saved_report_gh_cover', ''), unsafe_allow_html=True)
            st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
            
        if st.session_state.get('saved_report_gh_m'):
            st.markdown(st.session_state.get('saved_report_gh_m', ''), unsafe_allow_html=True)
            st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)

        if st.session_state.get('saved_report_gh_f'):
            st.markdown(st.session_state.get('saved_report_gh_f', ''), unsafe_allow_html=True)
            st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)

        if st.session_state.get('saved_report_gh_g'):
            st.markdown(st.session_state.get('saved_report_gh_g', ''), unsafe_allow_html=True)

        if st.session_state.get('saved_report_del'):
            st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
            st.markdown(st.session_state.get('saved_report_del', ''), unsafe_allow_html=True)
