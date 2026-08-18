# ==============================================================================
# html_views.py (ver 72.7 Master - 화면 단일 프레임 & 인쇄 A4 분할 듀얼 완결본)
# ==============================================================================
# [핵심 반영 사항]
# 1. 화면(Screen) 뷰: A4 바깥선 완전 제거(투명), 단일 .vip-inset-frame 안에서 연속 출력
# 2. 인쇄/PDF(@media print) 뷰: .page-break 엔진이 작동하여 A4 1장씩 정밀 분할 출력
# 3. 동양 전통 예법 엄수: 남명/여명 인명 붉은색(朱書) 전면 배제 (품격 있는 먹색 #111111 적용)
# 4. 서체 전면 통일: 전 표지, 원국표, 마스터바, 황금문구, 통변 본문 '나눔명조(Nanum Myeongjo)' 강제 적용
# 5. 궁합 표지 통합: 타이틀 1줄 강제 방어 및 남/녀 생년월일 <strong> 볼드체 적용 (DRY 통일)
# ==============================================================================
import re
import streamlit as st

# ==============================================================================
# 📦 섹션 1. 글로벌 스타일 (CSS) 및 AI 통변 텍스트 포맷터
# ==============================================================================

def get_global_css():
    """전체 시스템 UI/UX 및 화면/인쇄 듀얼 분리 스타일시트"""
    return """<style>
    @import url("https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Nanum+Gothic:wght@400;700;800;900&display=swap");

    .stApp { background-color: #FFF8E1 !important; }
    
    /* 사이드바 컨트롤 영역 (고딕체 유지) */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span[data-testid="stMarkdownContainer"] { 
        font-family: 'Nanum Gothic', sans-serif !important; 
    }
    div[data-testid="stSidebar"] * { font-size: 14px !important; }
    div[data-testid="stRadio"] label p { font-size: 14px !important; }
    div[data-testid="stCheckbox"] label p { font-size: 14px !important; }

    /* 감명서 리포트 전 영역 나눔명조체 통일 */
    .report-page, .report-page *, .cover-page, div.cover-page *, .choyeon-premium-report, .result-table td { 
        font-family: 'Nanum Myeongjo', 'Batang', serif !important; 
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .b-text { font-weight: 800 !important; color: #000000 !important; display: inline-block; }
    .b-text-point { font-weight: 800 !important; color: #1A237E !important; display: inline-block; }

    /* 버튼 기본 공통 규격 */
    div.stButton > button { 
        font-family: 'Nanum Gothic', sans-serif !important; 
        font-weight: 900 !important; 
        font-size: 16px !important; 
        border-radius: 8px !important; 
        height: 50px !important; 
        border: none !important; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.12) !important; 
    }

    /* 1. [초연 시공명리 풀이 가동] (Primary) */
    div.stButton > button[kind="primary"],
    div.stButton > button[data-testid="baseButton-primary"],
    div.stButton > button[data-testid="stBaseButton-primary"] { 
        background-color: #D32F2F !important; 
        color: #FFFFFF !important; 
    }
    div.stButton > button[kind="primary"]:hover,
    div.stButton > button[data-testid="baseButton-primary"]:hover,
    div.stButton > button[data-testid="stBaseButton-primary"]:hover { 
        background-color: #B71C1C !important; 
        color: #FFFFFF !important; 
    }

    /* 2. [풀이결과 인쇄/PDF 저장] (Secondary) */
    div.stButton > button[kind="secondary"],
    div.stButton > button[data-testid="baseButton-secondary"],
    div.stButton > button[data-testid="stBaseButton-secondary"] { 
        background-color: #00A843 !important; 
        color: #FFFFFF !important; 
    }
    div.stButton > button[kind="secondary"]:hover,
    div.stButton > button[data-testid="baseButton-secondary"]:hover,
    div.stButton > button[data-testid="stBaseButton-secondary"]:hover { 
        background-color: #008937 !important; 
        color: #FFFFFF !important; 
    }

    /* A4 백지 캔버스 */
    .report-page { 
        width: 210mm; 
        min-height: 297mm; 
        max-width: 100%; 
        margin: 20px auto; 
        background-color: #FFFFFF !important; 
        border: none !important; 
        box-shadow: none !important; 
        padding: 12mm 10mm; 
        box-sizing: border-box; 
        color: #222222; 
    }

    /* 안쪽 표준 둥근 사각 액자 */
    .vip-inset-frame { 
        border: 2px solid #3E2723 !important; 
        border-radius: 12px !important; 
        padding: 25px !important; 
        background-color: #FFFFFF !important; 
        box-shadow: none !important; 
        box-sizing: border-box;
    }

    /* 오행 색상 규격 */
    .color-목 { background: #2E7D32 !important; color: #FFF !important; }
    .color-화 { background: #C62828 !important; color: #FFF !important; }
    .color-토 { background: #F9A825 !important; color: #000 !important; }
    .color-금 { background: #9E9E9E !important; color: #FFF !important; }
    .color-수 { background: #212121 !important; color: #FFF !important; }

    /* 원국표 테이블 규격 */
    .result-table { width: 100%; border-collapse: collapse !important; border: 3px solid #3E2723 !important; margin-bottom: 12px; table-layout: fixed; }
    .result-table td { border: 1px solid #444 !important; padding: 2px 0 !important; text-align: center; vertical-align: middle; font-weight: 800 !important; font-size: 13px; line-height: 1.25 !important; }
    .ganji-cell-24 { font-size: 24px !important; font-weight: 900 !important; }

    .top-header-cell { background-color: #1A237E !important; height: 30px !important; }
    .top-header-cell td { background-color: #1A237E !important; color: #FFFFFF !important; font-weight: 900 !important; font-size: 15px !important; border: 1px solid #444 !important; }
    .header-cell-main, .header-cell-sub { background-color: #E8EAF6 !important; color: #000000 !important; font-weight: 800 !important; font-size: 13px !important; }

    /* 인쇄 및 PDF 저장 시 자동 A4 낱장 분할 엔진 */
    .page-break { display: none; }

    @media print { 
        @page { size: A4 portrait; margin: 12mm 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; -webkit-print-color-adjust: exact !important; }
        .report-page { box-shadow: none; margin: 0 auto; width: 100%; padding: 0; }
        .page-break { display: block !important; page-break-after: always !important; break-after: page !important; height: 1px; }
        .vip-inset-frame { box-shadow: none !important; border: 1.5px solid #333333 !important; }
    }
    </style>
    """

def format_ai_text_to_html(text):
    """
    AI 생성 텍스트 포맷터 (단정하고 눈이 편안한 표준 명조체 규격)
    - 대제목(1.) 20px Bold 800
    - 특수헤더 17px Bold 800 (중앙정렬, 밑줄 2.5px solid #1A237E)
    - 소제목(1)) 17px Bold 700 (검정색 #000000)
    - 소소제목((1)) 16px Bold 700 (진먹색 #333333)
    - 일반본문 15.5px Regular 400 (기본 정규 굵기, 줄간격 1.85, 편안한 먹색 #222222)
    """
    if not text:
        return ""
        
    lines = str(text).split('\n')
    html_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 마크다운 찌꺼기 제거
        line = line.replace('*', '').replace('#', '')

        # 🌟 [특수 헤더] 수석보좌관 1:1 장단점 정밀 비교 등
        if '수석보좌관' in line or '장단점 정밀 비교' in line or line.startswith('[수석보좌관'):
            html_lines.append(
                f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 17px; font-weight: 800; color: #1A237E; "
                f"text-align: center; padding-bottom: 6px; margin-top: 18px; margin-bottom: 8px; border-bottom: 2.5px solid #1A237E; letter-spacing: -0.3px;'>"
                f"{line}</div>"
            )
        # 🌟 [대제목 1.] (20px / 800)
        elif re.match(r'^\d+\.\s', line):
            html_lines.append(
                f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 20px; font-weight: 800; color: #000000; "
                f"margin-top: 22px; margin-bottom: 10px; border-bottom: 1px solid #E0E0E0; padding-bottom: 5px; letter-spacing: -0.5px;'>"
                f"{line}</div>"
            )
        # 🌟 [소제목 1)] (17px / 700)
        elif re.match(r'^\d+\)\s', line):
            html_lines.append(
                f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 17px; font-weight: 700; color: #000000; "
                f"margin-top: 14px; margin-bottom: 6px; letter-spacing: -0.3px;'>"
                f"{line}</div>"
            )
        # 🌟 [소소제목 (1)] (16px / 700)
        elif re.match(r'^\(\d+\)\s', line):
            html_lines.append(
                f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 16px; font-weight: 700; color: #333333; "
                f"margin-top: 10px; margin-bottom: 4px; letter-spacing: -0.2px;'>"
                f"{line}</div>"
            )
        # 🌟 [일반 본문] (15.5px / 500 Medium 탄탄한 두께 / 선명한 먹색 #111111)
        else:
            if line.startswith('-'):
                html_lines.append(
                    f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15.5px; font-weight: 500; line-height: 1.85; "
                    f"color: #111111; text-align: justify; margin-top: 4px; margin-bottom: 8px; text-indent: 5px; padding-left: 10px;'>"
                    f"{line}</p>"
                )
            else:
                html_lines.append(
                    f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15.5px; font-weight: 500; line-height: 1.85; "
                    f"color: #111111; text-align: justify; margin-top: 4px; margin-bottom: 8px; text-indent: 15px;'>"
                    f"{line}</p>"
                )
            
    return "\n".join(html_lines)
# ==============================================================================
# 📦 섹션 2. 공통 역학 테이블 및 컴포넌트 모듈 (원국, 대운, 세운, 월운, 주간운)
# ==============================================================================

def td_func(val, engine):
    oh = engine.get_color(val)
    cls_str = f"color-{oh}" if oh != '무' else ""
    return f"<td class='{cls_str} ganji-cell-24' style='border:1px solid #444 !important; width:21.25%;'>{val}</td>"

def get_saju_table(gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, y_shinsal, d_shinsal, gen_shinsal):
    """사주팔자 원국 표 HTML 구조"""
    return f"""
    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
        <tr class='top-header-cell'>
            <td style='width:15%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>구분</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>시주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>일주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>월주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>년주</td>
        </tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:800;'>천간합충</td>{gan_rel}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:800;'>천간십성</td>{gan_ss}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:16px !important;'>천간</td>{gan_row}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:16px !important;'>지지</td>{ji_row}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:800;'>지지십성</td>{ji_ss}</tr>
        <tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:800;'>지장간</td>{jijanggan}</tr>
        {ji_rel_rows}
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:800;'>십이운성</td>{unsung}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:800;'>년지신살</td>{y_shinsal}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:800;'>일지신살</td>{d_shinsal}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:800;'>일반신살</td>{gen_shinsal}</tr>
    </table>
    """

def generate_saju_table_data(gans, jjis, ds, gender, engine):
    """사주 원국 데이터를 연산하여 표 HTML 생성"""
    gan_rel = "".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])
    
    hs, ds_val, ms, ys = gans[0], gans[1], gans[2], gans[3]
    gan_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, hs)}</td>" \
             f"<td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td>" \
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
        b_bot = "2px solid #CCCCCC !important" if l_idx == 1 else "1px solid #444 !important"
        
        cells = []
        for ci in range(4):
            if ci == r_idx:
                if r_idx == 0:   lbl_txt = f"({jjis[r_idx]})→"
                elif r_idx == 3: lbl_txt = f"←({jjis[r_idx]})"
                else:            lbl_txt = f"←({jjis[r_idx]})→"
                cells.append(f"<td style='color:#1A237E; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important; padding:2px 0 !important; vertical-align: middle;'>{lbl_txt}</td>")
            else:
                rel_val = engine.get_ji_rel_set(jjis[r_idx], jjis[ci])
                txt_color = "#000" if rel_val != "-" else "#BBB"
                cells.append(f"<td style='color:{txt_color}; font-weight:800; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important; padding:2px 0 !important; vertical-align: middle;'>{rel_val}</td>")
                
        lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:13px !important; vertical-align: middle; padding:0 !important;'>합충형파해</td>" if l_idx == 0 else ""
        ji_rel_rows += f"<tr style='border:none; height:auto;'>{lbl}{''.join(cells)}</tr>"

    unsung = "".join([f"<td style='color:#0D47A1; font-weight:800; border:1px solid #444 !important;'>{engine.get_unsung(ds, jjis[i])}</td>" for i in range(4)])

    y_shinsal_tds, d_shinsal_tds = [], []
    for i in range(4):
        y_s = engine.get_12_shinsal(yb, jjis[i]) if jjis[i] != "-" else "-"
        raw_d = engine.get_12_shinsal(db, jjis[i]) if jjis[i] != "-" else "-"
        clean_d = str(raw_d).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
        d_s = f"({clean_d})" if clean_d and clean_d != "-" else "(-)"
        
        y_shinsal_tds.append(f"<td style='color:#C62828; font-weight:800; font-size:13px; border:1px solid #444 !important; padding:3px 0;'>{y_s}</td>")
        d_shinsal_tds.append(f"<td style='color:#C62828; font-weight:800; font-size:13px; border:1px solid #444 !important; padding:3px 0;'>{d_s}</td>")
        
    y_shinsal_html = "".join(y_shinsal_tds)
    d_shinsal_html = "".join(d_shinsal_tds)

    gen_shinsals = []
    for i in range(4):
        filtered = engine.get_general_shinsal_filtered(i, gans, jjis, gender)
        gen_shinsals.append("<br>".join(filtered[:6]) if filtered else "-")
    gen_shinsal = "".join([f"<td style='vertical-align:top; padding:2px; font-weight:800; border:1px solid #444 !important;'>{s}</td>" for s in gen_shinsals])

    return get_saju_table(gan_rel, gan_ss, gan_row_html, ji_row_html, ji_ss_html, jijanggan_html, ji_rel_rows, unsung, y_shinsal_html, d_shinsal_html, gen_shinsal)

def get_master_bar(calc_d, m, f, e, mtl, w, guiin, n_gong, i_gong, samjae_color, cur_samjae):
    """사주팔자 하단 핵심 명리 종합 바 (정통 나눔명조 적용)"""
    return f"""
    <div style="background:#FFF8E1; padding:8px 12px; border-radius:8px; margin:10px 0; border:1px solid #3E2723; font-family:'Nanum Myeongjo', serif; font-weight:700; font-size:13px; color:#1A237E; display:flex; justify-content:space-between; align-items:center; white-space:nowrap;">
        <span style="flex: 1; text-align: center;">🔢 대운수: {calc_d}</span>
        <span style="flex: 1; text-align: center;">💥 오행: 木{m} 火{f} 土{e} 金{mtl} 水{w}</span>
        <span style="flex: 1; text-align: center;">🌟 천을귀인: {guiin}</span>
        <span style="flex: 1; text-align: center;">🎯 공망: [년]{n_gong} [일]{i_gong}</span>
        <span style="flex: 1; text-align: center;">🌪️ 삼재: <span style="color:{samjae_color};">{cur_samjae}</span></span>
    </div>
    """

def get_un_layout(title, content):
    return f"""
    <div style='margin-top:14px; margin-bottom:8px; font-size:16px; font-weight:800; color:#1A237E; font-family:"Nanum Myeongjo", serif;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:10px; table-layout:fixed; font-family:"Nanum Myeongjo", serif;'>
        {content}
    </div>
    """

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
    <div style='flex:1; width:10%; {active_style} text-align:center; padding-bottom:4px; background-color:{bg_col}; min-width:0; display:flex; flex-direction:column; box-sizing:border-box; overflow:hidden;'>
        <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:800; font-size:12px; height:24px; display:flex; align-items:center; justify-content:center; white-space:nowrap; letter-spacing:-0.5px;'>{title_str}</div>
        <div style='font-size:12px; font-weight:800; color:#000000; height:22px; display:flex; align-items:center; justify-content:center;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:17px; font-weight:900; height:28px; display:flex; align-items:center; justify-content:center;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:17px; font-weight:900; height:28px; display:flex; align-items:center; justify-content:center;'>{ji}</div>
        <div style='font-size:12px; font-weight:800; color:#000000; height:22px; display:flex; align-items:center; justify-content:center;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:12px; font-weight:800; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#0D47A1;'>{u_val}</span></div>
        <div class='color-shinsal' style='font-size:12px; font-weight:800; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{y_val}</span></div>
        <div class='color-shinsal-day' style='font-size:12px; font-weight:800; border-top:1px dashed #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{d_val}</span></div>
    </div>
    """

def generate_daewun_layout(daewun_list, direction_str, calc_d, get_oh_class_func):
    un_content = ""
    for data in daewun_list:
        bg_col = "#FFF9C4" if data.get("is_current", False) else "transparent"
        b_left = "none" if data.get("is_first", False) else "1px solid #ccc"
        y_s_val = data.get("y_shinsal", data.get("shin_sal", "-"))
        d_s_val = data.get("d_shinsal", "-")
        
        un_content += get_un_cell(
            data["age_range"], data["ss_gan"], data["c_hanja"], get_oh_class_func(data["c_hangul"]), 
            data["j_hanja"], get_oh_class_func(data["j_hangul"]), data["ss_ji"], 
            data["un_sung"], y_s_val, d_s_val, bg_col, b_left, data.get("is_current", False)
        )
    return get_un_layout(f"[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]", un_content)

def get_sewun_layout(title, content):
    return f"""
    <div style='margin-top:14px; margin-bottom:8px; font-size:16px; font-weight:800; color:#1A237E; font-family:"Nanum Myeongjo", serif;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:10px; table-layout:fixed; font-family:"Nanum Myeongjo", serif;'>
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
    <div style='flex:1; width:8.33%; {active_style} text-align:center; padding-bottom:4px; background-color:{bg_col}; display:flex; flex-direction:column; box-sizing:border-box; min-width:0; overflow:hidden;'>
        <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:800; font-size:12px; height:26px; display:flex; align-items:center; justify-content:center; box-sizing:border-box; white-space:nowrap;'>
            <span>{title_str}</span>
        </div>
        <div style='font-size:12px; font-weight:800; color:#000000; height:20px; display:flex; align-items:center; justify-content:center;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:15px; font-weight:900; height:26px; display:flex; align-items:center; justify-content:center;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:15px; font-weight:900; height:26px; display:flex; align-items:center; justify-content:center;'>{ji}</div>
        <div style='font-size:12px; font-weight:800; color:#000000; height:20px; display:flex; align-items:center; justify-content:center;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:12px; font-weight:800; border-top:1px solid #ccc; height:20px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#0D47A1;'>{u_val}</span></div>
        <div class='color-shinsal' style='font-size:12px; font-weight:800; border-top:1px solid #ccc; height:20px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{y_val}</span></div>
        <div class='color-shinsal-day' style='font-size:12px; font-weight:800; border-top:1px dashed #ccc; height:20px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{d_val}</span></div>
    </div>
    """

def get_wolun_layout(title, content):
    return f"""
    <div style='margin-top:14px; margin-bottom:8px; font-size:16px; font-weight:800; color:#1A237E; font-family:"Nanum Myeongjo", serif;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:10px; table-layout:fixed; font-family:"Nanum Myeongjo", serif;'>
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
    <div style='flex:1; width:8.33%; {active_style} text-align:center; padding-bottom:4px; background-color:{bg_col}; display:flex; flex-direction:column; box-sizing:border-box; min-width:0; overflow:hidden;'>
        <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:800; font-size:12px; height:24px; display:flex; align-items:center; justify-content:center; white-space:nowrap; letter-spacing:-0.5px;'>{tm}월</div>
        <div style='font-size:12px; font-weight:800; color:#000000; height:20px; display:flex; align-items:center; justify-content:center;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:15px; font-weight:900; height:26px; display:flex; align-items:center; justify-content:center;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:15px; font-weight:900; height:26px; display:flex; align-items:center; justify-content:center;'>{ji}</div>
        <div style='font-size:12px; font-weight:800; color:#000000; height:20px; display:flex; align-items:center; justify-content:center;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:12px; font-weight:800; border-top:1px solid #ccc; height:20px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#0D47A1;'>{u_val}</span></div>
        <div class='color-shinsal' style='font-size:12px; font-weight:800; border-top:1px solid #ccc; height:20px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{y_val}</span></div>
        <div class='color-shinsal-day' style='font-size:12px; font-weight:800; border-top:1px dashed #ccc; height:20px; display:flex; align-items:center; justify-content:center; overflow:hidden;'><span style='color:#C62828;'>{d_val}</span></div>
    </div>
    """

def generate_weekly_calendar_html(weekly_days_data, today_day, yb=None, db=None):
    """1-4 일운 분석 전용 주간 달력 HTML"""
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
            ds_hanja = st.session_state.get('ds_hanja', '甲') if hasattr(st, 'session_state') else '甲'
            ss_val = engine.get_ss(ds_hanja, ji_char) if ji_char != "-" else "-"
            unsung_val = engine.get_unsung(ds_hanja, ji_char) if ji_char != "-" else "-"
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
        <div style='flex:1; width:14.28%; {active_style} text-align:center; padding-bottom:4px; background-color:{bg_col}; display:flex; flex-direction:column; box-sizing:border-box; min-width:0; overflow:hidden;'>
            <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:800; font-size:14px; height:26px; display:flex; align-items:center; justify-content:center; white-space:nowrap;'>
                {day_num}일 ({wday})
            </div>
            <div style='font-size:12px; font-weight:800; color:#000000; height:22px; display:flex; align-items:center; justify-content:center;'>{ss_val}</div>
            <div class='{gan_cls}' style='font-size:17px; font-weight:900; height:26px; display:flex; align-items:center; justify-content:center;'>{gan_char}</div>
            <div class='{ji_cls}' style='font-size:17px; font-weight:900; height:26px; display:flex; align-items:center; justify-content:center;'>{ji_char}</div>
            <div class='color-unsung' style='font-size:12px; font-weight:800; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center;'>{u_val}</div>
            <div class='color-shinsal' style='font-size:12px; font-weight:800; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center;'>{y_val}</div>
            <div class='color-shinsal-day' style='font-size:12px; font-weight:800; border-top:1px dashed #ccc; height:22px; display:flex; align-items:center; justify-content:center;'>{d_val}</div>
        </div>
        """

    return f"""
    <div style='margin-top:14px; margin-bottom:8px; font-size:15px; font-weight:800; color:#3E2723; font-family:"Nanum Myeongjo", serif;'>📅 이번 주 운세 흐름 (일요일 ~ 토요일)</div>
    <div style='display:flex; flex-direction:row; width:100%; border:3px solid #3E2723; background:white; margin-bottom:10px; table-layout:fixed; font-family:"Nanum Myeongjo", serif;'>
        {content}
    </div>
    """


# ==============================================================================
# 📦 섹션 3. 1인용 개인 사주 및 운세 상품군 (상품 1-1 ~ 2-5 활성 모듈)
# ==============================================================================

def get_personal_cover(version, report_title, u_icon, u_name, u_sol, u_lun, u_time, today_str):
    """1인용 감명서 표준 표지 (26px 대형 볼드 1줄 완벽 고정)"""
    raw_title = str(report_title or "초연 전통 명리 사주풀이").replace("🏮", "").replace("🎯", "")
    for tag in ["<br>", "<br/>", "<br />", "\n", "\r"]:
        raw_title = raw_title.replace(tag, " ")
    clean_title = " ".join(raw_title.split())
    clean_u_name = str(u_name or "무명").strip()

    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:210mm; height:297mm; min-height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; box-sizing: border-box; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 42px 24px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 92%; max-width: 680px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            
            <!-- 🌟 대제목 영역: 26px 초극태 블랙 볼드 & 1줄 완벽 고정 -->
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 28px; width: 100%; box-sizing: border-box;'>
                <h1 style='font-family: "Nanum Gothic", sans-serif !important; font-size: 26px !important; font-weight: 900 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -0.5px !important; white-space: nowrap !important; line-height: 1.2 !important; text-align: center;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family: "Nanum Gothic", sans-serif; font-size: 13px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            
            <!-- 신청인 정보 박스 -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 22px 20px; border-radius: 14px; margin-bottom: 24px;'>
                <h2 style='font-family: "Nanum Gothic", sans-serif; font-size: 23px; font-weight: 800; color: #1A237E; margin: 0 0 10px 0;'>{u_icon} {clean_u_name} 님</h2>
                <div style='font-family: "Nanum Gothic", sans-serif; font-size: 16px; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap; color: #000000;'><strong style='font-weight: 900 !important;'>[양력] {u_sol} | [음력] {u_lun}</strong></p>
                    <p style='margin: 4px 0 0 0; white-space: nowrap; font-weight: 800; color: #1A237E;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
            
            <p style='font-family: "Nanum Gothic", sans-serif; font-size: 17px; margin-top: 35px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>
            <p style='font-family: "Nanum Gothic", sans-serif; font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 8px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class='page-break'></div>
    """

def get_info_header(p_icon, name, gender, marital, age, sol_str, lun_str, time_str, p_color="#1A237E"):
    """본문 상단 신상 정보 헤더 (인명 검정색 확정)"""
    return f"""
    <div style='font-family:"Nanum Myeongjo", serif; text-align:center; margin-bottom:10px; line-height:1.6;'>
        <span style='font-size:19px; font-weight:800; color:{p_color}; letter-spacing:0.5px; white-space:nowrap;'>{p_icon} {name}님 ({gender}, {marital}, {age}세)</span><br>
        <span style='font-size:13px; letter-spacing:0.5px; white-space:nowrap;'>[<span class='b-text'>양력: {sol_str} | 음력: {lun_str}</span> <span class='b-text-point'>{time_str}</span>]</span>
    </div>
    """

def get_intro_html():
    """시공명리학 소개 안내문"""
    return """
    <hr style="border: 0; border-top: 2px solid #000000; margin: 20px 0;">
    <div style="margin: 0; padding: 0; font-family: 'Nanum Myeongjo', serif;">
        <p class="ai-body-p" style="margin-top: 0; margin-bottom: 6px; font-weight: 600; text-align: justify; text-indent: 0; line-height: 1.8;">
            <b>"초연 시공 명리학"</b>은 5년에 한 번 돌아오는 '60월령과 60일주'의 조합으로 <b>3,600개 유형</b>으로 분류하지만, <b>"기존의 전통 명리학"</b>은 1년에 한 번 돌아오는 '12월지와 60일주'의 조합으로 <b>720개 유형</b>으로 분류하여 풀이합니다.
        </p> 
        <p class="ai-body-p" style="margin-top: 0; margin-bottom: 0; font-weight: 600; text-align: justify; text-indent: 0; line-height: 1.8;">
            따라서, <b>"본 초연 시공 명리학"</b>은 기존 전통명리학에 비하여 <b>5배</b>, 요즘 유행하는 16개 유형으로 분류하는 MBTI와 비교하면 무려 <b>225배</b> 더 정확한 사주풀이 입니다.
        </p>
    </div>
    <hr style="border: 0; border-top: 2px solid #000000; margin: 20px 0;">
    """

def get_golden_text(name, w_val, i_val, s_name, s_type, s_desc, mb="子", gyuk_name="알수없음격"):
    SEASON_SOLAR_TERMS = {
        '寅': '입춘과 경칩 사이의 이른 봄(寅月)', '卯': '경칩과 청명 사이의 완연한 봄(卯月)',
        '辰': '청명과 입하 사이의 봄과 여름의 환절기(辰月)', '巳': '입하와 망종 사이의 이른 여름(巳月)',
        '午': '망종과 소서 사이의 완연한 여름(午月)', '未': '소서와 입추 사이의 가장 무더운 여름(未月)',
        '申': '입추와 백로 사이의 이른 가을(申月)', '酉': '백로와 한로 사이의 완연한 가을(酉月)',
        '戌': '한로와 입동 사이의 가을과 겨울의 환절기(戌月)', '亥': '입동과 대설 사이의 이른 겨울(亥月)',
        '子': '대설과 소한 사이의 완연한 한겨울(子月)', '丑': '소한과 입춘 사이의 가장 추운 겨울(丑月)'
    }
    wol_korean_str = SEASON_SOLAR_TERMS.get(mb, f"{mb}월")

    return f"""
    <div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 16px; line-height: 1.85; color: #000000; margin-bottom: 18px;'>
        <p style='text-indent: 1.0em; text-align: justify; margin-bottom: 8px;'>
            정통 명리학적으로 풀이하면 <b>{name}님</b>은 <b>{wol_korean_str}</b>에 <b>'{gyuk_name}'</b>의 그릇을 갖추고 태어나하셨으며, 성격은 <b>'{s_name}'</b>인 <b>'{s_type}'</b>으로 <b>'{s_desc}'</b>하는 기본 성향이 있습니다.
        </p>
        <p style='text-indent: 1.0em; text-align: justify; margin-bottom: 5px;'>
            또한, 초연 시공명리학적 관점에서 <b>'{w_val}'</b>의 역동적인 시공간 파동을 지니고 있으며, <b>'{i_val}'</b>의 내면적 본성을 함께 품고 살아갑니다.
        </p>
    </div>
    <hr style="border: 0; border-top: 2px solid #000000; margin: 20px 0;">
    """

def get_closing_html(name):
    return f"""
    <hr style="border: 0; border-top: 2px dashed #1A237E; margin: 30px 0 20px 0;">
    <div style="margin: 0; padding: 0; font-family: 'Nanum Myeongjo', serif;">
        <p style="font-size: 16px; font-weight: 400; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 8px; color: #111111;">'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드(bar-code)와 같지만, 우리가 살아가며 마주하는 스캐너(scanner)인 '운'은 늘 변화하며 흐릅니다.</p>
        <p style="font-size: 16px; font-weight: 400; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 8px; color: #111111;">따라서 오늘의 '초연 시공명리학과의 인연'이 <b>{name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
        <p style="font-size: 16px; font-weight: 400; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 12px; color: #111111;">앞으로 미래에 대한 더 깊은 시공명리의 지혜와 궁금증이 있으시면 언제든 <b>'초연 시공명리 연구소'</b>의 문을 두드려 주십시오.</p>
        <p style="font-size: 16px; font-weight: 800; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 0; color: #111111;">오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
        <div style="text-align: right; margin-top: 20px;">
            <span style="font-weight: 800; font-size: 17px; color: #1A237E;">- 초연 시공명리 연구소 드림 -</span>
        </div>
    </div>
    
    <div style='margin-top: 25px; padding: 12px 15px; background-color: #F8F9FA; border-left: 4px solid #1A237E; border-radius: 4px; font-family: "Nanum Myeongjo", serif;'>
        <p style='font-size: 15px; font-weight: 800; color: #1A237E; margin: 0; line-height: 1.6;'>💡 [초연 명리 안내]</p>
        <p style='font-size: 14px; font-weight: 400; color: #333; margin-top: 4px; margin-bottom: 0; line-height: 1.7;'>본 풀이는 사주 원국의 본질과 현재 운의 큰 흐름을 짚어드린 기본 감명입니다. 특정 연도별·월별 정밀한 세부 흐름은 <b>'올해 및 특정연도 운세 상세분석'</b>을, 재물·직업 등 특정 분야의 집중 상담은 <b>'테마별 특성화 상담'</b>을 통해 확인하실 수 있습니다.</p>
    </div>
    """

def get_final_report_box(content_html):
    """A4 백지 캔버스(무선/무그림자) 안쪽 둥근 VIP 프레임 단일 래핑"""
    return f"""
    <div class='report-page'>
        <div class='vip-inset-frame'>
            {content_html}
        </div>
    </div>
    """


# ==============================================================================
# 📦 섹션 4. 2인용 궁합 및 커플 상품군 (상품 3-1 활성 모듈)
# ==============================================================================

def get_couple_cover(version, report_title, u_icon, u_name, u_age, u_sol, u_lun, u_time, p_icon, p_name, p_age, p_sol, p_lun, p_time, today_str):
    """2인용 궁합/대조 감명서 표준 표지 (26px 대형 볼드 1줄 완벽 고정)"""
    
    raw_title = str(report_title or "초연 전통 명리궁합 풀이").replace("🏮", "").replace("🎯", "")
    for tag in ["<br>", "<br/>", "<br />", "\n", "\r"]:
        raw_title = raw_title.replace(tag, " ")
    clean_title = " ".join(raw_title.split())

    clean_u_name = str(u_name or "무명").strip()
    clean_p_name = str(p_name or "무명").strip()

    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:210mm; height:297mm; min-height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; box-sizing: border-box; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 38px 24px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 92%; max-width: 680px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            
            <!-- 🌟 대제목 영역: 26px 초극태 블랙 볼드 & 1줄 완벽 고정 -->
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 24px; width: 100%; box-sizing: border-box;'>
                <h1 style='font-family: "Nanum Gothic", sans-serif !important; font-size: 26px !important; font-weight: 900 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -0.5px !important; white-space: nowrap !important; line-height: 1.2 !important; text-align: center;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family: "Nanum Gothic", sans-serif; font-size: 13px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            
            <!-- 남명 정보 박스 -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 16px 18px; border-radius: 14px; margin-bottom: 12px;'>
                <h2 style='font-family: "Nanum Gothic", sans-serif; font-size: 21px; font-weight: 800; color: #1A237E; margin: 0 0 8px 0;'>♂️ 남명 : {clean_u_name} 님 <span style='font-size: 16px; color: #111111; font-weight: 900 !important;'>( {u_age}세 )</span></h2>
                <div style='font-family: "Nanum Gothic", sans-serif; font-size: 15px; line-height: 1.7;'>
                    <p style='margin: 0; white-space: nowrap; color: #000000;'><strong style='font-weight: 900 !important;'>[양력] {u_sol} | [음력] {u_lun}</strong></p>
                    <p style='margin: 3px 0 0 0; white-space: nowrap; font-weight: 800; color: #1A237E;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
            
            <!-- 여명 정보 박스 -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 16px 18px; border-radius: 14px;'>
                <h2 style='font-family: "Nanum Gothic", sans-serif; font-size: 21px; font-weight: 800; color: #1A237E; margin: 0 0 8px 0;'>♀️ 여명 : {clean_p_name} 님 <span style='font-size: 16px; color: #111111; font-weight: 900 !important;'>( {p_age}세 )</span></h2>
                <div style='font-family: "Nanum Gothic", sans-serif; font-size: 15px; line-height: 1.7;'>
                    <p style='margin: 0; white-space: nowrap; color: #000000;'><strong style='font-weight: 900 !important;'>[양력] {p_sol} | [음력] {p_lun}</strong></p>
                    <p style='margin: 3px 0 0 0; white-space: nowrap; font-weight: 800; color: #1A237E;'>태어난 시간 : {p_time}</p>
                </div>
            </div>
            
            <p style='font-family: "Nanum Gothic", sans-serif; font-size: 17px; margin-top: 26px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>
            <p style='font-family: "Nanum Gothic", sans-serif; font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 8px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class='page-break'></div>
    """
def get_gunghap_score_visual_html(gh_engine):
    """궁합 점수 및 비주얼 차트 HTML"""
    sky_blue = "#38B6FF"
    bars = "".join([
        f"<div style='display:flex; align-items:center; margin-bottom:10px; font-family:\"Nanum Myeongjo\", serif;'>"
        f"<div style='width:130px; font-size:13px; font-weight:700; color:#444;'>{d['label']}</div>"
        f"<div style='flex:1; height:12px; margin:0 10px;'><svg width='100%' height='12'><rect width='100%' height='12' rx='6' ry='6' fill='#eee' /><rect width='{d['pct']}%' height='12' rx='6' ry='6' fill='{d['color']}' /></svg></div>"
        f"<div style='width:35px; font-size:12px; font-weight:700;'>{d['pct']}%</div>"
        f"</div>" 
        for d in gh_engine.details
    ])

    score_chart_html = (
        f"<h2 style='font-family:\"Nanum Myeongjo\", serif; text-align:center; margin-top:30px; font-size:21px; font-weight:800;'>📊 최종 궁합 점수</h2>\n"
        f"<div style='display:flex; justify-content:center; align-items:center; margin:15px 0;'>\n"
        f"<div style='width:120px; height:120px; border-radius:50%; background:conic-gradient({sky_blue} {gh_engine.final_score}%, #eee 0); display:flex; justify-content:center; align-items:center; -webkit-print-color-adjust: exact;'>\n"
        f"<div style='width:90px; height:90px; background:#fff; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center;'>\n"
        f"<span style='font-family:\"Nanum Myeongjo\", serif; font-size:28px; font-weight:800; color:{sky_blue};'>{gh_engine.final_score}</span>\n"
        f"<span style='font-size:9px; color:#888; font-weight:bold;'>SCORE</span>\n"
        f"</div>\n"
        f"</div>\n"
        f"</div>\n"
        f"<div style='text-align:center; margin-bottom:15px;'><span style='font-family:\"Nanum Myeongjo\", serif; font-size:14px; font-weight:700; color:#fff; background:{sky_blue}; padding:5px 24px; border-radius:24px; -webkit-print-color-adjust: exact;'>{gh_engine.grade}</span></div>\n"
        f"<div style='max-width:460px; margin:0 auto; margin-bottom:15px;'>\n{bars}\n</div>\n"
    )
    return score_chart_html

def get_gunghap_closing(name1, name2):
    return f"""
    <div style='margin-top: 30px; border-top: 2px dashed #444; padding-top: 18px; font-family: "Nanum Myeongjo", serif;'>
        <p style='font-size: 16px !important; font-weight: 400 !important; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 8px; color: #111111;'>
        <b>{name1}님</b>과 <b>{name2}님</b>의 만남은 결코 우연이 아닌, <b>'수많은 인연의 이치 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 명식이지만, <b>'궁합(宮合)'</b>은 두 명식이 만나 그려내는 새로운 <b>'조화와 상생'</b>입니다.</p>
        <p style='font-size: 16px !important; font-weight: 400 !important; text-indent: 15px; text-align: justify; line-height: 1.85; margin-bottom: 8px; color: #111111;'>서로의 기운을 보완하고 다독여주는 든든한 <b>'반려자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 초연 시공명리의 축복이 가득하시길 소망합니다.</p>
        <p style='font-size: 16px !important; font-weight: 800 !important; text-indent: 15px; line-height: 1.85; margin-bottom: 0px; color: #111111;'>오늘 닿은 귀한 인연에 다시 한 번 깊이 감사드립니다.</p>
        <div style='text-align: right; margin-top: 20px;'>
            <span style='font-weight: 800; font-size: 17px !important; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
        </div>
    </div>
    """

def get_gunghap_three_page_report(part_1_fact, m_ess, f_ess, g_ess):
    """궁합 3분할 페이지 일괄 생성 함수 (화면 연속 / 인쇄 A4 1장씩 분할)"""
    m_page = f"""
    <div style='border: 1.5px solid #1565C0; border-radius: 12px; padding:20px; background:#FFFFFF; margin-bottom:20px;'>
        <h1 style='text-align:center; color:#1565C0; font-weight:800; border-bottom:2px solid #1565C0; padding-bottom:10px; margin-bottom:15px; font-size:21px;'>[ ♂️ 남명 사주 요약 ]</h1>
        {part_1_fact}
        <div style='margin-top:15px;'>{m_ess}</div>
    </div>
    <div class='page-break'></div>
    """
    
    f_page = f"""
    <div style='border: 1.5px solid #4A148C; border-radius: 12px; padding:20px; background:#FFFFFF; margin-bottom:20px;'>
        <h1 style='text-align:center; color:#4A148C; font-weight:800; border-bottom:2px solid #4A148C; padding-bottom:10px; margin-bottom:15px; font-size:21px;'>[ ♀️ 여명 사주 요약 ]</h1>
        <div style='margin-top:15px;'>{f_ess}</div>
    </div>
    <div class='page-break'></div>
    """
    
    g_page = f"""
    <div style='border: 1.5px solid #1B5E20; border-radius: 12px; padding:20px; background:#FFFFFF;'>
        <h1 style='text-align:center; color:#1B5E20; font-weight:800; border-bottom:2px solid #1B5E20; padding-bottom:10px; margin-bottom:15px; font-size:21px;'>[ 🍀 초연 시공명리 궁합 풀이 ]</h1>
        <div style='margin-top:15px;'>{g_ess}</div>
    </div>
    """
    return get_final_report_box(m_page + f_page + g_page)


# ==============================================================================
# 📦 섹션 5. 택일 상품군 (상품 3-2, 3-3 활성 모듈)
# ==============================================================================

def get_delivery_summary_box(best_days):
    """출산/결혼 길일 한눈에 보기 요약 상자"""
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
    <div style="background-color:#F0F4F8; border:2px solid #1A237E; border-radius:10px; padding:15px; margin-top:15px; margin-bottom:20px; font-family: 'Nanum Myeongjo', serif;">
        <h4 style="color:#1A237E; margin-top:0; margin-bottom:10px; font-size:15px; border-bottom:1px solid #C5CAE9; padding-bottom:6px;">
            📋 길일 한눈에 보기 (최적 길일 로드맵)
        </h4>
        <ul style="list-style-type:none; padding-left:0; margin:0; line-height:1.8; font-size:14px; color:#2C3E50;">
            {summary_items}
        </ul>
    </div>
    """

def get_childbirth_taegil_card(border_col, idx, b_date_str, score, b_time_str, b_time_pillar, gestation_warning, conception_title, conception_str, conception_msg, baby_saju_html, ai_output_html):
    """출산 택일 상세 추천 카드"""
    return f"""
    <div style="background-color:#FFFFFF; border:1px solid #E0E0E0; border-radius:12px; padding:18px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.05); font-family: 'Nanum Myeongjo', serif;">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #F1F3F4; padding-bottom:10px; margin-bottom:12px;">
            <h3 style="color:#1A237E; margin:0; font-size:17px; font-weight:800;">🏅 추천 {idx+1}순위 길일 : {b_date_str}</h3>
            <span style="background-color:#E8EAF6; color:#1A237E; font-weight:bold; padding:3px 10px; border-radius:20px; font-size:13px;">명리 종합점수: {score}점</span>
        </div>
        <ul style="list-style-type:none; padding-left:0; margin-top:8px; line-height:1.8; color:#333; font-size:14px;">
            <li><b>⏰ 가장 좋은 시간</b>: <span style="color:#00695C; font-weight:bold;">{b_time_str} ({b_time_pillar})</span></li>
            {gestation_warning}
            <li><b>{conception_title}</b>: <span style="font-weight:bold; color:#0277BD;">{conception_str}</span> <br>{conception_msg}</li>
        </ul>
        {baby_saju_html}
        <div style="margin-top:12px; padding-top:12px; border-top:1px dashed #DDD;">
            {ai_output_html}
        </div>
    </div>
    """


# ==============================================================================
# 📦 섹션 6. 타 감명서 1:1 대조 분석 리포트 상품군 (상품 4-1, 4-2 활성 모듈)
# ==============================================================================


def get_external_raw_text_box(other_text):
    return f"""
    <div style='margin-top:20px; margin-bottom:20px; padding:20px; background-color:#F5F5F5; border:1.5px solid #757575; border-radius:10px; font-family: "Nanum Myeongjo", serif;'>
        <div style='font-size:18px; font-weight:800; color:#212121; border-bottom:1.5px solid #9E9E9E; padding-bottom:8px; margin-bottom:12px;'>
            📄 [제출된 외부 타 감명서 원본]
        </div>
        <div style='font-size:16px; color:#111111; line-height:1.85; white-space:pre-wrap;'>{other_text}</div>
    </div>
    <div class='page-break'></div>
    """

def get_couple_golden_text(m_name, male_golden_html, f_name, female_golden_html):
    """4-2 타 감명서 비교 전용 듀얼 황금문구 뷰 (헤더 17px 표준 규격 적용)"""
    clean_male = male_golden_html.replace('<hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">', '').replace('<hr style="border: 0; border-top: 2px solid #000000; margin: 20px 0;">', '').strip()
    clean_female = female_golden_html.replace('<hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">', '').replace('<hr style="border: 0; border-top: 2px solid #000000; margin: 20px 0;">', '').strip()
    
    return f"""
    <div style="margin-bottom: 20px; padding: 18px 20px; background: #fafafa; border-radius: 8px; border: 1px solid #e0e0e0; font-family: 'Nanum Myeongjo', 'Batang', serif;">
        <div style="margin-bottom: 18px;">
            <!-- ♂️ 신랑 헤더: 17px Bold 800 -->
            <div style="font-size: 17px; font-weight: 800; color: #1565C0; margin-bottom: 6px; font-family: 'Nanum Myeongjo', serif; letter-spacing: -0.3px;">
                ♂️ [신랑 {m_name}님 타고난 그릇과 시공간 본성]
            </div>
            <div style="font-family: 'Nanum Myeongjo', serif; font-size: 16px; font-weight: 500; line-height: 1.85; color: #111111;">
                {clean_male}
            </div>
        </div>
        <div>
            <!-- ♀️ 신부 헤더: 17px Bold 800 -->
            <div style="font-size: 17px; font-weight: 800; color: #4A148C; margin-bottom: 6px; font-family: 'Nanum Myeongjo', serif; letter-spacing: -0.3px;">
                ♀️ [신부 {f_name}님 타고난 그릇과 시공간 본성]
            </div>
            <div style="font-family: 'Nanum Myeongjo', serif; font-size: 16px; font-weight: 500; line-height: 1.85; color: #111111;">
                {clean_female}
            </div>
        </div>
    </div>
    <hr style="border: 0; border-top: 2px solid #333333; margin: 20px 0;">
    """

def get_couple_fact_split_layout(male_block, female_block):
    """
    4-2 타 감명서 비교 (궁합) 상단 팩트 레이아웃
    - 화면에서는 연속 표출, 인쇄 시 남명 1장 -> 여명 1장으로 분할
    """
    return f"""
    <!-- 1페이지 분량: 남명 완전체 -->
    <div style="margin-bottom: 25px; font-family: 'Nanum Myeongjo', serif;">
        <div style="font-size: 21px; font-weight: 800; color: #1565C0; text-align: center; padding: 6px 0 10px 0; margin-bottom: 12px; border-bottom: 2.5px solid #1565C0; letter-spacing: -0.5px;">
            ♂️ [남명 사주 원국 및 대운 분석]
        </div>
        {male_block}
    </div>
    <div class='page-break'></div>
    
    <!-- 2페이지 분량: 여명 완전체 -->
    <div style="margin-bottom: 25px; font-family: 'Nanum Myeongjo', serif;">
        <div style="font-size: 21px; font-weight: 800; color: #4A148C; text-align: center; padding: 6px 0 10px 0; margin-bottom: 12px; border-bottom: 2.5px solid #4A148C; letter-spacing: -0.5px;">
            ♀️ [여명 사주 원국 및 대운 분석]
        </div>
        {female_block}
    </div>
    <div class='page-break'></div>
    """

def render_saju_comparison_report(saju_fact_html, external_raw_box, ai_content_html):
    """
    4-1 타 감명서 비교 (사주) 전용 뷰
    - 4-2 궁합 함수 구조를 완벽히 재활용하여 일관된 24px 대제목 및 스타일 유지
    """
    master_body = f"""
    <h2 style="font-family: 'Nanum Myeongjo', serif !important; font-size: 24px !important; font-weight: 900 !important; color: #1A237E !important; text-align: center !important; padding-bottom: 15px !important; margin-bottom: 25px !important; border-bottom: 3px solid #1A237E !important; letter-spacing: -0.5px !important; display: block !important; margin-top: 0 !important;">🔍 타 감명서 비교 (사주) 1:1 정밀 분석</h2>
    {saju_fact_html}
    {external_raw_box}
    <div style="margin-top: 20px;">
        {ai_content_html}
    </div>
    """
    return get_final_report_box(master_body)

def analyze_saju_facts_advanced(saju_data, current_dw_ji="-", current_sewun_ji="-"):
    """
    [초연 시공명리 정밀 감지 엔진 통합본]
    1. 복음 및 묘고 중첩 에너지 정체 지수 & 4대 실전 처세 솔루션
    2. 조토극수(未·戌 ➔ 亥·子) 시공간 침식 파동 건강 진단
    3. 배우자 인연 복합 파동 (관성입묘·암합·궁위파동)
    4. 丑戌未 가형(假刑) 상태 및 행운 개고(開庫) 변곡점
    5. 신살 + 시공간 복합체 (홍염/음욕 + 복음) 이성 구설 파동
    6. 부(富) vs 내면 평화 상호작용 지수 & 대안 시공간 설계
    """
    ys = saju_data.get('year_gan', '-')
    ms = saju_data.get('month_gan', '-')
    ds = saju_data.get('day_gan', '-')
    hs = saju_data.get('hour_gan', '-')
    
    y_ji = saju_data.get('year_ji', '-')
    m_ji = saju_data.get('month_ji', '-')
    d_ji = saju_data.get('day_ji', '-')
    h_ji = saju_data.get('hour_ji', '-')
    
    jis = [y_ji, m_ji, d_ji, h_ji]
    gans = [ys, ms, ds, hs]
    valid_jis = [j for j in jis if j and j != '-' and j != '?']
    valid_gans = [g for g in gans if g and g != '-' and g != '?']

    # 1. 복음(伏吟) 파동 감지
    is_bokgeum = False
    bokgeum_details = []
    if len(valid_jis) > len(set(valid_jis)):
        is_bokgeum = True
        for j in set(valid_jis):
            if valid_jis.count(j) >= 2:
                bokgeum_details.append(f"{j}{j} 복음")

    # 2. 묘고(墓庫) 및 조토극수 침식 감지
    vaults = ['辰', '戌', '丑', '未']
    detected_vaults = [j for j in valid_jis if j in vaults]
    has_vault = len(detected_vaults) > 0
    dry_earths = [j for j in valid_jis if j in ['未', '戌']]
    life_waters = [j for j in valid_jis if j in ['亥', '子']]
    has_erosion = (len(dry_earths) > 0) and (len(life_waters) > 0)

    # 3. 흉화 변곡점 및 건강 침식
    warnings = []
    health_erosion_facts = []

    if is_bokgeum:
        warnings.append(f"지지에 {', '.join(bokgeum_details)} 파동 형성(기운 정체 및 내적 소모)")
        
    if has_erosion:
        erosion_desc = f"조열한 흙({','.join(set(dry_earths))})이 생명수({','.join(set(life_waters))})를 말리는 [시공간 침식 파동]"
        warnings.append(erosion_desc)
        health_erosion_facts.append(
            f"⚠️ [조토극수 침식 경보] {erosion_desc} ➔ 혈관 탄력 저하(고혈압), 대사 정체(고혈당/당뇨), 신장·비뇨기·호르몬 불균형 집중 관리"
        )

    # 4. 정체 지수 & 4대 실전 처세 솔루션
    stagnation_level = "정상"
    action_solutions = []
    vault_cnt = len(detected_vaults)
    bokgeum_cnt = len(bokgeum_details)

    if has_vault and is_bokgeum:
        stagnation_level = "심각 (에너지 고갈 위험)" if (vault_cnt >= 2 or bokgeum_cnt >= 2) else "경고 (기운 정체)"
        warnings.append(f"복음·묘고 중첩({stagnation_level})으로 환경 급변 시 에너지 소모 주의")
        action_solutions.append("1) [시공간 이격]: 출장, 여행, 주말부부/각방 등 물리적 거리두기로 정체된 기운 환기")
        action_solutions.append("2) [활인 개운]: 교육, 상담, 봉사, 의료 등 활인업(活人業) 활동으로 살기(殺氣)를 덕(德)으로 승화")
        action_solutions.append("3) [수기 충전]: 물가 산책, 반신욕, 명상·호흡으로 메마른 생명수 순환 촉진")
        action_solutions.append("4) [비우기 처세]: 공간 미니멀리즘 정리 및 집착을 내려놓는 마음공부")
    elif is_bokgeum or has_vault:
        stagnation_level = "주의 (부분적 정체)"

    # 5. 배우자 인연 복합 파동
    spouse_risk_factors = []
    if d_ji in ['未', '戌', '辰', '丑']:
        spouse_risk_factors.append(f"일지 묘고·관대({d_ji})로 인한 강한 독립성 및 가주(家主) 기질")
    if (d_ji == '未' and '丑' in valid_jis) or (d_ji == '丑' and '未' in valid_jis):
        spouse_risk_factors.append("배우자궁 丑未충으로 인한 궁위 흔들림 및 환경적 급변동")
    elif d_ji in [y_ji, m_ji, h_ji]:
        spouse_risk_factors.append(f"배우자궁({d_ji}) 복음 중첩으로 인한 부부 관계 정체")
    if '亥' in valid_jis and valid_jis.count('亥') >= 2:
        spouse_risk_factors.append("관성 亥亥 복음 및 암합 파동으로 인한 배우자 인연 불안정")
    spouse_issue_str = " / ".join(spouse_risk_factors) if spouse_risk_factors else "배우자궁 비교적 안정적 흐름 유지"

    # 6. 丑戌未 가형(假刑) 및 개고(開庫) 변곡점
    samhyung_potential_factors = []
    vault_samhyung_set = {'丑', '戌', '未'}
    matched_v_samhyung = vault_samhyung_set.intersection(set(valid_jis))
    if len(matched_v_samhyung) == 2:
        missing_ji = list(vault_samhyung_set - matched_v_samhyung)[0]
        if current_dw_ji == missing_ji or current_sewun_ji == missing_ji:
            samhyung_potential_factors.append(
                f"⚡ [丑戌未 삼형 완성 및 개고 경보]: 운에서 {missing_ji}토가 가세하여 묘고 개고(開庫) 및 재물·건강·문서 지각변동 발생"
            )
        else:
            samhyung_potential_factors.append(
                f"원국에 {','.join(matched_v_samhyung)} 가형(잠재 상태) 형성 ➔ 향후 {missing_ji}운(대운/세운) 진입 시 개고 및 삼형 변곡점 주의"
            )
    elif len(matched_v_samhyung) == 3:
        samhyung_potential_factors.append("원국 자체에 丑戌未 삼형 완성으로 수술·조정 파동 상시 내재")
    samhyung_potential_str = " / ".join(samhyung_potential_factors) if samhyung_potential_factors else "특이 삼형 잠재 파동 없음"

    # 7. 신살 + 시공간 복합 파동 (이성 구설/육친 파동)
    shinsal_risk_factors = []
    if is_bokgeum and ('丁' in valid_gans and valid_gans.count('丁') >= 2):
        shinsal_risk_factors.append("丁丁 천간 중첩 및 지지 복음 결합으로 인한 이성 구설 및 감정적 에너지 소모 숙제")
    shinsal_risk_str = " / ".join(shinsal_risk_factors) if shinsal_risk_factors else "신살 복합 파동 안정"

    # 8. 부(富) vs 내면 평화 상호작용 지수 및 대안 시공간 설계
    has_wealth_comb = ('丁' in valid_gans and '辛' in valid_gans and '壬' in valid_gans)
    if has_wealth_comb and (has_erosion or is_bokgeum):
        harmony_index_str = "외적 번영도(재물 성취) 90점 / 내적 피로도(심리·건강 침식) 85점 ➔ 외화내빈(外華內貧)형 불균형 주의"
        alternative_space_str = "물리적 시공간 이격(주말부부/독립 가주화) 및 활인업(봉사/교육/멘토링) 실천 시 흉화 파동 70% 이상 상쇄 가능"
    else:
        harmony_index_str = "외적 성취와 내면의 에너지가 비교적 균형을 이루는 상태"
        alternative_space_str = "현재의 환경을 유지하며 점진적 자기계발 추천"

    # 최종 경고 메시지 조립
    warning_message = "⚠️ [시공간 파동 경보]: " + " / ".join(warnings) if warnings else "원국 내 왜곡 없이 비교적 원활한 순환 유지"
    action_solution_str = "\n".join(action_solutions) if action_solutions else "자연스러운 기운의 순환 유지 및 긍정적 마음가짐"

    return {
        "is_bokgeum": is_bokgeum,
        "bokgeum_details": bokgeum_details,
        "has_vault": has_vault,
        "detected_vaults": detected_vaults,
        "has_erosion": has_erosion,
        "stagnation_level": stagnation_level,
        "action_solutions": action_solution_str,
        "spouse_issue_facts": spouse_issue_str,
        "samhyung_potential_facts": samhyung_potential_str,
        "shinsal_risk_facts": shinsal_risk_str,
        "harmony_index_facts": harmony_index_str,
        "alternative_space_facts": alternative_space_str,
        "health_erosion_facts": " / ".join(health_erosion_facts) if health_erosion_facts else "특이 침식 파동 없음",
        "warning_message": warning_message
    }

def render_gunghap_comparison_report(couple_fact_html, external_raw_box, ai_content_html):
    """
    4-2 타 감명서 비교 (궁합) 전용 뷰
    - 박사님 지시 반영: Streamlit 강제 폰트 축소 무효화. <h2> 태그를 통한 대제목 24px 확정
    """
    master_body = f"""
    <h2 style="font-family: 'Nanum Myeongjo', serif !important; font-size: 24px !important; font-weight: 900 !important; color: #1A237E !important; text-align: center !important; padding-bottom: 15px !important; margin-bottom: 25px !important; border-bottom: 3px solid #1A237E !important; letter-spacing: -0.5px !important; display: block !important; margin-top: 0 !important;">🔍 타 감명서 비교 (궁합) 1:1 정밀 분석</h2>
    {couple_fact_html}
    {external_raw_box}
    <div style="margin-top: 20px;">
        {ai_content_html}
    </div>
    """
    return get_final_report_box(master_body)

def render_comparison_report(part_1_fact, external_raw_box, ai_comparison_html):
    """4-1 타 감명서 대조 전용 3단 순서 조립 (팩트 + 원본 + 대조 리포트)"""
    master_body = f"{part_1_fact}{external_raw_box}{ai_comparison_html}"
    return get_final_report_box(master_body)

def get_warning_box(title, message):
    """미입력 및 시스템 경고 메시지 출력 전용 뷰 함수"""
    return f"""
    <div style='padding:16px; background-color:#FFF3E0; border:2px solid #FB8C00; border-radius:8px; margin-top:15px; font-family: "Nanum Myeongjo", serif;'>
        <h3 style='color:#E65100; margin:0 0 6px 0; font-size:15px; font-weight:800;'>⚠️ [{title}]</h3>
        <p style='color:#E65100; font-size:14px; margin:0; line-height:1.6;'>{message}</p>
    </div>
    """

def analyze_samja_combination(saju_gan_data, dw_gan="-"):
    """
    [초연 시공명리 천간 3자조합 궁위별 시공간 물상 분기 엔진]
    - 丁辛壬 (활인·전문기술·돈벼락)
    - 甲戊庚 (귀격·우두머리·권력/대업)
    - 乙丙己 (교육·문화·화려한 개화)
    - 丙辛癸 (정밀 연구·의약·특수기술)
    """
    ys = saju_gan_data.get('year_gan', '-')
    ms = saju_gan_data.get('month_gan', '-')
    ds = saju_gan_data.get('day_gan', '-')
    hs = saju_gan_data.get('hour_gan', '-')

    gans = [ys, ms, ds, hs]
    valid_gans = [g for g in gans if g and g != '-' and g != '?']
    gan_set = set(valid_gans)

    comb_results = []

    # 1. 丁辛壬 (정신임) 삼자조합 판별
    target_set = {'丁', '辛', '壬'}
    matched = target_set.intersection(gan_set)
    
    # 원국에 2글자 이상 있거나 대운 결합 시
    if len(matched) >= 3 or (len(matched) == 2 and dw_gan in target_set):
        loc_desc = []
        # 년월궁(선천/부모/조상) vs 일시궁(본인/중말년/전문성) 판별
        yw_has = any(g in ['丁', '辛', '壬'] for g in [ys, ms])
        dh_has = any(g in ['丁', '辛', '壬'] for g in [ds, hs])

        if yw_has and dh_has:
            loc_desc.append("년월과 일시에 걸쳐 조상·부모의 선천적 혜택(돈벼락/두뇌)과 본인의 전문 장인정신이 완벽히 이어지는 형태")
        elif yw_has:
            loc_desc.append("년월에 위치하여 조상·부모 대의 유산 및 선천적 총명함으로 조기 사회적 발탁을 이루는 형태")
        elif dh_has:
            loc_desc.append("일시에 집중되어 중년 이후 본인의 독보적 전문 기술과 집념으로 자수성가 부를 일구는 형태")

        if dw_gan in target_set and len(matched) == 2:
            loc_desc.append(f"현재 {dw_gan}대운이 가세하여 잠자던 丁辛壬 삼자조합이 폭발적으로 개화하는 황금기")

        comb_results.append(f"✨ [丁辛壬 삼자조합]: {', '.join(loc_desc)}")

    # 2. 甲戊庚 (갑무경) 삼자조합 판별
    target_set_kmg = {'甲', '戊', '庚'}
    matched_kmg = target_set_kmg.intersection(gan_set)
    if len(matched_kmg) >= 3 or (len(matched_kmg) == 2 and dw_gan in target_set_kmg):
        comb_results.append("✨ [甲戊庚 삼자조합]: 거대한 조직과 권력을 장악하는 우두머리 리더십 발현")

    res_str = " / ".join(comb_results) if comb_results else "원국 특이 삼자조합 없음"
    return res_str
