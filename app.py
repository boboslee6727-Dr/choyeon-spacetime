import streamlit as st
import pandas as pd
import json
import os
import re
import math
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import ephem
import google.generativeai as genai
import streamlit.components.v1 as components

# ==============================================================================
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS (Ver 15.0 최적화 껍데기 계승)
# ==============================================================================
st.set_page_config(page_title="초연 AI 시공명리 사주풀이 Ver 509.0", layout="wide")

st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&family=Nanum+Myeongjo:wght@400;700;800&display=swap");
    
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
    
    .vip-box-loose { border: 3px solid #6D4C41; padding: 25px; border-radius: 8px; margin-bottom: 20px; background-color: #FAFAFA; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
    .rtl-scroll-container { display: flex; flex-direction: row-reverse; flex-wrap: nowrap !important; justify-content: flex-start; width: 100%; overflow: hidden; border: 2px solid #3E2723; margin-bottom: 5px; background: white; }
    .dw-sn-col { flex: 1 1 10%; min-width: 0; border-left: 1px solid #444; }
    .mn-col { flex: 1 1 8.33%; min-width: 0; border-left: 1px solid #444; }
    .active-un { outline: 3px solid #D50000 !important; outline-offset: -3px; background-color: #FFEBEE !important; position: relative; z-index: 2;}
    .inner-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    .inner-table td { border: 1px solid #eee; padding: 0px !important; text-align: center; font-weight: 900 !important; font-size: 12px !important; line-height: 1.1 !important; }
    .dw-age-head { background: #3E2723; color: white; height: 16px; font-size: 12px !important; }
    .seun-year-head { background: #1A237E; color: white; height: 16px; font-size: 12px !important; }
    .month-head { background: #004D40; color: white; height: 16px; font-size: 12px !important; }
    .standalone-master-box { border: 2px solid #3E2723; background-color: #FFF8E1; padding: 8px; display: flex; justify-content: space-between; font-size: 12px; font-weight: 900 !important; margin-bottom: 15px; border-radius: 8px; white-space: nowrap;}
    .un-title { font-weight: 900; font-size: 15px !important; margin-top: 15px !important; margin-bottom: 5px !important; color: #3E2723; }

    div[data-testid="stSidebar"] div.stButton > button:first-child { background-color: #D50000; color: white; border: none; font-weight: 900; height: 45px; }
    div[data-testid="stSidebar"] .navy-btn button { background-color: #1A237E !important; color: white !important; border: none !important; font-weight: 900 !important; height: 45px; }
    
    @media print {
        @page { size: A4 portrait; margin: 15mm; }
        .stSidebar, button, iframe, .print-hide, header, .no-print { display: none !important; }
        body, .stApp { background-color: white !important; }
        .report-page { 
            box-shadow: none; margin: 0 auto !important; padding: 10px !important; 
            page-break-after: always !important; 
            border-radius: 0; width: 100%; max-width: 100%; height: auto !important;
        }
        .report-page:last-of-type { page-break-after: auto !important; }
        .page-break-before { page-break-before: always; }
        .vip-inset-frame { border: 2px solid #000; border-radius: 20px; padding: 15px; }
        .vip-box-loose, .content-box-loose { -webkit-box-decoration-break: clone !important; box-decoration-break: clone !important; }
        h1, h2, h3, .un-title { page-break-after: avoid; }
        table, .standalone-master-box { page-break-inside: avoid; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 0.5. [초연 시공명리 5대 DB 도서관 로딩 엔진] (MyDrive 경로 탈피 ➡️ 캐싱 로컬 연동)
# ==============================================================================
# [설계 원칙] 박사님의 5대 비급 텍스트 파일을 app.py와 같은 폴더에 저장해 두어야 함.
DB_PATHS = {
    'wol': "60월령DB_(0505).txt",
    'ilju': "60일주DB_(0417).txt",
    'hch': "4자평_합충형해파v9.txt",
    'shinsal': "2자평_신살명리학v8.txt",
    'stru': "60일주_구조_유형_성격_(0406).txt"
}
JSON_DB_PATH = "choyeon_db.json"

@st.cache_data
def sync_and_load_choyeon_database():
    """웹 서버 부하를 줄이기 위해, 최초 1회만 TXT를 파싱하여 고속 JSON DB로 자동 동기화 및 로드"""
    if os.path.exists(JSON_DB_PATH):
        try:
            with open(JSON_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass

    def load_txt(path):
        if not os.path.exists(path): return ""
        with open(path, 'r', encoding='utf-8-sig', errors='ignore') as f: return f.read()

    def parse_sections(text):
        if not text: return {}
        pattern = r'(?:\[\s*\d{1,2}\s*\]|\d{1,2}\.)\s*([^\n\r:]+)'
        raw_sections = re.split(pattern, text)
        keys = re.findall(pattern, text)
        result = {}
        contents = [s.strip() for s in raw_sections[1:]]
        for key, content in zip(keys, contents):
            clean_key = key.replace('일주', '').strip()
            if clean_key and content: result[clean_key] = content
        return result

    db = {"wolryeong": {}, "ilju": {}, "structure": {}, "hch": "", "shinsal": ""}
    db['wolryeong'] = parse_sections(load_txt(DB_PATHS['wol']))
    db['ilju'] = parse_sections(load_txt(DB_PATHS['ilju']))
    db['structure'] = parse_sections(load_txt(DB_PATHS['stru']))
    for key in ['hch', 'shinsal']: 
        db[key] = load_txt(DB_PATHS[key])

    try:
        with open(JSON_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except: pass
    return db

CHOYEON_DB = sync_and_load_choyeon_database()

# ==============================================================================
# 0.7. [시공명리 핵심 운세 분석 이론] 체(體)와 용(用) 매트릭스 백엔드 엔진
# ==============================================================================
EXEC_DB = {
    '비겁': {'비겁':'식상발흥, 직무개척, 건강호조, 출산운, 처가와 유정', '식상':'업무원만, 진취력, 건강호조, 원행(遠行), 발표, 여행', '재성':'손재, 소비, 이성난, 가정불화, 부친반목', '관성':'설화, 관재, 가족불화, 직장문제, 공명심', '인성':'의식주안정, 스카우트, 계약, 학업순성, 합격, 가정화목'},
    '식상': {'비겁':'사업원만, 결과만족, 명진(名振), 의기투합, 긍정심', '식상':'재성발흥, 재적성취, 이성운, 가정원만, 재물입고, 환대', '재성':'이재순성, 사업원만, 인연, 가족화목, 건강, 횡재', '관성':'건강악화, 직업불안, 직주이동, 관재, 설화, 가족불화', '인성':'직업불안, 건강문제, 계약파기, 학문불안, 의식주 불안'},
    '재성': {'비겁':'일득삼재, 손재, 부부갈등, 과소비, 업무지연', '식상':'여행, 결과만족, 횡재수, 가정화목, 득자운', '재성':'관성발흥, 직업운 상승, 이성운 순성, 가정원만', '관성':'신분상승, 출마, 천거, 장기출장, 가정화목, 이성운', '인성':'매사불성, 소비지출, 가족불화, 계약파기, 손재, 흉사'},
    '관성': {'비겁':'업무지연, 관재, 설화, 다툼, 허언, 선민의식', '식상':'명예훼손, 직업이동, 질책, 가족불화, 이성난', '재성':'사업운 원만, 이성운 순성, 가정원만, 취업, 명예', '관성':'인성발흥, 승진승급, 계약성사, 자식운 원만', '인성':'합격, 승진, 계약, 스카우트, 의식주 안정, 당선'},
    '인성': {'비겁':'건강호조, 학업원만, 신분상승, 당선, 명예, 안정', '식상':'불안정, 계약파기, 학업불성, 구설, 육친흉사, 자식불효', '재성':'지출, 탈재, 파재, 사기수, 손재, 분주다망, 시성종패', '관성':'업무원활, 학업성취, 승진승급, 영전, 합격, 포상', '인성':'비겁발흥, 명예, 명진, 칭찬, 주체성 확립, 학문성취'}
}

class ChoYeonMyeongriEngine:
    def __init__(self):
        self.secret_matrix = EXEC_DB
    def get_secret_keywords(self, che_sung, yong_sung):
        return self.secret_matrix.get(che_sung, {}).get(yong_sung, '변동성 속에서 내면의 중심을 잡고 시공간의 흐름에 순응하십시오.')

cy_engine = ChoYeonMyeongriEngine()

# [안내] 다음 파트(2단계: 만세력 하위 함수 연산 및 입력 단) 이식 수술 대기 중.
# ==============================================================================
# 1. 시스템 변수 세팅 및 써머타임 엔진 (Ver 15.0 계승)
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
# 2. AI 설정 및 초연 명리 연산 엔진 (Ver 15.0 + 509.0 융합)
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

# [Ver 509.0 융합] 십성을 체용 5대 그룹으로 묶는 함수
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

# [Ver 509.0 융합] 묘고(입고/개고) 스캔 함수
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

# [Ver 15.0 사수] 10분 단위 초정밀 세차운동 보정 대운수 엔진
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

# [안내] 다음 파트(3단계: UI 사이드바 및 입력 수집부) 이식 수술 대기 중.

# ==============================================================================
# 3. 사이드바 UI 및 입력 폼 통제실 (Ver 15.0 UI 껍데기 + Ver 509.0 궁합 확장)
# ==============================================================================
with st.sidebar:
    st.title("🧪 초연 시공명리 연구소")
    st.caption("Ver 509.0 Spacetime Masterpiece")
    
    # [Ver 15.0 계승] 사주팔자 역산 검색기
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
                klc_find = KoreanLunarCalendar()
                found = False
                for y in range(2026, 1899, -1):
                    klc_find.setSolarDate(y, 7, 1)
                    gj_y = klc_find.getChineseGapJaString().split()
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
                                st.success(f"✅ [양력] {curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일 입력완료!")
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                        if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.error("간지를 정확히 입력하세요.")

    st.markdown("---")
    
    # [Ver 509.0 이식] 상품 선택 콤보박스 (개인사주 vs 궁합)
    u_product = st.selectbox("📋 분석 상품 선택", ["개인사주", "궁합"])
    
    st.markdown("<div style='font-weight:900; color:#1A237E; margin-bottom:5px;'>👤 신청인 정보 (공통)</div>", unsafe_allow_html=True)
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
    
    # [Ver 509.0 이식] 궁합 선택 시 동적으로 열리는 상대방 입력창 인터페이스
    p_name, p_gender, p_marital, p_cal, p_y, p_m, p_d, p_t = "", "여성", "미혼", "양력", 1967, 9, 24, "시간 모름"
    if u_product == "궁합":
        st.markdown("---")
        st.markdown("<div style='font-weight:900; color:#C62828; margin-bottom:5px;'>💕 상대방 정보</div>", unsafe_allow_html=True)
        p_name = st.text_input("상대방 이름", value="", placeholder="이영희")
        
        # 신청인 성별의 반대성별을 기본값으로 지혜롭게 세팅
        p_gender_default = "여성" if u_gender == "남성" else "남성"
        p_gender = st.selectbox("상대방 성별", ["남성", "여성"], index=["남성", "여성"].index(p_gender_default))
        p_marital = st.selectbox("상대방 혼인여부", ["미혼", "기혼", "돌싱"])
        p_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"])
        
        p_col1, p_col2, p_col3 = st.columns(3)
        p_y = p_col1.number_input("상대방 년", 1900, 2030, value=1967)
        p_m = p_col2.number_input("상대방 월", 1, 12, value=9)
        p_d = p_col3.number_input("상대방 일", 1, 31, value=24)
        p_t = st.selectbox("상대방 태어난 시간", idx_list, key="p_t_key")
        
    st.markdown("<br>", unsafe_allow_html=True)
    btn_single = st.button("🚀 초연 시공명리 가동", use_container_width=True, type="primary")

# [안내] 다음 파트(4단계: 핵심 데이터 추출 브릿지 및 연산부) 이식 수술 대기 중.
# ==============================================================================
# 4. 분석 가동 및 데이터 브릿지 엔진 (DB 추출 + 표지 렌더링)
# ==============================================================================
if btn_single:
    if not u_name.strip():
        st.warning("⚠️ 신청인의 이름을 입력해 주세요.")
    elif u_product == "궁합" and not p_name.strip():
        st.warning("⚠️ 상대방의 이름을 입력해 주세요.")
    else:
        with st.spinner("🔮 초연 시공명리 알고리즘 가동 중..."):
            # [4.1] 기본 날짜 및 천문 연산 (신청인)
            klc = KoreanLunarCalendar()
            if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
            elif u_cal == "음력(평달)": klc.setLunarDate(u_y, u_m, u_d, False)
            else: klc.setLunarDate(u_y, u_m, u_d, True)
            
            # 기준 시각 설정 (Ver 15.0의 정밀 보정 기술 적용)
            b_hr, b_mn = 12, 30
            if u_t != "시간 모름":
                try: b_hr = int(u_t.split(':')[0])
                except: pass
            
            # UTC 변환 및 대운수 산출
            in_dt = dt_mod.datetime(klc.solarYear, klc.solarMonth, klc.solarDay, b_hr, b_mn)
            adj_mins = get_total_time_adjustment(in_dt)
            utc_dt = in_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            
            # 간지 도출
            gj = klc.getChineseGapJaString().split()
            ys, yb, ms, mb, ds, db = gj[0][0], gj[0][1], gj[1][0], gj[1][1], gj[2][0], gj[2][1]
            hs, hb = get_time_ganji(ds, u_t, in_dt)
            
            gans, jjis = [hs, ds, ms, ys], [hb, db, mb, yb]
            order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
            calc_d = get_daeun_su_accurate(utc_dt, order)
            
            # [4.2] 시공명리 5대 DB 팩트 낚아채기 (Context Extraction)
            wol_key = ms + mb
            ilju_key = ds + db
            
            wol_db_text = CHOYEON_DB['wolryeong'].get(wol_key, "해당 월령 데이터를 도서관에서 찾을 수 없습니다.")
            ilju_db_text = CHOYEON_DB['ilju'].get(ilju_key, "해당 일주 데이터를 도서관에서 찾을 수 없습니다.")
            stru_db_text = CHOYEON_DB['structure'].get(ilju_key, "해당 구조 분석 데이터를 찾을 수 없습니다.")
            
            # [4.3] 시공간 타격 및 묘고 스캔
            curr_dt_sys = dt_mod.datetime.now()
            # 이번 달 지지 도출
            wol_jis_map = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]
            cur_month_ji = wol_jis_map[curr_dt_sys.month - 1]
            vault_scan = check_vault_status(gans, jjis, cur_month_ji)
            vault_summary = " / ".join(vault_scan) if vault_scan else "현재 시공간에서 특이 묘고(무덤) 동태 없음"

            # [4.4] 프리미엄 표지(Cover Page) 렌더링 - Ver 509.0 감성 완벽 살리기
            today_str = curr_dt_sys.strftime("%Y년 %m월 %d일")
            sol_str = f"{klc.solarYear}년 {klc.solarMonth:02d}월 {klc.solarDay:02d}일"
            is_leap = getattr(klc, 'isIntercalary', False)
            lun_str = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({'윤달' if is_leap else '평달'})"
            u_age = curr_dt_sys.year - u_y + 1
            
            # 인쇄용 표지 HTML (메인 도화지에 출력)
            if u_product == "개인사주":
                cover_html = f"""
                <div class='report-page'>
                    <div style='height: 240mm; display: flex; flex-direction: column; justify-content: center; align-items: center; border: 4px solid #1A237E; border-radius: 20px; padding: 40px; background: white;'>
                        <div style='border-bottom: 4px double #1A237E; padding-bottom: 20px; margin-bottom: 50px; text-align: center; width: 80%;'>
                            <h1 style='font-size: 38px; color: #1A237E; font-weight: 900; margin: 0;'>🏮 초연 AI 시공명리 사주감명</h1>
                            <p style='font-size: 18px; color: #333; margin-top: 10px; font-weight: 600;'>[ Spacetime Myeongri Premium Report ]</p>
                        </div>
                        <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 40px 30px; border-radius: 15px; width: 70%; text-align: center;'>
                            <h2 style='font-size: 28px; font-weight: 900; color: #1A237E; margin-bottom: 20px;'>신청인 : {u_name} 님</h2>
                            <div style='font-size: 17px; font-weight: 600; color: #333; line-height: 2.0;'>
                                <p style='margin: 0;'>[성별/나이] {u_gender} / {u_age}세 ({u_marital})</p>
                                <p style='margin: 0;'>[양력] {sol_str}</p>
                                <p style='margin: 0;'>[음력] {lun_str}</p>
                                <p style='margin: 10px 0 0 0; color: #D50000; font-size: 14px;'>| [시차보정] {adj_mins}분 적용 완료 |</p>
                            </div>
                        </div>
                        <div style='margin-top: 70px; text-align: center;'>
                            <p style='font-size: 18px; font-weight: bold; color: #555;'>{today_str}</p>
                            <h2 style='font-size: 24px; font-weight: 900; color: #1A237E; margin-top: 10px;'>초연 시공명리 연구소</h2>
                        </div>
                    </div>
                </div>
                """
                st.markdown(cover_html, unsafe_allow_html=True)
            
            # [안내] 다음 파트(5단계: AI 대형 프롬프트 빌더 및 출력 조립) 수술 대기 중.
# ==============================================================================
            # 5. [최종 엔진] 시공명리 프롬프트 빌드 및 화면 출력 (Ver 15.0 + 509.0 융합)
            # ==============================================================================
            n_gong = calculate_gongmang(ys, yb)
            i_gong = calculate_gongmang(ds, db)
            
            counts = {"목":0,"화":0,"토":0,"금":0,"수":0}
            for char in gans + jjis:
                if char != "?": counts[get_color(char)] += 1
                
            guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
            guiin_str = guiin_map.get(ds, '없음')
            
            # [5.1] 표 및 UI 요소 생성
            master_bar_html = f"<div class='standalone-master-box' style='border:2px solid #3E2723; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap; margin-bottom:15px;'><div>⏳ 대운수: {calc_d}</div><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin_str}</div><div>🎯 공망: [년] {n_gong} &nbsp;|&nbsp; [일] {i_gong}</div></div>"
            
            def td(c, size="18px"): return f"<td class='color-{get_color(c)}' style='font-size:{size}; font-weight:900; border:1px solid #444 !important;'>{('?' if c in ['?',' ','-'] else c)}</td>"
            
            ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444" if l_idx == 3 else "none"
                cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:none !important; border-bottom:{b_bot} !important; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important;'>합충형파해</td>" if l_idx==0 else ""
                ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

            table_html = f"""<table class='result-table' style='page-break-inside: avoid;'>
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

            # 대운, 세운, 월운 표 생성
            direction_str = "순행" if order == 1 else "역행"
            daewun_info, sewun_info = [], []
            un_html = f"<h4 style='color:#1A237E; margin-top:20px; page-break-after: avoid;'>11. 운의 흐름</h4><div style='margin-bottom:10px; font-weight:bold;'>[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]</div><div class='rtl-scroll-container'>"
            for i in range(10):
                val, c, j = i*10+calc_d, GAN[(GAN.index(ms)+(i+1)*order)%10] if ms in GAN else "-", JI[(JI.index(mb)+(i+1)*order)%12] if mb in JI else "-"
                daewun_info.append(f"{val}세:{c}{j}")
                is_active = val <= u_age < val+10
                bg_col = "#FFEBEE" if is_active else "transparent"
                un_html += f"<div class='dw-sn-col' style='background-color:{bg_col}; outline: {'3px solid #D50000' if is_active else 'none'};'><table class='inner-table'><tr><td class='dw-age-head'>{val}세</td></tr><tr><td>{get_ss(ds,c)}</td></tr><tr><td class='color-{get_color(c)}' style='font-size:16px !important;'>{c}</td></tr><tr><td class='color-{get_color(j)}' style='font-size:16px !important;'>{j}</td></tr><tr><td>{get_ss(ds,j)}</td></tr><tr><td style='color:#0D47A1;'>{get_unsung(ds,j)}</td></tr><tr><td style='color:#C62828;'>{get_12_shinsal(yb, j)}</td></tr></table></div>"
            un_html += "</div>"

            cur_dw_idx = max(0, (u_age - calc_d) // 10)
            current_daewun_age = cur_dw_idx * 10 + calc_d
            start_year = u_y + current_daewun_age - 1
            curr_y, curr_m = curr_dt_sys.year, curr_dt_sys.month
            
            se_html = f"<div style='margin-top:20px; margin-bottom:10px; font-weight:bold; page-break-after: avoid;'>[ 세운의 흐름 ({current_daewun_age}세 대운 기준) ]</div><div class='rtl-scroll-container'>"
            for i in range(10):
                ty = start_year + i
                base = (ty - 1984) % 60
                tc, tj = GAN[base % 10], JI[base % 12]
                sewun_info.append(f"{ty}년({tc}{tj})")
                is_cur_yr = (ty == curr_y)
                bg_col = "#FFEBEE" if is_cur_yr else "transparent"
                se_html += f"<div class='dw-sn-col' style='background-color:{bg_col}; outline: {'3px solid #D50000' if is_cur_yr else 'none'};'><table class='inner-table'><tr><td class='seun-year-head'>{ty}년</td></tr><tr><td>{get_ss(ds,tc)}</td></tr><tr><td class='color-{get_color(tc)}' style='font-size:16px !important;'>{tc}</td></tr><tr><td class='color-{get_color(tj)}' style='font-size:16px !important;'>{tj}</td></tr><tr><td>{get_ss(ds,tj)}</td></tr><tr><td style='color:#0D47A1;'>{get_unsung(ds,tj)}</td></tr><tr><td style='color:#C62828;'>{get_12_shinsal(yb, tj)}</td></tr></table></div>"
            se_html += "</div>"
            
            wol_gans = ["己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚"]
            wol_jis = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]
            
            wol_html = f"<div style='margin-top:20px; margin-bottom:10px; font-weight:bold; page-break-after: avoid;'>[ 월운의 흐름 ({curr_y}년 양력기준) ]</div><div class='rtl-scroll-container'>"
            for i in range(12):
                tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
                is_cur_m = (tm == curr_m)
                bg_col = "#FFEBEE" if is_cur_m else "transparent"
                wol_html += f"<div class='mn-col' style='background-color:{bg_col}; outline: {'3px solid #D50000' if is_cur_m else 'none'};'><table class='inner-table'><tr><td class='month-head'>{tm}월</td></tr><tr><td>{get_ss(ds,tc)}</td></tr><tr><td class='color-{get_color(tc)}' style='font-size:16px !important;'>{tc}</td></tr><tr><td class='color-{get_color(tj)}' style='font-size:16px !important;'>{tj}</td></tr><tr><td>{get_ss(ds,tj)}</td></tr><tr><td style='color:#0D47A1;'>{get_unsung(ds,tj)}</td></tr><tr><td style='color:#C62828;'>{get_12_shinsal(yb, tj)}</td></tr></table></div>"
            wol_html += "</div>"

            # [5.2] 연령/성별 맞춤형 프롬프트 타겟팅
            age_prompt = "내담자는 [청소년기(10대)]입니다. 학업과 부모운을 최우선으로 상세히 분석하십시오." if u_age < 20 else \
                         "내담자는 [청년기(20~30대)]입니다. 적성과 직업운, 연애/결혼운을 상세히 분석하십시오." if u_age < 40 else \
                         "내담자는 [중장년기(40~50대)]입니다. 인생의 황금기인 재물운과 사회적 관직/사업운을 가장 상세히 서술하십시오." if u_age < 60 else \
                         "내담자는 [노년기(60대 이상)]입니다. 건강운과 안정적인 자산 관리 유지에 중점을 두어 서술하십시오."
            gender_prompt = "내담자는 [남성]입니다. 재성과 관성을 남성의 사회적 역할과 가장의 책임에 맞춰 통변하십시오." if u_gender == "남성" else \
                            "내담자는 [여성]입니다. 식상과 관성의 조화를 통해 현대 여성의 독립적 성취를 강조하십시오."
                            
            # [5.3] 시공명리 통합 프롬프트 
            prompt = f"""
[절대 규칙]
1. 현재 시스템 시간: {curr_y}년 {curr_m}월
2. 응답의 첫 글자는 무조건 <h3 style='color:#1A237E; page-break-after: avoid;'>1. 사주팔자 구조 분석</h3> 으로 시작하십시오. (인사말 절대 금지)
3. 절대 들여쓰기(Tab)나 마크다운 기호(*, **)를 문장 맨 앞에 넣지 마십시오. HTML 표기를 흩뜨리지 마십시오.
4. [DAEWUN_TABLE_HERE] 등 마커는 시스템 치환용이므로 절대 지우지 마십시오.
5. 모든 문장에서 '내담자'라는 단어 대신 반드시 [{u_name}님]을 사용하십시오. 혼인 상태는 '{u_marital}'입니다.

[🚨 시공명리 5대 도서관 팩트 기반 강제 통변 지시]
다음 제공된 초연 박사님의 정품 DB 자료를 **최우선 뼈대**로 삼아 11단계 분석 에세이를 작성하십시오. AI 임의의 지식이나 환각을 섞지 마십시오.
- 📖 [월령 DB (환경/무대)]: {wol_db_text}
- 📖 [일주 DB (성품/속마음)]: {ilju_db_text}
- 📖 [구조 분석 DB]: {stru_db_text}
- 🚨 [현재 시공간 묘고(무덤) 스캔 팩트]: {vault_summary} (운세 분석 시 이 묘고의 열림/닫힘 현상을 현실 사건과 엮어 서술할 것)

[🔥 시공명리 운세 분석 방법론 (체용 분석법 강제)]
'11. 운의 흐름' 파트를 작성할 때, 대운과 세운을 단순한 길흉으로 논하지 마십시오. 반드시 다음 두 가지 관점을 융합하여 서술하십시오.
- 체(體): 해당 시기에 하늘이 명주에게 부여한 '사회적 무대와 환경적 분위기'
- 용(用): 명주가 이 환경 속에서 취해야 할 '현실적인 대처 방안과 실행력'
- [과거 분석 양식 규칙]: 과거 운 서술 시, 줄 맨 앞에 도트(•)를 찍고 한 칸 띄운 후 요약하되, 각 분석이 끝나면 반드시 '엔터 2번(빈 줄)'을 넣어 문단 간격을 확보하십시오. (마크다운 ** 기호 절대 금지)

[출력 템플릿 - 이 11단계 목차명과 구조를 100% 동일하게 복사하여 출력할 것]
<h3 style='color:#1A237E; page-break-after: avoid;'>1. 사주팔자 구조 분석</h3>
<div class='content-box-loose'>
<p>1) 타고난 삶의 무대와 기본 성향 (월령 DB 활용)</p>
<p>2) 내 삶의 온도와 에너지 균형 (조후/억부)</p>
<p>3) 사주팔자의 역동적 관계 분석 (합형충파해 팩트 기반)</p>
</div>
<h3 style='color:#1A237E; page-break-after: avoid;'>2. 성격</h3>
<div class='content-box-loose'>
<p>1) 겉으로 드러난 성격 (일주 DB 활용)</p>
<p>2) 감추어진 진짜 속마음 (공망 {i_gong}의 결핍 활용)</p>
</div>
<h3 style='color:#1A237E; page-break-after: avoid;'>3. 부모·형제운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E; page-break-after: avoid;'>4. 학업·진학운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E; page-break-after: avoid;'>5. 적성·직업운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E; page-break-after: avoid;'>6. 결혼·자녀운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E; page-break-after: avoid;'>7. 사업운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E; page-break-after: avoid;'>8. 관직·명예운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E; page-break-after: avoid;'>9. 재성운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E; page-break-after: avoid;'>10. 건강운</h3><div class='content-box-loose'></div>

[DAEWUN_TABLE_HERE]
<div class='content-box-loose'>
<p>▶ 지나온 각 과거 대운 요약 (도트 양식 및 빈 줄 간격 엄수)</p>
<p>▶ 현재 대운 상세 분석 (체와 용의 관점)</p>
</div>
[SEWUN_TABLE_HERE]
<div class='content-box-loose'>
<p>▶ 지나온 각 과거 세운 요약 (도트 양식 및 빈 줄 간격 엄수)</p>
<p>▶ 올해({curr_y}년) 세운 분석 (묘고 스캔 팩트 타격 포함)</p>
</div>
[WOLWUN_TABLE_HERE]
<div class='content-box-loose'>
<p>▶ 과거 월운 요약</p>
<p>▶ 이번 달({curr_m}월) 분석</p>
</div>

<h3 style='color:#1A237E; margin-top:30px; page-break-after: avoid;'>12. 삶을 바꾸는 지혜로운 조언</h3>
<div class='content-box-loose'>
<p>◈ 나를 돕는 에너지와 색상:</p>
<p>◈ 신체 밸런스와 방위의 지혜:</p>
<p>◈ 공간의 흐름과 방위의 지혜:</p>
<p>◈ 재능 효율을 높이는 직업적 지혜:</p>
<p>◈ 더 나은 내일을 위한 절제의 미학:</p>
<div style='margin-top:20px; margin-bottom:10px;'><span style='color:#1A237E; font-weight:900;'>[초연 시공명리 특별 개운 비법]</span></div>
<p>◈ 수호 천사의 기운:</p>
<p>◈ 행운에 따른 기운:</p>
</div>
"""
            
            try:
                # AI 통신 가동
                res = model.generate_content(prompt)
                ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                
                # HTML 표 치환
                ai_text = ai_text.replace("[DAEWUN_TABLE_HERE]", un_html).replace("[SEWUN_TABLE_HERE]", se_html).replace("[WOLWUN_TABLE_HERE]", wol_html)
                
                # 안전망: 마커 누락 시 표를 최상단에 배치
                if un_html not in ai_text:
                    ai_text = un_html + se_html + wol_html + "<div style='color:red;'>⚠️ AI가 템플릿 마커를 누락하여 표가 최상단에 강제 출력되었습니다.</div>" + ai_text

                # 최종 리포트 조립 (표지 제외 - 4단계에서 이미 출력됨)
                report_1_full_html = f"""
                <div class='report-page' style='margin-top: 10px !important;'>
                    <div class='vip-inset-frame' style='border-color:#1A237E;'>
                        {table_html}
                        {master_bar_html}
                        <div style='margin-top:20px;'>
                            {ai_text}
                            <div style='margin-top: 40px; padding-top: 20px; border-top: 1px dashed #CCC;'>
                                <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자(命)'는 태어날 때 부여받은 변하지 않는 '바코드(bar-code)'와 같지만, 우리가 살아가며 마주하는 '스캐너(scanner)'인 '운(運)'은 늘 변화하며 흐릅니다.</p>
                                <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{u_name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
                                <div style='text-align: right; margin-top: 30px;'>
                                    <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>"""
                
                # 스승님 전용 폭포수 통제실 버튼 UI (출력단 최하단)
                print_btn_html = "<div class='no-print' style='text-align: center; margin: 40px 0 20px 0; padding: 20px; border: 2px solid #1A237E; background-color: #f8f9fa; border-radius: 8px;'><h4 style='margin-bottom: 10px; color: #1A237E; font-weight: 900;'>🖨️ 초연 시공명리 감명서 출력</h4><button onclick='window.focus(); window.print()' style='padding: 12px 35px; background-color: #3E2723; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: 900; font-size: 16px; box-shadow: 0px 4px 6px rgba(0,0,0,0.3);'>감명서 인쇄 / PDF 저장</button></div>"
                
                # 최종 화면 렌더링
                st.markdown(report_1_full_html, unsafe_allow_html=True)
                components.html(print_btn_html, height=150)
                
            except Exception as e: 
                st.error(f"AI 연산 및 출력 오류: {e}")

# ==============================================================================
# 6. 프리미엄 궁합 전용 엔진 (UniversalPrintableGunghap) 및 가동 로직
# ==============================================================================
class UniversalPrintableGunghap:
    def __init__(self, applicant, partner_name, male, female, daeun_score=10):
        self.app, self.p_name, self.daeun_score = applicant, partner_name, daeun_score
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
                    ss = get_group_ss(get_ss(dc, c))
                    if ss in res: res[ss] += 1
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
        
        return f"""
        <div class='report-page' style='padding:40px; background:#fff;'>
            <div style='text-align:center; border-bottom:4px double #3E2723; padding-bottom:15px; margin-bottom:30px;'>
                <h1 style='margin:0; color:#3E2723; font-family: "Malgun Gothic", sans-serif; font-weight: 900;'>💞 초연 시공명리 종합 궁합풀이</h1>
            </div>
            <div style='background-color: #FAFAFA; padding: 40px; border: 2px solid #1A237E; border-radius: 15px; margin-bottom: 40px;'>
                <div class='content-box-loose' style='margin-bottom: 50px;'>
                    {ai_text}
                </div>
                <h2 style='text-align:center; margin-top:0; color:#333; font-family: "Malgun Gothic", sans-serif; font-weight: 900; font-size: 22px; margin-bottom: 25px;'>📊 최종 궁합 점수</h2>
                <div style='display:flex; justify-content:center; align-items:center; margin-bottom:20px;'>
                    <div style='width:130px; height:130px; border-radius:50%; background:conic-gradient({c} {self.final_score}%, #f0f0f0 0); display:flex; justify-content:center; align-items:center;'>
                        <div style='width:98px; height:98px; background:#fff; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
                            <span style='font-size:32px; font-weight:900; color:{c};'>{self.final_score}</span>
                        </div>
                    </div>
                </div>
                <div style='text-align:center; margin-bottom:25px;'>
                    <span style='font-size:16px; font-weight:bold; color:#fff; background:{c}; padding:8px 32px; border-radius:30px; display: inline-block;'>{self.grade}</span>
                </div>
                <div style='max-width:500px; margin:0 auto; margin-bottom: 20px;'>
                    {bars_html}
                </div>
            </div>
        </div>"""

# --- 궁합 버튼 가동 로직 (btn_single 블록 내부에 들여쓰기 맞춰 삽입 완료 처리) ---
if btn_single and u_product == "궁합":
    with st.spinner("💕 두 분의 시공간을 교차하여 궁합을 분석 중입니다..."):
        # 상대방 데이터 기본 연산 (간략화된 예시)
        p_klc = KoreanLunarCalendar()
        if p_cal == "양력": p_klc.setSolarDate(p_y, p_m, p_d)
        else: p_klc.setLunarDate(p_y, p_m, p_d, False)
        
        p_in_dt = dt_mod.datetime(p_klc.solarYear, p_klc.solarMonth, p_klc.solarDay, 12, 30)
        p_gj = p_klc.getChineseGapJaString().split()
        p_ys, p_yb, p_ms, p_mb, p_ds, p_db = p_gj[0][0], p_gj[0][1], p_gj[1][0], p_gj[1][1], p_gj[2][0], p_gj[2][1]
        p_hs, p_hb = get_time_ganji(p_ds, p_t, p_in_dt)
        
        # 궁합 스코어링 모듈 가동
        m_pillars, f_pillars = ([hs, ds, ms, ys], [hb, db, mb, yb]), ([p_hs, p_ds, p_ms, p_ys], [p_hb, p_db, p_mb, p_yb])
        if u_gender == "여성": m_pillars, f_pillars = f_pillars, m_pillars
        
        gh_engine = UniversalPrintableGunghap(u_name, p_name, m_pillars, f_pillars)
        gh_engine.run_universal_logic()
        
        # 궁합 전용 AI 프롬프트 (점수에 따른 분석)
        gh_prompt = f"""
        당신은 명리심리상담사 '초연 박사'입니다.
        신청인 {u_name}님과 상대방 {p_name}님의 궁합을 분석하십시오.
        시스템 산출 최종 궁합 점수: {gh_engine.final_score}점 ({gh_engine.grade})
        
        이 점수를 기반으로 두 사람의 '내면의 유대감', '환경 조화', '기운 상호보완'을 3문단으로 품격 있게 서술하십시오.
        점수 자체는 본문에 노출하지 마십시오.
        """
        try:
            gh_res = model.generate_content(gh_prompt)
            st.markdown(gh_engine.get_graphic_html(gh_res.text), unsafe_allow_html=True)
            components.html("<div class='no-print' style='text-align: center; margin: 40px 0;'><button onclick='window.focus(); window.print()' style='padding: 12px 35px; background-color: #3E2723; color: white; font-weight: 900; border: none; border-radius: 5px; cursor: pointer;'>궁합 감명서 인쇄 / PDF 저장</button></div>", height=100)
        except Exception as e:
            st.error(f"궁합 AI 분석 중 오류가 발생했습니다: {e}")



