# ==============================================================================
# app.py (ver 82.0 Master - 사이드바 100% 원상복구 및 관리자 스텔스 무소음 공장)
# ==============================================================================
import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from datetime import datetime
from korean_lunar_calendar import KoreanLunarCalendar
import os
import re
import time
import json
import math
import pytz
import sys
import importlib
from google import genai

import engine
import prompts
import html_views

# 💡 [영업부 호출]
from pipeline_manager import run_pipeline_router
# URL이 ?mode=admin이고 app_running=True일 때는 얘가 return 되어 아래 코드가 실행됨!
run_pipeline_router()

APP_VERSION = "ver 82.0 Master"
st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# 🧨 [진녹색 폰트 및 선 강제 초기화] 🧨
st.markdown("""
<style>
    span[style*="darkgreen"], span[style*="#006400"], span[style*="#008000"], span[style*="17px"], span[style*="1px solid"] {
        color: #2D3748 !important; font-size: 15px !important; border: none !important; background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

if hasattr(html_views, 'get_global_css'):
    st.markdown(html_views.get_global_css(), unsafe_allow_html=True)

idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]

if 'app_running' not in st.session_state: st.session_state['app_running'] = False

@st.cache_data
def load_choyeon_db():
    file_path = 'choyeon_db.json'
    if not os.path.exists(file_path): return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception: return {}
choyeon_db = load_choyeon_db()

try: _gemini_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as _api_e: _gemini_client = None; st.error(f"🚨 Gemini API 키 오류: {_api_e}")

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
    sys_role = engine.get_master_system_prompt()
    return get_ai_response(sys_role, prompt_text, model_name='gemini-2.5-flash')

extract_ganji = engine.extract_ganji
get_oh_class = engine.get_oh_class
kst_tz = pytz.timezone('Asia/Seoul')

# ------------------------------------------------------------------------------
# [도우미 함수 복구]
# ------------------------------------------------------------------------------
def do_auto_fill_user():
    st.session_state['app_running'] = False
    u_ry, u_rm, u_rd, u_rt = st.session_state.get("u_ry_rev", ""), st.session_state.get("u_rm_rev", ""), st.session_state.get("u_rd_rev", ""), st.session_state.get("u_rt_rev", "")
    _ry, _rm, _rd = extract_ganji(u_ry), extract_ganji(u_rm), extract_ganji(u_rd)
    if not _ry and not _rm and not _rd: return
    if len(_ry) >= 2 and len(_rm) >= 2 and len(_rd) >= 2:
        ry_h, rm_h, rd_h = engine.K2H_GAN.get(_ry[0], _ry[0]) + engine.K2H_JI.get(_ry[1], _ry[1]), engine.K2H_GAN.get(_rm[0], _rm[0]) + engine.K2H_JI.get(_rm[1], _rm[1]), engine.K2H_GAN.get(_rd[0], _rd[0]) + engine.K2H_JI.get(_rd[1], _rd[1])
        rt_ji = engine.K2H_JI.get(u_rt[-1], u_rt[-1]) if u_rt else None
        target_date_val = st.session_state.get('main_target_date_picker', dt_mod.date.today())
        matched_results = engine.search_dates_by_ganji(ry_h, rm_h, rd_h, rt_ji, target_date_val.year)
        if matched_results:
            st.session_state.update({'rev_matches_user': matched_results, 's_y': matched_results[0]["y"], 's_m': matched_results[0]["m"], 's_d': matched_results[0]["d"], 's_t': matched_results[0]["t"], 's_t_select': matched_results[0]["t"]})

def do_auto_fill_partner():
    st.session_state['app_running'] = False
    p_ry, p_rm, p_rd, p_rt = st.session_state.get("p_ry_rev", ""), st.session_state.get("p_rm_rev", ""), st.session_state.get("p_rd_rev", ""), st.session_state.get("p_rt_rev", "")
    _p_ry, _p_rm, _p_rd = extract_ganji(p_ry), extract_ganji(p_rm), extract_ganji(p_rd)
    if not _p_ry and not _p_rm and not _p_rd: return
    if len(_p_ry) >= 2 and len(_p_rm) >= 2 and len(_p_rd) >= 2:
        p_ry_h, p_rm_h, p_rd_h = engine.K2H_GAN.get(_p_ry[0], _p_ry[0]) + engine.K2H_JI.get(_p_ry[1], _p_ry[1]), engine.K2H_GAN.get(_p_rm[0], _p_rm[0]) + engine.K2H_JI.get(_p_rm[1], _p_rm[1]), engine.K2H_GAN.get(_p_rd[0], _p_rd[0]) + engine.K2H_JI.get(_p_rd[1], _p_rd[1])
        p_rt_ji = engine.K2H_JI.get(p_rt[-1], p_rt[-1]) if p_rt else None
        target_date_val = st.session_state.get('main_target_date_picker', dt_mod.date.today())
        matched_results = engine.search_dates_by_ganji(p_ry_h, p_rm_h, p_rd_h, p_rt_ji, target_date_val.year)
        if matched_results:
            st.session_state.update({'rev_matches_partner': matched_results, 'p_y_in': matched_results[0]["y"], 'p_m_in': matched_results[0]["m"], 'p_d_in': matched_results[0]["d"], 'p_t_key': matched_results[0]["t"], 'p_t_select': matched_results[0]["t"]})

# ==============================================================================
# 🛡️ [공장 자동화 스텔스 모드 vs 오리지널 수동 모드 분기]
# ==============================================================================
is_admin_mode = st.session_state.get('admin_proc_id') is not None

if is_admin_mode:
    # 관리자 패널(pipeline_manager)이 렌더링 된 상태이므로, app.py의 사이드바는 스킵
    # (절대 stSidebar를 CSS로 숨기면 안됨. 관리자 비밀번호 창도 숨겨지기 때문!)
    selected_target_date = st.session_state.get('target_date', dt_mod.datetime.now(kst_tz).date())
    main_category = st.session_state.get('main_category', '1. 사주팔자 및 운세 풀이 (종합)')
    u_product = st.session_state.get('sub_category_1', '1-1. 사주팔자 및 운세 분석')
    if "2." in main_category: u_product = st.session_state.get('sub_category_2', '2-1. 재물운 특화 분석')
    elif "3." in main_category: u_product = st.session_state.get('sub_category_3', '3-1. 커플 연애/결혼운 (궁합) 분석')
    elif "4." in main_category: u_product = st.session_state.get('sub_category_4', '4-1. 타 감명서 비교 (사주)')
    
    name, gender, u_marital, u_cal = st.session_state.get('u_n', '고객'), st.session_state.get('u_g', '여성'), st.session_state.get('u_m_stat', '선택'), st.session_state.get('u_c', '양력')
    b_year, b_month, b_day, b_time = st.session_state.get('s_y', 1980), st.session_state.get('s_m', 1), st.session_state.get('s_d', 1), st.session_state.get('s_t', '시간 모름')
    is_1person = not ("3-1." in u_product or "4-2." in u_product)
    is_2person = ("3-1." in u_product or "4-2." in u_product)
    
    f_name, f_gender, f_marital, f_cal = st.session_state.get('f_n', '상대방'), st.session_state.get('f_g', '남성'), st.session_state.get('f_m_stat', '선택'), st.session_state.get('f_c', '양력')
    f_y, f_m, f_d, f_t = st.session_state.get('p_y_in', 1980), st.session_state.get('p_m_in', 1), st.session_state.get('p_d_in', 1), st.session_state.get('p_t_key', '시간 모름')

else:
    # 🚨 [오리지널 수동 모드] 박사님의 연구용 사이드바 100% 완전 복구 🚨
    with st.sidebar:
        def stop_ai(): st.session_state['app_running'] = False
        st.markdown(f"<div style='text-align:center;'><h1 style='font-size: 20px;'>🏮 초연 시공명리 연구소</h1><p>{APP_VERSION}</p></div><hr>", unsafe_allow_html=True)
        selected_target_date = st.date_input("조회할 연/월/일 선택", value=st.session_state.get('target_date', dt_mod.datetime.now(kst_tz).date()), on_change=stop_ai, key="main_target_date_picker")
        st.markdown("<hr>", unsafe_allow_html=True)

        main_category = st.selectbox("어떤 상담을 원하십니까?", ["1. 사주팔자 및 운세 풀이 (종합)", "2. 테마별 특성화 상담", "3. 연애/결혼운 (궁합) 풀이", "4. 타 감명서 비교"], key="main_category", on_change=stop_ai)
        u_product = "1-1. 사주팔자 및 운세 분석"
        if "1." in main_category: u_product = st.radio("상세 분석 항목:", ["1-1. 사주팔자 및 운세 분석", "1-2. 올 해 (특정 년도) 운세 상세분석", "1-3. 이번 달 (특정 월) 운세 상세분석", "1-4. 이번(특정) 주간/일 운세 상세분석"], key="sub_category_1", on_change=stop_ai)
        elif "2." in main_category: u_product = st.radio("특성화 분석 항목:", ["2-1. 재물운 특화 분석", "2-2. 직업/진학운 특화 분석", "2-3. 커플 연애/결혼운 특화 분석", "2-4. 건강운 특화 분석", "2-5. 이사/개업 택일 특화 분석"], key="sub_category_2", on_change=stop_ai)
        elif "3." in main_category: u_product = st.radio("상세 분석 항목:", ["3-1. 커플 연애/결혼운 (궁합) 분석", "3-2. 결혼 택일 특화 분석", "3-3. 출산 택일 특화 분석"], key="sub_category_3", on_change=stop_ai)
        elif "4." in main_category: u_product = st.radio("타 감명서 비교 항목:", ["4-1. 타 감명서 비교 (사주)", "4-2. 타 감명서 비교 (궁합)"], key="sub_category_4", on_change=stop_ai)
        
        if "u_g" not in st.session_state: st.session_state["u_g"] = "남성"
        if "f_g" not in st.session_state: st.session_state["f_g"] = "여성"
        def sync_p(): st.session_state["f_g"] = "남성" if st.session_state.get("u_g", "남성")=="여성" else "여성"; stop_ai()
        def sync_u(): st.session_state["u_g"] = "여성" if st.session_state.get("f_g", "여성")=="남성" else "남성"; stop_ai()

        with st.expander("🔍 신청인 사주간지 역산", expanded=False):
            col_g1, col_g2 = st.columns(2); col_g3, col_g4 = st.columns(2)
            with col_g1: u_ry = st.text_input("년주", key="u_ry_rev", on_change=stop_ai)
            with col_g2: u_rm = st.text_input("월주", key="u_rm_rev", on_change=stop_ai)
            with col_g3: u_rd = st.text_input("일주", key="u_rd_rev", on_change=stop_ai)
            with col_g4: u_rt = st.text_input("시주", key="u_rt_rev", on_change=stop_ai)
            st.button("🔍 신청인 자동입력", use_container_width=True, key="btn_u_rev", on_click=do_auto_fill_user)

        with st.container():
            st.markdown("<b>👤 신청인 기본 정보</b>", unsafe_allow_html=True)
            name = st.text_input("이름", value=st.session_state.get("u_n", ""), key="u_n", on_change=stop_ai)
            gender = st.selectbox("성별", ["남성", "여성"], key="u_g", on_change=sync_p)
            u_marital = st.selectbox("혼인여부", ["미혼", "기혼", "돌싱"], key="u_m_stat", on_change=stop_ai)
            u_cal = st.selectbox("달력", ["양력", "음력", "음력(윤달)"], key="u_c", on_change=stop_ai)
            col_y, col_m, col_d = st.columns(3)
            with col_y: b_year = st.number_input("년도", 1926, 2046, value=st.session_state.get("s_y", 1964), key="s_y", on_change=stop_ai)
            with col_m: b_month = st.number_input("월", 1, 12, value=st.session_state.get("s_m", 1), key="s_m", on_change=stop_ai)
            with col_d: b_day = st.number_input("일", 1, 31, value=st.session_state.get("s_d", 15), key="s_d", on_change=stop_ai)
            curr_t_val = st.session_state.get("s_t", idx_list[0])
            b_time = st.selectbox("태어난 시간", idx_list, index=idx_list.index(curr_t_val) if curr_t_val in idx_list else 0, key="s_t_select", on_change=stop_ai)
            st.session_state["s_t"] = b_time

        is_1person = not ("3-1." in u_product or "4-2." in u_product)
        is_2person = ("3-1." in u_product or "4-2." in u_product)
        
        if is_1person:
            if "1-2." in u_product: st.number_input("📅 분석 연도", min_value=1900, max_value=2050, value=dt_mod.datetime.now(pytz.timezone('Asia/Seoul')).year, key="target_year_input", on_change=stop_ai)
            elif "1-4." in u_product: st.date_input("일운 기준일", value=selected_target_date, key="daily_calc_date", on_change=stop_ai)
            elif "2-1." in u_product: st.text_input("💰 고민되는 금전 문제는?", key="wealth_goal", on_change=stop_ai)
            elif "2-2." in u_product: st.text_input("💼 고민되는 직업/진학 분야는?", key="career_goal", on_change=stop_ai)
            elif "2-3." in u_product: st.text_input("💘 고민되는 연애/이성 문제는?", key="love_goal", on_change=stop_ai)
            elif "2-4." in u_product: st.text_input("🩺 좋지 않은 건강 부위는?", key="health_goal", on_change=stop_ai)
            elif "4-1." in u_product: st.text_area("비교할 타 감명서 원문을 넣어 주세요.", key="text_4_1")

        if is_2person:
            with st.container():
                st.markdown("<b>💕 상대방 기본 정보</b>", unsafe_allow_html=True)
                f_name = st.text_input("상대방 이름", value=st.session_state.get("f_n", ""), key="f_n", on_change=stop_ai)
                f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_g", on_change=sync_u)
                f_marital = st.selectbox("상대방 혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="f_m_stat", on_change=stop_ai)
                f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c", on_change=stop_ai)
                p_col1, p_col2, p_col3 = st.columns(3)
                with p_col1: f_y = st.number_input("년도(상대)", 1900, 2050, value=st.session_state.get("p_y_in", 1967), key="p_y_in", on_change=stop_ai)
                with p_col2: f_m = st.number_input("월(상대)", 1, 12, value=st.session_state.get("p_m_in", 9), key="p_m_in", on_change=stop_ai)
                with p_col3: f_d = st.number_input("일(상대)", 1, 31, value=st.session_state.get("p_d_in", 24), key="p_d_in", on_change=stop_ai)
                curr_p_t = st.session_state.get("p_t_key", idx_list[0])
                f_t = st.selectbox("태어난 시간(상대)", idx_list, index=idx_list.index(curr_p_t) if curr_p_t in idx_list else 0, key="p_t_select", on_change=stop_ai)
                st.session_state["p_t_key"] = f_t

        st.markdown("---")
        if st.button("✨ [초연 시공명리 풀이 가동]", key="btn_run", use_container_width=True, type="primary"): st.session_state['app_running'] = True
        if st.button("🖨️ 인쇄/PDF 저장", key="btn_print", use_container_width=True, type="secondary"): components.html("<script>window.parent.print();</script>", height=0)

# ==============================================================================
# 3. 백그라운드 공장 무소음 가동 (화면 전환 없이 그 자리에서 돌아감)
# ==============================================================================
if st.session_state.get('app_running', False):
    klc = KoreanLunarCalendar()
    b_year, b_month, b_day = st.session_state.get("s_y", 1980), st.session_state.get("s_m", 1), st.session_state.get("s_d", 1)

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
        
    curr_year, curr_m, curr_d = selected_target_date.year, selected_target_date.month, selected_target_date.day
    age = curr_year - sol_y + 1
    p_icon = "♂️" if gender == "남성" else "♀️"
    today_str = selected_target_date.strftime("%Y년 %m월 %d일")

    def extract_time(time_str):
        if "모름" in time_str: return 0, 0
        match = re.search(r'(\d{2}):(\d{2})', time_str)
        return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

    # 💡 [무소음 스피너] 관리자 모드일 때는 화면 하단에서 보일랑 말랑 조용히 돕니다.
    spinner_msg = f"⏳ [공장 스텔스 모드] {name}님의 사주를 정밀 분석 중입니다. 완료 시 서랍장이 자동으로 열립니다..." if is_admin_mode else f"⏳ [{u_product.strip()}] 시공명리 연산 가동 중..."

    with st.spinner(spinner_msg):
        h, m = extract_time(b_time)
        is_lunar_val, is_leap_val = ("음력" in u_cal), ("윤달" in u_cal)
        try:
            g_res = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)
            d_pillar, m_pillar, y_pillar = g_res[2], g_res[1], g_res[0]
        except: y_pillar, m_pillar, d_pillar = "甲子", "甲子", "甲子"
        try:
            t_res = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
            if t_res and len(t_res) >= 2: y_pillar, m_pillar = t_res[0], t_res[1]
        except: pass
        
        ds_hanja = engine.K2H_GAN.get(d_pillar[0], d_pillar[0])
        t_gan, t_ji = "?", "?"
        if "모름" not in b_time:
            match = re.search(r'\((.*?)\)', b_time)
            raw_ji = match.group(1).replace('朝', '').replace('夜', '') if match else "子"
            t_ji = engine.K2H_JI.get(raw_ji, raw_ji)
            gan_arr, ji_arr = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'], ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            if ds_hanja in gan_arr and t_ji in ji_arr:
                d_idx, j_idx = gan_arr.index(ds_hanja), ji_arr.index(t_ji)
                t_gan = gan_arr[((d_idx % 5) * 2 + j_idx) % 10]
         
        gans = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]]
        jjis = [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
        hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
        hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]
        
        ys_idx = engine.GAN.index(ys) if ys in engine.GAN else 0
        order_dir = 1 if (ys_idx % 2 == 0) == (gender == '남성') else -1
        
        base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
        utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=engine.get_total_time_adjustment(base_dt))
        calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
        
        counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
        for c in gans + jjis:
            oh = engine.get_color(c)
            if oh in counts: counts[oh] += 1
        
        guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 미','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
        guiin_str = guiin_map.get(ds_hanja, '없음')
        cur_samjae = engine.get_samjae(yb, engine.JI[(curr_year - 1984) % 60 % 12])
        n_gong = engine.calculate_gongmang(ys, yb) or "-"
        i_gong = engine.calculate_gongmang(ds, db) or "-"
        
        sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
        lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
        time_str_fmt = f"{b_time}" if b_time != "시간 모름" else "시간 미상"
        
        report_title = "🏮 초연 시공명리 정밀 감명서"
        u_icon_str = f"{p_icon}" 
        cover_html = html_views.get_personal_cover(APP_VERSION, report_title, u_icon_str, name, sol_str_fmt, lun_str_fmt, time_str_fmt, today_str)
        info_h = html_views.get_info_header(p_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, time_str_fmt)
        table_html = html_views.generate_saju_table_data(gans, jjis, ds, gender, engine)
        master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, "#555", cur_samjae)
        intro_html = html_views.get_intro_html()

        # 대운 연산
        c_idx = engine.GAN.index(ms) if ms in engine.GAN else 0
        j_idx = engine.JI.index(mb) if mb in engine.JI else 0
        cur_dw_idx = max(0, (age - calc_d) // 10)
        dw_g_cur = engine.GAN[(c_idx + (cur_dw_idx+1)*order_dir)%10]
        dw_j_cur = engine.JI[(j_idx + (cur_dw_idx+1)*order_dir)%12]
        daewun_data_list = []
        for i in range(10):
            val = i * 10 + calc_d
            c_hangul = engine.GAN[(c_idx + (i + 1) * order_dir) % 10] if ms in engine.GAN else "-"
            j_hangul = engine.JI[(j_idx + (i + 1) * order_dir) % 12] if mb in engine.JI else "-"
            daewun_data_list.append({
                "age_range": f"{val}~{val+9}세", "ss_gan": engine.get_ss(ds_hanja, c_hangul),
                "c_hanja": engine.K2H_GAN.get(c_hangul, c_hangul), "c_hangul": c_hangul,
                "j_hanja": engine.K2H_JI.get(j_hangul, j_hangul), "j_hangul": j_hangul,
                "ss_ji": engine.get_ss(ds_hanja, j_hangul), "un_sung": engine.get_unsung(ds_hanja, j_hangul),
                "y_shinsal": engine.get_12_shinsal(yb, j_hangul), "d_shinsal": engine.get_12_shinsal(db, j_hangul),
                "is_current": (val <= age < val + 10), "is_first": (i == 0)
            })
        un_html = html_views.generate_daewun_layout(daewun_data_list, "순행" if order_dir == 1 else "역행", calc_d, get_oh_class)

        w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{db}".strip()
        w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
        i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
        struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
        gyukgook, gyukgook_detail = engine.get_gyukgook_detailed(ds, ys, ms, hs, mb)
        golden_text_html = html_views.get_golden_text(name, w_val, i_val, struct_data[0], struct_data[1], struct_data[2], mb=mb, gyuk_name=gyukgook)
        closing_html = html_views.get_closing_html(name)            

        part_1_fact = str(info_h or "") + str(table_html or "") + str(master_bar_html or "")
        part_2_intro = str(intro_html or "")
        part_3_golden = str(golden_text_html or "")
        part_5_closing = str(closing_html or "")

        saju_fact_summary = f"- 명조: 년주({ys}{yb}), 월주({ms}{mb}), 일주({ds}{db}), 시주({hs}{hb})\n- 격국: {gyukgook_detail}\n"

        target_year_val = curr_year
        prompt_data = {
            "name": name, "age": age, "gender": gender, "marital": u_marital,
            "saju_fact_summary": saju_fact_summary, "dw_g_cur": dw_g_cur, "dw_j_cur": dw_j_cur, 
            "dw_fact_str": f"현재 {dw_g_cur}{dw_j_cur}대운 가동 중",
            "ds": ds, "db": db, "gyukgook_detail": gyukgook_detail,
            "oheng_counts_str": f"목:{counts['목']} 화:{counts['화']} 토:{counts['토']} 금:{counts['금']} 수:{counts['수']}",
            "curr_year": target_year_val, "target_year": target_year_val, "curr_m": curr_m
        }

        class SafeDict(dict):
            def __missing__(self, key): return '{' + key + '}'
        
        prompt_var_name = "프롬프트_1_1_기본"
        target_prompt = getattr(prompts, prompt_var_name, getattr(prompts, "프롬프트_1_1_기본", ""))
        formatted_prompt = target_prompt.format_map(SafeDict(prompt_data))
        
        # 💡 [AI 조련] 관리자 패널에서 입력한 지시사항이 있으면 즉시 주입!
        ai_feedback = st.session_state.get('ai_feedback_prompt', '').strip()
        if ai_feedback:
            formatted_prompt += f"\n\n[🔥 박사님의 특별 수정 지시사항 🔥]\n{ai_feedback}\n위 지시사항을 100% 반영하여 기존과 완전히 다른 맞춤형 문구로 재생성하시오."

        raw_response = call_gemini_api(formatted_prompt)
        
        if raw_response and isinstance(raw_response, str):
            clean_raw = raw_response.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
            ai_output_html = html_views.format_ai_text_to_html(clean_raw)
        else:
            ai_output_html = "<p style='padding:20px;'>분석 결과를 불러오지 못했습니다.</p>"

        def sub_marker(text, marker_name, table_code):
            pattern = r'\[\s*\*?\*?\s*' + marker_name + r'\s*\*?\*?\s*\]'
            return re.sub(pattern, table_code, text, flags=re.IGNORECASE)

        # 최종 HTML 조립
        formatted_ai = sub_marker(ai_output_html, 'DAEWUN_TABLE_HERE', un_html if 'un_html' in locals() and un_html else "")
        master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
        final_render_html = html_views.get_final_report_box(master_comp)

        final_render_html = str(final_render_html).strip()
        final_render_html = final_render_html.replace("darkgreen", "#2D3748").replace("#006400", "#2D3748").replace("#008000", "#2D3748")
        final_render_html = final_render_html.replace("17px", "15px").replace("1px solid", "0px solid")

    # =========================================================================
    # 📦 [공장 생산 완료] ➔ 스텔스 완료 처리 (URL 변경 없음, 그 자리에서 서랍장 오픈)
    # =========================================================================
    if is_admin_mode:
        gid = st.session_state['admin_proc_id']
        st.session_state[f'html_{gid}'] = final_render_html
        st.session_state['app_running'] = False
        
        # 💡 [핵심] URL 변경(mode=factory 등) 없이 그냥 rerun()만 호출하면 
        # 위에 있는 pipeline_manager의 render_admin_panel()이 서랍장 2,3번을 엽니다!
        st.rerun()
    else:
        # 🚨 박사님 단독 수동 연구 모드일 때는 정상적으로 화면 출력!
        if 'cover_html' in locals() and cover_html:
            safe_cover = re.sub(r'\n\s+', '\n', cover_html)
            st.markdown(safe_cover, unsafe_allow_html=True)
        st.markdown(final_render_html, unsafe_allow_html=True)
