# ==============================================================================
    # [3번 카테고리] 타 감명서 1:1 비교 (사이드바 버튼과 통합)
    # ==============================================================================
    elif "3-1." in u_product or "3-2." in u_product:
        current_key = "text_3-1." if "3-1." in u_product else "key_3_2"
        other_report = st.session_state.get(current_key, "")
        
        # 1. 데이터 입력 확인 (화면 상단 표시)
        if not other_report: 
            st.warning("👈 사이드바에 타 감명서 원문을 입력해주세요.")
        else: 
            st.info("✅ 데이터가 확인되었습니다. 사이드바의 [🚀 초연 시공명리 풀이 가동] 버튼을 누르십시오.")
            
        # 2. 풀이 가동 버튼 클릭 시 호출될 로직
        # [중요] 이 부분은 기존 메인 풀이 버튼 로직 안에 통합되어 있어야 합니다.
        if "btn_run_main" in st.session_state and st.session_state["btn_run_main"]:
            if other_report:
                with st.spinner("초연 시공명리 AI가 타 감명서와 비교 분석 중입니다..."):
                    # 박사님의 분석 로직 호출
                    # result = run_comparison_logic(other_report, u_product)
                    st.success("✅ 비교 분석이 완료되었습니다.")
            else:
                st.error("타 감명서 원문을 먼저 입력해주세요!")
