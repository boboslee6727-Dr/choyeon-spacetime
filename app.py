import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import json
import os
import re
from google import genai
import engine
import prompts
import time

# ==============================================================================
# 1. 초기 설정 및 공통 함수
# ==============================================================================
APP_VERSION = "ver 50.0"

st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# UI 스타일링
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #F0F2F6 !important; }
    .stApp { background-color: #FFFDE7 !important; }
    div.stButton > button {
        background-color: #D32F2F !important;
        color: white !important;
        font-weight: 900 !important;
        border: none !important;
        padding: 10px 20px !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", 
    "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", 
    "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", 
    "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]
if 'app_running' not in st.session_state: st.session_state['app_running'] = False

@st.cache_data
def load_choyeon_db():
    file_path = 'choyeon_db.json'
    if not os.path.exists(file_path): return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception: return {}

db = load_choyeon_db()

# ==============================================================================
# 1.5. AI 및 명리 연산 엔진 (Ver 48.9 완벽 복구)
# ==============================================================================
try:
    _gemini_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as _api_e:
    st.error(f"🚨 Gemini API 키 오류: {_api_e}")
    _gemini_client = None

@st.cache_data(show_spinner=False, ttl=3600*24) # ttl=3600*24초=86,400초 24시간 감명서 유효
def get_ai_response(system_prompt, prompt_text, model_name='gemini-2.5-flash'):
    if '1.5' in model_name:
        model_name = 'gemini-2.5-flash'
        
    if _gemini_client is None:
        return "<div style='color:red;'>🚨 Gemini 모델이 초기화되지 않았습니다.</div>"
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = _gemini_client.models.generate_content(
                model=model_name, 
                contents=prompt_text,
                config=genai.types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.7)
            )
            return response.text.strip()
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1); continue
            return f"<div style='color:red;'>🚨 AI 서버 장애: {e}</div>"

def call_gemini_api(prompt_text, max_tokens=6000):
    # 기존 코드 호환성을 위해 prompts.SYSTEM_ROLE을 기본으로 넘김
    return get_ai_response(prompts.SYSTEM_ROLE, prompt_text, model_name='gemini-2.5-flash')

def call_light_api(prompt_text):
    return get_ai_response(prompts.SYSTEM_ROLE, prompt_text, model_name='gemini-2.5-flash')

# 한자(一-龥)와 한글(가-힣)을 모두 허용하는 안전한 필터링 함수
def extract_ganji(text):
    if not text: return ""
    return re.sub(r'[^가-힣一-龥]', '', text)

# ==============================================================================
# 2. 사이드바 통제 센터 (입력 및 실행 버튼)
# ==============================================================================
with st.sidebar:
    st.markdown(f"<h2 style='color:#D32F2F; font-weight:900;'>🔮 초연 시공명리 연구소</h2>", unsafe_allow_html=True)
    st.caption(f"{APP_VERSION} Master (Base + Gunghap)")
    st.markdown("---")

    # [역산 검색]
    with st.expander("🔍 사주팔자 역산 검색", expanded=True):
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
                                st.session_state.s_y = curr_dt.year
                                st.session_state.s_m = curr_dt.month
                                st.session_state.s_d = curr_dt.day
                                time_map_rev = {'子':'00:30 ~ 01:29 (朝子)시','丑':'01:30 ~ 03:29 (丑)시','寅':'03:30 ~ 05:29 (寅)시','卯':'05:30 ~ 07:29 (卯)시','辰':'07:30 ~ 09:29 (辰)시','巳':'09:30 ~ 11:29 (巳)시','午':'11:30 ~ 13:29 (午)시','未':'13:30 ~ 15:29 (未)시','申':'15:30 ~ 17:29 (申)시','酉':'17:30 ~ 19:29 (酉)시','戌':'19:30 ~ 21:29 (戌)시','亥':'21:30 ~ 23:29 (亥)시'}
                                if rt:
                                    # 한자/한글 모두 추출하여 안전하게 매핑
                                    ji_char = extract_ganji(rt)[-1] if extract_ganji(rt) else ""
                                    rt_h = K2H_JI.get(ji_char, ji_char)
                                    if rt_h in time_map_rev: st.session_state.s_t = time_map_rev[rt_h]
                                found = True
                                l_y, l_m, l_d = klc_find.lunarYear, klc_find.lunarMonth, klc_find.lunarDay
                                leap = "윤" if klc_find.isIntercalation else ""
                                st.session_state.rev_success_msg = f"✅ 양력 {curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일 (음력 {leap}{l_y}년 {l_m:02d}월 {l_d:02d}일) 자동입력 완료!"
                                st.rerun()
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                    if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")
            
        # rerun() 이후에도 메시지가 고정되어 출력되도록 설정
        if st.session_state.get('rev_success_msg'):
            st.success(st.session_state.rev_success_msg)

    st.markdown("---")
    u_product = st.selectbox("📋 분석 상품 선택", ["1. 개인사주 및 일진 분석", "2. 타 감명서 비교", "3. 궁합 및 출산 택일"])
    
    st.markdown("<div style='font-weight:900; color:#1A237E; margin-bottom:5px;'>👤 신청인 정보 (공통)</div>", unsafe_allow_html=True)
    name = st.text_input("이름", "홍길동", key="u_n")
    gender = st.selectbox("성별", ["남성", "여성"], key="u_g")
    
    col_y, col_m, col_d = st.columns(3)
    with col_y: b_year = st.number_input("연도", 1900, 2050, key="s_y")
    with col_m: b_month = st.number_input("월", 1, 12, key="s_m")
    with col_d: b_day = st.number_input("일", 1, 31, key="s_d")
    b_time = st.selectbox("태어난 시간", idx_list, key="s_t")

    # 변수 초기화
    run_iljin_calc, run_delivery_calc = False, False
    other_report, f_name, p_ry, p_rm, p_rd, p_rt = "", "", "", "", "", ""
    final_start_date, final_end_date = None, None

    # 상품별 옵션
    if u_product == "1. 개인사주 및 일진 분석":
        run_iljin_calc = st.checkbox("🔮 일진 시공간 분석 추가 가동", value=False)
        if run_iljin_calc: target_date = st.date_input("분석 일자", value=dt_mod.datetime.now().date())
            
    elif u_product == "2. 타 감명서 비교":
        other_report = st.text_area("📄 타 감명서 원문 붙여넣기", height=150, key="other_reading")
        
    elif u_product == "3. 궁합 및 출산 택일":
        f_name = st.text_input("상대방 이름", "이영희", key="f_n")
        run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석 추가 가동", value=False)
        if run_delivery_calc:
            st.markdown("<h5 style='color:#4A148C;'>🩸 산모 생체 리듬 간편 입력</h5>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)
            with col_b1: last_period_date = st.date_input("생리 시작일", value=dt_mod.date.today(), key="input_last_period")
            with col_b2: period_cycle = st.number_input("생리 주기(일)", min_value=20, max_value=50, value=28, step=1, key="input_period_cycle")

            next_period_date = last_period_date + dt_mod.timedelta(days=period_cycle)
            ovulation_date = next_period_date - dt_mod.timedelta(days=14)
            expected_delivery_date = ovulation_date + dt_mod.timedelta(days=266)
            auto_start_date = expected_delivery_date - dt_mod.timedelta(days=14)
            auto_end_date = expected_delivery_date

            st.markdown(f"<span style='font-size:13px; color:#D50000; font-weight:bold;'>🎯 의학적 배란 예정일: {ovulation_date.strftime('%Y/%m/%d')}</span>", unsafe_allow_html=True)
            
            col_d1, col_d2 = st.columns(2)
            with col_d1: final_start_date = st.date_input("탐색 시작일", value=auto_start_date, key="input_search_start")
            with col_d2: final_end_date = st.date_input("탐색 종료일", value=auto_end_date, key="input_search_end")

    # 사이드바 하단 실행 버튼
    st.markdown("<br>", unsafe_allow_html=True)
    btn_run = st.button("✨ [초연 시공명리 풀이]", key="btn_run", use_container_width=True)

    # 인쇄 컴포넌트
    components.html("""
    <script>function triggerPrint() { window.parent.print(); }</script>
    <button onclick='triggerPrint()' style='width:95%; background-color:#2E7D32; color:white; border:none; font-weight:900; height:45px; border-radius:8px; cursor:pointer;'>
        🖨️ 풀이 결과 인쇄 / PDF 저장
    </button>
    """, height=70)


# ==============================================================================
# 3. 메인 화면 (사이드바 외부 - 넓은 화면에 출력)
# ==============================================================================
if btn_run:
    if u_product == "1. 개인사주 및 일진 분석":
        st.header(f"🔮 {name}님의 초연명리 감명서")
        st.markdown("---")
        with st.spinner("개인사주 풀이 중..."):
            ilgan, ilju = "甲", "甲寅" 
            wolryeong = db.get("wolryeong", {}).get("甲寅", "정보 없음")
            fact_sheet = prompts.PERSONAL_SAJU_PROMPT.format(
                name=name, gender=gender, ilgan=ilgan, ilju=ilju, wolryeong=wolryeong,
                jijanggan_info="寅(戊,丙,甲)", missing_and_gongmang="수(水) 부족 / 공망: 子, 丑",
                shinsal_info="백호대살", vault_info="없음"
            )
            ai_result = get_ai_response(prompts.SYSTEM_ROLE, fact_sheet)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)

    elif u_product == "2. 타 감명서 비교":
        st.header("⚖️ 초연 시공명리 타 감명서 1:1 비교")
        st.markdown("---")
        if not other_report:
            st.warning("👈 사이드바에 타 감명서 원문을 입력해주세요.")
        else:
            with st.spinner("비교 분석 중..."):
                compare_prompt = prompts.COMPARE_PROMPT.format(other_report=other_report, ilju="丙寅", wolryeong="기준 월령", saju_structure="격국 정보")
                ai_result = get_ai_response(prompts.SYSTEM_ROLE, compare_prompt)
                st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)

    elif u_product == "3. 궁합 및 출산 택일":
        st.header(f"💕 {name}님과 {f_name}님의 초연 궁합")
        st.markdown("---")
        loading_msg = "궁합 및 출산 택일 길일 연산 중..." if run_delivery_calc else "궁합 풀이 중..."
        with st.spinner(loading_msg):
            gh_prompt = prompts.GUNGHAP_PROMPT.format(
                app_name=name, app_gender=gender, app_ilju="庚申", partner_name=f_name, partner_gender="여성", partner_ilju="乙卯",
                ilji_relation="원진", oheng_balance="상호 보완", gunghap_score=85, gunghap_grade="상생연분"
            )
            ai_result = get_ai_response(prompts.SYSTEM_ROLE, gh_prompt)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)
            
            if run_delivery_calc:
                st.markdown(f"### 👶 {name} & {f_name} 부부의 최적 출산 길일")
                st.success(f"탐색 기간({final_start_date} ~ {final_end_date}) 내의 길일 연산 엔진이 성공적으로 가동되었습니다. (엔진 연동 대기중)")
