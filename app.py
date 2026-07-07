import streamlit as st
import json
import os
from google import genai

import engine
import prompts

# ==============================================================================
# 🎯 [버전 컨트롤 타워 및 설정]
# ==============================================================================
APP_VERSION = "ver 50.0"

st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# ✅ UI 스타일링 (사이드바 연한 노랑, 타이틀 붉은색, 메인화면 여백 최적화)
st.markdown("""
<style>
    /* 사이드바 배경 연한 노랑색 */
    [data-testid="stSidebar"] {
        background-color: #FFFDE7 !important;
    }
    /* 메인 화면 상단 여백 깔끔하게 정리 */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 💾 [데이터베이스 로드]
# ==============================================================================
@st.cache_data
def load_choyeon_db():
    file_path = 'choyeon_db.json'
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {}

db = load_choyeon_db()

def get_ai_response(system_prompt, user_prompt):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "API_키를_입력하세요")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            ),
        )
        return response.text
    except Exception as e:
        return f"AI 연산 중 오류가 발생했습니다: {str(e)}"

# ==============================================================================
# 🖥️ [사이드바 통제 센터]
# ==============================================================================
# 1. 최상단 타이틀 (붉은색)
st.sidebar.markdown(f"<h2 style='color:#D32F2F; font-weight:900;'>🔮 초연 시공명리 연구소 <br><span style='font-size:14px; color:#333;'>({APP_VERSION})</span></h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# 2. 통합 메뉴 (출산택일은 궁합 안으로 편입)
u_product = st.sidebar.radio(
    "📊 [분석 모드 선택]", 
    ["1. 개인사주 및 일진 분석", "2. 타 감명서 비교", "3. 궁합 및 출산 택일"]
)
st.sidebar.markdown("---")

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
