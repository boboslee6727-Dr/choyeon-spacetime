adv_saju_data = {'year_ji': yb, 'month_ji': mb, 'day_ji': db, 'hour_ji': hb}
        if hasattr(engine, 'analyze_saju_facts_advanced'):
            sewun_ji_param = curr_y_ji if 'curr_y_ji' in locals() else "-"
            _, _, adv_flags = engine.analyze_saju_facts_advanced(adv_saju_data, dw_j_cur, sewun_ji_param)
            adv_warning_str = adv_flags.get("warning_message", "정상 시공간 흐름")
            health_erosion_str = adv_flags.get("health_erosion_facts", "특이 침식 파동 없음")
            action_solutions_str = adv_flags.get("action_solutions", "자연스러운 기운의 순환을 유지하며 긍정적 마음가짐 유지")
            spouse_issue_str = adv_flags.get("spouse_issue_facts", "배우자궁 비교적 안정적 흐름 유지")
        else:
            adv_warning_str = "정상 시공간 흐름"
            health_erosion_str = "특이 침식 파동 없음"
            action_solutions_str = "자연스러운 기운의 순환을 유지하며 긍정적 마음가짐 유지"
            spouse_issue_str = "배우자궁 비교적 안정적 흐름 유지"

        health_cognitive_str = "특이 인지 파동 없음"
        health_tumor_str = "특이 종괴 파동 없음"
        health_siksang_str = "특이 식상 소진 파동 없음"
