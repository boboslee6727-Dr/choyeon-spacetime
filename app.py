def get_daeun_su_accurate(utc_dt, order):
    try:
        sun = ephem.Sun()
        # 1. 태양의 황경 계산 (정확한 에포크 사용)
        def get_sun_lon(dt):
            sun.compute(dt)
            return math.degrees(ephem.Ecliptic(sun).lon) % 360.0

        current_lon = get_sun_lon(utc_dt)
        jeol_lons = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]
        
        # 2. 절기점 찾기
        if order == 1:
            targets = [l for l in jeol_lons if l > current_lon]
            t_lon = min(targets) if targets else 315
        else:
            targets = [l for l in jeol_lons if l <= current_lon]
            t_lon = max(targets) if targets else 285

        search_dt = utc_dt
        step = dt_mod.timedelta(minutes=10) if order == 1 else dt_mod.timedelta(minutes=-10)
        
        # 3. 절기점 도달할 때까지 탐색
        for _ in range(6000):
            search_dt += step
            l = get_sun_lon(search_dt)
            if (order == 1 and l >= t_lon) or (order == -1 and l <= t_lon):
                break
            
        # 4. 대운수 산출: 3일 = 1년 (즉, 1일 = 4개월 = 120일)
        total_days = abs((search_dt - utc_dt).total_seconds()) / 86400.0
        d_su = round(total_days / 3.0) # 3일당 1년으로 반올림
        
        return max(1, min(10, d_su))
    except:
        return 1
