# --- (E) 최종 통합 렌더링 ---
            closing_html = html_views.get_closing_html(name)
            
            st.markdown(cover_html, unsafe_allow_html=True)
            final_report = (
                str(table_html or "") + 
                str(master_bar_html or "") + 
                str(intro_html or "") + 
                str(un_html or "") +      # 대운 표
                str(specific_ui_html or "") + # 세운 표, 월운 표 등 추가 UI
                str(ai_output_html or "") +   # 원국+대운+세운 등 통합 AI 통변
                str(closing_html or "")
            )
            st.markdown(html_views.get_final_report_box(final_report), unsafe_allow_html=True)

        # [7번 상품] 연애/궁합 
        elif "7. 연애" in u_product:
            st.header(f"💕 {name}님과 {f_name}님의 초연 궁합")
            st.markdown("---")
            with st.spinner("⏳ 두 분의 시공간을 교차 분석 중입니다..."):
                try:
                    # 1. 데이터 호출
                    gh_data = engine.get_gunghap_data(int(b_year), int(b_month), int(b_day), b_time, int(f_y), int(f_m), int(f_d), f_t)
                    
                    # 2. UI 조립
                    cover_html = html_views.get_gunghap_cover(APP_VERSION, "♂️" if gender == "남성" else "♀️", name, gender, u_marital, "♂️" if f_gender == "남성" else "♀️", f_name, f_gender, f_marital, dt_mod.datetime.now().strftime("%Y년 %m월 %d일"))
                    
                    m_box = html_views.get_gunghap_person_box(html_views.get_saju_table(*gh_data["m_table"]), html_views.get_master_bar(*gh_data["m_master"]))
                    w_box = html_views.get_gunghap_person_box(html_views.get_saju_table(*gh_data["w_table"]), html_views.get_master_bar(*gh_data["w_master"]), add_page_break=True)
                    closing = html_views.get_gunghap_closing(name, f_name)
                    
                    # 3. AI 통변
                    ai_html = ""
                    try:
                        prompt_content = f"신청인 {name}과 상대방 {f_name}의 궁합을 초연 시공명리 관점에서 분석하라."
                        ai_result = call_gemini_api(prompt_content)
                        if ai_result:
                            ai_html = html_views.get_ai_report_box(ai_result.replace('\n', '<p>'))
                    except Exception as e:
                        ai_html = f"<div style='color:red;'>AI 통변 오류: {e}</div>"
                    
                    # 4. 결합 및 렌더링
                    full_report_html = str(cover_html or "").strip() + str(m_box or "").strip() + str(w_box or "").strip() + str(ai_html or "").strip() + str(closing or "").strip()
                    st.markdown(html_views.get_final_report_box(full_report_html), unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"🚨 시스템 오류가 발생했습니다: {e}")

        # [8~12번 상품] 
        elif any(x in u_product for x in ["8. 결혼", "9. 출산", "10. 이사"]):
            st.header(f"🗓️ {name}님의 {u_product.split('.')[1].strip()}")
            st.markdown("---")
            st.info("명리학적 택일 분석 엔진 가동 대기 중입니다.")
