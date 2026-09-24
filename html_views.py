# ==============================================================================
# html_views.py (ver 87.1 - engine.py와 동일한 기준으로 구조 재정리판)
# 재정리 기준: 공용 CSS/포맷터 -> 공통 사주표 컴포넌트 -> 서술형 안내문구 ->
#              궁합/택일 부가 컴포넌트 -> 초연 시공명리 "타 감명서 비교" 전용 렌더링(맨 마지막)
# 함수 로직은 전혀 수정하지 않았고, 배치 순서와 섹션 주석만 재정리했습니다.
# ==============================================================================
import re
import streamlit as st
 
# ==============================================================================
# PART 0. 전역 CSS 및 AI 텍스트 포맷터 (변경 없음)
# ==============================================================================
 
def get_global_css():
    """전체 시스템 UI/UX 및 화면/인쇄 듀얼 분리 스타일시트 (나눔명조/스타일 충돌 해결)"""
    return """<link rel="preload" href="https://cdn.jsdelivr.net/gh/lxgw/LxgwSeal@0.001-alpha.7.24/TTF/LXGWSeal-Regular.ttf" as="font" type="font/ttf" crossorigin="anonymous"><style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&display=swap');
    @font-face {
        font-family: 'LXGW Seal';
        src: url('https://cdn.jsdelivr.net/gh/lxgw/LxgwSeal@0.001-alpha.7.24/TTF/LXGWSeal-Regular.ttf') format('truetype');
        font-weight: 400;
        font-display: block;
    }
    .stApp { background-color: #E8F5E9 !important; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span[data-testid="stMarkdownContainer"] { font-family: 'Nanum Gothic', sans-serif !important; }
    div[data-testid="stSidebar"] * { font-size: 14px !important; }
    /* 🚨 라디오 버튼 텍스트가 잘리지 않고 두 줄(\\n)로 나오도록 속성 부여 */
    div[data-testid="stRadio"] label p { font-size: 14px !important; white-space: pre-wrap !important; line-height: 1.6 !important; padding-bottom: 4px !important; }
    div[data-testid="stCheckbox"] label p { font-size: 15px !important; font-weight: 900 !important; color: #000000 !important; }
    /* 🛡️ 1. 본문 영역: 명조체(Noto Serif KR) 강제 */
    .report-page:not(.cover-page), .report-page:not(.cover-page) *, .choyeon-premium-report, .result-table td { font-family: 'Noto Serif KR', serif !important; }
    /* 🛡️ 2. 표지 영역: 나눔명조(Nanum Myeongjo) 최우선 보장 (일반 문장체 풀림 차단) */
    .cover-page, .cover-page *, div.cover-page, div.cover-page * { font-family: 'Nanum Myeongjo', serif !important; box-sizing: border-box !important; }
    /* 🛡️ 표지 내부 텍스트 여백 및 들여쓰기 초기화 */
    .cover-page p, .cover-page div, .cover-page span, .cover-page h1, .cover-page h2 { text-indent: 0 !important; }
    /* 🛡️ 표지 박스 기본 속성 (A4 인쇄 정밀 대응) */
    .cover-page { display: flex !important; flex-direction: column; justify-content: center; align-items: center; padding: 0 !important; background: #ffffff; margin: 0 auto; box-sizing: border-box; width: 210mm; height: 297mm; min-height: 297mm; page-break-after: always; -webkit-print-color-adjust: exact; }
    /* 🌟 본문 대제목(h1, h3, ai-title-l1) 진한 남색 밑줄 쫙 일괄 적용 (구 중복 규칙 통합) */
    .report-page:not(.cover-page) h1, .report-page h3, .ai-title-l1 { font-size: 26px !important; font-weight: 900 !important; color: #1A237E !important; text-align: left !important; border-bottom: 3px solid #1A237E !important; padding-bottom: 10px !important; margin-bottom: 25px !important; margin-top: 45px !important; letter-spacing: -0.5px !important; line-height: 1.4 !important; display: block !important; width: 100% !important; font-family: 'Noto Serif KR', serif !important; }
    .b-text { font-weight: 900 !important; color: #000000 !important; display: inline-block; }
    .b-text-red { font-weight: 900 !important; color: #D50000 !important; display: inline-block; }
    div.stButton > button { font-family: 'Nanum Gothic', sans-serif !important; font-weight: 900 !important; font-size: 16px !important; border-radius: 8px !important; width: 100% !important; }
    div.stButton > button[kind="primary"], div.stButton > button[data-testid="baseButton-primary"] { background-color: #D50000 !important; color: #FFFFFF !important; border: none !important; height: 50px !important; font-weight: 900 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; }
    div.stButton > button[kind="primary"]:hover, div.stButton > button[data-testid="baseButton-primary"]:hover { background-color: #B71C1C !important; color: #FFFFFF !important; }
    div.stButton > button[kind="secondary"], div.stButton > button[data-testid="baseButton-secondary"] { background-color: #00A843 !important; color: #FFFFFF !important; border: none !important; height: 50px !important; font-weight: 900 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.08) !important; }
    div.stButton > button[kind="secondary"]:hover, div.stButton > button[data-testid="baseButton-secondary"]:hover { background-color: #008937 !important; color: #FFFFFF !important; }
    /* 통변 제목 및 본문 스타일 */
    .sub-title, .ai-title-l2 { font-size: 18px !important; font-weight: 900 !important; color: #111111 !important; margin-top: 22px !important; margin-bottom: 10px !important; line-height: 1.4 !important; font-family: 'Noto Serif KR', serif !important; display: block !important; }
    .vip-inset-frame { border: 2px solid #3E2723 !important; border-radius: 12px !important; padding: 30px 25px !important; background-color: #FFFFFF !important; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .content-box-loose { margin-bottom: 25px !important; }
    /* 🛡️ 본문 p태그와 표지 p태그 충돌 방지 */
    .ai-body-p, .report-page:not(.cover-page) p { font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-justify: inter-character !important; text-indent: 1.0em !important; margin-bottom: 12px !important; word-break: break-all !important; }
    .color-목 { background: #2E7D32 !important; color: #FFF !important; }
    .color-화 { background: #C62828 !important; color: #FFF !important; }
    .color-토 { background: #F9A825 !important; color: #000 !important; }
    .color-금 { background: #9E9E9E !important; color: #FFF !important; }
    .color-수 { background: #212121 !important; color: #FFF !important; }
    .result-table { width: 100%; border-collapse: collapse !important; border: 3px solid #3E2723 !important; margin-bottom: 15px; table-layout: fixed; }
    .result-table td { border: 1px solid #444 !important; padding: 1px 0 !important; text-align: center; vertical-align: middle; font-weight: 900 !important; font-size: 13px; line-height: 1.2 !important; }
    /* 🌟 대운/세운/월운/일운표의 십성·운성·신살 글자를 원국표와 동일한 굵기로 통일 */
    .un-sub-text { font-weight: 900 !important; font-size: 13px !important; }
    .ganji-cell-24 { font-size: 24px !important; font-weight: 900 !important; }
    .top-header-cell { background-color: #1A237E !important; height: 30px !important; }
    .top-header-cell td { background-color: #1A237E !important; color: #FFFFFF !important; font-weight: 900 !important; font-size: 16px !important; border: 1px solid #444 !important; }
    .header-cell-main, .header-cell-sub { background-color: #E8EAF6 !important; color: #000000 !important; font-weight: 900 !important; font-size: 14px !important; }
    /* 🌟 AI 통변 페이지 최상단 대제목(main-report-title) 전용 이중선 구분 */
    .main-report-title { text-align: center !important; width: 100% !important; box-sizing: border-box !important; border-bottom: 4px double #1A237E !important; padding-bottom: 20px !important; margin: 10px 0 30px 0 !important; }
    /* 📄 감명서 페이지 기본 프레임 (A4 규격) */
    .report-page { width: 210mm; max-width: 100%; margin: 20px auto; background-color: #FFF !important; padding: 12mm 10mm; box-sizing: border-box; color: #000; }
    /* 🖨️ 인쇄 / PDF 저장 전용 규칙 */
    @media print {
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }
        @page { size: A4 portrait; margin: 15mm 12mm; }
        .stSidebar, button, iframe, .print-hide, header, [data-testid="stHeader"] { display: none !important; }
        body, .stApp { background-color: white !important; }
        .block-container, div[data-testid="stAppViewBlockContainer"] { padding-top: 0 !important; padding-bottom: 0 !important; margin-top: 0 !important; margin-bottom: 0 !important; }
        div[data-testid="stVerticalBlock"] { gap: 0 !important; }
        .element-container, .stMarkdown { margin-bottom: 0 !important; }
        .report-page { box-shadow: none; margin: 0 auto; padding: 0; page-break-after: always; border-radius: 0; width: 100%; max-width: 100%; }
        .page-break-before { page-break-before: always; }
        .vip-inset-frame { border: 2px solid #000 !important; border-radius: 20px !important; padding: 25px !important; box-decoration-break: clone !important; -webkit-box-decoration-break: clone !important; }
    </style>
    """
 
def format_ai_text_to_html(text, qna_text=""):
    """
    프롬프트 규칙 4번 대응 포맷터:
    대제목(1.), 중제목(1)), 소제목((1)), 소소제목(①②③), 강조기호(◆▶▷), 일반 본문을 완벽 구분하여 굵은체 및 규격 렌더링
    (마크다운 헤더 #, ##, ### 및 --- 구분선은 전부 제거하고 절대 특수 서식으로 승격하지 않음)
    ("라벨: 설명" 콜론 패턴을 소제목으로 자동 승격하던 기능 완전 제거 — 규칙 위반이 그대로 드러나도록 함)
    (색상은 전부 검정 통일, 위계는 font-weight 숫자 강약으로만 구분)
    """
    if not text:
        return ""
    text = re.sub(r'```(?:html)?\s*', '', text)
    lines = [line.strip() for line in text.split("\n")]
    html_lines = []
    preserved_markers = [
        '[DAEWUN_TABLE_HERE]', '[SEWUN_TABLE_HERE]', '[WOLUN_TABLE_HERE]',
        '[WEEKLY_CALENDAR_HERE]', '[COUPLE_DAEWUN_TABLES_HERE]',
        '[GOLDEN_TEXT_HERE]', '[CHOYEON_SIGN_HERE]'
    ]

    def _split_title_body(s):
        m = re.match(r'^(.*?[:：])\s*(\S.*)$', s)
        if m and re.search(r'\d$', re.sub(r'[:：]$', '', m.group(1))):
            return None
        return m

    for line in lines:
        if not line:
            continue
        if re.fullmatch(r'[-*_＊·•]{2,}', line):
            continue
        if any(marker in line for marker in preserved_markers):
            html_lines.append(f"\n{line}\n")
            continue
        line_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
        line_formatted = re.sub(r'^#{1,6}\s*', '', line_formatted)

        if re.match(r'^\d+\.\s+', line_formatted):
            html_lines.append(f"<div class='ai-title-l1' style='font-size: 21.5px !important; font-weight: 900 !important; color: #000000 !important; text-align: left !important; margin-top: 40px !important; margin-bottom: 22px !important; border-bottom: 3px solid #000000 !important; padding-bottom: 10px !important; letter-spacing: -0.5px !important; line-height: 1.4 !important; display: block !important; width: 100% !important; font-family: \"Noto Serif KR\", serif !important;'><b>{line_formatted}</b></div>")

        elif re.match(r'^\d+\)\s*', line_formatted):
            html_lines.append(f"<div class='sub-title' style='font-size: 19.5px !important; font-weight: 800 !important; color: #000000 !important; margin-top: 24px !important; margin-bottom: 11px !important; line-height: 1.4 !important; font-family: \"Noto Serif KR\", serif !important; display: block !important;'><b>{line_formatted}</b></div>")

        elif re.match(r'^\(\d+\)\s*', line_formatted) or re.match(r'^\[\d+\]\s*', line_formatted):
            split = _split_title_body(line_formatted)
            if split:
                title, body = split.group(1), split.group(2)
                html_lines.append(f"<div style='font-size: 18.5px !important; font-weight: 700 !important; color: #000000 !important; margin-top: 17px !important; margin-bottom: 15px !important; font-family: \"Noto Serif KR\", serif !important; display: block !important;'><b>{title}</b></div>")
                html_lines.append(f"<p class='ai-body-p' style='font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-indent: 1.0em !important; margin-bottom: 12px !important; margin-top: 0 !important; font-family: \"Noto Serif KR\", serif !important;'>{body}</p>")
            else:
                html_lines.append(f"<div style='font-size: 18.5px !important; font-weight: 700 !important; color: #000000 !important; margin-top: 17px !important; margin-bottom: 15px !important; font-family: \"Noto Serif KR\", serif !important; display: block !important;'><b>{line_formatted}</b></div>")

        elif re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]\s*', line_formatted):
            split = _split_title_body(line_formatted)
            if split:
                title, body = split.group(1), split.group(2)
                html_lines.append(f"<div style='font-size: 17.5px !important; font-weight: 600 !important; color: #000000 !important; margin-top: 15px !important; margin-bottom: 9px !important; line-height: 1.4 !important; font-family: \"Noto Serif KR\", serif !important; display: block !important;'><b>{title}</b></div>")
                html_lines.append(f"<p class='ai-body-p' style='font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-indent: 1.0em !important; margin-bottom: 12px !important; margin-top: 0 !important; font-family: \"Noto Serif KR\", serif !important;'>{body}</p>")
            else:
                html_lines.append(f"<div style='font-size: 17.5px !important; font-weight: 600 !important; color: #000000 !important; margin-top: 15px !important; margin-bottom: 9px !important; line-height: 1.4 !important; font-family: \"Noto Serif KR\", serif !important; display: block !important;'><b>{line_formatted}</b></div>")

        elif re.match(r'^[◆▶▷■◈●•]\s*', line_formatted):
            split = _split_title_body(line_formatted)
            if split:
                title, body = split.group(1), split.group(2)
                html_lines.append(f"<div style='font-size: 16.5px !important; font-weight: 500 !important; color: #000000 !important; margin-top: 13px !important; margin-bottom: 7px !important; font-family: \"Noto Serif KR\", serif !important; display: block !important;'><b>{title}</b></div>")
                html_lines.append(f"<p class='ai-body-p' style='font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-indent: 1.0em !important; margin-bottom: 12px !important; margin-top: 0 !important; font-family: \"Noto Serif KR\", serif !important;'>{body}</p>")
            else:
                html_lines.append(f"<div style='font-size: 16.5px !important; font-weight: 500 !important; color: #000000 !important; margin-top: 13px !important; margin-bottom: 7px !important; font-family: \"Noto Serif KR\", serif !important; display: block !important;'><b>{line_formatted}</b></div>")

        else:
            html_lines.append(f"<p class='ai-body-p' style='font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-indent: 1.0em !important; margin-bottom: 12px !important; margin-top: 0 !important; font-family: \"Noto Serif KR\", serif !important;'>{line_formatted}</p>")

    parsed_content = "\n".join(html_lines)
    qna_html = ""
    if qna_text:
        clean_qna = qna_text.replace('💡', '').strip()
        clean_qna = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean_qna).replace('\n\n', '<br><br>').replace('\n', '<br>')
        qna_html = f"<div style='margin-top:25px; padding:15px 20px; background:#F8F9FA; border-left:4px solid #1A237E; border-radius:4px; font-weight:bold;'>💡 고민 상담 Q&A<br>{clean_qna}</div>"
    return f"<div class='choyeon-premium-report' style='font-family: \"Noto Serif KR\", serif; font-size: 16px; line-height: 1.85; color: #222222;'>{parsed_content}{qna_html}</div>"
 
# ==============================================================================
# PART 1. 공통 사주표 / 대운·세운·월운·주간표 컴포넌트 (전통/시공 공용)
# ==============================================================================
 
def td_func(val, engine):
    oh = engine.get_color(val)
    return f"<td class='color-{oh}' style='font-size: 18px; font-weight: 900; border:1px solid #444 !important;'><span style='color:inherit !important;'>{('?' if val in ['?',' ','-'] else val)}</span></td>"
 
def get_personal_cover(version, report_title, u_icon, u_name, u_sol, u_lun, u_time, today_str):
    """1인용 감명서 표준 표지 (전체 나눔명조 강제 통일 + 타이틀 1줄 강제 방어막)"""
    raw_title = str(report_title or "초연 전통 명리 사주풀이").replace("🏮", "").replace("🎯", "")
    for tag in ["<br>", "<br/>", "<br />", "\n", "\r"]:
        raw_title = raw_title.replace(tag, " ")
    clean_title = " ".join(raw_title.split())
    clean_u_name = str(u_name or "무명").strip()
 
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:210mm; height:297mm; min-height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; box-sizing: border-box; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 42px 24px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 92%; max-width: 680px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
 
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 28px; width: 100%; box-sizing: border-box;'>
                <h1 style='font-family: "Nanum Myeongjo", serif !important; font-size: 28px !important; font-weight: 900 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -1.2px !important; white-space: nowrap !important; word-break: keep-all !important; line-height: 1.2 !important; text-align: center;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family: "Nanum Myeongjo", serif; font-size: 14px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
 
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 22px 20px; border-radius: 14px; margin-bottom: 24px;'>
                <h2 style='font-family: "Nanum Myeongjo", serif; font-size: 24px; font-weight: 900; color: #1A237E; margin: 0 0 10px 0;'>{u_icon} {clean_u_name} 님</h2>
                <div style='font-family: "Nanum Myeongjo", serif; font-size: 16px; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap; color: #000000;'><strong style='font-weight: 900 !important;'>[양력] {u_sol} | [음력] {u_lun}</strong></p>
                    <p style='margin: 4px 0 0 0; white-space: nowrap; font-weight: 800; color: #1A237E;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
 
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 18px; margin-top: 35px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 24px; font-weight: 900; color: #1A237E; margin-top: 20px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class='page-break'></div>
    """
 
def get_couple_cover(version="", report_title="", u_icon="♂️", u_name="무명", u_age="", u_sol="", u_lun="", u_time="", p_icon="♀️", p_name="무명", p_age="", p_sol="", p_lun="", p_time="", today_str="", *args, **kwargs):
    raw_title = str(report_title or "초연 시공명리 궁합풀이").replace("🏮", "").replace("🎯", "")
    for tag in ["<br>", "<br/>", "<br />", "\n", "\r"]:
        raw_title = raw_title.replace(tag, " ")
    clean_title = " ".join(raw_title.split())
    clean_u_name = str(u_name or "무명").strip()
    clean_p_name = str(p_name or "무명").strip()
    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:210mm; height:297mm; min-height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; box-sizing: border-box; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 42px 24px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 92%; max-width: 680px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 28px; width: 100%; box-sizing: border-box;'>
                <h1 style='font-family: "Nanum Myeongjo", serif !important; font-size: 28px !important; font-weight: 800 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -1.2px !important; white-space: nowrap !important; word-break: keep-all !important; line-height: 1.2 !important; text-align: center;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family: "Nanum Myeongjo", serif; font-size: 14px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 16px 18px; border-radius: 14px; margin-bottom: 14px;'>
                <h2 style='font-family: "Nanum Myeongjo", serif; font-size: 24px; font-weight: 800; color: #1565C0; margin: 0 0 6px 0;'>{u_icon} 남명 : {clean_u_name} 님 ({u_age}세)</h2>
                <div style='font-family: "Nanum Myeongjo", serif; font-size: 16px; line-height: 1.6;'>
                    <p style='margin: 0; text-align: center; white-space: nowrap; color: #000000;'><strong style='font-weight: 800;'>[양력] {u_sol} | [음력] {u_lun}</strong></p>
                    <p style='margin: 3px 0 0 0; text-align: center; white-space: nowrap; font-weight: 800; color: #1565C0;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
            <div style='background: #FFF3E0; border: 1px solid #FBE9E7; padding: 16px 18px; border-radius: 14px; margin-bottom: 22px;'>
                <h2 style='font-family: "Nanum Myeongjo", serif; font-size: 24px; font-weight: 800; color: #C62828; margin: 0 0 6px 0;'>{p_icon} 여명 : <span style='color:#000000 !important;'>{clean_p_name}</span> 님 ({p_age}세)</h2>
                <div style='font-family: "Nanum Myeongjo", serif; font-size: 16px; line-height: 1.6;'>
                    <p style='margin: 0; text-align: center; white-space: nowrap; color: #000000;'><strong style='font-weight: 800;'>[양력] {p_sol} | [음력] {p_lun}</strong></p>
                    <p style='margin: 3px 0 0 0; text-align: center; white-space: nowrap; font-weight: 800; color: #C62828;'>태어난 시간 : {p_time}</p>
                </div>
            </div>
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 18px; margin-top: 32px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 24px; font-weight: 900; color: #1A237E; margin-top: 24px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
        </div>
    </div>
    <div class='page-break'></div>
    """
 
def get_main_title_html(report_title=""):
    """AI 통변 페이지 최상단 대제목 - 표지와 동일한 이중선 구분선(전역 클래스 + 인라인 이중 적용)으로 위엄을 강조"""
    clean_title = str(report_title or "").strip()
    return f"""
    <div class='main-report-title' style='text-align: center; margin: 10px 0 30px 0; padding: 0 0 20px 0; width: 100%; box-sizing: border-box; border-bottom: 4px double #1A237E;'>
        <h2 style='font-family: "Nanum Myeongjo", serif !important; font-size: 28px !important; font-weight: 900 !important; color: #1A237E !important; letter-spacing: -0.5px !important; margin: 0 !important; padding: 0 !important; display: block !important;'>{clean_title}</h2>
    </div>
    """
 
def get_info_header(p_icon, name, gender, marital, age, sol_str, lun_str, time_str, p_color="#1A237E"):
    return f"""
    <div style='text-align:center; font-family:"Nanum Gothic", sans-serif; margin-bottom:15px; line-height:1.5;'>
        <span style='font-size:18px; font-weight:900; color:{p_color}; white-space:nowrap;'>{p_icon} {name}님 ({gender}, {marital}, {age}세)</span><br>
        <span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span>
    </div>
    """
 
def generate_saju_table_data(gans, jjis, ds, gender, engine):
    """50.7 완벽 동일 사주원국 테이블 렌더링"""
    gan_rel = "".join([f"<td style='border:1px solid #444;'><span style='color:inherit !important;'>{engine.get_gan_rel_all(i, gans)}</span></td>" for i in range(4)])
    hs, ds_val, ms, ys = gans[0], gans[1], gans[2], gans[3]
    hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]
 
    gan_ss = f"<td style='border:1px solid #444;'><span style='color:inherit !important;'>{engine.get_ss(ds, hs)}</span></td>" \
             f"<td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td>" \
             f"<td style='border:1px solid #444;'><span style='color:inherit !important;'>{engine.get_ss(ds, ms)}</span></td>" \
             f"<td style='border:1px solid #444;'><span style='color:inherit !important;'>{engine.get_ss(ds, ys)}</span></td>"
 
    gan_row_html = "".join([td_func(g, engine) for g in gans])
    ji_row_html = "".join([td_func(j, engine) for j in jjis])
 
    ji_ss_html = f"<td style='border:1px solid #444;'><span style='color:inherit !important;'>{engine.get_ss(ds, hb)}</span></td>" \
                 f"<td style='border:1px solid #444;'><span style='color:inherit !important;'>{engine.get_ss(ds, db)}</span></td>" \
                 f"<td style='border:1px solid #444;'><span style='color:inherit !important;'>{engine.get_ss(ds, mb)}</span></td>" \
                 f"<td style='border:1px solid #444;'><span style='color:inherit !important;'>{engine.get_ss(ds, yb)}</span></td>"
 
    jijanggan_html = "".join([f"<td style='padding:0; border:1px solid #444;'><span style='color:inherit !important;'>{engine.get_jijanggan_full(ds, jjis[i])}</span></td>" for i in range(4)])
 
    ji_rel_rows = ""
    for l_idx, r_idx in enumerate([1, 2, 0, 3]):
        b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
        b_top = "0px solid transparent !important"
        cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if engine.get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'><span style='color:inherit !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else engine.get_ji_rel_set(jjis[r_idx], jjis[ci]))}</span></td>" for ci in range(4)])
        lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'><span style='color:inherit !important;'>합충형파해</span></td>" if l_idx==0 else ""
        ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"
 
    unsung = "".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'><span style='color:inherit !important;'>{engine.get_unsung(ds, jjis[i])}</span></td>" for i in range(4)])
    y_shinsal_tds = "".join([f"<td style='color:#C62828; border:1px solid #444 !important;'><span style='color:inherit !important;'>{engine.get_12_shinsal(yb, jjis[i])}</span></td>" for i in range(4)])
    d_shinsal_tds = "".join([f"<td style='color:#1565C0; border:1px solid #444 !important;'><span style='color:inherit !important;'>{engine.get_12_shinsal(db, jjis[i])}</span></td>" for i in range(4)])
    gen_shinsal = "".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'><span style='color:inherit !important;'>{'<br>'.join(engine.get_general_shinsal_filtered(i, gans, jjis, gender)) if engine.get_general_shinsal_filtered(i, gans, jjis, gender) else '-'}</span></td>" for i in range(4)])
 
    table_html = f"""
    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
        <tr class='top-header-cell'>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'><span style='color:#FFFFFF !important;'>구분</span></td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'><span style='color:#FFFFFF !important;'>시주</span></td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'><span style='color:#FFFFFF !important;'>일주</span></td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'><span style='color:#FFFFFF !important;'>월주</span></td>
            <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'><span style='color:#FFFFFF !important;'>년주</span></td>
        </tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>천간합충</span></td>{gan_rel}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>천간십성</span></td>{gan_ss}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>천간</span></td>{gan_row_html}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>지지</span></td>{ji_row_html}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>지지십성</span></td>{ji_ss_html}</tr>
        <tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>지장간</span></td>{jijanggan_html}</tr>
        {ji_rel_rows}
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>십이운성</span></td>{unsung}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>년지 12신살</span></td>{y_shinsal_tds}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>일지 12신살</span></td>{d_shinsal_tds}</tr>
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>일반신살</span></td>{gen_shinsal}</tr>
    </table>
    """
    return table_html
 
def get_master_bar(calc_d, m, f, e, mtl, w, guiin, n_gong, i_gong, samjae_color, cur_samjae):
    return f"""
    <div style='border:2px solid #3E2723; margin-top:20px; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap;'>
        <div>🔢 대운수: {calc_d}</div>
        <div>💥 오행: 木({m}) 火({f}) 土({e}) 金({mtl}) 水({w})</div>
        <div>🌟 천을귀인: {guiin}</div>
        <div>🎯 공망: [년] {n_gong} [일] {i_gong}</div>
        <div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div>
    </div>
    """
 
def get_un_layout(title, content):
    return f"""
    <div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>
        {content}
    </div>
    """
 
def get_un_cell(title_str, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, y_shinsal, d_shinsal, bg_col, b_left, is_current=False):
    u_val = unsung if unsung and str(unsung).strip() else "-"
    y_val = y_shinsal if y_shinsal and str(y_shinsal).strip() and str(y_shinsal).strip() != "None" else "-"
    d_val = d_shinsal if d_shinsal and str(d_shinsal).strip() and str(d_shinsal).strip() != "None" else "-"
    bg_col = "#FFF9C4" if is_current else "transparent"
 
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; white-space:nowrap; border-bottom:1px solid #ccc;'>{title_str}</div>
        <div class='un-sub-text' style='padding:2px; font-size:12px;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:16px; font-weight:900;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:16px; font-weight:900;'>{ji}</div>
        <div class='un-sub-text' style='padding:2px; font-size:12px;'>{ss_ji}</div>
        <div class='un-sub-text' style='font-size:11px; border-top:1px solid #ccc;'>{u_val}</div>
        <div class='un-sub-text' style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{y_val}</div>
        <div class='un-sub-text' style='font-size:11px; color:#1565C0; border-top:1px solid #ccc;'>{d_val}</div>
    </div>
    """
 
def generate_daewun_layout(daewun_list, direction_str, calc_d, get_oh_class_func):
    """대운표 생성: 좌측 세로선 복원 및 '세' 중복 제거"""
    un_content = ""
    for data in daewun_list:
        b_left = "1px solid #ccc"
        age_str = str(data['age_range']).strip()
        display_age = age_str if age_str.endswith("세") else f"{age_str}세"
 
        un_content += get_un_cell(
            display_age, data["ss_gan"], data["c_hanja"], get_oh_class_func(data["c_hangul"]),
            data["j_hanja"], get_oh_class_func(data["j_hangul"]), data["ss_ji"],
            data["un_sung"], data.get("y_shinsal", "-"), data.get("d_shinsal", "-"), "-", b_left, data.get("is_current", False)
        )
    return get_un_layout(f"[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]", un_content)
 
def get_sewun_layout(title, content):
    return f"""
    <div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>
        {content}
    </div>
    """
 
def get_sewun_cell(title_str, tage, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, y_shinsal, d_shinsal, bg_col, b_left, is_current=False):
    """세운표 셀: 좌측 세로선 유지 및 나이 '세' 중복 제거"""
    u_val = unsung if unsung and str(unsung).strip() else "-"
    y_val = y_shinsal if y_shinsal and str(y_shinsal).strip() else "-"
    d_val = d_shinsal if d_shinsal and str(d_shinsal).strip() and str(d_shinsal).strip() != "None" else "-"
    bg_col = "#E1F5FE" if is_current else "transparent"
 
    age_str = str(tage).strip()
    display_tage = age_str if age_str.endswith("세") else f"{age_str}세"
 
    return f"""
    <div style='flex:1; border-left:1px solid #ccc; text-align:center; padding-bottom:3px; background-color:{bg_col};'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; line-height:1.2; border-bottom:1px solid #ccc;'>{title_str}<br>({display_tage})</div>
        <div class='un-sub-text' style='padding:2px; font-size:12px;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:16px; font-weight:900;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:16px; font-weight:900;'>{ji}</div>
        <div class='un-sub-text' style='padding:2px; font-size:12px;'>{ss_ji}</div>
        <div class='un-sub-text' style='font-size:11px; border-top:1px solid #ccc;'>{u_val}</div>
        <div class='un-sub-text' style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{y_val}</div>
        <div class='un-sub-text' style='font-size:11px; color:#1565C0; border-top:1px solid #ccc;'>{d_val}</div>
    </div>
    """
 
def get_wolun_layout(title, content):
    return f"""
    <div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>{title}</div>
    <div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>
        {content}
    </div>
    """
 
def get_wolun_cell(tm, ss_gan, gan, gan_cls, ji, ji_cls, ss_ji, unsung, y_shinsal, d_shinsal, bg_col, b_left, is_current=False):
    u_val = unsung if unsung and str(unsung).strip() else "-"
    y_val = y_shinsal if y_shinsal and str(y_shinsal).strip() else "-"
    d_val = d_shinsal if d_shinsal and str(d_shinsal).strip() and str(d_shinsal).strip() != "None" else "-"
    bg_col = "#E8F5E9" if is_current else "transparent"
 
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{tm}월</div>
        <div class='un-sub-text' style='padding:2px; font-size:12px;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:16px; font-weight:900;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:16px; font-weight:900;'>{ji}</div>
        <div class='un-sub-text' style='padding:2px; font-size:12px;'>{ss_ji}</div>
        <div class='un-sub-text' style='font-size:11px; border-top:1px solid #ccc;'>{u_val}</div>
        <div class='un-sub-text' style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{y_val}</div>
        <div class='un-sub-text' style='font-size:11px; color:#1565C0; border-top:1px solid #ccc;'>{d_val}</div>
    </div>
    """
 
def generate_weekly_calendar_html(weekly_days_data, today_day, yb=None, db=None, engine=None):
    if not weekly_days_data:
        return ""
    cells = ""
    header_color_map = {'일': '#C62828', '토': '#1565C0'}
    for day in weekly_days_data:
        bg_col = "#FFF9C4" if day.get("is_today") else "transparent"
        gan_cls = engine.get_oh_class(day['gan']) if engine and hasattr(engine, 'get_oh_class') else ""
        ji_cls = engine.get_oh_class(day['ji']) if engine and hasattr(engine, 'get_oh_class') else ""
        y_val = day.get('y_shinsal', '-')
        d_val = day.get('d_shinsal', '-')
        header_bg = header_color_map.get(day['weekday_kr'], '#424242')
        cells += f"""
        <div style='flex:1; border-left:1px solid #ccc; text-align:center; padding-bottom:3px; background-color:{bg_col};'>
            <div style='background-color:{header_bg}; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{day['day_num']}일({day['weekday_kr']})</div>
            <div class='un-sub-text' style='padding:2px; font-size:12px;'>{day['ss_gan']}</div>
            <div class='{gan_cls}' style='font-size:16px; font-weight:900;'>{day['gan']}</div>
            <div class='{ji_cls}' style='font-size:16px; font-weight:900;'>{day['ji']}</div>
            <div class='un-sub-text' style='padding:2px; font-size:12px;'>{day['ss_ji']}</div>
            <div class='un-sub-text' style='font-size:11px; border-top:1px solid #ccc;'>{day['unsung']}</div>
            <div class='un-sub-text' style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{y_val}</div>
            <div class='un-sub-text' style='font-size:11px; color:#1565C0; border-top:1px solid #ccc;'>{d_val}</div>
        </div>
        """
    return f"""
    <div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 이번 주 일운 흐름 ]</div>
    <div style='display:flex; flex-direction:row; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>
        {cells}
    </div>
    """
 
# ==============================================================================
# PART 2. 서술형 안내문구 (인트로 / 클로징 등 공용 문구)
# ==============================================================================
 
def get_intro_html():
    return """
    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
    <div style="margin: 0; padding: 0;">
        <p class="ai-body-p" style="margin-top: 0; margin-bottom: 6px; font-weight: 600; text-align: justify; text-indent: 0; color: #000000;">
            <b>"초연 시공 명리학"</b>은 5년에 한 번 돌아오는 '60월령과 60일주'의 조합으로 <b>3,600개 유형</b>으로 분류하지만, <b>"기존의 전통 명리학"</b>은 1년에 한 번 돌아오는 '12월지와 60일주'의 조합으로 <b>720개 유형</b>으로 분류하여 풀이합니다.
        </p>
        <p class="ai-body-p" style="margin-top: 0; margin-bottom: 0; font-weight: 600; text-align: justify; text-indent: 0; color: #000000;">
            따라서, <b>"본 초연 시공 명리학적 풀이"</b>는 기존 명리학적 풀이에 비하여 <b>5배</b>, 요즘 유행하는 16개 유형의 MBTI와 비교하면 무려 <b>225배</b> 더 정밀한 사주풀이 입니다.
        </p>
    </div>
    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
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
    <div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000; margin-bottom: 20px;'>
        <p style='text-indent: 1.0em; text-align: justify; margin-bottom: 5px;'>
            기존 명리학적으로 풀이하면 <b>{name}님</b>은 <b>{wol_korean_str}</b>에 <b>'{gyuk_name}'</b>의 그릇을 갖추고 태어나셨으며, 성격은 <b>'{s_name}'</b>인 <b>'{s_type}'</b>으로 <b>'{s_desc}'</b>하는 기본 성향이 있습니다.
        </p>
        <p style='text-indent: 1.0em; text-align: justify; margin-bottom: 0;'>
            또한, 시공명리학적으로 풀이하면 <b>'{w_val}'</b>의 시공간에서 태어났으며, <b>'{i_val}'</b>과 같은 내면적 성품을 갖고 살아가고 있습니다.
        </p>
    </div>
    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
    """

def get_closing_html(name, sign_html=""):
    return f"""
    <div style='margin-top: 30px;'>
        <hr style='border: 0; border-top: 2px dashed #1A237E; margin: 35px 0 20px 0;'>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'><b>'사주팔자(四柱八字)'</b>는 태어날 때 부여받은 <b>바코드(bar-code)</b>와 같지만, 우리가 살아가며 마주하는 <b>'운(運)'</b>은 늘 변화하며 흐릅니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{name}님</b>의 삶이라는 긴 여정에서 올바른 방향을 잡는 든든한 <b>'나침반'</b>이 되기를 진심으로 기원합니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 <b>'인생의 길흉화복'</b>과 <b>'명리에 대한 더 깊은 지혜'</b>가 필요하실 때 언제든 <b>'초연 시공명리 연구소 사주박사'</b>를 찾아 주십시오.</p>
        <p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 깊이 감사드립니다.</p>
        <div style='display: flex; justify-content: flex-end; align-items: center; gap: 18px; margin-top: 30px;'>
            <div style='text-align: right;'>
                <div style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 -</div>
                <div style='font-weight: 900; font-size: 18px; color: #1A237E; margin-top: 4px;'>사주박사 드림</div>
            </div>
            {sign_html}
        </div>
    </div>
    """
 
def get_couple_golden_text(m_name, male_golden_html, f_name, female_golden_html):
    return ""
 
# ==============================================================================
# PART 3. 궁합 · 택일 부가 컴포넌트 및 종합 렌더링 컨테이너
# ==============================================================================
 
def get_daewun_compare_box(m_name, m_daewun_html, f_name, f_daewun_html):
    return f"<div style='margin-bottom: 25px;'>{m_daewun_html}<div style='height:20px;'></div>{f_daewun_html}</div>"
 
def get_gunghap_score_visual_html(gh_engine):
    t_col = "#3498db" if gh_engine.final_score >= 70 else ("#f39c12" if gh_engine.final_score >= 60 else "#e74c3c")
    bars = "".join([f"<div style='display:flex; align-items:center; margin-bottom:12px;'><div style='width:130px; font-size:13px; font-weight:bold; color:#555;'>{d['label']}</div><div style='flex:1; height:12px; margin:0 10px;'><svg width='100%' height='12'><rect width='100%' height='12' rx='6' ry='6' fill='#eee' /><rect width='{d['pct']}%' height='12' rx='6' ry='6' fill='{d['color']}' /></svg></div><div style='width:35px; font-size:12px; font-weight:bold;'>{d['pct']}%</div></div>" for d in gh_engine.details])
    return f"""
    <h2 style='text-align:center; margin-top:40px; font-size:22px; font-weight:900;'>📊 최종 궁합 점수</h2>
    <div style='display:flex; justify-content:center; align-items:center; margin:20px 0;'>
        <div style='width:130px; height:130px; border-radius:50%; background:conic-gradient({t_col} {gh_engine.final_score}%, #eee 0); display:flex; justify-content:center; align-items:center; -webkit-print-color-adjust: exact;'>
            <div style='width:98px; height:98px; background:#fff; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
                <span style='font-size:32px; font-weight:900; color:{t_col};'>{gh_engine.final_score}</span>
                <span style='font-size:10px; color:#888; font-weight:bold;'>SCORE</span>
            </div>
        </div>
    </div>
    <div style='text-align:center; margin-bottom:20px;'><span style='font-size:16px; font-weight:bold; color:#fff; background:{t_col}; padding:8px 32px; border-radius:30px; -webkit-print-color-adjust: exact;'>{gh_engine.grade}</span></div>
    <div style='max-width:500px; margin:0 auto;'>
        {bars}
    </div>
    """
 
def get_gunghap_closing(name1, name2):
    return f"""
    <div style='margin-top: 40px; padding-top: 30px; page-break-inside: avoid;'>
        <p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #333;'>&nbsp;&nbsp;&nbsp;&nbsp;두 분의 <b style='color:#1A237E;'>'만남'</b>은 결코 우연이 아닌, <b style='color:#1A237E;'>'수많은 인연의 이치 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 명식이지만, <b style='color:#1A237E;'>'궁합(宮合)'</b>은 두 명식이 만나 그려내는 새로운 <b style='color:#1A237E;'>'조화와 상생'</b>입니다.</p>
        <p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #333; margin-top: 10px;'>&nbsp;&nbsp;&nbsp;&nbsp;서로의 기운을 보완하고 다독여주는 든든한 <b style='color:#1A237E;'>'반려자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 전통 명리의 축복이 가득하시길 소망합니다.</p>
        <div style='text-align: right; margin-top: 25px;'><span style='font-weight: 900; font-size: 16px; color: #1A237E; font-family: "Nanum Myeongjo", serif;'>- 초연 전통명리 연구소 드림 -</span></div>
    </div>
    """
 
def get_gunghap_three_page_report(male_saju_html, m_ess, female_saju_html, f_ess, g_ess):
    """
    궁합 3분할 페이지 생성 함수 (v2)
    - 남명/여명 각자의 사주표를 별도 인자로 받아 자기 페이지에만 표시
    - 1인용 상품과 동일하게, 페이지마다 get_final_report_box()를 개별 호출하여
      독립된 VIP 프레임(A4 여백 포함)으로 렌더링 → 여백 불일치 문제 해결
    - 제목 정렬에 !important를 추가하여 전역 CSS(.report-page h1 left)를 확실히 덮어씀
    """
    pb_tag = "<div style='page-break-before: always; break-before: page;'></div>"
    clean_m_ess = str(m_ess).replace(pb_tag, "").strip() if m_ess else ""
    clean_f_ess = str(f_ess).replace(pb_tag, "").strip() if f_ess else ""
    clean_g_ess = str(g_ess).replace(pb_tag, "").strip() if g_ess else ""
 
    m_content = f"""
        <h1 style='text-align:center !important; color:#1565C0; font-weight:800; border-bottom:2px solid #1565C0; padding-bottom:10px; margin-bottom:15px; margin-top:0 !important; font-size:21px;'>[ ♂️ 남명 사주 요약 ]</h1>
        {male_saju_html}
        <div style='margin-top:15px;'>{clean_m_ess}</div>
    """
    m_page = get_final_report_box(m_content)
 
    f_content = f"""
        <h1 style='text-align:center !important; color:#4A148C; font-weight:800; border-bottom:2px solid #4A148C; padding-bottom:10px; margin-bottom:15px; margin-top:0 !important; font-size:21px;'>[ ♀️ 여명 사주 요약 ]</h1>
        {female_saju_html}
        <div style='margin-top:15px;'>{clean_f_ess}</div>
    """
    f_page = get_final_report_box(f_content)
 
    g_page = ""
    if clean_g_ess:
        g_content = f"""
            <h1 style='text-align:center !important; color:#1B5E20; font-weight:800; border-bottom:2px solid #1B5E20; padding-bottom:10px; margin-bottom:15px; font-size:21px;'>[ 🍀 초연 시공명리 궁합 풀이 ]</h1>
            <div style='margin-top:15px;'>{clean_g_ess}</div>
        """
        g_page = get_final_report_box(g_content)
 
    return f"{m_page}{f_page}{g_page}"
 
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
 
def get_couple_fact_split_layout(male_block, female_block):
    """남명/여명 사주 원국 블록을 궁합 표지 뒤에 나란히 배치"""
    return f"{male_block}<br>{female_block}"
 
def get_warning_box(title, message):
    return f"""
    <div style='padding:20px; background-color:#FAFAFA; border:2px solid #000000; border-radius:10px; margin-top:20px; font-family: "Nanum Myeongjo", serif;'>
        <h3 style='color:#000000; margin:0 0 8px 0; font-size:17px; font-weight:900;'>⚠️ [{title}]</h3>
        <p style='color:#000000; font-size:15px; margin:0; line-height:1.85;'>{message}</p>
    </div>
    """
 
def get_final_report_box(content_html):
    """A4 백지 캔버스 안쪽 둥근 VIP 프레임 단일 래핑 (불필요 고정 제목 제거본)"""
    return f"""
    <div class='report-page' style='page-break-before: auto;'>
        <div class='vip-inset-frame' style='border: 2px solid #1A237E; padding: 20px; border-radius: 15px; box-sizing: border-box; box-decoration-break: clone; -webkit-box-decoration-break: clone; page-break-inside: auto; break-inside: auto;'>
            {content_html}
        </div>
    </div>
    """
  
# ==============================================================================
# PART 4. 초연 시공명리 '타 감명서 비교(4-1/4-2)' 전용 렌더링
# ※ 향후 비교 기능이 보강되며 추가되는 렌더링 함수는 이 PART 4 맨 뒤에 계속 이어서 추가하면 됩니다.
# ==============================================================================
 
def get_external_raw_text_box(other_text):
    # 빈 줄(문단 구분)을 기준으로 나누고, 각 문단을 AI 본문과 동일한 <p> 스타일로 렌더링
    raw = str(other_text).strip()
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', raw) if p.strip()]
    if not paragraphs:
        paragraphs = [raw]
    para_html = "".join([
        f"<p class='ai-body-p' style='font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-indent: 1.0em !important; margin-bottom: 12px !important; margin-top: 0 !important; font-family: \"Noto Serif KR\", serif !important;'>{p.replace(chr(10), ' ')}</p>"
        for p in paragraphs
    ])
    return f"""
    <div style='margin-top:25px; margin-bottom:25px; padding:24px; background-color:#F9F9F9; border-radius:8px; font-family: "Noto Serif KR", serif;'>
        <h3 style='color:#555; font-size:18px; font-weight:900; margin-bottom:10px;'>📜 [제출된 타 감명서 원문]</h3>
        {para_html}
    </div>
    """
 
def render_saju_comparison_report(saju_fact_html, external_raw_box, ai_content_html):
    master_body = f"""
    <h1 style="text-align:center; color:#2E7D32; font-size: 26px; font-weight: 900; border-bottom:2px solid #2E7D32; padding-bottom:15px; margin-bottom:20px;">⚖️ 타 감명서 학술 검증 및 1:1 대조 리포트</h1>
    {ai_content_html}
    <hr style='border:1px dashed #2E7D32; margin:30px 0;'>
    {external_raw_box}
    """
    return get_final_report_box(master_body)
 
def render_gunghap_comparison_report(couple_fact_html, external_raw_box, ai_content_html):
    master_body = f"""
    <h1 style="text-align:center; color:#C62828; font-size: 26px; font-weight: 900; border-bottom:2px solid #C62828; padding-bottom:15px; margin-bottom:20px;">⚖️ 타 궁합 감명서 학술 검증 및 1:1 대조 리포트</h1>
    {ai_content_html}
    <hr style='border:1px dashed #C62828; margin:30px 0;'>
    {external_raw_box}
    """
    return get_final_report_box(master_body)
 
def render_comparison_report(part_1_fact, external_raw_box, ai_comparison_html):
    master_body = f"{part_1_fact}{external_raw_box}{ai_comparison_html}"
    return get_final_report_box(master_body)

def get_choyeon_sign_html():
    """붉은 인주색 낙관 (이미지로 미리 그려서 삽입 — 폰트 로딩 문제 없이 항상 동일하게 표시됨).
    한글 '초연시공 / 사주박사', 나눔손글씨 붓 서체, 둥근 모서리, 이중 테두리. (2026-09-23 확정본)"""
    return """
    <div style="display:flex; justify-content:flex-end;">
        <img src="data:image/png;base64,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"
             alt="초연시공 사주박사 낙관"
             style="width:130px; height:130px; display:block;">
    </div>
    """
