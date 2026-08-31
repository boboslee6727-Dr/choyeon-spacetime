def get_couple_cover(version, report_title, u_icon, u_name, u_age, u_sol, u_lun, u_time, p_icon, p_name, p_age, p_sol, p_lun, p_time, today_str):
    """2인용(궁합/감명서 비교) 감명서 표준 표지 (타이틀 1줄 강제 방어막 적용)"""
    raw_title = str(report_title or "초연 전통 명리 궁합풀이").replace("🏮", "").replace("🎯", "")
    for tag in ["<br>", "<br/>", "<br />", "\n", "\r"]:
        raw_title = raw_title.replace(tag, " ")
    clean_title = " ".join(raw_title.split())
    
    clean_u_name = str(u_name or "무명").strip()
    clean_p_name = str(p_name or "무명").strip()

    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:210mm; height:297mm; min-height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; box-sizing: border-box; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 42px 24px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 92%; max-width: 680px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            
            <!-- 🌟 대제목 영역: 1인용과 동일하게 25px, 자간 압축, 1줄 강제 방어막 전개 -->
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 28px; width: 100%; box-sizing: border-box;'>
                <h1 style='font-family: "Nanum Myeongjo", serif !important; font-size: 25px !important; font-weight: 900 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -1.2px !important; white-space: nowrap !important; word-break: keep-all !important; line-height: 1.2 !important; text-align: center;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family: "Nanum Myeongjo", serif; font-size: 14px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            
            <!-- ♂️ 남성(신랑/기준) 정보 박스 -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 18px 20px; border-radius: 14px; margin-bottom: 15px;'>
                <h2 style='font-family: "Nanum Myeongjo", serif; font-size: 20px; font-weight: 800; color: #1565C0; margin: 0 0 8px 0;'>{u_icon} {clean_u_name} 님 ({u_age}세)</h2>
                <div style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.6;'>
                    <p style='margin: 0; white-space: nowrap; color: #000000;'><strong style='font-weight: 900 !important;'>[양력] {u_sol} | [음력] {u_lun}</strong></p>
                    <p style='margin: 4px 0 0 0; white-space: nowrap; font-weight: 800; color: #1565C0;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
            
            <!-- ♀️ 여성(신부/상대) 정보 박스 -->
            <div style='background: #FFF3E0; border: 1px solid #FBE9E7; padding: 18px 20px; border-radius: 14px; margin-bottom: 24px;'>
                <h2 style='font-family: "Nanum Myeongjo", serif; font-size: 20px; font-weight: 800; color: #C62828; margin: 0 0 8px 0;'>{p_icon} {clean_p_name} 님 ({p_age}세)</h2>
                <div style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.6;'>
                    <p style='margin: 0; white-space: nowrap; color: #000000;'><strong style='font-weight: 900 !important;'>[양력] {p_sol} | [음력] {p_lun}</strong></p>
                    <p style='margin: 4px 0 0 0; white-space: nowrap; font-weight: 800; color: #C62828;'>태어난 시간 : {p_time}</p>
                </div>
            </div>
            
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 17px; margin-top: 25px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 24px; font-weight: 900; color: #1A237E; margin-top: 8px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class='page-break'></div>
    """
