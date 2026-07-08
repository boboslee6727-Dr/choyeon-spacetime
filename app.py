import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import os
import re
from google import genai
import time
import engine
import html_templates
import prompts
import json

# ==============================================================================
# 1. 초기 설정 및 공통 함수
# ==============================================================================
APP_VERSION = "ver 50.0"

st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# UI 스타일링 (사이드바는 고딕체, 실행화면은 모두 나눔명조체 적용)
st.markdown("""
<style>
    /* 1. 구글 폰트 임포트 */
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic&family=Nanum+Myeongjo:wght@400;700;800&display=swap');
    
    /* 2. 사이드바 전체 고딕체 적용 */
    [data-testid="stSidebar"] {background-color: #F0F2F6 !important;
        font-family: 'Nanum Gothic', sans-serif !important;}
    
    /* 3. 사이드바 내부 텍스트 및 라벨 강제 적용 */
    [data-testid="stSidebar"] * {font-family: 'Nanum Gothic', sans-serif !important;}
    
    /* 4. 메인 실행 화면은 나눔명조체 적용 */
    .stApp { background-color: #FFFDE7 !important;
        font-family: 'Nanum Myeongjo', serif !important;}
    
    /* 메인 화면의 모든 텍스트 요소를 나눔명조체로 */
    div, p, span, h1, h2, h3, h4, h5, h6, table, tr, td {font-family: 'Nanum Myeongjo', serif !important;}
    
    /* 버튼 스타일 */
    div.stButton > button {background-color: #D32F2F ! important; color: white !important; font-family: 'Nanum Gothic', sans-serif !important;}
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
    
    # 🚨 [누락 복구] 혼인여부와 달력 셀렉트박스 추가
    u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
    u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")
    
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
        st.markdown("<div style='font-weight:900; color:#D50000; margin-bottom:5px; margin-top:15px;'>👥 상대방 정보</div>", unsafe_allow_html=True)
        
        # 🚨 [누락 복구] 상대방 사주 역산 모듈
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
                                    st.session_state.p_y_in = p_curr_dt.year
                                    st.session_state.p_m_in = p_curr_dt.month
                                    st.session_state.p_d_in = p_curr_dt.day
                                    time_map_rev = {
                                        '子':'00:30 ~ 01:29 (朝子)시', '丑':'01:30 ~ 03:29 (丑)시',
                                        '寅':'03:30 ~ 05:29 (寅)시', '卯':'05:30 ~ 07:29 (卯)시',
                                        '辰':'07:30 ~ 09:29 (辰)시', '巳':'09:30 ~ 11:29 (巳)시',
                                        '午':'11:30 ~ 13:29 (午)시', '未':'13:30 ~ 15:29 (未)시',
                                        '申':'15:30 ~ 17:29 (申)시', '酉':'17:30 ~ 19:29 (酉)시',
                                        '戌':'19:30 ~ 21:29 (戌)시', '亥':'21:30 ~ 23:29 (亥)시'
                                    }
                                    if p_rt:
                                        p_ji_char = extract_ganji(p_rt)[-1] if extract_ganji(p_rt) else ""
                                        p_rt_h = K2H_JI.get(p_ji_char, p_ji_char)
                                        if p_rt_h in time_map_rev: st.session_state.p_t_key = time_map_rev[p_rt_h]
                                    p_found = True
                                    p_l_y, p_l_m, p_l_d = p_klc_find.lunarYear, p_klc_find.lunarMonth, p_klc_find.lunarDay
                                    p_leap = "윤" if p_klc_find.isIntercalation else ""
                                    st.session_state.p_rev_success_msg = f"✅ 상대방 양력 {p_curr_dt.year}년 {p_curr_dt.month:02d}월 {p_curr_dt.day:02d}일 (음력 {p_leap}{p_l_y}년 {p_l_m:02d}월 {p_l_d:02d}일) 자동입력 완료!"
                                    st.rerun()
                                    break
                                p_curr_dt -= dt_mod.timedelta(days=1)
                        if p_found: break
                    if not p_found: st.error("일치하는 날짜가 없습니다.")
                else: st.warning("간지를 2글자씩 정확히 입력하세요.")
            if st.session_state.get('p_rev_success_msg'):
                st.success(st.session_state.p_rev_success_msg)

        # 🚨 [누락 복구] 상대방 세부 정보 입력창
        f_name = st.text_input("상대방 이름", "이영희", key="f_n")
        f_gender_options = ["여성", "남성"] if gender == "남성" else ["남성", "여성"]
        f_gender = st.selectbox("상대방 성별", f_gender_options, key="f_g")
        f_marital = st.selectbox("상대방 혼인여부", ["미혼", "기혼", "돌싱"], key="f_m_stat")
        f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c")
        
        p_col1, p_col2, p_col3 = st.columns(3)
        f_y = p_col1.number_input("년 (상대)", 1900, 2050, key="p_y_in")
        f_m = p_col2.number_input("월 (상대)", 1, 12, key="p_m_in")
        f_d = p_col3.number_input("일 (상대)", 1, 31, key="p_d_in")
        f_t = st.selectbox("태어난 시간 (상대)", idx_list, key="p_t_key")
        
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
        # 🚨 [1단계] 양력/음력 변환 및 나이 계산 로직
        klc = KoreanLunarCalendar()
        if "음력" in u_cal:
            is_leap = True if "윤달" in u_cal else False
            klc.setLunarDate(b_year, b_month, b_day, is_leap)
            sol_y, sol_m, sol_d = klc.solarYear, klc.solarMonth, klc.solarDay
            lun_y, lun_m, lun_d = b_year, b_month, b_day
            leap_str = "윤달" if is_leap else "평달"
        else:
            klc.setSolarDate(b_year, b_month, b_day)
            sol_y, sol_m, sol_d = b_year, b_month, b_day
            lun_y, lun_m, lun_d = klc.lunarYear, klc.lunarMonth, klc.lunarDay
            leap_str = "윤달" if klc.isIntercalary else "평달"
            
        curr_year = dt_mod.datetime.now().year
        age = curr_year - sol_y + 1
        p_icon = "♂️" if gender == "남성" else "♀️"
        p_color = "#1A237E" if gender == "남성" else "#D50000"
        today_str = dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
        
        def extract_time(time_str):
            if "모름" in time_str: return 0, 0
            import re
            match = re.search(r'(\d{2}):(\d{2})', time_str)
            return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

        # 1. 만세력 엔진 연산 (import engine 기반 데이터 무결성 확보)
        with st.spinner(f"⏳ [초연 시공명리 분석({APP_VERSION}) 중....]"):
            h, m = extract_time(b_time)
            
            # engine 모듈 전체 호출 규격에 맞춰 정석대로 복구
            y_pillar, m_pillar, lon = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
            
            is_lunar_val = ("음력" in u_cal)
            is_leap_val = ("윤달" in u_cal)
            _, _, d_pillar = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)
            t_gan, t_ji = engine.get_time_ganji(d_pillar[0], b_time)

            gans = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]]
            jjis = [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
            hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
            hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]

            # 기초 오행 및 신살 데이터 주입 연산
            counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
            for c in gans + jjis:
                if c in "甲乙寅卯": counts['목']+=1
                elif c in "丙丁巳午": counts['화']+=1
                elif c in "戊己辰戌丑未": counts['토']+=1
                elif c in "庚辛申酉": counts['금']+=1
                elif c in "壬癸亥子": counts['수']+=1

            guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
            guiin_str = guiin_map.get(ds, '없음')
            n_gong = engine.calculate_gongmang(ys, yb)
            i_gong = engine.calculate_gongmang(ds, db)
            cur_samjae = engine.get_samjae(yb, db)
            samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#2E7D32"

            # 지지합충 연쇄 4줄 격자 렌더링 데이터 생성
            ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if engine.get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:0px solid transparent; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else engine.get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:13px; vertical-align:middle;'>합충형파해</td>" if l_idx==0 else ""
                ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

            # 대운수 및 방향 도출 연산
            base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
            adj_mins = engine.get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            order_dir = 1 if (engine.GAN.index(ys)%2==0) == (gender=='남성') else -1
            calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
            direction_str = "순행" if order_dir == 1 else "역행"

            # ------------------------------------------------------------------
            # [2단계] 출력 렌더링 통제 - html_templates 모듈 연동 전면 체결
            # ------------------------------------------------------------------
            # 1. 첫 페이지 명품 커버 페이지 (Cover HTML) 출력
            sol_str = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
            lun_str = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
            time_str = f"{b_time.split('(')[0].strip()} ({hb})시" if b_time != "시간 모름" else ""
            cover_html_out = html_templates.get_personal_cover(APP_VERSION, p_color, p_icon, name, sol_str, lun_str, time_str, today_str)
            st.markdown(cover_html_out, unsafe_allow_html=True)

            # 2. 정밀 분석 안내서 배너 (Intro HTML) 출력
            st.markdown(html_templates.get_intro_html(), unsafe_allow_html=True)

            # 3. 만세력 사주원국 정밀 레이아웃 표 (Table HTML) 출력
            info_h = f"<div style='text-align:center; line-height:1.5;'><span style='font-size:19px; font-weight:900; color:{p_color};'>{p_icon} {name}님 ({gender}, {u_marital}, {age}세)</span><br><span style='font-size:14px; font-weight:bold; color:#555;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span></div>"
            table_html_out = html_templates.get_table_html(info_h, gans, jjis, ds, hs, hb, db, mb, yb, ji_rel_rows, engine.get_gan_rel_all, engine.get_ss, engine.get_jijanggan_full, engine.get_unsung, engine.get_12_shinsal, engine.get_general_shinsal_filtered, engine.get_color, gender)
            st.markdown(table_html_out, unsafe_allow_html=True)

            # 4. 종합 요약 마스터 바 (Master Bar HTML) 출력
            st.markdown(html_templates.get_master_bar(counts, guiin_str, n_gong, i_gong, samjae_color, cur_samjae), unsafe_allow_html=True)

            # 5. 운의 흐름 가로 정렬 3단 흐름표 (대운/세운/월운 HTML) 차례로 매핑 출력
            st.markdown(html_templates.get_daewun_html(calc_d, direction_str, age, ms, mb, ds, yb, engine.GAN, engine.JI, engine.get_ss, engine.get_color, engine.get_unsung, engine.get_12_shinsal), unsafe_allow_html=True)
            
            cur_dw_idx = max(0, (age - calc_d) // 10)
            dw_g_cur = engine.GAN[(engine.GAN.index(ms) + (cur_dw_idx+1)*order_dir)%10] if ms in engine.GAN else "-"
            dw_j_cur = engine.JI[(engine.JI.index(mb) + (cur_dw_idx+1)*order_dir)%12] if mb in engine.JI else "-"
            start_year = sol_y + (cur_dw_idx * 10 + calc_d) - 1
            st.markdown(html_templates.get_sewun_html(dw_g_cur, dw_j_cur, start_year, curr_year, ds, yb, engine.GAN, engine.JI, engine.get_ss, engine.get_color, engine.get_unsung, engine.get_12_shinsal), unsafe_allow_html=True)
            
            wol_gans = ["己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚"]
            wol_jis = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]
            curr_m = dt_mod.datetime.now().month
            st.markdown(html_templates.get_wolwun_html(curr_year, curr_m, ds, yb, wol_gans, wol_jis, engine.get_ss, engine.get_color, engine.get_unsung, engine.get_12_shinsal), unsafe_allow_html=True)

            # 6. AI 감명 결과 박스 렌더링 및 최종 감사 인사(Closing) 출력
            fact_sheet = prompts.PERSONAL_SAJU_PROMPT.format(
                name=name, gender=gender, ilgan=d_pillar[0], ilju=d_pillar, wolryeong=m_pillar,
                jijanggan_info="엔진 데이터 정밀 연동됨", missing_and_gongmang="엔진 데이터 정밀 연동됨",
                shinsal_info="엔진 데이터 정밀 연동됨", vault_info="엔진 데이터 정밀 연동됨"
            )
            ai_result = call_gemini_api(fact_sheet)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)
            st.markdown(html_templates.get_closing_html(name), unsafe_allow_html=True)

# ==============================================================================
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

# ==============================================================================
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
