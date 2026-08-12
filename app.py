# --- 1-1. 사주팔자와 운세풀이 ---
        if u_product.startswith("1-1"):
            daewun_table_code = un_html if 'un_html' in locals() and un_html else ""
            sewun_table_code = sewun_html if 'sewun_html' in locals() and sewun_html else ""

            formatted_ai = ai_output_html.replace('[DAEWUN_TABLE_HERE]', daewun_table_code)
            formatted_ai = formatted_ai.replace('[SEWUN_TABLE_HERE]', sewun_table_code)

            master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
            final_render_html = html_views.get_final_report_box(master_comp)

        # --- 1-2. 올 해 (특정 연도) 운세 상세분석 ---
        elif u_product.startswith("1-2"):
            sewun_table_code = sewun_html if 'sewun_html' in locals() and sewun_html else ""
            formatted_ai = ai_output_html.replace('[SEWUN_TABLE_HERE]', sewun_table_code)

            top_fact_stack = f"{part_1_fact}{un_html}"
            master_comp = f"{top_fact_stack}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
            final_render_html = html_views.get_final_report_box(master_comp)

        # --- 1-3. 이번 달 (특정 월) 운세 상세분석 ---
        elif u_product.startswith("1-3"):
            wolun_table_code = wolun_html if 'wolun_html' in locals() and wolun_html else ""
            formatted_ai = ai_output_html.replace('[WOLUN_TABLE_HERE]', wolun_table_code)

            top_fact_stack = f"{part_1_fact}{un_html}{sewun_html}"
            master_comp = f"{top_fact_stack}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
            final_render_html = html_views.get_final_report_box(master_comp)

        # --- 1-4. 이번 (특정) 주간 및 일 운세 상세분석 ---
        elif u_product.startswith("1-4"):
            weekly_days_data = engine.get_weekly_calendar_data(selected_target_date, ds_hanja) if hasattr(engine, 'get_weekly_calendar_data') else []
            weekly_table_code = html_views.generate_weekly_calendar_html(weekly_days_data, selected_target_date.day, yb, db)
            
            formatted_ai = ai_output_html.replace('[WEEKLY_CALENDAR_HERE]', weekly_table_code)

            top_fact_stack = f"{part_1_fact}{un_html}{sewun_html}{wolun_html}"
            master_comp = f"{top_fact_stack}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
            final_render_html = html_views.get_final_report_box(master_comp)
