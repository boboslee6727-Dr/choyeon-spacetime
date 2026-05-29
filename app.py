                # ------------------------------------------------------------------
                # [모드 1] 개인사주 전용 마크다운 호출 (궁합/비교 모드가 아닐 때만 실행)
                # ------------------------------------------------------------------
                if u_product in ["개인사주", "타 감명서"]:
                    # 🚨 [수정 완료] 누락되었던 나이, 성별, 육친 타겟팅 변수 선언 (NameError 해결)
                    if u_age < 30:
                        age_prompt = "내담자는 청년기(학업, 진로, 취업, 연애 고민)에 있으므로 현실적인 직업과 이성운에 초점을 맞출 것."
                    elif u_age < 55:
                        age_prompt = "내담자는 중장년기(사회적 안정, 재물 축적, 가정)에 있으므로 재물운, 사업/직장운, 가정의 안정에 초점을 맞출 것."
                    else:
                        age_prompt = "내담자는 노년기(은퇴, 건강, 노후)에 있으므로 건강운과 심리적 평안, 노후 자산 안정에 초점을 맞출 것."
                        
                    gender_prompt = f"내담자는 {u_gender}이므로, {u_gender}의 심리적/사회적 특성을 섬세하게 고려하여 카운슬링할 것."
                    yukchin_rule = "- 육친 통변 규칙: 남명의 경우 재성을 배우자로, 관성을 자식으로 통변. 여명의 경우 관성을 배우자로, 식상을 자식으로 통변할 것."

                    # 🚨 [수정 포인트 1] 대운 간지 문자열 조립 추가
                    wol_info_str = ", ".join([f"{i+1}월({wol_gans[i]}{wol_jis[i]})" for i in range(12)])
                    daewun_info_str = ", ".join(daewun_info)

                    # 🚨 [수정 포인트 2] db_header 내 년주 공망 삭제 및 오행 팩트 추가
                    db_header = (
                        f"[시스템 강제 시간 인식: 현재 시점은 {curr_y}년 {curr_m}월 입니다.]\n"
                        "당신은 명리심리상담사 1급 자격을 갖춘 초연 박사입니다. \n"
                        f"- 내담자 성함: {disp_name}\n"
                        f"- 나이 / 성별: {u_age}세 / {u_gender}\n"
                        f"- 🚨 [절대 기준 명조(사주팔자)]: 년주({ys}{yb}), 월주({ms}{mb}), 일주({ds}{db}), 시주({hs}{hb})\n"
                        f"- 🚨 [절대 기준 일간(본신)]: {ds} (모든 통변의 주체는 무조건 '{ds}' 일간을 기준으로 작성할 것)\n"
                        f"- 🚨 [오행 분포 팩트]: 목({counts['목']}), 화({counts['화']}), 토({counts['토']}), 금({counts['금']}), 수({counts['수']})\n"
                        f"- marital_status: {u_marital}\n"
                        f"- 타고난 심리 구조 팩트: {s_name} ({s_type} - {s_desc})\n"
                        f"- 공망 팩트: [일주 기준] {i_gong} (※ 반드시 일주 기준 공망만 사용하여 통변할 것)\n"
                    )

                    prompt = f"""
    {db_header}
    
    [ 🚨종합 특별지시 사항 : 대중을 위한 현대적 통변 원칙]
    (※ AI 지시: AI는 전체 에세이 작성 시 아래 원칙을 반드시 뼛속 깊이 새기고 준수하십시오.)
    1. 🚨명리 용어 순화: 격국, 비견, 식상, 관성, 조후, 용신, 희신 등의 딱딱한 한자어 전문 용어 남발을 엄격히 금지합니다.
    2. 직관적인 쉬운 해설: 부득이하게 명리 용어를 언급해야 할 경우, 반드시 일반인이 단번에 이해할 수 있는 일상적인 비유와 현대적 구어체로 부드럽게 풀어서 설명하십시오. 
    3. 따뜻한 상담가 마인드: 명리학 강의를 하듯 가르치려 들지 말고, 내담자의 삶을 깊이 이해하고 어루만져 주는 친절하고 세련된 카운슬러의 어조(현대적 구어체)로 모든 글을 전개하십시오.
    4. 🚨[절대 성역]: 단, 문서 상단에 주입되는 '[CHOYEON_GOLDEN_TEXT_HERE]' (자의형상) 문장은 초연 박사의 고유한 선언문이므로 절대 이 지시의 영향을 받지 않으며, 부연 설명 없이 원문 그대로 100% 출력해야 합니다.
    5. 🚨 초연 시공명리 3대 관점의 입체적 풀이: 사주를 단편적으로 해석하지 마십시오. 모든 통변을 전개할 때는 반드시 1) 육친적 관점, 2) 심리적 관점, 3) 사회적 관점이라는 세 가지 차원을 유기적으로 융합하여 매우 심도 있고 입체적인 에세이를 작성하십시오.
    
    [문단 통제 명령]
    1. 모든 통변 에세이 문장은 반드시 <p style='text-indent: 1em;'> 태그로 감싸십시오.
    2. 적절한 지점에서는 반드시 단락 나누기를 집행하십시오.
    3. 🚨 [계층별 글자 크기 및 상하 간격 강제 규격화] 가독성을 위해 목차의 성격에 따라 아래의 태그를 토씨 하나 틀리지 말고 적용하십시오! (반드시 display: block; 을 유지해야 상하 여백이 작동합니다)
    
       [지시 3-1] '1), 2)' 형태의 부목차는 20px 크기와 넓은 간격 적용:
       <span class='sub-title' style='display: block; font-size: 20px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 35px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
    
       [지시 3-2] '▶, ▷, ◈, •' 형태의 세부 소목차는 18px 크기와 좁은 간격 적용:
       <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 25px; margin-bottom: 5px;'>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</span>
       <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 25px; margin-bottom: 5px;'>• {dw_start_age}세~{dw_mid_age}세 대운:</span>
       <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 25px; margin-bottom: 5px;'>◈ 나를 돕는 에너지와 색상:</span>
    
    4. 별표 2개를 사용하여 글씨를 굵게 만드는 행위를 금지합니다.
    5. 🚨 호칭 강제: 내담자를 지칭할 때는 오직 '{disp_name}님'만 사용하십시오. ('선생님', '당신' 절대 사용 금지)
    6. 🚨 인사말 철저 금지: "안녕하십니까", "반갑습니다", "초연입니다" 등 쓸데없는 인사말이나 오지랖 멘트를 절대 작성하지 마십시오. 시작부터 바로 본론(사주 분석)으로 진입하십시오.
    7. 🚨 전통명리 이론 기반 통변: AI가 임의로 지어내는 문학적 비유를 철저히 금지합니다. 오직 사주 원국 간지의 물상 형상 등 정통 명리학 이론에 입각하여 이해하기 쉬운 구어체로 설명하십시오.
    8. 🚨 표(Table) 생성 절대 금지: AI가 임의로 마크다운 표(|---|)나 HTML <table>을 생성하는 것을 엄격히 금지합니다. 대운/세운/월운의 연도별 분석은 반드시 도트 기호(•)를 사용한 텍스트로만 작성하십시오.
    
    [내담자 맞춤형 정밀 타겟팅]
    - {age_prompt}
    - {gender_prompt}
    {yukchin_rule}
    
[통변 지시]
    - 모든 명리 용어는 대중이 이해하기 쉬운 현대적 구어체 표현 뒤에 괄호 형태로 병기하십시오.
    - 🚨 간지 및 지지 표기 규칙: 지지를 표기할 때 '巳화', '辰토'처럼 한글과 한자를 섞지 말고, 오직 巳(사), 辰(진)처럼 순수 한자 또는 괄호 병기 형태로만 일관되게 표기하십시오.
    - 격국 팩트: {gyukgook_detail}
    - 공망 팩트: 일주 기준 {i_gong}
    - 일반신살: {shinsal_str} / 12신살: {s12_str}
    - 입고/개고 팩트: 위 헤더에 제공된 원국 및 행운의 묘고 작용을 반드시 사주팔자의 역동적 관계 분석에 포함하십시오.
    
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>1. 사주팔자 구조 분석</h3>
    <div class='content-box-loose'>
    [CHOYEON_GOLDEN_TEXT_HERE]
    (※ AI 지시: 위 마커 자리에 들어갈 문장은 초연 박사가 직접 작성한 절대적인 원문이므로 절대 건드리지 마십시오. 
    어떠한 부연 설명이나 사족도 덧붙이지 말고, 즉시 아래 '1) 타고난 삶의 무대와 나의 주력 무기' 분석으로 넘어가십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 타고난 삶의 무대와 기본 성향</span>
    (※ AI 지시: 내담자의 사주구조({gyukgook_detail})를 바탕으로 사회적 무대와 기본 성향을 에세이로 작성하십시오.
    🚨특히, 내담자의 핵심 재능(월지 지장간)이 어느 위치(연간, 월간, 시간)로 투출(뻗어 나갔는지)하였는지를 분석하여, 
    "나의 재능이 어느 시기에(조기/즉각/대기만성), 어느 정도 규모의 무대(전국구/직장/개인)에서 어떻게 발현되는지"를 일반인이 이해하기 쉬운 현대적 구어체로 아주 구체적으로 풀어서 조언하십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 내 삶의 리듬과 에너지 균형</span>
    (※ AI 지시 🚨[오행 환각 절대 금지]: 반드시 헤더에 제공된 '🚨 [오행 분포 팩트]'의 실제 개수를 확인하십시오! 
    없는 오행(0개)을 강하다고 하거나, 있는 오행을 없다고 지어내는 소설을 엄격히 금지합니다. 
    실제 팩트 기반으로 사주팔자 오행의 분포와 계절적 조후, 억부의 균형 상태를 분석하고 삶에서 어떤 에너지를 추구해야 하는지 에세이를 작성하십시오.)

    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 사주팔자의 역동적 관계 분석</span>
    (※ AI 지시: 사주 원국의 합충형파해, 진술축미 입/개고, 일반신살 및 포태법의 명리적 원리를 철저히 분석하십시오. 
    🚨단, 절대 (丑丑), (卯丑)처럼 사주 원국의 한자나 명리 전문 용어를 괄호 안에 병기하거나 표면적으로 노출하지 마십시오. 
    오직 이 원리들을 바탕으로 내담자의 '전체적인 삶의 굴곡, 대인관계의 역동성, 직업적 변동성'에 초점을 맞추어 일반인이 이해하기 쉬운 구어체 에세이로만 작성하십시오. 
    이성운/부부운에 대한 언급은 제외하십시오.)
    </div>
    
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>2. 성격</h3>
    <div class='content-box-loose'>
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 겉으로 드러난 성격</span>
    (※ AI 지시: 일주의 십성 및 십이운성과 십이신살을 중심으로 육친적, 심리적, 사회적, 표면적으로 드러나는 성격과 기질을 구체적이고 현대적인 구어체로 작성하십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 감추어진 내 속마음</span>
    (※ AI 지시: 오행의 과다/과소 및 조후를 바탕으로 내면의 스트레스, 무의식적 욕구, 심리적 방어기제, 공망 등을 상세히 분석하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>3. 부모·형제운</h3><div class='content-box-loose'>
    (※ AI 지시: 사주 원국의 연주·월주 및 인성과 비겁의 상태를 분석하여 에세이를 작성하십시오. 1) 육친적으로 부모·형제와의 정서적 유대감과 덕의 유무를 살피고, 2) 심리적으로 이들이 내담자 내면의 자양분 혹은 결핍에 미친 영향을 진단하며, 3) 사회적으로 유년기 환경이 삶의 기반에 어떤 작용을 했는지 현대적 구어체로 친절하게 풀어내십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>4. 학업·진학운</h3><div class='content-box-loose'>
    (※ AI 지시: 인성과 식상의 관계, 관성의 통제력을 바탕으로 에세이를 작성하십시오. 1) 심리적으로 지적 호기심과 집중력의 방향성을 파악하고, 2) 육친적으로 학업 과정에서 주변 환경의 지지나 방해 요소를 보며, 3) 사회적으로 최종 학위나 전공이 현실적인 커리어와 어떻게 연결되는지 그 성패를 이해하기 쉽게 조언하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>5. 적성·직업운</h3><div class='content-box-loose'>
    (※ AI 지시: 원국의 구조와 주력 에너지를 바탕으로 에세이를 작성하십시오. 1) 심리적으로 어떤 직무나 환경에서 가장 큰 성취감과 동기를 얻는지, 2) 사회적으로 탄탄한 조직(직장)형 기질인지 개인 독립(전문직/사업)형 기질인지를 짚어 구체적인 직업적 방향성을 제안하고, 3) 육친적인 대인관계 협업 스타일까지 종합하여 세련된 구어체로 작성하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>6. 결혼·자녀운</h3><div class='content-box-loose'>
    (※ AI 지시: 일지와 시주, 재성/관성 및 식상의 동태를 분석하여 에세이를 작성하십시오. 1) 육친적으로 배우자 및 자녀 인연의 깊이와 형태를 살피고, 2) 심리적으로 내담자가 내면에서 바라는 이상적인 가정상과 정서적 정착 과정을 진단하며, 3) 사회적으로 가정을 꾸리는 것이 현실적 삶의 안정도에 미치는 변화를 카운슬러의 어조로 따뜻하게 서술하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>7. 재성운</h3><div class='content-box-loose'>
    (※ AI 지시: 재성의 유무와 상태, 식상의 생조 여부를 파악하여 에세이를 작성하십시오. 1) 심리적으로 돈과 물질을 대하는 가치관과 집착도를 진단하여 내담자 성향에 맞는 '재물 관리 스타일(투자형 vs 저축형)'을 정립해 주고, 2) 사회적으로 평생의 자산 규모와 경제적 성패의 흐름을 예측하며, 3) 육친적으로 재물로 인해 주변 사람들과 상생하거나 갈등하는 역동성을 조언하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>8. 사업운</h3><div class='content-box-loose'>
    (※ AI 지시: 식상생재의 흐름과 편재, 비겁의 조력 여부를 분석하여 에세이를 작성하십시오. 1) 심리적으로 위험을 감수하는 도전 정신과 시장을 읽는 직관력을 진단하고, 2) 사회적으로 독자적인 창업이나 사업체 운영의 적합성 및 규모 확장성을 예측하며, 3) 육친적으로 동업자, 직원, 고객을 끌어당기는 대인관계 리더십의 강점과 약점을 조언하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>9. 관직·명예운</h3><div class='content-box-loose'>
    (※ AI 지시: 관인상생 및 정관/편관의 상태를 바탕으로 에세이를 작성하십시오. 1) 사회적으로 조직 내에서의 승진, 명예, 라이선스(자격증) 취득 및 감투운을 평가하고, 2) 심리적으로 권력이나 자존심을 추구하는 욕구와 책임감의 크기를 분석하며, 3) 육친적으로 윗사람이나 대중, 사회적 시스템으로부터 인정받는 흐름을 매끄러운 구어체로 서술하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>10. 건강운</h3><div class='content-box-loose'>
    (※ AI 지시: 오행의 분포와 과다/과소, 그리고 계절적 조후의 균형 상태를 분석하여 에세이를 작성하십시오. 1) 심리적 스트레스나 과로가 취약한 신체 기관(질환)으로 발현되는 원리를 명리적 물상과 연결하여 경고하고, 2) 사회 활동을 건강하게 지속하기 위한 현실적인 에너지 관리법을 제시하며, 3) 육친적 환경이 내담자의 정서적 안정과 건강에 미치는 영향까지 고려하여 친절하게 서술하십시오.)
    </div>
    
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>11. 운의 흐름</h3>
    <div class='content-box-loose'>
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 대운의 흐름</span>
    [DAEWUN_TABLE_HERE]
    (🚨 대운 간지 및 방향 팩트: 대운 방향은 {direction_str}이며, 각 대운의 흐름은 [{daewun_info_str}] 입니다.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 대운 분석</span>
    (※ AI 지시 🚨[대운 환각 및 총평 절대 금지]: 바로 위에 제공된 '대운 간지 및 방향 팩트' 데이터를 반드시 확인하고, 해당 나이대에 맞는 정확한 간지 글자만을 사용하여 통변하십시오. AI 임의로 순행/역행을 착각하여 엉뚱한 간지를 지어내면 절대 안 됩니다. 첫 번째 대운부터 나열하되, "인생 전반부는 어떠했다"는 식의 도입부 오지랖 총평을 일절 생략하고 즉시 항목부터 서술하십시오. 항목 제목은 **• {calc_d}세~{calc_d+9}세 대운:** 과 같이 팩트에 기반하여 마크다운 굵은 글씨로 강조하십시오. 표 생성 절대 금지.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 현재 대운 전반기 상세 분석 ({dw_start_age}세~{dw_mid_age}세)</span>
    (※ AI 지시: 막 진입한 대운을 두고 "대운 한가운데를 지나고 있다"고 표현하는 등 시기적 착각을 절대 금지합니다. 현재 내담자의 나이({u_age}세)와 대운 진입 시점을 정확히 자각하십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</span>
    (※ AI 지시: 현재 대운의 십성과 오행 기운이 내담자의 삶에 미치는 심리적, 사회적 변화를 상세히 카운슬링하십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 세운의 흐름</span>
    [SEWUN_TABLE_HERE]
    (※ AI 지시: 위 마커 자리는 파이썬이 세운 흐름표를 꽂을 자리이므로 절대 지우지 말고 그대로 두십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 세운 분석</span>
    (※ AI 지시: 최근 지나온 과거 각 세운들을 하나씩 나열하되, 항목의 제목은 반드시 **• 2024년(갑진년):** 과 같이 마크다운 굵은 글씨(**)로 강조하여 2~3줄씩 요약하십시오. 단, 올해가 새로운 대운으로 바뀌는 첫 해일 경우, 이전 대운의 마지막 2~3년간의 세운을 분석하여 대운 교체기의 흐름을 명확히 서술하십시오. 표 생성 절대 금지.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 올해 세운 전반기 상세 분석</span>
    (※ AI 지시: 올해 세운 전반기(양력2월~7월)의 십성과 오행 기운이 내담자의 삶에 미치는 심리적, 사회적 변화를 상세히 카운슬링하십시오.)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 올해 세운 후반기 상세 분석</span>
    (※ AI 지시: 올해 세운 후반기(양력8월~다음년도 1월)의 십성과 오행 기운이 내담자의 삶에 미치는 심리적, 사회적 변화를 상세히 카운슬링하십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 월운의 흐름</span>
    [WOLWUN_TABLE_HERE]
    
    (🚨 올해 월운 간지 팩트: {wol_info_str})
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 월운 분석</span>
    {past_months_html}
    (※ AI 지시 🚨[양력 1월 특명 및 월운 환각 절대 금지]: 
    1. 🚨 양력 1월은 명리학적 기준(입춘 전)으로 '작년도 12월(己丑월)'에 해당합니다. 1월 운세 서술 시 반드시 "작년의 기운이 마무리되는 작년도 12월 기축(己丑)월의 흐름으로..."라는 맥락으로 감명하십시오.
    2. 바로 위에 제공된 '올해 월운 간지 팩트' 데이터를 반드시 확인하고, 해당 월의 정확한 간지 글자만을 사용하여 통변하십시오. 
    3. 항목 제목은 반드시 **• 1월(己丑월):**, **• 2월(庚寅월):** 과 같이 팩트에 기반하여 요약하십시오. 표 생성 절대 금지.)

    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>12. 삶을 바꾸는 지혜로운 조언</h3>
    <div class='content-box-loose'>
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 나를 돕는 에너지와 색상:</span>
    (※ AI 지시: 에세이 작성)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 신체 밸런스와 에너지 관리:</span>
    (※ AI 지시: 에세이 작성)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 공간의 흐름과 방위의 지혜:</span>
    (※ AI 지시: 에세이 작성)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 재능 효율을 높이는 직업적 지혜:</span>
    (※ AI 지시: 에세이 작성)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 더 나은 내일을 위한 절제의 미학:</span>
    (※ AI 지시: 에세이 작성)
    </div>
    
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'> 🎯 초연 시공명리 특별 개운 비법</h3>
    <div class='content-box-loose'>
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 수호 천사의 기운:</span>
    (※ AI 지시: 사주원국 및 운(시간)의 흐름에 따른 천을귀인과 길신 등의 작용에 대한 상세한 에세이를 작성하시오.)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 백년해로의 기운:</span>
    (※ AI 지시: 오행의 치우침, 원진, 고란살, 고신(남명), 과숙(여명) 등 이성 관계에 영향을 미치는 사주원국 및 운의 흐름을 분석하되, 전문 용어는 철저히 숨기십시오. 
    이곳에서는 오직 '부부 및 연인 관계에서 발생할 수 있는 성격적/상황적 갈등 요소'와 이를 슬기롭게 극복하고 백년해로하기 위한 
    '실질적이고 따뜻한 개운 비법(마음가짐, 소통 방식, 행동 요령 등)'에만 100% 초점을 맞추어 카운슬러의 어조로 작성하십시오.)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 행운에 따른 기운:</span>
    (※ AI 지시: 운의 흐름에 따른 합형충파해와 진술축미의 입고와 개고, 도화(연살)/망신/역마살 작용에 따른 역동성과 재물과 대인관계 등 주의할 점에 대한 상세한 에세이를 작성하시오.)
    </div>
    """
                res_text = call_claude_api(prompt, max_tokens=12000)
                ai_text = "\n".join([line.lstrip() for line in res_text.split("\n")])
                
                if "[CHOYEON_GOLDEN_TEXT_HERE]" in ai_text:
                    ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)
                else:
                    target_marker = "1) 타고난 삶의 무대와 기본 성향"
                    if target_marker in ai_text:
                        parts = ai_text.split(target_marker)
                        div_marker = "<div class='content-box-loose'>"
                        if div_marker in parts[0]:
                            top_clean = parts[0][:parts[0].find(div_marker) + len(div_marker)]
                            ai_text = top_clean + f"\n{choyeon_golden_text}\n<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>" + target_marker + parts[1]

                un_html_clean = un_html.replace("\n", " ").replace("\r", "")
                se_html_clean = se_html.replace("\n", " ").replace("\r", "")
                wol_html_clean = wol_html.replace("\n", " ").replace("\r", "")

                clean_ai_text = ai_text

                daeoun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{un_html_clean}</div>"
                sewun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{se_html_clean}</div>"
                wolwun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{wol_html_clean}</div>"

                clean_ai_text, count_d = re.subn(r'[\#\*\_\s]*\[\s*DAEWUN_TABLE_HERE\s*\][\#\*\_\s]*', daeoun_target, clean_ai_text, flags=re.IGNORECASE)
                clean_ai_text, count_s = re.subn(r'[\#\*\_\s]*\[\s*SEWUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                clean_ai_text, count_w = re.subn(r'[\#\*\_\s]*\[\s*WOLWUN_TABLE_HERE\s*\][\#\*\_\s]*', wolwun_target, clean_ai_text, flags=re.IGNORECASE)

                clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*CHAM_DAEOUN_TABLE_HERE\s*\][\#\*\_\s]*', daeoun_target, clean_ai_text, flags=re.IGNORECASE)
                clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*CHAM_SEEUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*CHAM_WOLEUN_TABLE_HERE\s*\][\#\*\_\s]*', wolwun_target, clean_ai_text, flags=re.IGNORECASE)

                if count_d == 0 and "table" not in clean_ai_text.lower():
                    clean_ai_text = clean_ai_text + f"<br><br><span style='color:red; font-weight:bold;'>⚠️ (AI 표 마커 누락으로 비상 출력된 운의 흐름표)</span><br>{un_html_clean}{se_html_clean}{wol_html_clean}"

                full_content_clean = f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000;'>{clean_ai_text}<br><br>{closing_html}</div>"

                # [수정 완료] 본문 내 중복 인쇄 버튼 삭제 및 깔끔한 레이아웃 결합
                report_1_full_html = f"{cover_html}<div class='report-page'><div class='vip-inset-frame' style='border-color:#1A237E; box-sizing: border-box; padding: 20px;'><h1 style='text-align:center;'>🎯[초연 시공명리 사주풀이]</h1>{table_html}{master_bar_html}<div style='margin-top:20px;'>{full_content_clean}</div></div></div>"
                
                # [화면 출력] 1단계가 무조건 화면에 렌더링 됩니다.
                st.markdown(report_1_full_html, unsafe_allow_html=True)
                
            except Exception as e: 
                st.error(f"1단계 사주풀이 AI 연산 오류: {e}")
                st.stop() # 1단계에서 꼬이면 다음 단계로 진행하지 않도록 완벽 차단
