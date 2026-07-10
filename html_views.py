def get_global_css():
    return """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic&family=Nanum+Myeongjo:wght@400;700;800&display=swap');
    .stApp { background-color: #FFFDE7 !important;}
    p, h1, h2, h3, h4, h5, h6, table, tr, td, div.report-page { font-family: 'Nanum Myeongjo', serif !important; }
    [data-testid="stSidebar"] {background-color: #F0F2F6 !important;}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {font-family: 'Nanum Gothic', sans-serif !important;}
    div.stButton > button { font-family: 'Nanum Gothic', sans-serif !important; font-weight: 900 !important; }
    div.stButton > button[kind="primary"] {background-color: #D32F2F !important; color: white !important;}
    div.stButton > button[kind="secondary"] {background-color: #E8F5E9 !important; color: #2E7D32 !important; border: 1px solid #81C784 !important;}
    .color-목 { background-color: #2E7D32 !important; color: #FFFFFF !important; }
    .color-화 { background-color: #C62828 !important; color: #FFFFFF !important; }
    .color-토 { background-color: #F9A825 !important; color: #000000 !important; }
    .color-금 { background-color: #9E9E9E !important; color: #FFFFFF !important; }
    .color-수 { background-color: #212121 !important; color: #FFFFFF !important; }
    .result-table { width: 100%; border-collapse: collapse; border: 3px solid #3E2723; table-layout: fixed; }
    .result-table td { border: 1px solid #444 !important; padding: 5px !important; text-align: center; vertical-align: middle; }
    .top-header-cell { background-color: #1A237E !important; }
    .header-cell-main { background-color: #f5f5f5 !important; font-weight: 900; white-space: nowrap; }
    .report-page, .report-page * { color: #000000 !important; }
    .report-page h1, .report-page h3 { color: #1A237E !important; } 
    .content-box-loose { line-height: 1.8; font-size: 16px; text-align: justify; word-break: keep-all; font-family: 'Nanum Myeongjo', serif !important; }
    span.material-symbols-rounded, i, svg {font-family: 'Material Symbols Rounded' !important;}
    @media print { 
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; }
        .block-container { padding: 0 !important; }
        .report-page { box-shadow: none; margin: 0 auto; page-break-after: always; width: 100%; }
        .page-break-before { page-break-before: always; }
    }
</style>
"""

def get_personal_cover(version, p_icon, name, sol_str, lun_str, time_str, today_str):
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 90%; max-width: 800px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
            <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                <h1 class='title-gothic' style='font-size: 24px !important; margin:0 !important; font-weight: 900; white-space: nowrap;'>🏮초연 시공명리 사주풀이</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>
                <h2 style='font-size: 24px; font-weight: 800; color: #1A237E; margin-bottom: 20px;'>{p_icon} 신청인 : {name} 님</h2>
                <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p>
                    <p style='margin: 5px 0 0 0; color: #1A237E; white-space: nowrap;'>{time_str}</p>
                </div>
            </div>
            <p style='font-size: 18px; margin-top: 50px; font-weight: 800;'>{today_str}</p>
            <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 20px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    """

def get_intro_html():
    return """
    <div style='font-size: 16px; font-weight: 600; color: #333; text-align: justify; line-height: 1.8; margin-bottom: 5px;'>
        <p style='text-indent: 15px; margin: 0 0 5px 0;'>기존 전통 명리학 사주풀이는 1년에 한 번 돌아오는 '12월지'와 '60일주'의 조합으로 720가지의 유형으로 시작합니다만,</p>
        <p style='text-indent: 15px; margin: 0 0 5px 0;'>본 초연 시공명리 사주풀이는 5년에 한 번 돌아오는 '60월령'과 '60일주'의 조합으로 3,600가지의 유형으로 보다 더 정밀한 분석이 가능합니다.</p>
        <p style='text-indent: 15px; margin: 0;'>기존 전통명리학에 비교하면 '5배', 요즘 유행하는 MBTI의 16가지 유형과 비교하면 무려 '225배' 더 세분화된 정밀한 사주풀이 분석입니다.</p>
    </div>
    """

def get_info_header(p_icon, name, gender, marital, age, sol_str, lun_str, time_str, p_color="#1A237E"):
    return f"""
    <div style='text-align:center; margin-bottom:25px; line-height:1.6; font-family:"Nanum Myeongjo", serif;'>
        <span style='font-size:20px; font-weight:800; color:{p_color}; letter-spacing:1px; white-space:nowrap;'>{p_icon} {name}님 ({gender}, {marital}, {age}세)</span><br>
        <span style='font-size:14px; font-weight:700; color:#444444; letter-spacing:0.5px; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span>
    </div>
    """

def get_saju_table(info_h, gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal):
    return f"""
    <div style='text-align:center; margin-bottom:10px;'>{info_h}</div>
    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
        <tr class='top-header-cell'>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>구분</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>시주</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>일주</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>월주</td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>년주</td>
        </tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간합충</td>{gan_rel}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간십성</td>{gan_ss}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>천간</td>{gan_row}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>지지</td>{ji_row}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지십성</td>{ji_ss}</tr>
        <tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지장간</td>{jijanggan}</tr>
        {ji_rel_rows}
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이운성</td>{unsung}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이신살</td>{shinsal}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>{gen_shinsal}</tr>
    </table>
    """

def get_master_bar(calc_d, c_mok, c_hwa, c_to, c_geum, c_su, guiin_str, n_gong, i_gong, samjae_color, cur_samjae):
    return f"""
    <div style='border:2px solid #3E2723; margin-top:15px; padding:8px 10px; display:flex; justify-content:space-between; align-items:center; font-family:"Noto Serif KR", serif !important; font-weight:900; font-size:12.5px; border-radius:8px; white-space:nowrap; background:#FFFDE7; letter-spacing:-0.7px;'>
        <div>🔢 대운수: <span style='color:#1A237E;'>{calc_d}</span></div>
        <div>💥 오행: 木({c_mok}) 火({c_hwa}) 土({c_to}) 金({c_geum}) 水({c_su})</div>
        <div>🌟 귀인: <span style='color:#1A237E;'>{guiin_str}</span></div>
        <div>🎯 공망: [년]<span style='color:#1A237E;'>{n_gong}</span> [일]<span style='color:#1A237E;'>{i_gong}</span></div>
        <div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div>
    </div>
    """

def get_un_layout(title, content):
    return f"""
    <div style='margin-top:10px; margin-bottom:8px; font-size:17px; font-weight:900; color:#1A237E; font-family:"Noto Serif KR", serif !important;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:12px; font-family:"Noto Serif KR", serif !important;'>
        {content}
    </div>
    """

def get_un_cell(title_str, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, shinsal, bg_col, b_left):
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:2px; background-color:{bg_col}; line-height:1.15;'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:11.5px; line-height:1.2; border-bottom:1px solid #ccc;'>{title_str}</div>
        <div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:15px; font-weight:900; padding:1px 0;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:15px; font-weight:900; padding:1px 0;'>{ji}</div>
        <div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{ss_ji}</div>
        <div style='font-size:11px; font-weight:normal; color:#0D47A1; border-top:1px solid #ccc; padding-top:1px;'>{unsung}</div>
        <div style='font-size:11px; font-weight:normal; color:#C62828; border-top:1px solid #ccc; padding-top:1px;'>{shinsal}</div>
    </div>
    """

def get_sewun_layout(title, content):
    return f"""
    <div style='margin-top:10px; margin-bottom:8px; font-size:17px; font-weight:900; color:#1A237E; font-family:"Noto Serif KR", serif !important;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:12px; font-family:"Noto Serif KR", serif !important;'>
        {content}
    </div>
    """

def get_sewun_cell(title_str, tage, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, shinsal, bg_col, b_left):
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:2px; background-color:{bg_col}; line-height:1.15;'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:11.5px; line-height:1.2; border-bottom:1px solid #ccc;'>{title_str}<br>({tage}세)</div>
        <div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:15px; font-weight:900; padding:1px 0;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:15px; font-weight:900; padding:1px 0;'>{ji}</div>
        <div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{ss_ji}</div>
        <div style='font-size:11px; font-weight:normal; color:#0D47A1; border-top:1px solid #ccc; padding-top:1px;'>{unsung}</div>
        <div style='font-size:11px; font-weight:normal; color:#C62828; border-top:1px solid #ccc; padding-top:1px;'>{shinsal}</div>
    </div>
    """

def get_wolun_layout(title, content):
    return f"""
    <div style='margin-top:10px; margin-bottom:8px; font-size:17px; font-weight:900; color:#1A237E; font-family:"Noto Serif KR", serif !important;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:12px; font-family:"Noto Serif KR", serif !important;'>
        {content}
    </div>
    """

def get_wolun_cell(tm, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, shinsal, bg_col, b_left):
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:2px; background-color:{bg_col}; line-height:1.15;'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:2px 0; font-size:11.5px; border-bottom:1px solid #ccc;'>{tm}월</div>
        <div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:15px; font-weight:900; padding:1px 0;'>{gan}</div>
        <div class='{j_cls}' style='font-size:15px; font-weight:900; padding:1px 0;'>{ji}</div>
        <div style='padding:1px 0; font-size:11.5px; font-weight:900; color:#000000;'>{ss_ji}</div>
        <div style='font-size:11px; font-weight:normal; color:#0D47A1; border-top:1px solid #ccc; padding-top:1px;'>{unsung}</div>
        <div style='font-size:11px; font-weight:normal; color:#C62828; border-top:1px solid #ccc; padding-top:1px;'>{shinsal}</div>
    </div>
    """

def get_closing_html(name):
    return f"""
    <div style='margin-top: 40px; border-top: 2px dashed #444; padding-top: 25px;'>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드(bar-code)와 같지만, 우리가 살아가며 마주하는 스캐너(scanner)인 '운'은 늘 변화하며 흐릅니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 시공명리의 지혜와 궁금증이 있으시면 언제든 <b>'초연 시공명리 연구소'</b>의 문을 두드려 주십시오.</p>
        <p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
        <div style='text-align: right; margin-top: 30px;'>
            <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
        </div>
    </div>
    """

def get_final_report_box(content_html):
    return f"""
    <div style='background-color:#FFFFFF; padding:40px; margin:20px auto; border:1px solid #E0E0E0; border-radius:15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); max-width:1000px;'>
        <div style='border: 2px solid #5D4037; border-radius: 12px; padding: 30px; background-color:#FAFAFA;'>
            {content_html}
        </div>
    </div>
    """

def get_gunghap_cover(version, app_icon, name, gender, marital, part_icon, f_name, f_gender, f_marital, today_str):
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 60px 30px; border-radius: 20px; text-align: center; background: white; width: 90%; max-width: 800px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
            <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:50px;'>
                <h1 style='font-size: 26px !important; margin:0 !important; font-weight: 900; color: #1A237E; white-space: nowrap;'>&#127982; 초연 시공명리 궁합 감명서</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span style='font-size: 14px; letter-spacing: 1px; color: #555;'>{version}</span>
                </div>
            </div>
            
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 40px 20px; border-radius: 15px; margin-bottom: 40px;'>
                <div style='text-align: center;'>
                    <span style='font-size: 22px; font-weight: 800; color: #1A237E;'>{app_icon} {name} 님</span>
                    <p style='font-size: 15px; color: #555; margin: 8px 0 0 0;'>{gender} / {marital}</p>
                </div>
                
                <div style='text-align: center; margin: 30px 0;'>
                    <span style='font-size: 24px; color: #1A237E; font-weight: 900; border-top: 1px dashed #CCC; border-bottom: 1px dashed #CCC; padding: 10px 40px;'>緣</span>
                </div>
                
                <div style='text-align: center;'>
                    <span style='font-size: 20px; font-weight: 800; color: #1A237E;'>{part_icon} {f_name} 님</span>
                    <p style='font-size: 15px; color: #555; margin: 8px 0 0 0;'>{f_gender} / {f_marital}</p>
                </div>
            </div>
            
            <p style='font-size: 16px; font-weight: 700; color: #444; margin-top: 50px;'>위 두 분의 인연을 시공간적 에너지 흐름과 음양오행의 조화로 정밀하게 풀이했습니다.</p>
            <p style='font-size: 16px; margin-top: 60px; font-weight: 800; color: #000;'>{today_str}</p>
            <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class="page-break-before"></div>
    """

def get_gunghap_person_box(table_html, master_bar_html, add_page_break=False):
    pb = '<div class="page-break-before"></div>' if add_page_break else ''
    return f"""
    <div style='background-color:#FFFFFF; padding:40px; margin:20px auto; border:1px solid #E0E0E0; border-radius:15px; max-width:1000px;'>
        <div style='border: 2px solid #5D4037; border-radius: 12px; padding: 30px; background-color:#FAFAFA;'>
            {table_html}
            {master_bar_html}
        </div>
    </div>
    {pb}
    """

def get_daewun_compare_box(m_name, m_un_html, w_name, w_un_html):
    return f"""
    <div style='background-color:#FFFFFF; padding:40px; margin:20px auto; border:1px solid #E0E0E0; border-radius:15px; max-width:1000px;'>
        <div style='border: 2px solid #1A237E; border-radius: 12px; padding: 30px; background-color:#FAFAFA;'>
            <h2 style='text-align:center; color:#1A237E; font-weight:900; margin-bottom: 30px;'>[ 부부 대운(大運) 흐름 비교 분석 ]</h2>
            <div style='margin-bottom: 40px;'>
                <h4 style='color:#3E2723; font-weight:800;'>&#9794; 男命 ({m_name}님) 대운 흐름</h4>
                {m_un_html}
            </div>
            <div>
                <h4 style='color:#3E2723; font-weight:800;'>&#9792; 女命 ({w_name}님) 대운 흐름</h4>
                {w_un_html}
            </div>
        </div>
    </div>
    <div class="page-break-before"></div>
    """

def get_gunghap_closing():
    return """
    <div style='margin-top: 20px;'>
        <p style='font-size:15px; text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>사랑하는 부부님, 하늘의 뜻과 부모님의 깊은 사랑이 한데 어우러져 귀한 인연이 이 세상에 찬란하게 빛을 발하며 나아가기를 진심으로 기원합니다.</p>
        <p style='font-size:15px; text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>두 분의 앞날에 건강과 행복이 가득하시기를 간절히 축원합니다.</p>
        <div style='text-align: right; margin-top: 25px;'>
            <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>초연 시공명리 연구소</span>
        </div>
    </div>
    <div class='page-break-before'></div>
    """

def get_ai_report_box(content):
    return f"""
    <div style='margin-top:20px; padding:20px; border: 2px solid #1A237E; border-radius:10px; background-color:#F9F9F9;'>
        <h3 style='color:#1A237E; margin-bottom:15px;'>🔍 초연 시공명리 AI 정밀 통변</h3>
        <div class='content-box-loose'>
            {content}
        </div>
    </div>
    """
