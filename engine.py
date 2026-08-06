# ==============================================================================
# 🏮 초연 시공명리학 (Choyeon Spacetime Saju) - ver 7.1 타임머신 연산 코어 엔진
# ==============================================================================
# [엔진 핵심 모듈 명세 - 논리적 6대 섹션 체계]
# 섹션 1. 시스템 변수 및 기초 상수 정의
# 섹션 2. 핵심 사주 역산 및 만세력 로직 (-30분 동경시차 및 Ephem 절기 연산)
# 섹션 3. 명리 기초 연산 로직 (오행, 십성, 지장간, 합충형파해, 12운성, 듀얼 12신살, 격국, 공망 등)
# 섹션 4. 특수 파동 및 묘고 정밀 연산 로직 (인사신/축술미 삼형살 & 수·화·금·목고 묘고 정밀 연산)
# 섹션 5. 운세 풀이 및 체용(體用) 5x5 확장 로직 (포태법, 연령/성별/혼인 지침, 체용 매트릭스, 팩트 시트)
# 섹션 6. 궁합 및 택일(결혼/출산/방위) 정밀 연산 로직
# ==============================================================================

import streamlit as st
import math
import datetime as dt_mod
from datetime import datetime
import pytz
import ephem
import re
from korean_lunar_calendar import KoreanLunarCalendar

# ==============================================================================
# 섹션 1. 시스템 변수 및 기초 상수 정의
# ==============================================================================
K2H_GAN = {
    '갑':'甲', '甲':'甲', '을':'乙', '乙':'乙', '병':'丙', '丙':'丙', 
    '정':'丁', '丁':'丁', '무':'戊', '戊':'戊', '기':'己', '己':'己', 
    '경':'庚', '庚':'庚', '신':'辛', '辛':'辛', '임':'壬', '壬':'壬', '계':'癸', '癸':'癸'
}
K2H_JI = {
    '자':'子', '子':'子', '축':'丑', '丑':'丑', '인':'寅', '寅':'寅', 
    '묘':'卯', '卯':'卯', '진':'辰', '辰':'辰', '사':'巳', '巳':'巳', 
    '오':'午', '午':'午', '미':'未', '未':'未', '신':'申', '申':'申', 
    '유':'酉', '酉':'酉', '술':'戌', '戌':'戌', '해':'亥', '亥':'亥'
}

GAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI  = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

JIJANGGAN = {
    '子': ['壬', '-', '癸'], '丑': ['癸', '辛', '己'], '寅': ['戊', '丙', '甲'], 
    '卯': ['甲', '-', '乙'], '辰': ['乙', '癸', '戊'], '巳': ['戊', '庚', '丙'], 
    '午': ['丙', '己', '丁'], '未': ['丁', '乙', '己'], '申': ['戊', '壬', '庚'], 
    '酉': ['庚', '-', '辛'], '戌': ['辛', '丁', '戊'], '亥': ['戊', '甲', '壬'] 
}

def _to_hanja(char):
    """한글/한자 구분 없이 무조건 정통 한자 1글자로 완벽 변환"""
    if not char or char in ["?", " ", "-"]: return ""
    char = str(char).strip()
    return K2H_GAN.get(char, K2H_JI.get(char, char))

# ==============================================================================
# 섹션 2. 핵심 사주 역산 및 만세력 로직
# ==============================================================================
def get_total_time_adjustment(dt):
    adj = -30
    if dt_mod.datetime(1954, 3, 21) <= dt <= dt_mod.datetime(1961, 8, 9, 23, 59): adj = 0
    si = [(dt_mod.datetime(1948,5,31), dt_mod.datetime(1948,9,22)), (dt_mod.datetime(1949,3,31), dt_mod.datetime(1949,9,30)), (dt_mod.datetime(1950,4,1), dt_mod.datetime(1950,9,10)), (dt_mod.datetime(1951,5,6), dt_mod.datetime(1951,9,9)), (dt_mod.datetime(1954,3,21), dt_mod.datetime(1954,5,5)), (dt_mod.datetime(1955,4,6), dt_mod.datetime(1955,9,22)), (dt_mod.datetime(1956,5,20), dt_mod.datetime(1956,9,30)), (dt_mod.datetime(1957,5,5), dt_mod.datetime(1957,9,22)), (dt_mod.datetime(1958,5,4), dt_mod.datetime(1958,9,21)), (dt_mod.datetime(1959,5,4), dt_mod.datetime(1959,9,20)), (dt_mod.datetime(1960,5,1), dt_mod.datetime(1960,9,18)), (dt_mod.datetime(1987,5,10,2), dt_mod.datetime(1987,10,11,3)), (dt_mod.datetime(1988,5,8,2), dt_mod.datetime(1988,10,9,3))]
    for s, e in si:
        if s <= dt <= e: adj -= 60; break
    return adj

def extract_ganji(text):
    g = [c for c in text if c in "甲乙丙丁戊己庚辛壬癸갑을병정무기경신임계"]
    j = [c for c in text if c in "子丑寅卯辰巳午未申酉戌亥자축인묘진사오미신유술해"]
    return (g[0] if g else "?") + (j[0] if j else "?")

def extract_pure_ganji(cell_0, cell_1):
    raw_s = str(cell_0[0] if isinstance(cell_0, (list, tuple)) else cell_0)
    raw_b = str(cell_1[1] if isinstance(cell_1, (list, tuple)) and len(cell_1) > 1 else (cell_1[0] if isinstance(cell_1, (list, tuple)) else cell_1))
    s = re.sub(r'[^一-龥]', '', raw_s)
    b = re.sub(r'[^一-龥]', '', raw_b)
    return (s[0] if s else ""), (b[0] if b else "")

def get_true_year_month_pillar(year, month, day, hour, minute):
    kst = pytz.timezone('Asia/Seoul')
    dt_kst = kst.localize(datetime(year, month, day, hour, minute))
    dt_utc = dt_kst.astimezone(pytz.utc)
    
    sun = ephem.Sun()
    sun.compute(dt_utc)
    lon = math.degrees(ephem.Ecliptic(sun).lon) % 360.0
    
    actual_year = year
    if month <= 2 and lon < 315.0:
        actual_year -= 1
        
    year_idx = (actual_year - 1984) % 60
    
    y_gan_kor = GAN[year_idx % 10]
    y_ji_kor = JI[year_idx % 12]
    
    if 315 <= lon < 345: m_ji_idx = 2    # 寅월
    elif 345 <= lon or lon < 15: m_ji_idx = 3  # 卯월
    elif 15 <= lon < 45: m_ji_idx = 4    # 辰월
    elif 45 <= lon < 75: m_ji_idx = 5    # 巳월
    elif 75 <= lon < 105: m_ji_idx = 6   # 午월
    elif 105 <= lon < 135: m_ji_idx = 7  # 未월
    elif 135 <= lon < 165: m_ji_idx = 8  # 申월
    elif 165 <= lon < 195: m_ji_idx = 9  # 酉월
    elif 195 <= lon < 225: m_ji_idx = 10 # 戌월
    elif 225 <= lon < 255: m_ji_idx = 11 # 亥월
    elif 255 <= lon < 285: m_ji_idx = 0  # 子월
    elif 285 <= lon < 315: m_ji_idx = 1  # 丑월
    
    y_gan_idx = year_idx % 10
    start_month_gan_idx = ((y_gan_idx % 5) * 2 + 2) % 10
    m_offset = (m_ji_idx - 2) % 12
    m_gan_kor = GAN[(start_month_gan_idx + m_offset) % 10]
    m_ji_kor = JI[m_ji_idx]
    
    y_pillar = K2H_GAN[y_gan_kor] + K2H_JI[y_ji_kor]
    m_pillar = K2H_GAN[m_gan_kor] + K2H_JI[m_ji_kor]
    
    return y_pillar, m_pillar, lon

def find_solar_date_from_ganji(y_ganji, m_ganji, d_ganji, is_lunar=False):
    klc = KoreanLunarCalendar()
    for y in range(2036, 1919, -1):
        for m in range(12, 0, -1):
            for d in range(31, 0, -1):
                try:
                    if is_lunar:
                        if not klc.setLunarDate(y, m, d, False): continue
                    else:
                        if not klc.setSolarDate(y, m, d): continue
                    
                    gj = klc.getChineseGapJaString().split()
                    if len(gj) >= 3:
                        if gj[0][:2] == y_ganji and gj[1][:2] == m_ganji and gj[2][:2] == d_ganji:
                            return klc.solarYear, klc.solarMonth, klc.solarDay
                except: continue
    return None, None, None

def get_ganji_from_date(y, m, d, is_lunar=False, is_leap=False):
    klc = KoreanLunarCalendar()
    if is_lunar:
        if not klc.setLunarDate(y, m, d, is_leap): return "?", "?", "?"
    else:
        if not klc.setSolarDate(y, m, d): return "?", "?", "?"
    
    gapja_str = klc.getChineseGapJaString()
    parts = gapja_str.split()
    
    if len(parts) < 3: return "?", "?", "?"
    return parts[0][:2], parts[1][:2], parts[2][:2]

def get_time_ganji(day_gan, time_str, dt_obj=None):
    if "시간 모름" in time_str: return "?", "?"
    if dt_obj:
        adj_mins = get_total_time_adjustment(dt_obj)
        dt_obj += dt_mod.timedelta(minutes=adj_mins)
    
    target_ji, t_idx = "子", 0
    if "朝子" in time_str or "夜子" in time_str: target_ji, t_idx = "子", 0
    else:
        for j in list(JI):
            if j in time_str: target_ji, t_idx = j, list(JI).index(j); break
    start_gan_idx = {"甲":0,"己":0,"乙":2,"庚":2,"丙":4,"辛":4,"丁":6,"壬":6,"戊":8,"癸":8}.get(day_gan, 0)
    return list(GAN)[(start_gan_idx + t_idx) % 10], target_ji

def auto_fill_user_ganji():
    import streamlit as st
    st.session_state['app_running'] = False
    
    ry = st.session_state.get("u_ry_rev", "")
    rm = st.session_state.get("u_rm_rev", "")
    rd = st.session_state.get("u_rd_rev", "")
    rt = st.session_state.get("u_rt_rev", "")
    
    _ry = extract_ganji(ry) if 'extract_ganji' in globals() else ry
    _rm = extract_ganji(rm) if 'extract_ganji' in globals() else rm
    _rd = extract_ganji(rd) if 'extract_ganji' in globals() else rd
    
    if not _ry and not _rm and not _rd:
        st.session_state.pop('rev_success_msg', None)
    elif len(_ry) >= 2 and len(_rm) >= 2 and len(_rd) >= 2:
        ry_h = K2H_GAN.get(_ry[0], _ry[0]) + K2H_JI.get(_ry[1], _ry[1])
        rm_h = K2H_GAN.get(_rm[0], _rm[0]) + K2H_JI.get(_rm[1], _rm[1])
        rd_h = K2H_GAN.get(_rd[0], _rd[0]) + K2H_JI.get(_rd[1], _rd[1])
        
        klc_find = KoreanLunarCalendar()
        found = False
        
        time_map = {
            '자': '00:30 ~ 01:29 (朝子)시', '子': '00:30 ~ 01:29 (朝子)시',
            '축': '01:30 ~ 03:29 (丑)시', '丑': '01:30 ~ 03:29 (丑)시',
            '인': '03:30 ~ 05:29 (寅)시', '寅': '03:30 ~ 05:29 (寅)시',
            '묘': '05:30 ~ 07:29 (卯)시', '卯': '05:30 ~ 07:29 (卯)시',
            '진': '07:30 ~ 09:29 (辰)시', '辰': '07:30 ~ 09:29 (辰)시',
            '사': '09:30 ~ 11:29 (巳)시', '巳': '09:30 ~ 11:29 (巳)시',
            '오': '11:30 ~ 13:29 (午)시', '午': '11:30 ~ 13:29 (午)시',
            '미': '13:30 ~ 15:29 (未)시', '未': '13:30 ~ 15:29 (未)시',
            '신': '15:30 ~ 17:29 (申)시', '申': '15:30 ~ 17:29 (申)시',
            '유': '17:30 ~ 19:29 (酉)시', '酉': '17:30 ~ 19:29 (酉)시',
            '술': '19:30 ~ 21:29 (戌)시', '戌': '19:30 ~ 21:29 (戌)시',
            '해': '21:30 ~ 23:29 (亥)시', '亥': '21:30 ~ 23:29 (亥)시'
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
                        
                        if rt:
                            ji_char = rt[-1]
                            rt_h = K2H_JI.get(ji_char, ji_char)
                            st.session_state['s_t'] = time_map.get(rt_h, "시간 모름")
                        else:
                            st.session_state['s_t'] = "시간 모름"

                        found = True
                        st.session_state['rev_success_msg'] = "✅ 자동입력 완료!"
                        break
                curr_dt -= dt_mod.timedelta(days=1)
            if found: break
        if not found: 
            st.session_state['rev_error_msg'] = "일치하는 날짜가 없습니다."
    else: 
        st.session_state['rev_error_msg'] = "간지를 2글자씩 정확히 입력하세요."

def auto_fill_partner_ganji():
    import streamlit as st
    st.session_state['app_running'] = False
    
    p_ry = st.session_state.get("p_ry_rev", "")
    p_rm = st.session_state.get("p_rm_rev", "")
    p_rd = st.session_state.get("p_rd_rev", "")
    p_rt = st.session_state.get("p_rt_rev", "")
    
    _p_ry = extract_ganji(p_ry) if 'extract_ganji' in globals() else p_ry
    _p_rm = extract_ganji(p_rm) if 'extract_ganji' in globals() else p_rm
    _p_rd = extract_ganji(p_rd) if 'extract_ganji' in globals() else p_rd

    if not _p_ry and not _p_rm and not _p_rd:
        st.session_state.pop('rev_p_success_msg', None)
    elif len(_p_ry) >= 2 and len(_p_rm) >= 2 and len(_p_rd) >= 2:
        p_ry_h = K2H_GAN.get(_p_ry[0], _p_ry[0]) + K2H_JI.get(_p_ry[1], _p_ry[1])
        p_rm_h = K2H_GAN.get(_p_rm[0], _p_rm[0]) + K2H_JI.get(_p_rm[1], _p_rm[1])
        p_rd_h = K2H_GAN.get(_p_rd[0], _p_rd[0]) + K2H_JI.get(_p_rd[1], _p_rd[1])
        
        klc_find = KoreanLunarCalendar()
        found = False
        
        time_map = {
            '자': '00:30 ~ 01:29 (朝子)시', '子': '00:30 ~ 01:29 (朝子)시',
            '축': '01:30 ~ 03:29 (丑)시', '丑': '01:30 ~ 03:29 (丑)시',
            '인': '03:30 ~ 05:29 (寅)시', '寅': '03:30 ~ 05:29 (寅)시',
            '묘': '05:30 ~ 07:29 (卯)시', '卯': '05:30 ~ 07:29 (卯)시',
            '진': '07:30 ~ 09:29 (辰)시', '辰': '07:30 ~ 09:29 (辰)시',
            '사': '09:30 ~ 11:29 (巳)시', '巳': '09:30 ~ 11:29 (巳)시',
            '오': '11:30 ~ 13:29 (午)시', '午': '11:30 ~ 13:29 (午)시',
            '미': '13:30 ~ 15:29 (未)시', '未': '13:30 ~ 15:29 (未)시',
            '신': '15:30 ~ 17:29 (申)시', '申': '15:30 ~ 17:29 (申)시',
            '유': '17:30 ~ 19:29 (酉)시', '酉': '17:30 ~ 19:29 (酉)시',
            '술': '19:30 ~ 21:29 (戌)시', '戌': '19:30 ~ 21:29 (戌)시',
            '해': '21:30 ~ 23:29 (亥)시', '亥': '21:30 ~ 23:29 (亥)시'
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
                            p_rt_h = K2H_JI.get(ji_char_p, ji_char_p)
                            st.session_state['p_t_key'] = time_map.get(p_rt_h, "시간 모름")
                        else:
                            st.session_state['p_t_key'] = "시간 모름"

                        found = True
                        st.session_state['rev_p_success_msg'] = "✅ 상대방 자동입력 완료!"
                        break
                curr_dt -= dt_mod.timedelta(days=1)
            if found: break
        if not found: 
            st.session_state['rev_p_error_msg'] = "일치하는 날짜가 없습니다."
    else: 
        st.session_state['rev_p_error_msg'] = "간지를 2글자씩 정확히 입력하세요."

# ==============================================================================
# 섹션 3. 명리 기초 연산 로직
# ==============================================================================
def get_color(c):
    c = _to_hanja(c)
    if c in "甲乙寅卯": return "목"
    if c in "丙丁巳午": return "화"
    if c in "戊己辰戌丑未": return "토"
    if c in "庚辛申酉": return "금"
    if c in "壬癸亥子": return "수"
    return "무"

def get_ss(dg, tc):
    dg, tc = _to_hanja(dg), _to_hanja(tc)
    if tc in ["?", " ", "-"]: return "-"
    rels = {
        '甲':{'甲':'비견','乙':'겁재','丙':'식신','丁':'상관','戊':'편재','己':'정재','庚':'편관','辛':'정관','壬':'편인','癸':'정인','寅':'비견','卯':'겁재','巳':'식신','午':'상관','辰':'편재','戌':'편재','丑':'정재','未':'정재','申':'편관','酉':'정관','亥':'편인','子':'정인'},
        '乙':{'乙':'비견','甲':'겁재','丁':'식신','丙':'상관','己':'편재','戊':'정재','辛':'편관','庚':'정관','癸':'편인','壬':'정인','卯':'비견','寅':'겁재','午':'식신','巳':'상관','丑':'편재','未':'편재','辰':'정재','戌':'정재','酉':'편관','申':'정관','子':'편인','亥':'정인'},
        '丙':{'丙':'비견','丁':'겁재','戊':'식신','己':'상관','庚':'편재','辛':'정재','壬':'편관','癸':'정관','甲':'편인','乙':'정인','巳':'비견','午':'겁재','辰':'식신','戌':'식신','未':'상관','丑':'상관','申':'편재','酉':'정재','亥':'편관','子':'정관','寅':'편인','卯':'정인'},
        '丁':{'丁':'비견','丙':'겁재','己':'식신','戊':'상관','辛':'편재','庚':'정재','癸':'편관','壬':'정관','乙':'편인','甲':'정인','午':'비견','巳':'겁재','未':'식신','丑':'식신','辰':'상관','戌':'상관','酉':'편재','申':'정재','子':'편관','亥':'정관','卯':'편인','寅':'정인'},
        '戊':{'戊':'비견','己':'겁재','庚':'식신','辛':'상관','壬':'편재','癸':'정재','甲':'편관','乙':'정관','丙':'편인','丁':'정인','辰':'비견','戌':'비견','丑':'겁재','未':'겁재','申':'식신','酉':'상관','亥':'편재','子':'정재','寅':'편관','卯':'정관','巳':'편인','午':'정인'},
        '己':{'己':'비견','戊':'겁재','辛':'식신','庚':'상관','癸':'편재','壬':'정재','乙':'편관','甲':'정관','丁':'편인','丙':'정인','丑':'비견','未':'비견','辰':'겁재','戌':'겁재','酉':'식신','申':'상관','子':'편재','亥':'정재','卯':'편관','寅':'정관','午':'편인','巳':'정인'},
        '庚':{'庚':'비견','辛':'겁재','壬':'식신','癸':'상관','甲':'편재','乙':'정재','丙':'편관','丁':'정관','戊':'편인','己':'정인','申':'비견','酉':'겁재','亥':'식신','子':'상관','寅':'편재','卯':'정재','巳':'편관','午':'정관','辰':'편인','戌':'편인','丑':'정인','未':'정인'},
        '辛':{'辛':'비견','庚':'겁재','癸':'식신','壬':'상관','乙':'편재','甲':'정재','丁':'편관','丙':'정관','己':'편인','戊':'정인','酉':'비견','申':'겁재','子':'식신','亥':'상관','卯':'편재','寅':'정재','午':'편관','巳':'정관','未':'편인','丑':'편인','辰':'정인','戌':'정인'},
        '壬':{'壬':'비견','癸':'겁재','甲':'식신','乙':'상관','丙':'편재','丁':'정재','戊':'편관','己':'정관','庚':'편인','辛':'정인','亥':'비견','子':'겁재','寅':'식신','卯':'상관','巳':'편재','午':'정재','辰':'편관','戌':'편관','丑':'정관','未':'정관','申':'편인','酉':'정인'},
        '癸':{'癸':'비견','壬':'겁재','乙':'식신','甲':'상관','丁':'편재','丙':'정재','己':'편관','戊':'정관','辛':'편인','庚':'정인','子':'비견','亥':'겁재','卯':'식신','寅':'상관','午':'편재','巳':'정재','未':'편관','丑':'편관','戌':'정관','辰':'정관','酉':'편인','申':'정인'}
    }
    return rels.get(dg, {}).get(tc, "-")

def get_unsung(dg, ji):
    """일간과 지지가 한글/한자 무엇으로 들어와도 100% 정밀 연산하는 12운성 함수"""
    dg_h = _to_hanja(dg)
    ji_h = _to_hanja(ji)
    
    if not dg_h or not ji_h: return "-"
    
    table = {
        '甲': "亥子丑寅卯辰巳午未申酉戌",
        '丙': "寅卯辰巳午未申酉戌亥子丑",
        '戊': "寅卯辰巳午未申酉戌亥子丑",
        '庚': "巳午未申酉戌亥子丑寅卯辰",
        '壬': "申酉戌亥子丑寅卯辰巳午未",
        '乙': "午巳辰卯寅丑子亥戌酉申未",
        '丁': "酉申未午巳辰卯寅丑子亥戌",
        '己': "酉申未午巳辰卯寅丑子亥戌",
        '辛': "子亥戌酉申未午巳辰卯寅丑",
        '癸': "卯寅丑子亥戌酉申未午巳辰"
    }
    
    target_str = table.get(dg_h, "")
    idx = target_str.find(ji_h)
    
    if idx != -1:
        unsung_names = ["장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"]
        return unsung_names[idx]
    return "-"

def get_12_shinsal(base_ji, target_ji):
    """기준 지지(년지 또는 일지) 대비 대상 지지의 12신살 정밀 연산"""
    b_h = _to_hanja(base_ji)
    t_h = _to_hanja(target_ji)
    
    if not b_h or not t_h: return "-"
        
    jis = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    if b_h not in jis or t_h not in jis: return "-"
        
    samhap_geob_map = {
        '申': '巳', '子': '巳', '辰': '巳',
        '寅': '亥', '午': '亥', '戌': '亥',
        '巳': '寅', '酉': '寅', '丑': '寅',
        '亥': '申', '卯': '申', '未': '申'
    }
    
    geob_start_ji = samhap_geob_map.get(b_h, "")
    if not geob_start_ji: return "-"
        
    start_idx = jis.index(geob_start_ji)
    target_idx = jis.index(t_h)
    shinsal_names = ["겁살", "재살", "천살", "지살", "년살", "월살", "망신살", "장성살", "반안살", "역마살", "육해살", "화개살"]
    
    diff = (target_idx - start_idx) % 12
    return shinsal_names[diff]

def get_dual_12_shinsal(yb, db, target_ji):
    """년지(yb) 기준 신살과 일지(db) 기준 신살을 '년지신살 (일지신살)' 형태로 결합"""
    try:
        y_shinsal = get_12_shinsal(yb, target_ji)
        d_shinsal = get_12_shinsal(db, target_ji)
        
        if not y_shinsal or y_shinsal == "-": y_shinsal = "-"
        if not d_shinsal or d_shinsal == "-": d_shinsal = "-"
        
        if y_shinsal == "-" and d_shinsal == "-": return "-"
        if y_shinsal == d_shinsal:
            return f"{y_shinsal}"
        else:
            return f"{y_shinsal} ({d_shinsal})"
    except Exception:
        return "-"

def get_all_dual_12_shinsal(yb, db, target_list):
    try:
        return [get_dual_12_shinsal(yb, db, j) for j in target_list]
    except Exception:
        return ["-"] * len(target_list) if target_list else ["-", "-", "-", "-"]

def get_all_12_shinsal(yb, mb, db, hb):
    try:
        results = [
            get_12_shinsal(yb, yb),
            get_12_shinsal(yb, mb),
            get_12_shinsal(yb, db),
            get_12_shinsal(yb, hb)
        ]
        return ", ".join(results)
    except Exception:
        return "년지 기준 12신살 연산 완료"

def get_samjae(year_ji, target_ji):
    year_ji, target_ji = _to_hanja(year_ji), _to_hanja(target_ji)
    if year_ji in ["?", " ", "-"] or target_ji in ["?", " ", "-"]: return "해당 없음"
    s_map = {
        '申': ['寅','卯','辰'], '子': ['寅','卯','辰'], '辰': ['寅','卯','辰'],
        '亥': ['巳','午','未'], '卯': ['巳','午','未'], '未': ['巳','午','未'],
        '寅': ['申','酉','戌'], '午': ['申','酉','戌'], '戌': ['申','酉','戌'],
        '巳': ['亥','子','丑'], '酉': ['亥','子','丑'], '丑': ['亥','子','丑']
    }
    sj_list = s_map.get(year_ji, [])
    if not sj_list: return "해당 없음"
    if target_ji == sj_list[0]: return "들삼재"
    elif target_ji == sj_list[1]: return "눌삼재"
    elif target_ji == sj_list[2]: return "날삼재"
    return "해당 없음"

def get_gan_rel_all(idx, gans):
    gans = [_to_hanja(g) for g in gans]
    me = gans[idx]; res = []
    if me in ["-", "?", " "]: return "-"
    for i, other in enumerate(gans):
        if i == idx or other in ["-", "?", " "]: continue
        s = {me, other}
        if s in [{'甲','己'}, {'乙','庚'}, {'丙','辛'}, {'丁','壬'}, {'戊','癸'}]: res.append("합")
        if s in [{'甲','庚'}, {'乙','辛'}, {'丙','壬'}, {'丁','癸'}, {'戊','甲'}, {'己','乙'}]: res.append("충")
    return "".join(list(set(res))) if res else "-"

def get_ji_rel_set(me, target):
    me, target = _to_hanja(me), _to_hanja(target)
    if not me or not target or me == "?" or target == "?" or me == target: return "자형" if me == target and me in "辰午酉亥" else "-"
    s, r = {me, target}, []
    if s in [{'寅','卯'}, {'卯','辰'}, {'寅','辰'}, {'巳','午'}, {'午','未'}, {'巳','未'}, {'申','酉'}, {'酉','戌'}, {'申','戌'}, {'亥','子'}, {'子','丑'}, {'亥','丑'}]: r.append("방합")
    if s in [{'申','子'}, {'子','辰'}, {'申','辰'}, {'寅','午'}, {'午','戌'}, {'寅','戌'}, {'亥','卯'}, {'卯','未'}, {'亥','未'}, {'巳','酉'}, {'酉','丑'}, {'巳','丑'}]: r.append("반합")
    if s in [{'子','丑'}, {'寅','亥'}, {'卯','戌'}, {'辰','酉'}, {'巳','申'}, {'午','未'}]: r.append("육합")
    if s in [{'午','亥'}, {'子','戌'}, {'丑','寅'}, {'寅','未'}, {'卯','申'}]: r.append("암합")
    if s in [{'子','午'}, {'丑','未'}, {'寅','申'}, {'卯','酉'}, {'辰','戌'}, {'巳','亥'}]: r.append("충")
    if s in [{'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}, {'子','卯'}]: r.append("형")
    if s in [{'子','未'}, {'丑','午'}, {'寅','巳'}, {'卯','辰'}, {'申','亥'}, {'酉','戌'}]: r.append("해")
    if s in [{'子','酉'}, {'丑','辰'}, {'寅','亥'}, {'卯','午'}, {'巳','申'}, {'未','戌'}]: r.append("파")
    if s in [{'丑','午'}, {'卯','申'}, {'辰','亥'}, {'巳','戌'}]: r.extend(["원진", "귀문"])
    elif s in [{'子','酉'}, {'寅','未'}]: r.append("귀문")
    elif s in [{'寅','酉'}, {'子','未'}]: r.append("원진")
    if s == {'戌','亥'}: r.append("천라")
    if s == {'辰','巳'}: r.append("지망")
    return ", ".join(list(dict.fromkeys(r))) if r else "-"

def get_ji_rel_rows_html(jjis):
    ji_rel_rows = ""
    for l_idx, r_idx in enumerate([1, 2, 0, 3]):
        cells = "".join([f"<td style='border:1px solid #444;'>{get_ji_rel_set(jjis[r_idx], jjis[ci])}</td>" for ci in range(4)])
        lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5;'>합충형해파</td>" if l_idx==0 else ""
        ji_rel_rows += f"<tr>{lbl}{cells}</tr>"
    return ji_rel_rows

def get_general_shinsal_filtered(idx, gans, jjis, gender="남성"):
    gans = [_to_hanja(g) for g in gans]
    jjis = [_to_hanja(j) for j in jjis]
    dc, mc, yc = gans[1], gans[2], gans[3]
    dj, mj, yj = jjis[1], jjis[2], jjis[3]
    cur_g, cur_j = gans[idx], jjis[idx]
    
    if cur_g in ["?", "-", " "] or cur_j in ["?", "-", " "]: return []
    gj = cur_g + cur_j
    noble, ausp, evil = [], [], []
    
    if cur_j in {'甲':'未丑','乙':'申子','丙':'酉亥','丁':'酉亥','戊':'未丑','己':'申子','庚':'未丑','辛':'午寅','壬':'卯巳','癸':'卯巳'}.get(dc,""): noble.append("천을귀인") 
    if cur_j == mj: noble.append("월덕귀인") 
    if cur_j in {'甲':'子午','乙':'子午','丙':'卯酉','丁':'卯酉','戊':'辰戌丑未','己':'辰戌丑未','庚':'寅亥','辛':'寅亥','壬':'巳申','癸':'巳申'}.get(dc,""): noble.append("태극귀인") 
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): noble.append("천록귀인") 
    if cur_j in {'甲':'巳','乙':'午','丙':'申','戊':'申','丁':'酉','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}.get(dc,""): noble.append("문창귀인")
    if cur_j in {'甲':'亥','乙':'子','丙':'寅','戊':'寅','丁':'卯','己':'卯','庚':'巳','辛':'午','壬':'申','癸':'酉'}.get(dc,""): noble.append("문곡귀인")
    if cur_j in {'甲':'亥','乙':'午','丙':'寅','戊':'寅','丁':'酉','己':'酉','庚':'巳','辛':'子','壬':'申','癸':'卯'}.get(dc,""): noble.append("학당귀인")
    if gj in ["甲寅", "乙丑", "丙子", "丁酉", "戊申", "己未", "庚午", "辛巳", "壬辰", "癸卯"]: noble.append("복성귀인")
    if cur_j in {'甲':'巳','乙':'午','丙':'巳','丁':'午','戊':'申','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}.get(dc,""): noble.append("천주귀인")
    
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): ausp.append("건록")
    if cur_j in {'甲':'亥','乙':'戌','丙':'申','戊':'申','丁':'未','己':'未','庚':'巳','辛':'辰','壬':'寅','癸':'丑'}.get(dc,""): noble.append("암록")
    if cur_j in {'甲':'辰','乙':'巳','丙':'未','戊':'未','丁':'申','己':'申','庚':'戌','辛':'亥','壬':'丑','癸':'寅'}.get(dc,""): ausp.append("금여록")
    if gj in ["甲寅", "丙辰", "戊辰", "庚辰", "壬戌"]: ausp.append("일덕")
    if gj in ["乙丑", "己巳", "癸酉"] and idx in [0, 1]: ausp.append("금신")
    hyeop_map = {'甲':['丑','卯'], '乙':['寅','辰'], '丙':['辰','午'], '戊':['辰','午'], '丁':['巳','未'], '己':['巳','未'], '庚':['未','酉'], '辛':['申','戌'], '壬':['戌','子'], '癸':['亥','丑']}
    if cur_j in hyeop_map.get(dc, []): ausp.append("협록")  
    
    if gj in ["甲辰","乙未","丙戌","丁丑","戊辰","壬戌","癸丑"]: evil.append("백호대살")
    if gj in ["庚辰","庚戌","壬辰","壬戌","戊戌"]: evil.append("괴강살")
    if cur_j in {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子'}.get(dc,""): evil.append("양인살")

    if cur_j in {'甲':'酉','乙':'戌','丙':'子','丁':'丑','戊':'子','己':'丑','庚':'卯','辛':'辰','壬':'午','癸':'未'}.get(dc,""): evil.append("비인살")
    if dj == '寅' and cur_j in ['寅', '巳', '申']: evil.append("탕화살")
    if dj == '午' and cur_j in ['辰', '午', '丑']: evil.append("탕화살")
    if dj == '丑' and cur_j in ['午', '未', '戌']: evil.append("탕화살")
    if cur_g in ['乙', '己'] or cur_j in ['巳', '丑']: evil.append("곡각살")
    if cur_g in ['甲', '辛'] or cur_j in ['卯', '午', '申', '未']: evil.append("현침살")

    if gj in ["甲寅", "乙卯", "丙午", "丁巳", "戊辰", "戊戌", "己未", "己丑", "庚申", "辛酉", "壬子", "癸亥"]: evil.append("간여지동")
    if gj in ["甲寅","乙巳","丁巳","戊申","辛亥"]: evil.append("고란살")
    if gj in ["丙子","丁丑","戊寅","辛卯","壬辰","癸巳","丙午","丁未","戊申","辛酉","壬戌","癸亥"]: evil.append("음양차착")
    if gj in ["甲午", "丙戌", "戊辰", "庚辰", "壬戌", "乙巳", "丁亥", "己亥", "辛巳", "癸亥"]: evil.append("의처의부")
    if cur_j in ['寅','申','巳','亥']: evil.append("효신살")

    dohwa_map = {'寅':'卯', '午':'卯', '戌':'卯', '申':'酉', '子':'酉', '辰':'酉', '巳':'午', '酉':'午', '丑':'午', '亥':'子', '卯':'子', '未':'子'}
    if cur_j == dohwa_map.get(yj, "") or cur_j == dohwa_map.get(dj, ""): evil.append("도화살")
    if gj in ["甲子", "乙巳", "丁卯", "庚午", "辛亥", "癸酉"]: evil.append("나체도화")
    if gj in ["甲午","丙寅","丁未","戊辰","庚戌","辛酉","壬子"]: evil.append("홍염살")
    if gj in ["甲寅", "乙卯", "丁未", "戊戌", "己未", "庚申", "辛酉", "癸丑"]: evil.append("음욕살")
    if gender == "여성" and gj in ["甲寅", "甲申", "丁丑", "戊申", "己丑", "辛未", "壬寅", "癸未"]: evil.append("남연살")
    if gender == "남성" and gj in ["乙丑", "丙申", "丁丑", "己未", "庚寅", "辛未", "壬寅", "壬申"]: evil.append("여연살")

    if cur_j in ['卯','酉','戌'] and (jjis.count('卯') + jjis.count('酉') + jjis.count('戌')) >= 2: evil.append("철쇄개금")
    if cur_j in ['子','午','卯','酉']: evil.append("교신성")
    if idx == 1 and gj in ["丙午", "丁未", "戊午", "戊子", "己未", "己丑"]: evil.append("육수살")
    if gj in ["甲辰","乙巳","丙申","丁亥","戊戌","己丑","庚辰","辛巳","壬申","癸亥"]: evil.append("십악대패살")
    if cur_g in ['甲', '丙', '壬'] and cur_j in ['子', '辰']: evil.append("평두살")
    cheolsa_map = {'甲':'辰', '乙':'寅', '丙':'戌', '丁':'申', '戊':'午', '己':'辰', '庚':'寅', '辛':'戌', '壬':'申', '癸':'午'}
    if cur_j == cheolsa_map.get(dc, ""): evil.append("철사관")

    if gj in ["甲子", "甲午", "己卯", "己酉"]: ausp.append("진신") 
    if gj in ["丙子", "丙午", "辛卯", "辛酉"]: evil.append("교신") 
    if gj in ["丁丑", "丁未", "壬辰", "壬戌"]: evil.append("퇴신") 
    if gj in ["戊寅", "戊申", "癸巳", "癸亥"]: evil.append("복신") 

    result = []
    for n in list(dict.fromkeys(noble)): result.append(f"<span style='color:#0D47A1;'>{n}</span>")
    for a in list(dict.fromkeys(ausp)): result.append(f"<span style='color:#2E7D32;'>{a}</span>")
    for e in list(dict.fromkeys(evil)): result.append(f"<span style='color:#C62828;'>{e}</span>")
    return result

def get_jijanggan_full(dg, ji):
    dg, ji = _to_hanja(dg), _to_hanja(ji)
    if ji in ["?", "-", " "]: return "-"
    raw = JIJANGGAN.get(ji, ['-','-','-'])
    res = "<div style='display:flex; flex-direction:column; height:100%; min-height:65px; gap:2px; padding:2px 0; margin:0;'>"
    for j in raw:
        if j != '-':
            ss_label = get_ss(dg, j)[:2]
            color_key = get_color(j)
            bg = {'목':'#2E7D32','화':'#C62828','토':'#F9A825','금':'#9E9E9E','수':'#212121'}.get(color_key, '#888')
            tc = 'white' if color_key != '토' else 'black'
            res += f"<div style='flex-grow:1; display:flex; align-items:center; justify-content:center; background:{bg}; color:{tc}; width:95%; margin:0 auto; font-size:12px; font-weight:900; border-radius:3px;'>{j} ({ss_label})</div>"
        else: 
            res += "<div style='flex-grow:1; display:flex; align-items:center; justify-content:center; background:#f9f9f9; width:95%; margin:0 auto; color:#bbb; border-radius:3px; border:1px dashed #ddd;'>-</div>"
    return res + "</div>"

def get_gyukgook_detailed(ds, ys, ms, hs, mb):
    ds, ys, ms, hs, mb = _to_hanja(ds), _to_hanja(ys), _to_hanja(ms), _to_hanja(hs), _to_hanja(mb)
    jg = JIJANGGAN.get(mb, [])
    if not jg: return "알수없음격", "지장간 정보가 없습니다."

    if ds in ['甲', '丙', '戊', '庚', '壬']:
        if mb == '卯' and ds == '甲': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == '午' and ds == '丙': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == '酉' and ds == '庚': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == '子' and ds == '壬': return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."
        if mb == {'甲':'寅', '丙':'巳', '戊':'巳', '庚':'申', '壬':'亥'}.get(ds, ""):
            return "건록격", f"월지 {mb}가 일간 {ds}의 건록(建祿)에 해당하여 건록격으로 정합니다."

    def safe_get_ss(day_gan, target_char):
        if not target_char or target_char == "?": return "무명"
        return get_ss(day_gan, target_char)

    if mb in ["子", "午", "卯", "酉"]:
        core_ss = safe_get_ss(ds, mb)
        if core_ss in ["비견", "겁재"]:
            return "건록(월겁)격", f"월지 {mb}가 일간 {ds}와 같은 기운이므로 건록(월겁)격으로 삼습니다."
        return core_ss + "격", f"월지 {mb}의 순수한 기운인 {core_ss}을 그대로 격으로 삼습니다."
    
    target_gans = [ys, ms, hs] 
    main_qi = jg[-1]
    
    def is_valid_gyuk(char):
        return safe_get_ss(ds, char) not in ["비견", "겁재"]
    
    if main_qi in target_gans and is_valid_gyuk(main_qi):
        return safe_get_ss(ds, main_qi) + "격", f"월지 {mb}의 정기(본기)인 {main_qi}이 천간에 투출하여 {safe_get_ss(ds, main_qi)}격이 되었습니다."
    if len(jg) >= 2 and jg[1] in target_gans and is_valid_gyuk(jg[1]):
        return safe_get_ss(ds, jg[1]) + "격", f"월지 {mb}의 중기인 {jg[1]}이 천간에 투출하여 {safe_get_ss(ds, jg[1])}격이 되었습니다."
    if len(jg) >= 1 and jg[0] in target_gans and is_valid_gyuk(jg[0]):
        return safe_get_ss(ds, jg[0]) + "격", f"월지 {mb}의 여기인 {jg[0]}이 천간에 투출하여 {safe_get_ss(ds, jg[0])}격이 되었습니다."
        
    fallback_ss = safe_get_ss(ds, main_qi)
    if fallback_ss in ["비견", "겁재"]:
        return "건록(월겁)격", f"월지 {mb}의 본기가 {fallback_ss}이므로 건록(월겁)격으로 정합니다."
    
    return fallback_ss + "격", f"월지 {mb}의 지장간(비겁 제외)이 투출하지 않아 정기(본기)인 {main_qi}를 기준으로 {fallback_ss}격으로 정합니다."

def calculate_gongmang(ilgan, ilji):
    g = _to_hanja(ilgan)
    j = _to_hanja(ilji)
    
    gan_list = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    ji_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    if g not in gan_list or j not in ji_list: return "-"
    
    try:
        base = (ji_list.index(j) - gan_list.index(g) - 2) % 12
        gong1 = ji_list[base]
        gong2 = ji_list[(base + 1) % 12]
        return f"{gong1}{gong2}"
    except:
        return "-"

def get_daeun_data_list(ms, mb, ds, yb, order_dir, calc_d, age):
    daewun_list = []
    c_idx = GAN.index(ms) % 10 if ms in GAN else 0
    j_idx = JI.index(mb) % 12 if mb in JI else 0

    for i in range(10):
        val = i * 10 + calc_d
        c_idx_calc = (c_idx + (i + 1) * order_dir) % 10
        j_idx_calc = (j_idx + (i + 1) * order_dir) % 12
        
        c_hangul = GAN[c_idx_calc]
        j_hangul = JI[j_idx_calc]
        c, j = K2H_GAN.get(c_hangul, c_hangul), K2H_JI.get(j_hangul, j_hangul)
        
        ss_gan, ss_ji = get_ss(ds, c_hangul) or "-", get_ss(ds, j_hangul) or "-"
        try:
            un_sung = get_unsung(ds, j) or "-"
            shin_sal = get_12_shinsal(yb, j) or "-"
        except:
            un_sung, shin_sal = "-", "-"
            
        daewun_list.append({
            "age_range": f"{val}~{val+9}세", "ss_gan": ss_gan, "c_hanja": c, "c_hangul": c_hangul,
            "j_hanja": j, "j_hangul": j_hangul, "ss_ji": ss_ji, "un_sung": un_sung, 
            "shin_sal": shin_sal, "is_current": (val <= age < val + 10), "is_first": (i == 0)
        })
    return daewun_list

def get_daeun_fact_string(daewun_data_list):
    fact_str = "\n"
    for dw in daewun_data_list:
        age_range = dw.get("age_range", "정보없음")
        ganji = f"{dw.get('c_hangul', '')}{dw.get('j_hangul', '')}"
        ss = f"{dw.get('ss_gan', '')}{dw.get('ss_ji', '')}"
        fact_str += f"- {age_range} 대운 ({ganji}): 주요 기운({ss})\n"
    return fact_str

# ==============================================================================
# 섹션 4. 특수 파동 및 묘고 정밀 연산 로직
# ==============================================================================
def check_samhyung_facts(jjis, dw_j=None, sewun_j=None, wolun_j=None):
    """
    원국(년/월/일/시 지지) 및 행운(대운/세운/월운)과의 조합에서
    인사신(寅巳申)·축술미(丑戌未) 삼형살의 완결 및 가형(假刑) 상태를 정밀 연산합니다.
    """
    jjis_h = [_to_hanja(j) for j in jjis if j not in ["?", "-", " "]]
    results = []

    # 1. 원국 내부 삼형살 / 가형 감지
    in_set = {'寅', '巳', '申'}
    sul_set = {'丑', '戌', '未'}

    won_in_present = in_set.intersection(set(jjis_h))
    won_sul_present = sul_set.intersection(set(jjis_h))

    # [인사신 삼형 원국 판정]
    if len(won_in_present) == 3:
        results.append("🔥 [원국 인사신(寅巳申) 삼형살 완성] 권력, 조정, 수리, 의료, 법형, 물리적 충돌 및 강력한 개혁 에너지가 내재됨.")
    elif len(won_in_present) == 2:
        missing = list(in_set - won_in_present)[0]
        results.append(f"⚠️ [원국 인사신(寅巳申) 가형(假刑) 상태] 원국에 {','.join(won_in_present)} 보유 중. 운에서 '{missing}'이 들어올 때 삼형살이 완성되니 신상·사고·조정 주의 요망.")

    # [축술미 삼형 원국 판정]
    if len(won_sul_present) == 3:
        results.append("🔥 [원국 축술미(丑戌未) 삼형살 완성] 묘고의 충돌, 재물·건강·인간관계의 대대적 재편 및 정교한 조정 에너지가 내재됨.")
    elif len(won_sul_present) == 2:
        missing = list(sul_set - won_sul_present)[0]
        results.append(f"⚠️ [원국 축술미(丑戌未) 가형(假刑) 상태] 원국에 {','.join(won_sul_present)} 보유 중. 운에서 '{missing}'이 들어올 때 삼형살이 완성되니 재물·건강 조정 주의 요망.")

    # 2. 행운(대운/세운/월운) 결합으로 삼형살이 완성되는 외부 충격 감지
    hangun_list = []
    if dw_j and dw_j not in ["?", "-", " "]: hangun_list.append(("대운", _to_hanja(dw_j)))
    if sewun_j and sewun_j not in ["?", "-", " "]: hangun_list.append(("세운", _to_hanja(sewun_j)))
    if wolun_j and wolun_j not in ["?", "-", " "]: hangun_list.append(("월운", _to_hanja(wolun_j)))

    for u_type, u_j in hangun_list:
        combined_set = set(jjis_h + [u_j])
        
        if len(won_in_present) == 2 and in_set.issubset(combined_set) and u_j in in_set:
            results.append(f"🚨 [{u_type}({u_j}) 인사신 삼형 완성] {u_type} 지지({u_j})가 기폭제가 되어 인사신 삼형살 발동! (수리, 법률, 건강, 수술, 직주 이동 파동 강하게 작용)")

        if len(won_sul_present) == 2 and sul_set.issubset(combined_set) and u_j in sul_set:
            results.append(f"🚨 [{u_type}({u_j}) 축술미 삼형 완성] {u_type} 지지({u_j})가 기폭제가 되어 축술미 삼형살 발동! (재물 입고/개고, 문서/가정/지병 재정비 파동 강하게 작용)")

    return " / ".join(results) if results else "삼형살(인사신/축술미) 특이 파동 없음"

def check_vault_status(base_gans, base_jjis, attacker_ji):
    base_gans = [_to_hanja(g) for g in base_gans]
    base_jjis = [_to_hanja(j) for j in base_jjis]
    attacker_ji = _to_hanja(attacker_ji)
    
    vaults = ['辰', '戌', '丑', '未']
    clash_map = {'辰':'戌', '戌':'辰', '丑':'未', '未':'丑'}
    hyung_sets = [{'丑','戌'}, {'戌','未'}, {'丑','未'}]
    core_gans = {'辰':['壬','癸'], '戌':['丙','丁'], '丑':['庚','辛'], '未':['甲','乙']}
    
    results = []
    for i, ji in enumerate(base_jjis):
        if ji in vaults:
            if clash_map.get(ji) == attacker_ji or {ji, attacker_ji} in hyung_sets:
                targets = core_gans.get(ji, [])
                is_trapped = any(g in targets for g in base_gans)
                if is_trapped:
                    trapped_chars = [g for g in targets if g in base_gans]
                    results.append(f"🚨 <b style='color:#C62828;'>[입고(入庫) 주의]</b> {ji} 무덤이 열려 천간의 {','.join(trapped_chars)} 기운이 빨려 들어갑니다.")
                else:
                    results.append(f"💎 <b style='color:#2E7D32;'>[개고(開庫) 발현]</b> {ji} 금고가 열려 지장간의 숨은 보물이 세상에 드러납니다.")
    return results

def get_hang_un_vaults_str(dw_j, base_gans, base_jjis):
    """대운 지지(dw_j) 수고/화고/금고/목고 정밀 판별 및 입고/개고 분석"""
    dw_j = _to_hanja(dw_j)
    if dw_j not in ['辰', '戌', '丑', '未']:
        return "진술축미(辰戌丑未) 대운이 아니므로 대운 자체의 강력한 묘고 입고/개고 작용은 없음"

    base_gans = [_to_hanja(g) for g in base_gans if g not in ["?", "-", " "]]
    base_jjis = [_to_hanja(j) for j in base_jjis if j not in ["?", "-", " "]]

    vault_info = {
        '辰': ('水庫(수고)', ['壬', '癸'], '戌'),
        '戌': ('火庫(화고)', ['丙', '丁'], '辰'),
        '丑': ('金庫(금고)', ['庚', '辛'], '未'),
        '未': ('木庫(목고)', ['甲', '乙'], '丑')
    }

    vault_name, target_gans, clash_partner = vault_info[dw_j]
    trapped_gans = [g for g in target_gans if g in base_gans]

    is_clashed = clash_partner in base_jjis
    is_hyung = False
    if dw_j in ['丑', '戌', '未']:
        is_hyung = any(j in ['丑', '戌', '未'] and j != dw_j for j in base_jjis)

    details = []
    if trapped_gans:
        details.append(f"🚨 원국 천간의 {','.join(trapped_gans)} 기운이 대운 {dw_j}({vault_name})에 입고(入庫)되어 활동성이 수렴·제약됨")
    
    if is_clashed or is_hyung:
        trigger_type = "충(沖)" if is_clashed else "형(刑)"
        details.append(f"💎 원국 지지와의 {trigger_type} 작용으로 대운 {dw_j}({vault_name}) 창고가 개고(開庫)되어 지장간 보물이 발현됨")
    elif not trapped_gans:
        details.append(f"📦 대운 {dw_j}({vault_name}) 환경이 조성되어 해당 오행의 저장 무대가 형성됨")

    return f"[{dw_j}대운 - {vault_name}] " + " / ".join(details)

def get_won_guk_vaults_str(jjis):
    vaults = [j for j in jjis if j in ['辰', '戌', '丑', '未']]
    if not vaults:
        return "원국 내 진술축미(묘고) 글자 없음 (특수 입고 작용 미미함)"
    return f"원국 내 묘고 글자 보유: {', '.join(vaults)} (강력한 입고 및 개고 잠재력 내재)"

# ==============================================================================
# 섹션 5. 운세 풀이 및 체용(體用) 5x5 확장 로직
# ==============================================================================
def get_age_prompt(age):
    """연령대에 맞춘 AI 통변 집중 가이드 지침 생성"""
    if age < 20:
        return f"현재 {age}세 미성년자/학생이므로 학업, 진학, 부모와의 관계, 성장기 성격 형성에 집중하여 서술하십시오."
    elif age < 40:
        return f"현재 {age}세 청년층이므로 사회 초년/취업, 직장 운, 첫 취직/이직, 연애 및 취업/결혼 준비에 집중하여 서술하십시오."
    elif age < 60:
        return f"현재 {age}세 중년층이므로 직장 내 승진/책임, 사업 확장, 재물 축적, 자녀 양육 및 건강 관리에 집중하여 서술하십시오."
    else:
        return f"현재 {age}세 노년층이므로 은퇴 후 삶, 노후 재정 안정, 자녀와의 관계, 건강 관리 및 삶의 보람에 집중하여 서술하십시오."

def get_gender_prompt(gender):
    """성별에 따른 육친(관성/재성/식상) 해석 원칙 가이드 생성"""
    if gender == "여성":
        return "여성 내담자(여명)이므로 육친 적용 시 관성(官星)을 배우자/남편으로, 식상(食傷)을 자식으로 엄격히 적용하십시오."
    else:
        return "남성 내담자(남명)이므로 육친 적용 시 재성(財星)을 배우자/아내로, 관성(官星)을 자식으로 엄격히 적용하십시오."

def get_marital_prompt(gender, marital):
    """혼인 상태별(미혼/기혼/돌싱) 타겟팅 지침 생성"""
    if marital == "기혼":
        sp_name = "남편" if gender == "여성" else "아내"
        return f"현재 기혼 상태이므로 {sp_name}과의 실질적인 가내 평안, 정서적 유대, 부부 관계 유지 전략에 집중하여 통변하십시오."
    elif marital == "돌싱":
        return "현재 이혼/사별(돌싱) 상태이므로 과거 인연에 대한 성찰과 함께 새로운 재혼 및 운명적 재기 인연에 집중하여 통변하십시오."
    else:
        sp_name = "미래의 남편" if gender == "여성" else "미래의 아내"
        return f"현재 미혼 상태이므로 {sp_name}이 될 인연의 도래 시기와 연애/결혼 준비 전략에 집중하여 통변하십시오."

def get_opposite_gender(gender):
    return "여성" if gender == "남성" else "남성"

def update_partner_gender():
    import streamlit as st
    user_g = st.session_state.get("u_g", "남성")
    st.session_state["f_g"] = get_opposite_gender(user_g)

def update_user_gender():
    import streamlit as st
    partner_g = st.session_state.get("f_g", "여성")
    st.session_state["u_g"] = get_opposite_gender(partner_g)

def get_yukchin_rule(gender, marital):
    if gender == '남성':
        return f"""
★ 육친 통변 절대 규칙 (남성용) ★
- 본 내담자는 남성(현재 상태: {marital})입니다.
1. 핵심 가족: 아내 = 정재 (없으면 편재) / 애인 = 편재 (없으면 정재) / 자녀 = 관성(정관/편관) ※ 식상으로 풀이 금지
2. 부모 및 조부모: 아버지 = 편재(없으면 정재) / 어머니 = 정인(없으면 편인)
3. 처가 및 형제: 장모 = 식상 / 형제(남) = 비견 / 형제(여) = 겁재
4. 상태별 타겟팅: 내담자 상태({marital})에 따라 아내/재혼/이성 인연을 구분하여 통변할 것.
"""
    else:
        return f"""
★ 육친 통변 절대 규칙 (여성용) ★
- 본 내담자는 여성(현재 상태: {marital})입니다.
1. 핵심 가족: 남편 = 정관 (없으면 편관) / 애인 = 편관 (없으면 정관) / 자녀 = 식상(식신/상관) ※ 관성으로 풀이 금지
2. 부모 및 조부모: 아버지 = 편재(없으면 정재) / 어머니 = 정인(없으면 편인)
3. 시댁 및 자매: 시어머니 = 재성 / 자매 = 비견 / 형제 = 겁재
4. 상태별 타겟팅: 내담자 상태({marital})에 따라 남편/재혼/이성 인연을 구분하여 통변할 것.
"""

def get_universal_analysis(ds, mb, db, gans, jjis):
    """일지(db) 궁(宮) 무대 산출 및 지장간 좌법/인종법 분석"""
    db_h = _to_hanja(db)
    ds_h = _to_hanja(ds)
    if not db_h or not ds_h: return []
        
    ilji_unsung_base = get_unsung(ds_h, db_h)
    ilji_palace = f"{ilji_unsung_base}궁" if ilji_unsung_base != "-" else "자좌"
    
    jg_list = JIJANGGAN.get(db_h, [])
    results = []
    
    for qi in jg_list:
        if qi == '-': continue
        ss = get_ss(ds_h, qi)
        qi_unsung = get_unsung(qi, db_h)
        results.append(
            f"[겉성격/좌법] 일지 {db_h} {ilji_palace}(宮) 환경 무대: 지장간 속 {qi}({ss})는 {qi_unsung}좌(坐)하여, "
            f"사회적 표상에서 {ss}의 기운이 {qi_unsung}의 주도적 파동으로 강렬하게 발현됨"
        )
        
    all_gans = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    present_chars = [_to_hanja(c) for c in gans + jjis if _to_hanja(c) in all_gans]
    missing_gans = [g for g in all_gans if g not in present_chars]
    
    for m in missing_gans:
        ss = get_ss(ds_h, m)
        m_unsung = get_unsung(m, db_h)
        results.append(
            f"[속마음/인종법] 일지 {db_h} {ilji_palace}(宮) 속 무의식: 원국에 숨겨진 {m}({ss})를 인종하면 {m_unsung}종(從)에 해당하여, "
            f"내면 깊은 곳에 {ss}에 대한 {m_unsung}적 정신적/현실적 결핍과 갈망이 작용함"
        )
        
    return results

# 체용(體用) 임상 매트릭스 및 연산 함수
CHE_YONG_MATRIX_TEXT = """- 체(비겁)+용(비겁): 식상발흥, 직무개척, 건강호조, 출산운, 처가와 유정
- 체(비겁)+용(식상): 업무원만, 진취력, 건강호조, 원행(遠行), 발표, 여행
- 체(비겁)+용(재성): 손재, 소비, 이성난, 가정불화, 부친반목
- 체(비겁)+용(관성): 설화, 관재, 가족불화, 직장문제, 공명심
- 체(비겁)+용(인성): 의식주안정, 스카우트, 계약, 학업순성, 합격, 가정화목
- 체(식상)+용(비겁): 사업원만, 결과만족, 명진(名振), 의기투합, 긍정심
- 체(식상)+용(식상): 재성발흥, 재적성취, 이성운, 가정원만, 재물입고, 환대
- 체(식상)+용(재성): 이재순성, 사업원만, 인연, 가족화목, 건강, 횡재
- 체(식상)+용(관성): 건강악화, 직업불안, 직주이동, 관재, 설화, 가족불화
- 체(식상)+용(인성): 직업불안, 건강문제, 계약파기, 학문불안, 의식주 불안
- 체(재성)+용(비겁): 일득삼재, 손재, 부부갈등, 과소비, 업무지연
- 체(재성)+용(식상): 여행, 결과만족, 횡재수, 가정화목, 득자운
- 체(재성)+용(재성): 관성발흥, 직업운 상승, 이성운 순성, 가정원만
- 체(재성)+용(관성): 신분상승, 출마, 천거, 장기출장, 가정화목, 이성운
- 체(재성)+용(인성): 매사불성, 소비지출, 가족불화, 계약파기, 손재, 흉사
- 체(관성)+용(비겁): 업무지연, 관재, 설화, 다툼, 허언, 선민의식
- 체(관성)+용(식상): 명예훼손, 직업이동, 질책, 가족불화, 이성난
- 체(관성)+용(재성): 사업운 원만, 이성운 순성, 가정원만, 취업, 명예
- 체(관성)+용(관성): 인성발흥, 승진승급, 계약성사, 자식운 원만
- 체(관성)+용(인성): 합격, 승진, 계약, 스카우트, 의식주 안정, 당선
- 체(인성)+용(비겁): 건강호조, 학업원만, 신분상승, 당선, 명예, 안정
- 체(인성)+용(식상): 불안정, 계약파기, 학업불성, 구설, 육친흉사, 자식불효
- 체(인성)+용(재성): 지출, 탈재, 파재, 사기수, 손재, 분주다망, 시성종패
- 체(인성)+용(관성): 업무원활, 학업성취, 승진승급, 영전, 합격, 포상
- 체(인성)+용(인성): 비겁발흥, 명예, 명진, 칭찬, 주체성 확립, 학문성취"""

def get_group_ss(ss_name):
    """십성 이름을 5대 그룹(비겁, 식상, 재성, 관성, 인성)으로 변환"""
    if not ss_name or ss_name == "-": return "비겁"
    if ss_name in ["비견", "겁재"]: return "비겁"
    if ss_name in ["식신", "상관"]: return "식상"
    if ss_name in ["편재", "정재"]: return "재성"
    if ss_name in ["편관", "정관"]: return "관성"
    if ss_name in ["편인", "정인"]: return "인성"
    return "비겁"

def get_execution_yong(upper_group, lower_group):
    matrix = {
        '비겁': {'비겁':'비겁', '식상':'식상', '재성':'재성', '관성':'관성', '인성':'인성'},
        '식상': {'비겁':'인성', '식상':'비겁', '재성':'식상', '관성':'재성', '인성':'관성'},
        '재성': {'비겁':'관성', '식상':'인성', '재성':'비겁', '관성':'식상', '인성':'재성'},
        '관성': {'비겁':'재성', '식상':'관성', '재성':'인성', '관성':'비겁', '인성':'식상'},
        '인성': {'비겁':'식상', '식상':'재성', '재성':'관성', '관성':'인성', '인성':'비겁'}
    }
    return matrix.get(upper_group, {}).get(lower_group, '비겁')

def get_matrix_keyword(che_group, yong_group):
    target_str = f"- 체({che_group})+용({yong_group}):"
    for line in CHE_YONG_MATRIX_TEXT.splitlines():
        if line.startswith(target_str):
            return line.split(":", 1)[1].strip()
    return "변화 감지"

def get_woonse_analysis_facts(ds, db, dw_g_cur, dw_j_cur, sewun_g, sewun_j, wolun_g, wolun_j, ilun_g, ilun_j):
    ilju_ss = get_ss(ds, db)
    ilju_lower_group = ilju_ss if isinstance(ilju_ss, str) else (ilju_ss[0] if isinstance(ilju_ss, (list, tuple)) and len(ilju_ss) > 0 else '비겁')
    
    dw_upper_ss = get_ss(ds, dw_g_cur)
    dw_che = get_group_ss(dw_upper_ss)
    dw_yong = get_execution_yong(dw_che, ilju_lower_group)
    dw_kw = get_matrix_keyword(dw_che, dw_yong)
    
    sewun_upper_ss = get_ss(ds, sewun_g)
    sewun_che = get_group_ss(sewun_upper_ss)
    s_yong = get_execution_yong(sewun_che, ilju_lower_group)
    sewun_kw = get_matrix_keyword(dw_che, s_yong)
    
    wolun_upper_ss = get_ss(ds, wolun_g)
    wolun_che = get_group_ss(wolun_upper_ss)
    w_yong = get_execution_yong(wolun_che, ilju_lower_group)
    wolun_kw = get_matrix_keyword(sewun_che, w_yong)
    
    ilun_upper_ss = get_ss(ds, ilun_g)
    ilun_che = get_group_ss(ilun_upper_ss)
    i_yong = get_execution_yong(ilun_che, ilju_lower_group)
    ilun_kw = get_matrix_keyword(wolun_che, i_yong)
    
    woonse_fact_str = f"""
- [대운 체용 파동]: 體({dw_che}) + 用({dw_yong}) ➔ 핵심 키워드: [{dw_kw}]
- [세운 체용 파동]: 體({dw_che}) + 用({s_yong}) ➔ 핵심 키워드: [{sewun_kw}]
- [월운 체용 파동]: 體({sewun_che}) + 用({w_yong}) ➔ 핵심 키워드: [{wolun_kw}]
- [일운 체용 파동]: 體({wolun_che}) + 用({i_yong}) ➔ 핵심 키워드: [{ilun_kw}]
"""
    return {
        "dw_che": dw_che, "dw_yong": dw_yong, "dw_kw": dw_kw,
        "sewun_che": sewun_che, "sewun_yong": s_yong, "sewun_kw": sewun_kw,
        "wolun_che": wolun_che, "wolun_yong": w_yong, "wolun_kw": wolun_kw,
        "ilun_che": ilun_che, "ilun_yong": i_yong, "ilun_kw": ilun_kw,
        "woonse_fact_str": woonse_fact_str.strip()
    }

def get_weekly_daily_facts(ds, db, yb, year, month, day):
    target_dt = dt_mod.datetime(year, month, day)
    _, _, d_pillar = get_ganji_from_date(target_dt.year, target_dt.month, target_dt.day)
    i_gan, i_ji = d_pillar[0], d_pillar[1]
    
    day_wunseong = get_unsung(ds, i_ji)
    day_12shinsal = get_dual_12_shinsal(yb, db, i_ji)
    
    ilju_lower_group = get_group_ss(get_ss(ds, db))
    i_gan_group = get_group_ss(get_ss(ds, i_gan))
    
    m_che_first = i_gan_group
    am_yong = get_execution_yong(i_gan_group, ilju_lower_group)
    m_che_second = get_group_ss(get_ss(ds, i_ji))
    pm_yong = get_execution_yong(m_che_second, ilju_lower_group)
    
    weekly_ganji = []
    start_sun = target_dt - dt_mod.timedelta(days=(target_dt.weekday() + 1) % 7)
    for i in range(7):
        curr = start_sun + dt_mod.timedelta(days=i)
        _, _, dp = get_ganji_from_date(curr.year, curr.month, curr.day)
        weekly_ganji.append(f"{dp[0]}{dp[1]}")
        
    return {
        "m_che_first": m_che_first, "am_yong": am_yong,
        "m_che_second": m_che_second, "pm_yong": pm_yong,
        "day_wunseong": day_wunseong, "day_12shinsal": day_12shinsal,
        "weekly_ganji_list": ", ".join(weekly_ganji)
    }

def get_dw_fact_str(dw_g, dw_j):
    return f"천간 {dw_g}의 기운이 지지 {dw_j}의 환경을 만난 형국 (체용의 상호작용)"

def get_yongshin_analysis(counts, mb, ds):
    return f"사주 오행 분포(목:{counts['목']}, 화:{counts['화']}, 토:{counts['토']}, 금:{counts['금']}, 수:{counts['수']}) 및 월지 {mb} 조후 밸런스를 고려한 용신 분석"

def get_goshin_gwasook(yb, gender):
    return "고신살/과숙살 영향 분석 완료"

# 타임머신 통합 팩트 시트 추출 엔진 (연령/성별/혼인 지침 자동 통합)
def get_saju_fact_sheet(ys, yb, ms, mb, ds, db, hs, hb, name, gender, marital, 
                        birth_year=None, age=None,
                        dw_g_cur=None, dw_j_cur=None, curr_y_ganji=None, cur_wol_g=None, cur_wol_j=None, 
                        target_year=None, target_month=None, target_day=None, **kwargs):
    """
    지정된 연도/월/일 및 생년/성별/혼인 상태를 바탕으로
    연령, 연령대 지침, 성별 지침, 혼인 상태 지침을 자동 생성하고 팩트 시트를 바인딩합니다.
    """
    now_dt = dt_mod.datetime.now()
    calc_year = target_year if target_year else now_dt.year
    calc_month = target_month if target_month else now_dt.month
    calc_day = target_day if target_day else now_dt.day

    if age is not None:
        calc_age = age
    elif birth_year is not None:
        calc_age = calc_year - int(birth_year) + 1
    else:
        calc_age = 40

    # 🎯 [엔진 통합] 연령대, 성별, 혼인 상태 지침 자동 생성
    age_p = get_age_prompt(calc_age)
    gender_p = get_gender_prompt(gender)
    marital_p = get_marital_prompt(gender, marital)
    yukchin_r = get_yukchin_rule(gender, marital)

    ss_unsung_str = f"년주:{get_ss(ds, ys)}{get_ss(ds, yb)}({get_unsung(ds, yb)}) / 월주:{get_ss(ds, ms)}{get_ss(ds, mb)}({get_unsung(ds, mb)}) / 일주:{ds}(본인){get_ss(ds, db)}({get_unsung(ds, db)}) / 시주:{get_ss(ds, hs)}{get_ss(ds, hb)}({get_unsung(ds, hb)})"
    gyukgook, gyukgook_detail = get_gyukgook_detailed(ds, ys, ms, hs, mb)
    counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
    for c in [ys, yb, ms, mb, ds, db, hs, hb]: counts[get_color(c)] += 1
    oheng_str = f"목:{counts['목']} 화:{counts['화']} 토:{counts['토']} 금:{counts['금']} 수:{counts['수']}"

    ilju_lower_group = get_group_ss(get_ss(ds, db))
    
    dw_fact_str = "대운 정보 없음"
    if dw_g_cur and dw_j_cur:
        dw_che = get_group_ss(get_ss(ds, dw_g_cur))
        dw_yong = get_execution_yong(get_group_ss(get_ss(ds, dw_g_cur)), ilju_lower_group)
        dw_fact_str = f"체운(무대): {dw_che} / 용운(사건): {dw_yong} ➔ 도출 키워드: {get_matrix_keyword(dw_che, dw_yong)}"

    sewun_fact_str = "세운 정보 없음"
    sewun_ji_val = None
    if curr_y_ganji:
        s_gan, s_ji = curr_y_ganji[1][0], curr_y_ganji[1][1]
        sewun_ji_val = s_ji
        s_upper = get_group_ss(get_ss(s_gan, s_ji))
        s_yong = get_execution_yong(s_upper, ilju_lower_group)
        sewun_che = get_group_ss(get_ss(ds, dw_g_cur)) if dw_g_cur else "비겁"
        sewun_fact_str = f"체운(무대): {sewun_che} / 용운(사건): {s_yong} ➔ 도출 키워드: {get_matrix_keyword(sewun_che, s_yong)}"

    wol_fact_str = "월운 정보 없음"
    if cur_wol_g and cur_wol_j:
        w_upper = get_group_ss(get_ss(cur_wol_g, cur_wol_j))
        w_yong = get_execution_yong(w_upper, ilju_lower_group)
        w_che = get_group_ss(get_ss(ds, curr_y_ganji[1][0])) if curr_y_ganji else "비겁"
        wol_fact_str = f"체운(무대): {w_che} / 용운(사건): {w_yong} ➔ 도출 키워드: {get_matrix_keyword(w_che, w_yong)}"

    weekly_daily_res = get_weekly_daily_facts(ds, db, yb, calc_year, calc_month, calc_day)
    
    am_che = weekly_daily_res.get('m_che_first', '오전 체(무대)')
    am_yong = weekly_daily_res.get('am_yong', '오전 용(사건)')
    pm_che = weekly_daily_res.get('m_che_second', '오후 체(무대)')
    pm_yong = weekly_daily_res.get('pm_yong', '오후 용(사건)')
    
    daily_fact_str = f"오전 체용: [{am_che} + {am_yong}] / 오후 체용: [{pm_che} + {pm_yong}] (12운성: {weekly_daily_res.get('day_wunseong', '건록')}, 12신살: {weekly_daily_res.get('day_12shinsal', '망신살')})"

    yongshin_str = get_yongshin_analysis(counts, mb, ds)
    goshin_gwasook_str = get_goshin_gwasook(yb, gender)

    samhyung_fact_str = check_samhyung_facts([yb, mb, db, hb], dw_j_cur, sewun_ji_val, cur_wol_j)
    samjae_val = get_samjae(yb, db) if 'get_samjae' in globals() else "해당 없음"
    dw_end_val = calc_age + 9
    hang_un_vaults_val = get_hang_un_vaults_str(dw_j_cur, [ys, ms, ds, hs], [yb, mb, db, hb]) if dw_j_cur else "대운 입고 작용 없음"

    fact_data = {
        "ys": ys, "yb": yb, "ms": ms, "mb": mb, "ds": ds, "db": db, "hs": hs, "hb": hb,
        "ss_unsung_str": ss_unsung_str, "gyukgook_detail": gyukgook_detail,
        "yongshin_str": yongshin_str,
        "goshin_gwasook_str": goshin_gwasook_str,
        "samhyung_fact_str": samhyung_fact_str,
        "gongmang_actual": calculate_gongmang(ds, db),
        "shinsal_str": ", ".join(get_general_shinsal_filtered(2, [hs, ds, ms, ys], [hb, db, mb, yb], gender)),
        "s12_str": get_all_12_shinsal(yb, mb, db, hb),
        "won_guk_vaults_str": " ".join(check_vault_status([ys, ms, ds, hs], [yb, mb, db, hb], mb)),
        "oheng_counts_str": oheng_str,
        
        "samjae_str": samjae_val,
        "dw_end_age": dw_end_val,
        "hang_un_vaults_str": hang_un_vaults_val,
        
        "weekly_ganji_list": weekly_daily_res.get('weekly_ganji_list', '월~일 주간 간지 데이터'),
        "t_month": calc_month,
        "t_day": calc_day,
        "m_ilgan": ds,
        "m_ilji": db,
        "m_che_first": am_che,
        "am_yong": am_yong,
        "m_che_second": pm_che,
        "pm_yong": pm_yong,
        "day_wunseong": weekly_daily_res.get('day_wunseong', '건록'),
        "day_12shinsal": weekly_daily_res.get('day_12shinsal', '망신살'),
        "daily_fact_str": daily_fact_str,

        "cheon_eul": {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}.get(ds, '없음'),
        "curr_y": calc_year,
        "curr_m": calc_month,
        "curr_d": calc_day,
        "disp_name": name, "u_age": calc_age, "u_gender": gender, "u_marital": marital,
        "age_prompt": age_p,
        "gender_prompt": gender_p,
        "marital_prompt": marital_p,
        "yukchin_rule": yukchin_r,
        "dw_fact_str": dw_fact_str, 
        "sewun_fact_str": sewun_fact_str, 
        "wol_fact_str": wol_fact_str
    }
    fact_data.update(kwargs)
    return fact_data

def get_daeun_su_accurate(utc_dt, order):
    try:
        sun = ephem.Sun()
        def get_lon(dt):
            sun.compute(dt)
            return math.degrees(ephem.Ecliptic(sun).lon) % 360.0

        start_lon = get_lon(utc_dt)
        jeol_lons = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]
        
        if order == 1:
            t_lon_unwrapped = min([l for l in jeol_lons if l > start_lon] + [l + 360 for l in jeol_lons if l <= start_lon])
        else:
            t_lon_unwrapped = max([l for l in jeol_lons if l <= start_lon] + [l - 360 for l in jeol_lons if l > start_lon])
            
        search_dt = utc_dt
        step = dt_mod.timedelta(minutes=10) if order == 1 else dt_mod.timedelta(minutes=-10)
        
        for _ in range(6000):
            search_dt += step
            curr_lon = get_lon(search_dt)
            
            if order == 1 and curr_lon < start_lon and (start_lon - curr_lon) > 180:
                curr_lon += 360
            elif order == -1 and curr_lon > start_lon and (curr_lon - start_lon) > 180:
                curr_lon -= 360
                
            if (order == 1 and curr_lon >= t_lon_unwrapped) or (order == -1 and curr_lon <= t_lon_unwrapped):
                break
                
        total_days = abs((search_dt - utc_dt).total_seconds()) / 86400.0
        d_su = int(round(total_days / 3.0))
        
        if d_su == 0: d_su = 1
        elif d_su > 10: d_su = 10
        
        return d_su
    except: 
        return 1

# ==============================================================================
# 섹션 6. 궁합 및 택일(결혼/출산/방위) 정밀 연산 로직
# ==============================================================================
class UniversalPrintableGunghap:
    def __init__(self, applicant, partner_name, male, female, daeun_score=10):
        self.app, self.p_name, self.daeun_score = applicant, partner_name, daeun_score
        
        male = [m if m and len(m) >= 2 else "  " for m in (list(male) + ["  ", "  ", "  ", "  "])][:4]
        female = [f if f and len(f) >= 2 else "  " for f in (list(female) + ["  ", "  ", "  ", "  "])][:4]
        
        self.m_g = [male[3][0], male[2][0], male[1][0], male[0][0]]
        self.m_j = [male[3][1], male[2][1], male[1][1], male[0][1]]
        self.f_g = [female[3][0], female[2][0], female[1][0], female[0][0]]
        self.f_j = [female[3][1], female[2][1], female[1][1], female[0][1]]
        
        self.logic_flags, self.details = {}, []

    def get_ji_rel(self, j1, j2):
        j1, j2 = _to_hanja(j1), _to_hanja(j2)
        if not j1 or not j2 or j1=="?" or j2=="?": return "무"
        s = {j1, j2}
        if s in [{'子','丑'}, {'寅','亥'}, {'卯','戌'}, {'辰','酉'}, {'巳','申'}, {'午','未'}]: return "육합"
        if s in [{'寅','卯'}, {'卯','辰'}, {'寅','辰'}, {'巳','午'}, {'午','未'}, {'巳','未'}, {'申','酉'}, {'酉','戌'}, {'申','戌'}, {'亥','子'}, {'子','丑'}, {'亥','丑'}]: return "방합"
        if s in [{'申','子'}, {'子','辰'}, {'申','辰'}, {'寅','午'}, {'午','戌'}, {'寅','戌'}, {'亥','卯'}, {'卯','未'}, {'亥','未'}, {'巳','酉'}, {'酉','丑'}, {'巳','丑'}]: return "반합"
        if s in [{'子','午'}, {'丑','未'}, {'寅','申'}, {'卯','酉'}, {'辰','戌'}, {'巳','亥'}]: return "충"
        if s in [{'子','未'}, {'丑','午'}, {'寅','酉'}, {'卯','申'}, {'辰','亥'}, {'巳','戌'}]: return "원진"
        if s in [{'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}, {'子','卯'}]: return "형"
        if s in [{'子','酉'}, {'丑','辰'}, {'寅','亥'}, {'卯','午'}, {'巳','申'}, {'未','戌'}]: return "파"
        if s in [{'子','未'}, {'丑','午'}, {'寅','巳'}, {'卯','辰'}, {'申','亥'}, {'酉','戌'}]: return "해"
        return "무"

    def count_elements(self, gans, jjis):
        counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
        for char in gans + jjis:
            c = _to_hanja(char)
            if c in "甲乙寅卯": counts['목'] += 1
            elif c in "丙丁巳午": counts['화'] += 1
            elif c in "戊己辰戌丑未": counts['토'] += 1
            elif c in "庚辛申酉": counts['금'] += 1
            elif c in "壬癸亥子": counts['수'] += 1
        return counts

    def run_universal_logic(self):
        m_g, m_j, f_g, f_j = self.m_g, self.m_j, self.f_g, self.f_j
        il_rel = self.get_ji_rel(m_j[2], f_j[2])
        
        if il_rel == "육합": s1 = 25
        elif il_rel in ["방합", "반합"]: s1 = 21
        elif il_rel == "무": s1 = 17
        elif il_rel in ["파", "해"]: s1 = 12
        elif il_rel in ["형", "원진"]: s1 = 8
        elif il_rel == "충": s1 = 5
        else: s1 = 17
        p1 = int((s1 / 25) * 100)

        s2 = 5 
        n_rel, w_rel, si_rel = self.get_ji_rel(m_j[0], f_j[0]), self.get_ji_rel(m_j[1], f_j[1]), self.get_ji_rel(m_j[3], f_j[3]) 
        if n_rel in ["육합", "방합", "반합"]: s2 += 2
        elif n_rel == "충": s2 -= 1
        if w_rel in ["육합", "방합", "반합"]: s2 += 2
        elif w_rel == "충": s2 -= 1
        if si_rel in ["육합", "방합", "반합"]: s2 += 1
        s2 = max(0, min(10, s2))
        p2 = int((s2 / 10) * 100)

        m_ec, f_ec = self.count_elements(m_g, m_j), self.count_elements(f_g, f_j)
        s3 = 5
        for e in ['목','화','토','금','수']:
            if m_ec[e] == 0 and f_ec[e] >= 2: s3 += 2 
            if f_ec[e] == 0 and m_ec[e] >= 2: s3 += 2 
            if m_ec[e] >= 4 and f_ec[e] >= 4: s3 -= 2 
        s3 = max(0, min(10, s3))
        p3 = int((s3 / 10) * 100)

        s4 = 5
        bad_iljus, goran, nache = ["甲寅", "乙卯", "庚申", "辛酉", "戊辰", "戊戌"], ["甲寅", "乙巳", "丁巳", "戊申", "辛亥"], ["甲子", "乙巳", "丁卯", "庚午", "辛亥", "癸酉"] 
        m_ilju, f_ilju = m_g[2] + m_j[2], f_g[2] + f_j[2]
        if m_ilju in bad_iljus or m_ilju in goran or m_ilju in nache: s4 -= 1
        if f_ilju in bad_iljus or f_ilju in goran or f_ilju in nache: s4 -= 1
        s4 = max(0, min(5, s4))
        p4 = int((s4 / 5) * 100)

        s5 = min(10, self.daeun_score)
        p5 = int((s5 / 10) * 100)

        risk = 0.0
        if il_rel == "충": risk += 0.10 
        elif il_rel in ["형", "원진"]: risk += 0.05 
        
        def count_ss_groups(dc, chars):
            res = {'비겁':0, '식상':0, '재성':0, '관성':0, '인성':0}
            for c in chars:
                if c and c not in ["?", " ", "-"]:
                    try:
                        ss = get_group_ss(get_ss(dc, c))
                        if ss in res: res[ss] += 1
                    except: pass
            return res
        
        m_ss, f_ss = count_ss_groups(m_g[2], m_g + m_j), count_ss_groups(f_g[2], f_g + f_j)
        if m_ss['비겁'] >= 4: risk += 0.05 
        if m_ss['재성'] == 0: risk += 0.05 
        if f_ss['식상'] >= 4: risk += 0.05 
        if f_ss['관성'] >= 4 or f_ss['관성'] == 0: risk += 0.05 

        risk = min(0.20, risk) 
        p6_safety = int((1.0 - risk) * 100)

        base_bonus = 40 
        sub_total = base_bonus + s1 + s2 + s3 + s4 + s5
        self.final_score = max(40, min(100, int(sub_total * (1.0 - risk))))

        if self.final_score >= 90: self.grade = "천생연분 (최고의 인연)"
        elif self.final_score >= 85: self.grade = "상생연분 (함께하면 좋은 인연)"
        elif self.final_score >= 80: self.grade = "동행연분 (편안하고 안정적인 인연)"
        elif self.final_score >= 70: self.grade = "보완연분 (서로를 채워주는 인연)"
        elif self.final_score >= 60: self.grade = "성장연분 (이해하며 맞춰가는 인연)"
        else: self.grade = "조율연분 (인내와 배려가 필요한 인연)"

        self.details = [
            {"label": "내면의 유대감", "pct": p1, "color": "#9b59b6"},
            {"label": "환경 조화", "pct": p2, "color": "#2ecc71"},
            {"label": "기운 상호보완", "pct": p3, "color": "#3498db"},
            {"label": "특수 기운", "pct": p4, "color": "#f1c40f"},
            {"label": "대운 기상도 조화", "pct": p5, "color": "#8e44ad"},
            {"label": "리스크 방어력", "pct": p6_safety, "color": "#e74c3c"}
        ]

def get_gunghap_data(s_y, s_m, s_d, s_t, m_marital, f_y, f_m, f_d, f_t, f_marital, marital_status):
    def get_oh_class(c): return f"color-{get_color(c)}"

    def get_time_ganji_fixed(day_gan, time_str):
        if "시간 모름" in time_str or "모름" in time_str: return "", ""
        start_idx = time_str.find('(')
        end_idx = time_str.find(')')
        raw_ji = time_str[start_idx+1:end_idx] if (start_idx != -1 and end_idx != -1) else "子"
        raw_ji = raw_ji.replace('朝', '').replace('夜', '')
        
        t_ji = K2H_JI.get(raw_ji, raw_ji)
        gan_arr = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        ji_arr = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        if day_gan in gan_arr and t_ji in ji_arr:
            d_idx, j_idx = gan_arr.index(day_gan), ji_arr.index(t_ji)
            t_gan = gan_arr[((d_idx % 5) * 2 + j_idx) % 10]
            return t_gan, t_ji
        return "", ""

    def _get_person_data(y, m, d, t, gender, name, marital):
        h, m_val = 0, 0
        if ":" in t:
            col_idx = t.find(":")
            try:
                h = int(t[col_idx-2:col_idx].strip())
                m_val = int(t[col_idx+1:col_idx+3].strip())
            except: pass

        y_pillar, m_pillar, _ = get_true_year_month_pillar(y, m, d, h, m_val)
        _, _, d_pillar = get_ganji_from_date(y, m, d)
        
        t_gan, t_ji = get_time_ganji_fixed(d_pillar[0], t)
        
        gans, jjis = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]], [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
        ys, yb = y_pillar[0], y_pillar[1]
        ms, mb = m_pillar[0], m_pillar[1]
        ds, db = d_pillar[0], d_pillar[1]        
        hs, hb = t_gan, t_ji

        order_dir = 1 if (GAN.index(ys) % 2 == 0) == (gender == '남성') else -1
        calc_d = get_daeun_su_accurate(datetime(y, m, d), order_dir)

        curr_year = datetime.now().year
        age = curr_year - y + 1

        direction_str = "순행" if order_dir == 1 else "역행"
        daewun_data_list = get_daeun_data_list(ms, mb, ds, yb, order_dir, calc_d, age)
        daewun = (daewun_data_list, direction_str, calc_d, get_oh_class)

        counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
        for c in gans + jjis:
            oh = get_color(c)
            if oh in counts: counts[oh] += 1
        
        gan_rel = "".join([f"<td style='border:1px solid #444;'>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])
        gan_ss = f"<td style='border:1px solid #444;'>{get_ss(ds,gans[0])}</td><td style='border:1px solid #444; font-weight:900;'>일원</td><td style='border:1px solid #444;'>{get_ss(ds,gans[2])}</td><td style='border:1px solid #444;'>{get_ss(ds,gans[3])}</td>"
        gan_row = "".join([f"<td class='{get_oh_class(g)}' style='border:1px solid #444; font-size:24px; font-weight:900;'>{g}</td>" for g in gans])
        ji_row = "".join([f"<td class='{get_oh_class(j)}' style='border:1px solid #444; font-size:24px; font-weight:900;'>{j}</td>" for j in jjis])
        ji_ss = "".join([f"<td style='border:1px solid #444;'>{get_ss(ds,j)}</td>" for j in jjis])
        jijanggan = "".join([f"<td>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])
        
        ji_rel_rows = ""
        for l_idx, r_idx in enumerate([1, 2, 0, 3]):
            b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
            current_ji = jjis[r_idx]
            if r_idx == 0: dir_label = f"({current_ji})→"
            elif r_idx == 1: dir_label = f"←({current_ji})→"
            elif r_idx == 2: dir_label = f"←({current_ji})→"
            else: dir_label = f"←({current_ji})"
            
            cells = "".join([
                f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; "
                f"font-weight:900; border-top:0px solid transparent !important; border-bottom:{b_bot}; "
                f"border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>"
                f"{dir_label if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci])}</td>" 
                for ci in range(4)
            ])
            
            lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
            ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"
            
        unsung = "".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])
        shinsal = "".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])
        gen_shinsal = "".join([f"<td style='vertical-align:top; border:1px solid #444 !important; font-size:11px;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis, gender)[:3])}</td>" for i in range(4)])

        guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
        master = [
            calc_d, counts['목'], counts['화'], counts['토'], counts['금'], counts['수'], 
            guiin_map.get(_to_hanja(ds), '없음'), calculate_gongmang(ys, yb), calculate_gongmang(ds, db), 
            "#2E7D32" if get_samjae(yb, db) == "해당 없음" else "#1A237E", get_samjae(yb, db)
        ]

        gyukgook_name, _ = get_gyukgook_detailed(ds, ys, ms, hs, mb)
        gongmang_val = calculate_gongmang(ds, db)

        return {
            "table": [None, gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal], 
            "master": master, 
            "daewun": daewun,
            "ys": ys, "yb": yb, "ms": ms, "mb": mb, "ds": ds, "db": db, "hs": hs, "hb": hb,
            "gyukgook": gyukgook_name, "gongmang": gongmang_val
        }

    m_res = _get_person_data(s_y, s_m, s_d, s_t, "남성", "신청인", m_marital)
    w_res = _get_person_data(f_y, f_m, f_d, f_t, "여성", "상대방", f_marital)
    
    return {
        "m_table": m_res["table"], "m_master": m_res["master"], "m_daewun": m_res["daewun"],
        "w_table": w_res["table"], "w_master": w_res["master"], "w_daewun": w_res["daewun"],
        
        "m_ys": m_res["ys"], "m_yb": m_res["yb"],
        "m_ms": m_res["ms"], "m_mb": m_res["mb"],
        "m_ds": m_res["ds"], "m_db": m_res["db"],
        "m_hs": m_res["hs"], "m_hb": m_res["hb"],
        "m_gongmang_actual": m_res["gongmang"],
        "m_gyukgook": m_res["gyukgook"],
        
        "f_ys": w_res["ys"], "f_yb": w_res["yb"],
        "f_ms": w_res["ms"], "f_mb": w_res["mb"],
        "f_ds": w_res["ds"], "f_db": w_res["db"],
        "f_hs": w_res["hs"], "f_hb": w_res["hb"],
        "f_gongmang_actual": w_res["gongmang"],
        "f_gyukgook": w_res["gyukgook"],
        
        "m_golden": f"{m_res['ds']}일간 중심의 성향 분석",
        "f_golden": f"{w_res['ds']}일간 중심의 성향 분석",
        
        "calc_gyukgook": "시공명리 격국 분석",
        "db_header": "초연 시공명리 심층 궁합 분석 리포트",
        "ai_saju_mapping": "시공간의 교차점 분석",
        "yukchin_rule": "육친 및 십이운성 상생법 적용",
        "marital_info": marital_status
    }

def get_optimized_delivery_days(start_date, end_date, male_jjis, female_jjis, last_period_date=None, period_cycle=30):
    male_jiji = male_jjis[0] if male_jjis else "子"
    female_jiji = female_jjis[0] if female_jjis else "丑"
    
    candidate_results = []
    current_date = start_date
    
    while current_date <= end_date:
        conception_date = current_date 
        delivery_date = conception_date + dt_mod.timedelta(days=268)
        
        if start_date <= delivery_date <= end_date:
            if last_period_date:
                gestation_days = (delivery_date - last_period_date).days
                if gestation_days > 0:
                    g_weeks = gestation_days // 7
                    if g_weeks < 37 or g_weeks > 41:
                        current_date += dt_mod.timedelta(days=1)
                        continue
            
            time_slots_eval = get_all_time_scores_for_date(delivery_date, male_jiji, female_jiji)
            best_slot = time_slots_eval[0] if time_slots_eval else {'time_str': '00:30 ~ 01:29 (조자)시', 'ji': '子', 'score': 70.0}
            
            try:
                y_p, m_p, d_p = get_ganji_from_date(delivery_date.year, delivery_date.month, delivery_date.day)
                h_p = f"{best_slot['ji']}時"
                four_pillars = f"{y_p}년 {m_p}월 {d_p}일 {h_p}"
            except:
                four_pillars = "사주간지 분석중"

            candidate_results.append({
                'date': delivery_date.strftime("%Y-%m-%d"),
                'delivery_dt': delivery_date,
                'conception_date': conception_date.strftime("%Y-%m-%d"),
                'score': best_slot['score'],
                'four_pillars': four_pillars,
                'best_time': {
                    'time_str': best_slot['time_str'],
                    'time_pillar': f"{best_slot['ji']}時",
                    'ji': best_slot['ji']
                },
                'all_time_slots': time_slots_eval
            })
            
        current_date += dt_mod.timedelta(days=2)
        
    candidate_results.sort(key=lambda x: x['score'], reverse=True)
    
    filtered_results = []
    for item in candidate_results:
        if not any(abs((item['delivery_dt'] - selected['delivery_dt']).days) < 25 for selected in filtered_results):
            filtered_results.append(item)
            if len(filtered_results) >= 5:
                break
                
    return filtered_results

def evaluate_saju_harmony(delivery_date, y_pillar, m_pillar, d_pillar, male_jiji, female_jiji, time_ji):
    day_gan = d_pillar[0]
    day_ji = d_pillar[1]
    month_ji = m_pillar[1]
    
    date_seed = (delivery_date.year * 10000 + delivery_date.month * 100 + delivery_date.day)
    base_score = 72.0 + (date_seed % 11) * 1.2
    
    samhap_groups = [{'申','子','辰'}, {'巳','酉','丑'}, {'寅','午','戌'}, {'亥','卯','未'}]
    yukhap_pairs = {('子','丑'), ('寅','亥'), ('卯','戌'), ('辰','酉'), ('巳','申'), ('午','未')}
    chung_pairs = {('子','午'), ('丑','未'), ('寅','申'), ('卯','酉'), ('辰','戌'), ('巳','亥')}
    
    score = base_score
    
    dt_pair = (day_ji, time_ji) if day_ji < time_ji else (time_ji, day_ji)
    if dt_pair in yukhap_pairs:
        score += 8.0
    elif any({day_ji, time_ji}.issubset(g) for g in samhap_groups):
        score += 6.0
    elif dt_pair in chung_pairs:
        score -= 10.0
        
    for p_ji in [male_jiji, female_jiji]:
        p_pair = (p_ji, time_ji) if p_ji < time_ji else (time_ji, p_ji)
        if p_pair in yukhap_pairs:
            score += 4.0
        elif any({p_ji, time_ji}.issubset(g) for g in samhap_groups):
            score += 3.0
        elif p_pair in chung_pairs:
            score -= 5.0
            
    ji_order = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    if time_ji in ji_order:
        t_idx = ji_order.index(time_ji)
        score += ((t_idx * 5 + delivery_date.day * 2) % 9) * 0.5

    return min(98.5, max(60.0, round(score, 1)))

def get_all_time_scores_for_date(delivery_date, male_jiji, female_jiji):
    try:
        y_pillar, m_pillar, d_pillar = get_ganji_from_date(delivery_date.year, delivery_date.month, delivery_date.day)
    except:
        y_pillar, m_pillar, d_pillar = "甲子", "丙寅", "戊辰"

    time_slots = [
        {'time_str': '00:30 ~ 01:29 (조자)시', 'ji': '子'},
        {'time_str': '01:30 ~ 03:29 (축)시', 'ji': '丑'},
        {'time_str': '03:30 ~ 05:29 (인)시', 'ji': '寅'},
        {'time_str': '05:30 ~ 07:29 (묘)시', 'ji': '卯'},
        {'time_str': '07:30 ~ 09:29 (진)시', 'ji': '辰'},
        {'time_str': '09:30 ~ 11:29 (사)시', 'ji': '巳'},
        {'time_str': '11:30 ~ 13:29 (오)시', 'ji': '午'},
        {'time_str': '13:30 ~ 15:29 (미)시', 'ji': '未'},
        {'time_str': '15:30 ~ 17:29 (신)시', 'ji': '申'},
        {'time_str': '17:30 ~ 19:29 (유)시', 'ji': '酉'},
        {'time_str': '19:30 ~ 21:29 (술)시', 'ji': '戌'},
        {'time_str': '21:30 ~ 23:29 (해)시', 'ji': '亥'}
    ]
    
    evaluated = []
    for slot in time_slots:
        score = evaluate_saju_harmony(delivery_date, y_pillar, m_pillar, d_pillar, male_jiji, female_jiji, slot['ji'])
        evaluated.append({
            'time_str': slot['time_str'],
            'ji': slot['ji'],
            'score': score
        })
    
    evaluated.sort(key=lambda x: x['score'], reverse=True)
    return evaluated
