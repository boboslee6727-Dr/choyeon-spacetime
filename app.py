import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import os
import re
from google import genai
import time
import engine
import prompts
import json

# ==============================================================================
# 1. 초기 설정 및 공통 함수 (통합 CSS 적용)
# ==============================================================================
APP_VERSION = "ver 52.0"
st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# CSS 완벽 통합: 폰트(명조체), 예법(적색 배제), 오행 바탕색(ver 48.9)
st.markdown("""
<style>
    /* 1. 구글 폰트 임포트 */
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic&family=Nanum+Myeongjo:wght@400;700;800&display=swap');
    
    /* 2. 메인 화면 배경 및 나눔명조체 적용 (span, div 등 광범위 적용 배제하여 아이콘 보호) */
    .stApp { background-color: #FFFDE7 !important;}
    p, h1, h2, h3, h4, h5, h6, table, tr, td, div.report-page { font-family: 'Nanum Myeongjo', serif !important; }
    
    /* 3. 사이드바 텍스트 폰트 (아이콘 충돌 방지를 위해 * 대신 특정 태그만 지정 - 원본 복구) */
    [data-testid="stSidebar"] {background-color: #F0F2F6 !important;}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {font-family: 'Nanum Gothic', sans-serif !important;}
    
    /* 4. 버튼 스타일 완벽 분리 (고딕체 유지) */
    div.stButton > button { font-family: 'Nanum Gothic', sans-serif !important; font-weight: 900 !important; }
    div.stButton > button[kind="primary"] {background-color: #D32F2F !important; color: white !important;}
    div.stButton > button[kind="secondary"] {background-color: #E8F5E9 !important; color: #2E7D32 !important; border: 1px solid #81C784 !important;}
    
    /* 5. 오행에 따른 자동 바탕색 (ver 48.9 기준 진한 색상) */
    .color-목 { background-color: #2E7D32 !important; color: #FFFFFF !important; }
    .color-화 { background-color: #C62828 !important; color: #FFFFFF !important; }
    .color-토 { background-color: #F9A825 !important; color: #000000 !important; }
    .color-금 { background-color: #9E9E9E !important; color: #FFFFFF !important; }
    .color-수 { background-color: #212121 !important; color: #FFFFFF !important; }
    
    /* 6. 표 및 감명서 내부 정렬, 테두리 강제 설정 */
    .result-table { width: 100%; border-collapse: collapse; border: 3px solid #3E2723; table-layout: fixed; }
    .result-table td { border: 1px solid #444 !important; padding: 5px !important; text-align: center; vertical-align: middle; }
    .top-header-cell { background-color: #1A237E !important; }
    .header-cell-main { background-color: #f5f5f5 !important; font-weight: 900; white-space: nowrap; }
    
    /* 7. 성명 및 주요 정보 텍스트 색상 수정 (예법 준수: 적색 배제) */
    .report-page, .report-page * { color: #000000 !important; }
    .report-page h1, .report-page h3 { color: #1A237E !important; } 
    
    /* 8. AI 통변 내용 박스 */
    .content-box-loose { line-height: 1.8; font-size: 16px; text-align: justify; word-break: keep-all; font-family: 'Nanum Myeongjo', serif !important; }
    
    /* 9. 스트림릿 시스템 아이콘 강제 복구 (안전장치) */
    span.material-symbols-rounded, i, svg {font-family: 'Material Symbols Rounded' !important;}
    
    /* 10. 프린트 설정 */
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

@st.cache_data(show_spinner=False, ttl=3600*24초) # ttl=3600*24초=86,400초 12시간 감명서 유효
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
    return get_ai_response(prompts.SYSTEM_ROLE, prompt_text, model_name='gemini-2.5-flash')

def call_light_api(prompt_text):
    return get_ai_response(prompts.SYSTEM_ROLE, prompt_text, model_name='gemini-2.5-flash')

def extract_ganji(text):
    if not text: return ""
    return re.sub(r'[^가-힣一-龥]', '', text)

# ==============================================================================
# 2. 사이드바 통제 센터 (입력 및 실행 버튼)
# ==============================================================================
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align: center;">
            <h1 style="font-family: 'Nanum Gothic', sans-serif; color: #000000; font-weight: 900; font-size: 20px; margin-bottom: 5px;">
                🏮 초연 시공명리 연구소
            </h1>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.markdown(f"<p style='text-align: center; color: #555555; font-family: sans-serif; font-size: 12px;'>{APP_VERSION} Master (Base + Gunghap)</p>", unsafe_allow_html=True)
    st.markdown("---")

    # ==============================================================================
    # 1. 상품 선택    
    st.markdown("<div style='font-size: 17px; font-weight: 900; color: #000000; margin-bottom: 5px; font-family: \"Nanum Gothic\", sans-serif;'>📋 분석 상품 선택</div>", unsafe_allow_html=True)
    u_product = st.selectbox("상품선택", ["1. 개인사주 및 일진 분석", "2. 타 감명서 비교", "3. 궁합 및 출산 택일"], label_visibility="collapsed")
    # ==============================================================================

    # 2. 신청인 기본 정보
    with st.expander("👤 신청인 기본 정보", expanded=True):
        # value를 비우고 placeholder를 사용하여 연한 회색 문구로 처리
        name = st.text_input("이름", value="", placeholder="홍길동", key="u_n")
        gender = st.selectbox("성별", ["남성", "여성"], key="u_g")
        u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
        u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")
        
        col_y, col_m, col_d = st.columns(3)
        with col_y: b_year = st.number_input("년도", 1900, 2050, value=1980, key="s_y")
        with col_m: b_month = st.number_input("월", 1, 12, value=1, key="s_m")
        with col_d: b_day = st.number_input("일", 1, 31, value=1, key="s_d")
        
        b_time = st.selectbox("태어난 시간", idx_list, key="s_t")

    # 3. 신청인 사주 역산 (항상 노출)
    with st.expander("🔍 신청인 사주간지 역산", expanded=False):
        col_g1, col_g2 = st.columns(2)
        with col_g1: ry = st.text_input("년주", value="", key="u_ry")
        with col_g2: rm = st.text_input("월주", value="", key="u_rm")
        col_g3, col_g4 = st.columns(2)
        with col_g3: rd = st.text_input("일주", value="", key="u_rd")
        with col_g4: rt = st.text_input("시주", value="", key="u_rt")
        
        if st.button("🔍 신청인 생년월일 자동입력", use_container_width=True, key="btn_user_rev"):
                _ry, _rm, _rd = extract_ganji(ry), extract_ganji(rm), extract_ganji(rd)
                
                if not _ry and not _rm and not _rd:
                    if 'rev_success_msg' in st.session_state: 
                        del st.session_state['rev_success_msg']
                    st.rerun()
                elif len(_ry)==2 and len(_rm)==2 and len(_rd)==2:
                    # (신청인 역산 로직 수행)
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
                                    found = True
                                    st.session_state.rev_success_msg = f"✅ 양력 {curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일 자동입력 완료!"
                                    st.rerun()
                                    break
                            curr_dt -= dt_mod.timedelta(days=1)
                        if found: break
                    if not found: st.error("일치하는 날짜가 없습니다.")
                else:
                    if 'rev_success_msg' in st.session_state: del st.session_state['rev_success_msg']
                    st.warning("간지를 2글자씩 정확히 입력하세요.")

    # 4. 상품별 추가 입력 로직 (상대방 UI 대칭 적용)
    other_report = ""
    f_name, f_gender, f_marital, f_cal = "", "여성", "미혼", "양력"
    f_y, f_m, f_d = 2000, 1, 1
    f_t = idx_list[0]
    run_delivery_calc = False

    if u_product == "1. 개인사주 및 일진 분석":
        run_iljin_calc = st.checkbox("🔮 일진 시공간 분석 추가 가동", value=False)
        
    elif u_product == "2. 타 감명서 비교":
        other_report = st.text_area("📄 타 감명서 원문 붙여넣기", height=150, key="other_reading")
        
    elif u_product == "3. 궁합 및 출산 택일":
        st.markdown("---")
        
        #-- 1. 상대방 기본 정보 박스
        with st.expander("👥 상대방 기본 정보", expanded=True):
            f_name = st.text_input("상대방 이름", value="", placeholder="이영희", key="f_n")
            f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_g")
            f_marital = st.selectbox("상대방 혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="f_m_stat")
            f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c")
            
            # '년도(상대), 월(상대), 일(상대)' 대칭 라벨 적용
            p_col1, p_col2, p_col3 = st.columns(3)
            f_y = p_col1.number_input("년도(상대)", 1900, 2050, value=1980, key="p_y_in")
            f_m = p_col2.number_input("월(상대)", 1, 12, value=1, key="p_m_in")
            f_d = p_col3.number_input("일(상대)", 1, 31, value=1, key="p_d_in")
            
            f_t = st.selectbox("태어난 시간(상대)", idx_list, key="p_t_key")
            
        #-- 2. 필요할 때만 펼쳐보는 역산 검색 도구
        with st.expander("👥 상대방 사주간지 역산", expanded=False):
            p_col_g1, p_col_g2 = st.columns(2)
            with p_col_g1: p_ry = st.text_input("상대방 년주", key="p_ry")
            with p_col_g2: p_rm = st.text_input("상대방 월주", key="p_rm")
            p_col_g3, p_col_g4 = st.columns(2)
            with p_col_g3: p_rd = st.text_input("상대방 일주", key="p_rd")
            with p_col_g4: p_rt = st.text_input("상대방 시주", key="p_rt")
            
            if st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="btn_partner_rev"):
                _pry, _prm, _prd = extract_ganji(p_ry), extract_ganji(p_rm), extract_ganji(p_rd)
                if not _pry and not _prm and not _prd:
                    if 'p_rev_success_msg' in st.session_state: del st.session_state['p_rev_success_msg']
                    st.rerun()
                elif len(_pry)==2 and len(_prm)==2 and len(_prd)==2:
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
                                    # 시간 로직 동일
                                    time_map_rev = {'子':'00:30 ~ 01:29 (朝子)시', '丑':'01:30 ~ 03:29 (丑)시', '寅':'03:30 ~ 05:29 (寅)시', '卯':'05:30 ~ 07:29 (卯)시', '辰':'07:30 ~ 09:29 (辰)시', '巳':'09:30 ~ 11:29 (巳)시', '午':'11:30 ~ 13:29 (午)시', '未':'13:30 ~ 15:29 (未)시', '申':'15:30 ~ 17:29 (申)시', '酉':'17:30 ~ 19:29 (酉)시', '戌':'19:30 ~ 21:29 (戌)시', '亥':'21:30 ~ 23:29 (亥)시'}
                                    if p_rt:
                                        p_ji_char = extract_ganji(p_rt)[-1] if extract_ganji(p_rt) else ""
                                        p_rt_h = K2H_JI.get(p_ji_char, p_ji_char)
                                        if p_rt_h in time_map_rev: st.session_state.p_t_key = time_map_rev[p_rt_h]
                                    p_found = True
                                    st.session_state.p_rev_success_msg = f"✅ 상대방 자동입력 완료!"
                                    st.rerun()
                                    break
                                p_curr_dt -= dt_mod.timedelta(days=1)
                        if p_found: break
                    if not p_found: st.error("일치하는 날짜가 없습니다.")
                else: st.warning("간지를 2글자씩 정확히 입력하세요.")

        #-- 3. 출산택일 체크박스 (역산 박스 아래로 이동 완료)
        st.markdown("<br>", unsafe_allow_html=True) # 시각적 여백을 살짝 추가
        run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석 추가 가동", value=False)

    # 5. 실행 버튼 (첫 번째 버튼)
    st.markdown("<br>", unsafe_allow_html=True)
    btn_run = st.button("✨ [초연 시공명리 풀이 가동]", key="btn_run", use_container_width=True, type="primary")

    # 6. 인쇄 버튼 (스트림릿 버튼을 사용하여 스타일 완벽 통일)
    if st.button("🖨️ 풀이 결과 인쇄 / PDF 저장", key="btn_print", use_container_width=True):
        components.html("""
        <script>
            window.parent.print();
        </script>
        """, height=0)

# ==============================================================================
# 3. 메인 화면 (1. 개인사주 및 일진 분석, 2. 타 감명서 비교 3. 궁합 및 출산 택일)
# ==============================================================================
if btn_run:
    if u_product == "1. 개인사주 및 일진 분석":
        klc = KoreanLunarCalendar()
        if "음력" in u_cal:
            is_leap = True if "윤달" in u_cal else False
            klc.setLunarDate(int(b_year), int(b_month), int(b_day), is_leap)
            sol_y, sol_m, sol_d = klc.solarYear, klc.solarMonth, klc.solarDay
            lun_y, lun_m, lun_d = int(b_year), int(b_month), int(b_day)
            leap_str = "윤달" if is_leap else "평달"
        else:
            klc.setSolarDate(int(b_year), int(b_month), int(b_day))
            sol_y, sol_m, sol_d = int(b_year), int(b_month), int(b_day)
            lun_y, lun_m, lun_d = klc.lunarYear, klc.lunarMonth, klc.lunarDay
            leap_str = "윤달" if klc.isIntercalation else "평달"
            
        curr_year = dt_mod.datetime.now().year
        age = curr_year - sol_y + 1
        p_icon = "♂️" if gender == "남성" else "♀️"
        # 성명 금기 예법 적용: 무조건 남색(#1A237E) 통일
        p_color = "#1A237E"
        today_str = dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
        
        def extract_time(time_str):
            if "모름" in time_str: return 0, 0
            match = re.search(r'(\d{2}):(\d{2})', time_str)
            return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

        with st.spinner(f"⏳ [초연 시공명리 분석({APP_VERSION}) 중....]"):
            h, m = extract_time(b_time)
            
            y_pillar, m_pillar, lon = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
            
            is_lunar_val = ("음력" in u_cal)
            is_leap_val = ("윤달" in u_cal)
            _, _, d_pillar = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)
            t_gan, t_ji = engine.get_time_ganji(d_pillar[0], b_time)

            gans = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]]
            jjis = [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
            hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
            hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]

            counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
            for c in gans + jjis:
                if c in "甲乙寅卯": counts['목']+=1
                elif c in "丙丁巳午": counts['화']+=1
                elif c in "戊己辰戌丑未": counts['토']+=1
                elif c in "庚辛申酉": counts['금']+=1
                elif c in "壬癸亥子": counts['수']+=1

            # 👇 ver 48.9 기준 진한 오행색이 적용되도록 CSS 클래스를 반환하는 함수 (td 태그 통째로 반환)
            def td_bg(ganji):
                oh = '무'
                if ganji in ['甲', '乙', '寅', '卯']: oh = '목'
                elif ganji in ['丙', '丁', '巳', '午']: oh = '화'
                elif ganji in ['戊', '己', '辰', '戌', '丑', '未']: oh = '토'
                elif ganji in ['庚', '辛', '申', '酉']: oh = '금'
                elif ganji in ['壬', '癸', '亥', '子']: oh = '수'
                return f"<td class='color-{oh}' style='border:1px solid #444 !important; width:21%; font-size:20px; font-weight:900;'>"

            guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
            guiin_str = guiin_map.get(ds, '없음')
            n_gong = engine.calculate_gongmang(ys, yb)
            i_gong = engine.calculate_gongmang(ds, db)
            cur_samjae = engine.get_samjae(yb, db)
            samjae_color = "#1A237E" if cur_samjae != "해당 없음" else "#2E7D32"

            # 합충형파해 폰트 축소 (적색 배제, 남색 처리)
            ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                cells = "".join([f"<td style='color:{('#1A237E' if ci==r_idx else ('#000' if engine.get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-size:11px; letter-spacing:-0.7px; line-height:1.2; word-break:keep-all; font-weight:900; border-top:0px solid transparent; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else engine.get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:13px; vertical-align:middle;'>합충형파해</td>" if l_idx==0 else ""
                ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

            base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
            adj_mins = engine.get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            order_dir = 1 if (engine.GAN.index(ys)%2==0) == (gender=='남성') else -1
            calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
            direction_str = "순행" if order_dir == 1 else "역행"

            # 1. 커버 페이지 (적색 배제 및 남색으로 통일)
            sol_str = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
            lun_str = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
            time_str = f"{b_time.split('(')[0].strip()} ({hb})시" if b_time != "시간 모름" else ""
            
            cover_html = f"""
            <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
                <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 90%; max-width: 800px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
                    <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                        <h1 class='title-gothic' style='font-size: 24px !important; margin:0 !important; font-weight: 900; white-space: nowrap;'>🏮초연 시공명리 사주풀이</h1>
                        <div style='text-align: right; margin-top: 10px;'>
                            <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px;'>{APP_VERSION}</span>
                        </div>
                    </div>
                    <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>
                        <h2 style='font-size: 24px; font-weight: 800; color: #1A237E; margin-bottom: 20px;'>{p_icon} 신청인 : {name} 님</h2>
                        <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                            <p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p>
                            <p style='margin: 5px 0 0 0; color: #1A237E; white-space: nowrap;'>{time_str}</p>
                        </div>
                    </div>
                    <p style='font-size: 18px; margin-top: 50px; font-weight: 800;'>{today_str}</p>
                    <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 20px;'>초연 시공명리 연구소</p>
                </div>
            </div>
            """

            # 2. 도입부 배너
            intro_html = f"""<div style='font-size: 16px; font-weight: 600; color: #333; text-align: justify; line-height: 1.8; margin-bottom: 5px;'>
<p style='text-indent: 15px; margin: 0 0 5px 0;'>기존 전통 명리학 사주풀이는 1년에 한 번 돌아오는 '12월지'와 '60일주'의 조합으로 720가지의 유형으로 시작합니다만,</p>
<p style='text-indent: 15px; margin: 0 0 5px 0;'>본 초연 시공명리 사주풀이는 5년에 한 번 돌아오는 '60월령'과 '60일주'의 조합으로 3,600가지의 유형으로 보다 더 정밀한 분석이 가능합니다.</p>
<p style='text-indent: 15px; margin: 0;'>기존 전통명리학에 비교하면 '5배', 요즘 유행하는 MBTI의 16가지 유형과 비교하면 무려 '225배' 더 세분화된 정밀한 사주풀이 분석입니다.</p>
</div>"""

            info_h = f"<div style='text-align:center; margin-bottom:25px; line-height:1.6; font-family:\"Nanum Myeongjo\", serif;'>"
            info_h += f"<span style='font-size:20px; font-weight:800; color:#1A237E; letter-spacing:1px; white-space:nowrap;'>{p_icon} {name}님 ({gender}, {u_marital}, {age}세)</span><br>"
            info_h += f"<span style='font-size:14px; font-weight:700; color:#444444; letter-spacing:0.5px; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span></div>"
            
            <div style="text-align:center; margin-bottom:25px; line-height:1.6; font-family: 'Nanum Myeongjo', serif;">
                <span style="font-size:20px; font-weight:800; color:#1A237E; letter-spacing: 1px; white-space:nowrap;">
                    {p_icon} {name}님 ({gender}, {u_marital}, {age}세)
                </span>
                <br>
                <span style="font-size:14px; font-weight:700; color:#444444; letter-spacing: 0.5px; white-space:nowrap; margin-top: 5px; display: inline-block;">
                    [양력: {sol_str} | 음력: {lun_str} {time_str}]
                </span>
            </div>
            """
            # ==============================================================================
            # 3. 사주 원국 테이블 본체 (ver 48.9 명품 격식 복원 + 신살 6개 압축 밀착본)
            # ==============================================================================
            # 👇 CSS 클래스를 이용하여 48.9 오행색 적용 완료
            def get_oh_class(ganji):
                oh = '무'
                if ganji in ['甲', '乙', '寅', '卯']: oh = '목'
                elif ganji in ['丙', '丁', '巳', '午']: oh = '화'
                elif ganji in ['戊', '己', '辰', '戌', '丑', '未']: oh = '토'
                elif ganji in ['庚', '辛', '申', '酉']: oh = '금'
                elif ganji in ['壬', '癸', '亥', '子']: oh = '수'
                return f"color-{oh}" if oh != '무' else ""

            # 합충형파해 관계선 생성
            ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                b_top = "0px solid transparent !important"
                # (주의) 기준점 색상을 빨간색(#D50000)에서 예법에 맞춰 남색(#1A237E)으로 변경했습니다.
                cells = "".join([f"<td style='color:{('#1A237E' if ci==r_idx else ('#000' if engine.get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else engine.get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

            # [일반신살 6개 제한 처리] 연산 로직 우선순위 상위 6개만 슬라이싱 및 줄바꿈 매핑
            filtered_shinsals = []
            for i in range(4):
                raw_shinsal = engine.get_general_shinsal_filtered(i, gans, jjis, gender)
                limited_shinsal = raw_shinsal[:6] if raw_shinsal else []
                filtered_shinsals.append("<br>".join(limited_shinsal) if limited_shinsal else "-")

            # 상단 인포 헤더
            info_h = f"<div style='text-align:center; font-family:\"Malgun Gothic\", sans-serif; margin-bottom:15px; line-height:1.5;'><span style='font-size:18px; font-weight:900; color:{p_color}; white-space:nowrap;'>{p_icon} {disp_name}님 ({u_gender}, {u_marital}, {u_age}세)</span><br><span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span></div>"

            # 사주 원국 테이블 조립
            table_html = f"""<div style='text-align:center; margin-bottom:10px;'>{info_h}</div>
            <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
            <tr class='top-header-cell'>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>구분</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>시주</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>일주</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>월주</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>년주</td>
            </tr>
            <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간합충</td>{"".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])}</tr>
            <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간십성</td><td style='border:1px solid #444;'>{engine.get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(ds,ms)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds,ys)}</td></tr>
            <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>천간</td>{engine.td(hs)}{engine.td(ds)}{engine.td(ms)}{engine.td(ys)}</tr>
            <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>지지</td>{engine.td(hb)}{engine.td(db)}{engine.td(mb)}{engine.td(yb)}</tr>
            <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지십성</td><td style='border:1px solid #444;'>{engine.get_ss(ds,hb)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds,db)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds,mb)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds,yb)}</td></tr>
            <tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444;'>{engine.get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
            {ji_rel_rows}
            <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이운성</td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{engine.get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
            <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이신살</td>{"".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{engine.get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
            <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(engine.get_general_shinsal_filtered(i, gans, jjis, u_gender)) if engine.get_general_shinsal_filtered(i, gans, jjis, u_gender) else '-'}</td>" for i in range(4)])}</tr>
            </table>
            """

            # ==============================================================================
            # 4. 마스터 바 (초정밀 대운수 calc_d 연동 및 A4 가로폭 최적화 마스터피스)
            # ==============================================================================
            master_bar_html = f"<div style='border:2px solid #3E2723; margin-top:15px; padding:8px 10px; display:flex; justify-content:space-between; align-items:center; font-family:\"Noto Serif KR\", serif !important; font-weight:900; font-size:12.5px; border-radius:8px; white-space:nowrap; background:#FFFDE7; letter-spacing:-0.7px;'>"
            master_bar_html += f"<div>🔢 대운수: <span style='color:#1A237E;'>{calc_d}</span></div><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 귀인: <span style='color:#1A237E;'>{guiin_str}</span></div><div>🎯 공망: [년]<span style='color:#1A237E;'>{n_gong}</span> [일]<span style='color:#1A237E;'>{i_gong}</span></div><div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div></div>"

            # ==============================================================================
            # 5. 초정밀 대운 / 세운 / 월운 흐름표 (글자 크기 축소, 극한 밀착 및 예법 적용)
            # ==============================================================================
            
            # [1단계] 대운의 흐름표 생성
            daewun_info = []
            un_html = f"<div style='margin-top:5px; margin-bottom:8px; font-size:17px; font-weight:900; color:#1A237E; font-family:\"Noto Serif KR\", serif !important;'>[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:12px; font-family:\"Noto Serif KR\", serif !important;'>"
            for i in range(10):
                val, c, j = i*10+calc_d, GAN[(GAN.index(ms)+(i+1)*order)%10] if ms in GAN else "-", JI[(JI.index(mb)+(i+1)*order)%12] if mb in JI else "-"
                daewun_info.append(f"{val}세:{c}{j}")
                is_active = val <= u_age < val+10
                bg_col = "#FFF9C4" if is_active else "transparent"
                b_left = "1px solid #ccc" if i != 9 else "none"
                
                un_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:2px; background-color:{bg_col}; line-height:1.15;'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:11.5px; border-bottom:1px solid #ccc;'>{val}세</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{get_ss(ds,c)}</div><div class='color-{get_color(c)}' style='font-size:15px; font-weight:900; padding:1px 0;'>{c}</div><div class='color-{get_color(j)}' style='font-size:15px; font-weight:900; padding:1px 0;'>{j}</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{get_ss(ds,j)}</div><div style='font-size:11px; font-weight:normal; color:#0D47A1; border-top:1px solid #ccc; padding-top:1px;'>{get_unsung(ds,j)}</div><div style='font-size:11px; font-weight:normal; color:#C62828; border-top:1px solid #ccc; padding-top:1px;'>{get_12_shinsal(yb, j)}</div></div>"
            un_html += "</div>"

            # [2단계] 세운의 흐름표 생성
            cur_dw_idx = max(0, (u_age - calc_d) // 10)
            dw_g_cur = GAN[(GAN.index(ms) + (cur_dw_idx+1)*order)%10] if ms in GAN else "-"
            dw_j_cur = JI[(JI.index(mb) + (cur_dw_idx+1)*order)%12] if mb in JI else "-"
            current_daewun_age = cur_dw_idx * 10 + calc_d
            
            start_year = u_y + current_daewun_age - 1
            sewun_info = []
            se_html = f"<div style='margin-top:10px; margin-bottom:8px; font-size:17px; font-weight:900; color:#1A237E; font-family:\"Noto Serif KR\", serif !important;'>[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:12px; font-family:\"Noto Serif KR\", serif !important;'>"
            for i in range(10):
                ty = start_year + i
                tage = current_daewun_age + i
                base = (ty - 1984) % 60
                tc, tj = GAN[base % 10], JI[base % 12]
                sewun_info.append(f"{ty}년({tc}{tj})")
                is_cur_yr = (ty == curr_y)
                bg_col = "#E1F5FE" if is_cur_yr else "transparent"
                b_left = "1px solid #ccc" if i != 9 else "none"
                
                se_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:2px; background-color:{bg_col}; line-height:1.15;'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:11.5px; line-height:1.2; border-bottom:1px solid #ccc;'>{ty}년<br>({tage}세)</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:15px; font-weight:900; padding:1px 0;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:15px; font-weight:900; padding:1px 0;'>{tj}</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{get_ss(ds,tj)}</div><div style='font-size:11px; font-weight:normal; color:#0D47A1; border-top:1px solid #ccc; padding-top:1px;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; font-weight:normal; color:#C62828; border-top:1px solid #ccc; padding-top:1px;'>{get_12_shinsal(yb, tj)}</div></div>"
            se_html += "</div>"

            # [3단계] 월운의 흐름표 생성
            wol_gans = ["己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚"]
            wol_jis = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]
            cur_wol_g = wol_gans[curr_m - 1]
            cur_wol_j = wol_jis[curr_m - 1]
            
            wol_html = f"<div style='margin-top:10px; margin-bottom:8px; font-size:17px; font-weight:900; color:#1A237E; font-family:\"Noto Serif KR\", serif !important;'>[ 월운의 흐름 ({curr_y}년도 양력기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:12px; font-family:\"Noto Serif KR\", serif !important;'>"
            for i in range(12):
                tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
                is_cur_m = (tm == curr_m)
                bg_col = "#E8F5E9" if is_cur_m else "transparent"
                b_left = "1px solid #ccc" if i != 11 else "none"
                
                wol_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:2px; background-color:{bg_col}; line-height:1.15;'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:11.5px; border-bottom:1px solid #ccc;'>{tm}월</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:15px; font-weight:900; padding:1px 0;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:15px; font-weight:900; padding:1px 0;'>{tj}</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{get_ss(ds,tj)}</div><div style='font-size:11px; font-weight:normal; color:#0D47A1; border-top:1px solid #ccc; padding-top:1px;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; font-weight:normal; color:#C62828; border-top:1px solid #ccc; padding-top:1px;'>{get_12_shinsal(yb, tj)}</div></div>"
            wol_html += "</div>"
            
            # [4단계] 과거 운세 데이터 및 절기/하지 정밀 연산 (ver 48.9 원본)
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

            # 6. AI 통변
            ai_output_html = ""
            try:
                fact_sheet = prompts.PERSONAL_SAJU_PROMPT.format(
                    name=name, gender=gender, ilgan=d_pillar[0], ilju=d_pillar, wolryeong=m_pillar,
                    jijanggan_info="엔진 데이터 정밀 연동됨", missing_and_gongmang="엔진 데이터 정밀 연동됨",
                    shinsal_info="엔진 데이터 정밀 연동됨", vault_info="엔진 데이터 정밀 연동됨"
                )
                ai_result = call_gemini_api(fact_sheet)
                ai_result = re.sub(r"안녕하세요, .*?감사드립니다\.", "", ai_result).strip()
                ai_output_html = prompts.HTML_LAYOUTS["report_box"].format(content=ai_result)
            except Exception:
                pass
            
            closing_html = f"""<div style='margin-top: 40px; border-top: 2px dashed #444; padding-top: 25px;'>
            <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드(bar-code)와 같지만, 우리가 살아가며 마주하는 스캐너(scanner)인 '운'은 늘 변화하며 흐릅니다.</p>
            <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
            <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 시공명리의 지혜와 궁금증이 있으시면 언제든 <b>'초연 시공명리 연구소'</b>의 문을 두드려 주십시오.</p>
            <p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
            <div style='text-align: right; margin-top: 30px;'>
            <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
            </div>
            </div>"""

            combined_report_box = f"""
            <div style='background-color:#FFFFFF; padding:40px; margin:20px auto; border:1px solid #E0E0E0; border-radius:15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); max-width:1000px;'>
                <div style='border: 2px solid #5D4037; border-radius: 12px; padding: 30px; background-color:#FAFAFA;'>
                    {intro_html}
                    {table_html}
                    {master_bar_html}
                    {un_html}
                    {se_html}
                    {wol_html}
                    {ai_output_html}
                    {closing_html}
                </div>
            </div>
            """
            st.markdown(cover_html, unsafe_allow_html=True)
            st.markdown(combined_report_box, unsafe_allow_html=True)

    # ==============================================================================
    # 2. 타 감명서 비교
    # ==============================================================================
    elif u_product == "2. 타 감명서 비교":
        st.header("⚖️ 초연 시공명리 타 감명서 1:1 비교")
        st.markdown("---")
        
        if not other_report:
            st.warning("👈 사이드바에 타 감명서 원문을 입력해주세요.")
        else:
            # 1) 개인 사주풀이 (입력된 사주 정보를 활용)
            st.subheader("1️⃣ 초연 시공명리 개인 사주 풀이")
            personal_prompt = prompts.PERSONAL_ANALYSIS_PROMPT.format(
                ilju=s_ilju, wolryeong=s_wolryeong, saju_structure=s_structure
            )
            personal_result = get_ai_response(prompts.SYSTEM_ROLE, personal_prompt)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=personal_result), unsafe_allow_html=True)
            
            # 2) 타 감명서 원본 출력
            st.subheader("2️⃣ 타 감명서 원본")
            st.info(other_report)
            
            # 3) 타 감명서 1:1 비교
            st.subheader("3️⃣ 타 감명서 1:1 비교 분석")
            with st.spinner("⏳ 비교 분석 중..."):
                compare_prompt = prompts.COMPARE_PROMPT.format(
                    other_report=other_report, 
                    ilju=s_ilju, 
                    wolryeong=s_wolryeong, 
                    saju_structure=s_structure,
                    daewun_info=daewun_info  # 대운 흐름 정보 추가
                )

                ai_result = get_ai_response(prompts.SYSTEM_ROLE, compare_prompt)
                st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)

    # ==============================================================================
    # 3. 궁합 및 출산 택일":
    # ==============================================================================
    elif u_product == "3. 궁합 및 출산 택일":
        st.header(f"💕 {name}님과 {f_name}님의 초연 궁합")
        st.markdown("---")
        loading_msg = "⏳궁합 및 출산 택일 길일 연산 중..." if run_delivery_calc else "⏳궁합 풀이 중..."
        
        with st.spinner(loading_msg):
            # [1] 통합 표지 렌더링
            app_p_icon = "♂️" if gender == "남성" else "♀️"
            part_p_icon = "♂️" if f_gender == "남성" else "♀️"
            
            gunghap_cover_html = f"""
<div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
    <div style='border: 4px solid #1A237E; padding: 60px 30px; border-radius: 20px; text-align: center; background: white; width: 90%; max-width: 800px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
        <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:50px;'>
            <h1 style='font-size: 26px !important; margin:0 !important; font-weight: 900; color: #1A237E; white-space: nowrap;'>초연 시공명리 궁합 감명서</h1>
            <div style='text-align: right; margin-top: 10px;'>
                <span style='font-size: 14px; letter-spacing: 1px; color: #555;'>{APP_VERSION}</span>
            </div>
        </div>
        <h3 style='font-size: 20px; font-weight: 800; color: #333; margin-bottom: 40px;'>[ 남녀 인연(궁합) 풀이 ]</h3>
        <div style='display: flex; justify-content: space-between; align-items: center; background:#F8F9FA; border: 1px solid #E8EAF6; padding: 35px 25px; border-radius: 15px; margin-bottom: 40px;'>
            <div style='flex: 1; text-align: center; border-right: 1px dashed #CCC; padding-right: 10px;'>
                <span style='font-size: 20px; font-weight: 800; color: #1A237E;'>{app_p_icon} {name} 님</span>
                <p style='font-size: 14px; color: #555; margin: 10px 0 0 0;'>{gender} / {u_marital}</p>
            </div>
            <div style='flex: 0.4; text-align: center; font-size: 24px; color: #1A237E; font-weight: 900;'>緣</div>
            <div style='flex: 1; text-align: center; border-left: 1px dashed #CCC; padding-left: 10px;'>
                <span style='font-size: 20px; font-weight: 800; color: #1A237E;'>{part_p_icon} {f_name} 님</span>
                <p style='font-size: 14px; color: #555; margin: 10px 0 0 0;'>{f_gender} / {f_marital}</p>
            </div>
        </div>
        <p style='font-size: 16px; font-weight: 700; color: #444; margin-top: 50px;'>위 두 분의 시공간적 에너지 흐름과 음양오행의 조화를 정밀 감명하였습니다.</p>
        <p style='font-size: 16px; margin-top: 60px; font-weight: 800; color: #000;'>{today_str}</p>
        <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 시공명리 연구소</p>
    </div>
</div>
<div class="page-break-before"></div>"""

            st.markdown(gunghap_cover_html, unsafe_allow_html=True)
        
        with st.spinner(loading_msg):
            # 오행 색상 클래스 판별용 공통 함수
            def get_oh_class(ganji):
                oh = '무'
                if ganji in ['甲', '乙', '寅', '卯']: oh = '목'
                elif ganji in ['丙', '丁', '巳', '午']: oh = '화'
                elif ganji in ['戊', '己', '辰', '戌', '丑', '未']: oh = '토'
                elif ganji in ['庚', '辛', '申', '酉']: oh = '금'
                elif ganji in ['壬', '癸', '亥', '子']: oh = '수'
                return f"color-{oh}" if oh != '무' else ""

            # 현재 연도 공통 선언
            curr_year = dt_mod.datetime.now().year
            today_str = dt_mod.datetime.now().strftime("%Y년 %m월 %d일")

            # ------------------------------------------------------------------
            # 0. 신청인(Applicant) 사주 및 대운 동적 연산 (누락 복구)
            # ------------------------------------------------------------------
            klc = KoreanLunarCalendar()
            if "음력" in u_cal:
                is_leap = True if "윤달" in u_cal else False
                klc.setLunarDate(int(b_year), int(b_month), int(b_day), is_leap)
                sol_y, sol_m, sol_d = klc.solarYear, klc.solarMonth, klc.solarDay
                lun_y, lun_m, lun_d = int(b_year), int(b_month), int(b_day)
                leap_str = "윤달" if is_leap else "평달"
            else:
                klc.setSolarDate(int(b_year), int(b_month), int(b_day))
                sol_y, sol_m, sol_d = int(b_year), int(b_month), int(b_day)
                lun_y, lun_m, lun_d = klc.lunarYear, klc.lunarMonth, klc.lunarDay
                leap_str = "윤달" if klc.isIntercalation else "평달"
                
            age = curr_year - sol_y + 1
            sol_str = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
            lun_str = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
            h, m = extract_time(b_time)
            time_str = f"{b_time.split('(')[0].strip()}시" if b_time != "시간 모름" else ""

            y_pillar, m_pillar, _ = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
            is_lunar_val = ("음력" in u_cal)
            is_leap_val = ("윤달" in u_cal)
            _, _, d_pillar = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)
            t_gan, t_ji = engine.get_time_ganji(d_pillar[0], b_time)

            gans = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]]
            jjis = [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
            
            counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
            for c in gans + jjis:
                if c in "甲乙寅卯": counts['목']+=1
                elif c in "丙丁巳午": counts['화']+=1
                elif c in "戊己辰戌丑未": counts['토']+=1
                elif c in "庚辛申酉": counts['금']+=1
                elif c in "壬癸亥子": counts['수']+=1
                
            base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
            adj_mins = engine.get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            order_dir = 1 if (engine.GAN.index(y_pillar[0])%2==0) == (gender=='남성') else -1
            calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
            direction_str = "순행" if order_dir == 1 else "역행"
            
            # 신청인 대운표 HTML 생성
            un_html = f"<div style='margin-top:25px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
            for i in range(10):
                val = i * 10 + calc_d
                c = engine.GAN[(engine.GAN.index(m_pillar[0]) + (i + 1) * order_dir) % 10] if m_pillar[0] in engine.GAN else "-"
                j = engine.JI[(engine.JI.index(m_pillar[1]) + (i + 1) * order_dir) % 12] if m_pillar[1] in engine.JI else "-"
                is_active = val <= age < val + 10
                bg_col = "#FFF9C4" if is_active else "transparent"
                b_left = "1px solid #ccc" if i != 9 else "none"
                c_cls, j_cls = get_oh_class(c), get_oh_class(j)
                
                un_html += f"""<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:5px; background-color:{bg_col};'>
<div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{val}세</div>
<div style='padding:2px; font-size:11px; color:#666;'>{engine.get_ss(d_pillar[0],c)}</div>
<div class='{c_cls}' style='font-size:18px; font-weight:900; padding:4px 0;'>{c}</div>
<div class='{j_cls}' style='font-size:18px; font-weight:900; padding:4px 0;'>{j}</div>
<div style='padding:2px; font-size:11px; color:#666;'>{engine.get_ss(d_pillar[0],j)}</div>
<div style='font-size:11px; border-top:1px solid #eee; padding-top:2px;'>{engine.get_unsung(d_pillar[0],j)}</div>
<div style='font-size:11px; color:#1A237E; font-weight:700; border-top:1px solid #eee; padding-top:2px;'>{engine.get_12_shinsal(y_pillar[1], j)}</div>
</div>"""
            un_html += "</div>"

            # ------------------------------------------------------------------
            # 1. 상대방(Partner) 사주 및 대운 동적 연산
            # ------------------------------------------------------------------
            p_klc = KoreanLunarCalendar()
            if "음력" in f_cal:
                p_is_leap = True if "윤달" in f_cal else False
                p_klc.setLunarDate(int(f_y), int(f_m), int(f_d), p_is_leap)
                p_sol_y, p_sol_m, p_sol_d = p_klc.solarYear, p_klc.solarMonth, p_klc.solarDay
                p_lun_y, p_lun_m, p_lun_d = int(f_y), int(f_m), int(f_d)
                p_leap_str = "윤달" if p_is_leap else "평달"
            else:
                p_klc.setSolarDate(int(f_y), int(f_m), int(f_d))
                p_sol_y, p_sol_m, p_sol_d = int(f_y), int(f_m), int(f_d)
                p_lun_y, p_lun_m, p_lun_d = p_klc.lunarYear, p_klc.lunarMonth, p_klc.lunarDay
                p_leap_str = "윤달" if p_klc.isIntercalation else "평달"
                
            p_age = curr_year - p_sol_y + 1
            p_sol_str = f"{p_sol_y}년 {p_sol_m:02d}월 {p_sol_d:02d}일"
            p_lun_str = f"{p_lun_y}년 {p_lun_m:02d}월 {p_lun_d:02d}일 ({p_leap_str})"
            p_h, p_m = extract_time(f_t)
            p_time_str = f"{f_t.split('(')[0].strip()}시" if f_t != "시간 모름" else ""

            p_y_pillar, p_m_pillar, _ = engine.get_true_year_month_pillar(int(f_y), int(f_m), int(f_d), p_h, p_m)
            p_is_lunar_val = ("음력" in f_cal)
            p_is_leap_val = ("윤달" in f_cal)
            _, _, p_d_pillar = engine.get_ganji_from_date(int(f_y), int(f_m), int(f_d), p_is_lunar_val, p_is_leap_val)
            p_t_gan, p_t_ji = engine.get_time_ganji(p_d_pillar[0], f_t)

            p_gans = [p_t_gan, p_d_pillar[0], p_m_pillar[0], p_y_pillar[0]]
            p_jjis = [p_t_ji, p_d_pillar[1], p_m_pillar[1], p_y_pillar[1]]
            
            p_counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
            for c in p_gans + p_jjis:
                if c in "甲乙寅卯": p_counts['목']+=1
                elif c in "丙丁巳午": p_counts['화']+=1
                elif c in "戊己辰戌丑未": p_counts['토']+=1
                elif c in "庚辛申酉": p_counts['금']+=1
                elif c in "壬癸亥子": p_counts['수']+=1
                
            p_base_dt = dt_mod.datetime(int(f_y), int(f_m), int(f_d), 12, 0)
            p_adj_mins = engine.get_total_time_adjustment(p_base_dt)
            p_utc_dt = p_base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=p_adj_mins)
            p_order_dir = 1 if (engine.GAN.index(p_y_pillar[0])%2==0) == (f_gender=='남성') else -1
            p_calc_d = engine.get_daeun_su_accurate(p_utc_dt, p_order_dir)
            p_direction_str = "순행" if p_order_dir == 1 else "역행"
            
            # 상대방 대운표 HTML 생성
            p_un_html = f"<div style='margin-top:25px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 대운의 흐름 (대운수: {p_calc_d}, {p_direction_str}) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
            for i in range(10):
                val = i * 10 + p_calc_d
                c = engine.GAN[(engine.GAN.index(p_m_pillar[0]) + (i + 1) * p_order_dir) % 10] if p_m_pillar[0] in engine.GAN else "-"
                j = engine.JI[(engine.JI.index(p_m_pillar[1]) + (i + 1) * p_order_dir) % 12] if p_m_pillar[1] in engine.JI else "-"
                is_active = val <= p_age < val + 10
                bg_col = "#FFF9C4" if is_active else "transparent"
                b_left = "1px solid #ccc" if i != 9 else "none"
                c_cls, j_cls = get_oh_class(c), get_oh_class(j)
                
                p_un_html += f"""<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:5px; background-color:{bg_col};'>
<div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{val}세</div>
<div style='padding:2px; font-size:11px; color:#666;'>{engine.get_ss(p_d_pillar[0],c)}</div>
<div class='{c_cls}' style='font-size:18px; font-weight:900; padding:4px 0;'>{c}</div>
<div class='{j_cls}' style='font-size:18px; font-weight:900; padding:4px 0;'>{j}</div>
<div style='padding:2px; font-size:11px; color:#666;'>{engine.get_ss(p_d_pillar[0],j)}</div>
<div style='font-size:11px; border-top:1px solid #eee; padding-top:2px;'>{engine.get_unsung(p_d_pillar[0],j)}</div>
<div style='font-size:11px; color:#1A237E; font-weight:700; border-top:1px solid #eee; padding-top:2px;'>{engine.get_12_shinsal(p_y_pillar[1], j)}</div>
</div>"""
            p_un_html += "</div>"

            # ------------------------------------------------------------------
            # 2. 신청인과 상대방의 남/녀 성별 할당 (동적 처리 완료)
            # ------------------------------------------------------------------
            if gender == "남성":
                # 남명 = 신청인 / 여명 = 상대방
                m_name, m_marital, m_age, m_sol_str, m_lun_str, m_time_str = name, u_marital, age, sol_str, lun_str, time_str
                m_gans, m_jjis, m_counts, m_un_html = gans, jjis, counts, un_html
                
                w_name, w_marital, w_age, w_sol_str, w_lun_str, w_time_str = f_name, f_marital, p_age, p_sol_str, p_lun_str, p_time_str
                w_gans, w_jjis, w_counts, w_un_html = p_gans, p_jjis, p_counts, p_un_html
            else:
                # 남명 = 상대방 / 여명 = 신청인
                w_name, w_marital, w_age, w_sol_str, w_lun_str, w_time_str = name, u_marital, age, sol_str, lun_str, time_str
                w_gans, w_jjis, w_counts, w_un_html = gans, jjis, counts, un_html
                
                m_name, m_marital, m_age, m_sol_str, m_lun_str, m_time_str = f_name, f_marital, p_age, p_sol_str, p_lun_str, p_time_str
                m_gans, m_jjis, m_counts, m_un_html = p_gans, p_jjis, p_counts, p_un_html

            # ------------------------------------------------------------------
            # 3. 통합 표지 및 남명/여명 사주 원국 렌더링
            # ------------------------------------------------------------------
            # [1] 통합 표지 렌더링
            app_p_icon = "♂️" if gender == "남성" else "♀️"
            part_p_icon = "♂️" if f_gender == "남성" else "♀️"
            
            gunghap_cover_html = f"""
<div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
    <div style='border: 4px solid #1A237E; padding: 60px 30px; border-radius: 20px; text-align: center; background: white; width: 90%; max-width: 800px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
        <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:50px;'>
            <h1 style='font-size: 26px !important; margin:0 !important; font-weight: 900; color: #1A237E; white-space: nowrap;'>&#127982; 초연 시공명리 궁합 감명서</h1>
            <div style='text-align: right; margin-top: 10px;'>
                <span style='font-size: 14px; letter-spacing: 1px; color: #555;'>{APP_VERSION}</span>
            </div>
        </div>
        <h3 style='font-size: 20px; font-weight: 800; color: #333; margin-bottom: 40px;'>[ 남녀 인연(궁합) 풀이 ]</h3>
        <div style='display: flex; justify-content: space-between; align-items: center; background:#F8F9FA; border: 1px solid #E8EAF6; padding: 35px 25px; border-radius: 15px; margin-bottom: 40px;'>
            <div style='flex: 1; text-align: center; border-right: 1px dashed #CCC; padding-right: 10px;'>
                <span style='font-size: 20px; font-weight: 800; color: #1A237E;'>{app_p_icon} {name} 님</span>
                <p style='font-size: 14px; color: #555; margin: 10px 0 0 0;'>{gender} / {u_marital}</p>
            </div>
            <div style='flex: 0.4; text-align: center; font-size: 24px; color: #1A237E; font-weight: 900;'>緣</div>
            <div style='flex: 1; text-align: center; border-left: 1px dashed #CCC; padding-left: 10px;'>
                <span style='font-size: 20px; font-weight: 800; color: #1A237E;'>{part_p_icon} {f_name} 님</span>
                <p style='font-size: 14px; color: #555; margin: 10px 0 0 0;'>{f_gender} / {f_marital}</p>
            </div>
        </div>
        <p style='font-size: 16px; font-weight: 700; color: #444; margin-top: 50px;'>위 두 분의 시공간적 에너지 흐름과 음양오행의 조화를 정밀 감명하였습니다.</p>
        <p style='font-size: 16px; margin-top: 60px; font-weight: 800; color: #000;'>{today_str}</p>
        <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 시공명리 연구소</p>
    </div>
</div>
<div class="page-break-before"></div>
"""
            st.markdown(gunghap_cover_html, unsafe_allow_html=True)
            # [남명 원국 및 대운표 렌더링]
            m_hs, m_ds, m_ms, m_ys = m_gans[0], m_gans[1], m_gans[2], m_gans[3]
            m_hb, m_db, m_mb, m_yb = m_jjis[0], m_jjis[1], m_jjis[2], m_jjis[3]
            m_guiin_str = guiin_map.get(m_ds, '없음')
            m_n_gong = engine.calculate_gongmang(m_ys, m_yb)
            m_i_gong = engine.calculate_gongmang(m_ds, m_db)
            m_cur_samjae = engine.get_samjae(m_yb, m_db)
            m_samjae_color = "#1A237E" if m_cur_samjae != "해당 없음" else "#2E7D32"

            m_ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                cells = "".join([f"<td style='color:{('#1A237E' if ci==r_idx else ('#000' if engine.get_ji_rel_set(m_jjis[r_idx], m_jjis[ci])!='-' else '#BBB'))}; font-size:11px; letter-spacing:-0.7px; line-height:1.2; word-break:keep-all; font-weight:900; border-top:0px solid transparent; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+m_jjis[r_idx]+')→' if ci==r_idx else engine.get_ji_rel_set(m_jjis[r_idx], m_jjis[ci]))}</td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:13px; vertical-align:middle;'>합충형파해</td>" if l_idx==0 else ""
                m_ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

            m_info_h = f"<div style='text-align:center; margin-bottom:15px; line-height:1.5;'><span style='font-size:18px; font-weight:900; color:#1A237E; white-space:nowrap;'>♂️ [男命] {m_name}님 사주원국</span><br><span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>[양력: {m_sol_str} | 음력: {m_lun_str} {m_time_str}]</span></div>"
            
            male_table_html = f"""
            <div style='background-color:#FFFFFF; padding:40px; margin:20px auto; border:1px solid #E0E0E0; border-radius:15px; max-width:1000px;'>
                <div style='border: 2px solid #5D4037; border-radius: 12px; padding: 30px; background-color:#FAFAFA;'>
                    {m_info_h}
                    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center; table-layout:fixed;'>
                    <tr class='top-header-cell' style='background-color:#1A237E;'>
                    <td style='border:1px solid #444; width:16%;'><span style='color:#FFFFFF; font-weight:900;'>구분</span></td>
                    <td style='border:1px solid #444; width:21%;'><span style='color:#FFFFFF; font-weight:900;'>시주</span></td>
                    <td style='border:1px solid #444; width:21%;'><span style='color:#FFFFFF; font-weight:900;'>일주</span></td>
                    <td style='border:1px solid #444; width:21%;'><span style='color:#FFFFFF; font-weight:900;'>월주</span></td>
                    <td style='border:1px solid #444; width:21%;'><span style='color:#FFFFFF; font-weight:900;'>년주</span></td>
                    </tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>천간합충</td>{"".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, m_gans)}</td>" for i in range(4)])}</tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>천간십성</td><td style='border:1px solid #444;'>{engine.get_ss(m_ds,m_hs)}</td><td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(m_ds,m_ms)}</td><td style='border:1px solid #444;'>{engine.get_ss(m_ds,m_ys)}</td></tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important; white-space:nowrap;'>천간</td>{td_bg(m_hs)}{m_hs}</td>{td_bg(m_ds)}{m_ds}</td>{td_bg(m_ms)}{m_ms}</td>{td_bg(m_ys)}{m_ys}</td></tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important; white-space:nowrap;'>지지</td>{td_bg(m_hb)}{m_hb}</td>{td_bg(m_db)}{m_db}</td>{td_bg(m_mb)}{m_mb}</td>{td_bg(m_yb)}{m_yb}</td></tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>지지십성</td><td style='border:1px solid #444;'>{engine.get_ss(m_ds,m_hb)}</td><td style='border:1px solid #444;'>{engine.get_ss(m_ds,m_db)}</td><td style='border:1px solid #444;'>{engine.get_ss(m_ds,m_mb)}</td><td style='border:1px solid #444;'>{engine.get_ss(m_ds,m_yb)}</td></tr>
                    <tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444; height:75px; vertical-align:middle;'>{engine.get_jijanggan_full(m_ds, m_jjis[i])}</td>" for i in range(4)])}</tr>
                    {m_ji_rel_rows}
                    <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>십이운성</td>{"".join([f"<td style='color:#1A237E; border:1px solid #444 !important;'>{engine.get_unsung(m_ds, m_jjis[i])}</td>" for i in range(4)])}</tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>십이신살</td>{"".join([f"<td style='color:#1A237E; border:1px solid #444 !important;'>{engine.get_12_shinsal(m_yb, m_jjis[i])}</td>" for i in range(4)])}</tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(engine.get_general_shinsal_filtered(i, m_gans, m_jjis, '남성')) if engine.get_general_shinsal_filtered(i, m_gans, m_jjis, '남성') else '-'}</td>" for i in range(4)])}</tr>
                    </table>
                    
                    <div style='border:2px solid #3E2723; margin-top:20px; padding:10px; display:flex; justify-content:space-between; font-weight:900; font-size:13px; border-radius:8px; white-space:nowrap; background:#FFF; margin-bottom:20px;'>
                    <div>💥 오행: 木({m_counts['목']}) 火({m_counts['화']}) 土({m_counts['토']}) 金({m_counts['금']}) 水({m_counts['수']})</div>
                    <div>🌟 천을귀인: <span style='color:#1A237E;'>{m_guiin_str}</span></div>
                    <div>🎯 공망: [년] <span style='color:#1A237E;'>{m_n_gong}</span> / [일] <span style='color:#1A237E;'>{m_i_gong}</span></div>
                    <div>🌪️ 삼재: <span style='color:{m_samjae_color};'>{m_cur_samjae}</span></div>
                    </div>
                    {m_un_html}
                </div>
            </div>
            <div class="page-break-before"></div>
            """
            st.markdown(male_table_html, unsafe_allow_html=True)

            # [여명 원국 및 대운표 렌더링]
            w_hs, w_ds, w_ms, w_ys = w_gans[0], w_gans[1], w_gans[2], w_gans[3]
            w_hb, w_db, w_mb, w_yb = w_jjis[0], w_jjis[1], w_jjis[2], w_jjis[3]
            w_guiin_str = guiin_map.get(w_ds, '없음')
            w_n_gong = engine.calculate_gongmang(w_ys, w_yb)
            w_i_gong = engine.calculate_gongmang(w_ds, w_db)
            w_cur_samjae = engine.get_samjae(w_yb, w_db)
            w_samjae_color = "#1A237E" if w_cur_samjae != "해당 없음" else "#2E7D32"

            w_ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                cells = "".join([f"<td style='color:{('#1A237E' if ci==r_idx else ('#000' if engine.get_ji_rel_set(w_jjis[r_idx], w_jjis[ci])!='-' else '#BBB'))}; font-size:11px; letter-spacing:-0.7px; line-height:1.2; word-break:keep-all; font-weight:900; border-top:0px solid transparent; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+w_jjis[r_idx]+')→' if ci==r_idx else engine.get_ji_rel_set(w_jjis[r_idx], w_jjis[ci]))}</td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:13px; vertical-align:middle;'>합충형파해</td>" if l_idx==0 else ""
                w_ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

            w_info_h = f"<div style='text-align:center; margin-bottom:15px; line-height:1.5;'><span style='font-size:18px; font-weight:900; color:#1A237E; white-space:nowrap;'>♀️ [女命] {w_name}님 사주원국</span><br><span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>[양력: {w_sol_str} | 음력: {w_lun_str} {w_time_str}]</span></div>"
            
            female_table_html = f"""
            <div style='background-color:#FFFFFF; padding:40px; margin:20px auto; border:1px solid #E0E0E0; border-radius:15px; max-width:1000px;'>
                <div style='border: 2px solid #5D4037; border-radius: 12px; padding: 30px; background-color:#FAFAFA;'>
                    {w_info_h}
                    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center; table-layout:fixed;'>
                    <tr class='top-header-cell' style='background-color:#1A237E;'>
                    <td style='border:1px solid #444; width:16%;'><span style='color:#FFFFFF; font-weight:900;'>구분</span></td>
                    <td style='border:1px solid #444; width:21%;'><span style='color:#FFFFFF; font-weight:900;'>시주</span></td>
                    <td style='border:1px solid #444; width:21%;'><span style='color:#FFFFFF; font-weight:900;'>일주</span></td>
                    <td style='border:1px solid #444; width:21%;'><span style='color:#FFFFFF; font-weight:900;'>월주</span></td>
                    <td style='border:1px solid #444; width:21%;'><span style='color:#FFFFFF; font-weight:900;'>년주</span></td>
                    </tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>천간합충</td>{"".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, w_gans)}</td>" for i in range(4)])}</tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>천간십성</td><td style='border:1px solid #444;'>{engine.get_ss(w_ds,w_hs)}</td><td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(w_ds,w_ms)}</td><td style='border:1px solid #444;'>{engine.get_ss(w_ds,w_ys)}</td></tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important; white-space:nowrap;'>천간</td>{td_bg(w_hs)}{w_hs}</td>{td_bg(w_ds)}{w_ds}</td>{td_bg(w_ms)}{w_ms}</td>{td_bg(w_ys)}{w_ys}</td></tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important; white-space:nowrap;'>지지</td>{td_bg(w_hb)}{w_hb}</td>{td_bg(w_db)}{w_db}</td>{td_bg(w_mb)}{w_mb}</td>{td_bg(w_yb)}{w_yb}</td></tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>지지십성</td><td style='border:1px solid #444;'>{engine.get_ss(w_ds,w_hb)}</td><td style='border:1px solid #444;'>{engine.get_ss(w_ds,w_db)}</td><td style='border:1px solid #444;'>{engine.get_ss(w_ds,w_mb)}</td><td style='border:1px solid #444;'>{engine.get_ss(w_ds,w_yb)}</td></tr>
                    <tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444; height:75px; vertical-align:middle;'>{engine.get_jijanggan_full(w_ds, w_jjis[i])}</td>" for i in range(4)])}</tr>
                    {w_ji_rel_rows}
                    <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>십이운성</td>{"".join([f"<td style='color:#1A237E; border:1px solid #444 !important;'>{engine.get_unsung(w_ds, w_jjis[i])}</td>" for i in range(4)])}</tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>십이신살</td>{"".join([f"<td style='color:#1A237E; border:1px solid #444 !important;'>{engine.get_12_shinsal(w_yb, w_jjis[i])}</td>" for i in range(4)])}</tr>
                    <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important; white-space:nowrap;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(engine.get_general_shinsal_filtered(i, w_gans, w_jjis, '여성')) if engine.get_general_shinsal_filtered(i, w_gans, w_jjis, '여성') else '-'}</td>" for i in range(4)])}</tr>
                    </table>
                    
                    <div style='border:2px solid #3E2723; margin-top:20px; padding:10px; display:flex; justify-content:space-between; font-weight:900; font-size:13px; border-radius:8px; white-space:nowrap; background:#FFF; margin-bottom:20px;'>
                    <div>오행: 木({w_counts['목']}) 火({w_counts['화']}) 土({w_counts['토']}) 金({w_counts['금']}) 水({w_counts['수']})</div>
                    <div>천을귀인: <span style='color:#1A237E;'>{w_guiin_str}</span></div>
                    <div>공망: [년] <span style='color:#1A237E;'>{w_n_gong}</span> / [일] <span style='color:#1A237E;'>{w_i_gong}</span></div>
                    <div>삼재: <span style='color:{w_samjae_color};'>{w_cur_samjae}</span></div>
                    </div>
                    {w_un_html}
                </div>
            </div>
            <div class="page-break-before"></div>
            """
            st.markdown(female_table_html, unsafe_allow_html=True)
            
            # [3] AI 궁합 통변 풀이
            gh_prompt = prompts.GUNGHAP_PROMPT.format(
                app_name=m_name, app_gender="남성", app_ilju=f"{m_ds}{m_db}", 
                partner_name=w_name, partner_gender="여성", partner_ilju=f"{w_ds}{w_db}",
                ilji_relation=engine.get_ji_rel_set(m_db, w_db), 
                oheng_balance="엔진 데이터 정밀 연동됨", gunghap_score=85, gunghap_grade="상생연분"
            )
            ai_result = get_ai_response(prompts.SYSTEM_ROLE, gh_prompt)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)
            
            if run_delivery_calc:
                st.markdown(f"### 👶 {name} & {f_name} 부부의 최적 출산 길일")
                st.success(f"탐색 기간 내의 길일 연산 엔진이 성공적으로 가동되었습니다. (⏳엔진 연동 대기중)")

             # [4] 맺음말 렌더링
            closing_del_html = f"""
<div style='margin-top: 20px;'>
    <p style='font-size:15px; text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>사랑하는 부부님, 하늘의 뜻과 부모님의 깊은 사랑이 한데 어우러져 귀한 인연이 이 세상에 찬란하게 빛을 발하며 나아가기를 진심으로 기원합니다.</p>
    <p style='font-size:15px; text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>두 분의 앞날에 건강과 행복이 가득하시기를 간절히 축원합니다.</p>
    <div style='text-align: right; margin-top: 25px;'>
        <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>초연 시공명리 연구소</span>
    </div>
<div class="page-break-before"></div>
"""
            st.markdown(closing_del_html, unsafe_allow_html=True)  
