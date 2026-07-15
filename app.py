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
APP_VERSION = "ver 60.2"
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
    return get_ai_response(prompts.SYSTEM_ROLE, prompt_text, model_name='gemini-2.5-flash')

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
# 2. 사이드바 통제 센터 (입력 및 실행 버튼)
# ==============================================================================
with st.sidebar:
    st.markdown(f"""<div style="text-align: center;"><h1 style="font-family: 'Nanum Gothic', sans-serif; color: #000000; font-weight: 900; font-size: 20px; margin-bottom: 5px;">🏮 초연 시공명리 연구소</h1></div>""", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #555555; font-family: sans-serif; font-size: 12px;'>{APP_VERSION} Master (Base + Gunghap)</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<div style='font-size: 17px; font-weight: 900; color: #000000; margin-bottom: 5px; font-family: \"Nanum Gothic\", sans-serif;'>📋 분석 상품 선택</div>", unsafe_allow_html=True)
    
    u_product = st.selectbox("상품선택", [
        "1. 개인사주 및 일진 분석", "2. 올 해의 운세 (세운)", "3. 이번 달의 운세 (월운)",
        "4. 재물운 특화 분석", "5. 직업/직장운 특화 분석", "6. 건강운 특화 분석",
        "7. 연애 및 궁합운 특화 분석", "8. 결혼 택일 정밀 분석", "9. 출산 택일", "10. 이사 및 방위", "11. 타 감명서 비교 (개인)", "12. 타 감명서 비교 (궁합)"
    ], label_visibility="collapsed")

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
                            curr_dt -= dt_mod.timedelta(days=1) # [수정] while 문 안으로 올바르게 들여쓰기
                    if found: break # [수정] for 문 안으로 올바르게 들여쓰기
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

    with st.expander("👤 신청인 기본 정보", expanded=True):
        name = st.text_input("이름", value="", placeholder="홍길동", key="u_n")
        gender = st.selectbox("성별", ["남성", "여성"], key="u_g")
        u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
        u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")
        col_y, col_m, col_d = st.columns(3)
        with col_y: b_year = st.number_input("년도", 1900, 2050, value=1980, key="s_y")
        with col_m: b_month = st.number_input("월", 1, 12, value=1, key="s_m")
        with col_d: b_day = st.number_input("일", 1, 31, value=1, key="s_d")
        b_time = st.selectbox("태어난 시간", idx_list, key="s_t")

    # ---------------------------------------------------------
    # 상품별 동적 입력창
    # ---------------------------------------------------------
    if "1. 개인사주" in u_product:
        run_iljin_calc = st.checkbox("🔮 일진 시공간 분석 추가 가동", value=False)
    
    elif any(x in u_product for x in ["2. 올 해", "3. 이번 달", "4. 재물", "5. 직업", "6. 건강"]):
        if "4. 재물" in u_product: wealth_goal = st.text_input("고민되는 금전 문제는?", key="wealth_goal")
        elif "5. 직업" in u_product: career_goal = st.text_input("고민되는 직업 분야는?", key="career_goal")
        elif "6. 건강" in u_product: health_goal = st.text_input("관리할 건강 부위는?", key="health_goal")

    elif any(x in u_product for x in ["7. 연애", "8. 결혼", "9. 출산"]):
        st.markdown("---")
        with st.expander("👥 상대방 사주간지 역산", expanded=False):
            p_col_g1, p_col_g2 = st.columns(2)
            with p_col_g1: p_ry = st.text_input("상대방 년주", key="p_ry")
            with p_col_g2: p_rm = st.text_input("상대방 월주", key="p_rm")
            p_col_g3, p_col_g4 = st.columns(2)
            with p_col_g3: p_rd = st.text_input("상대방 일주", key="p_rd")
            with p_col_g4: p_rt = st.text_input("상대방 시주", key="p_rt")
            
            if st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="btn_partner_rev"):
                _p_ry, _p_rm, _p_rd = extract_ganji(p_ry), extract_ganji(p_rm), extract_ganji(p_rd)
                if not _p_ry and not _p_rm and not _p_rd:
                    if 'rev_p_success_msg' in st.session_state: del st.session_state['rev_p_success_msg']
                    st.rerun()
                elif len(_p_ry)==2 and len(_p_rm)==2 and len(_p_rd)==2:
                    p_ry_h = engine.K2H_GAN.get(_p_ry[0], _p_ry[0]) + engine.K2H_JI.get(_p_ry[1], _p_ry[1])
                    p_rm_h = engine.K2H_GAN.get(_p_rm[0], _p_rm[0]) + engine.K2H_JI.get(_p_rm[1], _p_rm[1])
                    p_rd_h = engine.K2H_GAN.get(_p_rd[0], _p_rd[0]) + engine.K2H_JI.get(_p_rd[1], _p_rd[1])
                    klc_find = KoreanLunarCalendar(); found = False
                    for y in range(2026, 1899, -1):
                        klc_find.setSolarDate(y, 7, 1); gj_y = klc_find.getChineseGapJaString().split()
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
                                curr_dt -= dt_mod.timedelta(days=1) # [수정] while 문 안으로 올바르게 들여쓰기
                        if found: break # [수정] for 문 안으로 올바르게 들여쓰기
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

        with st.expander("👥 상대방 기본 정보", expanded=True):
            f_name = st.text_input("상대방 이름", value="", key="f_n")
            f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_g")
            f_marital = st.selectbox("상대방 혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="f_m_stat")
            f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c")
            p_col1, p_col2, p_col3 = st.columns(3)
            f_y = p_col1.number_input("년도(상대)", 1900, 2050, value=1980, key="p_y_in")
            f_m = p_col2.number_input("월(상대)", 1, 12, value=1, key="p_m_in")
            f_d = p_col3.number_input("일(상대)", 1, 31, value=1, key="p_d_in")
            f_t = st.selectbox("태어난 시간(상대)", idx_list, key="p_t_key")

        if "8. 결혼" in u_product:
            date_mode = st.radio("택일 방식", ["기간 선택", "특정일 지정"])
            if date_mode == "기간 선택":
                start_date = st.date_input("시작일"); end_date = st.date_input("종료일")
        elif "9. 출산" in u_product:
            run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석", value=True)

    elif "10. 이사" in u_product:
        moving_date = st.date_input("이사 희망일")
        moving_dir = st.selectbox("이사 희망 방위", ["동쪽", "서쪽", "남쪽", "북쪽", "기타"])

    elif "11. 타 감" in u_product:
        other_report = st.text_area("📄 타 감명서 원문 붙여넣기", height=150, key="other_reading")

    # ---------------------------------------------------------
    # 실행 및 인쇄 버튼
    # ---------------------------------------------------------
    st.markdown("---")
    if st.button("✨ [초연 시공명리 풀이 가동]", key="btn_run", use_container_width=True, type="primary"):
        st.session_state['app_running'] = True
        
    if st.button("🖨️ 풀이 결과 인쇄 / PDF 저장", key="btn_print", use_container_width=True):
        components.html("<script>window.parent.print();</script>", height=0)

# ==============================================================================
# 3. 메인 화면 출력부
# ==============================================================================
if st.session_state.get('app_running', False):
    
    # ---------------------------------------------------------
    # [1번 상품] 개인사주 및 일진 분석
    # ---------------------------------------------------------
    if "1. 개인사주" in u_product:
        klc = KoreanLunarCalendar()
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

        with st.spinner(f"⏳ [초연 시공명리 분석({APP_VERSION}) 중....]"):
            # 1. 기초 연산
            h, m = extract_time(b_time)
            y_pillar, m_pillar, lon = get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
            is_lunar_val, is_leap_val = ("음력" in u_cal), ("윤달" in u_cal)
            _, _, d_pillar = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)
            
            # 2. 오서둔 직접 연산 (시주 추출)
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

            # [핵심] 모든 변수를 추출된 그대로 사용합니다 (engine에서 처리하므로)
            gans, jjis = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]], [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
            hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
            hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]

            # 4. 마스터바 데이터 조립
            #--1. 대운수 계산
            base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
            adj_mins = engine.get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            
            # [수정 적용] ys를 직접 사용하여 index 도출
            order_dir = 1 if (engine.GAN.index(ys) % 2 == 0) == (gender == '남성') else -1
            calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
            direction_str = "순행" if order_dir == 1 else "역행"

            #--2. 오행 수 계산
            counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
            for c in gans + jjis:
                oh = engine.get_color(c)
                if oh in counts: counts[oh] += 1

            #--3. 천을귀인
            guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
            guiin_str = guiin_map.get(engine.K2H_GAN.get(ds, ds), '없음')
            
            curr_year = dt_mod.datetime.now().year
            curr_y_ji = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'][(curr_year - 1984) % 12]
            
            # --4. 공망 계산
            n_gong = engine.calculate_gongmang(ys, yb)  # 년 공망
            i_gong = engine.calculate_gongmang(ds, db)  # 일 공망
            n_gong = n_gong if n_gong else "-"
            i_gong = i_gong if i_gong else "-"
            
            # --5. 삼재 계산
            cur_samjae = engine.get_samjae(yb, curr_y_ji)
            samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"

            # 5. UI 데이터 준비
            sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
            lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
            time_str_fmt = f"{b_time.split('(')[0].strip()} ({hb})시" if b_time != "시간 모름" else ""

            # ---------------------------------------------------------
            # HTML 렌더링 조립
            # ---------------------------------------------------------
            cover_html = html_views.get_personal_cover(APP_VERSION, p_icon, name, sol_str_fmt, lun_str_fmt, time_str_fmt, today_str)
            intro_html = html_views.get_intro_html()
            info_h = html_views.get_info_header(p_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, time_str_fmt)

            ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                cells = "".join([f"<td style='color:{('#1A237E' if ci==r_idx else ('#000' if engine.get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else engine.get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

            gan_rel = "".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])
            
            # [수정 적용] 엔진이 통역을 완벽히 하므로 직관적으로 값 전달
            gan_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, hs)}</td><td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(ds, ms)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, ys)}</td>"
            gan_row = "".join([td_bg(g)+f"{g}</td>" for g in gans])
            ji_row = "".join([td_bg(j)+f"{j}</td>" for j in jjis])
            ji_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds, hb)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, db)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, mb)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds, yb)}</td>"
            jijanggan = "".join([f"<td style='padding:0; border:1px solid #444;'>{engine.get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])
            unsung = "".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{engine.get_unsung(ds, jjis[i])}</td>" for i in range(4)])
            shinsal = "".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{engine.get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])
            
            filtered_shinsals = ["<br>".join(engine.get_general_shinsal_filtered(i, gans, jjis, gender)[:6]) if engine.get_general_shinsal_filtered(i, gans, jjis, gender) else "-" for i in range(4)]
            gen_shinsal = "".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{filtered_shinsals[i]}</td>" for i in range(4)])

            table_html = html_views.get_saju_table(info_h, gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal)
            master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, samjae_color, cur_samjae)

            yukchin_rule = engine.get_yukchin_rule(gender, u_marital)
            try:
                daewun_data_list = engine.get_daewun_data_list(ms, mb, ds, yb, order_dir, calc_d, age)
            except AttributeError:
                # 만약 함수명이 바뀌었다면 엔진을 다시 체크해야 합니다.
                st.error("분석 엔진에서 daewun 함수를 찾을 수 없습니다. engine.py를 확인하세요.")
                daewun_data_list = []
            un_html = html_views.generate_daewun_layout(daewun_data_list, direction_str, calc_d, get_oh_class)

            # AI 통변
            ai_output_html = ""
            try:
                fact_sheet = prompts.PERSONAL_SAJU_PROMPT.format(name=name, gender=gender, ilgan=ds, ilju=ds+db, wolryeong=ms+mb, jijanggan_info="엔진 데이터 연동", missing_and_gongmang="엔진 데이터 연동", shinsal_info="엔진 데이터 연동", vault_info="엔진 데이터 연동")
                ai_result = call_gemini_api(fact_sheet)
                ai_result = re.sub(r"안녕하세요, .*?감사드립니다\.", "", ai_result).strip()
                ai_output_html = prompts.HTML_LAYOUTS["report_box"].format(content=ai_result)
            except Exception: pass

            closing_html = html_views.get_closing_html(name)
            
            # 최종 렌더링 출력
            st.markdown(cover_html, unsafe_allow_html=True)
            final_report = (
                str(table_html or "") + 
                str(master_bar_html or "") + 
                str(intro_html or "") + 
                str(un_html or "") + 
                str(ai_output_html or "") + 
                str(closing_html or "")
            )
            st.markdown(html_views.get_final_report_box(final_report), unsafe_allow_html=True)

    # ---------------------------------------------------------
    # [2번 상품] 올 해 (세운 전용 출력)
    # ---------------------------------------------------------
    elif "2. 올 해" in u_product:
        st.header(f"🔮 {name}님의 올해(세운) 분석")
        st.markdown("---")
        with st.spinner("⏳ 세운 정밀 분석 중...."):
            klc = KoreanLunarCalendar()
            if "음력" in u_cal:
                is_leap = True if "윤달" in u_cal else False
                klc.setLunarDate(int(b_year), int(b_month), int(b_day), is_leap)
                sol_y = klc.solarYear
            else:
                klc.setSolarDate(int(b_year), int(b_month), int(b_day))
                sol_y = int(b_year)
                
            curr_year = dt_mod.datetime.now().year
            age = curr_year - sol_y + 1

            def extract_time(time_str):
                if "모름" in time_str: return 0, 0
                match = re.search(r'(\d{2}):(\d{2})', time_str)
                return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

            h, m = extract_time(b_time)
            y_pillar, m_pillar, lon = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
            is_lunar_val, is_leap_val = ("음력" in u_cal), ("윤달" in u_cal)
            _, _, d_pillar = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)

            ys, yb = y_pillar[0], y_pillar[1]
            ms, mb = m_pillar[0], m_pillar[1]
            ds = d_pillar[0]

            base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
            adj_mins = engine.get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            order_dir = 1 if (engine.GAN.index(ys) % 2 == 0) == (gender == '남성') else -1
            calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)

            c_idx = engine.GAN.index(ms) if ms in engine.GAN else 0
            j_idx = engine.JI.index(mb) if mb in engine.JI else 0
            
            cur_dw_idx = max(0, (age - calc_d) // 10)
            dw_g_cur_hangul = engine.GAN[(c_idx + (cur_dw_idx+1)*order_dir)%10]
            dw_j_cur_hangul = engine.JI[(j_idx + (cur_dw_idx+1)*order_dir)%12]
            dw_g_cur = engine.K2H_GAN.get(dw_g_cur_hangul, dw_g_cur_hangul)
            dw_j_cur = engine.K2H_JI.get(dw_j_cur_hangul, dw_j_cur_hangul)
            
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
                
                ss_gan = engine.get_ss(ds, tc_hangul)
                ss_ji = engine.get_ss(ds, tj_hangul)
                un_sung = engine.get_unsung(ds, tj_hangul)
                shin_sal = engine.get_12_shinsal(yb, tj_hangul)

                bg_col = "#E1F5FE" if ty == curr_year else "transparent"
                b_left = "1px solid #ccc" if i != 0 else "none"

                se_content += html_views.get_sewun_cell(
                    f"{ty}년", tage, ss_gan, tc, get_oh_class(tc), 
                    tj, get_oh_class(tj), ss_ji, un_sung, shin_sal, bg_col, b_left
                )

            se_html = html_views.get_sewun_layout(f"[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]", se_content)
            st.markdown(html_views.get_final_report_box(se_html), unsafe_allow_html=True)

    # ---------------------------------------------------------
    # [3번 상품] 이번 달 (월운 전용 출력)
    # ---------------------------------------------------------
    elif "3. 이번 달" in u_product:
        st.header(f"🔮 {name}님의 이번 달(월운) 분석")
        st.markdown("---")
        with st.spinner("⏳ 월운 정밀 분석 중...."):
            curr_year = dt_mod.datetime.now().year
            curr_m = dt_mod.datetime.now().month

            def extract_time(time_str):
                if "모름" in time_str: return 0, 0
                match = re.search(r'(\d{2}):(\d{2})', time_str)
                return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

            h, m = extract_time(b_time)
            y_pillar, _, _ = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
            is_lunar_val, is_leap_val = ("음력" in u_cal), ("윤달" in u_cal)
            _, _, d_pillar = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)

            yb = y_pillar[1]
            ds = d_pillar[0]

            wol_gans_kor = ["기", "경", "신", "임", "계", "갑", "을", "병", "정", "무", "기", "경"]
            wol_jis_kor = ["축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해", "자"]
            wol_content = ""
            
            for i in range(12):
                tm = i + 1
                wc_kor, wj_kor = wol_gans_kor[i], wol_jis_kor[i]
                
                wc = engine.K2H_GAN.get(wc_kor, wc_kor)
                wj = engine.K2H_JI.get(wj_kor, wj_kor)
                
                ss_gan = engine.get_ss(ds, wc_kor) or "-"
                ss_ji = engine.get_ss(ds, wj_kor) or "-"
                un_sung = engine.get_unsung(ds, wj_kor) or "-"
                shin_sal = engine.get_12_shinsal(yb, wj_kor) or "-"
                
                bg_col = "#E8F5E9" if tm == curr_m else "transparent"
                b_left = "1px solid #ccc" if i != 0 else "none" 
                
                wol_content += html_views.get_wolun_cell(
                    tm, ss_gan, wc, get_oh_class(wc), 
                    wj, get_oh_class(wj), ss_ji, un_sung, shin_sal, bg_col, b_left
                )
            
            wol_html = html_views.get_wolun_layout(f"[ 월운의 흐름 ({curr_year}년도 양력기준) ]", wol_content)
            st.markdown(html_views.get_final_report_box(wol_html), unsafe_allow_html=True)

    # ---------------------------------------------------------
    # [4~6번 상품] 재물, 직업, 건강 등
    # ---------------------------------------------------------
    elif any(x in u_product for x in ["4. 재물", "5. 직업", "6. 건강"]):
        st.header(f"🔮 {name}님의 {u_product.split('.')[1].strip()} 분석")
        st.markdown("---")
        with st.spinner(f"⏳ [{u_product.split('.')[1].strip()}] 정밀 분석 중...."):
            st.info("데이터 연동 및 AI 분석 대기 중입니다. (향후 1번 상품의 연산 로직을 기반으로 확장될 공간입니다.)")
            if "4. 재물" in u_product:
                st.success(f"입력하신 금전 고민: {wealth_goal}")
            elif "5. 직업" in u_product:
                st.success(f"입력하신 직업 고민: {career_goal}")
            elif "6. 건강" in u_product:
                st.success(f"입력하신 건강 고민: {health_goal}")
                
    # ---------------------------------------------------------
    # [7번 상품] 연애 및 궁합운 특화 분석
    # ---------------------------------------------------------
    elif "7. 연애" in u_product:
        st.header(f"💕 {name}님과 {f_name}님의 초연 궁합")
        st.markdown("---")
        with st.spinner("⏳ 두 분의 시공간을 교차 분석 중입니다..."):
            app_p_icon = "♂️" if gender == "남성" else "♀️"
            part_p_icon = "♂️" if f_gender == "남성" else "♀️"
            today_str = dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
            
            cover_html = html_views.get_gunghap_cover(APP_VERSION, app_p_icon, name, gender, u_marital, part_p_icon, f_name, f_gender, f_marital, today_str)
            st.markdown(cover_html, unsafe_allow_html=True)

            gh_data = engine.get_gunghap_data(b_year, b_month, b_day, b_time, f_y, f_m, f_d, f_t)
            
            def build_master_bar(m_data):
                return html_views.get_master_bar(
                    m_data[0], m_data[1], m_data[2], m_data[3], m_data[4], m_data[5], 
                    m_data[6], m_data[7], m_data[8], m_data[9], m_data[10]
                )

            m_master_html = build_master_bar(gh_data["m_master"])
            w_master_html = build_master_bar(gh_data["w_master"])
            
            m_table = html_views.get_saju_table(*gh_data["m_table"])
            w_table = html_views.get_saju_table(*gh_data["w_table"])

            st.markdown(html_views.get_gunghap_person_box(m_table, m_master_html), unsafe_allow_html=True)
            st.markdown(html_views.get_gunghap_person_box(w_table, w_master_html, add_page_break=True), unsafe_allow_html=True)
            
            st.markdown(html_views.get_gunghap_closing(), unsafe_allow_html=True)

    # ---------------------------------------------------------
    # [8~10번 상품] 결혼, 출산, 이사 택일
    # ---------------------------------------------------------
    elif any(x in u_product for x in ["8. 결혼", "9. 출산", "10. 이사"]):
        st.header(f"🗓️ {name}님의 {u_product.split('.')[1].strip()}")
        st.markdown("---")
        with st.spinner("⏳ 길일 및 시공간 분석 중..."):
            st.info("명리학적 택일 분석 엔진 가동 대기 중입니다.")

    # ---------------------------------------------------------
    # [11번 상품] 타 감명서 비교 (개인)
    # ---------------------------------------------------------
    elif "11. 타 감" in u_product:
        st.header("⚖️ 초연 시공명리 타 감명서 1:1 비교")
        st.markdown("---")
        if not other_report: 
            st.warning("👈 사이드바에 타 감명서 원문을 입력해주세요.")
        else: 
            st.info("타 감명서 비교 로직이 작동합니다.")

    # ---------------------------------------------------------
    # [12번 상품] 타 감명서 비교 (궁합)
    # ---------------------------------------------------------
    elif "12. 타 감" in u_product:
        st.header("⚖️ 초연 시공명리 타 감명서 비교 (궁합)")
        st.markdown("---")
        if not st.session_state.get('other_reading', ""): 
            st.warning("👈 사이드바에 타 감명서 원문을 입력해주세요.")
        else:
            # 7번 궁합 로직의 핵심 결과(gh_data)를 여기서 호출하여 비교합니다.
            st.info("상대방 사주 데이터와 타 감명서 궁합 내용을 대조 분석합니다.")
            # 7번(궁합)의 로직을 그대로 가져오되, 비교 분석 결과만 추가로 띄우면 됩니다.
