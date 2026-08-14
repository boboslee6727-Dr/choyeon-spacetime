# ==============================================================================
# app.py (ver 72.6 Master - 간지 역산 콜백 & AI 완전 통제 최종본)
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

# ==============================================================================
# 1. 초기 설정 및 공통 함수
# ==============================================================================
APP_VERSION = "ver 72.6 Master"
st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# 전역 CSS 적용
if hasattr(html_views, 'get_global_css'):
    st.markdown(html_views.get_global_css(), unsafe_allow_html=True)

idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", 
    "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", 
    "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", 
    "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]

if 'app_running' not in st.session_state: 
    st.session_state['app_running'] = False

@st.cache_data
def load_choyeon_db():
    file_path = 'choyeon_db.json'
    if not os.path.exists(file_path): return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception: return {}

choyeon_db = load_choyeon_db()

# ==============================================================================
# 1.5. AI 및 간지 역산 콜백 함수
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
    sys_role = getattr(prompts, '공통_시스템_헤더', None)
    if sys_role is None:
        sys_role = getattr(prompts, 'COMMON_SYSTEM_HEADER', "당신은 초연 시공명리 전문가입니다. 팩트 데이터를 바탕으로 정확하게 분석하세요.")
    return get_ai_response(sys_role, prompt_text, model_name='gemini-2.5-flash')

def extract_ganji(text):
    if not text: return ""
    return re.sub(r'[^가-힣一-龥]', '', text)

def get_oh_class(ganji):
    oh = engine.get_color(ganji)
    return f"color-{oh}" if oh != '무' else ""

# 🎯 [신청인] 사주간지 역산 전용 콜백 함수 (AI 구동 완전 차단 + 위젯 수치 즉시 반영)
def do_auto_fill_user():
    st.session_state['app_running'] = False  # 🚨 AI 구동 방지
    u_ry = st.session_state.get("u_ry_rev", "")
    u_rm = st.session_state.get("u_rm_rev", "")
    u_rd = st.session_state.get("u_rd_rev", "")
    u_rt = st.session_state.get("u_rt_rev", "")

    _ry = extract_ganji(u_ry)
    _rm = extract_ganji(u_rm)
    _rd = extract_ganji(u_rd)

    if not _ry and not _rm and not _rd:
        st.session_state.pop('rev_success_msg', None)
        st.session_state.pop('rev_error_msg', None)
        return

    if len(_ry) >= 2 and len(_rm) >= 2 and len(_rd) >= 2:
        ry_h = engine.K2H_GAN.get(_ry[0], _ry[0]) + engine.K2H_JI.get(_ry[1], _ry[1])
        rm_h = engine.K2H_GAN.get(_rm[0], _rm[0]) + engine.K2H_JI.get(_rm[1], _rm[1])
        rd_h = engine.K2H_GAN.get(_rd[0], _rd[0]) + engine.K2H_JI.get(_rd[1], _rd[1])

        klc_find = KoreanLunarCalendar()
        found = False
        time_map = {
            '자':'00:30 ~ 01:29 (朝子)시', '子':'00:30 ~ 01:29 (朝子)시',
            '축':'01:30 ~ 03:29 (丑)시', '丑':'01:30 ~ 03:29 (丑)시',
            '인':'03:30 ~ 05:29 (寅)시', '寅':'03:30 ~ 05:29 (寅)시',
            '묘':'05:30 ~ 07:29 (卯)시', '卯':'05:30 ~ 07:29 (卯)시',
            '진':'07:30 ~ 09:29 (辰)시', '辰':'07:30 ~ 09:29 (辰)시',
            '사':'09:30 ~ 11:29 (巳)시', '巳':'09:30 ~ 11:29 (巳)시',
            '오':'11:30 ~ 13:29 (午)시', '午':'11:30 ~ 13:29 (午)시',
            '미':'13:30 ~ 15:29 (未)시', '未':'13:30 ~ 15:29 (未)시',
            '신':'15:30 ~ 17:29 (申)시', '申':'15:30 ~ 17:29 (申)시',
            '유':'17:30 ~ 19:29 (酉)시', '酉':'17:30 ~ 19:29 (酉)시',
            '술':'19:30 ~ 21:29 (戌)시', '戌':'19:30 ~ 21:29 (戌)시',
            '해':'21:30 ~ 23:29 (亥)시', '亥':'21:30 ~ 23:29 (亥)시'
        }

        for y in range(2026, 1899, -1):
            klc_find.setSolarDate(y, 7, 1)
            gj_y = klc_find.getChineseGapJaString().split()
            if gj_y and gj_y[0][:2] == ry_h:
                curr_dt = dt_mod.date(y+1, 2, 28)
                while curr_dt >= dt_mod.date(y, 1, 1):
                    klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                    gj = klc_find.getChineseGapJaString().split()
                    if len(gj) >= 3 and gj[0][:2] == ry_h and gj[1][:2] == rm_h and gj[2][:2] == rd_h:
                        st.session_state['s_y'] = int(curr_dt.year)
                        st.session_state['s_m'] = int(curr_dt.month)
                        st.session_state['s_d'] = int(curr_dt.day)

                        if u_rt:
                            ji_char_u = u_rt[-1]
                            u_rt_h = engine.K2H_JI.get(ji_char_u, ji_char_u)
                            target_time_str = time_map.get(u_rt_h, "시간 모름")
                        else:
                            target_time_str = "시간 모름"

                        st.session_state['s_t'] = target_time_str
                        st.session_state['s_t_select'] = target_time_str

                        found = True
                        s_sol_fmt = f"{curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일"
                        s_lun_fmt = f"{klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일"
                        st.session_state['rev_success_msg'] = f"✅양력{s_sol_fmt} 음력{s_lun_fmt}"
                        break
                    curr_dt -= dt_mod.timedelta(days=1)
            if found: break

        if not found:
            st.session_state['rev_error_msg'] = "일치하는 날짜가 없습니다."
    else:
        st.session_state['rev_error_msg'] = "간지를 2글자씩 정확히 입력하세요."

# 🎯 [상대방] 사주간지 역산 전용 콜백 함수
def do_auto_fill_partner():
    st.session_state['app_running'] = False  # 🚨 AI 구동 방지
    p_ry = st.session_state.get("p_ry_rev", "")
    p_rm = st.session_state.get("p_rm_rev", "")
    p_rd = st.session_state.get("p_rd_rev", "")
    p_rt = st.session_state.get("p_rt_rev", "")

    _p_ry = extract_ganji(p_ry)
    _p_rm = extract_ganji(p_rm)
    _p_rd = extract_ganji(p_rd)

    if not _p_ry and not _p_rm and not _p_rd:
        st.session_state.pop('rev_p_success_msg', None)
        st.session_state.pop('rev_p_error_msg', None)
        return

    if len(_p_ry) >= 2 and len(_p_rm) >= 2 and len(_p_rd) >= 2:
        p_ry_h = engine.K2H_GAN.get(_p_ry[0], _p_ry[0]) + engine.K2H_JI.get(_p_ry[1], _p_ry[1])
        p_rm_h = engine.K2H_GAN.get(_p_rm[0], _p_rm[0]) + engine.K2H_JI.get(_p_rm[1], _p_rm[1])
        p_rd_h = engine.K2H_GAN.get(_p_rd[0], _p_rd[0]) + engine.K2H_JI.get(_p_rd[1], _p_rd[1])

        klc_find = KoreanLunarCalendar()
        found = False
        time_map = {
            '자':'00:30 ~ 01:29 (朝子)시', '子':'00:30 ~ 01:29 (朝子)시',
            '축':'01:30 ~ 03:29 (丑)시', '丑':'01:30 ~ 03:29 (丑)시',
            '인':'03:30 ~ 05:29 (寅)시', '寅':'03:30 ~ 05:29 (寅)시',
            '묘':'05:30 ~ 07:29 (卯)시', '卯':'05:30 ~ 07:29 (卯)시',
            '진':'07:30 ~ 09:29 (辰)시', '辰':'07:30 ~ 09:29 (辰)시',
            '사':'09:30 ~ 11:29 (巳)시', '巳':'09:30 ~ 11:29 (巳)시',
            '오':'11:30 ~ 13:29 (午)시', '午':'11:30 ~ 13:29 (午)시',
            '미':'13:30 ~ 15:29 (未)시', '未':'13:30 ~ 15:29 (未)시',
            '신':'15:30 ~ 17:29 (申)시', '申':'15:30 ~ 17:29 (申)시',
            '유':'17:30 ~ 19:29 (酉)시', '酉':'17:30 ~ 19:29 (酉)시',
            '술':'19:30 ~ 21:29 (戌)시', '戌':'19:30 ~ 21:29 (戌)시',
            '해':'21:30 ~ 23:29 (亥)시', '亥':'21:30 ~ 23:29 (亥)시'
        }

        # 🎯 [신청인] 사주간지 역산 전용 콜백 함수
def do_auto_fill_user():
    st.session_state['app_running'] = False
    u_ry = st.session_state.get("u_ry_rev", "")
    u_rm = st.session_state.get("u_rm_rev", "")
    u_rd = st.session_state.get("u_rd_rev", "")
    u_rt = st.session_state.get("u_rt_rev", "")

    _ry = extract_ganji(u_ry)
    _rm = extract_ganji(u_rm)
    _rd = extract_ganji(u_rd)

    if not _ry and not _rm and not _rd:
        st.session_state.pop('rev_matches_user', None)
        st.session_state.pop('rev_error_msg', None)
        return

    if len(_ry) >= 2 and len(_rm) >= 2 and len(_rd) >= 2:
        ry_h = engine.K2H_GAN.get(_ry[0], _ry[0]) + engine.K2H_JI.get(_ry[1], _ry[1])
        rm_h = engine.K2H_GAN.get(_rm[0], _rm[0]) + engine.K2H_JI.get(_rm[1], _rm[1])
        rd_h = engine.K2H_GAN.get(_rd[0], _rd[0]) + engine.K2H_JI.get(_rd[1], _rd[1])

        klc_find = KoreanLunarCalendar()
        matched_results = []
        time_map = {
            '자':'00:30 ~ 01:29 (朝子)시', '子':'00:30 ~ 01:29 (朝子)시',
            '축':'01:30 ~ 03:29 (丑)시', '丑':'01:30 ~ 03:29 (丑)시',
            '인':'03:30 ~ 05:29 (寅)시', '寅':'03:30 ~ 05:29 (寅)시',
            '묘':'05:30 ~ 07:29 (卯)시', '卯':'05:30 ~ 07:29 (卯)시',
            '진':'07:30 ~ 09:29 (辰)시', '辰':'07:30 ~ 09:29 (辰)시',
            '사':'09:30 ~ 11:29 (巳)시', '巳':'09:30 ~ 11:29 (巳)시',
            '오':'11:30 ~ 13:29 (午)시', '午':'11:30 ~ 13:29 (午)시',
            '미':'13:30 ~ 15:29 (未)시', '未':'13:30 ~ 15:29 (未)시',
            '신':'15:30 ~ 17:29 (申)시', '申':'15:30 ~ 17:29 (申)시',
            '유':'17:30 ~ 19:29 (酉)시', '酉':'17:30 ~ 19:29 (酉)시',
            '술':'19:30 ~ 21:29 (戌)시', '戌':'19:30 ~ 21:29 (戌)시',
            '해':'21:30 ~ 23:29 (亥)시', '亥':'21:30 ~ 23:29 (亥)시'
        }

        # 🌟 2056년부터 1905년까지 역추적 탐색
        for y in range(2056, 1904, -1):
            klc_find.setSolarDate(y, 7, 1)
            gj_y = klc_find.getChineseGapJaString().split()
            if gj_y and gj_y[0][:2] == ry_h:
                curr_dt = dt_mod.date(y+1, 2, 28)
                while curr_dt >= dt_mod.date(y, 1, 1):
                    klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                    gj = klc_find.getChineseGapJaString().split()
                    if len(gj) >= 3 and gj[0][:2] == ry_h and gj[1][:2] == rm_h and gj[2][:2] == rd_h:
                        if u_rt:
                            ji_char_u = u_rt[-1]
                            u_rt_h = engine.K2H_JI.get(ji_char_u, ji_char_u)
                            target_time_str = time_map.get(u_rt_h, "시간 모름")
                        else:
                            target_time_str = "시간 모름"

                        s_sol_fmt = f"{curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일"
                        s_lun_fmt = f"{klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일"
                        
                        matched_results.append({
                            "display": f"양력 {s_sol_fmt} (음력 {s_lun_fmt})",
                            "y": int(curr_dt.year),
                            "m": int(curr_dt.month),
                            "d": int(curr_dt.day),
                            "t": target_time_str
                        })
                    curr_dt -= dt_mod.timedelta(days=1)

        if matched_results:
            st.session_state['rev_matches_user'] = matched_results
            # 기본값으로 가장 최신 첫 번째 결과 자동 세팅
            st.session_state['s_y'] = matched_results[0]["y"]
            st.session_state['s_m'] = matched_results[0]["m"]
            st.session_state['s_d'] = matched_results[0]["d"]
            st.session_state['s_t'] = matched_results[0]["t"]
            st.session_state['s_t_select'] = matched_results[0]["t"]
            st.session_state.pop('rev_error_msg', None)
        else:
            st.session_state.pop('rev_matches_user', None)
            st.session_state['rev_error_msg'] = "일치하는 날짜가 없습니다."
    else:
        st.session_state['rev_error_msg'] = "간지를 2글자씩 정확히 입력하세요."

# 🎯 [상대방] 사주간지 역산 전용 콜백 함수
def do_auto_fill_partner():
    st.session_state['app_running'] = False
    p_ry = st.session_state.get("p_ry_rev", "")
    p_rm = st.session_state.get("p_rm_rev", "")
    p_rd = st.session_state.get("p_rd_rev", "")
    p_rt = st.session_state.get("p_rt_rev", "")

    _p_ry = extract_ganji(p_ry)
    _p_rm = extract_ganji(p_rm)
    _p_rd = extract_ganji(p_rd)

    if not _p_ry and not _p_rm and not _p_rd:
        st.session_state.pop('rev_matches_partner', None)
        st.session_state.pop('rev_p_error_msg', None)
        return

    if len(_p_ry) >= 2 and len(_p_rm) >= 2 and len(_p_rd) >= 2:
        p_ry_h = engine.K2H_GAN.get(_p_ry[0], _p_ry[0]) + engine.K2H_JI.get(_p_ry[1], _p_ry[1])
        p_rm_h = engine.K2H_GAN.get(_p_rm[0], _p_rm[0]) + engine.K2H_JI.get(_p_rm[1], _p_rm[1])
        p_rd_h = engine.K2H_GAN.get(_p_rd[0], _p_rd[0]) + engine.K2H_JI.get(_p_rd[1], _p_rd[1])

        klc_find = KoreanLunarCalendar()
        matched_results = []
        time_map = {
            '자':'00:30 ~ 01:29 (朝子)시', '子':'00:30 ~ 01:29 (朝子)시',
            '축':'01:30 ~ 03:29 (丑)시', '丑':'01:30 ~ 03:29 (丑)시',
            '인':'03:30 ~ 05:29 (寅)시', '寅':'03:30 ~ 05:29 (寅)시',
            '묘':'05:30 ~ 07:29 (卯)시', '卯':'05:30 ~ 07:29 (卯)시',
            '진':'07:30 ~ 09:29 (辰)시', '辰':'07:30 ~ 09:29 (辰)시',
            '사':'09:30 ~ 11:29 (巳)시', '巳':'09:30 ~ 11:29 (巳)시',
            '오':'11:30 ~ 13:29 (午)시', '午':'11:30 ~ 13:29 (午)시',
            '미':'13:30 ~ 15:29 (未)시', '未':'13:30 ~ 15:29 (未)시',
            '신':'15:30 ~ 17:29 (申)시', '申':'15:30 ~ 17:29 (申)시',
            '유':'17:30 ~ 19:29 (酉)시', '酉':'17:30 ~ 19:29 (酉)시',
            '술':'19:30 ~ 21:29 (戌)시', '戌':'19:30 ~ 21:29 (戌)시',
            '해':'21:30 ~ 23:29 (亥)시', '亥':'21:30 ~ 23:29 (亥)시'
        }

        # 🌟 2056년부터 1905년까지 역추적 탐색
        for y in range(2056, 1904, -1):
            klc_find.setSolarDate(y, 7, 1)
            gj_y = klc_find.getChineseGapJaString().split()
            if gj_y and gj_y[0][:2] == p_ry_h:
                curr_dt = dt_mod.date(y+1, 2, 28)
                while curr_dt >= dt_mod.date(y, 1, 1):
                    klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                    gj = klc_find.getChineseGapJaString().split()
                    if len(gj) >= 3 and gj[0][:2] == p_ry_h and gj[1][:2] == p_rm_h and gj[2][:2] == p_rd_h:
                        if p_rt:
                            ji_char_p = p_rt[-1]
                            p_rt_h = engine.K2H_JI.get(ji_char_p, ji_char_p)
                            target_time_str = time_map.get(p_rt_h, "시간 모름")
                        else:
                            target_time_str = "시간 모름"

                        s_sol_fmt = f"{curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일"
                        s_lun_fmt = f"{klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일"
                        
                        matched_results.append({
                            "display": f"양력 {s_sol_fmt} (음력 {s_lun_fmt})",
                            "y": int(curr_dt.year),
                            "m": int(curr_dt.month),
                            "d": int(curr_dt.day),
                            "t": target_time_str
                        })
                    curr_dt -= dt_mod.timedelta(days=1)

        if matched_results:
            st.session_state['rev_matches_partner'] = matched_results
            st.session_state['p_y_in'] = matched_results[0]["y"]
            st.session_state['p_m_in'] = matched_results[0]["m"]
            st.session_state['p_d_in'] = matched_results[0]["d"]
            st.session_state['p_t_key'] = matched_results[0]["t"]
            st.session_state['p_t_select'] = matched_results[0]["t"]
            st.session_state.pop('rev_p_error_msg', None)
        else:
            st.session_state.pop('rev_matches_partner', None)
            st.session_state['rev_p_error_msg'] = "일치하는 날짜가 없습니다."
    else:
        st.session_state['rev_p_error_msg'] = "간지를 2글자씩 정확히 입력하세요."

# ==============================================================================
# 2. 사이드바 통제 센터
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

    st.markdown("<div style='font-size: 15px; font-weight: 900; color: #000000; margin-bottom: 5px; font-family: \"Nanum Gothic\", sans-serif;'>📅 분석 기준 시점 선택</div>", unsafe_allow_html=True)
    kst_tz = pytz.timezone('Asia/Seoul')
    default_date_today = dt_mod.datetime.now(kst_tz).date()
    
    selected_target_date = st.date_input(
        "조회할 연/월/일 선택",
        value=st.session_state.get('target_date', dt_mod.date.today()),
        on_change=stop_ai,
        key="main_target_date_picker"
    )
    st.caption(f"💡 현재 지정 기준일: **{selected_target_date.year}년 {selected_target_date.month}월 {selected_target_date.day}일**")
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    st.markdown("<div style='font-size: 17px; font-weight: 900; color: #000000; margin-bottom: 10px; font-family: \"Nanum Gothic\", sans-serif;'>📋 분석 상품 선택</div>", unsafe_allow_html=True)

    main_category = st.selectbox(
        "어떤 상담을 원하십니까?", 
        [
            "1. 개인 사주팔자 풀이 (종합)", 
            "2. 테마별 특성화 상담", 
            "3. 커플 연애/결혼운 (궁합) 풀이", 
            "4. 타 감명서 비교"
        ], 
        key="main_category", 
        on_change=stop_ai
    )

    u_product = "1-1. 사주팔자와 운세풀이"

    if main_category == "1. 개인 사주팔자 풀이 (종합)":
        u_product = st.radio(
            "상세 분석 항목:", 
            [
                "1-1. 사주팔자와 운세풀이", 
                "1-2. 올 해 (특정 연도) 운세 상세분석", 
                "1-3. 이번 달 (특정 월) 운세 상세분석", 
                "1-4. 이번(특정) 주 및 일 운세 상세분석"
            ], 
            key="sub_category_1", 
            on_change=stop_ai
        )
    elif main_category == "2. 테마별 특성화 상담":
        u_product = st.radio(
            "특성화 상품 선택:", 
            [
                "2-1. 재물운 특화 분석", 
                "2-2. 직업/진학운 특화 분석", 
                "2-3. 연애/결혼운 특화 분석", 
                "2-4. 건강운 특화 분석", 
                "2-5. 이사 및 개업 택일"
            ], 
            key="sub_category_2", 
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
            key="sub_category_3", 
            on_change=stop_ai
        )
    elif main_category == "4. 타 감명서 비교":
        u_product = st.radio(
            "타 감명서 비교:", 
            [
                "4-1. 타 감명서 비교 (사주)", 
                "4-2. 타 감명서 비교 (궁합)"
            ], 
            key="sub_category_4", 
            on_change=stop_ai
        )
        
        st.markdown("---")

    if "u_g" not in st.session_state: st.session_state["u_g"] = "남성"
    if "f_g" not in st.session_state: st.session_state["f_g"] = "여성"

    def sync_partner_gender():
        u_val = st.session_state.get("u_g", "남성")
        st.session_state["f_g"] = "남성" if u_val == "여성" else "여성"
        stop_ai()

    def sync_user_gender():
        f_val = st.session_state.get("f_g", "여성")
        st.session_state["u_g"] = "여성" if f_val == "남성" else "남성"
        stop_ai()

    # 🔍 신청인 사주간지 역산 모듈 (on_click 콜백 연결)
    with st.expander("🔍 신청인 사주간지 역산", expanded=False):
        col_g1, col_g2 = st.columns(2)
        with col_g1: u_ry = st.text_input("년주", key="u_ry_rev", on_change=stop_ai)
        with col_g2: u_rm = st.text_input("월주", key="u_rm_rev", on_change=stop_ai)
        col_g3, col_g4 = st.columns(2)
        with col_g3: u_rd = st.text_input("일주", key="u_rd_rev", on_change=stop_ai)
        with col_g4: u_rt = st.text_input("시주", key="u_rt_rev", on_change=stop_ai)

        st.button("🔍 신청인 생년월일 자동입력", use_container_width=True, key="btn_user_rev", on_click=do_auto_fill_user)

        if 'rev_matches_user' in st.session_state and st.session_state['rev_matches_user']:
            matches = st.session_state['rev_matches_user']
            st.success(f"✅ 총 {len(matches)}개의 일치하는 연도가 검색되었습니다.")
            
            def on_select_user_match():
                sel_str = st.session_state.get('user_match_selector')
                for m in matches:
                    if m['display'] == sel_str:
                        st.session_state['s_y'] = m['y']
                        st.session_state['s_m'] = m['m']
                        st.session_state['s_d'] = m['d']
                        st.session_state['s_t'] = m['t']
                        st.session_state['s_t_select'] = m['t']
                        break
                stop_ai()

            st.selectbox(
                "📅 적용할 생년월일 선택:",
                options=[m['display'] for m in matches],
                key="user_match_selector",
                on_change=on_select_user_match
            )

        if 'rev_error_msg' in st.session_state:
            st.error(st.session_state['rev_error_msg'])
            del st.session_state['rev_error_msg']

    # 👤 신청인 기본 정보 입력부
    u_box = st.container()
    with u_box:
        st.subheader("👤 신청인 기본 정보")
        name = st.text_input("이름", value=st.session_state.get("u_n", ""), placeholder="홍길동", key="u_n", on_change=stop_ai)
        gender = st.selectbox("성별", ["남성", "여성"], key="u_g", on_change=sync_partner_gender)
        u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat", on_change=stop_ai)
        u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c", on_change=stop_ai)

        col_y, col_m, col_d = st.columns(3)
        with col_y: b_year = st.number_input("년도", 1900, 2050, value=st.session_state.get("s_y", 1980), key="s_y", on_change=stop_ai)
        with col_m: b_month = st.number_input("월", 1, 12, value=st.session_state.get("s_m", 1), key="s_m", on_change=stop_ai)
        with col_d: b_day = st.number_input("일", 1, 31, value=st.session_state.get("s_d", 1), key="s_d", on_change=stop_ai)
        
        curr_t_val = st.session_state.get("s_t", idx_list[0])
        t_idx = idx_list.index(curr_t_val) if curr_t_val in idx_list else 0
        
        b_time = st.selectbox("태어난 시간", idx_list, index=t_idx, key="s_t_select", on_change=stop_ai)
        st.session_state["s_t"] = b_time

    # 🌟 [수정 후] 1인용 가지와 2인용 가지의 명확한 분기 및 4번 상품 편입
    
    is_1person = not ( (main_category == "3. 커플 연애/결혼운 (궁합) 풀이") or ("4-2." in u_product) )
    
    if is_1person:
        if u_product.startswith("1-"):
            is_vip_package = st.checkbox("👑 VIP 패키지 모드", value=st.session_state.get("is_vip_package_val", False), key="is_vip_package_val", on_change=stop_ai)
            is_compare_traditional = st.checkbox("⚖️ 전통 : 시공 명리 운세풀이 비교", value=st.session_state.get("is_compare_trad_val", False), key="is_compare_trad_val", on_change=stop_ai)

        if "1-2." in u_product:
            curr_yr_val = dt_mod.datetime.now(pytz.timezone('Asia/Seoul')).year
            st.number_input("📅 분석 연도", min_value=1900, max_value=2050, value=curr_yr_val, key="target_year_input", on_change=stop_ai)
        elif "1-4." in u_product:
            st.date_input("일운 기준일", value=selected_target_date, key="daily_calc_date", on_change=stop_ai)
        elif "2-1." in u_product: 
            wealth_goal = st.text_input("고민되는 금전 문제는?", key="wealth_goal", on_change=stop_ai)
        elif "2-2." in u_product: 
            career_goal = st.text_input("고민되는 직업/진학 분야는?", key="career_goal", on_change=stop_ai)
        elif "2-3." in u_product:
            love_goal = st.text_input("고민되는 연애/이성 문제는?", key="love_goal", on_change=stop_ai)
        elif "2-4." in u_product: 
            health_goal = st.text_input("관리할 건강 부위는?", key="health_goal", on_change=stop_ai)
        elif "2-5." in u_product:
            tackil_purpose = st.radio("택일 목적", ["이사", "개업"], key="tackil_purpose", on_change=stop_ai)
            col_start, col_end = st.columns(2)
            start_date = col_start.date_input("시작일", key="moving_start", on_change=stop_ai)
            end_date = col_end.date_input("종료일", key="moving_end", on_change=stop_ai)
        
        # 🚨 [버그 수정]: 4-1 입력창 고정키(text_4_1) 부여 및 value 속성 완전 삭제!
        elif "4-1." in u_product:
            st.markdown("---")
            st.text_area("📄 [1인용] 타 사주 감명서 원문", height=150, key="text_4_1")

    # 2인 전용 상품(궁합, 택일) 상대방 사주 역산 및 기본 정보 모듈
    is_2person = (main_category == "3. 커플 연애/결혼운 (궁합) 풀이") or ("4-2." in u_product)
    if is_2person:
        st.markdown("<hr style='border:1px dashed #C62828; margin:15px 0;'>", unsafe_allow_html=True)
        
        if 'p_t_key' not in st.session_state: st.session_state['p_t_key'] = idx_list[0]
        
        with st.expander("🔍 상대방 사주간지 역산", expanded=False):
            p_col_g1, p_col_g2 = st.columns(2)
            with p_col_g1: p_ry = st.text_input("상대방 년주", key="p_ry_rev", on_change=stop_ai)
            with p_col_g2: p_rm = st.text_input("상대방 월주", key="p_rm_rev", on_change=stop_ai)
            p_col_g3, p_col_g4 = st.columns(2)
            with p_col_g3: p_rd = st.text_input("상대방 일주", key="p_rd_rev", on_change=stop_ai)
            with p_col_g4: p_rt = st.text_input("상대방 시주", key="p_rt_rev", on_change=stop_ai)
            
            st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="btn_partner_rev", on_click=do_auto_fill_partner)

        # 🌟 상대방 역산 결과가 1개 이상일 때 나타나는 선택창
        if 'rev_matches_partner' in st.session_state and st.session_state['rev_matches_partner']:
            p_matches = st.session_state['rev_matches_partner']
            st.success(f"✅ 총 {len(p_matches)}개의 일치하는 연도가 검색되었습니다.")
            
            def on_select_partner_match():
                sel_p_str = st.session_state.get('partner_match_selector')
                for m in p_matches:
                    if m['display'] == sel_p_str:
                        st.session_state['p_y_in'] = m['y']
                        st.session_state['p_m_in'] = m['m']
                        st.session_state['p_d_in'] = m['d']
                        st.session_state['p_t_key'] = m['t']
                        st.session_state['p_t_select'] = m['t']
                        break
                stop_ai()

            st.selectbox(
                "📅 적용할 상대방 생년월일 선택:",
                options=[m['display'] for m in p_matches],
                key="partner_match_selector",
                on_change=on_select_partner_match
            )

        if 'rev_p_error_msg' in st.session_state:
            st.error(st.session_state['rev_p_error_msg'])
            del st.session_state['rev_p_error_msg']

        if 'f_n' not in st.session_state: st.session_state['f_n'] = ""
        if 'p_y_in' not in st.session_state: st.session_state['p_y_in'] = 1990
        if 'p_m_in' not in st.session_state: st.session_state['p_m_in'] = 1
        if 'p_d_in' not in st.session_state: st.session_state['p_d_in'] = 1

        p_box = st.container()
        with p_box:
            st.subheader("💕 상대방 기본 정보")
            f_name = st.text_input("상대방 이름", key="f_n", on_change=stop_ai)
            f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_g", on_change=sync_user_gender)
            f_marital = st.selectbox("상대방 혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="f_m_stat", on_change=stop_ai)
            f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c", on_change=stop_ai)
            
            p_col1, p_col2, p_col3 = st.columns(3)
            f_y = p_col1.number_input("년도(상대)", 1900, 2050, key="p_y_in", on_change=stop_ai)
            f_m = p_col2.number_input("월(상대)", 1, 12, key="p_m_in", on_change=stop_ai)
            f_d = p_col3.number_input("일(상대)", 1, 31, key="p_d_in", on_change=stop_ai)
            
            p_t_idx = idx_list.index(st.session_state["p_t_key"]) if st.session_state["p_t_key"] in idx_list else 0
            f_t = st.selectbox("태어난 시간(상대)", idx_list, index=p_t_idx, key="p_t_select", on_change=stop_ai)
            st.session_state["p_t_key"] = f_t

    if "3-2." in u_product:
        date_mode = st.radio("결혼 택일 방식", ["기간 선택", "특정일 지정"], key="radio_marriage_mode", on_change=stop_ai)
        if date_mode == "기간 선택":
            col_start, col_end = st.columns(2)
            start_date = col_start.date_input("시작일", key="start_date_m", on_change=stop_ai)
            end_date = col_end.date_input("종료일", key="end_date_m", on_change=stop_ai)
        else:
            target_date = st.date_input("결혼 예정일 선택", key="target_date_m", on_change=stop_ai)
            
    elif "3-3." in u_product:
        run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석 가동", value=True, key="run_delivery_calc", on_change=stop_ai)
        if run_delivery_calc:
            st.subheader("🩺 산모 생리 주기 및 기준 정보")
            today_dt = dt_mod.date.today()
            default_last_period = today_dt - dt_mod.timedelta(days=30)
            last_period_date = st.date_input("마지막 생리 시작일", value=default_last_period, key="last_period_date", on_change=stop_ai)
            period_cycle = st.number_input("평균 생리 주기 (일)", min_value=20, max_value=45, value=30, key="period_cycle", on_change=stop_ai)
            st.markdown("---")
            st.subheader("📅 출산 길일 탐색 기간 설정")
            default_start = today_dt
            default_end = today_dt + dt_mod.timedelta(days=365)
            col_d1, col_d2 = st.columns(2)
            delivery_start_date = col_d1.date_input("탐색 시작일", value=default_start, key="delivery_start_date", on_change=stop_ai)
            delivery_end_date = col_d2.date_input("탐색 종료일", value=default_end, key="delivery_end_date", on_change=stop_ai)

    # 🚨 [버그 수정]: 4-2 입력창 고정키(text_4_2) 부여 및 value 속성 완전 삭제!
    elif "4-2." in u_product:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.markdown("### 📄 [2인용 커플] 타 궁합 감명서 원문")
        st.text_area("비교할 외부 커플/궁합 감명서 텍스트를 붙여넣어 주세요.", height=150, key="text_4_2")
        
    st.markdown("---")

    u_n = st.session_state.get('u_n', name if 'name' in locals() else "")
    u_g = st.session_state.get('u_g', gender if 'gender' in locals() else "")
    u_m = st.session_state.get('u_m_stat', u_marital if 'u_marital' in locals() else "")
    u_y = st.session_state.get('s_y', "")
    u_mo = st.session_state.get('s_m', "")
    u_d = st.session_state.get('s_d', "")
    
    current_user_key = f"{main_category}_{u_n}_{u_g}_{u_m}_{u_y}_{u_mo}_{u_d}_{selected_target_date}"
    
    if st.session_state.get('user_key') != current_user_key:
        st.session_state['user_key'] = current_user_key
        st.session_state['base_fact_cache'] = None
        st.session_state['report_essays'] = {}
        st.session_state['app_running'] = False

    # 🚨 오직 이 실행 버튼을 누를 때만 AI 풀이가 작동하도록 제어
    if st.button("✨ [초연 시공명리 풀이 가동]", key="btn_run", use_container_width=True, type="primary"):
        st.session_state['app_running'] = True

    if st.button("🖨️ 풀이 결과 인쇄 / PDF 저장", key="btn_print", use_container_width=True, type="secondary"):
        components.html("<script>window.parent.print();</script>", height=0)

# ==============================================================================
# 3. 메인 화면 범용 연산 및 AI 통변 모듈 연동부 (원초적 구조 완전체)
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
    next_year = curr_year + 1
    
    age = curr_year - sol_y + 1
    p_icon = "♂️" if gender == "남성" else "♀️"
    today_str = selected_target_date.strftime("%Y년 %m월 %d일")

    def extract_time(time_str):
        if "모름" in time_str: return 0, 0
        match = re.search(r'(\d{2}):(\d{2})', time_str)
        return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

    with st.spinner(f"⏳ [{u_product.strip()}] 시공명리 연산 및 정밀 통변 가동 중..."):
        h, m = extract_time(b_time)
        is_lunar_val, is_leap_val = ("음력" in u_cal), ("윤달" in u_cal)
        
        try:
            g_res = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)
            d_pillar = g_res[2] if len(g_res) > 2 else "甲子"
            y_pillar = g_res[0] if len(g_res) > 0 else "甲子"
            m_pillar = g_res[1] if len(g_res) > 1 else "甲子"
        except Exception:
            y_pillar, m_pillar, d_pillar = "甲子", "甲子", "甲子"
            
        lon = 0
        if hasattr(engine, 'get_true_year_month_pillar'):
            try:
                t_res = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
                if t_res and len(t_res) >= 2:
                    y_pillar = t_res[0]
                    m_pillar = t_res[1]
                    lon = t_res[2] if len(t_res) > 2 else 0
            except Exception:
                pass
        
        ds_hanja = engine.K2H_GAN.get(d_pillar[0], d_pillar[0])
        if "모름" in b_time:
            t_gan, t_ji = "", ""
        else:
            match = re.search(r'\((.*?)\)', b_time)
            raw_ji = match.group(1).replace('朝', '').replace('夜', '') if match else "子"
            t_ji = engine.K2H_JI.get(raw_ji, raw_ji)
            gan_arr, ji_arr = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'], ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            if ds_hanja in gan_arr and t_ji in ji_arr:
                d_idx, j_idx = gan_arr.index(ds_hanja), ji_arr.index(t_ji)
                t_gan = gan_arr[((d_idx % 5) * 2 + j_idx) % 10]
            else:
                t_gan = ""
         
        gans = [t_gan if t_gan else "-", d_pillar[0] if len(d_pillar)>0 else "甲", m_pillar[0] if len(m_pillar)>0 else "甲", y_pillar[0] if len(y_pillar)>0 else "甲"]
        jjis = [t_ji if t_ji else "-", d_pillar[1] if len(d_pillar)>1 else "子", m_pillar[1] if len(m_pillar)>1 else "子", y_pillar[1] if len(y_pillar)>1 else "子"]
        
        hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
        hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]
        
        base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
        adj_mins = engine.get_total_time_adjustment(base_dt)
        utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
        
        ys_idx = engine.GAN.index(ys) if ys in engine.GAN else 0
        order_dir = 1 if (ys_idx % 2 == 0) == (gender == '남성') else -1
        calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
        direction_str = "순행" if order_dir == 1 else "역행"
        
        counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
        for c in gans + jjis:
            oh = engine.get_color(c)
            if oh in counts: counts[oh] += 1
        
        guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
        guiin_str = guiin_map.get(ds_hanja, '없음')
        curr_y_ji = engine.JI[(curr_year - 1984) % 60 % 12]
        
        n_gong = engine.calculate_gongmang(ys, yb) or "-"
        i_gong = engine.calculate_gongmang(ds, db) or "-"
        cur_samjae = engine.get_samjae(yb, curr_y_ji)
        samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"
        
        sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
        lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
        time_str_fmt = f"{b_time}" if b_time != "시간 모름" else "시간 미상"
        
        if u_product.startswith("1-1"): report_title = "🏮 사주팔자와 운세풀이"
        elif u_product.startswith("1-2"): report_title = "🏮 올 해 (특정 연도) 운세 상세분석"
        elif u_product.startswith("1-3"): report_title = "🏮 이번 달 (특정 월) 운세 상세분석"
        elif u_product.startswith("1-4"): report_title = "🏮 이번 (특정) 주간 및 일 운세 상세분석"
        elif u_product.startswith("2-1"): report_title = "🏮 재물운 특화 정밀 분석"
        elif u_product.startswith("2-2"): report_title = "🏮 직업/진학운 특화 정밀 분석"
        elif u_product.startswith("2-3"): report_title = "🏮 연애/결혼운 특화 정밀 분석"
        elif u_product.startswith("2-4"): report_title = "🏮 건강운 특화 정밀 분석"
        elif u_product.startswith("2-5"): report_title = "🏮 이사 및 개업 택일 정밀 분석"
        elif u_product.startswith("3-1"): report_title = "🏮 커플 연애/결혼운 정밀 궁합 분석"
        elif u_product.startswith("3-2"): report_title = "🏮 최고의 결혼 길일 추천 리포트"
        elif u_product.startswith("3-3"): report_title = "🏮 새 생명 마중 출산 길일 추천 리포트"
        elif u_product.startswith("4-1"): report_title = "🏮 사주 감명서 1:1 대조 리포트"
        elif u_product.startswith("4-2"): report_title = "🏮 궁합 감명서 1:1 대조 리포트"
        else: report_title = "🏮 사주팔자 정밀 분석"

        gh_score = 0
        gh_grade = ""
        partner_bazi = ["?", "?", "?", "?"]

        # ----------------------------------------------------------------------
        # 2인용 파트너 연산 및 표지 구성
        # ----------------------------------------------------------------------
        if is_2person:
            p_y = st.session_state.get('p_y_in', 1980)
            p_m = st.session_state.get('p_m_in', 1)
            p_d = st.session_state.get('p_d_in', 1)
            p_cal_val = st.session_state.get('f_c', "양력")
            p_is_lunar = "음력" in p_cal_val
            p_is_leap = "윤달" in p_cal_val
            p_time_str = st.session_state.get('p_t_key', "시간 모름")

            try:
                p_g_res = engine.get_ganji_from_date(p_y, p_m, p_d, p_is_lunar, p_is_leap)
                p_y_p = p_g_res[0] if len(p_g_res) > 0 else "甲子"
                p_m_p = p_g_res[1] if len(p_g_res) > 1 else "甲子"
                p_d_p = p_g_res[2] if len(p_g_res) > 2 else "甲子"

                p_ds_hanja = engine.K2H_GAN.get(p_d_p[0], p_d_p[0])
                if "모름" in p_time_str:
                    p_t_gan, p_t_ji = "?", "?"
                else:
                    match = re.search(r'\((.*?)\)', p_time_str)
                    raw_ji = match.group(1).replace('朝', '').replace('夜', '') if match else "子"
                    p_t_ji = engine.K2H_JI.get(raw_ji, raw_ji)
                    gan_arr = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
                    ji_arr = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
                    if p_ds_hanja in gan_arr and p_t_ji in ji_arr:
                        d_idx, j_idx = gan_arr.index(p_ds_hanja), ji_arr.index(p_t_ji)
                        p_t_gan = gan_arr[((d_idx % 5) * 2 + j_idx) % 10]
                    else:
                        p_t_gan = "?"
                partner_bazi = [f"{p_t_gan}{p_t_ji}", p_d_p, p_m_p, p_y_p]
            except Exception:
                partner_bazi = ["甲子", "甲子", "甲子", "甲子"]

            st.session_state['partner_bazi'] = partner_bazi

            curr_yr_for_age = dt_mod.datetime.now(pytz.timezone('Asia/Seoul')).year
            p_age_val = curr_yr_for_age - p_y + 1
            
            f_gender_val = st.session_state.get("f_g", "여성")
            u_icon_str = "♂️ 남명 :" if gender == "남성" else "♀️ 여명 :"
            p_icon_str = "♀️ 여명 :" if f_gender_val == "여성" else "♂️ 남명 :"
            
            p_name_val = st.session_state.get("f_n", "상대방")
            p_time_val = p_time_str
            p_sol_str_val = f"{p_y}년 {p_m:02d}월 {p_d:02d}일"
            p_lun_str_val = ""
            
            cover_html = html_views.get_couple_cover(
                APP_VERSION, report_title, 
                u_icon_str, name, age, sol_str_fmt, lun_str_fmt, time_str_fmt,
                p_icon_str, p_name_val, p_age_val, p_sol_str_val, p_lun_str_val, p_time_val, 
                today_str
            )
            
            male_data_pack = [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"] if gender == "남성" else partner_bazi
            female_data_pack = partner_bazi if gender == "남성" else [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"]
            
            m_name_val = name if gender == "남성" else p_name_val
            f_name_val = p_name_val if gender == "남성" else name
            
            try:
                if hasattr(engine, 'UniversalPrintableGunghap'):
                    gh_engine = engine.UniversalPrintableGunghap(m_name_val, f_name_val, male_data_pack, female_data_pack, 10)
                    gh_engine.run_universal_logic()
                    gh_score = gh_engine.final_score
                    gh_grade = gh_engine.grade
                else:
                    gh_score = 0
                    gh_grade = "엔진 업데이트 필요"
            except Exception:
                gh_score, gh_grade = 0, "점수 산출 불가"
                
        else:
            u_icon_str = f"{p_icon}" 
            cover_html = html_views.get_personal_cover(
                APP_VERSION, report_title, u_icon_str, name, sol_str_fmt, lun_str_fmt, time_str_fmt, today_str
            )
        
        info_h = html_views.get_info_header(p_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, time_str_fmt)
        table_html = html_views.generate_saju_table_data(gans, jjis, ds, gender, engine)
        master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, samjae_color, cur_samjae)
        intro_html = html_views.get_intro_html()
        
        # ----------------------------------------------------------------------
        # 신청인 대운표 연산
        # ----------------------------------------------------------------------
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
            c_hanja = engine.K2H_GAN.get(c_hangul, c_hangul)
            j_hanja = engine.K2H_JI.get(j_hangul, j_hangul)
            is_active = (val <= age < val + 10)
            u_sung_val = engine.get_unsung(ds_hanja, j_hanja) if j_hanja != "-" else "-"
            y_shin_val = engine.get_12_shinsal(yb, j_hangul) if j_hangul != "-" else "-"
            d_shin_val = engine.get_12_shinsal(db, j_hangul) if j_hangul != "-" else "-"
            
            daewun_data_list.append({
                "age_range": f"{val}~{val+9}세", "ss_gan": engine.get_ss(ds_hanja, c_hangul),
                "c_hanja": c_hanja, "c_hangul": c_hangul, "j_hanja": j_hanja, "j_hangul": j_hangul,
                "ss_ji": engine.get_ss(ds_hanja, j_hangul), "un_sung": u_sung_val,
                "y_shinsal": y_shin_val, "d_shinsal": d_shin_val, "is_current": is_active, "is_first": (i == 0)
            })

        un_html = html_views.generate_daewun_layout(daewun_data_list, direction_str, calc_d, get_oh_class)

        # ----------------------------------------------------------------------
        # 상대방 대운표 연산 (2인용 전용)
        # ----------------------------------------------------------------------
        p_un_html = ""
        p_info_h, p_table_html, p_master_bar_html = "", "", ""
        if is_2person:
            try:
                p_ys = partner_bazi[3][0] if len(partner_bazi[3]) > 0 else "甲"
                p_yb = partner_bazi[3][1] if len(partner_bazi[3]) > 1 else "子"
                p_ms = partner_bazi[2][0] if len(partner_bazi[2]) > 0 else "甲"
                p_mb = partner_bazi[2][1] if len(partner_bazi[2]) > 1 else "子"
                p_ds = partner_bazi[1][0] if len(partner_bazi[1]) > 0 else "甲"
                p_db = partner_bazi[1][1] if len(partner_bazi[1]) > 1 else "子"
                p_ds_hanja = engine.K2H_GAN.get(p_ds, p_ds)
                
                p_ys_idx = engine.GAN.index(p_ys) if p_ys in engine.GAN else 0
                p_order_dir = 1 if (p_ys_idx % 2 == 0) == (f_gender_val == '남성') else -1
                
                p_base_dt = dt_mod.datetime(p_y, p_m, p_d, 12, 0)
                p_adj_mins = engine.get_total_time_adjustment(p_base_dt)
                p_utc_dt = p_base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=p_adj_mins)
                
                p_calc_d = engine.get_daeun_su_accurate(p_utc_dt, p_order_dir)
                p_direction_str = "순행" if p_order_dir == 1 else "역행"
                
                p_c_idx = engine.GAN.index(p_ms) if p_ms in engine.GAN else 0
                p_j_idx = engine.JI.index(p_mb) if p_mb in engine.JI else 0
                
                p_daewun_data_list = []
                for i in range(10):
                    p_val = i * 10 + p_calc_d
                    p_c_hangul = engine.GAN[(p_c_idx + (i + 1) * p_order_dir) % 10] if p_ms in engine.GAN else "-"
                    p_j_hangul = engine.JI[(p_j_idx + (i + 1) * p_order_dir) % 12] if p_mb in engine.JI else "-"
                    p_c_hanja = engine.K2H_GAN.get(p_c_hangul, p_c_hangul) if p_c_hangul != "-" else "-"
                    p_j_hanja = engine.K2H_JI.get(p_j_hangul, p_j_hangul) if p_j_hangul != "-" else "-"
                    p_is_active = (p_val <= p_age_val < p_val + 10)
                    p_u_sung_val = engine.get_unsung(p_ds_hanja, p_j_hanja) if p_j_hanja != "-" else "-"
                    p_y_shin_val = engine.get_12_shinsal(p_yb, p_j_hangul) if p_j_hangul != "-" else "-"
                    p_d_shin_val = engine.get_12_shinsal(p_db, p_j_hangul) if p_j_hangul != "-" else "-"
                    
                    p_daewun_data_list.append({
                        "age_range": f"{p_val}~{p_val+9}세", "ss_gan": engine.get_ss(p_ds_hanja, p_c_hangul),
                        "c_hanja": p_c_hanja, "c_hangul": p_c_hangul, "j_hanja": p_j_hanja, "j_hangul": p_j_hangul,
                        "ss_ji": engine.get_ss(p_ds_hanja, p_j_hangul), "un_sung": p_u_sung_val,
                        "y_shinsal": p_y_shin_val, "d_shinsal": p_d_shin_val, "is_current": p_is_active, "is_first": (i == 0)
                    })
                p_un_html = html_views.generate_daewun_layout(p_daewun_data_list, p_direction_str, p_calc_d, get_oh_class)
                
                # 상대방 원국표 및 마스터바 빌드
                p_gans = [partner_bazi[0][0] if len(partner_bazi[0])>0 else "-", partner_bazi[1][0] if len(partner_bazi[1])>0 else "甲", partner_bazi[2][0] if len(partner_bazi[2])>0 else "甲", partner_bazi[3][0] if len(partner_bazi[3])>0 else "甲"]
                p_jjis = [partner_bazi[0][1] if len(partner_bazi[0])>1 else "-", partner_bazi[1][1] if len(partner_bazi[1])>1 else "子", partner_bazi[2][1] if len(partner_bazi[2])>1 else "子", partner_bazi[3][1] if len(partner_bazi[3])>1 else "子"]
                p_counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
                for c in p_gans + p_jjis:
                    p_oh = engine.get_color(c)
                    if p_oh in p_counts: p_counts[p_oh] += 1
                p_guiin_str = guiin_map.get(p_ds_hanja, '없음')
                p_n_gong = engine.calculate_gongmang(p_ys, p_yb) or "-"
                p_i_gong = engine.calculate_gongmang(p_ds, p_db) or "-"
                p_samjae = engine.get_samjae(p_yb, curr_y_ji)
                p_samjae_color = "#C62828" if p_samjae != "해당 없음" else "#555"

                p_info_h = html_views.get_info_header("♀️" if f_gender_val=="여성" else "♂️", p_name_val, f_gender_val, st.session_state.get("f_m_stat","선택"), p_age_val, p_sol_str_val, p_lun_str_val, p_time_val)
                p_table_html = html_views.generate_saju_table_data(p_gans, p_jjis, p_ds, f_gender_val, engine)
                p_master_bar_html = html_views.get_master_bar(p_calc_d, p_counts['목'], p_counts['화'], p_counts['토'], p_counts['금'], p_counts['수'], p_guiin_str, p_n_gong, p_i_gong, p_samjae_color, p_samjae)
            except Exception:
                p_un_html = "<p style='text-align:center;'>상대방 대운 연산 중</p>"

        # ----------------------------------------------------------------------
        # 세운 및 월운 연산
        # ----------------------------------------------------------------------
        current_daewun_age = max(0, int(cur_dw_idx) * 10 + int(calc_d))
        start_year = int(sol_y) + current_daewun_age - 1

        se_content = ""
        for i in range(10):
            ty = start_year + i
            tage = current_daewun_age + i
            base = (ty - 1984) % 60
            tc_hangul, tj_hangul = engine.GAN[base % 10], engine.JI[base % 12]
            tc, tj = engine.K2H_GAN.get(tc_hangul, tc_hangul), engine.K2H_JI.get(tj_hangul, tj_hangul)
            is_cur_yr = (ty == curr_year)
            bg_col = "#E1F5FE" if is_cur_yr else "transparent"
            b_left = "1px solid #ccc"
            se_content += html_views.get_sewun_cell(
                f"{ty}년", tage, engine.get_ss(ds_hanja, tc), tc, get_oh_class(tc), 
                tj, get_oh_class(tj), engine.get_ss(ds_hanja, tj), engine.get_unsung(ds_hanja, tj), 
                engine.get_12_shinsal(yb, tj), engine.get_12_shinsal(db, tj), bg_col, b_left, is_cur_yr
            )
            
        dw_title_hanja = f"({engine.K2H_GAN.get(dw_g_cur, dw_g_cur)}{engine.K2H_JI.get(dw_j_cur, dw_j_cur)}대운 기준)"
        sewun_html = html_views.get_sewun_layout(f"[ 세운의 흐름 {dw_title_hanja} ]", se_content)

        wol_content = ""
        for i in range(12):
            tm = i + 1
            try:
                _, m_p_res, _ = engine.get_true_year_month_pillar(curr_year, tm, 15, 12, 0)
                wc_hanja, wj_hanja = m_p_res[0], m_p_res[1]
            except Exception:
                wc_hanja, wj_hanja = "甲", "子"
            is_cur_m = (tm == curr_m)
            bg_col = "#E8F5E9" if is_cur_m else "transparent"
            b_left = "1px solid #ccc"
            wol_content += html_views.get_wolun_cell(
                tm, engine.get_ss(ds_hanja, wc_hanja), wc_hanja, get_oh_class(wc_hanja), 
                wj_hanja, get_oh_class(wj_hanja), engine.get_ss(ds_hanja, wj_hanja), 
                engine.get_unsung(ds_hanja, wj_hanja), engine.get_12_shinsal(yb, wj_hanja), 
                engine.get_12_shinsal(db, wj_hanja), bg_col, b_left, is_cur_m
            )

        wolun_html = html_views.get_wolun_layout(f"[ 월운의 흐름 ({curr_year}년도 양력기준) ]", wol_content)

        w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{db}".strip()
        w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
        i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
        struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
        
        gyukgook, gyukgook_detail = engine.get_gyukgook_detailed(ds, ys, ms, hs, mb)
        # 신청인 기본 황금문구
        golden_text_html = html_views.get_golden_text(name, w_val, i_val, struct_data[0], struct_data[1], struct_data[2], mb=mb, gyuk_name=gyukgook)
        
        # 🌟 2인용 궁합(4-2 등)을 위한 상대방 황금문구 및 남녀 듀얼 황금문구 생성
        golden_box_gunghap_html = golden_text_html
        if is_2person:
            try:
                p_w_key, p_i_key = f"{p_ms}{p_mb}".strip(), f"{p_ds}{p_db}".strip()
                p_w_val = choyeon_db.get("wolryeong", {}).get(p_w_key, f"[{p_w_key}] 시공간 데이터 없음")
                p_i_val = choyeon_db.get("ilju", {}).get(p_i_key, f"[{p_i_key}] 성품 데이터 없음")
                p_struct_data = choyeon_db.get("ilju_structure", {}).get(p_i_key, ["구조 미상", "유형 미상", "성향 미상"])
                p_gyuk, _ = engine.get_gyukgook_detailed(p_ds, p_ys, p_ms, partner_bazi[0][0] if len(partner_bazi[0])>0 else "甲", p_mb)
                
                p_golden_html = html_views.get_golden_text(p_name_val, p_w_val, p_i_val, p_struct_data[0], p_struct_data[1], p_struct_data[2], mb=p_mb, gyuk_name=p_gyuk)
                
                m_g_html = golden_text_html if gender == "남성" else p_golden_html
                f_g_html = p_golden_html if gender == "남성" else golden_text_html
                
                golden_box_gunghap_html = html_views.get_couple_golden_text(m_name_val, m_g_html, f_name_val, f_g_html)
            except Exception:
                golden_box_gunghap_html = golden_text_html

        closing_html = html_views.get_closing_html(name)            
        closing_part = str(closing_html or "").strip()

        # ----------------------------------------------------------------------
        # 팩트 블록 구성 (1인용 vs 2인용 완전 분리)
        # ----------------------------------------------------------------------
        part_1_fact = str(info_h or "") + str(table_html or "") + str(master_bar_html or "")
        part_2_intro = str(intro_html or "")
        part_3_golden = str(golden_text_html or "")
        part_5_closing = str(closing_part or "")

        # 🌟 4-2번 궁합 비교 전용 [남명 완전체 ➔ 여명 완전체] 상단 팩트 (뷰 함수로 분리)
        part_1_fact_gunghap = part_1_fact
        if is_2person:
            u_full = str(info_h or "") + str(table_html or "") + str(master_bar_html or "") + str(un_html or "")
            p_full = str(p_info_h or "") + str(p_table_html or "") + str(p_master_bar_html or "") + str(p_un_html or "")
            
            male_block = u_full if gender == "남성" else p_full
            female_block = p_full if gender == "남성" else u_full

            if hasattr(html_views, 'get_couple_fact_split_layout'):
                part_1_fact_gunghap = html_views.get_couple_fact_split_layout(male_block, female_block)
            else:
                part_1_fact_gunghap = f"{male_block}<br>{female_block}"

        won_guk_vaults_list = engine.check_vault_status([ys, ms, ds, hs], [yb, mb, db, hb], mb)
        won_guk_vaults_str = " ".join([re.sub(r'<[^>]+>', '', v) for v in won_guk_vaults_list])
        if not won_guk_vaults_str: won_guk_vaults_str = engine.get_won_guk_vaults_str([hb, db, mb, yb])
            
        hap_chung_hyoung_pa_hae = f"일-월지:{engine.get_ji_rel_set(db, mb)}, 일-년지:{engine.get_ji_rel_set(db, yb)}, 일-시지:{engine.get_ji_rel_set(db, hb)}, 월-년지:{engine.get_ji_rel_set(mb, yb)}"
        
        try:
            shinsal_raw = engine.get_general_shinsal_filtered(1, gans, jjis, gender) if hasattr(engine, 'get_general_shinsal_filtered') else []
        except Exception:
            shinsal_raw = []
        shinsal_str = ", ".join([re.sub(r'<[^>]+>', '', str(s)) for s in shinsal_raw]) if shinsal_raw else "특이 신살 없음"

        w_facts = engine.get_woonse_analysis_facts(ds, db, dw_g_cur, dw_j_cur, engine.GAN[(curr_year-1984)%60%10], engine.JI[(curr_year-1984)%60%12], "丙", "午", "甲", "子")

        saju_fact_summary = f"""
- 내담자 명조: 년주({ys}{yb}), 월주({ms}{mb}), 일주({ds}{db}), 시주({hs}{hb})
- 격국 및 용신 팩트: {gyukgook_detail}
- 원국 오행 분포: 목:{counts['목']}, 화:{counts['화']}, 토:{counts['토']}, 금:{counts['금']}, 수:{counts['수']}
- 공망 궁위 팩트: [년지공망] {n_gong} / [일지공망] {i_gong}
- 삼재 여부: {cur_samjae}
"""

        target_year_val = st.session_state.get('target_year_input', curr_year)
        cur_sewun_base = (target_year_val - 1984) % 60
        cur_sewun_gan_val = engine.GAN[cur_sewun_base % 10]
        cur_sewun_ji_val = engine.JI[cur_sewun_base % 12]

        ilju_master_context = engine.get_ilju_master_prompt_context(f"{ds}{db}", choyeon_db)
        seun_first_half, seun_second_half = engine.get_seun_half_periods(target_year_val) if hasattr(engine, 'get_seun_half_periods') else ("상반기(입춘~입추 전)", "하반기(입추~다음해 입춘 전)")
        wolun_first_half, wolun_second_half = engine.get_wolun_half_periods(target_year_val, curr_m) if hasattr(engine, 'get_wolun_half_periods') else ("전반기(절입일~중기 전)", "후반기(중기~다음 절입일 전)")

        # 🌟 4번 상품 외부 원문 추출 및 특수문자 정제
        user_entered_text = ""
        if u_product.startswith("4-1"):
            user_entered_text = (st.session_state.get("text_4_1", "") or st.session_state.get(f"text_{u_product}", "")).strip()
        elif u_product.startswith("4-2"):
            user_entered_text = (st.session_state.get("text_4_2", "") or st.session_state.get(f"text_{u_product}", "")).strip()

        if user_entered_text:
            user_entered_text = re.sub(r'[▷▶◈\[\]\■\□\●\○\◆\◇\★\☆\※\▪\▫]', '', user_entered_text)

        prompt_data = {
            "name": name, "age": age, "gender": gender, "marital": u_marital,
            "ilju_master_prompt_context": ilju_master_context,
            "age_prompt": engine.get_age_prompt(age), "gender_prompt": engine.get_gender_prompt(gender), 
            "marital_prompt": engine.get_marital_prompt(gender, u_marital), "yukchin_rule": engine.get_yukchin_rule(gender, u_marital),
            "saju_fact_summary": saju_fact_summary, "dw_g_cur": dw_g_cur, "dw_j_cur": dw_j_cur, 
            "dw_fact_str": f"현재 {dw_g_cur}{dw_j_cur}대운 가동 중",
            "samhyung_fact_str": engine.check_samhyung_facts([yb, mb, db, hb], dw_j_cur),
            "hang_un_vaults_str": engine.get_hang_un_vaults_str(dw_j_cur, [ys, ms, ds, hs], [yb, mb, db, hb]),
            "dw_che": w_facts.get("dw_che", "대운 시공간 무대"),
            "ds": ds, "db": db, "gyukgook_detail": gyukgook_detail,
            "year_gongmang": n_gong, "day_gongmang": i_gong,
            "oheng_counts_str": f"목:{counts['목']} 화:{counts['화']} 토:{counts['토']} 금:{counts['금']} 수:{counts['수']}",
            "hap_chung_hyoung_pa_hae": hap_chung_hyoung_pa_hae, "won_guk_vaults_str": won_guk_vaults_str,
            "shinsal_str": shinsal_str, "cheon_eul": guiin_str, "samjae_str": cur_samjae,
            "curr_year": target_year_val, "cur_sewun_gan": cur_sewun_gan_val, "cur_sewun_ji": cur_sewun_ji_val,
            "target_year": target_year_val, "curr_m": curr_m, "target_date_str": selected_target_date.strftime("%Y년 %m월 %d일"),
            "gh_score": gh_score, "gh_grade": gh_grade,
            "first_half_period": seun_first_half if "1-2" in u_product else wolun_first_half,
            "second_half_period": seun_second_half if "1-2" in u_product else wolun_second_half,
            "wealth_goal": st.session_state.get('wealth_goal', '자산 증식'),
            "career_goal": st.session_state.get('career_goal', '직업 적성'),
            "love_goal": st.session_state.get('love_goal', '인연 관계'),
            "health_goal": st.session_state.get('health_goal', '건강 관리'),
            "tackil_purpose": st.session_state.get('tackil_purpose', '이사'),
            "target_date_range": f"{st.session_state.get('moving_start', selected_target_date)} ~ {st.session_state.get('moving_end', selected_target_date + dt_mod.timedelta(days=30))}",
            "other_reading_text": user_entered_text, "other_report": user_entered_text,
            "m_name": name if gender == "남성" else p_name_val if 'p_name_val' in locals() else "신랑",
            "f_name": p_name_val if 'p_name_val' in locals() and gender == "남성" else name
        }

        class SafeDict(dict):
            def __missing__(self, key): return '{' + key + '}'
        
        def get_prompt_var_name(u_prod):
            if "1-1" in u_prod: return "프롬프트_1_1_기본"
            if "1-2" in u_prod: return "프롬프트_1_2_연도운"
            if "1-3" in u_prod: return "프롬프트_1_3_월운"
            if "1-4" in u_prod: return "프롬프트_1_4_일운"
            if "2-1" in u_prod: return "프롬프트_2_1_재물운"
            if "2-2" in u_prod: return "프롬프트_2_2_직업운"
            if "2-3" in u_prod: return "프롬프트_2_3_연애운"
            if "2-4" in u_prod: return "프롬프트_2_4_건강운"
            if "2-5" in u_prod: return "프롬프트_2_5_이사개업 택일"
            if "3-1" in u_prod: return "프롬프트_3_1_궁합"
            if "3-2" in u_prod: return "프롬프트_3_2_결혼택일"
            if "3-3" in u_prod: return "프롬프트_3_3_출산택일"
            if "4-1" in u_prod: return "프롬프트_4_1_사주대조"
            if "4-2" in u_prod: return "프롬프트_4_2_궁합대조"
            return "프롬프트_1_1_기본"

        prompt_var_name = get_prompt_var_name(u_product)
        target_prompt = getattr(prompts, prompt_var_name, getattr(prompts, "프롬프트_1_1_기본", ""))
        
        formatted_prompt = target_prompt.format_map(SafeDict(prompt_data))
        raw_response = call_gemini_api(formatted_prompt)
        
        if raw_response and isinstance(raw_response, str):
            clean_raw = raw_response.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
            ai_output_html = html_views.format_ai_text_to_html(clean_raw)
        else:
            ai_output_html = "<p style='padding:20px;'>분석 결과를 불러오지 못했습니다.</p>"

        # ==============================================================================
        # 🏮 [ver 72.5 파이프라인] 최종 화면 렌더링
        # ==============================================================================
        if 'cover_html' in locals() and cover_html:
            safe_cover = re.sub(r'\n\s+', '\n', cover_html)
            st.markdown(safe_cover, unsafe_allow_html=True)

        final_render_html = ""

        def sub_marker(text, marker_name, table_code):
            pattern = r'\[\s*\*?\*?\s*' + marker_name + r'\s*\*?\*?\s*\]'
            return re.sub(pattern, table_code, text, flags=re.IGNORECASE)

        if u_product.startswith("1-1"):
            daewun_table_code = un_html if 'un_html' in locals() and un_html else ""
            sewun_table_code = sewun_html if 'sewun_html' in locals() and sewun_html else ""
            formatted_ai = sub_marker(ai_output_html, 'DAEWUN_TABLE_HERE', daewun_table_code)
            formatted_ai = sub_marker(formatted_ai, 'SEWUN_TABLE_HERE', sewun_table_code)
            master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
            final_render_html = html_views.get_final_report_box(master_comp)

        elif u_product.startswith("1-2"):
            sewun_table_code = sewun_html if 'sewun_html' in locals() and sewun_html else ""
            formatted_ai = sub_marker(ai_output_html, 'SEWUN_TABLE_HERE', sewun_table_code)
            master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
            final_render_html = html_views.get_final_report_box(master_comp)

        elif u_product.startswith("1-3"):
            wolun_table_code = wolun_html if 'wolun_html' in locals() and wolun_html else ""
            formatted_ai = sub_marker(ai_output_html, 'WOLUN_TABLE_HERE', wolun_table_code)
            master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
            final_render_html = html_views.get_final_report_box(master_comp)

        elif u_product.startswith("1-4"):
            weekly_days_data = engine.get_weekly_calendar_data(selected_target_date, ds_hanja) if hasattr(engine, 'get_weekly_calendar_data') else []
            weekly_table_code = html_views.generate_weekly_calendar_html(weekly_days_data, selected_target_date.day, yb, db)
            formatted_ai = sub_marker(ai_output_html, 'WEEKLY_CALENDAR_HERE', weekly_table_code)
            master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
            final_render_html = html_views.get_final_report_box(master_comp)

        elif u_product.startswith("2-"):
            daewun_table_code = un_html if 'un_html' in locals() and un_html else ""
            formatted_ai = sub_marker(ai_output_html, 'DAEWUN_TABLE_HERE', daewun_table_code)
            master_comp = f"{part_1_fact}{formatted_ai}{part_5_closing}"
            final_render_html = html_views.get_final_report_box(master_comp)

        elif u_product == "3-1. 연애/결혼운 (궁합) 풀이":
            m_ess, f_ess, g_ess = "", "", clean_raw
            m_match = re.search(r'\[MALE_START\](.*?)\[MALE_END\]', clean_raw, re.DOTALL)
            if m_match: m_ess = html_views.format_ai_text_to_html(m_match.group(1).strip())
            f_match = re.search(r'\[FEMALE_START\](.*?)\[FEMALE_END\]', clean_raw, re.DOTALL)
            if f_match: f_ess = html_views.format_ai_text_to_html(f_match.group(1).strip())
            g_match = re.search(r'\[GUNGHAP_START\](.*?)\[GUNGHAP_END\]', clean_raw, re.DOTALL)
            if g_match: g_ess = html_views.format_ai_text_to_html(g_match.group(1).strip())

            m_daewun_html = un_html if gender == "남성" else p_un_html
            f_daewun_html = p_un_html if gender == "남성" else un_html
            c_daewun_html = html_views.get_daewun_compare_box(m_name_val, m_daewun_html, f_name_val, f_daewun_html)
            g_ess = sub_marker(g_ess, 'COUPLE_DAEWUN_TABLES_HERE', c_daewun_html)

            score_ui, closing_ui = "", ""
            if 'gh_engine' in locals():
                score_ui = html_views.get_gunghap_score_visual_html(gh_engine)
                closing_ui = html_views.get_gunghap_closing(m_name_val, f_name_val)
            g_ess += score_ui + closing_ui
            final_render_html = html_views.get_gunghap_three_page_report(part_1_fact, m_ess, f_ess, g_ess)

        elif u_product.startswith("4-1"):
            if not user_entered_text:
                warn_html = html_views.get_warning_box("타 감명서 원문 미입력 경고", "비교 분석을 진행할 <b>[외부 타 감명서 원문 텍스트]</b>가 입력되지 않았습니다.")
                final_render_html = html_views.render_comparison_report(part_1_fact, warn_html, "")
            else:
                external_raw_box = html_views.get_external_raw_text_box(user_entered_text)
                daewun_table_code = un_html if 'un_html' in locals() and un_html else ""
                sewun_table_code = sewun_html if 'sewun_html' in locals() and sewun_html else ""
                formatted_ai = sub_marker(ai_output_html, 'DAEWUN_TABLE_HERE', daewun_table_code)
                formatted_ai = sub_marker(formatted_ai, 'SEWUN_TABLE_HERE', sewun_table_code)
                golden_box_html = golden_box_gunghap_html if 'golden_box_gunghap_html' in locals() else golden_text_html
                full_ai_content = golden_box_html + ("<br>" if golden_box_html else "") + formatted_ai
                final_render_html = html_views.render_comparison_report(part_1_fact, external_raw_box, full_ai_content)

        # 🌟 4-2. 타 감명서 비교 (궁합) -> 기존 표준 렌더링 함수 완벽 일치
        elif u_product.startswith("4-2"):
            if not user_entered_text:
                warn_html = html_views.get_warning_box("타 궁합 감명서 원문 미입력 경고", "비교 분석을 진행할 <b>[외부 타 궁합 감명서 원문 텍스트]</b>가 입력되지 않았습니다.")
                final_render_html = html_views.render_comparison_report(part_1_fact_gunghap, warn_html, "")
            else:
                external_raw_box = html_views.get_external_raw_text_box(user_entered_text)
                formatted_ai = sub_marker(ai_output_html, 'COUPLE_DAEWUN_TABLES_HERE', '')
                formatted_ai = sub_marker(formatted_ai, 'DAEWUN_TABLE_HERE', '')
                golden_box_html = golden_text_html if 'golden_text_html' in locals() else ""
                full_ai_content = golden_box_html + ("<br>" if golden_box_html else "") + formatted_ai
                
                # 🌟 별도 함수 없이 기존 4-1과 완전히 동일한 표준 뷰 함수로 직접 출력
                final_render_html = html_views.render_comparison_report(part_1_fact_gunghap, external_raw_box, full_ai_content)

        if 'final_render_html' not in locals() or final_render_html is None:
            final_render_html = ""

        final_render_html = str(final_render_html).strip()
        if final_render_html.startswith("</div>"):
            final_render_html = final_render_html[6:].strip()

        final_render_html = re.sub(r'\n\s+', '\n', final_render_html)
        st.markdown(final_render_html, unsafe_allow_html=True)
