def get_personal_cover(version, report_title, u_icon, name, sol, lun, time, today):
    """50.5 버전 디자인 규격에 맞춘 1인용 표지 렌더링"""
    return f"""
    <div class='report-page cover-page' style='padding:40px; margin:0 auto; width:100%; max-width: 800px; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact; background: #FFFFFF;'>
        <div style='border: 4px solid #1A237E; padding: 60px 40px; border-radius: 20px; text-align: center; background: white; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.05);'>
            <div style='border-bottom:4px double #1A237E; padding-bottom:30px; margin-bottom:50px;'>
                <h1 style='font-family:\"Nanum Gothic\", sans-serif; font-size: 45px !important; margin:0 !important; color:#000000;'>{report_title.replace("🏮 ", "")}</h1>
                <div style='text-align: right; margin-top: 15px;'>
                    <span style='font-family:\"Nanum Gothic\", sans-serif; font-size: 14px; letter-spacing: 1px; color:#555;'>{version}</span>
                </div>
            </div>
            
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 40px 30px; border-radius: 15px; margin-bottom: 30px;'>
                <h2 style='font-size: 32px; font-weight: 900; color: #1A237E; margin-bottom: 25px;'>{u_icon} 신청인 : {name} 님</h2>
                <div style='font-size: 18px; line-height: 2.2; color:#333;'>
                    <p style='margin: 0;'>양력 : {sol}</p>
                    <p style='margin: 0;'>음력 : {lun}</p>
                    <p style='margin: 0;'>태어난 시간 : {time}</p>
                </div>
            </div>
            
            <p style='font-size: 20px; margin-top: 40px; font-weight: 700; color:#444;'>{today}</p>
            <p style='font-size: 26px; font-weight: 900; color: #1A237E; margin-top: 20px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class="page-break-before" style="page-break-before: always;"></div>
    """
