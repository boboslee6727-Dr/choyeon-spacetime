# 🎯 [1] 궁합 모드 (if 블록 내부) -> 2인용 표지(get_couple_cover, 15개) 호출
            u_icon = "♂️" if "남" in str(gender) else "♀️"
            p_icon = "♀️" if "여" in str(p_gender) else "♂️"

            cover_html = html_views.get_couple_cover(
                APP_VERSION, 
                report_title, 
                u_icon, 
                name, 
                u_age, 
                sol_str, 
                lun_str, 
                time_str,
                p_icon, 
                p_name, 
                p_age, 
                p_sol_str, 
                p_lun_str, 
                p_time_str, 
                today_str
            )
            
            male_data_pack = [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"] if "남" in str(gender) else partner_bazi
            female_data_pack = partner_bazi if "남" in str(gender) else [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"]
            
            try:
                if hasattr(engine, 'UniversalPrintableGunghap'):
                    gh_engine = engine.UniversalPrintableGunghap(m_name_val, f_name_val, male_data_pack, female_data_pack, 10)
                    gh_engine.run_universal_logic()
                    gh_score = gh_engine.final_score
                    gh_grade = gh_engine.grade
                else:
                    gh_score = 0
                    gh_grade = ""
            except Exception:
                gh_score, gh_grade = 0, "점수 산출 불가"
                
        else:
            # 🎯 [2] 1인용 개인 모드 (else 블록 내부) -> 1인용 표지(get_personal_cover, 8개) 호출
            gh_score = 0
            gh_grade = ""
            partner_bazi = ["?", "?", "?", "?"]
            u_icon = "♂️" if "남" in str(gender) else "♀️"

            cover_html = html_views.get_personal_cover(
                APP_VERSION, 
                report_title, 
                u_icon, 
                name, 
                sol_str, 
                lun_str, 
                time_str, 
                today_str
            )

        info_h = html_views.get_info_header(u_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, time_str_fmt)
        table_html = html_views.generate_saju_table_data(gans, jjis, ds, gender, engine)
        master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, samjae_color, cur_samjae)

        intro_html = html_views.get_intro_html()
