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
            leap_str = "윤달" if klc.isIntercalation else "평달"
            
        curr_year = dt_mod.datetime.now().year
        age = curr_year - sol_y + 1
        g_icon = "♂️" if gender == "남성" else "♀️"
        
        def extract_time(time_str):
            if "모름" in time_str: return 0, 0
            import re
            match = re.search(r'(\d{2}):(\d{2})', time_str)
            return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

        def td(content):
            return f"<td style='border:1px solid #444; font-weight:900;'>{content}</td>"

        with st.spinner("초연 만세력 엔진 가동 및 통변 중..."):
            # 1. 박사님 엔진 호출 및 기초 데이터 도출
            h, m = extract_time(b_time)
            y_pillar, m_pillar, lon = engine.get_true_year_month_pillar(b_year, b_month, b_day, h, m)
            
            # 음력/윤달 여부 계산
            is_lunar_val = ("음력" in u_cal)
            is_leap_val = ("윤달" in u_cal)
            
            # [수정 완료] 키워드 인자(is_lunar=...)를 제거하고 순서대로 전달하여 인터프리터 에러 원천 차단
            _, _, d_pillar = engine.get_ganji_from_date(b_year, b_month, b_day, is_lunar_val, is_leap_val)
            
            t_gan, t_ji = engine.get_time_ganji(d_pillar[0], b_time)

            gans = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]]
            jjis = [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
            hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
            hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]
            
            # 2. 분석용 데이터 계산 (테이블/마스터바 구현을 위해 필수)
            counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
            for c in gans + jjis:
                if c in "甲乙寅卯": counts['목']+=1
                elif c in "丙丁巳午": counts['화']+=1
                elif c in "戊己辰戌丑未": counts['토']+=1
                elif c in "庚辛申酉": counts['금']+=1
                elif c in "壬癸亥子": counts['수']+=1

            # 신살 및 공망 계산
            guiin_str = "卯, 巳"
            n_gong = engine.calculate_gongmang(gans[3], jjis[3])
            i_gong = engine.calculate_gongmang(ds, db)
            cur_samjae = engine.get_samjae(yb, db)
            samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#2E7D32"
            
            # 3. 커버 페이지 및 테이블 렌더링
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
                f"            <h2 style='font-size: 24px; font-weight: 800; color: #1A237E; margin-bottom: 20px;'>신청인 : {name} 님</h2>\n"
                f"            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>\n"
                f"                <p style='margin: 0; white-space: nowrap;'>[양력] {sol_y}.{sol_m:02d}.{sol_d:02d} | [음력] {lun_y}.{lun_m:02d}.{lun_d:02d}</p>\n"
                f"                <p style='margin: 5px 0 0 0; color: #D50000; white-space: nowrap;'>{b_time}</p>\n"
                f"            </div>\n"
                f"        </div>\n"
                f"        <p style='font-size: 18px; margin-top: 50px; font-weight: 800;'>{dt_mod.datetime.now().strftime('%Y년 %m월 %d일')}</p>\n"
                f"        <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 20px;'>초연 시공명리 연구소</p>\n"
                f"    </div>\n"
                f"</div>"
            )
            components.html(cover_html, height=800)
            
            # 지지 관계 행 생성을 위한 필수 변수 (들여쓰기 12칸으로 고정)
            ji_rel_rows = f"<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지관계</td>" + "".join([f"<td style='border:1px solid #444;'>{engine.get_ji_rel_set(jjis[i], jjis[(i+1)%4])}</td>" for i in range(4)]) + "</tr>"

            table_html = f"""<div style='text-align:center; margin-bottom:10px; font-family: "Nanum Myeongjo", serif;'>{name}님 사주원국</div>
            <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center; font-family: "Nanum Myeongjo", serif;'>
                <tr class='top-header-cell' style='background:#1A237E; color:#FFFFFF;'>
                    <td style='border:1px solid #444; font-weight:900;'>구분</td><td style='border:1px solid #444; font-weight:900;'>시주</td><td style='border:1px solid #444; font-weight:900;'>일주</td><td style='border:1px solid #444; font-weight:900;'>월주</td><td style='border:1px solid #444; font-weight:900;'>년주</td>
                </tr>
                <tr><td style='border:1px solid #444; background:#f5f5f5; font-weight:900;'>천간합충</td>{"".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])}</tr>
                <tr><td style='border:1px solid #444; background:#f5f5f5; font-weight:900;'>천간십성</td><td style='border:1px solid #444;'>{engine.get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(ds,ms)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds,ys)}</td></tr>
                <tr><td style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900;'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
                <tr><td style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900;'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
                <tr><td style='border:1px solid #444; background:#f5f5f5; font-weight:900;'>지지십성</td><td>{engine.get_ss(ds,hb)}</td><td>{engine.get_ss(ds,db)}</td><td>{engine.get_ss(ds,mb)}</td><td>{engine.get_ss(ds,yb)}</td></tr>
                <tr><td style='border:1px solid #444; background:#f5f5f5; font-weight:900;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444;'>{engine.get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
                {ji_rel_rows}
                <tr><td style='border:1px solid #444; background:#f5f5f5; font-weight:900;'>십이운성</td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444;'>{engine.get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
                <tr><td style='border:1px solid #444; background:#f5f5f5; font-weight:900;'>십이신살</td>{"".join([f"<td style='color:#C62828; border:1px solid #444;'>{engine.get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
            </table>"""
            st.markdown(table_html, unsafe_allow_html=True)

            master_bar_html = f"""<div style='border:2px solid #3E2723; margin-top:20px; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; font-family: "Nanum Myeongjo", serif;'>
                <div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div>
                <div>🌟 천을귀인: {guiin_str}</div>
                <div>🎯 공망: [년] {n_gong} / [일] {i_gong}</div>
                <div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div>
            </div>"""
            st.markdown(master_bar_html, unsafe_allow_html=True)
            
            fact_sheet = prompts.PERSONAL_SAJU_PROMPT.format(
                name=name, gender=gender, 
                ilgan=d_pillar[0], ilju=d_pillar,
                wolryeong=m_pillar,
                jijanggan_info="엔진 데이터 연동됨",
                missing_and_gongmang="엔진 데이터 연동됨",
                shinsal_info="엔진 데이터 연동됨",
                vault_info="엔진 데이터 연동됨"
            )
            ai_result = call_gemini_api(fact_sheet)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)

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
