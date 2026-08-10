import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
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

# ==============================================================================
# 1. 초기 설정 및 공통 함수
# ==============================================================================
APP_VERSION = "ver 72.2 Master"
st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

if hasattr(html_views, 'get_global_css'):
    st.markdown(html_views.get_global_css(), unsafe_allow_html=True)

idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", 
    "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", 
    "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", 
    "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]

if 'app_running' not in st.session_state: st.session_state['app_running'] = False

@st.cache_data
def load_choyeon_db():
    file_path = 'choyeon_db.json'
    if not os.path.exists(file_path): return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception: return {}

db = load_choyeon_db()

# ==============================================================================
# 1.5. AI 및 명리 연산 엔진
# ==============================================================================
try:
    _gemini_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as _api_e:
    st.error(f"🚨 Gemini API 키 오류: {_api_e}")
    _gemini_client = None

@st.cache_data(show_spinner=False, ttl=86400)
def get_ai_response(system_prompt, prompt_text, model_name='gemini-2.5-flash'):
    if '1.5' in model_name: model_name = 'gemini-2.5-flash'
    if _gemini_client is None: return "<div style='color:red;'>🚨 Gemini 모델이 초기화되지 않았습니다.</div>"
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = _gemini_client.models.generate_content(
                model=model_name, contents=prompt_text,
                config=genai.types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.7)
            )
            return response.text.strip()
        except Exception as e:
            if attempt < max_retries: time.sleep(1); continue
            return f"<div style='color:red;'>🚨 AI 서버 장애: {e}</div>"

def call_gemini_api(prompt_text, max_tokens=6000):
    sys_role = getattr(prompts, '공통_시스템_헤더', "당신은 초연 시공명리 전문가입니다.")
    return get_ai_response(sys_role, prompt_text, model_name='gemini-2.5-flash')

def get_oh_class(ganji):
    oh = engine.get_color(ganji)
    return f"color-{oh}" if oh != '무' else ""

# ==============================================================================
# 2. 사이드바 통제 센터 (구버전과 동일한 4대 메뉴 체계 완전 재구성)
# ==============================================================================
with st.sidebar:
    def stop_ai():
        st.session_state['app_running'] = False

    st.markdown(f"""
        <div style="padding-top: 15px; margin-bottom: 5px; text-align: center;">
            <h1 style="font-family: 'Nanum Gothic', sans-serif; color: #000000; font-weight: 900; font-size: 20px; margin: 0 0 5px 0;">🏮 초연 시공명리 연구소</h1>
            <p style="color: #555555; font-family: sans-serif; font-size: 12px; margin: 0;">{APP_VERSION}</p>
        </div>
        <hr style="margin: 10px 0 15px 0;">
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size: 15px; font-weight: 900; color: #000000; margin-bottom: 5px;'>📅 분석 기준 시점 선택</div>", unsafe_allow_html=True)
    kst_tz = pytz.timezone('Asia/Seoul')
    default_date_today = dt_mod.datetime.now(kst_tz).date()
    
    selected_target_date = st.date_input(
        "조회할 연/월/일 선택",
        value=st.session_state.get("main_target_calc_date", default_date_today),
        key="main_target_calc_date",
        on_change=stop_ai
    )
    st.caption(f"💡 현재 지정 기준일: **{selected_target_date.year}년 {selected_target_date.month}월 {selected_target_date.day}일**")
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    st.markdown("<div style='font-size: 17px; font-weight: 900; color: #000000; margin-bottom: 10px;'>📋 상담 분야 선택</div>", unsafe_allow_html=True)

    # 구버전(ver 50.5)과 동일한 4대 상담 분류 복원
    main_category = st.selectbox(
        "상담 분야를 선택하십시오:", 
        [
            "1. 개인 사주팔자 풀이 (종합)", 
            "2. 테마별 특성화 상담", 
            "3. 커플 연애/결혼운 (궁합) 풀이", 
            "4. 타 감명서 비교"
        ], 
        key="main_category", 
        on_change=stop_ai
    )

    u_product = "1-1. 사주팔자와 운세풀이 (기본)"

    if main_category == "1. 개인 사주팔자 풀이 (종합)":
        u_product = st.radio(
            "상세 분석 항목:", 
            [
                "1-1. 사주팔자와 운세풀이 (기본)", 
                "1-2. 올해 및 특정연도 운세 상세분석", 
                "1-3. 이번달 및 특정월 운세 상세분석", 
                "1-4. 특정 주간 및 특정일운 상세분석"
            ], 
            key="sub_cat_1", 
            on_change=stop_ai
        )
        if u_product == "1-2. 올해 및 특정연도 운세 상세분석":
            curr_yr_val = dt_mod.datetime.now(pytz.timezone('Asia/Seoul')).year
            st.number_input("📅 분석할 특정 연도 (기본값: 올해)", min_value=1900, max_value=2050, value=curr_yr_val, key="target_year_input")

    elif main_category == "2. 테마별 특성화 상담":
        u_product = st.radio(
            "특성화 상품 선택:", 
            [
                "2-1. 재물운 특화 분석", 
                "2-2. 직업/진학운 특화 분석", 
                "2-3. 연애/결혼운 특화 분석", 
                "2-4. 건강운 특화 분석", 
                "2-5. 이사 및 방위 특화 분석"
            ], 
            key="sub_cat_2", 
            on_change=stop_ai
        )

    elif main_category == "3. 커플 연애/결혼운 (궁합) 풀이":
        u_product = st.radio(
            "상세 분석 항목:", 
            [
                "3-1. 연애/결혼운 (궁합) 풀이", 
                "3-2. 결혼 택일", 
                "3-3. 출산 택일"
            ], 
            key="sub_cat_3", 
            on_change=stop_ai
        )

    else:
        u_product = st.radio(
            "비교 분석 대상:", 
            [
                "4-1. 전통 명리 vs 시공명리 대조", 
                "4-2. 전통 궁합 vs 시공명리 궁합 대조"
            ], 
            key="sub_cat_4", 
            on_change=stop_ai
        )

    st.markdown("---")

    # 👤 신청인 기본 정보
    u_box = st.container()
    with u_box:
        st.subheader("👤 신청인 기본 정보")
        name = st.text_input("이름", value=st.session_state.get("u_n", ""), placeholder="홍길동", key="u_n")
        gender = st.selectbox("성별", ["남성", "여성"], key="u_g")
        u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
        u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")

        col_y, col_m, col_d = st.columns(3)
        with col_y: b_year = st.number_input("년도", 1900, 2050, value=st.session_state.get("s_y", 1980), key="s_y")
        with col_m: b_month = st.number_input("월", 1, 12, value=st.session_state.get("s_m", 1), key="s_m")
        with col_d: b_day = st.number_input("일", 1, 31, value=st.session_state.get("s_d", 1), key="s_d")
        
        curr_t_val = st.session_state.get("s_t", idx_list[0])
        t_idx = idx_list.index(curr_t_val) if curr_t_val in idx_list else 0
        b_time = st.selectbox("태어난 시간", idx_list, index=t_idx, key="s_t_select")
        st.session_state["s_t"] = b_time

    # 👥 2인 전용 상품(궁합, 택일) 시 상대방 정보 입력
    is_2person = (main_category == "3. 커플 연애/결혼운 (궁합) 풀이") or (u_product == "4-2. 전통 궁합 vs 시공명리 궁합 대조")
    if is_2person:
        st.markdown("<hr style='border:1px dashed #C62828; margin:15px 0;'>", unsafe_allow_html=True)
        st.subheader("💕 상대방 기본 정보")
        p_name = st.text_input("상대방 이름", value=st.session_state.get("p_n", ""), placeholder="이영희", key="p_n")
        p_gender_default = "여성" if gender == "남성" else "남성"
        p_gender = st.selectbox("상대방 성별", ["남성", "여성"], index=["남성", "여성"].index(p_gender_default), key="p_g")
        p_marital = st.selectbox("상대방 혼인여부", ["미혼", "기혼", "돌싱"], index=0, key="p_m_stat")
        p_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], index=0, key="p_c")

        p_col1, p_col2, p_col3 = st.columns(3)
        p_y = p_col1.number_input("년(상대)", 1900, 2050, value=st.session_state.get('p_y_in', 1985), key="p_y_in")
        p_m = p_col2.number_input("월(상대)", 1, 12, value=st.session_state.get('p_m_in', 1), key="p_m_in")
        p_d = p_col3.number_input("일(상대)", 1, 31, value=st.session_state.get('p_d_in', 1), key="p_d_in")
        p_t = st.selectbox("태어난 시간(상대)", idx_list, index=0, key="p_t_select_key")

    st.markdown("---")

    if st.button("✨ [초연 시공명리 풀이 가동]", key="btn_run", use_container_width=True, type="primary"):
        st.session_state['app_running'] = True

    if st.button("🖨️ 풀이 결과 인쇄 / PDF 저장", key="btn_print", use_container_width=True, type="secondary"):
        components.html("<script>window.parent.print();</script>", height=0)

# ==============================================================================
# 3. 메인 화면 범용 연산 및 AI 통변 모듈 연동부
# ==============================================================================
if st.session_state.get('app_running', False):
    klc = KoreanLunarCalendar()

    b_year = st.session_state.get("s_y", 1980)
    b_month = st.session_state.get("s_m", 1)
    b_day = st.session_state.get("s_d", 1)

    if "음력" in u_cal:
        is_leap = True if "윤달" in u_cal else False
        klc.setLunarDate(int(b_year), int(b_month), int(b_day), is_leap)
        sol_y, sol_m, sol_d = klc.solarYear, klc.solarMonth, klc.solarDay
        lun_y, lun_m, lun_d = int(b_year), int(b_month), int(b_day)
        leap_str = "윤달" if is_leap else "평달"
    else:
        klc.setSolarDate(int(b_year), int(b_month), int(b_day))
        sol_y, sol_m, sol_d = int(b_year), int(b_month), int(b_day)
        lun_y, lun_m, lun_d = klc.lunarYear, klc.lunarMonth, klc.lunarDay
        leap_str = "윤달" if klc.isIntercalation else "평달"
        
    curr_year = selected_target_date.year
    curr_m = selected_target_date.month
    curr_d = selected_target_date.day
    
    age = curr_year - sol_y + 1
    p_icon = "♂️" if gender == "남성" else "♀️"
    today_str = selected_target_date.strftime("%Y년 %m월 %d일")

    with st.spinner(f"⏳ [{u_product.strip()}] 시공명리 연산 및 정밀 통변 가동 중..."):
        # 기초 역산 데이터 준비
        g_res = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day))
        d_pillar = g_res[2] if len(g_res) > 2 else "甲子"
        y_pillar = g_res[0] if len(g_res) > 0 else "甲子"
        m_pillar = g_res[1] if len(g_res) > 1 else "甲子"
        
        ds_hanja = engine.K2H_GAN.get(d_pillar[0], d_pillar[0])
        hs, ds, ms, ys = "甲", d_pillar[0], m_pillar[0], y_pillar[0]
        hb, db, mb, yb = "子", d_pillar[1], m_pillar[1], y_pillar[1]
        
        base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
        adj_mins = engine.get_total_time_adjustment(base_dt)
        utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
        
        order_dir = 1 if (engine.GAN.index(ys) % 2 == 0) == (gender == '남성') else -1
        calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
        
        counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
        for c in [hs, ds, ms, ys, hb, db, mb, yb]:
            oh = engine.get_color(c)
            if oh in counts: counts[oh] += 1
        
        guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 해','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
        guiin_str = guiin_map.get(ds_hanja, '없음')
        curr_y_ji = engine.JI[(curr_year - 1984) % 60 % 12]
        
        n_gong = engine.calculate_gongmang(ys, yb) or "-"
        i_gong = engine.calculate_gongmang(ds, db) or "-"
        cur_samjae = engine.get_samjae(yb, curr_y_ji)
        
        sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
        lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
        
        cover_html = html_views.get_personal_cover(APP_VERSION, p_icon, name, sol_str_fmt, lun_str_fmt, b_time, today_str)
        info_h = html_views.get_info_header(p_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, b_time)
        table_html = html_views.generate_saju_table_data([hs, ds, ms, ys], [hb, db, mb, yb], ds, gender, engine)
        master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, "#C62828", cur_samjae)
        intro_html = html_views.get_intro_html()
        
        choyeon_db = load_choyeon_db()
        w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{db}".strip()
        w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
        i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
        struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
        golden_text_html = html_views.get_golden_text(name, w_val, i_val, struct_data[0], struct_data[1], struct_data[2])

        closing_html = html_views.get_closing_html(name)            

        part_1_fact = str(info_h or "") + str(table_html or "") + str(master_bar_html or "")
        part_2_intro = str(intro_html or "")
        part_3_golden = str(golden_text_html or "")
        part_5_closing = str(closing_html or "")

        gyukgook, gyukgook_detail = engine.get_gyukgook_detailed(ds, ys, ms, hs, mb)
        
        saju_fact_summary = f"""
- 내담자 명조: 년주({ys}{yb}), 월주({ms}{mb}), 일주({ds}{db}), 시주({hs}{hb})
- 격국 및 용신 팩트: {gyukgook_detail}
- 원국 오행 분포: 목:{counts['목']}, 화:{counts['화']}, 토:{counts['토']}, 금:{counts['금']}, 수:{counts['수']}
- 공망 궁위 팩트: [년지공망] {n_gong} / [일지공망] {i_gong}
- 삼재 여부: {cur_samjae}
"""

        prompt_data = {
            "name": name, "age": age, "gender": gender, "marital": u_marital,
            "age_prompt": engine.get_age_prompt(age), 
            "gender_prompt": engine.get_gender_prompt(gender), 
            "marital_prompt": engine.get_marital_prompt(gender, u_marital), 
            "yukchin_rule": engine.get_yukchin_rule(gender, u_marital),
            "saju_fact_summary": saju_fact_summary,
            "dw_fact_str": "대운 흐름 가동 중",
            "samhyung_fact_str": engine.check_samhyung_facts([yb, mb, db, hb]),
            "hang_un_vaults_str": "묘고 입고/개고 분석",
            "dw_che": "대운 시공간 무대",
            "ds": ds, "db": db, "gyukgook_detail": gyukgook_detail,
            "year_gongmang": n_gong, "day_gongmang": i_gong,
            "oheng_counts_str": f"목:{counts['목']} 화:{counts['화']} 토:{counts['토']} 금:{counts['금']} 수:{counts['수']}",
            "hap_chung_hyoung_pa_hae": "천간합충 및 지지합충형해파",
            "won_guk_vaults_str": "묘고 작용",
            "shinsal_str": "일반신살",
            "cheon_eul": guiin_str,
            "samjae_str": cur_samjae,
            "dw_g_cur": "丙", "dw_j_cur": "午", "curr_year": curr_year,
            "target_year": st.session_state.get('target_year_input', curr_year),
            "curr_m": curr_m, "target_date_str": selected_target_date.strftime("%Y년 %m월 %d일")
        }
        
        class SafeDict(dict):
            def __missing__(self, key): return '{' + key + '}'
        
        # 상품별 한글 변수명 1:1 매칭 바인딩
        target_prompt_map = {
            "1-1. 사주팔자와 운세풀이 (기본)": "프롬프트_1_1_기본",
            "1-2. 올해 및 특정연도 운세 상세분석": "프롬프트_1_2_연도운",
            "1-3. 이번달 및 특정월 운세 상세분석": "프롬프트_1_3_월운",
            "1-4. 특정 주간 및 특정일운 상세분석": "프롬프트_1_4_일운",
            "2-1. 재물운 특화 분석": "프롬프트_2_1_재물운",
            "2-2. 직업/진학운 특화 분석": "프롬프트_2_2_직업운",
            "2-3. 연애/결혼운 특화 분석": "프롬프트_2_3_연애운",
            "2-4. 건강운 특화 분석": "프롬프트_2_4_건강운",
            "2-5. 이사 및 방위 특화 분석": "프롬프트_2_5_이사방위",
            "3-1. 연애/결혼운 (궁합) 풀이": "프롬프트_3_1_궁합",
            "3-2. 결혼 택일": "프롬프트_3_2_결혼택일",
            "3-3. 출산 택일": "프롬프트_3_3_출산택일",
            "4-1. 전통 명리 vs 시공명리 대조": "프롬프트_4_1_사주대조",
            "4-2. 전통 궁합 vs 시공명리 궁합 대조": "프롬프트_4_2_궁합대조"
        }

        prompt_var_name = target_prompt_map.get(u_product, "프롬프트_1_1_기본")
        target_prompt = getattr(prompts, prompt_var_name, getattr(prompts, "프롬프트_1_1_기본", ""))
        
        formatted_prompt = target_prompt.format_map(SafeDict(prompt_data))
        raw_response = call_gemini_api(formatted_prompt)
        
        if raw_response and isinstance(raw_response, str):
            cleaned = raw_response.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
            ai_output_html = html_views.format_ai_text_to_html(cleaned)
        else:
            ai_output_html = "<p style='padding:20px;'>분석 결과를 불러오지 못했습니다.</p>"

        master_composite_report = part_1_fact + part_2_intro + part_3_golden + f"<div style='margin-top:20px;'>{ai_output_html}</div>" + part_5_closing

        st.markdown(html_views.get_final_report_box(master_composite_report), unsafe_allow_html=True)
