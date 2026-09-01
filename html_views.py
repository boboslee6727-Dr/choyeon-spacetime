# ==============================================================================
# html_views.py (ver 86.3 Master - 50.7 황금비율 UI/UX 및 렌더링 완벽 보강본)
# [수정] 표지 폰트: Nanum Gothic -> Nanum Myeongjo(나눔명조) / 발행일자·발행인 크게+굵게 강조
# ==============================================================================
import re
import streamlit as st
# ==============================================================================
# 📦 섹션 1. 글로벌 스타일 (CSS) 및 AI 통변 텍스트 포맷터
# ==============================================================================
def get_global_css():
    """전체 시스템 UI/UX 및 화면/인쇄 듀얼 분리 스타일시트 (나눔명조/스타일 충돌 해결)"""
    return """<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&display=swap');
    .stApp { background-color: #E8F5E9 !important; }
 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span[data-testid="stMarkdownContainer"] {
        font-family: 'Nanum Gothic', sans-serif !important;
    }
    div[data-testid="stSidebar"] * { font-size: 14px !important; }
 
    /* 🚨 라디오 버튼 텍스트가 잘리지 않고 두 줄(\n)로 나오도록 속성 부여 */
    div[data-testid="stRadio"] label p {
        font-size: 14px !important;
        white-space: pre-wrap !important;
        line-height: 1.6 !important;
        padding-bottom: 4px !important;
    }
    div[data-testid="stCheckbox"] label p { font-size: 14px !important; }
    /* 🛡️ 1. 본문 영역: 명조체(Noto Serif KR) 강제 */
    .report-page:not(.cover-page), .report-page:not(.cover-page) *, .choyeon-premium-report, .result-table td {
        font-family: 'Noto Serif KR', serif !important;
    }
    /* 🛡️ 2. 표지 영역: 나눔명조(Nanum Myeongjo) 최우선 보장 (일반 문장체 풀림 차단) */
    .cover-page, .cover-page *, div.cover-page, div.cover-page * {
        font-family: 'Nanum Myeongjo', serif !important;
        box-sizing: border-box !important;
    }
    /* 🛡️ 표지 내부 텍스트 여백 및 들여쓰기 초기화 */
    .cover-page p, .cover-page div, .cover-page span, .cover-page h1, .cover-page h2 {
        text-indent: 0 !important;
    }
    /* 🛡️ 표지 박스 기본 속성 (A4 인쇄 정밀 대응) */
    .cover-page {
        display: flex !important;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 0 !important;
        background: #ffffff;
        margin: 0 auto;
        box-sizing: border-box;
        width: 210mm;
        height: 297mm;
        min-height: 297mm;
        page-break-after: always;
        -webkit-print-color-adjust: exact;
    }
    /* 🌟 본문 대제목(h1 및 ai-title-l1) 진한 남색 밑줄 쫙 일괄 적용 */
    .report-page:not(.cover-page) h1, .ai-title-l1 {
        font-size: 26px !important;
        font-weight: 900 !important;
        color: #1A237E !important;
        text-align: center !important;
        border-bottom: 3px solid #1A237E !important;
        padding-bottom: 10px !important;
        margin-bottom: 25px !important;
        margin-top: 10px !important;
        letter-spacing: -0.5px !important;
        display: block !important;
        width: 100% !important;
        font-family: 'Noto Serif KR', serif !important;
    }
    .b-text { font-weight: 900 !important; color: #000000 !important; display: inline-block; }
    .b-text-red { font-weight: 900 !important; color: #D50000 !important; display: inline-block; }
    div.stButton > button {
        font-family: 'Nanum Gothic', sans-serif !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        width: 100% !important;
    }
    div.stButton > button[kind="primary"], div.stButton > button[data-testid="baseButton-primary"] {
        background-color: #D50000 !important;
        color: #FFFFFF !important;
        border: none !important;
        height: 50px !important;
        font-weight: 900 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button[kind="primary"]:hover, div.stButton > button[data-testid="baseButton-primary"]:hover {
        background-color: #B71C1C !important;
        color: #FFFFFF !important;
    }
    div.stButton > button[kind="secondary"], div.stButton > button[data-testid="baseButton-secondary"] {
        background-color: #00A843 !important;
        color: #FFFFFF !important;
        border: none !important;
        height: 50px !important;
        font-weight: 900 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08) !important;
    }
    div.stButton > button[kind="secondary"]:hover, div.stButton > button[data-testid="baseButton-secondary"]:hover {
        background-color: #008937 !important;
        color: #FFFFFF !important;
    }
    /* 50.7 통변 제목 및 본문 스타일 */
    .ai-title-l1, .report-page h3 { font-size: 24px !important; font-weight: 900 !important; color: #1A237E !important; margin-top: 35px !important; margin-bottom: 15px !important; border-bottom: 2px solid #1A237E !important; padding-bottom: 5px !important; line-height: 1.4 !important; font-family: 'Noto Serif KR', serif !important; display: block !important; }
    .sub-title, .ai-title-l2 { font-size: 18px !important; font-weight: 900 !important; color: #111111 !important; margin-top: 22px !important; margin-bottom: 10px !important; line-height: 1.4 !important; font-family: 'Noto Serif KR', serif !important; display: block !important; }
    .vip-inset-frame { border: 2px solid #3E2723 !important; border-radius: 12px !important; padding: 30px 25px !important; background-color: #FFFFFF !important; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .content-box-loose { margin-bottom: 25px !important; }
 
    /* 🛡️ 본문 p태그와 표지 p태그 충돌 방지 */
    .ai-body-p, .report-page:not(.cover-page) p { font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-justify: inter-character !important; text-indent: 1.0em !important; margin-bottom: 12px !important; word-break: break-all !important; }
    .cover-page p { text-indent: 0 !important; }
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
        .stSidebar, button, iframe, .print-hide, header, [data-testid="stHeader"] { display: none !important; }
        body, .stApp { background-color: white !important; }
 
        .block-container, div[data-testid="stAppViewBlockContainer"] { padding-top: 0 !important; padding-bottom: 0 !important; margin-top: 0 !important; margin-bottom: 0 !important; }
        div[data-testid="stVerticalBlock"] { gap: 0 !important; }
        .element-container, .stMarkdown { margin-bottom: 0 !important; }
 
        .report-page { box-shadow: none; margin: 0 auto; padding: 0; page-break-after: always; border-radius: 0; width: 100%; max-width: 100%; }
        .report-page:last-of-type { page-break-after: auto; }
        .page-break-before { page-break-before: always; }
 
        .vip-inset-frame {
            border: 2px solid #000 !important;
            border-radius: 20px !important;
            padding: 15px !important;
            box-decoration-break: clone !important;
            -webkit-box-decoration-break: clone !important;
        }
    }
    </style>"""

def format_ai_text_to_html(text, qna_text=""):
    """
    프롬프트 규칙 4번 대응 포맷터:
    대제목(1.), 중제목(1)), 소제목((1), ◆, ■), 일반 본문을 완벽 구분하여 굵은체 및 규격 렌더링
    (AI가 임의로 붙이는 마크다운 헤더 #, ##, ### 및 --- 구분선도 안전하게 처리)
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
    for line in lines:
        if not line:
            continue
        if re.fullmatch(r'[-*_]{3,}', line):
            continue
        if any(marker in line for marker in preserved_markers):
            html_lines.append(f"\n{line}\n")
            continue
        line_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
        line_formatted = re.sub(r'^#{1,6}\s*', '', line_formatted)
        if re.match(r'^\d+\.\s+', line_formatted):
            html_lines.append(f"<div class='ai-title-l1' style='font-size: 24px !important; font-weight: 900 !important; color: #1A237E !important; margin-top: 35px !important; margin-bottom: 15px !important; border-bottom: 2px solid #1A237E !important; padding-bottom: 5px !important; line-height: 1.4 !important; font-family: \"Noto Serif KR\", serif !important;'><b>{line_formatted}</b></div>")
        elif re.match(r'^\d+\)\s*', line_formatted):
            html_lines.append(f"<div class='sub-title' style='font-size: 18px !important; font-weight: 900 !important; color: #111111 !important; margin-top: 22px !important; margin-bottom: 8px !important; font-family: \"Noto Serif KR\", serif !important;'><b>{line_formatted}</b></div>")
        elif re.match(r'^\(\d+\)\s*', line_formatted) or re.match(r'^\[\d+\]\s*', line_formatted) or re.match(r'^[◆▶▷■◈●•]\s*', line_formatted):
            html_lines.append(f"<div style='font-size: 16.5px !important; font-weight: 900 !important; color: #1A237E !important; margin-top: 16px !important; margin-bottom: 6px !important; font-family: \"Noto Serif KR\", serif !important; display: block !important;'><b>{line_formatted}</b></div>")
        else:
            html_lines.append(f"<p class='ai-body-p' style='font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-indent: 1.0em !important; margin-bottom: 12px !important; margin-top: 0 !important; font-family: \"Noto Serif KR\", serif !important;'>{line_formatted}</p>")
    parsed_content = "\n".join(html_lines)
    qna_html = ""
    if qna_text:
        clean_qna = qna_text.replace('💡', '').strip()
        clean_qna = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean_qna).replace('\n\n', '<br><br>').replace('\n', '<br>')
        qna_html = f"<div style='margin-top:25px; padding:15px 20px; background:#F8F9FA; border-left:4px solid #1A237E; border-radius:4px; font-weight:bold;'>💡 사주박사의 1:1 심층 솔루션 안내<br>{clean_qna}</div>"
    return f"<div class='choyeon-premium-report' style='font-family: \"Noto Serif KR\", serif; font-size: 16px; line-height: 1.85; color: #222222;'>{parsed_content}{qna_html}</div>"

# ==============================================================================
# 📦 섹션 2. 공통 역학 테이블 및 컴포넌트 모듈 (50.7 완벽 이식)
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
            
            <!-- 🌟 대제목 영역: 사이즈를 25px로 최적화하고 자간 압축(-1.2px) 및 1줄 고정 방어막 전개 -->
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 28px; width: 100%; box-sizing: border-box;'>
                <h1 style='font-family: "Nanum Myeongjo", serif !important; font-size: 25px !important; font-weight: 900 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -1.2px !important; white-space: nowrap !important; word-break: keep-all !important; line-height: 1.2 !important; text-align: center;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span style='font-family: "Nanum Myeongjo", serif; font-size: 14px; font-weight: 700; color: #555555; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            
            <!-- 신청인 정보 박스: 나눔명조 강제 적용 -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 22px 20px; border-radius: 14px; margin-bottom: 24px;'>
                <h2 style='font-family: "Nanum Myeongjo", serif; font-size: 24px; font-weight: 800; color: #1A237E; margin: 0 0 10px 0;'>{u_icon} {clean_u_name} 님</h2>
                <div style='font-family: "Nanum Myeongjo", serif; font-size: 16px; line-height: 1.8;'>
                    <p style='margin: 0; white-space: nowrap; color: #000000;'><strong style='font-weight: 900 !important;'>[양력] {u_sol} | [음력] {u_lun}</strong></p>
                    <p style='margin: 4px 0 0 0; white-space: nowrap; font-weight: 800; color: #1A237E;'>태어난 시간 : {u_time}</p>
                </div>
            </div>
            
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 20px; margin-top: 35px; margin-bottom: 0; font-weight: 800; color: #000000; letter-spacing: 0.5px;'>{today_str}</p>
            <p style='font-family: "Nanum Myeongjo", serif; font-size: 28px; font-weight: 900; color: #1A237E; margin-top: 8px; margin-bottom: 0; letter-spacing: 1px;'>초연 시공명리 연구소</p>
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
            <!-- 상단 대제목 영역 -->
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 16px; margin-bottom: 28px; width: 100%; box-sizing: border-box;'>
                <h1 class='title-myeongjo' style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 25px !important; font-weight: 800 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -1.2px !important; white-space: nowrap !important; word-break: keep-all !important; line-height: 1.2 !important; text-align: center;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span class='ver-myeongjo' style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 14px !important; font-weight: 700 !important; color: #555555 !important; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            <!-- 중단 남명 / 여명 정보 박스 -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 16px 18px; border-radius: 14px; margin-bottom: 14px;'>
                <h2 style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 24px !important; font-weight: 800 !important; color: #1565C0 !important; margin: 0 0 6px 0 !important;'>{u_icon} 남명 : {clean_u_name} 님 ({u_age}세)</h2>
                <div style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 16px !important; line-height: 1.6;'>
                    <p style='margin: 0; text-align: center !important; width: 100% !important; white-space: nowrap; color: #000000;'><strong style='font-weight: 800 !important;'>[양력] {u_sol} | [음력] {u_lun}</strong></div>
                    <p style='margin: 3px 0 0 0; text-align: center !important; width: 100% !important; white-space: nowrap; font-weight: 800 !important; color: #1565C0;'>태어난 시간 : {u_time}</div>
                </div>
            </div>
            <div style='background: #FFF3E0; border: 1px solid #FBE9E7; padding: 16px 18px; border-radius: 14px; margin-bottom: 22px;'>
                <h2 style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 24px !important; font-weight: 800 !important; color: #C62828 !important; margin: 0 0 6px 0 !important;'>{p_icon} 여명 : {clean_p_name} 님 ({p_age}세)</h2>
                <div style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 16px !important; line-height: 1.6;'>
                    <p style='margin: 0; text-align: center !important; width: 100% !important; white-space: nowrap; color: #000000;'><strong style='font-weight: 800 !important;'>[양력] {p_sol} | [음력] {p_lun}</strong></div>
                    <p style='margin: 3px 0 0 0; text-align: center !important; width: 100% !important; white-space: nowrap; font-weight: 800 !important; color: #C62828;'>태어난 시간 : {p_time}</div>
                </div>
            </div>
            <!-- 하단 발행일자 및 연구소명 (크고 굵게 강조) -->
            <div style='margin-top: 32px !important; text-align: center !important;'>
                <p style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 20px !important; font-weight: 800 !important; color: #111111 !important; letter-spacing: 0.5px !important; line-height: 1.2 !important; margin: 0 0 12px 0 !important; display: block !important;'>{today_str}</div>
                <p style='font-family: \"Nanum Myeongjo\", serif !important; font-size: 28px !important; font-weight: 800 !important; color: #1A237E !important; letter-spacing: 1px !important; line-height: 1.2 !important; margin: 0 !important; display: block !important;'>초연 시공명리 연구소</div>
            </div>
        </div>
    </div>
    <div class='page-break'></div>
    """

def get_main_title_html(report_title=""):
    """AI 통변 페이지 최상단 대제목 - 제목 밑에 굵은 밑줄로 위엄을 강조"""
    clean_title = str(report_title or "").strip()
    return f"""
    <div style='text-align: center; margin: 10px 0 30px 0; padding: 0; width: 100%;'>
        <h2 style='font-family: "Nanum Myeongjo", serif !important; font-size: 28px !important; font-weight: 900 !important; color: #1A237E !important; letter-spacing: -0.5px !important; margin: 0 !important; padding: 0 0 14px 0 !important; display: inline-block !important; border-bottom: 3px solid #1A237E !important;'>{clean_title}</h2>
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
        <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'><span style='color:inherit !important;'>십이신살</span></td>{y_shinsal_tds}</tr>
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
        <div>🎯 공망: [일] {i_gong}</div>
        <div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div>
    </div>
    """

# 🌟 대운/세운/월운표: ver 50.7 황금비율
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
    bg_col = "#FFF9C4" if is_current else "transparent"
    
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{title_str}</div>
        <div style='padding:2px; font-size:12px;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:16px; font-weight:900;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:16px; font-weight:900;'>{ji}</div>
        <div style='padding:2px; font-size:12px;'>{ss_ji}</div>
        <div style='font-size:11px; border-top:1px solid #ccc;'>{u_val}</div>
        <div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{y_val}</div>
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
            data["un_sung"], data.get("y_shinsal", "-"), "", "", b_left, data.get("is_current", False)
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
    bg_col = "#E1F5FE" if is_current else "transparent"
    
    age_str = str(tage).strip()
    display_tage = age_str if age_str.endswith("세") else f"{age_str}세"
    
    return f"""
    <div style='flex:1; border-left:1px solid #ccc; text-align:center; padding-bottom:3px; background-color:{bg_col};'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; line-height:1.2; border-bottom:1px solid #ccc;'>{title_str}<br>({display_tage})</div>
        <div style='padding:2px; font-size:12px;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:16px; font-weight:900;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:16px; font-weight:900;'>{ji}</div>
        <div style='padding:2px; font-size:12px;'>{ss_ji}</div>
        <div style='font-size:11px; border-top:1px solid #ccc;'>{u_val}</div>
        <div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{y_val}</div>
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
    bg_col = "#E8F5E9" if is_current else "transparent"
    
    return f"""
    <div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'>
        <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{tm}월</div>
        <div style='padding:2px; font-size:12px;'>{ss_gan}</div>
        <div class='{gan_cls}' style='font-size:16px; font-weight:900;'>{gan}</div>
        <div class='{ji_cls}' style='font-size:16px; font-weight:900;'>{ji}</div>
        <div style='padding:2px; font-size:12px;'>{ss_ji}</div>
        <div style='font-size:11px; border-top:1px solid #ccc;'>{u_val}</div>
        <div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{y_val}</div>
    </div>
    """

def generate_weekly_calendar_html(weekly_days_data, today_day, yb=None, db=None):
    pass

# ==============================================================================
# 📦 섹션 3. 서술형 텍스트 박스 (인트로, 황금문구, 클로징 등)
# ==============================================================================

def get_intro_html():
    return """
    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
    <div style="margin: 0; padding: 0;">
        <p class="ai-body-p" style="margin-top: 0; margin-bottom: 6px; font-weight: 600; text-align: justify; text-indent: 0; color: #000000;">
            <b>"초연 시공 명리학"</b>은 5년에 한 번 돌아오는 '60월령과 60일주'의 조합으로 <b>3,600개 유형</b>으로 분류하지만, <b>"기존의 전통 명리학"</b>은 1년에 한 번 돌아오는 '12월지와 60일주'의 조합으로 <b>720개 유형</b>으로 분류하여 풀이합니다.
        </p> 
        <p class="ai-body-p" style="margin-top: 0; margin-bottom: 0; font-weight: 600; text-align: justify; text-indent: 0; color: #000000;">
            따라서, <b>"본 초연 시공 명리학적 풀이"</b>는 기존 명리학적 풀이에 비하여 <b>5배</b>, 요즘 유행하는 16개 유형의 MBTI와 비교하면 무려 <b>225배</b> 더 정확한 사주풀이 입니다.
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
            또한, 시공명리학적으로 풀이하면 <b>'{w_val}'</b>의 역동적인 시공간 파동을 지니고 있으며, <b>'{i_val}'</b>의 내면적 본성을 함께 품고 살아갑니다.
        </p>
    </div>
    <hr style="border: 0; border-top: 2px solid #000000; margin: 25px 0;">
    """

def get_closing_html(name):
    return f"""
    <div style='margin-top: 30px;'>
        <hr style='border: 0; border-top: 2px dashed #1A237E; margin: 35px 0 20px 0;'>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 정통 명식의 바코드와 같지만, 우리가 살아가며 마주하는 '운'은 늘 변화하며 흐릅니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{name}님</b>의 삶이라는 긴 여정에서 올바른 방향을 잡는 든든한 '나침반'이 되기를 진심으로 기원합니다.</p>
        <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 인생의 길흉화복과 명리에 대한 더 깊은 지혜가 필요하실 때 언제든 <b>'초연 전통명리 연구소'</b>를 찾아 주십시오.</p>
        <p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 깊이 감사드립니다.</p>
        <div style='text-align: right; margin-top: 30px;'>
            <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
        </div>
    </div>
    """

def get_couple_golden_text(m_name, male_golden_html, f_name, female_golden_html):
    return ""

def get_external_raw_text_box(other_text):
    return f"""
    <div style='margin-top:25px; margin-bottom:25px; padding:24px; background-color:#F9F9F9; border-radius:8px; font-family: "Nanum Myeongjo", serif;'>
        <h3 style='color:#555; font-size:18px; font-weight:900; margin-bottom:10px;'>📜 [제출된 타 감명서 원문]</h3>
        <div style='font-size: 14px; line-height: 1.8; color: #444; word-break: keep-all;'>{other_text}</div>
    </div>
    """

# ==============================================================================
# 📦 섹션 4. 궁합 및 택일 부가 컴포넌트 
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

def get_gunghap_three_page_report(m_saju_html, m_ess, f_ess, g_ess):
    """
    [제2원칙 최종 승인판] 궁합 3분할 페이지 일괄 생성 함수
    - app.py 고정 환경 완벽 대응: 섞여 들어온 페이지 넘김 태그를 안전하게 분리
    """
    
    # 1. 🚨 [불순물 제거 필터] app.py가 억지로 집어넣은 페이지 넘김 태그
    pb_tag = "<div style='page-break-before: always; break-before: page;'></div>"
    
    # f_ess와 g_ess에서 테두리를 찢어발기는 원흉(pb_tag)만 완벽히 삭제하고 알맹이만 남깁니다.
    clean_f_ess = str(f_ess).replace(pb_tag, "").strip() if f_ess else ""
    clean_g_ess = str(g_ess).replace(pb_tag, "").strip() if g_ess else ""

    # 2. [1페이지] ♂️ 남명 사주 요약 조립
    m_page = f"""
    <div style='border: 2px solid #1565C0; border-radius: 12px; padding:20px; background:#FFFFFF; margin-bottom:20px;'>
        <h1 style='text-align:center; color:#1565C0; font-weight:800; border-bottom:2px solid #1565C0; padding-bottom:10px; margin-bottom:15px; font-size:21px;'>[ ♂️ 남명 사주 요약 ]</h1>
        {m_saju_html}
        <div style='margin-top:15px;'>{m_ess}</div>
    </div>
    """
    
    # 3. [2페이지] ♀️ 여명 사주 요약 조립 (불순물이 제거된 알맹이 사용)
    f_page = ""
    if clean_f_ess:
        f_page = f"""
        <div class='page-break'></div>
        <div style='border: 2px solid #4A148C; border-radius: 12px; padding:20px; background:#FFFFFF; margin-bottom:20px;'>
            <h1 style='text-align:center; color:#4A148C; font-weight:800; border-bottom:2px solid #4A148C; padding-bottom:10px; margin-bottom:15px; font-size:21px;'>[ ♀️ 여명 사주 요약 ]</h1>
            <div style='margin-top:15px;'>{clean_f_ess}</div>
        </div>
        """
        
    # 4. [3페이지] 🍀 커플 궁합 풀이 조립 (불순물이 제거된 알맹이 사용)
    g_page = ""
    if clean_g_ess:
        g_page = f"""
        <div class='page-break'></div>
        <div style='border: 2px solid #1B5E20; border-radius: 12px; padding:20px; background:#FFFFFF;'>
            <h1 style='text-align:center; color:#1B5E20; font-weight:800; border-bottom:2px solid #1B5E20; padding-bottom:10px; margin-bottom:15px; font-size:21px;'>[ 🍀 초연 시공명리 궁합 풀이 ]</h1>
            <div style='margin-top:15px;'>{clean_g_ess}</div>
        </div>
        """
        
    # 5. 최종 액자(A4 VIP 프레임)에 넣어서 렌더링 반환!
    return get_final_report_box(m_page + f_page + g_page)

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
# 📦 섹션 5. 종합 렌더링 컨테이너 모듈 
# ==============================================================================

def get_couple_fact_split_layout(male_block, female_block):
    pass

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
