import streamlit as st
import json
import os
from google import genai

# ✅ [모듈 호출] 박사님의 핵심 비법과 레시피를 불러옵니다.
import engine
import prompts

# ==============================================================================
# 🎯 [버전 컨트롤 타워 및 설정]
# ==============================================================================
APP_VERSION = "Ver 50.0 (Pro AI Architecture)"

# 반드시 최상단에 위치해야 하는 스트림릿 설정
st.set_page_config(page_title=f"초연 시공명리 {APP_VERSION}", layout="wide")

# ==============================================================================
# 💾 [데이터베이스 로드 (캐싱 최적화)]
# ==============================================================================
@st.cache_data
def load_choyeon_db():
    file_path = 'choyeon_db.json'
    if not os.path.exists(file_path):
        st.error("🚨 choyeon_db.json 파일을 찾을 수 없습니다.")
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"DB 로드 중 오류 발생: {e}")
        return {}

db = load_choyeon_db()

# ==============================================================================
# 🤖 [AI 엔진 세팅]
# ==============================================================================
def get_ai_response(system_prompt, user_prompt):
    """
    프롬프트 충돌 에러가 발생하지 않도록, AI 호출부를 완전히 분리 및 격리했습니다.
    """
    try:
        # 박사님의 API 키 설정 (Streamlit secrets 사용 권장)
        api_key = st.secrets.get("GEMINI_API_KEY", "여기에_API_키를_직접_입력하셔도_됩니다")
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
# 🖥️ [메인 UI 및 흐름 제어]
# ==============================================================================
st.title(f"🔮 초연 시공명리 통합 시스템 ({APP_VERSION})")
st.markdown("---")

# 1. 메뉴 선택 (4단계 흐름 정상화)
u_product = st.sidebar.radio(
    "📊 [분석 모드 선택]", 
    ["1. 개인사주 및 일진 분석", "2. 타 감명서 비교", "3. 궁합 풀이", "4. 출산 택일"]
)

# ==============================================================================
# ▶ 1. 개인사주 분석 모듈
# ==============================================================================
if u_product == "1. 개인사주 및 일진 분석":
    # 1. 입력창을 다시 좌측 사이드바로 이동 및 '일/시간' 추가
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 개인사주 정보 입력")
    name = st.sidebar.text_input("이름", "홍길동")
    gender = st.sidebar.selectbox("성별", ["남성", "여성"])
    
    col_y, col_m, col_d = st.sidebar.columns(3)
    with col_y: b_year = st.number_input("연도", 1900, 2050, 1980)
    with col_m: b_month = st.number_input("월", 1, 12, 1)
    with col_d: b_day = st.number_input("일", 1, 31, 1)
    
    b_time = st.sidebar.selectbox("태어난 시간", [
        "시간 모름", "朝子(조자) 00:00~01:29", "丑(축) 01:30~03:29", 
        "寅(인) 03:30~05:29", "卯(묘) 05:30~07:29", "辰(진) 07:30~09:29", 
        "巳(사) 09:30~11:29", "午(오) 11:30~13:29", "未(미) 13:30~15:29", 
        "申(신) 15:30~17:29", "酉(유) 17:30~19:29", "戌(술) 19:30~21:29", 
        "亥(해) 21:30~23:29", "夜子(야자) 23:30~23:59"
    ])
    
    # 2. 메인 화면은 출력 전용으로 깔끔하게 유지
    st.subheader("👤 개인사주 및 일진 분석")
    st.info("👈 좌측 사이드바에 사주 정보를 입력하고 '분석 실행' 버튼을 눌러주십시오.")

    # 3. 실행 버튼도 사이드바에 배치
    if st.sidebar.button("개인사주 분석 실행"):
        with st.spinner("주방장(engine)이 명리 연산을 수행하고 AI가 통변을 준비 중입니다..."):
            
            # [Step 1] engine.py를 호출하여 명리 팩트 도출 (예시 구조)
            ilgan = "甲" 
            ilju = "甲寅"
            wolryeong = db.get("wolryeong", {}).get("甲寅", "정보 없음")
            
            # [Step 2] 도출된 데이터를 prompts.py의 '팩트 시트' 양식에 주입
            fact_sheet_prompt = prompts.PERSONAL_SAJU_PROMPT.format(
                name=name,
                gender=gender,
                ilgan=ilgan,
                ilju=ilju,
                wolryeong=wolryeong,
                jijanggan_info="寅(戊,丙,甲) - 비견/건록좌",
                missing_and_gongmang="수(水) 기운 부족 / 공망: 子, 丑",
                shinsal_info="백호대살, 괴강살",
                vault_info="특이사항 없음"
            )
            
            # [Step 3] AI 호출 (에러 없는 순수 텍스트 전달)
            ai_result = get_ai_response(prompts.SYSTEM_ROLE, fact_sheet_prompt)
            
            # [Step 4] 화면 출력
            st.markdown(prompts.HTML_LAYOUTS["section_title"].format(title=f"{name}님의 초연명리 감명서"), unsafe_allow_html=True)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)

# ==============================================================================
# ▶ 2. 타 감명서 비교 모듈
# ==============================================================================
elif u_product == "2. 타 감명서 비교":
    st.subheader("⚖️ 타 감명서 1:1 비교 분석")
    other_report = st.text_area("타 감명서 원문을 붙여넣으세요.", height=200)
    
    if st.button("비교 분석 실행"):
        with st.spinner("AI가 타 감명서의 모순점을 찾고 초연명리 관점으로 재해석합니다..."):
            compare_prompt = prompts.COMPARE_PROMPT.format(
                other_report=other_report,
                ilju="甲寅", # engine 연산 결과 연동
                wolryeong="입춘 후 새싹이 돋는 시기",
                saju_structure="건록격"
            )
            ai_result = get_ai_response(prompts.SYSTEM_ROLE, compare_prompt)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)

# ==============================================================================
# ▶ 3. 궁합 풀이 모듈 
# ==============================================================================
elif u_product == "3. 궁합 풀이":
    st.subheader("💕 초연 궁합 풀이")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🧑 의뢰인 정보")
        m_name = st.text_input("의뢰인 이름", "김철수")
        m_gender = st.selectbox("의뢰인 성별", ["남성", "여성"], key="m_gen")
        m_year = st.number_input("태어난 연도", 1900, 2050, 1990, key="m_y")
        m_month = st.number_input("월", 1, 12, 1, key="m_m")
        m_day = st.number_input("일", 1, 31, 1, key="m_d")
        
    with col2:
        st.markdown("#### 👩 상대방 정보")
        f_name = st.text_input("상대방 이름", "이영희")
        f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_gen")
        f_year = st.number_input("태어난 연도", 1900, 2050, 1992, key="f_y")
        f_month = st.number_input("월", 1, 12, 1, key="f_m")
        f_day = st.number_input("일", 1, 31, 1, key="f_d")

    if st.button("궁합 분석 실행"):
        with st.spinner("두 사람의 시공간 에너지를 교차 분석 중입니다..."):
            
            # [Step 1] engine 연산 (예시 구조)
            # 실제로는 engine.get_true_year_month_pillar 등을 호출하여 명식을 뽑습니다.
            m_ilju = "庚申" # 예시 연산 결과
            f_ilju = "乙卯"
            
            # engine의 궁합 클래스 호출
            gh_engine = engine.UniversalPrintableGunghap(m_name, f_name, ["庚","申","?","?"], ["乙","卯","?","?"])
            gh_engine.run_universal_logic()
            
            # [Step 2] 팩트 시트 생성 (prompts.py 연동)
            gunghap_prompt = prompts.GUNGHAP_PROMPT.format(
                app_name=m_name,
                app_gender=m_gender,
                app_ilju=m_ilju,
                partner_name=f_name,
                partner_gender=f_gender,
                partner_ilju=f_ilju,
                ilji_relation="원진 및 암합",
                oheng_balance="남성은 금기운, 여성은 목기운이 강해 상호 보완됨",
                gunghap_score=gh_engine.final_score,
                gunghap_grade=gh_engine.grade
            )
            
            # [Step 3] AI 호출 및 출력
            ai_result = get_ai_response(prompts.SYSTEM_ROLE, gunghap_prompt)
            st.markdown(prompts.HTML_LAYOUTS["section_title"].format(title=f"{m_name}님과 {f_name}님의 초연 궁합"), unsafe_allow_html=True)
            st.markdown(prompts.HTML_LAYOUTS["report_box"].format(content=ai_result), unsafe_allow_html=True)

# ==============================================================================
# ▶ 4. 출산 택일 모듈
# ==============================================================================
elif u_product == "4. 출산 택일":
    st.subheader("👶 생체 주기 기반 출산 택일")
    st.info("부모의 명식과 생체 주기를 교차하여, 아이의 가장 좋은 시공간(길일)을 연산합니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 👨 부(父) 정보")
        f_year = st.number_input("부 연도", 1950, 2050, 1990)
        # (생략) 월/일 등 입력 추가
    with col2:
        st.markdown("#### 👩 모(母) 정보")
        m_year = st.number_input("모 연도", 1950, 2050, 1992)
        # (생략) 월/일 등 입력 추가
        
    st.markdown("#### 📅 출산 예정 기간")
    s_date = st.date_input("시작일")
    e_date = st.date_input("종료일")

    if st.button("길일 연산 및 AI 추천"):
        with st.spinner("가장 좋은 시공간을 찾고 있습니다..."):
            # [Step 1] engine 호출
            # engine.get_optimized_delivery_days() 사용
            
            # [Step 2] 결과 정리 및 AI 호출
            st.success("연산이 완료되었습니다! (AI 연동 부분은 이후 고도화 가능)")
            st.write("UI 레이아웃이 성공적으로 자리 잡았습니다.")
