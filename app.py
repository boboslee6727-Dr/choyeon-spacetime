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
                        u_name_str = locals().get('name', '신청인')
                        p_icon_str = locals().get('p_icon', '♂️')
                        
                        sol_val = locals().get('sol_str', f"{b_year}년 {b_month}월 {b_day}일")
                        lun_val = locals().get('lun_str', '')
                        time_val = locals().get('b_time', '')
                        today_val = dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
                        
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
                            u_name_val = locals().get('name', '신청인')
                            u_gender_val = locals().get('gender', '남성')
                            b_y = locals().get('b_year', '')
                            b_m = locals().get('b_month', '')
                            b_d = locals().get('b_day', '')
                            b_t = locals().get('b_time', '')
                            
                            g_list = locals().get('gans', ['', '', '', ''])
                            j_list = locals().get('jjis', ['', '', '', ''])
                            pillar_str = f"{g_list[3]}{j_list[3]}년 {g_list[2]}{j_list[2]}월 {g_list[1]}{j_list[1]}일 {g_list[0]}{j_list[0]}시" if len(g_list) >= 4 else ""
                            calc_daewun = locals().get('calc_d', '')

                            saju_fact_summary = f"👤 신청인: <b>{u_name_val}</b> 님 ({u_gender_val}) &nbsp;|&nbsp; <b>{b_y}년 {b_m}월 {b_d}일 {b_t}</b><br>📜 사주명식: <b>{pillar_str}</b> (대운수: {calc_daewun})"
                            
                            comp_prompt = prompts.COMPARE_PROMPT.format(
                                full_content_clean=str(locals().get('ai_output_html', '')).strip(),
                                other_report=str(other_text_input).strip(),
                                fact_reference=saju_fact_summary
                            )
                            
                            c_res = call_gemini_api(comp_prompt)
                            
                            if c_res:
                                # 🚨 [태그 노출 방지 핵심]: AI가 뱉어낸 HTML 태그 및 주석 완벽 정화
                                c_res_clean = re.sub(r'<!--.*?-->', '', c_res, flags=re.DOTALL)
                                c_res_clean = re.sub(r'```[a-zA-Z]*', '', c_res_clean).replace("```", "").strip()
                                c_res_clean = re.sub(r'^(안녕하세요|반갑습니다|저는|AI).*?\n', '', c_res_clean, flags=re.MULTILINE)
                                
                                # HTML 치환 문자가 원문 텍스트 형태로 드러나는 것 전면 방지
                                c_res_clean = c_res_clean.replace("&lt;", "<").replace("&gt;", ">")
                                
                                formatted_comp = c_res_clean.replace("\n", "<br>")
                                formatted_comp = re.sub(r'###\s*(.*?)(<br>|$)', r"<h3 style='color:#2E7D32; font-size:20px; font-weight:800; border-bottom:1px solid #2E7D32; padding-bottom:5px; margin-top:25px; margin-bottom:10px;'>\1</h3>", formatted_comp)
                                formatted_comp = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted_comp)
                                
                                c_res_html = html_views.get_comparison_result_box_html(formatted_comp, saju_fact_summary)
                                
                                # st.components.v1 대신 표준 st.markdown으로 안전 출력
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
