def get_couple_cover(version, report_title, u_icon, u_name, u_age, u_sol, u_lun, u_time, p_icon, p_name, p_age, p_sol, p_lun, p_time, today_str):
    """2인용 궁합 감명서 표준 표지 (1:1 결함 완벽 방어 완결본)"""
    clean_title = str(report_title or "초연 전통 명리궁합 풀이").replace("🏮 ", "").replace("🎯 ", "").strip()
    
    # 🌟 [해결 1] 정규식으로 '남명 :', '여명 :', '신청인 :' 중복 완벽 박멸
    def extract_pure_name(raw_name):
        n = str(raw_name or "").strip()
        n = re.sub(r'^(?:남명\s*[:：]?|여명\s*[:：]?|신청인\s*[:：]?|상대방\s*[:：]?|\s+)+', '', n).strip()
        return n if n else "무명"

    clean_u_name = extract_pure_name(u_name)
    clean_p_name = extract_pure_name(p_name)
    
    # 🌟 [해결 2] app.py에서 p_lun이 빈값('')으로 넘어와도 p_sol로부터 음력 즉시 자동 산출
    def ensure_lunar_str(sol_str, lun_str):
        if lun_str and str(lun_str).strip() and str(lun_str).strip() != "-":
            return str(lun_str).strip()
        nums = re.findall(r'\d+', str(sol_str))
        if len(nums) >= 3:
            y, m, d = int(nums[0]), int(nums[1]), int(nums[2])
            klc = KoreanLunarCalendar()
            if klc.setSolarDate(y, m, d):
                leap_str = "윤달" if getattr(klc, 'isIntercalary', False) else "평달"
                return f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({leap_str})"
        return "음력 정보 없음"

    final_u_lun = ensure_lunar_str(u_sol, u_lun)
    final_p_lun = ensure_lunar_str(p_sol, p_lun)

    # 🌟 [해결 3] 대제목을 26px Bold 900 / letter-spacing: -1.2px 로 1줄 강제 안착
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:210mm; height:297mm; min-height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; box-sizing: border-box; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 40px 25px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 88%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            
            <!-- [대제목 H1] 26px Bold 900 / 1줄 완벽 고정 -->
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 26px;'>
                <h1 style='font-family: "Nanum Gothic", sans-serif !important; font-size: 26px !important; font-weight: 900 !important; margin: 0 !important; color: #111111; letter-spacing: -1.2px !important; white-space: nowrap !important; line-height: 1.2 !important;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family: "Nanum Gothic", sans-serif; font-size: 13px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            
            <!-- [남명 정보 박스] -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 18px 20px; border-radius: 14px; margin-bottom: 14px;'>
                <h2 style='font-family: "Nanum Gothic", sans-serif; font-size: 22px; font-weight: 800; color: #1A237E; margin: 0 0 10px 0;'>{u_icon} 남명 : {clean_u_name} 님 <span style='font-size: 15px; color: #555555; font-weight: 600;'>( {u_age}세 )</span></h2>
                <div style='font-family: "Nanum Gothic", sans-serif; font-size: 15px; font-weight: 700; color: #111111; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {u_sol} | [음력] {final_u_lun}</p>
                    <p style='margin: 3px 0 0 0; color: #D50000; font-weight: 800; white-space: nowrap;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
            
            <!-- [여명 정보 박스] -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 18px 20px; border-radius: 14px;'>
                <h2 style='font-family: "Nanum Gothic", sans-serif; font-size: 22px; font-weight: 800; color: #D50000; margin: 0 0 10px 0;'>{p_icon} 여명 : {clean_p_name} 님 <span style='font-size: 15px; color: #555555; font-weight: 600;'>( {p_age}세 )</span></h2>
                <div style='font-family: "Nanum Gothic", sans-serif; font-size: 15px; font-weight: 700; color: #111111; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {p_sol} | [음력] {final_p_lun}</p>
                    <p style='margin: 3px 0 0 0; color: #D50000; font-weight: 800; white-space: nowrap;'>태어난 시간 : {p_time}</p>
                </div>
            </div>
            
            <!-- [발행일자 및 연구소명] -->
            <p style='font-family: "Nanum Gothic", sans-serif; font-size: 18px; margin-top: 30px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>
            <p style='font-family: "Nanum Gothic", sans-serif; font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 10px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class='page-break'></div>
    """
