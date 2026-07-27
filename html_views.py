import re

def get_global_css():
    return """<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic&family=Nanum+Myeongjo:wght@400;700;800&display=swap');
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");

    html, body, [class*="css"] { font-family: 'Nanum Gothic', sans-serif; }
    .stApp { background-color: #FFF8E1 !important; }
    p, h1, h2, h3, h4, h5, h6, table, tr, td, div.report-page { font-family: 'Noto Serif KR', 'Nanum Myeongjo', serif !important; }
    [data-testid="stSidebar"] { background-color: #F0F2F6 !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] { font-family: 'Nanum Gothic', sans-serif !important; }

    /* 사이드바 알림 상자 : 단 두 줄 완벽 고정 스타일 */
    [data-testid="stSidebar"] div[data-testid="stNotification"] {
        padding: 3px 3px !important;
    }
    [data-testid="stSidebar"] div[data-testid="stNotification"] p {
        font-size: 11px !important;
        line-height: 1.5 !important;
        letter-spacing: -0.5px !important;
        font-family: 'Nanum Gothic', sans-serif !important;
        white-space: pre-wrap !important; /* 줄바꿈 100% 보장 */
    }

    /* ==========================================================================
       🔴🟢 [버튼 전용 명확한 보색 대비 스타일]
       ========================================================================== */
    /* 모든 버튼 공통 폰트 및 굵은 글씨 지정 */
    div.stButton > button { 
        font-family: 'Nanum Gothic', sans-serif !important; 
        font-weight: 900 !important; 
        font-size: 16px !important;
        border-radius: 8px !important;
    }

    /* 🔴 1. ✨ [초연 시공명리 풀이 가동] 버튼 : 강렬한 빨간색 바탕 + 흰색 굵은 글자 */
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

    /* 🟢 2. 🖨️ [풀이 결과 인쇄 / PDF 저장] 버튼 : 완벽 보색 녹색 바탕 + 흰색 굵은 글자 */
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

    .color-목 { background-color: #2E7D32 !important; color: #FFFFFF !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important; }
    .color-화 { background-color: #C62828 !important; color: #FFFFFF !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important; }
    .color-토 { background-color: #F9A825 !important; color: #000000 !important; text-shadow: 1px 1px 2px rgba(255,255,255,0.8) !important; }
    .color-금 { background-color: #9E9E9E !important; color: #FFFFFF !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important; }
    .color-수 { background-color: #212121 !important; color: #FFFFFF !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important; }
    .color-무 { background-color: transparent !important; color: #000000 !important; }

    .color-unsung, td[style*="0D47A1"], div[style*="0D47A1"] { color: #0D47A1 !important; font-weight: 900 !important; }
    .color-shinsal, td[style*="C62828"], div[style*="C62828"] { color: #C62828 !important; font-weight: 900 !important; }

    .result-table { width: 100%; border-collapse: collapse; border: 2px solid #444 !important; margin-bottom: 5px !important; }
    .result-table td { border: 1px solid #444 !important; padding: 4px 2px !important; text-align: center; vertical-align: middle; font-weight: 900 !important; line-height: 1.3 !important; }
    .result-table tr:has(.ganji-cell) td { font-size: 24px !important; font-weight: 900 !important; padding: 10px 4px !important; -webkit-text-stroke: 0.5px rgba(0,0,0,0.3); }
    .result-table td:has(.unsung), .result-table td:has(.shinsal), .result-table td:has(.gen-shinsal) { font-weight: 900 !important; }

    .master-bar { padding: 1px 0 !important; margin: 1px 0 2px 0 !important; }
    .un-table td { padding: 1px 0 !important; line-height: 1.0 !important; }
    .ganji-cell { font-size: 18px !important; font-weight: 900 !important; }

    .top-header-cell { background-color: #1A237E !important; height: 30px !important; }
    .top-header-cell td { font-size: 15px !important; color: #FFFFFF !important; border: 1px solid #444 !important; font-weight: 900 !important; }
    .header-cell-main { background-color: #f5f5f5 !important; font-weight: 900 !important; white-space: nowrap; color: #1A237E !important; font-size: 15px !important; }

    .report-page { width: 210mm; max-width: 100%; margin: 30px auto; background-color: #FFFFFF !important; padding: 15mm 10mm; box-shadow: 0 0 20px rgba(0,0,0,0.15); border-radius: 20px; box-sizing: border-box; color: #000000; font-family: 'Nanum Myeongjo', serif; }
    .report-page h1, .report-page h3 { color: #1A237E !important; } 
    .choyeon-premium-report { font-family: 'Nanum Myeongjo', serif; }
    .content-box-loose { line-height: 1.8; font-size: 16px; text-align: justify; word-break: keep-all; padding: 0 !important; }

    @media print { 
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        .block-container { padding: 0 !important; margin: 0 !important; }
        .report-page { box-shadow: none; margin: 0 auto; page-break-after: always; width: 100%; border-radius: 0; padding: 0; }
        .report-page:last-of-type { page-break-after: auto; }
        .page-break-before { page-break-before: always; }
    }
    </style>"""

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

def get_info_header(p_icon, name, gender, marital, age, sol_str, lun_str, time_str, p_color="#1A237E"):
    return f"""
    <div style='text-align:center; margin-bottom:25px; line-height:1.6;'>
        <span style='font-size:22px; font-weight:900; color:{p_color}; letter-spacing:1px; white-space:nowrap;'>{p_icon} {name}님 ({gender}, {marital}, {age}세)</span><br>
        <span style='font-size:15px; font-weight:400; color:#444444; letter-spacing:0.5px; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span>
    </div>
    """

def get_saju_table(gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal):
    # '구분' 난 15% 배분, 나머지 4열 21.25% 균등 배분
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
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; color:#C62828 !important; font-weight:900; font-size:14px !important;'>십이신살</td>{shinsal}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>{gen_shinsal}</tr>
    </table>
    """

def generate_saju_table_data(gans, jjis, ds, gender, engine):
    """모든 테이블 HTML 조각을 조립하여 최종 테이블을 반환하는 함수"""
    
    # 여기서 각 행을 생성하는 로직을 html_views가 직접 처리
    gan_rel = "".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])
    gan_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, gans[0])}</td><td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(ds, gans[2])}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, gans[3])}</td>"
    gan_row = "".join([get_styled_td(g, f"color-{engine.get_color(g)}") for g in gans]) # get_styled_td 활용
    ji_row = "".join([f"<td class='color-{engine.get_color(j)} ganji-cell'>{j}</td>" for j in jjis])
    ji_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, jjis[0])}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, jjis[1])}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, jjis[2])}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, jjis[3])}</td>"
    jijanggan = "".join([f"<td style='padding:0 !important; border:1px solid #444 !important; height:45px; vertical-align:middle;'><div style='display:flex; flex-direction:column; justify-content:center; align-items:center; height:100%; font-size:13px; font-weight:900; line-height:1.0;'>{get_jijanggan_full(ds, jjis[i])}</div></td>" for i in range(4)])
    unsung = "".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{engine.get_unsung(ds, jjis[i])}</td>" for i in range(4)])
    shinsal = "".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{engine.get_12_shinsal(gans[3], jjis[i])}</td>" for i in range(4)])
    
    filtered_shinsals = ["<br>".join(engine.get_general_shinsal_filtered(i, gans, jjis, gender)[:6]) if engine.get_general_shinsal_filtered(i, gans, jjis, gender) else "-" for i in range(4)]
    gen_shinsal = "".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{filtered_shinsals[i]}</td>" for i in range(4)])
    ji_rel_rows = engine.get_ji_rel_rows_html(jjis)

    return get_saju_table(gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal)

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
    <div style='font-size: 16px; font-weight: 600; color: #333; text-align: justify; line-height: 1.8; margin-bottom: 10px; padding: 0 10px;'>
        <p style='text-indent: 15px; margin: 0 0 5px 0;'><b>"초연 시공 명리학"</b>는 5년에 한 번 돌아오는 '60월령과 60일주'의 조합으로 <b>3,600개 유형</b>으로 분류하지만, <b>"기존의 전통 명리학"</b>은 1년에 한 번 돌아오는 '12월지와 60일주'의 조합으로 <b>720개 유형</b>으로 분류하여 풀이합니다.</p> 
        <p style='text-indent: 15px; margin: 0 0 5px 0;'>따라서, <b>"본 초연 시공 명리학"</b>는 기존 전통명리학에 비하여 <b>5배</b>, 요즘 유행하는 16개 유형으로 분류하는 MBT'와 비교하면 무려 <b>225배</b> 더 정확한 사주풀이 입니다.</p>
    </div>
    """

def get_golden_text(name, w_val, i_val, s_name, s_type, s_desc):
    # s_name: 비식관구조, s_type: 조직봉사형, s_desc: 조직과 봉사활동을 통해 정체성을 추구
    return f"""
    <div style='font-family: "Nanum Myeongjo", serif; font-size: 16px; line-height: 1.8; color: #000000; 
                margin: 25px 0; border-top: 2px solid #1A237E; border-bottom: 2px solid #1A237E; 
                padding: 20px; background-color: #FAFAFA;'>
        <p style='text-indent: 0px; margin: 0;'>
            <b>초연 시공명리학적</b>으로 풀이하면 <b>{name}님</b>은 <b>'{w_val}'</b>의 시공간에서, 
            <b>'{i_val}'</b>의 성품을 가지고 태어나셨으며, 성격은 <b>'{s_name}'</b>인 <b>'{s_type}'</b>으로, <b>'{s_desc}'</b>하는 성향이 있습니다.
        </p>
    </div>
    """

def get_un_layout(title, content):
    return f"""
    <div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px;'>
        {content}
    </div>
    """

def generate_daewun_layout(daewun_list, direction_str, calc_d, get_oh_class_func):
    un_content = ""
    for data in daewun_list:
        bg_col = "#FFF9C4" if data["is_current"] else "transparent"
        b_left = "none" if data["is_first"] else "1px solid #ccc"
        un_content += get_un_cell(
            data["age_range"], data["ss_gan"], data["c_hanja"], get_oh_class_func(data["c_hangul"]), 
            data["j_hanja"], get_oh_class_func(data["j_hangul"]), data["ss_ji"], 
            data["un_sung"], data["shin_sal"], bg_col, b_left
        )
    return get_un_layout(f"[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]", un_content)

def get_un_cell(title_str, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, shinsal, bg_col, b_left):
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:5px; background-color:{bg_col}; min-width:50px;'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:13px;'>{title_str}</div>
        <div style='padding:3px 0; font-size:13px; font-weight:900; color:#333 !important;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:18px; font-weight:900; padding:3px 0;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:18px; font-weight:900; padding:3px 0;'>{ji}</div>
        <div style='padding:3px 0; font-size:13px; font-weight:900; color:#333 !important;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:12px; border-top:1px solid #ccc; padding-top:3px;'>{unsung}</div>
        <div class='color-shinsal' style='font-size:12px; border-top:1px solid #ccc; padding-top:3px;'>{shinsal}</div>
    </div>
    """

def get_sewun_layout(title, content):
    return f"""
    <div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px;'>
        {content}
    </div>
    """

def get_sewun_cell(title_str, tage, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, shinsal, bg_col, b_left):
    # 한자 변환 딕셔너리 (필요한 간지 추가 가능)
    hanja_map = {
        "갑자": "甲子", "을축": "乙丑", "병인": "丙寅", "정묘": "丁卯", "무진": "戊辰", "기사": "己巳", "경오": "庚午", "신미": "辛未", "임신": "壬申", "계유": "癸酉",
        "갑술": "甲戌", "을해": "乙亥", "병자": "丙子", "정축": "丁축", "무인": "戊寅", "기묘": "己卯", "경진": "庚辰", "신사": "辛巳", "임오": "壬午", "계미": "癸未",
        "갑신": "甲申", "을유": "乙酉", "병술": "丙戌", "정해": "丁亥", "무자": "戊子", "기축": "己丑", "경인": "庚寅", "신묘": "辛卯", "임진": "壬辰", "계사": "癸巳",
        "갑오": "甲午", "을미": "乙未", "병신": "丙申", "정유": "丁酉", "무술": "戊戌", "기해": "己亥", "경자": "庚子", "신축": "辛丑", "임인": "壬寅", "계묘": "癸卯",
        "갑진": "甲辰", "을사": "乙巳", "병오": "丙午", "정미": "丁未", "무신": "戊申", "기유": "己酉", "경술": "庚戌", "신해": "辛亥", "임자": "壬子", "계축": "癸丑",
        "갑인": "甲寅", "을묘": "乙卯", "병진": "丙辰", "정사": "丁巳", "무오": "戊午", "기미": "己未", "경신": "庚申", "신유": "辛酉", "임술": "壬戌", "계해": "癸亥"
    }
    
    # 제목에서 대운명 추출 및 한자 변환
    display_title = title_str
    for hangul, hanja in hanja_map.items():
        if hangul in title_str:
            display_title = title_str.replace(hangul, hanja)
            break
            
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:5px; background-color:{bg_col}; line-height:1.2;'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{display_title}<br>({tage}세)</div>
        <div style='padding:3px 0; font-size:12px; font-weight:900; color:#000000;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:16px; font-weight:900; padding:3px 0;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:16px; font-weight:900; padding:3px 0;'>{ji}</div>
        <div style='padding:3px 0; font-size:12px; font-weight:900; color:#000000;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:11px; border-top:1px solid #ccc; padding-top:2px;'>{unsung}</div>
        <div class='color-shinsal' style='font-size:11px; border-top:1px solid #ccc; padding-top:2px;'>{shinsal}</div>
    </div>
    """

def get_wolun_layout(title, content):
    return f"""
    <div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px;'>
        {content}
    </div>
    """

def get_wolun_cell(tm, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, shinsal, bg_col, b_left):
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:5px; background-color:{bg_col}; line-height:1.2;'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:13px; border-bottom:1px solid #ccc;'>{tm}월</div>
        <div style='padding:3px 0; font-size:12px; font-weight:900; color:#000000;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:16px; font-weight:900; padding:3px 0;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:16px; font-weight:900; padding:3px 0;'>{ji}</div>
        <div style='padding:3px 0; font-size:12px; font-weight:900; color:#000000;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:11px; border-top:1px solid #ccc; padding-top:2px;'>{unsung}</div>
        <div class='color-shinsal' style='font-size:11px; border-top:1px solid #ccc; padding-top:2px;'>{shinsal}</div>
    </div>
    """

def get_closing_html(name):
    return f"""
    <div style='margin-top: 40px; border-top: 2px dashed #444; padding-top: 25px;'>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드(bar-code)와 같지만, 우리가 살아가며 마주하는 스캐너(scanner)인 '운'은 늘 변화하며 흐릅니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 시공명리의 지혜와 궁금증이 있으시면 언제든 <b>'초연 시공명리 연구소'</b>의 문을 두드려 주십시오.</p>
        <p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: 900; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
        <div style='text-align: right; margin-top: 30px;'>
            <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
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
    """

def get_gunghap_saju_table(gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal):
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
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; color:#C62828 !important; font-weight:900; font-size:14px !important;'>십이신살</td>{shinsal}</tr>
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
    <div class='report-page'>
        <div style='border: 2px solid #1A237E; border-radius: 12px; padding: 25px; background-color:#FAFAFA;'>
            <h2 style='text-align:center; color:#1A237E; font-weight:900; margin-bottom: 30px;'>[ 부부 대운 흐름 비교 분석 ]</h2>
            <div style='margin-bottom: 40px;'>
                <h4 style='color:#3E2723; font-weight:900;'>&#9794; 남명 ({m_name}님) 대운 흐름</h4>
                {m_un_html}
            </div>
            <div>
                <h4 style='color:#3E2723; font-weight:900;'>&#9792; 여명 ({w_name}님) 대운 흐름</h4>
                {w_un_html}
            </div>
        </div>
    </div>
    <div class="page-break-before"></div>
    """

def get_daewun_compare_box(m_name, m_un_html, w_name, w_un_html):
    return f"""
    <div class='report-page' style='font-family: "Nanum Myeongjo", serif; margin-top: 20px;'>
        <div style='border: 1px solid #E0E0E0; border-radius: 16px; padding: 35px 25px; background: linear-gradient(145deg, #ffffff, #f8f9fa); box-shadow: 0 8px 24px rgba(0,0,0,0.04);'>
            
            <h2 style='text-align:center; color:#1A237E; font-size: 24px; font-weight:900; margin-bottom: 8px; letter-spacing: 1px;'>
                [ 부부 대운 흐름 교차 분석 ]
            </h2>
            <p style='text-align:center; color:#757575; font-size: 14px; margin-bottom: 35px; font-family: "Nanum Gothic", sans-serif;'>
                두 사람의 시공간 궤도를 한눈에 비교하는 대운 로드맵입니다.
            </p>
            
            <!-- 남명 섹션 -->
            <div style='margin-bottom: 35px; background: #ffffff; border-left: 5px solid #283593; padding: 20px 25px; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.03);'>
                <h4 style='color:#283593; font-weight:900; font-size: 18px; margin-top: 0; margin-bottom: 20px; display: flex; align-items: center;'>
                    <span style='font-size: 22px; margin-right: 8px;'>♂️</span> 남명 ({m_name}님) 대운 흐름
                </h4>
                <div style='overflow-x: auto;'>
                    {m_un_html}
                </div>
            </div>
            
            <!-- 여명 섹션 -->
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

def get_comparison_saju_cover_html(name, gender):
    """🔍 타 감명서 비교 (사주) 전용 표지 HTML"""
    return f"""<div style='text-align: center; padding: 40px 20px; background-color: #f9f9f9; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 30px;'>
<div style='font-size: 15px; color: #666; letter-spacing: 2px; margin-bottom: 10px;'>📊 초연 시공명리 R&D 리포트</div>
<div style='font-size: 21px; font-weight: 900; color: #1A237E; margin-bottom: 15px;'>🔍 {name}님 타 감명서 비교 분석 (개인사주)</div>
<div style='font-size: 14px; color: #555;'>신청인 성별: {gender} | 본 분석은 의뢰인이 제공한 타 감명서와 초연 시공명리를 1:1로 대조한 R&D 검증 보고서입니다.</div>
</div>
"""

def get_comparison_gunghap_cover_html(m_name, f_name):
    """⚖️ 타 감명서 비교 (궁합) 전용 표지 HTML"""
    return f"""<div style='text-align: center; padding: 40px 20px; background-color: #fffaf0; border-radius: 12px; border: 1px solid #f5e6cc; margin-bottom: 30px;'>
<div style='font-size: 15px; color: #b8860b; letter-spacing: 2px; margin-bottom: 10px;'>💕 초연 시공명리 R&D 리포트</div>
<div style='font-size: 21px; font-weight: 900; color: #B71C1C; margin-bottom: 15px;'>🔍 {m_name} & {f_name} 타 감명서 비교 분석 (궁합풀이)</div>
<div style='font-size: 14px; color: #555;'>남명: {m_name} & 여명: {f_name} | 두 사주의 체용 조화와 타 감명서의 명리학적 오류를 정밀 검증합니다.</div>
</div>
"""

def get_comparison_gumhap_report_html(m_name, f_name, other_report):
    return f"""<div style='margin-top: 40px; padding: 20px; border: 1px solid #ccc; background-color: #f5f5f5; border-radius: 8px;'>
<div style='font-size:21px; font-weight:900; margin-bottom: 15px; color:#333;'>💕 남성({m_name}) & 여성({f_name}) 타 감명서 원문 (의뢰인 제공)</div>
<div style='white-space: pre-wrap; font-family: Nanum Myeongjo; line-height: 1.6; color:#444;'>{other_report}</div>
</div>
"""

def get_original_report_html(other_report):
    return f"""<div style='margin-top: 40px; padding: 20px; border: 1px solid #ccc; background-color: #f5f5f5; border-radius: 8px;'>
<div style='font-size:21px; font-weight:900; margin-bottom: 15px; color:#333;'>📄 타 감명서 원문 (의뢰인 제공)</div>
<div style='white-space: pre-wrap; font-family: Nanum Myeongjo; line-height: 1.6; color:#444;'>{other_report}</div>
</div>
"""

def get_comparison_html(comp_fmt):
    return f"""<div style='margin-top: 30px; padding: 25px; border: 1px solid #B71C1C; background-color: #FFEBEE; border-radius: 10px;'>
<div style='font-size:21px; font-weight:900; margin-bottom: 20px; color:#B71C1C;'>🔍 초연 시공명리 vs 타 감명서 1:1 상세비교 분석</div>
{comp_fmt}
</div>
"""

def get_gunghap_score_visual_html(gh_engine):
    """
    구 버전 오리지널 시각화 차트, 최종 궁합 점수, 6대 세부항목 바, 클로징 멘트를 
    HTML 뷰로 완벽 조합하여 반환하는 전담 함수 (도넛: 하늘색 / 막대: 구버전 원본색)
    """
    # 💙 박사님 요청 반영: 도넛 원형 차트 및 점수 뱃지는 맑은 하늘색으로 지정
    sky_blue = "#38B6FF"
    
    # 📊 구 버전 ver 48.6 오리지널 막대 그래프 색상 (d['color']) 유지
    bars = "".join([
        f"<div style='display:flex; align-items:center; margin-bottom:12px;'>"
        f"<div style='width:130px; font-size:13px; font-weight:bold; color:#555;'>{d['label']}</div>"
        f"<div style='flex:1; height:12px; margin:0 10px;'><svg width='100%' height='12'><rect width='100%' height='12' rx='6' ry='6' fill='#eee' /><rect width='{d['pct']}%' height='12' rx='6' ry='6' fill='{d['color']}' /></svg></div>"
        f"<div style='width:35px; font-size:12px; font-weight:bold;'>{d['pct']}%</div>"
        f"</div>" 
        for d in gh_engine.details
    ])
    
    closing_original = (
        f"<div style='margin-top: 40px; padding-top: 30px; page-break-inside: avoid;'>\n"
        f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333;'>&nbsp;&nbsp;&nbsp;&nbsp;두 분의 <b style='color:#1A237E;'>'만남'</b>은 결코 우연이 아닌, <b style='color:#1A237E;'>'셀 수 없이 많은 시간 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 바코드지만, <b style='color:#1A237E;'>'궁합(宮合)'</b>은 두 바코드가 만나 그려내는 새로운 <b style='color:#1A237E;'>'하모니(harmonie)'</b>입니다.</p>\n"
        f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333; margin-top: 10px;'>&nbsp;&nbsp;&nbsp;&nbsp;서로의 다름을 이해하고 채워주는 든든한 <b style='color:#1A237E;'>'동반자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 시공간의 축복이 가득하시길 소망합니다. </p>\n"
        f"<div style='text-align: right; margin-top: 25px;'><span style='font-weight: 900; font-size: 16px; color: #1A237E; font-family: \"Nanum Myeongjo\", serif;'>- 초연 시공명리 연구소 드림 -</span></div>\n"
        f"</div>"
    )

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
        f"<div style='max-width:500px; margin:0 auto;'>\n{bars}\n</div>\n"
        f"{closing_original}"
    )
    return score_chart_html


def get_gunghap_closing(name1, name2): # 인자를 2개 받도록 수정
    return f"""
    <div style='margin-top: 20px;'>
        <p style='font-size:16px; text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>
        {name1}님과 {name2}님의 소중한 인연이 하늘의 뜻과 부모님의 깊은 사랑 속에서 찬란하게 빛을 발하기를 진심으로 기원합니다.</p>
        <p style='font-size:16px; text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>두 분의 앞날에 건강과 행복이 가득하시기를 간절히 축원합니다.</p>
        <div style='text-align: right; margin-top: 25px;'>
            <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>초연 시공명리 연구소</span>
        </div>
    </div>
    <div class='page-break-before'></div>
    """

def get_childbirth_taegil_card(border_col, idx, b_date_str, score, b_time_str, b_time_pillar, gestation_warning, conception_title, conception_str, conception_msg, baby_saju_html, ai_output_html):
    """
    [출산 택일 카드 뷰 - 좌측 세로선 완벽 제거 버전]
    """
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
    """
    [출산 길일 한눈에 보기 요약 박스 View]
    """
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

    html_code = f"""
    <div style="background-color:#F0F4F8; border:2px solid #1A237E; border-radius:10px; padding:18px; margin-top:15px; margin-bottom:25px;">
        <h4 style="color:#1A237E; margin-top:0; margin-bottom:12px; font-size:16px; border-bottom:1px solid #C5CAE9; padding-bottom:8px;">
            📋 출산 길일 한눈에 보기 (가임/배란 주기별 최적 길일)
        </h4>
        <ul style="list-style-type:none; padding-left:0; margin:0; line-height:1.8; font-size:14px; color:#2C3E50;">
            {summary_items}
        </ul>
    </div>
    """
    return html_code

def get_comparison_saju_cover(version, p_icon, name, sol_str, lun_str, time_str, today_str):
    """기존 개인사주 표지와 100% 동일한 레이아웃 (타이틀만 타 감명서 비교로 교체)"""
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 90%; max-width: 800px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
            <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                <h1 style='font-size: 26px !important; margin:0 !important; font-weight: 900; white-space: nowrap;'>🏮 초연 시공명리 타 감명서 비교</h1>
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
    <div clas

def get_comparison_gunghap_cover(app_version, male_name, female_name, today_str):
    """2. 타 감명서 비교 (궁합) 전용 표지 HTML"""
    return f"""
    <div class='page-break-before'></div>
    <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #2E7D32; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
            <div style='border-bottom:4px double #2E7D32; padding-bottom:20px; margin-bottom:40px;'>
                <h1 class='title-gothic' style='font-size: 32px !important; margin:0 !important; color:#2E7D32;'>초연 시공명리 타 감명서 비교 (궁합)</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px; color:#555;'>{app_version}</span>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>
                <h2 style='font-size: 20px; font-weight: 800; color: #2E7D32; margin-bottom: 10px;'>👫 대상 : {male_name} 님 & {female_name} 님</h2>
            </div>
            <p style='font-size: 16px; margin-top: 40px; font-weight: 800; color:#333;'>{today_str}</p>
            <p style='font-size: 20px; font-weight: 800; color: #2E7D32; margin-top: 15px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    """

def get_other_report_original_html(other_report_text):
    """3. 타 감명서 원문 카드 (공통)"""
    formatted_text = str(other_report_text).replace(chr(10), '<br>')
    return f"""
    <div class='page-break-before'></div>
    <div class='report-page' style='margin-top:20px;'>
        <div class='vip-inset-frame' style='border:2px solid #555555; padding:25px; background:#FAFAFA; border-radius:8px;'>
            <h2 style='text-align:center; color:#333333; font-family:"Malgun Gothic", sans-serif; font-weight:900; margin-bottom:20px;'>📜 타 감명서 원문</h2>
            <div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #111111; text-align: justify; word-break: keep-all;'>
                {formatted_text}
            </div>
        </div>
    </div>
    """

def get_comparison_result_box_html(comp_clean_text):
    """4. 1:1 상세비교 AI 본문 리포트 카드 (공통)"""
    return f"""
    <div class='page-break-before'></div>
    <div class='report-page' style='margin-top:20px;'>
        <div class='vip-inset-frame' style='border:2px solid #2E7D32; padding:25px; background:#FFFFFF; border-radius:8px;'>
            <h1 style='text-align:center; color:#2E7D32; font-size: 24px; font-weight: 800; border-bottom:2px solid #2E7D32; padding-bottom:15px; margin-bottom:20px;'>⚖️ 1:1 상세비교 본문 리포트</h1>
            <div style='font-family: "Nanum Myeongjo", serif; font-size:15px; line-height:1.8; color:#111111; text-align:justify;'>
                {comp_clean_text}
            </div>
        </div>
    </div>
    """

def get_ai_report_box(content):
    """5. 기본 AI 통변용 감싸기 카드"""
    return f"""
    <div style='margin-top:20px; padding:20px; border: 2px solid #1A237E; border-radius:10px; background-color:#F9F9F9;'>
        <h3 style='color:#1A237E; margin-bottom:15px; border-bottom:none;'>🔍 초연 시공명리 AI 정밀 통변</h3>
        <div class='content-box-loose'>
            {content}
        </div>
    </div>
    """
