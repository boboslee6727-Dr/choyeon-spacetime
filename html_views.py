# ==============================================================================
# html_views.py (ver 75.0 Master - 화면 단일 프레임 & 인쇄 A4 분할 듀얼 완결본)
# ==============================================================================
# [핵심 반영 사항]
# 1. 화면(Screen) 뷰: A4 바깥선 완전 제거(투명), 단일 .vip-inset-frame 안에서 연속 출력
# 2. 인쇄/PDF(@media print) 뷰: .page-break 엔진이 작동하여 A4 1장씩 정밀 분할 출력
# 3. 동양 전통 예법 엄수: 남명/여명 인명 붉은색(朱書) 전면 배제 (품격 있는 먹색 #111111 적용)
# 4. 서체 전면 통일: 전 표지, 원국표, 마스터바, 황금문구, 통변 본문 '나눔명조(Nanum Myeongjo)' 강제 적용
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
    }

    .b-text { font-weight: 800 !important; color: #000000 !important; display: inline-block; }
    .b-text-point { font-weight: 800 !important; color: #1A237E !important; display: inline-block; }

    /* 버튼 스타일 */
    div.stButton > button { 
        font-family: 'Nanum Gothic', sans-serif !important; 
        font-weight: 900 !important; 
        font-size: 16px !important; 
        border-radius: 8px !important; 
    }
    div.stButton > button[kind="primary"] { 
        background-color: #1A237E !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        height: 50px !important; 
        font-weight: 900 !important; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; 
    }
    div.stButton > button[kind="primary"]:hover { background-color: #0D47A1 !important; color: #FFFFFF !important; }

    div.stButton > button[kind="secondary"] { 
        background-color: #00A843 !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        height: 50px !important; 
        font-weight: 900 !important; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.08) !important; 
    }
    div.stButton > button[kind="secondary"]:hover { background-color: #008937 !important; color: #FFFFFF !important; }

    /* A4 백지 캔버스 (외곽선 및 그림자 완전 제거, 순백 바탕) */
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
        color: #000000; 
    }

    /* 안쪽 표준 둥근 사각 액자 (단일 프레임, 그림자 제거) */
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
    AI 생성 텍스트 포맷터 (박사님 확정 폰트 크기 및 스타일 최종 규격)
    - 대제목(1.) 20px Bold 900
    - 특수헤더 17px Bold 800 (중앙정렬, 밑줄 2.5px solid #1A237E)
    - 소제목(1)) 17px Bold 800 (검정색 #000000)
    - 소소제목((1)) 16px Bold 700 (진먹색 #333333)
    - 일반본문 16px Medium 500 (줄간격 1.85, 들여쓰기 15px)
    """
    if not text:
        return ""
        
    lines = str(text).split('\n')
    html_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 마크다운 찌꺼기만 제거 (따옴표, 괄호 등 문장부호 100% 보존)
        line = line.replace('*', '').replace('#', '')

        # 🌟 [특수 헤더] 수석보좌관 1:1 장단점 정밀 비교 등 (17px / 800 / 중앙 정렬 / 밑줄 2.5px solid #1A237E)
        if '수석보좌관' in line or '장단점 정밀 비교' in line or line.startswith('[수석보좌관'):
            html_lines.append(
                f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 17px; font-weight: 800; color: #1A237E; "
                f"text-align: center; padding-bottom: 6px; margin-top: 18px; margin-bottom: 8px; border-bottom: 2.5px solid #1A237E; letter-spacing: -0.3px;'>"
                f"{line}</div>"
            )
        # 🌟 [대제목 1.] (20px / 900 / 상단 22px, 하단 10px, 하단 옅은 구분선)
        elif re.match(r'^\d+\.\s', line):
            html_lines.append(
                f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 20px; font-weight: 900; color: #000000; "
                f"margin-top: 22px; margin-bottom: 10px; border-bottom: 1px solid #E0E0E0; padding-bottom: 5px; letter-spacing: -0.5px;'>"
                f"{line}</div>"
            )
        # 🌟 [소제목 1)] (17px / 800 / 검정색 #000000 / 상단 14px, 하단 6px)
        elif re.match(r'^\d+\)\s', line):
            html_lines.append(
                f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 17px; font-weight: 800; color: #000000; "
                f"margin-top: 14px; margin-bottom: 6px; letter-spacing: -0.3px;'>"
                f"{line}</div>"
            )
        # 🌟 [소소제목 (1)] (16px / 700 / 진먹색 #333333 / 상단 10px, 하단 4px)
        elif re.match(r'^\(\d+\)\s', line):
            html_lines.append(
                f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 16px; font-weight: 700; color: #333333; "
                f"margin-top: 10px; margin-bottom: 4px; letter-spacing: -0.2px;'>"
                f"{line}</div>"
            )
        # 🌟 [일반 본문] (16px / 500 / 줄간격 1.85 / 들여쓰기 15px)
        else:
            if line.startswith('-'):
                html_lines.append(
                    f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 16px; font-weight: 500; line-height: 1.85; "
                    f"color: #111111; text-align: justify; margin-top: 4px; margin-bottom: 8px; text-indent: 5px; padding-left: 10px;'>"
                    f"{line}</p>"
                )
            else:
                html_lines.append(
                    f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 16px; font-weight: 500; line-height: 1.85; "
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

def render_ai_with_tables(ai_text, **tables):
    """AI 본문 내 마커([DAEWUN_TABLE_HERE] 등)를 실제 HTML 표로 치환"""
    if not ai_text: return ""
    patterns = {
        'daewun': r'\[\s*\*?\*?\s*DAEWUN_TABLE_HERE\s*\*?\*?\s*\]',
        'sewun': r'\[\s*\*?\*?\s*SEWUN_TABLE_HERE\s*\*?\*?\s*\]',
        'wolun': r'\[\s*\*?\*?\s*WOLUN_TABLE_HERE\s*\*?\*?\s*\]',
        'weekly': r'\[\s*\*?\*?\s*WEEKLY_CALENDAR_HERE\s*\*?\*?\s*\]',
        'couple': r'\[\s*\*?\*?\s*COUPLE_DAEWUN_TABLES_HERE\s*\*?\*?\s*\]',
    }
    for key, table_html in tables.items():
        if table_html and key in patterns:
            ai_text = re.sub(patterns[key], table_html, ai_text, flags=re.IGNORECASE)
    return ai_text


# ==============================================================================
# 📦 섹션 3. 1인용 개인 사주 및 운세 상품군 (상품 1-1 ~ 2-5 활성 모듈)
# ==============================================================================

def get_personal_cover(version, report_title, u_icon, name, sol, lun, time, today):
    """1인용 감명서 표준 표지 (Ver 50.5 폰트 위계·굵기 및 A4 상하 중앙정렬 완결본)"""
    clean_title = str(report_title or "초연 전통 명리사주 풀이").replace("🏮 ", "").replace("🎯 ", "").strip()
    
    # 🌟 신청인 이름 앞 중복 호칭 정제
    clean_name = str(name or "").strip()
    for prefix in ["신청인 :", "신청인:", "남명 :", "남명:", "여명 :", "여명:"]:
        if clean_name.startswith(prefix):
            clean_name = clean_name[len(prefix):].strip()
    if not clean_name:
        clean_name = "홍길동"

    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:210mm; height:297mm; min-height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; box-sizing: border-box; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 45px 30px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 85%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            
            <!-- [대제목 H1] Ver 50.5 규격: 36px Bold 900 -->
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 18px; margin-bottom: 35px;'>
                <h1 style='font-family: "Nanum Gothic", sans-serif !important; font-size: 36px !important; font-weight: 900 !important; margin: 0 !important; color: #111111; letter-spacing: -0.5px;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span style='font-family: "Nanum Gothic", sans-serif; font-size: 14px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            
            <!-- [신청인 정보 박스] Ver 50.5 규격: 성명 24px Bold 800 / 인적사항 15px Bold 700 (#111111 진하게) -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 30px 25px; border-radius: 15px; margin-bottom: 30px;'>
                <h2 style='font-family: "Nanum Gothic", sans-serif; font-size: 24px; font-weight: 800; color: #1A237E; margin: 0 0 16px 0;'>{u_icon} 신청인 : {clean_name} 님</h2>
                <div style='font-family: "Nanum Gothic", sans-serif; font-size: 15px; font-weight: 700; color: #111111; line-height: 2.0;'>
                    <p style='margin: 0;'>양력 : {sol}</p>
                    <p style='margin: 0;'>음력 : {lun}</p>
                    <p style='margin: 4px 0 0 0; color: #D50000; font-weight: 800;'>태어난 시간 : {time}</p>
                </div>
            </div>
            
            <!-- [발행일자 및 연구소명] Ver 50.5 규격: 18px Bold 800 / 22px Bold 800 (#1A237E) -->
            <p style='font-family: "Nanum Gothic", sans-serif; font-size: 18px; margin-top: 35px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today}</p>
            <p style='font-family: "Nanum Gothic", sans-serif; font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 12px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
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

def get_ai_report_box(content):
    return get_final_report_box(content)

def render_basic_report(part_1_fact, part_2_intro, part_3_golden, ai_output_html, un_html, sewun_html, part_5_closing):
    body = f"{part_1_fact}{part_2_intro}{part_3_golden}<div class='page-break'></div>{ai_output_html}{un_html}{sewun_html}{part_5_closing}"
    return get_final_report_box(body)

def render_yeareun_report(part_1_fact, sewun_html, ai_output_html, part_5_closing):
    body = f"{part_1_fact}{sewun_html}<div class='page-break'></div>{ai_output_html}{part_5_closing}"
    return get_final_report_box(body)

def render_wolun_report(part_1_fact, wolun_html, ai_output_html, part_5_closing):
    body = f"{part_1_fact}{wolun_html}<div class='page-break'></div>{ai_output_html}{part_5_closing}"
    return get_final_report_box(body)

def render_ilun_report(part_1_fact, weekly_html, ai_output_html, part_5_closing):
    body = f"{part_1_fact}{weekly_html}<div class='page-break'></div>{ai_output_html}{part_5_closing}"
    return get_final_report_box(body)


# ==============================================================================
# 📦 섹션 4. 2인용 궁합 및 커플 상품군 (상품 3-1 활성 모듈)
# ==============================================================================

def get_couple_cover(version, report_title, u_icon, u_name, u_age, u_sol, u_lun, u_time, p_icon, p_name, p_age, p_sol, p_lun, p_time, today_str):
    """2인용 궁합 감명서 표준 표지 (1:1 결함 완벽 방어 완결본)"""
    clean_title = str(report_title or "초연 전통 명리궁합 풀이").replace("🏮 ", "").replace("🎯 ", "").strip()
    
    # 🌟 [해결 1] 정규식으로 '남명 :', '여명 :', '신청인 :' 중복 완벽 박멸
    def extract_pure_name(raw_name):
        n = str(raw_name or "").strip()
        n = re.sub(r'^(?:남명\s*[:：]?|여명\s*[:：]?|신청인\s*[:：]?|상대방\s*[:：]?|\s+)+', '', n).strip()
        return n if n else "무명"

    clean_u_name = extract_pure_name(u_name)
    clean_p_name = extract_pure_name(p_name)
    
    # 🌟 [해결 2] app.py에서 p_lun이 빈값('')으로 넘어와도 p_sol로부터 음력 즉시 자동 산출
    def ensure_lunar_str(sol_str, lun_str):
        if lun_str and str(lun_str).strip() and str(lun_str).strip() != "-":
            return str(lun_str).strip()
        nums = re.findall(r'\d+', str(sol_str))
        if len(nums) >= 3:
            y, m, d = int(nums[0]), int(nums[1]), int(nums[2])
            klc = KoreanLunarCalendar()
            if klc.setSolarDate(y, m, d):
                leap_str = "윤달" if getattr(klc, 'isIntercalary', False) else "평달"
                return f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({leap_str})"
        return "음력 정보 없음"

    final_u_lun = ensure_lunar_str(u_sol, u_lun)
    final_p_lun = ensure_lunar_str(p_sol, p_lun)

    # 🌟 [해결 3] 대제목을 26px Bold 900 / letter-spacing: -1.2px 로 1줄 강제 안착
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:210mm; height:297mm; min-height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; box-sizing: border-box; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 40px 25px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 88%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            
            <!-- [대제목 H1] 26px Bold 900 / 1줄 완벽 고정 -->
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 26px;'>
                <h1 style='font-family: "Nanum Gothic", sans-serif !important; font-size: 26px !important; font-weight: 900 !important; margin: 0 !important; color: #111111; letter-spacing: -1.2px !important; white-space: nowrap !important; line-height: 1.2 !important;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family: "Nanum Gothic", sans-serif; font-size: 13px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            
            <!-- [남명 정보 박스] -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 18px 20px; border-radius: 14px; margin-bottom: 14px;'>
                <h2 style='font-family: "Nanum Gothic", sans-serif; font-size: 22px; font-weight: 800; color: #1A237E; margin: 0 0 10px 0;'>{u_icon} 남명 : {clean_u_name} 님 <span style='font-size: 15px; color: #555555; font-weight: 600;'>( {u_age}세 )</span></h2>
                <div style='font-family: "Nanum Gothic", sans-serif; font-size: 15px; font-weight: 700; color: #111111; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {u_sol} | [음력] {final_u_lun}</p>
                    <p style='margin: 3px 0 0 0; color: #D50000; font-weight: 800; white-space: nowrap;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
            
            <!-- [여명 정보 박스] -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 18px 20px; border-radius: 14px;'>
                <h2 style='font-family: "Nanum Gothic", sans-serif; font-size: 22px; font-weight: 800; color: #D50000; margin: 0 0 10px 0;'>{p_icon} 여명 : {clean_p_name} 님 <span style='font-size: 15px; color: #555555; font-weight: 600;'>( {p_age}세 )</span></h2>
                <div style='font-family: "Nanum Gothic", sans-serif; font-size: 15px; font-weight: 700; color: #111111; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap;'>[양력] {p_sol} | [음력] {final_p_lun}</p>
                    <p style='margin: 3px 0 0 0; color: #D50000; font-weight: 800; white-space: nowrap;'>태어난 시간 : {p_time}</p>
                </div>
            </div>
            
            <!-- [발행일자 및 연구소명] -->
            <p style='font-family: "Nanum Gothic", sans-serif; font-size: 18px; margin-top: 30px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>
            <p style='font-family: "Nanum Gothic", sans-serif; font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 10px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class='page-break'></div>
    """

def get_daewun_compare_box(m_name, m_un_html, w_name, w_un_html):
    """부부 대운 흐름 교차 분석 대조 상자"""
    return f"""
    <div style='margin-top: 25px; margin-bottom: 25px;'>
        <h2 style='text-align:center; color:#1A237E; font-size: 21px; font-weight:800; margin-bottom: 6px; letter-spacing: 0.5px;'>
            [ 부부 대운 흐름 교차 분석 ]
        </h2>
        <p style='text-align:center; color:#666; font-size: 13px; margin-bottom: 20px;'>
            두 사람의 시공간 궤도를 한눈에 비교하는 대운 로드맵입니다.
        </p>
        <div style='margin-bottom: 20px; background: #fafafa; border-left: 4px solid #1565C0; padding: 12px 16px; border-radius: 8px;'>
            <h4 style='color:#1565C0; font-weight:800; font-size: 15px; margin-top: 0; margin-bottom: 12px; display: flex; align-items: center;'>
                <span style='font-size: 17px; margin-right: 6px;'>♂️</span> 남명 ({m_name}님) 대운 흐름
            </h4>
            <div style='overflow-x: auto;'>
                {m_un_html}
            </div>
        </div>
        <div style='background: #fafafa; border-left: 4px solid #4A148C; padding: 12px 16px; border-radius: 8px;'>
            <h4 style='color:#4A148C; font-weight:800; font-size: 15px; margin-top: 0; margin-bottom: 12px; display: flex; align-items: center;'>
                <span style='font-size: 17px; margin-right: 6px;'>♀️</span> 여명 ({w_name}님) 대운 흐름
            </h4>
            <div style='overflow-x: auto;'>
                {w_un_html}
            </div>
        </div>
    </div>
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

def get_auto_comparison_cover(app_version, p_icon, u_name, sol_str, lun_str, time_str, today_str):
    """4-1 사주 1:1 대조 분석서 표지"""
    return f"""
    <div class='report-page cover-page'>
        <div class='vip-inset-frame' style='text-align: center;'>
            <div style='border-bottom:3px double #1A237E; padding-bottom:18px; margin-bottom:35px;'>
                <h1 style='font-family:"Nanum Myeongjo", serif !important; font-size: 24px !important; white-space: nowrap !important; margin:0 !important; color:#1A237E !important; font-weight:800;'>전통 명리 vs 시공명리 1:1 비교</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span style='font-family:"Nanum Myeongjo", serif; font-size: 13px; letter-spacing: 1px; color:#666;'>{app_version}</span>
                </div>
            </div>
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 12px; margin-bottom: 25px;'>
                <h2 style='font-family:"Nanum Myeongjo", serif; font-size: 22px; font-weight: 800; color: #111111; margin-bottom: 15px;'>{p_icon} 신청인 : {u_name} 님</h2>
                <div style='font-family:"Nanum Myeongjo", serif; font-size: 15px; line-height: 1.9;'>
                    <p style='margin: 0; white-space: nowrap; font-weight: 700; color: #000000;'>[양력] {sol_str} | [음력] {lun_str}</p>
                    <p style='margin: 4px 0 0 0; white-space: nowrap; font-weight: 700; color: #1A237E;'>{time_str}</p>
                </div>
            </div>
            <p style='font-family:"Nanum Myeongjo", serif; font-size: 16px; margin-top: 35px; font-weight: 700; color:#444;'>{today_str}</p>
            <p style='font-family:"Nanum Myeongjo", serif; font-size: 21px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class='page-break'></div>
    """

def get_auto_gunghap_comparison_cover(app_version, m_name, m_sol, m_lun, m_time, f_name, f_sol, f_lun, f_time, today_str):
    """4-2 궁합 1:1 대조 분석서 표지"""
    return f"""
    <div class='report-page cover-page'>
        <div class='vip-inset-frame' style='text-align: center;'>
            <div style='border-bottom:3px double #1A237E; padding-bottom:18px; margin-bottom:28px;'>
                <h1 style='font-family:"Nanum Myeongjo", serif !important; font-size: 23px !important; white-space: nowrap !important; margin:0 !important; color:#1A237E !important; font-weight:800;'>전통 궁합 vs 시공명리 궁합 1:1 비교</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family:"Nanum Myeongjo", serif; font-size: 13px; letter-spacing: 1px; color:#666;'>{app_version}</span>
                </div>
            </div>
            
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 18px 20px; border-radius: 12px; margin-bottom: 12px;'>
                <h2 style='font-family:"Nanum Myeongjo", serif; font-size: 20px; font-weight: 800; color: #111111; margin-bottom: 8px;'>♂️ 남명 : {m_name} 님</h2>
                <div style='font-family:"Nanum Myeongjo", serif; font-size: 14px; line-height: 1.7;'>
                    <p style='margin: 0; white-space: nowrap; font-weight: 700; color: #000000;'>[양력] {m_sol} | [음력] {m_lun}</p>
                    <p style='margin: 3px 0 0 0; white-space: nowrap; font-weight: 700; color: #1A237E;'>{m_time}</p>
                </div>
            </div>
            
            <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 18px 20px; border-radius: 12px;'>
                <h2 style='font-family:"Nanum Myeongjo", serif; font-size: 20px; font-weight: 800; color: #111111; margin-bottom: 8px;'>♀️ 여명 : {f_name} 님</h2>
                <div style='font-family:"Nanum Myeongjo", serif; font-size: 14px; line-height: 1.7;'>
                    <p style='margin: 0; white-space: nowrap; font-weight: 700; color: #000000;'>[양력] {f_sol} | [음력] {f_lun}</p>
                    <p style='margin: 3px 0 0 0; white-space: nowrap; font-weight: 700; color: #1A237E;'>{f_time}</p>
                </div>
            </div>
            
            <p style='font-family:"Nanum Myeongjo", serif; font-size: 16px; margin-top: 30px; font-weight: 700; color:#444;'>{today_str}</p>
            <p style='font-family:"Nanum Myeongjo", serif; font-size: 21px; font-weight: 800; color: #1A237E; margin-top: 12px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class='page-break'></div>
    """

def get_auto_comparison_header():
    """대조 분석서 본문 헤더"""
    return """<div style='margin-bottom:20px; padding-bottom:10px; border-bottom:2px solid #1A237E;'>
        <h2 style='font-family:"Nanum Myeongjo", serif !important; font-size:21px !important; font-weight:800 !important; color:#1A237E !important; margin:0 !important; text-align:center; white-space:nowrap;'>
            ⚖️ 전통 명리 vs 시공명리 1:1 비교 리포트
        </h2>
    </div>"""

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

def render_gunghap_comparison_report(couple_fact_html, external_raw_box, ai_content_html):
    """
    4-2 타 감명서 비교 (궁합) 전용 뷰
    - 바깥선/그림자 없는 A4 백지 캔버스 + 안쪽 .vip-inset-frame 단독 적용
    - 최상단 메인 타이틀: 22px / 900 / 중앙 정렬 / 밑줄 2.5px solid #1A237E
    """
    master_body = f"""
    <div style="font-family: 'Nanum Myeongjo', serif; font-size: 22px; font-weight: 900; color: #1A237E; text-align: center; padding: 6px 0 10px 0; margin-bottom: 15px; border-bottom: 2.5px solid #1A237E; letter-spacing: -0.5px;">
        🔍 타 감명서 비교 (궁합) 1:1 정밀 분석
    </div>
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
