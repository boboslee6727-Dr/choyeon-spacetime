# 3-2. 출산택일 연산 및 출력 (사이드바에서 택일 선택 시에만)
        if run_delivery_calc and start_date and end_date and not st.session_state.get('saved_report_del') and st.session_state.get('saved_report_gh_g'):
            with st.spinner("⏳ 모래시계와 함께 출산택일 분석 중..."):
                try:
                    gans = st.session_state.get('global_gans', ["?", "?", "?", "?"])
                    jjis = st.session_state.get('global_jjis', ["?", "?", "?", "?"])
                    p_bazi_context = st.session_state.get('partner_bazi', ["?", "?", "?", "?"])
                    
                    if u_gender == "남성":
                        m_jjis = jjis
                        f_jjis = [b[1] if len(b)>1 else "?" for b in p_bazi_context]
                        m_gans_str = "".join(gans)
                        f_gans_str = "".join([b[0] if len(b)>0 else "?" for b in p_bazi_context])
                    else:
                        m_jjis = [b[1] if len(b)>1 else "?" for b in p_bazi_context]
                        f_jjis = jjis
                        m_gans_str = "".join([b[0] if len(b)>0 else "?" for b in p_bazi_context])
                        f_gans_str = "".join(gans)

                    # 🚨 1. 타이틀 및 합궁일 텍스트 수정
                    del_content = f"<h2 style='text-align:center; color:#4A148C; font-weight:900;'>👶 새 생명 마중 길일(출산 택일) 추천</h2>\n<p style='text-align:center; font-weight:bold; color:#4A148C;'>부모님의 사주와 조화를 이루는 합궁 길일입니다.</p>\n<div style='display:flex; flex-direction:column; align-items:center; margin-bottom:15px;'>"
                    
                    FORBIDDEN_LIST = ['병오', '임자', '계해', '신유', '경신']
                    delivery_days = get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, FORBIDDEN_LIST)
                    
                    # 🚨 2. 날짜 리스트 병합 (점수가 같은 연속된 날짜를 "A일 ~ B일"로 묶음)
                    if delivery_days:
                        first_day = dt_mod.datetime.strptime(delivery_days[0]['date'], '%Y-%m-%d').date()
                        last_day = dt_mod.datetime.strptime(delivery_days[-1]['date'], '%Y-%m-%d').date()
                        score = delivery_days[0]['score']
                        del_content += f"<div style='font-size:16px; font-weight:bold;'>✅ {first_day.year}년 {first_day.month}월 {first_day.day}일 ~ {last_day.day}일 (합 점수: {score})</div>\n"
                    del_content += "</div>"
                    
                    # 🚨 3. 가이드라인 폰트 크기 동기화 및 들여쓰기
                    del_content += f"<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px;'><b>💡 부부를 위한 임신 계획 가이드:</b><br>아래의 출산 길일은 아이의 사주 기운을 우선으로 선정한 것입니다. 의학적 평균 임신 기간(약 280일)을 고려할 때, <b>합궁 시기는 출산 예정일로부터 약 9개월 10일 전후</b>가 됩니다. 부인분의 생리 주기와 배란일을 면밀히 고려하시어, 부부께서 상의하에 가장 건강한 시기를 계획하시길 바랍니다.</p>"
                    
                    # 🚨 4. 박사님 고품격 도입부 (고정 텍스트로 삽입하여 AI 환각 원천 차단)
                    intro_essay = f"""<div style='margin-top:25px;'>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:8px;'>깊고 고요한 시간의 흐름 속에서, 새로운 생명의 탄생은 하늘과 땅, 그리고 부모의 염원이 조화롭게 어우러지는 기적과 같습니다. 귀한 부부께서 보내주신 소중한 사주 정보를 바탕으로, 장차 태어날 아기의 선천적 명식이 부모님과의 오행 상생 조화를 극대화하고, 나아가 아이 스스로 빛나는 삶의 궤적을 그려나갈 수 있도록 '최고의 프리미엄 출산 희망일과 시간'을 심혈을 기울여 선정하였습니다.</p>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:8px;'>부부의 사주를 살펴보니, 신청인 남성분({m_gans_str[3]}{m_jjis[3]}년 {m_gans_str[2]}{m_jjis[2]}월 {m_gans_str[1]}{m_jjis[1]}일 {m_gans_str[0]}{m_jjis[0]}시)께서는 {m_gans_str[1]} 일간으로 자신만의 고유한 기운이 특징적입니다. 상대방 여성분({f_gans_str[3]}{f_jjis[3]}년 {f_gans_str[2]}{f_jjis[2]}월 {f_gans_str[1]}{f_jjis[1]}일 {f_gans_str[0]}{f_jjis[0]}시)께서는 {f_gans_str[1]} 일간으로 지혜롭고 활발한 에너지를 지니셨습니다.</p>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:8px;'>아이가 태어날 시공간은 부모의 사주에 부족한 오행을 채우고, 동시에 아이 자신이 타고난 길운(吉運)을 펼칠 수 있는 절묘한 지점을 찾아야 합니다. 부부 모두에게 긍정적인 상생의 흐름을 만들어낼 수 있는 기운을 중심으로, 동시에 아이의 명식이 균형과 조화를 이루는 날들을 엄선하였습니다.</p>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:8px;'>이제, 부부의 간절한 바람을 담아 선정한 세 가지 최적의 출산 희망일을 <b>초연 시공명리 궁합</b> 관점에서 자세히 풀어내어 올립니다. 부디 이 추천들이 아기의 밝은 미래를 여는 데 귀한 나침반이 되기를 바랍니다.</p>
</div>"""
                    del_content += intro_essay

                    # 🚨 5. AI 프롬프트 정밀 통제 (여백, 간지 표기, 마크다운 컷)
                    delivery_prompt = f"""
당신은 명리심리상담사 초연 박사입니다. 부모의 사주 기운을 분석하여, 탐색 기간({start_date} ~ {end_date}) 내에서 아이의 선천적 명식과 부모간 상생 조화가 가장 극대화되는 '최고의 프리미엄 출산 희망일(3가지)'을 선정하여 명리 에세이로 풀어내십시오.

[부모 사주 정보]
- 신청인(남성): {m_gans_str[3]}{m_jjis[3]}년 {m_gans_str[2]}{m_jjis[2]}월 {m_gans_str[1]}{m_jjis[1]}일 {m_gans_str[0]}{m_jjis[0]}시
- 상대방(여성): {f_gans_str[3]}{f_jjis[3]}년 {f_gans_str[2]}{f_jjis[2]}월 {f_gans_str[1]}{f_jjis[1]}일 {f_gans_str[0]}{f_jjis[0]}시

🚨 [출력 절대 규칙 - 위반 시 치명적 오류]
1. 에세이 최상단/하단에 서론, 인사말, 맺음말(감사합니다 등) 절대 금지.
2. 단락을 구분할 때 '---' 같은 마크다운 구분선 및 빈 줄(엔터) 절대 금지.
3. 3가지 추천 일자 각각에 대해 아래의 HTML 포맷을 100% 토씨 하나 틀리지 말고 그대로 복사해서 채워 넣으십시오.
4. 모든 문단은 `<p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'>` 로 감싸서 출력하십시오.
5. 추천 일자 제목에 09:31~11:30 같은 구체적 시간과 사주 8글자를 반드시 병기하십시오.

[출력 포맷 템플릿]
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111; margin-top:15px; margin-bottom:5px; display:block;'>▶ 추천 일자: OOOO년 OO월 OO일 OO:OO~OO:OO (OO년 OO월 OO일 OO시)</span>
<div style='padding-left: 15px; margin-bottom: 15px;'>
    <div style='margin-bottom: 5px;'><b>1) 일반 명리 풀이:</b></div>
    <p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'> (아이 명식의 오행, 격국, 육친적 장점 및 부모 사주와의 상생 보완 관계 상세 기술) </p>
    <div style='margin-bottom: 5px; margin-top:10px;'><b>2) 시공 명리 풀이:</b></div>
    <p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'> (해당 시공간의 기운이 아이의 학업, 직업적 성취, 자산 운용에 미치는 장기적 운명 기술) </p>
</div>
"""
                    ai_delivery_html = call_gemini_api(delivery_prompt).replace('\n', '')
                    
                    # 🚨 6. 클로징 에세이
                    closing_del_html = f"""<div style='margin-top: 25px;'>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>사랑하는 부부님, 이 세 가지 출산 희망일은 각각 독특하고 고귀한 기운을 담고 있습니다. 하늘의 뜻과 부모님의 깊은 사랑, 그리고 제가 바친 노력이 한데 어우러져 귀한 아기가 이 세상에 가장 찬란하게 빛을 발하며 첫걸음을 내딛기를 진심으로 기원합니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>어떤 날을 선택하시든, 그 선택은 아기에게 최고의 축복이 될 것입니다. 아기의 탄생으로 가정이 더욱 행복하고 번창하시기를 간절히 축원합니다.</p>
<div style='text-align: right; margin-top: 30px;'>
<span style='font-weight: 900; font-size: 18px; color: #4A148C;'>- 초연 시공명리 연구소 드림 -</span>
</div>
</div>"""

                    del_content += f"<div class='content-box-loose' style='font-size:15px; line-height:1.8; margin-top:15px;'>\n{ai_delivery_html}\n{closing_del_html}\n</div>"

                    def wrap_a4_del(content, title_color="#4A148C", title="초연 시공명리 출산택일"):
                        return f"<div class='report-page'>\n<div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'>\n<div style='border-bottom:4px double {title_color}; padding-bottom:20px; margin-bottom:30px;'>\n<h1 style='text-align:center; font-size: 32px; color:{title_color}; font-weight: 900; margin:0; font-family:\"Malgun Gothic\", sans-serif;'>👶 {title}</h1>\n</div>\n{content}\n</div>\n</div>"

                    st.session_state['saved_report_del'] = wrap_a4_del(del_content, "#4A148C", "초연 시공명리 출산택일")
                    st.rerun() 
                except Exception as e:
                    st.error(f"출산택일 연산 장애: {e}")
