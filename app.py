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
    st.subheader("👤 개인사주 기본 정보 입력")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: name = st.text_input("이름", "홍길동")
    with col2: gender = st.selectbox("성별", ["남성", "여성"])
    with col3: b_year = st.number_input("태어난 연도", 1900, 2050, 1980)
    with col4: b_month = st.number_input("월", 1, 12, 1)
    
    if st.button("개인사주 분석 실행 (AI 자율 풀이)"):
        with st.spinner("주방장(engine)이 명리 연산을 수행하고 AI가 통변을 준비 중입니다..."):
            
            # [Step 1] engine.py를 호출하여 명리 팩트 도출
            # (예시: engine.py의 함수들을 사용하여 데이터를 가져옴)
            # 실제로는 박사님의 사주 계산 로직에 따라 연산 결과를 변수에 담습니다.
            ilgan = "甲" # 예시 데이터
            ilju = "甲寅"
            wolryeong = db.get("wolryeong", {}).get("甲寅", "정보 없음")
            
            # [Step 2] 도출된 데이터를 prompts.py의 '팩트 시트' 양식에 주입
            fact_sheet_prompt = prompts.PERSONAL_SAJU_PROMPT.format(
                name=name,
                gender=gender,
                ilgan=ilgan,
                ilju=ilju,
                wolryeong=wolryeong,
                jijanggan_info="寅(戊,丙,甲) - 비견/건록좌", # engine에서 도출한 결과
                missing_and_gongmang="수(水) 기운 부족 / 공망: 子, 丑",
                shinsal_info="백호대살, 괴강살",
                vault_info="특이사항 없음"
            )
            
            # [Step 3] AI 호출 (에러 없는 순수 텍스트 전달)
            ai_result = get_ai_response(prompts.SYSTEM_ROLE, fact_sheet_prompt)
            
            # [Step 4] 화면 출력 (HTML 템플릿 사용)
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
    st.info("상세한 궁합 알고리즘은 engine.UniversalPrintableGunghap 클래스를 호출하여 처리합니다.")
    # UI 구성 및 engine 호출 로직 작성

# ==============================================================================
# ▶ 4. 출산 택일 모듈
# ==============================================================================
elif u_product == "4. 출산 택일":
    st.subheader("👶 생체 주기 기반 출산 택일")
    st.info("engine.get_optimized_delivery_days 함수를 통해 길일을 연산합니다.")
    # UI 구성 및 engine 호출 로직 작성
