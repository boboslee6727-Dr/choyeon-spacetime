with st.spinner("초연 만세력 엔진 가동 및 통변 중..."):
            # 1. 박사님 엔진 호출
            h, m = extract_time(b_time)
            y_pillar, m_pillar, lon = engine.get_true_year_month_pillar(b_year, b_month, b_day, h, m)
            
            # [수정] 인자 이름을 생략하고 순서대로 전달 (가장 에러가 적은 방식)
            is_lunar_val = ("음력" in u_cal)
            is_leap_val = ("윤달" in u_cal)
            
            # y, m, d, is_lunar, is_leap 순서대로 5개를 전달합니다.
            _, _, d_pillar = engine.get_ganji_from_date(b_year, b_month, b_day, is_lunar_val, is_leap_val)
            
            t_gan, t_ji = engine.get_time_ganji(d_pillar[0], b_time)
