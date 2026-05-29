# ==================================================================
            # 🚀 [2단계] 타 감명서 비교분석 (선택적)
            # ==================================================================
            if u_product == "타 감명서":
                try:
                    st.info("▶ [타 감명서] 원본 출력 및 상세 비교 분석 중...") 
                    comp_text = other_reading_text

                    report_2_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#555;'><h2 style='text-align:center; color:#555; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; margin-bottom:20px;'>📜 타 감명서 원문</h2><div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #111;'>{comp_text.replace(chr(10), '<br>')}</div></div></div>"
                    st.markdown(report_2_html, unsafe_allow_html=True)
                        
                    # 🚨 수정 내용: 고정 목차 13개를 삭제하고, AI가 타 감명서 흐름에 맞춰 유연하게 제목을 생성하도록 지시
                    comp_prompt = f"""
    당신은 명리심리상담사 '초연 박사'를 보조하는 수석 분석관입니다.
    아래 [사주 팩트]를 절대 기준으로 삼고, [1. 초연 사주풀이]와 [2. 타 감명서]의 내용을 인사말이나 서론 없이, 곧바로 대조 포맷 규칙에 의거하여 분석하십시오.

    🚨 [절대 사주 팩트 - 환각 방지용 족쇄]
    - 내담자 명조 팩트: {saju_info_str}
    - 본 명조와 무관한 다른 일간이나 존재하지 않는 신살, 합형충파해를 언급할 경우 치명적인 시스템 오류로 간주합니다.

    🚨 [출력 및 서식 절대 규칙]
    1. "네, 분석을 시작합니다" 등의 서론 멘트를 철저히 금지합니다. 첫 글자는 무조건 제목 태그로 시작해야 합니다.
    2. 차이점 기술 시 반드시 <b>&lt;초연&gt;</b> 및 <b>&lt;타 감명&gt;</b> 마커를 문단 앞에 기입하고 공통점도 빠짐없이 발굴하십시오.
    3. 통변 근거 제시 시 반드시 명리적 근거(십성, 합형충파해, 신살 등)를 기반으로 논증하십시오.
    4. (유연한 목차 구성) 억지로 정해진 개수의 목차를 채울 필요가 없습니다. 타 감명서의 목차와 논리 흐름을 면밀히 분석하여, 해당 감명서가 다루고 있는 핵심 주제들에 맞추어 AI가 유연하게 비교 항목(목차)을 도출하십시오.

    [목차 HTML 서식 정의]
    각 비교 항목의 제목을 출력할 때는 반드시 아래의 HTML 태그 구조를 그대로 복사하여 사용하되, 숫자와 항목 이름만 상황에 맞게 변경하십시오.
    <h3 style='color:#1A237E; font-size: 22px; font-weight: 900; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 25px; margin-bottom: 8px; display:block;'>1. [도출된 비교 항목 이름]</h3>
    
    가장 마지막 결론인 총평을 작성할 때만 아래의 붉은색 태그를 사용하십시오.
    <h3 style='color:#D50000; font-size: 22px; font-weight: 900; border-bottom: 2px solid #D50000; padding-bottom: 5px; margin-top: 35px; margin-bottom: 8px; display:block;'>[마지막 번호]. 총평 및 향후 개선점</h3>

    =========================================
    [1. 초연 사주풀이 원문]
    {report_1_text_data}  

    [2. 타 감명서 원문]
    {comp_text}
    =========================================
    """
                    c_res = call_claude_api(comp_prompt, max_tokens=10000)
                    report_3_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#D50000;'><h1 style='text-align:center; color:#D50000; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; margin-bottom:25px;'>⚖️ 1:1 상세비교 리포트</h1><div style='margin-top:20px;'>{c_res}</div></div></div>"
                    st.markdown(report_3_html, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"2단계 비교 분석 장애: {e}")
