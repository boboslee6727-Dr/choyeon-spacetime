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
APP_VERSION = "ver 60.0"
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
    u_product = st.selectbox("상품선택", ["1. 개인사주 및 일진 분석", "2. 타 감명서 비교", "3. 궁합 및 출산 택일"], label_visibility="collapsed")

    # ---------------------------------------------------------
    # 1. 신청인 사주간지 역산 (최종 검수본)
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
                
                if len(_ry) == 2 and len(_rm) == 2 and len(_rd) == 2:
                    ry_h = engine.K2H_GAN.get(_ry[0], _ry[0]) + engine.K2H_JI.get(_ry[1], _ry[1])
                    rm_h = engine.K2H_GAN.get(_rm[0], _rm[0]) + engine.K2H_JI.get(_rm[1], _rm[1])
                    rd_h = engine.K2H_GAN.get(_rd[0], _rd[0]) + engine.K2H_JI.get(_rd[1], _rd[1])
                    
                    is_lunar = ("음력" in st.session_state.get("u_c", "양력"))
                    y, m, d = engine.find_solar_date_from_ganji(ry_h, rm_h, rd_h, is_lunar=is_lunar)
                    
                    if y:
                        # 생년월일 세션 업데이트
                        st.session_state['s_y_input'] = y
                        st.session_state['s_m_input'] = m
                        st.session_state['s_d_input'] = d
                        
                        # 태어난 시간 처리 및 위젯 강제 업데이트
                        if rt and len(extract_ganji(rt)) == 2:
                            ji_char = extract_ganji(rt)[-1]
                            rt_h = engine.K2H_JI.get(ji_char, ji_char)
                            
                            time_map = {'자':'00:30 ~ 01:29 (朝子)시', '子':'00:30 ~ 01:29 (朝子)시', '축':'01:30 ~ 03:29 (丑)시', '丑':'01:30 ~ 03:29 (丑)시', '인':'03:30 ~ 05:29 (寅)시', '寅':'03:30 ~ 05:29 (寅)시', '묘':'05:30 ~ 07:29 (卯)시', '卯':'05:30 ~ 07:29 (卯)시', '진':'07:30 ~ 09:29 (辰)시', '辰':'07:30 ~ 09:29 (辰)시', '사':'09:30 ~ 11:29 (巳)시', '巳':'09:30 ~ 11:29 (巳)시', '오':'11:30 ~ 13:29 (午)시', '午':'11:30 ~ 13:29 (午)시', '미':'13:30 ~ 15:29 (未)시', '未':'13:30 ~ 15:29 (未)시', '신':'15:30 ~ 17:29 (申)시', '申':'15:30 ~ 17:29 (申)시', '유':'17:30 ~ 19:29 (酉)시', '酉':'17:30 ~ 19:29 (酉)시', '술':'19:30 ~ 21:29 (戌)시', '戌':'19:30 ~ 21:29 (戌)시', '해':'21:30 ~ 23:29 (亥)시', '亥':'21:30 ~ 23:29 (亥)시'}
                            found_time = time_map.get(rt_h, "시간 모름")
                            
                            # [핵심] 인덱스와 함께 위젯 키(s_t_input)를 갱신
                            st.session_state['s_t_idx'] = idx_list.index(found_time) if found_time in idx_list else 0
                            st.session_state['s_t_input'] = found_time
                        else:
                            st.session_state['s_t_idx'] = 0
                            st.session_state['s_t_input'] = idx_list[0] if idx_list else "시간 모름"
                            
                        st.session_state['rev_success_msg'] = f"✅ 양력: {y}년 {m}월 {d}일 입력 완료!"
                        st.rerun()
                    else:
                        st.error("일치하는 간지 날짜를 찾을 수 없습니다.")
                else:
                    st.warning("년, 월, 일 간지는 반드시 2글자씩 입력해야 합니다.")

    if st.session_state.get('rev_success_msg'):
        st.success(st.session_state['rev_success_msg'])
        st.session_state['rev_success_msg'] = ""
    # ---------------------------------------------------------
    # 2. 신청인 기본 정보 (위젯과 세션의 강제 연결)
    # ---------------------------------------------------------
    with st.expander("👤 신청인 기본 정보", expanded=True):
        name = st.text_input("이름", value="", placeholder="홍길동", key="u_n")
        gender = st.selectbox("성별", ["남성", "여성"], key="u_g")
        u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
        u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")
        
        col_y, col_m, col_d = st.columns(3)
        
        # [수정] value에 session_state 값을 강제 주입하여 위젯 갱신
        b_year = col_y.number_input("년도", 1900, 2050, value=st.session_state.get('s_y_input', 1980), key="s_y_input")
        b_month = col_m.number_input("월", 1, 12, value=st.session_state.get('s_m_input', 1), key="s_m_input")
        b_day = col_d.number_input("일", 1, 31, value=st.session_state.get('s_d_input', 1), key="s_d_input")
        
        # [수정] selectbox 괄호 오류 수정 및 인덱스 강제 지정
        b_time = st.selectbox("태어난 시간", options=idx_list, index=st.session_state.get('s_t_idx', 0), key="s_t_input")

    other_report = ""
    f_name, f_gender, f_marital, f_cal = "", "여성", "미혼", "양력"
    f_y, f_m, f_d = 2000, 1, 1
    f_t = "시간 모름"
    run_delivery_calc = False

    if u_product == "1. 개인사주 및 일진 분석":
        run_iljin_calc = st.checkbox("🔮 일진 시공간 분석 추가 가동", value=False)

    elif u_product == "2. 타 감명서 비교":
        other_report = st.text_area("📄 타 감명서 원문 붙여넣기", height=150, key="other_reading")

    elif u_product == "3. 궁합 및 출산 택일":
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
                
                if len(_p_ry) == 2 and len(_p_rm) == 2 and len(_p_rd) == 2:
                    p_ry_h = engine.K2H_GAN.get(_p_ry[0], _p_ry[0]) + engine.K2H_JI.get(_p_ry[1], _p_ry[1])
                    p_rm_h = engine.K2H_GAN.get(_p_rm[0], _p_rm[0]) + engine.K2H_JI.get(_p_rm[1], _p_rm[1])
                    p_rd_h = engine.K2H_GAN.get(_p_rd[0], _p_rd[0]) + engine.K2H_JI.get(_p_rd[1], _p_rd[1])
                    
                    is_lunar_p = ("음력" in st.session_state.get("f_c", "양력"))
                    y_p, m_p, d_p = engine.find_solar_date_from_ganji(p_ry_h, p_rm_h, p_rd_h, is_lunar=is_lunar_p)
                    
                    if y_p:
                        st.session_state['p_y_input'] = y_p
                        st.session_state['p_m_input'] = m_p
                        st.session_state['p_d_input'] = d_p
                        
                        if p_rt and len(extract_ganji(p_rt)) == 2:
                            ji_char_p = extract_ganji(p_rt)[-1]
                            p_rt_h = engine.K2H_JI.get(ji_char_p, ji_char_p)
                            time_map = {'축':'01:30 ~ 03:29 (丑)시', '丑':'01:30 ~ 03:29 (丑)시', '인':'03:30 ~ 05:29 (寅)시', '寅':'03:30 ~ 05:29 (寅)시', '묘':'05:30 ~ 07:29 (卯)시', '卯':'05:30 ~ 07:29 (卯)시', '진':'07:30 ~ 09:29 (辰)시', '辰':'07:30 ~ 09:29 (辰)시', '사':'09:30 ~ 11:29 (巳)시', '巳':'09:30 ~ 11:29 (巳)시', '오':'11:30 ~ 13:29 (午)시', '午':'11:30 ~ 13:29 (午)시', '미':'13:30 ~ 15:29 (未)시', '未':'13:30 ~ 15:29 (未)시', '신':'15:30 ~ 17:29 (申)시', '申':'15:30 ~ 17:29 (申)시', '유':'17:30 ~ 19:29 (酉)시', '酉':'17:30 ~ 19:29 (酉)시', '술':'19:30 ~ 21:29 (戌)시', '戌':'19:30 ~ 21:29 (戌)시', '해':'21:30 ~ 23:29 (亥)시', '亥':'21:30 ~ 23:29 (亥)시'}
                            found_time = time_map.get(p_rt_h, "시간 모름")
                            
                            # [추가/수정] 인덱스 저장 및 위젯 키와 연결
                            st.session_state['p_t_idx'] = idx_list.index(found_time) if found_time in idx_list else 0
                            st.session_state['p_t_input'] = found_time 
                        else:
                            st.session_state['p_t_idx'] = 0
                            
                        st.session_state['rev_partner_success_msg'] = f"✅ 상대방 양력: {y_p}년 {m_p}월 {d_p}일 입력 완료!"
                        st.rerun()
                    else:
                        st.error("일치하는 간지 날짜를 찾을 수 없습니다.")
                else:
                    st.warning("상대방 년, 월, 일 간지는 반드시 2글자씩 입력해야 합니다.")

            if st.session_state.get('rev_partner_success_msg'):
                st.success(st.session_state['rev_partner_success_msg'])
                st.session_state['rev_partner_success_msg'] = ""

        with st.expander("👥 상대방 기본 정보", expanded=True):
            f_name = st.text_input("상대방 이름", value="", placeholder="이영희", key="f_n")
            f_gender = st.selectbox("상대방 성별", ["여성", "남성"], key="f_g")
            f_marital = st.selectbox("상대방 혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="f_m_stat")
            f_cal = st.selectbox("상대방 달력", ["양력", "음력(평달)", "음력(윤달)"], key="f_c")
            
            p_col1, p_col2, p_col3 = st.columns(3)
            
            # [수정] 위젯의 key를 세션 저장 키와 일치시키고 value를 강제 지정
            f_y = p_col1.number_input("년도(상대)", 1900, 2050, value=st.session_state.get('p_y_input', 1980), key="p_y_input")
            f_m = p_col2.number_input("월(상대)", 1, 12, value=st.session_state.get('p_m_input', 1), key="p_m_input")
            f_d = p_col3.number_input("일(상대)", 1, 31, value=st.session_state.get('p_d_input', 1), key="p_d_input")
            
            # 상대방 시간 선택 연동 준비
            current_p_time_val = st.session_state.get('p_t_val', "시간 모름")
            try:
                p_t_index = idx_list.index(current_p_time_val)
            except ValueError:
                p_t_index = 0
            f_t = st.selectbox("태어난 시간(상대)", options=idx_list, index=st.session_state.get('p_t_idx', 0), 
                key="p_t_input")
            
        st.markdown("<br>", unsafe_allow_html=True)
        run_delivery_calc = st.checkbox("👶 출산택일 정밀 분석 추가 가동", value=False)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. 풀이 가동 버튼 (키를 동적으로 생성)
    run_key = f"btn_run_{u_product.replace(' ', '_')}"
    btn_run = st.button("✨ [초연 시공명리 풀이 가동]", key=run_key, use_container_width=True, type="primary")

    # 2. 인쇄 버튼 (여기도 키를 동적으로 생성하여 중복 방지)
    print_key = f"btn_print_{u_product.replace(' ', '_')}"
    if st.button("🖨️ 풀이 결과 인쇄 / PDF 저장", key=print_key, use_container_width=True):
        # 자바스크립트를 보다 확실하게 실행하기 위한 구조
        js_code = """
        <script>
            window.parent.print();
        </script>
        """
        components.html(js_code, height=0)
        # 인쇄 버튼이 눌렸음을 사용자에게 알림
        st.info("인쇄 창을 호출했습니다. PDF 저장 옵션을 선택해 주세요.")
# ==============================================================================
# 3. 메인 화면 출력부
# ==============================================================================
if btn_run:
    if u_product == "1. 개인사주 및 일진 분석":
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
            h, m = extract_time(b_time)
            y_pillar, m_pillar, lon = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
            
            is_lunar_val = ("음력" in u_cal)
            is_leap_val = ("윤달" in u_cal)
            _, _, d_pillar = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)
            t_gan, t_ji = engine.get_time_ganji(d_pillar[0], b_time)

            gans = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]]
            jjis = [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
            hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
            hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]

            counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
            for c in gans + jjis:
                if c in "甲乙寅卯": counts['목']+=1
                elif c in "丙丁巳午": counts['화']+=1
                elif c in "戊己辰戌丑未": counts['토']+=1
                elif c in "庚辛申酉": counts['금']+=1
                elif c in "壬癸亥子": counts['수']+=1

            guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
            guiin_str = guiin_map.get(ds, '없음')
            n_gong = engine.calculate_gongmang(ys, yb)
            i_gong = engine.calculate_gongmang(ds, db)
            cur_samjae = engine.get_samjae(yb, db)
            samjae_color = "#1A237E" if cur_samjae != "해당 없음" else "#2E7D32"

            base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
            adj_mins = engine.get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            order_dir = 1 if (engine.GAN.index(ys)%2==0) == (gender=='남성') else -1
            calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
            direction_str = "순행" if order_dir == 1 else "역행"

            sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
            lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
            time_str_fmt = f"{b_time.split('(')[0].strip()} ({hb})시" if b_time != "시간 모름" else ""

            # ---------------------------------------------------------
            # HTML 렌더링 호출부 (html_views.py 이용)
            # ---------------------------------------------------------
            cover_html = html_views.get_personal_cover(APP_VERSION, p_icon, name, sol_str_fmt, lun_str_fmt, time_str_fmt, today_str)
            intro_html = html_views.get_intro_html()
            info_h = html_views.get_info_header(p_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, time_str_fmt)

            # 사주 테이블 행(Rows) 문자열 조립
            ji_rel_rows = ""
            for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                cells = "".join([f"<td style='color:{('#1A237E' if ci==r_idx else ('#000' if engine.get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else engine.get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

            filtered_shinsals = ["<br>".join(engine.get_general_shinsal_filtered(i, gans, jjis, gender)[:6]) if engine.get_general_shinsal_filtered(i, gans, jjis, gender) else "-" for i in range(4)]
            
            gan_rel = "".join([f"<td style='border:1px solid #444;'>{engine.get_gan_rel_all(i, gans)}</td>" for i in range(4)])
            gan_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#1A237E; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{engine.get_ss(ds,ms)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds,ys)}</td>"
            gan_row = f"{td_bg(hs)}{hs}</td>{td_bg(ds)}{ds}</td>{td_bg(ms)}{ms}</td>{td_bg(ys)}{ys}</td>"
            ji_row = f"{td_bg(hb)}{hb}</td>{td_bg(db)}{db}</td>{td_bg(mb)}{mb}</td>{td_bg(yb)}{yb}</td>"
            ji_ss = f"<td style='border:1px solid #444;'>{engine.get_ss(ds,hb)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds,db)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds,mb)}</td><td style='border:1px solid #444;'>{engine.get_ss(ds,yb)}</td>"
            jijanggan = "".join([f"<td style='padding:0; border:1px solid #444;'>{engine.get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])
            unsung = "".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{engine.get_unsung(ds, jjis[i])}</td>" for i in range(4)])
            shinsal = "".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{engine.get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])
            gen_shinsal = "".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{filtered_shinsals[i]}</td>" for i in range(4)])

            table_html = html_views.get_saju_table(info_h, gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal)
            master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, samjae_color, cur_samjae)

            # 대운 연산
            un_content = ""
            for i in range(10):
                val = i*10+calc_d
                c = engine.GAN[(engine.GAN.index(ms)+(i+1)*order_dir)%10] if ms in engine.GAN else "-"
                j = engine.JI[(engine.JI.index(mb)+(i+1)*order_dir)%12] if mb in engine.JI else "-"
                bg_col = "#FFF9C4" if val <= age < val+10 else "transparent"
                b_left = "1px solid #ccc" if i != 9 else "none"
                un_content += html_views.get_un_cell(f"{val}세", engine.get_ss(ds,c), c, get_oh_class(c), j, get_oh_class(j), engine.get_ss(ds,j), engine.get_unsung(ds,j), engine.get_12_shinsal(yb, j), bg_col, b_left)
            un_html = html_views.get_un_layout(f"[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]", un_content)

            # 세운 연산
            cur_dw_idx = max(0, (age - calc_d) // 10)
            dw_g_cur = engine.GAN[(engine.GAN.index(ms) + (cur_dw_idx+1)*order_dir)%10] if ms in engine.GAN else "-"
            dw_j_cur = engine.JI[(engine.JI.index(mb) + (cur_dw_idx+1)*order_dir)%12] if mb in engine.JI else "-"
            current_daewun_age = cur_dw_idx * 10 + calc_d
            start_year = sol_y + current_daewun_age - 1
            se_content = ""
            for i in range(10):
                ty = start_year + i
                tage = current_daewun_age + i
                base = (ty - 1984) % 60
                tc, tj = engine.GAN[base % 10], engine.JI[base % 12]
                bg_col = "#E1F5FE" if ty == curr_year else "transparent"
                b_left = "1px solid #ccc" if i != 9 else "none"
                se_content += html_views.get_un_cell(f"{ty}년<br>({tage}세)", engine.get_ss(ds,tc), tc, get_oh_class(tc), tj, get_oh_class(tj), engine.get_ss(ds,tj), engine.get_unsung(ds,tj), engine.get_12_shinsal(yb, tj), bg_col, b_left)
            se_html = html_views.get_un_layout(f"[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]", se_content)

            # 월운 연산
            wol_gans = ["己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚"]
            wol_jis = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]
            wol_content = ""
            for i in range(12):
                tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
                bg_col = "#E8F5E9" if tm == curr_m else "transparent"
                b_left = "1px solid #ccc" if i != 11 else "none"
                wol_content += html_views.get_un_cell(f"{tm}월", engine.get_ss(ds,tc), tc, get_oh_class(tc), tj, get_oh_class(tj), engine.get_ss(ds,tj), engine.get_unsung(ds,tj), engine.get_12_shinsal(yb, tj), bg_col, b_left)
            wol_html = html_views.get_un_layout(f"[ 월운의 흐름 ({curr_year}년도 양력기준) ]", wol_content)

            gunghap_cover = html_views.get_gunghap_cover(APP_VERSION, p_icon, name, gender, u_marital, part_icon, f_name, f_gender, f_marital, today_str)
            st.markdown(gunghap_cover, unsafe_allow_html=True)

            # AI 통변
            ai_output_html = ""
            try:
                # 인사말을 원천 봉쇄하는 프롬프트 지시사항 추가
                fact_sheet = prompts.PERSONAL_SAJU_PROMPT.format(
                    name=name, gender=gender, ilgan=d_pillar[0], ilju=d_pillar, wolryeong=m_pillar, 
                    jijanggan_info="엔진 데이터 연동", missing_and_gongmang="엔진 데이터 연동", 
                    shinsal_info="엔진 데이터 연동", vault_info="엔진 데이터 연동"
                )
                fact_sheet += "\n\n[지시사항] 서두의 인사말이나 맺음말은 절대 작성하지 말고, 오직 사주 분석 내용만 바로 작성해 주십시오."
                
                ai_result = call_gemini_api(fact_sheet)
                
                # 혹시 모를 인사말 잔재 제거 (보조 수단)
                ai_result = re.sub(r"^(안녕하세요|반갑습니다|감사합니다).+?\.", "", ai_result, flags=re.MULTILINE).strip()
                
                # html_views.py의 함수 호출로 변경
                ai_output_html = html_views.get_ai_report_box(ai_result)
            except Exception as e:
                ai_output_html = f"<div style='color:red;'>🚨 통변 생성 중 오류가 발생했습니다: {e}</div>"

            # 맺음말은 html_views.py에서 가져옴
            closing_html = html_views.get_closing_html(name)
            
            # 최종 렌더링
            st.markdown(cover_html, unsafe_allow_html=True)
            st.markdown(html_views.get_combined_report_box(intro_html + table_html + master_bar_html + un_html + se_html + wol_html + ai_output_html + closing_html), unsafe_allow_html=True)

    elif u_product == "2. 타 감명서 비교":
        st.header("⚖️ 초연 시공명리 타 감명서 1:1 비교")
        st.markdown("---")
        if not other_report: st.warning("👈 사이드바에 타 감명서 원문을 입력해주세요.")
        else: st.info("타 감명서 비교 로직이 작동합니다.")

    elif u_product == "3. 궁합 및 출산 택일":
        st.header(f"💕 {name}님과 {f_name}님의 초연 궁합")
        st.markdown("---")
        with st.spinner("⏳궁합 풀이 데이터 연산 중..."):
            
            app_p_icon, part_p_icon = ("♂️" if gender == "남성" else "♀️"), ("♂️" if f_gender == "남성" else "♀️")
            today_str = dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
          
        # ---------------------------------------------------------
        # 3. 궁합/출산택일 풀이 가동 (책임지고 수정한 전체 블록)
        # ---------------------------------------------------------
        if st.button("✨ [초연 시공명리 풀이 가동]", key="btn_run", use_container_width=True, type="primary"):
            
            # 1. 엔진 데이터 연산
            results = engine.calculate_gunghap(s_y, s_m, s_d, s_t, f_y, f_m, f_d, f_t)
            
            # 데이터 개수 검증 (최소 22개 항목 확보)
            if results and len(results) >= 22:
                
                # 2. 표지 출력 (아이콘 변수 적용)
                cover_html = html_views.get_gunghap_cover(APP_VERSION, app_p_icon, name, gender, u_marital, part_p_icon, f_name, f_gender, f_marital, today_str)
                st.markdown(cover_html, unsafe_allow_html=True)
                
                # 3. 데이터 분리 (박사님 작성 코드 유지)
                (m_info_h, gan_rel_m, gan_ss_m, gan_row_m, ji_row_m, ji_ss_m, 
                 jijanggan_m, m_ji_rel_rows, unsung_m, shinsal_m, gen_shinsal_m) = results[0:11]
                
                (w_info_h, gan_rel_w, gan_ss_w, gan_row_w, ji_row_w, ji_ss_w, 
                 jijanggan_w, w_ji_rel_rows, unsung_w, shinsal_w, gen_shinsal_w) = results[11:22]

                # 4. 남명 테이블 및 마스터바
                m_table_html = html_views.get_saju_table(
                    m_info_h, gan_rel_m, gan_ss_m, gan_row_m, ji_row_m, ji_ss_m, 
                    jijanggan_m, m_ji_rel_rows, unsung_m, shinsal_m, gen_shinsal_m
                )
                m_master_html = html_views.get_master_bar(
                    calc_d_m, m_counts['목'], m_counts['화'], m_counts['토'], m_counts['금'], 
                    m_counts['수'], guiin_map.get(m_ds, '없음'), engine.calculate_gongmang(m_ys, m_yb), 
                    engine.calculate_gongmang(m_ds, m_db), m_samjae_color, engine.get_samjae(m_yb, m_db)
                )
                st.markdown(html_views.get_gunghap_person_box(m_table_html, m_master_html), unsafe_allow_html=True)
                    
                # 5. 여명 테이블 및 마스터바
                w_table_html = html_views.get_saju_table(
                    w_info_h, gan_rel_w, gan_ss_w, gan_row_w, ji_row_w, ji_ss_w, 
                    jijanggan_w, w_ji_rel_rows, unsung_w, shinsal_w, gen_shinsal_w
                )
                w_master_html = html_views.get_master_bar(
                    calc_d_w, w_counts['목'], w_counts['화'], w_counts['토'], w_counts['금'], 
                    w_counts['수'], guiin_map.get(w_ds, '없음'), engine.calculate_gongmang(w_ys, w_yb), 
                    engine.calculate_gongmang(w_ds, w_db), w_samjae_color, engine.get_samjae(w_yb, w_db)
                )
                st.markdown(html_views.get_gunghap_person_box(w_table_html, w_master_html, add_page_break=True), unsafe_allow_html=True)

                # 6. AI 통변 및 맺음말
                ai_content = engine.get_gunghap_report(results)
                st.markdown(html_views.get_ai_report_box(ai_content), unsafe_allow_html=True)
                st.markdown(html_views.get_gunghap_closing(), unsafe_allow_html=True)
            else:
                st.error("데이터 연산 중 오류가 발생했습니다. 입력 정보를 확인해 주십시오.")
