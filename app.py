elif "7. 연애" in u_product:
        st.header(f"💕 {name}님과 {f_name}님의 초연 궁합")
        st.markdown("---")
        with st.spinner("⏳ 두 분의 시공간을 교차 분석 중입니다..."):
            try:
                gh_data = engine.get_gunghap_data(int(b_year), int(b_month), int(b_day), b_time, int(f_y), int(f_m), int(f_d), f_t)
                
                # 1. 표지 데이터 조립
                birth_str = f"{b_year}년 {b_month}월 {b_day}일"
                f_birth_str = f"{f_y}년 {f_m}월 {f_d}일"
                cover_html = html_views.get_gunghap_cover(
                    APP_VERSION, "♂️" if gender == "남성" else "♀️", name, gender, u_marital, birth_str, 
                    "♂️" if f_gender == "남성" else "♀️", f_name, f_gender, f_marital, f_birth_str, 
                    dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
                )
                
                # 2. 본문 내용 조립 (표지 제외)
                m_content = html_views.get_saju_table(*gh_data["m_table"]) + html_views.get_master_bar(*gh_data["m_master"])
                w_content = html_views.get_saju_table(*gh_data["w_table"]) + html_views.get_master_bar(*gh_data["w_master"])
                closing = html_views.get_gunghap_closing(name, f_name)
                
                # 3. AI 통변 조립
                ai_html = ""
                try:
                    prompt_content = f"신청인 {name}({birth_str})과 상대방 {f_name}({f_birth_str})의 궁합을 초연 시공명리 관점에서 분석하라."
                    ai_result = call_gemini_api(prompt_content)
                    if ai_result:
                        ai_html = html_views.get_ai_report_box(ai_result.replace('\n', '<p>'))
                except Exception as e:
                    ai_html = f"<div style='color:red;'>AI 통변 오류: {e}</div>"

                # 4. 출력: 표지는 별도 출력, 본문은 A4 박스에 통합
                st.markdown(cover_html, unsafe_allow_html=True) # 표지 독립 출력
                
                full_body_content = m_content + "<br>" + w_content + ai_html + closing
                st.markdown(html_views.get_final_report_box(full_body_content), unsafe_allow_html=True) # 본문만 박스에 담음
                
            except Exception as e:
                st.error(f"🚨 시스템 오류가 발생했습니다: {e}")
