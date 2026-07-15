import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import os
import re
from google import genai
import time
import importlib
import engine
import json
with open('choyeon_db.json', 'r', encoding='utf-8') as f:
    choyeon_db = json.load(f)
import math
import pytz
import html_views
import prompts
class SafeDict(dict):
    def __missing__(self, key):
        return f"{{{key}}}"

# ==============================================================================
# 1. 초기 설정 및 공통 함수
# ==============================================================================
APP_VERSION = "Ver 60.3 (Master AI Optimized)"
st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# CSS 전역 적용
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
    # prompts.py에 SYSTEM_ROLE이 없으면 기본값을 강제로 주입하여 시스템 중단을 막습니다.
    sys_role = getattr(prompts, 'SYSTEM_ROLE', "당신은 초연 시공명리 연구소의 수석 명리학자 AI입니다. 제공된 사주 원국과 데이터를 바탕으로 내담자에게 정확하고 따뜻한 명리학적 통변을 제공하십시오.")
    return get_ai_response(sys_role, prompt_text, model_name='gemini-2.5-flash')

def extract_ganji(text):
    if not text: return ""
    return re.sub(r'[^가-힣一-龥]', '', text)

def get_oh_class(ganji):
    oh = engine.get_color(ganji)
    return f"color-{oh}" if oh != '무' else "color-무"

def td_bg(ganji):
    cls = get_oh_class(ganji)
    # CSS 클래스가 오행별 색상을 알아서 처리하며, ganji-cell로 글자 크기와 입체감을 줍니다.
    return f"<td class='{cls} ganji-cell'>"

# ==============================================================================
# 2. 사이드바 통제 센터
# ==============================================================================
with st.sidebar:
    st.markdown(f"""<div style="text-align: center;"><h1 style="font-family: 'Nanum Gothic', sans-serif; color: #000000; font-weight: 900; font-size: 20px; margin-bottom: 5px;">🏮 초연 시공명리 연구소</h1></div>""", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #555555; font-family: sans-serif; font-size: 12px;'>{APP_VERSION} Master</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<div style='font-size: 17px; font-weight: 900; color: #000000; margin-bottom: 5px; font-family: \"Nanum Gothic\", sans-serif;'>📋 분석 상품 선택</div>", unsafe_allow_html=True)
    
    u_product = st.selectbox("상품선택", [
        "1. 개인사주 (대운) 및 일진 분석", 
        "2. 올 해의 운세 (세운)", 
        "3. 이번 달의 운세 (월운)",
        "4. 재물운 특화 분석", 
        "5. 직업/직장운 특화 분석", 
        "6. 건강운 특화 분석",
        "7. 이사 및 방위", 
        "8. 연애 및 궁합운 특화 분석", 
        "9. 결혼 택일 정밀 분석", 
        "10. 출산 택일 정밀 분석", 
        "11. 타 감명서 비교 (개인)", 
        "12. 타 감명서 비교 (궁합)"
    ], label_visibility="collapsed")

    # [신청인 사주간지 역산 로직 유지]
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

    # [수정] 조건문을 더 정확한 이름 매칭으로 변경
    if "1. 개인사주" in u_product:
        run_iljin_calc = st.checkbox("🔮 일진 시공간 분석 추가 가동", value=False)
    
    if any(x in u_product for x in ["2. 올 해", "3. 이번 달", "4. 재물", "5. 직업", "6. 건강"]):
        if "4. 재물" in u_product: wealth_goal = st.text_input("고민되는 금전 문제는?", key="wealth_goal")
        elif "5. 직업" in u_product: career_goal = st.text_input("고민되는 직업 분야는?", key="career_goal")
        elif "6. 건강" in u_product: health_goal = st.text_input("관리할 건강 부위는?", key="health_goal")

    # 상대방 정보가 필요한 상품들
    if any(x in u_product for x in ["8. 연애 및 궁합운", "9. 결혼 택일", "10. 출산 택일", "12. 타 감명서 비교 (궁합)"]):
        st.markdown("---")
        with st.expander("👥 상대방 사주간지 역산", expanded=False):
            # (상대방 자동입력 로직 동일...)
            pass # (박사님 원본 로직을 여기에 그대로 두십시오)

        with st.expander("👥 상대방 기본 정보", expanded=True):
            # (상대방 기본정보 로직 동일...)
            pass 

    if "7. 이사" in u_product:
        moving_date = st.date_input("이사 희망일")
        moving_dir = st.selectbox("이사 희망 방위", ["동쪽", "서쪽", "남쪽", "북쪽", "기타"])

    # 타 감명서 원문 입력창
    if "11. 타 감명서 비교 (개인)" in u_product or "12. 타 감명서 비교 (궁합)" in u_product:
        st.markdown("---")
        other_report = st.text_area("📄 타 감명서 원문 붙여넣기", height=150, key="other_reading")

    st.markdown("---")
    if st.button("✨ [초연 시공명리 풀이 가동]", key="btn_run", use_container_width=True, type="primary"):
        st.session_state['app_running'] = True

# ==============================================================================
# 2.5 프롬프트 사전 로딩 (메인 화면 출력부 직전, app.py 내부)
# ==============================================================================

# 상품명 리스트와 딕셔너리 키를 완벽히 일치시켰습니다.
PROMPT_MAP = {
    "1. 개인사주 (대운) 및 일진 분석": prompts.PERSONAL_SAJU_PROMPT, 
    "2. 올 해의 운세 (세운)": prompts.SEWUN_PROMPT,
    "3. 이번 달의 운세 (월운)": prompts.WOLWUN_PROMPT,
    "4. 재물운 특화 분석": prompts.WEALTH_PROMPT,
    "5. 직업/직장운 특화 분석": prompts.CAREER_PROMPT,
    "6. 건강운 특화 분석": prompts.HEALTH_PROMPT,
    "7. 이사 및 방위": prompts.MOVING_DATE_PROMPT,
    "8. 연애 및 궁합운 특화 분석": prompts.GUNGHAP_ESSAY_PROMPT,
    "9. 결혼 택일 정밀 분석": prompts.WEDDING_DATE_PROMPT,
    "10. 출산 택일 정밀 분석": prompts.DELIVERY_LOOP_PROMPT,
    "11. 타 감명서 비교 (개인)": prompts.COMPARE_PROMPT,
    "12. 타 감명서 비교 (궁합)": prompts.COMPARE_PROMPT
}

# u_product를 기준으로 템플릿을 안전하게 가져옵니다.
# 만약 매핑되지 않는 상품일 경우, 시스템 오류 방지를 위해 에러 로그를 남기는 것도 좋은 방법입니다.
selected_prompt_template = PROMPT_MAP.get(u_product, prompts.PERSONAL_SAJU_PROMPT)

# ==============================================================================
# 3. 메인 화면 출력부
# ==============================================================================
if st.session_state.get('app_running', False):
    curr_dt = dt_mod.datetime.now()
    curr_year = curr_dt.year
    curr_month = curr_dt.month

    # 🚨 [핵심 우회 장치] 11번, 12번을 선택해도 1번, 7번 풀이를 먼저 타도록 내부 목표(Target)를 변경합니다.
    base_product = u_product
    is_compare_mode = False
    compare_type = ""

    if "11. 타 감명서 비교 (개인)" in u_product:
        base_product = "1. 개인사주"
        is_compare_mode = True
        compare_type = "개인"
    elif "12. 타 감명서 비교 (궁합)" in u_product:
        base_product = "7. 연애"
        is_compare_mode = True
        compare_type = "궁합"

# --------------------------------------------------------------------------
    # 🌟 [제1단계: 공통 데이터 추출부] (검수 및 최적화 완료)
    # --------------------------------------------------------------------------
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
        
    age = curr_year - sol_y + 1
    p_icon = "♂️" if gender == "남성" else "♀️"
    today_str = dt_mod.datetime.now().strftime("%Y년 %m월 %d일")
    
    def extract_time(time_str):
        if "모름" in time_str: return 0, 0
        match = re.search(r'(\d{2}):(\d{2})', time_str)
        return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

    with st.spinner("⏳ [초연 시공명리 우주 기운 분석 중....]"):
        h, m = extract_time(b_time)
        # 공통 기준 시간 설정
        base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
        
        y_pillar, m_pillar, lon = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
        is_lunar_val, is_leap_val = ("음력" in u_cal), ("윤달" in u_cal)
        _, _, d_pillar = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)
        
        ds_hanja = engine.K2H_GAN.get(d_pillar[0], d_pillar[0])
        
        if "모름" in b_time:
            t_gan, t_ji = "" , ""
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
        
        gans, jjis = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]], [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
        hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
        hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]

        # 대운수 계산 (최적화: base_dt 활용)
        total_adj = engine.get_total_time_adjustment(base_dt)
        utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=total_adj)
        order_dir = 1 if (engine.GAN.index(ys) % 2 == 0) == (gender == '남성') else -1
        calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
        direction_str = "순행" if order_dir == 1 else "역행"

    # --------------------------------------------------------------------------
    # 🌟 [제2단계: 상품별 분기부] u_product 대신 base_product 변수 적용
    # --------------------------------------------------------------------------
    if "1. 개인사주" in base_product:
        counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
        for c in gans + jjis:
            oh = engine.get_color(c)
            if oh in counts: counts[oh] += 1

        guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
        guiin_str = guiin_map.get(engine.K2H_GAN.get(ds, ds), '없음')
        
        curr_year_ji = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'][(curr_year - 1984) % 12]
        
        n_gong = engine.calculate_gongmang(ys, yb)
        i_gong = engine.calculate_gongmang(ds, db)
        n_gong = n_gong if n_gong else "-"
        i_gong = i_gong if i_gong else "-"
        
        cur_samjae = engine.get_samjae(yb, curr_year_ji)
        samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"

        sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
        lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
        time_str_fmt = f"{b_time.split('(')[0].strip()} ({hb})시" if b_time != "시간 모름" else ""

        cover_html = html_views.get_personal_cover(APP_VERSION, p_icon, name, sol_str_fmt, lun_str_fmt, time_str_fmt, today_str)
        intro_html = html_views.get_intro_html()
        info_h = html_views.get_info_header(p_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, time_str_fmt)

        table_html = html_views.generate_saju_table_data(info_h, gans, jjis, ds, gender, engine)
        master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, samjae_color, cur_samjae)

        yukchin_rule = engine.get_yukchin_rule(gender, u_marital)
        daewun_data_list = engine.get_daewun_data_list(ms, mb, ds, yb, order_dir, calc_d, age)
        un_html = html_views.generate_daewun_layout(daewun_data_list, direction_str, calc_d, get_oh_class)

        w_key = ms + mb
        i_key = ds + db
        w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
        i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
        golden_text_html = html_views.get_golden_text(name, w_val, i_val)

        ai_output_html = ""
        try:
            saju_facts = engine.get_saju_fact_sheet(
                ys, yb, ms, mb, ds, db, hs, hb, 
                name=name, age=age, gender=gender, marital=u_marital
            )
            safe_facts = SafeDict(saju_facts)
            final_prompt_text = selected_prompt_template.format_map(safe_facts)
                
            ai_result = call_gemini_api(final_prompt_text)
            st.session_state['ai_full_text'] = ai_result # R&D 비교 리포트를 위해 세션에 저장
            ai_result = ai_result.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
            
            ai_result = re.sub(r'###\s*(.*?)\n', r"<div style='font-size:21px; font-weight:900; margin:20px 0 10px 0;'>\1</div>", ai_result)
            ai_result = ai_result.replace('\n', '<p style="margin:8px 0; line-height:1.6;">')
            
            ai_output_html = html_views.get_ai_report_box(ai_result)
            
        except Exception as e:
            ai_output_html = f"<div style='color:red;'>🚨 AI 시스템 에러: {str(e)}</div>"

        closing_html = html_views.get_closing_html(name)
        st.markdown(cover_html, unsafe_allow_html=True)
            
        final_report = (
            str(table_html or "") + 
            str(master_bar_html or "") + 
            str(un_html or "") +
            str(intro_html or "") +
            str(golden_text_html or "") +
            str(ai_output_html or "") + 
            str(closing_html or "")
        )
        
        full_html = html_views.get_final_report_box(final_report)
        full_html_clean = re.sub(r'\n\s+', ' ', full_html)
        st.markdown(full_html_clean, unsafe_allow_html=True)

    elif "2. 올 해" in base_product:
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

            curr_year = dt_mod.datetime.now().year 
            
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

    elif "3. 이번 달" in base_product:
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

    elif any(x in base_product for x in ["4. 재물", "5. 직업", "6. 건강"]):
        st.header(f"🔮 {name}님의 {base_product.split('.')[1].strip()} 분석")
        st.markdown("---")
        with st.spinner(f"⏳ [{base_product.split('.')[1].strip()}] 정밀 분석 중...."):
            st.info("데이터 연동 및 AI 분석 대기 중입니다. (향후 1번 상품의 연산 로직을 기반으로 확장될 공간입니다.)")

    elif "7. 연애" in base_product:
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

    elif any(x in base_product for x in ["8. 결혼", "9. 출산", "10. 이사"]):
        st.header(f"🗓️ {name}님의 {base_product.split('.')[1].strip()}")
        st.markdown("---")
        with st.spinner("⏳ 길일 및 시공간 분석 중..."):
            st.info("명리학적 택일 분석 엔진 가동 대기 중입니다.")

    # --------------------------------------------------------------------------
    # 🌟 [제3단계: 타 감명서 비교 추가 출력부] (최종 검수본)
    # --------------------------------------------------------------------------
    if is_compare_mode:
        other_report = st.session_state.get('other_reading', "")
        
        if not other_report: 
            st.warning("👈 사이드바에 타 감명서 원문을 입력해주세요.")
        else: 
            with st.spinner("⚖️ 타 감명서 정밀 분석 및 R&D 리포트 생성 중..."):
                try:
                    # 1. 팩트 조립
                    if compare_type == "궁합":
                        fact_ref = f"- 신청인 사주: {ys}{yb}년 {ms}{mb}월 {ds}{db}일 {hs}{hb}시\n- 상대방 생년월일: {f_y}년 {f_m}월 {f_d}일\n- 궁합 분석 핵심: 체용 조화 및 기운 매트릭스 대조"
                    else:
                        fact_ref = f"- 신청인: {name} ({gender})\n- 사주 구성: {ys}{yb}년 {ms}{mb}월 {ds}{db}일 {hs}{hb}시\n- 일주/월령: {ds}{db} / {ms}{mb}"

                    saju_facts = engine.get_saju_fact_sheet(
                        ys, yb, ms, mb, ds, db, hs, hb, 
                        name=name, age=age, gender=gender, marital=u_marital,
                        other_report=other_report,
                        fact_reference=fact_ref
                    )
                    
                    saju_facts['full_content_clean'] = st.session_state.get('ai_full_text', '초연 사주풀이 선행 데이터')
                    final_prompt_text = prompts.COMPARE_PROMPT.format_map(SafeDict(saju_facts))
                    
                    # 2. AI 통변 및 정제
                    c_res = call_gemini_api(final_prompt_text)
                    c_res = c_res.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
                    
                    # HTML 스타일링
                    c_res = re.sub(r'###\s*(.*?)\n', r"<div style='font-size:21px; font-weight:900; margin:20px 0 10px 0;'>\1</div>", c_res)
                    c_res = c_res.replace('\n', '<p style="margin:8px 0; line-height:1.6;">')
                    
                    # 3. 결과 출력
                    report_2_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#555;'><h2 style='text-align:center; color:#555;'>📜 타 감명서 원문</h2><div style='font-size: 15px; line-height: 1.8;'>{other_report.replace(chr(10), '<br>')}</div></div></div>"
                    detail_report_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#2E7D32;'><h1 style='text-align:center; color:#2E7D32;'>⚖️ 1:1 상세비교 및 R&D 총평 리포트</h1><div style='margin-top:20px;'>{c_res}</div></div></div>"
                    
                    st.markdown(report_2_html + detail_report_html, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"🚨 타 감명서 비교 분석 중 오류가 발생했습니다: {e}")


