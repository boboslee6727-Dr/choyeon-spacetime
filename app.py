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
APP_VERSION = "ver 60.9"
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
# 2. 사이드바 통제 센터 (최종 정밀 수색 및 버그 완벽 차단 버전) ver 60.9 - 무결점 원상복구
# ==============================================================================
with st.sidebar:
    def stop_ai():
        st.session_state['app_running'] = False

    st.markdown(f"""<div style="text-align: center;"><h1 style="font-family: 'Nanum Gothic', sans-serif; color: #000000; font-weight: 900; font-size: 20px; margin-bottom: 5px;">🏮 초연 시공명리 연구소</h1></div>""", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #555555; font-family: sans-serif; font-size: 12px;'>{APP_VERSION} Master (Base + Gunghap)</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<div style='font-size: 17px; font-weight: 900; color: #000000; margin-bottom: 10px; font-family: \"Nanum Gothic\", sans-serif;'>📋 분석 상품 선택</div>", unsafe_allow_html=True)
    
    main_category = st.selectbox("어떤 상담을 원하십니까?", ["1. 사주팔자 및 운세 풀이", "2. 연애/결혼운 (궁합) 풀이", "3. 타 감명서 비교"], key="main_category", on_change=stop_ai)

    if main_category == "1. 사주팔자 및 운세 풀이":
        u_product = st.radio("상세 분석 항목:", ["1-1. 사주팔자 및 대운 분석", "1-2. 올 해의 운세 상세 분석", "1-3. 이번 달의 운세 상세 분석", "1-4. 재물운 특화 분석", "1-5. 직업/진학운 특화 분석", "1-6. 건강운 특화 분석", "1-7. 이사 및 방위 특화 분석"], key="sub_category_1", on_change=stop_ai)
    elif main_category == "2. 연애/결혼운 (궁합) 풀이":
        u_product = st.radio("상세 분석 항목:", ["2-0. 연애/결혼운 (궁합) 기본 풀이", "2-1. 결혼 택일", "2-2. 출산 택일"], key="sub_category_2", on_change=stop_ai)
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
    # 🔍 신청인 사주간지 역산
    # ==============================================================================
    with st.expander("🔍 신청인 사주간지 역산", expanded=False):
        col_g1, col_g2 = st.columns(2)
        with col_g1: st.text_input("년주", value="", key="u_ry_rev")
        with col_g2: st.text_input("월주", value="", key="u_rm_rev")
        col_g3, col_g4 = st.columns(2)
        with col_g3: st.text_input("일주", value="", key="u_rd_rev")
        with col_g4: st.text_input("시주", value="", key="u_rt_rev")
        
        # engine.py 로직 호출
        st.button("🔍 신청인 생년월일 자동입력", use_container_width=True, key="btn_user_rev", on_click=getattr(engine, 'auto_fill_user_ganji', None))
        
        if 'rev_success_msg' in st.session_state:
            st.success(st.session_state['rev_success_msg'])
            del st.session_state['rev_success_msg']
        if 'rev_error_msg' in st.session_state:
            st.error(st.session_state['rev_error_msg'])
            del st.session_state['rev_error_msg']

    # ==============================================================================
    # 👤 신청인 기본 정보
    # ==============================================================================
    if "s_y" not in st.session_state: st.session_state["s_y"] = 1980
    if "s_m" not in st.session_state: st.session_state["s_m"] = 1
    if "s_d" not in st.session_state: st.session_state["s_d"] = 1
    if "s_t" not in st.session_state: st.session_state["s_t"] = idx_list[0] if 'idx_list' in locals() or 'idx_list' in globals() else "시간 모름"

    with st.expander("👤 신청인 기본 정보", expanded=True):
        name = st.text_input("이름", value="", placeholder="홍길동", key="u_n")
        gender = st.selectbox("성별", ["남성", "여성"], key="u_g", on_change=sync_partner_gender)
        u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
        u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")
        col_y, col_m, col_d = st.columns(3)
        b_year = col_y.number_input("년도", 1900, 2050, key="s_y")
        b_month = col_m.number_input("월", 1, 12, key="s_m")
        b_day = col_d.number_input("일", 1, 31, key="s_d")
        b_time = st.selectbox("태어난 시간", idx_list, key="s_t")
    st.markdown("</div>", unsafe_allow_html=True)

    # ==============================================================================
    # 📌 특화 상품별 추가 옵션 입력부
    # ==============================================================================
    if "1-1." in u_product:
        run_iljin_calc = st.checkbox("🔮 일진 시공간 분석 추가 가동", value=False, key="sb_run_iljin")
        
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

    # ==============================================================================
    # 👥 상대방 사주간지 역산 & 기본 정보 (무한루프 완전 소멸 버전)
    # ==============================================================================
    elif any(x in u_product for x in ["2-", "3-2."]):
        with st.expander("👥 상대방 사주간지 역산", expanded=False):
            p_col_g1, p_col_g2 = st.columns(2)
            with p_col_g1: st.text_input("상대방 년주", key="p_ry_rev")
            with p_col_g2: st.text_input("상대방 월주", key="p_rm_rev")
            p_col_g3, p_col_g4 = st.columns(2)
            with p_col_g3: st.text_input("상대방 일주", key="p_rd_rev")
            with p_col_g4: st.text_input("상대방 시주", key="p_rt_rev")
            
            # engine.py의 자립형 콜백 함수 안전 호출
            st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="btn_partner_rev", on_click=getattr(engine, 'auto_fill_partner_ganji', None))
            
            if 'rev_p_success_msg' in st.session_state:
                st.success(st.session_state['rev_p_success_msg'])
                del st.session_state['rev_p_success_msg']
            if 'rev_p_error_msg' in st.session_state:
                st.error(st.session_state['rev_p_error_msg'])
                del st.session_state['rev_p_error_msg']

        # ==============================================================================
        # 👥 상대방 기본 정보 (value 매개변수를 완전히 지워 무한루프 충돌 원천 차단)
        # ==============================================================================
        if 'p_y_in' not in st.session_state: st.session_state['p_y_in'] = 1980
        if 'p_m_in' not in st.session_state: st.session_state['p_m_in'] = 1
        if 'p_d_in' not in st.session_state: st.session_state['p_d_in'] = 1
        if 'p_t_key' not in st.session_state: st.session_state['p_t_key'] = idx_list[0] if 'idx_list' in locals() or 'idx_list' in globals() else "시간 모름"

        with st.expander("👥 상대방 기본 정보", expanded=True):
            f_name = st.text_input("상대방 이름", value="", key="f_n")
            f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_g", on_change=sync_user_gender)
            f_marital = st.selectbox("상대방 혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="f_m_stat")
            f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c")
            p_col1, p_col2, p_col3 = st.columns(3)
            # 💡 value=p_def_y 등을 제거하여 Streamlit 엔진의 무한 Rerun을 차단합니다.
            f_y = p_col1.number_input("년도(상대)", 1900, 2050, key="p_y_in")
            f_m = p_col2.number_input("월(상대)", 1, 12, key="p_m_in")
            f_d = p_col3.number_input("일(상대)", 1, 31, key="p_d_in")
            f_t = st.selectbox("태어난 시간(상대)", idx_list, key="p_t_key")
        st.markdown("</div>", unsafe_allow_html=True)
        
    # ==============================================================================
    # 📌 궁합(2-1, 2-2) 및 타 감명서(3-2) 특화 옵션 입력부
    # ==============================================================================
    if "2-1." in u_product:
        date_mode = st.radio("결혼 택일 방식", ["기간 선택", "특정일 지정"], key="radio_marriage_mode")
        if date_mode == "기간 선택":
            col_start, col_end = st.columns(2)
            start_date = col_start.date_input("시작일", key="start_date_m")
            end_date = col_end.date_input("종료일", key="end_date_m")
        else:
            target_date = st.date_input("결혼 예정일 선택", key="target_date_m")
            
    elif "2-2." in u_product:
        run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석 가동", value=True, key="run_delivery_calc")
        
        st.markdown("<p style='font-size:14px; font-weight:bold; margin-bottom:0px;'>📅 길일 탐색 기간 설정</p>", unsafe_allow_html=True)
        col_d1, col_d2 = st.columns(2)
        delivery_start_date = col_d1.date_input("탐색 시작일", key="delivery_start_date")
        delivery_end_date = col_d2.date_input("탐색 종료일", key="delivery_end_date")

        last_period_date = st.date_input("마지막 생리 시작일", key="last_period_date")
        period_cycle = st.number_input("평균 생리 주기 (일)", min_value=20, max_value=45, value=28, key="period_cycle")

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
                # 💡 [추가] 월운 전용 지시사항 강제 주입 (원국/대운 중복 설명 완전 차단)
                target_prompt += "\n\n[🚨 극비 강제 지시사항: 사주 원국, 대운, 세운에 대한 기본 설명이나 도입부는 완전히 생략하고, 즉시 이번 달(월운)의 핵심 흐름과 인과관계, 행동 지침만 집중적으로 출력하라.]"
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
                
                s12_str = engine.get_all_12_shinsal(yb, mb, db, hb)
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

                # 현재 월운의 천간과 지지 추출 (엔진 내 함수 사용)
                try:
                    # 엔진 내 월운 구하는 함수 호출 (또는 cur_wol_g, cur_wol_j 변수 생성)
                    cur_wol_g, cur_wol_j = engine.get_current_wolun_gan_ji() 
                except Exception:
                    # 혹시 함수명이 다를 경우를 대비한 안전 장치 (기본값 설정)
                    cur_wol_g = getattr(engine, 'cur_wol_g', '')
                    cur_wol_j = getattr(engine, 'cur_wol_j', '')

                # --- [프로모델 캡처 로직: Streamlit 변수 증발 원천 차단] ---
                # 호출 시점의 지역(locals) 및 전역(globals) 스코프를 미리 확보
                _current_locals = locals()
                _current_globals = globals()
                
                def get_val(*keys):
                    """세션 상태, 지역 변수, 전역 변수를 교차 검증하여 유효한 첫 번째 값을 반환합니다."""
                    for k in keys:
                        # 1. session_state 확인 (가장 확실한 Streamlit 데이터 보관소)
                        if 'st' in _current_globals and hasattr(_current_globals['st'], 'session_state'):
                            if k in _current_globals['st'].session_state and _current_globals['st'].session_state[k]:
                                v = str(_current_globals['st'].session_state[k]).strip()
                                if v: return v
                        # 2. 현재 지역 및 전역 스코프 확인
                        if k in _current_locals and _current_locals[k]:
                            v = str(_current_locals[k]).strip()
                            if v: return v
                        if k in _current_globals and _current_globals[k]:
                            v = str(_current_globals[k]).strip()
                            if v: return v
                    return None

                # 헬퍼 함수를 통해 텍스트 최우선 추출 (없을 경우에만 디폴트값 적용)
                career_val = get_val('u_career_issue', 'u_job', 'user_query', 'u_question') or "특별히 제시된 고민 내용 없음"
                wealth_val = get_val('u_wealth_issue', 'u_wealth_goal', 'u_money_issue') or "특별히 제시된 고민 내용 없음"
                health_val = get_val('u_health_goal') or "전반적인 건강 체질 관리"
                question_val = get_val('u_question') or "특별히 제시된 질문 없음"

                prompt_data = {
                    "name": name, "age": age, "gender": gender, "marital": u_marital,
                    "ys": ys, "yb": yb, "ms": ms, "mb": mb, "ds": ds, "db": db, "hs": hs, "hb": hb,
                    "gyukgook_detail": gyukgook_detail, "gongmang_actual": i_gong, "year_gongmang": n_gong,
                    "mok": counts['목'], "hwa": counts['화'], "to": counts['토'], "geum": counts['금'], "su": counts.get('수', counts.get('su', 0)),
                    "oheng_total": sum(counts.values()), "ss_unsung_str": ss_unsung_str, "won_guk_vaults_str": won_guk_vaults_str,
                    "hap_chung_hyoung_pa_hae": hap_chung_hyoung_pa_hae, "cheon_eul": guiin_str, "s12_str": s12_str, 
                    "shinsal_str": shinsal_str, "cur_samjae": cur_samjae,
                    # --- [상위 환경: 대운/세운/월운 변수] ---
                    "curr_y": curr_year,
                    "sewun_gan": cur_sewun_gan,
                    "sewun_ji": cur_sewun_ji,
                    "dw_g_cur": dw_g_cur,
                    "dw_j_cur": dw_j_cur,
                    "cur_wol_g": cur_wol_g,
                    "cur_wol_j": cur_wol_j,
                    "sewun_fact_str": "올해의 흐름(사주 원국과 대운의 연계 작용)",
                    
                    # --- [건강/직업/재물 팩트 변수] ---
                    "ohang_balance_str": ohang_balance_str if 'ohang_balance_str' in _current_locals else f"목:{counts['목']}, 화:{counts['화']}, 토:{counts['토']}, 금:{counts['금']}, 수:{counts.get('수', 0)}",
                    "weak_health_str": weak_health_str if 'weak_health_str' in _current_locals else "취약 장기 및 신체 부위 분석 팩트",
                    "health_goal": health_val,
                    "jaeseong_str": jaeseong_str if 'jaeseong_str' in _current_locals else "재성 세력 분석 팩트",
                    "wealth_fact_str": wealth_fact_str if 'wealth_fact_str' in _current_locals else "금전 흐름 체용 매트릭스",
                    "career_fact_str": career_fact_str if 'career_fact_str' in _current_locals else "직업/진학 핵심 십성 분석",
                    
                    # --- [실제 입력 텍스트 바인딩 (철통 방어)] ---
                    "user_query": career_val,
                    "wealth_issue": wealth_val,
                    "u_question": question_val
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
                # 1-1 ~ 1-7 모든 일반 상품 (1-3 월운 포함): 기존 A4 박스 구조 100% 통출력
                final_report = str(final_report_base or "") + str(ai_output_html or "") + str(closing_part or "")
                st.markdown(html_views.get_final_report_box(final_report), unsafe_allow_html=True)

    # ==============================================================================
    # [2번 카테고리] 연애/궁합 풀이
    # ==============================================================================
    elif any(x in u_product for x in ["2-0", "궁합", "3-2"]) and not any(x in u_product for x in ["2-1.", "2-2."]):
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

                m_info = html_views.get_info_header("♂️", male_name, "남성", male_marital, male_age, male_sol, male_lun, f"{male_time}시", p_color="#1A237E")
                w_info = html_views.get_info_header("♀️", female_name, "여성", female_marital, female_age, female_sol, female_lun, f"{female_time}시", p_color="#2E7D32")
                
                cover_html = html_views.get_gunghap_cover(
                    APP_VERSION, male_name, male_age, male_sol, male_lun, f"{male_time}",  
                    female_name, female_age, female_sol, female_lun, f"{female_time}", 
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
                
                # 시각화 엔진 가동
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

                # AI 통변 호출
                ai_result = call_gemini_api(prompt_text)
                
                if ai_result:
                    clean_ai = re.sub(r'```[a-zA-Z]*', '', ai_result).replace("```", "").strip()
                    clean_ai = clean_ai.replace('[MALE_START]', '').replace('[MALE_END]', '').replace('[FEMALE_START]', '').replace('[FEMALE_END]', '').replace('[GUNGHAP_START]', '').replace('[GUNGHAP_END]', '').strip()
                    
                    couple_daewun_tables = html_views.get_couple_daewun_tables(gh_data) if hasattr(html_views, 'get_couple_daewun_tables') else ""
                    if '[COUPLE_DAEWUN_TABLES_HERE]' in clean_ai:
                        clean_ai = clean_ai.replace('[COUPLE_DAEWUN_TABLES_HERE]', couple_daewun_tables)
                    
                    # 마크다운 제목 치환 (들여쓰기 제거)
                    clean_ai = re.sub(r'###\s*(.*?)\n', r'<h3 style="color:#1A237E; font-size:20px; font-weight:bold; margin-top:25px; margin-bottom:10px;">\1</h3>', clean_ai)
                    clean_ai = re.sub(r'##\s*(.*?)\n', r'<h2 style="color:#0D47A1; font-size:22px; font-weight:bold; margin-top:30px; margin-bottom:15px; border-bottom:1px solid #ddd;">\1</h2>', clean_ai)
                    
                    # 라인별 안전 P 태그 포장 (들여쓰기 없는 단일 라인)
                    formatted_lines = []
                    for line in clean_ai.split('\n'):
                        line_str = line.strip()
                        if line_str:
                            if line_str.startswith('<h') or line_str.startswith('<div') or line_str.startswith('<table'):
                                formatted_lines.append(line_str)
                            else:
                                formatted_lines.append(f'<p style="margin:10px 0; line-height:1.8; font-family:\'Nanum Myeongjo\', serif; font-size:16px; color:#333;">{line_str}</p>')
                    
                    ai_output_html = "".join(formatted_lines)
                else:
                    ai_output_html = '<p style="color:red;">⚠️ 궁합 AI 통변 데이터를 생성하지 못했습니다.</p>'

                # html_views 함수 호출
                score_visual_html = html_views.get_gunghap_score_visual_html(gh_engine)

                # AI 통변 박스 감싸기 (공백/들여쓰기 차단)
                ai_box_html = f'<div style="margin-top:20px; padding:20px; background-color:#ffffff; border-radius:10px; border:1px solid #E0E0E0;">{ai_output_html}</div>'

                # 파이썬 들여쓰기 공백이 유입되지 않도록 join 결합
                full_inner_content = "".join([
                    str(m_info or ''), str(m_table or ''), str(m_master_html or ''), str(m_un or ''), str(m_golden_html or ''),
                    str(w_info or ''), str(w_table or ''), str(w_master_html or ''), str(w_un or ''), str(f_golden_html or ''),
                    str(intro_h or ''),
                    str(ai_box_html or ''),
                    str(score_visual_html or '')
                ])
                
                # [수정계획안] HTML 태그 사이의 들여쓰기 공백/줄바꿈을 정제하여 코드블록 노출 현상 완전 차단
                clean_full_inner = re.sub(r'>\s+<', '><', full_inner_content.replace('\n', '')).strip()
                report_box = html_views.get_final_report_box(clean_full_inner)
                
                st.session_state['cached_gunghap_cover'] = cover_html
                st.session_state['cached_gunghap_report'] = report_box
                
                st.markdown(cover_html, unsafe_allow_html=True)
                st.markdown(report_box, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"🚨 궁합 분석 처리 중 예외 발생: {e}")

    # ==============================================================================
    # 💍 [2-1번 카테고리] 결혼 택일 복원 (고품격 AI 통변 및 A4 테두리 박스 적용)
    # ==============================================================================
    elif "2-1." in u_product:
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

                taegil_html = "<h3 style='color:#1A237E; margin-bottom:15px; text-align:center;'>💍 결혼 택일(길일) 정밀 감명 보고서</h3>"

                if date_mode == "기간 선택":
                    start_date = st.session_state.get("start_date_m", dt_mod.date.today())
                    end_date = st.session_state.get("end_date_m", dt_mod.date.today() + dt_mod.timedelta(days=90))
                    
                    taegil_html += f"<p style='color:#0277BD; font-weight:bold;'>💡 선택된 택일 탐색 구간: {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}<br>💡 분석 기준: 두 사람의 일지({m_db}, {f_db})와 상생하며 합(合)이 드는 최적의 길일을 스캔합니다.</p>"
                    
                    best_marriage_days = engine.get_optimized_delivery_days(start_date, end_date, [m_db], [f_db])

                    if not best_marriage_days:
                        taegil_html += "<p style='color:#D32F2F; font-weight:bold;'>⚠️ 지정하신 기간 내에 두 분의 기운과 합치하는 최적의 길일이 부족합니다. 기간을 넓혀 재조정해 주십시오.</p>"
                    else:
                        for idx, day_info in enumerate(best_marriage_days):
                            border_col = "#C62828" if idx == 0 else "#1A237E"
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

                    # 💡 프롬프트 변수명(WEDDING_DATE_PROMPT) 및 팩트 시트 매핑 완벽 수정
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
                    
                    # KeyError 방지용 안전 딕셔너리
                    class SafeDict(dict):
                        def __missing__(self, key): return "{" + key + "}"
                        
                    safe_facts = SafeDict(**taegil_facts)
                    prompt_text = prompts.WEDDING_DATE_PROMPT.format_map(safe_facts)
                    ai_result = call_gemini_api(prompt_text)
                    
                    if ai_result:
                        clean_ai = re.sub(r'```[a-zA-Z]*', '', ai_result).replace("```", "").strip()
                        clean_ai = re.sub(r'###\s*(.*?)\n', r'<h3 style="color:#1A237E; font-size:18px; font-weight:bold; margin-top:20px; margin-bottom:10px;">\1</h3>', clean_ai)
                        clean_ai = re.sub(r'##\s*(.*?)\n', r'<h2 style="color:#0D47A1; font-size:20px; font-weight:bold; margin-top:25px; margin-bottom:12px; border-bottom:1px solid #ddd;">\1</h2>', clean_ai)
                        
                        formatted_lines = []
                        for line in clean_ai.split('\n'):
                            line_str = line.strip()
                            if line_str:
                                if line_str.startswith('<h') or line_str.startswith('<div'):
                                    formatted_lines.append(line_str)
                                else:
                                    formatted_lines.append(f'<p style="margin:10px 0; line-height:1.8; font-family:\'Nanum Myeongjo\', serif; font-size:16px; color:#333;">{line_str}</p>')
                        ai_output_html = "".join(formatted_lines)
                    else:
                        ai_output_html = '<p style="color:red;">⚠️ 특정일 택일 AI 정밀 분석 응답을 불러오지 못했습니다.</p>'

                    taegil_html += f"<h4 style='color:#2E7D32; font-weight:bold; text-align:center;'>🎯 지정일: {target_date.strftime('%Y년 %m월 %d일')} [{target_ganji}일]</h4>"
                    taegil_html += f"""
                    <div style='padding: 20px; background-color: #F0F4F8; border-radius: 8px; border: 1px solid #D0DCE5; margin-top:15px;'>
                        {ai_output_html}
                    </div>
                    """

                # 💡 수집된 결과를 A4 테두리 박스로 포장하여 최종 출력
                clean_taegil_html = re.sub(r'>\s+<', '><', taegil_html.replace('\n', '')).strip()
                report_box = html_views.get_final_report_box(clean_taegil_html)
                st.markdown(report_box, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"🚨 결혼 택일 분석 중 오류 발생: {e}")

    # ==============================================================================
    # 👶 [2-2번 카테고리] 출산 택일 (신생아 사주 + 남녀 대운 분석 + 부모 인연)
    # ==============================================================================
    elif "2-2." in u_product:
        if 'cached_gunghap_cover' in st.session_state:
            st.markdown(st.session_state['cached_gunghap_cover'], unsafe_allow_html=True)
        if 'cached_gunghap_report' in st.session_state:
            st.markdown(st.session_state['cached_gunghap_report'], unsafe_allow_html=True)

        st.markdown("---")
        with st.spinner("⏳ 신생아의 명조 분석 및 남/여 대운 흐름, 부모 인연을 심층 분석 중입니다..."):
            try:
                start_date = st.session_state.get("delivery_start_date", dt_mod.date.today())
                end_date = st.session_state.get("delivery_end_date", dt_mod.date.today() + dt_mod.timedelta(days=30))
                last_period = st.session_state.get('last_period_date')
                cycle = st.session_state.get('period_cycle', 28)
                
                s_y, s_m, s_d = st.session_state.get("s_y", 1980), st.session_state.get("s_m", 1), st.session_state.get("s_d", 1)
                p_y, p_m, p_d = st.session_state.get("p_y_in", 1980), st.session_state.get("p_m_in", 1), st.session_state.get("p_d_in", 1)

                _, _, m_d_pillar = engine.get_ganji_from_date(int(s_y), int(s_m), int(s_d))
                _, _, f_d_pillar = engine.get_ganji_from_date(int(p_y), int(p_m), int(p_d))
                m_db = m_d_pillar[1] if m_d_pillar else "알 수 없음"
                f_db = f_d_pillar[1] if f_d_pillar else "알 수 없음"
                m_jjis = [m_d_pillar[1]] if m_d_pillar else []
                f_jjis = [f_d_pillar[1]] if f_d_pillar else []

                best_days = engine.get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis)

                taegil_html = "<h3 style='color:#1A237E; margin-bottom:15px; text-align:center;'>👶 출산 택일(제왕절개/임신 계획) 정밀 분석 결과</h3>"
                
                if last_period:
                    taegil_html += f"<p style='color:#0277BD; font-weight:bold;'>💡 지정한 길일 탐색 구간: {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}<br>💡 참고 산모 정보: 마지막 생리일({last_period.strftime('%Y-%m-%d')}), 평균 주기({cycle}일)</p>"
                else:
                    taegil_html += f"<p style='color:#0277BD; font-weight:bold;'>💡 지정한 길일 탐색 구간: {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}</p>"

                if not best_days:
                    taegil_html += "<p style='color:#D32F2F; font-weight:bold;'>⚠️ 지정하신 탐색 기간 내에 오행이 조화로운 특A급 길일이 없습니다. 탐색 기간을 더 넓게 조정해 주십시오.</p>"
                else:
                    today_dt = dt_mod.date.today()
                    
                    for idx, day_info in enumerate(best_days):
                        border_col = "#C62828" if idx == 0 else "#2E7D32"
                        b_time_info = day_info['best_time']
                        
                        b_date_str = day_info['date']
                        if isinstance(b_date_str, str):
                            y_s, m_s, d_s = map(int, b_date_str.split('-'))
                            b_dt = dt_mod.date(y_s, m_s, d_s)
                        else:
                            b_dt = b_date_str
                            b_date_str = b_dt.strftime("%Y-%m-%d")
                            
                        # 1. 합궁 기간 및 텍스트 결정
                        conception_start = b_dt - dt_mod.timedelta(days=268)
                        conception_end = b_dt - dt_mod.timedelta(days=264)
                        conception_str = f"{conception_start.strftime('%Y년 %m월 %d일')} ~ {conception_end.strftime('%Y년 %m월 %d일')}"

                        if conception_end < today_dt:
                            conception_title = "💖 추정 잉태(합궁) 시기"
                            conception_msg = f"<span style='font-size:13px; color:#D32F2F; font-weight:bold;'>(※ 주의: 이 날짜에 출산하려면 과거에 이미 잉태가 완료되었어야 합니다. 현재 임신 중인 산모 전용 길일입니다.)</span>"
                        else:
                            conception_title = "💖 잉태(합궁) 권장 기간"
                            conception_msg = f"<span style='font-size:13px; color:#0277BD; font-weight:bold;'>(※ 계획 임신 시, 위 기간 내에 잉태해야 해당 길일에 출산할 확률이 높습니다.)</span>"

                        # 2. 산모 임신 주차 역산
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

                        # 3. 신생아 사주 원국 테이블 획득
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

                        # 4. 💡 신생아 AI 심층 통변 가동 (남/여 대운 분리 및 부모 인연)
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
                                clean_ai = re.sub(r'###\s*(.*?)\n', r'<h3 style="color:#00695C; font-size:18px; font-weight:bold; margin-top:20px; margin-bottom:10px;">\1</h3>', clean_ai)
                                clean_ai = re.sub(r'##\s*(.*?)\n', r'<h2 style="color:#004D40; font-size:20px; font-weight:bold; margin-top:25px; margin-bottom:12px; border-bottom:1px solid #ddd;">\1</h2>', clean_ai)
                                
                                formatted_lines = []
                                for line in clean_ai.split('\n'):
                                    line_str = line.strip()
                                    if line_str:
                                        if line_str.startswith('<h') or line_str.startswith('<div'):
                                            formatted_lines.append(line_str)
                                        else:
                                            formatted_lines.append(f'<p style="margin:10px 0; line-height:1.8; font-family:\'Nanum Myeongjo\', serif; font-size:15px; color:#333;">{line_str}</p>')
                                ai_output_html = "".join(formatted_lines)
                            else:
                                ai_output_html = '<p style="color:red;">⚠️ 출산 택일 AI 정밀 분석 응답을 불러오지 못했습니다.</p>'
                        except Exception as e:
                            ai_output_html = f'<p style="color:red;">⚠️ AI 분석 중 오류: {e}</p>'

                        # 5. HTML 종합 조립
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
                
                clean_taegil_html = re.sub(r'>\s+<', '><', taegil_html.replace('\n', '')).strip()
                report_box = html_views.get_final_report_box(clean_taegil_html)
                st.markdown(report_box, unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"🚨 출산 택일 분석 중 오류 발생: {e}")

    # ==============================================================================
    # [3-2번 카테고리] 타 감명서 비교 (궁합) 정밀 분석 (들여쓰기 제거 포함)
    # ==============================================================================
    elif "3-2" in u_product:
        st.markdown("---")
        with st.spinner("⏳ 입력받은 궁합 감명서와 초연 시공명리 알고리즘을 교차 검증 중입니다..."):
            try:
                external_review_text = st.session_state.get("external_review_input", "").strip()

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

                m_info = html_views.get_info_header("♂️", male_name, "남성", male_marital, male_age, male_sol, male_lun, f"{male_time}시", p_color="#1A237E")
                w_info = html_views.get_info_header("♀️", female_name, "여성", female_marital, female_age, female_sol, female_lun, f"{female_time}시", p_color="#2E7D32")
                
                cover_html = html_views.get_gunghap_cover(
                    APP_VERSION, male_name, male_age, male_sol, male_lun, f"{male_time}",  
                    female_name, female_age, female_sol, female_lun, f"{female_time}", 
                    dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
                )

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

                compare_facts = {
                    "m_name": male_name, "f_name": female_name,
                    "m_ganju": f"{m_ys}{m_yb} {m_ms}{m_mb} {m_ds}{m_db} {m_hs}{m_hb}",
                    "f_ganju": f"{f_ys}{f_yb} {f_ms}{f_mb} {f_ds}{f_db} {f_hs}{f_hb}",
                    "external_text": external_review_text if external_review_text else "입력된 외부 감명서가 없습니다."
                }

                prompt_text = prompts.COMPARE_GUNGHAP_PROMPT.format_map(compare_facts)
                ai_result = call_gemini_api(prompt_text)

                if ai_result:
                    clean_ai = re.sub(r'```[a-zA-Z]*', '', ai_result).replace("```", "").strip()
                    clean_ai = re.sub(r'###\s*(.*?)\n', r'<h3 style="color:#1A237E; font-size:20px; font-weight:bold; margin-top:25px; margin-bottom:10px;">\1</h3>', clean_ai)
                    clean_ai = re.sub(r'##\s*(.*?)\n', r'<h2 style="color:#0D47A1; font-size:22px; font-weight:bold; margin-top:30px; margin-bottom:15px; border-bottom:1px solid #ddd;">\1</h2>', clean_ai)
                    
                    formatted_lines = []
                    for line in clean_ai.split('\n'):
                        line_str = line.strip()
                        if line_str:
                            if line_str.startswith('<h') or line_str.startswith('<div') or line_str.startswith('<table'):
                                formatted_lines.append(line_str)
                            else:
                                formatted_lines.append(f'<p style="margin:10px 0; line-height:1.8; font-family:\'Nanum Myeongjo\', serif; font-size:16px; color:#333;">{line_str}</p>')
                    ai_output_html = "".join(formatted_lines)
                else:
                    ai_output_html = '<p style="color:red;">⚠️ 타 감명서 비교 분석 AI 응답을 불러오지 못했습니다.</p>'

                ai_box_html = f'<div style="margin-top:20px; padding:20px; background-color:#ffffff; border-radius:10px; border:1px solid #E0E0E0;"><h2 style="color:#0D47A1; border-bottom:2px solid #0D47A1; padding-bottom:8px;">🔍 타 감명서(궁합) 초연 정밀 비교 검증 보고서</h2>{ai_output_html}</div>'

                full_inner_content = "".join([
                    str(m_info or ''), str(m_table or ''), str(m_master_html or ''), str(m_un or ''),
                    str(w_info or ''), str(w_table or ''), str(w_master_html or ''), str(w_un or ''),
                    str(ai_box_html or '')
                ])
                
                # 💡 들여쓰기 공백 정제 후 A4 테두리 씌워서 최종 출력
                clean_full_inner = re.sub(r'>\s+<', '><', full_inner_content.replace('\n', '')).strip()
                report_box = html_views.get_final_report_box(clean_full_inner)
                
                st.markdown(cover_html, unsafe_allow_html=True)
                st.markdown(report_box, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"🚨 타 감명서 비교(궁합) 처리 중 오류 발생: {e}")
