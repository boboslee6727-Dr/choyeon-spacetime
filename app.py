import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import os
import re
from google import genai
import time
import engine
import prompts
import json
import math
import pytz
import html_views

# ==============================================================================
# 1. 초기 설정 및 공통 함수
# ==============================================================================
APP_VERSION = "ver 60.8"
st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# CSS 적용 (html_views에서 호출)
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
# 2. 사이드바 통제 센터 (ver 60.8)
# ==============================================================================
with st.sidebar:
    # [추가] 타이핑 시 원치 않는 AI 가동을 차단하는 제동 함수
    def stop_ai():
        st.session_state['app_running'] = False

    st.markdown(f"""<div style="text-align: center;"><h1 style="font-family: 'Nanum Gothic', sans-serif; color: #000000; font-weight: 900; font-size: 20px; margin-bottom: 5px;">🏮 초연 시공명리 연구소</h1></div>""", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #555555; font-family: sans-serif; font-size: 12px;'>{APP_VERSION} Master (Base + Gunghap)</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<div style='font-size: 17px; font-weight: 900; color: #000000; margin-bottom: 10px; font-family: \"Nanum Gothic\", sans-serif;'>📋 분석 상품 선택</div>", unsafe_allow_html=True)
    
    # [수정] 1단계: 대분류 선택 (on_change=stop_ai 유지)
    main_category = st.selectbox(
        "어떤 상담을 원하십니까?", 
        [
            "1. 사주팔자 및 운세 풀이", 
            "2. 연애/결혼운 (궁합) 풀이", 
            "3. 타 감명서 비교"
        ], 
        key="main_category", 
        on_change=stop_ai
    )

    st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)

    # [수정] 2단계: 중분류 선택 (선택된 값을 기존 u_product 변수에 담아 하위 로직과 완벽 호환)
    if main_category == "1. 사주팔자 및 운세 풀이":
        u_product = st.radio(
            "상세 분석 항목을 선택하십시오:",
            ["1-1. 사주팔자 및 대운 분석",
             "1-2. 올 해의 운세 상세 분석",
             "1-3. 이번 달의 운세 상세 분석",
             "1-4. 재물운 특화 분석",
             "1-5. 직업/진학운 특화 분석",
             "1-6. 건강운 특화 분석",
             "1-7. 이사 및 방위 특화 분석"], key="sub_category_1", on_change=stop_ai)

    elif main_category == "2. 연애/결혼운 (궁합) 풀이":
        u_product = st.radio(
            "상세 분석 항목을 선택하십시오:",
            ["2-0. 연애/결혼운 (궁합) 기본 풀이", 
             "2-1. 결혼 택일",
             "2-2. 출산 택일"], key="sub_category_2", on_change=stop_ai)

    elif main_category == "3. 타 감명서 비교":
        u_product = st.radio(
            "비교 분석 대상을 선택하십시오:",
            ["3-1. 타 감명서 비교 (사주)",
             "3-2. 타 감명서 비교 (궁합)" ], key="sub_category_3", on_change=stop_ai)
    st.markdown("---")

    # 성별 양방향 자동 동기화를 위한 콜백 함수
    if "u_g" not in st.session_state: st.session_state["u_g"] = "남성"
    if "f_g" not in st.session_state: st.session_state["f_g"] = "여성"

    def sync_partner_gender():
        if st.session_state["u_g"] == "여성":
            st.session_state["f_g"] = "남성"
        else:
            st.session_state["f_g"] = "여성"

    def sync_user_gender():
        if st.session_state["f_g"] == "남성":
            st.session_state["u_g"] = "여성"
        else:
            st.session_state["u_g"] = "남성"

    # ==============================================================================
    # 🔍 신청인 사주간지 역산 및 생년월일 자동입력
    # ==============================================================================
    with st.expander("🔍 신청인 사주간지 역산", expanded=False):
        col_g1, col_g2 = st.columns(2)
        with col_g1: ry = st.text_input("년주", value="", key="u_ry")
        with col_g2: rm = st.text_input("월주", value="", key="u_rm")
        col_g3, col_g4 = st.columns(2)
        with col_g3: rd = st.text_input("일주", value="", key="u_rd")
        with col_g4: rt = st.text_input("시주", value="", key="u_rt")
        
        if st.button("🔍 신청인 생년월일 자동입력", use_container_width=True, key="btn_user_rev"):
            _ry, _rm, _rd = extract_ganji(ry), extract_ganji(rm), extract_ganji(rd)
            if not _ry and not _rm and not _rd:
                if 'rev_success_msg' in st.session_state: del st.session_state['rev_success_msg']
                st.rerun()
            elif len(_ry)==2 and len(_rm)==2 and len(_rd)==2:
                ry_h = engine.K2H_GAN.get(_ry[0], _ry[0]) + engine.K2H_JI.get(_ry[1], _ry[1])
                rm_h = engine.K2H_GAN.get(_rm[0], _rm[0]) + engine.K2H_JI.get(_rm[1], _rm[1])
                rd_h = engine.K2H_GAN.get(_rd[0], _rd[0]) + engine.K2H_JI.get(_rd[1], _rd[1])
                klc_find = KoreanLunarCalendar(); found = False
                for y in range(2026, 1899, -1):
                    klc_find.setSolarDate(y, 7, 1); gj_y = klc_find.getChineseGapJaString().split()
                    if gj_y and gj_y[0][:2] == ry_h:
                        curr_dt = dt_mod.date(y+1, 2, 28)
                        while curr_dt >= dt_mod.date(y, 1, 1):
                            klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                            gj = klc_find.getChineseGapJaString().split()
                            if len(gj) >= 3 and gj[0][:2] == ry_h and gj[1][:2] == rm_h and gj[2][:2] == rd_h:
                                st.session_state['s_y'] = curr_dt.year
                                st.session_state['s_m'] = curr_dt.month
                                st.session_state['s_d'] = curr_dt.day
                                
                                if rt:
                                    ji_char = rt[-1]
                                    rt_h = engine.K2H_JI.get(ji_char, ji_char)
                                    time_map = {'자':'00:30 ~ 01:29 (朝子)시', '子':'00:30 ~ 01:29 (朝子)시', '축':'01:30 ~ 03:29 (丑)시', '丑':'01:30 ~ 03:29 (丑)시', '인':'03:30 ~ 05:29 (寅)시', '寅':'03:30 ~ 05:29 (寅)시', '묘':'05:30 ~ 07:29 (卯)시', '卯':'05:30 ~ 07:29 (卯)시', '진':'07:30 ~ 09:29 (辰)시', '辰':'07:30 ~ 09:29 (辰)시', '사':'09:30 ~ 11:29 (巳)시', '巳':'09:30 ~ 11:29 (巳)시', '오':'11:30 ~ 13:29 (午)시', '午':'11:30 ~ 13:29 (午)시', '미':'13:30 ~ 15:29 (未)시', '未':'13:30 ~ 15:29 (未)시', '신':'15:30 ~ 17:29 (申)시', '申':'15:30 ~ 17:29 (申)시', '유':'17:30 ~ 19:29 (酉)시', '酉':'17:30 ~ 19:29 (酉)시', '술':'19:30 ~ 21:29 (戌)시', '戌':'19:30 ~ 21:29 (戌)시', '해':'21:30 ~ 23:29 (亥)시', '亥':'21:30 ~ 23:29 (亥)시'}
                                    st.session_state['s_t'] = time_map.get(rt_h, "시간 모름")
                                else:
                                    st.session_state['s_t'] = "시간 모름"

                                found = True
                                st.session_state['rev_success_msg'] = f"✅ 자동입력 완료!"
                                st.rerun()
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                    if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

    # ==============================================================================
    # 🔍 신청인 정보 입력
    # ==============================================================================
    with st.expander("👤 신청인 기본 정보", expanded=True):
        name = st.text_input("이름", value="", placeholder="홍길동", key="u_n")
        gender = st.selectbox("성별", ["남성", "여성"], key="u_g", on_change=engine.update_partner_gender)
        u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
        u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")
        col_y, col_m, col_d = st.columns(3)
        with col_y: b_year = st.number_input("년도", 1900, 2050, value=1980, key="s_y")
        with col_m: b_month = st.number_input("월", 1, 12, value=1, key="s_m")
        with col_d: b_day = st.number_input("일", 1, 31, value=1, key="s_d")
        b_time = st.selectbox("태어난 시간", idx_list, key="s_t")

    # ==============================================================================
    # 📌 특화 상품별 추가 옵션 입력부 (안전성 강화 코드)
    # ==============================================================================
    # 1-1. 사주팔자 및 대운 분석 선택 시
    if "1-1." in u_product:
        run_iljin_calc = st.checkbox("🔮 일진 시공간 분석 추가 가동", value=False, key="sb_run_iljin")
        
    # 1-2 ~ 1-7. 3-1 중 특화 분석이 선택되었을 때만 입력창 활성화
    elif any(x in u_product for x in ["1-2.", "1-3.", "1-4.", "1-5.", "1-6.", "1-7.", "3-1."]):
        if "1-4." in u_product: 
            wealth_goal = st.text_input("고민되는 금전 문제는?", key="wealth_goal")
        elif "1-5." in u_product: 
            career_goal = st.text_input("고민되는 직업/진학 분야는?", key="career_goal")
        elif "1-6." in u_product: 
            health_goal = st.text_input("관리할 건강 부위는?", key="health_goal")
        elif "1-7." in u_product:
            moving_date = st.date_input("이사 희망일", key="moving_date")
            moving_dir = st.selectbox("이사 희망 방위", ["동쪽", "서쪽", "남쪽", "북쪽", "기타"], key="moving_dir")
        elif "3-1." in u_product:
            other_report = st.text_area("📄 타 감명서 원문 (사주) 붙여넣기", height=150, key=f"text_{u_product}")

    # 2. 궁합/결혼/출산/비교 (2-x, 3-2)
    elif any(x in u_product for x in ["2-", "3-2."]):
        
        # u_product 변수가 정의되지 않았을 경우를 대비해 안전하게 참조
        curr_prod = u_product if 'u_product' in locals() else ""
         
        # ==============================================================================
        # 👥 상대방(배우자/연인) 사주간지 역산 (원문 완벽 유지) ver 60.8 (구 버전)
        # ==============================================================================
        with st.expander("👥 상대방 사주간지 역산", expanded=False):
            p_col_g1, p_col_g2 = st.columns(2)
            with p_col_g1: p_ry = st.text_input("상대방 년주", key="p_ry")
            with p_col_g2: p_rm = st.text_input("상대방 월주", key="p_rm")
            p_col_g3, p_col_g4 = st.columns(2)
            with p_col_g3: p_rd = st.text_input("상대방 일주", key="p_rd")
            with p_col_g4: p_rt = st.text_input("상대방 시주", key="p_rt")
            
            if st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="btn_partner_rev"):
                _p_ry, _p_rm, _p_rd = extract_ganji(p_ry), extract_ganji(p_rm), extract_ganji(p_rd)
                
                # 들여쓰기 완벽 수정 완료
                if not _p_ry and not _p_rm and not _p_rd:
                    if 'rev_p_success_msg' in st.session_state: 
                        del st.session_state['rev_p_success_msg']
                    st.rerun()
                    
                elif len(_p_ry)==2 and len(_p_rm)==2 and len(_p_rd)==2:
                    p_ry_h = engine.K2H_GAN.get(_p_ry[0], _p_ry[0]) + engine.K2H_JI.get(_p_ry[1], _p_ry[1])
                    p_rm_h = engine.K2H_GAN.get(_p_rm[0], _p_rm[0]) + engine.K2H_JI.get(_p_rm[1], _p_rm[1])
                    p_rd_h = engine.K2H_GAN.get(_p_rd[0], _p_rd[0]) + engine.K2H_JI.get(_p_rd[1], _p_rd[1])
                    klc_find = KoreanLunarCalendar()
                    found = False
                    
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
                                        time_map = {'자':'00:30 ~ 01:29 (朝子)시', '子':'00:30 ~ 01:29 (朝子)시', '축':'01:30 ~ 03:29 (丑)시', '丑':'01:30 ~ 03:29 (丑)시', '인':'03:30 ~ 05:29 (寅)시', '寅':'03:30 ~ 05:29 (寅)시', '묘':'05:30 ~ 07:29 (卯)시', '卯':'05:30 ~ 07:29 (卯)시', '진':'07:30 ~ 09:29 (辰)시', '辰':'07:30 ~ 09:29 (辰)시', '사':'09:30 ~ 11:29 (巳)시', '巳':'09:30 ~ 11:29 (巳)시', '오':'11:30 ~ 13:29 (午)시', '午':'11:30 ~ 13:29 (午)시', '미':'13:30 ~ 15:29 (未)시', '未':'13:30 ~ 15:29 (未)시', '신':'15:30 ~ 17:29 (申)시', '申':'15:30 ~ 17:29 (申)시', '유':'17:30 ~ 19:29 (酉)시', '酉':'17:30 ~ 19:29 (酉)시', '술':'19:30 ~ 21:29 (戌)시', '戌':'19:30 ~ 21:29 (戌)시', '해':'21:30 ~ 23:29 (亥)시', '亥':'21:30 ~ 23:29 (亥)시'}
                                        st.session_state['p_t_key'] = time_map.get(p_rt_h, "시간 모름")
                                    else:
                                        st.session_state['p_t_key'] = "시간 모름"

                                    found = True
                                    st.session_state['rev_p_success_msg'] = f"✅ 상대방 자동입력 완료!"
                                    st.rerun()
                                    break
                                curr_dt -= dt_mod.timedelta(days=1)
                        if found: break
                    if not found: 
                        st.error("일치하는 날짜가 없습니다.")
                        
                else: 
                    st.warning("간지를 2글자씩 정확히 입력하세요.")

    # ==============================================================================
    # 👥 상대방(배우자/연인) 정보 입력 (2번 전체 또는 3-2. 선택 시 노출)
    # ==============================================================================
    if "2-" in u_product or "3-2." in u_product:
        with st.expander("👥 상대방 기본 정보", expanded=True):
            f_name = st.text_input("상대방 이름", value="", key="f_n")
            f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_g", on_change=engine.update_user_gender)
            f_marital = st.selectbox("상대방 혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="f_m_stat")
            f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c")
            p_col1, p_col2, p_col3 = st.columns(3)
            f_y = p_col1.number_input("년도(상대)", 1900, 2050, value=1980, key="p_y_in")
            f_m = p_col2.number_input("월(상대)", 1, 12, value=1, key="p_m_in")
            f_d = p_col3.number_input("일(상대)", 1, 31, value=1, key="p_d_in")
            f_t = st.selectbox("태어난 시간(상대)", idx_list, key="p_t_key")

    # ==============================================================================
    # 📌 특화 상품별 2-1, 2-2, 3-2 추가 옵션 입력부
    # ==============================================================================
    if "2-1." in u_product:
        date_mode = st.radio("결혼 택일 방식", ["기간 선택", "특정일 지정"], key="radio_marriage_mode")
        if date_mode == "기간 선택":
            # 화면을 깔끔하게 좌우로 나누어 시작일/종료일 배치
            col_start, col_end = st.columns(2)
            start_date = col_start.date_input("시작일", key="start_date_m")
            end_date = col_end.date_input("종료일", key="end_date_m")
            
    elif "2-2." in u_product:
        run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석", value=True, key="run_delivery_calc")

    elif "3-2." in u_product:
        other_report = st.text_area("📄 타 감명서 원문 (궁합) 붙여넣기", height=150, key="key_3_2")
        
    st.markdown("---")

    # ==============================================================================
    # 🚀 실행 및 인쇄 버튼
    # ==============================================================================
    if st.button("✨ [초연 시공명리 풀이 가동]", key="btn_run", use_container_width=True, type="primary"):
        st.session_state['app_running'] = True
        
    if st.button("🖨️ 풀이 결과 인쇄 / PDF 저장", key="btn_print", use_container_width=True):
        components.html("<script>window.parent.print();</script>", height=0)

# ==============================================================================
# 3. 메인 화면 출력부
# ==============================================================================
if st.session_state.get('app_running', False):
    # ---------------------------------------------------------
    # [1-1 ~ 1-7번 + 3-1번 상품 통합 블록] 
    # ---------------------------------------------------------
    if any(x in u_product for x in ["1-", "3-1."]): 
 
        # --- (A) 기본 사주 원국 및 대운 연산 ---
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

        with st.spinner(f"⏳ [{u_product.split('.')[1].strip()}] 정밀 분석 중...."):
            h, m = extract_time(b_time)
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
            
            guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
            guiin_str = guiin_map.get(engine.K2H_GAN.get(ds, ds), '없음')
            curr_y_ji = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'][(curr_year - 1984) % 12]
            
            n_gong = engine.calculate_gongmang(ys, yb) or "-"
            i_gong = engine.calculate_gongmang(ds, db) or "-"
            cur_samjae = engine.get_samjae(yb, curr_y_ji)
            samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"
            
            # --- (B) 공통 UI 렌더링 (원국, 마스터바) ---

            sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
            lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
            time_str_fmt = f"{b_time.split('(')[0].strip()}" if b_time != "시간 모름" else "시간 미상"
            
            ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                cells = "".join([f"<td style='color:{('#1A237E' if ci==r_idx else ('#000' if engine.get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else engine.get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

            gan_rel = "".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])
            gan_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, hs)}</td><td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(ds, ms)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, ys)}</td>"
            gan_row = "".join([td_bg(g)+f"{g}</td>" for g in gans])
            ji_row = "".join([td_bg(j)+f"{j}</td>" for j in jjis])
            ji_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, hb)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, db)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, mb)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, yb)}</td>"
            jijanggan = "".join([f"<td style='padding:0; border:1px solid #444;'>{engine.get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])
            unsung = "".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{engine.get_unsung(ds, jjis[i])}</td>" for i in range(4)])
            shinsal = "".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{engine.get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])
                        
            filtered_shinsals = ["<br>".join(engine.get_general_shinsal_filtered(i, gans, jjis, gender)[:6]) if engine.get_general_shinsal_filtered(i, gans, jjis, gender) else "-" for i in range(4)]
            gen_shinsal = "".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{filtered_shinsals[i]}</td>" for i in range(4)])

            cover_html = html_views.get_personal_cover(APP_VERSION, p_icon, name, sol_str_fmt, lun_str_fmt, time_str_fmt, today_str)
            info_h = html_views.get_info_header(p_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, time_str_fmt)
            
            table_html = html_views.get_saju_table(gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal)
            master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, samjae_color, cur_samjae)
            intro_html = html_views.get_intro_html()
            
            # --- (C) 대운/세운 기준점 연산 ---
            c_idx = engine.GAN.index(ms) if ms in engine.GAN else 0
            j_idx = engine.JI.index(mb) if mb in engine.JI else 0
            cur_dw_idx = max(0, (age - calc_d) // 10)
            dw_g_cur = engine.GAN[(c_idx + (cur_dw_idx+1)*order_dir)%10]
            dw_j_cur = engine.JI[(j_idx + (cur_dw_idx+1)*order_dir)%12]
            
            # [1. 공통 데이터 및 모든 표(대운/세운/월운) 일괄 준비] 

            # 대운표 생성
            daewun_data_list = engine.get_daeun_data_list(ms, mb, ds, yb, order_dir, calc_d, age)
            all_daewun_data = engine.get_daeun_fact_string(daewun_data_list)
            un_html = html_views.generate_daewun_layout(daewun_data_list, direction_str, calc_d, get_oh_class)

            try:
                current_daewun_age = max(0, int(cur_dw_idx) * 10 + int(calc_d))
                start_year = int(sol_y) + current_daewun_age - 1
            except:
                current_daewun_age = max(0, int(age))
                start_year = curr_year

            # 세운표 생성 (중복 제거 완료)
            se_content = ""
            for i in range(10):
                ty = start_year + i
                tage = current_daewun_age + i
                base = (ty - 1984) % 60
                tc_hangul, tj_hangul = engine.GAN[base % 10], engine.JI[base % 12]
                tc = engine.K2H_GAN.get(tc_hangul, tc_hangul)
                tj = engine.K2H_JI.get(tj_hangul, tj_hangul)
                bg_col = "#E1F5FE" if ty == curr_year else "transparent"
                b_left = "1px solid #ccc" if i != 0 else "none"
                se_content += html_views.get_sewun_cell(
                    f"{ty}년", tage, engine.get_ss(ds, tc_hangul), tc, get_oh_class(tc), 
                    tj, get_oh_class(tj), engine.get_ss(ds, tj_hangul), engine.get_unsung(ds, tj_hangul), engine.get_12_shinsal(yb, tj_hangul), bg_col, b_left
                )
            sewun_html = html_views.get_sewun_layout(f"[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]", se_content)
            
            # 월운표 생성
            wol_gans_kor = ["기", "경", "신", "임", "계", "갑", "을", "병", "정", "무", "기", "경"]
            wol_jis_kor = ["축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해", "자"]
            wol_content = ""
            for i in range(12):
                tm = i + 1
                wc_kor, wj_kor = wol_gans_kor[i], wol_jis_kor[i]
                wc, wj = engine.K2H_GAN.get(wc_kor, wc_kor), engine.K2H_JI.get(wj_kor, wj_kor)
                bg_col = "#E8F5E9" if tm == curr_m else "transparent"
                b_left = "1px solid #ccc" if i != 0 else "none" 
                wol_content += html_views.get_wolun_cell(
                    tm, engine.get_ss(ds, wc_kor) or "-", wc, get_oh_class(wc), 
                    wj, get_oh_class(wj), engine.get_ss(ds, wj_kor) or "-", engine.get_unsung(ds, wj_kor) or "-", engine.get_12_shinsal(yb, wj_kor) or "-", bg_col, b_left
                )
            wolun_html = html_views.get_wolun_layout(f"[ 월운의 흐름 ({curr_year}년도 양력기준) ]", wol_content)

            # 초연 시공명리 풀이 (골든 텍스트)
            choyeon_db = load_choyeon_db()
            w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{d_pillar[1]}".strip() 
            w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
            i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
            struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
            s_name, s_type, s_desc = struct_data[0], struct_data[1], struct_data[2]
            golden_text_html = html_views.get_golden_text(name, w_val, i_val, s_name, s_type, s_desc)

            closing_html = html_views.get_closing_html(name)            
            closing_part = str(closing_html or "")

            # ---------------------------------------------------------
            # [2. 통합 HTML 베이스 조립 (표지는 제외하고 묶음)]
            # ---------------------------------------------------------
            final_report_base = (
                str(info_h or "") + 
                str(table_html or "") + str(master_bar_html or "") + 
                str(un_html or "") + str(sewun_html or "") + str(wolun_html or "") + 
                str(intro_html or "") + str(golden_text_html or "")
            )

            # ---------------------------------------------------------
            # [3. 상품별 AI 통변 프롬프트 및 로직 분기]
            # ---------------------------------------------------------
            extra_facts = {}
            if "1-1." in u_product:
                target_prompt = getattr(prompts, 'PERSONAL_SAJU_PROMPT', "")
            elif "1-2." in u_product:
                target_prompt = getattr(prompts, 'SEWUN_PROMPT', "")
            elif "1-3." in u_product:
                target_prompt = getattr(prompts, 'WOLWUN_PROMPT', "")
            elif "1-4." in u_product:
                target_prompt = getattr(prompts, 'WEALTH_PROMPT', "")
            elif "1-5." in u_product:
                target_prompt = getattr(prompts, 'CAREER_PROMPT', "")
            elif "1-6." in u_product:
                target_prompt = getattr(prompts, 'HEALTH_PROMPT', "")
            elif "1-7." in u_product:
                target_prompt = getattr(prompts, 'MOVING_DIRECTION_PROMPT', "")
            elif "3-1." in u_product:
                target_prompt = getattr(prompts, 'PERSONAL_SAJU_PROMPT', "")
            else:
                target_prompt = getattr(prompts, 'PERSONAL_SAJU_PROMPT', "")

            # ---------------------------------------------------------
            # [4. AI 통변 (플래시 모델 전환 및 Safe Pipeline)]
            # ---------------------------------------------------------
            # 1. 변수 안전 초기화 (NameError 방지)
            ai_output_html = ""
            
            if True:  # 스피너 무력화 (들여쓰기 유지용 뼈대)
                pass  # 중복된 import re를 삭제하고 pass로 빈자리만 채움 (또는 # import re 로 주석처리)
                # ... (아래쪽 코드들은 단 1칸도 건드릴 필요 없이 그대로 둡니다!) ...
                
                # --- [A. 엔진 데이터 추출부] ---
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
                
                s12_str = engine.get_all_12_shinsal(yb, yb, mb, db, hb)
                shinsal_raw = engine.get_general_shinsal_filtered(1, gans, jjis, gender)
                shinsal_str = ", ".join([re.sub(r'<[^>]+>', '', s) for s in shinsal_raw]) if shinsal_raw else "특이 신살 없음"
                
                # --- [B. 프롬프트 데이터 통합 바인딩] ---
                # 1. 1-2(세운)를 위해 현재 세운의 천간/지지 변수를 안전하게 가져옵니다.
                try:
                    current_sewun_base = (curr_year - 1984) % 60
                    cur_sewun_gan = engine.GAN[current_sewun_base % 10]
                    cur_sewun_ji = engine.JI[current_sewun_base % 12]
                except:
                    cur_sewun_gan, cur_sewun_ji = "", ""

                # 2. 모든 프롬프트(1-1 ~ 1-7)가 요구할 수 있는 변수들을 하나의 사전에 몽땅 넣습니다.
                prompt_data = {
                    "name": name, "age": age, "gender": gender, "marital": u_marital,
                    "ys": ys, "yb": yb, "ms": ms, "mb": mb, "ds": ds, "db": db, "hs": hs, "hb": hb,
                    "gyukgook_detail": gyukgook_detail, "gongmang_actual": i_gong, "year_gongmang": n_gong,
                    "mok": counts['목'], "hwa": counts['화'], "to": counts['토'], "geum": counts['금'], "su": counts.get('수', counts.get('su', 0)),
                    "oheng_total": sum(counts.values()), "ss_unsung_str": ss_unsung_str, "won_guk_vaults_str": won_guk_vaults_str,
                    "hap_chung_hyoung_pa_hae": hap_chung_hyoung_pa_hae, "cheon_eul": guiin_str, "s12_str": s12_str, 
                    "shinsal_str": shinsal_str, "cur_samjae": cur_samjae,
                    # --- 아래는 1-2 (세운) 등에서 추가로 요구하는 변수들 ---
                    "curr_y": curr_year,
                    "sewun_gan": cur_sewun_gan,
                    "sewun_ji": cur_sewun_ji,
                    "dw_g_cur": dw_g_cur,
                    "dw_j_cur": dw_j_cur,
                    "sewun_fact_str": "올해의 흐름(사주 원국과 대운의 연계 작용)" # HTML(se_content)을 텍스트로 요약하는 변수가 없으므로 임시 대체
                }

                # 3. 안전한 포매팅 클래스 (프롬프트에 정의되지 않은 {}가 있어도 에러 방지)
                class SafeDict(dict):
                    def __missing__(self, key):
                        return '{' + key + '}'
                
                # target_prompt 하나만 포매팅하면 끝납니다!
                formatted_prompt = target_prompt.format_map(SafeDict(prompt_data))
                
                # --- [C. 플래시 모델 API 호출] ---
                # call_gemini_api 호출 시 플래시 모델 명시 (내부 구현에 맞게 파라미터 전달)
                try:
                    raw_response = call_gemini_api(formatted_prompt, extra_facts, model="gemini-2.5-flash")
                except TypeError:
                    # 함수가 model 인자를 직접 받지 않는 구조일 경우 기본 호출
                    raw_response = call_gemini_api(formatted_prompt, extra_facts)
                
                # --- [D. 텍스트 정제 및 문단 스타일링] ---
                if raw_response and isinstance(raw_response, str):
                    # 1. 마크다운 코드 블록 제거
                    cleaned = raw_response.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
                    
                    # 2. 상단 불필요 팩트 및 지시사항 텍스트 도려내기
                    cleaned = re.sub(r'(?s)1\.\s*신청자 기본 정보.*?2\.\s*사주 원국 정밀 분석 팩트.*?(?=1\.\s*성격 분석)', '', cleaned)
                    cleaned = re.sub(r'분석 지시 사항', '', cleaned)
                    
                    # 3. 제목 태그(###) 제거하고 텍스트 깔끔히 보정
                    cleaned = re.sub(r'###\s*', '', cleaned)
                    cleaned = re.sub(r'##\s*', '', cleaned)
                    
                    # 4. 줄바꿈을 문단 <p> 태그로 변환하여 뭉텅이 문장 해소 (들여쓰기 및 행간 적용)
                    paragraphs = [p.strip() for p in cleaned.split('\n') if p.strip()]
                    formatted_paragraphs = [
                        f"<p style='margin-bottom:16px; line-height:1.8; text-indent:10px; font-family:Nanum Myeongjo, serif; font-size:15px; color:#2c3e50;'>{p}</p>" 
                        for p in paragraphs
                    ]
                    ai_output_html = "".join(formatted_paragraphs)
                else:
                    ai_output_html = "<p style='padding:20px;'>분석 결과를 불러오지 못했습니다. 다시 시도해 주십시오.</p>"

            # ---------------------------------------------------------
            # [5. 최종 화면 렌더링 (1-1~1-7 / 3-1 완전 분리)]
            # ---------------------------------------------------------
            st.markdown(cover_html, unsafe_allow_html=True) 
            
            if "3-1." in u_product:
                try:
                    final_report = str(final_report_base or "") + str(ai_output_html or "") + str(closing_part or "")
                    comparison_saju_report = html_views.get_comparison_saju_cover_html(name, gender)
                    saju_report = str(comparison_saju_report or "") + final_report
                    st.markdown(html_views.get_final_report_box(saju_report), unsafe_allow_html=True)
                    
                    # 3-1 고유 1:1 비교 분석 렌더링
                    other_report = st.session_state.get("text_3-1.", "")
                    if other_report:
                        original_report_html = html_views.get_comparison_gumhap_report_html(name, gender, other_report)
                        with st.spinner("⚖️ 타 감명서 1:1 비교 분석 중..."):
                            fact_str = f"신청인 기운: {name}({gender}) 원국 및 대운/세운/월운"
                            comp_prompt = getattr(prompts, 'COMPARE_PROMPT', "").format(
                                full_content_clean=ai_output_html.replace("<div style='margin-top: 30px; padding: 20px; font-family: Nanum Myeongjo; line-height: 1.6;'>", "").replace("</div>", "").strip(),
                                other_report=other_report,
                                fact_reference=fact_str
                            )
                            comp_result = call_gemini_api(comp_prompt, model="gemini-2.5-flash")
                            
                            comp_clean = comp_result.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
                            comp_clean = re.sub(r'^(안녕하세요|반갑습니다|저는|AI).*?\n', '', comp_clean, flags=re.MULTILINE)
                            comp_fmt = re.sub(r'###\s*(.*?)\n', r"<div style='font-size:21px; font-weight:900; margin:20px 0 10px 0; color:#B71C1C;'>⚖️ \1</div>", comp_clean)
                            comp_fmt = comp_fmt.replace('\n', '<p style="margin:8px 0; line-height:1.6; font-family:Nanum Myeongjo;">')
                            comparison_output_html = html_views.get_comparison_html(comp_fmt)
                            
                        st.markdown("<br><br><hr style='border:1px dashed #ccc;'><br>", unsafe_allow_html=True)
                        comp_report = original_report_html + comparison_output_html
                        st.markdown(html_views.get_final_report_box(comp_report), unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ 타 감명서 원문이 입력되지 않았습니다.")
                except Exception as e:
                    st.error(f"🚨 [3-1. 타 감명서 비교] 처리 중 오류 발생: {e}")
            
            else:
                # 1-1 ~ 1-7 일반 상품 출력
                final_report = str(final_report_base or "") + str(ai_output_html or "") + str(closing_part or "")
                st.markdown(html_views.get_final_report_box(final_report), unsafe_allow_html=True)

    # ==============================================================================
    # [2번 카테고리] 연애/궁합 풀이 및 3-2. 타 감명서(궁합) 비교
    # ==============================================================================
    elif any(x in u_product for x in ["2-0.", "2-1", "2-2", "3-2."]):
        st.header(f"💕 {name} & {f_name} 초연 궁합")
        st.markdown("---")
        with st.spinner("⏳ 두 분의 시공간을 교차 분석 중입니다..."):
            try:
                # 1. 커버 데이터 계산 
                curr_y = dt_mod.datetime.now().year
                age = curr_y - int(b_year) + 1    # 신청인 나이
                p_age = curr_y - int(f_y) + 1     # 파트너 나이
                
                klc = KoreanLunarCalendar()
                klc.setSolarDate(int(b_year), int(b_month), int(b_day))
                m_sol, m_lun = f"{b_year}년 {b_month}월 {b_day}일", f"{klc.lunarYear}년 {klc.lunarMonth}월 {klc.lunarDay}일"
                klc.setSolarDate(int(f_y), int(f_m), int(f_d))
                f_sol, f_lun = f"{f_y}년 {f_m}월 {f_d}일", f"{klc.lunarYear}년 {klc.lunarMonth}월 {klc.lunarDay}일"
                
                if gender == "여성":
                    marital_status = f"{f_marital}-{u_marital}" 
                    gh_data = engine.get_gunghap_data(...)
                    # 💡 여기서 male_age에 p_age를, female_age에 age를 할당
                    male_name, male_age, male_sol, male_lun, male_time, male_marital = f_name, p_age, f_sol, f_lun, f_t, f_marital
                    female_name, female_age, female_sol, female_lun, female_time, female_marital = name, age, m_sol, m_lun, b_time, u_marital
                else:
                    marital_status = f"{u_marital}-{f_marital}" 
                    gh_data = engine.get_gunghap_data(
                        int(b_year), int(b_month), int(b_day), b_time, u_marital, 
                        int(f_y), int(f_m), int(f_d), f_t, f_marital,              
                        marital_status
                    )

                    # 💡 여기가 중요합니다! 변수 할당을 확실하게 넣어주십시오.
                    male_name, male_age, male_sol, male_lun, male_time, male_marital = name, age, m_sol, m_lun, b_time, u_marital
                    female_name, female_age, female_sol, female_lun, female_time, female_marital = f_name, p_age, f_sol, f_lun, f_t, f_marital

                m_data, m_master_list, m_daewun = gh_data["m_table"], gh_data["m_master"], gh_data["m_daewun"]
                f_data, f_master_list, f_daewun = gh_data["w_table"], gh_data["w_master"], gh_data["w_daewun"]

                # [정보 헤더 및 커버 생성]
                m_info = html_views.get_info_header("♂️", male_name, "남성", male_marital, male_age, male_sol, male_lun, f"{male_time}시", p_color="#1A237E")
                w_info = html_views.get_info_header("♀️", female_name, "여성", female_marital, female_age, female_sol, female_lun, f"{female_time}시", p_color="#2E7D32")
                
                cover_html = html_views.get_gunghap_cover(
                    APP_VERSION, 
                    male_name, male_age, male_sol, male_lun, f"{male_time}",  
                    female_name, female_age, female_sol, female_lun, f"{female_time}", 
                    dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
                )
                st.markdown(cover_html, unsafe_allow_html=True)
                
                # [본문 조립] 
                intro_h = html_views.get_intro_html() 
                closing = html_views.get_gunghap_closing(name, f_name)
                m_table = html_views.get_gunghap_saju_table(*m_data[1:])
                m_master_html = html_views.get_master_bar(m_master_list[0], m_master_list[1], m_master_list[2], m_master_list[3], m_master_list[4], m_master_list[5], m_master_list[6], m_master_list[7], m_master_list[8], m_master_list[9], m_master_list[10])
                m_un = html_views.generate_daewun_layout(*m_daewun)
                w_table = html_views.get_gunghap_saju_table(*f_data[1:])
                w_master_html = html_views.get_master_bar(f_master_list[0], f_master_list[1], f_master_list[2], f_master_list[3], f_master_list[4], f_master_list[5], f_master_list[6], f_master_list[7], f_master_list[8], f_master_list[9], f_master_list[10])
                w_un = html_views.generate_daewun_layout(*f_daewun)

                # ==========================================
                # [STEP 1] 초연 시공명리 궁합 풀이 (첫 번째 AI 호출)
                # ==========================================
                ai_output_html = ""
                clean_ai = "" 
                
                # 2. gunghap_facts는 기존 키(m_age, f_age)를 유지
                with st.spinner("⏳ 초연 시공명리 궁합 풀이 중..."):
                    gunghap_facts = {
                        "m_name": male_name, 
                        "m_age": male_age,  # 이 male_age 변수가 위에서 계산된 age/p_age를 담고 있음
                        "f_name": female_name, 
                        "f_age": female_age, # 이 female_age 변수가 위에서 계산된 age/p_age를 담고 있음
                        "marital_info": f"{u_marital}-{f_marital}"
                    }
                    gunghap_facts.update(gh_data)
                    
                    class SafeDict(dict):
                        def __missing__(self, key): return "{" + key + "}"

                    safe_gh_facts = SafeDict(**gunghap_facts)
                    prompt_text = prompts.GUNGHAP_ESSAY_PROMPT.format_map(safe_gh_facts)
                    prompt_text += "\n\n🚨 [경고] 남명과 여명의 데이터를 각각 독립적으로 분석하여 완벽히 차별화된 통변을 작성하십시오."
                    
                    ai_result = call_gemini_api(prompt_text)
                    
                    if ai_result:
                        clean_ai = ai_result.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
                        clean_ai = clean_ai.replace('[MALE_START]', '').replace('[MALE_END]', '').replace('[FEMALE_START]', '').replace('[FEMALE_END]', '').replace('[GUNGHAP_START]', '').replace('[GUNGHAP_END]', '').replace('[COUPLE_DAEWUN_TABLES_HERE]', '').strip()
                        
                        ai_result_fmt = re.sub(r'^(안녕하세요|반갑습니다|저는|AI).*?\n', '', clean_ai, flags=re.MULTILINE)
                        ai_result_fmt = re.sub(r'###\s*(.*?)\n', r"<div style='font-size:21px; font-weight:900; margin:20px 0 10px 0; color:#1A237E;'>\1</div>", ai_result_fmt)
                        ai_result_fmt = ai_result_fmt.replace('\n', '<p style="margin:8px 0; line-height:1.6; font-family:Nanum Myeongjo;">')
                        
                        # 스트림릿 버그 방지를 위해 들여쓰기 없이 밀착 배치
                        ai_output_html = f"<div style='margin-top: 30px; padding: 20px; font-family: Nanum Myeongjo; line-height: 1.6;'>{ai_result_fmt}</div>"

                # ==========================================
                # [STEP 2] 타 감명서 원문 및 1:1 비교 분석 준비
                # ==========================================
                original_report_html = ""
                comparison_output_html = ""
                
                if "3-2." in u_product:
                    other_report = st.session_state.get("key_3_2", "")
                    if other_report:
                        
                        # 💡 html_views에서 원문 박스 디자인을 우아하게 호출
                        original_report_html = html_views.get_original_report_html(other_report)
                        
                        with st.spinner("⏳ 타 감명서 1:1 비교 분석 중..."):
                            # 💡 1. 팩트 데이터를 문자열로 정리
                            fact_str = "\n".join([f"- {k}: {v}" for k, v in gunghap_facts.items()])
                            
                            # 💡 2. prompts.py의 공통 프롬프트를 스마트하게 호출
                            comp_prompt = prompts.COMPARE_PROMPT.format(
                                full_content_clean=clean_ai if clean_ai else "분석 내용 없음",
                                other_report=other_report,
                                fact_reference=fact_str
                            )
                            
                            comp_result = call_gemini_api(comp_prompt)
                            
                            if comp_result:
                                comp_clean = comp_result.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
                                comp_clean = re.sub(r'^(안녕하세요|반갑습니다|저는|AI).*?\n', '', comp_clean, flags=re.MULTILINE)
                                
                                comp_fmt = re.sub(r'###\s*(.*?)\n', r"<div style='font-size:21px; font-weight:900; margin:20px 0 10px 0; color:#B71C1C;'>⚖️ \1</div>", comp_clean)
                                comp_fmt = comp_fmt.replace('\n', '<p style="margin:8px 0; line-height:1.6; font-family:Nanum Myeongjo;">')
                                
                                # 💡 html_views에서 비교 분석 박스 디자인을 우아하게 호출
                                comparison_output_html = html_views.get_comparison_html(comp_fmt)
                    else:
                        st.warning("⚠️ 타 감명서 원문이 입력되지 않았습니다.")
                
                # ==========================================
                # [STEP 3] 최종 통합 출력 (전용 표지 매핑 완료)
                # ==========================================
                
                # 💡 단순 텍스트 대신, html_views에 생성한 전용 품격 표지로 매핑!
                comparison_gumhap_report = html_views.get_comparison_gunghap_cover_html(male_name, female_name)
                
                # 원본 데이터 구조 최상단에 전용 표지 결합
                gunghap_report = (
                    comparison_gumhap_report +
                    m_info + m_table + m_master_html + m_un + 
                    w_info + w_table + w_master_html + w_un + 
                    intro_h + 
                    ai_output_html +           
                    closing
                )
                
                # 1. 초연 궁합 풀이 메인 화면 출력
                report_box = html_views.get_final_report_box(gunghap_report)
                st.markdown(report_box, unsafe_allow_html=True)
                
                # 2. 비교 상품일 경우 구분선 처리 후 타 감명서 원문 및 비교 분석 출력
                if ("3-2." in u_product or "12." in u_product) and original_report_html:
                    st.markdown("<br><br><hr style='border:1px dashed #ccc;'><br>", unsafe_allow_html=True)
                    
                    # html_views에서 정의한 함수 호출 및 결합
                    original_report_html = html_views.get_comparison_gumhap_report_html(male_name, female_name, other_report)
                    comp_report = original_report_html + comparison_output_html
                    comp_box = html_views.get_final_report_box(comp_report)
                    st.markdown(comp_box, unsafe_allow_html=True)
            
            except Exception as e:
                st.error(f"🚨 궁합 분석 중 오류가 발생했습니다: {e}")
                
    # ==============================================================================
    # [2번 카테고리 특화] 결혼 / 출산 택일
    # ==============================================================================
    elif any(x in u_product for x in ["2-1.", "2-2."]):
        # 💡 택일 파트도 별도의 try문으로 독립시켜야 안전합니다.
        try:
            title_str = u_product.split('.')[1].strip() if "." in u_product else u_product
            st.header(f"🗓️ {name}님의 {title_str}")
            st.markdown("---")
            with st.spinner("⏳ 길일 및 시공간 분석 중..."):
                st.info("명리학적 택일 분석 엔진 가동 대기 중입니다.")
        
        except Exception as e:
            st.error(f"🚨 택일 분석 중 오류가 발생했습니다: {e}")
