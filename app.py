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
import html_views  # 👈 HTML 보관소 불러오기

# ==============================================================================
# 1. 초기 설정 및 공통 함수
# ==============================================================================
APP_VERSION = "ver 60.1"
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

# 👇 전역 공통 함수: 오행 판별 및 배경색 지정 (DRY 원칙 적용)
def get_oh_class(ganji):
    oh = '무'
    if ganji in ['甲', '乙', '寅', '卯']: oh = '목'
    elif ganji in ['丙', '丁', '巳', '午']: oh = '화'
    elif ganji in ['戊', '己', '辰', '戌', '丑', '未']: oh = '토'
    elif ganji in ['庚', '辛', '申', '酉']: oh = '금'
    elif ganji in ['壬', '癸', '亥', '子']: oh = '수'
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
        "7. 연애 및 궁합운 특화 분석", "8. 결혼 택일 정밀 분석", "9. 출산 택일", "10. 이사 및 방위", "11. 타 감명서 비교"
    ], label_visibility="collapsed")

    # ---------------------------------------------------------
    # [수정 완료] 신청인 정보: 역산(계산) 먼저 -> 기본정보(출력) 나중
    # ---------------------------------------------------------
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
                                # [강제 업데이트] 년, 월, 일
                                st.session_state['s_y'] = curr_dt.year
                                st.session_state['s_m'] = curr_dt.month
                                st.session_state['s_d'] = curr_dt.day
                                
                                # [강제 업데이트] 태어난 시간 (위젯 key="s_t")
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
        # [수정 완료] 상대방 정보: 역산(계산) 먼저 -> 기본정보(출력) 나중
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
                                    # [강제 업데이트] 년, 월, 일
                                    st.session_state['p_y_in'] = curr_dt.year
                                    st.session_state['p_m_in'] = curr_dt.month
                                    st.session_state['p_d_in'] = curr_dt.day
                                    
                                    # [강제 업데이트] 태어난 시간 (위젯 key="p_t_key")
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
        # 버튼을 누르면 '실행 중'이라는 상태를 시스템에 각인시킵니다.
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
            y_pillar, m_pillar, lon = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
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

            gans, jjis = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]], [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
            hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
            hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]

            counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
            for c in gans + jjis:
                if c in "甲乙寅卯": counts['목']+=1
                elif c in "丙丁巳午": counts['화']+=1
                elif c in "戊己辰戌丑未": counts['토']+=1
                elif c in "庚辛申酉": counts['금']+=1
                elif c in "壬癸亥子": counts['수']+=1

            guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 亥','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
            guiin_str = guiin_map.get(ds, '없음')

            # --- [사전 작업] 연산용 한글 기준점 명확화 ---
            ys_kor = {v: k for k, v in engine.K2H_GAN.items()}.get(ys, ys)
            yb_kor = {v: k for k, v in engine.K2H_JI.items()}.get(yb, yb)
            ms_kor = {v: k for k, v in engine.K2H_GAN.items()}.get(ms, ms)
            mb_kor = {v: k for k, v in engine.K2H_JI.items()}.get(mb, mb)
            ds_kor = {v: k for k, v in engine.K2H_GAN.items()}.get(ds, ds)
            db_kor = {v: k for k, v in engine.K2H_JI.items()}.get(db, db)

            # 3. 공망 및 삼재 연산
            try:
                n_gong_str = engine.calculate_gongmang(ys_kor, yb_kor)
                i_gong_str = engine.calculate_gongmang(ds_kor, db_kor)
            except TypeError:
                n_gong_str = engine.calculate_gongmang(ys_kor + yb_kor)
                i_gong_str = engine.calculate_gongmang(ds_kor + db_kor)
                
            n_gong = "".join([engine.K2H_JI.get(ch, ch) for ch in (n_gong_str if n_gong_str else "")])
            i_gong = "".join([engine.K2H_JI.get(ch, ch) for ch in (i_gong_str if i_gong_str else "")])
            if not n_gong: n_gong = "-"
            if not i_gong: i_gong = "-"

            curr_base = (dt_mod.datetime.now().year - 1984) % 60
            cur_samjae = engine.get_samjae(yb_kor, engine.JI[curr_base % 12])
            samjae_color = "#1A237E" if cur_samjae != "해당 없음" else "#2E7D32"

            # 4. 대운수 계산
            base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
            adj_mins = engine.get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            order_dir = 1 if (engine.GAN.index(ys_kor) % 2 == 0) == (gender == '남성') else -1
            calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
            direction_str = "순행" if order_dir == 1 else "역행"

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

            filtered_shinsals = ["<br>".join(engine.get_general_shinsal_filtered(i, gans, jjis, gender)[:6]) if engine.get_general_shinsal_filtered(i, gans, jjis, gender) else "-" for i in range(4)]
            
            gan_rel = "".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])
            gan_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds_kor, {v: k for k, v in engine.K2H_GAN.items()}.get(hs, hs))}</td><td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(ds_kor, ms_kor)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds_kor, ys_kor)}</td>"
            gan_row = f"{td_bg(hs)}{hs}</td>{td_bg(ds)}{ds}</td>{td_bg(ms)}{ms}</td>{td_bg(ys)}{ys}</td>"
            ji_row = f"{td_bg(hb)}{hb}</td>{td_bg(db)}{db}</td>{td_bg(mb)}{mb}</td>{td_bg(yb)}{yb}</td>"
            ji_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds_kor, {v: k for k, v in engine.K2H_JI.items()}.get(hb, hb))}</td><td style='border:1px solid #444;'>{engine.get_ss(ds_kor, db_kor)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds_kor, mb_kor)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds_kor, yb_kor)}</td>"
            jijanggan = "".join([f"<td style='padding:0; border:1px solid #444;'>{engine.get_jijanggan_full(ds_kor, {v: k for k, v in engine.K2H_JI.items()}.get(jjis[i], jjis[i]))}</td>" for i in range(4)])
            unsung = "".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{engine.get_unsung(ds_kor, {v: k for k, v in engine.K2H_JI.items()}.get(jjis[i], jjis[i]))}</td>" for i in range(4)])
            shinsal = "".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{engine.get_12_shinsal(yb_kor, {v: k for k, v in engine.K2H_JI.items()}.get(jjis[i], jjis[i]))}</td>" for i in range(4)])
            gen_shinsal = "".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{filtered_shinsals[i]}</td>" for i in range(4)])

            table_html = html_views.get_saju_table(info_h, gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal)
            master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, samjae_color, cur_samjae)

            # ---------------- [대운 연산] ----------------
            un_content = ""
            c_idx = engine.GAN.index(ms_kor) if ms_kor in engine.GAN else 0
            j_idx = engine.JI.index(mb_kor) if mb_kor in engine.JI else 0

            for i in range(10):
                val = i*10+calc_d
                
                # 1. 연산용 한글 100% 추출
                c_hangul = engine.GAN[(c_idx+(i+1)*order_dir)%10]
                j_hangul = engine.JI[(j_idx+(i+1)*order_dir)%12]
                
                # 2. 출력용 한자 변환
                c = engine.K2H_GAN.get(c_hangul, c_hangul)
                j = engine.K2H_JI.get(j_hangul, j_hangul)
                
                # 3. 십성/운성 계산 (결과 없으면 "-" 강제 삽입)
                ss_gan = engine.get_ss(ds_kor, c_hangul) or "-"
                ss_ji = engine.get_ss(ds_kor, j_hangul) or "-"
                un_sung = engine.get_unsung(ds_kor, j_hangul) or "-"
                shin_sal = engine.get_12_shinsal(yb_kor, j_hangul) or "-"
                
                bg_col = "#FFF9C4" if val <= age < val+10 else "transparent"
                b_left = "1px solid #ccc" if i != 0 else "none"
                
                # 4. 반복문 안쪽 (들여쓰기 16칸 기준)
                un_content += html_views.get_un_cell(
                    f"{val}세", ss_gan, c, get_oh_class(c), 
                    j, get_oh_class(j), ss_ji, un_sung, shin_sal, bg_col, b_left
                )

            # 5. 반복문 밖 (들여쓰기 12칸 기준)
            un_html = html_views.get_un_layout(f"[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]", un_content)

            # AI 통변
            ai_output_html = ""
            try:
                fact_sheet = prompts.PERSONAL_SAJU_PROMPT.format(name=name, gender=gender, ilgan=d_pillar[0], ilju=d_pillar, wolryeong=m_pillar, jijanggan_info="엔진 데이터 연동", missing_and_gongmang="엔진 데이터 연동", shinsal_info="엔진 데이터 연동", vault_info="엔진 데이터 연동")
                ai_result = call_gemini_api(fact_sheet)
                ai_result = re.sub(r"안녕하세요, .*?감사드립니다\.", "", ai_result).strip()
                ai_output_html = prompts.HTML_LAYOUTS["report_box"].format(content=ai_result)
            except Exception: pass

            closing_html = html_views.get_closing_html(name)
            
            # 최종 렌더링 출력 (박사님 지시 순서 적용)
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
            # 독립적 구동을 위한 최소 기초 연산
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

            ys_kor = {v: k for k, v in engine.K2H_GAN.items()}.get(y_pillar[0], y_pillar[0])
            yb_kor = {v: k for k, v in engine.K2H_JI.items()}.get(y_pillar[1], y_pillar[1])
            ms_kor = {v: k for k, v in engine.K2H_GAN.items()}.get(m_pillar[0], m_pillar[0])
            mb_kor = {v: k for k, v in engine.K2H_JI.items()}.get(m_pillar[1], m_pillar[1])
            ds_kor = {v: k for k, v in engine.K2H_GAN.items()}.get(d_pillar[0], d_pillar[0])

            base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
            adj_mins = engine.get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            order_dir = 1 if (engine.GAN.index(ys_kor) % 2 == 0) == (gender == '남성') else -1
            calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)

            c_idx = engine.GAN.index(ms_kor) if ms_kor in engine.GAN else 0
            j_idx = engine.JI.index(mb_kor) if mb_kor in engine.JI else 0
            
            # [세운 연산]
            cur_dw_idx = max(0, (age - calc_d) // 10)
            dw_g_cur_hangul = engine.GAN[(c_idx + (cur_dw_idx+1)*order_dir)%10]
            dw_j_cur_hangul = engine.JI[(j_idx + (cur_dw_idx+1)*order_dir)%12]
            dw_g_cur = engine.K2H_GAN.get(dw_g_cur_hangul, dw_g_cur_hangul)
            dw_j_cur = engine.K2H_JI.get(dw_j_cur_hangul, dw_j_cur_hangul)
            
            # [오류 방지] 루프 시작 전 변수 명확히 정의
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
                
                ss_gan = engine.get_ss(ds_kor, tc_hangul)
                ss_ji = engine.get_ss(ds_kor, tj_hangul)
                un_sung = engine.get_unsung(ds_kor, tj_hangul)
                shin_sal = engine.get_12_shinsal(yb_kor, tj_hangul)

                # 변수 선언 후 호출
                bg_col = "#E1F5FE" if ty == curr_year else "transparent"
                b_left = "1px solid #ccc" if i != 0 else "none"

                se_content += html_views.get_sewun_cell(
                    f"{ty}년", tage, ss_gan, tc, get_oh_class(tc), 
                    tj, get_oh_class(tj), ss_ji, un_sung, shin_sal, bg_col, b_left
                )

            se_html = html_views.get_sewun_layout(f"[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]", se_content)
            
            # 최종 렌더링
            st.markdown(html_views.get_final_report_box(se_html), unsafe_allow_html=True)

# ---------------------------------------------------------
    # [3번 상품] 이번 달 (월운 전용 출력)
    # ---------------------------------------------------------
    elif "3. 이번 달" in u_product:
        st.header(f"🔮 {name}님의 이번 달(월운) 분석")
        st.markdown("---")
        with st.spinner("⏳ 월운 정밀 분석 중...."):
            # 독립적 구동을 위한 최소 기초 연산
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

            yb_kor = {v: k for k, v in engine.K2H_JI.items()}.get(y_pillar[1], y_pillar[1])
            ds_kor = {v: k for k, v in engine.K2H_GAN.items()}.get(d_pillar[0], d_pillar[0])

            # [월운 연산]
            wol_gans_kor = ["기", "경", "신", "임", "계", "갑", "을", "병", "정", "무", "기", "경"]
            wol_jis_kor = ["축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해", "자"]
            wol_content = ""
            
            for i in range(12):
                tm = i + 1
                wc_kor, wj_kor = wol_gans_kor[i], wol_jis_kor[i]
                
                wc = engine.K2H_GAN.get(wc_kor, wc_kor)
                wj = engine.K2H_JI.get(wj_kor, wj_kor)
                
                # 십성 및 운성 연산 (빈값일 경우 "-" 처리)
                ss_gan = engine.get_ss(ds_kor, wc_kor) or "-"
                ss_ji = engine.get_ss(ds_kor, wj_kor) or "-"
                un_sung = engine.get_unsung(ds_kor, wj_kor) or "-"
                shin_sal = engine.get_12_shinsal(yb_kor, wj_kor) or "-"
                
                bg_col = "#E8F5E9" if tm == curr_m else "transparent"
                b_left = "1px solid #ccc" if i != 0 else "none" # i=0이 아닐 때만 좌측선
                
                # 월운 전용 셀 호출
                wol_content += html_views.get_wolun_cell(
                    tm, ss_gan, wc, get_oh_class(wc), 
                    wj, get_oh_class(wj), ss_ji, un_sung, shin_sal, bg_col, b_left
                )
            
            # 월운 전용 레이아웃 호출
            wol_html = html_views.get_wolun_layout(f"[ 월운의 흐름 ({curr_year}년도 양력기준) ]", wol_content)
            
            # 최종 렌더링 출력
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
            
            # (1) 표지 강제 렌더링
            cover_html = html_views.get_gunghap_cover(APP_VERSION, app_p_icon, name, gender, u_marital, part_p_icon, f_name, f_gender, f_marital, today_str)
            st.markdown(cover_html, unsafe_allow_html=True)

            # ==========================================================
            # 🚨 [60.0 버전 완벽 캡슐화 및 들여쓰기/변수 오류 수정 완료] 🚨
            # ==========================================================
            def extract_time(time_str):
                if "모름" in time_str: return 0, 0
                match = re.search(r'(\d{2}):(\d{2})', time_str)
                return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

            def generate_person_saju(p_name, p_gender, p_year, p_month, p_day, p_time, p_cal, p_marital, p_icon):
                # 1. 양음력 변환 및 나이 계산
                klc = KoreanLunarCalendar()
                if "음력" in p_cal:
                    is_leap = True if "윤달" in p_cal else False
                    klc.setLunarDate(int(p_year), int(p_month), int(p_day), is_leap)
                    sol_y, sol_m, sol_d = klc.solarYear, klc.solarMonth, klc.solarDay
                    lun_y, lun_m, lun_d = int(p_year), int(p_month), int(p_day)
                    leap_str = "윤달" if is_leap else "평달"
                else:
                    klc.setSolarDate(int(p_year), int(p_month), int(p_day))
                    sol_y, sol_m, sol_d = int(p_year), int(p_month), int(p_day)
                    lun_y, lun_m, lun_d = klc.lunarYear, klc.lunarMonth, klc.lunarDay
                    leap_str = "윤달" if klc.isIntercalation else "평달"

                curr_year = dt_mod.datetime.now().year
                age = curr_year - sol_y + 1

                # 2. 기초 연산
                h, m = extract_time(p_time)
                y_pillar, m_pillar, lon = engine.get_true_year_month_pillar(int(p_year), int(p_month), int(p_day), h, m)
                is_lunar_val, is_leap_val = ("음력" in p_cal), ("윤달" in p_cal)
                _, _, d_pillar = engine.get_ganji_from_date(int(p_year), int(p_month), int(p_day), is_lunar_val, is_leap_val)

                # 3. 오서둔 직접 연산
                ds_hanja = engine.K2H_GAN.get(d_pillar[0], d_pillar[0])
                if "모름" in p_time:
                    t_gan, t_ji = "", ""
                else:
                    match = re.search(r'\((.*?)\)', p_time)
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

                counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
                for c in gans + jjis:
                    if c in "甲乙寅卯": counts['목']+=1
                    elif c in "丙丁巳午": counts['화']+=1
                    elif c in "戊己辰戌丑未": counts['토']+=1
                    elif c in "庚辛申酉": counts['금']+=1
                    elif c in "壬癸亥子": counts['수']+=1

                guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 亥','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
                guiin_str = guiin_map.get(ds, '없음')

                # --- [사전 작업] 연산용 한글 기준점 명확화 (들여쓰기 완벽 복구) ---
                ys_kor = {v: k for k, v in engine.K2H_GAN.items()}.get(ys, ys)
                yb_kor = {v: k for k, v in engine.K2H_JI.items()}.get(yb, yb)
                ms_kor = {v: k for k, v in engine.K2H_GAN.items()}.get(ms, ms)
                mb_kor = {v: k for k, v in engine.K2H_JI.items()}.get(mb, mb)
                ds_kor = {v: k for k, v in engine.K2H_GAN.items()}.get(ds, ds)
                db_kor = {v: k for k, v in engine.K2H_JI.items()}.get(db, db)

                yb_han = engine.K2H_JI.get(yb_kor, yb_kor)

                # ---------------------------------------------------------
                # 3. 공망 및 삼재 연산
                # ---------------------------------------------------------
                n_gong_raw = engine.calculate_gongmang(ys_kor, yb_kor)
                i_gong_raw = engine.calculate_gongmang(ds_kor, db_kor)

                n_gong = "".join([engine.K2H_JI.get(ch, ch) for ch in (n_gong_raw if n_gong_raw else "-") if ch not in [',', ' ']])
                i_gong = "".join([engine.K2H_JI.get(ch, ch) for ch in (i_gong_raw if i_gong_raw else "-") if ch not in [',', ' ']])

                if not n_gong or n_gong == "-": n_gong = "-"
                if not i_gong or i_gong == "-": i_gong = "-"

                curr_base = (curr_year - 1984) % 60
                curr_y_ji_kor = engine.JI[curr_base % 12]
                curr_y_ji_han = engine.K2H_JI.get(curr_y_ji_kor, curr_y_ji_kor)
                
                cur_samjae = engine.get_samjae(yb_han, curr_y_ji_han)
                samjae_color = "#1A237E" if cur_samjae != "해당 없음" else "#2E7D32"

                # 4. 대운수 계산
                base_dt = dt_mod.datetime(int(p_year), int(p_month), int(p_day), 12, 0)
                adj_mins = engine.get_total_time_adjustment(base_dt)
                utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
                order_dir = 1 if (engine.GAN.index(ys_kor) % 2 == 0) == (p_gender == '남성') else -1
                calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
                direction_str = "순행" if order_dir == 1 else "역행"

                # 6. UI 데이터 준비
                sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
                lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
                time_str_fmt = f"{p_time.split('(')[0].strip()} ({hb})시" if p_time != "시간 모름" else ""

                info_h = html_views.get_info_header(p_icon, p_name, p_gender, p_marital, age, sol_str_fmt, lun_str_fmt, time_str_fmt)

                # 7. 사주 테이블 HTML 조립
                ji_rel_rows = ""
                for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                    b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                    cells = "".join([f"<td style='color:{('#1A237E' if ci==r_idx else ('#000' if engine.get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else engine.get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                    lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                    ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

                filtered_shinsals = ["<br>".join(engine.get_general_shinsal_filtered(i, gans, jjis, p_gender)[:6]) if engine.get_general_shinsal_filtered(i, gans, jjis, p_gender) else "-" for i in range(4)]
                
                gan_rel = "".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])
                gan_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds_kor, {v: k for k, v in engine.K2H_GAN.items()}.get(hs, hs))}</td><td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(ds_kor, ms_kor)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds_kor, ys_kor)}</td>"
                gan_row = f"{td_bg(hs)}{hs}</td>{td_bg(ds)}{ds}</td>{td_bg(ms)}{ms}</td>{td_bg(ys)}{ys}</td>"
                ji_row = f"{td_bg(hb)}{hb}</td>{td_bg(db)}{db}</td>{td_bg(mb)}{mb}</td>{td_bg(yb)}{yb}</td>"
                ji_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds_kor, {v: k for k, v in engine.K2H_JI.items()}.get(hb, hb))}</td><td style='border:1px solid #444;'>{engine.get_ss(ds_kor, db_kor)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds_kor, mb_kor)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds_kor, yb_kor)}</td>"
                jijanggan = "".join([f"<td style='padding:0; border:1px solid #444;'>{engine.get_jijanggan_full(ds_kor, {v: k for k, v in engine.K2H_JI.items()}.get(jjis[i], jjis[i]))}</td>" for i in range(4)])
                unsung = "".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{engine.get_unsung(ds_kor, {v: k for k, v in engine.K2H_JI.items()}.get(jjis[i], jjis[i]))}</td>" for i in range(4)])
                shinsal = "".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{engine.get_12_shinsal(yb_kor, {v: k for k, v in engine.K2H_JI.items()}.get(jjis[i], jjis[i]))}</td>" for i in range(4)])
                gen_shinsal = "".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{filtered_shinsals[i]}</td>" for i in range(4)])

                t_html = html_views.get_saju_table(info_h, gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal)
                mb_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, samjae_color, cur_samjae)

                # ---------------------------------------------------------
                # [대운 연산] 
                # ---------------------------------------------------------
                un_content = ""
                c_idx = engine.GAN.index(ms_kor) if ms_kor in engine.GAN else 0
                j_idx = engine.JI.index(mb_kor) if mb_kor in engine.JI else 0

                for i in range(10):
                    val = i*10+calc_d
                    
                    c_hangul = engine.GAN[(c_idx+(i+1)*order_dir)%10]
                    j_hangul = engine.JI[(j_idx+(i+1)*order_dir)%12]
                    
                    c = engine.K2H_GAN.get(c_hangul, c_hangul)
                    j = engine.K2H_JI.get(j_hangul, j_hangul)
                    
                    ss_gan = engine.get_ss(ds_kor, c_hangul)
                    ss_ji = engine.get_ss(ds_kor, j_hangul)
                    un_sung = engine.get_unsung(ds_kor, j_hangul)
                    shin_sal = engine.get_12_shinsal(yb_kor, j_hangul)
                    
                    bg_col = "#FFF9C4" if val <= age < val+10 else "transparent"
                    b_left = "1px solid #ccc" if i != 9 else "none"
                    
                    un_content += html_views.get_un_cell(f"{val}세", ss_gan, c, get_oh_class(c), j, get_oh_class(j), ss_ji, un_sung, shin_sal, bg_col, b_left)
                   
                un_html = html_views.get_un_layout(f"[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]", un_content)

                # [수정포인트 2] u_html 오타를 un_html로 수정하여 정상 반환되도록 조치
                return t_html, mb_html, un_html

            # --- 남명(m_)과 여명(w_) 변수 할당 로직 ---
            # [수정포인트 1] 파트너 데이터에 존재하지 않는 f_year 대신 UI에 정의된 f_y, f_m, f_d, f_t 사용
            user_data = (name, gender, b_year, b_month, b_day, b_time, u_cal, u_marital, app_p_icon)
            partner_data = (f_name, f_gender, f_y, f_m, f_d, f_t, f_cal, f_marital, part_p_icon)

            # 성별에 따라 남명(m) / 여명(w) 올바르게 매칭
            if gender == "남성" and f_gender == "여성":
                m_table_html, m_master_html, m_un_html = generate_person_saju(*user_data)
                w_table_html, w_master_html, w_un_html = generate_person_saju(*partner_data)
            elif gender == "여성" and f_gender == "남성":
                w_table_html, w_master_html, w_un_html = generate_person_saju(*user_data)
                m_table_html, m_master_html, m_un_html = generate_person_saju(*partner_data)
            else:
                m_table_html, m_master_html, m_un_html = generate_person_saju(*user_data)
                w_table_html, w_master_html, w_un_html = generate_person_saju(*partner_data)

            # (2) 남명/여명 박스 렌더링
            if 'm_table_html' in locals() and m_table_html:
                st.markdown(html_views.get_gunghap_person_box(m_table_html, m_master_html), unsafe_allow_html=True)
            if 'w_table_html' in locals() and w_table_html:
                st.markdown(html_views.get_gunghap_person_box(w_table_html, w_master_html, add_page_break=True), unsafe_allow_html=True)
            
            # (3) 대운 비교 렌더링
            if 'm_un_html' in locals() and 'w_un_html' in locals():
                m_name = name if gender == "남성" else f_name
                w_name = f_name if gender == "남성" else name
                st.markdown(html_views.get_daewun_compare_box(m_name, m_un_html, w_name, w_un_html), unsafe_allow_html=True)

            # (4) 클로징 렌더링
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
    # [11번 상품] 타 감명서 비교
    # ---------------------------------------------------------
    elif "11. 타 감" in u_product:
        st.header("⚖️ 초연 시공명리 타 감명서 1:1 비교")
        st.markdown("---")
        if not other_report: 
            st.warning("👈 사이드바에 타 감명서 원문을 입력해주세요.")
        else: 
            st.info("타 감명서 비교 로직이 작동합니다.")
