# ==============================================================================
# app.py (ver 60.0 Master - 초연 전통명리 완결판) 일지 신살 추가
# ====================================================================
import streamlit as st
import pandas as pd
import json
import os
import math
import calendar
import time  
import datetime as dt_mod
from datetime import datetime
from korean_lunar_calendar import KoreanLunarCalendar
import ephem
from google import genai
import pytz
import streamlit.components.v1 as components
import re

# ==============================================================================
# 🎯 [버전 컨트롤 타워]
# ==============================================================================
APP_VERSION = "Ver 60.0 (Master & 14종 세분화 완결본)"

# ==============================================================================
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS (ver 50.5 원본 유지 + 백지 차단/대제목 위엄 추가)
# ==============================================================================
st.set_page_config(page_title=f"초연 전통 명리 {APP_VERSION}", layout="wide")

st.markdown("""<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800;900&display=swap');

    .stApp { background-color: #E8F5E9 !important; }
    
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

    /* 🌟 [신규 추가] 본문 대제목(h1)의 위엄 살리기 (진한 남색 밑줄) */
    .report-page h1:not(.cover-page h1) {
        font-size: 26px !important;
        font-weight: 900 !important;
        color: #1A237E !important;
        text-align: center !important;
        border-bottom: 3px solid #1A237E !important;
        padding-bottom: 10px !important;
        margin-bottom: 25px !important;
        margin-top: 0 !important;
        letter-spacing: -0.5px !important;
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

    /* Secondary 버튼 (인쇄/저장 - 초록색 #00A843) */
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

    /* 🚨 [PDF 인쇄 오류 완벽 차단용 수정] 🚨 */
    @media print { 
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; }
        
        /* 🚨 [수술 완료] 스트림릿 고유의 쓸데없는 상단 여백 완벽 제거 (빈 페이지 발생 원천 차단) */
        .block-container, div[data-testid="stAppViewBlockContainer"] { padding-top: 0 !important; padding-bottom: 0 !important; margin-top: 0 !important; margin-bottom: 0 !important; }
        div[data-testid="stVerticalBlock"] { gap: 0 !important; }
        .element-container, .stMarkdown { margin-bottom: 0 !important; }
        
        .report-page { box-shadow: none; margin: 0 auto; padding: 0; page-break-after: always; border-radius: 0; width: 100%; max-width: 100%; }
        .report-page:last-of-type { page-break-after: auto; }
        .page-break-before { page-break-before: always; }
        
        /* 🚨 [프레임 분할 닫기 적용] 매 페이지마다 테두리가 새로 열리고 닫히도록 복제(clone) */
        .vip-inset-frame { 
            border: 2px solid #000 !important; 
            border-radius: 20px !important; 
            padding: 15px !important; 
            box-decoration-break: clone !important; 
            -webkit-box-decoration-break: clone !important; 
        }
    }
</style>
""", unsafe_allow_html=True)

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

def extract_ganji(text):
    """'신'처럼 천간/지지가 겹칠 때 2개 이상 중 올바른 글자를 선택하는 완벽한 필터링"""
    if not text: return ""
    text = text.replace(" ", "").replace("년", "").replace("월", "").replace("일", "").replace("시", "")
    g_char, j_char = "?", "?"
    
    for c in text:
        # 천간이 비어있고 천간 글자면 넣은 뒤, 다음 글자로 넘어감 (지지에 중복 할당 방지)
        if g_char == "?" and c in "甲乙丙丁戊己庚辛壬癸갑을병정무기경신임계":
            g_char = c
            continue 
            
        # 지지가 비어있고 지지 글자면 넣음
        if j_char == "?" and c in "子丑寅卯辰巳午未申酉戌亥자축인묘진사오미신유술해":
            j_char = c
            
    return g_char + j_char

def get_true_year_month_pillar(year, month, day, hour, minute):
    kst = pytz.timezone('Asia/Seoul')
    dt_kst = kst.localize(datetime(year, month, day, hour, minute))
    dt_utc = dt_kst.astimezone(pytz.utc)
    
    sun = ephem.Sun()
    sun.compute(dt_utc)
    lon = math.degrees(ephem.Ecliptic(sun).lon) % 360.0
    
    actual_year = year
    if month <= 2 and lon < 315.0: actual_year -= 1
        
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
        def __init__(self, genai_client): self.client = genai_client
        def generate_content(self, contents, **kwargs):
            return self.client.models.generate_content(model="gemini-2.5-flash", contents=contents)
    model = GeminiModelCompat(client)
except Exception as _api_e:
    st.error(f"🚨 Gemini API 키 오류: {_api_e}")
    client, model = None, None

def call_claude_api(prompt_text, max_tokens=8000):
    if client is None: return "<div style='color:red;'>🚨 Gemini 모델이 초기화되지 않았습니다.</div>"
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt_text)
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

def get_group_ss(ss_str):
    return {'비견':'비겁', '겁재':'비겁', '식신':'식상', '상관':'식상', '편재':'재성', '정재':'재성', '편관':'관성', '정관':'관성', '편인':'인성', '정인':'인성'}.get(ss_str, '비겁')

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
    s_map = {'申':['寅','卯','辰'],'子':['寅','卯','辰'],'辰':['寅','卯','辰'],'亥':['巳','午','未'],'卯':['巳','午','未'],'未':['巳','午','未'],'寅':['申','酉','戌'],'午':['申','酉','戌'],'戌':['申','酉','戌'],'巳':['亥','子','丑'],'酉':['亥','子','丑'],'丑':['亥','子','丑']}
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
    return ", ".join(list(dict.fromkeys(r))) if r else "-"

def get_general_shinsal_filtered(idx, gans, jjis, gender="남성"):
    dc, mc, yc = gans[1], gans[2], gans[3]
    cur_g, cur_j = gans[idx], jjis[idx]
    if cur_g in ["?", "-", " "] or cur_j in ["?", "-", " "]: return []
    gj = cur_g + cur_j
    noble, ausp, evil = [], [], []
    
    if cur_j in {'甲':'未丑','乙':'申子','丙':'酉亥','丁':'酉亥','戊':'未丑','己':'申子','庚':'未丑','辛':'午寅','壬':'卯巳','癸':'卯巳'}.get(dc,""): noble.append("천을귀인") 
    if cur_j == jjis[2]: noble.append("월덕귀인") 
    if gj in ["甲辰","乙未","丙戌","丁丑","戊辰","壬戌","癸丑"]: evil.append("백호대살")
    if gj in ["庚辰","庚戌","壬辰","壬戌","戊戌"]: evil.append("괴강살")
    if cur_j in {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子'}.get(dc,""): evil.append("양인살")

    result = []
    for n in list(dict.fromkeys(noble)): result.append(f"<span style='color:#0D47A1;'>{n}</span>")
    for a in list(dict.fromkeys(ausp)): result.append(f"<span style='color:#2E7D32;'>{a}</span>")
    for e in list(dict.fromkeys(evil)): result.append(f"<span style='color:#C62828;'>{e}</span>")
    return result

def get_jijanggan_full(dg, ji):
    if ji in ["?", " ", "-"]: return "-"
    raw = JIJANGGAN.get(ji, ['-','-','-'])
    res = "<div style='display:flex; flex-direction:column; height:100%; min-height:65px; gap:2px; padding:2px 0; margin:0;'>"
    for j in raw:
        if j != '-':
            ss_label = get_ss(dg, j)[:2]; color_key = get_color(j)
            bg = {'목':'#2E7D32','화':'#C62828','토':'#F9A825','금':'#9E9E9E','수':'#212121'}.get(color_key, '#888')
            tc = 'white' if color_key != '토' else 'black'
            res += f"<div style='flex-grow:1; display:flex; align-items:center; justify-content:center; background:{bg}; color:{tc}; width:95%; margin:0 auto; font-size:12px; font-weight:900; border-radius:3px;'>{j} ({ss_label})</div>"
        else: res += "<div style='flex-grow:1; display:flex; align-items:center; justify-content:center; background:#f9f9f9; width:95%; margin:0 auto; color:#bbb; border-radius:3px; border:1px dashed #ddd;'>-</div>"
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
        if mb == {'甲':'寅', '丙':'巳', '戊':'巳', '庚':'申', '壬':'亥'}.get(ds, ""): return "건록격", f"월지 {mb}가 일간 {ds}의 건록에 해당하여 건록격으로 정합니다."

    if mb in ["子", "午", "卯", "酉"]:
        core_ss = safe_get_ss(ds, mb)
        if core_ss in ["비견", "겁재"]: return "건록(월겁)격", f"월지 {mb}가 일간 {ds}와 같은 기운이므로 건록격으로 삼습니다."
        return core_ss + "격", f"월지 {mb}의 순수한 기운인 {core_ss}을 그대로 격으로 삼습니다."
    
    main_qi = jg[-1]
    fallback_ss = safe_get_ss(ds, main_qi)
    return fallback_ss + "격", f"월지 {mb}의 본기인 {main_qi}를 기준으로 {fallback_ss}격으로 정합니다."

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
        if order == 1: t_lon_unwrapped = min([l for l in jeol_lons if l > start_lon] + [l + 360 for l in jeol_lons if l <= start_lon])
        else: t_lon_unwrapped = max([l for l in jeol_lons if l <= start_lon] + [l - 360 for l in jeol_lons if l > start_lon])
        search_dt = utc_dt
        step = dt_mod.timedelta(minutes=10) if order == 1 else dt_mod.timedelta(minutes=-10)
        for _ in range(6000):
            search_dt += step
            curr_lon = get_lon(search_dt)
            if order == 1 and curr_lon < start_lon and (start_lon - curr_lon) > 180: curr_lon += 360
            elif order == -1 and curr_lon > start_lon and (curr_lon - start_lon) > 180: curr_lon -= 360
            if (order == 1 and curr_lon >= t_lon_unwrapped) or (order == -1 and curr_lon <= t_lon_unwrapped): break
        total_days = abs((search_dt - utc_dt).total_seconds()) / 86400.0
        d_su = int(round(total_days / 3.0))
        return max(1, min(10, d_su))
    except: return 1

def get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, forbidden_list):
    results = []
    curr_date = start_date
    while curr_date <= end_date:
        results.append({'date': curr_date.strftime('%Y-%m-%d'), 'score': 85})
        curr_date += dt_mod.timedelta(days=1)
    return sorted(results, key=lambda x: x['score'], reverse=True)[:5]

# ==============================================================================
# 3. 프리미엄 궁합 분석 엔진 클래스 (ver 48.3 원형 100% 보존 및 조후/묘고 메서드 포함)
# ==============================================================================
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
# 4. 사이드바 UI (14종 상세 분석 항목 완벽 분기)
# ==============================================================================
with st.sidebar:
    st.title("🏮초연 전통명리 연구소")
    st.caption(f"{APP_VERSION}")
    st.markdown("---")

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
        u_product = st.radio("상세 분석 항목:", [
            "1-1. 사주팔자와 운세풀이", 
            "1-2. 올해 운세 상세분석", 
            "1-3. 이번달 운세 상세분석", 
            "1-4. 주간 및 일운 상세분석"
        ], key="sub_cat_1")
        
        if u_product == "1-2. 올해 및 특정연도 운세 상세분석":
            curr_yr_val = dt_mod.datetime.now(pytz.timezone('Asia/Seoul')).year
            st.number_input("📅 분석할 특정 연도 (기본값: 올해)", min_value=1900, max_value=2050, value=curr_yr_val, key="target_year_input")
    elif main_category == "2. 테마별 특성화 상담":
        u_product = st.radio("특성화 상품 선택:", [
            "2-1. 재물운 특화 분석", 
            "2-2. 연애/결혼운 특화 분석",
            "2-3. 진학/입시운 특화 분석",
            "2-4. 직업/경력운 특화 분석",
            "2-5. 건강운 특화 분석", 
            "2-6. 이사 택일",
            "2-7. 개업 택일"
        ], key="sub_cat_2")
    elif main_category == "3. 커플 연애/결혼운 (궁합) 풀이":
        u_product = st.radio("상세 분석 항목:", [
            "3-1. 연애/결혼운 (궁합) 풀이", 
            "3-2. 결혼 택일", 
            "3-3. 출산 택일"
        ], key="sub_cat_3")
    else:
        u_product = st.radio("비교 분석 대상:", [
            "4-1. 타 감명서 비교 (사주)",  
            "4-2. 타 감명서 비교 (궁합)"
        ], key="sub_cat_4")

    st.markdown("---")

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
            # 🚨 [수술 1] '신묘' 등 중복 글자 파괴 방지 헬퍼
            def _extract(text):
                if not text: return ""
                text = text.replace(" ", "").replace("년", "").replace("월", "").replace("일", "").replace("시", "")
                g_char, j_char = "?", "?"
                for c in text:
                    if g_char == "?" and c in "甲乙丙丁戊己庚辛壬癸갑을병정무기경신임계":
                        g_char = c; continue
                    if j_char == "?" and c in "子丑寅卯辰巳午未申酉戌亥자축인묘진사오미신유술해":
                        j_char = c
                return g_char + j_char

            _ry, _rm, _rd = _extract(ry), _extract(rm), _extract(rd)
            
            if len(_ry)==2 and len(_rm)==2 and len(_rd)==2:
                ry_h = K2H_GAN.get(_ry[0], _ry[0]) + K2H_JI.get(_ry[1], _ry[1])
                rm_h = K2H_GAN.get(_rm[0], _rm[0]) + K2H_JI.get(_rm[1], _rm[1])
                rd_h = K2H_GAN.get(_rd[0], _rd[0]) + K2H_JI.get(_rd[1], _rd[1])
                
                klc_find = KoreanLunarCalendar()
                time_map_rev = {'子':'00:30 ~ 01:29 (朝子)시','丑':'01:30 ~ 03:29 (丑)시','寅':'03:30 ~ 05:29 (寅)시','卯':'05:30 ~ 07:29 (卯)시','辰':'07:30 ~ 09:29 (辰)시','巳':'09:30 ~ 11:29 (巳)시','午':'11:30 ~ 13:29 (午)시','未':'13:30 ~ 15:29 (未)시','申':'15:30 ~ 17:29 (申)시','酉':'17:30 ~ 19:29 (酉)시','戌':'19:30 ~ 21:29 (戌)시','亥':'21:30 ~ 23:29 (亥)시'}
                
                rt_val = "시간 모름"
                if rt:
                    clean_rt = rt.replace("시", "").strip()
                    if clean_rt:
                        rt_h = K2H_JI.get(clean_rt[-1], clean_rt[-1])
                        rt_val = time_map_rev.get(rt_h, "시간 모름")

                matched_list = []
                
                # 🚨 [수술 2] 1800년대부터 2050년까지 스캔하여 일치하는 '모두'를 수집!
                for y in range(2050, 1800, -1):
                    klc_find.setSolarDate(y, 7, 1)
                    gj_y = klc_find.getChineseGapJaString().split()
                    if gj_y and gj_y[0][:2] == ry_h:
                        curr_dt = dt_mod.date(y+1, 2, 28)
                        while curr_dt >= dt_mod.date(y, 1, 1):
                            klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                            gj = klc_find.getChineseGapJaString().split()
                            if len(gj) >= 3 and gj[0][:2] == ry_h and gj[1][:2] == rm_h and gj[2][:2] == rd_h:
                                is_leap = getattr(klc_find, 'isIntercalary', getattr(klc_find, 'isIntercalation', False))
                                leap_str = "윤달" if is_leap else "평달"
                                
                                # 🚨 두 줄 띄어쓰기(\n) 강제 삽입!
                                display_str = f"양력 {curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일\n(음력 {klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일, {leap_str})"
                                
                                matched_list.append({
                                    "display": display_str,
                                    "y": curr_dt.year,
                                    "m": curr_dt.month,
                                    "d": curr_dt.day,
                                    "t": rt_val
                                })
                                break 
                            curr_dt -= dt_mod.timedelta(days=1)
                
                if matched_list:
                    st.session_state['u_matched_list'] = matched_list
                    # 가장 최근 연도를 기본값으로 세팅
                    st.session_state.s_y = matched_list[0]['y']
                    st.session_state.s_m = matched_list[0]['m']
                    st.session_state.s_d = matched_list[0]['d']
                    if matched_list[0]['t'] != "시간 모름":
                        st.session_state.s_t = matched_list[0]['t']
                    st.session_state.pop('rev_error_msg', None)
                else:
                    st.session_state['rev_error_msg'] = "일치하는 날짜가 없습니다."
                    st.session_state.pop('u_matched_list', None)
            else: 
                st.session_state['rev_error_msg'] = "간지를 2글자씩 정확히 입력하세요."

        # 🚨 [수술 3] 버튼의 실행이 끝난 후, 바깥쪽에서 라디오 버튼 UI를 그려줌!
        if 'u_matched_list' in st.session_state and st.session_state['u_matched_list']:
            matches = st.session_state['u_matched_list']
            if len(matches) > 1:
                st.success(f"💡 일치하는 생년월일이 **{len(matches)}건** 검색되었습니다. 적용할 날짜를 선택하세요.")
                cur_y_val = st.session_state.get('s_y')
                match_opts = [m['display'] for m in matches]
                
                default_idx = 0
                for idx, m in enumerate(matches):
                    if m['y'] == cur_y_val:
                        default_idx = idx
                        break

                def on_select_user_match():
                    sel_str = st.session_state.get('user_match_selector')
                    for m in matches:
                        if m['display'] == sel_str:
                            st.session_state['s_y'] = m['y']
                            st.session_state['s_m'] = m['m']
                            st.session_state['s_d'] = m['d']
                            if m['t'] != "시간 모름":
                                st.session_state['s_t'] = m['t']
                            break
                    if 'need_calc' in st.session_state: 
                        st.session_state['need_calc'] = False

                st.radio(
                    "📅 적용할 생년월일 선택:",
                    options=match_opts,
                    index=default_idx,
                    key="user_match_selector",
                    on_change=on_select_user_match
                )
            else:
                # 1개만 나왔을 때는 \n을 제거하고 1줄로 예쁘게 출력
                one_line_str = matches[0]['display'].replace('\n', ' ')
                st.success(f"✅ {one_line_str}")

        if 'rev_error_msg' in st.session_state:
            st.error(st.session_state['rev_error_msg'])
            del st.session_state['rev_error_msg']

    st.markdown("---")
    st.markdown("<div style='font-weight:900; color:#1A237E; margin-bottom:5px;'>👤 신청인 기본 정보</div>", unsafe_allow_html=True)
    u_name = st.text_input("이름", value="", placeholder="홍길동", key="u_n")
    
    # 🚨 [원천적인 수술 포인트] KeyError의 뿌리 차단! 안전한 .get() 함수를 사용하여 변수 부재 시 시스템 다운 원천 방지
    def auto_flip_gender():
        current_u_g = st.session_state.get('u_g', '남성')
        st.session_state['p_g'] = "여성" if current_u_g == "남성" else "남성"

    # 앱 최초 실행 시 에러 방지용 (기본값 세팅)
    if 'p_g' not in st.session_state:
        st.session_state['p_g'] = "여성"
        
    u_gender = st.selectbox("성별", ["남성", "여성"], index=0, key="u_g", on_change=auto_flip_gender)
    u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], index=0, key="u_c")
    
    col1, col2, col3 = st.columns(3)
    u_y = col1.number_input("년", 1900, 2050, value=st.session_state.get('s_y', 2010), key="s_y")
    u_m = col2.number_input("월", 1, 12, value=st.session_state.get('s_m', 1), key="s_m")
    u_d = col3.number_input("일", 1, 31, value=st.session_state.get('s_d', 1), key="s_d")
    
    idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]
    u_t = st.selectbox("태어난 시간", idx_list, index=0, key="s_t")
    
    # 🚨 [수술 완료] "궁합"이나 "3."이라는 글자가 들어가 있으면 무조건 2인용 상품으로 인식하도록 강력하게 수정!
    is_2person_product = ("궁합" in main_category or "3." in main_category or "4-2" in u_product)
    
    p_name, p_gender, p_marital, p_cal, p_y, p_m, p_d, p_t = "", "여성", "미혼", "양력", 0, 0, 0, "시간 모름"
    other_reading_text = ""
    run_delivery_calc = False  
    start_date, end_date = None, None
    baby_gender = "미정"
    compare_mode = "자동대조"
    run_iljin_calc = False
    is_vip_package = False

    # 🚨 [안전장치]: 85.5의 stop_ai 함수가 50.5에서도 에러 없이 작동하도록 선언
    def stop_ai():
        if 'need_calc' in st.session_state: st.session_state['need_calc'] = False

    if main_category in ["1. 개인 사주팔자 풀이 (종합)", "2. 테마별 특성화 상담"]:
        
        # 🚨 [수술 1]: 85.5 버전의 VIP 패키지 모드 완벽 이식!
        if u_product.startswith("1-"):
            st.markdown("<hr style='border:1px dashed #1A237E; margin:15px 0;'>", unsafe_allow_html=True)
            is_vip_package = st.checkbox("👑 VIP 패키지 모드", value=st.session_state.get("is_vip_package_val", False), key="is_vip_package_val", on_change=stop_ai)

        # 🚨 [수술 1]: 1-1번에서는 일운 스위치 철거! 1-4번에서만 가동되도록 분리!
        if u_product == "1-4. 주간 및 일운 상세분석":
            run_iljin_calc = st.checkbox("🔮 일운 운세 분석 가동", value=False)
            if run_iljin_calc:
                if 'target_date' not in st.session_state: st.session_state['target_date'] = dt_mod.datetime.now(pytz.timezone('Asia/Seoul')).date()
                st.session_state['target_date'] = st.date_input("분석할 일자 선택", value=st.session_state['target_date'])
                
        elif u_product == "1-1. 사주팔자와 운세풀이":
            run_iljin_calc = False  # 1-1번은 무조건 메인 사주만 풀이 (일진 스위치 차단)

    elif main_category == "4. 타 감명서 비교":
        st.markdown("<hr style='border:1px dashed #2E7D32; margin:15px 0;'>", unsafe_allow_html=True)
        compare_mode = st.radio("대조 분석 모드", ["전통 명리학과 1:1 자동 대조", "외부 타 감명서 원문 대조"], index=0)
        if compare_mode == "외부 타 감명서 원문 대조":
            other_reading_text = st.text_area("타 감명서 원문 텍스트 입력", value="", height=180)

    # 🚨 [수술 포인트] 4번 메뉴에서 탈출하여 왼쪽으로 4칸 나와 독립했습니다! (if가 elif와 세로줄이 맞아야 합니다)
    if is_2person_product:
        st.markdown("<hr style='border:1px dashed #C62828; margin:15px 0;'>", unsafe_allow_html=True)
        
        with st.expander("🔍 상대방 사주팔자 역산 검색", expanded=False):
            p_col_g1, p_col_g2 = st.columns(2)
            with p_col_g1: p_ry = st.text_input("상대방 년주", value="", key="p_ry_rev")
            with p_col_g2: p_rm = st.text_input("상대방 월주", value="", key="p_rm_rev")
            p_col_g3, p_col_g4 = st.columns(2)
            with p_col_g3: p_rd = st.text_input("상대방 일주", value="", key="p_rd_rev")
            with p_col_g4: p_rt = st.text_input("상대방 시주", value="", key="p_rt_rev")
            
            def do_auto_fill_partner_507():
                def _extract(text):
                    if not text: return ""
                    text = text.replace(" ", "").replace("년", "").replace("월", "").replace("일", "").replace("시", "")
                    g_char, j_char = "?", "?"
                    for c in text:
                        if g_char == "?" and c in "甲乙丙丁戊己庚辛壬癸갑을병정무기경신임계":
                            g_char = c; continue
                        if j_char == "?" and c in "子丑寅卯辰巳午未申酉戌亥자축인묘진사오미신유술해":
                            j_char = c
                    return g_char + j_char

                _p_ry, _p_rm, _p_rd = _extract(p_ry), _extract(p_rm), _extract(p_rd)
                
                if len(_p_ry) >= 2 and len(_p_rm) >= 2 and len(_p_rd) >= 2:
                    K2H_GAN = {'갑':'甲','을':'乙','병':'丙','정':'丁','무':'戊','기':'己','경':'庚','신':'辛','임':'壬','계':'癸'}
                    K2H_JI = {'자':'子','축':'丑','인':'寅','묘':'卯','진':'辰','사':'巳','오':'午','미':'未','신':'申','유':'酉','술':'戌','해':'亥'}
                    p_ry_h = K2H_GAN.get(_p_ry[0], _p_ry[0]) + K2H_JI.get(_p_ry[1], _p_ry[1])
                    p_rm_h = K2H_GAN.get(_p_rm[0], _p_rm[0]) + K2H_JI.get(_p_rm[1], _p_rm[1])
                    p_rd_h = K2H_GAN.get(_p_rd[0], _p_rd[0]) + K2H_JI.get(_p_rd[1], _p_rd[1])
                    
                    klc_find = KoreanLunarCalendar()
                    time_map_rev = {'子':'00:30 ~ 01:29 (朝子)시','丑':'01:30 ~ 03:29 (丑)시','寅':'03:30 ~ 05:29 (寅)시','卯':'05:30 ~ 07:29 (卯)시','辰':'07:30 ~ 09:29 (辰)시','巳':'09:30 ~ 11:29 (巳)시','午':'11:30 ~ 13:29 (午)시','未':'13:30 ~ 15:29 (未)시','申':'15:30 ~ 17:29 (申)시','酉':'17:30 ~ 19:29 (酉)시','戌':'19:30 ~ 21:29 (戌)시','亥':'21:30 ~ 23:29 (亥)시'}
                    
                    p_rt_val = "시간 모름"
                    if p_rt:
                        clean_rt = p_rt.replace("시", "").strip()
                        if clean_rt:
                            rt_h = K2H_JI.get(clean_rt[-1], clean_rt[-1])
                            # 🚨 [수술 포인트] 입력된 글자에 '야자'가 포함되어 있으면 야자시로 완벽하게 맵핑!
                            if rt_h == '子' and "야자" in p_rt:
                                p_rt_val = "23:30 ~ 00:29 (夜子)시"
                            else:
                                p_rt_val = time_map_rev.get(rt_h, "시간 모름")

                    matched_list = []
                    for y in range(2050, 1800, -1):
                        klc_find.setSolarDate(y, 7, 1)
                        gj_y = klc_find.getChineseGapJaString().split()
                        if gj_y and gj_y[0][:2] == p_ry_h:
                            curr_dt = dt_mod.date(y+1, 2, 28)
                            while curr_dt >= dt_mod.date(y, 1, 1):
                                klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                                gj = klc_find.getChineseGapJaString().split()
                                if len(gj) >= 3 and gj[0][:2] == p_ry_h and gj[1][:2] == p_rm_h and gj[2][:2] == p_rd_h:
                                    is_leap = getattr(klc_find, 'isIntercalary', getattr(klc_find, 'isIntercalation', False))
                                    leap_str = "윤달" if is_leap else "평달"
                                    display_str = f"양력 {curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일\n(음력 {klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일, {leap_str})"
                                    
                                    matched_list.append({
                                        "display": display_str,
                                        "y": curr_dt.year,
                                        "m": curr_dt.month,
                                        "d": curr_dt.day,
                                        "t": p_rt_val
                                    })
                                    break 
                                curr_dt -= dt_mod.timedelta(days=1)
                    
                    if matched_list:
                        st.session_state['p_matched_list'] = matched_list
                        st.session_state.p_y_in = matched_list[0]['y']
                        st.session_state.p_m_in = matched_list[0]['m']
                        st.session_state.p_d_in = matched_list[0]['d']
                        if matched_list[0]['t'] != "시간 모름":
                            st.session_state.p_t_key = matched_list[0]['t']
                            st.session_state.p_t_select_key = matched_list[0]['t']
                        st.session_state.pop('rev_p_error_msg', None)
                    else:
                        st.session_state['rev_p_error_msg'] = "일치하는 날짜가 없습니다."
                        st.session_state.pop('p_matched_list', None)
                else:
                    st.session_state['rev_p_error_msg'] = "간지를 2글자씩 정확히 입력하세요."

            st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="btn_partner_rev", on_click=do_auto_fill_partner_507)

            if 'p_matched_list' in st.session_state and st.session_state['p_matched_list']:
                p_matches = st.session_state['p_matched_list']
                if len(p_matches) > 1:
                    st.success(f"💡 상대방 일치 날짜가 **{len(p_matches)}건** 검색되었습니다. 적용할 날짜를 선택하세요.")
                    cur_p_y_val = st.session_state.get('p_y_in')
                    p_match_opts = [m['display'] for m in p_matches]
                    p_default_idx = 0
                    for idx, m in enumerate(p_matches):
                        if m['y'] == cur_p_y_val:
                            p_default_idx = idx; break

                    def on_select_partner_match():
                        sel_str = st.session_state.get('partner_match_selector')
                        for m in p_matches:
                            if m['display'] == sel_str:
                                st.session_state['p_y_in'] = m['y']
                                st.session_state['p_m_in'] = m['m']
                                st.session_state['p_d_in'] = m['d']
                                if m['t'] != "시간 모름":
                                    st.session_state['p_t_key'] = m['t']
                                    st.session_state['p_t_select_key'] = m['t']
                                break
                        if 'need_calc' in st.session_state: st.session_state['need_calc'] = False

                    st.radio("📅 적용할 상대방 생년월일 선택:", options=p_match_opts, index=p_default_idx, key="partner_match_selector", on_change=on_select_partner_match)
                else:
                    one_line_str = p_matches[0]['display'].replace('\n', ' ')
                    st.success(f"✅ {one_line_str}")

            if 'rev_p_error_msg' in st.session_state:
                st.error(st.session_state['rev_p_error_msg'])
                del st.session_state['rev_p_error_msg']

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

        if u_product in ["3-2. 결혼 택일", "3-3. 출산 택일"] or ((current_year - f_year + 1) <= 49 and main_category == "3. 커플 연애/결혼운 (궁합) 풀이"):
            st.markdown("<hr style='border:1px solid #ddd; margin:15px 0;'>", unsafe_allow_html=True)
            
            with st.expander("📅 택일 달력 기간 선택", expanded=(u_product in ["3-2. 결혼 택일", "3-3. 출산 택일"])):
                baby_gender = st.radio("태아 성별 (출산택일 전용)", ["미정", "남아", "여아"], index=0)
                start_date = st.date_input("탐색 시작일", value=dt_mod.date.today())
                end_date = st.date_input("탐색 종료일", value=dt_mod.date.today() + dt_mod.timedelta(days=30))
                
                st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
                run_delivery_calc = st.checkbox("✅ 택일 가동 확정 (체크 후 하단 메인 가동버튼 클릭)", value=(u_product in ["3-2. 결혼 택일", "3-3. 출산 택일"]))

    st.markdown("---")
    btn_single = st.button("🚀 초연 시공명리 사주풀이 가동", key="btn_run", use_container_width=True, type="primary")

    if st.button("🖨️ 풀이 결과 인쇄 / PDF 저장", key="btn_print", use_container_width=True, type="secondary"):
        components.html("<script>window.parent.print();</script>", height=0)
    
    # 🚨 [수술 완료] 들여쓰기를 4칸으로 완벽하게 맞춘 가동 엔진입니다! 🚨
    if btn_single:
        is_compare_type = (main_category == "4. 타 감명서 비교")

        if not u_name.strip(): 
            st.warning("⚠️ 신청인의 이름을 입력해 주세요.")
        elif is_compare_type and compare_mode == "외부 타 감명서 원문 대조" and not other_reading_text.strip():
            st.warning("⚠️ 타 감명서 원문을 입력해 주세요.")
        elif is_2person_product and not p_name.strip(): 
            st.warning("⚠️ 상대방의 이름을 입력해 주세요.")
        else:
            st.session_state['app_running'] = True
            
            # 이전 결과 초기화
            for key in ['saved_report_html', 'saved_report_2', 'saved_report_gh_cover', 'saved_report_gh_m', 'saved_report_gh_f', 'saved_report_gh_g', 'saved_report_del', 'saved_report_iljin']:
                if key in st.session_state: del st.session_state[key]

            if main_category in ["1. 개인 사주팔자 풀이 (종합)", "2. 테마별 특성화 상담"] and run_iljin_calc:
                st.session_state['need_calc'] = True
                st.session_state['run_waterfall'] = True
            elif is_2person_product and run_delivery_calc:
                st.session_state['need_calc'] = True
                st.session_state['run_delivery_only'] = True
            else:
                st.session_state['need_calc'] = True
                st.session_state['run_waterfall'] = False
                st.session_state['run_delivery_only'] = False
            
            st.rerun()

# ==============================================================================
# 5. 분석 가동 로직 (Ver 50.4 완결본)
# ==============================================================================
if st.session_state.get('need_calc', False):
    spinner_msg = f"⏳ [초연 전통명리 정밀 분석({u_product}) 연산 중....]"
    with st.spinner(spinner_msg):
        try:
            # 🚨 [최후의 절대 방어막] 파이썬 변수 증발(NameError) 원천 차단!
            # 연산 엔진이 가동되는 최상단에서 모든 변수를 절대기억장치에서 몽땅 강제 소환하여 주입합니다.
            u_name = st.session_state.get('u_n', '홍길동')
            u_gender = st.session_state.get('u_g', '남성')
            u_marital = st.session_state.get('u_m_stat', '미혼')
            u_cal = st.session_state.get('u_c', '양력')
            u_y = st.session_state.get('s_y', 1980)
            u_m = st.session_state.get('s_m', 1)
            u_d = st.session_state.get('s_d', 1)
            u_t = st.session_state.get('s_t', '시간 모름')
            
            p_name = st.session_state.get('p_n', '상대방')
            p_gender = st.session_state.get('p_g', '여성')
            p_marital = st.session_state.get('p_m_stat', '미혼')
            p_cal = st.session_state.get('p_c', '양력')
            p_y = st.session_state.get('p_y_in', 1980)
            p_m = st.session_state.get('p_m_in', 1)
            p_d = st.session_state.get('p_d_in', 1)
            p_t = st.session_state.get('p_t_key', '시간 모름')

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

            # 🚨 [수술 1] 남명과 똑같은 색상 통일을 위해 p_color를 무력화하고 진한 남색(#1A237E)으로 고정!
            safe_color = "#1A237E"

            cover_html = (
                f"<div class='report-page cover-page' style='margin:0 auto; width:100%; height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; -webkit-print-color-adjust: exact; box-sizing: border-box;'>\n"
                f"    <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 90%; max-width: 700px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>\n"
                f"        <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>\n"
                f"            <h1 class='title-gothic' style='font-family: \"Nanum Gothic\", sans-serif; font-size: 26px !important; font-weight: 900; margin:0 !important; white-space: nowrap !important; letter-spacing: -2px !important;'>초연&nbsp;전통&nbsp;명리사주&nbsp;풀이</h1>\n"
                f"            <div style='text-align: right; margin-top: 10px;'>\n"
                f"                <span class='ver-gothic' style='font-family: \"Nanum Gothic\", sans-serif; font-size: 14px; font-weight: 700; letter-spacing: 1px;'>{APP_VERSION}</span>\n"
                f"            </div>\n"
                f"        </div>\n"
                f"        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>\n"
                f"            <h2 style='font-family: \"Nanum Gothic\", sans-serif; font-size: 24px; font-weight: 800; color: {safe_color}; margin-bottom: 20px;'>{p_icon} 신청인 : {u_name} 님</h2>\n"
                f"            <div style='font-family: \"Nanum Gothic\", sans-serif; font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>\n"
                f"                <p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p>\n"
                f"                <p style='margin: 5px 0 0 0; color: {safe_color}; white-space: nowrap;'>{time_str}</p>\n"
                f"            </div>\n"
                f"        </div>\n"
                f"        <p style='font-family: \"Nanum Gothic\", sans-serif; font-size: 18px; margin-top: 50px; font-weight: 800;'>{today_str}</p>\n"
                f"        <p style='font-family: \"Nanum Gothic\", sans-serif; font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 20px;'>초연 전통명리 연구소</p>\n"
                f"    </div>\n"
                f"</div>"
            )
            st.session_state['saved_report_cover'] = cover_html

            if u_product == "1-1. 사주팔자와 운세풀이":
                report_title = "사주팔자와 운세풀이"
            elif u_product == "1-2. 올해 운세 상세분석":
                report_title = "올해 운세 상세분석"
            elif u_product == "1-3. 이번달 운세 상세분석":
                report_title = "이번달 운세 상세분석"
            elif u_product == "1-4. 주간 및 일운 상세분석":
                report_title = "주간 및 일운 상세분석"
            elif u_product == "2-1. 재물운 특화 분석":
                report_title = "재물운 특화 분석"
            elif u_product == "2-2. 연애/결혼운 특화 분석":
                report_title = "연애/결혼운 특화 분석"
            elif u_product == "2-3. 진학/입시운 특화 분석":
                report_title = "진학/입시운 특화 분석"
            elif u_product == "2-4. 직업/경력운 특화 분석":
                report_title = "직업/커리어운 특화 분석"
            elif u_product == "2-5. 건강운 특화 분석":
                report_title = "건강운 특화 분석"
            elif u_product == "2-6. 이사 택일":
                report_title = "이사 택일 추천"
            elif u_product == "2-7. 개업 택일":
                report_title = "개업 택일 추천"
            elif u_product == "3-1. 연애/결혼운 (궁합) 풀이":
                report_title = "커플 연애/결혼운 (궁합) 풀이"
            elif u_product == "3-2. 결혼 택일":
                report_title = "결혼 택일 추천"
            elif u_product == "3-3. 출산 택일":
                report_title = "출산 택일 추천"
            elif u_product == "4-1. 타 감명서 비교 (사주)":
                report_title = "타 감명서 비교 (사주)"
            elif u_product == "4-2. 타 감명서 비교 (궁합)":
                report_title = "타 감명서 비교 (궁합)"
            else:
                report_title = "사주팔자 정밀 분석"

            ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                b_top = "0px solid transparent !important"
                cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'><span style='color:inherit !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</span></td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'><span style='color:inherit !important;'>합충형파해</span></td>" if l_idx==0 else ""
                ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

            # 🚨 [수술 완료] 여명 붉은색 멸종! {p_color}를 날려버리고 남명과 동일한 진한 남색(#1A237E)으로 강제 고정
            info_h = f"<div style='text-align:center; font-family:\"Nanum Gothic\", sans-serif; margin-bottom:15px; line-height:1.5;'><span style='font-size:18px; font-weight:900; color:#1A237E; white-space:nowrap;'>{p_icon} {disp_name}님 ({u_gender}, {u_marital}, {u_age}세)</span><br><span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span></div>"

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
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>년지 12신살</span></td>{"".join([f"<td style='color:#C62828; border:1px solid #444 !important;'><span style='color:inherit !important;'>{get_12_shinsal(yb, jjis[i])}</span></td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>일지 12신살</span></td>{"".join([f"<td style='color:#1565C0; border:1px solid #444 !important;'><span style='color:inherit !important;'>{get_12_shinsal(db, jjis[i])}</span></td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>일반신살</span></td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'><span style='color:inherit !important;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis, u_gender)) if get_general_shinsal_filtered(i, gans, jjis, u_gender) else '-'}</span></td>" for i in range(4)])}</tr>
</table>
"""
            calc_gyukgook, gyukgook_detail = get_gyukgook_detailed(ds, ys, ms, hs, mb)

            SEASON_SOLAR_TERMS = {
                '寅': '입춘과 경칩 사이의 이른 봄(寅月)', '卯': '경칩과 청명 사이의 완연한 봄(卯月)',
                '辰': '청명과 입하 사이의 봄과 여름의 환절기(辰月)', '巳': '입하와 망종 사이의 이른 여름(巳月)',
                '午': '망종과 소서 사이의 완연한 여름(午月)', '未': '소서와 입추 사이의 가장 무더운 여름(未月)',
                '申': '입추와 백로 사이의 이른 가을(申月)', '酉': '백로와 한로 사이의 완연한 가을(酉月)',
                '戌': '한로와 입동 사이의 가을과 겨울의 환절기(戌月)', '亥': '입동과 대설 사이의 이른 겨울(亥月)',
                '子': '대설과 소한 사이의 완연한 한겨울(子月)', '丑': '소한과 입춘 사이의 가장 추운 겨울(丑月)'
            }
            wol_korean_str = SEASON_SOLAR_TERMS.get(mb, f"{mb}월")
            gyuk_name = calc_gyukgook

            ilju_struct_db = choyeon_db.get("ilju_structure", {})
            struct_data = ilju_struct_db.get(user_ilju_key, [])
            if len(struct_data) >= 3:
                action_type = struct_data[1]
                main_tendency = struct_data[2]
            else:
                action_type = "자율활동형"
                main_tendency = "독자적인 삶의 무대를 개척하는"

            ilju_full_db = choyeon_db.get("ilju_full_master", {})
            ilju_master_data = ilju_full_db.get(user_ilju_key, {})
            ilju_summary_text = ilju_master_data.get('summary', '고유의 역량을 품은')

            choyeon_golden_text = f"""
<div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000; margin-bottom: 20px;'>
    <p style='text-indent: 1.0em; text-align: justify; margin-bottom: 5px;'>
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
            
            guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'午寅','壬':'卯巳','癸':'卯, 巳'}
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
                un_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{val}세</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,c)}</div><div class='color-{get_color(c)}' style='font-size:16px; font-weight:900;'>{c}</div><div class='color-{get_color(j)}' style='font-size:16px; font-weight:900;'>{j}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,j)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,j)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, j)}</div><div style='font-size:11px; color:#1565C0; border-top:1px solid #ccc;'>{get_12_shinsal(db, j)}</div></div>"
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
                se_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; line-height:1.2; border-bottom:1px solid #ccc;'>{ty}년<br>({tage}세)</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div><div style='font-size:11px; color:#1565C0; border-top:1px solid #ccc;'>{get_12_shinsal(db, tj)}</div></div>"
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
                wol_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{tm}월</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div><div style='font-size:11px; color:#1565C0; border-top:1px solid #ccc;'>{get_12_shinsal(db, tj)}</div></div>"
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
                    if math.degrees(ephem.Ecliptic(sun).lon) % 360.0 >= 90.0: haji_day = d; break
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

            # 🚨 [수술 2]: 첫 장 백지 출력 원천 차단! (쓸데없는 page-break 삭제 및 HTML 구조 정화)
            report_1_full_html = f"""{cover_html}
<div class='report-page' style='page-break-before: auto;'>
<div class='vip-inset-frame' style='border:2px solid #1A237E; box-sizing: border-box; padding: 20px; border-radius:15px; margin-top: 0;'>
<h1 style='text-align:center; font-size: 24px; font-weight: 900; white-space: nowrap;'>{report_title}</h1>
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
                ilju_master_prompt_context = (
                    f"🎯 [초연 전통명리의 뼈때리는 팩트폭격 - {user_ilju_key}일주 전용 마스터 비기]\n"
                    f"- 물상 및 성향 요약: {ilju_master_data.get('summary', '')}\n"
                    f"- 심리적 관점: {ilju_master_data.get('psychology', '')}\n"
                    f"- 육친적 관점: {ilju_master_data.get('family', '')}\n"
                    f"- 사회적 관점: {ilju_master_data.get('society', '')}\n"
                    f"- 지장간 좌법(座法) 분석: {ilju_master_data.get('jijanggan_zaBeob', '')}\n"
                    f"- 인종법(引從法) 숨겨진 내면: {ilju_master_data.get('injong_beob', '')}\n"
                    f"- 신살, 변곡점, 건강, 과숙/고신, 도망역: {ilju_master_data.get('shinsal_warnings', '')}\n"
                    f"- 💥 뼈때리는 팩트폭격 핵심 비기: {ilju_master_data.get('choyeon_secret', '')}\n"
                )
            else:
                ilju_master_prompt_context = ""
                                
            db_header = (
                f"[SYSTEM ROLE & 절대 철학: 전통명리 최고위 통합 거장]\n"
                f"당신은 수십 년 임상 노하우를 지닌 세계 최고의 명리학자이자 심리 상담가 '초연 사주 박사'이다.\n"
                f"명리 용어를 나열하는 기계적이고 딱딱한 사전식 작성을 엄격히 금지하며, 신청자의 삶을 깊이 이해하고 어루만져 주는 따뜻하고 친절한 카운슬러의 어조(현대적 구어체)로 깊이 있는 에세이를 작성할 것.\n\n"
                f"[시스템 강제 시간 인식: 현재 시점은 {curr_y}년 {curr_m}월 입니다.]\n"
                f"- 내담자 성함: {disp_name}\n"
                f"- 나이 / 성별: {u_age}세 / {u_gender}\n"
                f"- 혼인 상태: {u_marital}\n"
                f"- 선택 상품: {u_product}\n"
                f"- 격국 팩트: {gyukgook_detail}\n"
                f"- 실제 타격받는 공망 궁위 팩트: {gongmang_actual}\n"
                f"- 올해({curr_y}년) 삼재 여부: {cur_samjae}\n"
                f"- 원국 삼형살(인사신/축술미) 팩트: {samhyung_warn}\n"
                f"- 원국 내부 묘고(입고/개고) 작용: {won_guk_vaults_str}\n"
                f"- 현재 행운(대/세/월운) 묘고 작용: {hang_un_vaults_str}\n\n"
                f"🚨 1. [종합 특별지시 사항 : 대중을 위한 현대적 에세이 통변 원칙]\n"
                f"■ 명리 용어 전략적 해제: 한자어 전문 용어를 제목이나 본문에 날것으로 남발하는 것을 절대 금지한다. 반드시 일반인이 단번에 이해할 수 있는 일상적인 비유와 현대적 언어로 부드럽게 풀어서 설명할 것.\n"
                f"■ 공망(空亡) 심리 분석: 공망의 결핍을 나쁘다고 뭉개지 말고, 심리적 공허감을 따뜻하게 어루만지며 '대체 생존 전략'을 제시할 것.\n"
                f"■ 숙명론의 현대적 치환: 흉사나 갈등 요소를 성장의 동력과 궤도 수정의 기회로 재해석할 것.\n"
                f"■ 서두 인사말 금지: 기계적인 도입부 없이, 첫 글자는 반드시 지정된 1번 대목차 제목으로 즉시 시작할 것.\n\n"
                f"🚨 2. [전통 명리 파동의 현실적 팩트폭격과 처세 연동]\n"
                f"■ 합형파해의 비틀림을 대인관계 단절, 직장 이동 등 구체적 현실 사건으로 명확히 짚어낼 것.\n"
                f"■ 묘고(辰戌丑未) 작용: 자산 창고의 입고/개고에 따른 거대 자산의 변동을 직관적으로 서술할 것.\n"
                f"■ 처세 솔루션 강제 연동: 흉한 파동 감지 시 공간 이동, 수기 충전, 비우기 등 구체적 행동 수칙을 세트로 조언할 것.\n\n"
                f"🚨 3. [시스템 표 마커 및 구조 분할 태그 필수 출력 및 위치 엄수]\n"
                f"■ `[DAEWUN_TABLE_HERE]`, `[SEWUN_TABLE_HERE]` 마커는 지정된 소제목 바로 다음 줄에 정확히 1회만 출력할 것.\n\n"
                f"🚨 4. [목차 및 서식 위계 절대 규칙]\n"
                f"■ 대제목: 1., 2., 3. / 중제목: 1), 2), 3) / 소제목: (1), (2), (3) (※ 원숫자 절대 금지)\n"
                f"■ 강조 기호 위계: ◆ (소제목) → ▶ (목록 1단계) → ▷ (목록 2단계)\n"
                f"■ 기호 중복 금지 및 제목 직후 강제 줄바꿈(Enter) 준수. 콜론(:) 병기 절대 금지.\n"
                f"■ 소제목 및 대제목 번호 재사용 절대 금지. 지정된 목차 외 임의 신설 금지.\n"
                f"■ HTML 색상 태그 절대 금지. 오직 마크다운 볼드체(**강조**)만 허용.\n"
                f"■ 천간/지지 절대 구분 규칙: 형/충/파/해는 지지끼리만 성립하므로 간지를 혼동하지 말 것.\n\n"
                f"🚨 5. [고민 상담 Q&A 섹션 - 공백 시 대응 원칙]\n"
                f"■ 특별히 전달된 고민 사연이 없다면 개인 고민을 억지로 지어내지 말고, '특별히 말씀해주신 고민은 없으시지만'으로 시작하여 해당 연령대와 사주에서 통상적으로 겪는 고민을 예시로 들어 일반적이고 유익한 조언으로 마무리할 것.\n"
            )

            if u_gender == '남성':
                yukchin_rule = (
                    f"\n🚨 [육친 통변 특수부대 절대 규칙 (남성용)]:\n"
                    f"- 본 내담자는 남성(현재 상태: {u_marital})입니다. 아래의 명리학적 육친 생극제화 및 대체 규칙을 100% 엄수하십시오.\n"
                    f"1. 👨‍👩‍👦 [핵심 가족]:\n"
                    f"   - 아내(부인) = 정재 (정재가 없으면 편재로 대체)\n"
                    f"   - 애인(여친) = 편재 (편재가 없으면 정재로 대체)\n"
                    f"   - 자녀 = 관성(정관/편관) 🚨(경고: 남명에서 '식상'을 자녀로 풀이하는 즉시 치명적 오류로 간주함!)\n"
                    f"2. 👵👴 [부모 및 조부모]:\n"
                    f"   - 아버지 = 편재 (없으면 정재) / 어머니 = 정인 (없으면 편인)\n"
                    f"   - 조부(할아버지) = 편인 / 조모(할머니) = 상관\n"
                    f"3. 🏠 [처가 및 형제]:\n"
                    f"   - 장모(처가) = 식상 (아내를 생하는 기운)\n"
                    f"   - 동성 형제(형/남동생) = 비견 / 이성 형제(누나/여동생) = 겁재\n"
                    f"4. 🚨 [상태별 호칭 맞춤형 타겟팅]: 내담자의 현재 혼인 상태({u_marital})를 반드시 반영하십시오.\n"
                    f"   - 기혼: '현재 아내/배우자'로 칭할 것.\n"
                    f"   - 미혼: '미래의 인연'으로 칭할 것.\n"
                    f"   - 🚨돌싱(이혼/사별): '과거의 인연(전처)'에 대한 성찰이나 '새로운 인연(재혼운)'으로 변환하여 카운슬링할 것.\n"
                )
            else:
                yukchin_rule = (
                    f"\n🚨 [육친 통변 특수부대 절대 규칙 (여성용)]:\n"
                    f"- 본 내담자는 여성(현재 상태: {u_marital})입니다. 아래의 명리학적 육친 생극제화 및 대체 규칙을 100% 엄수하십시오.\n"
                    f"1. 👩‍❤️‍👨 [핵심 가족]:\n"
                    f"   - 남편 = 정관 (정관이 없으면 편관으로 대체)\n"
                    f"   - 애인(남친) = 편관 (편관이 없으면 정관으로 대체)\n"
                    f"   - 자녀 = 식상(식신/상관) 🚨(경고: 여명에서 '관성'을 자녀로 풀이하는 즉시 치명적 오류로 간주함!)\n"
                    f"2. 👵👴 [부모 및 조부모]:\n"
                    f"   - 아버지 = 편재 (없으면 정재) / 어머니 = 정인 (없으면 편인)\n"
                    f"   - 조부(외할아버지) = 편인 / 조모(외할머니) = 상관\n"
                    f"3. 🏠 [시댁 및 자매]:\n"
                    f"   - 시어머니(시댁) = 재성 (남편을 생하는 기운)\n"
                    f"   - 동성 형제(언니/여동생) = 비견 / 이성 형제(오빠/남동생) = 겁재\n"
                    f"4. 🚨 [상태별 호칭 맞춤형 타겟팅]: 내담자의 현재 혼인 상태({u_marital})를 반드시 반영하십시오.\n"
                    f"   - 기혼: '현재 남편/배우자'로 칭할 것.\n"
                    f"   - 미혼: '미래의 인연'으로 칭할 것.\n"
                    f"   - 🚨돌싱(이혼/사별): '과거의 인연(전 남편)'에 대한 성찰이나 '새로운 인연(재혼운)'으로 변환하여 카운슬링할 것.\n"
                )

            prompt = ""
            clean_ai_text = ""

            # ==============================================================
            # [A-1] 1. 개인 사주팔자 풀이 (종합 파이프라인)
            # ==============================================================
            if main_category == "1. 개인 사주팔자 풀이 (종합)":

                wood_cnt = counts.get('목', 0)
                fire_cnt = counts.get('화', 0)
                earth_cnt = counts.get('토', 0)
                metal_cnt = counts.get('금', 0)
                water_cnt = counts.get('수', 0)

                if u_product == "1-1. 사주팔자와 운세풀이":
                    prompt = (
                        f"{db_header}\n"
                        f"{ilju_master_prompt_context}\n"
                        f"{yukchin_rule}\n\n"
                        f"[SYSTEM ROLE: 초연 전통명리 최고위 카운슬러]\n"
                        f"제공된 신청자 팩트 데이터를 분석의 근거로 삼아, {disp_name}님의 타고난 성품, 삶의 구조적 역학, 대운 및 세운의 흐름을 대중이 직관적으로 이해할 수 있는 '따뜻하고 통찰력 있는 에세이' 형식으로 종합 분석할 것.\n\n"
                        f"🚨 [출력 목차의 대중화 지시]: 아래 제시된 목차 텍스트는 명리학을 모르는 신청자가 바로 읽는 '제목'이다.\n"
                        f"- 임의로 명리 용어(격국, 십성 등)를 섞어서 제목을 변경하지 말고, 아래 지정된 감성적이고 대중적인 제목 텍스트를 100% 그대로 출력할 것.\n"
                        f"(단, 대괄호 안의 [※ AI 통변 지시: ...] 내용은 시스템 명령어이므로 절대 출력하지 말 것.)\n\n"
                        f"[출력 서식 및 통변 지침]\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 내면과 외면의 심리 스케치</h3>\n"
                        f"<div class='content-box-loose'>\n"

                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 겉으로 드러나는 내 모습</span>\n"
                        f"[※ AI 통변 지시: 원국의 오행 분포와 일간을 기반으로 겉으로 드러나는 태도와 행동 양식을 부드러운 에세이로 서술하십시오.]\n"

                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 감추어진 깊은 속마음</span>\n"
                        f"[※ AI 통변 지시: 지장간 및 일지/시지 구조와 내적 갈등, 본능적 욕구를 따뜻한 심리 상담가처럼 깊이 있게 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 타고난 삶의 구조와 운명의 나침반</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 내 삶의 그릇과 궤도</span>\n"
                        f"[CHOYEON_GOLDEN_TEXT_HERE]\n"
                        f"[※ AI 통변 지시: 아래 (1), (2), (3) 소제목을 순서대로 출력하며 서술하십시오.]\n"

                        f"<br><b>(1) 내 삶을 담는 그릇과 타고난 에너지</b>\n"
                        f"[※ AI 통변 지시: 격국({gyukgook_detail})과 오행 분포를 바탕으로 주된 환경과 그릇을 명리 용어를 순화하여 서술하십시오.]\n"

                        f"<br><b>(2) 내 마음의 온도와 삶의 균형점</b>\n"
                        f"[※ AI 통변 지시: 조후(계절감)와 억부의 균형 상태를 심리적, 환경적 요인으로 풀어내십시오.]\n"

                        f"<br><b>(3) 숨겨진 특별한 재능과 잠재력</b>\n"
                        f"[※ AI 통변 지시: 원국의 특징적 글자 조합을 분석하여 타고난 총명함과 직업적 잠재력을 짚어내십시오.]\n\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 인생의 역동성과 관계의 흐름</span>\n"
                        f"[※ AI 통변 지시: 아래 (1), (2) 소제목을 순서대로 출력하며 서술하십시오.]\n"

                        f"<br><b>(1) 시기별 삶의 무대와 행동 패턴</b>\n"
                        f"[※ AI 통변 지시: 궁위별 에너지를 기반으로 육친·심리·사회적 변화를 알기 쉽게 서술하십시오. 항목이 여럿일 경우 강조 기호(▶, ▷) 사용 및 줄바꿈 준수.]\n"

                        f"<br><b>(2) 내 삶을 흔드는 변화와 도약의 타이밍</b>\n"
                        f"◆ 인연의 끌림과 환경의 변화\n"
                        f"[※ AI 통변 지시: 원국의 합충형파해({hap_chung_hyoung_pa_hae})를 실제 겪는 사건으로 번역하여 서술하십시오. 줄바꿈 엄수.]\n"
                        f"◆ 자산과 재물의 수렴 및 폭발\n"
                        f"[※ AI 통변 지시: 창고 동태({won_guk_vaults_str})를 바탕으로 재물과 환경의 위축/도약을 서술하십시오. 줄바꿈 엄수.]\n"
                        f"◆ 운명의 변곡점과 주의할 파동\n"
                        f"[※ AI 통변 지시: 사주 내 주의할 파동을 다정하게 상세히 서술하십시오. 줄바꿈 엄수.]\n"
                        f"◆ 보이지 않는 압박과 궤도 수정\n"
                        f"[※ AI 통변 지시: 억압된 합충 기운을 대인관계와 직업적 굴곡의 팩트로 풀어내십시오. 줄바꿈 엄수.]\n"
                        f"◆ 심리적 정체와 낯선 환경의 경험\n"
                        f"[※ AI 통변 지시: 심리적 단절감 등을 위로와 함께 풀어주십시오. 줄바꿈 엄수.]\n\n"

                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>3) 삶에 작용하는 특별한 행운과 전환점</span>\n"
                        f"<br><b>(1) 나를 도와주는 수호 천사의 기운</b>\n"
                        f"[※ AI 통변 지시: 천을귀인({guiin_str})의 도움과 활용법을 부드럽게 설명하십시오.]\n"
                        f"<br><b>(2) 내 삶에 스며드는 특수한 기운들</b>\n"
                        f"[※ AI 통변 지시: 주요 신살({shinsal_str})의 영향을 공포감 없이 긍정적 에너지로 재해석하십시오.]\n"
                        f"<br><b>(3) 내면의 공허함과 채워야 할 갈증</b>\n"
                        f"[※ AI 통변 지시: 공망({gongmang_actual}) 결핍을 시기별로 따뜻하게 어루만지며 해법을 제시하십시오.]\n"
                        f"<br><b>(4) 주기적으로 찾아오는 삶의 고비, 지혜롭게 넘기는 법</b>\n"
                        f"[※ AI 통변 지시: 삼재({cur_samjae})를 안심시키는 조언으로 해석하십시오.]\n"
                        f"<br><b>(5) 삶의 큰 전환점과 극복의 지혜</b>\n"
                        f"[※ AI 통변 지시: 삼형살({samhyung_warn}) 작용을 큰 도약의 변곡점으로 서술하고, 없다면 생략하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 세월 따라 달라지는 삶의 결</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 10년 단위의 큰 인생 궤도</span>\n"
                        f"[※ AI 통변 지시: 전체 대운(초/중/말년)의 거대한 흐름과 큰 줄기를 조망하십시오. 임의로 나이나 연도를 추정하지 말고 대운표의 흐름을 반영하여 에세이처럼 풀어내십시오.]\n"
                        f"</div>\n\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 1년 단위의 세밀한 파동</span>\n"
                        f"[SEWUN_TABLE_HERE]\n"
                        f"<br><b>(1) 향후 10년의 기류 변화</b>\n"
                        f"[※ AI 통변 지시: 향후 10년 세운의 기류 변화를 거시적으로 먼저 설명하십시오.]\n"
                        f"<br><b>(2) 올해의 현실적 사건과 조언</b>\n"
                        f"[※ AI 통변 지시: 올해({curr_y}년)의 현실적 사건과 다정한 조언을 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 삶을 풍요롭게 만드는 실천 플랜</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<br><b>1) 나를 돕는 행운의 에너지와 색상</b>\n"
                        f"[※ AI 통변 지시: 일상에서 쉽게 활용할 수 있는 행운의 색상과 수리를 다정하게 제시하십시오.]\n"
                        f"<br><b>2) 재물을 지키고 불리는 절제의 지혜</b>\n"
                        f"[※ AI 통변 지시: 지출을 통제하고 자산을 안정적으로 관리하기 위한 가이드를 조언하십시오.]\n"
                        f"<br><b>3) 타고난 재능을 극대화하는 직업적 실전 전략</b>\n"
                        f"[※ AI 통변 지시: 본인의 강점을 살릴 수 있는 현실적인 무기 활용법을 조언하십시오.]\n"
                        f"<br><b>4) 인생의 정체를 돌파하는 4대 실전 솔루션</b>\n"
                        f"[※ AI 통변 지시: 명리적 환경 보완 원리를 활용해 실전 솔루션을 상세히 조언하십시오.]\n"
                        f"<br><b>5) 긍정적 기운을 부르는 공간과 방위 활용법</b>\n"
                        f"[※ AI 통변 지시: 긍정적 기운을 끌어당기는 가구 배치 및 인테리어 팁을 제시하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>5. 운의 흐름을 내 편으로 만드는 특별 솔루션</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<br><b>1) 결정적 순간에 나를 돕는 조력자 활용법</b>\n"
                        f"[※ AI 통변 지시: 천을귀인 등의 에너지를 활용해 든든한 힘이 되어주는 조력자 활용법을 설명하십시오.]\n"
                        f"<br><b>2) 소중한 인연을 지키고 가꾸는 관계의 지혜</b>\n"
                        f"[※ AI 통변 지시: 관계 속 마찰 원인을 짚어내고 인연을 단단하게 가꾸는 소통 가이드를 조언하십시오.]\n"
                        f"<br><b>3) 위기를 기회로 반전시키는 마인드셋</b>\n"
                        f"[※ AI 통변 지시: 변화 속에서도 멘탈을 다잡고 유리한 국면으로 전환할 행동 가이드를 조언하십시오.]\n"
                        f"</div>\n\n"

                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 현재 고민에 대한 원인 진단</span>\n"
                        f"[※ AI 통변 지시: 신청자의 고민이 없다면 일반적 조언을, 있다면 현 상황에 공감하고 사주적 원인을 진단하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 답답함을 풀어줄 명확한 해법과 타개 시기</span>\n"
                        f"[※ AI 통변 지시: 언제쯤 고비가 풀리는지 시기를 명시하고 현실적 행동 지침을 세련되게 처방하십시오.]\n"
                        f"</div>\n"
                    )
                    
                    # 🚨 여기서부터 아래로 쭈욱 덮어써 주십시오! (들여쓰기 20칸)
                    try:
                        # AI API 호출
                        res = model.generate_content(prompt)
                        ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                        
                        # 1. 옥의 티 수술 (마크다운 볼드체 html 변환)
                        ai_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', ai_text)
                        
                        # 2. 골든 텍스트 치환
                        if "[CHOYEON_GOLDEN_TEXT_HERE]" in ai_text:
                            ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)
                        
                        # 3. 표 HTML 정리
                        un_html_clean = un_html.replace("\n", " ").replace("\r", "")
                        se_html_clean = se_html.replace("\n", " ").replace("\r", "")
                        
                        daeoun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{un_html_clean}</div>"
                        sewun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{se_html_clean}</div>"
                        
                        # 4. AI 텍스트 내 마커 정리 (대운표 마커 삭제, 세운표 삽입)
                        clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*DAEWUN_TABLE_HERE\s*\][\#\*\_\s]*', '', ai_text, flags=re.IGNORECASE)
                        clean_ai_text, count_s = re.subn(r'[\#\*\_\s]*\[\s*SEWUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                        
                        if count_s == 0 and "table" not in clean_ai_text.lower():
                            clean_ai_text += f"<br><br><span style='color:red; font-weight:bold;'>⚠️ (AI 세운표 마커 누락 비상 출력)</span><br>{sewun_target}"
                        
                        # 5. [최종 조립] 원국표 -> 대운표 -> intro_html -> AI통변 -> 맺음말
                        bordered_closing_html = f"<hr style='border: 0; border-top: 2px dashed #000000; margin: 35px 0 20px 0;'>{closing_html}"
                        
                        full_content_clean = (
                            f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000;'>"
                            f"{daeoun_target}\n"
                            f"{intro_html}\n"
                            f"{clean_ai_text}\n<br><br>"
                            f"{bordered_closing_html}"
                            f"</div>"
                        )
                        
                        # 6. 표지 타이틀 교체 및 여백 강제 축소
                        import re
                        dynamic_title = u_product.split('. ')[-1] if '. ' in u_product else u_product
                        
                        report_1_full_html = re.sub(r'(<h1[^>]*>).*?(<\/h1>)', r'\g<1>' + dynamic_title + r'\2', report_1_full_html, count=1, flags=re.IGNORECASE|re.DOTALL)
                        report_1_full_html = re.sub(r'min-height:\s*250mm\s*;?', 'min-height: 120mm;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'padding:\s*40px\s+0\s*;?', 'padding: 10px 0;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'padding:\s*42px\s+24px\s*;?', 'padding: 20px 24px;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'margin-bottom:\s*28px\s*;?', 'margin-bottom: 15px;', report_1_full_html, flags=re.IGNORECASE)

                        # 7. 최종 렌더링 세팅
                        report_1_full_html = report_1_full_html.replace("{full_content_clean_placeholder}", full_content_clean)
                        
                        st.session_state['saved_report_html'] = report_1_full_html
                        
                    except Exception as e:
                        st.error(f"1-1번 사주풀이 가동 장애: {e}")

                elif u_product == "1-2. 올해 운세 상세분석":
                    target_year_val = st.session_state.get('target_year_input', curr_y)
                    prompt = (
                        f"{db_header}\n"
                        f"{ilju_master_prompt_context}\n\n"
                        f"🧠 [1-2. {target_year_val}년 운세 상세분석 정밀 지침]\n"
                        f"[SYSTEM ROLE: 초연시공명리 최고위 전문가]\n"
                        f"🚨 아래 목차는 정확히 '1. / 2. / 3. / 4. 고민 상담 Q&A' 4개 대제목으로만 구성되어 있다.\n"
                        f"이 4개 외에 새로운 대제목을 임의로 추가하거나, 목차를 확장하는 것을 절대 금지한다.\n"
                        f"본 상담은 원국과 대운({dw_g_cur}{dw_j_cur})의 거시적 기운을 뼈대로 삼아, 지정된 **{target_year_val}년**의 연도별 운세 흐름을 칼같이 분석하는 상세 리포트입니다.\n\n"
                        f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                        f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                        f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                        f"3. 표(Table) 생성 절대 금지.\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 지나온 과거 세운 흐름 회고</h3>\n"
                        f"[SEWUN_TABLE_HERE]\n"
                        f"<div class='content-box-loose'>\n"
                        f"🚨 [세운 줄바꿈 절대 규칙]: 각 세운 항목(• ... :)의 쌍점(:) 뒤 해설은 반드시 독립된 <p style='text-indent: 1em; margin-bottom: 12px;'> 태그로 감싸 한 줄씩 완전히 줄바꿈하여 작성하십시오.\n"
                        f"{past_sewun_html}\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. {target_year_val}년 운세 정밀 상세분석</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>▶ {target_year_val}년 전반기(상반기) 상세 분석</span>\n"
                        f"[※ AI 통변 지시: 상반기 동안 일어나는 주된 환경적 기회, 재물/직업상의 변동성, 실질적 사건·사고의 팩트를 명쾌하게 풀이하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>▶ {target_year_val}년 후반기(하반기) 상세 분석</span>\n"
                        f"[※ AI 통변 지시: 하반기 동안 집중해야 할 핵심 결실, 인연의 길흉, 리스크 방어를 위한 실질적 지침을 서술하십시오.]\n"
                        f"</div>\n\n"


                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. {target_year_val}년 맞춤형 개운 비법 및 조언</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"[※ AI 통변 지시: 해당 연도의 기운을 극대화하고 리스크를 우회할 실질적 처세술 및 개운 비법을 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 고민 상담 Q&A</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 올해의 고민 상황 공감</span>\n"
                        f"[※ AI 통변 지시: 신청자가 남긴 단기적 고민에 공감해 주십시오. 구체적 사실을 묻고 있다면 에둘러가지 말고 이 항목 안에서 곧바로 명확한 답을 제시한 후, 원국의 뼈대와 올해({target_year_val}년)의 기운을 바탕으로 현 상황을 분석하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 올해 핵심 행동 처방</span>\n"
                        f"[※ AI 통변 지시: 올해 내로 가장 성과가 좋거나 갈등이 풀릴 달(월)과 시기를 짚어주고, 즉각적인 행동 지침을 세련되게 처방하십시오.]\n"
                        f"</div>\n"
                    )
                    try:
                        res = model.generate_content(prompt)
                        ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                        ai_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', ai_text)
                        
                        if "[CHOYEON_GOLDEN_TEXT_HERE]" in ai_text:
                            ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)
                        
                        un_html_clean = un_html.replace("\n", " ").replace("\r", "")
                        se_html_clean = se_html.replace("\n", " ").replace("\r", "")
                        
                        daeoun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{un_html_clean}</div>"
                        sewun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{se_html_clean}</div>"
                        
                        # 🚨 대운표 마커 삭제 (상단 고정할 것이므로) 및 세운표 본문 삽입
                        clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*DAEWUN_TABLE_HERE\s*\][\#\*\_\s]*', '', ai_text, flags=re.IGNORECASE)
                        clean_ai_text, count_s = re.subn(r'[\#\*\_\s]*\[\s*SEWUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                        
                        # 🚨 [최종 조립] 원국표 -> 대운표 -> AI통변(intro_html 제외) -> 맺음말
                        bordered_closing_html = f"<hr style='border: 0; border-top: 2px dashed #000000; margin: 35px 0 20px 0;'>{closing_html}"
                        full_content_clean = (
                            f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000;'>"
                            f"{daeoun_target}\n"
                            f"{clean_ai_text}\n<br><br>"
                            f"{bordered_closing_html}"
                            f"</div>"
                        )
                        
                        # 🚨 표지 타이틀 교체 및 여백 강제 축소
                        dynamic_title = u_product.split('. ')[-1] if '. ' in u_product else u_product
                        report_1_full_html = re.sub(r'(<h1[^>]*>).*?(<\/h1>)', r'\g<1>' + dynamic_title + r'\2', report_1_full_html, count=1, flags=re.IGNORECASE|re.DOTALL)
                        report_1_full_html = re.sub(r'min-height:\s*250mm\s*;?', 'min-height: 120mm;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'padding:\s*40px\s+0\s*;?', 'padding: 10px 0;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'padding:\s*42px\s+24px\s*;?', 'padding: 20px 24px;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'margin-bottom:\s*28px\s*;?', 'margin-bottom: 15px;', report_1_full_html, flags=re.IGNORECASE)

                        report_1_full_html = report_1_full_html.replace("{full_content_clean_placeholder}", full_content_clean)
                        st.session_state['saved_report_html'] = report_1_full_html
                        
                    except Exception as e:
                        st.error(f"1-2번 연산 오류: {e}")


                elif u_product == "1-3. 이번달 운세 상세분석":
                    prompt = (
                        f"{db_header}\n"
                        f"{ilju_master_prompt_context}\n\n"
                        f"================================================================================\n"
                        f"🧠 [1-3. 월운 상세분석 정밀 지침]\n"
                        f"================================================================================\n"
                        f"[SYSTEM ROLE: 초연시공명리 최고위 전문가]\n"
                        f"🚨 아래 목차는 정확히 '1. / 2. / 3. / 4. 고민 상담 Q&A' 4개 대제목으로만 구성되어 있다.\n"
                        f"이 4개 외에 새로운 대제목을 임의로 추가하거나, 목차를 확장하는 것을 절대 금지한다.\n"
                        f"본 상담은 세운({curr_y_ganji[0]}{curr_y_ganji[1]}년)의 거시적 기운을 뼈대로 삼아, 특정 월의 미세한 기운 파동을 포착하는 초단기 실전 분석 리포트입니다.\n\n"
                        f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                        f"1. 난해한 용어 배제, 즉각적 행동 지침 위주.\n"
                        f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                        f"3. 표(Table) 생성 절대 금지.\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 지나온 월운 회고</h3>\n"
                        f"[SEWUN_TABLE_HERE]\n"
                        f"[WOLWUN_TABLE_HERE]\n"
                        f"<div class='content-box-loose'>\n"
                        f"🚨 [월운 줄바꿈 절대 규칙]: 각 월운 항목(• ... :)의 쌍점(:) 뒤 해설은 반드시 독립된 <p style='text-indent: 1em; margin-bottom: 12px;'> 태그로 감싸 한 줄씩 완전히 줄바꿈하여 작성하십시오.\n"
                        f"{past_months_html}\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 월운 상세 파동 분석</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>{prompt_first_half}</span>\n"
                        f"[※ AI 통변 지시: 이번 달 전반기 동안 발생할 주요 심리 파동, 실질적 행동 지침 및 주의점 팩트를 서술하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>{prompt_second_half}</span>\n"
                        f"[※ AI 통변 지시: 이번 달 후반기 동안 맞이할 실질적 사건, 재물/대인관계의 성패, 마무리 대응 전략을 상세히 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 단기 성공을 위한 개운 비법</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"[※ AI 통변 지시: 이번 달 파동을 극대화할 단기 처세술과 행운의 에너지 활용법을 조언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 고민 상담 Q&A</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 이달의 고민 상황 공감</span>\n"
                        f"[※ AI 통변 지시: 신청자가 남긴 단기적 고민에 공감해 주십시오. 구체적 사실을 묻고 있다면 에둘러가지 말고 이 항목 안에서 곧바로 명확한 답을 제시한 후, 원국의 뼈대와 이번 달의 기운을 바탕으로 현 상황을 분석하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 이번 달 핵심 행동 처방</span>\n"
                        f"[※ AI 통변 지시: 이번 달 내로 가장 성과가 좋거나 갈등이 풀릴 주간이나 일자를 짚어주고, 즉각적인 행동 지침을 세련되게 처방하십시오.]\n"
                        f"</div>\n"
                    )
                    try:
                        res = model.generate_content(prompt)
                        ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                        ai_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', ai_text)
                        
                        if "[CHOYEON_GOLDEN_TEXT_HERE]" in ai_text:
                            ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)
                        
                        un_html_clean = un_html.replace("\n", " ").replace("\r", "")
                        se_html_clean = se_html.replace("\n", " ").replace("\r", "")
                        wol_html_clean = wol_html.replace("\n", " ").replace("\r", "")
                        
                        daeoun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{un_html_clean}</div>"
                        sewun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{se_html_clean}</div>"
                        wolwun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{wol_html_clean}</div>"
                        
                        clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*DAEWUN_TABLE_HERE\s*\][\#\*\_\s]*', '', ai_text, flags=re.IGNORECASE)
                        clean_ai_text, count_s = re.subn(r'[\#\*\_\s]*\[\s*SEWUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                        clean_ai_text, count_w = re.subn(r'[\#\*\_\s]*\[\s*WOLWUN_TABLE_HERE\s*\][\#\*\_\s]*', wolwun_target, clean_ai_text, flags=re.IGNORECASE)
                        
                        bordered_closing_html = f"<hr style='border: 0; border-top: 2px dashed #000000; margin: 35px 0 20px 0;'>{closing_html}"
                        full_content_clean = (
                            f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000;'>"
                            f"{daeoun_target}\n"
                            f"{clean_ai_text}\n<br><br>"
                            f"{bordered_closing_html}"
                            f"</div>"
                        )
                        
                        dynamic_title = u_product.split('. ')[-1] if '. ' in u_product else u_product
                        report_1_full_html = re.sub(r'(<h1[^>]*>).*?(<\/h1>)', r'\g<1>' + dynamic_title + r'\2', report_1_full_html, count=1, flags=re.IGNORECASE|re.DOTALL)
                        report_1_full_html = re.sub(r'min-height:\s*250mm\s*;?', 'min-height: 120mm;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'padding:\s*40px\s+0\s*;?', 'padding: 10px 0;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'padding:\s*42px\s+24px\s*;?', 'padding: 20px 24px;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'margin-bottom:\s*28px\s*;?', 'margin-bottom: 15px;', report_1_full_html, flags=re.IGNORECASE)

                        report_1_full_html = report_1_full_html.replace("{full_content_clean_placeholder}", full_content_clean)
                        st.session_state['saved_report_html'] = report_1_full_html
                        
                    except Exception as e:
                        st.error(f"1-3번 연산 오류: {e}")

                elif u_product == "1-4. 주간 및 일운 상세분석":
                    t_date = st.session_state.get('target_date', dt_mod.date.today())
                    
                    prompt = (
                        f"{db_header}\n"
                        f"{ilju_master_prompt_context}\n\n"
                        f"================================================================================\n"
                        f"🧠 [1-4. 이번 (특정) 주간 및 일 운세 상세분석 프롬프트]\n"
                        f"================================================================================\n"
                        f"[SYSTEM ROLE: 초연시공명리 최고위 전문가]\n"
                        f"🚨 아래 목차는 정확히 '1. / 2. / 3. / 4. 고민 상담 Q&A' 4개 대제목으로만 구성되어 있다. \n"
                        f"이 4개 외에 새로운 대제목을 임의로 추가하거나, 목차를 확장하는 것을 절대 금지한다.\n"
                        f"본 1-4 분석은 초연시공명리의 자랑인 '폭포수 운세분석(원국 ➡️ 대운 ➡️ 세운 ➡️ 주/일운)'의 정수이다.\n"
                        f"원국과 대운({dw_g_cur}{dw_j_cur}), 세운이 만들어내는 거시적인 기운(체: 體)을 든든한 뼈대로 삼아, \n"
                        f"지정된 날짜({t_date})의 주간 및 일진(日辰) 흐름(용: 用)이 신청자의 삶에 미치는 미세한 파동을 폭포수처럼 유기적으로 연결하여 정밀 분석할 것.\n\n"
                        f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                        f"1. 난해한 용어 배제, 즉각적 행동 지침 위주.\n"
                        f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                        f"3. 표(Table) 생성 절대 금지.\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 이번 주간 및 오늘의 운 분석</h3>\n"
                        f"[SEWUN_TABLE_HERE]\n"
                        f"[WOLWUN_TABLE_HERE]\n"
                        f"[WEEKLY_CALENDAR_HERE]\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 주간 거시 흐름과 체용의 결합</span>\n"
                        f"[※ AI 통변 지시: 원국과 대운/세운의 거대한 기류(체) 속에서, 이번 한 주 동안 전개되는 기운(용)이 어떤 의미를 가지는지 '폭포수 흐름'으로 연결하여 명확히 서술하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 오늘의 일진 분석과 융합 기류</span>\n"
                        f"[※ AI 통변 지시: {t_date} 오늘 하루를 지배하는 일진 간지의 자의 형상과 원국의 결합 기류를 바탕으로 컨디션 기복 및 대인관계 핵심 기류를 서술하십시오. 일진의 십성 작용과 시공명리의 합형파해 기류, 시간방향성을 융합하여 실전적인 감정/행동 파동을 짚어내십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 시간대별 운의 분석</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 전반부 흐름 (23:30 ~ 11:29)</span>\n"
                        f"[※ AI 통변 지시: 한국 표준시 시차(-30분)가 적용된 야간 자시(夜子時)부터 오전까지의 기운 흐름, 집중도, 업무/소통 시 성과 창출 타이밍을 정밀 서술하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 후반부 흐름 (11:30 ~ 23:29)</span>\n"
                        f"[※ AI 통변 지시: 오시(午時)를 기점으로 낮부터 저녁/야간으로 이어지는 기운의 수렴 양상, 감정 조율, 저녁 시간대 처세 및 피로 관리 가이드를 조언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 오늘의 행동 지침</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"[※ AI 통변 지시: 오늘 하루의 운을 극대화하고 마찰을 완벽히 방어하기 위한 실전 행동 조언을 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 고민 상담 Q&A</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 오늘의 고민 상황 공감</span>\n"
                        f"[※ AI 통변 지시: 신청자가 남긴 단기적 고민에 공감해 주십시오. 구체적 사실을 묻고 있다면 에둘러가지 말고 이 항목 안에서 곧바로 명확한 답을 제시한 후, 원국의 뼈대와 오늘의 단기적인 기운을 바탕으로 현 상황을 분석하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 이번 주 핵심 행동 처방</span>\n"
                        f"[※ AI 통변 지시: 이번 주 내로 가장 성과가 좋거나 갈등이 풀릴 요일/시간대와 함께, 즉각적인 행동 지침을 세련되게 처방하십시오.]\n"
                        f"</div>\n"
                    )
                    try:
                        # 1. 캘린더 생성부 (이전 교정사항 모두 유지)
                        klc = KoreanLunarCalendar()
                        days_offset = (t_date.weekday() + 1) % 7
                        start_of_week = t_date - dt_mod.timedelta(days=days_offset)
                        
                        weekly_html = f"<div style='margin-bottom: 20px;'><div style='margin-top: 5px; margin-bottom: 10px; font-size: 18px; font-weight: 900; color: #000000;'>[ 주간 일진 흐름표 ({t_date.strftime('%Y-%m-%d')} 기준) ]</div>"
                        weekly_html += "<div style='display:flex; width:100%; border:2px solid #000000; background:white;'>"
                        
                        day_names = ["일", "월", "화", "수", "목", "금", "토"]
                        day_colors = ["#D50000", "#555555", "#555555", "#555555", "#555555", "#555555", "#1565C0"]
                        
                        actual_ds = st.session_state['global_gans'][1] if 'global_gans' in st.session_state else ds
                        actual_yb = st.session_state['global_jjis'][3] if 'global_jjis' in st.session_state else yb
                        actual_db = st.session_state['global_jjis'][1] if 'global_jjis' in st.session_state else db
                        
                        for i in range(7):
                            cur_d = start_of_week + dt_mod.timedelta(days=i)
                            klc.setSolarDate(cur_d.year, cur_d.month, cur_d.day)
                            gapja = klc.getChineseGapJaString()
                            iljin = gapja.split()[2] if len(gapja.split()) >= 3 else "甲子"
                            c_hanja = iljin[0]
                            j_hanja = iljin[1]
                            
                            ss_gan = get_ss(actual_ds, c_hanja)
                            ss_ji = get_ss(actual_ds, j_hanja)
                            unsung = get_unsung(actual_ds, j_hanja)
                            y_shinsal = get_12_shinsal(actual_yb, j_hanja)
                            d_shinsal = get_12_shinsal(actual_db, j_hanja)
                            
                            b_left = "1px solid #ccc" if i > 0 else "none"
                            bg_col = "#FFF9C4" if cur_d == t_date else "transparent"
                            head_bg = day_colors[i]
                            
                            date_str = f"{cur_d.month}/{cur_d.day}"
                            day_str = day_names[i]
                            
                            gan_color_cls = f"color-{get_color(c_hanja)}"
                            ji_color_cls = f"color-{get_color(j_hanja)}"
                            
                            cell_html = (
                                f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'>"
                                f"    <div style='background-color:{head_bg}; color:#FFFFFF; font-weight:900;'>"
                                f"        <div style='padding:6px 0; font-size:16px; border-bottom:1px solid rgba(255,255,255,0.4);'>{day_str}</div>"
                                f"        <div style='padding:4px 0; font-size:13px; border-bottom:1px solid #ccc;'>{date_str}</div>"
                                f"    </div>"
                                f"    <div style='padding:2px; font-size:11px; color:#000000;'>{ss_gan}</div>"
                                f"    <div class='{gan_color_cls}' style='font-size:16px; font-weight:900;'>{c_hanja}</div>"
                                f"    <div class='{ji_color_cls}' style='font-size:16px; font-weight:900;'>{j_hanja}</div>"
                                f"    <div style='padding:2px; font-size:11px; color:#000000;'>{ss_ji}</div>"
                                f"    <div style='font-size:10px; border-top:1px solid #eee; color:#0D47A1;'>{unsung}</div>"
                                f"    <div style='font-size:10px; color:#C62828; border-top:1px solid #eee;'>{y_shinsal}</div>"
                                f"    <div style='font-size:10px; color:#1565C0; border-top:1px solid #eee;'>{d_shinsal}</div>"
                                f"</div>"
                            )
                            weekly_html += cell_html
                            
                        weekly_html += "</div></div>"

                        # 2. AI 호출 및 파싱
                        res = model.generate_content(prompt)
                        ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                        ai_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', ai_text)
                        
                        if "[CHOYEON_GOLDEN_TEXT_HERE]" in ai_text:
                            ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)

                        un_html_clean = un_html.replace("\n", " ").replace("\r", "")
                        se_html_clean = se_html.replace("\n", " ").replace("\r", "")
                        wol_html_clean = wol_html.replace("\n", " ").replace("\r", "")
                        weekly_html_clean = weekly_html.replace("\n", " ").replace("\r", "")

                        daeoun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{un_html_clean}</div>"
                        sewun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{se_html_clean}</div>"
                        wolwun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{wol_html_clean}</div>"
                        weekly_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{weekly_html_clean}</div>"

                        # 3. 마커 치환 및 조립
                        clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*DAEWUN_TABLE_HERE\s*\][\#\*\_\s]*', '', ai_text, flags=re.IGNORECASE)
                        clean_ai_text, count_s = re.subn(r'[\#\*\_\s]*\[\s*SEWUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                        clean_ai_text, count_w = re.subn(r'[\#\*\_\s]*\[\s*WOLWUN_TABLE_HERE\s*\][\#\*\_\s]*', wolwun_target, clean_ai_text, flags=re.IGNORECASE)
                        clean_ai_text, count_wk = re.subn(r'[\#\*\_\s]*\[\s*WEEKLY_CALENDAR_HERE\s*\][\#\*\_\s]*', weekly_target, clean_ai_text, flags=re.IGNORECASE)

                        bordered_closing_html = f"<hr style='border: 0; border-top: 2px dashed #000000; margin: 35px 0 20px 0;'>{closing_html}"
                        full_content_clean = (
                            f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000;'>"
                            f"{daeoun_target}\n"
                            f"{clean_ai_text}\n<br><br>"
                            f"{bordered_closing_html}"
                            f"</div>"
                        )

                        # 4. 표지 타이틀 교체 및 여백 강제 축소
                        import re
                        dynamic_title = u_product.split('. ')[-1] if '. ' in u_product else u_product
                        report_1_full_html = re.sub(r'(<h1[^>]*>).*?(<\/h1>)', r'\g<1>' + dynamic_title + r'\2', report_1_full_html, count=1, flags=re.IGNORECASE|re.DOTALL)
                        report_1_full_html = re.sub(r'min-height:\s*250mm\s*;?', 'min-height: 120mm;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'padding:\s*40px\s+0\s*;?', 'padding: 10px 0;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'padding:\s*42px\s+24px\s*;?', 'padding: 20px 24px;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'margin-bottom:\s*28px\s*;?', 'margin-bottom: 15px;', report_1_full_html, flags=re.IGNORECASE)

                        report_1_full_html = report_1_full_html.replace("{full_content_clean_placeholder}", full_content_clean)
                        st.session_state['saved_report_html'] = report_1_full_html
                        
                    except Exception as e:
                        st.error(f"1-4번 연산 오류: {e}")

            # ==============================================================
            # [A-2] 2. 테마별 특성화 상담 (85.5버전 프롬프트 완벽 이식 & Q&A 추가)
            # ==============================================================
            elif main_category == "2. 테마별 특성화 상담":
                
                wealth_goal = st.session_state.get('wealth_goal', '안정적인 자산 증식')
                love_goal = st.session_state.get('love_goal', '좋은 인연과 화목한 관계')
                career_goal = st.session_state.get('career_goal', '성공적인 진로와 커리어 성취')
                health_goal = st.session_state.get('health_goal', '일상의 활력과 신체 밸런스 유지')
                
                s_d_val = start_date if start_date else dt_mod.date.today()
                e_d_val = end_date if end_date else dt_mod.date.today() + dt_mod.timedelta(days=30)
                
                공통_시스템_헤더 = f"{db_header}\n{ilju_master_prompt_context}\n"

                if u_product == "2-1. 재물운 특화 분석":
                    prompt = (
                        f"{공통_시스템_헤더}\n"
                        f"[SYSTEM ROLE: 초연시공명리 최고위 재물 자산 컨설턴트]\n"
                        f"귀하는 초연시공명리학의 원리와 시공간 파동을 완벽히 통달한 대명리학자이다.\n"
                        f"원국의 재성(財星)과 식상(食傷), 관성(官星)의 유기적 관계, 묘고(庫)의 동태, 천간 삼자조합 물상 팩트, \n"
                        f"丑戌未 개고 변곡점, 부 vs 내면평화 상호작용 지수, \n"
                        f"그리고 시간방향(時間方向)에 따른 재물 에너지의 자발적 유입 vs 방해 협자(夾字) 제압 메커니즘을 바탕으로 타고난 재물 그릇의 크기, 이재 감각, \n"
                        f"그리고 일생을 관통하는 부(富)의 축적 타이밍과 손재수 방어책을 정밀 통변할 것.\n\n"
                        f"🚨 [재물 특화 상담 절대 지시]\n"
                        f"■ 일반적인 성격 풀이나 원국 전체의 일반적 서사는 철저히 배제한다.\n"
                        f"■ 오직 신청자의 재물 고민({wealth_goal})을 중심 축으로 삼아, 재물 그릇, 현금 흐름, 대운/세운별 재성운 발현 시기 및 실전 자산 방어/증식 솔루션에 통변의 90% 이상을 집중할 것.\n"
                        f"■ '1. 타고난 재물 그릇 및 고민 정밀 진단' 소제목 바로 아래 줄에 `[DAEWUN_TABLE_HERE]` 및 `[SEWUN_TABLE_HERE]` 마커를 반드시 출력할 것.\n\n"
                        f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                        f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                        f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                        f"3. 표(Table) 생성 절대 금지.\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 타고난 재물 그릇 및 고민({wealth_goal}) 정밀 진단</h3>\n"
                        f"[SEWUN_TABLE_HERE]\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 재물 그릇과 정재 vs 편재 성향</span>\n"
                        f"[※ AI 통변 지시: 원국의 재성 오행 및 십성 구조를 바탕으로 타고난 재물 그릇의 규모와 정재(안정적 수입) vs 편재(사업/투자) 성향을 정밀 분석하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 자산 축적 메커니즘과 창고 동태</span>\n"
                        f"[※ AI 통변 지시: 식상생재, 재생관, 그리고 묘고(창고)의 개고/입고 시점 및 자산 축적 메커니즘을 짚어내십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>3) 시간방향에 따른 재물 유입 판정</span>\n"
                        f"[※ AI 통변 지시: 원국의 시간방향을 분석하여 억지로 좇지 않아도 부가 스스로 유입되는 그릇인지 판별하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>4) 신청인 재물 고민의 명리적 진단</span>\n"
                        f"[※ AI 통변 지시: 신청자의 재물 고민({wealth_goal})에 대해 사주 기운이 어떻게 작용하는지 직언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 재산 축적의 유리한 시기와 현금 흐름 분석</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 대운 및 세운별 재성운 발현 타이밍</span>\n"
                        f"[※ AI 통변 지시: 전체 흐름 중 어느 대운에 재성운이 들어오는지 분석하고, 현 대운 중 어느 연도에 발현되는지 서술하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 방해 협자 제압과 개고 황금기</span>\n"
                        f"[※ AI 통변 지시: 재물 합을 가로막던 협자가 제압되거나 묘고가 열리는 황금기 변곡점을 제시하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>3) 최적의 재산 증식 수단 추천</span>\n"
                        f"[※ AI 통변 지시: 본인 사주에 가장 부합하는 최적의 재산 증식 수단(부동산, 주식, 사업 등)을 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 손재수 방어 및 리스크 가이드</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 손재수 발생 시기와 경고</span>\n"
                        f"[※ AI 통변 지시: 비겁 발동, 충형에 의한 재물 창고 파손 등 손재수 발생 시기를 명확히 경고하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 이재 약점 진단과 방어 가이드</span>\n"
                        f"[※ AI 통변 지시: 본인의 이재 패턴 약점을 진단하고 실전 방어 가이드를 조언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 부를 부르는 맞춤형 개운법</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"[※ AI 통변 지시: 부족한 재성 기운을 활성화하기 위한 실천적 마인드셋과 행운의 팁을 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>5. 고민 상담 Q&A</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 재물 고민 공감 및 원인 분석</span>\n"
                        f"[※ AI 통변 지시: 신청자의 고민({wealth_goal})에 깊이 공감하고, 자금 흐름이 답답한 원인을 사주 원리(비겁 발동, 묘고 등)로 명확히 진단하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 재물운 개화 시기와 자산 솔루션</span>\n"
                        f"[※ AI 통변 지시: 답답함이 풀리고 재물운이 크게 트이는 정확한 시기(연도)와 실질적인 자산 관리법을 세련되게 제시하십시오.]\n"
                        f"</div>\n"
                    )

                elif u_product == "2-2. 연애/결혼운 특화 분석":
                    prompt = (
                        f"{공통_시스템_헤더}\n"
                        f"[SYSTEM ROLE: 초연시공명리 최고위 부부/연애 심리 상담가 & 흉화 예방 컨설턴트]\n"
                        f"귀하는 초연시공명리학의 원리와 시공간 파동을 완벽히 통달한 대명리학자이다.\n"
                        f"배우자궁(일지)의 환경, 배우자 인연 복합 파동, 신살 리스크, 대안적 시공간 설계, \n"
                        f"그리고 일지 배우자성에서 타인궁으로 흐르는 시간방향 이탈 궤도를 종합하여, \n"
                        f"타고난 연애 관념, 인연 도래 시기, 결혼 전 점검해야 할 흉화 방어 백신 조언을 정밀 통변할 것.\n\n"
                        f"🚨 [결혼 전 흉화 예방 특화 상담 절대 지시]\n"
                        f"■ 일반적인 서사는 배제하고, 이성/결혼 고민({love_goal})을 중심 축으로 삼아 인연 도래 시기 및 실전 애정 솔루션에 집중할 것.\n"
                        f"■ '1. 타고난 연애 성향 및 고민 정밀 진단' 소제목 바로 아래 줄에 `[DAEWUN_TABLE_HERE]` 마커를 반드시 출력할 것.\n\n"
                        f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                        f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                        f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                        f"3. 표(Table) 생성 절대 금지.\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 타고난 연애 성향 및 고민({love_goal}) 정밀 진단</h3>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 이상형과 애정 표현 스타일</span>\n"
                        f"[※ AI 통변 지시: 일지(배우자궁)와 배우자성의 십성을 분석하여 이상형과 연애 스타일을 서술하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 배우자궁 인연 패턴과 기질</span>\n"
                        f"[※ AI 통변 지시: 일지 묘고·관대로 인한 독립성, 궁위 흔들림 등 복합적인 인연 패턴을 깊이 있게 통변하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>3) 시간방향에 따른 배우자 궤도</span>\n"
                        f"[※ AI 통변 지시: 일지 배우자가 시지(타인)를 향하는지, 협자로 인해 위축되는 형태인지 정밀 진단하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>4) 이성/결혼 고민의 명리적 진단</span>\n"
                        f"[※ AI 통변 지시: 신청자의 이성 고민({love_goal})에 대해 기운이 어떻게 작용하는지 직언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 인연이 도래하는 시기와 만남의 형태</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 대운 및 세운별 인연운 발현 시기</span>\n"
                        f"[※ AI 통변 지시: 어느 대운/세운에 인연운이 강하게 발현되는지 분석하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 운명적 인연 도래 골든타임</span>\n"
                        f"[※ AI 통변 지시: 도화살, 귀인, 일지 합 등을 바탕으로 만남의 골든 타임과 경로를 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. [결혼 전 사전 체크] 갈등 패턴과 흉화 리스크</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 이성 구설 및 감정 소모 리스크</span>\n"
                        f"[※ AI 통변 지시: 신살과 파동을 엮어 감정 소모 및 구설 리스크를 경고하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 배우자궁 충형과 주도권 다툼</span>\n"
                        f"[※ AI 통변 지시: 배우자궁 충형 마찰과 주도권 다툼을 사전에 엄정히 판별하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 백년해로를 위한 사전 개운 백신</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"[※ AI 통변 지시: 시공간적 물리적 이격(주말부부, 각방 등) 및 실천 마인드셋을 조언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>5. 고민 상담 Q&A</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 애정 고민 공감 및 원인 분석</span>\n"
                        f"[※ AI 통변 지시: 신청자의 이별/애정 고민({love_goal})에 따뜻하게 공감하고, 꼬인 관계의 원인을 일지 충형, 도화살 등 기류로 분석하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 대박을 위한 실전 사업가 마인드</span>\n"
                        f"[※ AI 통변 지시: 완벽한 길일이 선사할 재물 파동을 믿고 돌격할 수 있도록 실전 사업가 마인드를 조언하십시오.]\n"
                        f"</div>\n"
                    ) 

                elif u_product == "2-3. 진학/입시운 특화 분석":
                    prompt = (
                        f"{공통_시스템_헤더}\n"
                        f"[SYSTEM ROLE: 초연시공명리 최고위 학업 진로 & 입시 전략 컨설턴트]\n"
                        f"귀하는 초연시공명리학의 원리와 시공간 파동을 완벽히 통달한 대명리학자이다.\n"
                        f"인성(학문)과 식상(응용력), 관성(합격운), 시간방향(時間方向)에 따른 학업 몰입도를 바탕으로 \n"
                        f"타고난 학습 기질, 문·이과 적성, 최적의 대학 전공 계열, 시험 및 입시 합격의 골든타임을 정밀 통변할 것.\n\n"
                        f"🚨 [진학/입시 특화 상담 절대 지시]\n"
                        f"■ 성인 대상의 일반 직무나 서사는 철저히 배제한다.\n"
                        f"■ 신청자의 학업 고민({career_goal})을 축으로 학습 적성, 전공 계열 추천, 합격운 타이밍에 집중할 것.\n"
                        f"■ '1. 타고난 학업 성향 및 고민 정밀 진단' 소제목 아래에 `[DAEWUN_TABLE_HERE]` 및 `[SEWUN_TABLE_HERE]` 마커를 출력할 것.\n\n"
                        f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                        f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                        f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                        f"3. 표(Table) 생성 절대 금지.\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 타고난 학업 성향 및 고민({career_goal}) 정밀 진단</h3>\n"
                        f"[SEWUN_TABLE_HERE]\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 두뇌 기질과 학습 스타일 분석</span>\n"
                        f"[※ AI 통변 지시: 인성과 식상의 역학을 바탕으로 타고난 두뇌 스타일(암기형 vs 응용형)을 정밀 분석하고, 현재 운기가 성적 상승장인지 슬럼프인지 짚어내십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 진학/학업 고민의 명리적 진단</span>\n"
                        f"[※ AI 통변 지시: 신청자의 학업 고민({career_goal})에 대해 대운/세운 기운이 어떻게 작용하는지 직언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 최적의 전공 계열 및 문·이과 진로 적성</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 추천 계열 및 대학 전공 학과</span>\n"
                        f"[※ AI 통변 지시: 타고난 오행 물상에 완벽히 부합하는 최적의 전공 계열과 학과를 명시하여 추천하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 수시 vs 정시 유리성 판별</span>\n"
                        f"[※ AI 통변 지시: 수시(학생부)가 유리한지, 정시(수능)가 유리한지 명리적 근거를 들어 판별하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 시험운, 합격운 및 입시 성공의 변곡점</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 대운별 관성·인성운 발현 시기</span>\n"
                        f"[※ AI 통변 지시: 대운 중 어느 연도에 결정적인 시험 합격과 승리의 기운이 발현되는지 짚어내십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 시험운 극대화 골든타임</span>\n"
                        f"[※ AI 통변 지시: 시험운을 극대화하는 결정적 골든타임을 명확한 시기(연도/월)로 제시하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 학업 성취를 위한 개운 처세술</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"[※ AI 통변 지시: 집중력 극대화 풍수 팁과 멘탈 관리 전략을 제시하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>5. 고민 상담 Q&A</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 입시 고민 공감 및 원인 진단</span>\n"
                        f"[※ AI 통변 지시: 신청자의 진학 고민({career_goal})에 깊이 공감하고 불안한 마음을 다독이며, 성적 정체의 원인을 사주 기운으로 논리정연하게 짚어내십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 성적 도약 타이밍과 선택 기준</span>\n"
                        f"[※ AI 통변 지시: 슬럼프가 끝나고 성적이 도약할 시기와, 최종 합격을 위해 당장 집중해야 할 선택 기준을 명쾌하게 제시하십시오.]\n"
                        f"</div>\n"
                    )

                elif u_product == "2-4. 직업/경력운 특화 분석":
                    prompt = (
                        f"{공통_시스템_헤더}\n"
                        f"[SYSTEM ROLE: 초연시공명리 최고위 커리어 & 진로 전략가]\n"
                        f"귀하는 초연시공명리학의 원리와 시공간 파동을 완벽히 통달한 대명리학자이다.\n"
                        f"격국과 용신, 관성(조직)과 식재(독립/사업)의 결합 구조, 시간방향(時間方向)의 순류/역류 파동을 결합하여 \n"
                        f"조직형 vs 사업형 성향을 명확히 판별하고 최상의 사회적 성취를 위한 직업적 승부처를 정밀 통변할 것.\n\n"
                        f"🚨 [직업/커리어 특화 상담 절대 지시]\n"
                        f"■ 오직 신청자의 커리어/진로 고민({career_goal})을 중심 축으로 삼아, 직업적성 그릇, 조직 내 위상, 대운/세운별 승진·이직 발현 시기에 집중할 것.\n"
                        f"■ '1. 타고난 직무 성향 및 고민 정밀 진단' 소제목 아래에 `[DAEWUN_TABLE_HERE]` 및 `[SEWUN_TABLE_HERE]` 마커를 출력할 것.\n\n"
                        f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                        f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                        f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                        f"3. 표(Table) 생성 절대 금지.\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 내 삶의 무대와 타고난 커리어 성향</h3>\n"
                        f"[DAEWUN_TABLE_HERE]\n"
                        f"[SEWUN_TABLE_HERE]\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 나의 직무 재능과 나만의 경쟁력</span>\n"
                        f"[※ AI 통변 지시: 격국({gyukgook_detail})과 십성을 바탕으로 타고난 재능, 장인정신, 리더십 성향을 정밀 분석하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 조직에 남을 것인가, 나만의 길을 갈 것인가</span>\n"
                        f"[※ AI 통변 지시: 관인상생(직장형)인지 식상생재(프리랜서형)인지 명확히 판별하고, 대운 기운의 순류/역류를 짚어내십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>3) 현재의 커리어운 흐름 진단</span>\n"
                        f"[※ AI 통변 지시: 신청자의 커리어 고민({career_goal})에 대해 사주 원국과 대운 기운이 어떻게 작용하는지 직언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 나를 성장시킬 최적의 직무와 환경</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 내 에너지가 가장 잘 발휘되는 산업과 직종</span>\n"
                        f"[※ AI 통변 지시: 사주 구조에 완벽히 부합하는 핵심 산업군, 전문 직종을 추천하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 가치를 인정받는 슬기로운 직장 처세술</span>\n"
                        f"[※ AI 통변 지시: 직장 내 상호작용 갈등 요인을 짚어내고 현명한 대인관계 처세술을 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 도약과 성취를 이루는 커리어 변곡점</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 승진과 이직을 위한 결정적 골든타임</span>\n"
                        f"[※ AI 통변 지시: 관운, 인성운 도래 시기나 부서 이동, 승진의 결정적 골든 타임을 제시하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 성공적인 커리어를 위한 개운법</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"[※ AI 통변 지시: 조직 내 가치를 극대화하기 위한 실전 개운 수칙을 조언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>5. 고민 상담 Q&A</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 커리어 고민 공감 및 원인 진단</span>\n"
                        f"[※ AI 통변 지시: 신청자의 이직/진로 고민({career_goal})에 뼈저리게 공감하고, 혼란의 원인을 명리적 충돌 기류로 짚어내십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 최적 이직/합격 타이밍과 선택 기준</span>\n"
                        f"[※ AI 통변 지시: 이직이나 승진에 가장 유리한 시기와 현재 가져야 할 명확한 선택 기준을 솔루션으로 제공하십시오.]\n"
                        f"</div>\n"
                    )

                elif u_product == "2-5. 건강운 특화 분석":
                    prompt = (
                        f"{공통_시스템_헤더}\n"
                        f"[SYSTEM ROLE: 초연시공명리 최고위 명리 의학 & 헬스 케어 전문가]\n"
                        f"귀하는 초연시공명리학의 원리와 시공간 파동을 완벽히 통달한 대명리학자이다.\n"
                        f"신청자의 사주 원국 오행 태과/불급, 조후 불균형, 오행 손상 및 충극 파동을 바탕으로 기혈의 막힘과 장부 허실을 정밀 분석할 것.\n\n"
                        f"🚨 [건강 특화 상담 절대 지시]\n"
                        f"■ 오직 신청자의 특정 건강 고민({health_goal})과 오행 편중에 통변의 90% 이상을 집중할 것.\n"
                        f"■ 성별({u_gender})에 어긋나는 생리적 오류를 원천 차단한다.\n"
                        f"■ '1. 선천적 체질 및 고민 정밀 진단' 소제목 아래에 `[DAEWUN_TABLE_HERE]` 및 `[SEWUN_TABLE_HERE]` 마커를 출력할 것.\n\n"
                        f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                        f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                        f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                        f"3. 표(Table) 생성 절대 금지.\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 선천적 체질 및 고민({health_goal}) 정밀 진단</h3>\n"
                        f"[DAEWUN_TABLE_HERE]\n"
                        f"[SEWUN_TABLE_HERE]\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 선천적 기질과 체력 분석</span>\n"
                        f"[※ AI 통변 지시: 원국 오행 분포와 불균형 상태를 관찰하여 타고난 신체적 강약점과 취약 장기를 짚어주십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 앞으로의 10년, 그리고 올해의 건강 흐름</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 현재 대운에서 살필 신체 밸런스</span>\n"
                        f"[※ AI 통변 지시: 향후 10년간 기운의 쏠림 현상이 건강(혈관, 대사, 신경계 등)에 미칠 영향을 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 건강한 일상을 지키기 위한 리스크 관리</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 피로와 스트레스가 쌓이는 시기의 대처법</span>\n"
                        f"[※ AI 통변 지시: 만성 피로 및 정신적 스트레스 리스크를 분석하고 관리법을 다독여 주십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 내 몸을 살리는 다정한 섭생과 개운법</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"[※ AI 통변 지시: 부족한 기운을 채우기 위한 섭생 루틴, 음식, 운동법 등을 다정하게 조언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>5. 고민 상담 Q&A</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 건강 고민 공감 및 명리적 원인 진단</span>\n"
                        f"[※ AI 통변 지시: 신청자의 건강 고민({health_goal})에 진심 어린 공감을 표하고, 오행 불균형에서 어떻게 촉발되었는지 직언하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 일상 속 실천적 치유 가이드</span>\n"
                        f"[※ AI 통변 지시: 몸과 마음의 균형을 되찾고 호전될 시기를 짚어주며 구체적인 치유 가이드를 제시하십시오.]\n"
                        f"</div>\n"
                    )

                elif u_product == "2-6. 이사 택일":
                    prompt = (
                        f"{공통_시스템_헤더}\n"
                        f"[SYSTEM ROLE: 초연시공명리 최고위 공간 풍수 & 이사 택일 전략가]\n"
                        f"귀하는 초연시공명리학의 원리와 시공간 파동을 완벽히 통달한 대명리학자이다.\n"
                        f"신청자가 요청한 이사 목적에 맞추어, 지정된 예정 기간({s_d_val} ~ {e_d_val}) 내에서 사주 원국과 시간방향(時間方向)에 부합하는 공간 이동 파동을 결합하여 최상의 길일을 선별하고 정밀 통변할 것.\n\n"
                        f"🚨 [이사 택일 특화 상담 절대 지시]\n"
                        f"■ 가정궁의 안정, 평온한 시공간, 부부 및 가족 간의 화목에 집중할 것.\n"
                        f"■ '1. 새로운 공간으로의 이동이 갖는 의미' 소제목 아래에 `[DAEWUN_TABLE_HERE]` 및 `[SEWUN_TABLE_HERE]` 마커를 출력할 것.\n\n"
                        f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                        f"1. 난해한 용어 배제, 즉각적 행동 지침 위주.\n"
                        f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                        f"3. 표(Table) 생성 절대 금지.\n\n"
                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 새로운 공간으로의 이동이 갖는 의미</h3>\n"
                        f"[DAEWUN_TABLE_HERE]\n"
                        f"[SEWUN_TABLE_HERE]\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 이사가 나의 운명에 가져올 긍정적인 변화</span>\n"
                        f"[※ AI 통변 지시: 역마살, 지살 등 이동의 기운이 사주에 어떤 활력을 주는지 분석하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 복을 부르는 이사 당일의 지혜와 풍수</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 이사 당일 행운을 부르는 시간대(길시)</span>\n"
                        f"[※ AI 통변 지시: 흉시를 피하고 짐을 들이기 좋은 길시를 지정하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 새로운 집을 안락하게 채울 개운 풍수 팁</span>\n"
                        f"[※ AI 통변 지시: 용희신 방향이나 행운의 색상 등 수맥 차단, 안방 풍수를 조언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 이사 이후의 안락함과 실행 마인드셋</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"[※ AI 통변 지시: 새로운 터전에서 싹틀 가족의 안녕과 평안을 기원하는 따뜻한 메시지를 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 고민 상담 Q&A</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 이사 전 불안 공감 및 개운 이치</span>\n"
                        f"[※ AI 통변 지시: 이사를 앞두고 느끼는 현실적 고민에 깊이 공감하며, 이동이 나쁜 기운을 환기시키는 긍정적 액션임을 설명하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 화목을 위한 가족 실천 마인드</span>\n"
                        f"[※ AI 통변 지시: 이사 후 반드시 지켜야 할 가족 간의 배려 마인드를 조언하십시오.]\n"
                        f"</div>\n"
                    )

                elif u_product == "2-7. 개업 택일":
                    prompt = (
                        f"{공통_시스템_헤더}\n"
                        f"[SYSTEM ROLE: 초연시공명리 최고위 비즈니스 풍수 & 개업 택일 전략가]\n"
                        f"귀하는 초연시공명리학의 원리와 시공간 파동을 완벽히 통달한 대명리학자이다.\n"
                        f"신청자가 요청한 개업 목적에 맞추어, 지정된 예정 기간({s_d_val} ~ {e_d_val}) 내에서 사주 원국과 시간방향(時間方向)에 부합하는 재물 폭발 파동을 결합하여 최상의 길일을 선별하고 정밀 통변할 것.\n\n"
                        f"🚨 [개업 택일 특화 상담 절대 지시]\n"
                        f"■ 손님(식상)의 유입, 재물(현금 흐름)의 폭발, 사업장 확장 파동에 집중할 것.\n"
                        f"■ '1. 새로운 도약과 사업 시작의 타이밍' 소제목 아래에 `[DAEWUN_TABLE_HERE]` 및 `[SEWUN_TABLE_HERE]` 마커를 출력할 것.\n\n"
                        f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                        f"1. 난해한 용어 배제, 즉각적 행동 지침 위주.\n"
                        f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                        f"3. 표(Table) 생성 절대 금지.\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 새로운 도약과 사업 시작의 타이밍</h3>\n"
                        f"[DAEWUN_TABLE_HERE]\n"
                        f"[SEWUN_TABLE_HERE]\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 개업이 내 운명에 불어넣을 새로운 성장의 기운</span>\n"
                        f"[※ AI 통변 지시: 사주의 식상생재 기운을 바탕으로 사업 개창의 운기가 발동함을 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 대박을 터뜨릴 오픈 당일의 지혜와 비즈니스 풍수</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 손님을 끌어모을 개업 당일의 최적 시간대(길시)</span>\n"
                        f"[※ AI 통변 지시: 오픈 및 고사를 지내기 좋은 길시를 지정하십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 재물을 당기는 사업장 풍수와 인테리어 팁</span>\n"
                        f"[※ AI 통변 지시: 카운터 배치 등 재물을 끌어당기는 비즈니스 풍수 비법을 조언하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 개업 이후의 도약과 실행 마인드셋</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"[※ AI 통변 지시: 새로운 사업장에서 겪게 될 번창과 이를 담아낼 사업가의 배포를 응원하는 강력한 메시지를 서술하십시오.]\n"
                        f"</div>\n\n"

                        f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 고민 상담 Q&A</h3>\n"
                        f"<div class='content-box-loose'>\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 개업 전 중압감 공감과 명리적 타이밍</span>\n"
                        f"[※ AI 통변 지시: 사업 시작 전 느끼는 책임감에 공감하며 안심시켜 주고, 이번 개업이 사주상 식상생재의 확실한 타이밍임을 짚어주십시오.]\n"
                        f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 대박을 위한 실전 사업가 마인드</span>\n"
                        f"[※ AI 통변 지시: 완벽한 길일이 선사할 재물 파동을 믿고 돌격할 수 있도록 실전 사업가 마인드를 조언하십시오.]\n"
                        f"</div>\n"
                    ) # 👈 2-7 개업 택일 프롬프트가 끝나는 괄호
                    
                    try:
                        # 1. AI API 호출 및 기본 텍스트 파싱
                        res = model.generate_content(prompt)
                        ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                        ai_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', ai_text)
                    
                        # 2. 표 HTML 정리
                        un_html_clean = un_html.replace("\n", " ").replace("\r", "")
                        se_html_clean = se_html.replace("\n", " ").replace("\r", "")
                    
                        daeoun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{un_html_clean}</div>"
                        sewun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{se_html_clean}</div>"
                    
                        # 3. AI 텍스트 내 마커 정리
                        # 🚨 대운표는 상단에 강제 고정되므로 AI 텍스트 안에서는 무조건 삭제! 세운표만 본문 치환!
                        clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*DAEWUN_TABLE_HERE\s*\][\#\*\_\s]*', '', ai_text, flags=re.IGNORECASE)
                        clean_ai_text, count_s = re.subn(r'[\#\*\_\s]*\[\s*SEWUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                    
                        # 4. 택일 상품(2-6, 2-7) 전용 추천 길일 생성 로직
                        extra_html = ""
                        if u_product in ["2-6. 이사 택일", "2-7. 개업 택일"]:
                            FORBIDDEN_LIST = ['병오', '임자', '계해', '신유', '경신']
                            recommended_days = get_optimized_delivery_days(s_d_val, e_d_val, jjis, jjis, FORBIDDEN_LIST)
                        
                            extra_html += f"<h3 style='color:#000000; text-align:center; margin-top:20px;'>📅 추천 길일 (탐색기간: {s_d_val} ~ {e_d_val})</h3>\n"
                            for day_info in recommended_days:
                                extra_html += f"<div style='font-size:16px; font-weight:bold; margin-bottom:8px; padding:8px; background:#F8F9FA; border-radius:6px; text-align:center; color:#000000;'>✅ 추천 길일: <b style='color:#000000;'>{day_info['date']}</b> (명리 적합도: {day_info['score']}점)</div>\n"
                            extra_html += "<hr style='border:1px solid #000000; margin:15px 0;'>\n"

                        # 5. 🚨 [최종 조립] 원국표 -> 대운표 -> 택일(있다면) -> AI통변 -> 맺음말
                        bordered_closing_html = f"<hr style='border: 0; border-top: 2px dashed #000000; margin: 35px 0 20px 0;'>{closing_html}"
                    
                        full_content_clean = (
                            f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000;'>"
                            f"{daeoun_target}\n"        # 원국표 바로 아래에 대운표 고정
                            f"{extra_html}"             # 택일 상품일 경우 추천 길일 표기
                            f"{clean_ai_text}\n<br><br>"# AI 맞춤형 에세이 (세운표 포함)
                            f"{bordered_closing_html}"  # 맺음말
                            f"</div>"
                        )

                        # 6. 표지 타이틀 교체 및 여백 강제 축소
                        dynamic_title = u_product.split('. ')[-1] if '. ' in u_product else u_product
                    
                        report_1_full_html = re.sub(r'(<h1[^>]*>).*?(<\/h1>)', r'\g<1>' + dynamic_title + r'\2', report_1_full_html, count=1, flags=re.IGNORECASE|re.DOTALL)
                        report_1_full_html = re.sub(r'min-height:\s*250mm\s*;?', 'min-height: 120mm;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'padding:\s*40px\s+0\s*;?', 'padding: 10px 0;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'padding:\s*42px\s+24px\s*;?', 'padding: 20px 24px;', report_1_full_html, flags=re.IGNORECASE)
                        report_1_full_html = re.sub(r'margin-bottom:\s*28px\s*;?', 'margin-bottom: 15px;', report_1_full_html, flags=re.IGNORECASE)

                        # 7. 최종 렌더링 세팅
                        report_1_full_html = report_1_full_html.replace("{full_content_clean_placeholder}", full_content_clean)
                    
                        st.session_state['saved_report_html'] = report_1_full_html
                    
                    except Exception as e: 
                        st.error(f"테마별 특성화 분석 AI 연산 오류: {e}")

            # ==============================================================
            # [A-3] 4-1. 타 감명서 비교 (사주) 파이프라인
            # ==============================================================
            elif main_category == "4. 타 감명서 비교" and u_product == "4-1. 타 감명서 비교 (사주)":
                comp_prompt = (
                    f"{db_header}\n"
                    f"{ilju_master_prompt_context}\n\n"
                    f"[SYSTEM ROLE: 초연시공명리 최고위 학술 대조 판정관 & 수석보좌관]\n"
                    f"귀하는 제출된 [타 감명서 원문 텍스트]에서 다룬 핵심 주제와 인생의 쟁점을 분석 기준으로 삼아, \n"
                    f"신청자({disp_name})의 사주 팩트 데이터에 기반한 [초연 시공명리 정답 풀이]를 먼저 완벽히 전개한 후, \n"
                    f"타 감명서와 1:1로 정밀하게 비교 검증하여 시공명리학적 우수성을 입증하는 수석보좌관 AI이다.\n\n"
                    f"📜 [제출된 타 감명서 원문 텍스트]:\n"
                    f"{other_reading_text}\n\n"
                    f"🚫 [표 치환 태그 출력 절대 금지]\n"
                    f"■ 본문 통변 작성 시 `[SEWUN_TABLE_HERE]`, `[WOLUN_TABLE_HERE]`, `[WEEKLY_CALENDAR_HERE]`, `[DAEWUN_TABLE_HERE]`, `[COUPLE_DAEWUN_TABLES_HERE]` 등의 \n"
                    f"시스템 표 치환 태그 문자열을 직접 작성하거나 출력하는 것을 절대 금지한다.\n"
                    f"■ 모든 운세와 시공간 파동 분석은 태그 문구가 아닌 명리적 서술 텍스트와 표준 위계 서식으로만 완결되게 서술할 것.\n\n"
                    f"🚨 [타 사주 감명서 vs 시공명리 사주 감명서 1:1 상세 분석 지시]\n"
                    f"■ **[타 감명서 원문 주제 기반 분석 우선 전개]**: 제출된 타 감명서 원문에서 언급된 주요 주제를 기준으로, \n"
                    f"1번 대목차에서 상기 제공된 {disp_name}님의 사주 팩트 데이터에 입각한 '초연 시공명리 사주풀이 및 운세분석'을 객관적으로 서술할 것.\n"
                    f"■ **[타 감명서 vs 초연 시공명리 1:1 정밀 학술 대조]**: 2번 대목차에서는 타 감명서의 전통적 해석과 \n"
                    f"1번의 초연 시공명리 통변을 1:1로 직접 맞대조하여, 장단점 및 현실적 차이점을 편파 없이 비교 분석할 것.\n"
                    f"■ **[수석보좌관 총평 및 엔진 업데이트 제안]**: 3번 대목차에서는 1:1 정밀 대조를 통해 도출된 장단점을 평가하고, \n"
                    f"'초연시공명리 연산 알고리즘 및 통변 데이터베이스 고도화 업데이트 제안'을 수석보좌관 보고 형식으로 정밀 서술할 것.\n\n"
                    f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                    f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                    f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                    f"3. 표(Table) 생성 절대 금지.\n\n"
                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 초연 시공명리 사주풀이 및 운세분석</h3>\n"
                    f"<div class='content-box-loose'>\n"
                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 핵심 인생 주제별 시공명리 정밀 통변</span>\n"
                    f"[※ AI 통변 지시: 타 감명서가 다루고 있는 핵심 인생 주제를 중심으로, {disp_name}님의 사주 팩트를 바탕으로 초연 시공명리학의 정밀 통변을 전개하십시오.]\n"
                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 60월령 에너지와 대운 흐름 융합</span>\n"
                    f"[※ AI 통변 지시: 60월령 시공간의 계절적 에너지, 지장간의 상호작용 및 대운의 흐름을 융합하여 삶의 궤도를 입체적으로 풀어내십시오.]\n"
                    f"</div>\n\n"
                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 타 사주 감명서와 시공명리 감명서의 1:1 항목별 정밀 대조 및 장단점 분석</h3>\n"
                    f"<div class='content-box-loose'>\n"
                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 핵심 쟁점별 1:1 맞대조 분석</span>\n"
                    f"[※ AI 통변 지시: 원본의 주장과 초연 시공명리 사주풀이 결과를 핵심 쟁점에 맞추어 반드시 (1), (2), (3) 기호를 사용한 단답형 소제목으로 먼저 작성한 후, 무조건 줄바꿈(Enter)을 하고 다음 줄에 1:1 직접 대조를 서술하십시오.]\n"
                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 전통명리의 한계와 시공명리의 정밀성 입증</span>\n"
                    f"[※ AI 통변 지시: 기존 전통명리 단식 판단의 한계를 짚어내고, 초연 시공명리 시공간 파동 해석이 왜 실제 현실과 일치하는지 이치를 입증하십시오.]\n"
                    f"</div>\n\n"
                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 총괄: 수석보좌관 시공명리 학술 승화 및 엔진 업데이트 제안</h3>\n"
                    f"<div class='content-box-loose'>\n"
                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 1:1 대조 총괄 평가 및 유효 통찰 수용</span>\n"
                    f"[※ AI 통변 지시: 핵심 장단점을 종합 분석하고, 수용할 가치가 있는 학술적 요소를 (1) 기호를 사용한 소제목으로 작성 후 줄바꿈하여 명확히 정리하십시오.]\n"
                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 연산 알고리즘 및 통변 DB 고도화 제안</span>\n"
                    f"[※ AI 통변 지시: 임상 팩트를 바탕으로 향후 어떻게 고도화할 것인지 수석보좌관의 고품격 학술 제안을 반드시 (1), (2) 기호를 사용한 소제목을 달고 줄바꿈하여 완결하십시오.]\n"
                    f"</div>\n"
                )
                try:
                    c_res = call_claude_api(comp_prompt, max_tokens=10000)
                    c_res = "\n".join([line.lstrip() for line in c_res.split("\n")])
                    
                    report_2_html = (
                        f"<div class='page-break-before'></div>\n"
                        f"<div class='report-page'>\n"
                        f"<div class='vip-inset-frame' style='border:2px solid #000000; padding:20px;'>\n"
                        f"<h1 style='text-align:center; color:#000000; font-size: 26px; font-weight: 900; border-bottom:2px solid #000000; padding-bottom:15px; margin-bottom:20px;'>⚖️ 타 감명서 학술 검증 및 1:1 대조 리포트</h1>\n"
                        f"<div style='margin-top:20px; font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 16px; line-height: 1.85; color: #000000;'>{c_res}</div>\n"
                        f"<hr style='border:1px solid #000000; margin:30px 0;'>\n"
                        f"<h3 style='color:#000000; font-size:18px; font-weight:900; margin-bottom:10px;'>📜 [제출된 타 감명서 원문]</h3>\n"
                        f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 14px; line-height: 1.85; color: #000000; background:#FAFAFA; padding:15px; border-radius:8px;'>{other_reading_text.replace(chr(10), '<br>')}</div>\n"
                        f"</div>\n"
                        f"</div>"
                    )
                    st.session_state['saved_report_2'] = report_2_html
                except Exception as e:
                    st.error(f"비교 분석 가동 장애: {e}")

            # ==============================================================
            # [C] 2인 명조 파이프라인 (궁합 3-1, 택일 3-2/3-3, 타감명서 궁합 4-2)
            # ==============================================================
            elif is_2person_product:
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
                    st.session_state['partner_bazi'] = partner_bazi

                    # 🚨 [원천 수술 포인트] 신청인/상대방의 이름, 성별, 혼인여부 절대 방어막 세팅!
                    _u_name = st.session_state.get('u_n', '신청인')
                    _p_name = st.session_state.get('p_n', '상대방')
                    _u_gen  = st.session_state.get('u_g', '남성')
                    _p_gen  = "여성" if _u_gen == "남성" else "남성"  # 🚨 상대방 성별마저 강제 고정하여 에러 원천 차단!
                    _u_mar  = st.session_state.get('u_m_stat', '미혼')
                    _p_mar  = st.session_state.get('p_m_stat', '미혼')

                    if _u_gen == "남성":
                        m_name, m_sol, m_lun, m_time, m_age = _u_name, sol_str, lun_str, time_str, u_age
                        m_gans, m_jjis = gans, jjis
                        m_ys, m_yb, m_ms, m_mb, m_ds, m_db, m_hs, m_hb = ys, yb, ms, mb, ds, db, hs, hb
                        m_calc_d, m_order = calc_d, order
                        m_marital = _u_mar  # 남명이 신청인이므로 신청인 혼인여부 할당
                        
                        f_name, f_sol, f_lun, f_time, f_age = _p_name, p_sol_str, p_lun_str, f" {p_t.split('(')[0].strip()} ({p_hb})시" if p_t != "시간 모름" else "", p_age
                        f_gans, f_jjis = [p_hs, p_ds, p_ms, p_ys], [p_hb, p_db, p_mb, p_yb]
                        f_ys, f_yb, f_ms, f_mb, f_ds, f_db, f_hs, f_hb = p_ys, p_yb, p_ms, p_mb, p_ds, p_db, p_hs, p_hb
                        p_utc_dt = p_base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=get_total_time_adjustment(p_base_dt))
                        p_order = 1 if (GAN.index(p_ys)%2==0) == (_p_gen=='남성') else -1  # 🚨 불안정한 p_gender 대신 안전한 _p_gen 사용!
                        f_calc_d, f_order = get_daeun_su_accurate(p_utc_dt, p_order), p_order
                        f_marital = _p_mar  # 여명이 상대방이므로 상대방 혼인여부 할당
                        
                        male_data_pack, female_data_pack = applicant_bazi, partner_bazi
                    else:
                        m_name, m_sol, m_lun, m_time, m_age = _p_name, p_sol_str, p_lun_str, f" {p_t.split('(')[0].strip()} ({p_hb})시" if p_t != "시간 모름" else "", p_age
                        m_gans, m_jjis = [p_hs, p_ds, p_ms, p_ys], [p_hb, p_db, p_mb, p_yb]
                        m_ys, m_yb, m_ms, m_mb, m_ds, m_db, m_hs, m_hb = p_ys, p_yb, p_ms, p_mb, p_ds, p_db, p_hs, p_hb
                        p_utc_dt = p_base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=get_total_time_adjustment(p_base_dt))
                        p_order = 1 if (GAN.index(p_ys)%2==0) == (_p_gen=='남성') else -1  # 🚨 불안정한 p_gender 대신 안전한 _p_gen 사용!
                        m_calc_d, m_order = get_daeun_su_accurate(p_utc_dt, p_order), p_order
                        m_marital = _p_mar  # 남명이 상대방이므로 상대방 혼인여부 할당
                        
                        f_name, f_sol, f_lun, f_time, f_age = _u_name, sol_str, lun_str, time_str, u_age
                        f_gans, f_jjis = gans, jjis
                        f_ys, f_yb, f_ms, f_mb, f_ds, f_db, f_hs, f_hb = ys, yb, ms, mb, ds, db, hs, hb
                        f_calc_d, f_order = calc_d, order
                        f_marital = _u_mar  # 여명이 신청인이므로 신청인 혼인여부 할당
                        
                        male_data_pack, female_data_pack = partner_bazi, applicant_bazi

                    if u_product == "4-2. 타 감명서 비교 (궁합)":
                        # 🚨 [수술 1] 증발 위험이 있는 옛날 변수 대신, 최상단에서 완벽히 세팅된 m_name과 f_name으로 직행 연결!
                        m_name_val = m_name
                        f_name_val = f_name
                        
                        gh_engine = UniversalPrintableGunghap(m_name_val, f_name_val, male_data_pack, female_data_pack, 10)
                        gh_engine.run_universal_logic()

                        comp_prompt = (
                            f"{db_header}\n"
                            f"{ilju_master_prompt_context}\n\n"
                            f"[SYSTEM ROLE: 초연시공명리 최고위 궁합 학술 대조 판정관 & 수석보좌관]\n"
                            f"귀하는 제출된 [타 궁합 감명서 원문 텍스트]에서 다룬 궁합의 핵심 쟁점을 분석 기준으로 삼아, \n"
                            f"두 사람의 사주 팩트 데이터에 기반한 [초연 시공명리 정답 궁합 및 운세분석]을 먼저 완벽히 전개한 후, \n"
                            f"타 감명서와 1:1로 정밀하게 비교 검증하여 시공명리학적 우수성을 입증하는 수석보좌관 AI이다.\n\n"
                            f"📜 [제출된 타 감명서 원문 텍스트]:\n"
                            f"{other_reading_text}\n\n"
                            f"🚫 [표 치환 태그 출력 절대 금지]\n"
                            f"■ 본문 통변 작성 시 `[SEWUN_TABLE_HERE]`, `[WOLUN_TABLE_HERE]`, `[WEEKLY_CALENDAR_HERE]`, `[DAEWUN_TABLE_HERE]`, `[COUPLE_DAEWUN_TABLES_HERE]` 등의 \n"
                            f"시스템 표 치환 태그 문자열을 직접 작성하거나 출력하는 것을 절대 금지한다.\n"
                            f"■ 모든 운세와 시공간 파동 분석은 태그 문구가 아닌 명리적 서술 텍스트와 표준 위계 서식으로만 완결되게 서술할 것.\n\n"
                            f"🚨 [타 궁합 감명서 vs 시공명리 궁합 감명서 1:1 상세 분석 지시]\n"
                            f"■ **[타 궁합 감명서 쟁점 기반 분석 우선 전개]**: 제출된 타 감명서 핵심 쟁점을 기준으로, 1번 대목차에서 남명과 여명의 팩트에 입각한 궤도 결합 통변을 서술할 것.\n"
                            f"■ **[전통 궁합 vs 초연 시공명리 궤도 분석 1:1 대조]**: 2번 대목차에서는 1:1로 직접 맞대조하여 장단점 및 명리적 차이를 균형 있게 비교 분석할 것.\n"
                            f"■ **[총괄: 수석보좌관 궁합 학술 총평 및 엔진 업데이트 제안]**: 3번 대목차에서는 '초연시공명리 궁합 연산 알고리즘 고도화 업데이트 제안'을 서술할 것.\n\n"
                            f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                            f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                            f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                            f"3. 표(Table) 생성 절대 금지.\n\n"
                            f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 초연 시공명리 궁합 및 운세분석</h3>\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 핵심 궁합 쟁점별 시공명리 정밀 통변</span>\n"
                            f"[※ AI 통변 지시: 타 궁합 감명서가 다루고 있는 핵심 궁합 주제를 중심으로 초연 시공명리학의 정밀 궁합 통변을 전개하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 60월령 에너지와 대운 궤도 결합 분석</span>\n"
                            f"[※ AI 통변 지시: 60월령 시공간 에너지, 일지 지장간, 대운 궤도의 흐름이 서로 어떻게 얽히고 맞물리는지 입체적으로 풀어내십시오.]\n"
                            f"</div>\n\n"
                            f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 타 궁합 감명서와 시공명리 궁합 감명서의 1:1 정밀 대조 및 장단점 분석</h3>\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 핵심 쟁점별 1:1 맞대조 분석</span>\n"
                            f"[※ AI 통변 지시: 원본의 주장과 위 결과를 주요 항목별로 반드시 (1), (2), (3) 기호를 사용한 단답형 소제목으로 먼저 작성한 후, 무조건 줄바꿈(Enter)을 하고 다음 줄에 1:1 직접 대조하여 서술하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 전통 궁합의 한계와 시공명리 우수성 입증</span>\n"
                            f"[※ AI 통변 지시: 전통 궁합 단식 판단의 한계를 짚어내고, 초연 시공명리 상보성 연산이 왜 부부 인연을 정확히 관통하는지 명리적 이치로 입증하십시오.]\n"
                            f"</div>\n\n"
                            f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 총괄: 수석보좌관 시공명리 학술 승화 및 엔진 업데이트 제안</h3>\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 1:1 대조 총괄 평가 및 유효 통찰 수용</span>\n"
                            f"[※ AI 통변 지시: 도출된 핵심 장단점을 종합 분석하고, 수용할 가치가 있는 학술적 요소를 반드시 (1) 기호를 사용한 소제목으로 작성 후 줄바꿈하여 명확히 정리하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 궁합 연산 알고리즘 및 통변 DB 고도화 제안</span>\n"
                            f"[※ AI 통변 지시: 임상 팩트를 바탕으로 향후 업데이트 제안을 반드시 (1), (2) 기호를 사용한 소제목을 달고 줄바꿈하여 완결하십시오.]\n"
                            f"</div>\n"
                        )
                        c_res = call_claude_api(comp_prompt, max_tokens=10000)
                        c_res = "\n".join([line.lstrip() for line in c_res.split("\n")])
                        
                        report_2_html = (
                            f"<div class='page-break-before'></div>\n"
                            f"<div class='report-page'>\n"
                            f"<div class='vip-inset-frame' style='border:2px solid #000000; padding:20px;'>\n"
                            f"<h1 style='text-align:center; color:#000000; font-size: 26px; font-weight: 900; border-bottom:2px solid #000000; padding-bottom:15px; margin-bottom:20px;'>⚖️ 타 궁합 감명서 학술 검증 및 1:1 대조 리포트</h1>\n"
                            f"<div style='margin-top:20px; font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 16px; line-height: 1.85; color: #000000;'>{c_res}</div>\n"
                            f"<hr style='border:1px solid #000000; margin:30px 0;'>\n"
                            f"<h3 style='color:#000000; font-size:18px; font-weight:900; margin-bottom:10px;'>📜 [제출된 타 감명서 원문]</h3>\n"
                            f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 14px; line-height: 1.85; color: #000000; background:#FAFAFA; padding:15px; border-radius:8px;'>{other_reading_text.replace(chr(10), '<br>')}</div>\n"
                            f"</div>\n"
                            f"</div>"
                        )
                        st.session_state['saved_report_2'] = report_2_html

                    else:
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

                            info_str = f"<div style='text-align:center; margin-bottom:15px; font-family:\"Malgun Gothic\", sans-serif;'><span style='font-size:18px; font-weight:900; color:{color};'>{gender_icon} {name}님 ({gender_str}, {marital_str}, {age}세)</span><br><span style='font-size:14px; font-weight:900; color:#000000;'>[양력] {sol} | [음력] {lun}{time}</span></div>"
                            
                            def td(c): return f"<td class='color-{get_color(c)}' style='font-size:20px; font-weight:900; border:1px solid #444 !important;'><span style='color:inherit !important;'>{('?' if c in ['?',' ','-'] else c)}</span></td>"
                            
                            gen_shinsal_cells = ""
                            gender_param = gender_str.replace("명", "성")
                            for i in range(4):
                                shinsals = get_general_shinsal_filtered(i, t_gans, t_jjis, gender_param)
                                shinsal_text = "<br>".join(shinsals) if shinsals else "-"
                                gen_shinsal_cells += f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'><span style='color:inherit !important;'>{shinsal_text}</span></td>"
                            
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
                                f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:inherit !important;'>년지 12신살</span></td>{''.join([f'<td style=\"border:1px solid #444; color:#C62828; font-weight:bold;\"><span style=\"color:inherit !important;\">{get_12_shinsal(t_yb, t_jjis[i])}</span></td>' for i in range(4)])}</tr>\n"
                                f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:inherit !important;'>일지 12신살</span></td>{''.join([f'<td style=\"border:1px solid #444; color:#1565C0; font-weight:bold;\"><span style=\"color:inherit !important;\">{get_12_shinsal(t_jjis[1], t_jjis[i])}</span></td>' for i in range(4)])}</tr>\n"
                                f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'><span style='color:inherit !important;'>일반신살</span></td>{gen_shinsal_cells}</tr>\n"
                                f"</table>\n"
                                f"<div style='border:2px solid {color}; margin-top:10px; margin-bottom:20px; padding:6px 8px; display:flex; justify-content:space-between; align-items:center; font-weight:900; font-size:11px; letter-spacing:-0.5px; border-radius:8px; background-color:#FAFAFA;'><div style='white-space:nowrap; color:#000000;'>🔢 대운수: {daeun_su}</div><div style='white-space:nowrap; color:#000000;'>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div style='white-space:nowrap; color:#000000;'>🌟 천을귀인: <span style='color:#000000;'>{guiin}</span></div><div style='white-space:nowrap; color:#000000;'>🎯 공망: [년] <span style='color:#C62828;'>{y_gong}</span> [일] <span style='color:#C62828;'>{d_gong}</span></div><div style='white-space:nowrap; color:#000000;'>🌪️ 삼재: {samjae}</div></div>"
                            )

                        # 🚨 [수술 2] 중복 코드 청소: 최상단에서 이미 완벽하게 세팅했으므로 중복 선언된 변수들을 깔끔하게 삭제합니다!
                        guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 해','辛':'午寅','壬':'卯巳','癸':'卯, 巳'}
                        
                        m_tbl = build_bazi_table("♂️", m_name, "남명", m_marital, m_age, m_sol, m_lun, m_time, m_gans, m_jjis, m_ds, m_yb, m_cnt, guiin_map.get(m_ds, '-'), calculate_gongmang(m_ys, m_yb), calculate_gongmang(m_ds, m_db), get_samjae(m_yb, curr_j), m_calc_d, "#000000")
                        f_tbl = build_bazi_table("♀️", f_name, "여명", f_marital, f_age, f_sol, f_lun, f_time, f_gans, f_jjis, f_ds, f_yb, f_cnt, guiin_map.get(f_ds, '-'), calculate_gongmang(f_ys, f_yb), calculate_gongmang(f_ds, f_db), get_samjae(f_yb, curr_j), f_calc_d, "#000000")
                        
                        def build_daewun_html(name, t_ds, t_ms, t_mb, t_yb, t_calc_d, t_order, age, color):
                            d_str = "순행" if t_order == 1 else "역행"
                            html = f"<div style='margin-bottom:10px;'><div style='font-size:15px; font-weight:900; color:#000000; margin-bottom:5px;'>[ {name}님 대운 흐름표 (대운수: {t_calc_d}), {d_str} ]</div>"
                            html += f"<div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #000000; background:white;'>"
                            for i in range(10):
                                val = i*10 + t_calc_d
                                tc = GAN[(GAN.index(t_ms)+(i+1)*t_order)%10]
                                tj = JI[(JI.index(t_mb)+(i+1)*t_order)%12]
                                bg = "#FFF9C4" if val <= age < val+10 else "transparent"
                                brd = "1px solid #ccc" if i != 9 else "none"
                                html += f"<div style='flex:1; border-left:{brd}; text-align:center; padding-bottom:3px; background-color:{bg};'><div style='background-color:#222222; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:11px; border-bottom:1px solid #ccc;'>{val}세</div><div style='padding:2px; font-size:11px; color:#000000;'>{get_ss(t_ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:15px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:15px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:11px; color:#000000;'>{get_ss(t_ds,tj)}</div><div style='font-size:10px; border-top:1px solid #eee; color:#0D47A1;'>{get_unsung(t_ds,tj)}</div><div style='font-size:10px; color:#C62828; border-top:1px solid #eee;'>{get_12_shinsal(t_yb, tj)}</div></div>"
                            return html + "</div></div>"

                        m_page_un_html = build_daewun_html(m_name, m_ds, m_ms, m_mb, m_yb, m_calc_d, m_order, m_age, "#000000")
                        f_page_un_html = build_daewun_html(f_name, f_ds, f_ms, f_mb, f_yb, f_calc_d, f_order, f_age, "#000000")
                        
                        couple_daewun_tables = f"<div style='margin-bottom: 25px;'>{m_page_un_html}<div style='height:20px;'></div>{f_page_un_html}</div>"

                        ilju_struct_db = choyeon_db.get("ilju_structure", {})

                        m_ilju_key = f"{m_ds}{m_db}"
                        m_struct_data = ilju_struct_db.get(m_ilju_key, [])
                        m_action_type = m_struct_data[1] if len(m_struct_data) >= 3 else "자율활동형"
                        m_main_tendency = m_struct_data[2] if len(m_struct_data) >= 3 else "독자적인 삶의 무대를 개척하는"
                        m_gy_name, m_gy_desc = get_gyukgook_detailed(m_ds, m_ys, m_ms, m_hs, m_mb)

                        m_traditional_text_html = (
                            f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 16px; line-height: 1.85; color: #000000; margin-bottom: 20px;'>\n"
                            f"    <p style='text-indent: 15px; margin-bottom: 5px;'>\n"
                            f"        정통 명리학적으로 풀이하면 <b style='color:#000000;'>{m_name}님</b>은 <b style='color:#000000;'>{m_mb}월</b>에 <b style='color:#000000;'>'{m_gy_name}'</b>의 그릇을 갖추고 태어나셨으며, 성격은 <b style='color:#000000;'>'{m_action_type}'</b>으로 <b style='color:#000000;'>'{m_main_tendency}'</b> 성향이 있습니다.\n"
                            f"    </p>\n"
                            f"</div>\n"
                            f"<hr style='border: 0; border-top: 2px solid #000000; margin: 25px 0;'>\n"
                        )

                        f_ilju_key = f"{f_ds}{f_db}"
                        f_struct_data = ilju_struct_db.get(f_ilju_key, [])
                        f_action_type = f_struct_data[1] if len(f_struct_data) >= 3 else "자율활동형"
                        f_main_tendency = f_struct_data[2] if len(f_struct_data) >= 3 else "독자적인 삶의 무대를 개척하는"
                        f_gy_name, f_gy_desc = get_gyukgook_detailed(f_ds, f_ys, f_ms, f_hs, f_mb)

                        f_traditional_text_html = (
                            f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 16px; line-height: 1.85; color: #000000; margin-bottom: 20px;'>\n"
                            f"    <p style='text-indent: 15px; margin-bottom: 5px;'>\n"
                            f"        정통 명리학적으로 풀이하면 <b style='color:#000000;'>{f_name}님</b>은 <b style='color:#000000;'>{f_mb}월</b>에 <b style='color:#000000;'>'{f_gy_name}'</b>의 그릇을 갖추고 태어나셨으며, 성격은 <b style='color:#000000;'>'{f_action_type}'</b>으로 <b style='color:#000000;'>'{f_main_tendency}'</b> 성향이 있습니다.\n"
                            f"    </p>\n"
                            f"</div>\n"
                            f"<hr style='border: 0; border-top: 2px solid #000000; margin: 25px 0;'>\n"
                        )

                        gh_engine = UniversalPrintableGunghap(u_name, p_name, male_data_pack, female_data_pack, 10)
                        gh_engine.run_universal_logic()
                        
                        essay_prompt = (
                            f"{db_header}\n"
                            f"[SYSTEM ROLE: 초연시공명리 최고위 커플 궁합 & 부부 심리 컨설턴트]\n"
                            f"제공된 남명과 여명의 사주 원국 및 시공간 팩트 데이터를 바탕으로, \n"
                            f"두 사람의 음양오행적 조화, 육친적 인연의 깊이, 심리적 기류, 대운 궤도의 교차 동조성 및 시간방향(時間方向) 상호보완성을 엄정하고 입체적으로 통변할 것.\n\n"
                            f"🚨 [절대 강제: 3분할 파싱 태그 서식 엄수]\n"
                            f"■ 시스템이 남명 풀이, 여명 풀이, 종합 궁합 풀이를 개별 페이지로 분리하여 렌더링할 수 있도록 반드시 아래 태그 구조를 정확히 사용하여 작성할 것.\n"
                            f"■ [목차 임의 변경 절대 금지]: [MALE_START]~[MALE_END], [FEMALE_START]~[FEMALE_END] 구간 안에서는 \n"
                            f"반드시 아래 지정된 '1. 성격 및 가치관 / 2. 사주팔자의 요약' 목차와 그 하위 소제목만 사용할 것.\n"
                            f"이 구간 안에서 다른 개인 사주 상품(1-1 등)에서 쓰는 것과 같은 별도의 대제목(예: 'OO일주의 진정한 초상', '육친관계' 등)을 새로 만들어내거나, 목차를 늘리는 것을 절대 금지한다.\n\n"
                            f"[ 🚨문단 레이아웃 및 AI 환각 통제 명령 ]\n"
                            f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                            f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                            f"3. 표(Table) 생성 절대 금지.\n\n"
                            f"[MALE_START]\n"

                            f"<h3 style='color:#000000; font-size: 24px; font-weight: 900; margin-top: 15px;'>1. 성격 및 가치관</h3>\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #000000; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>\n"
                            f"[※ AI 통변 지시: 남명({m_name})의 타고난 일주/월령 기반 표면 성격을 분석한 에세이를 작성하십시오.]\n"
                            f"<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #000000; margin-top: 15px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>\n"
                            f"[※ AI 통변 지시: 남명의 내면 가치관, 무의식적 심리 패턴을 서술하십시오.]\n"
                            f"<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #000000; margin-top: 15px; margin-bottom: 5px;'>3) 무의식이 갈망하는 반려자의 상</span>\n"
                            f"[※ AI 통변 지시: 남성의 연애 및 결혼관을 에세이로 작성하십시오.]\n"
                            f"</div>\n\n"

                            f"<h3 style='color:#000000; font-size: 24px; font-weight: 900; margin-top: 15px;'>2. 사주팔자의 요약</h3>\n"
                            f"{m_traditional_text_html}\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #000000; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>\n"
                            f"[※ AI 통변 지시: 남명의 정통 명리적 성향을 분석한 에세이를 작성하십시오.]\n"
                            f"<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #000000; margin-top: 15px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>\n"
                            f"[※ AI 통변 지시: 남명의 오행 및 조후 에너지를 분석한 에세이를 작성하십시오.]\n"
                            f"</div>\n"
                            f"[MALE_END]\n\n"
                            f"[FEMALE_START]\n"

                            f"<h3 style='color:#000000; font-size: 24px; font-weight: 900; margin-top: 15px;'>1. 성격 및 가치관</h3>\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #000000; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>\n"
                            f"[※ AI 통변 지시: 여명({f_name})의 타고난 일주/월령 기반 표면 성격을 분석한 에세이를 작성하십시오.]\n"
                            f"<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #000000; margin-top: 15px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>\n"
                            f"[※ AI 통변 지시: 여명의 내면 가치관, 무의식적 심리 패턴을 서술하십시오.]\n"
                            f"<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #000000; margin-top: 15px; margin-bottom: 5px;'>3) 무의식이 갈망하는 반려자의 상</span>\n"
                            f"[※ AI 통변 지시: 여명의 연애 및 결혼관을 에세이로 작성하십시오.]\n"
                            f"</div>\n\n"
                            f"<h3 style='color:#000000; font-size: 24px; font-weight: 900; margin-top: 15px;'>2. 사주팔자의 요약</h3>\n"
                            f"{f_traditional_text_html}\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #000000; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>\n"
                            f"[※ AI 통변 지시: 여성의 정통 명리적 성향을 분석한 에세이를 작성하십시오.]\n"
                            f"<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #000000; margin-top: 15px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>\n"
                            f"[※ AI 통변 지시: 여성의 오행 및 조후 에너지를 분석한 에세이를 작성하십시오.]\n"
                            f"</div>\n"
                            f"[FEMALE_END]\n\n"
                            f"[GUNGHAP_START]\n"

                            f"<h3 style='color: #000000; font-size: 24px; font-weight: 900; margin-top: 10px;'>1. 두 사람의 운명적 만남에 대하여</h3>\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 인연의 의미</span>\n"
                            f"[※ AI 통변 지시: 두 사람의 인연이 갖는 명리적 의미와 인연의 깊이를 서술하십시오.]\n"
                            f"</div>\n\n"

                            f"<h3 style='color: #000000; font-size: 24px; font-weight: 900; margin-top: 25px;'>2. 커플의 대운 비교 분석</h3>\n"
                            f"[COUPLE_DAEWUN_TABLES_HERE]\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 커플의 인생 주기의 상생조화</span>\n"
                            f"[※ AI 통변 지시: 상하 대운 교차점에 따른 상생과 보완점을 분석하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 커플의 인생 주기의 궤도 동조성</span>\n"
                            f"[※ AI 통변 지시: 각자의 원국 근기가 맞물려 일어나는 상호 공명하는 시공간 궤적을 서술하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>3) 커플이 겪게 될 가장 큰 변화의 순간</span>\n"
                            f"[※ AI 통변 지시: 일주 복음이나 대운 전환기에 발생하는 부부 관계의 결정적 분기점을 정밀 분석하십시오.]\n"
                            f"</div>\n\n"

                            f"<h3 style='color: #000000; font-size: 24px; font-weight: 900; margin-top: 25px;'>3. 커플의 최종 궁합 분석</h3>\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 배우자 인연 복합 파동 분석</span>\n"
                            f"[※ AI 통변 지시: 엔진 팩트를 결합하여 각자의 가주(家主) 기질, 합충형해파와 복음 등이 부부 관계에 미치는 영향을 심층 분석하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 사회적·가문적 무대</span>\n"
                            f"[※ AI 통변 지시: 연지(年支)와 월지(月支) 간의 상호작용을 통해 사회적 가치관과 집안 배경의 어우러짐을 분석하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>3) 내면의 유대감</span>\n"
                            f"[※ AI 통변 지시: 일지(日支) 간의 합과 충을 분석하여 무의식적 정서 밀착도를 규명하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>4) 환경 조화</span>\n"
                            f"[※ AI 통변 지시: 조후(한난조습)를 대조하여 서로가 처한 심리적 온도가 어떻게 어우러지는지 판별하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>5) 기운 상호보완</span>\n"
                            f"[※ AI 통변 지시: 한 사람에게 부족한 오행(십성)을 상대방이 어떻게 채워주는지 억부적 시너지를 설명하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>6) 특수 기운</span>\n"
                            f"[※ AI 통변 지시: 특수 신살(원진, 귀문, 천을귀인 등)의 파동을 긍정적 에너지로 승화시킬 비책을 제시하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>7) 리스크 방어력</span>\n"
                            f"[※ AI 통변 지시: 운세적 위기나 흉의를 상대방의 사주 기운이 어떻게 완충하고 막아주는지 조명하십시오.]\n"
                            f"</div>\n\n"

                            f"<h3 style='color: #000000; font-size: 24px; font-weight: 900; margin-top: 25px;'>4. 조율의 지혜</h3>\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 부 vs 내면평화 지수 분석</span>\n"
                            f"[※ AI 통변 지시: 두 사람의 성향을 바탕으로 내면평화 지수를 산출하여 서술하십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 4대 실전 처세와 백년해로 솔루션</span>\n"
                            f"[※ AI 통변 지시: 실전 처세 솔루션을 소제목으로 나열 후 백년해로 실전 가이드를 서술하십시오.]\n"
                            f"</div>\n\n"

                            f"<h3 style='color: #000000; font-size: 24px; font-weight: 900; margin-top: 25px;'>5. 고민 상담 Q&A</h3>\n"
                            f"<div class='content-box-loose'>\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 부부 갈등 공감 및 진짜 원인 규명</span>\n"
                            f"[※ AI 통변 지시: 신청자가 남긴 갈등 사연에 공감하고 명리적 원인을 짚어주십시오.]\n"
                            f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 화목한 결합을 위한 현실적 해법</span>\n"
                            f"[※ AI 통변 지시: 재물/자식 운의 흐름과 함께 현실적인 해법을 제시하십시오.]\n"
                            f"</div>\n"
                            f"[GUNGHAP_END]\n"
                        )

                        res_text = call_claude_api(essay_prompt, max_tokens=12000)
                        ai_clean = "\n".join([line.lstrip() for line in res_text.split("\n")])
                        
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
                        
                        g_ess, count = re.subn(r'\[\s*COUPLE_DAEWUN_TABLES_HERE\s*\]', couple_daewun_tables, g_ess, flags=re.IGNORECASE)
                        if count == 0:
                            g_ess = re.sub(r'(<h3[^>]*>🌈 커플의 인생 기상도 분석</h3>)', r'\1\n<div style="margin-top:15px;">' + couple_daewun_tables + '</div>', g_ess)

                        def wrap_a4(content, title_color="#000000", title="[ 초연 전통 명리사주 풀이 ]"):
                            return (
                                f"<div class='report-page'>\n"
                                f"<div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'>\n"
                                f"<h1 style='text-align:center; color:{title_color}; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; border-bottom:2px solid {title_color}; padding-bottom:15px; margin-bottom:30px;'>{title}</h1>\n"
                                f"{content}\n"
                                f"</div>\n"
                                f"</div>"
                            )

                        # 🚨 50.5 원본 복구: 점수에 따라 도넛 색상(하늘색/주황색/빨간색) 자동 변경
                        t_col = "#3498db" if gh_engine.final_score >= 70 else ("#f39c12" if gh_engine.final_score >= 60 else "#e74c3c")
                        
                        # 🚨 50.5 원본 복구: 6개 항목마다 각각 다른 예쁜 색상(d['color'])이 들어가도록 완벽 복구[cite: 2]
                        bars = "".join([f"<div style='display:flex; align-items:center; margin-bottom:12px;'><div style='width:130px; font-size:13px; font-weight:bold; color:#555;'>{d['label']}</div><div style='flex:1; height:12px; margin:0 10px;'><svg width='100%' height='12'><rect width='100%' height='12' rx='6' ry='6' fill='#eee' /><rect width='{d['pct']}%' height='12' rx='6' ry='6' fill='{d['color']}' /></svg></div><div style='width:35px; font-size:12px; font-weight:bold;'>{d['pct']}%</div></div>" for d in gh_engine.details])
                        
                        # 🚨 50.5 원본 복구: 맺음말 텍스트[cite: 2]
                        closing_original = (
                            f"<div style='margin-top: 40px; padding-top: 30px; page-break-inside: avoid;'>\n"
                            f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333;'>&nbsp;&nbsp;&nbsp;&nbsp;두 분의 <b style='color:#1A237E;'>'만남'</b>은 결코 우연이 아닌, <b style='color:#1A237E;'>'수많은 인연의 이치 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 명식이지만, <b style='color:#1A237E;'>'궁합(宮合)'</b>은 두 명식이 만나 그려내는 새로운 <b style='color:#1A237E;'>'조화와 상생'</b>입니다.</p>\n"
                            f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333; margin-top: 10px;'>&nbsp;&nbsp;&nbsp;&nbsp;서로의 기운을 보완하고 다독여주는 든든한 <b style='color:#1A237E;'>'반려자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 전통 명리의 축복이 가득하시길 소망합니다.</p>\n"
                            f"<div style='text-align: right; margin-top: 25px;'><span style='font-weight: 900; font-size: 16px; color: #1A237E; font-family: \"Nanum Myeongjo\", serif;'>- 초연 전통명리 연구소 드림 -</span></div>\n"
                            f"</div>"
                        )

                        # 🚨 50.5 원본 복구: VIP 프레임 밖으로 튀어나가지 않도록 원본 HTML 구조 그대로 복구[cite: 2]
                        # (단, AI 환각으로 인한 레이아웃 깨짐을 방지하기 위해 safe_g_ess 필터링만 추가로 씌웠습니다)
                        safe_g_ess = g_ess.replace("</div>\n</div>\n</div>", "</div>\n").replace("</div>\n</div>", "</div>\n")

                        g_full_content = (
                            f"<div class='choyeon-premium-report'>\n{safe_g_ess}\n</div>\n"
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

                        closing_original = (
                            f"<div style='margin-top: 40px; border-top: 2px solid #000000; padding-top: 25px; font-family: \"Nanum Myeongjo\", serif; page-break-inside: avoid;'>\n"
                            f"<p style='font-size: 15px !important; font-weight: 500 !important; text-indent: 14px; text-align: justify; line-height: 1.85; margin-bottom: 12px; color: #000000; word-break: keep-all;'>\n"
                            f"<b style=\"font-weight:900; color:#000000;\">{m_name}님</b>과 <b style=\"font-weight:900; color:#000000;\">{f_name}님</b>의 만남은 결코 우연이 아닌, <b style=\"font-weight:900; color:#000000;\">'수많은 인연의 이치 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 명식이지만, <b style=\"font-weight:900; color:#000000;\">'궁합(宮合)'</b>은 두 명식이 만나 그려내는 새로운 <b style=\"font-weight:900; color:#000000;\">'조화와 상생'</b>입니다.</p>\n"
                            f"<p style='font-size: 15px !important; font-weight: 500 !important; text-indent: 14px; text-align: justify; line-height: 1.85; margin-bottom: 12px; color: #000000; word-break: keep-all;'>서로의 기운을 보완하고 다독여주는 든든한 <b style=\"font-weight:900; color:#000000;\">'반려자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 초연 시공명리의 축복이 가득하시길 소망합니다.</p>\n"
                            f"<p style='font-size: 15px !important; font-weight: 900 !important; text-indent: 14px; line-height: 1.85; margin-bottom: 0px; color: #000000; word-break: keep-all;'>오늘 닿은 귀한 인연에 다시 한 번 깊이 감사드립니다.</p>\n"
                            f"<div style='text-align: right; margin-top: 30px; margin-bottom: 15px;'>\n"
                            f"<span style='font-weight: 900; font-size: 18px !important; color: #000000;'>- 초연 시공명리 연구소 드림 -</span>\n"
                            f"</div>\n"
                            f"</div>\n"
                        )

                        # 🚨 2. AI의 환각(여분의 </div>)으로 인해 VIP 프레임이 깨지는 현상 원천 차단
                        safe_g_ess = g_ess.replace("</div>\n</div>\n</div>", "</div>\n").replace("</div>\n</div>", "</div>\n")


                        # 🚨 1. 표지 강제 슬림화 및 타이틀을 선택상품명으로 동적 연계
                        dynamic_title = u_product.split('. ')[-1] if '. ' in u_product else u_product
                        
                        # 🚨 [수술 포인트] 기호를 ♂️ / ♀️ 로 변경하고 직관적인 이름(m_icon, f_icon)으로 세팅합니다.
                        m_icon = "♂️"
                        f_icon = "♀️"
                        
                        cover_html = (
                            f"<div class='report-page cover-page' style='padding:20px 0; margin:0 auto; width:100%; height:auto; min-height:120mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>\n"
                            f"    <div style='border: 4px solid #000000; padding: 20px 24px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 92%; max-width: 680px; margin: auto; box-sizing: border-box;'>\n"
                            f"        <div style='border-bottom: 4px double #000000; padding-bottom: 12px; margin-bottom: 15px; width: 100%; box-sizing: border-box;'>\n"
                            f"            <h1 style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 30px !important; font-weight: 900 !important; margin: 0 !important; padding: 0 !important; color: #000000 !important; letter-spacing: -1px !important; white-space: nowrap !important; line-height: 1.4 !important; text-align: center; border-bottom: none !important;'>{dynamic_title}</h1>\n"
                            f"            <div style='text-align: right; margin-top: 8px;'>\n"
                            f"                <span style='font-family: \"Nanum Myeongjo\", serif; font-size: 14px; font-weight: 700; color: #000000; letter-spacing: 1px;'>{APP_VERSION}</span>\n"
                            f"            </div>\n"
                            f"        </div>\n"
                            f"        <div style='background: #FAFAFA; border: 1px solid #000000; padding: 18px 20px; border-radius: 14px; margin-bottom: 15px;'>\n"
                            f"            <h2 style='font-family: \"Nanum Myeongjo\", serif; font-size: 20px; font-weight: 800; color: #000000; margin: 0 0 8px 0; border-bottom: none !important;'>{m_icon} {m_name} 님 ({m_age}세)</h2>\n"
                            f"            <div style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.6;'>\n"
                            f"                <p style='margin: 0; color: #000000;'><strong style='font-weight: 800 !important;'>[양력] {m_sol} | [음력] {m_lun}</strong></p>\n"
                            f"            </div>\n"
                            f"        </div>\n"
                            f"        <div style='background: #FAFAFA; border: 1px solid #000000; padding: 18px 20px; border-radius: 14px; margin-bottom: 24px;'>\n"
                            f"            <h2 style='font-family: \"Nanum Myeongjo\", serif; font-size: 20px; font-weight: 800; color: #000000; margin: 0 0 8px 0; border-bottom: none !important;'>{f_icon} {f_name} 님 ({f_age}세)</h2>\n"
                            f"            <div style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.6;'>\n"
                            f"                <p style='margin: 0; color: #000000;'><strong style='font-weight: 800 !important;'>[양력] {f_sol} | [음력] {f_lun}</strong></p>\n"
                            f"            </div>\n"
                            f"        </div>\n"
                            f"        <p style='font-family: \"Nanum Myeongjo\", serif; font-size: 17px; margin-top: 25px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>\n"
                            f"        <p style='font-family: \"Nanum Myeongjo\", serif; font-size: 24px; font-weight: 900; color: #000000; margin-top: 8px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>\n"
                            f"    </div>\n"
                            f"</div>"
                        )
                        st.session_state['saved_report_gh_cover'] = cover_html

                        # 🚨 2. 남/녀 개별 분석 페이지 조립 규칙 동기화: [원국표 -> 대운표 -> AI본문]
                        m_page_content = f"{m_tbl}\n{m_page_un_html}\n<div class='choyeon-premium-report' style='margin-top:20px;'>\n{m_ess}\n</div>"
                        f_page_content = f"{f_tbl}\n{f_page_un_html}\n<div class='choyeon-premium-report' style='margin-top:20px;'>\n{f_ess}\n</div>"
                        
                        st.session_state['saved_report_gh_m'] = wrap_a4(m_page_content, "#000000", "[ ♂️ 남명 사주 요약 ]")
                        st.session_state['saved_report_gh_f'] = wrap_a4(f_page_content, "#000000", "[ ♀️ 여명 사주 요약 ]")
                        st.session_state['saved_report_gh_g'] = wrap_a4(g_full_content, "#000000", "[ 🍀 초연 전통명리 궁합 풀이 ]")

                        if u_product in ["3-2. 결혼 택일", "3-3. 출산 택일"]:
                            s_d_val = start_date if start_date else dt_mod.date.today()
                            e_d_val = end_date if end_date else dt_mod.date.today() + dt_mod.timedelta(days=30)
                            # 🚨 [수술 3] 여기서도 에러를 유발할 수 있는 낡은 u_gender를 절대 방어막 변수인 _u_gen으로 교체!
                            m_jj_list = m_jjis if _u_gen == "남성" else [b[1] if len(b)>1 else "?" for b in partner_bazi]
                            f_jj_list = [b[1] if len(b)>1 else "?" for b in partner_bazi] if _u_gen == "남성" else m_jjis
                            
                            FORBIDDEN_LIST = ['병오', '임자', '계해', '신유', '경신']
                            delivery_days = get_optimized_delivery_days(s_d_val, e_d_val, m_jj_list, f_jj_list, FORBIDDEN_LIST)
                            
                            t_title = "결혼 택일 추천" if u_product == "3-2. 결혼 택일" else "출산택일 추천"
                            del_content = f"<h2 style='text-align:center; color:#000000;'>{t_title}</h2><p style='text-align:center; font-weight:bold; color:#000000;'>탐색 기간: {s_d_val} ~ {e_d_val} (태아 성별: {baby_gender})</p><hr style='border:1px solid #000000; margin:15px 0;'>\n"
                            for day_info in delivery_days:
                                del_content += f"<div style='font-size:16px; font-weight:bold; margin-bottom:8px; padding:8px; background:#F8F9FA; border-radius:6px; color:#000000;'>✅ 추천 길일: <b style='color:#000000;'>{day_info['date']}</b> (조화 점수: {day_info['score']}점)</div>\n"
                            
                            if u_product == "3-2. 결혼 택일":
                                delivery_prompt = (
                                    f"{db_header}\n"
                                    f"[SYSTEM ROLE: 초연시공명리 최고위 인연 & 혼례 택일 전문가]\n"
                                    f"신랑({m_name})과 신부({f_name}) 두 사람의 사주 원국 기운을 절대적 기준점으로 삼아 가문과 부부의 안녕을 극대화하는 최상의 혼례 길일 추천 리포트를 작성할 것.\n\n"
                                    f"🚨 [출력 목차 강제 지시]\n"
                                    f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                                    f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                                    f"3. 표(Table) 생성 절대 금지.\n\n"

                                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 커플 원국·대운 분석과 혼례 택일의 원칙</h3>\n"
                                    f"<div class='content-box-loose'>\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 신랑의 기본 성향과 삶의 무대</span>\n"
                                    f"[※ AI 통변 지시: 남명의 정통 명리적 격국과 삶의 주된 환경 그릇을 서술하십시오.]\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 신부의 기본 성향과 조후 균형</span>\n"
                                    f"[※ AI 통변 지시: 여명 원국의 오행 분포, 조후 균형 및 기혈 순환의 특징을 통변하십시오.]\n"
                                    f"</div>\n\n"

                                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 최적의 결혼 길일 정밀 통변 및 살성 방어</h3>\n"
                                    f"<div class='content-box-loose'>\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 길일과 배우자궁·용신의 상생 조화</span>\n"
                                    f"[※ AI 통변 지시: 추천된 결혼 길일의 일진 간지가 두 사람의 배우자 궁 및 용신 기운과 어떻게 상생하며 충형파해를 방어하는지 서술하십시오.]\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 대흉일 배제 및 살성 완벽 방어</span>\n"
                                    f"[※ AI 통변 지시: 흉살을 철저히 배제하고 방어한 근거를 서술하십시오.]\n"
                                    f"</div>\n\n"

                                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 예식 진행을 위한 최적의 길시(吉時)</h3>\n"
                                    f"<div class='content-box-loose'>\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 최상의 예식 시간대와 시충 안내</span>\n"
                                    f"[※ AI 통변 지시: 예식을 진행하기에 가장 귀한 최상의 예식 시간대(길시)와 피해야 할 시충(時沖)을 정밀 안내하십시오.]\n"
                                    f"</div>\n\n"

                                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 부부 화목과 가운 번창을 위한 개운 처세술</h3>\n"
                                    f"<div class='content-box-loose'>\n"
                                    f"[※ AI 통변 지시: 혼례 이후 신혼 생활 전반에서 두 사람의 운을 다스리고 복록을 키워나갈 실전 개운 처세법을 조언하십시오.]\n"
                                    f"</div>\n\n"

                                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>5. 고민 상담 Q&A</h3>\n"
                                    f"<div class='content-box-loose'>\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 결혼 준비 과정의 현실적 고민 공감</span>\n"
                                    f"[※ AI 통변 지시: 결혼 준비 과정에서 겪는 고민 사연에 공감하고 명리적으로 진단하십시오.]\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 완벽한 길일이 주는 확신과 조언</span>\n"
                                    f"[※ AI 통변 지시: 평생 부부 금슬을 지켜줄 가장 완벽한 길일이 주는 확신을 조언하십시오.]\n"
                                    f"</div>\n"
                                )
                            else:  # 3-3. 출산 택일
                                delivery_prompt = (
                                    f"{db_header}\n"
                                    f"[SYSTEM ROLE: 초연시공명리 최고위 산영 & 출산 택일 전문가]\n"
                                    f"부모의 사주 원국 기운과 280일 출산 예정 가임 기간 내에서 엄선된 길일을 바탕으로 프리미엄 출산 택일 리포트를 작성할 것.\n"
                                    f"- 분만 방식별 길시(吉時) 현실적 제약(제왕절개 시 주간 수술 시간 중심)을 반영할 것.\n"
                                    f"- 성별 대운(남아/여아) 분리 통변을 제공할 것.\n\n"
                                    f"🚨 [출력 목차 강제 지시]\n"
                                    f"1. 난해한 명리학 용어 해설 배제, 현실적 결론 직행.\n"
                                    f"2. 모든 문단은 <p style='text-indent: 1em;'> 태그 적용.\n"
                                    f"3. 표(Table) 생성 절대 금지.\n\n"

                                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>1. 새 생명 마중과 시공명리적 택일의 이치</h3>\n"
                                    f"<div class='content-box-loose'>\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 생명 탄생 시공간의 의의와 부모 상생</span>\n"
                                    f"[※ AI 통변 지시: 아이가 첫 호흡을 하는 시공간이 갖는 의의와 부모와의 상생 기준을 해설하십시오.]\n"
                                    f"</div>\n\n"

                                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>2. 추천 길일별 풀이 및 성별 대운 통변</h3>\n"
                                    f"<div class='content-box-loose'>\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 1순위 최상 길일 분석</span>\n"
                                    f"[※ AI 통변 지시: 1순위 길일의 명리 총평 및 남아/여아 태생 시 대운 궤도를 분석하십시오.]\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 2순위~5순위 길일 요약</span>\n"
                                    f"[※ AI 통변 지시: 나머지 길일의 핵심 특징을 요약 서술하십시오.]\n"
                                    f"</div>\n\n"

                                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>3. 출산을 위한 최적의 길시 및 보양 가이드</h3>\n"
                                    f"<div class='content-box-loose'>\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 분만 방식별 최적 출산 시간대 안내</span>\n"
                                    f"[※ AI 통변 지시: 자연분만 vs 제왕절개 최적의 출산 시간대와 피해야 할 흉시를 안내하십시오.]\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 산모와 아기를 위한 보양 처세</span>\n"
                                    f"[※ AI 통변 지시: 출산 전후 산모와 아기의 기운을 북돋을 조언을 서술하십시오.]\n"
                                    f"</div>\n\n"

                                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>4. 육아 & 양생 개운 전략</h3>\n"
                                    f"<div class='content-box-loose'>\n"
                                    f"[※ AI 통변 지시: 명리적 양육 지침과 맞춤형 환경 배치 비법을 서술하십시오.]\n"
                                    f"</div>\n\n"

                                    f"<h3 style='color:#000000; font-size: 24px; font-weight: 900;'>5. 고민 상담 Q&A</h3>\n"
                                    f"<div class='content-box-loose'>\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>1) 출산을 앞둔 부모의 불안 공감</span>\n"
                                    f"[※ AI 통변 지시: 부모의 불안함 사연에 공감하고 안심시켜 주십시오.]\n"
                                    f"<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #000000;'>2) 아이를 위한 덕담과 양육 조언</span>\n"
                                    f"[※ AI 통변 지시: 건강하고 총명한 아이로 키워내기 위한 따뜻한 덕담으로 마무리하십시오.]\n"
                                    f"</div>\n"
                                )
                            
                            del_res = model.generate_content(delivery_prompt)
                            ai_delivery_html = del_res.text.strip().replace("\n", "<br>")
                            del_content += f"<div class='content-box-loose' style='font-size:15px; line-height:1.85; margin-top:20px; color:#000000;'>\n{ai_delivery_html}\n</div>"

                            def wrap_takil_a4(content, title_color="#000000", title="[ 초연 전통명리 택일 리포트 ]"):
                                return f"<div class='report-page'>\n<div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'>\n<h1 style='text-align:center; color:{title_color}; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; border-bottom:2px solid {title_color}; padding-bottom:15px; margin-bottom:30px;'>{title}</h1>\n{content}\n</div>\n</div>"

                            st.session_state['saved_report_del'] = wrap_takil_a4(del_content, "#000000", f"[ 초연 전통명리 {u_product} ]")

                except Exception as e:
                    st.error(f"3단계 궁합 종합 분석 가동 장애: {e}")

            st.session_state['need_calc'] = False

        # 🚨 [수술]: 여기가 날아갔습니다! 전체 연산을 감싸는 거대 try를 닫아주는 뚜껑입니다.
        except Exception as e:
            st.error(f"시스템 전체 연산 중 치명적 오류 발생: {e}")

# ==============================================================================
# 🍽️ 9. 화면 출력부 (통합 완결 출력)
# ==============================================================================
if st.session_state.get('app_running', False):
    
    # 1. 개인 사주 및 특성화 상품 출력
    if main_category in ["1. 개인 사주팔자 풀이 (종합)", "2. 테마별 특성화 상담"]:
        if st.session_state.get('saved_report_html'):
            st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
        if st.session_state.get('saved_report_iljin'):
            st.markdown(st.session_state.get('saved_report_iljin', ''), unsafe_allow_html=True)
    
    # 2. 타 감명서 대조 출력 (사주)
    elif main_category == "4. 타 감명서 비교" and u_product == "4-1. 타 감명서 비교 (사주)":
        if st.session_state.get('saved_report_html'):
            st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
        if st.session_state.get('saved_report_2'):
            st.markdown(st.session_state.get('saved_report_2', ''), unsafe_allow_html=True)
        
    # 3. 궁합 및 택일 / 타 감명서 대조 출력 (궁합)
    elif main_category == "3. 커플 연애/결혼운 (궁합) 풀이" or u_product == "4-2. 타 감명서 비교 (궁합)":
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

        if st.session_state.get('saved_report_2'):
            st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
            st.markdown(st.session_state.get('saved_report_2', ''), unsafe_allow_html=True)
