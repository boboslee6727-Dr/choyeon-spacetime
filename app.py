# ------------------------------------------------------------------
            # 3. 통합 표지 및 남명/여명 사주 원국 렌더링
            # ------------------------------------------------------------------
            
            # [통합 표지 출력]
            app_p_icon = "♂️" if gender == "남성" else "♀️"
            part_p_icon = "♂️" if f_gender == "남성" else "♀️"
            
            gunghap_cover_html = f"""
            <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
                <div style='border: 4px solid #1A237E; padding: 60px 30px; border-radius: 20px; text-align: center; background: white; width: 90%; max-width: 800px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
                    <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:50px;'>
                        <h1 style='font-size: 26px !important; margin:0 !important; font-weight: 900; color: #1A237E; white-space: nowrap;'>&#127982; 초연 시공명리 궁합 감명서</h1>
                        <div style='text-align: right; margin-top: 10px;'>
                            <span style='font-size: 14px; letter-spacing: 1px; color: #555;'>{APP_VERSION}</span>
                        </div>
                    </div>
                    <!-- 🚨 이모지 인코딩 에러 방지를 위해 꽃다발 이모지를 HTML 엔티티(&#128144;)로 교체 -->
                    <h3 style='font-size: 20px; font-weight: 800; color: #333; margin-bottom: 40px;'>[ &#128144; 百年偕老 緣分 鑑定書 ]</h3>
                    <div style='display: flex; justify-content: space-between; align-items: center; background:#F8F9FA; border: 1px solid #E8EAF6; padding: 35px 25px; border-radius: 15px; margin-bottom: 40px;'>
                        <div style='flex: 1; text-align: center; border-right: 1px dashed #CCC; padding-right: 10px;'>
                            <span style='font-size: 20px; font-weight: 800; color: #1A237E;'>{app_p_icon} {name} 님</span>
                            <p style='font-size: 14px; color: #555; margin: 10px 0 0 0;'>{gender} / {u_marital}</p>
                        </div>
                        <div style='flex: 0.4; text-align: center; font-size: 24px; color: #1A237E; font-weight: 900;'>緣</div>
                        <div style='flex: 1; text-align: center; border-left: 1px dashed #CCC; padding-left: 10px;'>
                            <span style='font-size: 20px; font-weight: 800; color: #1A237E;'>{part_p_icon} {f_name} 님</span>
                            <p style='font-size: 14px; color: #555; margin: 10px 0 0 0;'>{f_gender} / {f_marital}</p>
                        </div>
                    </div>
                    <p style='font-size: 16px; font-weight: 700; color: #444; margin-top: 50px;'>위 두 분의 시공간적 에너지 흐름과 음양오행의 조화를 정밀 감명하였습니다.</p>
                    <p style='font-size: 16px; margin-top: 60px; font-weight: 800; color: #000;'>{today_str}</p>
                    <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 시공명리 연구소</p>
                </div>
            </div>
            <div class="page-break-before"></div>
            """
            st.markdown(gunghap_cover_html, unsafe_allow_html=True)
