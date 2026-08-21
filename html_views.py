def format_ai_text_to_html(text):
    """
    AI 생성 텍스트 포맷터 (에러 유발 코드 완전 삭제 및 안정성 최우선 버전)
    """
    if not text:
        return ""

    # 🌟 [방어막 0] 한자 진녹색 오염 원천 차단 CSS
    anti_color_css = """
    <style>
    .ai-content span[class*="color-"], .ai-content span[class*="ganji-"] {
        background-color: transparent !important;
        color: inherit !important;
        font-size: inherit !important;
        font-weight: inherit !important;
        padding: 0 !important;
        border: none !important;
    }
    .ai-content { color: #111111; }
    </style>
    """

    # 🌟 [방어막 1] 소따옴표 안쪽만 볼드 (글로벌 CSS의 .b-text 재활용)
    text = re.sub(r'\*\*[\'\"](.*?)[\'\"]\*\*', r"'<b class=\"b-text\">\1</b>'", text)
    text = re.sub(r'[\'\"]\*\*(.*?)\*\*[\'\"]', r"'<b class=\"b-text\">\1</b>'", text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b class="b-text">\1</b>', text)
    text = text.replace('*', '').replace('#', '')

    # 🚨 (에러를 유발했던 '뭉텅이 텍스트 강제 절단기' 정규식 코드는 박사님 지시에 따라 완전히 삭제했습니다!) 🚨

    # 💡 Q&A 박스 분리
    match = re.search(r'(?:\n\s*|^)(\d+[\.\)]\s*)?💡(.*)', text, re.DOTALL)
    if match:
        split_idx = match.start()
        main_text = text[:split_idx].strip()
        qna_text = "💡" + match.group(2).strip()
    else:
        main_text = text.strip()
        qna_text = ""

    lines = str(main_text).split('\n')
    html_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        clean_line = re.sub(r'^#+\s*', '', line)

        # 수석보좌관 헤더
        if '수석보좌관' in clean_line or '장단점 정밀 비교' in clean_line or clean_line.startswith('[수석보좌관'):
            html_lines.append(f"<div style='font-size: 18px; font-weight: 800; color: #1A237E; text-align: center; padding-bottom: 6px; margin-top: 18px; margin-bottom: 8px; border-bottom: 2.5px solid #1A237E;'>{clean_line}</div>")
            continue

        # (1) "1) [소제목]: 본문"
        colon_match = re.match(r'^(\d+)([\.\)])\s*(.*?):(.*)', clean_line)
        if colon_match:
            num = colon_match.group(1)
            title_text = colon_match.group(3).strip()
            body_part = colon_match.group(4).strip()
            title_part = f"{num}) {title_text}:"
            
            html_lines.append(f"<div style='font-size: 20px; font-weight: 900; color: #1A237E; margin-top: 18px; margin-bottom: 8px;'>{title_part}</div>")
            if body_part:
                html_lines.append(f"<p style='font-size: 16px; font-weight: 500; line-height: 1.85; text-align: justify; margin: 0 0 12px 0; text-indent: 10px;'>{body_part}</p>")
            continue

        # (2) "[소제목]: 본문"
        colon_match_no_num = re.match(r'^(\[.*?\])\s*:(.*)', clean_line)
        if colon_match_no_num:
            title_part = colon_match_no_num.group(1).strip() + ":"
            body_part = colon_match_no_num.group(2).strip()
            html_lines.append(f"<div style='font-size: 17px; font-weight: 800; color: #1A237E; margin-top: 16px; margin-bottom: 4px;'>{title_part}</div>")
            if body_part:
                html_lines.append(f"<p style='font-size: 16px; font-weight: 500; line-height: 1.85; text-align: justify; margin: 0 0 12px 0; text-indent: 10px;'>{body_part}</p>")
            continue

        # 👑 (3) 순수 대제목 (1. 제목)
        if re.match(r'^\d+\.\s', clean_line) and len(clean_line) <= 60:
            html_lines.append(f"<div style='font-size: 22px; font-weight: 900; color: #000000; margin-top: 24px; margin-bottom: 12px; border-bottom: 1px solid #E0E0E0; padding-bottom: 5px;'>{clean_line}</div>")
            continue

        # 👑 (4) 순수 중/소제목 (1) 제목)
        if re.match(r'^\d+\)\s', clean_line) and len(clean_line) <= 60:
            html_lines.append(f"<div style='font-size: 20px; font-weight: 900; color: #1A237E; margin-top: 18px; margin-bottom: 8px;'>{clean_line}</div>")
            continue

        # 👑 (5) 순수 소소제목 ((1) 제목)
        if re.match(r'^\(\d+\)\s', clean_line) and len(clean_line) <= 60:
            html_lines.append(f"<div style='font-size: 18px; font-weight: 800; color: #333333; margin-top: 14px; margin-bottom: 6px;'>{clean_line}</div>")
            continue

        # 👑 (6) 일반 서술 문장 (줄간격 1.85)
        indent = "5px" if clean_line.startswith('-') else "15px"
        padding = "padding-left: 10px;" if clean_line.startswith('-') else ""
        html_lines.append(f"<p style='font-size: 16px; font-weight: 500; line-height: 1.85; text-align: justify; margin: 4px 0 8px 0; text-indent: {indent}; {padding}'>{clean_line}</p>")

    main_html = "\n".join(html_lines)

    # 💡 Q&A 박스 포맷팅
    qna_html = ""
    if qna_text:
        qna_body = qna_text.replace('\n\n', '<br><br>').replace('\n', '<br>')
        qna_html = f"""
        <div style='background-color: #FFFDF5; border: 2px solid #FFE082; border-radius: 12px; padding: 22px; margin-top: 30px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);'>
            <div style='font-size: 16px; line-height: 1.85; font-weight: 600;'>
                {qna_body}
            </div>
        </div>
        """

    # 🌟 무균실(.ai-content)에 텍스트를 담아서 내보냅니다!
    return anti_color_css + f"<div class='ai-content'>\n{main_html}\n{qna_html}\n</div>"
