# ---------------------------------------------------------
    # [2~6번 상품] 운세 및 특화 분석 (재물, 직업, 건강 등)
    # ---------------------------------------------------------
    elif any(x in u_product for x in ["2. 올 해", "3. 이번 달", "4. 재물", "5. 직업", "6. 건강"]):
        st.header(f"🔮 {name}님의 {u_product.split('.')[1].strip()} 분석")
        st.markdown("---")
        with st.spinner(f"⏳ [{u_product.split('.')[1].strip()}] 정밀 분석 중...."):
            st.info("데이터 연동 및 AI 분석 대기 중입니다. (향후 1번 상품의 연산 로직을 기반으로 확장될 공간입니다.)")
            if "4. 재물" in u_product:
                st.success(f"입력하신 금전 고민: {wealth_goal}")
            elif "5. 직업" in u_product:
                st.success(f"입력하신 직업 고민: {career_goal}")
            elif "6. 건강" in u_product:
                st.success(f"입력하신 건강 고민: {health_goal}")
                

    # ---------------------------------------------------------
    # [7번 상품] 연애 및 궁합운 특화 분석 (강제 렌더링 버전)
    # ---------------------------------------------------------
    elif "7. 연애" in u_product:
        st.header(f"💕 {name}님과 {f_name}님의 초연 궁합")
        st.markdown("---")
        with st.spinner("⏳ 궁합 풀이 중..."):
            
            # (1) 표지 강제 렌더링
            app_p_icon = "♂️" if gender == "남성" else "♀️"
            part_p_icon = "♂️" if f_gender == "남성" else "♀️"
            today_str = dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
            
            cover_html = html_views.get_gunghap_cover(APP_VERSION, app_p_icon, name, gender, u_marital, part_p_icon, f_name, f_gender, f_marital, today_str)
            st.markdown(cover_html, unsafe_allow_html=True)

            # ==========================================================
            # 🚨 [박사님 필수 작업 구간] 🚨
            # 기존에 만드셨던 연산 코드(남명 m_..., 여명 w_...)를 여기에 넣으십시오
            # 1번 상품의 60.0 버전 연산 로직을 남/여 각각 두 번 수행하는 코드입니다.
            # ==========================================================
            
            # (2) 남명/여명 박스 렌더링 (값이 존재할 때만 출력되도록 방어 로직 적용)
            if 'm_table_html' in locals() and m_table_html:
                st.markdown(html_views.get_gunghap_person_box(m_table_html, m_master_html), unsafe_allow_html=True)
            
            if 'w_table_html' in locals() and w_table_html:
                st.markdown(html_views.get_gunghap_person_box(w_table_html, w_master_html, add_page_break=True), unsafe_allow_html=True)
            
            # (3) 대운 비교 렌더링
            if 'm_un_html' in locals() and 'w_un_html' in locals():
                st.markdown(html_views.get_daewun_compare_box(name, m_un_html, f_name, w_un_html), unsafe_allow_html=True)

            # (4) 맺음말 렌더링 (※ 누락되었던 부분 복구 완료!)
            st.markdown(html_views.get_gunghap_closing(), unsafe_allow_html=True)


    # ---------------------------------------------------------
    # [8~10번 상품] 결혼, 출산, 이사 택일
    # ---------------------------------------------------------
    elif any(x in u_product for x in ["8. 결혼", "9. 출산", "10. 이사"]):
        st.header(f"🗓️ {name}님의 {u_product.split('.')[1].strip()}")
        st.markdown("---")
        with st.spinner("⏳ 길일 및 시공간 분석 중..."):
            st.info("명리학적 택일 분석 엔진 가동 대기 중입니다.")


    # ---------------------------------------------------------
    # [11번 상품] 타 감명서 비교 (기존 2번 로직 100% 이관)
    # ---------------------------------------------------------
    elif "11. 타 감" in u_product:
        st.header("⚖️ 초연 시공명리 타 감명서 1:1 비교")
        st.markdown("---")
        if not other_report: 
            st.warning("👈 사이드바에 타 감명서 원문을 입력해주세요.")
        else: 
            st.info("타 감명서 비교 로직이 작동합니다.")
