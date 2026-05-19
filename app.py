# ==============================================================================
# 5. 분석 가동 및 출력 (스위치 분기)
# ==============================================================================
if btn_single:
    if not u_name.strip(): st.warning("⚠️ 신청인의 이름을 입력해 주세요.")
    elif u_product == "궁합" and not p_name.strip(): st.warning("⚠️ 상대방의 이름을 입력해 주세요.")
    else:
        spinner_msg = "초연 시공명리 사주풀이 분석 중..." if u_product == "개인사주" else "💕 두 분의 시공간을 교차하여 궁합을 분석 중입니다..."
        
        # 🎯 [김집사 수정] JSON 마스터 DB 로드 (프로그램 가동 시 1회 로드)
        try:
            with open("/content/drive/MyDrive/choyeon-spacetime/choyeon_db.json", 'r', encoding='utf-8') as f:
                choyeon_db = json.load(f)
        except Exception as e:
            choyeon_db = {"wolryeong": {}, "ilju": {}}

        with st.spinner(spinner_msg):
            # ------------------------------------------------------------------
            # [공통 연산 - 신청인]
            # ------------------------------------------------------------------
            klc = KoreanLunarCalendar()
            if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
            elif u_cal == "음력(평달)": klc.setLunarDate(u_y, u_m, u_d, False)
            else: klc.setLunarDate(u_y, u_m, u_d, True)
            
            is_leap = getattr(klc, 'isIntercalary', False)
            leap_str = "윤달" if is_leap else "평달"
            
            sol_str = f"{klc.solarYear}년 {klc.solarMonth:02d}월 {klc.solarDay:02d}일"
            lun_str = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({leap_str})"
            
            curr_dt_sys = dt_mod.datetime.now()
            curr_y = curr_dt_sys.year
            curr_m = curr_dt_sys.month
            u_age = curr_y - u_y + 1
            
            base_y_idx = (curr_y - 1984) % 60
            curr_y_ganji = GAN[base_y_idx % 10] + JI[base_y_idx % 12]           
            gj = klc.getChineseGapJaString().split()
            ys, yb, ms, mb, ds, db = gj[0][0], gj[0][1], gj[1][0], gj[1][1], gj[2][0], gj[2][1]
            
            base_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0)
            hs, hb = get_time_ganji(ds, u_t, base_dt)
            gans, jjis = [hs, ds, ms, ys], [hb, db, mb, yb]
            
            time_str = f" {u_t.split('(')[0].strip()} ({hb})시" if u_t != "시간 모름" else ""
            
            def td(c, size="18px"): return f"<td class='color-{get_color(c)}' style='font-size:{size}; font-weight:900; border:1px solid #444 !important;'>{('?' if c in ['?',' ','-'] else c)}</td>"
            
            # ------------------------------------------------------------------
            # 🟢 [모드 1] 개인사주 분석 (Ver 22.0 통합본)
            # ------------------------------------------------------------------
            if u_product == "개인사주":
                components.html(f"<div style='text-align:right;'><button style='background:#2E7D32; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-family:\"Noto Serif KR\", serif;' onclick='window.parent.print()'>🖨️ 초연 사주풀이 인쇄/PDF</button></div>", height=50)
                
                ji_rel_rows = ""
                for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                    b_bot = "1px solid #444 !important" if l_idx == 3 else "none !important"
                    cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:none !important; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                    lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top:none !important;'>합충형파해</td>" if l_idx==0 else ""
                    ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

                disp_name = u_name if u_name.strip() else "홍길동"
                info_h = f"<div style='text-align:center; margin-bottom:20px;'><span style='font-size:20px; font-weight:900; color:#1A237E;'>🏮 {disp_name}님 ({u_gender}, {u_marital}, {u_age}세)</span><br><span style='font-size:16px; color:#333; font-weight:900;'>[양력: {sol_str} | 음력: {lun_str}{time_str}]</span></div>"

                table_html = f"""<table class='result-table'>
                <tr class='top-header-cell'>
                <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>구분</span></td>
                <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>시주</span></td>
                <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>일주</span></td>
                <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>월주</span></td>
                <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>년주</span></td>
                </tr>
                <tr><td class='header-cell-main' style='border:1px solid #444;'>천간합충</td>{"".join([f"<td style='border:1px solid #444;'>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])}</tr>
                <tr><td class='header-cell-main' style='border:1px solid #444;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#D50000;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(ds,ms)}</td><td style='border:1px solid #444;'>{get_ss(ds,ys)}</td></tr>
                <tr><td class='header-cell-main' style='border:1px solid #444;'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
                <tr><td class='header-cell-main' style='border:1px solid #444;'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
                <tr><td class='header-cell-main' style='border:1px solid #444;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(ds,hb)}</td><td style='border:1px solid #444;'>{get_ss(ds,db)}</td><td style='border:1px solid #444;'>{get_ss(ds,mb)}</td><td style='border:1px solid #444;'>{get_ss(ds,yb)}</td></tr>
                <tr><td class='header-cell-main' style='padding:0; border:1px solid #444;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
                {ji_rel_rows}
                <tr><td class='header-cell-main' style='border:1px solid #444 !important;'>십이운성</td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
                <tr><td class='header-cell-main' style='border:1px solid #444 !important;'>십이신살</td>{"".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
                <tr><td class='header-cell-main' style='border:1px solid #444 !important;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis)) if get_general_shinsal_filtered(i, gans, jjis) else '-'}</td>" for i in range(4)])}</tr>
                </table>"""
                
                calc_gyukgook, gyukgook_detail = get_gyukgook_detailed(ds, ys, ms, hs, mb)

                gen_shinsal_list = []
                for i in range(4):
                    raw_tags = get_general_shinsal_filtered(i, gans, jjis)
                    for tag in raw_tags:
                        if ">" in tag and "<" in tag: gen_shinsal_list.append(tag.split('>')[1].split('<')[0])
                shinsal_str = ", ".join(list(dict.fromkeys(gen_shinsal_list))) if gen_shinsal_list else "특이 신살 없음"
                
                s12_list = [get_12_shinsal(yb, j) for j in jjis if get_12_shinsal(yb, j) != "-"]
                s12_str = ", ".join(list(dict.fromkeys(s12_list))) if s12_list else "특이 12신살 없음"
          
                samhyung_warn = ""
                has_in, has_sa, has_shin = '寅' in jjis, '巳' in jjis, '申' in jjis
                if sum([has_in, has_sa, has_shin]) == 2:
                    missing = [x for x, has in zip(['寅','巳','申'], [has_in, has_sa, has_shin]) if not has][0]
                    samhyung_warn += f"원국에 인사신(寅巳申) 중 2글자가 있어 가형(假刑) 상태입니다. 운에서 '{missing}'이/가 들어올 때 삼형살이 완성되니 관재구설/수술수/배신에 강력히 주의 요망. "
                has_chuk, has_sul, has_mi = '丑' in jjis, '戌' in jjis, '未' in jjis
                if sum([has_chuk, has_sul, has_mi]) == 2:
                    missing = [x for x, has in zip(['丑','戌','未'], [has_chuk, has_sul, has_mi]) if not has][0]
                    samhyung_warn += f"원국에 축술미(丑戌未) 중 2글자가 있어 가형(假刑) 상태입니다. 운에서 '{missing}'이/가 들어올 때 삼형살이 완성되니 관재구설/수술수/배신에 강력히 주의 요망. "
                if not samhyung_warn: samhyung_warn = "해당 없음"

                counts = {"목":0,"화":0,"토":0,"금":0,"수":0}
                for char in gans + jjis:
                    if char != "?": counts[get_color(char)] += 1
                
                guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
                guiin_str = guiin_map.get(ds, '없음')
                    
                adj_mins = get_total_time_adjustment(base_dt)
                utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
                order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
                direction_str = "순행" if order == 1 else "역행"
                calc_d = get_daeun_su_accurate(utc_dt, order)
                
                n_gong = calculate_gongmang(ys, yb)
                i_gong = calculate_gongmang(ds, db)
                
                master_bar_html = f"<div style='border:2px solid #3E2723; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap;'><div>⏳ 대운수: {calc_d}</div><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin_str}</div><div>🎯 공망: [년] {n_gong} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; [일] {i_gong}</div></div>"
                
                daewun_info = []
                un_html = f"<h3 style='color:#1A237E; margin-top:40px;'>11. 운의 흐름</h3><div style='margin-bottom:10px; font-weight:bold;'>[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(10):
                    val, c, j = i*10+calc_d, GAN[(GAN.index(ms)+(i+1)*order)%10] if ms in GAN else "-", JI[(JI.index(mb)+(i+1)*order)%12] if mb in JI else "-"
                    daewun_info.append(f"{val}세:{c}{j}")
                    is_active = val <= u_age < val+10
                    bg_col = "#FFF9C4" if is_active else "transparent"
                    b_left = "1px solid #ccc" if i != 9 else "none"
                    un_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{val}세</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,c)}</div><div class='color-{get_color(c)}' style='font-size:16px; font-weight:900;'>{c}</div><div class='color-{get_color(j)}' style='font-size:16px; font-weight:900;'>{j}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,j)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,j)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, j)}</div></div>"
                un_html += "</div>"
                daewun_info_str = ", ".join(daewun_info)

                cur_dw_idx = max(0, (u_age - calc_d) // 10)
                dw_g_cur = GAN[(GAN.index(ms) + (cur_dw_idx+1)*order)%10] if ms in GAN else "-"
                dw_j_cur = JI[(JI.index(mb) + (cur_dw_idx+1)*order)%12] if mb in JI else "-"
                current_daewun_age = cur_dw_idx * 10 + calc_d
                
                start_year = u_y + current_daewun_age - 1
                
                sewun_info = []
                se_html = f"<div style='margin-top:20px; margin-bottom:10px; font-weight:bold;'>[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(10):
                    ty = start_year + i
                    tage = current_daewun_age + i
                    base = (ty - 1984) % 60
                    tc, tj = GAN[base % 10], JI[base % 12]
                    sewun_info.append(f"{ty}년({tc}{tj})")
                    is_cur_yr = (ty == curr_y)
                    bg_col = "#E1F5FE" if is_cur_yr else "transparent"
                    b_left = "1px solid #ccc" if i != 9 else "none"
                    se_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; line-height:1.2; border-bottom:1px solid #ccc;'>{ty}년<br>({tage}세)</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div></div>"
                se_html += "</div>"
                sewun_info_str = ", ".join(sewun_info)

                wol_gans = ["己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚"]
                wol_jis = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]
                cur_wol_g = wol_gans[curr_m - 1]
                cur_wol_j = wol_jis[curr_m - 1]
                
                wol_html = f"<div style='margin-top:20px; margin-bottom:10px; font-weight:bold;'>[ 월운의 흐름 ({curr_y}년도 양력기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(12):
                    tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
                    is_cur_m = (tm == curr_m)
                    bg_col = "#E8F5E9" if is_cur_m else "transparent"
                    b_left = "1px solid #ccc" if i != 11 else "none"
                    wol_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{tm}월</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div></div>"
                wol_html += "</div>"
                
                closing_html = f"""<div style='margin-top: 30px;'>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자(命)'는 태어날 때 부여받은 변하지 않는 '바코드(bar-code)'와 같지만, 우리가 살아가며 마주하는 '스캐너(scanner)'인 '운(運)'은 늘 변화하며 흐릅니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 전통명리와의 인연'이 <b>{disp_name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 전통명리의 지혜와 궁금증이 있으시면 언제든 '초연 전통명리 연구소의 문'을 두드려 주십시오.</p>
<p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
<div style='text-align: right; margin-top: 30px;'>
<span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
</div>
</div>"""

                age_prompt = ""
                if u_age < 20:
                    age_prompt = "내담자는 [청소년기(10대)]입니다. '4. 학업·진학운'과 '3. 부모·형제운'을 최우선으로 가장 상세히 분석하고, 재성운(재물)/사업운은 간략히 축소하십시오."
                elif 20 <= u_age < 40:
                    age_prompt = "내담자는 [청년기(20~30대)]입니다. '5. 적성·직업운'과 '6. 결혼·자녀운' 등 사회적 자립과 연애/혼인 과정을 상세히 통변하십시오."
                elif 40 <= u_age < 60:
                    age_prompt = "내담자는 [중장년기(40~50대)]입니다. 인생의 황금기이므로 '9. 재성운(재물)'과 '8. 관직·명예운(사업/승진)'에 통변의 화력을 집중하여 가장 길고 상세하게 서술하십시오."
                else:
                    age_prompt = "내담자는 [노년기(60대 이상 시니어)]입니다. '10. 건강운' 및 대운/세운 통변 시 노인성 질환, 관절, 혈관 예방 등 건강 관리를 최우선으로 깊이 다루고, 재산의 안정적 유지에 대해 상세히 통변하십시오."

                gender_prompt = ""
                if u_gender == "남성":
                    gender_prompt = "내담자는 [남성]입니다. 육친 해석 시 재성(아내/재물)과 관성(자녀/사회적 명예)의 동태를 남성의 생애 주기와 가장의 역할에 맞춰 현실적으로 통변하십시오."
                else:
                    gender_prompt = "내담자는 [여성]입니다. 육친 해석 시식상(자녀/표현력)과 관성(남편/직장)의 조화를 중심으로 풀되, 현대 사회 여성의 독립적 사회 활동과 성취를 비중 있게 강조하십시오."

                dw_start_age = current_daewun_age
                dw_mid_age = current_daewun_age + 4
                dw_mid2_age = current_daewun_age + 5
                dw_end_age = current_daewun_age + 9
                
                past_months_html = "<span class='sub-title'>▶ 지나온 각 과거 월운 요약</span>\n"
                for m in range(1, curr_m):
                    g = wol_gans[m-1]
                    j = wol_jis[m-1]
                    if m == 1:
                        past_months_html += f"<span class='sub-title'>• {curr_y}년 1월 ({g}{j}월: 작년도 하반기 연장선):</span>\n"
                    elif m == 2:
                        past_months_html += f"<span class='sub-title'>• {curr_y}년 2월 ({g}{j}월: 새로운 시작):</span>\n"
                    else:
                        past_months_html += f"<span class='sub-title'>• {curr_y}년 {m}월 ({g}{j}월):</span>\n"

                # 🎯 [김집사 핵심 투입구간] JSON에서 키값(월주는 끝에 '월' 붙임)으로 명리 정보 추출
                w_key = f"{ms}{mb}월"
                i_key = f"{ds}{db}"
                
                w_core = choyeon_db.get("wolryeong", {}).get(w_key, "시공간 데이터 준비 중")
                i_core = choyeon_db.get("ilju", {}).get(i_key, "데이터 준비 중")
                
                # 🎯 황금 문장 HTML 조립
                choyeon_golden_text = f"""
<p style='text-indent: 15px; margin-top: 15px; line-height: 1.8; font-size: 16px; color: #1A237E; font-weight: bold;'>
<b>{disp_name}</b>님은 '{w_core}'의 시공간에서, '{i_core}'의 성품을 가지고 태어나셨습니다.
</p>
<p style='text-indent: 15px; line-height: 1.8;'>
사주 구조의 핵심을 나타내는 격국(格局)은 <b>{gyukgook_detail}</b>
</p>
"""

                db_header = (
                    f"[시스템 강제 시간 인식: 현재 시점은 {curr_y}년 {curr_m}월 입니다. 절대 과거나 미래를 현재로 착각하지 마십시오.]\n\n"
                    "당신은 명리심리상담사 1급 자격을 갖춘 **'초연 박사'**입니다. \n\n"
                    "[🚨 전체 통변 절대 원칙 - 반드시 숙지할 것]\n"
                    f"1. 타겟 맞춤형 통변: 모든 해설과 조언은 내담자의 연령과 성별({u_age}세 {u_gender})이 겪을 수 있는 현실적 상황(직장, 가정, 재물, 육아, 노후 등)에 철저히 맞추어 현대적인 구어체로 작성하십시오.\n"
                    "2. 명리 용어 사용 금지: 내담자가 이해하기 어려운 한자어나 전문 명리 용어(예: 비견, 겁재, 입고, 개고, 지장간, 인종법, 묘고 등)를 본문 에세이에 직접 노출하지 마십시오. 반드시 일상적이고 심리적인 언어로 치환하여 풀어내십시오.\n\n"
                    "[기본 분석 데이터 - 박사님 정밀 DB 추출본]\n"
                    f"- 내담자 성함: {disp_name}\n"
                    f"- 나이 / 성별: {u_age}세 / {u_gender}\n"
                    f"- 혼인 여부: {u_marital}\n"
                    f"- 공망 팩트: [년주] {n_gong}, [일주] {i_gong}\n\n"
                )

                prompt = f"""
{db_header}

[🚨 가독성 혁명 및 문단 통제 엄명]
1. 모든 통변 에세이 문장은 반드시 <p>내용</p> 태그로 감싸십시오. (CSS에서 20px 들여쓰기가 자동 적용됩니다.)
2. 문장이 길어지거나 문맥이 전환되는 적절한 지점에서는 절대로 글을 한 덩어리로 뭉치지 말고 반드시 </p><p>를 사용하여 줄바꿈(단락 나누기)을 집행하십시오.
3. [특수기호 소제목 강제 룰] 아래의 기호(1), 2), ▶, •, ◈)가 들어간 문장은 절대 들여쓰기를 해선 안 됩니다. 반드시 아래의 지정된 태그 템플릿을 토씨 하나 틀리지 말고 복사해서 쓰십시오!
   <span class='sub-title'>1) 겉으로 드러난 성격</span>
   <span class='sub-title'>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</span>
   <span class='sub-title'>• {dw_start_age}세~{dw_mid_age}세 ({dw_g_cur}{dw_j_cur} 대운):</span>
   <span class='sub-title'>◈ 나를 돕는 에너지와 색상:</span>
4. 🚫 절대 금지: 마크다운 문법인 별표 2개(**)를 사용하여 글씨를 굵게 만드는 행위를 전면 금지합니다. 모든 소제목은 <span class='sub-title'> 태그에 의해 자동으로 굵게 처리되므로, 당신이 임의로 **를 넣지 마십시오.

[🚨 3D 입체 통변 및 육친 강제 지시]
1번~11번 모든 항목은 평면적 해석을 금지하며, 반드시 [관계, 심리적 내면, 사회적 영역(직업/재물)] 3차원 관점을 융합하여 풀이하십시오.
현재 혼인 상태: '{u_marital}'. 절대 '육친적'이라는 단어를 쓰지 말고 "인간관계 측면에서 살펴보면" 등으로 순화하십시오.

[🔥 내담자 맞춤형 정밀 타겟팅 룰 (반드시 엄수)]
- {age_prompt}
- {gender_prompt}

[🌟 대중 친화적 하이브리드 통변 강제 지시]
- [천간 합/충 짝짓기 오류(환각) 절대 금지] 천간의 합(合)은 '甲己, 乙庚, 丙辛, 丁壬, 戊癸' 이고, 천간의 충(沖)은 '甲庚, 乙辛, 丙壬, 丁癸' 뿐입니다. 절대 '갑경합', '을기충' 등 글자 짝을 잘못 지어 명리학에 없는 거짓 용어를 지어내지 마십시오.
- 모든 명리 용어(십성, 신살, 묘유충 등)는 절대로 단독으로 쓰지 마십시오.
- 반드시 [대중이 이해하기 쉬운 현대적 구어체 표현] + (명리용어) 형태로 병기하십시오.
- [한자 100% 표기 규칙] 반드시 '甲木', '己土', '亥水', '甲庚충' 등 100% 한자(漢字)로 표기하십시오.
- [궁성 스토리텔링 강제] 합형충파해 설명 시 각 지지(자리)가 상징하는 육친과 의미를 엮어 풀이하십시오.
- [십이운성 3D 결합 강제] 십성(육친) 통변 시, 반드시 해당 기둥의 십이운성(十二運星)이 부여하는 에너지의 강약과 상태를 결합하여 입체적으로 통변하십시오.

[🚨 핵심 팩트 강제 지시]
- 공망(空亡) 팩트: [년주: {n_gong}, 일주: {i_gong}] -> 년공망은 사회적/초년 결핍, 일공망은 개인적/배우자 결핍으로 나누어 설명하십시오.
- 부모운 특수 지시: 사주 원국에서 부모를 상징하는 기운이 약하거나 극을 받는다면, 이를 '초년 시절의 뼈아픈 상실이나 짊어져야 했던 삶의 무게' 등으로 통변에 깊이 녹여내십시오.
- 건강운 시작 전 지시: '10. 건강운'을 시작하기 전, 일반인이 이해하기 쉽게 오행의 생극제화 원리를 1~2줄로 비유적으로 먼저 설명하십시오.
- 일반신살: [{shinsal_str}] / 12신살: [{s12_str}]
- [경계령] 분석 순서는 [합 ➡️ 형 ➡️ 충 ➡️ 파 ➡️ 해] 순서를 엄수.
- [과거 대운/세운/월운 전수 분석 및 3줄 요약 규칙] 과거 운을 분석할 때는 첫 번째 대운부터 현재 직전 대운까지 압축하여 '반드시 정확히 3줄(3문장)'로 명쾌하게 요약하여 서술하십시오.
- [조언 및 개운비법 논리성 강제] '12. 삶을 바꾸는 지혜로운 조언'과 '개운 비법' 파트는 용신 오행을 논리적 근거로 삼아 서술하십시오.
- 통변 시 가장 강조할 명리적 단어나 문구는 반드시 ' ' (작은따옴표)로 묶어 시각적으로 강조하십시오.

실제 대운 흐름: {daewun_info_str}
실제 세운 흐름: {sewun_info_str}
사주: {ys}{yb}년 {ms}{mb}월 {ds}{db}일 {hs}{hb}시

[출력 템플릿 - 이 목차명과 구조를 100% 동일하게 복사하여 출력할 것. 절대 내용 임의 추가 금지!]
<h3 style='color:#1A237E;'>1. 사주팔자 구조 분석</h3>
<div class='content-box-loose'>
<span class='sub-title'>1) 타고난 삶의 무대와 기본 성향 (격국)</span>
{choyeon_golden_text}
(※ AI 특별 지시: 위 제시된 자의형상과 격국의 시적인 의미를 바탕으로, 일반 내담자가 현실에서 어떤 강점과 성향으로 나타나는지 비유를 들어 상세한 해설을 덧붙여 주십시오.)
<span class='sub-title'>2) 내 삶의 온도와 에너지 균형 (조후/억부/용신)</span>
<span class='sub-title'>3) 사주팔자의 역동적 관계 분석 (합형충파해/진술축미)</span>
</div>
<h3 style='color:#1A237E;'>2. 성격</h3>
<div class='content-box-loose'>
<span class='sub-title'>1) 겉으로 드러난 성격</span>
<span class='sub-title'>2) 감추어진 진짜 속마음</span>
</div>
<h3 style='color:#1A237E;'>3. 부모·형제운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>4. 학업·진학운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>5. 적성·직업운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>6. 결혼·자녀운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>7. 사업운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>8. 관직·명예운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>9. 재성운</h3><div class='content-box-loose'></div>
<h3 style='color:#1A237E;'>10. 건강운</h3><div class='content-box-loose'></div>

[DAEWUN_TABLE_HERE]
<div class='content-box-loose'>
<span class='sub-title'>▶ 지나온 과거 대운 분석</span>
<span class='sub-title'>▶ 현재 대운 전반기 상세 분석 ({dw_start_age}세~{dw_mid_age}세)</span>
<span class='sub-title'>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</span>
</div>
[SEWUN_TABLE_HERE]
<div class='content-box-loose'>
<span class='sub-title'>▶ 지나온 과거 세운 분석</span>
<span class='sub-title'>▶ 올해({curr_y}년 {curr_y_ganji}년) 세운 전반기(양력 2월~7월 말) 상세 분석</span>
<span class='sub-title'>▶ 올해({curr_y}년 {curr_y_ganji}년) 세운 후반기(양력 8월~내년 1월 말) 상세 분석</span>
</div>
[WOLWUN_TABLE_HERE]
<div class='content-box-loose'>
{past_months_html}
<span class='sub-title'>▶ 이번 달({curr_m}월 {cur_wol_g}{cur_wol_j}월) 전반기 (양력 5일~19일) 상세 분석</span>
<span class='sub-title'>▶ 이번 달({curr_m}월 {cur_wol_g}{cur_wol_j}월) 후반기 (양력 20일~익월 4일) 상세 분석</span>
</div>

<h3 style='color:#1A237E; margin-top:30px;'>12. 삶을 바꾸는 지혜로운 조언</h3>
<div class='content-box-loose'>
<span class='sub-title'>◈ 나를 돕는 에너지와 색상:</span>
<span class='sub-title'>◈ 신체 밸런스와 에너지 관리:</span>
<span class='sub-title'>◈ 공간의 흐름과 방위의 지혜:</span>
<span class='sub-title'>◈ 재능 효율을 높이는 직업적 지혜:</span>
<span class='sub-title'>◈ 더 나은 내일을 위한 절제의 미학:</span>
<div style='margin-top:20px; margin-bottom:10px;'><span style='color:#1A237E; font-weight:900;'>[초연 시공명리 특별 개운 비법]</span></div>
<span class='sub-title'>◈ 수호 천사의 기운:</span>
<span class='sub-title'>◈ 백년해로의 기운:</span>
<span class='sub-title'>◈ 행운에 따른 기운:</span>
</div>
"""
                try:
                    res = model.generate_content(prompt)
                    ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                    
                    ai_text = ai_text.replace("[DAEWUN_TABLE_HERE]", un_html).replace("[SEWUN_TABLE_HERE]", se_html).replace("[WOLWUN_TABLE_HERE]", wol_html)
                    
                    if un_html not in ai_text:
                        ai_text = un_html + se_html + wol_html + "<div style='color:red;'>⚠️ AI가 템플릿 마커를 누락하여 표가 최상단에 출력되었습니다.</div>" + ai_text

                    report_1_full_html = f"""<div class='report-page'>
<div class='vip-inset-frame' style='border-color:#1A237E;'>
<h1 style='text-align:center;'>🎯[초연 시공명리 사주풀이]</h1>
{info_h}
{table_html}
{master_bar_html}
<div style='margin-top:20px;'>
{ai_text}
{closing_html}
</div>
</div>
</div>"""
                    st.markdown(report_1_full_html, unsafe_allow_html=True)
                    
                except Exception as e: 
                    st.error(f"AI 연산 오류: {e}")

            # ------------------------------------------------------------------
            # 🔴 [모드 2] 궁합 분석 (Ver 509.0 궁합 엔진 단독 이식)
            # ------------------------------------------------------------------
            elif u_product == "궁합":
                p_klc = KoreanLunarCalendar()
                if p_cal == "양력": p_klc.setSolarDate(p_y, p_m, p_d)
                elif p_cal == "음력(평달)": p_klc.setLunarDate(p_y, p_m, p_d, False)
                else: p_klc.setLunarDate(p_y, p_m, p_d, True)
                
                p_in_dt = dt_mod.datetime(p_klc.solarYear, p_klc.solarMonth, p_klc.solarDay, 12, 30)
                p_gj = p_klc.getChineseGapJaString().split()
                p_ys, p_yb, p_ms, p_mb, p_ds, p_db = p_gj[0][0], p_gj[0][1], p_gj[1][0], p_gj[1][1], p_gj[2][0], p_gj[2][1]
                try: p_hs, p_hb = get_time_ganji(p_ds, p_t, p_in_dt)
                except: p_hs, p_hb = "?", "?"
                
                m_pillars, f_pillars = ([hs, ds, ms, ys], [hb, db, mb, yb]), ([p_hs, p_ds, p_ms, p_ys], [p_hb, p_db, p_mb, p_yb])
                
                m_ctx = {'u_name': u_name, 'dc': ds}
                f_ctx = {'u_name': p_name, 'dc': p_ds}
                
                if u_gender == "여성":
                    m_pillars, f_pillars = f_pillars, m_pillars
                    m_ctx, f_ctx = f_ctx, m_ctx
                
                gh_engine = UniversalPrintableGunghap(u_name, p_name, m_pillars, f_pillars)
                gh_engine.run_universal_logic()
                
                def draw_saju_table(gans, jjis, name_str, title_str):
                    c_gans = "".join([f"<td class='color-{get_color(g)}' style='font-size:20px; font-weight:900;'>{g}</td>" for g in gans])
                    c_jjis = "".join([f"<td class='color-{get_color(j)}' style='font-size:20px; font-weight:900;'>{j}</td>" for j in jjis])
                    return f"""
                    <div style='margin-bottom: 20px;'>
                        <div style='font-size: 18px; font-weight: 900; color: #1A237E; margin-bottom: 5px;'>🏮 {title_str} : {name_str}님</div>
                        <table class='result-table' style='width: 100%;'>
                            <tr class='top-header-cell'><td>시주</td><td>일주</td><td>월주</td><td>년주</td></tr>
                            <tr>{c_gans}</tr>
                            <tr>{c_jjis}</tr>
                        </table>
                    </div>
                    """
                
                tables_html = "<div class='report-page'><div class='vip-inset-frame'>"
                tables_html += f"<div style='text-align:center; border-bottom:4px double #3E2723; padding-bottom:15px; margin-bottom:20px;'><h1 style='margin:0; color:#3E2723; font-weight: 900;'>🗝️ 두 사람의 사주 명조</h1></div>"
                if u_gender == '남성':
                    tables_html += draw_saju_table(gh_engine.m_g, gh_engine.m_j, u_name, "남명 원국")
                    tables_html += draw_saju_table(gh_engine.f_g, gh_engine.f_j, p_name, "여명 원국")
                else:
                    tables_html += draw_saju_table(gh_engine.m_g, gh_engine.m_j, p_name, "남명 원국")
                    tables_html += draw_saju_table(gh_engine.f_g, gh_engine.f_j, u_name, "여명 원국")
                tables_html += "</div></div>"
                
                try:
                    ai_text = gh_engine.generate_ai_report(m_ctx, f_ctx)
                    gunghap_html = gh_engine.get_graphic_html(ai_text)
                    
                    st.markdown(tables_html, unsafe_allow_html=True)
                    st.markdown(gunghap_html, unsafe_allow_html=True)
                    
                    print_btn_html = "<div class='no-print' style='text-align: center; margin: 40px 0;'><button onclick='window.focus(); window.print()' style='padding: 12px 35px; background-color: #3E2723; color: white; font-weight: 900; border-radius: 5px; cursor: pointer;'>궁합 감명서 인쇄 / PDF 저장</button></div>"
                    components.html(print_btn_html, height=100)
                except Exception as e:
                    st.error(f"궁합 AI 구동 실패 오류: {e}")
