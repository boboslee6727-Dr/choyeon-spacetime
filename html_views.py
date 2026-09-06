def get_couple_cover(version="", report_title="", u_icon="♂️", u_name="무명", u_age="", u_sol="", u_lun="", u_time="", p_icon="♀️", p_name="무명", p_age="", p_sol="", p_lun="", p_time="", today_str="", *args, **kwargs):
    raw_title = str(report_title or "초연 시공명리 궁합풀이").replace("🏮", "").replace("🎯", "")
    for tag in ["<br>", "<br/>", "<br />", "\n", "\r"]:
        raw_title = raw_title.replace(tag, " ")
    clean_title = " ".join(raw_title.split())
    clean_u_name = str(u_name or "무명").strip()
    clean_p_name = str(p_name or "무명").strip()
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:210mm; height:297mm; min-height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; box-sizing: border-box; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 42px 24px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 92%; max-width: 680px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            <!-- 상단 대제목 영역 -->
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 28px; width: 100%; box-sizing: border-box;'>
                <h1 class='title-myeongjo' style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 28px !important; font-weight: 800 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -1.2px !important; white-space: nowrap !important; word-break: keep-all !important; line-height: 1.2 !important; text-align: center;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span class='ver-myeongjo' style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 14px !important; font-weight: 700 !important; color: #555555 !important; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            <!-- 중단 남명 / 여명 정보 박스 -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 16px 18px; border-radius: 14px; margin-bottom: 14px;'>
                <h2 style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 24px !important; font-weight: 800 !important; color: #1565C0 !important; margin: 0 0 6px 0 !important;'>{u_icon} 남명 : {clean_u_name} 님 ({u_age}세)</h2>
                <div style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 16px !important; line-height: 1.6;'>
                    <p style='margin: 0; text-align: center !important; width: 100% !important; white-space: nowrap; color: #000000;'><strong style='font-weight: 800 !important;'>[양력] {u_sol} | [음력] {u_lun}</strong></p>
                    <p style='margin: 3px 0 0 0; text-align: center !important; width: 100% !important; white-space: nowrap; font-weight: 800 !important; color: #1565C0;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
            <div style='background: #FFF3E0; border: 1px solid #FBE9E7; padding: 16px 18px; border-radius: 14px; margin-bottom: 22px;'>
                <h2 style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 24px !important; font-weight: 800 !important; color: #C62828 !important; margin: 0 0 6px 0 !important;'>{p_icon} 여명 : {clean_p_name} 님 ({p_age}세)</h2>
                <div style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 16px !important; line-height: 1.6;'>
                    <p style='margin: 0; text-align: center !important; width: 100% !important; white-space: nowrap; color: #000000;'><strong style='font-weight: 800 !important;'>[양력] {p_sol} | [음력] {p_lun}</strong></p>
                    <p style='margin: 3px 0 0 0; text-align: center !important; width: 100% !important; white-space: nowrap; font-weight: 800 !important; color: #C62828;'>태어난 시간 : {p_time}</p>
                </div>
            </div>
            <!-- 하단 발행일자 및 연구소명 (크고 굵게 강조) -->
            <div style='margin-top: 32px !important; text-align: center !important;'>
                <p style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 18px !important; font-weight: 800 !important; color: #111111 !important; letter-spacing: 0.5px !important; line-height: 1.2 !important; margin: 0 0 24px 0 !important; display: block !important;'>{today_str}</p>
                <p style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 24px !important; font-weight: 800 !important; color: #1A237E !important; letter-spacing: 1px !important; line-height: 1.2 !important; margin: 0 !important; display: block !important;'>초연 시공명리 연구소</p>
            </div>
        </div>
    </div>
    <div class='page-break'></div>
    """
