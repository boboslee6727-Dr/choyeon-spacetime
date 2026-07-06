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
APP_VERSION = "Ver 48.9 (Master AI Optimized)"

# (스트림릿 절대 규칙: 레이아웃 설정은 반드시 다른 스트림릿 명령어보다 먼저 와야 합니다.)
st.set_page_config(page_title=f"초연 시공명리 {APP_VERSION}", layout="wide")

# ==============================================================================
# 💾 [초연 시공명리 데이터베이스 연동 (캐싱 최적화)]
# ==============================================================================
@st.cache_data
def load_choyeon_db():
    file_path = 'choyeon_db.json'
    
    # 1. 파일 존재 여부 확인
    if not os.path.exists(file_path):
        st.error("🚨 choyeon_db.json 파일을 찾을 수 없습니다. 깃허브에 업로드되었는지 확인해 주세요.")
        return {}
        
    # 2. 한글 깨짐 방지 및 JSON 로드
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error("🚨 JSON 파일 내부의 괄호나 쉼표 형식이 깨져 있습니다. 문법을 확인해 주세요.")
        return {}

# 앱 시작 시 DB 로드 (전역 변수로 메모리에 상주하여 속도 저하 0%)
choyeon_db = load_choyeon_db()

# ==============================================================================
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS
# ==============================================================================
st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");    
    body, .stApp { background-color: #FFF8E1; }
    
    .report-page { width: 210mm; max-width: 100%; margin: 30px auto; background-color: #FFFFFF !important; padding: 15mm 10mm; box-shadow: 0 0 20px rgba(0,0,0,0.15); border-radius: 20px; box-sizing: border-box; }
    .report-page, .report-page * { font-family: 'Noto Serif KR', serif !important; color: #000000; }
    
    .vip-inset-frame { border: 2px solid #1A237E; border-radius: 15px; padding: 20px; background: transparent; box-sizing: border-box; width: 100%; overflow: hidden; word-break: keep-all; -webkit-box-decoration-break: clone; box-decoration-break: clone; }

    .cover-page .title-gothic { font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif !important; color: #0054FF !important; font-weight: 900 !important; }
    .cover-page .ver-gothic { font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif !important; color: #555555 !important; font-weight: 900 !important; }

    .report-page h1 { font-size: 26px !important; margin-bottom: 15px !important; color: #1A237E !important; font-weight: 900 !important; }
    .report-page h2 { font-size: 22px !important; margin-bottom: 15px !important; font-weight: 900 !important; }
    .report-page h3 { font-size: 22px !important; margin-top: 25px !important; margin-bottom: 8px !important; border-bottom: 2px solid #1A237E; padding-bottom: 5px; color: #1A237E !important; font-weight: 900 !important; }
    .report-page h4 { font-size: 18px !important; margin-top: 15px !important; margin-bottom: 8px !important; font-weight: 900 !important; }
    
    .result-table { width: 100%; border-collapse: collapse; border: 3px solid #3E2723; margin-bottom: 15px; table-layout: fixed; }
    .result-table td { border: 1px solid #444; padding: 1px; text-align: center; vertical-align: middle; font-weight: 900; font-size: 13px; line-height: 1.2; word-wrap: break-word; }
    
    .no-border-row td { border-top: none !important; border-bottom: none !important; }
    .no-border-row:last-of-type td { border-bottom: 1px solid #444 !important; }
    
    .header-cell-main { background-color: #E8EAF6 !important; color: #1A237E !important; font-weight: 900 !important; font-size: 15px !important; border: 1px solid #444 !important; }
    
    .top-header-cell { background-color: #1A237E !important; height: 30px !important; }
    .top-header-cell td, .top-header-cell span { color: #FFFFFF !important; font-weight: 900 !important; font-size: 16px !important; }
    
    .color-목 { background-color: #2E7D32 !important; color: white !important; }
    .color-화 { background-color: #C62828 !important; color: white !important; }
    .color-토 { background-color: #F9A825 !important; color: black !important; }
    .color-금 { background-color: #9E9E9E !important; color: white !important; }
    .color-수 { background-color: #212121 !important; color: white !important; }
    .color-무 { background-color: white !important; }
    
    .content-box-loose { line-height: 1.8; font-size: 15px; color: #111; text-align: justify; word-break: keep-all; font-family: 'Noto Serif KR', 'Nanum Myeongjo', serif !important; padding: 0 !important; }
    .content-box-loose .sub-title { text-indent: 0px !important; margin-top: 25px !important; margin-bottom: 10px !important; font-weight: 900 !important; display: block; color: #111 !important; }
    
    div[data-testid="stSidebar"] div.stButton > button:first-child,
    div.stButton > button[kind="primary"] { background-color: #D50000 !important; color: white !important; border: none !important; height: 45px !important; }
    
    div[data-testid="stSidebar"] div.stButton > button:first-child p,
    div.stButton > button[kind="primary"] p { font-weight: 900 !important; font-size: 15px !important; font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif !important; color: white !important; margin: 0 !important; }

    div[data-testid="stSidebar"] .navy-btn button { background-color: #1A237E !important; color: white !important; border: none !important; font-weight: 900 !important; height: 45px !important; }   
    
    @media print { 
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; }
        
        .block-container, div[data-testid="stAppViewBlockContainer"] { padding-top: 0 !important; padding-bottom: 0 !important; margin-top: 0 !important; margin-bottom: 0 !important; }
        div[data-testid="stVerticalBlock"] { gap: 0 !important; }
        .element-container, .stMarkdown { margin-bottom: 0 !important; }
        
        .report-page { box-shadow: none; margin: 0 auto; padding: 0; page-break-after: always; border-radius: 0; width: 100%; max-width: 100%; }
        .report-page:last-of-type { page-break-after: auto; }
        .page-break-before { page-break-before: always; }
        .vip-inset-frame { border: 2px solid #000; border-radius: 20px; padding: 15px; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. 시스템 변수 세팅 및 써머타임 엔진
# ==============================================================================

idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]

def get_total_time_adjustment(dt):
    adj = -30
    if dt_mod.datetime(1954, 3, 21) <= dt <= dt_mod.datetime(1961, 8, 9, 23, 59): adj = 0
    si = [(dt_mod.datetime(1948,5,31), dt_mod.datetime(1948,9,22)), (dt_mod.datetime(1949,3,31), dt_mod.datetime(1949,9,30)), (dt_mod.datetime(1950,4,1), dt_mod.datetime(1950,9,10)), (dt_mod.datetime(1951,5,6), dt_mod.datetime(1951,9,9)), (dt_mod.datetime(1954,3,21), dt_mod.datetime(1954,5,5)), (dt_mod.datetime(1955,4,6), dt_mod.datetime(1955,9,22)), (dt_mod.datetime(1956,5,20), dt_mod.datetime(1956,9,30)), (dt_mod.datetime(1957,5,5), dt_mod.datetime(1957,9,22)), (dt_mod.datetime(1958,5,4), dt_mod.datetime(1958,9,21)), (dt_mod.datetime(1959,5,4), dt_mod.datetime(1959,9,20)), (dt_mod.datetime(1960,5,1), dt_mod.datetime(1960,9,18)), (dt_mod.datetime(1987,5,10,2), dt_mod.datetime(1987,10,11,3)), (dt_mod.datetime(1988,5,8,2), dt_mod.datetime(1988,10,9,3))]
    for s, e in si:
        if s <= dt <= e: adj -= 60; break
    return adj

# 십천간 / 십이지지 리스트 전역 선언
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

def extract_ganji(text):
    g = [c for c in text if c in "甲乙丙丁戊己庚辛壬癸갑을병정무기경신임계"]
    j = [c for c in text if c in "子丑寅卯辰巳午未申酉戌亥자축인묘진사오미신유술해"]
    return (g[0] if g else "?") + (j[0] if j else "?")

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
    
    if 315 <= lon < 345: m_ji_idx = 2    # 寅(인)월
    elif 345 <= lon or lon < 15: m_ji_idx = 3  # 卯(묘)월
    elif 15 <= lon < 45: m_ji_idx = 4    # 辰(진)월
    elif 45 <= lon < 75: m_ji_idx = 5    # 巳(사)월
    elif 75 <= lon < 105: m_ji_idx = 6   # 午(오)월
    elif 105 <= lon < 135: m_ji_idx = 7  # 未(미)월
    elif 135 <= lon < 165: m_ji_idx = 8  # 申(신)월
    elif 165 <= lon < 195: m_ji_idx = 9  # 酉(유)월
    elif 195 <= lon < 225: m_ji_idx = 10 # 戌(술)월
    elif 225 <= lon < 255: m_ji_idx = 11 # 亥(해)월
    elif 255 <= lon < 285: m_ji_idx = 0  # 子(자)월
    elif 285 <= lon < 315: m_ji_idx = 1  # 丑(축)월
    
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
    _gemini_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as _api_e:
    st.error(f"🚨 Gemini API 키 오류: {_api_e}")
    _gemini_client = None

@st.cache_data(show_spinner=False, ttl=3600*24) #ttl=3600*24초=86,400초 24시간 감명서 유효
def get_ai_response(prompt_text, model_name='gemini-2.5-flash'):
    if '1.5' in model_name:
        model_name = 'gemini-2.5-flash'
        
    if _gemini_client is None:
        return "<div style='color:red;'>🚨 Gemini 모델이 초기화되지 않았습니다.</div>"
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = _gemini_client.models.generate_content(model=model_name, contents=prompt_text)
            return response.text.strip()
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1); continue
            return f"<div style='color:red;'>🚨 AI 서버 장애: {e}</div>"

def call_gemini_api(prompt_text, max_tokens=8000):
    return get_ai_response(prompt_text, model_name='gemini-2.5-flash')

def call_light_api(prompt_text):
    return get_ai_response(prompt_text, model_name='gemini-2.5-flash')

JIJANGGAN = {'子': ['壬', '-', '癸'], '丑': ['癸', '辛', '己'], '寅': ['戊', '丙', '甲'], '卯': ['甲', '-', '乙'], '辰': ['乙', '癸', '戊'], '巳': ['戊', '庚', '丙'], '午': ['丙', '己', '丁'], '未': ['丁', '乙', '己'], '申': ['戊', '壬', '庚'], '酉': ['庚', '-', '辛'], '戌': ['辛', '丁', '戊'], '亥': ['戊', '甲', '壬'] }

def get_color(c):
    if c in "甲乙寅卯": return "목"
    if c in "丙丁巳午": return "화"
    if c in "戊己辰戌丑未": return "토"
    if c in "庚辛申酉": return "금"
    if c in "壬癸亥子": return "수"
    return "무"

def get_current_saju_data():
    try:
        gans = st.session_state.get('saju_gans', ['?', '?', '?', '?'])
        jjis = st.session_state.get('saju_jjis', ['?', '?', '?', '?'])
        return gans, jjis
    except:
        return ['?', '?', '?', '?'], ['?', '?', '?', '?']

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
    if gj in ["戊寅", "戊申", "癸巳", "癸亥"]: evil.append("복신") 

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

    if ds in ['甲', '丙', '戊', '庚', '壬']:
        if mb == '卯' and ds == '甲': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == '午' and ds == '丙': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == '酉' and ds == '庚': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == '子' and ds == '壬': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == {'甲':'寅', '丙':'巳', '戊':'巳', '庚':'申', '壬':'亥'}.get(ds, ""):
            return "건록격", f"월지 {mb}가 일간 {ds}의 건록(建祿)에 해당하여 건록격으로 정합니다."

    def safe_get_ss(day_gan, target_char):
        if not target_char or target_char == "?": return "무명"
        return get_ss(day_gan, target_char)

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
    
    return fallback_ss + "격", f"월지 {mb}의 지장간(비겁 제외)이 투출하지 않아 정기(본기)인 {main_qi}를 기준으로 {fallback_ss}격으로 정합니다."

def calculate_gongmang(ilgan, ilji):
    if ilgan in ["?"," ","-"] or ilji in ["?"," ","-"]: return "-"
    try:
        base = (list(JI).index(ilji) - list(GAN).index(ilgan) - 2) % 12
        return list(JI)[base] + "," + list(JI)[(base+1)%12]
    except: return "-"

def get_universal_analysis(ds, mb, db, gans, jjis):
    jg_list = JIJANGGAN.get(mb, [])
    
    def get_info(gan, target_char, base_ji):
        ss = get_ss(gan, target_char) 
        twelve = get_unsung(target_char, base_ji) 
        return ss, twelve
        
    results = []
    for qi in jg_list:
        ss, twelve = get_info(ds, qi, mb)
        results.append(f"{qi}({ss}): {twelve}좌")
        
    all_present = list(gans)
    for j in jjis:
        if j not in ["?", " ", "-"]:
            all_present.extend(JIJANGGAN.get(j, [])) 
            
    missing = [elem for elem in ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'] if elem not in all_present]
    for m in missing:
        ss, twelve = get_info(ds, m, db)
        results.append(f"{m}({ss}): 인종법 적용 - {twelve}종")
    return results

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

def get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, forbidden_list=None):
    import datetime as dt_mod
    from korean_lunar_calendar import KoreanLunarCalendar
    
    OHENG_MAP = {
        '갑':'목', '을':'목', '인':'목', '묘':'목',
        '병':'화', '정':'화', '사':'화', '오':'화',
        '무':'토', '기':'토', '축':'토', '진':'토', '미':'토', '술':'토',
        '경':'금', '신':'금', '유':'금',
        '임':'수', '계':'수', '자':'수', '해':'수'
    }
    
    # [0단계] 절대 흉살 및 백호/괴강 원천 차단 킬스위치
    KILL_SWITCH = {'병오', '임자', '신유', '경신', '을묘', '무오', '무술', '정축', '갑진', '을미', '병술', '무진', '임술', '계축'}
    hap_list = [{'자', '축'}, {'인', '해'}, {'묘', '술'}, {'진', '유'}, {'사', '신'}, {'오', '미'}]
    choong_list = [{'자', '오'}, {'축', '미'}, {'인', '신'}, {'묘', '유'}, {'진', '술'}, {'사', '해'}]
    
    H2K_MAP = {'甲':'갑','乙':'을','丙':'병','丁':'정','戊':'무','己':'기','庚':'경','辛':'신','壬':'임','癸':'계',
               '子':'자','丑':'축','寅':'인','卯':'묘','辰':'진','巳':'사','午':'오','未':'미','申':'신','酉':'유','戌':'술','亥':'해'}
    def h2k(text): return "".join([H2K_MAP.get(c, c) for c in text])

    TIME_SLOTS = [
        ("자", "23:30~01:29"), ("축", "01:30~03:29"), ("인", "03:30~05:29"),
        ("묘", "05:30~07:29"), ("진", "07:30~09:29"), ("사", "09:30~11:29"),
        ("오", "11:30~13:29"), ("미", "13:30~15:29"), ("신", "15:30~17:29"),
        ("유", "17:30~19:29"), ("술", "19:30~21:29"), ("해", "21:30~23:29")
    ]
    TIME_STEM_START = {'갑':'갑', '기':'갑', '을':'병', '경':'병', '병':'무', '신':'무', '정':'경', '임':'경', '무':'임', '계':'임'}
    GAN_LIST = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계']

    raw_candidates = []
    curr = start_date
    
    HOT_JI = ['사', '오', '미', '술']
    COLD_JI = ['해', '자', '축', '진']
    
    while curr <= end_date:
        birth_d = curr + dt_mod.timedelta(days=280)
        
        b_klc = KoreanLunarCalendar()
        b_klc.setSolarDate(birth_d.year, birth_d.month, birth_d.day)
        b_gj = b_klc.getChineseGapJaString().split()
        
        if len(b_gj) >= 3:
            b_gj_kor = [h2k(pillar) for pillar in b_gj[:3]] 
            b_year, b_month, b_day = b_gj_kor[0], b_gj_kor[1], b_gj_kor[2]
            
            # [0단계] 흉살 및 복음(간지 중복) 배제
            if b_year in KILL_SWITCH or b_month in KILL_SWITCH or b_day in KILL_SWITCH:
                curr += dt_mod.timedelta(days=1); continue
            if b_year == b_month or b_month == b_day or b_year == b_day:
                curr += dt_mod.timedelta(days=1); continue
            
            # ------------------------------------------------------------------
            # [1단계 - 최우선] 년주와 월주의 기후(조후) 평가 (최대 45점)
            # ------------------------------------------------------------------
            ym_score = 25 # 기본 점수
            y_ji = b_year[1]
            m_ji = b_month[1]
            
            # 년도의 조열/한랭함을 월(Month)이 보완해주는 달에 압도적 가점 부여
            if y_ji in HOT_JI:
                if m_ji in COLD_JI or m_ji in ['신', '유']: ym_score += 20
                elif m_ji in HOT_JI: ym_score -= 20
            elif y_ji in COLD_JI:
                if m_ji in HOT_JI or m_ji in ['인', '묘']: ym_score += 20
                elif m_ji in COLD_JI: ym_score -= 20
            else:
                ym_score += 10 
                
            ym_score = max(0, min(45, ym_score))
            
            b_day_stem = b_day[0]
            start_stem = TIME_STEM_START.get(b_day_stem, '갑')
            start_idx = GAN_LIST.index(start_stem)

            best_time_score = -999
            best_time_data = {}

            # ------------------------------------------------------------------
            # [2단계 - 추천] 최적의 일주/시주 핀셋 탐색 (최대 25점)
            # ------------------------------------------------------------------
            for t_idx, (t_ji, t_time_str) in enumerate(TIME_SLOTS):
                t_gan = GAN_LIST[(start_idx + t_idx) % 10]
                b_time = f"{t_gan}{t_ji}"

                if b_time in KILL_SWITCH or b_time in [b_year, b_month, b_day]:
                    continue

                four_pillars = [b_year, b_month, b_day, b_time]
                characters = []
                for pillar in four_pillars:
                    characters.extend([pillar[0], pillar[1]])
                    
                oheng_counts = {'목': 0, '화': 0, '토': 0, '금': 0, '수': 0}
                for char in characters:
                    oh = OHENG_MAP.get(char)
                    if oh: oheng_counts[oh] += 1
                    
                # 4주 8자의 오행 구비 점수 (최대 25점)
                present_types = [t for t, c in oheng_counts.items() if c > 0]
                dt_score = len(present_types) * 5 
                for t, c in oheng_counts.items():
                    if c >= 3: dt_score -= 10 # 편중 감점
                
                dt_score = max(0, min(25, dt_score))
                baby_score = ym_score + dt_score # 신생아 명식 총점 (최대 70점)
                
                # ------------------------------------------------------------------
                # [3단계] 부모 조화도 (최대 30점)
                # ------------------------------------------------------------------
                parent_score = 15
                b_ilji = b_day[1]
                for p_ji in m_jjis + f_jjis:
                    if p_ji == '?': continue
                    pair = {b_ilji, p_ji}
                    if pair in hap_list: parent_score += 10
                    if pair in choong_list: parent_score -= 10
                parent_score = max(0, min(30, parent_score))
                
                # 소수점 오류 방지: 빠른 날짜에 극미세 가중치 (31일 쏠림 방지)
                tie_breaker = ((32 - birth_d.day) * 0.001) + (t_idx * 0.0001)
                total_score = baby_score + parent_score + tie_breaker

                if total_score > best_time_score:
                    best_time_score = total_score
                    best_time_data = {
                        'time_pillar': b_time,
                        'time_str': t_time_str,
                        'score': total_score,
                        'ym_score': ym_score
                    }

            if best_time_data:
                raw_candidates.append({
                    'date': curr.strftime('%Y-%m-%d'),
                    'month': curr.strftime('%Y-%m'),
                    'score': best_time_data['score'],
                    'ym_score': best_time_data['ym_score'],
                    'best_time': best_time_data
                })
                
        curr += dt_mod.timedelta(days=1)
        
    # 월(Month) 단위로 그룹화 (년/월 점수가 가장 높은 달을 최우선 추출)
    month_best_bucket = {}
    for item in raw_candidates:
        m_key = item['month']
        if m_key not in month_best_bucket or item['score'] > month_best_bucket[m_key]['score']:
            month_best_bucket[m_key] = item
            
    sorted_months = sorted(month_best_bucket.values(), key=lambda x: x['score'], reverse=True)
    return sorted_months[:3]
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
# 4. 사이드바 UI (Top-Down 동적 레이아웃)
# ==============================================================================
with st.sidebar:
    st.title("🏮초연 시공명리 연구소")
    st.caption(f"{APP_VERSION} Master (Base + Gunghap)")
    st.markdown("---")

    # 1. 본인 사주 역산 (통합 파싱 모듈)
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
            _ry, _rm, _rd = extract_ganji(ry), extract_ganji(rm), extract_ganji(rd)
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
                                    ji_char = extract_ganji(rt)[-1]
                                    rt_h = K2H_JI.get(ji_char, ji_char)
                                    if rt_h in time_map_rev: st.session_state.s_t = time_map_rev[rt_h]
                                found = True
                                st.success(f"✅ {curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일 입력완료!")
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                    if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

    st.markdown("---")
    u_product = st.selectbox("📋 분석 상품 선택", ["개인사주", "궁합", "타 감명서"])
    
    st.markdown("<div style='font-weight:900; color:#1A237E; margin-bottom:5px;'>👤 신청인 정보 (공통)</div>", unsafe_allow_html=True)
    u_name = st.text_input("이름", value="", key="u_n")
    u_gender = st.selectbox("성별", ["남성", "여성"], key="u_g")
    u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
    u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")
    
    col1, col2, col3 = st.columns(3)
    u_y = col1.number_input("년", 1900, 2050, value=2010, key="s_y")
    u_m = col2.number_input("월", 1, 12, value=1, key="s_m")
    u_d = col3.number_input("일", 1, 31, value=1, key="s_d")
    u_t = st.selectbox("태어난 시간", idx_list, key="s_t")
    
    # 🚨 [수술 완료] 어떤 조건에서도 에러가 나지 않도록 스위치 기본값 강제 선언!
    run_iljin_calc = False
    run_delivery_calc = False
    
    # 2. 상품별 동적 UI
    if u_product == "개인사주":
        # 패턴 1: 개인사주 -> 체크박스로 일진 추가
        run_iljin_calc = st.checkbox("🔮 일진 시공간 분석 추가 가동", value=False)
        if run_iljin_calc: 
            st.session_state['target_date'] = st.date_input("분석 일자", value=dt_mod.datetime.now().date())
            
    elif u_product == "타 감명서":
        # 패턴 2: 타 감명서 -> 원문 입력창
        other_reading_text = st.text_area("📄 타 감명서 원문", height=150, key="other_reading")
        
    elif u_product == "궁합":
        with st.expander("🔍 상대방 사주팔자 역산 검색", expanded=False):
            p_col_g1, p_col_g2 = st.columns(2)
            with p_col_g1: p_ry = st.text_input("상대방 년주", key="p_ry")
            with p_col_g2: p_rm = st.text_input("상대방 월주", key="p_rm")
            p_col_g3, p_col_g4 = st.columns(2)
            with p_col_g3: p_rd = st.text_input("상대방 일주", key="p_rd")
            with p_col_g4: p_rt = st.text_input("상대방 시주", key="p_rt")
            if st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="p_rev_btn"):
                _pry, _prm, _prd = extract_ganji(p_ry), extract_ganji(p_rm), extract_ganji(p_rd)
                if len(_pry)==2 and len(_prm)==2 and len(_prd)==2:
                    p_ry_h = K2H_GAN.get(_pry[0], _pry[0]) + K2H_JI.get(_pry[1], _pry[1])
                    p_rm_h = K2H_GAN.get(_prm[0], _prm[0]) + K2H_JI.get(_prm[1], _prm[1])
                    p_rd_h = K2H_GAN.get(_prd[0], _prd[0]) + K2H_JI.get(_prd[1], _prd[1])
                    p_klc_find = KoreanLunarCalendar(); p_found = False
                    for y in range(2026, 1899, -1):
                        p_klc_find.setSolarDate(y, 7, 1); p_gj_y = p_klc_find.getChineseGapJaString().split()
                        if p_gj_y and p_gj_y[0][:2] == p_ry_h:
                            p_curr_dt = dt_mod.date(y+1, 2, 28)
                            while p_curr_dt >= dt_mod.date(y, 1, 1):
                                p_klc_find.setSolarDate(p_curr_dt.year, p_curr_dt.month, p_curr_dt.day)
                                p_gj = p_klc_find.getChineseGapJaString().split()
                                if len(p_gj) >= 3 and p_gj[0][:2] == p_ry_h and p_gj[1][:2] == p_rm_h and p_gj[2][:2] == p_rd_h:
                                    st.session_state.p_y_in, st.session_state.p_m_in, st.session_state.p_d_in = p_curr_dt.year, p_curr_dt.month, p_curr_dt.day
                                    time_map_rev = {'子':'00:30 ~ 01:29 (朝子)시','丑':'01:30 ~ 03:29 (丑)시','寅':'03:30 ~ 05:29 (寅)시','卯':'05:30 ~ 07:29 (卯)시','辰':'07:30 ~ 09:29 (辰)시','巳':'09:30 ~ 11:29 (巳)시','午':'11:30 ~ 13:29 (午)시','未':'13:30 ~ 15:29 (未)시','申':'15:30 ~ 17:29 (申)시','酉':'17:30 ~ 19:29 (酉)시','戌':'19:30 ~ 21:29 (戌)시','亥':'21:30 ~ 23:29 (亥)시'}
                                    if p_rt:
                                        p_ji_char = extract_ganji(p_rt)[-1]
                                        p_rt_h = K2H_JI.get(p_ji_char, p_ji_char)
                                        if p_rt_h in time_map_rev: st.session_state.p_t_key = time_map_rev[p_rt_h]
                                    p_found = True
                                    st.success(f"✅ 상대방 {p_curr_dt.year}년 {p_curr_dt.month:02d}월 {p_curr_dt.day:02d}일 입력완료!")
                                    break
                                p_curr_dt -= dt_mod.timedelta(days=1)
                        if p_found: break
                    if not p_found: st.error("일치하는 날짜가 없습니다.")
                else: st.warning("간지를 2글자씩 정확히 입력하세요.")
        
        st.markdown("<div style='font-weight:900; color:#D50000; margin-bottom:5px; margin-top:15px;'>👥 상대방 정보</div>", unsafe_allow_html=True)
        p_name = st.text_input("이름", value="", key="p_n")
        
        p_gender_options = ["여성", "남성"] if u_gender == "남성" else ["남성", "여성"]
        p_gender = st.selectbox("성별", p_gender_options, key="p_g")
        
        p_marital = st.selectbox("혼인여부", ["미혼", "기혼", "돌싱"], key="p_m_stat")
        p_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="p_c")
        
        p_col1, p_col2, p_col3 = st.columns(3)
        p_y = p_col1.number_input("년 (상대)", 1900, 2050, value=1980, key="p_y_in")
        p_m = p_col2.number_input("월 (상대)", 1, 12, value=1, key="p_m_in")
        p_d = p_col3.number_input("일 (상대)", 1, 31, value=1, key="p_d_in")
        
        p_t = st.selectbox("태어난 시간", idx_list, key="p_t_key")
        
        # 🚨 [박사님 의도 100% 반영] 패턴 3: 출산택일 옵션 및 탐색 기간 직접 통제 UI 복구
        run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석 추가 가동", value=False)
        if run_delivery_calc:
            # 🚨 [오류 원인 철거] 화면을 깨지게 만들던 강제 HTML div 래퍼를 완전히 삭제했습니다.
            st.markdown("<h5 style='color:#4A148C; margin-top:10px; margin-bottom:10px;'>🩸 산모 생체 리듬 간편 입력</h5>", unsafe_allow_html=True)
            
            # 🚨 [수술 1] key="고유이름" 을 부여하여 메모리 증발을 원천 차단
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                last_period_date = st.date_input("생리 시작일", value=dt_mod.date.today(), key="input_last_period")
            with col_b2:
                period_cycle = st.number_input("생리 주기(일)", min_value=20, max_value=50, value=28, step=1, key="input_period_cycle")

            # 🧬 [의학 로직 & 탐색 윈도우 기본값 계산]
            next_period_date = last_period_date + dt_mod.timedelta(days=period_cycle)
            ovulation_date = next_period_date - dt_mod.timedelta(days=14)
            
            expected_delivery_date = ovulation_date + dt_mod.timedelta(days=266)
            auto_start_date = expected_delivery_date - dt_mod.timedelta(days=14)
            auto_end_date = expected_delivery_date

            st.markdown(f"<span style='font-size:13px; color:#D50000; font-weight:bold; display:block; margin-top:5px;'>🎯 의학적 배란(합궁) 예정일: {ovulation_date.strftime('%Y/%m/%d')}</span>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:10px 0px; border: 0.5px dashed #ccc;'>", unsafe_allow_html=True)
            st.markdown("<h5 style='color:#1A237E; margin-top:0px; margin-bottom:10px;'>📅 출산 탐색 기간 (자유 변경 가능)</h5>", unsafe_allow_html=True)
            
            # 🚨 [수술 2] 탐색 기간에도 key를 부여하여 안전하게 고정
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                final_start_date = st.date_input("탐색 시작일", value=auto_start_date, key="input_search_start")
            with col_d2:
                final_end_date = st.date_input("탐색 종료일", value=auto_end_date, key="input_search_end")

            # 🚨 [수술 3] 8번 모듈로 전달하기 위해 변수 4개를 모두 명시적으로 저장
            st.session_state['search_start_date'] = final_start_date
            st.session_state['search_end_date'] = final_end_date
            st.session_state['last_period_date'] = last_period_date
            st.session_state['period_cycle'] = period_cycle

    btn_single = st.button("🚀 초연 시공명리 사주풀이 가동", use_container_width=True, type="primary")

    components.html("""
    <script>
        function triggerPrint() {
            window.parent.print();
        }
    </script>
    <button onclick='triggerPrint()' style='width:95%; background-color:#2E7D32; color:white; border:none; font-weight:900; height:45px; border-radius:8px; cursor:pointer; font-size:15px; font-family:"Malgun Gothic", sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.15); margin:5px;'>
        🖨️ 풀이 결과 인쇄 / PDF 저장
    </button>
    """, height=70)

    if btn_single:
        # [0단계] 입력값 유효성 정밀 검증
        if not u_name.strip(): 
            st.warning("🚨 [입력 오류] 신청인의 이름이 누락되었습니다. 정확한 성명을 입력해 주십시오.")
            st.stop()
        elif len(u_name.strip()) > 10:
            st.warning("🚨 [입력 오류] 이름이 너무 깁니다. 10자 이내로 정확히 입력해 주십시오.")
            st.stop()
            
        if u_y < 1900 or u_y > 2050:
            st.warning("🚨 [입력 오류] 입력하신 출생 연도가 범위를 벗어났습니다. (허용 범위: 1900년 ~ 2050년)")
            st.stop()
            
        if u_product == "타 감명서" and not other_reading_text.strip():
            st.warning("🚨 [입력 오류] 타 감명서 원문을 입력해 주십시오.")
            st.stop()
            
        if u_product == "궁합" and not p_name.strip(): 
            st.warning("🚨 [입력 오류] 상대방의 이름을 입력해 주십시오.")
            st.stop()
            
        if "모름" in str(u_t) or not u_t:
            st.info("ℹ️ [안내] 태어난 시간을 입력하지 않으셨습니다. 시주(時柱)를 제외한 삼주육자(三柱六字)로 감명을 진행합니다.")
        
        st.session_state['app_running'] = True
        
        if u_product == "개인사주" and run_iljin_calc and st.session_state.get('saved_report_html'):
            st.session_state['need_calc'] = False
            st.session_state['run_waterfall'] = True
            if 'saved_report_iljin' in st.session_state: del st.session_state['saved_report_iljin']
            
        elif u_product == "타 감명서":
            st.session_state['need_calc'] = True
            st.session_state['run_waterfall'] = False
            st.session_state['run_delivery_only'] = False
            for key in ['saved_report_html', 'saved_report_2', 'saved_report_gh_cover', 'saved_report_gh_m', 'saved_report_gh_f', 'saved_report_gh_g', 'saved_report_del', 'saved_report_iljin']:
                if key in st.session_state: del st.session_state[key]
                
        elif u_product == "궁합" and run_delivery_calc and st.session_state.get('saved_report_gh_g'):
            st.session_state['need_calc'] = False
            st.session_state['run_delivery_only'] = True
            if 'saved_report_del' in st.session_state: del st.session_state['saved_report_del']
            
        else:
            st.session_state['need_calc'] = True
            st.session_state['run_waterfall'] = run_iljin_calc if u_product == "개인사주" else False 
            st.session_state['run_delivery_only'] = run_delivery_calc if u_product == "궁합" else False
            for key in ['saved_report_html', 'saved_report_2', 'saved_report_gh_cover', 'saved_report_gh_m', 'saved_report_gh_f', 'saved_report_gh_g', 'saved_report_del', 'saved_report_iljin', 'partner_bazi']:
                if key in st.session_state: del st.session_state[key]

# ==============================================================================
# 5. 분석 가동 로직 (need_calc 상태일 때만 무거운 연산 실행)
# ==============================================================================
if st.session_state.get('need_calc', False):
    spinner_msg = f"⏳ [초연 시공명리 분석({APP_VERSION}) 중....]"
    with st.spinner(spinner_msg):
        try:
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
            
            def td(c, size="18px"): return f"<td class='color-{get_color(c)}' style='font-size:{size}; font-weight:900; border:1px solid #444 !important;'>{('?' if c in ['?',' ','-'] else c)}</td>"
            
            disp_name = u_name if u_name.strip() else "홍길동"
            p_icon = "♂️" if u_gender == "남성" else "♀️"
            p_color = "#1A237E" if u_gender == "남성" else "#D50000"
            today_str = (dt_mod.datetime.utcnow() + dt_mod.timedelta(hours=9)).strftime("%Y년 %m월 %d일")

            # ------------------------------------------------------------------
            # [모드 1] 개인사주 분석
            # ------------------------------------------------------------------
            if u_product in ["개인사주", "궁합", "타 감명서"]:
                past_months_html = ""

                cover_html = (
                        f"<div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>\n"
                        f"    <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>\n"
                        f"        <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>\n"
                        f"            <h1 class='title-gothic' style='font-size: 40px !important; margin:0 !important;'>초연 시공명리 사주팔자 풀이</h1>\n"
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
                        f"        <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 20px;'>초연 시공명리 연구소</p>\n"
                        f"    </div>\n"
                        f"</div>"
                    )
                st.session_state['saved_report_cover'] = cover_html

                ji_rel_rows = ""
                for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                    b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                    b_top = "0px solid transparent !important"
                    cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                    lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                    ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

                info_h = f"<div style='text-align:center; font-family:\"Malgun Gothic\", sans-serif; margin-bottom:15px; line-height:1.5;'><span style='font-size:18px; font-weight:900; color:{p_color}; white-space:nowrap;'>{p_icon} {disp_name}님 ({u_gender}, {u_marital}, {u_age}세)</span><br><span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span></div>"

                table_html = f"""<div style='text-align:center; margin-bottom:10px;'>{info_h}</div>
<table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
<tr class='top-header-cell'>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>구분</td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>시주</td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>일주</td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>월주</td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>년주</td>
</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간합충</td>{"".join([f"<td style='border:1px solid #444;'>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(ds,ms)}</td><td style='border:1px solid #444;'>{get_ss(ds,ys)}</td></tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(ds,hb)}</td><td style='border:1px solid #444;'>{get_ss(ds,db)}</td><td style='border:1px solid #444;'>{get_ss(ds,mb)}</td><td style='border:1px solid #444;'>{get_ss(ds,yb)}</td></tr>
<tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
{ji_rel_rows}
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이운성</td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이신살</td>{"".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis, u_gender)) if get_general_shinsal_filtered(i, gans, jjis, u_gender) else '-'}</td>" for i in range(4)])}</tr>
</table>
"""
                calc_gyukgook, gyukgook_detail = get_gyukgook_detailed(ds, ys, ms, hs, mb)

                gen_shinsal_list = []
                for i in range(4):
                    raw_tags = get_general_shinsal_filtered(i, gans, jjis, u_gender)
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
                
                master_bar_html = f"""
<div style='border:2px solid #3E2723; margin-top:20px; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap;'>
    <div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div>
    <div>🌟 천을귀인: {guiin_str}</div>
    <div>🎯 공망: [년] {n_gong} / [일] {i_gong}</div>
    <div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div>
</div>
"""
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
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드(bar-code)와 같지만, 우리가 살아가며 마주하는 스캐너(scanner)인 '운'은 늘 변화하며 흐릅니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{disp_name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 시공명리의 지혜와 궁금증이 있으시면 언제든 <b>'초연 시공명리 연구소'</b>의 문을 두드려 주십시오.</p>
<p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
<div style='text-align: right; margin-top: 30px;'>
<span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
</div>
</div>"""

                report_1_full_html = f"""{cover_html}
<div class='report-page' style='page-break-before: avoid;'>
<div class='vip-inset-frame' style='border:2px solid #1A237E; box-sizing: border-box; padding: 20px; border-radius:15px; margin-top: 0;'>

<h1 style='text-align:center;'>🎯[초연 시공명리 사주풀이]</h1>
{table_html}
{master_bar_html}
<div style='margin-top:20px;'>
{{full_content_clean_placeholder}}
</div>
</div>
</div>"""

                jeolip_day = 5
                prev_wol_pillar = ""
                curr_wol_pillar = ""
                _, p1, _ = get_true_year_month_pillar(curr_y, curr_m, 1, 12, 0)
                for d in range(2, 12):
                    _, pd, _ = get_true_year_month_pillar(curr_y, curr_m, d, 12, 0)
                    if pd != p1:
                        jeolip_day = d
                        prev_wol_pillar = p1
                        curr_wol_pillar = pd
                        break
                if not curr_wol_pillar:
                    curr_wol_pillar = p1
                    prev_wol_pillar = p1

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

                ipchun_day = 4
                _, p1_feb, _ = get_true_year_month_pillar(curr_y, 2, 1, 12, 0)
                for d in range(2, 10):
                    _, pd_feb, _ = get_true_year_month_pillar(curr_y, 2, d, 12, 0)
                    if pd_feb != p1_feb:
                        ipchun_day = d
                        break

                soseo_day = 7
                _, p1_jul, _ = get_true_year_month_pillar(curr_y, 7, 1, 12, 0)
                for d in range(2, 12):
                    _, pd_jul, _ = get_true_year_month_pillar(curr_y, 7, d, 12, 0)
                    if pd_jul != p1_jul:
                        soseo_day = d
                        break

                next_ipchun_day = 4
                _, p1_next_feb, _ = get_true_year_month_pillar(curr_y + 1, 2, 1, 12, 0)
                for d in range(2, 10):
                    _, pd_next_feb, _ = get_true_year_month_pillar(curr_y + 1, 2, d, 12, 0)
                    if pd_next_feb != p1_next_feb:
                        next_ipchun_day = d
                        break

                sewun_first_half_date = f"{curr_y}.02.{ipchun_day:02d}(입춘) ~ {curr_y}.07.{soseo_day:02d}(소서 전)"
                sewun_second_half_date = f"{curr_y}.07.{soseo_day:02d}(소서) ~ {curr_y + 1}.02.{next_ipchun_day:02d}(입춘 전)"
                
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

                w_key = f"{ms}{mb}".strip()
                i_key = f"{ds}{db}".strip()

                w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
                i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
                struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
                s_name, s_type, s_desc = struct_data[0], struct_data[1], struct_data[2]

                choyeon_golden_text = f"""
<div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000; margin-bottom: 20px;'>
    <p style='text-indent: 15px; margin-bottom: 5px;'>
        <b>{disp_name}님</b>은 '{w_val}'의 시공간에서, '{i_val}'의 성품을 가지고 태어나셨습니다.
    </p>
</div>
"""
                dw_start_age = current_daewun_age
                dw_mid_age   = current_daewun_age + 4
                dw_mid2_age  = current_daewun_age + 5
                dw_end_age   = current_daewun_age + 9
                                
                db_header = (
                    f"[시스템 강제 시간 인식: 현재 시점은 {curr_y}년 {curr_m}월 입니다.]\n"
                    "당신은 명리심리상담사 1급 자격을 갖춘 초연 박사입니다. \n"
                    f"- 내담자 성함: {disp_name}\n"
                    f"- 나이 / 성별: {u_age}세 / {u_gender}\n"
                    f"- marital_status: {u_marital}\n"
                    f"- 타고난 심리 구조 팩트: {s_name} ({s_type} - {s_desc})\n"
                    f"- 실제 타격받는 공망 궁위 팩트: {gongmang_actual}\n"
                    f"- 올해({curr_y}년) 삼재 여부: {cur_samjae}\n"  
                    f"- 원국 내부 묘고(입고/개고) 작용: {won_guk_vaults_str}\n"
                    f"- 현재 행운(대/세/월운) 외부 충격에 의한 묘고 작용: {hang_un_vaults_str}\n"
                    f"🚨 [AI 환각 및 UI 파괴 원천 차단 절대 규칙]\n"
                    f"1. 서론 철저 금지: '안녕하십니까', '기쁩니다' 등의 인사말이나 감성적인 도입부를 절대로 작성하지 마십시오.\n"
                    f"2. 호칭 절대 규칙: 각 대목차의 첫 문장은 반드시 '{disp_name}님은~'으로 격식있게 시작하고, 그 이후 본문에서는 친근하게 '{disp_first_name}님은~'으로 부르십시오.\n"
                    f"3. 🚨 공망 소설 금지: 위 '실제 타격받는 공망 궁위 팩트'에 명시된 자리만 공망으로 해석하십시오. 명시되지 않은 자리(예: 일지가 없는데 일지 공망이라고 하는 등)가 비어있다고 소설을 쓰면 즉시 치명적 시스템 오류로 간주합니다!\n"
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
   - 미혼: '미래의 아내/인연'으로 칭할 것.
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
   - 미혼: '미래의 남편/인연'으로 칭할 것.
   - 🚨돌싱(이혼/사별): '과거의 인연(전 남편)'에 대한 성찰이나 '새로운 인연(재혼운)'으로 변환하여 카운슬링할 것.
"""

                def get_group_ss_local(ss_name):
                    if not ss_name or ss_name in ["?", "-", " "]: return "비겁"
                    if "비" in ss_name or "겁" in ss_name: return "비겁"
                    if "식" in ss_name or "상" in ss_name: return "식상"
                    if "재" in ss_name: return "재성"
                    if "관" in ss_name: return "관성"
                    if "인" in ss_name: return "인성"
                    return "비겁"

                def get_execution_yong_local(upper_group, lower_group):
                    matrix = {
                        '비겁': {'비겁':'비겁', '식상':'식상', '재성':'재성', '관성':'관성', '인성':'인성'},
                        '식상': {'비겁':'인성', '식상':'비겁', '재성':'식상', '관성':'재성', '인성':'관성'},
                        '재성': {'비겁':'관성', '식상':'인성', '재성':'비겁', '관성':'식상', '인성':'재성'},
                        '관성': {'비겁':'재성', '식상':'관성', '재성':'인성', '관성':'비겁', '인성':'식상'},
                        '인성': {'비겁':'식상', '식상':'재성', '재성':'관성', '관성':'인성', '인성':'비겁'}
                    }
                    return matrix.get(upper_group, {}).get(lower_group, '비겁')

                def get_matrix_keyword_local(che_group, yong_group, matrix_text):
                    target_str = f"- 체({che_group})+용({yong_group}):"
                    for line in matrix_text.splitlines():
                        if line.startswith(target_str):
                            return line.split(":", 1)[1].strip()
                    return "변화 감지"

                che_yong_matrix_text = """
- 체(비겁)+용(비겁): 식상발흥, 직무개척, 건강호조, 출산운, 처가와 유정
- 체(비겁)+용(식상): 업무원만, 진취력, 건강호조, 원행, 발표, 여행
- 체(비겁)+용(재성): 손재, 소비, 이성난, 가정불화, 부친반목
- 체(비겁)+용(관성): 설화, 관재, 가족불화, 직장문제, 공명심
- 체(비겁)+용(인성): 의식주안정, 스카우트, 계약, 학업순성, 합격, 가정화목
- 체(식상)+용(비겁): 사업원만, 결과만족, 명진, 의기투합, 긍정심
- 체(식상)+용(식상): 재성발흥, 재적성취, 이성운, 가정원만, 재물입고, 환대
- 체(식상)+용(재성): 이재순성, 사업원만, 인연, 가족화목, 건강, 횡재
- 체(식상)+용(관성): 건강악화, 직업불안, 직주이동, 관재, 설화, 가족불화
- 체(식상)+용(인성): 직업불안, 건강문제, 계약파기, 학문불안, 의식주 불안
- 체(재성)+용(비겁): 일득삼재, 손재, 부부갈등, 과소비, 업무지연
- 체(재성)+용(식상): 여행, 결과만족, 횡재수, 가정화목, 득자운
- 체(재성)+용(재성): 관성발흥, 직업운 상승, 이성운 순성, 가정원만
- 체(재성)+용(관성): 신분상승, 출마, 천거, 장기출장, 가정화목, 이성운
- 체(재성)+용(인성): 매사불성, 소비지출, 가족불화, 계약파기, 손재, 흉사
- 체(관성)+용(비겁): 업무지연, 관재, 설화, 다툼, 허언, 선민의식
- 체(관성)+용(식상): 명예훼손, 직업이동, 질책, 가족불화, 이성난
- 체(관성)+용(재성): 사업운 원만, 이성운 순성, 가정원만, 취업, 명예
- 체(관성)+용(관성): 인성발흥, 승진승급, 계약성사, 자식운 원만
- 체(관성)+용(인성): 합격, 승진, 계약, 스카우트, 의식주 안정, 당선
- 체(인성)+용(비겁): 건강호조, 학업원만, 신분상승, 당선, 명예, 안정
- 체(인성)+용(식상): 불안정, 계약파기, 학업불성, 구설, 육친흉사, 자식불효
- 체(인성)+용(재성): 지출, 탈재, 파재, 사기수, 손재, 분주다망, 시성종패
- 체(인성)+용(관성): 업무원활, 학업성취, 승진승급, 영전, 합격, 포상
- 체(인성)+용(인성): 비겁발흥, 명예, 명진, 칭찬, 주체성 확립, 학문성취
"""
                
                sewun_gan = curr_y_ganji[1][0] if len(curr_y_ganji[1]) > 0 else "-"
                sewun_ji = curr_y_ganji[1][1] if len(curr_y_ganji[1]) > 1 else "-"
                
                ilju_lower_group = get_group_ss_local(get_ss(ds, db)) 
                
                dw_che_group = get_group_ss_local(get_ss(ds, dw_g_cur)) 
                dw_upper_group = get_group_ss_local(get_ss(dw_g_cur, dw_j_cur))
                dw_yong = get_execution_yong_local(dw_upper_group, ilju_lower_group)
                dw_fact_keyword = get_matrix_keyword_local(dw_che_group, dw_yong, che_yong_matrix_text)
                dw_fact_str = f"체운(무대): {dw_che_group} / 용운(사건): {dw_yong} ➔ 도출 키워드: {dw_fact_keyword}"

                sewun_upper_group = get_group_ss_local(get_ss(sewun_gan, sewun_ji)) 
                sewun_yong = get_execution_yong_local(sewun_upper_group, ilju_lower_group)
                sewun_fact_keyword = get_matrix_keyword_local(dw_che_group, sewun_yong, che_yong_matrix_text)
                sewun_fact_str = f"체운(무대): {dw_che_group} / 용운(사건): {sewun_yong} ➔ 도출 키워드: {sewun_fact_keyword}"

                wol_upper_group = get_group_ss_local(get_ss(cur_wol_g, cur_wol_j))
                wol_yong = get_execution_yong_local(wol_upper_group, ilju_lower_group)
                sewun_che_for_wolwun = get_group_ss_local(get_ss(ds, sewun_gan)) 
                wol_fact_keyword = get_matrix_keyword_local(sewun_che_for_wolwun, wol_yong, che_yong_matrix_text)
                wol_fact_str = f"체운(무대): {sewun_che_for_wolwun} / 용운(사건): {wol_yong} ➔ 도출 키워드: {wol_fact_keyword}"

                try:
                    analysis_summary = "\n".join(get_universal_analysis(ds, mb, db, gans, jjis))
                except Exception:
                    analysis_summary = "- 사주 원국 지장간 및 인종법 분석 팩트"

                # -----------------------------------------------------------------------------
                # [김 집사 긴급 패치: AI 팩트 주입용 현재 운세 변수 매핑]
                # (※ 반드시 팩트 문자열 조립 '이전'에 변수가 정의되어야 에러가 안 납니다.)
                # -----------------------------------------------------------------------------
                current_daewun_ganji = f"{dw_g_cur}{dw_j_cur}"
                current_sewun_ganji = f"{GAN[(curr_y - 1984) % 10]}{JI[(curr_y - 1984) % 12]}"
                current_wolwun_ganji = curr_wol_pillar
                
                # -----------------------------------------------------------------------------
                # [만세력 초연사주 팩트 주입 로직] AI가 변명하지 못하도록 텍스트에 '명찰'을 달아줍니다.
                # -----------------------------------------------------------------------------
                # 1. 대운/세운/월운 팩트 텍스트 강제 조립 
                dw_fact_str = f"[제공 팩트: 대운 간지 {current_daewun_ganji} / 십성: {get_ss(ds, current_daewun_ganji[0])},{get_ss(ds, current_daewun_ganji[1])} / 12운성: {get_unsung(ds, current_daewun_ganji[1])}]"
                sewun_fact_str = f"[제공 팩트: 세운 간지 {current_sewun_ganji} / 십성: {get_ss(ds, current_sewun_ganji[0])},{get_ss(ds, current_sewun_ganji[1])} / 12운성: {get_unsung(ds, current_sewun_ganji[1])}]"
                wolwun_fact_str = f"[제공 팩트: 월운 간지 {current_wolwun_ganji} / 십성: {get_ss(ds, current_wolwun_ganji[0])},{get_ss(ds, current_wolwun_ganji[1])} / 12운성: {get_unsung(ds, current_wolwun_ganji[1])}]"

                # 2. 프롬프트에 들어갈 변수들은 화면 출력용이므로 깔끔하게 나이/날짜만 남깁니다.
                dw_start_age_str = f"{dw_start_age}세~{dw_mid_age}세"
                dw_mid2_age_str = f"{dw_mid2_age}세~{dw_end_age}세"
                sewun_first_half_date_str = f"{sewun_first_half_date}"
                sewun_second_half_date_str = f"{sewun_second_half_date}"
                prompt_first_half_str = f"{prompt_first_half}"
                prompt_second_half_str = f"{prompt_second_half}"
                # -----------------------------------------------------------------------------
                
                # 1. 내담자의 월주/일주 키워드 조립
                wol_keyword = f"{ds}{mb}" # 예: 甲子 (일간+월지)
                ilju_keyword = f"{ds}{db}" # 예: 乙丑 (일간+일지)

                # 2. JSON DB에서 깔끔하게 데이터 빼오기
                wolryeong_fact = choyeon_db.get("wolryeong", {}).get(wol_keyword, "월령 정보가 없습니다.")
                ilju_fact = choyeon_db.get("ilju", {}).get(ilju_keyword, "일주 자의형상 정보가 없습니다.")
                
                # (만약 일주 구조 리스트가 필요하시다면 아래처럼 빼옵니다)
                # structure_list = choyeon_db.get("ilju_structure", {}).get(ilju_keyword, ["", "", ""])

                prompt = f"""
{db_header}

[1. 내담자 맞춤형 통변 톤앤매너]
- {age_prompt}
- 위 연령대와 타겟팅에 맞추어, 뻔한 사주 용어를 버리고 내담자가 100% 공감할 수 있는 현대적이고 다정한 에세이 문체로 작성하십시오.

[2. 육친 및 관계 해석 절대 규칙]
{yukchin_rule}
- 위 규칙을 각 목차(결혼·자녀운, 재성운, 사업운, 관직운 등)에 엄격하게 적용하여 서술하십시오. 성별에 어긋난 육친 해석은 치명적 오류입니다.

[3. 시공명리 폭포수 에세이 작성 규칙]
- [체운]이라는 무대와 [용운]이라는 사건이 만날 때 일어나는 감정의 파동을 묘사하십시오.
- {dw_fact_keyword} 등 도출된 키워드는 문장의 마침표가 아니라, 운의 흐름을 설명하는 '재료'로 사용하여 문장에 자연스럽게 녹여내십시오.
- 60월령('{w_val}')과 일주('{i_val}')의 자의형상을 활용하여, 내담자가 서 있는 시공간의 풍경을 한 편의 시처럼 묘사하십시오.

[4. 기초 팩트 데이터]
- 사주 정보: {ys}{yb}년, {ms}{mb}월, {ds}{db}일, {hs}{hb}시
- 격국: {gyukgook_detail} / 12신살: {s12_str} / 일반신살: {shinsal_str} 
- 시공명리 팩트: {dw_fact_str}, {sewun_fact_str}, {wol_fact_str}

[분석 지시 사항]
- 너는 내담자의 일주를 바탕으로 일지의 지장간(여기, 중기, 정기)을 스스로 도출하라.
- 도출한 각 지장간의 십성과 12운성 좌법을 바탕으로 에세이를 작성하라.
- 괄호 안의 데이터는 반드시 AI가 스스로 계산한 결과값을 텍스트로 기입하라.

[초연명리 상담가 시스템 지침: 범용 버전]

1. [데이터 호출 및 연산]:
   - 입력된 일주를 확인하고 해당 일주의 지장간(여기, 중기, 정기)을 파악하라.
   - 각 지장간의 [십성]과 [12운성 좌법]을 대입하여, 그 일주가 가진 본질적 성향을 도출하라.
   - 원국에 없는 오행은 12운성 종법(인종법)을 적용하여, 그 오행의 십성이 내면에서 어떤 갈망으로 작용하는지 도출하라.
   - 공망은 제공된 팩트 데이터에서 해당 궁위를 찾아, 그곳이 의미하는 현실적 결핍만을 간결하게 설명하라.

2. [범용 서술 알고리즘]:
   - 나열 금지: 신살을 무분별하게 나열하지 말고, 상담의 핵심이 되는 1~2개만 서술하라.
   - 명리적 인과 서술: "절좌(絶坐)에 놓인 정관은 직주의 이동이 잦지만 암합을 통해 근면함을 보인다"와 같이 [좌법의 명리적 근거] -> [현상] 순으로 서술하라.
   - 팩트 검증 병기: 통변 문단의 끝에 반드시 해당 십성의 좌법/종법을 괄호로 명시하라. (예: 정관/절좌/왕궁)

3. [데이터 구조 활용]:
   - 모든 통변은 {지장간1}, {지장간2}, {지장간3} 순서로 서술하며, 각각의 십성이 12운성 궁성에서 어떻게 발현되는지 논리적으로 연결하라.
   - 인종법 역시 마찬가지로, 사주에 없는 오행이 종법을 통해 원국을 어떻게 보완하거나 결핍을 만드는지 기술하라.

[출력 HTML 템플릿]
(※ 아래의 HTML 구조를 100% 그대로 유지하면서, 각 항목의 해설 부분만 지시에 맞춰 작성하십시오.)

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>1. 사주팔자 구조 분석</h3>
<div class='content-box-loose'>
[CHOYEON_GOLDEN_TEXT_HERE]

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 내 삶의 무대와 타고난 기본 성향</span>
(격국을 중심으로 일간이 7궁위 무대에서 어떤 에너지로 발현되는지 서술)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 내 삶의 리듬과 에너지 균형</span>
(오행, 조후, 억부 균형 분석 및 현실 처방)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 내 삶의 역동성과 상호작용</span>
(합충파해 연쇄반응, 묘고 작용, 격각의 이동과 고독을 서술)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>4) 내 삶의 숨겨진 강점과 잠재적 에너지</span>
(신살과 삼재를 강점으로 재해석)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>2. 성격 및 가치관</h3>
<div class='content-box-loose'>
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 겉으로 드러난 성격</span>
    <p style='margin-bottom: 12px; text-indent: 15px;'>
        {disp_name}님은 일간 {ds}의 물상을 바탕으로, 타고난 기질과 사회적 환경이 어우러져 {disp_name}님만의 고유한 페르소나를 형성합니다. 
        일지 지장간에 숨겨진 세 기운을 스스로 도출하여 각 기운의 좌법을 분석하고, 그 결과를 괄호 속에 데이터로 기입하라.
    </p>

    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111; display: block; margin-top: 20px;'>2) 감추어진 내 속마음</span>
    <p style='margin-bottom: 12px; text-indent: 15px;'>
    겉으로 드러난 활기찬 모습 이면에 {disp_name}님은 스스로도 잘 인지하지 못하는 내면의 갈망을 품고 계십니다. 
    원국에서 인종한 오행의 에너지와 비어있는 공망의 영역은 삶의 무대 위에서 미처 다 펼치지 못한 {disp_name}님의 깊은 속마음을 대변합니다. <b>(AI가 스스로 인종법 및 공망 분석 결과를 이곳에 서술하고 팩트를 괄호로 병기하시오)</b>
    </p>
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>3. 부모·형제운</h3><div class='content-box-loose'>
(년/월주의 십성과 {yukchin_rule}을 적용하여, 부모형제로부터 받은 심리적 자양분과 현실적 인연을 에세이 형식으로 서술)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>4. 학업·진학운</h3><div class='content-box-loose'>
(인성, 식상, 관성의 상호작용을 통해 지식을 습득하고 활용하는 성향 서술)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>5. 적성·직업운</h3><div class='content-box-loose'>
(원국의 주력 에너지를 분석하여, 가장 잘 어울리는 구체적 직업 물상과 사회적 역할 제시)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>6. 결혼·자녀운</h3><div class='content-box-loose'>
(🚨AI 필수: [2. 육친 절대 규칙]의 '핵심 가족' 및 '상태별 호칭'을 100% 반영하여 서술할 것)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>7. 재성운</h3><div class='content-box-loose'>
(식상생재 흐름과 재물 성취 방향을 서술하되, 남명일 경우 재물을 '연애/아내운'과 유기적으로 연결하여 묘사)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>8. 사업운</h3><div class='content-box-loose'>
(비겁의 독립성과 식상의 창조성을 바탕으로 한 창업/확장성의 득실 서술)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>9. 관직·명예운</h3><div class='content-box-loose'>
(관인상생 및 사회적 책임감을 서술하되, 여명일 경우 직장/명예운을 '남편/배우자운'의 동태와 연결하여 묘사)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>10. 건강운</h3><div class='content-box-loose'>
(오행의 불균형을 파악하여 취약 신체 질환을 경고하고, [1. 맞춤형 톤앤매너]에 맞춰 연령대에 맞는 건강 관리법 조언)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>11. 운의 흐름</h3>
<div class='content-box-loose'>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 대운의 흐름</span>
[DAEWUN_TABLE_HERE]

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 대운 분석</span>
{past_daewun_html}
[과거 대운 출력 템플릿]
(※ 🚨AI 지시: 위 데이터들을 빠짐없이 각각 아래 HTML 구조로 요약 작성. 변명/생략 금지.)
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 0px;'><b>1) 전통 명리 풀이:</b> (전통 관점 1~2문장 핵심 요약)</div>
    <div><b>2) 시공 명리 풀이:</b> (체용 매트릭스 관점 간략 요약)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 현재 {current_daewun_ganji}대운 전반기 상세 분석 ({dw_start_age_str})</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> (운의 환경 변화, 성취와 심리, 현실적 삶의 영역, 조언을 상세히 서술)</div>
    <div><b>2) 시공 명리 풀이:</b> (🚨지침: {dw_fact_str} 팩트 데이터를 체/용으로 엄격히 분리하여 폭포수처럼 기술)
        <p><b>[체운(體運): 환경의 본질]</b> {current_daewun_ganji}가 사주 원국에서 시공간을 어떻게 점유하는지 본질적 에너지 상태 서술.</p>
        <p><b>[용운(用運): 현상의 작용]</b> 본질적 체운이 현실의 삶에서 어떤 십성적/신살적 작용으로 표출되는지 구체적 발현 방식 서술.</p>
    </div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 현재 {current_daewun_ganji}대운 후반기 상세 분석 ({dw_mid2_age_str})</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> (운의 환경 변화, 성취와 심리, 현실적 삶의 영역, 조언을 상세히 서술)</div>
    <div><b>2) 시공 명리 풀이:</b> (🚨지침: {dw_fact_str} 팩트 데이터를 체/용으로 엄격히 분리하여 폭포수처럼 기술)
        <p><b>[체운(體運): 환경의 본질]</b> {current_daewun_ganji}가 사주 원국에서 시공간을 어떻게 점유하는지 본질적 에너지 상태 서술.</p>
        <p><b>[용운(用運): 현상의 작용]</b> 본질적 체운이 현실의 삶에서 어떤 십성적/신살적 작용으로 표출되는지 구체적 발현 방식 서술.</p>
    </div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 세운의 흐름</span>
[SEWUN_TABLE_HERE]

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 세운 분석</span>
{past_sewun_html}
[과거 세운 출력 템플릿]
(※ 🚨AI 지시: 위 데이터들을 빠짐없이 각각 아래 HTML 구조로 요약 작성. 변명/생략 금지.)
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 0px;'><b>1) 전통 명리 풀이:</b> (전통 관점 1~2문장 핵심 요약)</div>
    <div><b>2) 시공 명리 풀이:</b> (체용 매트릭스 관점 간략 요약)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 올해 세운 전반기 상세 분석 ({sewun_first_half_date_str})</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> 올해 상반기 운의 흐름, 기회와 리스크, 행동 지침 서술.</div>
    <div><b>2) 시공 명리 풀이:</b> (🚨지침: {sewun_fact_str} 팩트 데이터 기반 상세 서술)
        <p><b>[체운(體運): 환경의 본질]</b> {current_sewun_ganji}년 상반기 천간 에너지가 주는 본질적 흐름 서술.</p>
        <p><b>[용운(用運): 현상의 작용]</b> 상반기에 발생하는 구체적 현실 변화와 대처 방안 서술.</p>
    </div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 올해 세운 후반기 상세 분석 ({sewun_second_half_date_str})</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> 하반기 운의 결실과 주의사항, 마무리를 위한 전략 서술.</div>
    <div><b>2) 시공 명리 풀이:</b> (🚨지침: {sewun_fact_str} 팩트 데이터 기반 상세 서술)
        <p><b>[체운(體運): 환경의 본질]</b> {current_sewun_ganji}년 하반기 지지 에너지가 주는 환경적 특성 서술.</p>
        <p><b>[용운(用運): 현상의 작용]</b> 하반기에 나타나는 실질적 성과와 구체적 대응 서술.</p>
    </div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 월운의 흐름</span>
[WOLWUN_TABLE_HERE]

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 월운 분석</span>
{past_months_html}
[과거 월운 출력 템플릿]
(※ 🚨AI 지시: 위 데이터들을 빠짐없이 각각 아래 HTML 구조로 요약 작성. 변명/생략 금지.)
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 0px;'><b>1) 전통 명리 풀이:</b> (전통 관점 1~2문장 핵심 요약)</div>
    <div><b>2) 시공 명리 풀이:</b> (목차의 [팩트: 체운/용운/도출 키워드]를 바탕으로 시공명리 관점에서 상세 서술)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ {prompt_first_half_str}</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> 이번 달 상반기 변곡점, 집중해야 할 이슈와 행동 지침 서술.</div>
    <div><b>2) 시공 명리 풀이:</b> (🚨지침: {wolwun_fact_str} 팩트 데이터 기반 상세 서술)
        <p><b>[체운(體運): 환경의 본질]</b> 금월 상반기 에너지가 갖는 본질적 성격과 흐름 서술.</p>
        <p><b>[용운(用運): 현상의 작용]</b> 상반기에 발생할 구체적 사건과 실천적 지침 서술.</p>
    </div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ {prompt_second_half_str}</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> 이번 달 하반기 마무리, 성과 관리 및 다음 달 대비 조언 서술.</div>
    <div><b>2) 시공 명리 풀이:</b> (🚨지침: {wolwun_fact_str} 팩트 데이터 기반 상세 서술)
        <p><b>[체운(體運): 환경의 본질]</b> 금월 하반기 에너지가 갖는 본질적 의미 서술.</p>
        <p><b>[용운(用運): 현상의 작용]</b> 하반기에 취해야 할 실질적 행동과 결과물 관리 서술.</p>
    </div>
</div>
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>12. 삶을 바꾸는 지혜로운 조언</h3>
<div class='content-box-loose'>
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 나를 돕는 에너지와 색상:</span>
(작성)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 신체 밸런스와 에너지 관리:</span>
(작성)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 공간의 흐름과 방위의 지혜:</span>
(작성)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 재능 효율을 높이는 직업적 지혜:</span>
(작성)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 더 나은 내일을 위한 절제의 미학:</span>
(작성)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'> 🎯 특별 개운 비법</h3>
<div class='content-box-loose'>
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 수호 천사의 기운 조언:</span>
(천을귀인 등 길신 작용 서술)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 백년해로의 기운 조언:</span>
(연인/부부 갈등 극복 및 실질적 마음가짐 조언 - 전문 용어 철저히 배제)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 행운에 따른 기운 조언:</span>
(입고/개고, 역동성에 따른 재물/대인관계 주의점 서술)
</div>
"""
                try:
                    ai_text = call_gemini_api(prompt)
                    ai_text = "\n".join([line.lstrip() for line in ai_text.split("\n")])
                    
                    div_start = "<div class='content-box-loose'>"
                    target_sub = "1) 내 삶의 무대와 타고난 기본 성향"
                    
                    if target_sub in ai_text and div_start in ai_text:
                        parts = ai_text.split(target_sub)
                        top_clean = parts[0][:parts[0].find(div_start) + len(div_start)]
                        ai_text = top_clean + f"\n{choyeon_golden_text}\n<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>{target_sub}" + parts[1]
                    elif "[CHOYEON_GOLDEN_TEXT_HERE]" in ai_text:
                        ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)

                    un_html_clean = un_html.replace("\n", " ").replace("\r", "")
                    se_html_clean = se_html.replace("\n", " ").replace("\r", "")
                    wol_html_clean = wol_html.replace("\n", " ").replace("\r", "")

                    clean_ai_text = ai_text

                    daeoun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{un_html_clean}</div>"
                    sewun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{se_html_clean}</div>"
                    wolwun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{wol_html_clean}</div>"

                    clean_ai_text, count_d = re.subn(r'[\#\*\_\s]*\[\s*DAEWUN_TABLE_HERE\s*\][\#\*\_\s]*', daeoun_target, clean_ai_text, flags=re.IGNORECASE)
                    clean_ai_text, count_s = re.subn(r'[\#\*\_\s]*\[\s*SEWUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                    clean_ai_text, count_w = re.subn(r'[\#\*\_\s]*\[\s*WOLWUN_TABLE_HERE\s*\][\#\*\_\s]*', wolwun_target, clean_ai_text, flags=re.IGNORECASE)

                    if count_d == 0 and "table" not in clean_ai_text.lower():
                        clean_ai_text = clean_ai_text + f"<br><br><span style='color:red; font-weight:bold;'>⚠️ (AI 표 마커 누락으로 비상 출력된 운의 흐름표)</span><br>{un_html_clean}{se_html_clean}{wol_html_clean}"

                    full_content_clean = f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000;'>{clean_ai_text}<br><br>{closing_html}</div>"

                    report_1_full_html = report_1_full_html.replace("{full_content_clean_placeholder}", full_content_clean)
                    st.session_state['saved_report_html'] = report_1_full_html
                    
                except Exception as e: 
                    st.error(f"AI 연산 오류: {e}")

            # ------------------------------------------------------------------
            # [2단계] 타 감명서 비교분석
            # ------------------------------------------------------------------
            if u_product == "타 감명서":
                try:
                    report_2_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#555;'><h2 style='text-align:center; color:#555; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; margin-bottom:20px;'>📜 타 감명서 원문</h2><div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #111; text-align: justify; word-break: keep-all;'>{other_reading_text.replace(chr(10), '<br>')}</div></div></div>"

                    other_cover_html = (
                        f"<div class='page-break-before'></div>\n"
                        f"<div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>\n"
                        f"    <div style='border: 4px solid #2E7D32; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>\n"
                        f"        <div style='border-bottom:4px double #2E7D32; padding-bottom:20px; margin-bottom:40px;'>\n"
                        f"            <h1 style='font-size: 40px !important; color: #1A237E !important; font-weight: 900 !important; margin:0 !important; font-family: \"Malgun Gothic\", sans-serif !important;'>초연 시공명리 타 감명서 비교</h1>\n"
                        f"            <div style='text-align: right; margin-top: 10px;'><span style='font-size: 14px; color: #555; font-weight: 600; letter-spacing: 1px;'>{APP_VERSION}</span></div>\n"
                        f"        </div>\n"
                        f"        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>\n"
                        f"            <h2 style='font-size: 24px; font-weight: 800; color: #2E7D32; margin-bottom: 20px;'>👤 신청인 : {u_name} 님</h2>\n"
                        f"            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'><p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p></div>\n"
                        f"        </div>\n"
                        f"        <p style='font-size: 18px; margin-top: 50px; font-weight: 800;'>{today_str}</p>\n"
                        f"        <p style='font-size: 22px; font-weight: 800; color: #2E7D32; margin-top: 20px;'>초연 시공명리 연구소</p>\n"
                        f"    </div>\n"
                        f"</div>"
                    )

                    comp_prompt = f"""
    당신은 명리심리상담사 '초연 박사'를 보조하는 수석 분석관입니다.
    아래 [데이터]를 바탕으로 [초연 사주풀이]와 [타 감명서]를 1:1 대조 분석하십시오.

    🚨 [디자인 및 서식 절대 규칙]
    0. 🚨 [인사말 원천 차단]: 출력의 첫 글자는 반드시 <h3 style=...> 태그로 시작할 것.
    1. AI 임의의 목차 서식 생성을 절대 금지합니다.
    2. 목차 제목 출력 시, 반드시 명시된 태그 서식을 그대로 출력하십시오.
    3. 모든 본문 단락은 <p style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'> 로 감싸십시오.

    🚨 [내용 집중 대조 규칙]
    - 각 비교 항목의 도입부에는 반드시 [타 감명서 관점] vs [초연 시공명리 관점]을 1줄 요약으로 먼저 제시하십시오.
    - 타 감명서 원문이 다루고 있는 핵심 주제에 대해서만 초연 명리와 1:1 대조하십시오.
    - 🚨 [13번 총평 작성 지침]: 본문 분석과 별개로 반드시 500자 이상의 분량을 확보하여, 두 해석의 차이 발생 원인(정보 인지 여부, 해석 관점의 차이)을 명확히 규명하고 향후 초연 명리가 취해야 할 통변 전략을 제시하십시오.

    [데이터]
    - 사주 팩트: {gans}{jjis}
    - [1. 초연 사주풀이]: {full_content_clean}
    - [2. 타 감명서]: {other_reading_text}
    """
                    c_res = get_ai_response(comp_prompt, model_name='gemini-2.5-flash')
                    st.session_state['saved_report_2'] = other_cover_html + report_2_html + f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#2E7D32;'><h1 style='text-align:center; color:#2E7D32; font-size: 26px; font-weight: 800; border-bottom:2px solid #2E7D32; padding-bottom:15px;'>⚖️ 1:1 상세비교 본문 리포트</h1><div style='margin-top:20px;'>{c_res}</div></div></div>"

                except Exception as e:
                    st.error(f"2단계 비교 분석 중 오류 발생: {e}")

            # ------------------------------------------------------------------
            # [2.5 단계] 궁합 타 감명서 비교분석 (선택적 가동 모듈)
            # ------------------------------------------------------------------
            if u_product == "궁합" and st.session_state.get('run_comp_mode'):
                try:
                    comp_prompt = f"""
    당신은 명리심리상담사 '초연 박사'를 보조하는 수석 분석관입니다.
    [1. 초연 궁합 분석]과 [2. 타 감명서]를 1:1 대조 분석하십시오.
    
    [데이터]
    - 신청인(명주1) 사주: {full_content_clean}
    - 상대방(명주2) 사주: {partner_content_clean}
    - 타 감명서 원문: {st.session_state.get('other_reading_text')}
    """
                    c_res = get_ai_response(comp_prompt, model_name='gemini-2.5-flash')
                    st.session_state['saved_report_gh_comp'] = f"<div class='report-page'><div class='vip-inset-frame' style='border-color:#2E7D32;'><h1 style='text-align:center;'>⚖️ 궁합 1:1 상세비교 리포트</h1>{c_res}</div></div>"
                except Exception as e:
                    st.error(f"궁합 비교 분석 중 오류: {e}")

            # ==================================================================
            # 💕 [3단계] 궁합 풀이
            # ==================================================================
            if u_product == "궁합":
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
                    st.session_state['partner_bazi'] = partner_bazi # 🚨 출산택일 연산을 위해 영구 저장

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
                            cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(t_jjis[r_idx], t_jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:none !important; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+t_jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(t_jjis[r_idx], t_jjis[ci]))}</td>" for ci in range(4)])
                            lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important;'>합충형파해</td>" if l_idx==0 else ""
                            ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

                        info_str = f"<div style='text-align:center; margin-bottom:15px; font-family:\"Malgun Gothic\", sans-serif;'><span style='font-size:18px; font-weight:900; color:#1A237E;'>{gender_icon} {name}님 ({gender_str}, {marital_str}, {age}세)</span><br><span style='font-size:14px; font-weight:900; color:#222;'>[양력] {sol} | [음력] {lun}{time}</span></div>"
                        
                        def td(c):
                            bg_style = "background-color: white;" if c in ['?',' ','-'] else ""
                            return f"<td class='color-{get_color(c)}' style='{bg_style} font-size:20px; font-weight:900; border:1px solid #444 !important;'>{('?' if c in ['?',' ','-'] else c)}</td>"

                        return (
                            f"{info_str}\n"
                            f"<table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>\n"
                            f"<tr class='top-header-cell'>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>구분</td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>시주</td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>일주</td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>월주</td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>년주</td>\n"
                            f"</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_gans[0])}</td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(t_ds,t_gans[2])}</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_gans[3])}</td></tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>천간</td>{td(t_gans[0])}{td(t_gans[1])}{td(t_gans[2])}{td(t_gans[3])}</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>지지</td>{td(t_jjis[0])}{td(t_jjis[1])}{td(t_jjis[2])}{td(t_jjis[3])}</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_jjis[0])}</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_jjis[1])}</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_jjis[2])}</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_jjis[3])}</td></tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; padding:0; font-size:15px !important; white-space:nowrap;'>지장간</td>{''.join([f'<td style=\"border:1px solid #444; padding:0;\">{get_jijanggan_full(t_ds, t_jjis[i])}</td>' for i in range(4)])}</tr>\n"
                            f"{ji_rel_rows}\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>십이운성</td>{''.join([f'<td style=\"border:1px solid #444; color:#0D47A1; font-weight:bold;\">{get_unsung(t_ds, t_jjis[i])}</td>' for i in range(4)])}</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>십이신살</td>{''.join([f'<td style=\"border:1px solid #444; color:#C62828; font-weight:bold;\">{get_12_shinsal(t_yb, t_jjis[i])}</td>' for i in range(4)])}</tr>\n"
                            f"</table>\n"
                            f"<div style='border:2px solid {color}; margin-top:10px; margin-bottom:20px; padding:6px 8px; display:flex; justify-content:space-between; align-items:center; font-weight:900; font-size:11px; letter-spacing:-0.5px; border-radius:8px; background-color:#FAFAFA;'><div style='white-space:nowrap;'>🔢 대운수: {daeun_su}</div><div style='white-space:nowrap;'>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div style='white-space:nowrap;'>🌟 천을귀인: <span style='color:{color};'>{guiin}</span></div><div style='white-space:nowrap;'>🎯 공망: [년] <span style='color:#C62828;'>{y_gong}</span> [일] <span style='color:#C62828;'>{d_gong}</span></div><div style='white-space:nowrap;'>🌪️ 삼재: {samjae}</div></div>"
                        )

                    m_marital = u_marital if u_gender == "남성" else p_marital
                    f_marital = p_marital if u_gender == "남성" else u_marital
                    
                    guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 단','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
                    
                    m_tbl = build_bazi_table("♂️", m_name, "남명", m_marital, m_age, m_sol, m_lun, m_time, m_gans, m_jjis, m_ds, m_yb, m_cnt, guiin_map.get(m_ds, '-'), calculate_gongmang(m_ys, m_yb), calculate_gongmang(m_ds, m_db), get_samjae(m_yb, curr_j), m_calc_d, "#1A237E")
                    f_tbl = build_bazi_table("♀️", f_name, "여명", f_marital, f_age, f_sol, f_lun, f_time, f_gans, f_jjis, f_ds, f_yb, f_cnt, guiin_map.get(f_ds, '-'), calculate_gongmang(f_ys, f_yb), calculate_gongmang(f_ds, f_db), get_samjae(f_yb, curr_j), f_calc_d, "#D50000")
                    
                    def build_daewun_html(name, t_ds, t_ms, t_mb, t_yb, t_calc_d, t_order, age, color):
                        d_str = "순행" if t_order == 1 else "역행"
                        html = f"<div style='margin-bottom:10px;'><div style='font-size:15px; font-weight:900; color:#1A237E; margin-bottom:5px;'>[ {name}님 대운 흐름표 (대운수: {t_calc_d}), {d_str} ]</div>"
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
                    f_page_un_html = build_daewun_html(f_name, f_ds, f_ms, f_mb, f_yb, f_calc_d, f_order, f_age, "#1A237E")
                    
                    couple_daewun_tables = f"<div style='margin-bottom: 25px;'>{m_page_un_html}<div style='height:20px;'></div>{f_page_un_html}</div>"

                    m_w_val = choyeon_db.get("wolryeong", {}).get(m_ms+m_mb, "시공간 데이터 없음")
                    m_i_val = choyeon_db.get("ilju", {}).get(m_ds+m_db, "성품 데이터 없음")
                    # 🚨 [수술 적용 1] 골든 텍스트 여백을 개인사주와 동일하게 세팅
                    m_golden = f"<p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'><b>{m_name}님</b>은 '{m_w_val}'의 시공간에서, '{m_i_val}'의 성품을 지녔습니다.</p>"

                    f_w_val = choyeon_db.get("wolryeong", {}).get(f_ms+f_mb, "시공간 데이터 없음")
                    f_i_val = choyeon_db.get("ilju", {}).get(f_ds+f_db, "성품 데이터 없음")
                    f_golden = f"<p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'><b>{f_name}님</b>은 '{f_w_val}'의 시공간에서, '{f_i_val}'의 성품을 지녔습니다.</p>"
                    
                    gh_engine = UniversalPrintableGunghap(u_name, p_name, male_data_pack, female_data_pack, 10)
                    gh_engine.run_universal_logic()

                    # 🚨 [신규 수술 1] 파이썬에서 연산된 디테일 정보를 AI에게 넘길 '절대 맵핑표' 생성
                    m_y_gong = calculate_gongmang(m_ys, m_yb)
                    m_d_gong = calculate_gongmang(m_ds, m_db)
                    m_gongmang_actual = f"년주공망:{m_y_gong}, 일주공망:{m_d_gong}"
                    
                    f_y_gong = calculate_gongmang(f_ys, f_yb)
                    f_d_gong = calculate_gongmang(f_ds, f_db)
                    f_gongmang_actual = f"년주공망:{f_y_gong}, 일주공망:{f_d_gong}"

                    ai_saju_mapping = f"""
========================================================
[의뢰인 명식표 - 🚨 절대 위치 엄수 / 데이터 혼동 금지 🚨]
========================================================
■ ♂️ 남성({m_name}) 명식 데이터
* 년주(年柱) : {m_ys}{m_yb}
* 월주(月柱) : {m_ms}{m_mb}
* 일주(日柱, 본원) : {m_ds}{m_db}  <-- 남성 통변의 절대 기준점!
* 시주(時柱) : {m_hs}{m_hb}
* 공망: {m_gongmang_actual}

■ ♀️ 여성({f_name}) 명식 데이터
* 년주(年柱) : {f_ys}{f_yb}
* 월주(月柱) : {f_ms}{f_mb}
* 일주(日柱, 본원) : {f_ds}{f_db}  <-- 여성 통변의 절대 기준점!
* 시주(時柱) : {f_hs}{f_hb}
* 공망: {f_gongmang_actual}
========================================================
"""
                    # 🚨 [최종 수술] 궁합 모듈 내 '육친 규칙' 및 '상태별 호칭' 통합
                    gender_rules = yukchin_rule if u_gender == '남성' else yukchin_rule # 이 로직을 프롬프트 안에 직접 삽입합니다.
                    
                    # 🚨 [궁합 분량 대확장] 총 8페이지 규격 (남명 2도, 여명 2도, 종합궁합 4도 강제 분할)
                    essay_prompt = f"""[SYSTEM ROLE: CHOYEON SIGONG MASTER]
당신은 명리심리상담사 '초연 박사'입니다.
남성 의뢰인({m_name}, {m_age}세)과 여성 의뢰인({f_name}, {f_age}세)의 궁합을 연령의 눈 높이에 마추어 현대적 구어체로 통변하십시오.

{db_header}
{ai_saju_mapping}
{yukchin_rule}

🚨 [용어 사용 엄격 준수 규칙 - 최우선 순위!]
1. [금지어]: '임관'이라는 용어는 사주 통변에 절대 사용 금지. (무조건 '건록'으로 치환할 것.)
2. [표준 용어 체계]: 12운성 및 좌법 표기는 반드시 '건록', '장생', '록좌생궁', '생좌생궁', '병궁', '태궁' 등의 박사님 고유 용어를 사용하십시오.
3. [괄호 표기법]: 모든 명리 용어(십성, 12운성, 좌법/인종법 등)는 반드시 '쉬운 우리말 설명 (명리 용어)' 형태로 표기하여 2030세대의 가독성을 극대화하십시오.

🚨 [출력 절대 형식 및 내용 생성 규칙 - 매우 중요!]
1. 남성 풀이([MALE_START]~[MALE_END])와 여성 풀이([FEMALE_START]~[FEMALE_END])는 인쇄 기준 각각 '정확히 2페이지' 분량이 나와야 합니다.
2. 종합 궁합 풀이([GUNGHAP_START]~[GUNGHAP_END])는 '정확히 4페이지' 분량으로 확장되어야 합니다.
3. 🚨 [문단 간격 강제]: 모든 통변 문단은 반드시 HTML 태그 <p style='text-indent: 15px; margin-top: 0px; margin-bottom: 12px; font-size: 14.5px; line-height: 1.8;'> 로 감싸십시오.
4. 🚨 [시스템 마커 절대 보존]: [MALE_START], [MALE_END], [FEMALE_START], [FEMALE_END], [GUNGHAP_START], [GUNGHAP_END], [COUPLE_DAEWUN_TABLES_HERE] 태그를 절대 변형하지 마십시오.
5. 🚨 [연령 맞춤형 Tone & Manner]: 의뢰인의 나이와 상태에 맞춰 스스로 톤을 결정하십시오.

[MALE_START]
<h3 style='color:#1A237E; font-size: 24px; font-weight: 900; margin-top: 15px;'>[남명(男命) 사주 분석]</h3>
<p><b>[일주(日柱): {m_ds}{m_db}]</b></p>
{m_golden}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(격국({calc_gyukgook})을 중심으로, 7궁위에서의 에너지 발현을 현실적으로 서술)

<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>2) 겉으로 드러난 성격 (일지 지장간 좌법)</span>
(일간 {m_ds} 기준, 일지 {m_db} 지장간의 초기-중기-여기 순서로 분석)
- 형식: ▪ [성분명] : "현대적 구어체 비유 (십성명 + 십이운성 + '좌' + 십이운성 + '궁')"

<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>3) 감추어진 내 속마음 (인종법 및 공망)</span>
(원국에 없는 결핍 십성을 일지로 인종하여 분석)
- 형식: ▪ [십성명] : "무의식적 갈망에 대한 구어체 풀이 (십성명 + 십이운성 + '종' + 십이운성 + '궁')"
- 공망({m_gongmang_actual})의 현실적 영향 서술.
[MALE_END]

[FEMALE_START]
<h3 style='color:#D50000; font-size: 24px; font-weight: 900; margin-top: 15px;'>[여명(女命) 사주 분석]</h3>
<p><b>[일주(日柱): {f_ds}{f_db}]</b></p>
{f_golden}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(격국({calc_gyukgook})을 중심으로, 7궁위에서의 에너지 발현을 현실적으로 서술)

<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>2) 겉으로 드러난 성격 (일지 지장간 좌법)</span>
(일간 {f_ds} 기준, 일지 {f_db} 지장간의 초기-중기-여기 순서로 분석)
- 형식: ▪ [성분명] : "현대적 구어체 비유 (십성명 + 십이운성 + '좌' + 십이운성 + '궁')" 

<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>3) 감추어진 내 속마음 (인종법 및 공망)</span>
(원국에 없는 결핍 십성을 일지로 인종하여 분석)
- 형식: ▪ [십성명] : "무의식적 갈망에 대한 구어체 풀이 (십성명 + 십이운성 + '종' + 십이운성 + '궁')"
- 공망({f_gongmang_actual})의 현실적 영향 서술.
[FEMALE_END]

[GUNGHAP_START]
<h3 style='color: #1B5E20; font-size: 24px; font-weight: 900; margin-top: 15px;'>🍀 두 사람의 운명적 만남 총평</h3>
(남성 일주 '{m_ds}{m_db}'와 여성 일주 '{f_ds}{f_db}'의 기운적 융합과 만남의 우주적 의미를 대서사시 형태로 매우 상세히 서술하시오.)

<div style='page-break-after: always;'></div>

<h3 style='color: #1A237E; font-size: 24px; font-weight: 900; margin-top: 15px;'>🌈 커플의 인생 기상도 및 대운 교차 분석</h3>
[COUPLE_DAEWUN_TABLES_HERE]
(위 대운표를 바탕으로 향후 수십 년간 두 사람의 운이 교차하며 상생하는 지점과 극복 과제를 매우 상세히 도출)

<div style='page-break-after: always;'></div>

<h3 style='color: #1A237E; font-size: 24px; font-weight: 900; margin-top: 15px;'>💞 초연 시공명리 심층 조화 분석</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 10px; margin-bottom: 5px;'>1) 오행 및 조후의 상생 조화</span>
(오행의 과부족 완충 관계를 상세히 기록)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 20px; margin-bottom: 5px;'>2) 심리 및 가치관의 결속력</span>
(십성 구조에 따른 현실적 소통 및 재물관 융합 분석)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 20px; margin-bottom: 5px;'>3) 내면의 깊은 유대감 (속궁합)</span>
(일지 및 지장간 합형충파해 기반의 성향적 조화를 품격 있게 기술)

<div style='page-break-after: always;'></div>

<h3 style='color: #D50000; font-size: 24px; font-weight: 900; margin-top: 15px;'>⚓ 백년해로를 위한 조율의 지혜</h3>
(두 사람이 필연적으로 마주할 갈등 상황과 명리적 타개책, 실질적 행동 지침을 최고급 조언으로 완성)
[GUNGHAP_END]
"""
                    res_text = call_gemini_api(essay_prompt, max_tokens=12000)
                    ai_clean = "\n".join([line.lstrip() for line in res_text.split("\n")])
                    
                    m_ess, f_ess, g_ess = "", "", ai_clean
                    
                    # 남명 추출
                    m_match = re.search(r'\[MALE_START\](.*?)\[MALE_END\]', ai_clean, re.DOTALL)
                    if m_match: 
                        m_ess = m_match.group(1).strip()
                    
                    # 🚨 여명 추출 (태그 절단 시 2차 안전망 추가)
                    f_match = re.search(r'\[FEMALE_START\](.*?)\[FEMALE_END\]', ai_clean, re.DOTALL)
                    if f_match: 
                        f_ess = f_match.group(1).strip()
                    else:
                        # [FEMALE_END]가 없어도 [GUNGHAP_START] 이전까지 강제 추출
                        f_fallback = re.search(r'\[FEMALE_START\](.*?)\[GUNGHAP_START\]', ai_clean, re.DOTALL)
                        if f_fallback: 
                            f_ess = f_fallback.group(1).strip()
                        else: 
                            f_ess = "<div style='color:#D50000; font-weight:bold; padding:20px; text-align:center;'>여명 통변 데이터가 AI 연산 중 유실되었습니다. 시스템 재실행이 필요합니다.</div>"
                    
                    # 궁합 종합 추출
                    g_match = re.search(r'\[GUNGHAP_START\](.*?)\[GUNGHAP_END\]', ai_clean, re.DOTALL)
                    if g_match: 
                        g_ess = g_match.group(1).strip()
                    else:
                        g_fallback = re.search(r'\[GUNGHAP_START\](.*)', ai_clean, re.DOTALL)
                        if g_fallback:
                            g_ess = g_fallback.group(1).strip()
                        else:
                            g_ess = ai_clean.replace(m_ess, "").replace(f_ess, "").replace("[MALE_START]", "").replace("[MALE_END]", "").replace("[FEMALE_START]", "").replace("[FEMALE_END]", "")
                
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

                    def wrap_a4(content, title_color="#1A237E", title=f"[ 초연 시공명리 사주풀이 {APP_VERSION} ]"):  
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
                        f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333;'>&nbsp;&nbsp;&nbsp;&nbsp;두 분의 <b style='color:#1A237E;'>'만남'</b>은 결코 우연이 아닌, <b style='color:#1A237E;'>'셀 수 없이 많은 시간 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 바코드지만, <b style='color:#1A237E;'>'궁합(宮合)'</b>은 두 바코드가 만나 그려내는 새로운 <b style='color:#1A237E;'>'하모니(harmonie)'</b>입니다.</p>\n"
                        f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333; margin-top: 10px;'>&nbsp;&nbsp;&nbsp;&nbsp;서로의 다름을 이해하고 채워주는 든든한 <b style='color:#1A237E;'>'동반자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 시공간의 축복이 가득하시길 소망합니다. </p>\n"
                        f"<div style='text-align: right; margin-top: 25px;'><span style='font-weight: 900; font-size: 16px; color: #1A237E; font-family: \"Nanum Myeongjo\", serif;'>- 초연 시공명리 연구소 드림 -</span></div>\n"
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
                        f"            <h1 class='title-gothic' style='font-size: 40px !important; margin:0 !important;'>초연 시공명리 궁합풀이</h1>\n"
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
                        f"        <p style='font-size: 18px; margin-top: 30px; font-weight: 800;'>{today_str}</p>\n"
                        f"        <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 시공명리 연구소</p>\n"
                        f"    </div>\n"
                        f"</div>"
                    )
                    st.session_state['saved_report_gh_cover'] = cover_html

                    m_page_content = f"{m_tbl}\n<div class='choyeon-premium-report' style='margin-top:20px;'>\n{m_ess}\n</div>"
                    f_page_content = f"{f_tbl}\n<div class='choyeon-premium-report' style='margin-top:20px;'>\n{f_ess}\n</div>"
                    
                    st.session_state['saved_report_gh_m'] = wrap_a4(m_page_content, "#1A237E", "[ 남명 사주팔자표 및 요약 ]")
                    st.session_state['saved_report_gh_f'] = wrap_a4(f_page_content, "#D50000", "[ 여명 사주팔자표 및 요약 ]")
                    st.session_state['saved_report_gh_g'] = wrap_a4(g_full_content, "#1B5E20", "[ 초연 시공명리 종합 궁합풀이 ]")
                    
                except Exception as e:
                    st.error(f"3단계 궁합 종합 분석 가동 장애: {e}")

            # 🚨 연산 종료 (스위치 끄기)
            st.session_state['need_calc'] = False

        except Exception as e: 
            st.error(f"시스템 연산 중 치명적 오류 발생: {e}")
            st.session_state['need_calc'] = False
            st.stop()

# ==============================================================================
# 🌊 7. [독립 모듈] 일진 시공간 분석 (결과 출력부)
# ==============================================================================
import datetime as dt_mod

if st.session_state.get('app_running', False) and st.session_state.get('run_waterfall', False) and 'global_gans' in st.session_state:
    
    if not st.session_state.get('saved_report_iljin'):
        if st.session_state.get('saved_report_html'):
            st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
            
        t_date = st.session_state['target_date']
        
        gans_list = st.session_state['global_gans']
        jjis_list = st.session_state['global_jjis']
        m_ilgan = st.session_state['global_ds']
        m_ilji = st.session_state['global_db']
        
        # 🚨 [수술 1] 박사님 명조 정보 추출 (배열: [시, 일, 월, 년])
        local_curr_y = dt_mod.datetime.now().year
        local_u_age = local_curr_y - u_y + 1
        myongjo_str = f"명조: {gans_list[3]}{jjis_list[3]}년 {gans_list[2]}{jjis_list[2]}월 {gans_list[1]}{jjis_list[1]}일 {gans_list[0]}{jjis_list[0]}시 ({u_gender}, {local_u_age}세)"
        
        from korean_lunar_calendar import KoreanLunarCalendar
        dklc = KoreanLunarCalendar()
        dklc.setSolarDate(t_date.year, t_date.month, t_date.day)
        gj_str = dklc.getChineseGapJaString()
        
        if gj_str:
            parts = gj_str.split()
            target_year = parts[0][:2]
            target_wol = parts[1][:2]
            target_il_gan = parts[2][0]
            target_il_ji = parts[2][1] 
            
            def get_execution_yong(upper_group, lower_group):
                matrix = {'비겁': {'비겁':'비겁', '식상':'식상', '재성':'재성', '관성':'관성', '인성':'인성'}, '식상': {'비겁':'인성', '식상':'비겁', '재성':'식상', '관성':'재성', '인성':'관성'}, '재성': {'비겁':'관성', '식상':'인성', '재성':'비겁', '관성':'식상', '인성':'재성'}, '관성': {'비겁':'재성', '식상':'관성', '재성':'인성', '관성':'비겁', '인성':'식상'}, '인성': {'비겁':'식상', '식상':'재성', '재성':'관성', '관성':'인성', '인성':'비겁'} }
                return matrix.get(upper_group, {}).get(lower_group, '비겁')

            ilju_lower_group = get_group_ss(get_ss(m_ilgan, m_ilji))
            
            m_che_first = get_group_ss(get_ss(m_ilgan, target_wol[0]))
            d_gan_ss = get_group_ss(get_ss(m_ilgan, target_il_gan))  
            am_yong = get_execution_yong(d_gan_ss, ilju_lower_group)
            
            m_che_second = get_group_ss(get_ss(m_ilgan, target_wol[1]))
            d_ji_ss = get_group_ss(get_ss(m_ilgan, target_il_ji))    
            pm_yong = get_execution_yong(d_ji_ss, ilju_lower_group)

            gan_desc = {"합(合)": "생각과 뜻이 맞고 긍정적 결속력이 생기는 하루입니다.", "충(沖)": "정신적인 대립이나 스트레스가 발생할 수 있습니다.", "극(剋)": "상황을 통제하느라 피로감이 따를 수 있습니다."}
            gan_res = []
            labels_gan = ["시간", "일간", "월간", "년간"]
            for idx, label in enumerate(labels_gan):
                g1, g2 = gans_list[idx], target_il_gan
                if g1 not in ["?", "-", " "]:
                    s = {g1, g2}
                    rel = "-"
                    if s in [{'甲','己'}, {'乙','庚'}, {'丙','辛'}, {'丁','壬'}, {'戊','癸'}]: rel = "합(合)"
                    elif s in [{'甲','庚'}, {'乙','辛'}, {'丙','壬'}, {'丁','癸'}, {'戊','甲'}, {'己','乙'}]: rel = "충(沖)"
                    elif {'甲':'戊', '乙':'己', '丙':'庚', '丁':'辛', '戊':'壬', '己':'癸', '庚':'甲', '辛':'乙', '壬':'丙', '癸':'丁'}.get(g1) == g2 or {'甲':'戊', '乙':'己', '丙':'庚', '丁':'辛', '戊':'壬', '己':'癸', '庚':'甲', '辛':'乙', '壬':'丙', '癸':'丁'}.get(g2) == g1: rel = "극(剋)"
                    
                    if rel != "-":
                        gan_res.append(f"☁️ <b>{label}({g1})</b> → <span style='color:#1976D2; font-weight:bold;'>천간 {rel}</span> <span style='color:#555; font-size:13px;'>( {g1}{g2}{rel}하여 {gan_desc.get(rel, '영향 발생')} )</span>")

            # 🚨 [수술 1] 박사님 지시 반영: 지지 파동 구체적 서술 딕셔너리 추가
            ji_desc_map = {
                "육합": "일이 순조롭게 풀리고 화합하는 기운입니다.",
                "방합": "같은 목적을 가진 세력이 강하게 결집하는 기운입니다.",
                "반합": "새로운 국면으로 전환되거나 목적을 위해 협력하는 기운입니다.",
                "충": "역동적인 변동이나 충돌, 혹은 이동수가 발생하기 쉽습니다.",
                "형": "의견 조율 과정에서 시비나 조정, 수술수 등의 변동이 따릅니다.",
                "원진": "사소한 오해나 심리적인 갈등, 원망이 생길 수 있으니 주의하십시오.",
                "귀문": "신경이 예민해지고 직관력이 극대화되는 묘한 기운입니다.",
                "파": "기존의 틀이나 약속이 깨지고 새로운 것을 모색하게 되는 기운입니다.",
                "해": "예상치 못한 방해나 심리적 섭섭함이 발생할 수 있습니다.",
                "암합": "보이지 않는 곳에서 은밀하게 뜻이 맞고 결속되는 기운입니다."
            }

            r_res = []
            labels_ji = ["시지", "일지", "월지", "년지"]
            for idx, label in enumerate(labels_ji):
                j1 = jjis_list[idx]
                rel_full = get_ji_rel_set(j1, target_il_ji) 
                if rel_full != "-":
                    main_rel = rel_full.split(',')[0].strip()
                    desc_text = ji_desc_map.get(main_rel, "미세한 환경적 파동과 변화가 감지됩니다.")
                    r_res.append(f"🌊 <b>{label}({j1})</b> → <span style='color:#D50000; font-weight:bold;'>{rel_full}</span> <span style='color:#555; font-size:13px;'>( {j1}{target_il_ji} {main_rel}하여 {desc_text} )</span>")

            gan_res_html = '<br>'.join(gan_res) if gan_res else '특이 천간 파동 없음'
            r_res_html = '<br>'.join(r_res) if r_res else '특이 지지 파동 없음'

            day_wunseong = get_unsung(m_ilgan, target_il_ji)
            day_12shinsal = get_12_shinsal(jjis_list[3], target_il_ji) 
            
            s_res_html = f"✨ <b>오늘의 핵심 에너지:</b> 십이운성[{day_wunseong}] / 12신살[{day_12shinsal}]"

            # 🚨 [수술 2] AI 환각 통제 및 시공명리(체용) 강제 프롬프트
            iljin_prompt = f"""
당신은 명리심리상담사 초연 박사입니다.
오늘의 시공간 파동을 바탕으로 핵심만을 간결하게 통변하십시오.

[핵심 팩트]
- 내담자: {m_ilgan}{m_ilji} / 일진: {t_date.month}월 {t_date.day}일
- 천간/지지 파동: {gan_res_html} / {r_res_html}
- 전반부 체용: {m_che_first}(무대) + {am_yong}(사건)
- 후반부 체용: {m_che_second}(무대) + {pm_yong}(사건)
- 오늘의 운성/신살: {day_wunseong} / {day_12shinsal}

🚨 [AI 통제 헌법]
1. 서론, 인사말, '연산 팩트' 등 기술적 문구 출력 절대 금지.
2. 마크다운 표 및 `**` 강조 기호 사용 절대 금지. 오직 HTML <b> 태그만 사용.
3. 🚨 가장 중요한 규칙: 감성적인 심리 묘사나 전통 명리적 통변을 철저히 배제하십시오! 오직 제공된 **[시공명리의 체(환경/무대)와 용(사건/행동)]**의 결합 원리만을 사용하여, 구체적이고 현실적인 **'사건과 실질적 결과'** 위주로 통변해야 합니다.

[출력 포맷]
<span style='font-size: 16px; font-weight: 900;'>▶ 오전(00:31~13:30):</span> [시공명리 체({m_che_first})+용({am_yong})]의 결합을 바탕으로 오전의 실제적인 업무/대인관계 사건을 1~2문장으로 직관적으로 통변.
<br><span style='font-size: 16px; font-weight: 900;'>▶ 오후(13:31~23:30):</span> [시공명리 체({m_che_second})+용({pm_yong})]의 결합을 바탕으로 오후의 실질적 사건 흐름을 1~2문장으로 통변.
<br><span style='font-size: 16px; font-weight: 900;'>✨ 오늘의 개운 조언:</span> 박사님의 일주와 오늘의 파동({day_wunseong}/{day_12shinsal})을 접목한 구체적이고 현실적인 행동 지침 1문장.
"""
            with st.spinner("⏳ 메인 사주풀이 보존 완료! 하단에 [일진 시공간 분석]을 추가 가동 중입니다..."):
                try:
                    ai_iljin_html = call_light_api(iljin_prompt).replace('\n', '<br>')
                except Exception as e:
                    ai_iljin_html = f"<div style='color:red; font-weight:bold; padding:10px;'>🚨 AI 일진 분석 장애: {e}</div>"

            # 🚨 [수술 3] 화면 출력부에 박사님 명조 정보 삽입
            html_output = (
                f"<div class='page-break-before'></div>\n"
                f"<div class='report-page'>\n"
                f"<div class='vip-inset-frame' style='border: 3px solid #1A237E;'>\n"
                f"<h1 style='text-align: center; color: #1A237E;'>🔮 일진 시공간 정밀 분석서</h1>\n"
                f"<div style='text-align: center; font-size: 16px; font-weight: bold; color: #555; margin-bottom: 20px;'>\n"
                f"{myongjo_str}<br>\n"
                f"대상일자: {t_date.year}년 {t_date.month}월 {t_date.day}일 ({target_year}년 {target_wol}월 {target_il_gan}{target_il_ji}일)\n"
                f"</div>\n"
                f"<div style='margin-bottom: 25px; background: #FFF8E1; padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6;'>\n"
                f"{gan_res_html}<br>{r_res_html}<br><br>{s_res_html}\n"
                f"</div>\n"
                f"<div class='content-box-loose' style='font-size: 15px; line-height: 1.8;'>\n"
                f"{ai_iljin_html}\n"
                f"</div>\n"
                f"</div>\n"
                f"</div>"
            )
            
            # 🚨 [중요] 지워졌던 7번 모듈 마무리 저장 및 리런 코드 복구
            st.session_state['saved_report_iljin'] = html_output
            st.rerun()

# ==============================================================================
# 👶 8. [독립 모듈] 출산택일 정밀 분석 (연산 및 AI 두뇌 전용)
# ==============================================================================
if st.session_state.get('app_running', False) and st.session_state.get('run_delivery_only', False) and 'global_gans' in st.session_state:
    with st.spinner("⏳ [출산택일 분석실] 최적의 길일 연산 및 AI 통변 중... (기존 궁합풀이는 안전하게 보존 중입니다)"):
        try:
            # 🚨 [수술 4] 사이드바에 부여한 고유 key에서 직접 탈취하여 기본값(오늘 날짜) 덮어쓰기 원천 차단
            start_date = st.session_state.get('input_search_start', st.session_state.get('search_start_date'))
            end_date = st.session_state.get('input_search_end', st.session_state.get('search_end_date'))
            last_period_date = st.session_state.get('input_last_period', st.session_state.get('last_period_date'))
            period_cycle = st.session_state.get('input_period_cycle', st.session_state.get('period_cycle'))

            gans = st.session_state.get('global_gans', ["?", "?", "?", "?"])
            jjis = st.session_state.get('global_jjis', ["?", "?", "?", "?"])
            p_bazi_context = st.session_state.get('partner_bazi', ["?", "?", "?", "?"])

            if u_gender == "남성":
                m_jjis = jjis
                f_jjis = [b[1] if len(b)>1 else "?" for b in p_bazi_context]
                m_gans_str = "".join(gans)
                f_gans_str = "".join([b[0] if len(b)>0 else "?" for b in p_bazi_context])
            else:
                m_jjis = [b[1] if len(b)>1 else "?" for b in p_bazi_context]
                f_jjis = jjis
                m_gans_str = "".join([b[0] if len(b)>0 else "?" for b in p_bazi_context])
                f_gans_str = "".join(gans)

            H2K_MAP = {'甲':'갑','乙':'을','丙':'병','丁':'정','戊':'무','己':'기','庚':'경','辛':'신','壬':'임','癸':'계',
                       '子':'자','丑':'축','寅':'인','卯':'묘','辰':'진','巳':'사','午':'오','未':'미','申':'신','酉':'유','戌':'술','亥':'해'}
            def h2k(text): return "".join([H2K_MAP.get(c, c) for c in text])

            # 🚨 [신규 엔진] 생리 주기 시뮬레이션 및 실제 배란일 동기화 함수
            def get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, forbidden_list):
                OHENG_MAP = {'갑':'목', '을':'목', '인':'목', '묘':'목', '병':'화', '정':'화', '사':'화', '오':'화',
                             '무':'토', '기':'토', '축':'토', '진':'토', '미':'토', '술':'토', '경':'금', '신':'금', '유':'금',
                             '임':'수', '계':'수', '자':'수', '해':'수'}
                
                KILL_SWITCH = set(forbidden_list)
                KILL_SWITCH.update({'갑진', '을미', '병술', '정축', '무진', '임술', '계축'}) 
                hap_list = [{'자', '축'}, {'인', '해'}, {'묘', '술'}, {'진', '유'}, {'사', '신'}, {'오', '미'}]
                choong_list = [{'자', '오'}, {'축', '미'}, {'인', '신'}, {'묘', '유'}, {'진', '술'}, {'사', '해'}]
                wonjin_gwimun = [{'자', '미'}, {'축', '오'}, {'인', '유'}, {'묘', '신'}, {'진', '해'}, {'사', '술'}]
                hyung_list = [{'인', '사'}, {'사', '신'}, {'인', '신'}, {'축', '술'}, {'술', '미'}, {'축', '미'}, {'자', '묘'}] 
                ROOT_MAP = {'갑': ['인', '묘', '진', '해', '미'], '을': ['인', '묘', '진', '해', '미'], '병': ['사', '오', '미', '인', '술'], '정': ['사', '오', '미', '인', '술'], '무': ['진', '술', '축', '미', '사', '오'], '기': ['진', '술', '축', '미', '사', '오'], '경': ['신', '유', '술', '사', '축'], '신': ['신', '유', '술', '사', '축'], '임': ['해', '자', '축', '신', '진'], '계': ['해', '자', '축', '신', '진']}
                SPRING_AUTUMN = ['인', '묘', '진', '신', '유'] 
                EXTREME_SUMMER_WINTER = ['사', '오', '미', '해', '자', '축', '술'] 

                TIME_SLOTS = [("자", "23:30~01:29"), ("축", "01:30~03:29"), ("인", "03:30~05:29"), ("묘", "05:30~07:29"), ("진", "07:30~09:29"), ("사", "09:30~11:29"), ("오", "11:30~13:29"), ("미", "13:30~15:29"), ("신", "15:30~17:29"), ("유", "17:30~19:29"), ("술", "19:30~21:29"), ("해", "21:30~23:29")]
                TIME_STEM_START = {'갑':'갑', '기':'갑', '을':'병', '경':'병', '병':'무', '신':'무', '정':'경', '임':'경', '무':'임', '계':'임'}
                GAN_LIST = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계']
                GUIIN_MAP = {'갑': ['축', '미'], '을': ['자', '신'], '병': ['해', '유'], '정': ['해', '유'], '무': ['축', '미'], '기': ['자', '신'], '경': ['축', '미'], '신': ['인', '오'], '임': ['묘', '사'], '계': ['묘', '사']}

                # 🚨 [신규 연산 추가] 50사이클(약 4년)치 가임기 및 출산 가능 윈도우 사전 계산
                valid_delivery_dates = {}
                for i in range(50): 
                    cycle_start = last_period_date + dt_mod.timedelta(days=period_cycle * i)
                    ovul_d = cycle_start + dt_mod.timedelta(days=period_cycle - 14) # 실제 배란일
                    exp_del = ovul_d + dt_mod.timedelta(days=266) # 실제 출산 예정일
                    
                    # 배란일 1개당 -> 출산 가능일 15개(예정일 전 14일 ~ 당일) 매핑
                    for j in range(15):
                        d = exp_del - dt_mod.timedelta(days=j)
                        valid_delivery_dates[d] = ovul_d 

                raw_candidates = []
                curr = start_date
                
                while curr <= end_date:
                    # 🚨 [생체 리듬 필터] 모체의 가임기로 불가능한 출산일은 아예 건너뜁니다!
                    if curr not in valid_delivery_dates:
                        curr += dt_mod.timedelta(days=1)
                        continue
                        
                    birth_d = curr
                    exact_ovulation_d = valid_delivery_dates[birth_d] # 280일 역산이 아닌 실제 매핑된 배란일
                    
                    b_klc = KoreanLunarCalendar()
                    b_klc.setSolarDate(birth_d.year, birth_d.month, birth_d.day)
                    b_gj = b_klc.getChineseGapJaString().split()
                    
                    if len(b_gj) >= 3:
                        b_gj_kor = [h2k(pillar) for pillar in b_gj[:3]] 
                        b_year, b_month, b_day = b_gj_kor[0], b_gj_kor[1], b_gj_kor[2]
                        
                        if b_year in KILL_SWITCH or b_month in KILL_SWITCH or b_day in KILL_SWITCH:
                            curr += dt_mod.timedelta(days=1); continue
                        if b_year == b_month or b_month == b_day or b_year == b_day:
                            curr += dt_mod.timedelta(days=1); continue

                        is_bad_structure = False
                        for idx1 in range(3):
                            for idx2 in range(idx1 + 1, 3):
                                pair = {b_gj_kor[idx1][1], b_gj_kor[idx2][1]}
                                if pair in choong_list or pair in wonjin_gwimun or pair in hyung_list:
                                    is_bad_structure = True; break
                            if is_bad_structure: break
                        if is_bad_structure:
                            curr += dt_mod.timedelta(days=1); continue

                        b_day_stem = b_day[0]
                        if b_month[1] not in ROOT_MAP[b_day_stem] and b_day[1] not in ROOT_MAP[b_day_stem]:
                            curr += dt_mod.timedelta(days=1); continue 

                        season_score = 0
                        if b_month[1] in SPRING_AUTUMN: season_score += 50
                        elif b_month[1] in EXTREME_SUMMER_WINTER: season_score -= 100 

                        start_stem = TIME_STEM_START.get(b_day_stem, '갑')
                        start_idx = GAN_LIST.index(start_stem)

                        best_time_score = -999
                        best_time_data = {}

                        for t_idx, (t_ji, t_time_str) in enumerate(TIME_SLOTS):
                            t_gan = GAN_LIST[(start_idx + t_idx) % 10]
                            b_time = f"{t_gan}{t_ji}"

                            if b_time in KILL_SWITCH or b_time in [b_year, b_month, b_day]: continue
                            
                            is_time_bad = False
                            for p in b_gj_kor:
                                pair = {p[1], t_ji}
                                if pair in choong_list or pair in wonjin_gwimun:
                                    is_time_bad = True; break
                            if is_time_bad: continue

                            parent_score = 15
                            for p_ji in m_jjis + f_jjis:
                                if p_ji == '?': continue
                                pair = {b_month[1], p_ji} 
                                if pair in hap_list: parent_score += 10
                                if pair in choong_list: parent_score -= 10

                            god_score = 10
                            noble_branches = GUIIN_MAP.get(b_day_stem, [])
                            if b_month[1] in noble_branches or b_day[1] in noble_branches or t_ji in noble_branches: god_score += 10
                            
                            tie_breaker = ((32 - birth_d.day) * 0.001) + (t_idx * 0.0001)
                            total_score = max(0, min(100, season_score + parent_score + god_score)) + tie_breaker

                            if total_score > best_time_score:
                                best_time_score = total_score
                                best_time_data = {'time_pillar': b_time, 'time_str': t_time_str, 'score': total_score}

                        if best_time_data:
                            raw_candidates.append({
                                'ovulation_date': exact_ovulation_d.strftime('%Y-%m-%d'), # 🚨 실제 배란일
                                'birth_date': birth_d.strftime('%Y-%m-%d'), # 🚨 실제 출산일
                                'month': birth_d.strftime('%Y-%m'), 
                                'score': best_time_data['score'], 
                                'best_time': best_time_data
                            })
                            
                    curr += dt_mod.timedelta(days=1)
                    
                month_best_bucket = {}
                for item in raw_candidates:
                    m_key = item['month']
                    if m_key not in month_best_bucket or item['score'] > month_best_bucket[m_key]['score']:
                        month_best_bucket[m_key] = item
                        
                sorted_months = sorted(month_best_bucket.values(), key=lambda x: (-int(x['score']), x['month']))
                return sorted_months[:3]

            m_saju_hanja = f"{m_gans_str[3]}{m_jjis[3]}년 {m_gans_str[2]}{m_jjis[2]}월 {m_gans_str[1]}{m_jjis[1]}일 {m_gans_str[0]}{m_jjis[0]}시"
            f_saju_hanja = f"{f_gans_str[3]}{f_jjis[3]}년 {f_gans_str[2]}{f_jjis[2]}월 {f_gans_str[1]}{f_jjis[1]}일 {f_gans_str[0]}{f_jjis[0]}시"
            m_saju_kor = h2k(m_saju_hanja)
            f_saju_kor = h2k(f_saju_hanja)
            m_ilgan_kor = h2k(m_gans_str[1])
            f_ilgan_kor = h2k(f_gans_str[1])

            FORBIDDEN_LIST = ['갑인', '을묘', '병오', '정사', '무진', '무술', '기미', '기축', '신유', '경신', '임자', '계해']
            delivery_days = get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, FORBIDDEN_LIST)

            del_content = f"<div style='border-bottom:4px double #4A148C; padding-bottom:15px; margin-bottom:30px;'><h1 style='text-align:center; font-size: 30px; color:#4A148C; font-weight: 900; margin:0; font-family:\"Malgun Gothic\", sans-serif;'>👶 초연 시공명리 출산택일</h1></div>\n"
            del_content += f"<h2 style='text-align:center; color:#111; font-weight:900; font-size: 22px;'>🎯 새 생명 마중 길일(출산 택일) 추천</h2>\n"
            
            # 🚨 [수술 1] 가이드와 에세이를 상단으로 끌어올리고 중복 문구를 싹 정리했습니다.
            del_content += "<div style='color:#333; margin-top: 15px; margin-bottom: 5px; text-indent: 15px;'><span style='font-size:18px;'><b>💡 부부를 위한 임신 계획 가이드:</b></span></div>\n"
            del_content += f"<div style='color:#333; line-height:1.8; margin-top: 0px; margin-bottom: 5px; text-indent: 15px;'><span style='font-size:15px;'>위의 출산 길일은 아이의 사주 기운을 우선으로 선정한 것입니다. 의학적 평균 임신 기간(약 280일)을 고려할 때, <b>합궁 시기는 출산 예정일로부터 약 {period_cycle}일 주기를 고려한 실제 가임 기간</b>이 됩니다. 부인분의 생리 주기와 배란일을 면밀히 고려하시어, 부부께서 상의하에 가장 건강한 시기를 계획하시길 바랍니다.</span></div>\n"

            intro_essay = f"""<div style='margin-top:10px; margin-bottom:30px;'>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:5px;'>깊고 고요한 시간의 흐름 속에서, 새로운 생명의 탄생은 하늘과 땅, 그리고 부모의 염원이 조화롭게 어우러지는 기적과 같습니다. 귀한 부부께서 보내주신 소중한 사주 정보를 바탕으로, 장차 태어날 아기의 선천적 명식이 부모님과의 오행 상생 조화를 극대화하고, 나아가 아이 스스로 빛나는 삶의 궤적을 그려나갈 수 있도록 '최고의 프리미엄 출산 희망일과 시간'을 심혈을 기울여 선정하였습니다.</p>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:5px;'>부부의 사주를 살펴보니, 신청인 남성분({m_saju_kor})께서는 {m_ilgan_kor} 일간으로 자신만의 강인한 기운이 특징적입니다. 상대방 여성분({f_saju_kor})께서는 {f_ilgan_kor} 일간으로 지혜롭고 활발한 에너지를 지니셨습니다.</p>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:5px;'>아이가 태어날 시공간은 부모의 사주에 부족한 오행을 채우고, 동시에 아이 자신이 타고난 길운(吉運)을 펼칠 수 있는 절묘한 지점을 찾아야 합니다. 부모 모두에게 긍정적인 상생의 흐름을 만들어낼 수 있는 기운을 중심으로, 동시에 아이의 명식이 균형과 조화를 이루는 날들을 엄선하였습니다.</p>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:5px;'>이제, 부부의 간절한 바람을 담아 선정한 세 가지 최적의 출산 희망일을 <b>초연 시공명리 궁합</b> 관점에서 자세히 풀어내어 올립니다. 부디 이 추천들이 아기의 밝은 미래를 여는 데 귀한 나침반이 되기를 바랍니다.</p>
</div>"""
            del_content += intro_essay

            ai_target_days_facts = []
            del_content += f"<div style='display:flex; flex-direction:column; margin-bottom:15px; background:#f9f9f9; padding:20px; border-radius:10px;'>\n"
            
            def get_daewun_sequence(start_gan, start_ji, direction, count=8):
                GAN_L = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
                JI_L = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
                try:
                    g_idx = GAN_L.index(start_gan)
                    j_idx = JI_L.index(start_ji)
                except: return ["?"] * count
                seq = []
                for k in range(1, count + 1):
                    step = k if direction == 1 else -k
                    seq.append(f"{GAN_L[(g_idx + step) % 10]}{JI_L[(j_idx + step) % 12]}")
                return seq

            if delivery_days:
                K2H_MAP = {v: k for k, v in H2K_MAP.items()}
                
                for i in range(min(3, len(delivery_days))):
                    ovul_d_obj = dt_mod.datetime.strptime(delivery_days[i]['ovulation_date'], '%Y-%m-%d')
                    birth_d_obj = dt_mod.datetime.strptime(delivery_days[i]['birth_date'], '%Y-%m-%d')
                    total_score = int(delivery_days[i]['score']) 
                    
                    best_time_info = delivery_days[i]['best_time']
                    opt_time_str = best_time_info['time_str']
                    b_hs_hb = best_time_info['time_pillar']
                    b_hs, b_hb = b_hs_hb[0], b_hs_hb[1]
                    
                    b_ym, b_mm, _ = get_true_year_month_pillar(birth_d_obj.year, birth_d_obj.month, birth_d_obj.day, 10, 30)
                    b_klc = KoreanLunarCalendar()
                    b_klc.setSolarDate(birth_d_obj.year, birth_d_obj.month, birth_d_obj.day)
                    b_gj = b_klc.getChineseGapJaString().split()
                    b_ds, b_db = b_gj[2][0], b_gj[2][1]
                    
                    b_hs_hanja = K2H_MAP.get(b_hs, b_hs)
                    b_hb_hanja = K2H_MAP.get(b_hb, b_hb)
                    
                    bazi_hanja = f"{b_ym}년 {b_mm}월 {b_ds}{b_db}일 {b_hs_hanja}{b_hb_hanja}시"
                    bazi_hanja_strict = f"{b_ym}年 {b_mm}月 {b_ds}{b_db}日 {b_hs_hanja}{b_hb_hanja}時"
                    bazi_kor = f"{h2k(b_ym)}년 {h2k(b_mm)}월 {h2k(b_ds+b_db)}일 {h2k(b_hs+b_hb)}시"
                    
                    is_yang_year = b_ym[0] in ['甲', '丙', '戊', '庚', '壬']
                    m_dir = 1 if is_yang_year else -1
                    f_dir = -1 if is_yang_year else 1
                    m_dir_str = "순행" if m_dir == 1 else "역행"
                    f_dir_str = "순행" if f_dir == 1 else "역행"
                    
                    try:
                        b_hour, b_minute = int(opt_time_str[0:2]), int(opt_time_str[3:5])
                    except: b_hour, b_minute = 12, 0
                        
                    kst = pytz.timezone('Asia/Seoul')
                    dt_kst = kst.localize(dt_mod.datetime(birth_d_obj.year, birth_d_obj.month, birth_d_obj.day, b_hour, b_minute))
                    utc_dt = dt_kst.astimezone(pytz.utc)
                    
                    m_dsu = get_daeun_su_accurate(utc_dt, m_dir)
                    f_dsu = get_daeun_su_accurate(utc_dt, f_dir)
                    
                    m_daewun_list = get_daewun_sequence(b_mm[0], b_mm[1], m_dir, 10)
                    f_daewun_list = get_daewun_sequence(b_mm[0], b_mm[1], f_dir, 10)
                    
                    start_conception = ovul_d_obj - dt_mod.timedelta(days=5)
                    end_conception = ovul_d_obj
                    date_range_str = f"{start_conception.year}년 {start_conception.month:02d}월 {start_conception.day:02d}일 ~ {end_conception.year}년 {end_conception.month:02d}월 {end_conception.day:02d}일"
                    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                    
                    gans = [b_hs_hanja, b_ds, b_mm[0], b_ym[0]]
                    jjis = [b_hb_hanja, b_db, b_mm[1], b_ym[1]]
                    hs, ds, ms, ys = b_hs_hanja, b_ds, b_mm[0], b_ym[0]
                    hb, db, mb, yb = b_hb_hanja, b_db, b_mm[1], b_ym[1]

                    def td(char):
                        if char in ["?", "-", " "]: return f"<td style='border:1px solid #444; padding:3px 0;'>{char}</td>"
                        color_key = get_color(char)
                        bg = {'목':'#2E7D32','화':'#C62828','토':'#F9A825','금':'#9E9E9E','수':'#212121'}.get(color_key, '#888')
                        tc = 'white' if color_key != '토' else 'black'
                        return f"<td style='border:1px solid #444; background-color:{bg}; color:{tc}; font-weight:900; font-size:18px; padding:3px 0; line-height:1.2;'>{char}</td>"

                    ji_rel_rows = ""
                    for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                        b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                        b_top = "0px solid transparent !important"
                        cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                        lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                        ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

                    # 🚨 [수술 1] 겹박스 제거로 가로폭 100% 확보 & PDF 인쇄 시 중간 잘림 방지(page-break-inside: avoid)
                    del_content += "<div style='page-break-inside: avoid; margin-bottom: 20px; font-family: \"Malgun Gothic\", sans-serif;'>\n"
                    del_content += f"<div style='font-size: 18px; font-weight: 900; color: #4A148C; border-bottom: 2px solid #4A148C; padding-bottom: 8px; margin-bottom: 12px;'>{medal} {i+1}순위 추천 명식 요약 <span style='color: #D81B60; font-size: 15px;'>[종합점수: {total_score}점]</span></div>\n"
                    del_content += "<div style='line-height: 1.6; font-size: 15px; color: #333; padding-left: 5px; margin-bottom: 15px;'>\n"
                    del_content += f"<div style='margin-bottom: 4px;'>❤️ <b>합궁 가임 기간:</b> {date_range_str} <span style='font-size: 14px; color: #666;'>(최적일: {ovul_d_obj.month:02d}월 {ovul_d_obj.day:02d}일)</span></div>\n"
                    del_content += f"<div>🏥 <b>최적 출산 택일:</b> {birth_d_obj.year}년 {birth_d_obj.month:02d}월 {birth_d_obj.day:02d}일 {opt_time_str}</div>\n"
                    del_content += "</div>\n"
                    
                    # 안쪽 사주 표는 얇고 심플한 테두리만 남겨 넓게 사용
                    del_content += "<div style='border: 2px solid #eee; border-radius: 8px; padding: 10px;'>\n"
                    del_content += f"<div style='text-align:center; margin-bottom:10px;'><div style='font-size: 16px; font-weight: bold; color: #4A148C;'>[ {i+1}순위 사주원국 및 남녀 대운 흐름 ]</div></div>\n"
                    
                    del_content += "<table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>\n"
                    del_content += "<tr class='top-header-cell' style='background-color:#4A148C;'>\n"
                    del_content += "<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>구분</td><td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>시주</td><td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>일주</td><td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>월주</td><td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>년주</td>\n"
                    del_content += "</tr>\n"
                    
                    del_content += "<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간합충</td>" + "".join([f"<td style='border:1px solid #444;'>{get_gan_rel_all(idx, gans)}</td>" for idx in range(4)]) + "</tr>\n"
                    del_content += f"<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(ds,ms)}</td><td style='border:1px solid #444;'>{get_ss(ds,ys)}</td></tr>\n"
                    del_content += f"<tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>\n"
                    del_content += f"<tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>\n"
                    del_content += f"<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(ds,hb)}</td><td style='border:1px solid #444;'>{get_ss(ds,db)}</td><td style='border:1px solid #444;'>{get_ss(ds,mb)}</td><td style='border:1px solid #444;'>{get_ss(ds,yb)}</td></tr>\n"
                    del_content += "<tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지장간</td>" + "".join([f"<td style='padding:0; border:1px solid #444;'>{get_jijanggan_full(ds, jjis[idx])}</td>" for idx in range(4)]) + "</tr>\n"
                    del_content += ji_rel_rows + "\n"
                    del_content += "<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이운성</td>" + "".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{get_unsung(ds, jjis[idx])}</td>" for idx in range(4)]) + "</tr>\n"
                    del_content += "<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이신살</td>" + "".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{get_12_shinsal(yb, jjis[idx])}</td>" for idx in range(4)]) + "</tr>\n"
                    del_content += "<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>" + "".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(get_general_shinsal_filtered(idx, gans, jjis, '남성')) if get_general_shinsal_filtered(idx, gans, jjis, '남성') else '-'}</td>" for idx in range(4)]) + "</tr>\n"
                    del_content += "</table>\n"

                    def build_daewun_bar(dsu, d_list, gender_label, bg_color, d_dir):
                        bar_html = f"<div style='margin-top:15px; margin-bottom:5px; font-size:14px; font-weight:900; color:{bg_color};'>[ {gender_label} 대운 흐름 (대운수: {dsu}, {'순행' if d_dir==1 else '역행'}) ]</div>"
                        bar_html += f"<div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white;'>"
                        for k in range(10):
                            val = k * 10 + dsu
                            c, j = d_list[k][0], d_list[k][1]
                            b_left = "1px solid #ccc" if k != 9 else "none"
                            bar_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:2px;'>"
                            bar_html += f"<div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:12px; border-bottom:1px solid #ccc;'>{val}세</div>"
                            bar_html += f"<div style='padding:1px; font-size:12px;'>{get_ss(ds,c)}</div>"
                            
                            c_color, j_color = get_color(c), get_color(j)
                            c_bg = {'목':'#2E7D32','화':'#C62828','토':'#F9A825','금':'#9E9E9E','수':'#212121'}.get(c_color, '#fff')
                            j_bg = {'목':'#2E7D32','화':'#C62828','토':'#F9A825','금':'#9E9E9E','수':'#212121'}.get(j_color, '#fff')
                            c_tc = 'white' if c_color != '토' else 'black'
                            j_tc = 'white' if j_color != '토' else 'black'
                            
                            bar_html += f"<div style='font-size:15px; font-weight:900; background-color:{c_bg}; color:{c_tc}; padding:2px 0; line-height:1.2;'>{c}</div>"
                            bar_html += f"<div style='font-size:15px; font-weight:900; background-color:{j_bg}; color:{j_tc}; padding:2px 0; line-height:1.2;'>{j}</div>"
                            bar_html += f"<div style='padding:1px; font-size:12px;'>{get_ss(ds,j)}</div>"
                            bar_html += f"<div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,j)}</div>"
                            bar_html += f"<div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, j)}</div>"
                            bar_html += "</div>"
                        bar_html += "</div>"
                        return bar_html

                    del_content += build_daewun_bar(m_dsu, m_daewun_list, "🟦 남아", "#0D47A1", m_dir)
                    del_content += build_daewun_bar(f_dsu, f_daewun_list, "🟥 여아", "#D81B60", f_dir)
                    del_content += "</div>\n" 
                    
                    # 🚨 [새로운 방식] 루프 안에서 각 순위별로 AI 호출 (표 바로 아래에 풀이 삽입)
                    fact_line = f"▶ {i+1}순위 추천 명식: {bazi_hanja_strict}\n  - 남아: 대운수 {m_dsu}, {m_dir_str}\n  - 여아: 대운수 {f_dsu}, {f_dir_str}"
                    parent_info = f"부모 사주 정보 - 부(남성): {m_saju_kor}, 모(여성): {f_saju_kor}"

                    delivery_prompt = f"""
[SYSTEM ROLE: CHOYEON SIGONG MASTER]
당신은 명리심리상담사 '초연 박사'입니다.
{parent_info}

아래 [추천 명식 및 대운 데이터]를 바탕으로 해당 명식에 대한 냉철하고 객관적인 통변 에세이를 작성하십시오.

[추천 명식 및 대운 데이터]
{fact_line}
- 사주 원국: {bazi_hanja_strict}

🚨 [출산택일 특별 통제 규칙 - 맹목적 칭찬 금지!]
1. [객관적 검증]: 원국의 십성 분포(무재성, 무관성 등 결핍 여부), 양인살/백호살 등의 강렬한 기운, 오행의 편중을 반드시 '있는 그대로' 분석하십시오. 억지로 장점만 포장하지 마십시오.
2. [대운의 실효성]: 남/녀 대운을 분석할 때, 초년(학업), 청장년(재물/직업), 말년의 흐름에서 필요한 기운(재성/관성 등)이 제때 들어오는지, 아니면 엇박자가 나는지 예리하게 짚어내십시오.
3. [괄호 표기법]: 모든 명리 용어는 반드시 '현대적 풀이 (명리 용어)' 형태로 표기하여 2030 부모가 쉽게 이해하도록 하십시오. (예: "자신감이 지나쳐 고집으로 발현될 수 있는 기운 (병오 양인살)")
4. [표준 용어 준수]: '임관' 사용을 절대 금지하며 '건록'으로 대체하십시오.

[필수 준수 사항]
1. 1) 항목: 사주 원국의 뼈대(일간 특성, 오행 밸런스, 결핍된 십성)와 부모 사주와의 조화를 냉정하게 서술하십시오.
2. 2) 항목: 남아와 여아를 나누어, 각 성별의 대운수와 순/역행 흐름을 바탕으로 삶의 굴곡과 유불리를 구체적으로 분석하십시오.
3. 어떤 시스템적 명칭(규칙, 알고리즘 등)도 언급하지 말고 자연스러운 명리학자의 해설로 작성하십시오.

[출력 포맷 템플릿] (반드시 아래 HTML 형태를 그대로 사용하여 출력할 것)
<div style='margin-bottom: 10px; margin-top: 15px;'>
    <div style='font-size: 18px; font-weight: 900; color: #111; margin-bottom: 10px; border-bottom: 2px solid #4A148C; padding-bottom: 5px;'>{medal} {i+1}순위 추천 명식: {bazi_hanja_strict} 풀이</div>
    <div style='padding-left: 10px;'>
        <div style='margin-bottom: 3px; color:#D50000;'><b>1) 사주 원국의 그릇과 부모 조화:</b></div>
        <p style='text-indent: 15px; margin-top: 0px; margin-bottom: 10px;'> (통변 내용) </p>
        <div style='margin-bottom: 3px; margin-top:5px; color:#D50000;'><b>2) 성별 대운 흐름 기반 심층 분석:</b></div>
        <p style='text-indent: 15px; margin-top: 0px; margin-bottom: 5px;'><b>▶ 남아 (대운수 {m_dsu}, {m_dir_str}):</b></p>
        <p style='text-indent: 15px; margin-top: 0px; margin-bottom: 10px;'> (남아 대운의 유불리 통변 내용) </p>
        <p style='text-indent: 15px; margin-top: 0px; margin-bottom: 5px;'><b>▶ 여아 (대운수 {f_dsu}, {f_dir_str}):</b></p>
        <p style='text-indent: 15px; margin-top: 0px; margin-bottom: 10px;'> (여아 대운의 유불리 통변 내용) </p>
    </div>
</div>
"""
                    ai_delivery_html = call_gemini_api(delivery_prompt)
                    ai_delivery_html = ai_delivery_html.replace('```html', '').replace('```', '').strip()
                    
                    del_content += ai_delivery_html
                    del_content += "</div>\n" # 🚨 전체 순위 카드 닫기 (이중 겹박스를 뺐으므로 </div> 한 개만 닫습니다)

            del_content += "</div>\n" # display:flex 컨테이너 닫기

            closing_del_html = f"""<div style='margin-top: 20px;'>
<p style='font-size:15px; text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>사랑하는 부부님, 이 세 가지 출산 희망일은 각각 독특하고 고귀한 기운을 담고 있습니다. 하늘의 뜻과 부모님의 깊은 사랑, 그리고 제가 바친 노력이 한데 어우러져 귀한 아기가 이 세상에 가장 찬란하게 빛을 발하며 첫걸음을 내딛기를 진심으로 기원합니다.</p>
<p style='font-size:15px; text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>어떤 날을 선택하시든, 그 선택은 아기에게 최고의 축복이 될 것입니다. 아기의 탄생으로 가정이 더욱 행복하고 번창하시기를 간절히 축원합니다.</p>
<div style='text-align: right; margin-top: 25px;'>
<span style='font-weight: 900; font-size: 18px; color: #4A148C; font-family: "Nanum Myeongjo", serif;'>초연 시공명리 연구소</span>
</div>
</div>"""

            del_content += f"<div class='content-box-loose' style='font-size:15px; line-height:1.8; margin-top:20px;'>\n{closing_del_html}\n</div>"

            # 🚨 [긴급 복구] 표지와 개인사주를 망가뜨리던 전역 CSS 폭탄을 완전히 제거했습니다.
            def wrap_a4_del(content, title_color="#4A148C"):
                return f"<div class='report-page'>\n<div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'>\n{content}\n</div>\n</div>"

            st.session_state['saved_report_del'] = wrap_a4_del(del_content)
            st.session_state['run_delivery_only'] = False
            st.rerun()

        except Exception as e:
            st.error(f"출산택일 연산 장애: {e}")
            st.session_state['run_delivery_only'] = False
# ==============================================================================
# 📺 9. 화면 출력부 (순수 모니터 역할)
# ==============================================================================
if st.session_state.get('app_running', False):
    
    # 1. 개인사주 출력
    if u_product == "개인사주":
        st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
        if st.session_state.get('saved_report_iljin'):
            st.markdown(st.session_state.get('saved_report_iljin', ''), unsafe_allow_html=True)
    
    # 2. 타 감명서 출력
    if u_product == "타 감명서":
        st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
        st.markdown(st.session_state.get('saved_report_2', ''), unsafe_allow_html=True)
        
    # 3. 궁합 출력
    if u_product == "궁합":
        if st.session_state.get('saved_report_gh_cover'):
            st.markdown(st.session_state.get('saved_report_gh_cover', ''), unsafe_allow_html=True)
            st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
            
        st.markdown(st.session_state.get('saved_report_gh_m', ''), unsafe_allow_html=True)
        st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
        st.markdown(st.session_state.get('saved_report_gh_f', ''), unsafe_allow_html=True)
        st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
        st.markdown(st.session_state.get('saved_report_gh_g', ''), unsafe_allow_html=True)

        # 🚨 [수술 완료] 연산 찌꺼기 제거 및 생성된 출산택일 리포트 결합 출력
        if st.session_state.get('saved_report_del'):
            st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
            st.markdown(st.session_state.get('saved_report_del', ''), unsafe_allow_html=True)
