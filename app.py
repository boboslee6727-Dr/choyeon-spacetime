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
# 0. VIP 인셋 프레임 및 화면 설정
# ==============================================================================
st.set_page_config(page_title="초연 시공명리 Ver 8.7", layout="wide")

st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&family=Malgun+Gothic&display=swap");
    .stApp { background-color: #FFF8E1; font-family: 'Malgun Gothic', sans-serif; }
    .report-page { max-width: 950px; margin: 20px auto; background: white; padding: 25px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }
    .vip-inset-frame { border: 3px solid #1A237E; border-radius: 20px; padding: 40px; }
    .result-table { width: 100%; border-collapse: collapse; border: 3px solid #3E2723; margin-bottom: 20px; text-align: center; }
    .result-table td { border: 1px solid #444; padding: 8px; font-weight: 900; }
    .header-cell { background-color: #1A237E; color: white; }
    .sub-header { background-color: #E8EAF6; color: #1A237E; }
    .color-목 { background-color: #2E7D32; color: white; }
    .color-화 { background-color: #C62828; color: white; }
    .color-토 { background-color: #F9A825; color: black; }
    .color-금 { background-color: #9E9E9E; color: white; }
    .color-수 { background-color: #212121; color: white; }
    .content-box-loose { line-height: 1.8; font-size: 16px; font-family: 'Noto Serif KR', serif; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. DB 및 AI 설정
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
# 2. 명리 연산 엔진 (-30분 보정 적용)
# ==============================================================================
GAN = "甲乙丙丁戊己庚辛壬癸"
JI = "子丑寅卯辰巳午未申酉戌亥"

def get_color(c):
    if c in "甲乙寅卯": return "목"
    if c in "丙丁巳午": return "화"
    if c in "戊己辰戌丑未": return "토"
    if c in "庚辛申酉": return "금"
    if c in "壬癸亥子": return "수"
    return "토"

def calculate_gongmang(ilgan, ilji):
    if ilgan in ["?"," ","-"] or ilji in ["?"," ","-"]: return "모름"
    try:
        base = (list(JI).index(ilji) - list(GAN).index(ilgan) - 2) % 12
        return list(JI)[base] + "," + list(JI)[(base+1)%12]
    except: return "모름"

def get_time_ganji(time_str):
    for j in list(JI):
        if j in time_str: return "X", j
    return "?", "?"

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
# 3. 화면 UI 및 사이드바
# ==============================================================================
with st.sidebar:
    st.title("🧪 초연 임상 연구소")
    st.caption("Ver 8.7 Masterpiece")
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

# ==============================================================================
# 4. 분석 엔진 및 AI 감명
# ==============================================================================
tab1, tab2 = st.tabs(["🚀 정밀 사주풀이", "⚖️ 1:1 비교 분석"])

with tab1:
    if st.button("🚀 분석 가동", use_container_width=True):
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("API 키가 없습니다.")
        else:
            klc = KoreanLunarCalendar()
            if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
            else: klc.setLunarDate(u_y, u_m, u_d, False)
            gj = klc.getChineseGapJaString().split()
            ys, yb = gj[0][0], gj[0][1]; ms, mb = gj[1][0], gj[1][1]; ds, db = gj[2][0], gj[2][1]
            hs, hb = get_time_ganji(u_t)
            calc_d = get_daeun_su_accurate(dt_mod.datetime(u_y, u_m, u_d, 12, 0) - dt_mod.timedelta(hours=9), 1 if (list(GAN).index(ys)%2==0) == (u_gender=='남성') else -1)

            st.markdown(f"### 🏮 {u_name}님 원국 분석")
            st.table(pd.DataFrame({"구분": ["천간", "지지"], "시주": [hs, hb], "일주": [ds, db], "월주": [ms, mb], "년주": [ys, yb]}))

            with st.spinner("초연 509 시스템 가동 중..."):
                prompt = f"""초연 박사의 관점에서 {ys}{yb}년 {ms}{mb}월 {ds}{db}일 {hs}{hb}시 사주를 11단계로 정밀 분석하십시오. HTML 태그를 활용해 전문적으로 서술하십시오."""
                try:
                    res = model.generate_content(prompt)
                    st.markdown(f"<div class='report-page'><div class='vip-inset-frame'>{res.text}</div></div>", unsafe_allow_html=True)
                except Exception as e: st.error(f"오류: {e}")

with tab2:
    st.markdown("### ⚖️ 타 술사 감명서 1:1 비교")
    comp_text = st.text_area("타 감명서 입력", height=150)
    if st.button("⚖️ 비교 분석 시작"):
        with st.spinner("교차 분석 중..."):
            prompt = f"초연 박사로서 다음 감명서를 11단계 소제목에 맞춰 1:1 비교하고 12) 종합의견을 작성하시오. 대상 데이터: {comp_text}"
            try:
                res = model.generate_content(prompt)
                st.markdown(f"<div class='report-page'><div class='vip-inset-frame'>{res.text}</div></div>", unsafe_allow_html=True)
            except Exception as e: st.error(f"오류: {e}")
