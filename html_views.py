def generate_weekly_calendar_html(weekly_days_data, today_day, yb=None, db=None):
    """1-4 일운 및 택일 분석 전용 주간 달력 HTML (방어 코드 및 정밀 렌더링 완결판)"""
    import engine
    content = ""

    for item in weekly_days_data:
        wday = item.get('weekday', '-')
        day_num = item.get('day', 0)
        ganji_str = item.get('ganji') or item.get('ganji_str', '--')
        is_today = item.get('is_today', False) or item.get('is_target_day', False)
        
        gan_char = ganji_str[0] if len(ganji_str) >= 1 and ganji_str != "-" else "-"
        ji_char = ganji_str[1] if len(ganji_str) >= 2 else "-"
        
        gan_cls = engine.get_oh_class(gan_char)
        ji_cls = engine.get_oh_class(ji_char)
        
        # 십성 및 12운성/신살 매핑 (데이터셋 기반 + 엔진 실시간 보정)
        ss_val = item.get('ss_ji', '-')
        unsung_val = item.get('un_sung', '-')
        y_shinsal_val, d_shinsal_val = "-", "-"
        
        try:
            if hasattr(engine, 'get_12_shinsal'):
                if yb and ji_char != "-": 
                    y_shinsal_val = engine.get_12_shinsal(yb, ji_char)
                if db and ji_char != "-": 
                    d_shinsal_val = engine.get_12_shinsal(db, ji_char)
        except Exception:
            pass
            
        y_val = f"<span style='color:#C62828;'>{y_shinsal_val}</span>" if y_shinsal_val != "-" else "-"
        clean_d_w = str(d_shinsal_val).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
        d_val = f"<span style='color:#C62828;'>({clean_d_w})</span>" if clean_d_w and clean_d_w != "-" else "<span style='color:#C62828;'>(-)</span>"
        u_val = f"<span style='color:#0D47A1;'>{unsung_val}</span>" if unsung_val != "-" else "-"
            
        # 요일별 및 오늘 날짜 스타일 분기
        if is_today:
            active_style = "border: 3px solid #2E7D32 !important;"
            header_bg = "#2E7D32"
            bg_col = "#E8F5E9"
        elif wday == '일':
            active_style = "border-left: 1px solid #ccc; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
            header_bg = "#C62828"
            bg_col = "#FAFAFA"
        elif wday == '토':
            active_style = "border-left: 1px solid #ccc; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
            header_bg = "#1565C0"
            bg_col = "#FAFAFA"
        else:
            active_style = "border-left: 1px solid #ccc; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
            header_bg = "#555555"
            bg_col = "#FAFAFA"
        
        content += f"""
        <div style='flex:1; width:14.28%; {active_style} text-align:center; padding-bottom:4px; background-color:{bg_col}; display:flex; flex-direction:column; box-sizing:border-box; min-width:0; overflow:hidden;'>
            <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:800; font-size:14px; height:26px; display:flex; align-items:center; justify-content:center; white-space:nowrap;'>
                {day_num}일 ({wday})
            </div>
            <div style='font-size:12px; font-weight:800; color:#000000; height:22px; display:flex; align-items:center; justify-content:center;'>{ss_val}</div>
            <div class='{gan_cls}' style='font-size:17px; font-weight:900; height:26px; display:flex; align-items:center; justify-content:center;'>{gan_char}</div>
            <div class='{ji_cls}' style='font-size:17px; font-weight:900; height:26px; display:flex; align-items:center; justify-content:center;'>{ji_char}</div>
            <div class='color-unsung' style='font-size:12px; font-weight:800; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center;'>{u_val}</div>
            <div class='color-shinsal' style='font-size:12px; font-weight:800; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center;'>{y_val}</div>
            <div class='color-shinsal-day' style='font-size:12px; font-weight:800; border-top:1px dashed #ccc; height:22px; display:flex; align-items:center; justify-content:center;'>{d_val}</div>
        </div>
        """

    return f"""
    <div style='margin-top:14px; margin-bottom:8px; font-size:15px; font-weight:800; color:#3E2723; font-family:"Nanum Myeongjo", serif;'>📅 이번 주 운세 흐름 (일요일 ~ 토요일)</div>
    <div style='display:flex; flex-direction:row; width:100%; border:3px solid #3E2723; background:white; margin-bottom:10px; table-layout:fixed; font-family:"Nanum Myeongjo", serif;'>
        {content}
    </div>
    """
