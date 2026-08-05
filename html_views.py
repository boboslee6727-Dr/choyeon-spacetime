# ==============================================================================
# html_views.py (Pro-Model 대운 10칸 / 세운 12칸 가로폭 정렬 및 12신살 2단 완결본) ver 7.3 (수정본)
# ==============================================================================
import re

def get_global_css():
    return """<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800;900&display=swap');

    .stApp { background-color: #FFF8E1 !important; }
    
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span[data-testid="stMarkdownContainer"] { 
        font-family: 'Nanum Gothic', sans-serif !important; 
    }

    .report-page, .report-page *, .cover-page, div.cover-page *, .choyeon-premium-report, .result-table td { 
        font-family: 'Noto Serif KR', serif !important; 
    }

    /* 🎯 [굵은체 전용 클래스 추가 - Noto Serif 900 강제 적용] */
    .b-text {
        font-weight: 900 !important;
        color: #000000 !important;
        display: inline-block;
    }
    .b-text-red {
        font-weight: 900 !important;
        color: #D50000 !important;
        display: inline-block;
    }

    div.stButton > button { 
        font-family: 'Nanum Gothic', sans-serif !important; 
        font-weight: 900 !important; 
        font-size: 16px !important;
        border-radius: 8px !important;
    }

    div.stButton > button[kind="primary"] { 
        background-color: #D50000 !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        height: 50px !important; 
        font-weight: 900 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #B71C1C !important;
        color: #FFFFFF !important;
    }

    div.stButton > button[kind="secondary"] { 
        background-color: #00A843 !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        height: 50px !important;
        font-weight: 900 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08) !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #008937 !important;
        color: #FFFFFF !important;
    }

    .ai-title-l1 { font-size: 22px !important; font-weight: 900 !important; color: #000000 !important; margin-top: 35px !important; margin-bottom: 15px !important; border-bottom: 2px solid #000000 !important; padding-bottom: 5px !important; line-height: 1.4 !important; font-family: sans-serif !important; display: block !important; }
    .ai-title-l2 { font-size: 18px !important; font-weight: 900 !important; color: #000000 !important; margin-top: 22px !important; margin-bottom: 10px !important; line-height: 1.4 !important; font-family: sans-serif !important; display: block !important; }
    .vip-inset-frame { border: 2px solid #3E2723 !important; border-radius: 12px !important; padding: 30px 25px !important; background-color: #FFFFFF !important; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .ai-body-p { font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-justify: inter-character !important; text-indent: 1.0em !important; margin-bottom: 12px !important; word-break: break-all !important; }

    .color-목 { background: #2E7D32 !important; color: #FFF !important; }
    .color-화 { background: #C62828 !important; color: #FFF !important; }
    .color-토 { background: #F9A825 !important; color: #000 !important; }
    .color-금 { background: #9E9E9E !important; color: #FFF !important; }
    .color-수 { background: #212121 !important; color: #FFF !important; }

    .result-table { width: 100%; border-collapse: collapse !important; border: 3px solid #3E2723 !important; margin-bottom: 15px; table-layout: fixed; }
    .result-table td { border: 1px solid #444 !important; padding: 1px 0 !important; text-align: center; vertical-align: middle; font-weight: 900 !important; font-size: 13px; line-height: 1.2 !important; }
    .ganji-cell-24 { font-size: 24px !important; font-weight: 900 !important; }

    .top-header-cell { background-color: #1A237E !important; height: 30px !important; }
    .top-header-cell td { background-color: #1A237E !important; color: #FFFFFF !important; font-weight: 900 !important; font-size: 16px !important; border: 1px solid #444 !important; }
    .header-cell-main, .header-cell-sub { background-color: #E8EAF6 !important; color: #000000 !important; font-weight: 900 !important; font-size: 14px !important; }

    .report-page { width: 210mm; max-width: 100%; margin: 20px auto; background-color: #FFF !important; padding: 12mm 10mm; box-sizing: border-box; color: #000; }

    @media print { 
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; -webkit-print-color-adjust: exact !important; }
        .report-page { box-shadow: none; margin: 0 auto; page-break-after: always; width: 100%; padding: 0; }
    }
    </style>
    """

def get_personal_cover(version, p_icon, name, sol_str, lun_str, time_str, today_str):
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 90%; max-width: 800px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
            <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                <h1 style='font-size: 26px !important; margin:0 !important; font-weight: 900; white-space: nowrap;'>🏮 초연 시공명리 사주풀이</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span style='font-size: 14px; letter-spacing: 1px; color:#555;'>{version}</span>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>
                <h2 style='font-size: 24px; font-weight: 900; color: #1A237E; margin-bottom: 20px;'>{p_icon} 신청인 : {name} 님</h2>
                <div style='font-size: 16px; font-weight: 600; color: #555; line-height: 1.8;'>
                    <div style='font-size: 16px; color: #555; line-height: 1.8;'>
                        <!-- 🎯 [양력], |, [음력] 전체를 b-text 태그 안으로 이동하여 굵은체 적용 -->
                        <p style='margin: 0; white-space: nowrap;' class='b-text'>[양력] {sol_str} | [음력] {lun_str}</p>
                        <p style='margin: 5px 0 0 0; white-space: nowrap;'><span class='b-text-red'>{time_str}</span></p>
                    </div>
                </div>
            </div>
            <p style='font-size: 18px; margin-top: 50px; font-weight: 900;'>{today_str}</p>
            <p style='font-size: 22px; font-weight: 900; color: #1A237E; margin-top: 20px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class="page-break-before"></div>
    """

def get_info_header(p_icon, name, gender, marital, age, sol_str, lun_str, time_str, p_color="#1A237E"):
    return f"""
    <div style='text-align:center; margin-bottom:8px; line-height:1.6;'>
        <span style='font-size:22px; font-weight:900; color:{p_color}; letter-spacing:1px; white-space:nowrap;'>{p_icon} {name}님 ({gender}, {marital}, {age}세)</span><br>
        <!-- 🎯 [양력:, |, 음력:] 전체를 b-text 태그 안으로 이동하여 굵은체 적용 -->
        <span style='font-size:15px; letter-spacing:0.5px; white-space:nowrap;' class='b-text'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span>
    </div>
    """

def generate_saju_table_data(gans, jjis, ds, gender, engine):
    gan_rel = "".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])
    
    hs, ds_val, ms, ys = gans[0], gans[1], gans[2], gans[3]
    gan_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, hs)}</td>" \
             f"<td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td>" \
             f"<td style='border:1px solid #444;'>{engine.get_ss(ds, ms)}</td>" \
             f"<td style='border:1px solid #444;'>{engine.get_ss(ds, ys)}</td>"

    hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]
    
    gan_row_html = "".join([td_func(g, engine) for g in gans])
    ji_row_html = "".join([td_func(j, engine) for j in jjis])

    ji_ss_html = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, hb)}</td>" \
                 f"<td style='border:1px solid #444;'>{engine.get_ss(ds, db)}</td>" \
                 f"<td style='border:1px solid #444;'>{engine.get_ss(ds, mb)}</td>" \
                 f"<td style='border:1px solid #444;'>{engine.get_ss(ds, yb)}</td>"

    jijanggan_html = "".join([f"<td style='padding:0; border:1px solid #444;'>{engine.get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])

    ji_rel_rows = ""
    for l_idx, r_idx in enumerate([1, 2, 0, 3]):
        b_top = "0px !important"
        if l_idx == 1:
            b_bot = "2px solid #CCCCCC !important" 
        else:
            b_bot = "1px solid #444 !important"
        
        cells = []
        for ci in range(4):
            if ci == r_idx:
                if r_idx == 0:   lbl_txt = f"({jjis[r_idx]})→"
                elif r_idx == 3: lbl_txt = f"←({jjis[r_idx]})"
                else:           lbl_txt = f"←({jjis[r_idx]})→"
                cells.append(f"<td style='color:#D50000; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important; padding:2px 0 !important; vertical-align: middle;'>{lbl_txt}</td>")
            else:
                rel_val = engine.get_ji_rel_set(jjis[r_idx], jjis[ci])
                txt_color = "#000" if rel_val != "-" else "#BBB"
                cells.append(f"<td style='color:{txt_color}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important; padding:2px 0 !important; vertical-align: middle;'>{rel_val}</td>")
                
        lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important; vertical-align: middle; padding:0 !important;'>합충형파해</td>" if l_idx == 0 else ""
        ji_rel_rows += f"<tr style='border:none; height:auto;'>{lbl}{''.join(cells)}</tr>"

    unsung = "".join([f"<td style='color:#0D47A1; font-weight:900; border:1px solid #444 !important;'>{engine.get_unsung(ds, jjis[i])}</td>" for i in range(4)])

    y_shinsal_tds = []
    d_shinsal_tds = []
    for i in range(4):
        y_s = engine.get_12_shinsal(yb, jjis[i]) if jjis[i] != "-" else "-"
        raw_d = engine.get_12_shinsal(db, jjis[i]) if jjis[i] != "-" else "-"
        clean_d = str(raw_d).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
        d_s = f"({clean_d})" if clean_d and clean_d != "-" else "(-)"
        
        y_shinsal_tds.append(f"<td style='color:#C62828; font-weight:900; font-size:14px; border:1px solid #444 !important; padding:4px 0;'>{y_s}</td>")
        d_shinsal_tds.append(f"<td style='color:#C62828; font-weight:900; font-size:14px; border:1px solid #444 !important; padding:4px 0;'>{d_s}</td>")
        
    y_shinsal_html = "".join(y_shinsal_tds)
    d_shinsal_html = "".join(d_shinsal_tds)

    gen_shinsals = []
    for i in range(4):
        filtered = engine.get_general_shinsal_filtered(i, gans, jjis, gender)
        gen_shinsals.append("<br>".join(filtered[:6]) if filtered else "-")
    gen_shinsal = "".join([f"<td style='vertical-align:top; padding:2px; font-weight:900; border:1px solid #444 !important;'>{s}</td>" for s in gen_shinsals])

    return get_saju_table(gan_rel, gan_ss, gan_row_html, ji_row_html, ji_ss_html, jijanggan_html, ji_rel_rows, unsung, y_shinsal_html, d_shinsal_html, gen_shinsal)

def td_func(val, engine):
    oh = engine.get_color(val)
    cls_str = f"color-{oh}" if oh != '무' else ""
    return f"<td class='{cls_str} ganji-cell-24' style='border:1px solid #444 !important; width:21.25%;'>{val}</td>"

def get_saju_table(gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, y_shinsal, d_shinsal, gen_shinsal):
    return f"""
    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
        <tr class='top-header-cell'>
            <td style='width:15%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>구분</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>시주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>일주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>월주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>년주</td>
        </tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간합충</td>{gan_rel}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간십성</td>{gan_ss}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:24px !important;'>천간</td>{gan_row}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:24px !important;'>지지</td>{ji_row}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지십성</td>{ji_ss}</tr>
        <tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지장간</td>{jijanggan}</tr>
        {ji_rel_rows}
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이운성</td>{unsung}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>년지신살</td>{y_shinsal}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일지신살</td>{d_shinsal}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>{gen_shinsal}</tr>
    </table>
    """

def get_master_bar(calc_d, m, f, e, mtl, w, guiin, n_gong, i_gong, samjae_color, cur_samjae):
    return f"""
    <div style="background:#FFF8E1; padding:10px 15px; border-radius:8px; margin:15px 0; border:1px solid #3E2723; font-weight: 700; font-size: 13px; color: #1A237E; display: flex; justify-content: space-between; align-items: center; white-space: nowrap;">
        <span style="flex: 1; text-align: center;">🔢 대운수: {calc_d}</span>
        <span style="flex: 1; text-align: center;">💥 오행: 木{m} 火{f} 土{e} 金{mtl} 水{w}</span>
        <span style="flex: 1; text-align: center;">🌟 천을귀인: {guiin}</span>
        <span style="flex: 1; text-align: center;">🎯 공망: [년]{n_gong} [일]{i_gong}</span>
        <span style="flex: 1; text-align: center;">🌪️ 삼재: <span style="color:{samjae_color};">{cur_samjae}</span></span>
    </div>
    """

def get_styled_td(ganji, oh_class):
    return f"<td class='{oh_class} ganji-cell'>{ganji}</td>"

def get_intro_html():
    return """
    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
    <div style="margin: 0; padding: 0;">
        <p class="ai-body-p" style="margin-top: 0; margin-bottom: 6px; font-weight: 600; text-align: justify; text-indent: 0;">
            <b>"초연 시공 명리학"</b>은 5년에 한 번 돌아오는 '60월령과 60일주'의 조합으로 <b>3,600개 유형</b>으로 분류하지만, <b>"기존의 전통 명리학"</b>은 1년에 한 번 돌아오는 '12월지와 60일주'의 조합으로 <b>720개 유형</b>으로 분류하여 풀이합니다.
        </p> 
        <p class="ai-body-p" style="margin-top: 0; margin-bottom: 0; font-weight: 600; text-align: justify; text-indent: 0;">
            따라서, <b>"본 초연 시공 명리학"</b>은 기존 전통명리학에 비하여 <b>5배</b>, 요즘 유행하는 16개 유형으로 분류하는 MBTI와 비교하면 무려 <b>225배</b> 더 정확한 사주풀이 입니다.
        </p>
    </div>
    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
    """

def get_golden_text(name, w_val, i_val, s_name, s_type, s_desc):
    return f"""
    <div style="margin: 0; padding: 0;">
        <p class="ai-body-p" style="margin: 0; color: #000000; text-align: justify; text-indent: 0;">
            초연 시공명리학적으로 풀이하면 <b>{name}님</b>은 <b>'{w_val}'</b>의 시공간에서, <b>'{i_val}'</b>의 성품을 가지고 태어나셨으며, 성격은 <b>'{s_name}'</b>인 <b>'{s_type}'</b>으로, <b>'{s_desc}'</b>하는 성향이 있습니다.
        </p>
    </div>
    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
    """

def get_un_layout(title, content):
    return f"""
    <div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px; table-layout:fixed;'>
        {content}
    </div>
    """

def generate_daewun_layout(daewun_list, direction_str, calc_d, get_oh_class_func):
    un_content = ""
    for data in daewun_list:
        bg_col = "#FFF9C4" if data.get("is_current", False) else "transparent"
        b_left = "none" if data.get("is_first", False) else "1px solid #ccc"
        
        # 🎯 [완벽 보정] shin_sal과 y_shinSal 키 모두를 안전하게 호환하도록 수정
        y_s_val = data.get("y_shinsal", data.get("shin_sal", "-"))
        d_s_val = data.get("d_shinsal", "-")
        
        un_content += get_un_cell(
            data["age_range"], data["ss_gan"], data["c_hanja"], get_oh_class_func(data["c_hangul"]), 
            data["j_hanja"], get_oh_class_func(data["j_hangul"]), data["ss_ji"], 
            data["un_sung"], y_s_val, d_s_val, bg_col, b_left, data.get("is_current", False)
        )
    return get_un_layout(f"[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]", un_content)

def get_un_cell(title_str, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, y_shinsal, d_shinsal, bg_col, b_left, is_current=False):
    u_val = unsung if unsung and str(unsung).strip() else "-"
    y_val = y_shinsal if y_shinsal and str(y_shinsal).strip() and str(y_shinsal).strip() != "None" else "-"
    
    clean_d = str(d_shinsal).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
    d_val = f"({clean_d})" if clean_d and clean_d != "-" and clean_d != "None" else "(-)"
    
    if is_current:
        active_style = "border: 3px solid #E65100 !important;"
        header_bg = "#E65100"
        bg_col = "#FFF9C4"
    else:
        active_style = f"border-left: {b_left}; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
        header_bg = "#3E2723"
        
    return f"""
    <div style='flex:1; width:10%; {active_style} text-align:center; padding-bottom:5px; background-color:{bg_col}; min-width:0; display:flex; flex-direction:column; box-sizing:border-box; overflow:hidden;'>
        <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:900; font-size:12px; height:25px; display:flex; align-items:center; justify-content:center; white-space:nowrap; letter-spacing:-0.5px;'>{title_str}</div>
        <div style='font-size:12px; font-weight:900; color:#000000; height:24px; display:flex; align-items:center; justify-content:center;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:18px; font-weight:900; height:30px; display:flex; align-items:center; justify-content:center;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:18px; font-weight:900; height:30px; display:flex; align-items:center; justify-content:center;'>{ji}</div>
        <div style='font-size:12px; font-weight:900; color:#000000; height:24px; display:flex; align-items:center; justify-content:center;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:12px; font-weight:900; border-top:1px solid #ccc; height:24px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#0D47A1;'>{u_val}</span></div>
        <div class='color-shinsal' style='font-size:12px; font-weight:900; border-top:1px solid #ccc; height:24px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{y_val}</span></div>
        <div class='color-shinsal-day' style='font-size:12px; font-weight:900; border-top:1px dashed #ccc; height:24px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{d_val}</span></div>
    </div>
    """

def get_sewun_layout(title, content):
    return f"""
    <div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px; table-layout:fixed;'>
        {content}
    </div>
    """

def get_sewun_cell(title_str, tage, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, y_shinsal, d_shinsal, bg_col, b_left, is_current=False):
    u_val = unsung if unsung and str(unsung).strip() else "-"
    y_val = y_shinsal if y_shinsal and str(y_shinsal).strip() else "-"
    
    clean_d = str(d_shinsal).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
    d_val = f"({clean_d})" if clean_d and clean_d != "-" else "(-)"
    
    if is_current:
        active_style = "border: 3px solid #0277BD !important;"
        header_bg = "#0277BD"
        bg_col = "#E1F5FE"
    else:
        active_style = f"border-left: {b_left}; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
        header_bg = "#3E2723"
    
    return f"""
    <div style='flex:1; width:8.33%; {active_style} text-align:center; padding-bottom:5px; background-color:{bg_col}; display:flex; flex-direction:column; box-sizing:border-box; min-width:0; overflow:hidden;'>
        <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:900; font-size:14px; height:28px; display:flex; align-items:center; justify-content:center; box-sizing:border-box; white-space:nowrap;'>
            <span>{title_str}</span>
        </div>
        <div style='font-size:12px; font-weight:900; color:#000000; height:22px; display:flex; align-items:center; justify-content:center;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:15px; font-weight:900; height:28px; display:flex; align-items:center; justify-content:center;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:15px; font-weight:900; height:28px; display:flex; align-items:center; justify-content:center;'>{ji}</div>
        <div style='font-size:12px; font-weight:900; color:#000000; height:22px; display:flex; align-items:center; justify-content:center;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:12px; font-weight:900; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#0D47A1;'>{u_val}</span></div>
        <div class='color-shinsal' style='font-size:12px; font-weight:900; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{y_val}</span></div>
        <div class='color-shinsal-day' style='font-size:12px; font-weight:900; border-top:1px dashed #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{d_val}</span></div>
    </div>
    """

def get_wolun_layout(title, content):
    return f"""
    <div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px; table-layout:fixed;'>
        {content}
    </div>
    """

def get_wolun_cell(tm, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, y_shinsal, d_shinsal, bg_col, b_left, is_current=False):
    u_val = unsung if unsung and str(unsung).strip() else "-"
    y_val = y_shinsal if y_shinsal and str(y_shinsal).strip() else "-"
    
    clean_d = str(d_shinsal).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
    d_val = f"({clean_d})" if clean_d and clean_d != "-" else "(-)"
    
    if is_current:
        active_style = "border: 3px solid #2E7D32 !important;"
        header_bg = "#2E7D32"
        bg_col = "#E8F5E9"
    else:
        active_style = f"border-left: {b_left}; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
        header_bg = "#3E2723"
    
    return f"""
    <div style='flex:1; width:8.33%; {active_style} text-align:center; padding-bottom:5px; background-color:{bg_col}; display:flex; flex-direction:column; box-sizing:border-box; min-width:0; overflow:hidden;'>
        <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:900; font-size:14px; height:25px; display:flex; align-items:center; justify-content:center; white-space:nowrap; letter-spacing:-0.5px;'>{tm}월</div>
        <div style='font-size:13px; font-weight:900; color:#000000; height:22px; display:flex; align-items:center; justify-content:center;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:15px; font-weight:900; height:28px; display:flex; align-items:center; justify-content:center;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:15px; font-weight:900; height:28px; display:flex; align-items:center; justify-content:center;'>{ji}</div>
        <div style='font-size:13px; font-weight:900; color:#000000; height:22px; display:flex; align-items:center; justify-content:center;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:12px; font-weight:900; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#0D47A1;'>{u_val}</span></div>
        <div class='color-shinsal' style='font-size:12px; font-weight:900; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{y_val}</span></div>
        <div class='color-shinsal-day' style='font-size:12px; font-weight:900; border-top:1px dashed #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{d_val}</span></div>
    </div>
    """

def generate_weekly_calendar_html(weekly_days_data, today_day, yb=None, db=None):
    content = ""
    
    def get_oh_class_local(char):
        try:
            import engine
            oh = engine.get_color(char)
            return f"color-{oh}" if oh != '무' else ""
        except:
            return ""

    for item in weekly_days_data:
        wday = item['weekday']
        day_num = item['day']
        ganji_str = item['ganji']
        is_today = item['is_today']
        
        gan_char = ganji_str[0] if len(ganji_str) >= 1 and ganji_str != "-" else "-"
        ji_char = ganji_str[1] if len(ganji_str) >= 2 else "-"
        
        gan_cls = get_oh_class_local(gan_char)
        ji_cls = get_oh_class_local(ji_char)
        
        ss_val, unsung_val, y_shinsal_val, d_shinsal_val = "-", "-", "-", "-"
        try:
            import engine
            # 🎯 일간(甲 등 또는 사주 일간)에 따른 지지십성 연산 복구
            ds_hanja = st.session_state.get('ds_hanja', '甲') if 'st_session_state' in globals() else '甲'
            ss_val = engine.get_ss(ds_hanja, ji_char) if ji_char != "-" else "-"
            unsung_val = engine.get_unsung(ds_hanja, ji_char) if ji_char != "-" else "-"
            
            if yb and ji_char != "-": y_shinsal_val = engine.get_12_shinsal(yb, ji_char)
            if db and ji_char != "-": d_shinsal_val = engine.get_12_shinsal(db, ji_char)
        except:
            try:
                import engine
                ss_val = engine.get_ss("甲", ji_char) if ji_char != "-" else "-"
                unsung_val = engine.get_unsung("甲", ji_char) if ji_char != "-" else "-"
                if yb and ji_char != "-": y_shinsal_val = engine.get_12_shinsal(yb, ji_char)
                if db and ji_char != "-": d_shinsal_val = engine.get_12_shinsal(db, ji_char)
            except:
                pass
            
        y_val = f"<span style='color:#C62828;'>{y_shinsal_val}</span>" if y_shinsal_val != "-" else "-"
        
        clean_d_w = str(d_shinsal_val).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
        d_val = f"<span style='color:#C62828;'>({clean_d_w})</span>" if clean_d_w and clean_d_w != "-" else "<span style='color:#C62828;'>(-)</span>"
            
        if is_today:
            active_style = "border: 3px solid #2E7D32 !important;"
            header_bg = "#2E7D32"
            bg_col = "#E8F5E9"
        elif wday == '일':
            active_style = "border-left: 1px solid #ccc; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
            header_bg = "#C62828"
            bg_col = "#FAFAFA"
        elif wday == '토':
            active_style = "border-left: 1px solid #ccc; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
            header_bg = "#1565C0"
            bg_col = "#FAFAFA"
        else:
            active_style = "border-left: 1px solid #ccc; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
            header_bg = "#555555"
            bg_col = "#FAFAFA"
            
        u_val = f"<span style='color:#0D47A1;'>{unsung_val}</span>" if unsung_val != "-" else "-"
        
        content += f"""
        <div style='flex:1; width:14.28%; {active_style} text-align:center; padding-bottom:5px; background-color:{bg_col}; display:flex; flex-direction:column; box-sizing:border-box; min-width:0; overflow:hidden;'>
            <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:900; font-size:16px; height:28px; display:flex; align-items:center; justify-content:center; white-space:nowrap;'>
                {day_num}일 ({wday})
            </div>
            <div style='font-size:12px; font-weight:900; color:#000000; height:24px; display:flex; align-items:center; justify-content:center;'>{ss_val}</div>
            <div class='{gan_cls}' style='font-size:18px; font-weight:900; height:28px; display:flex; align-items:center; justify-content:center;'>{gan_char}</div>
            <div class='{ji_cls}' style='font-size:18px; font-weight:900; height:28px; display:flex; align-items:center; justify-content:center;'>{ji_char}</div>
            <div class='color-unsung' style='font-size:12px; font-weight:900; border-top:1px solid #ccc; height:24px; display:flex; align-items:center; justify-content:center;'>{u_val}</div>
            <div class='color-shinsal' style='font-size:12px; font-weight:900; border-top:1px solid #ccc; height:24px; display:flex; align-items:center; justify-content:center;'>{y_val}</div>
            <div class='color-shinsal-day' style='font-size:12px; font-weight:900; border-top:1px dashed #ccc; height:24px; display:flex; align-items:center; justify-content:center;'>{d_val}</div>
        </div>
        """

    layout = f"""
    <div style='margin-top:20px; margin-bottom:10px; font-size:16px; font-weight:900; color:#3E2723; font-family:"Nanum Gothic", sans-serif;'>📅 이번 주 간지 흐름 (일요일 ~ 토요일)</div>
    <div style='display:flex; flex-direction:row; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px; table-layout:fixed;'>
        {content}
    </div>
    """
    
    return layout

def get_closing_html(name):
    return f"""
    <hr style="border: 0; border-top: 2px solid #000000; margin: 40px 0 25px 0;">
    <div style="margin: 0; padding: 0;">
        <p style="font-size: 16px; font-weight: 400; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 10px; color: #111111;">'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드(bar-code)와 같지만, 우리가 살아가며 마주하는 스캐너(scanner)인 '운'은 늘 변화하며 흐릅니다.</p>
        <p style="font-size: 16px; font-weight: 400; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 10px; color: #111111;">따라서 오늘의 '초연 시공명리학과의 인연'이 <b>{name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
        <p style="font-size: 16px; font-weight: 400; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 15px; color: #111111;">앞으로 미래에 대한 더 깊은 시공명리의 지혜와 궁금증이 있으시면 언제든 <b>'초연 시공명리 연구소'</b>의 문을 두드려 주십시오.</p>
        <p style="font-size: 16px; font-weight: 800; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 0; color: #111111;">오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
        <div style="text-align: right; margin-top: 30px;">
            <span style="font-weight: 900; font-size: 18px; color: #1A237E;">- 초연 시공명리 연구소 드림 -</span>
        </div>
    </div>
    """

def get_final_report_box(content_html):
    return f"""
    <div class='report-page'>
        <div style='border: 2px solid #5D4037; border-radius: 12px; padding: 25px; background-color:#FAFAFA;'>
            {content_html}
        </div>
    </div>
    """

def get_gunghap_cover(version, m_name, m_age, m_sol, m_lun, m_time, f_name, f_age, f_sol, f_lun, f_time, today_str):
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
            <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                <h1 class='title-gothic' style='font-size: 40px !important; margin:0 !important;'>초연 시공명리 궁합풀이</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 15px; margin-bottom: 20px;'>
                <h2 style='font-size: 24px; font-weight: 800; color: #1A237E; margin-bottom: 15px;'>♂️ 남명 : {m_name} 님 <span style='font-size:16px; color:#555;'>( {m_age}세 )</span></h2>
                <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {m_sol} | [음력] {m_lun} {m_time}</p>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 15px;'>
                <h2 style='font-size: 24px; font-weight: 800; color: #2E7D32; margin-bottom: 15px;'>♀️ 여명 : {f_name} 님 <span style='font-size:16px; color:#555;'>( {f_age}세 )</span></h2>
                <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {f_sol} | [음력] {f_lun} {f_time}</p>
                </div>
            </div>
            <p style='font-size: 18px; margin-top: 30px; font-weight: 800;'>{today_str}</p>
            <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class="page-break-before"></div>
    """

def get_gunghap_saju_table(gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, y_shinsal, d_shinsal, gen_shinsal):
    return f"""
    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center; margin-top:10px; table-layout:fixed;'>
        <tr class='top-header-cell'>
            <td style='width:15%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>구분</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>시주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>일주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>월주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>년주</td>
        </tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간합충</td>{gan_rel}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간십성</td>{gan_ss}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:24px !important;'>천간</td>{gan_row}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:24px !important;'>지지</td>{ji_row}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지십성</td>{ji_ss}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지장간</td>{jijanggan}</tr>
        {ji_rel_rows}
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; color:#0D47A1 !important; font-weight:900; font-size:14px !important;'>십이운성</td>{unsung}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; color:#C62828 !important; font-weight:900; font-size:14px !important;'>년지신살</td>{y_shinsal}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; color:#C62828 !important; font-weight:900; font-size:14px !important;'>일지신살</td>{d_shinsal}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>{gen_shinsal}</tr>
    </table>
    """

def get_gunghap_person_box(table_html, master_bar_html, add_page_break=False):
    pb = '<div class="page-break-before"></div>' if add_page_break else ''
    return f"""
    <div class='report-page'>
        <div style='border: 2px solid #5D4037; border-radius: 12px; padding: 25px; background-color:#FAFAFA;'>
            {table_html}
            {master_bar_html}
        </div>
    </div>
    {pb}
    """

def get_daewun_compare_box(m_name, m_un_html, w_name, w_un_html):
    return f"""
    <div class='report-page' style='font-family: "Noto Serif KR", serif; margin-top: 20px;'>
        <div style='border: 1px solid #E0E0E0; border-radius: 16px; padding: 35px 25px; background: linear-gradient(145deg, #ffffff, #f8f9fa); box-shadow: 0 8px 24px rgba(0,0,0,0.04);'>
            <h2 style='text-align:center; color:#1A237E; font-size: 24px; font-weight:900; margin-bottom: 8px; letter-spacing: 1px;'>
                [ 부부 대운 흐름 교차 분석 ]
            </h2>
            <p style='text-align:center; color:#757575; font-size: 14px; margin-bottom: 35px; font-family: "Nanum Gothic", sans-serif;'>
                두 사람의 시공간 궤도를 한눈에 비교하는 대운 로드맵입니다.
            </p>
            <div style='margin-bottom: 35px; background: #ffffff; border-left: 5px solid #283593; padding: 20px 25px; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.03);'>
                <h4 style='color:#283593; font-weight:900; font-size: 18px; margin-top: 0; margin-bottom: 20px; display: flex; align-items: center;'>
                    <span style='font-size: 22px; margin-right: 8px;'>♂️</span> 남명 ({m_name}님) 대운 흐름
                </h4>
                <div style='overflow-x: auto;'>
                    {m_un_html}
                </div>
            </div>
            <div style='background: #ffffff; border-left: 5px solid #C62828; padding: 20px 25px; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.03);'>
                <h4 style='color:#C62828; font-weight:900; font-size: 18px; margin-top: 0; margin-bottom: 20px; display: flex; align-items: center;'>
                    <span style='font-size: 22px; margin-right: 8px;'>♀️</span> 여명 ({w_name}님) 대운 흐름
                </h4>
                <div style='overflow-x: auto;'>
                    {w_un_html}
                </div>
            </div>
        </div>
    </div>
    <div class="page-break-before"></div>
    """

def get_comparison_gunghap_report_html(m_name, f_name, other_report):
    return f"""<div style='margin-top: 40px; padding: 20px; border: 1px solid #ccc; background-color: #f5f5f5; border-radius: 8px;'>
<div style='font-size:21px; font-weight:900; margin-bottom: 15px; color:#333;'>💕 남성({m_name}) & 여성({f_name}) 타 감명서 원문 (의뢰인 제공)</div>
<div style='white-space: pre-wrap; font-family: Noto Serif KR; line-height: 1.6; color:#444;'>{other_report}</div>
</div>
"""

def get_original_report_html(other_report):
    return f"""<div style='margin-top: 40px; padding: 20px; border: 1px solid #ccc; background-color: #f5f5f5; border-radius: 8px;'>
<div style='font-size:21px; font-weight:900; margin-bottom: 15px; color:#333;'>📄 타 감명서 원문 (의뢰인 제공)</div>
<div style='white-space: pre-wrap; font-family: Noto Serif KR; line-height: 1.6; color:#444;'>{other_report}</div>
</div>
"""

def get_comparison_html(comp_fmt):
    return f"""<div style='margin-top: 30px; padding: 25px; border: 1px solid #B71C1C; background-color: #FFEBEE; border-radius: 10px;'>
<div style='font-size:21px; font-weight:900; margin-bottom: 20px; color:#B71C1C;'>🔍 초연 시공명리 vs 타 감명서 1:1 상세비교 분석</div>
{comp_fmt}
</div>
"""

def get_gunghap_score_visual_html(gh_engine):
    sky_blue = "#38B6FF"
    bars = "".join([
        f"<div style='display:flex; align-items:center; margin-bottom:12px;'>"
        f"<div style='width:130px; font-size:13px; font-weight:bold; color:#555;'>{d['label']}</div>"
        f"<div style='flex:1; height:12px; margin:0 10px;'><svg width='100%' height='12'><rect width='100%' height='12' rx='6' ry='6' fill='#eee' /><rect width='{d['pct']}%' height='12' rx='6' ry='6' fill='{d['color']}' /></svg></div>"
        f"<div style='width:35px; font-size:12px; font-weight:bold;'>{d['pct']}%</div>"
        f"</div>" 
        for d in gh_engine.details
    ])

    score_chart_html = (
        f"<h2 style='text-align:center; margin-top:40px; font-size:22px; font-weight:900;'>📊 최종 궁합 점수</h2>\n"
        f"<div style='display:flex; justify-content:center; align-items:center; margin:20px 0;'>\n"
        f"<div style='width:130px; height:130px; border-radius:50%; background:conic-gradient({sky_blue} {gh_engine.final_score}%, #eee 0); display:flex; justify-content:center; align-items:center; -webkit-print-color-adjust: exact;'>\n"
        f"<div style='width:98px; height:98px; background:#fff; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center;'>\n"
        f"<span style='font-size:32px; font-weight:900; color:{sky_blue};'>{gh_engine.final_score}</span>\n"
        f"<span style='font-size:10px; color:#888; font-weight:bold;'>SCORE</span>\n"
        f"</div>\n"
        f"</div>\n"
        f"</div>\n"
        f"<div style='text-align:center; margin-bottom:20px;'><span style='font-size:16px; font-weight:bold; color:#fff; background:{sky_blue}; padding:8px 32px; border-radius:30px; -webkit-print-color-adjust: exact;'>{gh_engine.grade}</span></div>\n"
        f"<div style='max-width:500px; margin:0 auto; margin-bottom:25px;'>\n{bars}\n</div>\n"
    )
    return score_chart_html

def get_gunghap_closing(name1, name2):
    return f"""
    <div style='margin-top: 40px; border-top: 2px dashed #444; padding-top: 25px;'>
        <p style='font-size:16px !important; font-weight: 400 !important; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 10px; color: #111111;'>
        <b>{name1}님</b>과 <b>{name2}님</b>의 소중한 인연이 하늘의 뜻과 깊은 기운 속에서 찬란하게 빛을 발하기를 진심으로 기원합니다.</p>
        <p style='font-size:16px !important; font-weight: 400 !important; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 10px; color: #111111;'>두 분이 서로의 다름을 이해하고 채워주는 든든한 동반자가 되어 삶이라는 길을 함께 걸어가시기를 소망합니다.</p>
        <p style='font-size:16px !important; font-weight: 800 !important; text-indent: 15px; line-height: 1.85; margin-bottom: 0px; color: #111111;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
        <div style='text-align: right; margin-top: 30px;'>
            <span style='font-weight: 900; font-size: 18px !important; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
        </div>
    </div>
    """

def get_childbirth_taegil_card(border_col, idx, b_date_str, score, b_time_str, b_time_pillar, gestation_warning, conception_title, conception_str, conception_msg, baby_saju_html, ai_output_html):
    card_html = f"""
    <div style="background-color:#FFFFFF; border:1px solid #E0E0E0; border-radius:12px; padding:20px; margin-bottom:25px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #F1F3F4; padding-bottom:12px; margin-bottom:15px;">
            <h3 style="color:#1A237E; margin:0; font-size:18px;">🏅 추천 {idx+1}순위 출산 길일 : {b_date_str}</h3>
            <span style="background-color:#E8EAF6; color:#1A237E; font-weight:bold; padding:5px 12px; border-radius:20px; font-size:14px;">명리 종합점수: {score}점</span>
        </div>
        <ul style="list-style-type:none; padding-left:0; margin-top:10px; line-height:1.8; color:#333; font-size:14px;">
            <li><b>⏰ 가장 좋은 출산 시간</b>: <span style="color:#00695C; font-weight:bold;">{b_time_str} ({b_time_pillar})</span></li>
            {gestation_warning}
            <li><b>{conception_title}</b>: <span style="font-weight:bold; color:#0277BD;">{conception_str}</span> <br>{conception_msg}</li>
        </ul>
        {baby_saju_html}
        <div style="margin-top:15px; padding-top:15px; border-top:1px dashed #DDD;">
            {ai_output_html}
        </div>
    </div>
    """
    return card_html

def get_delivery_summary_box(best_days):
    summary_items = ""
    for idx, day_info in enumerate(best_days):
        b_time_info = day_info['best_time']
        pillars_str = day_info.get('four_pillars', '')
        summary_items += f"""
        <li style="margin-bottom:6px;">
            🏅 <b>추천 {idx+1}순위</b> (명리 종합점수: <span style="color:#C62828; font-weight:bold;">{day_info['score']}점</span>) : 
            <b>{day_info['date']} {b_time_info['time_str']}</b> 
            <span style="color:#555; font-size:13px;">({pillars_str})</span>
        </li>
        """
    return f"""
    <div style="background-color:#F0F4F8; border:2px solid #1A237E; border-radius:10px; padding:18px; margin-top:15px; margin-bottom:25px;">
        <h4 style="color:#1A237E; margin-top:0; margin-bottom:12px; font-size:16px; border-bottom:1px solid #C5CAE9; padding-bottom:8px;">
            📋 출산 길일 한눈에 보기 (가임/배란 주기별 최적 길일)
        </h4>
        <ul style="list-style-type:none; padding-left:0; margin:0; line-height:1.8; font-size:14px; color:#2C3E50;">
            {summary_items}
        </ul>
    </div>
    """

def get_comparison_saju_cover(version, p_icon, name, sol_str, lun_str, time_str, today_str):
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 90%; max-width: 800px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
            <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                <h1 style='font-size: 26px !important; margin:0 !important; font-weight: 900; white-space: nowrap;'>🏮 타 감명서 비교 (사주)</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span style='font-size: 14px; letter-spacing: 1px; color:#555;'>{version}</span>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>
                <h2 style='font-size: 24px; font-weight: 900; color: #1A237E; margin-bottom: 20px;'>{p_icon} 신청인 : {name} 님</h2>
                <div style='font-size: 16px; font-weight: 600; color: #555; line-height: 1.8;'>
                    <div style='font-size: 16px; color: #555; line-height: 1.8; font-weight: 600;'>
                        <p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p>
                        <p style='margin: 5px 0 0 0; white-space: nowrap;'>{time_str}</p>
                    </div>
                </div>
            </div>
            <p style='font-size: 18px; margin-top: 50px; font-weight: 900;'>{today_str}</p>
            <p style='font-size: 22px; font-weight: 900; color: #1A237E; margin-top: 20px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class="page-break-before"></div>
    """

def get_comparison_gunghap_cover(version, m_name, m_age, m_sol, m_lun, m_time, f_name, f_age, f_sol, f_lun, f_time, today_str):
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
            <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                <h1 class='title-gothic' style='font-size: 32px !important; margin:0 !important; color:#1A237E; font-weight:900;'>🏮 타 감명서 비교 (궁합)</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px; color:#555;'>{version}</span>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 15px; margin-bottom: 20px;'>
                <h2 style='font-size: 24px; font-weight: 800; color: #1A237E; margin-bottom: 15px;'>♂️ 남명 : {m_name} 님 <span style='font-size:16px; color:#555;'>( {m_age}세 )</span></h2>
                <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {m_sol} | [음력] {m_lun} {m_time}</p>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 15px;'>
                <h2 style='font-size: 24px; font-weight: 800; color: #2E7D32; margin-bottom: 15px;'>♀️ 여명 : {f_name} 님 <span style='font-size:16px; color:#555;'>( {f_age}세 )</span></h2>
                <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {f_sol} | [음력] {f_lun} {f_time}</p>
                </div>
            </div>
            <p style='font-size: 18px; margin-top: 30px; font-weight: 800;'>{today_str}</p>
            <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class="page-break-before"></div>
    """

def get_other_report_original_html(other_text_input):
    paragraphs = str(other_text_input).strip().split('\n')
    formatted_p = []
    for p in paragraphs:
        p_clean = p.strip()
        if p_clean:
            if p_clean.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '1)', '2)', '3)', '4)', '5)', '■', '●', '◆', 'http')):
                formatted_p.append(f"<div style='font-weight:bold; color:#1F2937; margin-top:18px; margin-bottom:8px; font-size:16px;'>{p_clean}</div>")
            else:
                formatted_p.append(f"<p style='text-indent: 1em; margin: 8px 0; line-height: 1.85; word-break: keep-all;'>{p_clean}</p>")
    content_body = "".join(formatted_p)
    return f"""
    <div class='page-break-before'></div>
    <div class='report-page' style='margin-top:20px;'>
        <div class='vip-inset-frame' style='border:2px solid #4B5563; padding:30px 25px; background:#FFFFFF; border-radius:12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);'>
            <h2 style='text-align:center; color:#374151; font-size:24px; font-weight:900; border-bottom:2px solid #4B5563; padding-bottom:12px; margin-top:0; margin-bottom:20px;'>
                📜 타 감명서 원문
            </h2>
            <div style='font-family: "Noto Serif KR", serif; font-size:15px; color:#111111; text-align:justify;'>
                {content_body}
            </div>
        </div>
    </div>
    """

def format_ai_text_to_html(ai_raw_text):
    if not ai_raw_text: 
        return ""
    
    clean_raw = str(ai_raw_text).replace("```html", "").replace("```markdown", "").replace("```", "").strip()
    clean_raw = re.sub(r'<!--.*?-->', '', clean_raw, flags=re.DOTALL)
    
    def replace_ganji_un(match):
        stem = match.group(1)
        suffix = match.group(2)
        g_map = {
            "갑자": "甲子", "을축": "乙丑", "병인": "丙寅", "정묘": "丁卯", "무진": "戊辰",
            "기사": "己巳", "경오": "庚午", "신미": "辛未", "임신": "壬申", "계유": "癸酉",
            "갑술": "甲戌", "을해": "乙亥", "병자": "丙子", "정축": "丁丑", "무인": "戊寅",
            "기묘": "己卯", "경진": "庚辰", "신사": "辛巳", "임오": "壬午", "계미": "癸未",
            "갑신": "甲申", "을유": "乙酉", "병술": "丙戌", "정해": "丁亥", "무자": "戊子",
            "기축": "己丑", "경인": "庚寅", "신묘": "辛卯", "임진": "壬辰", "계사": "癸巳",
            "갑오": "甲午", "을미": "乙未", "병신": "丙申", "정유": "丁酉", "무술": "戊戌",
            "기해": "己亥", "경자": "庚子", "신축": "辛丑", "임인": "壬寅", "계묘": "癸卯",
            "갑진": "甲辰", "을사": "乙巳", "병오": "丙午", "정미": "丁未", "무신": "戊申",
            "기유": "己酉", "경술": "庚戌", "신해": "辛亥", "임자": "壬子", "계축": "癸丑"
        }
        hanja_ganji = g_map.get(stem, stem)
        return f"{hanja_ganji}{suffix}"

    clean_raw = re.sub(r'([가-힠]{2})(대운|세운|월운)', replace_ganji_un, clean_raw)

    lines = clean_raw.split('\n')
    formatted_html = []
    
    for line in lines:
        line_str = line.strip()
        if not line_str: 
            continue
        
        clean_line_str = line_str.replace("**", "").replace("*", "")
        clean_line_str = re.sub(r'#{1,6}\s*', '', clean_line_str).strip()
        
        if re.match(r'^\d+\.\s+', clean_line_str) and not re.match(r'^\d+\)\s*', clean_line_str):
            formatted_html.append(f"<div class='ai-title-l1'>{clean_line_str}</div>")
            
        elif re.match(r'^\d+\)\s*', clean_line_str):
            formatted_html.append(f"<div class='ai-title-l2'>{clean_line_str}</div>")

        elif clean_line_str.startswith("- ") and clean_line_str.endswith(":"):
            formatted_html.append(
                f"<div style='font-size:16px !important; font-weight:900 !important; "
                f"color:#000000 !important; margin-top:14px !important; margin-bottom:6px !important; "
                f"line-height:1.6 !important; font-family:sans-serif !important; text-indent:1.0em;'>"
                f"{clean_line_str}</div>"
            )
            
        else:
            safe_line = clean_line_str.replace("&nbsp;", " ").replace("<", "&lt;").replace(">", "&gt;")
            safe_line = re.sub(r'([가-힣]{2,4}님)', r'<b>\1</b>', safe_line)
            formatted_html.append(f"<p class='ai-body-p'>{safe_line}</p>")
            
    return "".join(formatted_html)

def get_ai_report_box(content):
    return get_final_report_box(content)
