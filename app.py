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
        # [끝] 
        except Exception as e:
            st.error(f"🚨 시스템 오류가 발생했습니다: {e}")
