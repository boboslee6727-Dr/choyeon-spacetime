# ==============================================================================
# app.py (ver 73.0 Master - 신청접수/수동입금승인/열람 파이프라인 통합 완결판)
# ==============================================================================
import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from datetime import datetime
from korean_lunar_calendar import KoreanLunarCalendar
import os
import re
from google import genai
import time
import json
import math
import pytz
import sys
import importlib

import engine
import prompts
import html_views

# 🔄 서브 모듈 변경 사항 즉시 반영을 위한 강제 리로드 설정
importlib.reload(engine)
importlib.reload(prompts)
importlib.reload(html_views)

# 🏮 파이프라인 관리 모듈 로드
from pipeline_manager import init_order_db, render_customer_order_form, render_admin_panel, render_view_page

init_order_db()
params = st.query_params

# ------------------------------------------------------------------------------
# 👑 [관리자 입금 승인 시 백그라운드 AI 감명서 자동 생성 래퍼 함수]
# ------------------------------------------------------------------------------
def generate_report_for_order(order_row):
    """관리자가 입금 확인 버튼을 눌렀을 때 실행되는 감명서 완성 생성기"""
    # order_row: DB에서 가져온 신청자 정보 (성명, 생년월일, 시간, 상품 등)
    name = order_row["name"]
    gender = order_row["gender"]
    b_date = order_row["birth_date"] # 'YYYY-MM-DD'
    b_time = order_row["birth_time"]
    cal_type = order_row["calendar_type"]
    product = order_row["product"]
    marital = order_row["marital"]
    
    y, m, d = [int(v) for v in b_date.split("-")]
    is_lunar = "음력" in cal_type
    is_leap = "윤달" in cal_type
    
    # 1. 간지 추출
    g_res = engine.get_ganji_from_date(y, m, d, is_lunar, is_leap)
    y_p, m_p, d_p = g_res[0], g_res[1], g_res[2]
    
    # 2. 사주 팩트 및 시공간 파동 산출
    gans = ["-", d_p[0], m_p[0], y_p[0]]
    jjis = ["-", d_p[1], m_p[1], y_p[1]]
    gyuk, gyuk_detail = engine.get_gyukgook_detailed(d_p[0], y_p[0], m_p[0], "-", m_p[1])
    
    adv_saju = {'year_ji': y_p[1], 'month_ji': m_p[1], 'day_ji': d_p[1], 'hour_ji': '-'}
    adv_flags = html_views.analyze_saju_facts_advanced(adv_saju, "-", "-") if hasattr(html_views, 'analyze_saju_facts_advanced') else {}
    adv_warning = adv_flags.get("warning_message", "정상 시공간 흐름")
    
    saju_summary = f"- {name}님 명조: 년주({y_p}), 월주({m_p}), 일주({d_p}), 시주({b_time})\n- 격국: {gyuk_detail}\n- 파동 경보: {adv_warning}"
    
    # 3. 프롬프트 매핑 및 AI 호출
    prompt_var = "프롬프트_1_1_기본"
    for code, var_name in [("1-1", "프롬프트_1_1_기본"), ("1-2", "프롬프트_1_2_연도운"), ("2-1", "프롬프트_2_1_재물운"), ("2-2", "프롬프트_2_2_직업운"), ("2-3", "프롬프트_2_3_연애운"), ("2-4", "프롬프트_2_4_건강운")]:
        if code in product:
            prompt_var = var_name
            break
            
    target_prompt = getattr(prompts, prompt_var, prompts.프롬프트_1_1_기본)
    
    prompt_input = {
        "name": name, "gender": gender, "marital": marital, "age": dt_mod.date.today().year - y + 1,
        "ilju_master_prompt_context": "", "saju_fact_summary": saju_summary,
        "dw_fact_str": "대운 순환 중", "adv_warning_str": adv_warning,
        "action_solutions": "자연스러운 기운의 순환 유지", "health_erosion_facts": "특이 침식 없음",
        "samja_comb_facts": "특이 조합 없음", "samhyung_potential_facts": "삼형 없음",
        "gyukgook_detail": gyuk_detail, "oheng_counts_str": "오행 균형",
        "shinsal_str": "특이 신살 없음", "cheon_eul": "천을귀인", "samjae_str": "해당 없음",
        "year_gongmang": "-", "day_gongmang": "-", "curr_year": dt_mod.date.today().year,
        "cur_sewun_gan": "甲", "cur_sewun_ji": "辰", "wealth_goal": "자산 증식",
        "career_goal": "직무 적성", "love_goal": "인연 관계", "health_goal": "건강 관리",
        "tackil_purpose": "이사", "target_date_range": "향후 1개월", "other_reading_text": ""
    }
    
    class SafeDict(dict):
        def __missing__(self, k): return '{' + k + '}'
        
    final_prompt = target_prompt.format_map(SafeDict(prompt_input))
    ai_raw = call_gemini_api(final_prompt)
    formatted_body = html_views.format_ai_text_to_html(ai_raw)
    
    # 4. 프리미엄 나눔명조체 리포트 조립
    cover = html_views.get_personal_cover("ver 73.0 Master", product.split(" (")[0], "🏮", name, f"{y}년 {m}월 {d}일", "", b_time, dt_mod.date.today().strftime("%Y년 %m월 %d일"))
    info_h = html_views.get_info_header("🏮", name, gender, marital, dt_mod.date.today().year - y + 1, f"{y}년 {m}월 {d}일", "", b_time)
    final_html = f"{cover}<br>{info_h}<br>{formatted_body}"
    return html_views.get_final_report_box(final_html)

# ------------------------------------------------------------------------------
# 🧭 [3대 화면 라우팅 분기]
# ------------------------------------------------------------------------------
if params.get("mode") == "admin":
    # 👑 박사님 관리자 패널
    render_admin_panel(generate_report_for_order)
    st.stop()
elif params.get("mode") == "view" and "code" in params:
    # 📜 고객 결과 열람 화면
    render_view_page(params["code"])
    st.stop()
elif params.get("mode") == "order":
    # 📱 고객 모바일 신청 접수창
    render_customer_order_form()
    st.stop()

# (이하 기존 app.py의 1. 초기 설정부터 메인 코드 원본 100% 그대로 유지)
