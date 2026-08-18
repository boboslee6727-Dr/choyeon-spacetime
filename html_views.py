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
