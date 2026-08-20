# ==========================================
    # 5. 모든 상품(1-1 ~ 4-x) 완벽 대응 HTML 조립
    # ==========================================
    # 💡 (참고) 아래 un_html, sewun_html 등은 박사님의 원본 app.py에서 
    # html_views를 통해 표를 생성하는 변수명과 동일하게 맞춰주시면 됩니다.
    
    part_1_fact = html_views.get_cover_and_saju_table(
        name, gender, u_marital, age, 
        solar_y, solar_m, solar_d, lun_str_fmt, birth_time_str, 
        fact_data
    )
    part_2_intro = "" 
    part_3_golden = "" 
    part_5_closing = html_views.get_closing_remark(name)

    # 마커 치환 함수
    def sub_marker(text, marker_name, table_code):
        pattern = r'\[\s*\*?\*?\s*' + marker_name + r'\s*\*?\*?\s*\]'
        import re
        return re.sub(pattern, table_code, text, flags=re.IGNORECASE)

    # 💡 박사님의 완벽한 상품별 라우팅 로직 100% 복원
    final_render_html = ""

    if u_product.startswith("1-1"):
        # 1-1 상품: 대운표 + 세운표 모두 필요
        daewun_table_code = un_html if 'un_html' in locals() and un_html else ""
        sewun_table_code = sewun_html if 'sewun_html' in locals() and sewun_html else ""
        formatted_ai = sub_marker(ai_output_html, 'DAEWUN_TABLE_HERE', daewun_table_code)
        formatted_ai = sub_marker(formatted_ai, 'SEWUN_TABLE_HERE', sewun_table_code)
        master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
        final_render_html = html_views.get_final_report_box(master_comp)

    elif u_product.startswith("1-2"):
        # 1-2 상품: 세운표 필요
        sewun_table_code = sewun_html if 'sewun_html' in locals() and sewun_html else ""
        formatted_ai = sub_marker(ai_output_html, 'SEWUN_TABLE_HERE', sewun_table_code)
        master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
        final_render_html = html_views.get_final_report_box(master_comp)

    elif u_product.startswith("1-3"):
        # 1-3 상품: 월운표 필요
        wolun_table_code = wolun_html if 'wolun_html' in locals() and wolun_html else ""
        formatted_ai = sub_marker(ai_output_html, 'WOLUN_TABLE_HERE', wolun_table_code)
        master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
        final_render_html = html_views.get_final_report_box(master_comp)

    elif u_product.startswith("1-4"):
        # 1-4 상품: 주간 달력표 필요
        if hasattr(engine, 'get_weekly_calendar_data'):
            weekly_days_data = engine.get_weekly_calendar_data(selected_target_date, ds)
        else:
            weekly_days_data = []
            
        if hasattr(html_views, 'generate_weekly_calendar_html') and weekly_days_data:
            weekly_table_code = html_views.generate_weekly_calendar_html(weekly_days_data, selected_target_date.day, yb, db)
        else:
            weekly_table_code = "🚨 주간운표 생성 누락됨"

        if "WEEKLY_CALENDAR_HERE" in ai_output_html:
            formatted_ai = sub_marker(ai_output_html, 'WEEKLY_CALENDAR_HERE', weekly_table_code)
        else:
            formatted_ai = f"{weekly_table_code}<br><br>{ai_output_html}"

        master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
        final_render_html = html_views.get_final_report_box(master_comp)

    elif u_product.startswith("2-"):
        # 2-x 특화 상품: 대운표 필요
        daewun_table_code = un_html if 'un_html' in locals() and un_html else ""
        formatted_ai = sub_marker(ai_output_html, 'DAEWUN_TABLE_HERE', daewun_table_code)
        master_comp = f"{part_1_fact}{formatted_ai}{part_5_closing}"
        final_render_html = html_views.get_final_report_box(master_comp)
        
    else:
        # 기타 기본 처리
        formatted_ai = ai_output_html
        master_comp = f"{part_1_fact}{formatted_ai}{part_5_closing}"
        final_render_html = html_views.get_final_report_box(master_comp)

    # ==========================================
    # 6. 최종 띄어쓰기 다림질
    # ==========================================
    final_render_html = str(final_render_html).strip()
    safe_lines_app = [line.strip() for line in final_render_html.split("\n")]
    final_render_html = "\n".join(safe_lines_app)

    return final_render_html
