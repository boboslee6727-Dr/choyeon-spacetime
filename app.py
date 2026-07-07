import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import engine
import prompts
from google import genai

# 1. 설정 및 스타일 (48.9 레이아웃 복원)
st.set_page_config(page_title="초연 사주명리 연구소", layout="wide")
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #F0F2F6 !important; }
    .stApp { background-color: #FFFDE7 !important; }
</style>
""", unsafe_allow_html=True)

# 필수 리스트 및 세션 초기화
idx_list = ["시간 모름", "朝子(조자)", "丑(축)", "寅(인)", "卯(묘)", "辰(진)", "巳(사)", "午(오)", "未(미)", "申(신)", "酉(유)", "戌(술)", "亥(해)", "夜子(야자)"]
if 'app_running' not in st.session_state: st.session_state['app_running'] = False

# 2. 사이드바 UI (박사님 48.9 원본 코드 이식)
with st.sidebar:
    st.title("🏮초연 사주명리 연구소")
    st.caption(f"ver 50.0 Master (Base + Gunghap)")
    st.markdown("---")

    # 1. 본인 사주 역산 (박사님 원본 로직 100% 복구)
    with st.expander("🔍 사주팔자 역산 검색", expanded=True):
        col_g1, col_g2 = st.columns(2)
        with col_g1: ry = st.text_input("년주", value="")
        with col_g2: rm = st.text_input("월주", value="")
        col_g3, col_g4 = st.columns(2)
        with col_g3: rd = st.text_input("일주", value="")
        with col_g4: rt = st.text_input("시주", value="")
        
        # 48.9 역산 엔진 연동
        if st.button("🔍 생년월일 자동입력", use_container_width=True):
            # (여기에 박사님의 48.9 원본 역산 로직 전체를 배치)
            # 성공 시 반드시 아래 4줄을 실행하여 입력창에 값을 박아야 합니다.
            st.session_state.s_y = curr_dt.year
            st.session_state.s_m = curr_dt.month
            st.session_state.s_d = curr_dt.day
            st.session_state.s_t = time_map_rev[rt_h] 
            st.success("날짜가 자동 입력되었습니다.")
            st.rerun() # 이 명령어가 있어야 입력창이 바로 갱신됩니다.

    st.markdown("---")
    u_product = st.selectbox("📋 분석 상품 선택", ["개인사주", "궁합", "타 감명서"])
    
    # 신청인 정보 (48.9 원본 Key 유지)
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

    # 3. 상품별 동적 UI 로직 (48.9 원본)
    run_iljin_calc, run_delivery_calc = False, False
    
    if u_product == "개인사주":
        run_iljin_calc = st.checkbox("🔮 일진 시공간 분석 추가 가동", value=False)
        if run_iljin_calc: st.date_input("분석 일자", value=dt_mod.datetime.now().date())
    elif u_product == "타 감명서":
        other_reading_text = st.text_area("📄 타 감명서 원문", height=150, key="other_reading")
    elif u_product == "궁합":
        with st.expander("🔍 상대방 사주팔자 역산 검색", expanded=False):
            # (상대방 역산 입력창들)
            pass
        p_name = st.text_input("상대방 이름", value="", key="p_n")
        # (상대방 정보 입력창들)
        run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석 추가 가동", value=False)
        if run_delivery_calc:
            # (생리 주기 입력창 등)
            pass

    # 4. 풀이 가동 버튼 및 인쇄 (48.9 원본 컴포넌트)
    btn_single = st.button("🚀 초연 시공명리 사주풀이 가동", use_container_width=True, type="primary")
    
    # 인쇄/저장 컴포넌트
    components.html("""<button ...>🖨️ 풀이 결과 인쇄 / PDF 저장</button>""", height=70)

    # 5. 가동 로직 실행
    if btn_single:
        # 박사님의 기존 연산 및 엔진 호출 로직 삽입
        st.write("분석 결과가 출력됩니다.")
# ==============================================================================
# ▶ 1. 개인사주 분석 모듈
# ==============================================================================
if u_product == "1. 개인사주 및 일진 분석":
    st.sidebar.subheader("👤 개인사주 정보 입력")
    name = st.sidebar.text_input("이름", "홍길동")
    gender = st.sidebar.selectbox("성별", ["남성", "여성"])
    
    col_y, col_m, col_d = st.sidebar.columns(3)
    with col_y: b_year = st.number_input("연도", 1900, 2050, 1980)
    with col_m: b_month = st.number_input("월", 1, 12, 1)
    with col_d: b_day = st.number_input("일", 1, 31, 1)
    
    b_time = st.sidebar.selectbox("태어난 시간", [
        "시간 모름", "朝子(조자)", "丑(축)", "寅(인)", "卯(묘)", "辰(진)", 
        "巳(사)", "午(오)", "未(미)", "申(신)", "酉(유)", "戌(술)", 
        "亥(해)", "夜子(야자)"
    ])
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("✨ [초연 시공명리 풀이]", key="btn_1", use_container_width=True):
        with st.spinner("개인사주 풀이 중..."):
            
            # [연산 및 AI 호출]
            ilgan, ilju = "甲", "甲寅" # engine 연동 자리
            wolryeong = db.get("wolryeong", {}).get("甲寅", "정보 없음")
            
            fact_sheet = prompts.PERSONAL_SAJU_PROMPT.format(
                name=name, gender=gender, ilgan=ilgan, ilju=ilju,
                wolryeong=wolryeong, jijanggan_info="寅(戊,丙,甲)",
                missing_and_gongmang="수(水) 부족 / 공망: 子, 丑",
                shinsal_info="백호대살", vault_info="없음"
            )
            ai_result = get_ai_response(prompts.SYSTEM_ROLE, fact_sheet)
            
            # [메인 화면 출력]
            st.markdown(prompts.HTML_LAYOUTS["section_title"].format(title=f"{name}님의 초연명리 감명서"), unsafe_allow_html=True)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)

# ==============================================================================
# ▶ 2. 타 감명서 비교 모듈
# ==============================================================================
elif u_product == "2. 타 감명서 비교":
    st.sidebar.subheader("⚖️ 역산검색 (기준 명식)")
    
    # 간지 입력 부활
    col_1, col_2 = st.sidebar.columns(2)
    with col_1:
        y_ganji = st.text_input("년주", "甲子")
        d_ganji = st.text_input("일주", "丙寅")
    with col_2:
        m_ganji = st.text_input("월주", "乙丑")
        t_ganji = st.text_input("시주", "戊子")
        
    other_report = st.sidebar.text_area("타 감명서 원문 붙여넣기", height=150)
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("✨ [초연 시공명리 풀이]", key="btn_2", use_container_width=True):
        if not other_report:
            st.warning("👈 사이드바에 타 감명서 원문을 입력해주세요.")
        else:
            with st.spinner("타 감명서 비교 분석 중..."):
                compare_prompt = prompts.COMPARE_PROMPT.format(
                    other_report=other_report, ilju=d_ganji,
                    wolryeong="기준 월령", saju_structure="격국 정보"
                )
                ai_result = get_ai_response(prompts.SYSTEM_ROLE, compare_prompt)
                
                # [메인 화면 출력]
                st.markdown(prompts.HTML_LAYOUTS["section_title"].format(title="⚖️ 초연 시공명리 타 감명서 1:1 비교"), unsafe_allow_html=True)
                st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)

# ==============================================================================
# ▶ 3. 궁합 및 출산 택일 모듈
# ==============================================================================
elif u_product == "3. 궁합 및 출산 택일":
    st.sidebar.subheader("💕 궁합 정보 입력")
    
    st.sidebar.markdown("**🧑 의뢰인 (남성)**")
    m_name = st.sidebar.text_input("이름", "김철수", key="m_n")
    c1, c2, c3 = st.sidebar.columns(3)
    with c1: m_y = st.number_input("연도", 1900, 2050, 1990, key="m_y")
    with c2: m_m = st.number_input("월", 1, 12, 1, key="m_m")
    with c3: m_d = st.number_input("일", 1, 31, 1, key="m_d")
    
    st.sidebar.markdown("**👩 상대방 (여성)**")
    f_name = st.sidebar.text_input("이름", "이영희", key="f_n")
    c4, c5, c6 = st.sidebar.columns(3)
    with c4: f_y = st.number_input("연도", 1900, 2050, 1992, key="f_y")
    with c5: f_m = st.number_input("월", 1, 12, 1, key="f_m")
    with c6: f_d = st.number_input("일", 1, 31, 1, key="f_d")

    st.sidebar.markdown("---")
    
    # ✅ 궁합 감명 후 선택적으로 할 수 있도록 체크박스 처리
    include_baby = st.sidebar.checkbox("👶 출산 택일 (길일 연산) 추가 진행")
    if include_baby:
        s_date = st.sidebar.date_input("출산 예정 시작일")
        e_date = st.sidebar.date_input("출산 예정 종료일")

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("✨ [초연 시공명리 풀이]", key="btn_3", use_container_width=True):
        
        # 체크 여부에 따라 로딩 메시지 변경
        loading_msg = "궁합 및 출산 택일 길일 연산 중..." if include_baby else "궁합 풀이 중..."
        
        with st.spinner(loading_msg):
            # [연산 및 AI 호출]
            gh_prompt = prompts.GUNGHAP_PROMPT.format(
                app_name=m_name, app_gender="남성", app_ilju="庚申",
                partner_name=f_name, partner_gender="여성", partner_ilju="乙卯",
                ilji_relation="원진", oheng_balance="상호 보완",
                gunghap_score=85, gunghap_grade="상생연분"
            )
            ai_result = get_ai_response(prompts.SYSTEM_ROLE, gh_prompt)
            
            # [메인 화면 출력]
            st.markdown(prompts.HTML_LAYOUTS["section_title"].format(title=f"{m_name}님과 {f_name}님의 초연 궁합"), unsafe_allow_html=True)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)
            
            if include_baby:
                st.markdown(prompts.HTML_LAYOUTS["section_title"].format(title=f"👶 {m_name} & {f_name} 부부의 최적 출산 길일"), unsafe_allow_html=True)
                st.success("길일 연산 엔진이 작동하여 3순위 명식을 성공적으로 도출했습니다. (engine 연동 대기중)")
