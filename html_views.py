def get_global_css():
    return """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic&family=Nanum+Myeongjo:wght@400;700;800&display=swap');
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");

    .stApp { background-color: #FFF8E1 !important;}
    p, h1, h2, h3, h4, h5, h6, table, tr, td, div.report-page { font-family: 'Noto Serif KR', 'Nanum Myeongjo', serif !important; }
    
    [data-testid="stSidebar"] {background-color: #F0F2F6 !important;}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {font-family: 'Nanum Gothic', sans-serif !important;}
    
    div.stButton > button { font-family: 'Nanum Gothic', sans-serif !important; font-weight: 900 !important; }
    div.stButton > button[kind="primary"] {background-color: #D50000 !important; color: white !important; border: none !important; height: 45px !important;}
    div.stButton > button[kind="secondary"] {background-color: #E8F5E9 !important; color: #2E7D32 !important; border: 1px solid #81C784 !important;}
    
    /* 🚨 오행별 색상 완벽 통제 (배경색 + 글자색 + 보색 텍스트 그림자 효과) */
    .color-목 { background-color: #2E7D32 !important; color: #FFFFFF !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important; }
    .color-화 { background-color: #C62828 !important; color: #FFFFFF !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important; }
    .color-토 { background-color: #F9A825 !important; color: #000000 !important; text-shadow: 1px 1px 2px rgba(255,255,255,0.8) !important; }
    .color-금 { background-color: #9E9E9E !important; color: #FFFFFF !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important; }
    .color-수 { background-color: #212121 !important; color: #FFFFFF !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important; }
    .color-무 { background-color: transparent !important; color: #000000 !important; }

    /* 🚨 십이운성(파란색), 십이신살(빨간색) 전역 통일 강제 */
    .color-unsung, td[style*="0D47A1"], div[style*="0D47A1"] { color: #0D47A1 !important; font-weight: 900 !important; }
    .color-shinsal, td[style*="C62828"], div[style*="C62828"] { color: #C62828 !important; font-weight: 900 !important; }

    /* 🚨 사주원국 천간/지지 행 전체 24px 확대 및 입체감 강화 */
    .result-table tr:has(.ganji-cell) td { font-size: 24px !important; font-weight: 900 !important; padding: 10px 4px !important; -webkit-text-stroke: 0.5px rgba(0,0,0,0.3); }

    /* 테이블 테두리 및 내부 선 통일 */
    .result-table { width: 100%; border-collapse: collapse; border: 2px solid #444 !important; }
    .result-table td { border: 1px solid #444 !important; padding: 2px !important; text-align: center; vertical-align: middle; font-weight: 900 !important; }

    /* 십이운성, 십이신살, 일반신살 굵기 강화 (기존 색상 유지) */
    .result-table td:has(.unsung), .result-table td:has(.shinsal), .result-table td:has(.gen-shinsal) { font-weight: 900 !important; }

    /* 대운 흐름표의 간지 설정 (이미 정의된 클래스 활용) */
    .ganji-cell { font-size: 18px !important; font-weight: 900 !important; }
    
    .top-header-cell { background-color: #1A237E !important; height: 30px !important; }
    .top-header-cell td { font-size: 15px !important; color: #FFFFFF !important; border: 1px solid #444 !important; font-weight: 900 !important;}
    
    .header-cell-main { background-color: #f5f5f5 !important; font-weight: 900 !important; white-space: nowrap; color: #1A237E !important; font-size: 15px !important;}
    
    .report-page { width: 210mm; max-width: 100%; margin: 30px auto; background-color: #FFFFFF !important; padding: 15mm 10mm; box-shadow: 0 0 20px rgba(0,0,0,0.15); border-radius: 20px; box-sizing: border-box; }
    .report-page { color: #000000; }
    .report-page h1, .report-page h3 { color: #1A237E !important; } 
    
    .content-box-loose { line-height: 1.8; font-size: 16px; text-align: justify; word-break: keep-all; padding: 0 !important; }
    
    @media print { 
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; }
        .block-container { padding: 0 !important; margin: 0 !important; }
        .report-page { box-shadow: none; margin: 0 auto; page-break-after: always; width: 100%; border-radius: 0; padding: 0; }
        .report-page:last-of-type { page-break-after: auto; }
        .page-break-before { page-break-before: always; }
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

def get_intro_html():
    return """
    <div style='font-size: 16px; font-weight: 600; color: #333; text-align: justify; line-height: 1.8; margin-bottom: 10px; padding: 0 10px;'>
        <p style='text-indent: 15px; margin: 0 0 5px 0;'>기존 전통 명리학 사주풀이는 1년에 한 번 돌아오는 '12월지'와 '60일주'의 조합으로 720가지의 유형으로 분석하지만,</p>
        <p style='text-indent: 15px; margin: 0 0 5px 0;'>본 초연 시공명리 사주풀이는 5년에 한 번 돌아오는 '60월령'과 '60일주'의 조합으로 3,600가지의 유형으로 분석하기 때문에, 기존 전통명리학에 비교하면 '5배', 요즘 유행하는 MBTI의 16가지 유형과 비교하면 무려 '225배' 더 세분화된 정밀한 사주풀이 분석입니다.</p>
    </div>
    """

def get_info_header(p_icon, name, gender, marital, age, sol_str, lun_str, time_str, p_color="#1A237E"):
    return f"""
    <div style='text-align:center; margin-bottom:25px; line-height:1.6;'>
        <span style='font-size:22px; font-weight:900; color:{p_color}; letter-spacing:1px; white-space:nowrap;'>{p_icon} {name}님 ({gender}, {marital}, {age}세)</span><br>
        <span style='font-size:15px; font-weight:400; color:#444444; letter-spacing:0.5px; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span>
    </div>
    """

def get_saju_table(info_h, gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal):
    # 수정: 테이블 바로 위에 info_h(이름/생년월일/시간 헤더)를 위치시킵니다.
    return f"""
    {info_h}
    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center; margin-top:10px;'>
        <tr class='top-header-cell'>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>구분</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>시주</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>일주</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>월주</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>년주</td>
        </tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간합충</td>{gan_rel}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간십성</td>{gan_ss}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:24px !important;'>천간</td>{gan_row}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:24px !important;'>지지</td>{ji_row}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지십성</td>{ji_ss}</tr>
        <tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지장간</td>{jijanggan}</tr>
        {ji_rel_rows}
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; color:#0D47A1 !important; font-weight:900; font-size:14px !important;'>십이운성</td>{unsung}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; color:#C62828 !important; font-weight:900; font-size:14px !important;'>십이신살</td>{shinsal}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>{gen_shinsal}</tr>
    </table>
    """

def generate_saju_table_data(info_h, gans, jjis, ds, gender, engine):
    """모든 테이블 HTML 조각을 조립하여 최종 테이블을 반환하는 함수"""
    
    # 여기서 각 행을 생성하는 로직을 html_views가 직접 처리
    gan_rel = "".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])
    gan_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, gans[0])}</td><td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(ds, gans[2])}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, gans[3])}</td>"
    gan_row = "".join([get_styled_td(g, f"color-{engine.get_color(g)}") for g in gans]) # get_styled_td 활용
    ji_row = "".join([f"<td class='color-{engine.get_color(j)} ganji-cell'>{j}</td>" for j in jjis])
    ji_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, jjis[0])}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, jjis[1])}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, jjis[2])}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, jjis[3])}</td>"
    jijanggan = "".join([f"<td style='padding:0; border:1px solid #444;'>{engine.get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])
    unsung = "".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{engine.get_unsung(ds, jjis[i])}</td>" for i in range(4)])
    shinsal = "".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{engine.get_12_shinsal(gans[3], jjis[i])}</td>" for i in range(4)])
    
    filtered_shinsals = ["<br>".join(engine.get_general_shinsal_filtered(i, gans, jjis, gender)[:6]) if engine.get_general_shinsal_filtered(i, gans, jjis, gender) else "-" for i in range(4)]
    gen_shinsal = "".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{filtered_shinsals[i]}</td>" for i in range(4)])
    ji_rel_rows = engine.get_ji_rel_rows_html(jjis)

    return get_saju_table(info_h, gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal)

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

def get_golden_text(name, w_val, i_val):
    return f"""
    <div style='font-family: "Nanum Myeongjo", serif; font-size: 16px; line-height: 1.8; color: #000000; 
                margin: 25px 0; border-top: 2px solid #1A237E; border-bottom: 2px solid #1A237E; 
                padding: 20px; background-color: #FAFAFA;'>
        <p style='text-indent: 0px; margin: 0;'>
            <b>{name}님</b>은 <b>'{w_val}'</b>의 시공간에서, <b>'{i_val}'</b>의 성품을 가지고 태어나셨습니다.
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
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:5px; background-color:{bg_col}; line-height:1.2;'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{title_str}<br>({tage}세)</div>
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
            <h2 style='text-align:center; color:#1A237E; font-weight:900; margin-bottom: 30px;'>[ 부부 대운(大運) 흐름 비교 분석 ]</h2>
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

def get_ai_report_box(content):
    return f"""
    <div style='margin-top:20px; padding:20px; border: 2px solid #1A237E; border-radius:10px; background-color:#F9F9F9;'>
        <h3 style='color:#1A237E; margin-bottom:15px; border-bottom:none;'>🔍 초연 시공명리 AI 정밀 통변</h3>
        <div class='content-box-loose'>
            {content}
        </div>
    </div>
    """
