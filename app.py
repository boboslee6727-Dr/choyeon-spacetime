# [4] 부부 대운 흐름 상하 비교표 출력 (새로운 레이아웃)
            daewoon_compare_html = f"""
            <div style='background-color:#FFFFFF; padding:40px; margin:20px auto; border:1px solid #E0E0E0; border-radius:15px; max-width:1000px;'>
                <div style='border: 2px solid #1A237E; border-radius: 12px; padding: 30px; background-color:#FAFAFA;'>
                    <h2 style='text-align:center; color:#1A237E; font-weight:900; margin-bottom: 30px;'>[ 부부 대운(大運) 흐름 비교 분석 ]</h2>
                    
                    <!-- 남명 대운 출력 -->
                    <div style='margin-bottom: 40px;'>
                        <h4 style='color:#3E2723; font-weight:800;'>&#9794; 男命 ({m_name}님) 대운 흐름</h4>
                        {m_un_html}
                    </div>
                    
                    <!-- 여명 대운 출력 -->
                    <div>
                        <h4 style='color:#3E2723; font-weight:800;'>&#9792; 女命 ({w_name}님) 대운 흐름</h4>
                        {w_un_html}
                    </div>
                </div>
            </div>
            <div class="page-break-before"></div>
            """
            st.markdown(daewoon_compare_html, unsafe_allow_html=True)
