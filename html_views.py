# ==============================================================================
# html_views.py (ver 86.4 Master - 50.7 황금비율 UI/UX 및 렌더링 완벽 보강본)
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

    /* 🛡️ 2. 표지 영역: 나눔고딕(Nanum Gothic) 최우선 보장 (일반 문장체 풀림 차단) */
    .cover-page, .cover-page *, div.cover-page, div.cover-page * {
        font-family: 'Nanum Gothic', sans-serif !important;
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
    """
    if not text:
        return ""

    # 1. 마크다운 코드 블록 제거 및 라인 분리
    text = re.sub(r'```(?:html)?\s*', '', text)
    lines = [line.strip() for line in text.split("\n")]

    html_lines = []

    # 예약 마커 리스트 (원형 보존)
    preserved_markers = [
        '[DAEWUN_TABLE_HERE]', '[SEWUN_TABLE_HERE]', '[WOLUN_TABLE_HERE]',
        '[WEEKLY_CALENDAR_HERE]', '[COUPLE_DAEWUN_TABLES_HERE]',
        '[CHOYEON_GOLDEN_TEXT_HERE]', '[CHOYEON_SIGN_HERE]'
    ]

    for line in lines:
        if not line:
            continue

        # 예약 마커 보존
        if any(marker in line for marker in preserved_markers):
            html_lines.append(f"\n{line}\n")
            continue

        # 볼드체 변환 (**text** -> <b>text</b>)
        line_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)

        # 1. 대제목: 1. , 2. , 3. 형태
        if re.match(r'^\d+\.\s+', line_formatted):
            html_lines.append(
                f"<div class='ai-title-l1' style='font-size: 24px !important; font-weight: 900 !important; color: #1A237E !important; margin-top: 35px !important; margin-bottom: 15px !important; border-bottom: 2px solid #1A237E !important; padding-bottom: 5px !important; line-height: 1.4 !important; font-family: \"Noto Serif KR\", serif !important;'><b>{line_formatted}</b></div>"
            )

        # 2. 중제목: 1) , 2) , 3) 형태
        elif re.match(r'^\d+\)\s*', line_formatted):
            html_lines.append(
                f"<div class='sub-title' style='font-size: 18px !important; font-weight: 900 !important; color: #111111 !important; margin-top: 22px !important; margin-bottom: 8px !important; font-family: \"Noto Serif KR\", serif !important;'><b>{line_formatted}</b></div>"
            )

        # 3. 🌟 소제목 및 기호: (1), (2), (3) / [1], [2] / ◆, ▶, ▷, ■, ◈, ●, • 형태 (완벽 볼드 강제)
        elif re.match(r'^\(\d+\)\s*', line_formatted) or re.match(r'^\[\d+\]\s*', line_formatted) or re.match(r'^[◆▶▷■◈●•]\s*', line_formatted):
            html_lines.append(
                f"<div style='font-size: 16.5px !important; font-weight: 900 !important; color: #1A237E !important; margin-top: 16px !important; margin-bottom: 6px !important; font-family: \"Noto Serif KR\", serif !important; display: block !important;'><b>{line_formatted}</b></div>"
            )

        # 4. 일반 본문 문단
        else:
            html_lines.append(
                f"<p class='ai-body-p' style='font-size: 16px !important; font-weight: 400 !important; line-height: 1.85 !important; color: #222222 !important; text-align: justify !important; text-indent: 1.0em !important; margin-bottom: 12px !important; margin-top: 0 !important; font-family: \"Noto Serif KR\", serif !important;'>{line_formatted}</p>"
            )

    parsed_content = "\n".join(html_lines)

    # 5. Q&A 텍스트 연동
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

def get_personal_cover(version="", report_title="", u_icon="♂️", u_name="무명", u_sol="", u_lun="", u_time="", today_str="", *args, **kwargs):
    raw_title = str(report_title or "초연 시공명리 사주풀이").replace("🏮", "").replace("🎯", "")
    for tag in ["<br>", "<br/>", "<br />", "\n", "\r"]:
        raw_title = raw_title.replace(tag, " ")
    clean_title = " ".join(raw_title.split())
    clean_u_name = str(u_name or "무명").strip()

    return f"""
    <div class='report-page cover-page' style='padding:0; margin:0 auto; width:210mm; height:297mm; min-height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; box-sizing: border-box; -webkit-print-color-adjust: exact;'>
        <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: #FFFFFF; width: 90%; max-width: 700px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto; box-sizing: border-box;'>
            
            <!-- 상단 대제목 영역 -->
            <div style='border-bottom: 4px double #1A237E; padding-bottom: 20px; margin-bottom: 40px; width: 100%; box-sizing: border-box;'>
                <h1 class='title-gothic' style='font-family: "Nanum Gothic", sans-serif !important; font-size: 26px !important; font-weight: 900 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; white-space: nowrap !important; letter-spacing: -2px !important; line-height: 1.2 !important; text-align: center;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 10px;'>
                    <span class='ver-gothic' style='font-family: "Nanum Gothic", sans-serif !important; font-size: 14px !important; font-weight: 700 !important; letter-spacing: 1px; color: #555555 !important;'>{version}</span>
                </div>
            </div>
            
            <!-- 중단 신청인 정보 영역 -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px; margin-bottom: 24px;'>
                <h2 style='font-family: "Nanum Gothic", sans-serif !important; font-size: 24px !important; font-weight: 800 !important; color: #1A237E !important; margin: 0 0 20px 0 !important;'>{u_icon} 신청인 : {clean_u_name} 님</h2>
                <div style='font-family: "Nanum Gothic", sans-serif !important; font-size: 15px !important; font-weight: 600 !important; color: #555555 !important; line-height: 1.8 !important;'>
                    <div style='margin: 0; text-align: center !important; width: 100% !important; white-space: nowrap;'>[양력] {u_sol} | [음력] {u_lun}</div>
                    <div style='margin: 5px 0 0 0; color: #1A237E !important; text-align: center !important; width: 100% !important; white-space: nowrap; font-weight: 800 !important;'>태어난 시간 : {u_time}</div>
                </div>
            </div>
            
            <!-- 하단 발행일자 및 연구소명 (18px/24px 800볼드 + 10px 간격 완결) -->
            <div style='margin-top: 45px !important; text-align: center !important;'>
                <div style='font-family: "Nanum Gothic", sans-serif !important; font-size: 18px !important; font-weight: 800 !important; color: #111111 !important; line-height: 1.2 !important; margin: 0 0 10px 0 !important; display: block !important;'>{today_str}</div>
                <div style='font-family: "Nanum Gothic", sans-serif !important; font-size: 24px !important; font-weight: 800 !important; color: #1A237E !important; line-height: 1.2 !important; margin: 0 !important; letter-spacing: 0.5px !important; display: block !important;'>초연 시공명리 연구소</div>
            </div>
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
                <h1 class='title-gothic' style='font-family: \"Nanum Gothic\", sans-serif !important; font-size: 25px !important; font-weight: 900 !important; margin: 0 !important; padding: 0 !important; color: #111111 !important; letter-spacing: -1.2px !important; white-space: nowrap !important; word-break: keep-all !important; line-height: 1.2 !important; text-align: center;'>{clean_title}</h1>
                <div style='text-align: right; margin-top: 8px;'>
                    <span class='ver-gothic' style='font-family: \"Nanum Gothic\", sans-serif !important; font-size: 14px !important; font-weight: 700 !important; color: #555555 !important; letter-spacing: 1px;'>{version}</span>
                </div>
            </div>
            
            <!-- 중단 남명 / 여명 정보 박스 -->
            <div style='background: #F8F9FA; border: 1px solid #E8EAF6; padding: 16px 18px; border-radius: 14px; margin-bottom: 14px;'>
                <h2 style='font-family: \"Nanum Gothic\", sans-serif !important; font-size: 20px !important; font-weight: 800 !important; color: #1565C0 !important; margin: 0 0 6px 0 !important;'>{u_icon} 남명 : {clean_u_name} 님 ({u_age}세)</h2>
                <div style='font-family: \"Nanum Gothic\", sans-serif !important; font-size: 14px !important; line-height: 1.6;'>
                    <div style='margin: 0; text-align: center !important; width: 100% !important; white-space: nowrap; color: #000000;'><strong style='font-weight: 800 !important;'>[양력] {u_sol} | [음력] {u_lun}</strong></div>
                    <div style='margin: 3px 0 0 0; text-align: center !important; width: 100% !important; white-space: nowrap; font-weight: 800; color: #1565C0;'>태어난 시간 : {u_time}</div>
                </div>
            </div>
            
            <div style='background: #FFF3E0; border: 1px solid #FBE9E7; padding: 16px 18px; border-radius: 14px; margin-bottom: 22px;'>
                <h2 style='font-family: \"Nanum Gothic\", sans-serif !important; font-size: 20px !important; font-weight: 800 !important; color: #C62828 !important; margin: 0 0 6px 0 !important;'>{p_icon} 여명 : {clean_p_name} 님 ({p_age}세)</h2>
                <div style='font-family: \"Nanum Gothic\", sans-serif !important; font-size: 14px !important; line-height: 1.6;'>
                    <div style='margin: 0; text-align: center !important; width: 100% !important; white-space: nowrap; color: #000000;'><strong style='font-weight: 800 !important;'>[양력] {p_sol} | [음력] {p_lun}</strong></div>
                    <div style='margin: 3px 0 0 0; text-align: center !important; width: 100% !important; white-space: nowrap; font-weight: 800; color: #C62828;'>태어난 시간 : {p_time}</div>
                </div>
            </div>
            
            <!-- 하단 발행일자 및 연구소명 (18px/24px 800볼드 + 10px 간격 완결) -->
            <div style='margin-top: 32px !important; text-align: center !important;'>
                <div style='font-family: \"Nanum Gothic\", sans-serif !important; font-size: 18px !important; font-weight: 800 !important; color: #111111 !important; letter-spacing: 0.5px !important; line-height: 1.2 !important; margin: 0 0 10px 0 !important; display: block !important;'>{today_str}</div>
                <div style='font-family: \"Nanum Gothic\", sans-serif !important; font-size: 24px !important; font-weight: 800 !important; color: #1A237E !important; letter-spacing: 1px !important; line-height: 1.2 !important; margin: 0 !important; display: block !important;'>초연 시공명리 연구소</div>
            </div>
        </div>
    </div>
    <div class='page-break'></div>
    """

def get_info_header(p_icon, name, gender, marital, age, sol_str, lun_str, time_str, p_color="#1A237E"):
    return f"""
    <div style='text-align:center; font-family:"Nanum Gothic", sans-serif; margin-bottom:15px; line-height:1.5;'>
        <span style='font-size:18px; font-weight:900; color:{p_color}; white-space:nowrap;'>{p_icon} {name}님 ({gender}, {marital}, {age}세)</span><br>
        <span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span>
    </div>
    """
