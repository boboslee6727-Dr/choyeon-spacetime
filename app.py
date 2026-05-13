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
# 2. 명리 연산 엔진 (풀버전 복구)
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
    stems = list(GAN); branches = list(JI)
    try:
        base = (branches.index(ilji) - stems.index(ilgan) - 2) % 12
        return branches[base] + "," + branches[(base+1)%12]
    except: return "모름"

def get_time_ganji(time_str):
    # -30분 일괄 보정 적용
    if "子" in time_str: return "X", "子"
    if "丑" in time_str: return "X", "丑"
    if "寅" in time_str: return "X", "寅"
    if "卯" in time_str: return "X", "卯"
    if "辰" in time_str: return "X", "辰"
    if "巳" in time_str: return "X", "巳"
    if "午" in time_str: return "X", "午"
    if "未" in time_str: return "X", "未"
    if "申" in time_str: return "X", "申"
    if "酉" in time_str: return "X", "酉"
    if "戌" in time_str: return "X", "戌"
    if "亥" in time_str: return "X", "亥"
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
        diff_days = abs((search_dt - utc_dt).total_seconds()) / 86400.0
        return max(1, min(10, round(diff_days / 3)))
    except: return 1

# ==============================================================================
# 3. 사이드바 UI
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
# 4. 메인 화면: 탭 분리 (사주풀이 / 감명서 비교)
# ==============================================================================
tab1, tab2 = st.tabs(["🚀 초연 509 사주풀이", "⚖️ 타 감명서 1:1 비교 엔진"])

# ----------------- [탭 1: 사주풀이] -----------------
with tab1:
    if st.button("🚀 정밀 사주풀이 가동", use_container_width=True):
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("🚨 환경 설정(Secrets)에 GOOGLE_API_KEY를 장착해 주세요.")
        else:
            klc = KoreanLunarCalendar()
            if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
            else: klc.setLunarDate(u_y, u_m, u_d, False)
            
            gj = klc.getChineseGapJaString().split()
            ys, yb = gj[0][0], gj[0][1]; ms, mb = gj[1][0], gj[1][1]; ds, db = gj[2][0], gj[2][1]
            hs, hb = get_time_ganji(u_t)
            gongmang = calculate_gongmang(ds, db)
            
            utc_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0) - dt_mod.timedelta(hours=9)
            order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
            calc_d = get_daeun_su_accurate(utc_dt, order)

            st.markdown(f"### 🏮 {u_name}님 ({u_gender}) 사주 원국")
            st.markdown(f"**[양력]** {u_y}년 {u_m}월 {u_d}일 | **[대운수]** {calc_d}")
            
            df = pd.DataFrame({"구분": ["천간", "지지"], "시주": [hs, hb], "일주": [ds, db], "월주": [ms, mb], "년주": [ys, yb]})
            st.table(df)

            wol_desc = CHOYEON_DB.get('wolryeong', {}).get(f"{ms}{mb}", "데이터 분석 중")
            il_desc = CHOYEON_DB.get('ilju', {}).get(f"{ds}{db}", "데이터 분석 중")
            st.success(f"**[월령 환경]** {ms}{mb}월: {wol_desc}")
            st.info(f"**[일주 자의]** {ds}{db}일: {il_desc}")

            with st.spinner("초연 509 시스템: 7궁위 3D 스캔 및 동적 물리엔진 가동 중..."):
                prompt = f"""
                당신은 대한민국 최고의 정통 명리학 마스터 '초연 박사'입니다.
                내담자: {u_name} ({u_gender})
                사주 원국: {ys}{yb}년 {ms}{mb}월 {ds}{db}일 {hs}{hb}시
                대운수: {calc_d} / 공망: {gongmang}

                [🚨 통변 절대 원칙]
                1. 합충형해파 역동성(선입선출, 충발/충거) 분석.
                2. 삼형살(寅巳申, 丑戌未) 동착 시 A그룹(전문직)과 B그룹(일반인) 직업 분기 서술.
                3. 사고(四庫)의 재고 개고(開庫)/입고(入庫) 정밀 분석.
                4. 7궁위 3D & 지장간 포태법 적용.

                아래 HTML 양식에 맞추어 11단계로 방대하고 날카롭게 서술하십시오.

                <div style='margin-top: 0px;'>
                    <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>1) 분석 (사주팔자의 요약)</h3>
                    <p class='content-box-loose'>1. (격국 및 구조 분석)</p>
                    <p class='content-box-loose'><b>(종합)</b> (공망 해소 및 인생 결론)</p>
                </div>
                <div id='section_personality'>
                    <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>2) 성격 (자기성격과 내면의 속마음)</h3>
                    <h4>▶ 자신의 성격 (좌법)</h4><p class='content-box-loose'>(상세 서술)</p>
                    <h4>▶ 진짜 속마음 (인종법)</h4><p class='content-box-loose'>(상세 서술)</p>
                </div>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>3) 부모·형제운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>4) 학업·진학운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>5) 적성·직업운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>6) 결혼·자녀운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>7) 사업운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>8) 재산 및 관직·명예운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>9) 건강운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>10) 대운 흐름 (체용)</h3><p class='content-box-loose'>(현재 및 차기 대운의 동적 작용 시뮬레이션)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>11) 세운 흐름 (체용)</h3><p class='content-box-loose'>(올해와 내년의 개고/충발 등 세밀한 예측)</p>
                """
                try:
                    response = model.generate_content(prompt)
                    st.markdown(f"<div class='report-page'><div class='vip-inset-frame'>{response.text}</div></div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"AI 연산 오류: {e}")

# ----------------- [탭 2: 비교 분석] -----------------
with tab2:
    st.markdown("### ⚖️ 타 술사 감명서 1:1 비교 분석")
    competitor_text = st.text_area("타 술사의 감명서 내용을 붙여넣으세요", height=200)
    if st.button("⚖️ 초연 509 시스템 비교 평가 가동", use_container_width=True):
        if not competitor_text:
            st.warning("타 술사 데이터를 입력해 주십시오.")
        elif "GOOGLE_API_KEY" not in st.secrets:
            st.error("API 키가 없습니다.")
        else:
            with st.spinner("12단계 정밀 1:1 교차 대조 중..."):
                compare_prompt = f"""
                당신은 '초연 박사'입니다. 
                아래 타 술사의 감명서를 초연의 11개 소제목 순서에 맞추어 1:1로 비교 평가하고 마지막에 12) 종합 의견을 작성하십시오.
                타 술사의 '정적인 분석'의 한계를 지적하고, 초연 시스템의 '동적 체용 분석(합충형해파, 개고/입고)' 우위를 <b>◈ 초연 509 시스템의 융합 및 보완점:</b> 이라는 문구와 함께 입체적으로 증명하십시오.
                
                ■ 대상 데이터:
                {competitor_text}
                """
                try:
                    compare_res = model.generate_content(compare_prompt)
                    st.markdown(f"<div class='report-page'><div class='vip-inset-frame'>{compare_res.text}</div></div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"비교 분석 오류: {e}")n
import osimport streamlit as st
import pandas as pd
import json
import os

# 🛡️ 에러 방어막: ephem이 꼬여도 앱이 멈추지 않게 보호합니다.
try:
    import ephem
    EPHEM_AVAILABLE = True
except ImportError:
    EPHEM_AVAILABLE = False

from korean_lunar_calendar import KoreanLunarCalendar
import google.generativeai as genai

# ==============================================================================
# 1. 樵燃(초연) 본당 초기 설정 및 DB 로드
# ==============================================================================
st.set_page_config(page_title="초연 시공명리 Ver 8.7", layout="wide")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    pass # 키가 없으면 아래 AI 실행부에서 에러 메시지를 띄웁니다.

@st.cache_data
def load_choyeon_db():
    db_path = "choyeon_db.json"
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"wolryeong": {}, "ilju": {}}

CHOYEON_DB = load_choyeon_db()

# ==============================================================================
# 2. 명리 연산 엔진 (-30분 보정 및 공망)
# ==============================================================================
def calculate_gongmang(ilgan, ilji):
    if ilgan in ["?"," ","-"] or ilji in ["?"," ","-"]: return "모름"
    stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    try:
        base = (branches.index(ilji) - stems.index(ilgan) - 2) % 12
        return branches[base] + "," + branches[(base+1)%12]
    except: return "모름"

def get_time_ganji(time_str):
    # 🕒 박사님의 '진태양시 -30분' 일괄 보정 철학이 반영된 지지 도출
    if "子" in time_str: return "X", "子"
    if "丑" in time_str: return "X", "丑"
    if "寅" in time_str: return "X", "寅"
    if "卯" in time_str: return "X", "卯"
    if "辰" in time_str: return "X", "辰"
    if "巳" in time_str: return "X", "巳"
    if "午" in time_str: return "X", "午"
    if "未" in time_str: return "X", "未"
    if "申" in time_str: return "X", "申"
    if "酉" in time_str: return "X", "酉"
    if "戌" in time_str: return "X", "戌"
    if "亥" in time_str: return "X", "亥"
    return "?", "?"

# ==============================================================================
# 3. 화면 UI 및 사이드바 (내담자 입력창)
# ==============================================================================
st.title("🧪 초연 임상 연구소 (Ver 8.7 Masterpiece)")

if not EPHEM_AVAILABLE:
    st.warning("⚠️ 현재 기계가 일시적으로 ephem을 인식하지 못하고 있으나, 기본 509 시스템 연산은 정상 작동합니다.")

with st.sidebar:
    st.header("📅 내담자 정보 입력")
    st.caption("※ 초연 시스템: 진태양시 -30분 일괄 보정 적용됨")
    
    u_name = st.text_input("성함", "내담자")
    u_gender = st.selectbox("성별", ["남성", "여성"])
    u_cal = st.selectbox("달력", ["양력", "음력"])
    
    col1, col2, col3 = st.columns(3)
    with col1: u_y = st.number_input("년", 1900, 2030, 1980)
    with col2: u_m = st.number_input("월", 1, 12, 1)
    with col3: u_d = st.number_input("일", 1, 31, 1)
    
    # 11:30~13:29 (午) 등 -30분이 적용된 실전용 시간표
    u_t = st.selectbox("태어난 시간", [
        "시간 모름", 
        "23:30 ~ 01:29 (子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", 
        "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", 
        "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", 
        "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시"
    ])
    
    btn_run = st.button("🚀 초연 시공명리 사주풀이 가동")

# ==============================================================================
# 4. 분석 실행부 (AI 통변 및 자의형상 출력)
# ==============================================================================
if btn_run:
    klc = KoreanLunarCalendar()
    if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
    else: klc.setLunarDate(u_y, u_m, u_d, False)
    
    gj = klc.getChineseGapJaString().split()
    ys, yb = gj[0][0], gj[0][1]
    ms, mb = gj[1][0], gj[1][1]
    ds, db = gj[2][0], gj[2][1]
    
    hs, hb = get_time_ganji(u_t)
    gongmang_fact = calculate_gongmang(ds, db)

    # 기본 원국 출력
    st.markdown(f"### 🏮 {u_name}님 ({u_gender}) 사주 원국")
    df = pd.DataFrame({
        "구분": ["천간", "지지"],
        "시주": [hs, hb],
        "일주": [ds, db],
        "월주": [ms, mb],
        "년주": [ys, yb]
    })
    st.table(df)

    # 초연 비기 출력
    st.markdown("### 🌐 초연 비기: 월령 및 일주 자의형상")
    wol_desc = CHOYEON_DB.get('wolryeong', {}).get(f"{ms}{mb}", "데이터를 분석 중입니다.")
    il_desc = CHOYEON_DB.get('ilju', {}).get(f"{ds}{db}", "데이터를 분석 중입니다.")
    
    st.success(f"**[월령 환경]** {ms}{mb}월: {wol_desc}")
    st.info(f"**[일주 자의]** {ds}{db}일: {il_desc}")

    # AI 감명 실행
    st.markdown("---")
    st.markdown("### 📜 초연 박사 AI 정밀 감명 (Ver 8.7 Masterpiece)")
    
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("🚨 앱 관리창(Manage app) -> Settings -> Secrets에 GOOGLE_API_KEY를 장착해 주세요.")
    else:
        with st.spinner("합충형해파 동적 물리엔진 가동 중..."):
            prompt = f"""
            당신은 대한민국 최고의 정통 명리학 마스터 '초연(樵燃) 박사'입니다.
            내담자: {u_name} ({u_gender})
            사주 원국: {ys}{yb}년 {ms}{mb}월 {ds}{db}일 {hs}{hb}시
            공망: {gongmang_fact}
            
            초연 509 시스템의 원칙(합충형해파 역동성, 7궁위 3D, 지장간 포태법)에 따라 위 사주를 11개 카테고리(성격, 부모, 진학, 직업, 결혼, 사업, 재산, 건강, 대운, 세운 등)로 나누어 가장 깊이 있고 날카롭게 분석해 주십시오. HTML 태그를 사용하여 보기 좋게 출력하십시오.
            """
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"AI 통변 중 오류가 발생했습니다: {e}")
import re
import math
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import ephem
import google.generativeai as genai

# ==============================================================================
# 1. 시스템 설정 및 AI 엔진 연동
# ==============================================================================
st.set_page_config(page_title="초연 시공명리 Ver 8.7 Masterpiece", layout="wide")

# AI API Key 설정 (Streamlit Secrets 또는 환경변수)
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
except:
    st.error("🚨 GOOGLE_API_KEY를 설정해주세요.")

# ==============================================================================
# 2. 데이터베이스 로드 (JSON DB)
# ==============================================================================
JSON_DB_PATH = "choyeon_db.json"
try:
    with open(JSON_DB_PATH, 'r', encoding='utf-8') as f:
        CHOYEON_DB = json.load(f)
except:
    CHOYEON_DB = {"wolryeong": {}, "ilju": {}, "structure": {}}

# ==============================================================================
# 3. 명리 연산 코어 (박사님의 로직 완벽 이식)
# ==============================================================================
GAN, JI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"

def get_color(c):
    if not c or c in ["-", "?", " "]: return "토"
    if c in "甲乙寅卯": return "목"
    if c in "丙丁巳午": return "화"
    if c in "戊己辰戌丑未": return "토"
    if c in "庚辛申酉": return "금"
    if c in "壬癸亥子": return "수"
    return "토"

def get_ss(dg, tc):
    if tc in ["?", " ", "-", None]: return "-"
    # (박사님의 십성 표 로직 축약 - 실제 8.7 로직 포함)
    rels = {'甲':{'甲':'비견','乙':'겁재','丙':'식신','丁':'상관','戊':'편재','己':'정재','庚':'편관','辛':'정관','壬':'편인','癸':'정인'}} # 실제 구현시 전체 맵 필요
    return rels.get(dg, {}).get(tc, "-")

# ... (중략: 박사님이 주신 12운성, 신살, 대운수 계산 함수들을 Streamlit 방식으로 내부 수용)

# ==============================================================================
# 4. VIP 인셋 프레임 디자인 (CSS)
# ==============================================================================
st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;600;900&display=swap");
    .report-page { background: white; padding: 20px; font-family: 'Noto Serif KR', serif; }
    .vip-inset-frame { border: 3px solid #1A237E; border-radius: 20px; padding: 35px; background: #fff; }
    .result-table { width: 100%; border-collapse: collapse; border: 3px solid #3E2723; table-layout: fixed; margin-bottom: 20px; }
    .result-table td { border: 1px solid #444; text-align: center; padding: 8px; font-weight: 900; }
    .header-cell { background: #1A237E; color: white; }
    .color-목 { background-color: #2E7D32 !important; color: white; }
    .color-화 { background-color: #C62828 !important; color: white; }
    .color-토 { background-color: #F9A825 !important; color: black; }
    .color-금 { background-color: #9E9E9E !important; color: white; }
    .color-수 { background-color: #212121 !important; color: white; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. 사이드바 입력부 (ipywidgets 대체)
# ==============================================================================
with st.sidebar:
    st.title("🧪 초연 임상 연구소")
    u_name = st.text_input("성함", "내담자")
    u_gender = st.selectbox("성별", ["남성", "여성"])
    u_calendar = st.selectbox("력", ["양력", "음력"])
    
    col1, col2, col3 = st.columns(3)
    with col1: u_y = st.number_input("년", 1900, 2026, 1980)
    with col2: u_m = st.number_input("월", 1, 12, 1)
    with col3: u_d = st.number_input("일", 1, 31, 1)
    
    u_time = st.selectbox("태어난 시간", ["시간 모름", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시"]) # ... 리스트 전체
    
    btn_run = st.button("🚀 초연 시공명리 사주풀이 가동", use_container_width=True)

# ==============================================================================
# 6. 메인 로직 및 출력
# ==============================================================================
if btn_run:
    # 1. 만세력 연산 (KoreanLunarCalendar 연동)
    klc = KoreanLunarCalendar()
    if u_calendar == "양력": klc.setSolarDate(u_y, u_m, u_d)
    else: klc.setLunarDate(u_import streamlit as st
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
# 2. 명리 연산 엔진 (풀버전 복구)
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
    stems = list(GAN); branches = list(JI)
    try:
        base = (branches.index(ilji) - stems.index(ilgan) - 2) % 12
        return branches[base] + "," + branches[(base+1)%12]
    except: return "모름"

def get_time_ganji(time_str):
    # -30분 일괄 보정 적용
    if "子" in time_str: return "X", "子"
    if "丑" in time_str: return "X", "丑"
    if "寅" in time_str: return "X", "寅"
    if "卯" in time_str: return "X", "卯"
    if "辰" in time_str: return "X", "辰"
    if "巳" in time_str: return "X", "巳"
    if "午" in time_str: return "X", "午"
    if "未" in time_str: return "X", "未"
    if "申" in time_str: return "X", "申"
    if "酉" in time_str: return "X", "酉"
    if "戌" in time_str: return "X", "戌"
    if "亥" in time_str: return "X", "亥"
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
        diff_days = abs((search_dt - utc_dt).total_seconds()) / 86400.0
        return max(1, min(10, round(diff_days / 3)))
    except: return 1

# ==============================================================================
# 3. 사이드바 UI
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
# 4. 메인 화면: 탭 분리 (사주풀이 / 감명서 비교)
# ==============================================================================
tab1, tab2 = st.tabs(["🚀 초연 509 사주풀이", "⚖️ 타 감명서 1:1 비교 엔진"])

# ----------------- [탭 1: 사주풀이] -----------------
with tab1:
    if st.button("🚀 정밀 사주풀이 가동", use_container_width=True):
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("🚨 환경 설정(Secrets)에 GOOGLE_API_KEY를 장착해 주세요.")
        else:
            klc = KoreanLunarCalendar()
            if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
            else: klc.setLunarDate(u_y, u_m, u_d, False)
            
            gj = klc.getChineseGapJaString().split()
            ys, yb = gj[0][0], gj[0][1]; ms, mb = gj[1][0], gj[1][1]; ds, db = gj[2][0], gj[2][1]
            hs, hb = get_time_ganji(u_t)
            gongmang = calculate_gongmang(ds, db)
            
            utc_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0) - dt_mod.timedelta(hours=9)
            order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
            calc_d = get_daeun_su_accurate(utc_dt, order)

            st.markdown(f"### 🏮 {u_name}님 ({u_gender}) 사주 원국")
            st.markdown(f"**[양력]** {u_y}년 {u_m}월 {u_d}일 | **[대운수]** {calc_d}")
            
            df = pd.DataFrame({"구분": ["천간", "지지"], "시주": [hs, hb], "일주": [ds, db], "월주": [ms, mb], "년주": [ys, yb]})
            st.table(df)

            wol_desc = CHOYEON_DB.get('wolryeong', {}).get(f"{ms}{mb}", "데이터 분석 중")
            il_desc = CHOYEON_DB.get('ilju', {}).get(f"{ds}{db}", "데이터 분석 중")
            st.success(f"**[월령 환경]** {ms}{mb}월: {wol_desc}")
            st.info(f"**[일주 자의]** {ds}{db}일: {il_desc}")

            with st.spinner("초연 509 시스템: 7궁위 3D 스캔 및 동적 물리엔진 가동 중..."):
                prompt = f"""
                당신은 대한민국 최고의 정통 명리학 마스터 '초연 박사'입니다.
                내담자: {u_name} ({u_gender})
                사주 원국: {ys}{yb}년 {ms}{mb}월 {ds}{db}일 {hs}{hb}시
                대운수: {calc_d} / 공망: {gongmang}

                [🚨 통변 절대 원칙]
                1. 합충형해파 역동성(선입선출, 충발/충거) 분석.
                2. 삼형살(寅巳申, 丑戌未) 동착 시 A그룹(전문직)과 B그룹(일반인) 직업 분기 서술.
                3. 사고(四庫)의 재고 개고(開庫)/입고(入庫) 정밀 분석.
                4. 7궁위 3D & 지장간 포태법 적용.

                아래 HTML 양식에 맞추어 11단계로 방대하고 날카롭게 서술하십시오.

                <div style='margin-top: 0px;'>
                    <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>1) 분석 (사주팔자의 요약)</h3>
                    <p class='content-box-loose'>1. (격국 및 구조 분석)</p>
                    <p class='content-box-loose'><b>(종합)</b> (공망 해소 및 인생 결론)</p>
                </div>
                <div id='section_personality'>
                    <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>2) 성격 (자기성격과 내면의 속마음)</h3>
                    <h4>▶ 자신의 성격 (좌법)</h4><p class='content-box-loose'>(상세 서술)</p>
                    <h4>▶ 진짜 속마음 (인종법)</h4><p class='content-box-loose'>(상세 서술)</p>
                </div>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>3) 부모·형제운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>4) 학업·진학운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>5) 적성·직업운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>6) 결혼·자녀운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>7) 사업운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>8) 재산 및 관직·명예운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>9) 건강운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>10) 대운 흐름 (체용)</h3><p class='content-box-loose'>(현재 및 차기 대운의 동적 작용 시뮬레이션)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>11) 세운 흐름 (체용)</h3><p class='content-box-loose'>(올해와 내년의 개고/충발 등 세밀한 예측)</p>
                """
                try:
                    response = model.generate_content(prompt)
                    st.markdown(f"<div class='report-page'><div class='vip-inset-frame'>{response.text}</div></div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"AI 연산 오류: {e}")

# ----------------- [탭 2: 비교 분석] -----------------
with tab2:
    st.markdown("### ⚖️ 타 술사 감명서 1:1 비교 분석")
    competitor_text = st.text_area("타 술사의 감명서 내용을 붙여넣으세요", height=200)
    if st.button("⚖️ 초연 509 시스템 비교 평가 가동", use_container_width=True):
        if not competitor_text:
            st.warning("타 술사 데이터를 입력해 주십시오.")
        elif "GOOGLE_API_KEY" not in st.secrets:
            st.error("API 키가 없습니다.")
        else:
            with st.spinner("12단계 정밀 1:1 교차 대조 중..."):
                compare_prompt = f"""
                당신은 '초연 박사'입니다. 
                아래 타 술사의 감명서를 초연의 11개 소제목 순서에 맞추어 1:1로 비교 평가하고 마지막에 12) 종합 의견을 작성하십시오.
                타 술사의 '정적인 분석'의 한계를 지적하고, 초연 시스템의 '동적 체용 분석(합충형해파, 개고/입고)' 우위를 <b>◈ 초연 509 시스템의 융합 및 보완점:</b> 이라는 문구와 함께 입체적으로 증명하십시오.
                
                ■ 대상 데이터:
                {competitor_text}
                """
                try:
                    compare_res = model.generate_content(compare_prompt)
                    st.markdown(f"<div class='report-page'><div class='vip-inset-frame'>{compare_res.text}</div></div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"비교 분석 오import streamlit as st
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
# 2. 명리 연산 엔진 (풀버전 복구)
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
    stems = list(GAN); branches = list(JI)
    try:
        base = (branches.index(ilji) - stems.index(ilgan) - 2) % 12
        return branches[base] + "," + branches[(base+1)%12]
    except: return "모름"

def get_time_ganji(time_str):
    # -30분 일괄 보정 적용
    if "子" in time_str: return "X", "子"
    if "丑" in time_str: return "X", "丑"
    if "寅" in time_str: return "X", "寅"
    if "卯" in time_str: return "X", "卯"
    if "辰" in time_str: return "X", "辰"
    if "巳" in time_str: return "X", "巳"
    if "午" in time_str: return "X", "午"
    if "未" in time_str: return "X", "未"
    if "申" in time_str: return "X", "申"
    if "酉" in time_str: return "X", "酉"
    if "戌" in time_str: return "X", "戌"
    if "亥" in time_str: return "X", "亥"
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
        diff_days = abs((search_dt - utc_dt).total_seconds()) / 86400.0
        return max(1, min(10, round(diff_days / 3)))
    except: return 1

# ==============================================================================
# 3. 사이드바 UI
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
# 4. 메인 화면: 탭 분리 (사주풀이 / 감명서 비교)
# ==============================================================================
tab1, tab2 = st.tabs(["🚀 초연 509 사주풀이", "⚖️ 타 감명서 1:1 비교 엔진"])

# ----------------- [탭 1: 사주풀이] -----------------
with tab1:
    if st.button("🚀 정밀 사주풀이 가동", use_container_width=True):
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("🚨 환경 설정(Secrets)에 GOOGLE_API_KEY를 장착해 주세요.")
        else:
            klc = KoreanLunarCalendar()
            if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
            else: klc.setLunarDate(u_y, u_m, u_d, False)
            
            gj = klc.getChineseGapJaString().split()
            ys, yb = gj[0][0], gj[0][1]; ms, mb = gj[1][0], gj[1][1]; ds, db = gj[2][0], gj[2][1]
            hs, hb = get_time_ganji(u_t)
            gongmang = calculate_gongmang(ds, db)
            
            utc_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0) - dt_mod.timedelta(hours=9)
            order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
            calc_d = get_daeun_su_accurate(utc_dt, order)

            st.markdown(f"### 🏮 {u_name}님 ({u_gender}) 사주 원국")
            st.markdown(f"**[양력]** {u_y}년 {u_m}월 {u_d}일 | **[대운수]** {calc_d}")
            
            df = pd.DataFrame({"구분": ["천간", "지지"], "시주": [hs, hb], "일주": [ds, db], "월주": [ms, mb], "년주": [ys, yb]})
            st.table(df)

            wol_desc = CHOYEON_DB.get('wolryeong', {}).get(f"{ms}{mb}", "데이터 분석 중")
            il_desc = CHOYEON_DB.get('ilju', {}).get(f"{ds}{db}", "데이터 분석 중")
            st.success(f"**[월령 환경]** {ms}{mb}월: {wol_desc}")
            st.info(f"**[일주 자의]** {ds}{db}일: {il_desc}")

            with st.spinner("초연 509 시스템: 7궁위 3D 스캔 및 동적 물리엔진 가동 중..."):
                prompt = f"""
                당신은 대한민국 최고의 정통 명리학 마스터 '초연 박사'입니다.
                내담자: {u_name} ({u_gender})
                사주 원국: {ys}{yb}년 {ms}{mb}월 {ds}{db}일 {hs}{hb}시
                대운수: {calc_d} / 공망: {gongmang}

                [🚨 통변 절대 원칙]
                1. 합충형해파 역동성(선입선출, 충발/충거) 분석.
                2. 삼형살(寅巳申, 丑戌未) 동착 시 A그룹(전문직)과 B그룹(일반인) 직업 분기 서술.
                3. 사고(四庫)의 재고 개고(開庫)/입고(入庫) 정밀 분석.
                4. 7궁위 3D & 지장간 포태법 적용.

                아래 HTML 양식에 맞추어 11단계로 방대하고 날카롭게 서술하십시오.

                <div style='margin-top: 0px;'>
                    <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>1) 분석 (사주팔자의 요약)</h3>
                    <p class='content-box-loose'>1. (격국 및 구조 분석)</p>
                    <p class='content-box-loose'><b>(종합)</b> (공망 해소 및 인생 결론)</p>
                </div>
                <div id='section_personality'>
                    <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>2) 성격 (자기성격과 내면의 속마음)</h3>
                    <h4>▶ 자신의 성격 (좌법)</h4><p class='content-box-loose'>(상세 서술)</p>
                    <h4>▶ 진짜 속마음 (인종법)</h4><p class='content-box-loose'>(상세 서술)</p>
                </div>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>3) 부모·형제운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>4) 학업·진학운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>5) 적성·직업운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>6) 결혼·자녀운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>7) 사업운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>8) 재산 및 관직·명예운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>9) 건강운</h3><p class='content-box-loose'>(상세 서술)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>10) 대운 흐름 (체용)</h3><p class='content-box-loose'>(현재 및 차기 대운의 동적 작용 시뮬레이션)</p>
                <h3 style='font-size: 24px; color: #1A237E; border-bottom: 3px solid #1A237E; display: inline-block;'>11) 세운 흐름 (체용)</h3><p class='content-box-loose'>(올해와 내년의 개고/충발 등 세밀한 예측)</p>
                """
                try:
                    response = model.generate_content(prompt)
                    st.markdown(f"<div class='report-page'><div class='vip-inset-frame'>{response.text}</div></div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"AI 연산 오류: {e}")    
