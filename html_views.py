def get_bottom_board(name_str):
    """
    사주 원국표 아래에 붙을 대운/세운/월운 및 맺음말 HTML을 반환합니다.
    (박사님께서 주신 원본 HTML 형태를 그대로 유지)
    """
    # 박사님의 원본 HTML 코드에 이름 부분만 {name_str}로 동적 처리
    html_content = f"""
    <div style='border:2px solid #3E2723; margin-top:15px; padding:8px 10px; display:flex; justify-content:space-between; align-items:center; font-family:"Noto Serif KR", serif !important; font-weight:900; font-size:12.5px; border-radius:8px; white-space:nowrap; background:#FFFDE7; letter-spacing:-0.7px;'>
        <div>🔢 대운수: <span style='color:#1A237E;'>3</span></div>
        <div>💥 오행: 木(2) 火(1) 土(2) 金(0) 水(3)</div>
        <div>🌟 귀인: <span style='color:#1A237E;'>卯, 巳</span></div>
        <div>🎯 공망: [년]<span style='color:#1A237E;'>辰,巳</span> [일]<span style='color:#1A237E;'>子,丑</span></div>
        <div>🌪️ 삼재: <span style='color:#2E7D32;'>해당 없음</span></div>
    </div>
    <div style='margin-top:5px; margin-bottom:8px; font-size:17px; font-weight:900; color:#1A237E; font-family:"Noto Serif KR", serif !important;'>[ 대운의 흐름 (대운수: 3, 역행) ]</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:12px; font-family:"Noto Serif KR", serif !important;'>
        <div style='flex:1; border-left:1px solid #ccc; text-align:center; padding-bottom:2px; background-color:transparent; line-height:1.15;'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:11.5px; border-bottom:1px solid #ccc;'>3세</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>상관</div><div class='color-목' style='font-size:15px; font-weight:900; padding:1px 0;'>甲</div><div class='color-수' style='font-size:15px; font-weight:900; padding:1px 0;'>子</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>비견</div><div style='font-size:11px; font-weight:normal; color:#0D47A1; border-top:1px solid #ccc; padding-top:1px;'>건록</div><div style='font-size:11px; font-weight:normal; color:#C62828; border-top:1px solid #ccc; padding-top:1px;'>년살</div></div>
        <div style='flex:1; border-left:1px solid #ccc; text-align:center; padding-bottom:2px; background-color:transparent; line-height:1.15;'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:11.5px; border-bottom:1px solid #ccc;'>13세</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>비견</div><div class='color-수' style='font-size:15px; font-weight:900; padding:1px 0;'>癸</div><div class='color-수' style='font-size:15px; font-weight:900; padding:1px 0;'>亥</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>겁재</div><div style='font-size:11px; font-weight:normal; color:#0D47A1; border-top:1px solid #ccc; padding-top:1px;'>제왕</div><div style='font-size:11px; font-weight:normal; color:#C62828; border-top:1px solid #ccc; padding-top:1px;'>지살</div></div>
        </div>
    
    <div style='margin-top:10px; margin-bottom:8px; font-size:17px; font-weight:900; color:#1A237E; font-family:"Noto Serif KR", serif !important;'>[ 세운의 흐름 (戊午대운 기준) ]</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:12px; font-family:"Noto Serif KR", serif !important;'>
        <div style='flex:1; border-left:1px solid #ccc; text-align:center; padding-bottom:2px; background-color:#E1F5FE; line-height:1.15;'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:11.5px; line-height:1.2; border-bottom:1px solid #ccc;'>2026년<br>(63세)</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>정재</div><div class='color-화' style='font-size:15px; font-weight:900; padding:1px 0;'>丙</div><div class='color-화' style='font-size:15px; font-weight:900; padding:1px 0;'>午</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>편재</div><div style='font-size:11px; font-weight:normal; color:#0D47A1; border-top:1px solid #ccc; padding-top:1px;'>절</div><div style='font-size:11px; font-weight:normal; color:#C62828; border-top:1px solid #ccc; padding-top:1px;'>육해살</div></div>
        </div>
    
    <div style='margin-top:10px; margin-bottom:8px; font-size:17px; font-weight:900; color:#1A237E; font-family:"Noto Serif KR", serif !important;'>[ 월운의 흐름 (2026년도 양력기준) ]</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:12px; font-family:"Noto Serif KR", serif !important;'>
        <div style='flex:1; border-left:1px solid #ccc; text-align:center; padding-bottom:2px; background-color:transparent; line-height:1.15;'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:11.5px; border-bottom:1px solid #ccc;'>1월</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>편관</div><div class='color-토' style='font-size:15px; font-weight:900; padding:1px 0;'>己</div><div class='color-토' style='font-size:15px; font-weight:900; padding:1px 0;'>丑</div><div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>편관</div><div style='font-size:11px; font-weight:normal; color:#0D47A1; border-top:1px solid #ccc; padding-top:1px;'>관대</div><div style='font-size:11px; font-weight:normal; color:#C62828; border-top:1px solid #ccc; padding-top:1px;'>월살</div></div>
        </div>
    
    <div style='margin-top: 40px; border-top: 2px dashed #444; padding-top: 25px;'>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드(bar-code)와 같지만, 우리가 살아가며 마주하는 스캐너(scanner)인 '운'은 늘 변화하며 흐릅니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{name_str}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 시공명리의 지혜와 궁금증이 있으시면 언제든 <b>'초연 시공명리 연구소'</b>의 문을 두드려 주십시오.</p>
        <p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
        <div style='text-align: right; margin-top: 30px;'>
            <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
        </div>
    </div>
    """
    return html_content
