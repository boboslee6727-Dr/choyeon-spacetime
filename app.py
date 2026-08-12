# ==============================================================================
        # 🎯 상품 고유번호(startswith) 기반 표지 타이틀 조건문 (100% 안전 방어)
        # ==============================================================================
        if u_product.startswith("1-1"):
            report_title = "🏮 사주팔자와 운세풀이"
        elif u_product.startswith("1-2"):
            report_title = "🏮 올 해 (특정 연도) 운세 상세분석"
        elif u_product.startswith("1-3"):
            report_title = "🏮 이번 달 (특정 월) 운세 상세분석"
        elif u_product.startswith("1-4"):
            report_title = "🏮 이번 (특정) 주간 및 일 운세 상세분석"
        elif u_product.startswith("2-1"):
            report_title = "🏮 재물운 특화 정밀 분석"
        elif u_product.startswith("2-2"):
            report_title = "🏮 직업/진학운 특화 정밀 분석"
        elif u_product.startswith("2-3"):
            report_title = "🏮 연애/결혼운 특화 정밀 분석"
        elif u_product.startswith("2-4"):
            report_title = "🏮 건강운 특화 정밀 분석"
        elif u_product.startswith("2-5"):
            report_title = "🏮 이사 및 방위 특화 정밀 분석"
        elif u_product.startswith("3-1"):
            report_title = "🏮 커플 연애/결혼운 정밀 궁합 분석"
        elif u_product.startswith("3-2"):
            report_title = "🏮 최고의 결혼 길일 추천 리포트"
        elif u_product.startswith("3-3"):
            report_title = "🏮 새 생명 마중 출산 길일 추천 리포트"
        elif u_product.startswith("4-1"):
            report_title = "🏮 사주 감명서 1:1 대조 리포트"
        elif u_product.startswith("4-2"):
            report_title = "🏮 궁합 감명서 1:1 대조 리포트"
        else:
            report_title = "🏮 사주팔자 정밀 분석"
