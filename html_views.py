# ==============================================================================
# html_views.py (ver 85.7 Master Layout + ver 50.5 폰트 황금비율/백지차단/정규식 진화)
# ==============================================================================
import re
import streamlit as st

# ==============================================================================
# 📦 섹션 1. 글로벌 스타일 (CSS) 및 AI 통변 텍스트 포맷터
# ==============================================================================

def get_global_css():
    """전체 시스템 UI/UX 및 화면/인쇄 듀얼 분리 스타일시트 (ver 50.5 폰트/가독성 복원)"""
    return """<style>
    @import url("[https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Nanum+Gothic:wght@400;700;800;900&display=swap](https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Nanum+Gothic:wght@400;700;800;900&display=swap)");

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

    /* 🌟 감명서 리포트 전 영역 나눔명조체 완벽 통일 */
    .report-page, .report-page *, .cover-page, div.cover-page *, .choyeon-premium-report, .result-table td { 
        font-family: 'Nanum Myeongjo', 'Batang', serif !important; 
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        color: #111111;
    }

    /* 🌟 [황금비율 1] h1 간판 타이틀 (50.5와 동일: 가운데 정렬, 26px, 밑줄 쫙!) */
    .report-page h1:not(.cover-page h1) {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #1A237E !important;
        text-align: center !important;
        border-bottom: 3px solid #1A237E !important;
        padding-bottom: 10px !important;
        margin-bottom: 25px !important;
        margin-top: 0 !important;
    }

    /* 🌟 [황금비율 2] h3 대목차 (여백과 폰트 굵기를 날렵하게 800) */
    .report-page h3 {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #1A237E !important;
        border-bottom: none !important;
        margin-top: 30px !important;
        margin-bottom: 15px !important;
    }

    /* 🌟 [황금비율 3] 에세이 서술 본문 (줄간격 1.8, 양쪽 정렬) */
    .content-box-loose, .content-box-loose p, .ai-content p {
        line-height: 1.8 !important;
        text-align: justify !important;
        word-break: keep-all !important;
        font-family: 'Nanum Myeongjo', serif !important;
    }

    /* 🌟 [황금비율 4] 모든 HTML 표 디자인 50.5 양식 롤백 (폰트 과도한 굵기 최적화) */
    .result-table { width: 100%; border-collapse: collapse !important; border: 3px solid #3E2723 !important; margin-bottom: 15px; table-layout: fixed; }
    .result-table td { border: 1px solid #444 !important; padding: 2px 1px !important; text-align: center; vertical-align: middle; font-weight: 800 !important; font-size: 14px; line-height: 1.2 !important; word-break: keep-all; }

    .top-header-cell { background-color: #1A237E !important; height: 32px !important; }
    .top-header-cell td { background-color: #1A237E !important; color: #FFFFFF !important; font-weight: 800 !important; font-size: 15px !important; border: 1px solid #444 !important; }
    .header-cell-main, .header-cell-sub { background-color: #E8EAF6 !important; color: #000000 !important; font-weight: 700 !important; font-size: 14px !important; }

    .b-text { font-weight: 800 !important; color: #000000 !important; display: inline-block; }
    .b-text-point { font-weight: 800 !important; color: #1A237E !important; display: inline-block; }

    /* 오행 색상 규격 */
    .color-목 { background: #2E7D32 !important; color: #FFF !important; }
    .color-화 { background: #C62828 !important; color: #FFF !important; }
    .color-토 { background: #F9A825 !important; color: #000 !important; }
    .color-금 { background: #9E9E9E !important; color: #FFF !important; }
    .color-수 { background: #212121 !important; color: #FFF !important; }

    /* 버튼 기본 공통 규격 */
    div.stButton > button { font-family: 'Nanum Gothic', sans-serif !important; font-weight: 800 !important; font-size: 16px !important; border-radius: 8px !important; height: 50px !important; border: none !important; box-shadow: 0 4px 6px rgba(0,0,0,0.12) !important; }
    div.stButton > button[kind="primary"], div.stButton > button[data-testid="baseButton-primary"] { background-color: #D32F2F !important; color: #FFFFFF !important; }
    div.stButton > button[kind="secondary"], div.stButton > button[data-testid="baseButton-secondary"] { background-color: #00A843 !important; color: #FFFFFF !important; }

    /* 🌟 A4 백지 캔버스 & 둥근 사각 액자 */
    .report-page { width: 210mm; height: auto; min-height: 250mm; max-width: 100%; margin: 20px auto; background-color: #FFFFFF !important; border: none !important; box-shadow: none !important; padding: 12mm 10mm; box-sizing: border-box; color: #111111; page-break-after: always; }
    .vip-inset-frame { border: 2px solid #3E2723 !important; border-radius: 12px !important; padding: 25px !important; background-color: #FFFFFF !important; box-shadow: none !important; box-sizing: border-box; }

    .page-break { display: none; }
    
    /* 🚨 PDF 인쇄 모드 전용 (백지 방지 및 강제 CSS 최적화) */
    @media print { 
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header, [data-testid="stHeader"] { display: none !important; }
        body, html, .stApp { background-color: white !important; margin: 0 !important; padding: 0 !important; -webkit-print-color-adjust: exact !important; }
        
        /* 백지 버그 주범 1: 투명 상단 여백 제거 */
        .block-container, div[data-testid="stAppViewBlockContainer"] { padding-top: 0 !important; padding-bottom: 0 !important; margin-top: 0 !important; }
        
        /* 백지 버그 주범 2: 캔버스 높이 및 고정 박스 그림자 해제 */
        .report-page { box-shadow: none !important; margin: 0 auto !important; width: 100% !important; padding: 0 !important; height: auto !important; min-height: auto !important; page-break-after: always !important; }
        .report-page:last-of-type { page-break-after: auto !important; }
        .page-break { display: block !important; page-break-after: always !important; break-after: page !important; height: 1px; }
        .vip-inset-frame { box-shadow: none !important; border: 1.5px solid #333333 !important; padding: 15px !important; }
    }
    </style>
    """

def format_ai_text_to_html(text, qna_text=""):
    if not text: return ""
    
    # 🚨 [수술] 소스코드 누수 차단: AI가 뱉는 마크다운 껍데기(```html 등) 완벽 제거
    text = re.sub(r'```(?:html)?\s*', '', text)
    
    # 🚨 [수술] 불필요한 색상 오염 차단: AI가 던지는 <span class="color-목"> 같은 태그 강제 삭제
    text = re.sub(r'<span class="color-[^>]+">(.*?)</span>', r'\1', text)
    
    # 간지 등에 불필요한 배경/색상이 입혀지던 기존의 정규식을 무력화하고, 
    # 단순한 볼드(굵게) 처리만 남겨 검정색으로 50.5처럼 롤백!
    text = re.sub(r':[a-zA-Z]+\[(.*?)\]', r'\1', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b style="font-weight: 800;">\1</b>', text)
    
    lines = text.split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list: html_lines.append("</div>"); in_list = False
            html_lines.append("<div style='height: 10px;'></div>")
            continue
            
        lower_line = line.lower()
        if lower_line.startswith('<div') or lower_line.startswith('</div') or \
           lower_line.startswith('<table') or lower_line.startswith('</table') or \
           lower_line.startswith('<tr') or lower_line.startswith('</tr') or \
           lower_line.startswith('<td') or lower_line.startswith('</td') or \
           lower_line.startswith('<th') or lower_line.startswith('</th') or \
           lower_line.startswith('<h3'):
            if in_list: html_lines.append("</div>"); in_list = False
            html_lines.append(line)
            continue
            
        is_colon_split = False
        forced_desc_html = ""
        
        if (':' in line or '：' in line) and not re.search(r'<[^>]+>', line):
            if not re.search(r'\d\s*[:：]\s*\d', line) and not re.match(r'^(?:<[^>]+>)*\s*[◆▶▷]', line):
                parts = re.split(r'[:：]', line, 1)
                title_part = parts[0].strip()
                desc_part = parts[1].strip()
                line = title_part
                forced_desc_html = f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 16px; font-weight: 400; line-height: 1.8; margin-top: 4px; margin-bottom: 14px; color: #111111; text-indent: 14px; text-align: justify; word-break: keep-all;'>{desc_part}</p>"
                is_colon_split = True

        if re.match(r'^(?:<[^>]+>)*\s*\d+\.\s', line):
            if in_list: html_lines.append("</div>"); in_list = False
            clean_line = line.replace('#', '').strip()
            html_lines.append(f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 20px; font-weight: 800; color: #1A237E; margin-top: 30px; margin-bottom: 12px;'>{clean_line}</div>")
            if forced_desc_html: html_lines.append(forced_desc_html)

        # 🚨 [수술] (1), (2) 등 괄호 형식의 소제목 완벽 인식 및 들여쓰기 디자인 적용
        elif re.match(r'^(?:<[^>]+>)*\s*\(\d+\)\s', line):
            if in_list: html_lines.append("</div>"); in_list = False
            clean_line = line.replace('#', '').strip()
            html_lines.append(f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 18px; font-weight: 800; color: #2C3E50; margin-top: 22px; margin-bottom: 8px;'>{clean_line}</div>")
            if forced_desc_html: html_lines.append(forced_desc_html)

        elif re.match(r'^(?:<[^>]+>)*\s*\d+\)\s', line):
            if in_list: html_lines.append("</div>"); in_list = False
            clean_line = line.replace('#', '').strip()
            html_lines.append(f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 18px; font-weight: 800; color: #2C3E50; margin-top: 22px; margin-bottom: 8px;'>{clean_line}</div>")
            if forced_desc_html: html_lines.append(forced_desc_html)

        elif re.match(r'^(?:<[^>]+>)*\s*[①②③④⑤⑥⑦⑧⑨⑩]\s*', line):
            if in_list: html_lines.append("</div>"); in_list = False
            clean_line = line.replace('#', '').strip()
            html_lines.append(f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 17px; font-weight: 700; color: #34495E; margin-top: 16px; margin-bottom: 6px; padding-left: 8px;'>{clean_line}</div>")
            if forced_desc_html: html_lines.append(forced_desc_html)

        elif re.match(r'^(?:<[^>]+>)*\s*[◆▶▷]', line):
            if in_list: html_lines.append("</div>"); in_list = False
            symbol_match = re.search(r'([◆▶▷])', line)
            symbol = symbol_match.group(1) if symbol_match else '▶'
            padding_left = "14px" if symbol == '◆' else ("18px" if symbol == '▶' else "24px")
            desc_padding = str(int(padding_left.replace("px", "")) + 18) + "px"
            clean_line = re.sub(r'^(?:<[^>]+>)*\s*[◆▶▷]\s*', '', line).replace('#', '').strip()
            
            if (':' in clean_line or '：' in clean_line) and not re.search(r'\d\s*[:：]\s*\d', clean_line):
                parts = re.split(r'[:：]', clean_line, 1)
                title_part = parts[0].strip()
                desc_part = parts[1].strip()
                html_lines.append(f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 16px; font-weight: 800; color: #2C3E50; margin-top: 12px; margin-bottom: 4px; padding-left: {padding_left};'><span style='margin-right: 6px;'>{symbol}</span>{title_part}:</div>")
                if desc_part:
                    html_lines.append(f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 16px; font-weight: 400; color: #111111; line-height: 1.8; margin-bottom: 8px; padding-left: {desc_padding}; word-break: keep-all; text-align: justify;'>{desc_part}</div>")
            else:
                html_lines.append(f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 16px; font-weight: 400; color: #111111; line-height: 1.8; margin-top: 8px; margin-bottom: 8px; padding-left: {padding_left}; word-break: keep-all; text-align: justify;'><span style='margin-right: 6px;'>{symbol}</span>{clean_line}</div>")

        else:
            if in_list: html_lines.append("</div>"); in_list = False
            clean_line = line.replace('#', '').strip()
            # 줄간격 1.8 및 명조체 세팅 (50.5 스타일 통일)
            html_lines.append(f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 16px; font-weight: 400; line-height: 1.8; margin-top: 0px; margin-bottom: 14px; color: #111111; letter-spacing: -0.2px; text-indent: 14px; text-align: justify; word-break: keep-all;'>{clean_line}</p>")
            if forced_desc_html: html_lines.append(forced_desc_html)
        
    if in_list: html_lines.append("</div>")
    main_html = "\n".join(html_lines)

    qna_html = ""
    if qna_text:
        clean_qna_body = qna_text.replace('💡', '').strip()
        qna_body = clean_qna_body.replace('\n\n', '<br><br>').replace('\n', '<br>')
        qna_html = f"""
        <div style='background-color: #FAFAFA; border: 1px solid #E0E0E0; border-radius: 12px; padding: 24px; margin-top: 28px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.03);'>
            <div style='font-family: "Nanum Myeongjo", serif; font-size: 20px; font-weight: 800; color: #1A237E; margin-top: 0px; margin-bottom: 16px; border-bottom: 2px solid #E8EAF6; padding-bottom: 10px;'>
                💡 사주박사 1:1 심층 솔루션 답변
            </div>
            <div style='font-family: "Nanum Myeongjo", serif; font-size: 16px; font-weight: 400; line-height: 1.8; color: #111111; text-indent: 14px; text-align: justify; word-break: keep-all;'>
                {qna_body}
            </div>
        </div>
        """
        
    return f"<div class='ai-content' style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif;'>\n{main_html}\n{qna_html}\n</div>"


# ==============================================================================
# 📦 섹션 2. 공통 역학 테이블 및 컴포넌트 모듈 (간지 강조 및 폰트 핏 적용)
# ==============================================================================

def td_func(val, engine):
    oh = engine.get_color(val)
    cls_str = f"color-{oh}" if oh != '무' else ""
    # 🌟 간지 글자 크기는 살리고 뚱뚱함(900)을 800으로 조정
    return f"<td class='{cls_str}' style='font-size: 24px !important; font-weight: 800 !important; border:1px solid #444 !important; padding: 1px !important; line-height: 1.2 !important; width:21.25%;'>{val}</td>"

def get_personal_cover(version, report_title, u_icon, u_name, u_sol, u_lun, u_time, today_str):
    """1인용 표지: 백지 방지(height 유연화) 및 타이틀 1줄 고정"""
    raw_title = str(report_title or "초연 전통 명리 사주풀이").replace("🏮", "").replace("🎯", "")
    clean_title = " ".join(raw_title.split())
    clean_u_name = str(u_name or "무명").strip()

    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:100%; height:auto; display:flex; flex-direction:column; justify-content:center; align-items:center; box-sizing: border-box; -webkit-print-color-adjust: exact; padding-top: 60px; padding-bottom: 60px;'>
        <div style='border: 4px solid #1A237E; padding: 42px 24px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 92%; max-width: 680px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 28px; width: 100%; box-sizing: border-box;'>
                <!-- 🚨 타이틀 1줄 고정: font-size 30px, nowrap 강제 -->
                <h1 style='font-family: "Nanum Myeongjo", serif !important; font-size: 30px !important; font-weight: 900 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -1px !important; white-space: nowrap !important; line-height: 1.4 !important; text-align: center; border-bottom: none !important;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family: "Nanum Myeongjo", serif; font-size: 14px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 22px 20px; border-radius: 14px; margin-bottom: 24px;'>
                <h2 style='font-family: "Nanum Myeongjo", serif; font-size: 23px; font-weight: 800; color: #1A237E; margin: 0 0 10px 0; border-bottom: none !important;'>{u_icon} {clean_u_name} 님</h2>
                <div style='font-family: "Nanum Myeongjo", serif; font-size: 16px; line-height: 1.8;'>
                    <p style='margin: 0; color: #000000;'><strong style='font-weight: 900 !important;'>[양력] {u_sol} | [음력] {u_lun}</strong></p>
                    <p style='margin: 4px 0 0 0; font-weight: 800; color: #1A237E;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 17px; margin-top: 35px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 24px; font-weight: 900; color: #1A237E; margin-top: 8px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    """

def get_couple_cover(version, report_title, u_icon, u_name, u_age, u_sol, u_lun, u_time, p_icon, p_name, p_age, p_sol, p_lun, p_time, today_str):
    """2인용(궁합) 표지: 백지 방지, 타이틀 1줄 고정, 여성(여명) 붉은색 금기(남명과 동일 남색) 적용"""
    raw_title = str(report_title or "초연 전통 명리 궁합풀이").replace("🏮", "").replace("🎯", "")
    clean_title = " ".join(raw_title.split())
    clean_u_name, clean_p_name = str(u_name or "무명").strip(), str(p_name or "무명").strip()
    safe_color = "#1A237E" # 여명 붉은색 강제 차단용

    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:100%; height:auto; display:flex; flex-direction:column; justify-content:center; align-items:center; box-sizing: border-box; -webkit-print-color-adjust: exact; padding-top: 40px; padding-bottom: 40px;'>
        <div style='border: 4px solid #1A237E; padding: 42px 24px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 92%; max-width: 680px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 28px; width: 100%; box-sizing: border-box;'>
                <h1 style='font-family: "Nanum Myeongjo", serif !important; font-size: 30px !important; font-weight: 900 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -1px !important; white-space: nowrap !important; line-height: 1.4 !important; text-align: center; border-bottom: none !important;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family: "Nanum Myeongjo", serif; font-size: 14px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 18px 20px; border-radius: 14px; margin-bottom: 15px;'>
                <h2 style='font-family: "Nanum Myeongjo", serif; font-size: 20px; font-weight: 800; color: #1565C0; margin: 0 0 8px 0; border-bottom: none !important;'>{u_icon} {clean_u_name} 님 ({u_age}세)</h2>
                <div style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.6;'>
                    <p style='margin: 0; color: #000000;'><strong style='font-weight: 800 !important;'>[양력] {u_sol} | [음력] {u_lun}</strong></p>
                    <p style='margin: 4px 0 0 0; font-weight: 800; color: #1565C0;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
            
            <!-- 🚨 여성(신부) 정보 블록: 빨간색(#C62828) 버리고 남명과 동일한 진한 남색 테마 적용 -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 18px 20px; border-radius: 14px; margin-bottom: 24px;'>
                <h2 style='font-family: "Nanum Myeongjo", serif; font-size: 20px; font-weight: 800; color: {safe_color}; margin: 0 0 8px 0; border-bottom: none !important;'>{p_icon} {clean_p_name} 님 ({p_age}세)</h2>
                <div style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.6;'>
                    <p style='margin: 0; color: #000000;'><strong style='font-weight: 800 !important;'>[양력] {p_sol} | [음력] {p_lun}</strong></p>
                    <p style='margin: 4px 0 0 0; font-weight: 800; color: {safe_color};'>태어난 시간 : {p_time}</p>
                </div>
            </div>
            
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 17px; margin-top: 25px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 24px; font-weight: 900; color: #1A237E; margin-top: 8px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    """

def get_info_header(p_icon, name, gender, marital, age, sol_str, lun_str, time_str, p_color="#1A237E"):
    # 🚨 여성 이름 붉은색 강제 차단 (진한 남색 정화)
    if p_color.upper() in ["#C62828", "#D50000", "#E91E63", "#FF0000", "RED"]:
        p_color = "#1A237E"
        
    return f"""
    <div style='font-family:"Nanum Myeongjo", serif; text-align:center; margin-bottom:15px; line-height:1.6;'>
        <span style='font-size:19px; font-weight:800; color:{p_color}; letter-spacing:0.5px; white-space:nowrap;'>{p_icon} {name}님 ({gender}, {marital}, {age}세)</span><br>
        <span style='font-size:15px; font-weight:700; color:#333; letter-spacing:0.5px; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} <span style='color:#1A237E;'>{time_str}</span>]</span>
    </div>
    """

def generate_saju_table_data(gans, jjis, ds, gender, engine):
    """사주 원국 HTML 생성 (로직 85.1 유지, 폰트/색상 50.5 규격 롤백 적용)"""
    gan_rel = "".join([f"<td style='border:1px solid #444; padding:3px 0 !important; font-size:14px;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])
    hs, ds_val, ms, ys = gans[0], gans[1], gans[2], gans[3]
    
    # 🌟 日元 빨간색 강조
    gan_ss = f"<td style='border:1px solid #444; padding:3px 0 !important; font-size:14px;'>{engine.get_ss(ds, hs)}</td>" \
             f"<td style='border:1px solid #444; padding:3px 0 !important; font-size:14px;'><span style='color:#C62828; font-weight:800;'>日元</span></td>" \
             f"<td style='border:1px solid #444; padding:3px 0 !important; font-size:14px;'>{engine.get_ss(ds, ms)}</td>" \
             f"<td style='border:1px solid #444; padding:3px 0 !important; font-size:14px;'>{engine.get_ss(ds, ys)}</td>"

    hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]
    gan_row_html = "".join([td_func(g, engine) for g in gans])
    ji_row_html = "".join([td_func(j, engine) for j in jjis])

    ji_ss_html = f"<td style='border:1px solid #444; padding:3px 0 !important; font-size:14px;'>{engine.get_ss(ds, hb)}</td>" \
                 f"<td style='border:1px solid #444; padding:3px 0 !important; font-size:14px;'>{engine.get_ss(ds, db)}</td>" \
                 f"<td style='border:1px solid #444; padding:3px 0 !important; font-size:14px;'>{engine.get_ss(ds, mb)}</td>" \
                 f"<td style='border:1px solid #444; padding:3px 0 !important; font-size:14px;'>{engine.get_ss(ds, yb)}</td>"

    jijanggan_html = "".join([f"<td style='padding:0 !important; border:1px solid #444; font-size:14px;'>{engine.get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])

    ji_rel_rows = ""
    for l_idx, r_idx in enumerate([1, 2, 0, 3]):
        b_top = "0px !important"
        b_bot = "2px solid #CCCCCC !important" if l_idx == 1 else "1px solid #444 !important"
        cells = []
        for ci in range(4):
            if ci == r_idx:
                lbl_txt = f"({jjis[r_idx]})→" if r_idx == 0 else (f"←({jjis[r_idx]})" if r_idx == 3 else f"←({jjis[r_idx]})→")
                cells.append(f"<td style='color:#C62828; font-weight:800; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important; padding:2px 0 !important; vertical-align: middle; font-size:14px;'>{lbl_txt}</td>")
            else:
                rel_val = engine.get_ji_rel_set(jjis[r_idx], jjis[ci])
                txt_color = "#000" if rel_val != "-" else "#BBB"
                cells.append(f"<td style='color:{txt_color}; font-weight:700; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important; padding:2px 0 !important; vertical-align: middle; font-size:14px;'>{rel_val}</td>")
                
        lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important; vertical-align: middle; padding:0 !important;'>합충형파해</td>" if l_idx == 0 else ""
        ji_rel_rows += f"<tr style='border:none; height:auto;'>{lbl}{''.join(cells)}</tr>"

    unsung = "".join([f"<td style='color:#0D47A1; font-weight:700; font-size:14px; border:1px solid #444 !important; padding:3px 0 !important;'>{engine.get_unsung(ds, jjis[i])}</td>" for i in range(4)])

    y_shinsal_tds, d_shinsal_tds = [], []
    for i in range(4):
        y_s = engine.get_12_shinsal(yb, jjis[i]) if jjis[i] != "-" else "-"
        raw_d = engine.get_12_shinsal(db, jjis[i]) if jjis[i] != "-" else "-"
        clean_d = str(raw_d).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
        d_s = f"({clean_d})" if clean_d and clean_d != "-" and clean_d != "None" else "(-)"
        y_shinsal_tds.append(f"<td style='color:#C62828; font-weight:700; font-size:14px; border:1px solid #444 !important; padding:3px 0 !important;'>{y_s}</td>")
        d_shinsal_tds.append(f"<td style='color:#C62828; font-weight:700; font-size:14px; border:1px solid #444 !important; padding:3px 0 !important;'>{d_s}</td>")
        
    gen_shinsals = []
    for i in range(4):
        filtered = engine.get_general_shinsal_filtered(i, gans, jjis, gender)
        gen_shinsals.append("<br>".join(filtered[:6]) if filtered else "-")
    gen_shinsal = "".join([f"<td style='vertical-align:top; padding:4px !important; font-weight:700; font-size:13px; border:1px solid #444 !important; line-height:1.4;'>{s}</td>" for s in gen_shinsals])

    table_html = f"""
    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center; border: 3px solid #3E2723 !important; font-family:"Nanum Myeongjo", serif;'>
        <tr class='top-header-cell'>
            <td style='width:15%; border:1px solid #444; color:#FFFFFF !important; font-weight:800; padding:5px 0 !important;'>구분</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:800; padding:5px 0 !important;'>시주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:800; padding:5px 0 !important;'>일주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:800; padding:5px 0 !important;'>월주</td>
            <td style='width:21.25%; border:1px solid #444; color:#FFFFFF !important; font-weight:800; padding:5px 0 !important;'>년주</td>
        </tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:700; padding:3px 0 !important;'>천간합충</td>{gan_rel}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:700; padding:3px 0 !important;'>천간십성</td>{gan_ss}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:800; font-size:16px !important; padding:0 !important;'>천간</td>{gan_row_html}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:800; font-size:16px !important; padding:0 !important;'>지지</td>{ji_row_html}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:700; padding:3px 0 !important;'>지지십성</td>{ji_ss_html}</tr>
        <tr><td class='header-cell-main' style='padding:0 !important; border:1px solid #444; background:#f5f5f5; font-weight:700;'>지장간</td>{jijanggan_html}</tr>
        {ji_rel_rows}
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:700; padding:3px 0 !important;'>십이운성</td>{unsung}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:700; padding:3px 0 !important;'>년지신살</td>{''.join(y_shinsal_tds)}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:700; padding:3px 0 !important;'>일지신살</td>{''.join(d_shinsal_tds)}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:700; padding:3px 0 !important;'>일반신살</td>{gen_shinsal}</tr>
    </table>
    """
    return table_html

def get_master_bar(calc_d, m, f, e, mtl, w, guiin, n_gong, i_gong, samjae_color, cur_samjae):
    return f"""
    <div style="background:#FFF8E1; padding:10px 12px; border-radius:8px; margin:15px 0; border:2px solid #3E2723; font-family:'Nanum Myeongjo', serif; font-weight:700; font-size:14px; color:#1A237E; display:flex; justify-content:space-between; align-items:center; white-space:nowrap;">
        <span style="flex: 1; text-align: center;">🔢 대운수: {calc_d}</span>
        <span style="flex: 1; text-align: center;">💥 오행: 木{m} 火{f} 土{e} 金{mtl} 水{w}</span>
        <span style="flex: 1; text-align: center;">🌟 천을귀인: {guiin}</span>
        <span style="flex: 1; text-align: center;">🎯 공망: [년]{n_gong} [일]{i_gong}</span>
        <span style="flex: 1; text-align: center;">🌪️ 삼재: <span style="color:{samjae_color}; font-weight: 800;">{cur_samjae}</span></span>
    </div>
    """

# 🌟 대운/세운/월운표: ver 50.5 황금비율 (크기 UP, 뚱뚱함 DOWN)
def get_un_layout(title, content):
    return f"""
    <div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:800; color:#1A237E; font-family:"Nanum Myeongjo", serif;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px; table-layout:fixed; font-family:"Nanum Myeongjo", serif;'>
        {content}
    </div>
    """

def get_un_cell(title_str, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, y_shinsal, d_shinsal, bg_col, b_left, is_current=False):
    u_val = unsung if unsung and str(unsung).strip() else "-"
    y_val = y_shinsal if y_shinsal and str(y_shinsal).strip() and str(y_shinsal).strip() != "None" else "-"
    clean_d = str(d_shinsal).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
    d_val = f"({clean_d})" if clean_d and clean_d != "-" and clean_d != "None" else "(-)"
    
    active_style = "border: 3px solid #E65100 !important;" if is_current else f"border-left: {b_left}; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
    header_bg = "#E65100" if is_current else "#3E2723"
    bg_col = "#FFF9C4" if is_current else bg_col
        
    return f"""
    <div style='flex:1; width:10%; {active_style} text-align:center; background-color:{bg_col}; min-width:0; display:flex; flex-direction:column; box-sizing:border-box; overflow:hidden;'>
        <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:700; font-size:13px; height:28px; display:flex; align-items:center; justify-content:center; white-space:nowrap; letter-spacing:-0.5px; line-height:1;'>{title_str}</div>
        <div style='font-size:13px; font-weight:700; color:#000000; height:24px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:18px; font-weight:800; height:32px; display:flex; align-items:center; justify-content:center; line-height:1;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:18px; font-weight:800; height:32px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ji}</div>
        <div style='font-size:13px; font-weight:700; color:#000000; height:24px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:12px; font-weight:700; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden; line-height:1;'><span style='color:#0D47A1;'>{u_val}</span></div>
        <div class='color-shinsal' style='font-size:12px; font-weight:700; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden; line-height:1;'><span style='color:#C62828;'>{y_val}</span></div>
        <div class='color-shinsal-day' style='font-size:12px; font-weight:700; border-top:1px dashed #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden; line-height:1;'><span style='color:#C62828;'>{d_val}</span></div>
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
    <div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:800; color:#1A237E; font-family:"Nanum Myeongjo", serif;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px; table-layout:fixed; font-family:"Nanum Myeongjo", serif;'>
        {content}
    </div>
    """

def get_sewun_cell(title_str, tage, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, y_shinsal, d_shinsal, bg_col, b_left, is_current=False):
    u_val = unsung if unsung and str(unsung).strip() else "-"
    y_val = y_shinsal if y_shinsal and str(y_shinsal).strip() else "-"
    clean_d = str(d_shinsal).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
    d_val = f"({clean_d})" if clean_d and clean_d != "-" else "(-)"
    
    active_style = "border: 3px solid #0277BD !important;" if is_current else f"border-left: {b_left}; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
    header_bg = "#0277BD" if is_current else "#3E2723"
    bg_col = "#E1F5FE" if is_current else bg_col
    
    return f"""
    <div style='flex:1; width:8.33%; {active_style} text-align:center; background-color:{bg_col}; display:flex; flex-direction:column; box-sizing:border-box; min-width:0; overflow:hidden;'>
        <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:700; font-size:13px; height:30px; display:flex; align-items:center; justify-content:center; box-sizing:border-box; white-space:nowrap; line-height:1.1;'>
            <span>{title_str}</span>
        </div>
        <div style='font-size:13px; font-weight:700; color:#000000; height:24px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:18px; font-weight:800; height:32px; display:flex; align-items:center; justify-content:center; line-height:1;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:18px; font-weight:800; height:32px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ji}</div>
        <div style='font-size:13px; font-weight:700; color:#000000; height:24px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:12px; font-weight:700; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden; line-height:1;'><span style='color:#0D47A1;'>{u_val}</span></div>
        <div class='color-shinsal' style='font-size:12px; font-weight:700; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden; line-height:1;'><span style='color:#C62828;'>{y_val}</span></div>
        <div class='color-shinsal-day' style='font-size:12px; font-weight:700; border-top:1px dashed #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden; line-height:1;'><span style='color:#C62828;'>{d_val}</span></div>
    </div>
    """

def get_wolun_layout(title, content):
    return f"""
    <div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:800; color:#1A237E; font-family:"Nanum Myeongjo", serif;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px; table-layout:fixed; font-family:"Nanum Myeongjo", serif;'>
        {content}
    </div>
    """

def get_wolun_cell(tm, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, y_shinsal, d_shinsal, bg_col, b_left, is_current=False):
    u_val = unsung if unsung and str(unsung).strip() else "-"
    y_val = y_shinsal if y_shinsal and str(y_shinsal).strip() else "-"
    clean_d = str(d_shinsal).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
    d_val = f"({clean_d})" if clean_d and clean_d != "-" else "(-)"
    
    active_style = "border: 3px solid #2E7D32 !important;" if is_current else f"border-left: {b_left}; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;"
    header_bg = "#2E7D32" if is_current else "#3E2723"
    bg_col = "#E8F5E9" if is_current else bg_col
    
    return f"""
    <div style='flex:1; width:8.33%; {active_style} text-align:center; background-color:{bg_col}; display:flex; flex-direction:column; box-sizing:border-box; min-width:0; overflow:hidden;'>
        <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:700; font-size:13px; height:28px; display:flex; align-items:center; justify-content:center; white-space:nowrap; letter-spacing:-0.5px; line-height:1;'>{tm}월</div>
        <div style='font-size:13px; font-weight:700; color:#000000; height:24px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:18px; font-weight:800; height:32px; display:flex; align-items:center; justify-content:center; line-height:1;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:18px; font-weight:800; height:32px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ji}</div>
        <div style='font-size:13px; font-weight:700; color:#000000; height:24px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ss_ji}</div>
        <div class='color-unsung' style='font-size:12px; font-weight:700; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden; line-height:1;'><span style='color:#0D47A1;'>{u_val}</span></div>
        <div class='color-shinsal' style='font-size:12px; font-weight:700; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden; line-height:1;'><span style='color:#C62828;'>{y_val}</span></div>
        <div class='color-shinsal-day' style='font-size:12px; font-weight:700; border-top:1px dashed #ccc; height:22px; display:flex; align-items:center; justify-content:center; overflow:hidden; line-height:1;'><span style='color:#C62828;'>{d_val}</span></div>
    </div>
    """

def generate_weekly_calendar_html(weekly_days_data, today_day, yb=None, db=None):
    import engine
    content = ""
    for item in weekly_days_data:
        wday = item.get('weekday', '-')
        day_num = item.get('day', 0)
        ganji_str = item.get('ganji') or item.get('ganji_str', '--')
        is_today = item.get('is_today', False) or item.get('is_target_day', False)
        gan_char = ganji_str[0] if len(ganji_str) >= 1 and ganji_str != "-" else "-"
        ji_char = ganji_str[1] if len(ganji_str) >= 2 else "-"
        gan_cls = engine.get_oh_class(gan_char)
        ji_cls = engine.get_oh_class(ji_char)
        ss_val = item.get('ss_ji', '-')
        unsung_val = item.get('un_sung', '-')
        y_shinsal_val, d_shinsal_val = "-", "-"
        try:
            if hasattr(engine, 'get_12_shinsal'):
                if yb and ji_char != "-": y_shinsal_val = engine.get_12_shinsal(yb, ji_char)
                if db and ji_char != "-": d_shinsal_val = engine.get_12_shinsal(db, ji_char)
        except: pass
        
        y_val = f"<span style='color:#C62828;'>{y_shinsal_val}</span>" if y_shinsal_val != "-" else "-"
        clean_d_w = str(d_shinsal_val).strip().replace("(", "").replace(")", "").replace("（", "").replace("）", "")
        d_val = f"<span style='color:#C62828;'>({clean_d_w})</span>" if clean_d_w and clean_d_w != "-" else "<span style='color:#C62828;'>(-)</span>"
        u_val = f"<span style='color:#0D47A1;'>{unsung_val}</span>" if unsung_val != "-" else "-"
            
        if is_today:
            active_style, header_bg, bg_col = "border: 3px solid #2E7D32 !important;", "#2E7D32", "#E8F5E9"
        elif wday == '일':
            active_style, header_bg, bg_col = "border-left: 1px solid #ccc; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;", "#C62828", "#FAFAFA"
        elif wday == '토':
            active_style, header_bg, bg_col = "border-left: 1px solid #ccc; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;", "#1565C0", "#FAFAFA"
        else:
            active_style, header_bg, bg_col = "border-left: 1px solid #ccc; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; border-right: 1px solid #ccc;", "#555555", "#FAFAFA"
        
        content += f"""
        <div style='flex:1; width:14.28%; {active_style} text-align:center; background-color:{bg_col}; display:flex; flex-direction:column; box-sizing:border-box; min-width:0; overflow:hidden;'>
            <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:700; font-size:13px; height:28px; display:flex; align-items:center; justify-content:center; white-space:nowrap; line-height:1;'>{day_num}일 ({wday})</div>
            <div style='font-size:13px; font-weight:700; color:#000000; height:24px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ss_val}</div>
            <div class='{gan_cls}' style='font-size:18px; font-weight:800; height:32px; display:flex; align-items:center; justify-content:center; line-height:1;'>{gan_char}</div>
            <div class='{ji_cls}' style='font-size:18px; font-weight:800; height:32px; display:flex; align-items:center; justify-content:center; line-height:1;'>{ji_char}</div>
            <div class='color-unsung' style='font-size:12px; font-weight:700; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; line-height:1;'>{u_val}</div>
            <div class='color-shinsal' style='font-size:12px; font-weight:700; border-top:1px solid #ccc; height:22px; display:flex; align-items:center; justify-content:center; line-height:1;'>{y_val}</div>
            <div class='color-shinsal-day' style='font-size:12px; font-weight:700; border-top:1px dashed #ccc; height:22px; display:flex; align-items:center; justify-content:center; line-height:1;'>{d_val}</div>
        </div>
        """
    return f"""
    <div style='margin-top:20px; margin-bottom:10px; font-size:18px; font-weight:800; color:#3E2723; font-family:"Nanum Myeongjo", serif;'>📅 이번 주 운세 흐름 (일요일 ~ 토요일)</div>
    <div style='display:flex; flex-direction:row; width:100%; border:3px solid #3E2723; background:white; margin-bottom:15px; table-layout:fixed; font-family:"Nanum Myeongjo", serif;'>
        {content}
    </div>
    """

# ==============================================================================
# 📦 섹션 3. 서술형 텍스트 박스 (인트로, 황금문구, 클로징 등) - 줄간격 1.8 적용
# ==============================================================================

def get_intro_html():
    return """
    <hr style="border: 0; border-top: 2px solid #3E2723; margin: 25px 0;">
    <div style="margin: 0; padding: 0; font-family: 'Nanum Myeongjo', serif;">
        <p style="margin-top: 0; margin-bottom: 12px; font-size: 16px; font-weight: 600; text-align: justify; text-indent: 14px; line-height: 1.8; word-break: keep-all; color: #111111;">
            <b>"초연 시공 명리학"</b>은 5년에 한 번 돌아오는 '60월령과 60일주'의 조합으로 <b>3,600개 유형</b>으로 분류하지만, <b>"기존의 전통 명리학"</b>은 1년에 한 번 돌아오는 '12월지와 60일주'의 조합으로 <b>720개 유형</b>으로 분류하여 풀이합니다.
        </p> 
        <p style="margin-top: 0; margin-bottom: 0; font-size: 16px; font-weight: 600; text-align: justify; text-indent: 14px; line-height: 1.8; word-break: keep-all; color: #111111;">
            따라서, <b>"본 초연 시공 명리학적 풀이"</b>는 기존 명리학적 풀이에 비하여 <b>5배</b>, 요즘 유행하는 16개 유형의 MBTI와 비교하면 무려 <b>225배</b> 더 정확한 사주풀이 입니다.
        </p>
    </div>
    <hr style="border: 0; border-top: 2px solid #3E2723; margin: 25px 0;">
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
    <div style='font-family: "Nanum Myeongjo", serif; font-size: 16px; line-height: 1.8; color: #111111; margin-bottom: 25px; word-break: keep-all;'>
        <p style='text-indent: 14px; text-align: justify; margin-top: 0; margin-bottom: 12px;'>
            기존 명리학적으로 풀이하면 <b style="color: #1A237E;">{name}님</b>은 <b>{wol_korean_str}</b>에 <b>'{gyuk_name}'</b>의 그릇을 갖추고 태어나셨으며, 성격은 <b>'{s_name}'</b>인 <b>'{s_type}'</b>으로 <b>'{s_desc}'</b>하는 기본 성향이 있습니다.
        </p>
        <p style='text-indent: 14px; text-align: justify; margin-top: 0; margin-bottom: 0;'>
            또한, 시공명리학적으로 풀이하면 <b>'{w_val}'</b>의 역동적인 시공간 파동을 지니고 있으며, <b>'{i_val}'</b>의 내면적 본성을 함께 품고 살아갑니다.
        </p>
    </div>
    <hr style="border: 0; border-top: 2px dashed #1A237E; margin: 25px 0;">
    """

def get_closing_html(name):
    return f"""
    <hr style="border: 0; border-top: 2px dashed #1A237E; margin: 35px 0 25px 0;">
    <div style="margin: 0; padding: 0; font-family: 'Nanum Myeongjo', serif;">
        <p style="font-size: 16px; font-weight: 400; text-indent: 14px; text-align: justify; line-height: 1.8; margin-bottom: 12px; color: #111111; word-break: keep-all;">'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드(bar-code)와 같지만, 우리가 살아가며 마주하는 스캐너(scanner)인 '운'은 늘 변화하며 흐릅니다.</p>
        <p style="font-size: 16px; font-weight: 400; text-indent: 14px; text-align: justify; line-height: 1.8; margin-bottom: 12px; color: #111111; word-break: keep-all;">따라서 오늘의 '초연 시공명리학과의 인연'이 <b style="color: #1A237E;">{name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
        <p style="font-size: 16px; font-weight: 800; text-indent: 14px; text-align: justify; line-height: 1.8; margin-bottom: 0; color: #111111; word-break: keep-all;">오늘 닿은 귀한 인연에 다시 한 번 깊이 감사드립니다.</p>
        <div style="text-align: right; margin-top: 25px; margin-bottom: 35px;">
            <span style="font-weight: 900; font-size: 18px; color: #1A237E;">- 초연 시공명리 연구소 드림 -</span>
        </div>
    </div>
    
    <div style='padding: 26px; background: #F8F9FA; border: 1.5px solid #E8EAF6; border-radius: 12px; font-family: "Nanum Myeongjo", serif; margin-top: 30px;'>
        <div style='color: #1A237E; font-size: 19px; font-weight: 800; letter-spacing: -0.3px; margin-bottom: 14px;'>
            💌 [사주박사의 1:1 애프터 서비스]
        </div>
        <p style='font-size: 16px; font-weight: 400; color: #333333; line-height: 1.8; margin: 0; text-indent: 14px; text-align: justify; word-break: keep-all;'>
        {name}님, 이번 리포트에서는 사주 원국과 함께 남겨주신 고민의 핵심 원인과 타개 시기를 우선적으로 짚어드렸습니다.
        </p>
        <p style='font-size: 16px; font-weight: 400; color: #333333; line-height: 1.8; margin-top: 12px; margin-bottom: 0; text-indent: 14px; text-align: justify; word-break: keep-all;'>
        혹시 제 풀이를 읽고 더 깊은 이야기나 추가로 궁금한 점이 생기셨나요? 언제든 <b style="color: #1A237E; font-weight: 800;">[사주박사의 1:1 애프터 서비스]</b>를 통해 편하게 상담해 주세요. 기존 신청자분들께는 '사주박사'가 직접 저렴하고 친절하게 1:1 추가 상담을 도와드리고 있습니다. 늘 응원합니다! 🙏
        </p>
    </div>
    """

def get_couple_golden_text(m_name, male_golden_html, f_name, female_golden_html):
    clean_male = male_golden_html.replace('<hr style="border: 0; border-top: 2px dashed #1A237E; margin: 25px 0;">', '').replace('<hr style="border: 0; border-top: 2px solid #000000; margin: 20px 0;">', '').strip()
    clean_female = female_golden_html.replace('<hr style="border: 0; border-top: 2px dashed #1A237E; margin: 25px 0;">', '').replace('<hr style="border: 0; border-top: 2px solid #000000; margin: 20px 0;">', '').strip()
    return f"""
    <div style="margin-bottom: 25px; padding: 22px; background: #fafafa; border-radius: 12px; border: 1px solid #e0e0e0; font-family: 'Nanum Myeongjo', serif;">
        <div style="margin-bottom: 22px;">
            <div style="font-size: 18px; font-weight: 800; color: #1565C0; margin-bottom: 8px; letter-spacing: -0.3px;">
                ♂️ [신랑 {m_name}님 타고난 그릇과 시공간 본성]
            </div>
            <div style="font-size: 16px; font-weight: 400; line-height: 1.8; color: #111111; text-align: justify; word-break: keep-all;">
                {clean_male}
            </div>
        </div>
        <div>
            <div style="font-size: 18px; font-weight: 800; color: #1A237E; margin-bottom: 8px; letter-spacing: -0.3px;">
                ♀️ [신부 {f_name}님 타고난 그릇과 시공간 본성]
            </div>
            <div style="font-size: 16px; font-weight: 400; line-height: 1.8; color: #111111; text-align: justify; word-break: keep-all;">
                {clean_female}
            </div>
        </div>
    </div>
    <hr style="border: 0; border-top: 2px solid #3E2723; margin: 25px 0;">
    """

def get_external_raw_text_box(other_text):
    return f"""
    <div style='margin-top:25px; margin-bottom:25px; padding:24px; background-color:#F5F5F5; border:1.5px solid #757575; border-radius:12px; font-family: "Nanum Myeongjo", serif;'>
        <div style='font-size:18px; font-weight:800; color:#212121; border-bottom:1.5px solid #9E9E9E; padding-bottom:10px; margin-bottom:15px;'>
            📄 [제출된 외부 타 감명서 원본]
        </div>
        <div style='font-size:16px; color:#111111; line-height:1.8; white-space:pre-wrap; text-align: justify; word-break: keep-all;'>{other_text}</div>
    </div>
    """

# ==============================================================================
# 📦 섹션 4. 궁합 및 택일 부가 컴포넌트 
# ==============================================================================

def get_daewun_compare_box(m_name, m_daewun_html, f_name, f_daewun_html):
    clean_m_name = str(m_name or "남명").strip()
    clean_f_name = str(f_name or "여명").strip()
    return f"""
    <div style="margin-top: 15px; margin-bottom: 15px; width: 100%;">
        <div style="width: 100%; margin-bottom: 15px;">
            <div style="text-align: left; font-family: 'Nanum Myeongjo', serif; font-size: 17px; font-weight: 800; color: #1565C0; margin-bottom: 8px; padding-left: 5px;">
                ♂️ 남명 : {clean_m_name} 님
            </div>
            <div style="width: 100%; overflow-x: auto; margin-bottom: 0px;">
                {m_daewun_html}
            </div>
        </div>
        <div style="width: 100%; margin-bottom: 0px;">
            <!-- 🚨 여명 보라색 정화 적용 -->
            <div style="text-align: left; font-family: 'Nanum Myeongjo', serif; font-size: 17px; font-weight: 800; color: #1A237E; margin-bottom: 8px; padding-left: 5px;">
                ♀️ 여명 : {clean_f_name} 님
            </div>
            <div style="width: 100%; overflow-x: auto; margin-bottom: 0px;">
                {f_daewun_html}
            </div>
        </div>
    </div>
    """

def get_gunghap_score_visual_html(gh_engine):
    sky_blue = "#38B6FF"
    bars = "".join([
        f"<div style='display:flex; align-items:center; margin-bottom:12px; font-family:\"Nanum Myeongjo\", serif;'>"
        f"<div style='width:130px; font-size:14px; font-weight:800; color:#444;'>{d['label']}</div>"
        f"<div style='flex:1; height:12px; margin:0 10px;'><svg width='100%' height='12'><rect width='100%' height='12' rx='6' ry='6' fill='#eee' /><rect width='{d['pct']}%' height='12' rx='6' ry='6' fill='{d['color']}' /></svg></div>"
        f"<div style='width:35px; font-size:13px; font-weight:800;'>{d['pct']}%</div>"
        f"</div>" 
        for d in gh_engine.details
    ])
    return f"""
    <h2 style='font-family:\"Nanum Myeongjo\", serif; text-align:center; margin-top:35px; font-size:24px; font-weight:900;'>📊 최종 궁합 점수</h2>
    <div style='display:flex; justify-content:center; align-items:center; margin:20px 0;'>
        <div style='width:130px; height:130px; border-radius:50%; background:conic-gradient({sky_blue} {gh_engine.final_score}%, #eee 0); display:flex; justify-content:center; align-items:center; -webkit-print-color-adjust: exact;'>
            <div style='width:98px; height:98px; background:#fff; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
                <span style='font-family:\"Nanum Myeongjo\", serif; font-size:32px; font-weight:900; color:{sky_blue};'>{gh_engine.final_score}</span>
                <span style='font-size:10px; color:#888; font-weight:bold;'>SCORE</span>
            </div>
        </div>
    </div>
    <div style='text-align:center; margin-bottom:20px;'><span style='font-family:\"Nanum Myeongjo\", serif; font-size:16px; font-weight:800; color:#fff; background:{sky_blue}; padding:8px 32px; border-radius:30px; -webkit-print-color-adjust: exact;'>{gh_engine.grade}</span></div>
    <div style='max-width:500px; margin:0 auto; margin-bottom:20px;'>
        {bars}
    </div>
    """

def get_gunghap_closing(name1, name2):
    return f"""
    <div style='margin-top: 30px; border-top: 2px dashed #444; padding-top: 20px; font-family: "Nanum Myeongjo", serif;'>
        <p style='font-size: 16px !important; font-weight: 400 !important; text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 12px; color: #111111; word-break: keep-all;'>
        <b>{name1}님</b>과 <b>{name2}님</b>의 만남은 결코 우연이 아닌, <b>'수많은 인연의 이치 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 명식이지만, <b>'궁합(宮合)'</b>은 두 명식이 만나 그려내는 새로운 <b>'조화와 상생'</b>입니다.</p>
        <p style='font-size: 16px !important; font-weight: 400 !important; text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 12px; color: #111111; word-break: keep-all;'>서로의 기운을 보완하고 다독여주는 든든한 <b>'반려자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 초연 시공명리의 축복이 가득하시길 소망합니다.</p>
        <p style='font-size: 16px !important; font-weight: 800 !important; text-indent: 15px; line-height: 1.8; margin-bottom: 0px; color: #111111; word-break: keep-all;'>오늘 닿은 귀한 인연에 다시 한 번 깊이 감사드립니다.</p>
        <div style='text-align: right; margin-top: 25px;'>
            <span style='font-weight: 900; font-size: 18px !important; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
        </div>
    </div>
    """

def get_gunghap_three_page_report(m_saju_html, m_ess, f_ess, g_ess):
    pb_tag = "<div style='page-break-before: always; break-before: page;'></div>"
    clean_f_ess = str(f_ess).replace(pb_tag, "").strip() if f_ess else ""
    clean_g_ess = str(g_ess).replace(pb_tag, "").strip() if g_ess else ""
    m_page = f"""
    <div style='border: 2px solid #1565C0; border-radius: 12px; padding:25px; background:#FFFFFF; margin-bottom:25px;'>
        <h1 style='text-align:center; color:#1A237E; font-weight:800; border-bottom:3px solid #1A237E; padding-bottom:10px; margin-bottom:25px; font-size:26px; font-family:"Nanum Myeongjo", serif;'>[ ♂️ 남명 사주 요약 ]</h1>
        {m_saju_html}
        <div style='margin-top:20px;'>{m_ess}</div>
    </div>
    """
    f_page = ""
    if clean_f_ess:
        f_page = f"""
        <div class='page-break'></div>
        <div style='border: 2px solid #4A148C; border-radius: 12px; padding:25px; background:#FFFFFF; margin-bottom:25px;'>
            <!-- 🚨 대제목 위엄 통일: 남색, 26px, 800, 밑줄 3px -->
            <h1 style='text-align:center; color:#1A237E; font-weight:800; border-bottom:3px solid #1A237E; padding-bottom:10px; margin-bottom:25px; font-size:26px; font-family:"Nanum Myeongjo", serif;'>[ ♀️ 여명 사주 요약 ]</h1>
            <div style='margin-top:20px;'>{clean_f_ess}</div>
        </div>
        """
    g_page = ""
    if clean_g_ess:
        g_page = f"""
        <div class='page-break'></div>
        <div style='border: 2px solid #1B5E20; border-radius: 12px; padding:25px; background:#FFFFFF;'>
            <!-- 🚨 대제목 위엄 통일: 남색, 26px, 800, 밑줄 3px -->
            <h1 style='text-align:center; color:#1A237E; font-weight:800; border-bottom:3px solid #1A237E; padding-bottom:10px; margin-bottom:25px; font-size:26px; font-family:"Nanum Myeongjo", serif;'>[ 🍀 초연 시공명리 궁합 풀이 ]</h1>
            <div style='margin-top:20px;'>{clean_g_ess}</div>
        </div>
        """
    return get_final_report_box(m_page + f_page + g_page)

def get_delivery_summary_box(best_days):
    summary_items = ""
    for idx, day_info in enumerate(best_days):
        b_time_info = day_info['best_time']
        pillars_str = day_info.get('four_pillars', '')
        summary_items += f"""
        <li style="margin-bottom:8px;">
            🏅 <b>추천 {idx+1}순위</b> (명리 종합점수: <span style="color:#C62828; font-weight:bold;">{day_info['score']}점</span>) : 
            <b>{day_info['date']} {b_time_info['time_str']}</b> 
            <span style="color:#555; font-size:14px;">({pillars_str})</span>
        </li>
        """
    return f"""
    <div style="background-color:#F0F4F8; border:2px solid #1A237E; border-radius:10px; padding:20px; margin-top:20px; margin-bottom:25px; font-family: 'Nanum Myeongjo', serif;">
        <h4 style="color:#1A237E; margin-top:0; margin-bottom:12px; font-size:17px; font-weight:800; border-bottom:2px solid #C5CAE9; padding-bottom:8px;">
            📋 길일 한눈에 보기 (최적 길일 로드맵)
        </h4>
        <ul style="list-style-type:none; padding-left:0; margin:0; line-height:1.8; font-size:15px; color:#2C3E50;">
            {summary_items}
        </ul>
    </div>
    """

def get_childbirth_taegil_card(border_col, idx, b_date_str, score, b_time_str, b_time_pillar, gestation_warning, conception_title, conception_str, conception_msg, baby_saju_html, ai_output_html):
    return f"""
    <div style="background-color:#FFFFFF; border:2px solid #E0E0E0; border-radius:12px; padding:22px; margin-bottom:25px; box-shadow:0 2px 8px rgba(0,0,0,0.05); font-family: 'Nanum Myeongjo', serif;">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #F1F3F4; padding-bottom:12px; margin-bottom:15px;">
            <h3 style="color:#1A237E; margin:0; font-size:19px; font-weight:800;">🏅 추천 {idx+1}순위 길일 : {b_date_str}</h3>
            <span style="background-color:#E8EAF6; color:#1A237E; font-weight:800; padding:4px 12px; border-radius:20px; font-size:14px;">명리 종합점수: {score}점</span>
        </div>
        <ul style="list-style-type:none; padding-left:0; margin-top:10px; line-height:1.8; color:#111; font-size:15px;">
            <li><b>⏰ 가장 좋은 시간</b>: <span style="color:#00695C; font-weight:800;">{b_time_str} ({b_time_pillar})</span></li>
            {gestation_warning}
            <li><b>{conception_title}</b>: <span style="font-weight:800; color:#0277BD;">{conception_str}</span> <br>{conception_msg}</li>
        </ul>
        <div style="margin-top:15px;">{baby_saju_html}</div>
        <div style="margin-top:15px; padding-top:15px; border-top:1px dashed #DDD;">
            {ai_output_html}
        </div>
    </div>
    """

# ==============================================================================
# 📦 섹션 5. 종합 렌더링 컨테이너 모듈 
# ==============================================================================

def get_couple_fact_split_layout(male_block, female_block):
    return f"""
    <div style="margin-bottom: 30px; font-family: 'Nanum Myeongjo', serif;">
        <div style="font-size: 22px; font-weight: 800; color: #1A237E; text-align: center; padding: 6px 0 10px 0; margin-bottom: 15px; border-bottom: 2.5px solid #1A237E; letter-spacing: -0.5px;">
            ♂️ [남명 사주 원국 및 대운 분석]
        </div>
        {male_block}
    </div>
    <div class='page-break'></div>
    <div style="margin-bottom: 30px; font-family: 'Nanum Myeongjo', serif;">
        <!-- 🚨 여명 위엄 통일: 남색 -->
        <div style="font-size: 22px; font-weight: 800; color: #1A237E; text-align: center; padding: 6px 0 10px 0; margin-bottom: 15px; border-bottom: 2.5px solid #1A237E; letter-spacing: -0.5px;">
            ♀️ [여명 사주 원국 및 대운 분석]
        </div>
        {female_block}
    </div>
    <div class='page-break'></div>
    """

def render_saju_comparison_report(saju_fact_html, external_raw_box, ai_content_html):
    master_body = f"""
    <h1 style="font-family: 'Nanum Myeongjo', serif !important; font-size: 26px !important; font-weight: 800 !important; color: #1A237E !important; text-align: center !important; padding-bottom: 10px !important; margin-bottom: 25px !important; border-bottom: 3px solid #1A237E !important; letter-spacing: -0.5px !important; display: block !important; margin-top: 0 !important;">🔍 타 감명서 비교 (사주) 1:1 정밀 분석</h1>
    {saju_fact_html}
    {external_raw_box}
    <div style="margin-top: 25px;">
        {ai_content_html}
    </div>
    """
    return get_final_report_box(master_body)

def render_gunghap_comparison_report(couple_fact_html, external_raw_box, ai_content_html):
    master_body = f"""
    <h1 style="font-family: 'Nanum Myeongjo', serif !important; font-size: 26px !important; font-weight: 800 !important; color: #1A237E !important; text-align: center !important; padding-bottom: 10px !important; margin-bottom: 25px !important; border-bottom: 3px solid #1A237E !important; letter-spacing: -0.5px !important; display: block !important; margin-top: 0 !important;">🔍 타 감명서 비교 (궁합) 1:1 정밀 분석</h1>
    {couple_fact_html}
    {external_raw_box}
    <div style="margin-top: 25px;">
        {ai_content_html}
    </div>
    """
    return get_final_report_box(master_body)

def render_comparison_report(part_1_fact, external_raw_box, ai_comparison_html):
    master_body = f"{part_1_fact}{external_raw_box}{ai_comparison_html}"
    return get_final_report_box(master_body)

def get_warning_box(title, message):
    return f"""
    <div style='padding:20px; background-color:#FFF3E0; border:2px solid #FB8C00; border-radius:10px; margin-top:20px; font-family: "Nanum Myeongjo", serif;'>
        <h3 style='color:#E65100; margin:0 0 8px 0; font-size:17px; font-weight:900;'>⚠️ [{title}]</h3>
        <p style='color:#E65100; font-size:15px; margin:0; line-height:1.6;'>{message}</p>
    </div>
    """

def get_final_report_box(content_html):
    """A4 백지 캔버스 안쪽 둥근 VIP 프레임 단일 래핑"""
    return f"""
    <div class='report-page'>
        <div class='vip-inset-frame'>
            {content_html}
        </div>
    </div>
    """
