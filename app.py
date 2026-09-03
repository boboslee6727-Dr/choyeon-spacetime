# ==============================================================================
# app.py (ver 86.6 Master - Claude 전용 버젼)
# ==============================================================================
import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from datetime import datetime
from korean_lunar_calendar import KoreanLunarCalendar
import os
import re
import anthropic
import time
import json
import math
import pytz
import sys
import importlib
import engine
import prompts
import html_views
# 서브 모듈 변경 사항 즉시 반영 (강제 리로드)
importlib.reload(engine)
importlib.reload(prompts)
importlib.reload(html_views)
extract_ganji = engine.extract_ganji
get_oh_class = engine.get_oh_class

# ==============================================================================
# 1. 초기 설정 및 공통 함수
# ==============================================================================
APP_VERSION = "ver 86.6 Master"
st.set_page_config(page_title=f"초연시공 Claud{APP_VERSION}", layout="wide")

# 외주 영업부(파이프라인) 호출 문지기
try:
    from pipeline_manager import run_pipeline_router
    run_pipeline_router()
except ImportError as e:

# 전역 CSS 적용
if hasattr(html_views, 'get_global_css'):
    st.markdown(html_views.get_global_css(), unsafe_allow_html=True)

# 라디오 버튼 두 줄 UI 강제 보장 및 표지 줄바꿈 방지 CSS
st.markdown("""
<style>
    div[data-testid="stRadio"] label p { font-size: 14px !important; white-space: pre-wrap !important; line-height: 1.6 !important; padding-bottom: 4px !important; }
    .cover-page h1, .cover-page h2, .report-page h1, .report-page h2 { white-space: nowrap !important; word-break: keep-all !important; letter-spacing: -0.5px !important; }
</style>
""", unsafe_allow_html=True)

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
# 1.5. AI 통신 및 간지 역산 콜백 함수
# ==============================================================================
try:
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    model = client  # 하위 호환용
except Exception as _api_e:
    st.error(f"🚨 Claude API 키 오류: {_api_e}")
    client, model = None, None

# ⚙️ 사용할 모델명. 필요시 여기서 바꾸세요.
CLAUDE_MODEL_NAME = "claude-haiku-4-5-20251001"  #"claude-sonnet-5"

def _call_claude(prompt_text, max_tokens=32000):
    if client is None: return "<div style='color:red;'>🚨 Claude 모델이 초기화되지 않았습니다. (ANTHROPIC_API_KEY 확인)</div>"
    try:
        result_text = ""
        stop_reason = None
        with client.messages.stream(
            model=CLAUDE_MODEL_NAME,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt_text}],
        ) as stream:
            for text in stream.text_stream:
                result_text += text
            final_message = stream.get_final_message()
            stop_reason = getattr(final_message, "stop_reason", None)
        result_text = result_text.strip()
        if stop_reason == "max_tokens":
            result_text += "\n\n<div style='color:red; font-weight:bold;'>⚠️ [시스템 경고] 응답이 토큰 한도에 도달하여 중간에 끊겼습니다. max_tokens를 늘려 주세요.</div>"
        return result_text
    except Exception as e:
        return f"<div style='color:red;'>🚨 Claude AI 서버 통신 장애: {e}</div>"

def call_claude_api(prompt_text, max_tokens=32000):
    return _call_claude(prompt_text, max_tokens=max_tokens)

# 🎯 [신청인] 사주간지 역산 전용 콜백
def do_auto_fill_user():
    st.session_state['app_running'] = False
    u_ry, u_rm, u_rd, u_rt = st.session_state.get("u_ry_rev", ""), st.session_state.get("u_rm_rev", ""), st.session_state.get("u_rd_rev", ""), st.session_state.get("u_rt_rev", "")

    def _extract(text):
        if not text: return ""
        text = text.replace(" ", "").replace("년", "").replace("월", "").replace("일", "").replace("시", "")
        g_char, j_char = "?", "?"
        for c in text:
            if g_char == "?" and c in "甲乙丙丁戊己庚辛壬癸갑을병정무기경신임계":
                g_char = c; continue
            if j_char == "?" and c in "子丑寅卯辰巳午未申酉戌亥자축인묘진사오미신유술해":
                j_char = c
        return g_char + j_char

    _ry, _rm, _rd = _extract(u_ry), _extract(u_rm), _extract(u_rd)

    if not _ry or _ry == "??" or not _rm or _rm == "??" or not _rd or _rd == "??":
        st.session_state.pop('rev_matches_user', None)
        st.session_state['rev_error_msg'] = "간지를 정확히 입력하세요."
        return

    ry_h = engine.K2H_GAN.get(_ry[0], _ry[0]) + engine.K2H_JI.get(_ry[1], _ry[1])
    rm_h = engine.K2H_GAN.get(_rm[0], _rm[0]) + engine.K2H_JI.get(_rm[1], _rm[1])
    rd_h = engine.K2H_GAN.get(_rd[0], _rd[0]) + engine.K2H_JI.get(_rd[1], _rd[1])
    
    rt_ji = None
    if u_rt:
        clean_rt = u_rt.replace("시", "").strip()
        if clean_rt: rt_ji = engine.K2H_JI.get(clean_rt[-1], clean_rt[-1])

    base_year = dt_mod.datetime.now().year
    matched_results = engine.search_dates_by_ganji(ry_h, rm_h, rd_h, rt_ji, base_year)

    if matched_results:
        st.session_state['rev_matches_user'] = matched_results
        st.session_state['s_y'] = matched_results[0]["y"]
        st.session_state['s_m'] = matched_results[0]["m"]
        st.session_state['s_d'] = matched_results[0]["d"]
        if matched_results[0]["t"] != "시간 모름":
            st.session_state['s_t'] = matched_results[0]["t"]
            st.session_state['s_t_select'] = matched_results[0]["t"]
        st.session_state.pop('rev_error_msg', None)
    else:
        st.session_state.pop('rev_matches_user', None)
        st.session_state['rev_error_msg'] = "일치하는 날짜가 없습니다."

# 🎯 [상대방] 사주간지 역산 전용 콜백
def do_auto_fill_partner():
    st.session_state['app_running'] = False
    p_ry, p_rm, p_rd, p_rt = st.session_state.get("p_ry_rev", ""), st.session_state.get("p_rm_rev", ""), st.session_state.get("p_rd_rev", ""), st.session_state.get("p_rt_rev", "")

    def _extract(text):
        if not text: return ""
        text = text.replace(" ", "").replace("년", "").replace("월", "").replace("일", "").replace("시", "")
        g_char, j_char = "?", "?"
        for c in text:
            if g_char == "?" and c in "甲乙丙丁戊己庚辛壬癸갑을병정무기경신임계":
                g_char = c; continue
            if j_char == "?" and c in "子丑寅卯辰巳午未申酉戌亥자축인묘진사오미신유술해":
                j_char = c
        return g_char + j_char

    _p_ry, _p_rm, _p_rd = _extract(p_ry), _extract(p_rm), _extract(p_rd)

    if not _p_ry or _p_ry == "??" or not _p_rm or _p_rm == "??" or not _p_rd or _p_rd == "??":
        st.session_state.pop('rev_matches_partner', None)
        st.session_state['rev_p_error_msg'] = "간지를 정확히 입력하세요."
        return

    p_ry_h = engine.K2H_GAN.get(_p_ry[0], _p_ry[0]) + engine.K2H_JI.get(_p_ry[1], _p_ry[1])
    p_rm_h = engine.K2H_GAN.get(_p_rm[0], _p_rm[0]) + engine.K2H_JI.get(_p_rm[1], _p_rm[1])
    p_rd_h = engine.K2H_GAN.get(_p_rd[0], _p_rd[0]) + engine.K2H_JI.get(_p_rd[1], _p_rd[1])
    
    p_rt_ji = None
    if p_rt:
        clean_p_rt = p_rt.replace("시", "").strip()
        if clean_p_rt: p_rt_ji = engine.K2H_JI.get(clean_p_rt[-1], clean_p_rt[-1])

    base_year = dt_mod.datetime.now().year
    matched_results = engine.search_dates_by_ganji(p_ry_h, p_rm_h, p_rd_h, p_rt_ji, base_year)

    if matched_results:
        st.session_state['rev_matches_partner'] = matched_results
        st.session_state['p_y_in'] = matched_results[0]["y"]
        st.session_state['p_m_in'] = matched_results[0]["m"]
        st.session_state['p_d_in'] = matched_results[0]["d"]
        if matched_results[0]["t"] != "시간 모름":
            st.session_state['p_t_key'] = matched_results[0]["t"]
            st.session_state['p_t_select_key'] = matched_results[0]["t"]
        st.session_state.pop('rev_p_error_msg', None)
    else:
        st.session_state.pop('rev_matches_partner', None)
        st.session_state['rev_p_error_msg'] = "일치하는 날짜가 없습니다."

# ==============================================================================
# 2. 사이드바 통제 센터 및 스코프(변수) 정규화
# ==============================================================================
is_admin_mode = st.session_state.get('admin_proc_id') is not None

# 모든 기능 동작 변수를 '최상단'에 기본값으로 선언 (NameError 원천 차단)
run_iljin_calc = False
run_delivery_calc = False
compare_mode = "자동대조"
other_reading_text = ""
start_date = None
end_date = None
target_date = None
tackil_purpose = "이사"
wealth_goal = ""
career_purpose = ""
career_goal = ""
love_goal = ""
health_goal = ""
baby_gender = "미정"

if is_admin_mode:
    selected_target_date = st.session_state.get('target_date', dt_mod.datetime.now(pytz.timezone('Asia/Seoul')).date())
    main_category = st.session_state.get('main_category', '1. 개인 사주팔자 풀이 (종합)')
    u_product = st.session_state.get('sub_category_1', '1-1. 사주팔자와 운세풀이')
    if "2." in main_category: u_product = st.session_state.get('sub_category_2', '2-1. 재물운 특화 분석')
    elif "3." in main_category: u_product = st.session_state.get('sub_category_3', '3-1. 커플 연애/결혼운 (궁합) 풀이')
    elif "4." in main_category: u_product = st.session_state.get('sub_category_4', '4-1. 타 감명서 비교 (사주)')
    
    name, gender, u_marital, u_cal = st.session_state.get('u_n', '고객'), st.session_state.get('u_g', '여성'), st.session_state.get('u_m_stat', '선택'), st.session_state.get('u_c', '양력')
    b_year, b_month, b_day, b_time = st.session_state.get('s_y', 1980), st.session_state.get('s_m', 1), st.session_state.get('s_d', 1), st.session_state.get('s_t', '시간 모름')
    is_1person = not ("3-" in u_product or "4-2." in u_product)
    is_2person = ("3-" in u_product or "4-2." in u_product)
    
    f_name, f_gender, f_marital, f_cal = st.session_state.get('f_n', '상대방'), st.session_state.get('f_g', '남성'), st.session_state.get('f_m_stat', '선택'), st.session_state.get('f_c', '양력')
    f_y, f_m, f_d, f_t = st.session_state.get('p_y_in', 1980), st.session_state.get('p_m_in', 1), st.session_state.get('p_d_in', 1), st.session_state.get('p_t_key', '시간 모름')

else:
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
        selected_target_date = st.date_input(
            "조회할 연/월/일 선택",
            value=st.session_state.get('target_date', dt_mod.date.today()),
            on_change=stop_ai,
            key="main_target_date_picker"
        )
        st.caption(f"💡 현재 지정 기준일: **{selected_target_date.year}년 {selected_target_date.month}월 {selected_target_date.day}일**")
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

        st.markdown("<div style='font-family: \"Nanum Gothic\", sans-serif; font-size: 16px; font-weight: 800; color: #111111; margin-top: 14px; margin-bottom: 8px;'>📋 분석 상품 선택</div>", unsafe_allow_html=True)

        main_category = st.selectbox(
            "어떤 상담을 원하십니까?", 
            ["1. 개인 사주팔자 풀이 (종합)", "2. 테마별 특성화 상담", "3. 커플 연애/결혼운 (궁합) 풀이", "4. 타 감명서 비교"], 
            key="main_category", 
            on_change=stop_ai
        )

        u_product = "1-1. 사주팔자와 운세풀이"
        if main_category == "1. 개인 사주팔자 풀이 (종합)":
            u_product = st.radio("상세 분석 항목:", ["1-1. 사주팔자와 운세풀이", "1-2. 올 해 (특정 연도) 운세 상세분석", "1-3. 이번 달 (특정 월) 운세 상세분석", "1-4. 이번(특정) 주 및 일 운세 상세분석"], key="sub_category_1", on_change=stop_ai)
        elif main_category == "2. 테마별 특성화 상담":
            u_product = st.radio("특성화 상품 선택:", ["2-1. 재물운 특화 분석", "2-2. 직업/진학운 특화 분석", "2-3. 연애/결혼운 특화 분석", "2-4. 건강운 특화 분석", "2-5. 이사 및 개업 택일"], key="sub_category_2", on_change=stop_ai)
        elif main_category == "3. 커플 연애/결혼운 (궁합) 풀이":
            u_product = st.radio("상세 분석 항목:", ["3-1. 연애/결혼운 (궁합) 풀이", "3-2. 결혼 택일", "3-3. 출산 택일"], key="sub_category_3", on_change=stop_ai)
        elif main_category == "4. 타 감명서 비교":
            u_product = st.radio("타 감명서 비교:", ["4-1. 타 감명서 비교 (사주)", "4-2. 타 감명서 비교 (궁합)"], key="sub_category_4", on_change=stop_ai)
            
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

        # =========================================================================
        # 🔍 [신청인] 사주간지 역산 UI
        # =========================================================================
        with st.expander("🔍 신청인 사주간지 역산", expanded=False):
            col_g1, col_g2 = st.columns(2)
            with col_g1: st.text_input("년주", key="u_ry_rev", on_change=stop_ai)
            with col_g2: st.text_input("월주", key="u_rm_rev", on_change=stop_ai)
            col_g3, col_g4 = st.columns(2)
            with col_g3: st.text_input("일주", key="u_rd_rev", on_change=stop_ai)
            with col_g4: st.text_input("시주", key="u_rt_rev", on_change=stop_ai)

            st.button("🔍 신청인 생년월일 자동입력", use_container_width=True, key="btn_user_rev", on_click=do_auto_fill_user)

            if 'rev_matches_user' in st.session_state and st.session_state['rev_matches_user']:
                matches = st.session_state['rev_matches_user']
                if len(matches) > 1:
                    st.success(f"💡 일치하는 생년월일이 **{len(matches)}건** 검색되었습니다.")
                    cur_y_val = st.session_state.get('s_y')
                    match_opts = [m['display'] for m in matches]
                    default_idx = 0
                    for idx, m in enumerate(matches):
                        if m['y'] == cur_y_val:
                            default_idx = idx; break

                    def on_select_user_match():
                        sel_str = st.session_state.get('user_match_selector')
                        for m in matches:
                            if m['display'] == sel_str:
                                st.session_state['s_y'] = m['y']
                                st.session_state['s_m'] = m['m']
                                st.session_state['s_d'] = m['d']
                                if m['t'] != "시간 모름":
                                    st.session_state['s_t'] = m['t']
                                    st.session_state['s_t_select'] = m['t']
                                break
                        stop_ai()

                    st.radio("📅 적용할 생년월일 선택:", options=match_opts, index=default_idx, key="user_match_selector", on_change=on_select_user_match)
                else:
                    st.success(f"✅ {matches[0]['display'].replace(chr(10), ' ')}")

            if 'rev_error_msg' in st.session_state:
                st.error(st.session_state['rev_error_msg'])
                del st.session_state['rev_error_msg']

        # 👤 신청인 기본 정보 입력
        st.markdown("<div style='font-family: \"Nanum Gothic\", sans-serif; font-size: 16px; font-weight: 800; color: #111111; margin-top: 14px; margin-bottom: 8px;'>👤 신청인 기본 정보</div>", unsafe_allow_html=True)
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

        # 🌟 상품별 특수 입력 분기
        is_1person = not (main_category == "3. 커플 연애/결혼운 (궁합) 풀이" or "4-2." in u_product)
        is_2person = (main_category == "3. 커플 연애/결혼운 (궁합) 풀이") or ("4-2." in u_product)
        
        if is_1person:
            if u_product.startswith("1-"):
                is_vip_package = st.checkbox("👑 VIP 패키지 모드", value=st.session_state.get("is_vip_package_val", False), key="is_vip_package_val", on_change=stop_ai)
            if "1-4." in u_product:
                run_iljin_calc = st.checkbox("🔮 일운 운세 분석 가동", value=False)
                if run_iljin_calc: target_date = st.date_input("일운 기준일", value=selected_target_date, key="daily_calc_date", on_change=stop_ai)
            elif "2-1." in u_product: wealth_goal = st.text_input("💰 고민되는 금전 문제는?", key="wealth_goal", on_change=stop_ai)
            elif "2-2." in u_product: 
                career_purpose = st.radio("💼 상담 목적 선택", ["직업·취업·이직", "진학·입시·학업"], key="career_purpose", on_change=stop_ai)
                career_goal = st.text_input("고민되는 진학/직업 분야는?", key="career_goal", on_change=stop_ai)
            elif "2-3." in u_product: love_goal = st.text_input("💘 고민되는 연애/이성 문제는?", key="love_goal", on_change=stop_ai)
            elif "2-4." in u_product: health_goal = st.text_input("🩺 좋지 않은 건강 부위는?", key="health_goal", on_change=stop_ai)
            elif "2-5." in u_product:
                tackil_purpose = st.radio("🗓️ 택일 목적", ["이사", "개업"], key="tackil_purpose", on_change=stop_ai)
                col_start, col_end = st.columns(2)
                start_date = col_start.date_input("시작일", key="moving_start", on_change=stop_ai)
                end_date = col_end.date_input("종료일", key="moving_end", on_change=stop_ai)
            elif "4-1." in u_product:
                st.markdown("---")
                compare_mode = st.radio("대조 분석 모드", ["전통 명리학과 1:1 자동 대조", "외부 타 감명서 원문 대조"], index=0, key="compare_mode_1")
                if compare_mode == "외부 타 감명서 원문 대조":
                    other_reading_text = st.text_area("비교할 타 감명서 (사주) 원문을 넣어 주세요.", height=150, key="text_4_1")

        # =========================================================================
        # 🔍 [상대방] 정보 및 사주간지 역산 UI
        # =========================================================================
        if is_2person:
            st.markdown("<hr style='border:1px dashed #C62828; margin:15px 0;'>", unsafe_allow_html=True)
            with st.expander("🔍 상대방 사주간지 역산", expanded=False):
                p_col_g1, p_col_g2 = st.columns(2)
                with p_col_g1: st.text_input("상대방 년주", key="p_ry_rev", on_change=stop_ai)
                with p_col_g2: st.text_input("상대방 월주", key="p_rm_rev", on_change=stop_ai)
                p_col_g3, p_col_g4 = st.columns(2)
                with p_col_g3: st.text_input("상대방 일주", key="p_rd_rev", on_change=stop_ai)
                with p_col_g4: st.text_input("상대방 시주", key="p_rt_rev", on_change=stop_ai)
                
                st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="btn_partner_rev", on_click=do_auto_fill_partner)

                if 'rev_matches_partner' in st.session_state and st.session_state['rev_matches_partner']:
                    p_matches = st.session_state['rev_matches_partner']
                    if len(p_matches) > 1:
                        st.success(f"💡 상대방 일치 날짜가 **{len(p_matches)}건** 검색되었습니다.")
                        cur_p_y_val = st.session_state.get('p_y_in')
                        p_match_opts = [m['display'] for m in p_matches]
                        p_default_idx = 0
                        for idx, m in enumerate(p_matches):
                            if m['y'] == cur_p_y_val:
                                p_default_idx = idx; break

                        def on_select_partner_match():
                            sel_p_str = st.session_state.get('partner_match_selector')
                            for m in p_matches:
                                if m['display'] == sel_p_str:
                                    st.session_state['p_y_in'] = m['y']
                                    st.session_state['p_m_in'] = m['m']
                                    st.session_state['p_d_in'] = m['d']
                                    if m['t'] != "시간 모름":
                                        st.session_state['p_t_key'] = m['t']
                                        st.session_state['p_t_select_key'] = m['t']
                                    break
                            stop_ai()

                        st.radio("📅 적용할 상대방 생년월일 선택:", options=p_match_opts, index=p_default_idx, key="partner_match_selector", on_change=on_select_partner_match)
                    else:
                        st.success(f"✅ {p_matches[0]['display'].replace(chr(10), ' ')}")

                if 'rev_p_error_msg' in st.session_state:
                    st.error(st.session_state['rev_p_error_msg'])
                    del st.session_state['rev_p_error_msg']

            st.markdown("<div style='font-family: \"Nanum Gothic\", sans-serif; font-size: 16px; font-weight: 800; color: #111111; margin-top: 14px; margin-bottom: 8px;'>💕 상대방 기본 정보</div>", unsafe_allow_html=True)
            f_name = st.text_input("상대방 이름", value=st.session_state.get("f_n", ""), placeholder="심청이", key="f_n", on_change=stop_ai)
            f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_g", on_change=sync_user_gender)
            f_marital = st.selectbox("상대방 혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="f_m_stat", on_change=stop_ai)
            f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c", on_change=stop_ai)
            
            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1: f_y = st.number_input("년도(상대)", 1900, 2050, value=st.session_state.get("p_y_in", 1990), key="p_y_in", on_change=stop_ai)
            with p_col2: f_m = st.number_input("월(상대)", 1, 12, value=st.session_state.get("p_m_in", 1), key="p_m_in", on_change=stop_ai)
            with p_col3: f_d = st.number_input("일(상대)", 1, 31, value=st.session_state.get("p_d_in", 1), key="p_d_in", on_change=stop_ai)
            
            curr_p_t = st.session_state.get("p_t_key", idx_list[0])
            p_t_idx = idx_list.index(curr_p_t) if curr_p_t in idx_list else 0
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
                run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석 가동", value=True, key="run_delivery_calc_cb", on_change=stop_ai)
                if run_delivery_calc:
                    today_dt = dt_mod.date.today()
                    last_period_date = st.date_input("마지막 생리 시작일", value=today_dt - dt_mod.timedelta(days=30), key="last_period_date", on_change=stop_ai)
                    period_cycle = st.number_input("평균 생리 주기 (일)", 20, 45, value=30, key="period_cycle", on_change=stop_ai)
                    col_d1, col_d2 = st.columns(2)
                    delivery_start_date = col_d1.date_input("탐색 시작일", value=today_dt, key="delivery_start_date", on_change=stop_ai)
                    delivery_end_date = col_d2.date_input("탐색 종료일", value=today_dt + dt_mod.timedelta(days=365), key="delivery_end_date", on_change=stop_ai)
                    baby_gender = st.radio("태아 성별", ["미정", "남아", "여아"], key="baby_gender", on_change=stop_ai)
            elif "4-2." in u_product:
                st.markdown("---")
                compare_mode = st.radio("대조 분석 모드", ["전통 명리학과 1:1 자동 대조", "외부 타 감명서 원문 대조"], index=0, key="compare_mode_2")
                if compare_mode == "외부 타 감명서 원문 대조":
                    other_reading_text = st.text_area("비교할 타 감명서 (궁합) 원문을 넣어 주세요.", height=150, key="text_4_2")

        st.markdown("---")
        
        # 🚨 [가동 모터] 버튼을 눌렀을 때 엔진 활성화! 
        btn_single = st.button("✨ [초연 시공명리 풀이 가동]", key="btn_run", use_container_width=True, type="primary")

        if st.button("🖨️ 풀이 결과 인쇄 / PDF 저장", key="btn_print", use_container_width=True, type="secondary"):
            components.html("<script>setTimeout(function(){ window.parent.print(); }, 1500);</script>", height=0)

        if btn_single:
            check_u_name = st.session_state.get('u_n', '')
            check_f_name = st.session_state.get('f_n', '')

            if not check_u_name.strip(): 
                st.warning("⚠️ 신청인의 이름을 입력해 주세요.")
            elif (main_category == "4. 타 감명서 비교") and compare_mode == "외부 타 감명서 원문 대조" and not other_reading_text.strip():
                st.warning("⚠️ 타 감명서 원문을 입력해 주세요.")
            elif is_2person and not check_f_name.strip(): 
                st.warning("⚠️ 상대방의 이름을 입력해 주세요.")
            else:
                st.session_state['app_running'] = True
                for key in ['saved_report_html', 'saved_report_2', 'saved_report_gh_cover', 'saved_report_gh_m', 'saved_report_gh_f', 'saved_report_gh_g', 'saved_report_del', 'saved_report_iljin']:
                    if key in st.session_state: del st.session_state[key]

                if is_1person and run_iljin_calc:
                    st.session_state['need_calc'] = True
                    st.session_state['run_waterfall'] = True
                elif is_2person and run_delivery_calc:
                    st.session_state['need_calc'] = True
                    st.session_state['run_delivery_only'] = True
                else:
                    st.session_state['need_calc'] = True
                    st.session_state['run_waterfall'] = False
                    st.session_state['run_delivery_only'] = False
                st.rerun()

# ==============================================================================
# 3. 메인 화면 범용 연산 및 AI 통변 모듈 연동부 
# ==============================================================================
if st.session_state.get('app_running', False):
    st.session_state['app_running'] = False  # 🛡️ 진입 즉시 플래그 리셋 (중간에 오류가 나도 다음 클릭에서 재실행되지 않도록 안전장치)

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
    u_icon = "♂️" if gender == "남성" else "♀️"
    today_str = selected_target_date.strftime("%Y년 %m월 %d일")

    def extract_time(time_str):
        if "모름" in time_str: return 0, 0
        match = re.search(r'(\d{2}):(\d{2})', time_str)
        return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

    spinner_msg = f"⏳ [{u_product.strip()}] 시공명리 연산 및 정밀 통변 가동 중..."

    with st.spinner(spinner_msg):
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
            gan_arr = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
            ji_arr = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
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
        
        if u_product.startswith("1-1"): report_title = "사주팔자 및 총 운세 풀이"
        elif u_product.startswith("1-2"): report_title = "올 해 운세 풀이"
        elif u_product.startswith("1-3"): report_title = "이번 달 운세 풀이"
        elif u_product.startswith("1-4"): report_title = "주간 및 일일 운세 풀이"
        elif u_product.startswith("2-1"): report_title = "재물운 특화 풀이"
        elif u_product.startswith("2-2"): report_title = "직업/진학운 특화 풀이"
        elif u_product.startswith("2-3"): report_title = "연애/결혼운 특화 풀이"
        elif u_product.startswith("2-4"): report_title = "건강운 특화 풀이"
        elif u_product.startswith("2-5"): report_title = "이사/개업 택일 추천"
        elif u_product.startswith("3-1"): report_title = "연애/결혼운 (궁합) 풀이"
        elif u_product.startswith("3-2"): report_title = "결혼 택일 추천"
        elif u_product.startswith("3-3"): report_title = "출산 택일 추천"
        elif u_product.startswith("4-1"): report_title = "타 감명서 비교 (사주)"
        elif u_product.startswith("4-2"): report_title = "타 감명서 비교 (궁합)"
        else: report_title = "사주팔자 정밀 분석"

        # 🌟 대제목 렌더링
        main_title_html = html_views.get_main_title_html(report_title) if hasattr(html_views, 'get_main_title_html') else f"<h2 style='text-align:center;'>{report_title}</h2>"

        # ----------------------------------------------------------------------
        # 단일 분기: 2인용 vs 1인용 파트너 연산 및 표지 구성
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
            p_name_val = st.session_state.get("f_n", "상대방")
            p_time_val = p_time_str
            
            p_klc = KoreanLunarCalendar()
            if p_is_lunar:
                p_klc.setLunarDate(int(p_y), int(p_m), int(p_d), p_is_leap)
                p_sol_str_val = f"{p_klc.solarYear}년 {p_klc.solarMonth:02d}월 {p_klc.solarDay:02d}일"
                p_lun_str_val = f"{p_y}년 {int(p_m):02d}월 {int(p_d):02d}일 ({'윤달' if p_is_leap else '평달'})"
            else:
                p_klc.setSolarDate(int(p_y), int(p_m), int(p_d))
                p_sol_str_val = f"{p_y}년 {int(p_m):02d}월 {int(p_d):02d}일"
                p_leap_txt = "윤달" if getattr(p_klc, 'isIntercalary', False) else "평달"
                p_lun_str_val = f"{p_klc.lunarYear}년 {p_klc.lunarMonth:02d}월 {p_klc.lunarDay:02d}일 ({p_leap_txt})"
            
            m_name_val = name if gender == "남성" else p_name_val
            m_age_val = age if gender == "남성" else p_age_val
            m_sol_val = sol_str_fmt if gender == "남성" else p_sol_str_val
            m_lun_val = lun_str_fmt if gender == "남성" else p_lun_str_val
            m_time_val = time_str_fmt if gender == "남성" else p_time_val

            f_name_val = p_name_val if gender == "남성" else name
            f_age_val = p_age_val if gender == "남성" else age
            f_sol_val = p_sol_str_val if gender == "남성" else sol_str_fmt
            f_lun_val = p_lun_str_val if gender == "남성" else lun_str_fmt
            f_time_val = p_time_val if gender == "남성" else time_str_fmt

            # 🎯 2인용 궁합 표지: 남명(♂️)과 여명(♀️) 데이터를 정확한 자리에 고정 바인딩
            cover_html = html_views.get_couple_cover(
                APP_VERSION, 
                report_title, 
                "♂️", 
                m_name_val, 
                m_age_val, 
                m_sol_val, 
                m_lun_val, 
                m_time_val,
                "♀️", 
                f_name_val, 
                f_age_val, 
                f_sol_val, 
                f_lun_val, 
                f_time_val, 
                today_str
            )
            
            male_data_pack = [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"] if gender == "남성" else partner_bazi
            female_data_pack = partner_bazi if gender == "남성" else [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"]
            
            try:
                if hasattr(engine, 'UniversalPrintableGunghap'):
                    gh_engine = engine.UniversalPrintableGunghap(m_name_val, f_name_val, male_data_pack, female_data_pack, 10)
                    gh_engine.run_universal_logic()
                    gh_score = gh_engine.final_score
                    gh_grade = gh_engine.grade
                else:
                    gh_score = 0
                    gh_grade = ""
            except Exception:
                gh_score, gh_grade = 0, "점수 산출 불가"
                
        else:
            # 🎯 1인용 개인 모드: 1인용 표지(get_personal_cover, 8개 인자) 호출
            gh_score = 0
            gh_grade = ""
            partner_bazi = ["?", "?", "?", "?"]

            cover_html = html_views.get_personal_cover(
                APP_VERSION, 
                report_title, 
                u_icon, 
                name, 
                sol_str_fmt, 
                lun_str_fmt, 
                time_str_fmt, 
                today_str
            )

        info_h = html_views.get_info_header(u_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, time_str_fmt)
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
                engine.get_12_shinsal(yb, tj), engine.get_12_shinsal(db, tj), bg_col, b_left, is_cur_yr)
            
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
                engine.get_12_shinsal(db, wj_hanja), bg_col, b_left, is_cur_m)

        wolun_html = html_views.get_wolun_layout(f"[ 월운의 흐름 ({curr_year}년도 양력기준) ]", wol_content)

        w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{db}".strip()
        w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
        i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
        struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
        
        gyukgook, gyukgook_detail = engine.get_gyukgook_detailed(ds, ys, ms, hs, mb)
        golden_text_html = html_views.get_golden_text(name, w_val, i_val, struct_data[0], struct_data[1], struct_data[2], mb=mb, gyuk_name=gyukgook)

        golden_box_gunghap_html = golden_text_html
        if is_2person:
            try:
                p_ys = partner_bazi[3][0] if len(partner_bazi[3]) > 0 else "甲"
                p_yb = partner_bazi[3][1] if len(partner_bazi[3]) > 1 else "子"
                p_ms = partner_bazi[2][0] if len(partner_bazi[2]) > 0 else "甲"
                p_mb = partner_bazi[2][1] if len(partner_bazi[2]) > 1 else "子"
                p_ds = partner_bazi[1][0] if len(partner_bazi[1]) > 0 else "甲"
                p_db = partner_bazi[1][1] if len(partner_bazi[1]) > 1 else "子"
                p_hs = partner_bazi[0][0] if len(partner_bazi[0]) > 0 and partner_bazi[0][0] != '?' else "甲"
                
                p_w_key = f"{p_ms}{p_mb}".strip()
                p_i_key = f"{p_ds}{p_db}".strip()
                p_w_val = choyeon_db.get("wolryeong", {}).get(p_w_key, f"[{p_w_key}] 시공간 데이터 없음")
                p_i_val = choyeon_db.get("ilju", {}).get(p_i_key, f"[{p_i_key}] 성품 데이터 없음")
                p_struct_data = choyeon_db.get("ilju_structure", {}).get(p_i_key, ["구조 미상", "유형 미상", "성향 미상"])
                
                p_gyuk, _ = engine.get_gyukgook_detailed(p_ds, p_ys, p_ms, p_hs, p_mb)
                
                p_golden_html = html_views.get_golden_text(
                    p_name_val, p_w_val, p_i_val, 
                    p_struct_data[0], p_struct_data[1], p_struct_data[2], 
                    mb=p_mb, gyuk_name=p_gyuk)
                
                m_g_html = golden_text_html if gender == "남성" else p_golden_html
                f_g_html = p_golden_html if gender == "남성" else golden_text_html
                
                if hasattr(html_views, 'get_couple_golden_text'):
                    golden_box_gunghap_html = html_views.get_couple_golden_text(m_name_val, m_g_html, f_name_val, f_g_html)
                else:
                    golden_box_gunghap_html = f"{m_g_html}<br>{f_g_html}"
            except Exception as e:
                golden_box_gunghap_html = golden_text_html

        closing_html = html_views.get_closing_html(name)            
        closing_part = str(closing_html or "").strip()

        part_1_fact = (
            str(main_title_html or "") + 
            str(info_h or "") + 
            str(table_html or "") + 
            str(master_bar_html or "") + 
            str(un_html or "")
        )
        
        part_2_intro = str(intro_html or "")
        part_3_golden = str(golden_text_html or "")
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

        adv_saju_data = {'year_ji': yb, 'month_ji': mb, 'day_ji': db, 'hour_ji': hb}
        if hasattr(engine, 'analyze_saju_facts_advanced'):
            sewun_ji_param = curr_y_ji if 'curr_y_ji' in locals() else "-"
            _, _, adv_flags = engine.analyze_saju_facts_advanced(adv_saju_data, dw_j_cur, sewun_ji_param)
            adv_warning_str = adv_flags.get("warning_message", "정상 시공간 흐름")
            health_erosion_str = adv_flags.get("health_erosion_facts", "특이 침식 파동 없음")
            action_solutions_str = adv_flags.get("action_solutions", "자연스러운 기운의 순환을 유지하며 긍정적 마음가짐 유지")
            spouse_issue_str = adv_flags.get("spouse_issue_facts", "배우자궁 비교적 안정적 흐름 유지")
        else:
            adv_warning_str = "정상 시공간 흐름"
            health_erosion_str = "특이 침식 파동 없음"
            action_solutions_str = "자연스러운 기운의 순환을 유지하며 긍정적 마음가짐 유지"
            spouse_issue_str = "배우자궁 비교적 안정적 흐름 유지"
        
        if u_product.startswith("2-4") and hasattr(engine, 'analyze_health_erosion_4d'):
            temp_sewun_10_list = []
            for i in range(10):
                ty = start_year + i
                temp_sewun_10_list.append({'year': ty, 'ji': engine.JI[(ty - 1984) % 60 % 12]})
                
            health_erosion_str = engine.analyze_health_erosion_4d(
                saju_data={'ji': [hb, db, mb, yb], 'current_dw_ji': dw_j_cur, 'current_sewun_ji': engine.JI[(curr_year - 1984) % 60 % 12]},
                daewun_list=daewun_data_list,
                sewun_10_list=temp_sewun_10_list,
                curr_year=curr_year
            )

        adv_gan_data = {'year_gan': ys, 'month_gan': ms, 'day_gan': ds, 'hour_gan': hs}
        if hasattr(html_views, 'analyze_samja_combination'):
            samja_comb_facts = html_views.analyze_samja_combination(adv_gan_data, dw_g_cur)
        else:
            samja_comb_facts = "원국 특이 삼자조합 없음"
        
        try:
            shinsal_raw = engine.get_general_shinsal_filtered(1, gans, jjis, gender) if hasattr(engine, 'get_general_shinsal_filtered') else []
        except Exception:
            shinsal_raw = []
        shinsal_str = ", ".join([re.sub(r'<[^>]+>', '', str(s)) for s in shinsal_raw]) if shinsal_raw else "특이 신살 없음"

        w_facts = engine.get_woonse_analysis_facts(ds, db, dw_g_cur, dw_j_cur, engine.GAN[(curr_year-1984)%60%10], engine.JI[(curr_year-1984)%60%12], "丙", "午", "甲", "子")

        if is_2person:
            m_h_raw = male_data_pack[0] if len(male_data_pack) > 0 else ""
            m_d_p = male_data_pack[1] if len(male_data_pack) > 1 else "甲子"
            m_m_p = male_data_pack[2] if len(male_data_pack) > 2 else "甲子"
            m_y_p = male_data_pack[3] if len(male_data_pack) > 3 else "甲子"

            f_h_raw = female_data_pack[0] if len(female_data_pack) > 0 else ""
            f_d_p = female_data_pack[1] if len(female_data_pack) > 1 else "甲子"
            f_m_p = female_data_pack[2] if len(female_data_pack) > 2 else "甲子"
            f_y_p = female_data_pack[3] if len(female_data_pack) > 3 else "甲子"

            m_h_p = "미상(시간 모름)" if (not m_h_raw or "?" in m_h_raw or "-" in m_h_raw) else m_h_raw
            f_h_p = "미상(시간 모름)" if (not f_h_raw or "?" in f_h_raw or "-" in f_h_raw) else f_h_raw

            m_gyuk_val = gyukgook_detail if gender == '남성' else (p_gyuk if 'p_gyuk' in locals() else "격국 분석")
            f_gyuk_val = (p_gyuk if 'p_gyuk' in locals() else "격국 분석") if gender == '남성' else gyukgook_detail

            saju_fact_summary = f"""
[남명({m_name_val}) 사주 팩트]
- 명조: {m_sol_val}생 (음력 {m_lun_val}) / {m_time_val}
- 사주팔자: 년주({m_y_p}), 월주({m_m_p}), 일주({m_d_p}), 시주({m_h_p})
- 격국: {m_gyuk_val}

[여명({f_name_val}) 사주 팩트]
- 명조: {f_sol_val}생 (음력 {f_lun_val}) / {f_time_val}
- 사주팔자: 년주({f_y_p}), 월주({f_m_p}), 일주({f_d_p}), 시주({f_h_p})
- 격국: {f_gyuk_val}
"""
        else:
            u_h_raw = f"{hs}{hb}"
            u_h_p = "미상(시간 모름)" if (not u_h_raw or "?" in u_h_raw or "-" in u_h_raw) else u_h_raw

            saju_fact_summary = f"""
- 내담자 명조: 년주({ys}{yb}), 월주({ms}{mb}), 일주({ds}{db}), 시주({u_h_p})
- 격국 및 용신 팩트: {gyukgook_detail}
- 원국 오행 분포: 목:{counts['목']}, 화:{counts['화']}, 토:{counts['토']}, 금:{counts['금']}, 수:{counts['수']}
- 공망 궁위 팩트: [년지공망] {n_gong} / [일지공망] {i_gong}
- 삼재 여부: {cur_samjae}
- 시공간 파동 정밀 감지: {adv_warning_str}
"""
        target_year_val = st.session_state.get('target_year_input', curr_year)
        cur_sewun_base = (target_year_val - 1984) % 60
        cur_sewun_gan_val = engine.GAN[cur_sewun_base % 10]
        cur_sewun_ji_val = engine.JI[cur_sewun_base % 12]

        ilju_master_context = engine.get_ilju_master_prompt_context(f"{ds}{db}", choyeon_db)
        seun_first_half, seun_second_half = engine.get_seun_half_periods(target_year_val) if hasattr(engine, 'get_seun_half_periods') else ("상반기(입춘~입추 전)", "하반기(입추~다음해 입춘 전)")
        wolun_first_half, wolun_second_half = engine.get_wolun_half_periods(target_year_val, curr_m) if hasattr(engine, 'get_wolun_half_periods') else ("전반기(절입일~중기 전)", "후반기(중기~다음 절입일 전)")

        user_entered_text = ""
        if u_product.startswith("4-1"):
            user_entered_text = (st.session_state.get("text_4_1", "") or st.session_state.get(f"text_{u_product}", "")).strip()
        elif u_product.startswith("4-2"):
            user_entered_text = (st.session_state.get("text_4_2", "") or st.session_state.get(f"text_{u_product}", "")).strip()

        if user_entered_text:
            user_entered_text = re.sub(r'[▷▶◈\[\]\■\□\●\○\◆\◇\★\☆\※\▪\▫]', '', user_entered_text)

        best_moving_days_str = "길일 연산 엔진 미가동"
        if u_product.startswith("2-5") and hasattr(engine, 'get_best_moving_opening_days'):
            tackil_purpose_val = st.session_state.get('tackil_purpose', '이사')
            start_d_val = st.session_state.get('moving_start', selected_target_date)
            end_d_val = st.session_state.get('moving_end', selected_target_date + dt_mod.timedelta(days=30))
            
            try:
                top3_days = engine.get_best_moving_opening_days(
                    start_date=start_d_val, 
                    end_date=end_d_val, 
                    user_gans=gans, 
                    user_jjis=jjis, 
                    purpose=tackil_purpose_val
                )
                if top3_days:
                    best_moving_days_str = "\n".join([f"[{i+1}순위 추천일]: {d['date']} ({d['ganji'][0]}{d['ganji'][1]}일) / 명리적합도: {d['score']}점" for i, d in enumerate(top3_days)])
                else:
                    best_moving_days_str = "해당 기간 내 적합한 명리적 길일이 없습니다. 기간을 넓혀주세요."
            except Exception as e:
                best_moving_days_str = "길일 연산 중 오류 발생"

        prompt_data = {
            "name": name, "age": age, "gender": gender, "marital": u_marital,
            "ilju_master_prompt_context": ilju_master_context,
            "age_prompt": engine.get_age_prompt(age), "gender_prompt": engine.get_gender_prompt(gender), 
            "marital_prompt": engine.get_marital_prompt(gender, u_marital), "yukchin_rule": engine.get_yukchin_rule(gender, u_marital),
            "saju_fact_summary": saju_fact_summary, "dw_g_cur": dw_g_cur, "dw_j_cur": dw_j_cur, 
            "dw_fact_str": f"현재 {dw_g_cur}{dw_j_cur}대운 가동 중",
            "samhyung_fact_str": engine.check_samhyung_facts([yb, mb, db, hb], dw_j_cur),
            "hang_un_vaults_str": engine.get_hang_un_vaults_str(dw_j_cur, [ys, ms, ds, hs], [yb, mb, db, hb]),
            "adv_warning_str": adv_warning_str,
            "health_erosion_facts": health_erosion_str,
            "samja_comb_facts": samja_comb_facts,
            "action_solutions": action_solutions_str,
            "spouse_issue_facts": spouse_issue_str,
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
            "best_moving_days_str": best_moving_days_str,
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
            if "2-2" in u_prod: 
                return "프롬프트_2_2_진학운" if "진학" in st.session_state.get('career_purpose', '직업') else "프롬프트_2_2_직업운"
            if "2-3" in u_prod: return "프롬프트_2_3_연애운"
            if "2-4" in u_prod: return "프롬프트_2_4_건강운"
            if "2-5" in u_prod: 
                return "프롬프트_2_5_개업_택일" if st.session_state.get('tackil_purpose', '이사') == '개업' else "프롬프트_2_5_이사_택일"
            if "3-1" in u_prod: return "프롬프트_3_1_궁합"
            if "3-2" in u_prod: return "프롬프트_3_2_결혼택일"
            if "3-3" in u_prod: return "프롬프트_3_3_출산택일"
            if "4-1" in u_prod: return "프롬프트_4_1_사주대조"
            if "4-2" in u_prod: return "프롬프트_4_2_궁합대조"
            return "프롬프트_1_1_기본"

        prompt_var_name = get_prompt_var_name(u_product)
        if not hasattr(prompts, prompt_var_name):
            st.error(f"🚨 시스템 경고: prompts.py 파일 안에 '{prompt_var_name}' 변수가 없습니다!")
            target_prompt = getattr(prompts, "프롬프트_1_1_기본", "")
        else:
            target_prompt = getattr(prompts, prompt_var_name, "")

        formatted_prompt = target_prompt.format_map(SafeDict(prompt_data))
        raw_response = call_claude_api(formatted_prompt)
        
        if raw_response and isinstance(raw_response, str):
            clean_raw = raw_response.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
            ai_output_html = html_views.format_ai_text_to_html(clean_raw)
        else:
            ai_output_html = "<p style='padding:20px;'>분석 결과를 불러오지 못했습니다.</p>"

        # ----------------------------------------------------------------------
        # 📦 마커 치환 유틸리티 함수
        # ----------------------------------------------------------------------
        def sub_marker(text, marker_name, table_code):
            safe_table_code = str(table_code)
            pattern = r'[ \t]*\[\s*\*?\*?\s*' + marker_name + r'\s*\*?\*?\s*\]'
            return re.sub(pattern, lambda m: safe_table_code, text, flags=re.IGNORECASE)

        # 안전 변수 로드
        safe_part_1 = str(part_1_fact).replace('\n', ' ') if 'part_1_fact' in locals() else ""
        safe_part_2 = str(part_2_intro).replace('\n', ' ') if 'part_2_intro' in locals() else ""
        safe_part_3 = str(part_3_golden) if 'part_3_golden' in locals() and part_3_golden else ""
        safe_part_1_gh = str(part_1_fact_gunghap).replace('\n', ' ') if 'part_1_fact_gunghap' in locals() else ""

        # ----------------------------------------------------------------------
        # 🔒 [입금확인 보안 규칙] 입금확인 완료 시에만 직인 날인, 미입금 시 미날인
        # ----------------------------------------------------------------------
        is_paid = False
        if is_admin_mode:
            is_paid = True
        elif st.session_state.get('is_paid', False) or st.session_state.get('payment_verified', False):
            is_paid = True
        elif 'admin_orders' in st.session_state:
            curr_gid = st.session_state.get('admin_proc_id', '')
            if curr_gid and st.session_state['admin_orders'].get(curr_gid, {}).get('is_paid', False):
                is_paid = True

        safe_part_5 = html_views.get_choyeon_sign_html() if is_paid and hasattr(html_views, 'get_choyeon_sign_html') else ""
        current_ai = ai_output_html if 'ai_output_html' in locals() and ai_output_html else "<p>분석 결과를 불러오지 못했습니다.</p>"

        final_render_html = ""

        # ==============================================================================
        # 📦 1인용 공통 본문 상단 기본 5대 묶음 (1-1 ~ 2-5, 4-1 사용)
        # ==============================================================================
        base_top_block = f"""
        {main_title_html}
        {info_h}
        {table_html}
        {master_bar_html}
        {un_html}
        """

        # 공통 테이블 및 텍스트 안전 변수 로드
        sewun_table_code = sewun_html if 'sewun_html' in locals() and sewun_html else ""
        wolun_table_code = wolun_html if 'wolun_html' in locals() and wolun_html else ""
        golden_text_code = safe_part_3 if 'safe_part_3' in locals() and safe_part_3 else ""
        intro_block = intro_html if 'intro_html' in locals() and intro_html else ""

        # ==============================================================================
        # 🎯 전 상품(1-1 ~ 4-2) 본문 조립 및 마커 치환 분기
        # ==============================================================================

        # ----------------------------------------------------------------------
        # [1계열] 종합 및 시계열 운세
        # ----------------------------------------------------------------------
        if u_product.startswith("1-1"):
            # 1-1. 사주팔자 및 총 운세 풀이 (기본 5대 묶음 + intro_html + 통변)
            formatted_ai = sub_marker(current_ai, 'DAEWUN_TABLE_HERE', '')
            formatted_ai = sub_marker(formatted_ai, 'SEWUN_TABLE_HERE', sewun_table_code)
            formatted_ai = sub_marker(formatted_ai, 'GOLDEN_TEXT_HERE', golden_text_code)
            formatted_ai = sub_marker(formatted_ai, 'CHOYEON_SIGN_HERE', safe_part_5)
            
            body_content = f"{base_top_block}{intro_block}{formatted_ai}"
            final_render_html = html_views.get_final_report_box(body_content) if hasattr(html_views, 'get_final_report_box') else f"<div class='vip-frame-box'>{body_content}</div>"

        elif u_product.startswith("1-2"):
            # 1-2. 올 해 운세 풀이 (연운)
            formatted_ai = sub_marker(current_ai, 'SEWUN_TABLE_HERE', sewun_table_code)
            formatted_ai = sub_marker(formatted_ai, 'CHOYEON_SIGN_HERE', safe_part_5)
            
            body_content = f"{base_top_block}{formatted_ai}"
            final_render_html = html_views.get_final_report_box(body_content) if hasattr(html_views, 'get_final_report_box') else f"<div class='vip-frame-box'>{body_content}</div>"

        elif u_product.startswith("1-3"):
            # 1-3. 이번 달 운세 풀이 (월운)
            formatted_ai = sub_marker(current_ai, 'SEWUN_TABLE_HERE', sewun_table_code)
            formatted_ai = sub_marker(formatted_ai, 'WOLUN_TABLE_HERE', wolun_table_code)
            formatted_ai = sub_marker(formatted_ai, 'CHOYEON_SIGN_HERE', safe_part_5)
            
            body_content = f"{base_top_block}{formatted_ai}"
            final_render_html = html_views.get_final_report_box(body_content) if hasattr(html_views, 'get_final_report_box') else f"<div class='vip-frame-box'>{body_content}</div>"

        elif u_product.startswith("1-4"):
            # 1-4. 주간 및 일일 운세 풀이 (폭포수 운세)
            weekly_days_data = engine.get_weekly_calendar_data(selected_target_date, ds_hanja) if hasattr(engine, 'get_weekly_calendar_data') else []
            weekly_table_code = html_views.generate_weekly_calendar_html(weekly_days_data, selected_target_date.day, yb, db) if hasattr(html_views, 'generate_weekly_calendar_html') else ""
            
            formatted_ai = sub_marker(current_ai, 'SEWUN_TABLE_HERE', sewun_table_code)
            formatted_ai = sub_marker(formatted_ai, 'WOLUN_TABLE_HERE', wolun_table_code)
            formatted_ai = sub_marker(formatted_ai, 'WEEKLY_CALENDAR_HERE', weekly_table_code)
            formatted_ai = sub_marker(formatted_ai, 'CHOYEON_SIGN_HERE', safe_part_5)
            
            body_content = f"{base_top_block}{formatted_ai}"
            final_render_html = html_views.get_final_report_box(body_content) if hasattr(html_views, 'get_final_report_box') else f"<div class='vip-frame-box'>{body_content}</div>"

        # ----------------------------------------------------------------------
        # [2계열] 2030 테마별 인생 특화 분석 (2-1 ~ 2-5)
        # ----------------------------------------------------------------------
        elif u_product.startswith("2-5"):
            # 2-5. 이사 및 개업 택일 추천
            tackil_target_dt = st.session_state.get('moving_start', selected_target_date)
            weekly_days_data = engine.get_weekly_calendar_data(tackil_target_dt, ds_hanja) if hasattr(engine, 'get_weekly_calendar_data') else []
            weekly_table_code = html_views.generate_weekly_calendar_html(weekly_days_data, tackil_target_dt.day, yb, db) if hasattr(html_views, 'generate_weekly_calendar_html') else ""
            
            formatted_ai = sub_marker(current_ai, 'DAEWUN_TABLE_HERE', '')
            formatted_ai = sub_marker(formatted_ai, 'SEWUN_TABLE_HERE', sewun_table_code)
            formatted_ai = sub_marker(formatted_ai, 'WOLUN_TABLE_HERE', wolun_table_code)
            formatted_ai = sub_marker(formatted_ai, 'WEEKLY_CALENDAR_HERE', weekly_table_code)
            formatted_ai = sub_marker(formatted_ai, 'CHOYEON_SIGN_HERE', safe_part_5)
            
            body_content = f"{base_top_block}{formatted_ai}"
            final_render_html = html_views.get_final_report_box(body_content) if hasattr(html_views, 'get_final_report_box') else f"<div class='vip-frame-box'>{body_content}</div>"

        elif u_product.startswith("2-"):
            # 2-1 ~ 2-4. 재물 / 직업(진학) / 연애 / 건강 특화
            formatted_ai = sub_marker(current_ai, 'DAEWUN_TABLE_HERE', '')  
            formatted_ai = sub_marker(formatted_ai, 'SEWUN_TABLE_HERE', sewun_table_code)
            formatted_ai = sub_marker(formatted_ai, 'WEEKLY_CALENDAR_HERE', '')
            formatted_ai = sub_marker(formatted_ai, 'CHOYEON_SIGN_HERE', safe_part_5)
            
            body_content = f"{base_top_block}{formatted_ai}"
            final_render_html = html_views.get_final_report_box(body_content) if hasattr(html_views, 'get_final_report_box') else f"<div class='vip-frame-box'>{body_content}</div>"

        # ----------------------------------------------------------------------
        # [3계열] 2인용 궁합 및 택일 분석 (3-1 ~ 3-3)
        # ----------------------------------------------------------------------
        elif u_product.startswith("3-1"):
            # 3-1. 연애/결혼운 (궁합) 풀이 (3단 멀티 페이지 분할)
            m_ess, f_ess, g_ess = "", "", current_ai
            m_match = re.search(r'\[MALE_START\](.*?)\[MALE_END\]', current_ai, re.DOTALL)
            if m_match: m_ess = m_match.group(1).strip()
            f_match = re.search(r'\[FEMALE_START\](.*?)\[FEMALE_END\]', current_ai, re.DOTALL)
            if f_match: f_ess = f_match.group(1).strip()
            g_match = re.search(r'\[GUNGHAP_START\](.*?)\[GUNGHAP_END\]', current_ai, re.DOTALL)
            if g_match: g_ess = g_match.group(1).strip()

            m_daewun_html = un_html if gender == "남성" else (p_un_html if 'p_un_html' in locals() else un_html)
            f_daewun_html = (p_un_html if 'p_un_html' in locals() else un_html) if gender == "남성" else un_html
            c_daewun_html = html_views.get_daewun_compare_box(m_name_val, m_daewun_html, f_name_val, f_daewun_html) if hasattr(html_views, 'get_daewun_compare_box') else ""
            
            g_ess = sub_marker(g_ess, 'COUPLE_DAEWUN_TABLES_HERE', c_daewun_html)
            g_ess = sub_marker(g_ess, 'CHOYEON_SIGN_HERE', safe_part_5)

            score_ui, closing_ui = "", ""
            if 'gh_engine' in locals() and hasattr(html_views, 'get_gunghap_score_visual_html'):
                score_ui = html_views.get_gunghap_score_visual_html(gh_engine)
                closing_ui = html_views.get_gunghap_closing(m_name_val, f_name_val) if hasattr(html_views, 'get_gunghap_closing') else ""
            g_ess += score_ui + closing_ui
            
            if hasattr(html_views, 'get_gunghap_three_page_report'):
                final_render_html = html_views.get_gunghap_three_page_report(safe_part_1_gh, m_ess, f_ess, g_ess)
            else:
                p1 = html_views.get_final_report_box(f"{male_info_h if 'male_info_h' in locals() else info_h}{male_table_html if 'male_table_html' in locals() else table_html}{m_ess}")
                p2 = html_views.get_final_report_box(f"{female_info_h if 'female_info_h' in locals() else info_h}{female_table_html if 'female_table_html' in locals() else table_html}{f_ess}")
                p3 = html_views.get_final_report_box(f"{main_title_html}{g_ess}")
                final_render_html = f"{p1}<div style='page-break-before: always;'></div>{p2}<div style='page-break-before: always;'></div>{p3}"

        elif u_product.startswith("3-2"):
            # 3-2. 결혼 택일
            m_target_dt = st.session_state.get('start_date_m', st.session_state.get('target_date_m', selected_target_date))
            weekly_days_data = engine.get_weekly_calendar_data(m_target_dt, ds_hanja) if hasattr(engine, 'get_weekly_calendar_data') else []
            weekly_table_code = html_views.generate_weekly_calendar_html(weekly_days_data, m_target_dt.day, yb, db) if hasattr(html_views, 'generate_weekly_calendar_html') else ""
            
            formatted_ai = sub_marker(current_ai, 'WEEKLY_CALENDAR_HERE', weekly_table_code)
            formatted_ai = sub_marker(formatted_ai, 'CHOYEON_SIGN_HERE', safe_part_5)
            
            couple_header = couple_info_h if 'couple_info_h' in locals() else safe_part_1_gh
            body_content = f"{main_title_html}{couple_header}{formatted_ai}"
            final_render_html = html_views.get_final_report_box(body_content) if hasattr(html_views, 'get_final_report_box') else f"<div class='vip-frame-box'>{body_content}</div>"

        elif u_product.startswith("3-3"):
            # 3-3. 출산 택일
            d_target_dt = st.session_state.get('delivery_start_date', selected_target_date)
            weekly_days_data = engine.get_weekly_calendar_data(d_target_dt, ds_hanja) if hasattr(engine, 'get_weekly_calendar_data') else []
            weekly_table_code = html_views.generate_weekly_calendar_html(weekly_days_data, d_target_dt.day, yb, db) if hasattr(html_views, 'generate_weekly_calendar_html') else ""
            
            formatted_ai = sub_marker(current_ai, 'WEEKLY_CALENDAR_HERE', weekly_table_code)
            formatted_ai = sub_marker(formatted_ai, 'CHOYEON_SIGN_HERE', safe_part_5)
            
            couple_header = couple_info_h if 'couple_info_h' in locals() else safe_part_1_gh
            body_content = f"{main_title_html}{couple_header}{formatted_ai}"
            final_render_html = html_views.get_final_report_box(body_content) if hasattr(html_views, 'get_final_report_box') else f"<div class='vip-frame-box'>{body_content}</div>"

        # ----------------------------------------------------------------------
        # [4계열] 연구소 타 감명서 비교 정밀 분석 (4-1, 4-2)
        # ----------------------------------------------------------------------
        elif u_product.startswith("4-1"):
            # 4-1. 사주 비교 분석 (1인용)
            if not user_entered_text:
                warn_html = html_views.get_warning_box("타 감명서 원문 미입력 경고", "비교 분석을 진행할 <b>[외부 타 감명서 원문 텍스트]</b>가 입력되지 않았습니다.") if hasattr(html_views, 'get_warning_box') else "<p>경고: 원문 누락</p>"
                final_render_html = html_views.get_final_report_box(warn_html)
            else:
                external_raw_box = html_views.get_external_raw_text_box(user_entered_text) if hasattr(html_views, 'get_external_raw_text_box') else f"<div>{user_entered_text}</div>"
                formatted_ai = sub_marker(current_ai, 'CHOYEON_SIGN_HERE', safe_part_5)
                formatted_ai = sub_marker(formatted_ai, 'DAEWUN_TABLE_HERE', '')
                formatted_ai = sub_marker(formatted_ai, 'SEWUN_TABLE_HERE', '')
                
                body_content = f"{base_top_block}{external_raw_box}{formatted_ai}"
                final_render_html = html_views.get_final_report_box(body_content) if hasattr(html_views, 'get_final_report_box') else f"<div class='vip-frame-box'>{body_content}</div>"

        elif u_product.startswith("4-2"):
            # 4-2. 궁합 비교 분석 (2인용)
            if not user_entered_text:
                warn_html = html_views.get_warning_box("타 궁합 감명서 원문 미입력 경고", "비교 분석을 진행할 <b>[외부 타 궁합 감명서 원문 텍스트]</b>가 입력되지 않았습니다.") if hasattr(html_views, 'get_warning_box') else "<p>경고: 궁합 원문 누락</p>"
                final_render_html = html_views.get_final_report_box(warn_html)
            else:
                external_raw_box = html_views.get_external_raw_text_box(user_entered_text) if hasattr(html_views, 'get_external_raw_text_box') else f"<div>{user_entered_text}</div>"
                formatted_ai = sub_marker(current_ai, 'CHOYEON_SIGN_HERE', safe_part_5)
                formatted_ai = sub_marker(formatted_ai, 'COUPLE_DAEWUN_TABLES_HERE', '')
                
                couple_header_box = couple_info_h if 'couple_info_h' in locals() else safe_part_1_gh
                body_content = f"{main_title_html}{couple_header_box}{external_raw_box}{formatted_ai}"
                final_render_html = html_views.get_final_report_box(body_content) if hasattr(html_views, 'get_final_report_box') else f"<div class='vip-frame-box'>{body_content}</div>"

        # ==============================================================================
        # 🚀 [최종 패키징 및 화면 렌더링 - 소스코드 노출 원천 차단]
        # ==============================================================================
        if 'final_render_html' not in locals() or final_render_html is None:
            final_render_html = ""

        safe_cover_str = cover_html if 'cover_html' in locals() and cover_html else ""

        # 본문 프레임 규격 적용 (HTML 태그 앞 공백 없이 인라인 결합하여 마크다운 코드블록 오인 방지)
        if "report-page" not in final_render_html:
            content_body = f"<div class='report-page' style='margin-top: 20px;'><div class='vip-inset-frame'>{final_render_html}</div></div>"
        else:
            content_body = final_render_html

        # 🆕 [안전장치] 맺음말이 누락된 경우, A4 규격 액자(report-page)로 감싸서 별도 페이지로 추가
        if closing_part and closing_part not in content_body:
            closing_page = html_views.get_final_report_box(closing_part) if hasattr(html_views, 'get_final_report_box') else f"<div class='report-page'><div class='vip-inset-frame'>{closing_part}</div></div>"
            content_body += closing_page

        # 전체 HTML 단순 결합
        combined_report_html = f"{safe_cover_str}\n{content_body}"

        # 1. 잔여 백틱 및 대제목 대괄호 제거
        clean_report_html = combined_report_html.replace('```html', '').replace('```markdown', '').replace('```', '')
        clean_report_html = re.sub(r'<h1([^>]*)>\s*\[\s*(.*?)\s*\]\s*</h1>', r'<h1\1>\2</h1>', clean_report_html)
        clean_report_html = re.sub(r'<h2([^>]*)>\s*\[\s*(.*?)\s*\]\s*</h2>', r'<h2\1>\2</h2>', clean_report_html)

        # 2. 🛡️ 마크다운 코드블록/문단 오인 방지용 정밀 트림
        #    (a) 각 줄 시작 부분의 4칸 이상 공백/탭 제거 (들여쓰기 → 코드블록 오인 차단)
        #    (b) 빈 줄(공백만 있는 줄 포함) 완전 제거
        #        -> HTML 블록 중간의 빈 줄이 있으면 CommonMark 파서가 그 지점에서
        #           HTML 블록을 종료시키고, 그 뒤에 오는 <div> 등을 다시 '일반 문단'으로
        #           재해석하면서 인라인 style(!important 포함)이 무시되는 문제가 있었음.
        #           (표지 하단 발행일자/연구소명이 16px 일반 문단체로 나오던 근본 원인)
        clean_lines = [re.sub(r'^[ \t]+(?=<)', '', line) for line in clean_report_html.split('\n') if line.strip() != '']
        final_clean_html = "\n".join(clean_lines)

        # ----------------------------------------------------------------------
        # 🤖 [스텔스 생산 파이프라인 연계 및 정식 렌더링]
        # ----------------------------------------------------------------------
        if is_admin_mode:
            gid = st.session_state.get('admin_proc_id', '')
            st.session_state[f'html_{gid}'] = final_clean_html
            if 'admin_orders' in st.session_state and gid in st.session_state['admin_orders']:
                st.session_state['admin_orders'][gid]['html'] = final_clean_html
                st.session_state['admin_orders'][gid]['is_generated'] = True
                st.session_state['admin_orders'][gid]['status'] = '제작완료'
            st.session_state['app_running'] = False
            st.session_state['admin_proc_id'] = None
            st.rerun()
        else:
            st.session_state['saved_report_html'] = final_clean_html
            st.markdown(final_clean_html, unsafe_allow_html=True)

# 🆕 인쇄 버튼 클릭 등으로 재실행됐을 때, 이미 만들어둔 감명서를 다시 화면에 보여줌
elif st.session_state.get('saved_report_html') and not is_admin_mode:
    st.markdown(st.session_state['saved_report_html'], unsafe_allow_html=True)
