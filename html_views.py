if "3-1." in u_product or u_product == "타 감명서":
                try:
                    # ------------------------------------------------------------------
                    # [1단계 PAGE] 오리지널 사주풀이
                    # ------------------------------------------------------------------
                    first_stage_html = str(final_report_base or "") + str(ai_output_html or "")
                    st.markdown(html_views.get_final_report_box(first_stage_html), unsafe_allow_html=True)
                    
                    # ------------------------------------------------------------------
                    # [2단계 PAGE] 타 감명서 전용 표지 + 원본 텍스트
                    # ------------------------------------------------------------------
                    other_text_input = st.session_state.get(f"text_{u_product}", "")
                    
                    if other_text_input and len(str(other_text_input).strip()) > 0:
                        u_name_str = name
                        p_icon_str = p_icon
                        
                        sol_val = sol_str_fmt
                        lun_val = lun_str_fmt
                        time_val = b_time
                        today_val = today_str
                        
                        # 1. 표지 출력
                        other_cover_html = html_views.get_comparison_saju_cover(
                            APP_VERSION, p_icon_str, u_name_str, sol_val, lun_val, time_val, today_val
                        )
                        st.markdown(other_cover_html, unsafe_allow_html=True)
                        
                        # 2. 타 감명서 원문 단독 출력
                        report_2_html = html_views.get_other_report_original_html(other_text_input)
                        st.markdown(report_2_html, unsafe_allow_html=True)
                        
                        # ------------------------------------------------------------------
                        # [3단계 PAGE] 1:1 상세비교 AI 리포트 출력
                        # ------------------------------------------------------------------
                        with st.spinner("⚖️ 1:1 상세 비교 리포트 분석 중..."):
                            u_name_val = name
                            u_gender_val = gender
                            u_age_val = age
                            u_marital_val = u_marital if 'u_marital' in locals() else (marital if 'marital' in locals() else "미혼")
                            
                            b_y = sol_y
                            b_m = sol_m
                            b_d = sol_d
                            b_t = b_time
                            
                            g_list = gans
                            j_list = jjis
                            pillar_str = f"{g_list[3]}{j_list[3]}년 {g_list[2]}{j_list[2]}월 {g_list[1]}{j_list[1]}일 {g_list[0]}{j_list[0]}시" if len(g_list) >= 4 else ""
                            calc_daewun = calc_d

                            saju_fact_summary = f"👤 신청인: <b>{u_name_val}</b> 님 ({u_gender_val}, {u_age_val}세, {u_marital_val}) &nbsp;|&nbsp; <b>{b_y}년 {b_m}월 {b_d}일 {b_t}</b><br>📜 사주명식: <b>{pillar_str}</b> (대운수: {calc_daewun})"
                            
                            # COMPARE_PERSONAL_PROMPT 포맷팅
                            comp_prompt = prompts.COMPARE_PERSONAL_PROMPT.format(
                                name=name,
                                age=age,
                                gender=gender,
                                marital=u_marital_val,
                                full_content_clean=str(locals().get('ai_output_html', '')).strip(),
                                other_report=str(other_text_input).strip(),
                                fact_reference=saju_fact_summary
                            )
                            
                            c_res = call_gemini_api(comp_prompt)
                            
                            if c_res:
                                # 1. AI 응답 기본 텍스트 정화
                                c_res_clean = re.sub(r'<!--.*?-->', '', c_res, flags=re.DOTALL)
                                c_res_clean = re.sub(r'```[a-zA-Z]*', '', c_res_clean).replace("```", "").strip()
                                c_res_clean = re.sub(r'^(안녕하세요|반갑습니다|저는|AI).*?\n', '', c_res_clean, flags=re.MULTILINE)
                                c_res_clean = c_res_clean.replace("&lt;", "<").replace("&gt;", ">")
                                
                                # 2. html_views 전용 뷰 함수를 거쳐 계층별 HTML 변환
                                formatted_comp = html_views.format_ai_text_to_html(c_res_clean)
                                
                                # 3. [핵심] 대제목 + 둥근 사각 테두리 박스로 완벽 출력
                                c_res_html = html_views.get_comparison_result_box_html(formatted_comp, saju_fact_summary)
                                st.markdown(c_res_html, unsafe_allow_html=True)
                            else:
                                st.error("⚠️ 타 감명서 비교 분석 AI 응답을 불러오지 못했습니다.")
                    else:
                        st.warning("⚠️ 타 감명서 원문이 입력되지 않았습니다. 텍스트 상자에 원문을 붙여넣어 주십시오.")
                
                except Exception as e:
                    st.error(f"🚨 [3-1. 타 감명서 비교] 처리 중 오류 발생: {e}")
            else:
                final_report = str(final_report_base or "") + str(ai_output_html or "") + str(closing_part or "")
                st.markdown(html_views.get_final_report_box(final_report), unsafe_allow_html=True)
