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
importlib.reload(html_views)

# ==============================================================================
# 1. 초기 설정 및 공통 함수
# ==============================================================================
APP_VERSION = "ver 72.0 Master"
st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# 전역 CSS 적용 (html_views 모듈 호출)
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
    sys_role = getattr(prompts, 'SYSTEM_ROLE', None)
    if sys_role is None:
        sys_role = getattr(prompts, 'SYSTEM_PROMPT', "당신은 초연 시공명리 전문가입니다. 팩트 데이터를 바탕으로 정확하게 분석하세요.")
    return get_ai_response(sys_role, prompt_text, model_name='gemini-2.5-flash')

def extract_ganji(text):
    if not text: return ""
    return re.sub(r'[^가-힣一-龥]', '', text)

def get_oh_class(ganji):
    oh = engine.get_color(ganji)
    return f"color-{oh}" if oh != '무' else ""

def td_bg(ganji):
    cls = get_oh_class(ganji)
    return f"<td class='{cls}' style='border:1px solid #444 !important; width:21%; font-size:20px; font-weight:900;'>"

# ==============================================================================
# 2. 사이드바 통제 센터 (방탄(Bulletproof) 범용 구조)
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

    main_category = st.selectbox("어떤 상담을 원하십니까?", ["1. 개인 사주팔자 풀이", "2. 커플 연애/결혼운 (궁합) 풀이", "3. 타 감명서 비교"], key="main_category", on_change=stop_ai)

    u_product = "1-1. 사주팔자 및 대운 분석"

    if main_category == "1. 개인 사주팔자 풀이":
        u_product = st.radio(
            "상세 분석 항목:", 
            [
                "1-1. 사주팔자 및 대운 분석", 
                "1-2. 올해 및 특정연도 운세 상세분석", 
                "1-3. 이번달 및 특정월 운세 상세분석", 
                "1-4. 특정 주간 및 특정일운 상세분석", 
                "1-5. 재물운 특화 분석", 
                "1-6. 직업/진학운 특화 분석", 
                "1-7. 연애운 특화 분석",
                "1-8. 건강운 특화 분석", 
                "1-9. 이사 및 방위 특화 분석"
            ], 
            key="sub_category_1", 
            on_change=stop_ai
        )
    elif main_category == "2. 커플 연애/결혼운 (궁합) 풀이":
        u_product = st.radio("상세 분석 항목:", ["2-1. 연애/결혼운 (궁합) 풀이", "2-2. 결혼 택일", "2-3. 출산 택일"], key="sub_category_2", on_change=stop_ai)
    else:
        u_product = st.radio("비교 분석 대상:", ["3-1. 타 감명서 비교 (사주)", "3-2. 타 감명서 비교 (궁합)"], key="sub_category_3", on_change=stop_ai)
    st.markdown("---")

    if "u_g" not in st.session_state: st.session_state["u_g"] = "남성"
    if "f_g" not in st.session_state: st.session_state["f_g"] = "여성"

    def sync_partner_gender():
        u_val = st.session_state.get("u_g", "남성")
        st.session_state["f_g"] = "남성" if u_val == "여성" else "여성"

    def sync_user_gender():
        f_val = st.session_state.get("f_g", "여성")
        st.session_state["u_g"] = "여성" if f_val == "남성" else "남성"

    # ==============================================================================
    # 🔍 신청인 사주간지 역산 입력부
    # ==============================================================================
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
                # 🛡️ 외부 모듈 의존성 제거 및 자체 안전 한글->한자 변환 맵 적용
                _k2h_g = {'갑':'甲', '을':'乙', '병':'丙', '정':'丁', '무':'戊', '기':'己', '경':'庚', '신':'辛', '임':'壬', '계':'癸', '甲':'甲', '乙':'乙', '丙':'丙', '丁':'丁', '戊':'戊', '己':'己', '庚':'庚', '辛':'辛', '壬':'壬', '癸':'癸'}
                _k2h_j = {'자':'子', '축':'丑', '인':'寅', '묘':'卯', '진':'辰', '사':'巳', '오':'午', '미':'未', '신':'申', '유':'酉', '술':'戌', '해':'亥', '子':'子', '丑':'丑', '寅':'寅', '卯':'卯', '辰':'辰', '巳':'巳', '午':'午', '未':'未', '申':'申', '酉':'酉', '戌':'戌', '亥':'亥'}
                
                ry_h = _k2h_g.get(_ry[0], _ry[0]) + _k2h_j.get(_ry[1], _ry[1])
                rm_h = _k2h_g.get(_rm[0], _rm[0]) + _k2h_j.get(_rm[1], _rm[1])
                rd_h = _k2h_g.get(_rd[0], _rd[0]) + _k2h_j.get(_rd[1], _rd[1])
                
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
                                    u_rt_h = _k2h_j.get(ji_char_u, ji_char_u)
                                    target_time_str = time_map.get(u_rt_h, "시간 모름")
                                else:
                                    target_time_str = "시간 모름"
                                
                                st.session_state['s_t'] = target_time_str
                                st.session_state['s_t_select'] = target_time_str
                                
                                found = True
                                s_sol_fmt = f"{curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일"
                                s_lun_fmt = f"{klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일"
                                st.session_state['rev_success_msg'] = f"✅ 양력 {s_sol_fmt}\n 음력 {s_lun_fmt}"
                                st.rerun()
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                    if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

        if 'rev_success_msg' in st.session_state:
            st.success(st.session_state['rev_success_msg'])
            del st.session_state['rev_success_msg']

    # ==============================================================================
    # 👤 신청인 기본 정보
    # ==============================================================================
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
        
        b_time = st.selectbox("태어난 시간", idx_list, index=t_idx, key="s_t_select")
        st.session_state["s_t"] = b_time

    # ==============================================================================
    # 📌 특화 상품별 옵션
    # ==============================================================================
    if u_product.startswith("1-"):
        is_vip_package = st.checkbox(
            "👑 VIP 패키지 모드 (누적 출력)", 
            value=st.session_state.get("is_vip_package_val", False), 
            key="is_vip_package_val",
            help="체크 시 풀이를 가동한 상품들이 삭제되지 않고 아래로 차곡차곡 쌓여 한 권의 종합 보고서로 인쇄됩니다."
        )
        
        if "1-4." in u_product:
            daily_calc_date = st.date_input(
                "일운 분석 기준일 선택", 
                value=selected_target_date, 
                key="daily_calc_date"
            )
        elif "1-5." in u_product: 
            wealth_goal = st.text_input("고민되는 금전 문제는?", key="wealth_goal")
        elif "1-6." in u_product: 
            career_goal = st.text_input("고민되는 직업/진학 분야는?", key="career_goal")
        elif "1-7." in u_product:
            love_goal = st.text_input("고민되는 연애/이성 문제는?", key="love_goal")
        elif "1-8." in u_product: 
            health_goal = st.text_input("관리할 건강 부위는?", key="health_goal")
        elif "1-9." in u_product:
            moving_date = st.date_input("이사 희망일", key="moving_date")
            moving_dir = st.selectbox("이사 희망 방위", ["동쪽", "서쪽", "남쪽", "북쪽", "기타"], key="moving_dir")

    elif "3-1." in u_product:
        other_report = st.text_area("📄 타 감명서 원문 (사주) 붙여넣기", height=150, key=f"text_{u_product}")

    # ==============================================================================
    # 👥 상대방 정보 입력부 (궁합)
    # ==============================================================================
    if any(x in u_product for x in ["2-1.", "2-2.", "2-3.", "3-2."]):
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
                    _k2h_g = {'갑':'甲', '을':'乙', '병':'丙', '정':'丁', '무':'戊', '기':'己', '경':'庚', '신':'辛', '임':'壬', '계':'癸', '甲':'甲', '乙':'乙', '丙':'丙', '丁':'丁', '戊':'戊', '己':'己', '庚':'庚', '辛':'辛', '壬':'壬', '癸':'癸'}
                    _k2h_j = {'자':'子', '축':'丑', '인':'寅', '묘':'卯', '진':'辰', '사':'巳', '오':'午', '미':'未', '신':'申', '유':'酉', '술':'戌', '해':'亥', '子':'子', '丑':'丑', '寅':'寅', '卯':'卯', '辰':'辰', '巳':'巳', '午':'午', '未':'未', '申':'申', '酉':'酉', '戌':'戌', '亥':'亥'}
                    
                    p_ry_h = _k2h_g.get(_p_ry[0], _p_ry[0]) + _k2h_j.get(_p_ry[1], _p_ry[1])
                    p_rm_h = _k2h_g.get(_p_rm[0], _p_rm[0]) + _k2h_j.get(_p_rm[1], _p_rm[1])
                    p_rd_h = _k2h_g.get(_p_rd[0], _p_rd[0]) + _k2h_j.get(_p_rd[1], _p_rd[1])
                    
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
                                        p_rt_h = _k2h_j.get(ji_char_p, ji_char_p)
                                        target_time_str = time_map.get(p_rt_h, "시간 모름")
                                    else:
                                        target_time_str = "시간 모름"
                                    
                                    st.session_state['p_t_key'] = target_time_str
                                    st.session_state['p_t_select'] = target_time_str
                                    
                                    found = True
                                    s_sol_fmt = f"{curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일"
                                    s_lun_fmt = f"{klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일"
                                    st.session_state['rev_p_success_msg'] = f"✅ 양력 {s_sol_fmt}\n 음력 {s_lun_fmt}"
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
        if 'p_t_key' not in st.session_state: st.session_state['p_t_key'] = idx_list[0]

        p_box = st.container()
        with p_box:
            st.subheader("👥 상대방 기본 정보")
            f_name = st.text_input("상대방 이름", key="f_n")
            f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_g", on_change=sync_user_gender)
            f_marital = st.selectbox("상대방 혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="f_m_stat")
            f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c")
            
            p_col1, p_col2, p_col3 = st.columns(3)
            f_y = p_col1.number_input("년도(상대)", 1900, 2050, key="p_y_in")
            f_m = p_col2.number_input("월(상대)", 1, 12, key="p_m_in")
            f_d = p_col3.number_input("일(상대)", 1, 31, key="p_d_in")
            
            p_t_idx = idx_list.index(st.session_state["p_t_key"]) if st.session_state["p_t_key"] in idx_list else 0
            f_t = st.selectbox("태어난 시간(상대)", idx_list, index=p_t_idx, key="p_t_select")
            st.session_state["p_t_key"] = f_t

    # ==============================================================================
    # 📌 택일 및 기타 특화 옵션
    # ==============================================================================
    if "2-2." in u_product:
        date_mode = st.radio("결혼 택일 방식", ["기간 선택", "특정일 지정"], key="radio_marriage_mode")
        if date_mode == "기간 선택":
            col_start, col_end = st.columns(2)
            start_date = col_start.date_input("시작일", key="start_date_m")
            end_date = col_end.date_input("종료일", key="end_date_m")
        else:
            target_date = st.date_input("결혼 예정일 선택", key="target_date_m")
            
    elif "2-3." in u_product:
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

    elif "3-2." in u_product:
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
