# ==============================================================================
# app.py (ver 80.0 Master - 무소음 백그라운드 스텔스 가동 및 자동 복귀)
# ==============================================================================
import streamlit as st
import streamlit.components.v1 as components
import datetime as dt_mod
from datetime import datetime
from korean_lunar_calendar import KoreanLunarCalendar
import os
import re
import time
import json
import math
import pytz
import sys
import importlib
from google import genai

import engine
import prompts
import html_views

# 💡 [영업부 호출]: 여기서 URL을 가로채어 고객/관리자 접속을 통제합니다.
# factory 모드일 때는 무사 통과하여 아래의 공장이 가동됩니다.
from pipeline_manager import run_pipeline_router
run_pipeline_router()

APP_VERSION = "ver 80.0 Master"
st.set_page_config(page_title=f"초연 시공명리 연구소 {APP_VERSION}", layout="wide")

# 🧨 [진녹색 폰트 및 선 강제 초기화 - 영구 사살] 🧨
st.markdown("""
<style>
    span[style*="darkgreen"], span[style*="#006400"], span[style*="#008000"], span[style*="17px"], span[style*="1px solid"] {
        color: #2D3748 !important; font-size: 15px !important; border: none !important; background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

if hasattr(html_views, 'get_global_css'):
    st.markdown(html_views.get_global_css(), unsafe_allow_html=True)

idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]

if 'app_running' not in st.session_state: st.session_state['app_running'] = False

@st.cache_data
def load_choyeon_db():
    file_path = 'choyeon_db.json'
    if not os.path.exists(file_path): return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception: return {}
choyeon_db = load_choyeon_db()

try: _gemini_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as _api_e: _gemini_client = None; st.error(f"🚨 Gemini API 키 오류: {_api_e}")

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
    sys_role = engine.get_master_system_prompt()
    return get_ai_response(sys_role, prompt_text, model_name='gemini-2.5-flash')

extract_ganji = engine.extract_ganji
get_oh_class = engine.get_oh_class
kst_tz = pytz.timezone('Asia/Seoul')

# ==============================================================================
# 🛡️ [공장 변수 세팅]
# ==============================================================================
if st.session_state.get('admin_proc_id'):
    st.markdown("<style>[data-testid='stSidebar'] {display: none !important;}</style>", unsafe_allow_html=True)
    selected_target_date = st.session_state.get('target_date', dt_mod.datetime.now(kst_tz).date())
    main_category = st.session_state.get('main_category', '1. 사주팔자 및 운세 풀이 (종합)')
    u_product = st.session_state.get('sub_category_1', '1-1. 사주팔자 및 운세 분석')
    if "2." in main_category: u_product = st.session_state.get('sub_category_2', '2-1. 재물운 특화 분석')
    elif "3." in main_category: u_product = st.session_state.get('sub_category_3', '3-1. 커플 연애/결혼운 (궁합) 분석')
    
    name, gender, u_marital, u_cal = st.session_state.get('u_n', '고객'), st.session_state.get('u_g', '여성'), st.session_state.get('u_m_stat', '선택'), st.session_state.get('u_c', '양력')
    b_year, b_month, b_day, b_time = st.session_state.get('s_y', 1980), st.session_state.get('s_m', 1), st.session_state.get('s_d', 1), st.session_state.get('s_t', '시간 모름')
    is_1person = not ("3-1." in u_product)
    is_2person = ("3-1." in u_product)
else:
    with st.sidebar: pass # 수동 모드 UI 생략(원본유지)

# ==============================================================================
# 3. 백그라운드 공장 스텔스 가동 (박사님 화면을 가리지 않음)
# ==============================================================================
if st.session_state.get('app_running', False):
    klc = KoreanLunarCalendar()
    b_year, b_month, b_day = st.session_state.get("s_y", 1980), st.session_state.get("s_m", 1), st.session_state.get("s_d", 1)

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
        
    curr_year, curr_m, curr_d = selected_target_date.year, selected_target_date.month, selected_target_date.day
    age = curr_year - sol_y + 1
    p_icon = "♂️" if gender == "남성" else "♀️"
    today_str = selected_target_date.strftime("%Y년 %m월 %d일")

    def extract_time(time_str):
        if "모름" in time_str: return 0, 0
        match = re.search(r'(\d{2}):(\d{2})', time_str)
        return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

    # 💡 [핵심] 관리자 모드일 때는 요란한 스피너 대신 스텔스 메시지 출력
    is_admin_mode = st.session_state.get('admin_proc_id') is not None
    spinner_msg = "⏳ 박사님의 명령에 따라 백그라운드에서 감명서를 조용히 조립하고 있습니다..." if is_admin_mode else f"⏳ [{u_product.strip()}] 시공명리 연산 및 정밀 통변 가동 중..."

    with st.spinner(spinner_msg):
        h, m = extract_time(b_time)
        is_lunar_val, is_leap_val = ("음력" in u_cal), ("윤달" in u_cal)
        try:
            g_res = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar_val, is_leap_val)
            d_pillar, m_pillar, y_pillar = g_res[2], g_res[1], g_res[0]
        except: y_pillar, m_pillar, d_pillar = "甲子", "甲子", "甲子"
        try:
            t_res = engine.get_true_year_month_pillar(int(b_year), int(b_month), int(b_day), h, m)
            if t_res and len(t_res) >= 2: y_pillar, m_pillar = t_res[0], t_res[1]
        except: pass
        
        ds_hanja = engine.K2H_GAN.get(d_pillar[0], d_pillar[0])
        t_gan, t_ji = "?", "?"
        if "모름" not in b_time:
            match = re.search(r'\((.*?)\)', b_time)
            raw_ji = match.group(1).replace('朝', '').replace('夜', '') if match else "子"
            t_ji = engine.K2H_JI.get(raw_ji, raw_ji)
            gan_arr, ji_arr = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'], ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            if ds_hanja in gan_arr and t_ji in ji_arr:
                d_idx, j_idx = gan_arr.index(ds_hanja), ji_arr.index(t_ji)
                t_gan = gan_arr[((d_idx % 5) * 2 + j_idx) % 10]
         
        gans = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]]
        jjis = [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
        hs, ds, ms, ys = gans[0], gans[1], gans[2], gans[3]
        hb, db, mb, yb = jjis[0], jjis[1], jjis[2], jjis[3]
        
        ys_idx = engine.GAN.index(ys) if ys in engine.GAN else 0
        order_dir = 1 if (ys_idx % 2 == 0) == (gender == '남성') else -1
        
        base_dt = dt_mod.datetime(int(b_year), int(b_month), int(b_day), 12, 0)
        utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=engine.get_total_time_adjustment(base_dt))
        calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
        
        counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
        for c in gans + jjis:
            oh = engine.get_color(c)
            if oh in counts: counts[oh] += 1
        
        guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 미','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
        guiin_str = guiin_map.get(ds_hanja, '없음')
        cur_samjae = engine.get_samjae(yb, engine.JI[(curr_year - 1984) % 60 % 12])
        n_gong = engine.calculate_gongmang(ys, yb) or "-"
        i_gong = engine.calculate_gongmang(ds, db) or "-"
        
        sol_str_fmt = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
        lun_str_fmt = f"{lun_y}년 {lun_m:02d}월 {lun_d:02d}일 ({leap_str})"
        time_str_fmt = f"{b_time}" if b_time != "시간 모름" else "시간 미상"
        
        report_title = "🏮 초연 시공명리 정밀 감명서"
        u_icon_str = f"{p_icon}" 
        cover_html = html_views.get_personal_cover(APP_VERSION, report_title, u_icon_str, name, sol_str_fmt, lun_str_fmt, time_str_fmt, today_str)
        info_h = html_views.get_info_header(p_icon, name, gender, u_marital, age, sol_str_fmt, lun_str_fmt, time_str_fmt)
        table_html = html_views.generate_saju_table_data(gans, jjis, ds, gender, engine)
        master_bar_html = html_views.get_master_bar(calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], guiin_str, n_gong, i_gong, "#555", cur_samjae)
        intro_html = html_views.get_intro_html()

        # 대운 연산
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
            daewun_data_list.append({
                "age_range": f"{val}~{val+9}세", "ss_gan": engine.get_ss(ds_hanja, c_hangul),
                "c_hanja": engine.K2H_GAN.get(c_hangul, c_hangul), "c_hangul": c_hangul,
                "j_hanja": engine.K2H_JI.get(j_hangul, j_hangul), "j_hangul": j_hangul,
                "ss_ji": engine.get_ss(ds_hanja, j_hangul), "un_sung": engine.get_unsung(ds_hanja, j_hangul),
                "y_shinsal": engine.get_12_shinsal(yb, j_hangul), "d_shinsal": engine.get_12_shinsal(db, j_hangul),
                "is_current": (val <= age < val + 10), "is_first": (i == 0)
            })
        un_html = html_views.generate_daewun_layout(daewun_data_list, "순행" if order_dir == 1 else "역행", calc_d, get_oh_class)

        w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{db}".strip()
        w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
        i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
        struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
        gyukgook, gyukgook_detail = engine.get_gyukgook_detailed(ds, ys, ms, hs, mb)
        golden_text_html = html_views.get_golden_text(name, w_val, i_val, struct_data[0], struct_data[1], struct_data[2], mb=mb, gyuk_name=gyukgook)
        closing_html = html_views.get_closing_html(name)            

        part_1_fact = str(info_h or "") + str(table_html or "") + str(master_bar_html or "")
        part_2_intro = str(intro_html or "")
        part_3_golden = str(golden_text_html or "")
        part_5_closing = str(closing_html or "")

        saju_fact_summary = f"- 명조: 년주({ys}{yb}), 월주({ms}{mb}), 일주({ds}{db}), 시주({hs}{hb})\n- 격국: {gyukgook_detail}\n"

        target_year_val = curr_year
        prompt_data = {
            "name": name, "age": age, "gender": gender, "marital": u_marital,
            "saju_fact_summary": saju_fact_summary, "dw_g_cur": dw_g_cur, "dw_j_cur": dw_j_cur, 
            "dw_fact_str": f"현재 {dw_g_cur}{dw_j_cur}대운 가동 중",
            "ds": ds, "db": db, "gyukgook_detail": gyukgook_detail,
            "oheng_counts_str": f"목:{counts['목']} 화:{counts['화']} 토:{counts['토']} 금:{counts['금']} 수:{counts['수']}",
            "curr_year": target_year_val, "target_year": target_year_val, "curr_m": curr_m
        }

        class SafeDict(dict):
            def __missing__(self, key): return '{' + key + '}'
        
        prompt_var_name = "프롬프트_1_1_기본"
        target_prompt = getattr(prompts, prompt_var_name, getattr(prompts, "프롬프트_1_1_기본", ""))
        formatted_prompt = target_prompt.format_map(SafeDict(prompt_data))
        
        # 💡 [AI 조련 지시사항 주입]
        ai_feedback = st.session_state.get('ai_feedback_prompt', '').strip()
        if ai_feedback:
            formatted_prompt += f"\n\n[🔥 박사님의 특별 수정 지시사항 🔥]\n{ai_feedback}\n위 지시사항을 100% 반영하여 기존과 완전히 다른 맞춤형 문구로 재생성하시오."

        raw_response = call_gemini_api(formatted_prompt)
        
        if raw_response and isinstance(raw_response, str):
            clean_raw = raw_response.replace("```html", "").replace("```markdown", "").replace("```", "").strip()
            ai_output_html = html_views.format_ai_text_to_html(clean_raw)
        else:
            ai_output_html = "<p style='padding:20px;'>분석 결과를 불러오지 못했습니다.</p>"

        def sub_marker(text, marker_name, table_code):
            pattern = r'\[\s*\*?\*?\s*' + marker_name + r'\s*\*?\*?\s*\]'
            return re.sub(pattern, table_code, text, flags=re.IGNORECASE)

        formatted_ai = sub_marker(ai_output_html, 'DAEWUN_TABLE_HERE', un_html if 'un_html' in locals() and un_html else "")
        master_comp = f"{part_1_fact}{part_2_intro}{part_3_golden}{formatted_ai}{part_5_closing}"
        final_render_html = html_views.get_final_report_box(master_comp)

        final_render_html = str(final_render_html).strip()
        final_render_html = final_render_html.replace("darkgreen", "#2D3748").replace("#006400", "#2D3748").replace("#008000", "#2D3748")
        final_render_html = final_render_html.replace("17px", "15px").replace("1px solid", "0px solid")

    # =========================================================================
    # 📦 [공장 생산 완료] ➔ 스텔스 모드로 즉시 admin 복귀 (서랍장 오픈)
    # =========================================================================
    if is_admin_mode:
        gid = st.session_state['admin_proc_id']
        st.session_state[f'html_{gid}'] = final_render_html
        st.session_state['app_running'] = False
        
        # 화면에 HTML을 출력하지 않고, 즉시 관리자 패널(mode=admin)로 자동 복귀!
        try: st.query_params["mode"] = "admin"
        except: st.experimental_set_query_params(mode="admin")
        st.rerun()
    else:
        # 박사님 단독 수동 연구 모드일 때는 정상적으로 화면 출력
        safe_cover = re.sub(r'\n\s+', '\n', cover_html)
        st.markdown(safe_cover, unsafe_allow_html=True)
        st.markdown(final_render_html, unsafe_allow_html=True)
