# ==============================================================================
# 5. 분석 가동 및 출력 (스위치 분기)
# ==============================================================================
if btn_single:
    if not u_name.strip(): st.warning("⚠️ 신청인의 이름을 입력해 주세요.")
    elif u_product == "궁합" and not p_name.strip(): st.warning("⚠️ 상대방의 이름을 입력해 주세요.")
    else:
        spinner_msg = f"⏳ [초연 시공명리 개인 사주풀이({APP_VERSION}) 분석 중....]" if u_product == "개인사주" else f"💕 [초연 시공명리 궁합 사주풀이 분석({APP_VERSION}) 중....]"
        
        # 🎯 완벽하게 정렬된 로딩 스피너 및 메인 로직 구역
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
            
            intro_html = f"""
<div style='font-family: "Noto Serif KR", serif; font-size: 16px; font-weight: 600; color: #333; text-align: justify; line-height: 1.8; padding-bottom: 0px; margin-bottom: 25px;'>
    <p style='text-indent: 15px; margin: 0 0 5px 0;'>기존 전통 명리학 사주풀이는 1년에 한 번 돌아오는 '12월지'와 '60일주'의 조합으로 720가지의 유형으로 시작합니다만,</p>
    <p style='text-indent: 15px; margin: 0 0 5px 0;'>본 초연 시공명리 사주풀이는 5년에 한 번 돌아오는 '60월령'과 '60일주'의 조합으로 3,600가지의 유형으로 보다 더 정밀한 분석이 가능합니다.</p>
    <p style='text-indent: 15px; margin: 0;'>기존 전통명리학에 비교하면 '5배', 요즘 유행하는 MBTI의 16가지 유형과 비교하면 무려 '225배' 더 세분화된 정밀한 사주풀이 분석입니다.</p>
</div>
"""
            # ------------------------------------------------------------------
            # [모드 1] 개인사주 분석 (렌더링 순서 통제 및 폰트업 완료)
            # ------------------------------------------------------------------
            if u_product == "개인사주":
                past_months_html = ""
                p_icon = "♂️" if u_gender == "남성" else "♀️"
                p_color = "#1A237E" if u_gender == "남성" else "#D50000"
                today_str = (dt_mod.datetime.utcnow() + dt_mod.timedelta(hours=9)).strftime("%Y년 %m월 %d일")
                
                # 🚨 표지 및 인쇄 버튼 생성 (화면 출력은 보류)
                cover_html = f"""
                <div class='report-page cover-page' style='padding:0; margin:0 auto; background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); display:flex; flex-direction:column; justify-content:center; align-items:center; min-height:100vh; page-break-after: always; -webkit-print-color-adjust: exact;'>
                    <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 85%; max-width: 750px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
                        <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                            <h1 style='font-size: 32px; color: #1A237E; font-weight: 900; margin:0; font-family:"Malgun Gothic", sans-serif;'>🏮 초연 시공명리 사주팔자 풀이</h1>
                        </div>
                        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>
                            <h2 style='font-size: 24px; font-weight: 900; color: {p_color}; margin-bottom: 20px; font-family:"Malgun Gothic", sans-serif;'>{p_icon} 신청인 : {u_name} 님</h2>
                            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                                <p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p>
                                <p style='margin: 5px 0 0 0; color: #D50000; white-space: nowrap;'>{time_str}</p>
                            </div>
                        </div>
                        <p style='font-size: 18px; margin-top: 50px; font-weight: bold;'>{today_str}</p>
                        <p style='font-size: 22px; font-weight: 900; color: #1A237E; margin-top: 20px; font-family:"Malgun Gothic", sans-serif;'>초연 시공명리 연구소</p>
                    </div>
                </div>
                """
                print_btn_html = f"<div class='no-print' style='text-align:right;'><button style='background:#2E7D32; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-family:\"Noto Serif KR\", serif;' onclick='window.parent.print()'>🖨️ 초연 사주풀이 인쇄/PDF</button></div>"
                
                # 🚨 사주 원국표 생성 (합충형파해 복원, 폰트 14px 적용, 화면 출력은 보류)
                ji_rel_rows = ""
                for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                    b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                    b_top = "0px solid transparent !important"
                    cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                    lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                    ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

                disp_name = u_name if u_name.strip() else "홍길동"
                info_h = f"<div style='text-align:center; font-family:\"Malgun Gothic\", sans-serif; margin-bottom:15px; line-height:1.5;'><span style='font-size:18px; font-weight:900; color:{p_color}; white-space:nowrap;'>{p_icon} {disp_name}님 ({u_gender}, {u_marital}, {u_age}세)</span><br><span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span></div>"

                table_html = f"""<div style='text-align:center; margin-bottom:10px;'>{info_h}</div>
<table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
<tr class='top-header-cell'>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>구분</td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>시주</td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>일주</td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>월주</td>
<td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>년주</td>
</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간합충</td>{"".join([f"<td style='border:1px solid #444;'>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(ds,ms)}</td><td style='border:1px solid #444;'>{get_ss(ds,ys)}</td></tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(ds,hb)}</td><td style='border:1px solid #444;'>{get_ss(ds,db)}</td><td style='border:1px solid #444;'>{get_ss(ds,mb)}</td><td style='border:1px solid #444;'>{get_ss(ds,yb)}</td></tr>
<tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
{ji_rel_rows}
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이운성</td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이신살</td>{"".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis, u_gender)) if get_general_shinsal_filtered(i, gans, jjis, u_gender) else '-'}</td>" for i in range(4)])}</tr>
</table>
"""
                calc_gyukgook, gyukgook_detail = get_gyukgook_detailed(ds, ys, ms, hs, mb)

                gen_shinsal_list = []
                for i in range(4):
                    raw_tags = get_general_shinsal_filtered(i, gans, jjis, u_gender)
                    for tag in raw_tags:
                        if ">" in tag and "<" in tag: gen_shinsal_list.append(tag.split('>')[1].split('<')[0])
                shinsal_str = ", ".join(list(dict.fromkeys(gen_shinsal_list))) if gen_shinsal_list else "특이 신살 없음"
                
                s12_list = [get_12_shinsal(yb, j) for j in jjis if get_12_shinsal(yb, j) != "-"]
                s12_str = ", ".join(list(dict.fromkeys(s12_list))) if s12_list else "특이 12신살 없음"
          
                samhyung_warn = ""
                has_in, has_sa, has_shin = '寅' in jjis, '巳' in jjis, '申' in jjis
                if sum([has_in, has_sa, has_shin]) == 2:
                    missing = [x for x, has in zip(['寅','巳','申'], [has_in, has_sa, has_shin]) if not has][0]
                    samhyung_warn += f"원국에 인사신 중 2글자가 있어 가형 상태입니다. 운에서 '{missing}'이 들어올 때 삼형살이 완성되니 주의 요망. "
                has_chuk, has_sul, has_mi = '丑' in jjis, '戌' in jjis, '未' in jjis
                if sum([has_chuk, has_sul, has_mi]) == 2:
                    missing = [x for x, has in zip(['丑','戌','未'], [has_chuk, has_sul, has_mi]) if not has][0]
                    samhyung_warn += f"원국에 축술미 중 2글자가 있어 가형 상태입니다. 운에서 '{missing}'이 들어올 때 삼형살이 완성되니 주의 요망. "
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
                
                cur_samjae = get_samjae(yb, curr_y_ganji[1])
                samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"
                
                master_bar_html = f"<div style='border:2px solid #3E2723; margin-top:20px; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap;'><div>⏳ 대운수: {calc_d}</div><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin_str}</div><div>🎯 공망: [일] {i_gong}</div><div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div></div>"                
                
                daewun_info = []
                un_html = f"<div style='margin-top:20px; margin-bottom:10px; font-weight:bold;'>[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
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
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드와 같지만, 우리가 살아가며 마주하는 스캐너인 운은 늘 변화하며 흐릅니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 초연 전통명리와의 인연이 <b>{disp_name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 나침반이 되기를 진심으로 기원합니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 전통명리의 지혜와 궁금증이 있으시면 언제든 초연 전통명리 연구소의 문을 두드려 주십시오.</p>
<p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
<div style='text-align: right; margin-top: 30px;'>
<span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
</div>
</div>"""

                base_gans_list = [hs, ds, ms, ys]
                base_jjis_list = [hb, db, mb, yb]

                won_guk_vaults = []
                for attacker in base_jjis_list:
                    won_guk_vaults.extend(check_vault_status(base_gans_list, base_jjis_list, attacker))
                won_guk_vaults = list(dict.fromkeys(won_guk_vaults)) 
                won_guk_vaults_str = ", ".join(won_guk_vaults) if won_guk_vaults else "해당 없음"

                daewun_vaults = check_vault_status(base_gans_list, base_jjis_list, dw_j_cur)
                sewun_vaults = check_vault_status(base_gans_list, base_jjis_list, curr_y_ganji[1])
                wolwun_vaults = check_vault_status(base_gans_list, base_jjis_list, cur_wol_j)

                hang_un_vaults = list(dict.fromkeys(daewun_vaults + sewun_vaults + wolwun_vaults))
                hang_un_vaults_str = ", ".join(hang_un_vaults) if hang_un_vaults else "해당 없음"

                age_prompt = ""
                if u_age < 20:
                    age_prompt = "내담자는 청소년기(10대)입니다. 학업 진학운과 부모 형제운을 최우선으로 상세히 분석하고 재물 사업운은 축소하십시오."
                elif 20 <= u_age < 40:
                    age_prompt = "내담자는 청년기(20~30대)입니다. 적성 직업운과 결혼 자녀운 등 사회적 자립과 혼인 과정을 상세히 통변하십시오."
                elif 40 <= u_age < 60:
                    age_prompt = "내담자는 중장년기(40~50대)입니다. 재성운과 관직 명예운에 집중하여 상세하게 서술하십시오."
                else:
                    age_prompt = "내담자는 노년기(60대 이상)입니다. 건강운 및 대운 세운 통변 시 건강 관리를 최우선으로 깊이 다루십시오."

                gender_prompt = ""
                if u_gender == "남성":
                    gender_prompt = "남성 내담자입니다. 배우자운(재성)과 자식운(관성)을 남명 이론에 입각하여 해석하십시오."
                else:
                    gender_prompt = "여성 내담자입니다. 배우자운(관성)과 자식운(식상)을 여명 이론에 입각하여 해석하십시오."

                # 🎯 [Ver 30.3: 하드코딩 DB 완벽 연동] 
                w_key = f"{ms}{mb}".strip()
                i_key = f"{ds}{db}".strip()

                w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
                i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
                struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
                s_name, s_type, s_desc = struct_data[0], struct_data[1], struct_data[2]

                choyeon_golden_text = f"""
<div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000; margin-bottom: 20px;'>
    <p style='text-indent: 15px; margin-bottom: 5px;'>
        <b>{disp_name}님</b>은 '{w_val}'의 시공간에서, '{i_val}'의 성품을 가지고 태어나셨습니다.
    </p>
</div>
"""
                dw_start_age = current_daewun_age
                dw_mid_age   = current_daewun_age + 4
                dw_mid2_age  = current_daewun_age + 5
                dw_end_age   = current_daewun_age + 9
                                
                db_header = (
                    f"[시스템 강제 시간 인식: 현재 시점은 {curr_y}년 {curr_m}월 입니다.]\n"
                    "당신은 명리심리상담사 1급 자격을 갖춘 초연 박사입니다. \n"
                    f"- 내담자 성함: {disp_name}\n"
                    f"- 나이 / 성별: {u_age}세 / {u_gender}\n"
                    f"- marital_status: {u_marital}\n"
                    f"- 타고난 심리 구조 팩트: {s_name} ({s_type} - {s_desc})\n"
                    f"- 공망 팩트: [년주] {n_gong}, [일주] {i_gong}\n"
                    f"- 올해({curr_y}년) 삼재 여부: {cur_samjae}\n"  
                    f"- 원국 내부 묘고(입고/개고) 작용: {won_guk_vaults_str}\n"
                    f"- 현재 행운(대/세/월운) 외부 충격에 의한 묘고 작용: {hang_un_vaults_str}\n"
                    f"🚨 [AI 환각 및 UI 파괴 원천 차단 절대 규칙]\n"
                    f"1. 원국에 없는 기운 창조 금지: 내담자의 사주에 없는 십성(예: 무인성일 경우)을 마치 있는 것처럼 지어내어 통변하지 마십시오.\n"
                    f"2. 괄호 병기 금지: 에세이 작성 시 '(일주 공망)', '(년주 공망)', '(인성)' 등의 명리 용어나 한자를 괄호 안에 병기하는 행위를 엄격히 금지합니다.\n"
                    f"3. 간지 추측 금지: 과거 월운 분석 시 '1월(丁丑월)'처럼 한자 간지를 임의로 추측해 적지 말고 오직 '1월:', '2월:' 로만 표기하십시오.\n"
                    f"4. HTML 훼손 금지: 에세이 도중 </div> 태그를 임의로 닫거나 마크다운 기호를 남발하여 전체 레이아웃을 부수지 마십시오.\n"
                    f"5. 🚨 이름 및 사주정보 중복 출력 금지: 결과물 상단에 '{disp_name}님 (남성, ...)' 식의 제목이나 생년월일 정보를 절대 반복해서 적지 마십시오.\n"
                )

                if u_gender == '남성':
                    yukchin_rule = f"""
🚨 [육친 통변 특수부대 절대 규칙 (남성용)]: 
- 본 내담자는 남성(현재 상태: {u_marital})입니다. 아래의 명리학적 육친 생극제화 및 대체 규칙을 100% 엄수하십시오.
1. 👨‍👩‍👦 [핵심 가족]: 
   - 아내(부인) = 정재 (정재가 없으면 편재로 대체)
   - 애인(여친) = 편재 (편재가 없으면 정재로 대체)
   - 자녀 = 관성(정관/편관) 🚨(경고: 남명에서 '식상'을 자녀로 풀이하는 즉시 치명적 오류로 간주함!)
2. 👵👴 [부모 및 조부모]: 
   - 아버지 = 편재 (없으면 정재) / 어머니 = 정인 (없으면 편인)
   - 조부(할아버지) = 편인 / 조모(할머니) = 상관
3. 🏠 [처가 및 형제]: 
   - 장모(처가) = 식상 (아내를 생하는 기운)
   - 동성 형제(형/남동생) = 비견 / 이성 형제(누나/여동생) = 겁재
4. 🚨 [상태별 호칭 맞춤형 타겟팅]: 내담자의 현재 혼인 상태({u_marital})를 반드시 반영하십시오. 
   - 기혼: '현재 아내/배우자'로 칭할 것.
   - 미혼: '미래의 아내/인연'으로 칭할 것.
   - 🚨돌싱(이혼/사별): 절대 '현재 아내'라고 부르지 말고, '과거의 인연(전처)'에 대한 성찰이나 '새로운 인연(재혼운/애인)'을 맞이하는 조언으로 센스 있게 변환하여 카운슬링할 것.
"""
                else:
                    yukchin_rule = f"""
🚨 [육친 통변 특수부대 절대 규칙 (여성용)]: 
- 본 내담자는 여성(현재 상태: {u_marital})입니다. 아래의 명리학적 육친 생극제화 및 대체 규칙을 100% 엄수하십시오.
1. 👩‍❤️‍👨 [핵심 가족]: 
   - 남편 = 정관 (정관이 없으면 편관으로 대체)
   - 애인(남친) = 편관 (편관이 없으면 정관으로 대체)
   - 자녀 = 식상(식신/상관) 🚨(경고: 여명에서 '관성'을 자녀로 풀이하는 즉시 치명적 오류로 간주함!)
2. 👵👴 [부모 및 조부모]: 
   - 아버지 = 편재 (없으면 정재) / 어머니 = 정인 (없으면 편인)
   - 조부(외할아버지) = 편인 / 조모(외할머니) = 상관
3. 🏠 [시댁 및 자매]: 
   - 시어머니(시댁) = 재성 (남편을 생하는 기운)
   - 동성 형제(언니/여동생) = 비견 / 이성 형제(오빠/남동생) = 겁재
4. 🚨 [상태별 호칭 맞춤형 타겟팅]: 내담자의 현재 혼인 상태({u_marital})를 반드시 반영하십시오. 
   - 기혼: '현재 남편/배우자'로 칭할 것.
   - 미혼: '미래의 남편/인연'으로 칭할 것.
   - 🚨돌싱(이혼/사별): 절대 '현재 남편'라고 부르지 말고, '과거의 인연(전 남편)'에 대한 성찰이나 '새로운 인연(재혼운/애인)'을 맞이하는 조언으로 센스 있게 변환하여 카운슬링할 것.
"""

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
   <span class='sub-title' style='display: block; font-size: 20px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 35px; margin-bottom: 12px;'>1) 겉으로 드러난 성격</span>

   [지시 3-2] '▶, ▷, ◈, •' 형태의 세부 소목차는 18px 크기와 좁은 간격 적용:
   <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 25px; margin-bottom: 8px;'>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</span>
   <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 25px; margin-bottom: 8px;'>• {dw_start_age}세~{dw_mid_age}세 대운:</span>
   <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 25px; margin-bottom: 8px;'>◈ 나를 돕는 에너지와 색상:</span>

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
- 간지 표기 시 반드시 한자로 표기하십시오.
- 격국 팩트: {gyukgook_detail}
- 공망 팩트: 년주 {n_gong}, 일주 {i_gong}
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
(※ AI 지시: 사주팔자 오행의 분포와 계절적 조후, 억부의 균형 상태를 분석하고 삶에서 어떤 에너지를 추구해야 하는지 상세한 에세이를 작성하십시오.)

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
(※ AI 지시: 운의 흐름이 내담자의 삶에 미치는 전반적인 영향에 대해 총평 에세이를 작성하십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 대운의 흐름</span>
[DAEWUN_TABLE_HERE]
(※ AI 지시: 위 마커 자리는 파이썬이 대운 흐름표를 꽂을 자리이므로 절대 지우지 말고 그대로 두십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 대운 분석</span>
(※ AI 지시 🚨[절대 누락 금지 규칙]: 내담자가 살아온 첫 번째 대운(초년)부터 현재 대운 직전까지의 '모든 대운'을 단 하나도 생략하거나 묶지 말고, 나이대별로 낱낱이 순서대로 나열하여 에세이로 분석하십시오. 절대 요약하거나 건너뛰지 마십시오.)

(※ AI 지시: 내담자가 지나온 과거 각 대운들을 하나씩 도트(•) 형태로 나열하여 2~3줄씩 요약하십시오. 표 생성 절대 금지.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 현재 대운 전반기 상세 분석 ({dw_start_age}세~{dw_mid_age}세)</span>
(※ AI 지시: 현재 대운의 십성과 오행 기운이 내담자의 삶에 미치는 심리적, 사회적 변화를 상세히 카운슬링하십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</span>
(※ AI 지시: 현재 대운의 십성과 오행 기운이 내담자의 삶에 미치는 심리적, 사회적 변화를 상세히 카운슬링하십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 세운의 흐름</span>
[SEWUN_TABLE_HERE]
(※ AI 지시: 위 마커 자리는 파이썬이 세운 흐름표를 꽂을 자리이므로 절대 지우지 말고 그대로 두십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 세운 분석</span>
(※ AI 지시: 최근 지나온 과거 각 세운들을 하나씩 도트(•) 형태로 나열하여 2~3줄씩 요약하십시오. 단, 올해가 새로운 대운으로 바뀌는 첫 해일 경우, 이전 대운의 마지막 2~3년간의 세운을 분석하여 대운 교체기의 흐름을 명확히 서술하십시오. 표 생성 절대 금지.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 올해 세운 전반기 상세 분석</span>
(※ AI 지시: 올해 세운 전반기(양력2월~7월)의 십성과 오행 기운이 내담자의 삶에 미치는 심리적, 사회적 변화를 상세히 카운슬링하십시오.)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 올해 세운 후반기 상세 분석</span>
(※ AI 지시: 올해 세운 후반기(양력8월~다음년도 1월)의 십성과 오행 기운이 내담자의 삶에 미치는 심리적, 사회적 변화를 상세히 카운슬링하십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 월운의 흐름</span>
[WOLWUN_TABLE_HERE]
(※ AI 지시: 위 마커 자리는 파이썬이 월운 흐름표를 꽂을 자리이므로 절대 지우지 말고 그대로 두십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 월운 분석</span>
{past_months_html}
(※ AI 지시: 올해 지나온 각 과거 월운들을 하나씩 도트(•) 형태로 나열하여 2~3줄씩 요약하십시오. 
🚨단, 명리학적 기준(입춘)에 따라 양력 1월은 작년도 세운의 음력 12월에 해당하므로, 1월 분석 시 반드시 이 점을 맞추어 풀이하십시오. 
표 생성 절대 금지. 예: 2026년의 경우 • 1월(기축월): 내용...)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 이번 달 전반기(5일~19일) 상세 분석</span>
(※ AI 지시: 해당하는 월의 전반기(5일~19일)를 구체적인 조후와 기운의 흐름을 조언하십시오.)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 이번 달 후반기(20일~다음달 4일) 상세 분석</span>
(※ AI 지시: 해당하는 월의 후반기(20일~다음 달 4일까지)를 구체적인 조후와 기운의 흐름을 조언하십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 행운에 따른 종합 기운 조언</span>
(※ AI 지시: 대운, 세운, 월운이 융합되어 일으키는 역동적인 변화와 내담자가 취해야 할 최종 삶의 태도를 따뜻하게 서술하며 마무리하십시오.)
</div>

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
                try:
                    res = model.generate_content(prompt)
                    ai_text = "\n".join([line.lstrip() for line in res.text.split("\n")])
                    
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

                    # 🚨 1. 모든 요소를 여기서 한 번에 결합하여 단 한 번만 출력합니다. (조루증 완벽 해결)
                    report_1_full_html = f"""
{cover_html}
<div style='margin-bottom:20px;'>{print_btn_html}</div>
<div class='report-page'>
<div class='vip-inset-frame' style='border:2px solid #1A237E; box-sizing: border-box; padding: 20px; border-radius:15px;'>
<h1 style='text-align:center;'>🎯[초연 시공명리 사주풀이]</h1>
{table_html}
{master_bar_html}
<div style='margin-top:20px;'>
{intro_html}
{full_content_clean}
</div>
</div>
</div>
"""
                    st.markdown(report_1_full_html, unsafe_allow_html=True)
                    
                except Exception as e: 
                    st.error(f"AI 연산 오류: {e}") 

            # ------------------------------------------------------------------
            # [모드 2] 궁합 분석 (폰트 14px 통일)
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
                
                m_pillars = [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"]
                f_pillars = [f"{p_hs}{p_hb}", f"{p_ds}{p_db}", f"{p_ms}{p_mb}", f"{p_ys}{p_yb}"]
                
                m_ctx = {'u_name': u_name, 'dc': ds}
                f_ctx = {'u_name': p_name, 'dc': p_ds}
                
                if u_gender == "여성":
                    m_pillars, f_pillars = f_pillars, m_pillars
                    m_ctx, f_ctx = f_ctx, m_ctx
                
                gh_engine = UniversalPrintableGunghap(u_name, p_name, m_pillars, f_pillars)
                gh_engine.run_universal_logic()
                
                def draw_rich_saju_table(engine_gans, engine_jjis, name_str, gender_str, title_str):
                    gans = engine_gans[::-1] 
                    jjis = engine_jjis[::-1] 
                    hs, ds, ms, ys = gans
                    hb, db, mb, yb = jjis

                    ji_rel_rows = ""
                    for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                        b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                        b_top = "0px solid transparent !important"
                        cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                        lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                        ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

                    def td(c, size="18px"): return f"<td class='color-{get_color(c)}' style='font-size:{size}; font-weight:900; border:1px solid #444 !important;'>{('?' if c in ['?',' ','-'] else c)}</td>"

                    # 🚨 2. 궁합 모드의 사주표도 폰트 사이즈 14px로 통일 적용 완료
                    return f"""
                    <div style='margin-bottom: 15px; width:100%;'>
                        <div style='font-size: 18px; font-weight: 900; color: #1A237E; margin-bottom: 5px; text-align: left;'>🏮 {title_str} : {name_str}님 ({gender_str})</div>
                        <table class='result-table'>
                        <tr class='top-header-cell'>
                        <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>구분</span></td>
                        <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>시주</span></td>
                        <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>일주</span></td>
                        <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>월주</span></td>
                        <td style='border:1px solid #444; color:#FFFFFF !important;'><span style='color:#FFFFFF !important; font-weight:900;'>년주</span></td>
                        </tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:14px !important;'>천간합충</td>{"".join([f"<td style='border:1px solid #444;'>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])}</tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:14px !important;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#D50000;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(ds,ms)}</td><td style='border:1px solid #444;'>{get_ss(ds,ys)}</td></tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:14px !important;'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:14px !important;'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:14px !important;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(ds,hb)}</td><td style='border:1px solid #444;'>{get_ss(ds,db)}</td><td style='border:1px solid #444;'>{get_ss(ds,mb)}</td><td style='border:1px solid #444;'>{get_ss(ds,yb)}</td></tr>
                        <tr><td class='header-cell-main' style='padding:0; border:1px solid #444; font-size:14px !important;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
                        {ji_rel_rows}
                        <tr><td class='header-cell-main' style='border:1px solid #444 !important; font-size:14px !important;'>십이운성</td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444 !important; font-size:14px !important;'>십이신살</td>{"".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444 !important; font-size:14px !important;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis, gender_str)) if get_general_shinsal_filtered(i, gans, jjis, gender_str) else '-'}</td>" for i in range(4)])}</tr>
                        </table>
                    </div>
                    """

                def get_master_and_summary(engine_gans, engine_jjis, name_str, gender_str, is_applicant):
                    gans, jjis = engine_gans[::-1], engine_jjis[::-1]
                    hs, ds, ms, ys = gans
                    hb, db, mb, yb = jjis
                    
                    counts = {"목":0,"화":0,"토":0,"금":0,"수":0}
                    for char in gans + jjis:
                        if char != "?": counts[get_color(char)] += 1
                        
                    guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 해','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
                    guiin_str = guiin_map.get(ds, '없음')
                    n_gong = calculate_gongmang(ys, yb)
                    i_gong = calculate_gongmang(ds, db)
                    
                    cur_samjae = get_samjae(yb, curr_y_ganji[1])
                    samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"
                    
                    t_y, t_m, t_d = (u_y, u_m, u_d) if is_applicant else (p_y, p_m, p_d)
                    
                    b_dt = dt_mod.datetime(t_y, t_m, t_d, 12, 0)
                    adj_mins = get_total_time_adjustment(b_dt)
                    utc_dt = b_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
                    
                    order = 1 if (GAN.index(ys)%2==0) == (gender_str=='남성') else -1
                    calc_d = get_daeun_su_accurate(utc_dt, order)
                    
                    master_bar = f"<div style='border:2px solid #3E2723; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap; margin-bottom: 20px;'><div>⏳ 대운수: {calc_d}</div><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin_str}</div><div>🎯 공망: [일] {i_gong}</div><div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div></div>"
                    
                    w_key = f"{ms}{mb}".strip()
                    i_key = f"{ds}{db}".strip()
                    
                    w_core = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터를 찾지 못했습니다")
                    i_core = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 데이터를 찾지 못했습니다")
                            
                    summary_html = f"""
                    <div class='content-box-loose' style='margin-bottom: 30px;'>
                        <h3 style='font-size:19px !important; margin-top:10px !important; margin-bottom:10px !important; border-bottom:2px solid #1A237E; padding-bottom:5px; color:#1A237E !important; font-weight:900 !important;'>1. 사주팔자의 요약</h3>
                        <div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000; margin-bottom: 10px;'>
                            <p style='text-indent: 15px; margin-bottom: 5px;'><b>{name_str}님</b>은 '{w_core}'의 시공간에서, '{i_core}'의 성품을 가지고 태어나셨습니다.</p>
                        </div>
                    </div>
                    """
                    
                    return master_bar + summary_html

                try:
                    ai_out = gh_engine.generate_ai_report(m_ctx, f_ctx)
                    
                    m_ai_content = ai_out.split("[MALE_START]")[1].split("[MALE_END]")[0].strip() if "[MALE_START]" in ai_out else ""
                    f_ai_content = ai_out.split("[FEMALE_START]")[1].split("[FEMALE_END]")[0].strip() if "[FEMALE_START]" in ai_out else ""
                    gunghap_main = ai_out.split("[GUNGHAP_START]")[1].strip() if "[GUNGHAP_START]" in ai_out else ai_out

                    import re
                    b3 = chr(96) + chr(96) + chr(96)
                    pattern_str = b3 + "html|" + b3
                    m_ai_content = re.sub(pattern_str, "", m_ai_content).strip()
                    f_ai_content = re.sub(pattern_str, "", f_ai_content).strip()
                    gunghap_main = re.sub(pattern_str, "", gunghap_main).strip()

                    m_name_target = u_name if u_gender == '남성' else p_name
                    f_name_target = p_name if u_gender == '남성' else u_name
                    m_marital_target = u_marital if u_gender == '남성' else p_marital
                    f_marital_target = p_marital if u_gender == '남성' else u_marital
                    
                    import datetime, pytz
                    today_str = datetime.datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y년 %m월 %d일")

                    cover_html = f"<div class='report-page' style='padding:0; margin:0 auto; background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); display:flex; flex-direction:column; justify-content:center; align-items:center; min-height:100vh; page-break-after: always; -webkit-print-color-adjust: exact;'><div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 85%; max-width: 750px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin:auto;'><div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'><h1 style='font-size: 32px; color: #1A237E; font-weight: 900; margin:0; font-family:\"Malgun Gothic\", sans-serif;'>💞 초연 시공명리 궁합풀이</h1></div><div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'><h2 style='font-size: 24px; font-weight: 900; color: #1A237E; margin-bottom: 10px; font-family:\"Malgun Gothic\", sans-serif;'>♂️ 남성 : {m_name_target} 님</h2><p style='margin-bottom: 25px; color: #555; font-weight: 600; white-space: nowrap;'>[양력] {m_ctx.get('birth_solar', sol_str)} | [음력] {m_ctx.get('birth_lunar', lun_str)}</p><h2 style='font-size: 24px; font-weight: 900; color: #D50000; margin-bottom: 10px; font-family:\"Malgun Gothic\", sans-serif;'>♀️ 여성 : {f_name_target} 님</h2><p style='margin-bottom: 0; color: #555; font-weight: 600; white-space: nowrap;'>[양력] {f_ctx.get('birth_solar', sol_str)} | [음력] {f_ctx.get('birth_lunar', lun_str)}</p></div><p style='font-size: 18px; margin-top: 50px; font-weight: bold;'>{today_str}</p><p style='font-size: 22px; font-weight: 900; color: #1A237E; margin-top: 20px; font-family:\"Malgun Gothic\", sans-serif;'>초연 시공명리 연구소</p></div></div>"

                    m_title_html = f"<div style='text-align:center; font-family:\"Malgun Gothic\", sans-serif; margin-bottom:15px; line-height:1.5;'><span style='font-size:18px; font-weight:900; color:#1A237E; white-space:nowrap;'>♂️ {m_name_target}님 (남성, {m_marital_target})</span></div>"
                    f_title_html = f"<div style='text-align:center; font-family:\"Malgun Gothic\", sans-serif; margin-bottom:15px; line-height:1.5;'><span style='font-size:18px; font-weight:900; color:#D50000; white-space:nowrap;'>♀️ {f_name_target}님 (여성, {f_marital_target})</span></div>"

                    tables_html = "<div class='report-page' style='padding:40px; background:#fff;'><div class='vip-inset-frame' style='border:2px solid #1A237E; border-radius:15px; padding:30px;'>"
                    tables_html += f"<div style='text-align:center; border-bottom:4px double #3E2723; padding-bottom:15px; margin-bottom:25px;'><h1 style='margin:0; color:#3E2723; font-weight: 900; font-family:\"Malgun Gothic\", sans-serif;'>🗝️ 두 사람의 사주팔자</h1></div>"
                    
                    tables_html += f"<div>{m_title_html}{draw_rich_saju_table(gh_engine.m_g, gh_engine.m_j, '', '남성', '')}{get_master_and_summary(gh_engine.m_g, gh_engine.m_j, m_name_target, '남성', (u_gender == '남성'))}<div class='content-box-loose'>{m_ai_content}</div></div>"
                    
                    tables_html += "<div style='page-break-before: always; margin-top: 50px;'></div>"
                    
                    tables_html += f"<div>{f_title_html}{draw_rich_saju_table(gh_engine.f_g, gh_engine.f_j, '', '여성', '')}{get_master_and_summary(gh_engine.f_g, gh_engine.f_j, f_name_target, '여성', (u_gender == '여성'))}<div class='content-box-loose'>{f_ai_content}</div></div>"
                    tables_html += "</div></div>"

                    def build_daeun_row_html(gans_val, jjis_val, gender_val, age_val, daewun_num):
                        gan_list, ji_list = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
                        ms, mb = gans_val[2], jjis_val[2]
                        ys = gans_val[3]
                        order = 1 if (gan_list.index(ys) % 2 == 0) == (gender_val == '남성') else -1
                        html = "<div style='display:flex; flex-wrap:nowrap; overflow:hidden; border:2px solid #3E2723; background:white; margin-bottom:10px; font-family:\"Malgun Gothic\", sans-serif;'>"
                        for i in range(10):
                            val = int(daewun_num) + i*10
                            c = gan_list[(gan_list.index(ms)+(i+1)*order)%10] if ms in gan_list else "-"
                            j = ji_list[(ji_list.index(mb)+(i+1)*order)%12] if mb in ji_list else "-"
                            active = "background:#FFEBEE; outline:3px solid #D50000; z-index:2; position:relative;" if (val <= age_val < val+10) else ""
                            html += f"<div style='flex:1; border-left:1px solid #ddd; text-align:center; {active}'><div style='background:#3E2723; color:white; font-size:12px; padding:2px 0;'>{val}세</div><div style='font-size:15px; font-weight:900; padding:3px 0;'>{c}</div><div style='font-size:15px; font-weight:900; padding:3px 0;'>{j}</div></div>"
                        return html + "</div>"

                    m_t_y, m_t_m, m_t_d = (u_y, u_m, u_d) if u_gender == '남성' else (p_y, p_m, p_d)
                    f_t_y, f_t_m, f_t_d = (p_y, p_m, p_d) if u_gender == '남성' else (u_y, u_m, u_d)
                    
                    m_b_dt = dt_mod.datetime(m_t_y, m_t_m, m_t_d, 12, 0)
                    f_b_dt = dt_mod.datetime(f_t_y, f_t_m, f_t_d, 12, 0)
                    
                    m_order = 1 if (GAN.index(gh_engine.m_g[3])%2==0) else -1
                    f_order = 1 if not (GAN.index(gh_engine.f_g[3])%2==0) else -1
                    
                    m_d_num = get_daeun_su_accurate(m_b_dt - dt_mod.timedelta(hours=9), m_order)
                    f_d_num = get_daeun_su_accurate(f_b_dt - dt_mod.timedelta(hours=9), f_order)
                    
                    m_age = curr_y - m_t_y + 1
                    f_age = curr_y - f_t_y + 1

                    m_daeun_html = f"<div style='font-family:\"Malgun Gothic\", sans-serif; font-weight:900; color:#1A237E; margin-bottom:5px; font-size:15px;'>♂️ {m_name_target}님의 대운 흐름</div>" + build_daeun_row_html(gh_engine.m_g, gh_engine.m_j, '남성', m_age, m_d_num)
                    f_daeun_html = f"<div style='font-family:\"Malgun Gothic\", sans-serif; font-weight:900; color:#D50000; margin-top:15px; margin-bottom:5px; font-size:15px;'>♀️ {f_name_target}님의 대운 흐름</div>" + build_daeun_row_html(gh_engine.f_g, gh_engine.f_j, '여성', f_age, f_d_num)
                    couple_daeun_box = f"<div style='background:#FAFAFA; padding:20px; border:1px solid #1A237E; border-radius:10px; margin:15px 0;'>{m_daeun_html}{f_daeun_html}</div>"
                    
                    if "[[COUPLE_DAEUN_TABLES]]" in gunghap_main:
                        gunghap_main = gunghap_main.replace("[[COUPLE_DAEUN_TABLES]]", couple_daeun_box)
                    else:
                        gunghap_main = couple_daeun_box + gunghap_main

                    gunghap_html = gh_engine.get_graphic_html(gunghap_main)
                    
                    # 🚨 3. 궁합 모드 역시 순차적으로 한 번에 출력되도록 보장
                    st.markdown(cover_html, unsafe_allow_html=True)
                    st.markdown(tables_html, unsafe_allow_html=True)
                    st.markdown(gunghap_html, unsafe_allow_html=True)
                    
                    print_btn_html = "<div class='no-print' style='text-align: center; margin: 40px 0;'><button onclick='window.focus(); window.print()' style='padding: 12px 35px; background-color: #3E2723; color: white; font-weight: 900; border-radius: 5px; cursor: pointer;'>🖨️ 궁합 감명서 인쇄 / PDF 저장</button></div>"
                    components.html(print_btn_html, height=100)
                except Exception as e:
                    st.error(f"궁합 AI 구동 실패 오류: {e}")
