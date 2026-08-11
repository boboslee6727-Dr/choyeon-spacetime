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
APP_VERSION = "ver 72.3 Master"
st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# 전역 CSS 적용
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

# ==============================================================================
# 2. 사이드바 통제 센터 (ver 72.3 원본 조건부 UI 100% 원상복구)
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
        value=st.session_state.get("main_target_calc_date", default_date_today),
        key="main_target_calc_date",
        help="기본값은 오늘 날짜이며, 원하는 특정 연/월/일을 선택하여 시뮬레이션할 수 있습니다.",
        on_change=stop_ai
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
                "2-5. 이사 및 방위 특화 분석"
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
    else:
        u_product = st.radio(
            "비교 분석 대상:", 
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

    def sync_user_gender():
        f_val = st.session_state.get("f_g", "여성")
        st.session_state["u_g"] = "여성" if f_val == "남성" else "남성"

    # 🔍 신청인 사주간지 역산 검색 모듈 (ver 72.1 원형 및 시간연동 완벽 보완)
    with st.expander("🔍 신청인 사주간지 역산", expanded=False):
        col_g1, col_g2 = st.columns(2)
        with col_g1: u_ry = st.text_input("년주", key="u_ry_rev")
        with col_g2: u_rm = st.text_input("월주", key="u_rm_rev")
        col_g3, col_g4 = st.columns(2)
        with col_g3: u_rd = st.text_input("일주", key="u_rd_rev")
        with col_g4: u_rt = st.text_input("시주", key="u_rt_rev")

        if st.button("🔍 신청인 생년월일 자동입력", use_container_width=True, key="btn_user_rev"):
            st.session_state['app_running'] = False
            
            _ry = re.sub(r'[^가-힣一-龥]', '', u_ry) if u_ry else ""
            _rm = re.sub(r'[^가-힣一-龥]', '', u_rm) if u_rm else ""
            _rd = re.sub(r'[^가-힣一-龥]', '', u_rd) if u_rd else ""
            
            if not _ry and not _rm and not _rd:
                if 'rev_success_msg' in st.session_state: del st.session_state['rev_success_msg']
                st.rerun()
            elif len(_ry) >= 2 and len(_rm) >= 2 and len(_rd) >= 2:
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
                                st.session_state['s_y'] = curr_dt.year
                                st.session_state['s_m'] = curr_dt.month
                                st.session_state['s_d'] = curr_dt.day
                                
                                if u_rt:
                                    ji_char_u = u_rt[-1]
                                    u_rt_h = engine.K2H_JI.get(ji_char_u, ji_char_u)
                                    target_time_str = time_map.get(u_rt_h, "시간 모름")
                                else:
                                    target_time_str = "시간 모름"
                                
                                # 🎯 [교정] 시간 세션 키값 일치화
                                st.session_state['s_t'] = target_time_str
                                st.session_state['s_t_select'] = target_time_str
                                
                                found = True
                                s_sol_fmt = f"{curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일"
                                s_lun_fmt = f"{klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일"
                                st.session_state['rev_success_msg'] = f"✅양력{s_sol_fmt}\n 음력{s_lun_fmt}"
                                st.rerun()
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                    if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

        if 'rev_success_msg' in st.session_state:
            st.success(st.session_state['rev_success_msg'])
            del st.session_state['rev_success_msg']

    # 👤 신청인 기본 정보 입력부
    u_box = st.container()
    with u_box:
        st.subheader("👤 신청인 기본 정보")
        name = st.text_input("이름", value=st.session_state.get("u_n", ""), placeholder="홍길동", key="u_n")
        gender = st.selectbox("성별", ["남성", "여성"], key="u_g", on_change=sync_partner_gender)
        u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
        u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")

        col_y, col_m, col_d = st.columns(3)
        with col_y: b_year = st.number_input("년도", 1900, 2050, value=st.session_state.get("s_y", 1980), key="s_y")
        with col_m: b_month = st.number_input("월", 1, 12, value=st.session_state.get("s_m", 1), key="s_m")
        with col_d: b_day = st.number_input("일", 1, 31, value=st.session_state.get("s_d", 1), key="s_d")
        
        curr_t_val = st.session_state.get("s_t", idx_list[0])
        t_idx = idx_list.index(curr_t_val) if curr_t_val in idx_list else 0
        
        # 🎯 [교정] index 연결을 바르게 정돈
        b_time = st.selectbox("태어난 시간", idx_list, index=t_idx, key="s_t_select")
        st.session_state["s_t"] = b_time

    # 선택 상품별 조건부 입력 옵션 모듈 (ver 72.1 원형)
    if u_product.startswith("1-") or u_product.startswith("2-"):
        if u_product.startswith("1-"):
            is_vip_package = st.checkbox(
                "👑 VIP 패키지 모드 (누적 출력)", 
                value=st.session_state.get("is_vip_package_val", False), 
                key="is_vip_package_val"
            )
            
            is_compare_traditional = st.checkbox(
                "⚖️ 전통 : 시공 명리 운세풀이 비교", 
                value=st.session_state.get("is_compare_trad_val", False), 
                key="is_compare_trad_val"
            )

        if "1-2." in u_product:
            curr_yr_val = dt_mod.datetime.now(pytz.timezone('Asia/Seoul')).year
            st.number_input("📅 분석할 특정 연도 (기본값: 올해)", min_value=1900, max_value=2050, value=curr_yr_val, key="target_year_input")
        elif "1-4." in u_product:
            daily_calc_date = st.date_input("일운 분석 기준일 선택", value=selected_target_date, key="daily_calc_date")
        elif "2-1." in u_product: 
            wealth_goal = st.text_input("고민되는 금전 문제는?", key="wealth_goal")
        elif "2-2." in u_product: 
            career_goal = st.text_input("고민되는 직업/진학 분야는?", key="career_goal")
        elif "2-3." in u_product:
            love_goal = st.text_input("고민되는 연애/이성 문제는?", key="love_goal")
        elif "2-4." in u_product: 
            health_goal = st.text_input("관리할 건강 부위는?", key="health_goal")
        elif "2-5." in u_product:
            moving_date = st.date_input("이사 희망일", key="moving_date")
            moving_dir = st.selectbox("이사 희망 방위", ["동쪽", "서쪽", "남쪽", "북쪽", "기타"], key="moving_dir")

    elif "4-1." in u_product:
        other_report = st.text_area("📄 타 감명서 원문 (사주) 붙여넣기", height=150, key=f"text_{u_product}")

    # 2인 전용 상품(궁합, 택일) 상대방 사주 역산 및 기본 정보 모듈
    is_2person = (main_category == "3. 커플 연애/결혼운 (궁합) 풀이") or ("4-2." in u_product)
    if is_2person:
        st.markdown("<hr style='border:1px dashed #C62828; margin:15px 0;'>", unsafe_allow_html=True)
        
        # 🎯 [교정] 상대방 초기 세션값 안전 선언
        if 'p_t_key' not in st.session_state: st.session_state['p_t_key'] = idx_list[0]
        
        with st.expander("🔍 상대방 사주간지 역산", expanded=False):
            p_col_g1, p_col_g2 = st.columns(2)
            with p_col_g1: p_ry = st.text_input("상대방 년주", key="p_ry")
            with p_col_g2: p_rm = st.text_input("상대방 월주", key="p_rm")
            p_col_g3, p_col_g4 = st.columns(2)
            with p_col_g3: p_rd = st.text_input("상대방 일주", key="p_rd")
            with p_col_g4: p_rt = st.text_input("상대방 시주", key="p_rt")
            
            if st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="btn_partner_rev"):
                st.session_state['app_running'] = False
                
                _p_ry = re.sub(r'[^가-힣一-龥]', '', p_ry) if p_ry else ""
                _p_rm = re.sub(r'[^가-힣一-龥]', '', p_rm) if p_rm else ""
                _p_rd = re.sub(r'[^가-힣一-龥]', '', p_rd) if p_rd else ""
                
                if not _p_ry and not _p_rm and not _p_rd:
                    if 'rev_p_success_msg' in st.session_state: del st.session_state['rev_p_success_msg']
                    st.rerun()
                elif len(_p_ry) >= 2 and len(_p_rm) >= 2 and len(_p_rd) >= 2:
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
                    for y in range(2026, 1899, -1):
                        klc_find.setSolarDate(y, 7, 1)
                        gj_y = klc_find.getChineseGapJaString().split()
                        if gj_y and gj_y[0][:2] == p_ry_h:
                            curr_dt = dt_mod.date(y+1, 2, 28)
                            while curr_dt >= dt_mod.date(y, 1, 1):
                                klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                                gj = klc_find.getChineseGapJaString().split()
                                if len(gj) >= 3 and gj[0][:2] == p_ry_h and gj[1][:2] == p_rm_h and gj[2][:2] == p_rd_h:
                                    st.session_state['p_y_in'] = curr_dt.year
                                    st.session_state['p_m_in'] = curr_dt.month
                                    st.session_state['p_d_in'] = curr_dt.day
                                    
                                    if p_rt:
                                        ji_char_p = p_rt[-1]
                                        p_rt_h = engine.K2H_JI.get(ji_char_p, ji_char_p)
                                        target_time_str = time_map.get(p_rt_h, "시간 모름")
                                    else:
                                        target_time_str = "시간 모름"
                                    
                                    # 🎯 [교정] 상대방 시간 키값 바인딩 완벽 수정
                                    st.session_state['p_t_key'] = target_time_str
                                    
                                    found = True
                                    s_sol_fmt = f"{curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일"
                                    s_lun_fmt = f"{klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일"
                                    st.session_state['rev_p_success_msg'] = f"✅양력{s_sol_fmt}\n 음력{s_lun_fmt}"
                                    st.rerun()
                                    break
                                curr_dt -= dt_mod.timedelta(days=1)
                        if found: break
                    if not found: st.error("일치하는 날짜가 없습니다.")
                else: st.warning("간지를 2글자씩 정확히 입력하세요.")

            if 'rev_p_success_msg' in st.session_state:
                st.success(st.session_state['rev_p_success_msg'])
                del st.session_state['rev_p_success_msg']

        if 'f_n' not in st.session_state: st.session_state['f_n'] = ""
        if 'p_y_in' not in st.session_state: st.session_state['p_y_in'] = 1980
        if 'p_m_in' not in st.session_state: st.session_state['p_m_in'] = 1
        if 'p_d_in' not in st.session_state: st.session_state['p_d_in'] = 1

        p_box = st.container()
        with p_box:
            st.subheader("💕 상대방 기본 정보")
            f_name = st.text_input("상대방 이름", key="f_n")
            f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_g", on_change=sync_user_gender)
            f_marital = st.selectbox("상대방 혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="f_m_stat")
            f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c")
            
            p_col1, p_col2, p_col3 = st.columns(3)
            f_y = p_col1.number_input("년도(상대)", 1900, 2050, key="p_y_in")
            f_m = p_col2.number_input("월(상대)", 1, 12, key="p_m_in")
            f_d = p_col3.number_input("일(상대)", 1, 31, key="p_d_in")
            
            # 🎯 [교정] 상대방 시간 선택 인덱스 연동 교정
            p_t_idx = idx_list.index(st.session_state["p_t_key"]) if st.session_state["p_t_key"] in idx_list else 0
            f_t = st.selectbox("태어난 시간(상대)", idx_list, index=p_t_idx, key="p_t_select")
            st.session_state["p_t_key"] = f_t

    # 택일 및 타 궁합 감명서 입력 옵션 모듈
    if "3-2." in u_product:
        date_mode = st.radio("결혼 택일 방식", ["기간 선택", "특정일 지정"], key="radio_marriage_mode")
        if date_mode == "기간 선택":
            col_start, col_end = st.columns(2)
            start_date = col_start.date_input("시작일", key="start_date_m")
            end_date = col_end.date_input("종료일", key="end_date_m")
        else:
            target_date = st.date_input("결혼 예정일 선택", key="target_date_m")
            
    elif "3-3." in u_product:
        run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석 가동", value=True, key="run_delivery_calc")
        
        if run_delivery_calc:
            st.subheader("🩺 산모 생리 주기 및 기준 정보")
            today_dt = dt_mod.date.today()
            default_last_period = today_dt - dt_mod.timedelta(days=30)
            
            last_period_date = st.date_input("마지막 생리 시작일", value=default_last_period, key="last_period_date")
            period_cycle = st.number_input("평균 생리 주기 (일)", min_value=20, max_value=45, value=30, key="period_cycle")
            
            st.markdown("---")
            st.subheader("📅 출산 길일 탐색 기간 설정")
            
            default_start = today_dt
            default_end = today_dt + dt_mod.timedelta(days=365)
            
            col_d1, col_d2 = st.columns(2)
            delivery_start_date = col_d1.date_input("탐색 시작일", value=default_start, key="delivery_start_date")
            delivery_end_date = col_d2.date_input("탐색 종료일", value=default_end, key="delivery_end_date")

    elif "4-2." in u_product:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        other_report = st.text_area("📄 타 감명서 원문 (궁합) 붙여넣기", height=150, key=f"text_{u_product}")

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

    if st.button("✨ [초연 시공명리 풀이 가동]", key="btn_run", use_container_width=True, type="primary"):
        st.session_state['app_running'] = True

    if st.button("🖨️ 풀이 결과 인쇄 / PDF 저장", key="btn_print", use_container_width=True, type="secondary"):
        components.html("<script>window.parent.print();</script>", height=0)

# ==============================================================================
# 3. 메인 화면 범용 연산 및 AI 통변 모듈 연동부 (612행 예외 방어 완전 적용)
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
         
        # 안전한 한자 변환 리스트 구성 (None 및 빈 문자열 방어)
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
        
        guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 해','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
        guiin_str = guiin_map.get(ds_hanja, '없음')
        curr_y_ji = engine.JI[(curr_year - 1984) % 60 % 12]
        
        n_gong = engine.calculate_gongmang(ys, yb) or "-"
        i_gong = engine.calculate_gongmang(ds, db) or "-"
        cur_samjae = engine.get_samjae(yb, curr_y_ji)
        samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"
        
        sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
        lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
        time_str_fmt = f"{b_time.split('(')[0].strip()}" if b_time != "시간 모름" else "시간 미상"
        
        # ==============================================================================
        # 🎯 [추가] 상품별 리포트 메인 타이틀 분기 및 표지(Cover) 생성 로직
        # ==============================================================================
        if u_product == "1-1. 사주팔자와 운세풀이 (기본)":
            report_title = "🏮 사주팔자와 운세풀이 (기본)"
        elif u_product == "1-2. 올해 및 특정연도 운세 상세분석":
            report_title = "🏮 올해 및 특정연도 운세 상세분석"
        elif u_product == "1-3. 이번달 및 특정월 운세 상세분석":
            report_title = "🏮 이번달 및 특정월 운세 상세분석"
        elif u_product == "1-4. 특정 주간 및 특정일운 상세분석":
            report_title = "🏮 특정 주간 및 특정일운 상세분석"
        elif u_product == "2-1. 재물운 특화 분석":
            report_title = "🏮 재물운 특화 정밀 분석"
        elif u_product == "2-2. 직업/진학운 특화 분석":
            report_title = "🏮 직업/진학운 특화 정밀 분석"
        elif u_product == "2-3. 연애/결혼운 특화 분석":
            report_title = "🏮 연애/결혼운 특화 정밀 분석"
        elif u_product == "2-4. 건강운 특화 분석":
            report_title = "🏮 건강운 특화 정밀 분석"
        elif u_product == "2-5. 이사 및 방위 특화 분석":
            report_title = "🏮 이사 및 방위 특화 정밀 분석"
        elif u_product == "3-1. 연애/결혼운 (궁합) 풀이":
            report_title = "🏮 커플 연애/결혼운 정밀 궁합 분석"
        elif u_product == "3-2. 결혼 택일":
            report_title = "🏮 최고의 결혼 길일 추천 리포트"
        elif u_product == "3-3. 출산 택일":
            report_title = "🏮 새 생명 마중 출산 길일 추천 리포트"
        elif u_product == "4-1. 타 감명서 비교 (사주)":
            report_title = "🏮 사주 감명서 학술 검증 및 1:1 대조 리포트"
        elif u_product == "4-2. 타 감명서 비교 (궁합)":
            report_title = "🏮 궁합 감명서 학술 검증 및 1:1 대조 리포트"
        else:
            report_title = "🏮 사주팔자 정밀 분석"

        # 🌟 궁합 점수 및 등급 변수 초기화
        gh_score = 0
        gh_grade = ""
        partner_bazi = ["?", "?", "?", "?"]

        # 🏮 표지 생성 분기 (1인용 vs 2인용 궁합)
        if is_2person:
            # --- 상대방 사주 원국 계산 ---
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

            # --- 상대방 나이 계산 ---
            curr_yr_for_age = dt_mod.datetime.now(pytz.timezone('Asia/Seoul')).year
            p_age_val = curr_yr_for_age - p_y + 1
            
            # 성별에 따른 명칭(남명/여명) 세팅
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
            
            # 🌟 [추가] 2인 사주 명조 데이터 정리 및 궁합 엔진 가동
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
            except Exception as e:
                gh_score = 0
                gh_grade = "점수 산출 불가"
                
        else:
            # 1인용 표지용 아이콘 명칭 간소화
            u_icon_str = f"{p_icon}" 
            cover_html = html_views.get_personal_cover(
                APP_VERSION, report_title, u_icon_str, name, sol_str_fmt, lun_str_fmt, time_str_fmt, today_str
            )
        
        info_h = html_views.get_info_header(p_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, b_time)
        
        table_html = html_views.generate_saju_table_data(gans, jjis, ds, gender, engine)
        master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, samjae_color, cur_samjae)
        intro_html = html_views.get_intro_html()
        
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
            j_hanja = engine.K2H_JI.get(j_hangul, j_hanja)
            is_active = (val <= age < val + 10)
            
            u_sung_val = engine.get_unsung(ds_hanja, j_hanja) if j_hanja != "-" else "-"
            y_shin_val = engine.get_12_shinsal(yb, j_hangul) if j_hangul != "-" else "-"
            d_shin_val = engine.get_12_shinsal(db, j_hangul) if j_hangul != "-" else "-"
            
            daewun_data_list.append({
                "age_range": f"{val}~{val+9}세",
                "ss_gan": engine.get_ss(ds_hanja, c_hangul),
                "c_hanja": c_hanja,
                "c_hangul": c_hangul,
                "j_hanja": j_hanja,
                "j_hangul": j_hangul,
                "ss_ji": engine.get_ss(ds_hanja, j_hangul),
                "un_sung": u_sung_val,
                "y_shinsal": y_shin_val, 
                "d_shinsal": d_shin_val, 
                "is_current": is_active,
                "is_first": (i == 0)
            })

        un_html = html_views.generate_daewun_layout(daewun_data_list, direction_str, calc_d, get_oh_class)

        current_daewun_age = max(0, int(cur_dw_idx) * 10 + int(calc_d))
        start_year = int(sol_y) + current_daewun_age - 1

        se_content = ""
        for i in range(10):
            ty = start_year + i
            tage = current_daewun_age + i
            base = (ty - 1984) % 60
            tc_hangul, tj_hangul = engine.GAN[base % 10], engine.JI[base % 12]
            tc = engine.K2H_GAN.get(tc_hangul, tc_hangul)
            tj = engine.K2H_JI.get(tj_hangul, tj_hangul)
            
            is_cur_yr = (ty == curr_year)
            bg_col = "#E1F5FE" if is_cur_yr else "transparent"
            b_left = "1px solid #ccc"
            
            se_content += html_views.get_sewun_cell(
                f"{ty}년", tage, 
                engine.get_ss(ds_hanja, tc), tc, get_oh_class(tc), 
                tj, get_oh_class(tj), engine.get_ss(ds_hanja, tj), 
                engine.get_unsung(ds_hanja, tj), 
                engine.get_12_shinsal(yb, tj), 
                engine.get_12_shinsal(db, tj),
                bg_col, b_left, is_cur_yr
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
                tm, 
                engine.get_ss(ds_hanja, wc_hanja), wc_hanja, get_oh_class(wc_hanja), 
                wj_hanja, get_oh_class(wj_hanja), engine.get_ss(ds_hanja, wj_hanja), 
                engine.get_unsung(ds_hanja, wj_hanja), 
                engine.get_12_shinsal(yb, wj_hanja), 
                engine.get_12_shinsal(db, wj_hanja),
                bg_col, b_left, is_cur_m
            )

        wolun_html = html_views.get_wolun_layout(f"[ 월운의 흐름 ({curr_year}년도 양력기준) ]", wol_content)

        choyeon_db = load_choyeon_db()
        w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{db}".strip()
        w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
        i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
        struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
        golden_text_html = html_views.get_golden_text(name, w_val, i_val, struct_data[0], struct_data[1], struct_data[2])

        closing_html = html_views.get_closing_html(name)            
        closing_part = str(closing_html or "").strip()

        part_1_fact = str(info_h or "") + str(table_html or "") + str(master_bar_html or "")
        part_2_intro = str(intro_html or "")
        part_3_golden = str(golden_text_html or "")
        part_5_closing = str(closing_part or "")

        gyukgook, gyukgook_detail = engine.get_gyukgook_detailed(ds, ys, ms, hs, mb)
        
        ss_unsung_str = (
            f"년주:{engine.get_ss(ds, ys)}{engine.get_ss(ds, yb)}({engine.get_unsung(ds, yb)}) / "
            f"월주:{engine.get_ss(ds, ms)}{engine.get_ss(ds, mb)}({engine.get_unsung(ds, mb)}) / "
            f"일주:{ds}(본인){engine.get_ss(ds, db)}({engine.get_unsung(ds, db)}) / "
            f"시주:{engine.get_ss(ds, hs)}{engine.get_ss(ds, hb)}({engine.get_unsung(ds, hb)})"
        )
        
        won_guk_vaults_list = engine.check_vault_status([ys, ms, ds, hs], [yb, mb, db, hb], mb)
        won_guk_vaults_str = " ".join([re.sub(r'<[^>]+>', '', v) for v in won_guk_vaults_list])
        if not won_guk_vaults_str:
            won_guk_vaults_str = engine.get_won_guk_vaults_str([hb, db, mb, yb])
            
        hap_chung_hyoung_pa_hae = (
            f"일-월지:{engine.get_ji_rel_set(db, mb)}, 일-년지:{engine.get_ji_rel_set(db, yb)}, "
            f"일-시지:{engine.get_ji_rel_set(db, hb)}, 월-년지:{engine.get_ji_rel_set(mb, yb)}"
        )
        
        s12_str = engine.get_all_12_shinsal(yb, mb, db, hb)

        # 🛡️ [수정 완료 및 방어 적용] 612행 신살 연산 시 인자 누락 및 타입 에러 원천 차단
        try:
            if hasattr(engine, 'get_general_shinsal_filtered'):
                shinsal_raw = engine.get_general_shinsal_filtered(1, gans, jjis, gender)
            else:
                shinsal_raw = []
        except Exception:
            shinsal_raw = []

        shinsal_str = ", ".join([re.sub(r'<[^>]+>', '', str(s)) for s in shinsal_raw]) if shinsal_raw else "특이 신살 없음"

        saju_fact_summary = f"""
- 내담자 명조: 년주({ys}{yb}), 월주({ms}{mb}), 일주({ds}{db}), 시주({hs}{hb})
- 격국 및 용신 팩트: {gyukgook_detail}
- 원국 오행 분포: 목:{counts['목']}, 화:{counts['화']}, 토:{counts['토']}, 금:{counts['금']}, 수:{counts['수']}
- 공망 궁위 팩트: [년지공망] {n_gong} / [일지공망] {i_gong}
- 삼재 여부: {cur_samjae}
"""

        # 대운 및 운세 팩트 데이터 추출 (w_facts 선언)
        w_facts = engine.get_woonse_analysis_facts(
            ds, db, dw_g_cur, dw_j_cur, 
            engine.GAN[(curr_year-1984)%60%10], engine.JI[(curr_year-1984)%60%12], 
            "丙", "午", "甲", "子"
        )

        saju_fact_summary = f"""
- 내담자 명조: 년주({ys}{yb}), 월주({ms}{mb}), 일주({ds}{db}), 시주({hs}{hb})
- 격국 및 용신 팩트: {gyukgook_detail}
- 원국 오행 분포: 목:{counts['목']}, 화:{counts['화']}, 토:{counts['토']}, 금:{counts['금']}, 수:{counts['수']}
- 공망 궁위 팩트: [년지공망] {n_gong} / [일지공망] {i_gong}
- 삼재 여부: {cur_samjae}
"""

        # 내담자의 지정 연도 세운 간지 동적 연산
        target_year_val = st.session_state.get('target_year_input', curr_year)
        cur_sewun_base = (target_year_val - 1984) % 60
        cur_sewun_gan_val = engine.GAN[cur_sewun_base % 10]
        cur_sewun_ji_val = engine.JI[cur_sewun_base % 12]

        prompt_data = {
            "name": name, "age": age, "gender": gender, "marital": u_marital,
            "age_prompt": engine.get_age_prompt(age), 
            "gender_prompt": engine.get_gender_prompt(gender), 
            "marital_prompt": engine.get_marital_prompt(gender, u_marital), 
            "yukchin_rule": engine.get_yukchin_rule(gender, u_marital),
            "saju_fact_summary": saju_fact_summary,
            
            # 동적 대운 간지 바인딩
            "dw_g_cur": dw_g_cur, 
            "dw_j_cur": dw_j_cur, 
            "dw_fact_str": f"현재 {dw_g_cur}{dw_j_cur}대운 가동 중",
            
            "samhyung_fact_str": engine.check_samhyung_facts([yb, mb, db, hb], dw_j_cur),
            "hang_un_vaults_str": engine.get_hang_un_vaults_str(dw_j_cur, [ys, ms, ds, hs], [yb, mb, db, hb]),
            "dw_che": w_facts.get("dw_che", "대운 시공간 무대"),
            "ds": ds, "db": db, "gyukgook_detail": gyukgook_detail,
            "year_gongmang": n_gong, "day_gongmang": i_gong,
            "oheng_counts_str": f"목:{counts['목']} 화:{counts['화']} 토:{counts['토']} 금:{counts['금']} 수:{counts['수']}",
            "hap_chung_hyoung_pa_hae": hap_chung_hyoung_pa_hae,
            "won_guk_vaults_str": won_guk_vaults_str,
            "shinsal_str": shinsal_str,
            "cheon_eul": guiin_str,
            "samjae_str": cur_samjae,
            "curr_year": target_year_val,
            "cur_sewun_gan": cur_sewun_gan_val,
            "cur_sewun_ji": cur_sewun_ji_val,
            "target_year": target_year_val,
            "curr_m": curr_m, 
            "target_date_str": selected_target_date.strftime("%Y년 %m월 %d일"),
            "gh_score": gh_score,
            "gh_grade": gh_grade
        }

        class SafeDict(dict):
            def __missing__(self, key): return '{' + key + '}'
        
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
            "4-1. 타 감명서 비교 (사주)": "프롬프트_4_1_사주대조",
            "4-2. 타 감명서 비교 (궁합)": "프롬프트_4_2_궁합대조"
        }

        # AI 프롬프트 바인딩 및 Gemini API 호출
        prompt_var_name = target_prompt_map.get(u_product, "프롬프트_1_1_기본")
        target_prompt = getattr(prompts, prompt_var_name, getattr(prompts, "프롬프트_1_1_기본", ""))
        
        formatted_prompt = target_prompt.format_map(SafeDict(prompt_data))
        raw_response = call_gemini_api(formatted_prompt)
        
        if raw_response and isinstance(raw_response, str):
            clean_raw = raw_response.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
            ai_output_html = html_views.format_ai_text_to_html(clean_raw)
        else:
            ai_output_html = "<p style='padding:20px;'>분석 결과를 불러오지 못했습니다.</p>"

        # ==============================================================================
        # 🏮 [ver 72.3 파이프라인] 표지 및 본문 보고서 완벽 출력부
        # ==============================================================================
        
        # 1. 표지(cover_html) 단독 출력 (A4 1페이지)
        if 'cover_html' in locals() and cover_html:
            safe_cover = re.sub(r'\n\s+', '\n', cover_html)
            st.markdown(safe_cover, unsafe_allow_html=True)

        # 2. 택일 특화 엔진 가동 (결과 HTML 생성)
        delivery_html = ""
        if u_product in ["3-2. 결혼 택일", "3-3. 출산 택일"]:
            try:
                s_d_val = st.session_state.get('delivery_start_date', dt_mod.date.today())
                e_d_val = st.session_state.get('delivery_end_date', dt_mod.date.today() + dt_mod.timedelta(days=30))
                m_jjis_val = jjis if gender == "남성" else [b[1] if len(b)>1 else "?" for b in partner_bazi]
                f_jjis_val = [b[1] if len(b)>1 else "?" for b in partner_bazi] if gender == "남성" else jjis
                forbidden_list = ['병오', '임자', '계해', '신유', '경신']
                
                if hasattr(engine, 'get_optimized_delivery_days'):
                    delivery_days = engine.get_optimized_delivery_days(s_d_val, e_d_val, m_jjis_val, f_jjis_val, forbidden_list)
                    del_list_str = "".join([f"<div style='margin-bottom:8px; padding:10px; background:#F8F9FA; border:1px solid #E8EAF6; border-radius:6px; color:#1A237E;'>✅ 추천 길일: <b>{d['date']}</b> (조화 점수: {d['score']}점)</div>" for d in delivery_days])
                    delivery_html = f"<div style='margin-top:20px; padding:20px; border:2px dashed #C62828; border-radius:10px;'><h3 style='color:#C62828; margin-top:0;'>📅 시공명리 최적 택일 추천</h3>{del_list_str}</div>"
            except Exception as e:
                pass

        # 3. 파이프라인 분기 (1인용 vs 3분할 2인용 vs 택일)
        final_render_html = ""
        if u_product in ["3-2. 결혼 택일", "3-3. 출산 택일"]:
            # 택일 파이프라인
            master_comp = delivery_html + f"<div style='margin-top:20px;'>{ai_output_html}</div>" + part_5_closing
            final_render_html = html_views.get_final_report_box(master_comp)
            
        elif u_product == "3-1. 연애/결혼운 (궁합) 풀이":
            # 🌟 궁합 3분할 파이프라인 가동 🌟
            m_ess, f_ess, g_ess = "", "", clean_raw
            
            # AI 텍스트 마커 정규식 분해
            m_match = re.search(r'\[MALE_START\](.*?)\[MALE_END\]', clean_raw, re.DOTALL)
            if m_match: m_ess = html_views.format_ai_text_to_html(m_match.group(1).strip())
            
            f_match = re.search(r'\[FEMALE_START\](.*?)\[FEMALE_END\]', clean_raw, re.DOTALL)
            if f_match: f_ess = html_views.format_ai_text_to_html(f_match.group(1).strip())
            
            g_match = re.search(r'\[GUNGHAP_START\](.*?)\[GUNGHAP_END\]', clean_raw, re.DOTALL)
            if g_match: g_ess = html_views.format_ai_text_to_html(g_match.group(1).strip())
            
            # 🌈 박사님의 기존 UI 함수 호출 (대운 대조표 결합)
            # (현재는 UI 테스트를 위해 신청인 un_html을 양쪽에 매핑해두었습니다. 추후 상대방 대운 연산 로직만 추가하시면 완벽해집니다.)
            c_daewun_html = html_views.get_daewun_compare_box(m_name_val, un_html, f_name_val, un_html)
            g_ess = g_ess.replace("[COUPLE_DAEWUN_TABLES_HERE]", c_daewun_html)
            
            # 📊 박사님의 기존 UI 함수 호출 (점수판 및 맺음말 결합)
            score_ui = ""
            closing_ui = ""
            if 'gh_engine' in locals():
                score_ui = html_views.get_gunghap_score_visual_html(gh_engine)
                closing_ui = html_views.get_gunghap_closing(m_name_val, f_name_val)
            g_ess += score_ui + closing_ui
            
            # 📄 3장 분할 래핑 (페이지 나누기 적용)
            m_page = f"""
            <div class='report-page' style='margin-top:20px;'>
                <div class='vip-inset-frame' style='border-color:#1A237E; padding:20px;'>
                    <h1 style='text-align:center; color:#1A237E; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; border-bottom:2px solid #1A237E; padding-bottom:15px; margin-bottom:20px;'>[ ♂️ 남명 사주 요약 ]</h1>
                    {part_1_fact}
                    <div style='margin-top:20px;'>{m_ess}</div>
                </div>
            </div>
            <div class='page-break-before' style='page-break-before: always; height: 1px;'></div>
            """
            
            f_page = f"""
            <div class='report-page' style='margin-top:20px;'>
                <div class='vip-inset-frame' style='border-color:#D50000; padding:20px;'>
                    <h1 style='text-align:center; color:#D50000; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; border-bottom:2px solid #D50000; padding-bottom:15px; margin-bottom:20px;'>[ ♀️ 여명 사주 요약 ]</h1>
                    <div style='margin-top:20px;'>{f_ess}</div>
                </div>
            </div>
            <div class='page-break-before' style='page-break-before: always; height: 1px;'></div>
            """
            
            g_page = f"""
            <div class='report-page' style='margin-top:20px;'>
                <div class='vip-inset-frame' style='border-color:#1B5E20; padding:20px;'>
                    <h1 style='text-align:center; color:#1B5E20; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; border-bottom:2px solid #1B5E20; padding-bottom:15px; margin-bottom:20px;'>[ 🍀 초연 시공명리 궁합 풀이 ]</h1>
                    <div style='margin-top:20px;'>{g_ess}</div>
                </div>
            </div>
            """
            
            final_render_html = m_page + f_page + g_page

        else:
            # 1인용 파이프라인 (기본) 및 타 감명서 대조용
            master_comp = part_1_fact + part_2_intro + part_3_golden + f"<div style='margin-top:20px;'>{ai_output_html}</div>" + part_5_closing
            if master_comp.startswith("</div>"):
                master_comp = master_comp[6:].strip()
            final_render_html = html_views.get_final_report_box(master_comp)

        # 4. 🚨 화면 최상단에 나타나는 </div> 찌꺼기 도려냄
        master_composite_report = master_composite_report.strip()
        if master_composite_report.startswith("</div>"):
            master_composite_report = master_composite_report[6:].strip()

        # 5. 박스 디자인 적용 및 들여쓰기 공백 제거
        final_html = html_views.get_final_report_box(master_composite_report)
        final_html = re.sub(r'\n\s+', '\n', final_html)

        # 6. 본문 종합 보고서 단독 최종 출력
        st.markdown(final_html, unsafe_allow_html=True)
