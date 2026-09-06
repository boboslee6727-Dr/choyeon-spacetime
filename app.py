st.markdown("<div style='font-family: \"Nanum Gothic\", sans-serif; font-size: 16px; font-weight: 800; color: #111111; margin-top: 14px; margin-bottom: 8px;'>📋 분석 상품 선택</div>", unsafe_allow_html=True)

        # 🆕 대제목(main_category)은 크고 굵게, 하위 상품(라디오)은 들여쓰기된 소제목처럼 보이도록 스타일 적용
        st.markdown("""
        <style>
        div[data-testid="stSelectbox"] label p { font-size: 17px !important; font-weight: 900 !important; color: #1A237E !important; }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] * { font-size: 16px !important; font-weight: 800 !important; }
        div[data-testid="stRadio"] { margin-left: 14px !important; padding-left: 10px !important; border-left: 3px solid #C5CAE9 !important; }
        div[data-testid="stRadio"] label p { font-size: 13.5px !important; font-weight: 500 !important; color: #333333 !important; }
        </style>
        """, unsafe_allow_html=True)

        main_category = st.selectbox(
            "어떤 상담을 원하십니까?", 
            ["1. 개인 사주팔자 풀이 (종합)", "2. 테마별 특성화 상담", "3. 커플 연애/결혼운 (궁합) 풀이", "4. 타 감명서 비교"], 
            key="main_category", 
            on_change=stop_ai
        )
        u_product = "1-1. 사주팔자와 운세풀이"
        if main_category == "1. 개인 사주팔자 풀이 (종합)":
            u_product = st.radio("상세 분석 항목:", ["1-1. 사주팔자와 운세풀이", "1-2. 올 해 (특정 연도) 운세 상세분석", "1-3. 이번 달 (특정 월) 운세 상세분석", "1-4. 이번(특정) 주 및 일 운세 상세분석"], key="sub_category_1", on_change=stop_ai)
        elif main_category == "2. 테마별 특성화 상담":
            u_product = st.radio("특성화 상품 선택:", ["2-1. 재물운 특화 분석", "2-2. 연애/결혼운 특화 분석", "2-3. 진학운 특화 분석", "2-4. 직업운 특화 분석", "2-5. 건강운 특화 분석", "2-6. 이사 택일", "2-7. 개업 택일"], key="sub_category_2", on_change=stop_ai)
        elif main_category == "3. 커플 연애/결혼운 (궁합) 풀이":
            u_product = st.radio("상세 분석 항목:", ["3-1. 연애/결혼운 (궁합) 풀이", "3-2. 결혼 택일", "3-3. 출산 택일"], key="sub_category_3", on_change=stop_ai)
        elif main_category == "4. 타 감명서 비교":
            u_product = st.radio("타 감명서 비교:", ["4-1. 타 감명서 비교 (사주)", "4-2. 타 감명서 비교 (궁합)"], key="sub_category_4", on_change=stop_ai)
            
        st.markdown("---")
