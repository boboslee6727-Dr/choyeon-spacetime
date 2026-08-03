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
APP_VERSION = "ver 70.5 Master"
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

    st.markdown("<div style='font-size: 17px; font-weight: 900; color: #000000; margin-bottom: 10px; font-family: \"Nanum Gothic\", sans-serif;'>📋 분석 상품 선택</div>", unsafe_allow_html=True)

    main_category = st.selectbox("어떤 상담을 원하십니까?", ["1. 개인 사주팔자 풀이", "2. 커플 연애/결혼운 (궁합) 풀이", "3. 타 감명서 비교"], key="main_category", on_change=stop_ai)

    u_product = "1-1. 사주팔자 및 대운 분석"

    if main_category == "1. 개인 사주팔자 풀이":
        u_product = st.radio(
            "상세 분석 항목:", 
            [
                "1-1. 사주팔자 및 대운 분석", 
                "1-2. 올 해의 운세 상세 분석", 
                "1-3. 이번 달의 운세 상세 분석", 
                "1-4. 주간 및 오늘의 일운(일진) 분석", 
                "1-5. 재물운 특화 분석", 
                "1-6. 직업/진학운 특화 분석", 
                "1-7. 건강운 특화 분석", 
                "1-8. 이사 및 방위 특화 분석"
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
    # 🔍 범용 사주간지 역산 입력부
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
                safe_gan = {'갑':'甲','을':'乙','병':'丙','정':'丁','무':'戊','기':'己','경':'庚','신':'辛','임':'壬','계':'癸'}
                safe_ji = {'자':'子','축':'丑','인':'寅','묘':'卯','진':'辰','사':'巳','오':'午','미':'未','신':'申','유':'酉','술':'戌','해':'亥'}
                
                ry_h = safe_gan.get(_ry[0], _ry[0]) + safe_ji.get(_ry[1], _ry[1])
                rm_h = safe_gan.get(_rm[0], _rm[0]) + safe_ji.get(_rm[1], _rm[1])
                rd_h = safe_gan.get(_rd[0], _rd[0]) + safe_ji.get(_rd[1], _rd[1])
                
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
                                    u_rt_h = safe_ji.get(ji_char_u, ji_char_u)
                                    target_time_str = time_map.get(u_rt_h, "시간 모름")
                                else:
                                    target_time_str = "시간 모름"
                                
                                st.session_state['s_t'] = target_time_str
                                st.session_state['s_t_select'] = target_time_str
                                
                                found = True
                                
                                s_sol_fmt = f"{curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일"
                                s_lun_fmt = f"{klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일"
                                st.session_state['rev_success_msg'] = f"✅양력{s_sol_fmt}\n 음력{s_lun_fmt}\n"
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
            kst_tz = pytz.timezone('Asia/Seoul')
            today_kst_date = dt_mod.datetime.now(kst_tz).date()
            
            daily_calc_date = st.date_input(
                "일운 분석 기준일 선택", 
                value=st.session_state.get("daily_calc_date", today_kst_date), 
                key="daily_calc_date"
            )
        elif "1-5." in u_product: 
            wealth_goal = st.text_input("고민되는 금전 문제는?", key="wealth_goal")
        elif "1-6." in u_product: 
            career_goal = st.text_input("고민되는 직업/진학 분야는?", key="career_goal")
        elif "1-7." in u_product: 
            health_goal = st.text_input("관리할 건강 부위는?", key="health_goal")
        elif "1-8." in u_product:
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
                    safe_gan = {'갑':'甲','을':'乙','병':'丙','정':'丁','무':'戊','기':'己','경':'庚','신':'辛','임':'壬','계':'癸'}
                    safe_ji = {'자':'子','축':'丑','인':'寅','묘':'卯','진':'辰','사':'巳','오':'午','미':'未','신':'申','유':'酉','술':'戌','해':'亥'}
                    
                    p_ry_h = safe_gan.get(_p_ry[0], _p_ry[0]) + safe_ji.get(_p_ry[1], _p_ry[1])
                    p_rm_h = safe_gan.get(_p_rm[0], _p_rm[0]) + safe_ji.get(_p_rm[1], _p_rm[1])
                    p_rd_h = safe_gan.get(_p_rd[0], _p_rd[0]) + safe_ji.get(_p_rd[1], _p_rd[1])
                    
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
                                        p_rt_h = safe_ji.get(ji_char_p, ji_char_p)
                                        st.session_state['p_t_key'] = time_map.get(p_rt_h, "시간 모름")
                                    else:
                                        st.session_state['p_t_key'] = "시간 모름"
                                    found = True
                                    
                                    p_sol_fmt = f"{curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일"
                                    p_lun_fmt = f"{klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일"
                                    st.session_state['rev_p_success_msg'] = f"✅양력{p_sol_fmt}\n음력{p_lun_fmt}\n"
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
    
    current_user_key = f"{main_category}_{u_n}_{u_g}_{u_m}_{u_y}_{u_mo}_{u_d}"
    
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
# 3. 메인 화면 범용 연산 및 AI 통변 엔진 실행부
# ==============================================================================
if st.session_state.get('app_running', False):
    if any(x in u_product for x in ["1-", "3-1."]):
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
            
        curr_year = dt_mod.datetime.now().year
        curr_m = dt_mod.datetime.now().month
        age = curr_year - sol_y + 1
        p_icon = "♂️" if gender == "남성" else "♀️"
        today_str = dt_mod.datetime.now().strftime("%Y년 %m월 %d일")

        def extract_time(time_str):
            if "모름" in time_str: return 0, 0
            match = re.search(r'(\d{2}):(\d{2})', time_str)
            return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

        with st.spinner(f"⏳ [{u_product.strip()}] 범용 시공명리 연산 및 정밀 분석 중...."):
            h, m = extract_time(b_time)
            
            # engine.py: -30분 동경시차 및 태양 황경(Ephem) 적용 연주/월주 선언
            y_pillar, m_pillar, lon = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
            is_lunar_val, is_leap_val = ("음력" in u_cal), ("윤달" in u_cal)
            _, _, d_pillar = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)
            
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
             
            gans, jjis = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]], [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
            hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
            hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]
            
            base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
            adj_mins = engine.get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            
            order_dir = 1 if (engine.GAN.index(ys) % 2 == 0) == (gender == '남성') else -1
            calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
            direction_str = "순행" if order_dir == 1 else "역행"
            
            counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
            for c in gans + jjis:
                oh = engine.get_color(c)
                if oh in counts: counts[oh] += 1
            
            guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 해','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
            guiin_str = guiin_map.get(ds_hanja, '없음')
            curr_y_ji = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'][(curr_year - 1984) % 12]
            
            n_gong = engine.calculate_gongmang(ys, yb) or "-"
            i_gong = engine.calculate_gongmang(ds, db) or "-"
            cur_samjae = engine.get_samjae(yb, curr_y_ji)
            samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"
            
            sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
            lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
            time_str_fmt = f"{b_time.split('(')[0].strip()}" if b_time != "시간 모름" else "시간 미상"
            
            cover_html = html_views.get_personal_cover(APP_VERSION, p_icon, name, sol_str_fmt, lun_str_fmt, b_time, today_str)
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
                j_hanja = engine.K2H_JI.get(j_hangul, j_hangul)
                is_active = (val <= age < val + 10)
                
                daewun_data_list.append({
                    "age_range": f"{val}~{val+9}세",
                    "ss_gan": engine.get_ss(ds_hanja, c_hangul),
                    "c_hanja": c_hanja,
                    "c_hangul": c_hangul,
                    "j_hanja": j_hanja,
                    "j_hangul": j_hangul,
                    "ss_ji": engine.get_ss(ds_hanja, j_hangul),
                    "un_sung": engine.get_unsung(ds_hanja, j_hangul),
                    "shin_sal": engine.get_12_shinsal(yb, j_hangul),
                    "is_current": is_active,
                    "is_first": (i == 0)
                })

            try:
                all_daewun_data = engine.get_daeun_fact_string(daewun_data_list)
            except:
                pass 

            un_html = html_views.generate_daewun_layout(daewun_data_list, direction_str, calc_d, get_oh_class)

            try:
                current_daewun_age = max(0, int(cur_dw_idx) * 10 + int(calc_d))
                start_year = int(sol_y) + current_daewun_age - 1
            except:
                current_daewun_age = max(0, int(age))
                start_year = curr_year

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
                    bg_col, b_left,
                    is_cur_yr
                )
                
            dw_title_hanja = f"({engine.K2H_GAN.get(dw_g_cur, dw_g_cur)}{engine.K2H_JI.get(dw_j_cur, dw_j_cur)}대운 기준)"
            sewun_html = html_views.get_sewun_layout(f"[ 세운의 흐름 {dw_title_hanja} ]", se_content)

            wol_content = ""
            for i in range(12):
                tm = i + 1
                _, m_pillar, _ = engine.get_true_year_month_pillar(curr_year, tm, 15, 12, 0)
                
                wc_hanja = m_pillar[0]
                wj_hanja = m_pillar[1]
                
                is_cur_m = (tm == curr_m)
                bg_col = "#E8F5E9" if is_cur_m else "transparent"
                b_left = "1px solid #ccc"
                
                wol_content += html_views.get_wolun_cell(
                    tm, 
                    engine.get_ss(ds_hanja, wc_hanja), wc_hanja, get_oh_class(wc_hanja), 
                    wj_hanja, get_oh_class(wj_hanja), engine.get_ss(ds_hanja, wj_hanja), 
                    engine.get_unsung(ds_hanja, wj_hanja), 
                    engine.get_12_shinsal(yb, wj_hanja), 
                    bg_col, b_left,
                    is_cur_m
                )

            wolun_html = html_views.get_wolun_layout(f"[ 월운의 흐름 ({curr_year}년도 양력기준) ]", wol_content)

            weekly_daily_html = ""
            weekly_ganji_list = "월~일 주간 간지 데이터"
            m_che_first, am_yong = "오전 체", "오전 용"
            m_che_second, pm_yong = "오후 체", "오후 용"
            day_wunseong, day_12shinsal = "건록", "망신살"

            if "1-4." in u_product:
                kst_tz = pytz.timezone('Asia/Seoul')
                now_dt = dt_mod.datetime.now(kst_tz)
                
                today_day = now_dt.day
                
                idx_from_sun = (now_dt.weekday() + 1) % 7
                sunday_dt = now_dt - dt_mod.timedelta(days=idx_from_sun)
                
                weekdays_str = ['일', '월', '화', '수', '목', '금', '토']
                weekly_days_data = []
                
                for i in range(7):
                    target_dt = sunday_dt + dt_mod.timedelta(days=i)
                    _, _, d_pillar = engine.get_ganji_from_date(target_dt.year, target_dt.month, target_dt.day) if hasattr(engine, 'get_ganji_from_date') else ("", "", ("",""))
                    ganji_str = f"{d_pillar[0]}{d_pillar[1]}" if d_pillar and len(d_pillar)>=2 else "-"
                    is_today = (target_dt.date() == now_dt.date())
                    
                    weekly_days_data.append({
                        'day': target_dt.day,
                        'weekday': weekdays_str[i],
                        'ganji': ganji_str,
                        'is_today': is_today
                    })
                
                weekly_calendar_html = html_views.generate_weekly_calendar_html(weekly_days_data, today_day) if hasattr(html_views, 'generate_weekly_calendar_html') else ""

                w_d_res = engine.get_weekly_daily_facts(ds, db, yb, curr_year, curr_m, today_day) if hasattr(engine, 'get_weekly_daily_facts') else {}
                weekly_ganji_list = w_d_res.get('weekly_ganji_list', weekly_ganji_list)
                m_che_first = w_d_res.get('m_che_first', m_che_first)
                am_yong = w_d_res.get('am_yong', am_yong)
                m_che_second = w_d_res.get('m_che_second', m_che_second)
                pm_yong = w_d_res.get('pm_yong', pm_yong)
                day_wunseong = w_d_res.get('day_wunseong', day_wunseong)
                day_12shinsal = w_d_res.get('day_12shinsal', day_12shinsal)
                
                daily_table_html = html_views.generate_weekly_daily_layout(
                    weekly_ganji_list, today_day, ds, db, 
                    m_che_first, am_yong, m_che_second, pm_yong, day_wunseong, day_12shinsal
                ) if hasattr(html_views, 'generate_weekly_daily_layout') else ""

                weekly_daily_html = str(weekly_calendar_html) + str(daily_table_html)
                weekly_daily_html = weekly_daily_html.replace('\n', '')

            choyeon_db = load_choyeon_db()
            w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{d_pillar[1]}".strip() if 'd_pillar' in locals() and len(d_pillar)>=2 else f"{ds}{db}".strip()
            w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
            i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
            struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
            s_name, s_type, s_desc = struct_data[0], struct_data[1], struct_data[2]
            golden_text_html = html_views.get_golden_text(name, w_val, i_val, s_name, s_type, s_desc)

            closing_html = html_views.get_closing_html(name)            
            closing_part = str(closing_html or "").strip()

            part_1_fact = (
                str(info_h or "") + 
                str(table_html or "") + str(master_bar_html or "") + 
                str(un_html or "") + str(sewun_html or "") + str(wolun_html or "") + 
                str(weekly_daily_html or "")
            )
            part_2_intro = str(intro_html or "")
            part_3_golden = str(golden_text_html or "")
            part_5_closing = str(closing_part or "")

            if main_category == "1. 개인 사주팔자 풀이":
                st.session_state['base_fact_cache'] = part_1_fact + part_2_intro + part_3_golden
            else:
                st.session_state['base_fact_cache'] = part_1_fact

            # ==============================================================================
            # 💡 [범용 완전 정돈본] 변수선언 안전확보 ➔ engine.py 5x5 연산 ➔ prompts.py
            # ==============================================================================
            
            # 1. 오늘 기준 KST 날짜 및 동경시차(-30분) 반영 일간/일지 안전 추출
            now_dt = dt_mod.datetime.now(pytz.timezone('Asia/Seoul'))
            _, _, d_pillar_today = engine.get_ganji_from_date(now_dt.year, now_dt.month, now_dt.day)
            i_gan, i_ji = d_pillar_today[0], d_pillar_today[1]

            # 2. 올해 세운 및 현재 월운 간지 안전 확보 (순서 역전 방지)
            try:
                current_sewun_base = (curr_year - 1984) % 60
                c_s_g = engine.GAN[current_sewun_base % 10]
                c_s_j = engine.JI[current_sewun_base % 12]
            except:
                c_s_g, c_s_j = "丙", "午"

            cur_sewun_gan = locals().get('cur_sewun_gan', c_s_g)
            cur_sewun_ji = locals().get('cur_sewun_ji', c_s_j)
            
            try:
                c_w_g, c_w_j = engine.get_current_wolun_gan_ji()
            except:
                c_w_g, c_w_j = "乙", "未"

            cur_wol_g_val = locals().get('cur_wol_g', c_w_g)
            cur_wol_j_val = locals().get('cur_wol_j', c_w_j)

            # 3. engine.py에서 -30분 동경시차 및 Ephem 절기가 정밀 반영된 범용 5x5 체용 팩트 연산
            w_facts = engine.get_woonse_analysis_facts(
                ds, db, dw_g_cur, dw_j_cur, cur_sewun_gan, cur_sewun_ji, cur_wol_g_val, cur_wol_j_val, i_gan, i_ji
            )

            # 4. 상품별 프롬프트 분기 정의
            extra_facts = {}
            if "1-1." in u_product:
                target_prompt = getattr(prompts, 'PERSONAL_SAJU_PROMPT', "")
            elif "1-2." in u_product:
                target_prompt = getattr(prompts, 'SEWUN_PROMPT', "")
            elif "1-3." in u_product:
                target_prompt = getattr(prompts, 'WOLWUN_PROMPT', "")
            elif "1-4." in u_product:
                target_prompt = getattr(prompts, 'WEEKLY_DAILY_PROMPT', "")
            elif "1-5." in u_product:
                target_prompt = getattr(prompts, 'WEALTH_PROMPT', "")
            elif "1-6." in u_product:
                target_prompt = getattr(prompts, 'CAREER_PROMPT', "")
            elif "1-7." in u_product:
                target_prompt = getattr(prompts, 'HEALTH_PROMPT', "")
            elif "1-8." in u_product:
                target_prompt = getattr(prompts, 'MOVING_DIRECTION_PROMPT', "")
            else:
                target_prompt = getattr(prompts, 'PERSONAL_SAJU_PROMPT', "")

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
            shinsal_raw = engine.get_general_shinsal_filtered(1, gans, jjis, gender)
            shinsal_str = ", ".join([re.sub(r'<[^>]+>', '', s) for s in shinsal_raw]) if shinsal_raw else "특이 신살 없음"

            yongshin_str = engine.get_yongshin_analysis(counts, mb, ds) if hasattr(engine, 'get_yongshin_analysis') else f"격국: {gyukgook_detail}"
            goshin_gwasook_str = engine.get_goshin_gwasook(yb, gender) if hasattr(engine, 'get_goshin_gwasook') else "특이 고신/과숙 없음"

            _current_locals = locals()
            _current_globals = globals()
            
            def get_val(*keys):
                for k in keys:
                    if 'st' in _current_globals and hasattr(_current_globals['st'], 'session_state'):
                        if k in _current_globals['st'].session_state and _current_globals['st'].session_state[k]:
                            v = str(_current_globals['st'].session_state[k]).strip()
                            if v: return v
                    if k in _current_locals and _current_locals[k]:
                        v = str(_current_locals[k]).strip()
                        if v: return v
                    if k in _current_globals and _current_globals[k]:
                        v = str(_current_globals[k]).strip()
                        if v: return v
                return None

            career_val = get_val('u_career_issue', 'u_job', 'user_query', 'u_question') or "특별히 제시된 고민 내용 없음"
            wealth_val = get_val('u_wealth_issue', 'u_wealth_goal', 'u_money_issue') or "특별히 제시된 고민 내용 없음"
            health_val = get_val('u_health_goal') or "전반적인 건강 체질 관리"
            question_val = get_val('u_question') or "특별히 제시된 질문 없음"

            universal_str = engine.get_universal_fact_str(ds, db, mb, yb, hb) if hasattr(engine, 'get_universal_fact_str') else "지장간 좌법 및 인종법 연산 팩트"

            if age < 20:
                age_p = f"현재 {age}세 미성년자/학생이므로 학업, 진학, 부모와의 관계, 성장기 성격 형성에 집중하여 서술하십시오."
            elif age < 40:
                age_p = f"현재 {age}세 청년층이므로 사회 초년/취업, 직장 운, 첫 취직/이직, 연애 및 취업/결혼 준비에 집중하여 서술하십시오."
            elif age < 60:
                age_p = f"현재 {age}세 중년층이므로 직장 내 승진/책임, 사업 확장, 재물 축적, 자녀 양육 및 건강 관리에 집중하여 서술하십시오."
            else:
                age_p = f"현재 {age}세 노년층이므로 은퇴 후 삶, 노후 재정 안정, 자녀와의 관계, 건강 관리 및 삶의 보람에 집중하여 서술하십시오."

            if gender == "여성":
                gender_p = "여성 내담자(여명)이므로 육친 적용 시 관성(官星)을 배우자/남편으로, 식상(食傷)을 자식으로 엄격히 적용하십시오."
            else:
                gender_p = "남성 내담자(남명)이므로 육친 적용 시 재성(財星)을 배우자/아내로, 관성(官星)을 자식으로 엄격히 적용하십시오."

            yukchin_r = engine.get_yukchin_rule(gender, u_marital)

            # 5. prompts.py 전용 범용 바인딩 딕셔너리 세팅
            prompt_data = {
                # 기본 내담자 프로필
                "name": name, "age": age, "gender": gender, "marital": u_marital,
                "age_prompt": age_p, "gender_prompt": gender_p, "yukchin_rule": yukchin_r,
                
                # engine.py에서 -30분 시차 및 절기로 완벽 계산된 범용 팩트
                "woonse_fact_str": w_facts["woonse_fact_str"],
                "dw_che": w_facts["dw_che"], "sewun_kw": w_facts["sewun_kw"],
                "wolun_kw": w_facts["wolun_kw"], "ilun_kw": w_facts["ilun_kw"],
                
                # 사주 원국 및 신살/격국/용신
                "ys": ys, "yb": yb, "ms": ms, "mb": mb, "ds": ds, "db": db, "hs": hs, "hb": hb,
                "gyukgook_detail": gyukgook_detail, "yongshin_str": yongshin_str,
                "goshin_gwasook_str": goshin_gwasook_str, "gongmang_actual": i_gong, "year_gongmang": n_gong,
                "universal_str": universal_str,
                "mok": counts['목'], "hwa": counts['화'], "to": counts['토'], "geum": counts['금'], "su": counts.get('수', 0),
                "oheng_total": sum(counts.values()), "ss_unsung_str": ss_unsung_str, "won_guk_vaults_str": won_guk_vaults_str,
                "hap_chung_hyoung_pa_hae": hap_chung_hyoung_pa_hae, "cheon_eul": guiin_str, "s12_str": s12_str, 
                "shinsal_str": shinsal_str, "cur_samjae": cur_samjae,
                
                # 행운(대운/세운/월운/일운) 간지
                "curr_y": curr_year, "sewun_gan": cur_sewun_gan, "sewun_ji": cur_sewun_ji,
                "dw_g_cur": dw_g_cur, "dw_j_cur": dw_j_cur, "cur_wol_g": cur_wol_g_val, "cur_wol_j": cur_wol_j_val,
                "weekly_ganji_list": weekly_ganji_list, "t_month": curr_m, "t_day": now_dt.day,
                "m_ilgan": ds, "m_ilji": db, "m_che_first": m_che_first, "am_yong": am_yong,
                "m_che_second": m_che_second, "pm_yong": pm_yong, "day_wunseong": day_wunseong, "day_12shinsal": day_12shinsal,
                "sewun_fact_str": f"올해 체용 키워드: [{w_facts['sewun_kw']}]",
                "wol_fact_str": f"이번달 체용 키워드: [{w_facts['wolun_kw']}]",
                "dw_fact_str": f"대운 체용 키워드: [{w_facts['dw_kw']}]",
                
                # 기타 특화 상담 입력 데이터
                "ohang_balance_str": f"목:{counts['목']}, 화:{counts['화']}, 토:{counts['토']}, 금:{counts['금']}, 수:{counts.get('수', 0)}",
                "weak_health_str": "취약 장기 및 신체 부위 분석 팩트", "health_goal": health_val,
                "jaeseong_str": "재성 세력 분석 팩트", "wealth_fact_str": "금전 흐름 체용 매트릭스",
                "career_fact_str": "직업/진학 핵심 십성 분석", "user_query": career_val,
                "wealth_issue": wealth_val, "u_question": question_val
            }
            
            # 6. 프롬프트 안전 치환
            class SafeDict(dict):
                def __missing__(self, key):
                    return '{' + key + '}'
            
            formatted_prompt = target_prompt.format_map(SafeDict(prompt_data))
            
            # 7. 단일 정돈 Gemini API 호출
            try:
                raw_response = call_gemini_api(formatted_prompt, extra_facts, model="gemini-2.5-flash")
            except TypeError:
                raw_response = call_gemini_api(formatted_prompt, extra_facts)
            
            if raw_response and isinstance(raw_response, str):
                cleaned = raw_response.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
                cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
                cleaned = re.sub(r'#{1,6}\s*', '', cleaned)
                ai_output_html = html_views.format_ai_text_to_html(cleaned)
            else:
                ai_output_html = "<p style='padding:20px;'>분석 결과를 불러오지 못했습니다. 다시 시도해 주십시오.</p>"

            # 8. VIP 스마트 누적 모드 및 일반 모드 저장 아키텍처
            is_vip_active = st.session_state.get("is_vip_package_val", False) if "1-1." in u_product else False

            if 'report_essays' not in st.session_state:
                st.session_state['report_essays'] = {}
            if 'vip_base_fact' not in st.session_state:
                st.session_state['vip_base_fact'] = ""

            if not st.session_state['vip_base_fact'] or not is_vip_active:
                st.session_state['vip_base_fact'] = part_1_fact + part_2_intro + part_3_golden

            if "1-4." in u_product:
                current_ai_block = f"<div style='margin-top: 20px;'>{ai_output_html}</div>" if ai_output_html else ""
            else:
                cleaned_ai = re.sub(r'>\s+<', '><', ai_output_html.replace('\n', '')).strip() if ai_output_html and 're' in globals() else ai_output_html
                current_ai_block = f"<div style='margin-top: 20px;'>{cleaned_ai}</div>" if cleaned_ai else ""

            if is_vip_active:
                st.session_state['report_essays'][u_product] = current_ai_block
            else:
                st.session_state['report_essays'] = {u_product: current_ai_block}

            # 표지 단 1회 출력
            st.markdown(cover_html, unsafe_allow_html=True)

            # 📚 [최종 종합 보고서 조립 및 렌더링]
            if "3-1." in u_product or u_product == "타 감명서":
                try:
                    part_4_ai = f"<div style='margin-top: 20px;'>{ai_output_html}</div>" if ai_output_html else ""
                    first_stage_html = part_1_fact + part_2_intro + part_3_golden + part_4_ai + part_5_closing
                    st.markdown(html_views.get_final_report_box(first_stage_html), unsafe_allow_html=True)
                    
                    other_text_input = st.session_state.get(f"text_{u_product}", "")
                    
                    if other_text_input and len(str(other_text_input).strip()) > 0:
                        u_name_str = name
                        p_icon_str = p_icon
                        sol_val = sol_str_fmt
                        lun_val = lun_str_fmt
                        time_val = b_time
                        today_val = today_str
                        
                        other_cover_html = html_views.get_comparison_saju_cover(
                            APP_VERSION, p_icon_str, u_name_str, sol_val, lun_val, time_val, today_val
                        )
                        st.markdown(other_cover_html, unsafe_allow_html=True)
                        
                        report_2_html = html_views.get_other_report_original_html(other_text_input)
                        st.markdown(report_2_html, unsafe_allow_html=True)
                        
                        with st.spinner("⚖️ 1:1 상세 비교 리포트 분석 중..."):
                            u_name_val = name
                            u_gender_val = gender
                            u_age_val = age
                            u_marital_val = u_marital if 'u_marital' in locals() else (marital if 'marital' in locals() else "미혼")
                            
                            b_y = sol_y
                            b_m = sol_m
                            b_d = sol_d
                            b_t = b_time
                            
                            g_list = gans
                            j_list = jjis
                            pillar_str = f"{g_list[3]}{j_list[3]}년 {g_list[2]}{j_list[2]}월 {g_list[1]}{j_list[1]}일 {g_list[0]}{j_list[0]}시" if len(g_list) >= 4 else ""
                            calc_daewun = calc_d

                            saju_fact_summary = f"👤 신청인: <b>{u_name_val}</b> 님 ({u_gender_val}, {u_age_val}세, {u_marital_val}) &nbsp;|&nbsp; <b>{b_y}년 {b_m}월 {b_d}일 {b_t}</b><br>📜 사주명식: <b>{pillar_str}</b> (대운수: {calc_daewun})"
                            
                            comp_prompt = prompts.COMPARE_PERSONAL_PROMPT.format(
                                name=name, age=age, gender=gender, marital=u_marital_val,
                                full_content_clean=str(locals().get('ai_output_html', '')).strip(),
                                other_report=str(other_text_input).strip(),
                                fact_reference=saju_fact_summary
                            )
                            
                            c_res = call_gemini_api(comp_prompt)
                            
                            if c_res:
                                c_res_clean = re.sub(r'<!--.*?-->', '', c_res, flags=re.DOTALL)
                                c_res_clean = re.sub(r'```[a-zA-Z]*', '', c_res_clean).replace("```", "").strip()
                                c_res_clean = re.sub(r'#{1,6}\s*', '', c_res_clean)
                                c_res_clean = c_res_clean.replace("&lt;", "<").replace("&gt;", ">")
                                
                                formatted_comp = html_views.format_ai_text_to_html(c_res_clean)
                                
                                section_header_html = """<div style='margin-bottom:25px; padding-bottom:12px; border-bottom:2px solid #3E2723;'>
                                    <h2 style='font-family:"Nanum Myeongjo", serif !important; font-size:22px !important; font-weight:900 !important; color:#000000 !important; margin:0 !important; text-align:center;'>
                                        📜 타 감명서 1:1 상세 분석
                                    </h2>
                                </div>"""
                                
                                full_stage3_html = section_header_html + f"<div style='text-align: left !important;'>{formatted_comp}</div>"
                                st.markdown(html_views.get_final_report_box(full_stage3_html), unsafe_allow_html=True)
                            else:
                                st.error("⚠️ 타 감명서 비교 분석 AI 응답을 불러오지 못했습니다.")
                    else:
                        st.warning("⚠️ 타 감명서 원문이 입력되지 않았습니다. 텍스트 상자에 원문을 붙여넣어 주십시오.")
                
                except Exception as e:
                    st.error(f"🚨 [3-1. 타 감명서 비교] 처리 중 오류 발생: {e}")

            else:
                master_composite_report = st.session_state['vip_base_fact']

                for prod_name, essay_block in st.session_state['report_essays'].items():
                    master_composite_report += essay_block

                master_composite_report += part_5_closing

                st.markdown(html_views.get_final_report_box(master_composite_report), unsafe_allow_html=True)

    elif any(x in u_product for x in ["2-1", "3-2"]):
        st.markdown("---")
        with st.spinner("⏳ 두 분의 시공간을 교차 분석 중입니다..."):
            try:
                user_gender = st.session_state.get("u_g", gender)
                curr_y = dt_mod.datetime.now().year
                m_age = curr_y - int(b_year) + 1
                p_age = curr_y - int(f_y) + 1
                
                klc = KoreanLunarCalendar()
                klc.setSolarDate(int(b_year), int(b_month), int(b_day))
                m_sol, m_lun = f"{b_year}년 {b_month}월 {b_day}일", f"{klc.lunarYear}년 {klc.lunarMonth}월 {klc.lunarDay}일"
                klc.setSolarDate(int(f_y), int(f_m), int(f_d))
                f_sol, f_lun = f"{f_y}년 {f_m}월 {f_d}일", f"{klc.lunarYear}년 {klc.lunarMonth}월 {klc.lunarDay}일"
                
                if user_gender == "여성":
                    marital_status = f"{f_marital}-{u_marital}" 
                    gh_data = engine.get_gunghap_data(
                        int(f_y), int(f_m), int(f_d), f_t, f_marital,
                        int(b_year), int(b_month), int(b_day), b_time, u_marital,
                        marital_status
                    )
                    male_name, male_age, male_sol, male_lun, male_time, male_marital = f_name, p_age, f_sol, f_lun, f_t, f_marital
                    female_name, female_age, female_sol, female_lun, female_time, female_marital = name, m_age, m_sol, m_lun, b_time, u_marital
                else:
                    marital_status = f"{u_marital}-{f_marital}" 
                    gh_data = engine.get_gunghap_data(
                        int(b_year), int(b_month), int(b_day), b_time, u_marital, 
                        int(f_y), int(f_m), int(f_d), f_t, f_marital,                
                        marital_status
                    )
                    male_name, male_age, male_sol, male_lun, male_time, male_marital = name, m_age, m_sol, m_lun, b_time, u_marital
                    female_name, female_age, female_sol, female_lun, female_time, female_marital = f_name, p_age, f_sol, f_lun, f_t, f_marital

                m_data, m_master_list, m_daewun = gh_data["m_table"], gh_data["m_master"], gh_data["m_daewun"]
                f_data, f_master_list, f_daewun = gh_data["w_table"], gh_data["w_master"], gh_data["w_daewun"]

                m_ys, m_yb = gh_data.get("m_ys", ""), gh_data.get("m_yb", "")
                m_ms, m_mb = gh_data.get("m_ms", ""), gh_data.get("m_mb", "")
                m_ds, m_db = gh_data.get("m_ds", ""), gh_data.get("m_db", "")
                m_hs, m_hb = gh_data.get("m_hs", ""), gh_data.get("m_hb", "")

                f_ys, f_yb = gh_data.get("f_ys", ""), gh_data.get("f_yb", "")
                f_ms, f_mb = gh_data.get("f_ms", ""), gh_data.get("f_mb", "")
                f_ds, f_db = gh_data.get("f_ds", ""), gh_data.get("f_db", "")
                f_hs, f_hb = gh_data.get("f_hs", ""), gh_data.get("f_hb", "")

                choyeon_db = load_choyeon_db() if 'load_choyeon_db' in globals() else {}

                m_w_key, m_i_key = f"{m_ms}{m_mb}".strip(), f"{m_ds}{m_db}".strip()
                m_w_val = choyeon_db.get("wolryeong", {}).get(m_w_key, f"[{m_w_key}] 시공간 데이터 없음")
                m_i_val = choyeon_db.get("ilju", {}).get(m_i_key, f"[{m_i_key}] 성품 데이터 없음")
                m_struct = choyeon_db.get("ilju_structure", {}).get(m_i_key, ["구조 미상", "유형 미상", "성향 미상"])
                m_golden_html = html_views.get_golden_text(male_name, m_w_val, m_i_val, m_struct[0], m_struct[1], m_struct[2]) if hasattr(html_views, 'get_golden_text') else ""
                m_golden_text = f"초연 시공명리학적으로 풀이하면 {male_name}님은 '{m_w_val}'의 시공간에서, '{m_i_val}'의 성품을 가지고 태어나셨으며, 성격은 '{m_struct[0]}'인 '{m_struct[1]}'으로, '{m_struct[2]}'하는 성향이 있습니다."

                f_w_key, f_i_key = f"{f_ms}{f_mb}".strip(), f"{f_ds}{f_db}".strip()
                f_w_val = choyeon_db.get("wolryeong", {}).get(f_w_key, f"[{f_w_key}] 시공간 데이터 없음")
                f_i_val = choyeon_db.get("ilju", {}).get(f_i_key, f"[{f_i_key}] 성품 데이터 없음")
                f_struct = choyeon_db.get("ilju_structure", {}).get(f_i_key, ["구조 미상", "유형 미상", "성향 미상"])
                f_golden_html = html_views.get_golden_text(female_name, f_w_val, f_i_val, f_struct[0], f_struct[1], f_struct[2]) if hasattr(html_views, 'get_golden_text') else ""
                f_golden_text = f"초연 시공명리학적으로 풀이하면 {female_name}님은 '{f_w_val}'의 시공간에서, '{f_i_val}'의 성품을 가지고 태어나셨으며, 성격은 '{f_struct[0]}'인 '{f_struct[1]}'으로, '{f_struct[2]}'하는 성향이 있습니다."

                m_time_clean = male_time if male_time.endswith("시") else f"{male_time}시"
                f_time_clean = female_time if female_time.endswith("시") else f"{female_time}시"

                m_info = html_views.get_info_header("♂️", male_name, "남성", male_marital, male_age, male_sol, male_lun, m_time_clean, p_color="#1A237E")
                w_info = html_views.get_info_header("♀️", female_name, "여성", female_marital, female_age, female_sol, female_lun, f_time_clean, p_color="#2E7D32")
                
                cover_html = html_views.get_gunghap_cover(
                    APP_VERSION, male_name, male_age, male_sol, male_lun, male_time,  
                    female_name, female_age, female_sol, female_lun, female_time, 
                    dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
                )
                
                intro_h = html_views.get_intro_html() 

                m_table = html_views.get_gunghap_saju_table(*m_data[1:])
                m_master_html = html_views.get_master_bar(
                    m_master_list[0], m_master_list[1], m_master_list[2], m_master_list[3], m_master_list[4], 
                    m_master_list[5], m_master_list[6], m_master_list[7], m_master_list[8], m_master_list[9], m_master_list[10]
                )
                m_un = html_views.generate_daewun_layout(*m_daewun)

                w_table = html_views.get_gunghap_saju_table(*f_data[1:])
                w_master_html = html_views.get_master_bar(
                    f_master_list[0], f_master_list[1], f_master_list[2], f_master_list[3], f_master_list[4], 
                    f_master_list[5], f_master_list[6], f_master_list[7], f_master_list[8], f_master_list[9], f_master_list[10]
                )
                w_un = html_views.generate_daewun_layout(*f_daewun)

                s_gan = cur_sewun_gan if 'cur_sewun_gan' in locals() else "丙"
                s_ji = cur_sewun_ji if 'cur_sewun_ji' in locals() else "午"
                w_gan = cur_wol_g if 'cur_wol_g' in locals() else "壬"
                w_ji = cur_wol_j if 'cur_wol_j' in locals() else "寅"
                
                male_pillars = [f"{m_ys}{m_yb}", f"{m_ms}{m_mb}", f"{m_ds}{m_db}", f"{m_hs}{m_hb}"]
                female_pillars = [f"{f_ys}{f_yb}", f"{f_ms}{f_mb}", f"{f_ds}{f_db}", f"{f_hs}{f_hb}"]

                gh_engine = engine.UniversalPrintableGunghap(
                    applicant=male_name,
                    partner_name=female_name,
                    male=male_pillars,
                    female=female_pillars,
                    daeun_score=10
                )
                gh_engine.run_universal_logic()

                gunghap_facts = {
                    "m_name": male_name, "m_age": male_age,
                    "m_ganju_str": f"년주:{m_ys}{m_yb}, 월주:{m_ms}{m_mb}, 일주:{m_ds}{m_db}, 시주:{m_hs}{m_hb}",
                    "m_ilju": m_i_key,
                    "m_dw_g_cur": m_daewun[0] if len(m_daewun) > 0 else "",
                    "m_dw_j_cur": m_daewun[1] if len(m_daewun) > 1 else "",
                    "m_sewun_gan": s_gan, "m_sewun_ji": s_ji,
                    "m_golden": m_golden_text,
                    "m_gyukgook": gh_data.get("m_gyukgook", "격국"),
                    "m_ds": m_ds, "m_db": m_db,
                    "m_gongmang_actual": gh_data.get("m_gongmang_actual", "공망"),
                    "m_spouse_star": gh_data.get("m_spouse_star", "재성 세력"),

                    "f_name": female_name, "f_age": female_age,
                    "f_ganju_str": f"년주:{f_ys}{f_yb}, 월주:{f_ms}{f_mb}, 일주:{f_ds}{f_db}, 시주:{f_hs}{f_hb}",
                    "f_ilju": f_i_key,
                    "f_dw_g_cur": f_daewun[0] if len(f_daewun) > 0 else "",
                    "f_dw_j_cur": f_daewun[1] if len(f_daewun) > 1 else "",
                    "f_sewun_gan": s_gan, "f_sewun_ji": s_ji,
                    "f_golden": f_golden_text,
                    "f_gyukgook": gh_data.get("f_gyukgook", "격국"),
                    "f_ds": f_ds, "f_db": f_db,
                    "f_gongmang_actual": gh_data.get("f_gongmang_actual", "공망"),
                    "f_spouse_star": gh_data.get("f_spouse_star", "관성 세력"),

                    "cur_wol_g": w_gan, "cur_wol_j": w_ji,
                    "db_header": "[초연 시공명리 정밀 해석 지침 적용]",
                    "ai_saju_mapping": "[상대적 시공간 세력 및 십성/12운성 자동 매핑 완료]",
                    "yukchin_rule": "[임관 표기 금지 -> 건록 대체 엄수]"
                }

                class SafeDict(dict):
                    def __missing__(self, key): return "{" + key + "}"

                safe_facts = SafeDict(**gunghap_facts)
                prompt_text = prompts.GUNGHAP_ESSAY_PROMPT.format_map(safe_facts)
                prompt_text += f"\n\n🚨 [주의]: 프롬프트 지시문 안의 '<...>' 예시 텍스트 문구를 그대로 복사하여 출력하지 말고, 주어진 사주팔자 팩트를 바탕으로 실제 완성된 통변 문장만 작성하십시오."

                ai_result = call_gemini_api(prompt_text)
                
                if ai_result:
                    clean_ai = re.sub(r'```[a-zA-Z]*', '', ai_result).replace("```", "").strip()
                    clean_ai = clean_ai.replace('[MALE_START]', '').replace('[MALE_END]', '').replace('[FEMALE_START]', '').replace('[FEMALE_END]', '').replace('[GUNGHAP_START]', '').replace('[GUNGHAP_END]', '').strip()
                    
                    couple_daewun_tables = html_views.get_couple_daewun_tables(gh_data) if hasattr(html_views, 'get_couple_daewun_tables') else ""
                    if '[COUPLE_DAEWUN_TABLES_HERE]' in clean_ai:
                        clean_ai = clean_ai.replace('[COUPLE_DAEWUN_TABLES_HERE]', couple_daewun_tables)
                    
                    formatted_ai = html_views.format_ai_text_to_html(clean_ai)
                    ai_output_html = f"<div style='text-align: left !important; line-height: 1.85;'>{formatted_ai}</div>"
                else:
                    ai_output_html = '<p style="color:red;">⚠️ 궁합 AI 통변 데이터를 생성하지 못했습니다.</p>'

                score_visual_html = html_views.get_gunghap_score_visual_html(gh_engine)
                ai_box_html = f'<div style="margin-top:20px; padding:20px; background-color:#ffffff; border-radius:10px; border:1px solid #E0E0E0;">{ai_output_html}</div>'

                closing_html = html_views.get_closing_html(f"{male_name} 님 & {female_name}") if hasattr(html_views, 'get_closing_html') else ""
                closing_part = str(closing_html or "").strip()

                full_inner_content = "".join([
                    str(m_info or ''), str(m_table or ''), str(m_master_html or ''), str(m_un or ''), str(m_golden_html or ''),
                    str(w_info or ''), str(w_table or ''), str(w_master_html or ''), str(w_un or ''), str(f_golden_html or ''),
                    str(intro_h or ''),
                    str(ai_box_html or ''),
                    str(score_visual_html or ''),
                    str(closing_part or '')
                ])
                
                clean_full_inner = re.sub(r'>\s+<', '><', full_inner_content.replace('\n', '')).strip()
                report_box = html_views.get_final_report_box(clean_full_inner)
                
                st.session_state['cached_gunghap_cover'] = cover_html
                st.session_state['cached_gunghap_report'] = report_box
                
                st.markdown(cover_html, unsafe_allow_html=True)
                st.markdown(report_box, unsafe_allow_html=True)

                if "3-2" in u_product:
                    other_text_input = st.session_state.get(f"text_{u_product}", "")
                    
                    if other_text_input and len(str(other_text_input).strip()) > 0:
                        today_val = dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
                        
                        gunghap_other_cover = html_views.get_comparison_gunghap_cover(
                            APP_VERSION, male_name, male_age, male_sol, male_lun, male_time,  
                            female_name, female_age, female_sol, female_lun, female_time, 
                            today_val
                        )
                        st.markdown(gunghap_other_cover, unsafe_allow_html=True)
                        
                        report_2_html = html_views.get_other_report_original_html(other_text_input)
                        st.markdown(report_2_html, unsafe_allow_html=True)

                        with st.spinner("⚖️ 궁합 1:1 상세 비교 리포트 분석 중..."):
                            gunghap_fact_summary = f"♂️ 남명: <b>{male_name}</b> 님 ({m_ys}{m_yb}년 {m_ms}{m_mb}월 {m_ds}{m_db}일 {m_hs}{m_hb}시)<br>♀️ 여명: <b>{female_name}</b> 님 ({f_ys}{f_yb}년 {f_ms}{f_mb}월 {f_ds}{f_db}일 {f_hs}{f_hb}시)"
                            
                            comp_prompt = prompts.COMPARE_GUNGHAP_PROMPT.format(
                                m_name=male_name, f_name=female_name,
                                full_content_clean=str(locals().get('ai_output_html', '')).strip(),
                                other_report=str(other_text_input).strip(),
                                fact_reference=gunghap_fact_summary
                            )
                            
                            ai_compare_result = call_gemini_api(comp_prompt)

                            if ai_compare_result:
                                clean_ai = re.sub(r'<!--.*?-->', '', ai_compare_result, flags=re.DOTALL)
                                clean_ai = re.sub(r'```[a-zA-Z]*', '', clean_ai).replace("```", "").strip()
                                clean_ai = re.sub(r'#{1,6}\s*', '', clean_ai)
                                clean_ai = clean_ai.replace("&lt;", "<").replace("&gt;", ">")
                                
                                formatted_comp = html_views.format_ai_text_to_html(clean_ai)
                                
                                gunghap_section_header = """<div style='margin-bottom:25px; padding-bottom:12px; border-bottom:2px solid #3E2723;'>
                                    <h2 style='font-family:"Nanum Myeongjo", serif !important; font-size:22px !important; font-weight:900 !important; color:#000000 !important; margin:0 !important; text-align:center;'>
                                        📜 타 궁합 감명서 1:1 상세 분석
                                    </h2>
                                </div>"""
                                
                                full_gunghap_stage3_html = gunghap_section_header + f"<div style='text-align: left !important;'>{formatted_comp}</div>" + str(closing_part or "")
                                st.markdown(html_views.get_final_report_box(full_gunghap_stage3_html), unsafe_allow_html=True)
                            else:
                                st.error("⚠️ 타 감명서 궁합 비교 분석 AI 응답을 불러오지 못했습니다.")
                    else:
                        st.warning("⚠️ 타 궁합 감명서 원문이 입력되지 않았습니다. 텍스트 상자에 원문을 붙여넣어 주십시오.")

            except Exception as e:
                st.error(f"🚨 궁합 및 타 감명서 비교 처리 중 오류 발생: {e}")

    elif "2-2." in u_product:
        if 'cached_gunghap_cover' in st.session_state:
            st.markdown(st.session_state['cached_gunghap_cover'], unsafe_allow_html=True)
        if 'cached_gunghap_report' in st.session_state:
            st.markdown(st.session_state['cached_gunghap_report'], unsafe_allow_html=True)

        st.markdown("---")
        with st.spinner("💍 초연 시공명리학 기반으로 지정하신 날짜의 시공간 에너지를 심층 분석 중입니다..."):
            try:
                date_mode = st.session_state.get("radio_marriage_mode", "기간 선택")
                s_y, s_m, s_d = st.session_state.get("s_y", 1980), st.session_state.get("s_m", 1), st.session_state.get("s_d", 1)
                p_y, p_m, p_d = st.session_state.get("p_y_in", 1980), st.session_state.get("p_m_in", 1), st.session_state.get("p_d_in", 1)
                
                _, _, m_d_pillar = engine.get_ganji_from_date(int(s_y), int(s_m), int(s_d))
                _, _, f_d_pillar = engine.get_ganji_from_date(int(p_y), int(p_m), int(p_d))
                m_db = m_d_pillar[1] if m_d_pillar else ""
                f_db = f_d_pillar[1] if f_d_pillar else ""
                
                m_n = st.session_state.get("name", "신랑")
                f_n = st.session_state.get("p_name_in", "신부")

                closing_html = html_views.get_closing_html(f"{m_n} 님 & {f_n}") if hasattr(html_views, 'get_closing_html') else ""
                closing_part = str(closing_html or "").strip()

                taegil_html = "<h3 style='color:#000000; margin-bottom:15px; text-align:center;'>💍 결혼 택일(길일) 정밀 감명 보고서</h3>"

                if date_mode == "기간 선택":
                    start_date = st.session_state.get("start_date_m", dt_mod.date.today())
                    end_date = st.session_state.get("end_date_m", dt_mod.date.today() + dt_mod.timedelta(days=90))
                    
                    taegil_html += f"<p style='color:#000000; font-weight:bold;'>💡 선택된 택일 탐색 구간: {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}<br>💡 분석 기준: 두 사람의 일지({m_db}, {f_db})와 상생하며 합(合)이 드는 최적의 길일을 스캔합니다.</p>"
                    
                    best_marriage_days = engine.get_optimized_delivery_days(start_date, end_date, [m_db], [f_db])

                    if not best_marriage_days:
                        taegil_html += "<p style='color:#D32F2F; font-weight:bold;'>⚠️ 지정하신 기간 내에 두 분의 기운과 합치하는 최적의 길일이 부족합니다. 기간을 넓혀 재조정해 주십시오.</p>"
                    else:
                        for idx, day_info in enumerate(best_marriage_days):
                            border_col = "#C62828" if idx == 0 else "#000000"
                            taegil_html += f"""
                            <div style='border-left: 5px solid {border_col}; padding: 15px; background-color: #f9f9f9; margin-bottom: 10px; border-radius: 5px;'>
                                <h4 style='margin-top:0; color: {border_col};'>🏅 추천 {idx+1}순위 결혼 길일 : {day_info['date']} (궁합 조화 점수: {day_info['score']:.1f}점)</h4>
                                <p style='margin-bottom:0;'>이 날은 두 사람의 사주간지와 조후가 안정적으로 맞물려 평화로운 가정을 이루기 좋은 길일입니다.</p>
                            </div>
                            """
                else:
                    target_date = st.session_state.get("target_date_m", dt_mod.date.today())
                    try:
                        _, _, target_d_pillar = engine.get_ganji_from_date(target_date.year, target_date.month, target_date.day)
                        target_ganji = f"{target_d_pillar[0]}{target_d_pillar[1]}" if target_d_pillar else "알 수 없음"
                    except:
                        target_ganji = "알 수 없음"

                    taegil_facts = {
                        "groom_ilju": m_db, 
                        "bride_ilju": f_db,
                        "groom_dw": "현재 대운 흐름",
                        "groom_sewun": "올해 세운",
                        "bride_dw": "현재 대운 흐름",
                        "bride_sewun": "올해 세운",
                        "selected_date": target_date.strftime('%Y년 %m월 %d일'),
                        "date_ganji": target_ganji,
                        "date_shinsal_str": "가내 평안과 상생의 길신 작용",
                        "date_interaction_str": "충형파해(沖刑破害) 없이 원만히 융합되는 흐름"
                    }
                    
                    class SafeDict(dict):
                        def __missing__(self, key): return "{" + key + "}"
                        
                    safe_facts = SafeDict(**taegil_facts)
                    prompt_text = prompts.WEDDING_DATE_PROMPT.format_map(safe_facts)
                    
                    ai_result = call_gemini_api(prompt_text)
                    
                    if ai_result:
                        clean_ai = re.sub(r'```[a-zA-Z]*', '', ai_result).replace("```", "").strip()
                        clean_ai = clean_ai.replace('[MALE_START]', '').replace('[MALE_END]', '').replace('[FEMALE_START]', '').replace('[FEMALE_END]', '').replace('[GUNGHAP_START]', '').replace('[GUNGHAP_END]', '').strip()
                        
                        formatted_ai = html_views.format_ai_text_to_html(clean_ai)
                        ai_output_html = f"<div style='text-align: left !important; line-height: 1.85;'>{formatted_ai}</div>"
                    else:
                        ai_output_html = '<p style="color:red;">⚠️ 특정일 택일 AI 정밀 분석 응답을 불러오지 못했습니다.</p>'

                    taegil_html += f"<h4 style='color:#000000; font-weight:bold; text-align:center;'>🎯 지정일: {target_date.strftime('%Y년 %m월 %d일')} [{target_ganji}일]</h4>"
                    taegil_html += f"""
                    <div style='padding: 20px; background-color: #F0F4F8; border-radius: 8px; border: 1px solid #D0DCE5; margin-top:15px;'>
                        {ai_output_html}
                    </div>
                    """

                taegil_html += closing_part
                clean_taegil_html = re.sub(r'>\s+<', '><', taegil_html.replace('\n', '')).strip()
                report_box = html_views.get_final_report_box(clean_taegil_html)
                st.markdown(report_box, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"🚨 결혼 택일 분석 중 오류 발생: {e}")

    elif "2-3." in u_product:
        if 'cached_gunghap_cover' in st.session_state:
            st.markdown(st.session_state['cached_gunghap_cover'], unsafe_allow_html=True)
        if 'cached_gunghap_report' in st.session_state:
            st.markdown(st.session_state['cached_gunghap_report'], unsafe_allow_html=True)

        run_delivery = st.session_state.get("run_delivery_calc", True)

        if run_delivery:
            st.markdown("---")
            with st.spinner("⏳ 신생아의 명조 분석 및 남/여 대운 흐름, 부모 인연을 심층 분석 중입니다..."):
                try:
                    start_date = st.session_state.get("delivery_start_date", dt_mod.date.today())
                    end_date = st.session_state.get("delivery_end_date", dt_mod.date.today() + dt_mod.timedelta(days=365))
                    last_period = st.session_state.get('last_period_date')
                    cycle = st.session_state.get('period_cycle', 30)
                    
                    s_y, s_m, s_d = st.session_state.get("s_y", 1980), st.session_state.get("s_m", 1), st.session_state.get("s_d", 1)
                    p_y, p_m, p_d = st.session_state.get("p_y_in", 1980), st.session_state.get("p_m_in", 1), st.session_state.get("p_d_in", 1)

                    _, _, m_d_pillar = engine.get_ganji_from_date(int(s_y), int(s_m), int(s_d))
                    _, _, f_d_pillar = engine.get_ganji_from_date(int(p_y), int(p_m), int(p_d))
                    m_db = m_d_pillar[1] if m_d_pillar else "알 수 없음"
                    f_db = f_d_pillar[1] if f_d_pillar else "알 수 없음"
                    m_jjis = [m_d_pillar[1]] if m_d_pillar else []
                    f_jjis = [f_d_pillar[1]] if f_d_pillar else []

                    m_n = st.session_state.get("name", "부")
                    f_n = st.session_state.get("p_name_in", "모")
                    closing_html = html_views.get_closing_html(f"{m_n} 님 & {f_n}") if hasattr(html_views, 'get_closing_html') else ""
                    closing_part = str(closing_html or "").strip()

                    best_days = engine.get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, last_period_date=last_period, period_cycle=cycle)

                    taegil_html = "<h3 style='color:#000000; margin-bottom:15px; text-align:center;'>👶 출산 택일(제왕절개/임신 계획) 정밀 분석 결과</h3>"
                    
                    if last_period:
                        taegil_html += f"<p style='color:#000000; font-weight:bold;'>💡 지정한 길일 탐색 구간: {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}<br>💡 참고 산모 정보: 마지막 생리일({last_period.strftime('%Y-%m-%d')}), 평균 주기({cycle}일)</p>"
                    else:
                        taegil_html += f"<p style='color:#000000; font-weight:bold;'>💡 지정한 길일 탐색 구간: {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}</p>"

                    if not best_days:
                        taegil_html += "<p style='color:#D32F2F; font-weight:bold;'>⚠️ 지정하신 탐색 기간 내에 오행이 조화로운 특A급 길일이 없습니다. 탐색 기간을 더 넓게 조정해 주십시오.</p>"
                    else:
                        if hasattr(html_views, 'get_delivery_summary_box'):
                            taegil_html += html_views.get_delivery_summary_box(best_days)

                        today_dt = dt_mod.date.today()
                        
                        for idx, day_info in enumerate(best_days):
                            border_col = "#C62828" if idx == 0 else "#000000"
                            b_time_info = day_info['best_time']
                            
                            b_date_str = day_info['date']
                            if isinstance(b_date_str, str):
                                y_s, m_s, d_s = map(int, b_date_str.split('-'))
                                b_dt = dt_mod.date(y_s, m_s, d_s)
                            else:
                                b_dt = b_date_str
                                b_date_str = b_dt.strftime("%Y-%m-%d")
                                
                            if last_period:
                                conception_start = last_period + dt_mod.timedelta(days=12)
                                conception_end = last_period + dt_mod.timedelta(days=16)
                                conception_title = "💖 실제 잉태(합궁) 추정 시기"
                                conception_msg = f"<span style='font-size:13px; color:#D32F2F; font-weight:bold;'>(※ 입력하신 마지막 생리일({last_period.strftime('%Y-%m-%d')})을 기준으로 산출된 실제 잉태 시기입니다.)</span>"
                            else:
                                conception_start = b_dt - dt_mod.timedelta(days=268)
                                conception_end = b_dt - dt_mod.timedelta(days=264)
                                conception_title = "💖 잉태(합궁) 권장 기간"
                                conception_msg = f"<span style='font-size:13px; color:#0277BD; font-weight:bold;'>(※ 계획 임신 시, 위 기간 내에 잉태해야 해당 길일에 출산할 확률이 높습니다.)</span>"

                            conception_str = f"{conception_start.strftime('%Y년 %m월 %d일')} ~ {conception_end.strftime('%Y년 %m월 %d일')}"

                            gestation_warning = ""
                            if last_period:
                                gestation_days = (b_dt - last_period).days
                                if gestation_days > 0:
                                    g_weeks = gestation_days // 7
                                    g_days = gestation_days % 7
                                    if 37 <= g_weeks <= 40:
                                        g_color, g_status = "#2E7D32", "정상 출산 주수"
                                    elif g_weeks < 37:
                                        g_color, g_status = "#C62828", "⚠️ 조산 위험 (주수 부족)"
                                    else:
                                        g_color, g_status = "#E65100", "⚠️ 출산 지연 (과숙아 위험)"
                                    gestation_warning = f"<li><b style='color:#673AB7;'>🩺 산모 생물학적 임신 주차</b>: <span style='font-weight:bold; color:{g_color};'>임신 {g_weeks}주 {g_days}일 ({g_status})</span> <br><span style='font-size:13px; color:#555;'>(※ 입력하신 생리일 기준이며, 의학적 소견과 교차 검증하시기 바랍니다.)</span></li>"

                            fake_gh = engine.get_gunghap_data(
                                b_dt.year, b_dt.month, b_dt.day, b_time_info['time_str'], "미혼",
                                b_dt.year, b_dt.month, b_dt.day, b_time_info['time_str'], "미혼",
                                "미혼-미혼"
                            )
                            b_table_data = fake_gh["m_table"]
                            b_master_list = fake_gh["m_master"]
                            
                            klc = KoreanLunarCalendar()
                            klc.setSolarDate(b_dt.year, b_dt.month, b_dt.day)
                            b_sol, b_lun = f"{b_dt.year}년 {b_dt.month}월 {b_dt.day}일", f"{klc.lunarYear}년 {klc.lunarMonth}월 {klc.lunarDay}일"
                            
                            baby_info = html_views.get_info_header("👶", f"신생아 (추천 {idx+1}순위)", "미정", "미혼", 1, b_sol, b_lun, b_time_info['time_str'], p_color="#00695C")
                            baby_table = html_views.get_gunghap_saju_table(*b_table_data[1:])
                            baby_master = html_views.get_master_bar(
                                b_master_list[0], b_master_list[1], b_master_list[2], b_master_list[3], b_master_list[4], 
                                b_master_list[5], b_master_list[6], b_master_list[7], b_master_list[8], b_master_list[9], b_master_list[10]
                            )
                            baby_saju_html = f"<div style='margin-top:15px;'>{baby_info}{baby_table}{baby_master}</div>"

                            try:
                                b_y_ganju = fake_gh.get("m_ys", "") + fake_gh.get("m_yb", "")
                                b_m_ganju = fake_gh.get("m_ms", "") + fake_gh.get("m_mb", "")
                                b_d_ganju = fake_gh.get("m_ds", "") + fake_gh.get("m_db", "")
                                b_h_ganju = fake_gh.get("m_hs", "") + fake_gh.get("m_hb", "")
                                baby_ganju_str = f"년주:{b_y_ganju}, 월주:{b_m_ganju}, 일주:{b_d_ganju}, 시주:{b_h_ganju}"
                                
                                taegil_facts = {
                                    "b_date_str": b_date_str,
                                    "b_time_str": b_time_info['time_str'],
                                    "baby_ganju": baby_ganju_str,
                                    "m_db": m_db, "f_db": f_db
                                }
                                
                                class SafeDict(dict):
                                    def __missing__(self, key): return "{" + key + "}"
                                    
                                safe_facts = SafeDict(**taegil_facts)
                                prompt_text = prompts.CHILDBIRTH_TAEGIL_PROMPT.format_map(safe_facts)
                                ai_result = call_gemini_api(prompt_text)
                                
                                if ai_result:
                                    clean_ai = re.sub(r'```[a-zA-Z]*', '', ai_result).replace("```", "").strip()
                                    formatted_ai = html_views.format_ai_text_to_html(clean_ai)
                                    ai_output_html = f"<div style='text-align: left !important; line-height: 1.85;'>{formatted_ai}</div>"
                                else:
                                    ai_output_html = '<p style="color:red;">⚠️ 출산 택일 AI 정밀 분석 응답을 불러오지 못했습니다.</p>'
                            except Exception as e:
                                ai_output_html = f'<p style="color:red;">⚠️ AI 분석 중 오류: {e}</p>'

                            taegil_html += html_views.get_childbirth_taegil_card(
                                border_col=border_col,
                                idx=idx,
                                b_date_str=b_date_str,
                                score=day_info['score'],
                                b_time_str=b_time_info['time_str'],
                                b_time_pillar=b_time_info['time_pillar'],
                                gestation_warning=gestation_warning,
                                conception_title=conception_title,
                                conception_str=conception_str,
                                conception_msg=conception_msg,
                                baby_saju_html=baby_saju_html,
                                ai_output_html=ai_output_html
                            )
                    
                    taegil_html += closing_part
                    clean_taegil_html = re.sub(r'>\s+<', '><', taegil_html.replace('\n', '')).strip()
                    report_box = html_views.get_final_report_box(clean_taegil_html)
                    st.markdown(report_box, unsafe_allow_html=True)
                            
                except Exception as e:
                    st.error(f"🚨 출산 택일 분석 중 오류 발생: {e}")
