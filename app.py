try:
                    res = model.generate_content(prompt)
                    ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                    
                    # 🎯 [어제 새벽의 완벽 복구 코드] AI의 환각을 100% 박살 내는 강제 주입 로직!
                    if "[CHOYEON_GOLDEN_TEXT_HERE]" in ai_text:
                        # 1. AI가 말을 잘 듣고 마커를 남겨두었을 경우 (정상 치환)
                        ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", f"<p style='font-size: 18px; line-height: 1.8; margin-bottom: 20px; font-weight: bold;'>{choyeon_golden_text}</p>")
                    else:
                        # 2. 🚨비상사태: AI가 마커를 지우고 제멋대로 서론(이병호님의 인생은...)을 지어냈을 경우!
                        # '1) 타고난 삶의 무대' 앞부분을 찾아 AI의 헛소리를 통째로 도려냅니다.
                        target_marker = "1) 타고난 삶의 무대"
                        if target_marker in ai_text:
                            parts = ai_text.split(target_marker)
                            div_marker = "<div class='content-box-loose'>"
                            # 상단에서 <div class='content-box-loose'> 까지만 남기고 AI의 망발은 삭제!
                            if div_marker in parts[0]:
                                top_clean = parts[0][:parts[0].find(div_marker) + len(div_marker)]
                                # 깨끗해진 상단 + 박사님의 옥음(자의형상) + 다시 1) 항목 연결
                                ai_text = top_clean + f"\n<p style='font-size: 18px; line-height: 1.8; margin-bottom: 20px; font-weight: bold;'>{choyeon_golden_text}</p>\n<span class='sub-title' style='font-size: 20px; font-weight: 900; color: #111;'>" + target_marker + parts[1]

                    # 운의 흐름표 주입 로직
                    ai_text = ai_text.replace("[DAEWUN_TABLE_HERE]", un_html).replace("[SEWUN_TABLE_HERE]", se_html).replace("[WOLWUN_TABLE_HERE]", wol_html)
                    
                    # 표 누락 비상장치 (표가 맨 밑으로 깔리도록)
                    if un_html not in ai_text:
                        ai_text = ai_text + "<div style='color:red; margin-top:30px;'>⚠️ (AI 표 마커 누락으로 비상 출력된 운의 흐름표)</div>" + un_html + se_html + wol_html

                    report_1_full_html = f"""<div class='report-page'>
