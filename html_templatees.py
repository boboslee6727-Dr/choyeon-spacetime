def get_intro_html():
    return """
    <div style='font-family: "Noto Serif KR", serif; font-size: 16px; font-weight: 600; color: #333; text-align: justify; line-height: 1.8; margin-bottom: 5px;'>
        <p style='text-indent: 15px; margin: 0 0 5px 0;'>기존 전통 명리학 사주풀이는 1년에 한 번 돌아오는 '12월지'와 '60일주'의 조합으로 720가지의 유형으로 시작합니다만,</p>
        <p style='text-indent: 15px; margin: 0 0 5px 0;'>본 초연 시공명리 사주풀이는 5년에 한 번 돌아오는 '60월령'과 '60일주'의 조합으로 3,600가지의 유형으로 보다 더 정밀한 분석이 가능합니다.</p>
        <p style='text-indent: 15px; margin: 0;'>기존 전통명리학에 비교하면 '5배', 요즘 유행하는 MBTI의 16가지 유형과 비교하면 무려 '225배' 더 세분화된 정밀한 사주풀이 분석입니다.</p>
    </div>
    """

def get_personal_cover(APP_VERSION, p_color, p_icon, u_name, sol_str, lun_str, time_str, today_str):
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
            <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                <h1 class='title-gothic' style='font-size: 40px !important; margin:0 !important; font-weight: 900;'>초연 시공명리 사주팔자 풀이</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px;'>{APP_VERSION}</span>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>
                <h2 style='font-size: 24px; font-weight: 800; color: {p_color}; margin-bottom: 20px;'>{p_icon} 신청인 : {u_name} 님</h2>
                <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p>
                    <p style='margin: 5px 0 0 0; color: #D50000; white-space: nowrap;'>{time_str}</p>
                </div>
            </div>
            <p style='font-size: 18px; margin-top: 50px; font-weight: 800;'>{today_str}</p>
            <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 20px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    """

def get_gunghab_cover(APP_VERSION, m_name, m_age, m_sol, m_lun, f_name, f_age, f_sol, f_lun, today_str):
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
            <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                <h1 class='title-gothic' style='font-size: 40px !important; margin:0 !important; font-weight: 900;'>초연 시공명리 궁합풀이</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px;'>{APP_VERSION}</span>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 15px; margin-bottom: 20px;'>
                <h2 style='font-size: 24px; font-weight: 800; color: #1A237E; margin-bottom: 15px;'>♂️ 남명 : {m_name} 님 <span style='font-size:16px; color:#555;'>( {m_age}세 )</span></h2>
                <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {m_sol} | [음력] {m_lun}</p>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 15px;'>
                <h2 style='font-size: 24px; font-weight: 800; color: #D50000; margin-bottom: 15px;'>♀️ 여명 : {f_name} 님 <span style='font-size:16px; color:#555;'>( {f_age}세 )</span></h2>
                <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {f_sol} | [음력] {f_lun}</p>
                </div>
            </div>
            <p style='font-size: 18px; margin-top: 30px; font-weight: 800;'>{today_str}</p>
            <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    """

def get_intro_html():
    return """
    <div style='font-family: "Nanum Myeongjo", serif; font-size: 16px; font-weight: 600; color: #333; text-align: justify; line-height: 1.8; margin-bottom: 25px; background: #FFF; padding: 15px; border-radius: 8px; border: 1px solid #E0E0E0;'>
        <p style='text-indent: 15px; margin: 0 0 8px 0;'>기존 전통 명리학 사주풀이는 1년에 한 번 돌아오는 '12월지'와 '60일주'의 조합으로 720가지의 유형으로 시작합니다만,</p>
        <p style='text-indent: 15px; margin: 0 0 8px 0;'>본 초연 시공명리 사주풀이는 5년에 한 번 돌아오는 '60월령'과 '60일주'의 조합으로 3,600가지의 유형으로 보다 더 정밀한 분석이 가능합니다.</p>
        <p style='text-indent: 15px; margin: 0;'>기존 전통명리학에 비교하면 '5배', 요즘 유행하는 MBTI의 16가지 유형과 비교하면 무려 '225배' 더 세분화된 정밀한 사주풀이 분석입니다.</p>
    </div>
    """

def get_table_html(info_h, gans, jjis, ds, hs, hb, db, mb, yb, ji_rel_rows, get_gan_rel_all, get_ss, get_jijanggan_full, get_unsung, get_12_shinsal, get_general_shinsal_filtered, get_color, u_gender):
    def td(c, size="18px"):
        color_map = {'목': '#E8F5E9', '화': '#FFEBEE', '토': '#FFFDE7', '금': '#F5F5F5', '수': '#E1F5FE', '무': '#FFFFFF'}
        col = get_color(c)
        bg = color_map.get(col, '#FFFFFF')
        text_color = '#1A237E' if col == '수' else ('#2E7D32' if col == '목' else ('#C62828' if col == '화' else '#333333'))
        return f"<td style='font-size:{size}; font-weight:900; border:1px solid #444 !important; background:{bg} !important; color:{text_color}; padding:12px; width:22%;'>{('?' if c in ['?',' ','-'] else c)}</td>"
    
    return f"""
    <div style='text-align:center; margin-bottom:15px;'>{info_h}</div>
    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center; table-layout: fixed; border: 2px solid #444;'>
        <tr class='top-header-cell' style='background:#1A237E; color:#FFFFFF; font-weight:900; height:40px;'>
            <td style='border:1px solid #444; width:12%; font-weight:900;'>구분</td><td style='border:1px solid #444;'>시주</td><td style='border:1px solid #444;'>일주</td><td style='border:1px solid #444;'>월주</td><td style='border:1px solid #444;'>년주</td>
        </tr>
        <tr style='height:38px;'><td style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:13px;'>천간합충</td>{"".join([f"<td style='border:1px solid #444; font-weight:700;'>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])}</tr>
        <tr style='height:38px;'><td style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:13px;'>천간십성</td><td style='border:1px solid #444; font-weight:700;'>{get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444; font-weight:700;'>{get_ss(ds,ms)}</td><td style='border:1px solid #444; font-weight:700;'>{get_ss(ds,ys)}</td></tr>
        <tr><td style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:13px;'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
        <tr><td style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:13px;'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
        <tr style='height:38px;'><td style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:13px;'>지지십성</td><td style='border:1px solid #444; font-weight:700;'>{get_ss(ds,hb)}</td><td style='border:1px solid #444; font-weight:700;'>{get_ss(ds,db)}</td><td style='border:1px solid #444; font-weight:700;'>{get_ss(ds,mb)}</td><td style='border:1px solid #444; font-weight:700;'>{get_ss(ds,yb)}</td></tr>
        <tr><td style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:13px;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444; vertical-align:middle;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
        {ji_rel_rows}
        <tr style='height:38px;'><td style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:13px;'>십이운성</td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444; font-weight:700;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
        <tr style='height:38px;'><td style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:13px;'>십이신살</td>{"".join([f"<td style='color:#C62828; border:1px solid #444; font-weight:700;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
        <tr><td style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:13px;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:6px; border:1px solid #444; font-size:12px; line-height:1.4;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis, u_gender)) if get_general_shinsal_filtered(i, gans, jjis, u_gender) else '-'}</td>" for i in range(4)])}</tr>
    </table>
    """

def get_master_bar(counts, guiin_str, n_gong, i_gong, samjae_color, cur_samjae):
    return f"""
    <div style='border:2px solid #3E2723; margin-top:20px; padding:10px; display:flex; justify-content:space-between; font-weight:900; font-size:13px; border-radius:8px; white-space:nowrap; background:#FFF;'>
        <div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div>
        <div>🌟 천을귀인: <span style='color:#0D47A1;'>{guiin_str}</span></div>
        <div>🎯 공망: [년] <span style='color:#C62828;'>{n_gong}</span> / [일] <span style='color:#C62828;'>{i_gong}</span></div>
        <div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div>
    </div>
    """

def get_daewun_html(calc_d, direction_str, u_age, ms, mb, ds, yb, GAN, JI, get_ss, get_color, get_unsung, get_12_shinsal):
    un_html = f"<div style='margin-top:25px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
    order = 1 if direction_str == "순행" else -1
    for i in range(10):
        val = i * 10 + calc_d
        c = GAN[(GAN.index(ms) + (i + 1) * order) % 10] if ms in GAN else "-"
        j = JI[(JI.index(mb) + (i + 1) * order) % 12] if mb in JI else "-"
        is_active = val <= u_age < val + 10
        bg_col = "#FFF9C4" if is_active else "transparent"
        b_left = "1px solid #ccc" if i != 9 else "none"
        un_html += f"""
        <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:5px; background-color:{bg_col};'>
            <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{val}세</div>
            <div style='padding:2px; font-size:11px; color:#666;'>{get_ss(ds,c)}</div>
            <div class='color-{get_color(c)}' style='font-size:17px; font-weight:900;'>{c}</div>
            <div class='color-{get_color(j)}' style='font-size:17px; font-weight:900;'>{j}</div>
            <div style='padding:2px; font-size:11px; color:#666;'>{get_ss(ds,j)}</div>
            <div style='font-size:11px; border-top:1px solid #eee; padding-top:2px;'>{get_unsung(ds,j)}</div>
            <div style='font-size:11px; color:#C62828; font-weight:700;'>{get_12_shinsal(yb, j)}</div>
        </div>
        """
    un_html += "</div>"
    return un_html

def get_sewun_html(dw_g_cur, dw_j_cur, start_year, curr_y, ds, yb, GAN, JI, get_ss, get_color, get_unsung, get_12_shinsal):
    se_html = f"<div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
    for i in range(10):
        ty = start_year + i
        base = (ty - 1984) % 60
        tc, tj = GAN[base % 10], JI[base % 12]
        is_cur_yr = (ty == curr_y)
        bg_col = "#E1F5FE" if is_cur_yr else "transparent"
        b_left = "1px solid #ccc" if i != 9 else "none"
        se_html += f"""
        <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:5px; background-color:{bg_col};'>
            <div style='background-color:#0D47A1; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{ty}년</div>
            <div style='padding:2px; font-size:11px; color:#666;'>{get_ss(ds,tc)}</div>
            <div class='color-{get_color(tc)}' style='font-size:17px; font-weight:900;'>{tc}</div>
            <div class='color-{get_color(tj)}' style='font-size:17px; font-weight:900;'>{tj}</div>
            <div style='padding:2px; font-size:11px; color:#666;'>{get_ss(ds,tj)}</div>
            <div style='font-size:11px; border-top:1px solid #eee; padding-top:2px;'>{get_unsung(ds,tj)}</div>
            <div style='font-size:11px; color:#C62828; font-weight:700;'>{get_12_shinsal(yb, tj)}</div>
        </div>
        """
    se_html += "</div>"
    return se_html

def get_wolwun_html(curr_y, curr_m, ds, yb, wol_gans, wol_jis, get_ss, get_color, get_unsung, get_12_shinsal):
    wol_html = f"<div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 월운의 흐름 ({curr_y}년도 양력기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
    for i in range(12):
        tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
        is_cur_m = (tm == curr_m)
        bg_col = "#E8F5E9" if is_cur_m else "transparent"
        b_left = "1px solid #ccc" if i != 11 else "none"
        wol_html += f"""
        <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:5px; background-color:{bg_col};'>
            <div style='background-color:#2E7D32; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{tm}월</div>
            <div style='padding:2px; font-size:11px; color:#666;'>{get_ss(ds,tc)}</div>
            <div class='color-{get_color(tc)}' style='font-size:17px; font-weight:900;'>{tc}</div>
            <div class='color-{get_color(tj)}' style='font-size:17px; font-weight:900;'>{tj}</div>
            <div style='padding:2px; font-size:11px; color:#666;'>{get_ss(ds,tj)}</div>
            <div style='font-size:11px; border-top:1px solid #eee; padding-top:2px;'>{get_unsung(ds,tj)}</div>
            <div style='font-size:11px; color:#C62828; font-weight:700;'>{get_12_shinsal(yb, tj)}</div>
        </div>
        """
    wol_html += "</div>"
    return wol_html

def get_closing_html(disp_name):
    return f"""
    <div style='margin-top: 40px; border-top: 2px dashed #444; padding-top: 25px; font-family: "Nanum Myeongjo", serif;'>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드(bar-code)와 같지만, 우리가 살아가며 마주하는 스캐너(scanner)인 '운'은 늘 변화하며 흐릅니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{disp_name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 시공명리의 지혜와 궁금증이 있으시면 언제든 <b>'초연 시공명리 연구소'</b>의 문을 두드려 주십시오.</p>
        <p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
        <div style='text-align: right; margin-top: 30px;'>
            <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
        </div>
    </div>
    """
