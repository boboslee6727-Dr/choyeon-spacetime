if "1-1." in u_product:
                # ---------------------------------------------------------
                # [1-1. 전용 데이터 및 프롬프트 준비]
                # ---------------------------------------------------------
                target_prompt = getattr(prompts, 'PERSONAL_SAJU_PROMPT', "")
                extra_facts = {
                    "daewun": all_daewun_data,
                    "curr_year": curr_year,
                    "curr_month": curr_m
                }
                
                # ---------------------------------------------------------
                # [1-1. AI 통변 실행]
                # ---------------------------------------------------------
                with st.spinner("🤖 [사주팔자 및 대운 분석] 정밀 통변 중..."):
                    # 실제 API 연동 시 아래 주석을 풀고 사용하십시오.
                    # ai_output_html = call_gemini_api(target_prompt, extra_facts)
                    ai_output_html = "<div style='padding:20px; font-family:Nanum Myeongjo;'>AI 심층 통변 내용이 이곳에 렌더링됩니다.</div>"
                
                # ---------------------------------------------------------
                # [1-1. 전용 마무리 텍스트 및 DB 준비]
                # ---------------------------------------------------------
                closing_html = html_views.get_closing_html(name)
                choyeon_db = load_choyeon_db()
                w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{d_pillar[1]}".strip() 
                w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
                i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
                struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
                s_name, s_type, s_desc = struct_data[0], struct_data[1], struct_data[2]
                golden_text_html = html_views.get_golden_text(name, w_val, i_val, s_name, s_type, s_desc)
                
                # ---------------------------------------------------------
                # [1-1. 최종 조립 및 화면 출력] (세운/월운표 없이 원국+대운만)
                # ---------------------------------------------------------
                st.markdown(cover_html, unsafe_allow_html=True)
                
                final_report = (
                    str(info_h or "") + 
                    str(table_html or "") + 
                    str(master_bar_html or "") + 
                    str(un_html or "") + 
                    str(intro_html or "") + 
                    str(golden_text_html or "") + 
                    str(ai_output_html or "") + 
                    str(closing_html or "")
                )
                
                st.markdown(html_views.get_final_report_box(final_report), unsafe_allow_html=True)
