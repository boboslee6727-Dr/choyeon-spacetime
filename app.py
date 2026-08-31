if 'final_render_html' not in locals() or final_render_html is None:
            final_render_html = ""

        # 표지 HTML 로드
        safe_cover_str = cover_html if 'cover_html' in locals() and cover_html else ""

        # 본문 영역이 report-page/vip-inset-frame으로 감싸져 있지 않은 경우 규격 프레임 자동 적용
        if "report-page" not in final_render_html:
            content_body = f"""
            <div class='report-page' style='margin-top: 20px;'>
                <div class='vip-inset-frame'>
                    {final_render_html}
                </div>
            </div>
            """
        else:
            content_body = final_render_html

        # 표지와 본문 다이렉트 결합 (상단 CSS와 충돌하지 않도록 깔끔하게 조립)
        combined_report_html = f"{safe_cover_str}\n{content_body}"

        # 1. 백틱 잔여물 및 대제목 불필요 괄호 제거
        clean_report_html = combined_report_html.replace('```html', '').replace('```markdown', '').replace('```', '')
        clean_report_html = re.sub(r'<h1([^>]*)>\s*\[\s*(.*?)\s*\]\s*</h1>', r'<h1\1>\2</h1>', clean_report_html)
        clean_report_html = re.sub(r'<h2([^>]*)>\s*\[\s*(.*?)\s*\]\s*</h2>', r'<h2\1>\2</h2>', clean_report_html)

        # ----------------------------------------------------------------------
        # 🤖 [스텔스 생산 파이프라인 연계 및 정식 렌더링]
        # ----------------------------------------------------------------------
        if is_admin_mode:
            gid = st.session_state.get('admin_proc_id', '')
            st.session_state[f'html_{gid}'] = clean_report_html
            if 'admin_orders' in st.session_state and gid in st.session_state['admin_orders']:
                st.session_state['admin_orders'][gid]['html'] = clean_report_html
                st.session_state['admin_orders'][gid]['is_generated'] = True
                st.session_state['admin_orders'][gid]['status'] = '제작완료'
            st.session_state['app_running'] = False
            st.session_state['admin_proc_id'] = None
            st.rerun()
        else:
            st.markdown(clean_report_html, unsafe_allow_html=True)
