# ==============================================================================
# 2. 사이드바 통제 센터 (방탄(Bulletproof) 구조 및 변수 선언 안전화)
# ==============================================================================
with st.sidebar:
    # 💡 [보완] 상품 카테고리를 새로 변경할 때만 이전 결과를 닫도록 안전화
    def stop_ai():
        # 사용자가 상품을 바꿨을 때만 결과를 끄도록 처리 (일반 Rerun 시에는 상태 유지)
        st.session_state['app_running'] = False

    # 🚨 [수정안] 사이드바 토글 버튼(>>)과의 겹침 방지를 위한 상단 여백 및 격리 블록 적용
    st.markdown(f"""
        <div style="padding-top: 15px; margin-bottom: 5px; text-align: center;">
            <h1 style="font-family: 'Nanum Gothic', sans-serif; color: #000000; font-weight: 900; font-size: 20px; margin: 0 0 5px 0;">🏮 초연 시공명리 연구소</h1>
            <p style="color: #555555; font-family: sans-serif; font-size: 12px; margin: 0;">{APP_VERSION} Master (Base + Gunghap)</p>
        </div>
        <hr style="margin: 10px 0 15px 0;">
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size: 17px; font-weight: 900; color: #000000; margin-bottom: 10px; font-family: \"Nanum Gothic\", sans-serif;'>📋 분석 상품 선택</div>", unsafe_allow_html=True)

    main_category = st.selectbox("어떤 상담을 원하십니까?", ["1. 사주팔자 및 운세 풀이", "2. 연애/결혼운 (궁합) 풀이", "3. 타 감명서 비교"], key="main_category", on_change=stop_ai)

    # 💡 u_product 변수 사전 안전 초기화 (NameError 및 렌더링 충돌 원천 방지)
    u_product = "1-1. 사주팔자 및 대운 분석"

    if main_category == "1. 사주팔자 및 운세 풀이":
        u_product = st.radio("상세 분석 항목:", ["1-1. 사주팔자 및 대운 분석", "1-2. 올 해의 운세 상세 분석", "1-3. 이번 달의 운세 상세 분석", "1-4. 재물운 특화 분석", "1-5. 직업/진학운 특화 분석", "1-6. 건강운 특화 분석", "1-7. 이사 및 방위 특화 분석"], key="sub_category_1", on_change=stop_ai)
    elif main_category == "2. 연애/결혼운 (궁합) 풀이":
        u_product = st.radio("상세 분석 항목:", ["2-0. 연애/결혼운 (궁합) 기본 풀이", "2-1. 결혼 택일", "2-2. 출산 택일"], key="sub_category_2", on_change=stop_ai)
    else:
        u_product = st.radio("비교 분석 대상:", ["3-1. 타 감명서 비교 (사주)", "3-2. 타 감명서 비교 (궁합)"], key="sub_category_3", on_change=stop_ai)
    st.markdown("---")

    if "u_g" not in st.session_state: st.session_state["u_g"] = "남성"
    if "f_g" not in st.session_state: st.session_state["f_g"] = "여성"

    def sync_partner_gender():
        u_val = st.session_state.get("u_g", "남성")
        st.session_state["f_g"] = "남성" if u_val == "여성" else "여성"

    def sync_user_gender():
        f_val = st.session_state.get("f_g", "여성")
        st.session_state["u_g"] = "여성" if f_val == "남성" else "남성"

    # ==============================================================================
    # 🔍 신청인 사주간지 역산 (시간 자동입력 완벽 연동 완제본)
    # ==============================================================================
