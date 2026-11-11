# ==============================================================================
# engine.py (ver 88.8 - 상품별 정리판)
# ==============================================================================
import os
import streamlit as st
import math
import datetime as dt_mod
from datetime import datetime
import pytz
import ephem
import re
from korean_lunar_calendar import KoreanLunarCalendar

# ==============================================================================
# PART 0. 시스템 상수 · 한자/한글 변환 · 공용 유틸 (모든 상품 공통)
# ==============================================================================

K2H_GAN = {
    '갑':'甲', '甲':'甲', '을':'乙', '乙':'乙', 
    '병':'丙', '丙':'丙', '정':'丁', '丁':'丁', 
    '무':'戊', '戊':'戊', '기':'己', '己':'己', 
    '경':'庚', '庚':'庚', '신':'辛', '辛':'辛', 
    '임':'壬', '壬':'壬', '계':'癸', '癸':'癸'
}

K2H_JI = {
    '자':'子', '子':'子', '축':'丑', '丑':'丑', '인':'寅', '寅':'寅',
    '묘':'卯', '卯':'卯', '진':'辰', '辰':'辰', '사':'巳', '巳':'巳',
    '오':'午', '午':'午', '미':'未', '未':'未', '신':'申', '申':'申',
    '유':'酉', '酉':'酉', '술':'戌', '戌':'戌', '해':'亥', '亥':'亥'
}

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

JI  = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

JIJANGGAN = {
    '子': ['壬', '-', '癸'], '丑': ['癸', '辛', '己'], '寅': ['戊', '丙', '甲'],
    '卯': ['甲', '-', '乙'], '辰': ['乙', '癸', '戊'], '巳': ['戊', '庚', '丙'],
    '午': ['丙', '己', '丁'], '未': ['丁', '乙', '己'], '申': ['戊', '壬', '庚'],
    '酉': ['庚', '-', '辛'], '戌': ['辛', '丁', '戊'], '亥': ['戊', '甲', '壬']
}

_AM_GAN_HAP = {frozenset(x) for x in ["甲己", "乙庚", "丙辛", "丁壬", "戊癸"]}

def _has_amhap(a, b):
    """두 지지의 지장간(여기·중기·정기 전부) 속 천간끼리 합이 하나라도 있으면 True (암합)."""
    ga = [g for g in JIJANGGAN.get(a, []) if g != '-']
    gb = [g for g in JIJANGGAN.get(b, []) if g != '-']
    return any(frozenset((x, y)) in _AM_GAN_HAP for x in ga for y in gb)

def get_amyeonghap_list(gans, jjis):
    """천간(시·일·월·년)과 지지(시·일·월·년) 지장간 속 천간의 합(암명합) 목록. 같은 기둥 안도 포함.
    반환: [(지지칸 번호, 천간 글자, 천간 자리 이름, 지장간 글자), ...]"""
    _lab = ["시", "일", "월", "년"]
    out = []
    for ci in range(4):
        jj = _to_hanja(jjis[ci]) if ci < len(jjis) else ""
        hidden = [g for g in JIJANGGAN.get(jj, []) if g != '-']
        for gi in range(4):
            g = _to_hanja(gans[gi]) if gi < len(gans) else ""
            if not g or g in ("-", "?"):
                continue
            for x in hidden:
                if frozenset((g, x)) in _AM_GAN_HAP:
                    out.append((ci, g, _lab[gi], x))
    return out

def get_amyeonghap_cells(gans, jjis):
    """원국표용: 시·일·월·년 지지 칸마다 '丙(시)↔辛' 모양의 줄바꿈 문자열 4개."""
    lst = get_amyeonghap_list(gans, jjis)
    return ["<br>".join(f"{g}({lab})↔{x}" for ci2, g, lab, x in lst if ci2 == ci) or "-" for ci in range(4)]

def get_amyeonghap_facts(gans, jjis):
    """풀이용 사실문. 일간·일지가 낀 것을 앞에 둔다."""
    _lab = ["시", "일", "월", "년"]
    lst = get_amyeonghap_list(gans, jjis)
    if not lst:
        return "(없음 — 글에 쓰지 말 것)"
    def _pri(t):
        ci, g, lab, x = t
        return (0 if lab == "일" else 1, 0 if ci == 1 else 1, ci)
    lines = []
    for ci, g, lab, x in sorted(lst, key=_pri):
        same = " (같은 기둥 안)" if _lab[ci] == lab else ""
        lines.append(f"{lab}간 {g}과 {_lab[ci]}지 {jjis[ci]} 속 {x}가 합{same}")
    return " / ".join(lines)

# 🚨 한자 간지 → 한글 발음 변환 (기존 K2H_GAN / K2H_JI 표를 거꾸로 재사용, 별도 표 관리 안 함)
_H2K_MAP = {}

for _k, _v in {**K2H_GAN, **K2H_JI}.items():
    if _k != _v:
        _H2K_MAP[_v] = _k

def get_han_reading(hanja_str):
    """한자 간지 문자열(예: '戊午')을 한글 발음(예: '무오')으로 변환"""
    return ''.join(_H2K_MAP.get(ch, ch) for ch in hanja_str)

def _to_hanja(char):
    if not char or char in ["?", " ", "-"]: return ""
    char = str(char).strip()
    return K2H_GAN.get(char, K2H_JI.get(char, char))

def _to_hanja_ji(char):
    if not char or char in ["?", " ", "-"]: return ""
    char = str(char).strip()
    return K2H_JI.get(char, K2H_GAN.get(char, char))

def extract_ganji(text):
    if not text: return ""
    return re.sub(r'[^가-힣一-龥]', '', text)

def get_oh_class(ganji):
    oh = get_color(ganji)
    return f"color-{oh}" if oh != '무' else ""

def get_master_system_prompt():
    return (
        "당신은 대한민국 최고의 정통 명리학이자 초연시공명리학 권위자 '초연 박사'입니다. "
        "주어진 사주 팩트 데이터에 근거하여 엄정하게 분석하십시오.\n\n"
        "🚨 [최고 엄수 규칙]: 어떠한 경우에도 텍스트에 색상을 입히지 마십시오! "
        "Streamlit 색상 마크다운이나 HTML 색상 태그 사용을 엄격히 금지합니다. "
        "오직 순수한 검정색 텍스트와 기본 기호만 사용하여 출력하십시오."
    )

# ==============================================================================
# PART 1. 공통 명리 코어 (1-x · 2-x · 3-x 모든 상품이 함께 쓰는 계산)
# ==============================================================================

# ---- 1-A. 만세력 · 절기 · 간지 계산 ----

def get_total_time_adjustment(dt):
    adj = -30
    if dt_mod.datetime(1954, 3, 21) <= dt <= dt_mod.datetime(1961, 8, 9, 23, 59): adj = 0
    si = [
        (dt_mod.datetime(1948,5,31), dt_mod.datetime(1948,9,22)),
        (dt_mod.datetime(1949,3,31), dt_mod.datetime(1949,9,30)),
        (dt_mod.datetime(1950,4,1), dt_mod.datetime(1950,9,10)),
        (dt_mod.datetime(1951,5,6), dt_mod.datetime(1951,9,9)),
        (dt_mod.datetime(1954,3,21), dt_mod.datetime(1954,5,5)),
        (dt_mod.datetime(1955,4,6), dt_mod.datetime(1955,9,22)),
        (dt_mod.datetime(1956,5,20), dt_mod.datetime(1956,9,30)),
        (dt_mod.datetime(1957,5,5), dt_mod.datetime(1957,9,22)),
        (dt_mod.datetime(1958,5,4), dt_mod.datetime(1958,9,21)),
        (dt_mod.datetime(1959,5,4), dt_mod.datetime(1959,9,20)),
        (dt_mod.datetime(1960,5,1), dt_mod.datetime(1960,9,18)),
        (dt_mod.datetime(1987,5,10,2), dt_mod.datetime(1987,10,11,3)),
        (dt_mod.datetime(1988,5,8,2), dt_mod.datetime(1988,10,9,3))
    ]
    for s, e in si:
        if s <= dt <= e: adj -= 60; break
    return adj

def lunar_to_solar(y, m, d, is_leap=False):
    """음력 날짜(y, m, d)를 양력(year, month, day)으로 변환"""
    klc = KoreanLunarCalendar()
    if klc.setLunarDate(y, m, d, is_leap):
        return klc.solarYear, klc.solarMonth, klc.solarDay
    return y, m, d  # 변환 실패 시 원본 반환 (안전장치)

def get_true_year_month_pillar(year, month, day, hour, minute):
    kst = pytz.timezone('Asia/Seoul')
    dt_kst = kst.localize(datetime(year, month, day, hour, minute))
    dt_utc = dt_kst.astimezone(pytz.utc)
 
    sun = ephem.Sun()
    _ed = ephem.Date(dt_utc)
    sun.compute(dt_utc, epoch=_ed)                          # 그 순간의 기준점으로 계산
    lon = math.degrees(ephem.Ecliptic(sun, epoch=_ed).lon) % 360.0
 
    actual_year = year
    if month <= 2 and lon < 315.0:
        actual_year -= 1
 
    year_idx = (actual_year - 1984) % 60
    y_gan_kor = GAN[year_idx % 10]
    y_ji_kor = JI[year_idx % 12]
 
    if 315 <= lon < 345: m_ji_idx = 2
    elif 345 <= lon or lon < 15: m_ji_idx = 3
    elif 15 <= lon < 45: m_ji_idx = 4
    elif 45 <= lon < 75: m_ji_idx = 5
    elif 75 <= lon < 105: m_ji_idx = 6
    elif 105 <= lon < 135: m_ji_idx = 7
    elif 135 <= lon < 165: m_ji_idx = 8
    elif 165 <= lon < 195: m_ji_idx = 9
    elif 195 <= lon < 225: m_ji_idx = 10
    elif 225 <= lon < 255: m_ji_idx = 11
    elif 255 <= lon < 285: m_ji_idx = 0
    elif 285 <= lon < 315: m_ji_idx = 1
 
    y_gan_idx = year_idx % 10
    start_month_gan_idx = ((y_gan_idx % 5) * 2 + 2) % 10
    m_offset = (m_ji_idx - 2) % 12
    m_gan_kor = GAN[(start_month_gan_idx + m_offset) % 10]
    m_ji_kor = JI[m_ji_idx]
 
    y_pillar = K2H_GAN[y_gan_kor] + K2H_JI[y_ji_kor]
    m_pillar = K2H_GAN[m_gan_kor] + K2H_JI[m_ji_kor]
 
    return y_pillar, m_pillar, lon

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

def _get_term_day(y, m):
    """해당 월의 절입일(월주가 바뀌는 날)을 찾아 반환"""
    _, p1, _ = get_true_year_month_pillar(y, m, 1, 12, 0)
    for d in range(2, 12):
        _, pd, _ = get_true_year_month_pillar(y, m, d, 23, 59)
        if pd != p1:
            return d, pd
    return 5, p1

def _true_term_day(y, m):
    """그 달의 절입일(일)을 정밀 월주 계산으로 찾습니다. 실패하면 기존 _get_term_day로 대신합니다."""
    try:
        _, p_end, _ = get_true_year_month_pillar(y, m, 28, 12, 0)   # 절입 이후의 월주
        for d in range(1, 16):
            _, p, _ = get_true_year_month_pillar(y, m, d, 23, 59)   # 그날 자정 직전의 월주
            if p == p_end:
                return d
    except Exception:
        pass
    return _get_term_day(y, m)[0]

def get_seun_half_periods(target_year):
    y = int(target_year)
    try:
        ipchun = _true_term_day(y, 2)          # 올해 입춘 날짜(일)
        ipchu = _true_term_day(y, 8)           # 올해 입추 날짜(일)
        ipchun_next = _true_term_day(y + 1, 2) # 다음 해 입춘 날짜(일)
        end1 = dt_mod.date(y, 8, ipchu) - dt_mod.timedelta(days=1)
        end2 = dt_mod.date(y + 1, 2, ipchun_next) - dt_mod.timedelta(days=1)
        return (
            f"{y}년 2월 {ipchun}일(입춘) ~ {end1.year}년 {end1.month}월 {end1.day}일(입추 전날)",
            f"{y}년 8월 {ipchu}일(입추) ~ {end2.year}년 {end2.month}월 {end2.day}일(입춘 전날)",
        )
    except Exception:
        return f"{y}년 2월 4일(입춘) ~ {y}년 8월 6일(입추 전날)", f"{y}년 8월 7일(입추) ~ {y+1}년 2월 3일(입춘 전날)"

def get_jeolgi_month_no(d):
    """날짜(d)가 속한 절기월의 월 번호를 돌려줍니다. 예) 11월 4일 → 10 (입동 11월 7일 전이라 아직 한로월·무술월)
    절입일 당일부터 새 달로 칩니다. 1월 1~4일처럼 전년도 12월 절기월에 걸리는 날은 그대로 둡니다."""
    try:
        if d.month == 1:
            return 1
        if d.day < _true_term_day(d.year, d.month):
            return d.month - 1
    except Exception:
        pass
    return d.month

def get_wolun_tail_fact(ds, db, tail_g, tail_j, sewun_che):
    """양력 달의 첫머리(전달 절기월의 끝자락) 구간의 월운 체용 키워드를 만듭니다.
    끝자락은 전달 절기월의 후반기(지지 기준)이므로 전달 월지의 체를 씁니다. sewun_che는 현재 세운의 활성 체."""
    ilju_lower_group = get_group_ss(get_ss(ds, db))
    che = get_group_ss(get_ss(ds, tail_j))
    yong = get_execution_yong(che, ilju_lower_group)
    kw = get_matrix_keyword(sewun_che, yong)
    return f"- [전달 끝자락 월운 {tail_g}{tail_j}: 체(후반기/지지) {che} + 실행({yong}) ➔ 키워드: [{kw}]]"

def get_wolun_calendar_periods(target_year, target_month):
    """양력 한 달을 절기에 맞춰 세 구간으로 나눕니다.
    ① 전달 절기월의 끝자락(1일 ~ 이번 달 절입 전날) ② 상반기(절입 ~ 중기 전날) ③ 후반기(중기 ~ 말일)
    돌려주는 값: (끝자락, 상반기, 후반기). 끝자락이 없는 달(절입이 1일)은 끝자락이 빈 글자("")입니다."""
    y = int(target_year)
    m = int(target_month)
    JUL = {1: "소한", 2: "입춘", 3: "경칩", 4: "청명", 5: "입하", 6: "망종", 7: "소서", 8: "입추", 9: "백로", 10: "한로", 11: "입동", 12: "대설"}
    JUNG = {1: "대한", 2: "우수", 3: "춘분", 4: "곡우", 5: "소만", 6: "하지", 7: "대서", 8: "처서", 9: "추분", 10: "상강", 11: "소설", 12: "동지"}
    last_day = (dt_mod.date(y + (m == 12), m % 12 + 1, 1) - dt_mod.timedelta(days=1)).day
    jul_day = _true_term_day(y, m)
    jung_day = jul_day + 15
    tail = ""
    if jul_day > 1:
        tail = f"{y}년 {m:02d}월 01일 ~ {y}년 {m:02d}월 {jul_day-1:02d}일({JUL[m]} 전날)"
    first = f"{y}년 {m:02d}월 {jul_day:02d}일({JUL[m]}) ~ {y}년 {m:02d}월 {jung_day-1:02d}일({JUNG[m]} 전날)"
    second = f"{y}년 {m:02d}월 {jung_day:02d}일({JUNG[m]}) ~ {y}년 {m:02d}월 {last_day:02d}일(월말)"
    return tail, first, second

def get_wolun_half_periods(target_year, target_month):
    y = int(target_year)
    m = int(target_month)
    next_m = m + 1 if m < 12 else 1
    next_y = y if m < 12 else y + 1
    JUL = {1: "소한", 2: "입춘", 3: "경칩", 4: "청명", 5: "입하", 6: "망종", 7: "소서", 8: "입추", 9: "백로", 10: "한로", 11: "입동", 12: "대설"}
    JUNG = {1: "대한", 2: "우수", 3: "춘분", 4: "곡우", 5: "소만", 6: "하지", 7: "대서", 8: "처서", 9: "추분", 10: "상강", 11: "소설", 12: "동지"}
    try:
        jul_day = _true_term_day(y, m)                 # 이달 절입일(일)
        next_jul_day = _true_term_day(next_y, next_m)  # 다음 달 절입일(일)
        jung_day = jul_day + 15                          # 중기 (엔진의 전·후반기 판정과 같은 기준)
        end2 = dt_mod.date(next_y, next_m, next_jul_day) - dt_mod.timedelta(days=1)
        return (
            f"{y}년 {m:02d}월 {jul_day:02d}일({JUL[m]}) ~ {y}년 {m:02d}월 {jung_day-1:02d}일({JUNG[m]} 전날)",
            f"{y}년 {m:02d}월 {jung_day:02d}일({JUNG[m]}) ~ {end2.year}년 {end2.month:02d}월 {end2.day:02d}일({JUL[next_m]} 전날)",
        )
    except Exception:
        terms_map = {1: (5, 20), 2: (4, 19), 3: (6, 21), 4: (5, 20), 5: (5, 21), 6: (6, 21), 7: (7, 23), 8: (7, 23), 9: (8, 23), 10: (8, 23), 11: (7, 22), 12: (7, 22)}
        jul_day, jung_day = terms_map.get(m, (5, 20))
        next_jul_day = terms_map.get(next_m, (5, 20))[0]
        return f"{y}년 {m:02d}월 {jul_day:02d}일 ~ {y}년 {m:02d}월 {jung_day-1:02d}일", f"{y}년 {m:02d}월 {jung_day:02d}일 ~ {next_y}년 {next_m:02d}월 {next_jul_day-1:02d}일"

# ---- 1-B. 십성 · 12운성 · 12신살 · 삼재 ----

def get_color(c):
    c = _to_hanja(c)
    if not c: return "무"   # 빈 글자('?', 공백, '-')는 오행 없음 (빈 글자를 목으로 세던 오류 방지)
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
    dg_h = _to_hanja(dg)
    ji_h = _to_hanja(ji)
    if not dg_h or not ji_h: return "-"
    table = {
        '甲': "亥子丑寅卯辰巳午未申酉戌", '丙': "寅卯辰巳午未申酉戌亥子丑",
        '戊': "寅卯辰巳午未申酉戌亥子丑", '庚': "巳午未申酉戌亥子丑寅卯辰",
        '壬': "申酉戌亥子丑寅卯辰巳午未", '乙': "午巳辰卯寅丑子亥戌酉申未",
        '丁': "酉申未午巳辰卯寅丑子亥戌", '己': "酉申未午巳辰卯寅丑子亥戌",
        '辛': "子亥戌酉申未午巳辰卯寅丑", '癸': "卯寅丑子亥戌酉申未午巳辰"
    }
    idx = table.get(dg_h, "").find(ji_h)
    if idx != -1:
        return ["장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"][idx]
    return "-"

def get_12_shinsal(base_ji, target_ji):
    b_h = _to_hanja_ji(base_ji)
    t_h = _to_hanja_ji(target_ji)
    if not b_h or not t_h: return "-"
    jis = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    if b_h not in jis or t_h not in jis: return "-"
    samhap_geob_map = {'申':'巳', '子':'巳', '辰':'巳', '寅':'亥', '午':'亥', '戌':'亥', '巳':'寅', '酉':'寅', '丑':'寅', '亥':'申', '卯':'申', '未':'申'}
    geob_start_ji = samhap_geob_map.get(b_h, "")
    if not geob_start_ji: return "-"
    start_idx = jis.index(geob_start_ji)
    target_idx = jis.index(t_h)
    diff = (target_idx - start_idx) % 12
    return ["겁살", "재살", "천살", "지살", "년살", "월살", "망신살", "장성살", "반안살", "역마살", "육해살", "화개살"][diff]

def get_dual_12_shinsal(yb, db, target_ji):
    try:
        y_shinsal = get_12_shinsal(yb, target_ji)
        d_shinsal = get_12_shinsal(db, target_ji)
        if not y_shinsal or y_shinsal == "-": y_shinsal = "-"
        if not d_shinsal or d_shinsal == "-": d_shinsal = "-"
        if y_shinsal == "-" and d_shinsal == "-": return "-"
        if y_shinsal == d_shinsal: return f"{y_shinsal}"
        else: return f"{y_shinsal} ({d_shinsal})"
    except: return "-"

def get_all_dual_12_shinsal(yb, db, target_list):
    try: return [get_dual_12_shinsal(yb, db, j) for j in target_list]
    except: return ["-"] * len(target_list) if target_list else ["-", "-", "-", "-"]

def get_all_12_shinsal(yb, mb, db, hb):
    try:
        results = [get_12_shinsal(yb, yb), get_12_shinsal(yb, mb), get_12_shinsal(yb, db), get_12_shinsal(yb, hb)]
        return ", ".join(results)
    except: return "년지 기준 12신살 풀이 완료"

def get_12_shinsal_fact_str(yb, db, jjis, dw_j=None, sewun_j=None, wolun_j=None, ilun_j=None):
    """년지 기준·일지 기준 12신살을 원국 4기둥과 대운·세운·월운·일운 지지에 대해 팩트 문자열로 만든다."""
    def _ok(j):
        return j not in (None, "", "?", "-", " ")
    names = ["시지", "일지", "월지", "년지"]
    parts = []
    for n, j in zip(names, jjis):
        if _ok(j):
            parts.append(f"원국 {n}({_to_hanja_ji(j)}): 년지기준 {get_12_shinsal(yb, j)} / 일지기준 {get_12_shinsal(db, j)}")
    for label, j in [("대운", dw_j), ("세운", sewun_j), ("월운", wolun_j), ("일운", ilun_j)]:
        if _ok(j):
            parts.append(f"{label} 지지({_to_hanja_ji(j)}): 년지기준 {get_12_shinsal(yb, j)} / 일지기준 {get_12_shinsal(db, j)}")
    return " / ".join(parts) if parts else "12신살 정보 없음"

# ─────────────────────────────────────────────────────────────
# 12신살 사전 · 동주포태(욕·묘·절·사) 전용 규칙  (신살명리학 기준, 일지 기준이 주)
# ─────────────────────────────────────────────────────────────
_S12_BOOK = {
    '겁살': {
        '뜻': "내 것을 지키려다 오히려 빼앗기거나 일에 휘말리기 쉬운 기운. 욕심을 줄이고 신중하게 움직이면 손해를 막을 수 있음",
        '기둥': {'년': "어린 시절 객지살이나 살림의 어려움을 겪었을 수 있음", '월': "부모·형제와 정이 얇을 수 있고 건강 관리가 중요함", '시': "자식 일이나 말년의 건강·살림을 미리 준비해 두면 좋음"},
        '십성': {'비겁': "형제·동료와 인연이 엷을 수 있고, 동업과 지나친 욕심은 조심", '식상': "하는 일이 막히거나, 실속 없이 넓히면 힘들어질 수 있음. 건강도 챙길 것", '재성': "{재} 일이나 돈 문제에서 손해·속임을 조심", '관성': "직업 변화가 많고 {관} 쪽에 신경 쓸 일이 생길 수 있음. 구설 조심", '인성': "부모와 떨어져 지내거나 계약·문서에서 불리할 수 있으니 서명 전에 꼼꼼히 확인"},
        '행운': "씀씀이가 커지거나 투기·도박성 투자에 끌리기 쉬운 때. 절제하고, 증개축·계약은 절차를 지켜 처리. 주도권 다툼은 한 발 물러서면 편안함",
    },
    '재살': {
        '뜻': "일이 꼬이거나 구설·다툼에 얽히기 쉬운 기운(수옥살). 서두르지 않고 말과 문서를 조심하면 무난함",
        '기둥': {'년': "어린 시절 건강이 약했거나 이곳저곳 옮겨 다닌 흔적", '월': "부모·형제와 정이 얇고 종교·정신세계에 관심이 생길 수 있음", '시': "마음고생은 있어도 재물 복은 따르는 편"},
        '십성': {'비겁': "동료·친지와 거리가 생기기 쉬움", '식상': "겉과 속이 달라 일이 잘 안 풀릴 수 있으니 말과 행동을 맞추면 좋음", '재성': "{재} 문제로 재물 손실이나 이성 문제를 조심", '관성': "{관}이나 직장 일로 힘든 일이 생길 수 있고, 서두르면 일이 깨질 수 있음", '인성': "부모 걱정, 학업·문서 일이 순탄치 않을 수 있어 생활 기반을 다지는 것이 좋음"},
        '행운': "남의 기운에 눌리거나 분실·실수가 생기기 쉬운 때. 반면 공부·시험·치장에는 유리한 힘이 있음. 끝무렵에는 방심하지 말 것",
    },
    '천살': {
        '뜻': "하늘이 시험하듯 뜻밖의 일이 닥치기 쉬운 기운. 자존심을 낮추고 베풀면 오히려 도움을 얻음",
        '기둥': {'년': "조상 덕이 약하다고 느끼거나 외로움·소극적인 마음이 있을 수 있음", '월': "가족 사이 마음이 맞지 않거나 건강을 살필 일이 있고, 배우자의 뜻밖의 행동이 있을 수 있음", '시': "일이 매듭지어지지 않고 말이 많아질 수 있어 말년에 베풀며 지내면 도움을 받음"},
        '십성': {'비겁': "잘난 체·자만을 낮추면 좋음", '식상': "반항심·구설이 있고 시작은 좋으나 끝이 약할 수 있음", '재성': "애는 많이 쓰는데 실속이 적을 수 있고 마음이 조급해짐", '관성': "직장·주거 이동, 신경이 예민해지는 일(두통 등)에 유의", '인성': "의식주가 불안하게 느껴지고 감정 기복이 있을 수 있음"},
        '행운': "문서 계약·매매는 서두르지 말 것. 자존심이 세져 남 밑에서 일하기 힘들 수 있고, 직업·신앙의 변화가 올 수 있는 때",
    },
    '지살': {
        '뜻': "새로운 일을 처음 시작하는 기운(시작살). 이동·이사·해외와 인연이 있고, 움직일수록 길이 열림",
        '기둥': {'년': "일찍 타향에서 자수성가하나 부모와 떨어질 수 있음", '월': "이동이 잦고 {배우}와 마음이 어긋날 때가 있으며 사고에 조심", '일': "재능에 비해 결과가 늦게 보일 수 있고, 먼 곳이나 이동이 많은 일과 인연이 있음. 일지가 寅申巳亥이면 한 번 바닥을 친 뒤 크게 일어나는 흐름", '시': "부모·형제와 인연이 엷으나 말년에 귀한 결실을 얻는 흐름"},
        '십성': {'비겁': "친인척·동료의 자본으로 사업, 일찍 고향을 떠남", '식상': "바쁜 데 돈은 안 되는 일이 많을 수 있음", '재성': "재물에 대한 집착이 강하나 뜻대로 되기 어려울 수 있음", '관성': "먼 곳 사업·무역·직장 이동으로 재물을 얻는 흐름", '인성': "참견이 많고 씀씀이가 커질 수 있으며 방랑 기질이 있음. 편인이면 아이디어가 뛰어남"},
        '행운': "이사·여행·이동의 일이 생기는 때. 일지와 같은 해에는 반복되는 일이 생기고, 충이 오면 이동 중 사고를 조심",
    },
    '년살': {
        '뜻': "매력과 인기, 사람을 끄는 기운(도화살). 표현력과 예술 감각이 좋고, 사람 관계 속에서 빛남",
        '기둥': {'년': "이성운이 좋고 일찍 인연이 닿는 경우가 많음", '월': "활동적이고 명랑하나 부모 덕은 약할 수 있음", '시': "나이 들어서도 적극적이고 멋진 삶을 추구함"},
        '십성': {'비겁': "감정을 거침없이 드러내는 경향", '식상': "예능·표현·감성 분야 재능이 뛰어남", '재성': "{재} 덕이 있고 사람을 상대하는 사업에 인연", '관성': "편관이면 이성에 대한 관심이 큼, 정관이면 반듯하고 단정함", '인성': "정인은 반듯하고 단정함, 편인은 호기심이 지나쳐 관계에서 조심할 일이 생길 수 있음"},
        '행운': "사람 만남과 인기가 늘고 소비도 늘어나는 때. 전문 분야는 이름이 알려지기 좋고, 결과가 더디더라도 참고 견디면 기회가 옴",
    },
    '월살': {
        '뜻': "앞길이 잘 안 보여 답답하고 일이 더디게 풀리는 기운(고초살). 기도·공부·봉사 같은 마음 닦는 일로 길을 찾으면 좋음",
        '기둥': {'년': "윗대에 어려움이 있었음을 뜻함", '월': "부모·형제와 인연이 엷고 일이 더디게 풀리는 흐름", '시': "자식 문제로 마음고생이 있다가 자식은 잘 풀림"},
        '십성': {},
        '행운': "일의 진척이 느리고 마음이 답답한 때. 심리·역사·종교·철학 같은 본원 공부나 남을 돕는 일로 풀어가면 좋음",
    },
    '망신살': {
        '뜻': "숨기고 싶던 일이 드러나 체면이 상하기 쉬운 기운. 평소 미뤄 둔 일을 이때 정리하면 오히려 얻음이 있음",
        '기둥': {'년': "일찍 변화가 많고 일찍 고향을 떠남", '월': "몸이 약해지기 쉽고 대인관계에 신경 써야 함", '시': "자식 일과 말년의 살림에 신경 쓸 일이 있음"},
        '십성': {'비겁': "형제·동료 때문에 마음 상할 일이 있을 수 있음", '식상': "남명은 가까운 사람 사이, 여명은 자식 일로 체면 상할 일을 조심", '재성': "{재} 때문에 체면이나 재물에 신경 쓸 일이 생길 수 있음", '관성': "{관}·사회적 명예와 관련해 마음 쓸 일이 생길 수 있음", '인성': "어머니와 관련해 신경 쓸 일이 생길 수 있음"},
        '행운': "속마음이 드러나기 쉬운 때. 뜻밖의 돈이 들어오기도 하고, 만남은 짧고 이별이 길 수 있음. 새 이성·부하 인연은 다툼에 주의",
    },
    '장성살': {
        '뜻': "가장 힘이 오르는 기운. 우두머리·중심인물의 자리에 서기 쉽고 승진·확장의 힘이 있음. 다만 분위기를 몰고 가려는 마음은 내려놓을 것",
        '기둥': {'년': "윗대가 힘 있는 집안이었음을 뜻함", '월': "객지에서 성공하나 부모·형제 덕은 약함", '시': "남의 도움 없이 자수성가하며, 본인과 자손이 크게 성공할 흐름"},
        '십성': {},
        '행운': "승진·승급 등 길한 일이 있는 때. 지살과 합하면 더욱 좋고, 화개와 합하면 차분히 가라앉음",
    },
    '반안살': {
        '뜻': "말 위의 안장처럼 안정되고 반듯한 기운. 성공·출세·번영의 힘이며 귀인의 도움이 따름",
        '기둥': {'년': "특별한 명문이 아니라면 평범하고 무난한 집안", '월': "마음이 온화하고 스스로 일어서는 운", '시': "부귀의 길함이 있고 자식이 현달함. 일지가 사생지이면서 시지 반안이면 글재주가 뛰어남"},
        '십성': {},
        '행운': "하늘이 돕듯 어려운 일도 잘 풀리고, 학생은 진학·직장인은 승진·사업자는 기반이 마련됨. 다만 새 사업 확장보다 지키는 것이 이로움",
    },
    '역마살': {
        '뜻': "움직이고 옮겨 다니는 기운. 이동·이사·유학·해외·출장과 인연이 있고, 움직이는 일에서 기회가 옴",
        '기둥': {'년': "일찍 고향을 떠나 먼 곳에서 공부하거나 객지 경험이 많음", '월': "후원을 받아 재물을 빨리 이루고 먼 곳과 인연", '시': "직장·주거 이동이 많고 속세의 얽매임을 벗어나려는 마음이 있음"},
        '십성': {'비겁': "자수성가형, 일찍 고향을 떠나고 감정 기복이 있을 수 있음", '식상': "박학다식하고 능수능란하며 사람들의 관심을 모음", '재성': "이재 능력이 뛰어나고 먼 곳 인연이 있으나 {배우}와 거리가 생길 수 있음", '관성': "직장·주거 이동, 권력과 거리가 있고 체면을 중시함", '인성': "학문을 좇아 이동이 많고 윗사람 덕은 약할 수 있음"},
        '행운': "이사·이동·여행·출장이 많은 때. 일지와 같은 해에는 움직임이 더 커지고 새로운 세계로 나아가는 계기가 됨",
    },
    '육해살': {
        '뜻': "몸과 마음이 가라앉고 기운이 막히기 쉬운 기운. 서두르지 않고 건강과 사람 사이를 살피면 무난함",
        '기둥': {'년': "부모의 보살핌이 부족한 가운데 스스로 공부한 흔적", '월': "신앙심이 깊은 배우자와 인연이 있고 성격이 급함", '시': "분주한데 얻는 것이 적다고 느끼기 쉬움"},
        '십성': {},
        '행운': "이유 없이 몸이 무겁거나 힘이 빠지기 쉬운 때. 여명은 친정·시댁 일에 마음 쓸 일이 있을 수 있음. 도화(년살) 운과 겹치면 오히려 길함",
    },
    '화개살': {
        '뜻': "마음을 안으로 모아 연구·종교·예술·학문에 몰두하는 기운. 겉은 조용하나 속이 깊고, 다시 일어서는 힘(재생)이 있음",
        '기둥': {'년': "부모와 인연이 엷고 홀로 서는 힘이 강함", '월': "형제 덕은 약하나 본인은 크게 발복하는 바탕", '일': "스스로 일어서고 종교·정신세계에 마음이 감", '시': "연구·기술의 결실로 재물 복을 얻고 말년이 편안함"},
        '십성': {'비겁': "자기 세계가 강하고 자유로운 성향", '식상': "능수능란하고 호기심이 많으나 바쁘고 허무감도 올 수 있음", '재성': "재물에 알뜰하고 이해타산이 밝음", '관성': "공명심은 있으나 우유부단·약속 지키기에 신경 쓸 것", '인성': "은둔·신비·종교·학문 쪽으로 깊이 들어감"},
        '행운': "멈췄던 일이 다시 풀리고 헤어진 인연이 다시 이어지는 때(복고). 지살·장성살과 만나면 이름과 재물이 따름",
    },
}
_S12_ORDER = ["겁살", "재살", "천살", "지살", "년살", "월살", "망신살", "장성살", "반안살", "역마살", "육해살", "화개살"]
 
 
def _s12_ss_group(ss):
    if ss in ("비견", "겁재"): return "비겁"
    if ss in ("식신", "상관"): return "식상"
    if ss in ("편재", "정재"): return "재성"
    if ss in ("편관", "정관"): return "관성"
    if ss in ("편인", "정인"): return "인성"
    return ""
 
 
def get_12shinsal_book_facts(ds, yb, db, jjis, dw_j=None, sewun_j=None, gender="남"):
    """일지 기준 12신살 사전(원국 기둥별·십성별·행운). 일지 기준이 주."""
    gender = "남" if str(gender).startswith("남") else "여"
    def _ok(j):
        return j not in (None, "", "?", "-", " ")
    jae = "아내" if gender == "남" else "아버지·시어머니"
    gwan = "자식·직장" if gender == "남" else "남편·직장"
    bae = "아내" if gender == "남" else "남편"
    def _fx(t):
        return t.replace("{재}", jae).replace("{관}", gwan).replace("{배우}", bae)
    out = []
    for n, key, j in zip(["시지", "일지", "월지", "년지"], ["시", "일", "월", "년"], jjis):
        if not _ok(j): continue
        jh = _to_hanja_ji(j)
        nm = get_12_shinsal(db, jh)
        d = _S12_BOOK.get(nm)
        if not d: continue
        ss = get_ss(ds, jh)
        grp = _s12_ss_group(ss)
        line = f"원국 {n}({jh})는 일지 기준 '{nm}'이며 이 자리의 십성은 {ss}: {d['뜻']}"
        pil = d['기둥'].get(key)
        if pil: line += f" / 이 자리에서는 → {_fx(pil)}"
        sip = d['십성'].get(grp)
        if sip and key != "일":
            if nm == "년살" and grp in ("관성", "인성"):
                if ss == "편관": sip = "편관이면 이성에 대한 관심이 큼"
                elif ss == "정관": sip = "정관이면 반듯하고 단정함"
                elif ss == "정인": sip = "정인이면 반듯하고 단정함"
                elif ss == "편인": sip = "편인이면 호기심이 지나쳐 관계에서 조심할 일이 생길 수 있음"
            if nm == "지살" and grp == "인성" and ss == "편인":
                sip += " (편인이라 아이디어와 창의성이 뛰어남)"
            line += f" / 십성으로 보면 → {_fx(sip)}"
        out.append(line)
        ny = get_12_shinsal(yb, jh)
        dy = _S12_BOOK.get(ny)
        if ny == nm:
            out[-1] += " (년지 기준으로도 같은 신살)"
        elif dy:
            ly = f"원국 {n}({jh})는 년지 기준(보조, 사회·집안에서의 모습) '{ny}': {dy['뜻']}"
            py = dy['기둥'].get(key)
            if py: ly += f" / 이 자리에서는 → {_fx(py)}"
            sy = dy['십성'].get(grp)
            if sy: ly += f" / 십성으로 보면 → {_fx(sy)}"
            out.append(ly)
    for label, j in [("대운", dw_j), ("세운", sewun_j)]:
        if not _ok(j): continue
        jh = _to_hanja_ji(j)
        nm = get_12_shinsal(db, jh)
        d = _S12_BOOK.get(nm)
        if not d: continue
        ss = get_ss(ds, jh)
        grp = _s12_ss_group(ss)
        line = f"{label} 지지({jh})는 일지 기준 '{nm}' 운이며 십성은 {ss}: {_fx(d['행운'])}"
        sip = d['십성'].get(grp)
        if sip: line += f" / 십성으로 보면 → {_fx(sip)}"
        out.append(line)
        ny = get_12_shinsal(yb, jh)
        dy = _S12_BOOK.get(ny)
        if dy and ny != nm:
            ly = f"{label} 지지({jh})는 년지 기준(보조) '{ny}' 운: {_fx(dy['행운'])}"
            sy = dy['십성'].get(grp)
            if sy: ly += f" / 십성으로 보면 → {_fx(sy)}"
            out.append(ly)
    return " || ".join(out) if out else "12신살 사전 정보 없음"
 
_DONGJU = {
    '동주욕': {
        'list': ['甲子', '乙巳', '庚午', '辛亥'],
        'head': "일간이 일지에서 목욕(씻고 옷을 갈아입는 자리)에 앉은 일주. 사교성과 매력이 좋고 변화·이동·새로운 만남을 즐김. 마음이 쉽게 바뀌고 시작에 비해 마무리가 약해지기 쉬우니 꾸준함이 열쇠. 허영과 이성에 대한 호기심은 절제하면 좋음",
        'ss': {'식상': "표현력·말솜씨·미각·예술 감각이 뛰어나고 멋을 즐기는 기질", '관성': "정관이면 단정하고 원칙적, 편관이면 외향적이고 활동적임", '인성': "다정다감하나 주변에 휩쓸려 주체성이 약해지기 쉽고, 어머니가 미인이거나 정이 깊음"},
        'extra': {'충': "일지가 충을 받으면 부부 사이에 변화가 생기기 쉬우니 서로 배려와 대화가 필요함", '합': "일지가 합을 이루면 이성 인연이 풍성하나 유혹에 흔들리지 않도록 절제가 필요함"},
    },
    '동주입묘': {
        'list': ['丙戌', '丁丑', '戊戌', '己丑', '壬辰', '癸未'],
        'head': "일간이 일지의 창고(묘고)에 들어앉은 일주. 알뜰하고 낭비를 싫어하며 속이 깊고 혼자 생각하는 시간이 많음. 금융·재정·연구·종교·활인(남을 살리는 일)에 적성이 있고, 가진 것을 쉽게 내놓지 않는 성향이 있음",
        'ss': {'식상': "식상입묘: 재능·표현이 안으로 쌓여 드러나기까지 시간이 걸리고, 자식과 거리감이 생길 수 있음", '재성': "재성입묘: 재물을 모으고 지키는 힘이 크나 쓰는 데 인색할 수 있음. 재물 창고로서 아버지·{재}와의 인연을 살필 것", '관성': "관성입묘: 직장·명예가 안으로 감춰지는 모양. 남명은 자식, 여명은 남편과의 인연을 살필 것. 여명은 재정이나 마음을 남편 몰래 쌓는 경향", '비겁': "일간 자신이 창고에 든 모양으로 자기 세계가 강하고 고독을 즐김"},
        'female_gwan': "여명 관성입묘(남편성이 창고에 듦): 남편을 가볍게 여기거나 마음이 멀어지기 쉬우니 존중하는 마음을 가지면 좋음. 남자가 많은 직장은 무난하나 결혼이 늦어질 수 있음",
        'extra': {'합': "일간이 합으로 묶이면 입묘의 작용이 멈춰 있는 상태", '충형': "일지가 충·형을 만나면 창고가 열려 입묘의 작용이 나타남", '백호': "백호살이 함께 있으면 충·형이 올 때 더 신중하게 움직이는 것이 좋음"},
    },
    '동주절': {
        'list': ['甲申', '乙酉', '庚寅', '辛卯'],
        'head': "일간이 일지에서 절(끊어졌다 다시 시작하는 자리)에 앉은 일주. 환경 변화에 민감하고 분위기에 쉽게 동화되며, 마음먹은 일이 중간에 끊겼다 다시 이어지기 쉬움. 거절을 잘 못하고 고집과 변덕이 섞여 있으니, 일을 시작할 때 끝까지 이어갈 구조를 만들어 두면 좋음. 새롭게 거듭나는 힘도 큼",
        'ss': {'비겁': "비겁 절: 애써도 얻는 것이 적다고 느끼기 쉬우니 동업은 신중히", '식상': "식상 절: 안으로 가라앉는 시기가 있어 재능이 늦게 꽃핌", '재성': "재성 절: 얻는 것보다 쓰는 것이 많을 수 있으니 지출 관리가 중요", '관성': "관성 절: 한 길만 고집하는 외골수 기질이 있음. 융통성을 가지면 직장운이 좋아짐", '인성': "인성 절: 어머니와 정이 담담할 수 있고, 학문은 끈기 있게 이어가면 곤곤함이 풀림"},
        'extra': {'일지': "일지가 절이므로 배우자를 인정하고 치켜세워 주면 오히려 어려워질 수 있으니 서로 존중하는 균형이 필요함. 남명은 중년 이후 아내에게 양보하는 모습이 늘 수 있음"},
    },
    '동주사': {
        'list': ['甲午', '乙亥', '庚子', '辛巳'],
        'head': "일간이 일지에서 사(힘이 다 빠져 멈추는 자리)에 앉은 일주. 몸을 쓰는 일보다 머리·전문 영역에서 빛나며, 고집과 자기 방식이 강해 논쟁에서 물러서기 어려움. 일이 멈추거나 끊기고 사람과 갈라지는 일이 있을 수 있으나, 전문가의 길을 걸으면 오히려 빛남",
        'ss': {'식상': "식상 사: 자식과 이별하거나 자식 보기가 어려울 수 있고, 건록을 놓은 상관(갑오·경자)은 직장 상사와 부딪히기 쉬움(관성을 밀어냄). 전문 분야로 나아가면 좋음", '인성': "인성 사: 부모와 일찍 떨어지거나 학업이 순탄치 않을 수 있고, 고부 사이 마음을 쓸 일이 있을 수 있음", '관성': "관성 사: 남명은 자식과 거리가 생기기 쉽고, 여명은 남편과 떨어지는 일을 살필 것. 건강과 인연을 소중히 하면 좋음"},
        'extra': {},
    },
}
 
 
def get_dongju_pothae_facts(ds, db, jjis, gender="남", dw_j=None, sewun_j=None, gans=None):
    """동주욕·동주입묘·동주절·동주사 전용 규칙. 해당 일주일 때만 풀이 글감을 돌려준다."""
    gender = "남" if str(gender).startswith("남") else "여"
    ilju = f"{_to_hanja(ds)}{_to_hanja_ji(db)}"
    kind = None
    for k, v in _DONGJU.items():
        if ilju in v['list']:
            kind = k; break
    if not kind:
        return "동주포태 해당 없음"
    d = _DONGJU[kind]
    jae = "아내" if gender == "남" else "아버지·시어머니"
    out = [f"일주 {ilju}({kind}): {d['head']}"]
    ss = get_ss(ds, _to_hanja_ji(db))
    grp = _s12_ss_group(ss)
    # 일지의 십성 (사·절·묘·욕이 어느 십성 위에 놓였는가)
    if kind == '동주사' and grp == '식상' and ilju in ('乙亥',):
        grp = '인성'
    sx = d['ss'].get(grp)
    if sx:
        out.append(f"일지 십성 {ss} 기준 → {sx.replace('{재}', jae)}")
    if kind == '동주입묘' and grp == '관성' and gender == "여":
        out.append(d['female_gwan'])
    others = [_to_hanja_ji(j) for i, j in enumerate(jjis) if i != 1 and j not in (None, "", "?", "-", " ")]
    haeng = [_to_hanja_ji(j) for j in (dw_j, sewun_j) if j not in (None, "", "?", "-", " ")]
    db_h = _to_hanja_ji(db)
    _CH = {frozenset(p) for p in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")}
    _HP = {frozenset(p) for p in ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")}
    won_ch = any(frozenset((db_h, o)) in _CH for o in others)
    won_hp = any(frozenset((db_h, o)) in _HP for o in others)
    hg_ch = any(frozenset((db_h, o)) in _CH for o in haeng)
    hg_hp = any(frozenset((db_h, o)) in _HP for o in haeng)
    if kind == '동주욕':
        if won_ch: out.append(d['extra']['충'])
        if won_hp: out.append(d['extra']['합'])
        if hg_ch: out.append("지금 대운·세운 지지가 일지와 충을 이루는 시기이니, 부부 사이에 변화가 생기기 쉬워 서로 배려와 대화가 필요함")
        if hg_hp: out.append("지금 대운·세운 지지가 일지와 합을 이루는 시기이니, 이성 인연과 표현 욕구가 커져 유혹에 흔들리지 않도록 절제가 필요함")
        if gender == "여" and ilju in ('乙巳', '辛亥'):
            out.append("여명의 을사·신해일주는 고란살이 겹쳐 있어 배우자 인연의 굴곡을 살피면 좋음")
    elif kind == '동주입묘':
        _HG = {frozenset(p) for p in ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")}
        ds_h = _to_hanja(ds)
        og = [_to_hanja(g) for i, g in enumerate(gans or []) if i != 1 and g not in (None, "", "?", "-", " ")]
        if any(frozenset((ds_h, g)) in _HG for g in og):
            out.append(d['extra']['합'] + " (현재 원국에 일간의 합이 있음)")
        out.append(d['extra']['충형'] + (" (현재 원국에 충이 있음)" if won_ch else ""))
        if hg_ch: out.append("지금 대운·세운 지지가 일지와 충을 이뤄 창고가 열리는 시기이니 입묘의 작용이 나타날 수 있음")
        if ilju in BAEKHO_GANJI:
            out.append(d['extra']['백호'])
    elif kind == '동주절':
        out.append(d['extra']['일지'])
    return " || ".join(out)

# ─────────────────────────────────────────────────────────────
# 돌싱(이혼·사별) 재혼·새 인연 글감 (신살명리학 + 배우자궁 기준, 단정 없이 흐름만)
# ─────────────────────────────────────────────────────────────
_GAN_YEOJU = {'甲寅', '乙卯', '丙午', '丁巳', '戊辰', '戊戌', '己丑', '己未', '庚申', '辛酉', '壬子', '癸亥'}
_JI_TTI = {'子': '쥐', '丑': '소', '寅': '호랑이', '卯': '토끼', '辰': '용', '巳': '뱀', '午': '말', '未': '양', '申': '원숭이', '酉': '닭', '戌': '개', '亥': '돼지'}
_JI_HAP = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅', '卯': '戌', '戌': '卯',
           '辰': '酉', '酉': '辰', '巳': '申', '申': '巳', '午': '未', '未': '午'}
 
 
def get_remarriage_facts(ds, gans, jjis, gender, marital, dw_g=None, dw_j=None):
    """돌싱(이혼·사별)일 때만 쓰는 재혼·새 인연 글감. gans·jjis 는 [시, 일, 월, 년] 순서.
    과거 인연의 모양(원국의 배우자성·배우자궁)과 새 인연의 모양·때를 사실문으로 만든다. 사건은 단정하지 않는다."""
    if str(marital).strip() != "돌싱":
        return "혼인 상태가 돌싱이 아니므로 재혼 풀이는 쓰지 않음"
    is_f = str(gender).startswith("여")
    star = ("정관", "편관") if is_f else ("정재", "편재")
    star_nm = "남편별(관성)" if is_f else "아내별(재성)"
    ds_h = _to_hanja(ds)
    gh = [_to_hanja(g) for g in gans]
    jh = [_to_hanja_ji(j) for j in jjis]
    if len(jh) < 4 or not jh[1] or jh[1] not in JI:
        return "재혼 풀이에 필요한 일지 정보가 부족함"
    dj = jh[1]
    out = []
    # 1) 배우자성의 구조 (정·편 혼잡 / 없음 / 개수)
    names = ["시", "일", "월", "년"]
    cnt = {"정": 0, "편": 0}
    for i in range(4):
        if i != 1 and gh[i] and gh[i] not in ("?", "-", ""):
            s = get_ss(ds_h, gh[i])
            if s in star: cnt[s[0]] += 1
        if jh[i] and jh[i] in JI:
            s = get_ss(ds_h, jh[i])
            if s in star: cnt[s[0]] += 1
    tot = cnt["정"] + cnt["편"]
    if cnt["정"] and cnt["편"]:
        out.append(f"{star_nm}이 정(正)과 편(偏) 두 가지로 섞여 있어(혼잡) 인연의 모양이 하나로 모이지 않고 마음이 여러 갈래로 갈리기 쉬운 구조. 지난 인연도 이 구조의 영향으로 읽을 수 있고, 새 인연은 한 사람에게 마음을 모으는 쪽이 길함")
    elif tot == 0:
        out.append(f"사주에 {star_nm}이 드러나 있지 않아 인연을 붙잡기 어렵고 인연이 늦게 닿는 구조. 운에서 {star_nm}이 들어오는 때가 새 인연의 문이 열리는 때")
    elif tot >= 3:
        out.append(f"{star_nm}이 {tot}개로 많아 인연의 무게와 부담이 큰 구조. 상대에게 기대는 마음이 커지지 않도록 균형을 잡는 것이 중요")
    else:
        out.append(f"{star_nm}이 {tot}개로 적당히 자리해 인연의 줄기는 갖춘 구조")
    # 2) 배우자성 공망
    try:
        gm_set = set()
        if gh[3] and jh[3]: gm_set |= set(calculate_gongmang(gh[3], jh[3]))
        if ds_h and dj: gm_set |= set(calculate_gongmang(ds_h, dj))
        gm_set.discard("-")
        hit = []
        for i in range(4):
            if jh[i] and jh[i] in gm_set and get_ss(ds_h, jh[i]) in star:
                hit.append(f"{names[i]}지({jh[i]})")
        if hit:
            out.append(f"{star_nm}이 인연의 빈자리에 놓인 곳: {', '.join(hit)}. 마음의 기대에 비해 인연이 허전하게 느껴지기 쉬우니, 그 빈자리가 채워지는 운(해당 글자가 들어오는 때)에 새 인연이 실속 있게 맺히기 쉬움(이미 채워졌다고 단정하지 말 것. 아래 띠 항목과 이어서 쓰지 말 것)")
        if dj in gm_set:
            out.append(f"배우자궁(일지 {dj}) 자체가 인연의 빈자리에 놓여 인연이 늦거나 허전함을 느끼기 쉬운 구조")
    except Exception:
        pass
    # 3) 일지의 특수 기운 (간여지동·백호·합충)
    ilju = f"{ds_h}{dj}"
    if ilju in _GAN_YEOJU:
        out.append("일주가 간여지동(일간과 일지가 같은 기운)이라 자기 뜻이 또렷해 배우자와 각자의 영역을 지킬 때 오히려 오래감. 새 인연은 서로의 영역을 존중하는 사람이 좋음")
    if ilju in BAEKHO_GANJI:
        out.append("일주에 백호대살이 있어 인연에 큰 굴곡이 한 번 지나가기 쉬운 기운. 새 인연에서는 평상심과 건강 관리가 힘이 됨")
    for i in (0, 2, 3):
        o = jh[i]
        if not o or o not in JI: continue
        rel = get_ji_rel_set(dj, o)
        if rel and rel != "-":
            tags = [t.strip() for t in rel.split(",")]
            neg = [t for t in tags if t in ("충", "형", "원진", "파", "해")]
            if neg:
                out.append(f"일지({dj})와 {names[i]}지({o})가 {'·'.join(neg)} 관계라 배우자궁이 흔들린 흔적. 새 인연에서는 같은 부딪힘이 반복되지 않도록 속도를 천천히 맞추는 것이 길함")
    # 4) 새 인연이 닿기 쉬운 띠(합) — 단정하지 말고 끌림의 방향으로만
    hap_ji = _JI_HAP.get(dj)
    if hap_ji:
        out.append(f"배우자궁과 합이 되는 글자는 {hap_ji}({_JI_TTI.get(hap_ji, '')}띠)로, 이 띠의 기운을 가진 사람에게 끌리기 쉬움(만남을 단정하지 말 것)")
    # 5) 현재 대운이 새 인연에 어떤 무대인가
    if dw_g and dw_j:
        dws = get_ss(ds_h, _to_hanja(dw_g))
        dwj = get_ss(ds_h, _to_hanja_ji(dw_j))
        t = []
        if dws in star or dwj in star:
            t.append(f"현재 대운에 {star_nm.split('(')[0]}({dws if dws in star else dwj})이 들어와 새 인연이 열리기 쉬운 무대")
        if _JI_HAP.get(dj) == _to_hanja_ji(dw_j):
            t.append(f"현재 대운 지지({_to_hanja_ji(dw_j)})가 일지와 합이라 인연이 묶이기 쉬운 시기")
        o = get_ji_rel_set(dj, _to_hanja_ji(dw_j))
        if o and "충" in o:
            t.append(f"현재 대운 지지({_to_hanja_ji(dw_j)})가 일지와 충이라 관계에 변화가 큰 시기이니 서두르지 말 것")
        if t: out.append(" / ".join(t))
        else: out.append("현재 대운에는 배우자별이 직접 들어오지 않아, 대운 자체는 인연을 서두르기보다 일과 생활의 기반을 다지는 무대이고 새 인연은 해마다 들어오는 운(세운)에서 열리기 쉬움")
    return " || ".join(out) if out else "재혼 풀이에 특별히 짚을 구조가 없음"

# ─────────────────────────────────────────────────────────────
# 두 사람을 직접 잇는 연결 고리 글감 (궁합용, 돌싱 포함). gans·jjis 는 [시, 일, 월, 년] 순서
# ─────────────────────────────────────────────────────────────
def get_couple_link_facts(m_gans, m_jjis, f_gans, f_jjis, m_marital="", f_marital=""):
    """남명·여명 사주를 서로 맞대어, 두 사람이 직접 끌리는 근거(일지 합, 상대 일간이 배우자별, 일간 합)와
    지난 인연(돌싱)에 관한 마음가짐 글감을 만든다. 만남·결혼은 단정하지 않는다."""
    out = []
    try:
        mg = [_to_hanja(g) for g in m_gans]
        fg = [_to_hanja(g) for g in f_gans]
        mj = [_to_hanja_ji(j) for j in m_jjis]
        fj = [_to_hanja_ji(j) for j in f_jjis]
        if len(mg) < 4 or len(fg) < 4 or len(mj) < 4 or len(fj) < 4:
            return "두 분 연결 정보가 부족함"
        names = ["시지", "일지", "월지", "년지"]
        _PW = {"일지": "일지는 배우자 자리끼리 맞닿아 가장 강한 근거", "월지": "월지는 생활·사회 속에서 맞닿는 보조 근거",
               "시지": "시지는 말년·자녀 쪽에서 맞닿는 보조 근거", "년지": "년지는 집안·뿌리 쪽에서 맞닿는 보조 근거"}
        def _pwtxt(pos):
            return " / ".join(_PW[p] for p in pos)

        # 1) 지난 인연(돌싱) 상태 — 마음가짐 글감
        if m_marital == "돌싱" and f_marital == "돌싱":
            out.append("두 분 모두 지난 인연을 겪은 분들이라, 이번 인연은 서로의 지난 아쉬움을 이해하고 같은 부딪힘을 반복하지 않는 것이 열쇠(지난 인연을 비교하거나 캐묻지 말고 새 약속을 쌓아 갈 것)")
        elif m_marital == "돌싱" or f_marital == "돌싱":
            who = "남명" if m_marital == "돌싱" else "여명"
            out.append(f"{who}께서 지난 인연을 겪은 분이라, 지난 일을 비교하거나 캐묻지 말고 천천히 속도를 맞추며 새 약속을 쌓아 가는 것이 중요")
        # 2) 일지 합: 한 사람의 배우자 자리와 합이 되는 글자가 상대 사주에 있는가
        hf = _JI_HAP.get(fj[1])
        hm = _JI_HAP.get(mj[1])
        if hf:
            pos = [names[i] for i in range(4) if mj[i] == hf]
            if pos:
                out.append(f"여명의 배우자 자리({fj[1]})와 합이 되는 글자({hf})가 남명 사주의 {', '.join(pos)}에 있어, 여명 쪽에서 남명에게 마음이 끌리고 묶이기 쉬운 근거 [{_pwtxt(pos)}]")
        if hm:
            pos = [names[i] for i in range(4) if fj[i] == hm]
            if pos:
                out.append(f"남명의 배우자 자리({mj[1]})와 합이 되는 글자({hm})가 여명 사주의 {', '.join(pos)}에 있어, 남명 쪽에서 여명에게 마음이 끌리고 묶이기 쉬운 근거 [{_pwtxt(pos)}]")
        # 2-2) 일지 삼합(반합): 한 사람의 배우자 자리와 상대 지지가 같은 삼합의 두 글자를 이루는가
        _SAMHAP = (("申子辰", "물"), ("亥卯未", "나무"), ("寅午戌", "불"), ("巳酉丑", "금속"))
        for who, me_ji, other_ji, other_nm in (("여명", fj[1], mj, "남명"), ("남명", mj[1], fj, "여명")):
            for grp, elem in _SAMHAP:
                if me_ji in grp:
                    pos = [names[i] for i in range(4) if other_ji[i] in grp and other_ji[i] != me_ji]
                    if pos:
                        out.append(f"{who}의 배우자 자리({me_ji})와 {other_nm} 사주의 {', '.join(pos)}({'·'.join(other_ji[names.index(p)] for p in pos)})가 서로 끌어당겨 {elem}의 기운을 이루어, {who} 쪽에서 {other_nm}에게 끌리고 하나로 묶이기 쉬운 근거 [{_pwtxt(pos)}]")
        # 3) 상대 일간이 나의 배우자별인가
        if get_ss(fg[1], mg[1]) in ("정관", "편관"):
            out.append(f"남명의 일간({mg[1]})이 여명에게는 남편별({get_ss(fg[1], mg[1])})에 해당해, 여명이 남명을 의지할 만한 사람으로 느끼기 쉬움")
        if get_ss(mg[1], fg[1]) in ("정재", "편재"):
            out.append(f"여명의 일간({fg[1]})이 남명에게는 아내별({get_ss(mg[1], fg[1])})에 해당해, 남명이 여명을 가정을 맡길 사람으로 느끼기 쉬움")
        # 4) 일간 합 (남명 양간·여명 음간)
        _HG = {frozenset(p) for p in ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")}
        if frozenset((mg[1], fg[1])) in _HG and mg[1] in "甲丙戊庚壬" and fg[1] in "乙丁己辛癸":
            out.append(f"두 분의 일간({mg[1]}·{fg[1]})이 서로 합을 이루어, 고전에서 인연이 닿는 표지로 보는 끌림이 있음")
    except Exception:
        return "두 분 연결 정보를 계산하지 못함"
    return " || ".join(out) if out else "두 분 사이에 특별히 짚을 직접 연결 고리는 크지 않음"

# ─────────────────────────────────────────────────────────────
# 배우자별(남=재성, 여=관성)의 위치·정편혼잡·천간/지지 판단 글감.  gans·jjis 는 [시, 일, 월, 년] 순서
# ─────────────────────────────────────────────────────────────
def get_spouse_star_facts(ds, gans, jjis, gender="남"):
    """배우자별이 어느 기둥(앞쪽=년·월 / 일지 / 뒤쪽=시)에 있는지, 정·편이 섞였는지, 천간·지지 어디에 있는지를
    AI 용 팩트 문자열로 만든다. 나이 숫자는 쓰지 않는다(수명이 길어져 구간이 달라지므로)."""
    try:
        g = "남" if str(gender).startswith("남") else "여"
        ds = _to_hanja(ds)
        gs = [_to_hanja(x) for x in gans]
        js = [_to_hanja_ji(x) for x in jjis]
        if len(gs) < 4 or len(js) < 4 or not ds:
            return "배우자별 판정 정보가 부족함"
        pair = ("정재", "편재") if g == "남" else ("정관", "편관")
        star = "아내별(재성)" if g == "남" else "남편별(관성)"
        _ro = lambda w: w + ("로" if w.endswith("재") else "으로")   # 편재→편재로, 편관→편관으로
        gan_hit, ji_hit = [], []          # (기둥인덱스, 십성)
        for i in (0, 2, 3):               # 천간: 일간 제외
            if gs[i] and get_ss(ds, gs[i]) in pair:
                gan_hit.append((i, get_ss(ds, gs[i])))
        for i in range(4):                # 지지(정기 기준)
            if js[i] and get_ss(ds, js[i]) in pair:
                ji_hit.append((i, get_ss(ds, js[i])))
        all_ss = [s for _, s in gan_hit + ji_hit]
        out = []
        if not all_ss:
            return f"{star}이 원국의 천간·지지에 보이지 않음(인연의 때는 운에서 {star}이 들어오는 시기)"

        # 1) 위치: 앞쪽(년·월) / 일지 / 뒤쪽(시)
        pos = {i for i, _ in gan_hit + ji_hit}
        front = bool(pos & {2, 3})
        back = 0 in pos
        day = any(i == 1 for i, _ in ji_hit)
        if day:
            out.append(f"{star}이 배우자 자리(일지)에 직접 앉아 있어 인연이 가장 직접적")
        if front and not back:
            out.append(f"{star}이 앞쪽 자리(년·월)에 있어 이른 시기에 이성 인연이 오기 쉬운 구조(나이를 단정하지 말 것)")
        elif back and not front:
            out.append(f"{star}이 뒤쪽 자리(시)에 있어 늦게 올수록 안정적인 구조(나이를 단정하지 말 것)")
        elif front and back:
            out.append(f"{star}이 앞쪽(년·월)과 뒤쪽(시)에 모두 있어 이른 인연과 늦은 인연이 모두 열려 있는 구조")

        # 2) 정·편 혼잡
        has_j = any(s == pair[0] for s in all_ss)
        has_p = any(s == pair[1] for s in all_ss)
        if has_j and has_p:
            out.append(f"{pair[0]}{'와' if pair[0].endswith('재') else '과'} {pair[1]}{'가' if pair[1].endswith('재') else '이'} 함께 있어(혼잡) 강하게 끌리는 쪽({pair[1]})과 안정을 주는 쪽({pair[0]}) 사이에서 마음이 갈리기 쉬움. 끌림은 {pair[1]} 쪽으로 가더라도 오래 가는 인연은 {pair[0]} 쪽 사람이 기준이라는 점을 짚을 것")
        elif has_j:
            out.append(f"{star}이 {_ro(pair[0])}만 있어 안정과 신뢰를 주는 인연을 만나기 쉬움")
        else:
            out.append(f"{star}이 {_ro(pair[1])}만 있어 강렬하고 자극적인 끌림을 따라 인연이 시작되기 쉬움")

        # 3) 천간·지지 구분
        if gan_hit and ji_hit:
            out.append(f"{star}이 겉(천간)과 속(지지) 모두에 있어 겉으로 만나는 인연과 속으로 맞는 실속이 함께 이어지는 구조")
        elif gan_hit and not ji_hit:
            out.append(f"{star}이 겉(천간)에만 있고 속(지지)에는 없어 이성 인연은 눈에 띄게 오지만 실속으로 붙잡는 데는 노력이 필요한 구조")
        else:
            out.append(f"{star}이 속(지지)에만 있고 겉(천간)에는 드러나지 않아 겉으로는 눈에 띄지 않아도 조용히 실속 있는 인연이 이어지기 쉬운 구조")
        out.append(f"{star} 개수: 천간 {len(gan_hit)}개, 지지 {len(ji_hit)}개")
        return " || ".join(out)
    except Exception:
        return "배우자별 판정 정보를 계산하지 못함"

# ─────────────────────────────────────────────────────────────
# 자녀별(남=관성, 여=식상)의 위치·겉속·자녀궁 에너지·눌림·부부 균형 글감. gans·jjis 는 [시, 일, 월, 년] 순서
# ─────────────────────────────────────────────────────────────
def get_child_star_facts(ds, gans, jjis, gender="남", marital=""):
    """자녀별이 어디에 있는지, 겉에 드러났는지 속에 숨었는지, 자녀궁(시지) 에너지, 자녀별을 누르는 기운,
    배우자별과의 균형·합을 AI 용 팩트 문자열로 만든다. 자녀의 성별·유무·사건은 단정하지 않는다."""
    try:
        g = "남" if str(gender).startswith("남") else "여"
        ds = _to_hanja(ds)
        gs = [_to_hanja(x) for x in gans]
        js = [_to_hanja_ji(x) for x in jjis]
        if len(gs) < 4 or len(js) < 4 or not ds:
            return "자녀별 판정 정보가 부족함"
        pair = ("정관", "편관") if g == "남" else ("식신", "상관")      # 자녀별
        mate = ("정재", "편재") if g == "남" else ("정관", "편관")      # 배우자별
        star = "자녀별(관성)" if g == "남" else "자녀별(식상)"
        mate_nm = "아내별" if g == "남" else "남편별"
        gan_hit = [(i, get_ss(ds, gs[i])) for i in (0, 2, 3) if gs[i] and get_ss(ds, gs[i]) in pair]
        ji_hit = [(i, get_ss(ds, js[i])) for i in range(4) if js[i] and get_ss(ds, js[i]) in pair]
        hid_hit = []          # 지지 속 숨은 자녀별(정기 제외)
        for i in range(4):
            raw = [c for c in JIJANGGAN.get(js[i], []) if c != "-"]
            for c in raw[:-1]:
                if get_ss(ds, c) in pair:
                    hid_hit.append((i, get_ss(ds, c)))
        if gan_hit or ji_hit:
            hid_hit = []      # 천간·지지에 자녀별이 있으면 지장간은 살피지 않음(없을 때만 속을 본다)
        out = []
        # 0) 혼인 상태에 따른 분량·어조
        if marital == "미혼":
            out.append("아직 결혼 전이므로 자녀 풀이는 2~3문장으로 짧게만 쓰되, 자녀 인연을 '결혼한 뒤'로만 한정하지 말 것(혼인과 별개로 자녀 인연이 있었거나 있을 수 있음). 자녀가 있다·없다·있었다를 가정하지 말 것. 배우자·부부·'가정을 꾸리실 때'처럼 앞으로의 가정 이야기와, 팩트에 없는 균형·합 문장은 쓰지 말 것")
        elif marital == "돌싱":
            out.append("지난 인연을 겪은 분이므로 부부 이야기는 지난 시절의 일로 과거형으로만 쓰고, 앞날 조언은 자녀·가까운 사람과의 균형과 새 인연을 대하는 마음가짐으로 쓸 것(지금 부부 사이가 있다고 가정하지 말고, 자녀가 있는지도 가정하지 말 것)")
        else:
            out.append("자녀가 있는지는 알 수 없으므로 있다·없다를 가정하지 말고, 자녀·돌보는 사람·이끌어 주는 후배와의 인연까지 폭넓게 풀 것")
        allpos = {i for i, _ in gan_hit + ji_hit + hid_hit}
        main_pos = {i for i, _ in gan_hit + ji_hit}
        if not allpos:
            out.append(f"{star}이 원국의 천간·지지·속에 보이지 않음(자녀 인연의 때는 운에서 {star}이 들어오는 시기이며, 약하다·없다고 쓰지 말 것)")
        else:

            # 1) 위치
            main_pos = {i for i, _ in gan_hit + ji_hit}
            if 0 in main_pos:
                out.append(f"자녀 자리(시주)에 {star}이 또렷이 있어 자녀와의 인연이 직접적")
            if 1 in main_pos:
                out.append(f"내 곁의 자리(일지)에 {star}이 있어 마음이 자녀에게 가까이 놓이는 구조")
            if main_pos & {2, 3}:
                out.append(f"앞쪽 자리(년·월)에 {star}이 있어 자녀 일이 일찍부터 마음에 자리하기 쉬움(나이를 단정하지 말 것)")

            # 2) 겉·속
            if gan_hit and ji_hit:
                out.append(f"{star}이 겉(천간)에도 지지에도 있어 자녀를 향한 마음과 현실의 일이 함께 이어지기 쉬운 구조")
            elif gan_hit:
                _lv = 0      # 겉에 드러난 자녀별 글자가 지지 속에 뿌리(통근)를 둔 정도: 2=중기 이상, 1=여기
                for _i, _ in gan_hit:
                    for _jj in js:
                        _raw = [c for c in JIJANGGAN.get(_jj, []) if c != "-"]
                        if gs[_i] in _raw:
                            _lv = max(_lv, 2 if _raw.index(gs[_i]) >= 1 else 1)
                if _lv == 2:
                    out.append(f"{star}이 겉(천간)에 드러나 있고 지지 속에도 뿌리를 두고 있어, 자녀를 향한 마음과 기대가 현실의 일로도 이어지기 쉬운 구조")
                elif _lv == 1:
                    out.append(f"{star}이 겉(천간)에 드러나 있고 지지 속에 가늘게 뿌리를 두고 있어, 마음과 기대는 분명하지만 현실에서 이어 가는 힘은 약한 편(약하다고 쓰되 '잃는다·일찍 떠난다' 같은 결과는 단정하지 말고, 섬세하게 살필수록 단단해지는 인연이라는 조언으로 마무리할 것)")
                else:
                    out.append(f"{star}이 겉(천간)에는 드러나 있으나 지지에는 뿌리가 없어, 자녀를 향한 마음과 기대는 분명하지만 현실에서 이어 가는 힘은 약한 편(약하다고 쓰되 결과는 단정하지 말고, 마음이 앞서는 구조로 쓸 것)")
            elif ji_hit:
                out.append(f"{star}이 겉에는 없고 속(지지의 중심 기운)에만 있어, 자녀를 향한 마음은 깊지만 겉으로 표현하는 데는 서툴기 쉬운 구조")
            else:
                out.append(f"{star}이 겉에는 없고 속 깊이 약하게만 있어, 자녀를 향한 마음은 조용히 이어지며 표현은 늦거나 서툴기 쉬운 구조")

            # 3) 혼잡
            ss_all = {s for _, s in gan_hit + ji_hit + hid_hit}
            if len(ss_all) == 2:
                if g == "여":
                    out.append("식신과 상관이 함께 있어 자녀를 향한 마음이 포근함과 날카로움 사이를 오가기 쉬움")
                else:
                    out.append("정관과 편관이 함께 있어 자녀에게 거는 기대와 책임감이 엇갈리기 쉬움")

        # 4) 자녀궁(시지) 에너지 — 12운성 이름은 글에 쓰지 않는다
        u = get_unsung(ds, js[0])
        if get_ss(ds, js[0]) not in pair:
            out.append(f"자녀 자리(시지)에는 자녀별이 아니라 {get_ss(ds, js[0])}{'가' if get_ss(ds, js[0]).endswith('재') else '이'} 앉아 있으므로, 자녀 자리의 힘이나 덕을 좋게 말하는 문장은 쓰지 말 것")
        elif u in ("장생", "건록", "제왕", "관대"):
            out.append("자녀 자리(시지)의 에너지가 강한 편이라 자녀 인연의 바탕이 든든한 구조('건강'이라는 낱말과 운성 이름은 글에 쓰지 말 것)")
        elif u in ("쇠", "병", "사", "묘", "절"):
            out.append("자녀 자리(시지)의 에너지가 잔잔한 편이라 정성에 비해 보람이 늦게 느껴질 수 있으나 마음을 나눌수록 깊어지는 구조(약하다·늦다·없다고 쓰지 말 것)")
        else:
            out.append("자녀 자리(시지)의 에너지가 보통이라 자녀 인연의 바탕은 무난한 구조")

        # 5) 자녀별을 누르는 기운
        if g == "여":
            ins_cnt = sum(1 for i in (0, 2, 3) if get_ss(ds, gs[i]) in ("편인", "정인")) + \
                      sum(1 for i in range(4) if get_ss(ds, js[i]) in ("편인", "정인"))
            if allpos and ins_cnt >= 3:
                out.append("자녀를 향한 마음을 생각과 걱정이 누르는 기운이 강해, 마음은 깊은데 표현이 서툴거나 걱정이 앞서기 쉬움(단정하지 말고 마음 표현을 권할 것)")
        else:
            if (gan_hit or ji_hit) and (any(get_ss(ds, gs[i]) == "상관" for i in (0, 2, 3)) or any(get_ss(ds, js[i]) == "상관" for i in range(4))):
                out.append("자녀별을 누르는 기운(상관)이 함께 있어 자녀에게 엄격하거나 말이 부딪히기 쉬움(말투를 부드럽게 권할 것)")

        # 6) 자녀별과 배우자별의 균형
        mate_gan = [i for i in (0, 2, 3) if get_ss(ds, gs[i]) in mate]
        mate_ji = [i for i in range(4) if get_ss(ds, js[i]) in mate]
        mate_hid = any(get_ss(ds, c) in mate for i in range(4) for c in JIJANGGAN.get(js[i], []) if c != "-")
        child_vis = len(gan_hit) + len(ji_hit)
        mate_vis = len(mate_gan) + len(mate_ji)
        if marital == "미혼":
            pass      # 아직 결혼 전이므로 부부 균형 문장은 만들지 않음
        elif allpos and not mate_gan and not mate_ji and not mate_hid:
            out.append(f"{mate_nm}이 원국에 보이지 않고 {star}만 있어, 마음이 자녀 쪽으로 쏠리기 쉬우니 배우자에게도 일부러 시간과 관심을 나누어 두는 것이 가정의 균형을 지키는 열쇠(이혼·별거는 언급하지 말 것)")
        elif child_vis >= 2 and mate_vis <= 1:
            out.append(f"{star}이 강하고 {mate_nm}이 약해, 마음이 자녀 쪽으로 쏠리기 쉬우니 배우자에게도 시간과 관심을 나누어 두는 것이 가정의 균형을 지키는 열쇠(이혼·별거는 언급하지 말 것)")
        elif (child_vis + len(hid_hit)) >= 3 and mate_vis == 0:
            out.append(f"{star}은 풍성한데 {mate_nm}은 겉에 없고 속에만 약하게 있어, 마음이 자녀 쪽으로 쏠리기 쉬우니 배우자에게도 시간과 관심을 나누어 두는 것이 가정의 균형을 지키는 열쇠(이혼·별거는 언급하지 말 것)")

        # 7) 자녀별과 배우자별의 합
        _HAP = {frozenset(p) for p in ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")}
        child_hid_all = [c for i in range(4) for c in JIJANGGAN.get(js[i], []) if c != "-" and get_ss(ds, c) in pair]
        mate_hid_all = [c for i in range(4) for c in JIJANGGAN.get(js[i], []) if c != "-" and get_ss(ds, c) in mate]
        ch_gan = [gs[i] for i, _ in gan_hit]
        mt_gan = [gs[i] for i in mate_gan]
        if marital != "미혼" and (any(frozenset((a, b)) in _HAP for a in mt_gan for b in child_hid_all) or
                                  any(frozenset((a, b)) in _HAP for a in ch_gan for b in mate_hid_all)):
            out.append(f"{star}과 {mate_nm}이 서로 합하는 모습이라, 자녀 일이 부부 사이를 이어 주기도 하고 부부의 이야기가 자녀 일로 번지기도 하는 구조(좋고 나쁨을 단정하지 말 것)")

        # 8) 지지에서 삼합 세 글자가 모두 모여 자녀별의 기운으로 한 덩어리가 된 경우
        _SAM = (("申子辰", "壬癸"), ("亥卯未", "甲乙"), ("寅午戌", "丙丁"), ("巳酉丑", "庚辛"))
        for trio, reps in _SAM:
            if all(c in js for c in trio) and any(get_ss(ds, r) in pair for r in reps):
                out.append(f"지지에서 세 글자가 모여 {star}의 기운이 한 덩어리로 크게 뭉쳐 있어, 자녀·표현·활동 쪽으로 마음과 힘이 크게 쏠리는 구조(속에 숨어 있다가 운을 만나면 크게 드러날 수 있음)")
        # 9) 일간(나)과 자녀별 천간이 바로 옆(시간·월간)에서 합하는 경우
        for i in (0, 2):
            if gs[i] and get_ss(ds, gs[i]) in pair and frozenset((ds, gs[i])) in _HAP:
                out.append(f"내(일간)가 바로 옆 {'시' if i == 0 else '월'}의 {star}과 합하는 모습이라 자녀와 정이 깊게 묶이고 마음이 자녀에게 쏠리기 쉬운 구조")
        return " || ".join(out)
    except Exception:
        return "자녀별 판정 정보를 계산하지 못함"

# ─────────────────────────────────────────────────────────────
# 자녀별(식상)이 대운으로 들어와 남편별(관성)과 합·극을 일으키는 시기 글감 (여명 전용).  gans·jjis 는 [시, 일, 월, 년] 순서
# ─────────────────────────────────────────────────────────────
def get_child_daewun_balance_facts(ds, gans, jjis, gender="남", daewun_list=None):
    """여명에서 대운 천간이 식신·상관이고, 원국 천간의 남편별(정관·편관)과 합하거나(식신) 극할 때(상관) 해당 대운을 짚는다.
    부부 사이에 마음 쏠림·거리감·말 부딪힘이 생기기 쉬운 시기로만 쓰며, 이혼·별거는 단정하지 않는다."""
    try:
        if not str(gender).startswith("여") or not daewun_list:
            return ""
        ds = _to_hanja(ds)
        gs = [_to_hanja(x) for x in gans]
        js = [_to_hanja_ji(x) for x in jjis]
        if len(gs) < 4 or len(js) < 4 or not ds:
            return ""
        _HAP = {frozenset(p) for p in ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")}
        mate_gans = [gs[i] for i in (0, 2, 3) if gs[i] and get_ss(ds, gs[i]) in ("정관", "편관")]
        if not mate_gans:
            return ""
        out = []
        for dw in daewun_list:
            cg = _to_hanja(dw.get("c_hanja", ""))
            cj = _to_hanja_ji(dw.get("j_hanja", ""))
            ss = get_ss(ds, cg) if cg else "-"
            if ss not in ("식신", "상관"):
                continue
            tag = ""
            if ss == "식신" and any(frozenset((cg, m)) in _HAP for m in mate_gans):
                tag = "자녀별이 남편별을 합으로 끌어가 마음이 자녀 쪽으로 쏠리고 부부 사이에 거리감이 생기기 쉬운 시기"
            elif ss == "상관":
                tag = "자녀별이 남편별을 눌러 부부 사이에 말이 부딪히기 쉬운 시기"
            if not tag:
                continue
            if cj and js[1] == cj:
                tag += "(배우자 자리와 같은 글자가 대운에 겹쳐 부부 관계의 변화가 더 크게 느껴지기 쉬움)"
            tag += "(이혼·별거는 언급하지 말고 '부부 관계의 변화·거리감'으로만 쓸 것)"
            mark = "현재 대운" if dw.get("is_current") else "대운"
            out.append(f"{dw.get('age_range', '')} {mark}: {tag}")
        return " || ".join(out) if out else ""
    except Exception:
        return ""

# ─────────────────────────────────────────────────────────────
# 자녀별(남=관성, 여=식상)이 대운으로 들어오는 시기 글감 (미혼·기혼·돌싱 공통). 자녀의 유무·성별은 단정하지 않는다.
# ─────────────────────────────────────────────────────────────
def get_child_timing_facts(ds, gender="남", daewun_list=None):
    """대운 천간·지지(정기)에 자녀별이 들어오는 대운을 나이대와 함께 짚는다."""
    try:
        if not daewun_list:
            return ""
        g = "남" if str(gender).startswith("남") else "여"
        ds = _to_hanja(ds)
        if not ds:
            return ""
        pair = ("정관", "편관") if g == "남" else ("식신", "상관")
        star = "자녀별(관성)" if g == "남" else "자녀별(식상)"
        out = []
        for dw in daewun_list:
            cg = _to_hanja(dw.get("c_hanja", ""))
            cj = _to_hanja_ji(dw.get("j_hanja", ""))
            gan_in = bool(cg) and cg != "-" and get_ss(ds, cg) in pair
            ji_in = bool(cj) and cj != "-" and get_ss(ds, cj) in pair
            if not (gan_in or ji_in):
                continue
            if gan_in and ji_in:
                how = f"{star}이 대운의 겉(천간)과 속(지지)으로 함께 들어와 자녀 인연의 기운이 가장 강하게 열리는 시기"
            elif gan_in:
                how = f"{star}이 대운의 겉(천간)으로 들어와 자녀 인연이 눈에 띄게 다가오기 쉬운 시기"
            else:
                how = f"{star}이 대운의 속(지지)으로 들어와 자녀 인연이 조용히 다가오기 쉬운 시기"
            mark = "현재 대운" if dw.get("is_current") else "대운"
            out.append(f"{dw.get('age_range', '')} {mark}: {how}(자녀가 생긴다·없다고 단정하지 말고 '인연의 기운이 열리는 때'로만 쓸 것)")
        return " || ".join(out)
    except Exception:
        return ""

def get_gungeop_jaeseong_risk_facts(ds, gans, jjis, dw_g="", dw_j="", sewun_g="", sewun_j=""):
    """군겁쟁재 + 편재 운 + 재성 입묘 사실문 (한 번에 크게 벌려는 승부 주의). gans/jjis = [시,일,월,년]"""
    try:
        ds = _to_hanja(ds)
        _g = [_to_hanja(x) for x in gans]
        _j = [_to_hanja_ji(x) for x in jjis]
        _pos = ("시지", "일지", "월지", "년지")

        def _bongi(j):
            try:
                lst = [x for x in JIJANGGAN[j] if x not in ("-", "", " ")]
                return lst[-1] if lst else ""
            except Exception:
                return ""

        bigeop = 0
        jae_vis = 0
        for k in range(4):
            if k != 1 and _g[k] not in ("?", "-", " ", ""):
                _s = get_ss(ds, _g[k])
                if _s in ("비견", "겁재"):
                    bigeop += 1
                if _s in ("정재", "편재"):
                    jae_vis += 1
            _b = _bongi(_j[k])
            if _b:
                _s2 = get_ss(ds, _b)
                if _s2 in ("비견", "겁재"):
                    bigeop += 1
                if _s2 in ("정재", "편재"):
                    jae_vis += 1
        gunggeop = (bigeop >= 3 and jae_vis <= 1)

        _MYO = {"壬": "辰", "癸": "辰", "丙": "戌", "丁": "戌", "庚": "丑", "辛": "丑", "甲": "未", "乙": "未"}
        out = []
        if gunggeop:
            out.append("형제·동료 기운이 많고 눈에 드러난 재물 기운은 약해, 재물을 나누어 갖거나 새기 쉬운 구조")
        for nm, g, j in (("현재 대운", dw_g, dw_j), ("올해 세운", sewun_g, sewun_j)):
            g = _to_hanja(g) if g else ""
            j = _to_hanja_ji(j) if j else ""
            if gunggeop:
                _hit = []
                if g and get_ss(ds, g) == "편재":
                    _hit.append("겉(천간)")
                if j and _bongi(j) and get_ss(ds, _bongi(j)) == "편재":
                    _hit.append("속(지지)")
                if _hit:
                    out.append(nm + ": 편재 기운이 " + "·".join(_hit) + "으로 들어와 '한 번에 크게 벌려는 마음'이 커지기 쉬운 때 → 한 번에 크게 얻으려는 승부, 내기성 돈거래, 보증·동업을 특히 조심하라고 쉬운 말로 경고할 것")
            if g and g in _MYO and get_ss(ds, g) in ("정재", "편재") and _MYO[g] in _j:
                _where = "·".join([_pos[k] for k in range(4) if _j[k] == _MYO[g]])
                out.append(nm + ": 천간의 재물 기운이 원국 " + _where + "의 창고에 들어가 쌓이는 모양(입고) → 재물이 모이기 쉬운 때. 좋고 나쁨의 판정은 체용 분석 사실문을 따르고 여기서 단정하지 말 것." + (" 군겁쟁재 구조이므로 모은 재물을 지키는 쪽에 무게를 둘 것." if gunggeop else "") + " 창고가 열리는 해는 별도의 창고 사실문만 따를 것")
        if not out:
            return "(해당 없음 — 이 항목은 글에 쓰지 말 것)"
        out.append("(도박·투기라는 낱말은 직접 쓰지 말고, 한 번에 크게 벌려는 승부·내기성 돈거래로 표현할 것. 이 내용은 재물 풀이와 현재 대운 풀이에만 반영할 것)")
        return " || ".join(out)
    except Exception:
        return "(해당 없음 — 이 항목은 글에 쓰지 말 것)"

def get_samjae(year_ji, target_ji):
    year_ji, target_ji = _to_hanja(year_ji), _to_hanja(target_ji)
    if year_ji in ["?", " ", "-"] or target_ji in ["?", " ", "-"]: return "해당 없음"
    s_map = {'申': ['寅','卯','辰'], '子': ['寅','卯','辰'], '辰': ['寅','卯','辰'], '亥': ['巳','午','未'], '卯': ['巳','午','未'], '未': ['巳','午','未'], '寅': ['申','酉','戌'], '午': ['申','酉','戌'], '戌': ['申','酉','戌'], '巳': ['亥','子','丑'], '酉': ['亥','子','丑'], '丑': ['亥','子','丑']}
    sj_list = s_map.get(year_ji, [])
    if not sj_list: return "해당 없음"
    if target_ji == sj_list[0]: return "들삼재"
    elif target_ji == sj_list[1]: return "눌삼재"
    elif target_ji == sj_list[2]: return "날삼재"
    return "해당 없음"


# ---- 1-C. 합충형파해 · 지장간 · 격국 · 공망 · 일반신살 ----

def get_gan_rel_all(idx, gans):
    gans = [_to_hanja(g) for g in gans]
    me = gans[idx]; res = []; far = False
    if me in ["-", "?", " "]: return "-"
    _OH = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    _GEUK = {('木','土'), ('土','水'), ('水','火'), ('火','金'), ('金','木')}
    _HAP = [{'甲','己'}, {'乙','庚'}, {'丙','辛'}, {'丁','壬'}, {'戊','癸'}]
    _CHUNG = [{'甲','庚'}, {'乙','辛'}, {'丙','壬'}, {'丁','癸'}]
    for i, other in enumerate(gans):
        if i == idx or other in ["-", "?", " "]: continue
        s = {me, other}
        if abs(i - idx) != 1:
            if s in _HAP: far = True
            continue
        if s in _HAP:
            res.append("합")
        elif s in _CHUNG:
            res.append("충")
        elif (_OH.get(me), _OH.get(other)) in _GEUK or (_OH.get(other), _OH.get(me)) in _GEUK:
            res.append("극")
    txt = "".join(x for x in ["합", "충", "극"] if x in res)
    far_html = "<span style='color:#9E9E9E; font-weight:700;'>격합</span>" if far else ""
    out = txt + (" " if txt and far_html else "") + far_html
    return out if out else "-"


def get_cheongan_hap_fact(ys, ms, ds, hs=None):
    """천간 합의 사실문: 이웃한 합/떨어진 합(격합), 쟁합(한 글자를 두 글자가 다툼), 일간이 묶이는지"""
    try:
        _HAP = {'甲':'己','己':'甲','乙':'庚','庚':'乙','丙':'辛','辛':'丙','丁':'壬','壬':'丁','戊':'癸','癸':'戊'}
        names = ["년간", "월간", "일간", "시간"]
        gans = [_to_hanja(g) if g is not None else "-" for g in (ys, ms, ds, hs)]
        _HAP_NAME = {
            frozenset(('甲','己')): "중정지합(중후하고 믿음으로 맺어지는 합. 위로 오르는 기운과 아래로 내리는 기운이 번갈아 방향을 바꾸는 움직임)",
            frozenset(('乙','庚')): "인의지합(의리와 정으로 맺어지는 합. 퍼지려는 기운과 거두어들이는 기운이 맞물려 열매를 만들어 가는 움직임)",
            frozenset(('丙','辛')): "위엄지합(체면과 위엄으로 맺어지는 합. 빛을 퍼뜨렸다 거두었다 하는 움직임)",
            frozenset(('丁','壬')): "음닉지합(겉으로 드러나지 않게 속으로 이끌리는 합. 열기를 모았다 풀었다 하는 움직임)",
            frozenset(('戊','癸')): "무정지합(겉보기에 정이 깊지 않고 담담하게 맺어지는 합. 퍼지는 기운을 넓혔다 줄였다 하는 움직임)",
        }
        def _lab(k):
            if k == 2 or gans[k] in ("-", "?", ""):
                return gans[k]
            try:
                return f"{gans[k]}, {get_ss(ds, gans[k])}"
            except Exception:
                return gans[k]
        links = []
        for i in range(4):
            for j in range(i + 1, 4):
                if gans[i] in _HAP and _HAP[gans[i]] == gans[j]:
                    links.append((i, j, j - i == 1))
        if not links:
            return "천간에 서로 합이 되는 글자 쌍은 사실문에 없음"
        lines = []
        for i, j, adj in links:
            how = "바로 이웃해 있어 합의 힘이 온전함" if adj else "서로 떨어져 있어 합의 힘이 약함(격합)"
            hn = _HAP_NAME.get(frozenset((gans[i], gans[j])), "")
            lines.append(f"{names[i]}({_lab(i)})과 {names[j]}({_lab(j)})이 합을 이룸: {how}" + (f" / 합의 성격: {hn}" if hn and adj else ""))
        for k in range(4):
            mates = [(a, b) for a, b, ad in links if ad and k in (a, b)]
            if len(mates) >= 2:
                others = [f"{names[b if a == k else a]}({_lab(b if a == k else a)})" for a, b in mates]
                lines.append(f"[쟁합] {names[k]}({_lab(k)})을 {', '.join(others)} 두 자리가 함께 합하려 함: 합하려는 힘이 나뉘어 한쪽으로 온전히 묶이지 못하고 서로 당기는 상태로 봄")
        for i, j, adj in links:
            if adj and 2 in (i, j):
                o = j if i == 2 else i
                try:
                    ss = get_ss(ds, gans[o])
                except Exception:
                    ss = ""
                lines.append(f"일간({gans[2]})이 이웃한 {names[o]}({gans[o]})과 합: 일간이 합에 묶임" + (f" (상대는 일간 기준 {ss})" if ss else ""))
        lines.append("합에 든 글자는 서로 당기는 힘 때문에 제 성질을 온전히 내기 어렵고 힘이 줄어드는 경향이 있음(결과를 단정하지 말 것)")
        lines.append("합화(다른 오행으로 변함)는 월령과 세력 조건이 모두 맞아야 하므로 기본은 변하지 않는 합으로 보고, 합화는 단정하지 말 것")
        return "[천간 합 사실] " + " / ".join(lines)
    except Exception:
        return "천간 합 정보 없음"


def get_jiji_samhap_bangap_fact(yb, mb, db, hb, ds=None):
    """지지 삼합·방합 사실문: 세 글자가 모두 모인 완성 여부, 반합(가운데 글자 포함), 합을 흔드는 충·형·해"""
    try:
        names = ["년지", "월지", "일지", "시지"]
        brs = [_to_hanja(b) if b is not None else "-" for b in (yb, mb, db, hb)]
        SAMHAP = [("목국", ('亥', '卯', '未'), '甲'), ("화국", ('寅', '午', '戌'), '丙'),
                  ("금국", ('巳', '酉', '丑'), '庚'), ("수국", ('申', '子', '辰'), '壬')]
        BANGHAP = [("목", ('寅', '卯', '辰')), ("화", ('巳', '午', '未')),
                   ("금", ('申', '酉', '戌')), ("수", ('亥', '子', '丑'))]
        CH = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅','卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}
        HYUNG = [{'子','卯'}, {'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}]
        HAE = [{'子','未'}, {'丑','午'}, {'寅','巳'}, {'卯','辰'}, {'申','亥'}, {'酉','戌'}]

        def _pos(letters):
            return "·".join(f"{names[i]} {brs[i]}" for i in range(4) if brs[i] in letters)

        def _damage(members):
            out = []
            for m in members:
                for i in range(4):
                    o = brs[i]
                    if o in members or o in ("-", "?", ""):
                        continue
                    if CH.get(m) == o:
                        out.append(f"{names[i]} {o}이(가) {m}과 충")
                    elif {m, o} in HYUNG:
                        out.append(f"{names[i]} {o}이(가) {m}과 형")
                    elif {m, o} in HAE:
                        out.append(f"{names[i]} {o}이(가) {m}과 해")
            return out

        lines = []
        for nm, mem, rep in SAMHAP:
            have = [x for x in mem if x in brs]
            if len(have) == 3:
                s = f"[삼합 완성] {_pos(mem)}이(가) 모여 {nm} 삼합이 완성됨"
                try:
                    if ds:
                        s += f" (일간 기준 {get_group_ss(get_ss(ds, rep))}의 기운이 크게 모임)"
                except Exception:
                    pass
                if brs[1] in mem:
                    s += ". 월지가 포함되어 계절의 힘을 얻음"
                dmg = _damage(mem)
                if dmg:
                    s += ". 다만 " + ", ".join(dmg) + "을 이루어 결속이 일부 흔들릴 수 있음"
                lines.append(s)
            elif len(have) == 2:
                if mem[1] in have:
                    lines.append(f"[반합] {_pos(have)}이(가) {nm} 반합(가운데 글자 포함)을 이룸. 나머지 한 글자({[x for x in mem if x not in have][0]})가 오면 삼합이 완성됨")
                else:
                    lines.append(f"[공합] {_pos(have)}은(는) {nm} 삼합의 양 끝 글자만 있어 합의 힘이 약함(참고)")
        for nm, mem in BANGHAP:
            have = [x for x in mem if x in brs]
            if len(have) == 3:
                lines.append(f"[방합 완성] {_pos(mem)}이(가) 모여 {nm} 기운의 방합이 완성됨")
            elif len(have) == 2:
                if mem[1] in have:
                    lines.append(f"[방합 미완] {_pos(have)}이(가) {nm} 기운의 방합(가운데 글자 포함)을 이룸. 나머지 한 글자({[x for x in mem if x not in have][0]})가 오면 방합이 완성됨")
                else:
                    lines.append(f"[공협] {_pos(have)}은(는) {nm} 기운의 방합 양 끝 글자만 있어 합의 힘이 약함(참고)")
        if not lines:
            return "지지에 삼합·방합과 관련된 모임은 사실문에 없음"
        return "[지지 삼합·방합 사실] " + " / ".join(lines)
    except Exception:
        return "지지 삼합·방합 정보 없음"


def get_jiji_yukhap_fact(yb, mb, db, hb):
    """지지 육합 사실문: 네 지지 전체에서 육합 찾기, 강도, 쟁합, 흔들림, 삼합 쪽 합과 겹침"""
    try:
        names = ["년지", "월지", "일지", "시지"]
        brs = [_to_hanja(b) if b is not None else "-" for b in (yb, mb, db, hb)]
        YUK = {frozenset(('子', '丑')): "강", frozenset(('午', '未')): "강",
               frozenset(('寅', '亥')): "중", frozenset(('巳', '申')): "중",
               frozenset(('卯', '戌')): "약", frozenset(('辰', '酉')): "약"}
        STR_TXT = {"강": "서로 당기는 힘이 가장 센 쌍(책의 거리 모델 기준, 참고)",
                   "중": "서로 당기는 힘이 중간쯤인 쌍(책의 거리 모델 기준, 참고)",
                   "약": "서로 당기는 힘이 비교적 약한 쌍(책의 거리 모델 기준, 참고)"}
        CH = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅','卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}
        HYUNG = [{'子','卯'}, {'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}]
        HAE = [{'子','未'}, {'丑','午'}, {'寅','巳'}, {'卯','辰'}, {'申','亥'}, {'酉','戌'}]
        PA = [{'子','酉'}, {'丑','辰'}, {'寅','亥'}, {'卯','午'}, {'巳','申'}, {'戌','未'}]
        SAMHAP = [("목국", ('亥', '卯', '未')), ("화국", ('寅', '午', '戌')),
                  ("금국", ('巳', '酉', '丑')), ("수국", ('申', '子', '辰'))]

        pairs = []
        for i in range(4):
            for j in range(i + 1, 4):
                k = frozenset((brs[i], brs[j]))
                if brs[i] != brs[j] and k in YUK:
                    pairs.append((i, j, YUK[k]))
        if not pairs:
            return "지지에 육합을 이루는 글자 쌍은 사실문에 없음"

        def _hit(letter, own):
            out = []
            for i in range(4):
                if i in own or brs[i] in ("-", "?", ""):
                    continue
                o = brs[i]
                if CH.get(letter) == o:
                    out.append(f"{names[i]} {o}이(가) {letter}과 충")
                elif {letter, o} in HYUNG:
                    out.append(f"{names[i]} {o}이(가) {letter}과 형")
                elif {letter, o} in HAE:
                    out.append(f"{names[i]} {o}이(가) {letter}과 해")
                elif {letter, o} in PA:
                    out.append(f"{names[i]} {o}이(가) {letter}과 파")
            return out

        cnt = {}
        for i, j, _ in pairs:
            cnt[i] = cnt.get(i, 0) + 1
            cnt[j] = cnt.get(j, 0) + 1

        lines = []
        for i, j, s in pairs:
            adj = (j - i == 1)
            txt = f"[육합] {names[i]} {brs[i]}과(와) {names[j]} {brs[j]}이(가) 육합을 이룸"
            txt += "(바로 이웃함)" if adj else "(떨어져 있으나 육합은 지지 전체를 봄)"
            txt += f". {STR_TXT[s]}"
            dmg = _hit(brs[i], (i, j)) + _hit(brs[j], (i, j))
            if frozenset((brs[i], brs[j])) in (frozenset(('寅', '亥')), frozenset(('巳', '申'))):
                dmg.append("이 쌍 자체가 합이면서 서로 파·형의 성질도 겸하는")
            if dmg:
                txt += ". 다만 " + ", ".join(dmg) + " 관계가 걸려 있어 합의 당김이 일부 흔들릴 수 있음"
            over = []
            for p in (i, j):
                partner = j if p == i else i
                for nm, mem in SAMHAP:
                    if brs[p] not in mem:
                        continue
                    for q in range(4):
                        if q in (p, partner) or brs[q] not in mem or brs[q] == brs[p]:
                            continue
                        if mem[1] in (brs[p], brs[q]):
                            over.append(f"{names[p]} {brs[p]}은(는) {names[q]} {brs[q]}과(와) {nm} 반합 쪽으로도 당겨짐")
            if over:
                txt += ". 또한 " + ", ".join(over) + "(한 글자가 두 방향으로 당겨지는 구조)"
            lines.append(txt)
        for p, c in cnt.items():
            if c >= 2:
                lines.append(f"[쟁합] {names[p]} {brs[p]}이(가) 둘 이상의 글자와 동시에 육합을 이룸: 한쪽으로 마음이 모이기 어렵고 여러 곳에 당겨지는 구조")
        lines.append("육합은 상대 힘을 줄이는 합이 아니라 서로 당겨 묶이는 합이며, 삼합처럼 오행이 바뀌는 것이 아니므로 합화로 단정하지 말 것")
        return "[지지 육합 사실] " + " / ".join(lines)
    except Exception:
        return "지지 육합 정보 없음"


def get_cheongan_chung_fact(ys, ms, ds, hs=None):
    """천간 충 사실문: 이웃한 충, 한 글자가 양쪽에서 충을 받는 쟁충, 일간이 걸리는지, 합이 충을 받는지, 일간 주변의 극"""
    try:
        names = ["년간", "월간", "일간", "시간"]
        gans = [_to_hanja(g) if g is not None else "-" for g in (ys, ms, ds, hs)]
        _CH = [{'甲','庚'}, {'乙','辛'}, {'丙','壬'}, {'丁','癸'}]
        _HP = [{'甲','己'}, {'乙','庚'}, {'丙','辛'}, {'丁','壬'}, {'戊','癸'}]
        _OH = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
        _GEUK = {('木','土'), ('土','水'), ('水','火'), ('火','金'), ('金','木')}

        def _lab(k):
            if k == 2 or gans[k] in ("-", "?", ""):
                return gans[k]
            try:
                return f"{gans[k]}, {get_ss(ds, gans[k])}"
            except Exception:
                return gans[k]

        chung, far_chung, hap = [], [], []
        for i in range(4):
            for j in range(i + 1, 4):
                s = {gans[i], gans[j]}
                if s in _CH:
                    (chung if j - i == 1 else far_chung).append((i, j))
                elif s in _HP and j - i == 1:
                    hap.append((i, j))

        lines = []
        for i, j in chung:
            lines.append(f"{names[i]}({_lab(i)})과 {names[j]}({_lab(j)})이 바로 이웃해 충을 이룸: 서로 밀어내며 변화를 만드는 움직임")
        for k in range(4):
            mates = [(a, b) for a, b in chung if k in (a, b)]
            if len(mates) >= 2:
                others = [f"{names[b if a == k else a]}({_lab(b if a == k else a)})" for a, b in mates]
                lines.append(f"[쟁충] {names[k]}({_lab(k)})이 {', '.join(others)} 양쪽에서 동시에 충을 받음: 한 글자가 여러 방향에서 밀리는 구조")
        for i, j in chung:
            if 2 in (i, j):
                o = j if i == 2 else i
                lines.append(f"일간({gans[2]})이 이웃한 {names[o]}({_lab(o)})과 충: 일간 자신이 충에 걸림")
        for i, j in hap:
            for m in (i, j):
                for a, b in chung:
                    if m in (a, b) and (a, b) != (i, j):
                        o = b if a == m else a
                        if o not in (i, j):
                            lines.append(f"{names[i]}({gans[i]})과 {names[j]}({gans[j]})의 합이 {names[o]}({gans[o]})의 충을 받아 합의 힘이 흔들림")
        for i, j in far_chung:
            lines.append(f"{names[i]}({gans[i]})과 {names[j]}({gans[j]})은 충의 글자 쌍이나 떨어져 있어 충으로 보지 않고 참고만")
        for o in (1, 3):
            s = {gans[2], gans[o]}
            if s in _CH or s in _HP or gans[o] in ("-", "?", ""):
                continue
            a, b = _OH.get(gans[2]), _OH.get(gans[o])
            if (a, b) in _GEUK:
                lines.append(f"일간({gans[2]})이 이웃한 {names[o]}({_lab(o)})을 극함")
            elif (b, a) in _GEUK:
                lines.append(f"일간({gans[2]})이 이웃한 {names[o]}({_lab(o)})에게 극을 받음")
        if not lines:
            return "천간에 이웃한 충이나 일간과 관련된 극은 사실문에 없음"
        _has_chung = any(("충" in x) and ("극함" not in x) and ("극을 받음" not in x) and ("충으로 보지 않고" not in x) for x in lines)
        if _has_chung:
            lines.append("충은 서로 밀어내며 변화를 만드는 움직임이라 흔들림이면서 동시에 변화의 계기가 되기도 하므로, 나쁜 일로만 단정하지 말 것")
        else:
            lines.append("위 내용은 충이 아니라 극(눌러서 다루는 관계)이므로, 마음이 여러 방향으로 흔들린다거나 변화의 계기가 된다는 식으로 풀지 말고, 일간이 그 기운을 직접 다루고 눌러 쓰는 모습으로만 풀 것")
        return "[천간 충 사실] " + " / ".join(lines)
    except Exception:
        return "천간 충 정보 없음"

def get_ji_rel_set(me, target):
    me, target = _to_hanja(me), _to_hanja(target)
    if not me or not target or me == "?" or target == "?" or me == target: return "자형" if me == target and me in "辰午酉亥" else "-"
    s, r = {me, target}, []
    if s in [{'申','子'}, {'子','辰'}, {'寅','午'}, {'午','戌'}, {'亥','卯'}, {'卯','未'}, {'巳','酉'}, {'酉','丑'}]: r.append("반합")
    if s in [{'亥','未'}, {'寅','戌'}, {'申','辰'}, {'巳','丑'}]: r.append("공합")
    if s in [{'寅','卯'}, {'卯','辰'}, {'巳','午'}, {'午','未'}, {'申','酉'}, {'酉','戌'}, {'亥','子'}, {'子','丑'}]: r.append("방합(미완)")
    if s in [{'寅','辰'}, {'巳','未'}, {'申','戌'}, {'亥','丑'}]: r.append("공협")
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

GOEGANG_ILJU = {'戊辰', '戊戌', '庚辰', '庚戌', '壬辰', '壬戌'}

BAEKHO_GANJI = {'甲辰', '乙未', '丙戌', '丁丑', '戊辰', '壬戌', '癸丑'}

def get_general_shinsal_filtered(idx, gans, jjis, gender="남성"):
    # 🚨 한자 변환(_to_hanja) 전에, 원본 값이 비어있는지 먼저 확인 (변환 후엔 "-"가 ""로 바뀌어 감지 불가)
    if gans[idx] in ["?", "-", " ", ""] or jjis[idx] in ["?", "-", " ", ""]:
        return []
 
    gans = [_to_hanja(g) for g in gans]
    jjis = [_to_hanja(j) for j in jjis]
    dc, mc, yc = gans[1], gans[2], gans[3]
    dj, mj, yj = jjis[1], jjis[2], jjis[3]
    cur_g, cur_j = gans[idx], jjis[idx]
    gj = cur_g + cur_j
    noble, ausp, evil = [], [], []
 
    if cur_j in {'甲':'未丑','乙':'申子','丙':'酉亥','丁':'酉亥','戊':'未丑','己':'申子','庚':'未丑','辛':'午寅','壬':'卯巳','癸':'卯巳'}.get(dc,""): noble.append("천을귀인")
    _WD = {'寅':'丙','午':'丙','戌':'丙','巳':'庚','酉':'庚','丑':'庚','申':'壬','子':'壬','辰':'壬','亥':'甲','卯':'甲','未':'甲'}
    if cur_g == _WD.get(mj, ""): noble.append("월덕귀인")
    if cur_j in {'甲':'子午','乙':'子午','丙':'卯酉','丁':'卯酉','戊':'辰戌','己':'丑未','庚':'寅亥','辛':'寅亥','壬':'巳申','癸':'巳申'}.get(dc,"") and idx in (1, 3): noble.append("태극귀인")
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): noble.append("천록귀인")
    if cur_j in {'甲':'巳','乙':'午','丙':'申','戊':'申','丁':'酉','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}.get(dc,""): noble.append("문창귀인")
    if cur_j in {'甲':'亥','乙':'子','丙':'寅','戊':'寅','丁':'卯','己':'卯','庚':'巳','辛':'午','壬':'申','癸':'酉'}.get(dc,""): noble.append("문곡귀인")
    if cur_j in {'甲':'亥','乙':'午','丙':'寅','戊':'寅','丁':'酉','己':'酉','庚':'巳','辛':'子','壬':'申','癸':'卯'}.get(dc,""): noble.append("학당귀인")
    if gj in ["甲寅", "乙丑", "丙子", "丁酉", "戊申", "己未", "庚午", "辛巳", "壬辰", "癸卯"]: noble.append("복성귀인")
    if cur_j in {'甲':'巳','乙':'午','丙':'巳','丁':'午','戊':'申','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}.get(dc,""): noble.append("천주귀인")
 
    if cur_j in {'甲':'亥','乙':'戌','丙':'申','戊':'申','丁':'未','己':'未','庚':'巳','辛':'辰','壬':'寅','癸':'丑'}.get(dc,""): noble.append("암록")
    if cur_j in {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}.get(dc,""): ausp.append("건록")
    if cur_j in {'甲':'辰','乙':'巳','丙':'未','戊':'未','丁':'申','己':'申','庚':'戌','辛':'亥','壬':'丑','癸':'寅'}.get(dc,""): ausp.append("금여록")
    if gj in ["甲寅", "丙辰", "戊辰", "庚辰", "壬戌"]: ausp.append("일덕")
    if gj in ["乙丑", "己巳", "癸酉"] and idx in [0, 1]: ausp.append("금신")

    if gj in ["甲辰","乙未","丙戌","丁丑","戊辰","壬戌","癸丑"]: evil.append("백호대살")
    if gj in ["庚辰","庚戌","壬辰","壬戌","戊辰","戊戌"]: evil.append("괴강살")
    if cur_j in {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子'}.get(dc,""): evil.append("양인살")
    if cur_j in {'甲':'酉','乙':'戌','丙':'子','丁':'丑','戊':'子','己':'丑','庚':'卯','辛':'辰','壬':'午','癸':'未'}.get(dc,""): evil.append("비인살")
    if dj == '寅' and cur_j in ['寅', '巳', '申']: evil.append("탕화살")
    if dj == '午' and cur_j in ['辰', '午', '丑']: evil.append("탕화살")
    if dj == '丑' and cur_j in ['午', '未', '戌']: evil.append("탕화살")
    if gj in ["乙卯","乙巳","乙未","乙丑","乙酉","乙亥","丁巳","己卯","己巳","己未","己酉","己亥","己丑","辛巳","癸巳"]: evil.append("곡각살")
    if cur_g in ['甲', '辛'] and cur_j in ['卯', '午', '申', '未']: evil.append("현침살")
 
    if gj in ["甲寅", "乙卯", "丙午", "丁巳", "戊辰", "戊戌", "己未", "己丑", "庚申", "辛酉", "壬子", "癸亥"]: evil.append("간여지동")
    if gender == "여성" and gj in ["甲寅","乙巳","丁巳","戊申","辛亥"]: evil.append("고란살")
    if gj in ["甲午", "丙戌", "戊辰", "庚辰", "壬戌", "乙巳", "丁亥", "己亥", "辛巳", "癸亥"]: evil.append("의처의부")
    if idx == 1 and gj in ["甲子", "乙亥", "丙寅", "丁卯", "戊午", "己巳", "庚辰", "庚戌", "辛丑", "辛未", "壬申", "癸酉"]: evil.append("효신살")
 
    dohwa_map = {'寅':'卯', '午':'卯', '戌':'卯', '申':'酉', '子':'酉', '辰':'酉', '巳':'午', '酉':'午', '丑':'午', '亥':'子', '卯':'子', '未':'子'}
    if cur_j == dohwa_map.get(yj, "") or cur_j == dohwa_map.get(dj, ""): evil.append("도화살")
    if gj in ["甲子", "乙巳", "丁卯", "庚午", "辛亥", "癸酉"]: evil.append("나체도화")
    if cur_j == {'甲':'午','丙':'寅','丁':'未','戊':'辰','庚':'戌','辛':'酉','壬':'子'}.get(dc, ""): evil.append("홍염살")
    if gj in ["甲寅", "乙卯", "丁未", "戊戌", "己未", "庚申", "辛酉", "癸丑"]: evil.append("음욕살")
    if gender == "남성" and gj in ["甲寅", "甲申", "丁丑", "戊申", "己丑", "辛未", "壬寅", "癸未"]: evil.append("남연살")
    if gender == "여성" and gj in ["乙丑", "丙申", "丁丑", "己未", "庚寅", "辛未", "壬寅", "壬申"]: evil.append("여연살")
 
    if dj in ['卯','酉','戌'] and cur_j in ['卯','酉','戌'] and (jjis.count('卯') + jjis.count('酉') + jjis.count('戌')) >= 2: evil.append("철쇄개금")
    if idx == 1 and gj in ["丙午", "丁未", "戊午", "戊子", "己未", "己丑"]: evil.append("육수살")
    if gj in ["甲子", "甲辰", "丙寅", "丙辰", "丙戌"]: evil.append("평두살")
    cheolsa_map = {'甲':'辰', '乙':'辰', '丙':'未申', '丁':'未申', '戊':'寅', '己':'寅', '庚':'戌', '辛':'戌', '壬':'丑', '癸':'丑'}
    if cur_j in cheolsa_map.get(dc, ""): evil.append("철사관")
 
    if gj in ["甲子", "甲午", "己卯", "己酉"]: ausp.append("진신")
    if gj in ["丙子", "丙午", "辛卯", "辛酉"]: evil.append("교신")
    if gj in ["丁丑", "丁未", "壬辰", "壬戌"]: evil.append("퇴신")
    if gj in ["戊寅", "戊申", "癸巳", "癸亥"]: evil.append("복신")

    # 책 13번 구추방해: 일주 10개 (시주에 있으면 말년·자식에게 비슷하게 작용)
    if idx == 1 and gj in ["乙卯", "乙酉", "戊午", "戊子", "己卯", "己酉", "辛卯", "辛酉", "壬午", "壬子"]: evil.append("구추방해")
    # 책 38번 신병: 일주 3개, 일·시에 같이 있으면 흉이 배로 커짐
    if idx in (0, 1) and gj in ["乙巳", "乙未", "己巳"]: evil.append("신병")
 
    # 🚨 흉살 우선순위: 백호/괴강/양인은 무조건 표시, 현침살은 중요도 낮춰 맨 뒤로
    MUST_SHOW_EVIL = ["백호대살", "괴강살", "양인살"]
    EVIL_PRIORITY = [
        "간여지동", "고란살", "구추방해", "신병", "탕화살", "비인살",
        "홍염살", "나체도화", "도화살",
        "의처의부", "남연살", "여연살", "음욕살",
        "십악대패살", "철쇄개금", "철사관", "곡각살", "육수살", "평두살",
        "현침살", "교신성", "교신", "퇴신", "복신",
    ]

    noble = list(dict.fromkeys(noble))
    ausp = list(dict.fromkeys(ausp))
    evil = list(dict.fromkeys(evil))

    good_pool = noble + ausp
    MAX_GOOD = 4
    shown_good = good_pool[:MAX_GOOD]

    # 흉살: 반드시 표시할 것 먼저, 그다음 우선순위 목록 순서
    must_evil = [e for e in MUST_SHOW_EVIL if e in evil]
    rest_evil = [e for e in evil if e not in MUST_SHOW_EVIL]
    rest_evil.sort(key=lambda x: EVIL_PRIORITY.index(x) if x in EVIL_PRIORITY else 999)
    ordered_evil = must_evil + rest_evil

    MAX_TOTAL = 7
    remain = max(2, MAX_TOTAL - len(shown_good))  # 흉살은 최소 3개 자리 보장
    rest_slots = max(0, remain - len(must_evil))
    shown_evil = must_evil + rest_evil[:rest_slots]

    result = []
    for n in shown_good:
        result.append(f"<span style='color:#0D47A1;'>{n}</span>")
    for e in shown_evil:
        result.append(f"<span style='color:#C62828;'>{e}</span>")
    return result

def get_general_shinsal_for_ai(idx, gans, jjis, gender="남성"):
    """AI 풀이용 신살 목록: 택일 전용 신살(십악대패살)은 뺀다. (사주표 화면용은 get_general_shinsal_filtered 그대로)"""
    return [s for s in (get_general_shinsal_filtered(idx, gans, jjis, gender) or [])
            if "십악대패" not in re.sub(r"<[^>]+>", "", str(s))]

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

def get_jijanggan_pure(ji):
    ji = _to_hanja(ji)
    if ji in ["?", "-", " "]: return "-"
    raw = JIJANGGAN.get(ji, ['-','-','-'])
    clean_list = [j for j in raw if j != '-']
    return "·".join(clean_list) if clean_list else "-"

def get_gyukgook_detailed(ds, ys, ms, hs, mb):
    ds, ys, ms, hs, mb = _to_hanja(ds), _to_hanja(ys), _to_hanja(ms), _to_hanja(hs), _to_hanja(mb)
    jg = JIJANGGAN.get(mb, [])
    if not jg: return "알수없음격", "지장간 정보가 없습니다."
 
    # 건록격: 월지가 일간의 건록 / 양인격: 양간이 월지에서 제왕 (12운성 기준)
    _GEONROK = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳', '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}
    _YANGIN = {'甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子'}
    if mb == _GEONROK.get(ds, ""):
        return "건록격", f"월지 {mb}가 일간 {ds}의 건록(建祿)에 해당하여 건록격으로 정합니다."
    if mb == _YANGIN.get(ds, ""):
        if ds == '戊':
            return "양인격", f"월지 {mb}가 일간 {ds}의 제왕(帝旺)에 해당하여 폭발적 에너지인 양인격으로 봅니다."
        return "양인격", "월지 겁재 및 제왕으로 폭발적 에너지인 양인격입니다."

    def safe_get_ss(day_gan, target_char):
        if not target_char or target_char == "?": return "무명"
        return get_ss(day_gan, target_char)
 
    if mb in ["子", "午", "卯", "酉"]:
        core_ss = safe_get_ss(ds, mb)
        if core_ss in ["비견", "겁재"]:
            return "월겁격", f"월지 {mb}가 일간 {ds}와 같은 기운이므로 월겁격으로 삼습니다."
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
        return "월겁격", f"월지 {mb}의 본기가 {fallback_ss}이므로 월겁격으로 정합니다."
 
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


# ---- 1-D. 오행 상생상극 · 용신 ----

_OHAENG_CYCLE = ['목', '화', '토', '금', '수']  # 상생 순서: 목생화, 화생토, 토생금, 금생수, 수생목

def _oh_next(e):
    """e가 생(生)해주는 다음 오행 (e의 자식)"""
    return _OHAENG_CYCLE[(_OHAENG_CYCLE.index(e) + 1) % 5]

def _oh_prev(e):
    """e를 생(生)해주는 이전 오행 (e의 부모)"""
    return _OHAENG_CYCLE[(_OHAENG_CYCLE.index(e) - 1) % 5]

def _oh_controls(e):
    """e가 극(剋)하는 오행"""
    return _OHAENG_CYCLE[(_OHAENG_CYCLE.index(e) + 2) % 5]

def _oh_controlled_by(e):
    """e를 극(剋)하는 오행"""
    return _OHAENG_CYCLE[(_OHAENG_CYCLE.index(e) - 2) % 5]

_EARTH_JI = "辰戌丑未"
_DEUK_UNSUNG = ("장생", "관대", "건록", "제왕")

def _earth_rooted(ds, ji):
    """월지·일지가 土(辰戌丑未)일 때, 일간의 12운성이 장생·관대·건록·제왕이면 뿌리가 있는 것으로 봅니다."""
    h = _to_hanja(ji)
    if not h or h not in _EARTH_JI:
        return False
    return get_unsung(ds, ji) in _DEUK_UNSUNG

def _judge_strength(counts, mb, ds, db=None):
    """신강/신약/중화 판정을 한 곳에 모은 도우미.
    - 일간 자신은 지원세력에서 뺀다(나머지 글자만 센다).
    - 월지가 일간을 도우면 득령 1점, 일지가 돕거나 빼가면 득지/실지 1점을 더한다(실령은 감점하지 않는다).
    - 점수가 같으면 중화.
    반환: (판정, 가산 전 지원, 가산 전 소모, 최종 지원, 최종 소모, 득령 설명, 득지 설명)"""
    dm = get_color(ds)
    biguk, inseong = dm, _oh_prev(dm)
    siksang, jaeseong, gwanseong = _oh_next(dm), _oh_controls(dm), _oh_controlled_by(dm)

    support = max(0, counts.get(biguk, 0) - 1) + counts.get(inseong, 0)   # 일간 자신(1글자)은 제외
    drain = counts.get(siksang, 0) + counts.get(jaeseong, 0) + counts.get(gwanseong, 0)
    raw_support, raw_drain = support, drain

    deukryeong_note = ""
    mb_elem = get_color(mb)
    if mb_elem in (biguk, inseong):
        support += 1
        deukryeong_note = f"월지({mb})가 일간을 돕는 오행({mb_elem})이라 득령"
    elif _earth_rooted(ds, mb):
        support += 1
        deukryeong_note = f"월지({mb})는 土이지만 일간의 12운성이 {get_unsung(ds, mb)}이라 뿌리가 있어 득령"
    elif mb_elem in (siksang, jaeseong, gwanseong):
        deukryeong_note = f"월지({mb})가 일간의 기운을 빼가는 오행({mb_elem})이라 실령(실령은 점수에 가감하지 않음)"

    deukji_note = ""
    db_elem = get_color(db) if db else None
    if db_elem in (biguk, inseong):
        support += 1
        deukji_note = f"일지({db})가 일간을 돕는 오행({db_elem})이라 득지"
    elif db and _earth_rooted(ds, db):
        support += 1
        deukji_note = f"일지({db})는 土이지만 일간의 12운성이 {get_unsung(ds, db)}이라 뿌리가 있어 득지"
    elif db_elem in (siksang, jaeseong, gwanseong):
        drain += 1
        deukji_note = f"일지({db})가 일간의 기운을 빼가는 오행({db_elem})이라 실지"

    if support > drain:
        strength = '신강'
    elif support < drain:
        strength = '신약'
    else:
        strength = '중화'
    return strength, raw_support, raw_drain, support, drain, deukryeong_note, deukji_note

def get_yongshin_analysis(counts, mb, ds, db=None):
    """억부(신강/신약)+조후(계절 한난)를 종합한 용신 판정, 희신/기신/구신/한신까지 자동 산출.
    억부용신과 조후용신이 다르고 조후 필요 오행이 희박(1개 이하)하며 계절도 극단적인 경우,
    두 용신이 상생 관계면 겸용 용신으로, 상극 관계면 조후 불균형을 '증상'으로만 짚고
    억부용신 단독 체제를 유지한다(조후 오행을 억지로 보강하면 용신을 해치는 모순을 방지)."""
    dm = get_color(ds)
    if not dm or dm not in _OHAENG_CYCLE:
        return "일간 오행을 판별할 수 없어 용신 분석을 생략합니다."

    biguk, inseong = dm, _oh_prev(dm)
    siksang, jaeseong, gwanseong = _oh_next(dm), _oh_controls(dm), _oh_controlled_by(dm)

    strength, raw_support, raw_drain, support, drain, deukryeong_note, deukji_note = _judge_strength(counts, mb, ds, db)
    is_strong = (strength == '신강')
    eok_bu_candidates = [siksang, jaeseong, gwanseong] if is_strong else [inseong, biguk]
    eok_bu_yongshin = min(eok_bu_candidates, key=lambda e: counts.get(e, 0))

    winter, summer = {'亥', '子', '丑'}, {'巳', '午', '未'}
    johu_yongshin = '화' if mb in winter else ('수' if mb in summer else None)

    secondary_yongshin = None  # 겸용 용신(상생 관계일 때만 채움)

    # 조후 우선: 겨울(亥·子·丑)이면 火, 여름(巳·午·未)이면 水가 조후 필요 오행입니다.
    # 단, 壬癸(수) 일간이 겨울에, 丙丁(화) 일간이 여름에 태어나고 그 오행이 1개 이하일 때만 조후용신을 먼저 세웁니다.
    johu_first = bool(johu_yongshin) and (
        (dm == '수' and johu_yongshin == '화') or (dm == '화' and johu_yongshin == '수')
    ) and counts.get(johu_yongshin, 0) <= 1

    if johu_first:
        final_yongshin = johu_yongshin
        if eok_bu_yongshin != johu_yongshin:
            secondary_yongshin = eok_bu_yongshin
        johu_cnt = counts.get(johu_yongshin, 0) - (1 if dm == johu_yongshin else 0)
        season_txt = '겨울' if johu_yongshin == '화' else '여름'
        role_txt = '얼어붙은 기운을 녹이는' if johu_yongshin == '화' else '타오르는 열기를 식히는'
        confidence_note = f"{season_txt}({mb}월)에 태어났고 조후 필요 오행({johu_yongshin})이 일간 자신을 빼면 {johu_cnt}개뿐이라 {role_txt} 조후용신({johu_yongshin})을 먼저 세움"
        if secondary_yongshin:
            confidence_note += f", 억부상 {strength}이므로 보조(겸용) 용신({secondary_yongshin})을 함께 표기"
        confidence_note += " (조후용신이 지나치게 늘어나면 오히려 균형을 해치므로 적당한 정도가 좋음)"

    elif johu_yongshin and johu_yongshin == eok_bu_yongshin:
        final_yongshin = eok_bu_yongshin
        confidence_note = f"억부({strength})와 조후(계절) 판단이 일치하여 {final_yongshin} 용신 확정"
    elif johu_yongshin and counts.get(johu_yongshin, 0) <= 1:
        # 조후 필요 오행이 희박(1개 이하)하고 계절도 극단적인 경우 → 상생/상극으로 처리 분기
        is_friendly = (johu_yongshin == _oh_prev(eok_bu_yongshin)) or (eok_bu_yongshin == _oh_prev(johu_yongshin))

        if is_friendly:
            final_yongshin = eok_bu_yongshin
            secondary_yongshin = johu_yongshin
            confidence_note = (
                f"억부상 {eok_bu_yongshin}, 조후상 {johu_yongshin}이 모두 필요하고 두 기운이 상생 관계이므로, "
                f"{eok_bu_yongshin}과 {johu_yongshin}을 함께 쓰는 겸용 용신으로 확정"
            )
        else:
            final_yongshin = eok_bu_yongshin
            confidence_note = (
                f"억부상 {strength}이므로 {eok_bu_yongshin}{'을' if eok_bu_yongshin in ('목', '금') else '를'} 용신으로 삼되, "
                f"조후상 필요한 {johu_yongshin}이 {eok_bu_yongshin}과 상극 관계라 억지로 보강할 수 없어, "
                f"조후 불균형({mb}월 한습/조열)으로 인한 현실적 애로는 별도의 증상으로만 짚고 보강 대상으로는 삼지 않음"
            )
    else:
        final_yongshin = eok_bu_yongshin
        confidence_note = f"억부상 {strength}이므로 {final_yongshin}{'을' if final_yongshin in ('목', '금') else '를'} 용신으로 삼음"
        if johu_yongshin:
            confidence_note += f" (계절상으로는 {johu_yongshin}도 보조적으로 필요)"

    if strength == '중화':
        confidence_note += " (신강·신약이 팽팽한 중화에 가까워 억부 용신의 확정도는 낮으므로 참고용으로 볼 것)"

    huishin, hanshin = _oh_prev(final_yongshin), _oh_next(final_yongshin)
    gishin = _oh_controlled_by(final_yongshin)
    gushin = _oh_prev(gishin)

    if johu_first:
        # 조후 우선일 때: 조후용신을 기신으로 삼지 않습니다.
        # 희신 = 조후용신을 생하는 오행 / 기신 = 신약이면 조후용신을 해치거나 빼가는 오행, 신강이면 일간을 더 키우는 오행
        used = {final_yongshin}
        if secondary_yongshin:
            used.add(secondary_yongshin)
        huishin = _oh_prev(final_yongshin)
        if huishin in used:
            huishin = None
        else:
            used.add(huishin)
        if is_strong:
            g_cands = [_oh_prev(dm), dm]
        else:
            g_cands = [e for e in (_oh_controlled_by(final_yongshin), _oh_next(final_yongshin)) if e != dm]
        g_cands += list(_OHAENG_CYCLE)
        gishin = next(e for e in g_cands if e not in used)
        used.add(gishin)
        gushin = None
        hanshin = next((e for e in _OHAENG_CYCLE if e not in used), None)

    label = (
        f"[용신={final_yongshin}"
        + (f" ({'조후 우선, ' if johu_first else ''}겸용:{secondary_yongshin})" if secondary_yongshin
           else (" (조후 우선)" if johu_first else ""))
        + (f" / 희신(용신을 돕는 이로운 기운)={huishin}" if huishin else "")
        + f" / 기신(용신을 해치는 해로운 기운, 반드시 피해야 함)={gishin}"
        + (f" / 구신={gushin}" if gushin else "")
        + (f" / 한신={hanshin}" if hanshin else "")
        + "] "
    )
    position_notes = " / ".join(n for n in (deukryeong_note, deukji_note) if n)
    return (
        label +
        f"일간({ds}, {dm}) 자신을 뺀 나머지 글자 기준 지원세력(비겁+인성)={raw_support} vs 소모세력(식상+재성+관성)={raw_drain}이고, "
        f"여기에 위치 가산(월지가 돕거나 일지가 돕거나 빼가면 각 1점)을 더한 최종 점수는 {support} vs {drain}로 {strength}입니다"
        f"{' (' + position_notes + ')' if position_notes else ''}. "
        f"{confidence_note}."
    )

def get_goshin_gwasook_ji(day_ji, gender):
    """일지 기준 방합 그룹으로 고신살(남명)/과숙살(여명) 지지를 산출.
    방합 그룹 바로 앞 지지 = 과숙, 방합 그룹 바로 뒤 지지 = 고신."""
    db_h = _to_hanja(day_ji)
    ji_order = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    banghap_groups = [("寅", "卯", "辰"), ("巳", "午", "未"), ("申", "酉", "戌"), ("亥", "子", "丑")]
    for group in banghap_groups:
        if db_h in group:
            start_idx = ji_order.index(group[0])
            end_idx = ji_order.index(group[-1])
            gwasook_ji = ji_order[(start_idx - 1) % 12]
            gosin_ji = ji_order[(end_idx + 1) % 12]
            return (gosin_ji if gender == "남성" else gwasook_ji), ("고신" if gender == "남성" else "과숙")
    return None, None


# ---- 1-E. 대운 계산 ----

def get_daeun_su_accurate(utc_dt, order):
    try:
        sun = ephem.Sun()
        def get_lon(dt):
            _ed = ephem.Date(dt)
            sun.compute(dt, epoch=_ed)
            return math.degrees(ephem.Ecliptic(sun, epoch=_ed).lon) % 360.0
 
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

def get_daeun_data_list(ms, mb, ds, yb, order_dir, calc_d, age, db=None, utc_dt=None):
    # calc_d 값이 전달되지 않았거나 태년 천문 시각(utc_dt)이 있는 경우 정확한 대운수 연산 적용
    if utc_dt is not None:
        calc_d = get_daeun_su_accurate(utc_dt, order_dir)
    elif not calc_d:
        calc_d = 1
 
    daewun_list = []
    c_idx = GAN.index(ms) % 10 if ms in GAN else 0
    j_idx = JI.index(mb) % 12 if mb in JI else 0
 
    yb_hanja = K2H_JI.get(yb, yb)
    db_hanja = K2H_JI.get(db, db) if db else ""
 
    for i in range(10):
        val = i * 10 + calc_d
        c_idx_calc = (c_idx + (i + 1) * order_dir) % 10
        j_idx_calc = (j_idx + (i + 1) * order_dir) % 12
 
        c_hangul = GAN[c_idx_calc]
        j_hangul = JI[j_idx_calc]
 
        c = K2H_GAN.get(c_hangul, c_hangul)
        j = K2H_JI.get(j_hangul, j_hangul)
 
        ss_gan = get_ss(ds, c_hangul) or get_ss(ds, c) or "-"
        ss_ji = get_ss(ds, j_hangul) or get_ss(ds, j) or "-"
 
        try:
            un_sung = get_unsung(ds, j) or get_unsung(ds, j_hangul) or "-"
        except Exception:
            un_sung = "-"
 
        y_shin = get_12_shinsal(yb_hanja, j)
        if not y_shin or y_shin == "-":
            y_shin = get_12_shinsal(yb, j_hangul)
 
        d_shin = get_12_shinsal(db_hanja, j) if db_hanja else "-"
        if not d_shin or d_shin == "-":
            d_shin = get_12_shinsal(db, j_hangul) if db else "-"
 
        daewun_list.append({
            "age_range": f"{val}~{val+9}세",
            "ss_gan": ss_gan,
            "c_hanja": c,
            "c_hangul": c_hangul,
            "j_hanja": j,
            "j_hangul": j_hangul,
            "ss_ji": ss_ji,
            "un_sung": un_sung,
            "y_shinsal": y_shin,
            "d_shinsal": d_shin,
            "shin_sal": y_shin,
            "is_current": (val <= age < val + 10),
            "is_first": (i == 0)
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


# ---- 1-F. 신청서 입력 보조 · 나이/성별/혼인 지침 · 육친 규칙 ----

def auto_fill_user_ganji():
    st.session_state['app_running'] = False
 
    ry = st.session_state.get("u_ry_rev", "")
    rm = st.session_state.get("u_rm_rev", "")
    rd = st.session_state.get("u_rd_rev", "")
    rt = st.session_state.get("u_rt_rev", "")
 
    def _extract(text):
        if not text: return ""
        text = text.replace(" ", "").replace("년", "").replace("월", "").replace("일", "").replace("시", "")
        g_char, j_char = "?", "?"
        for c in text:
            if g_char == "?" and c in "甲乙丙丁戊己庚辛壬癸갑을병정무기경신임계":
                g_char = c; continue
            if j_char == "?" and c in "子丑寅卯辰巳午未申酉戌亥자축인묘진사오미신유술해":
                j_char = c
        return g_char + j_char
 
    _ry = _extract(ry)
    _rm = _extract(rm)
    _rd = _extract(rd)
 
    if not _ry or _ry == "??" or not _rm or _rm == "??" or not _rd or _rd == "??":
        st.session_state.pop('rev_success_msg', None)
        st.session_state['rev_error_msg'] = "간지를 2글자씩 정확히 입력하세요."
        return
 
    ry_h = K2H_GAN.get(_ry[0], _ry[0]) + K2H_JI.get(_ry[1], _ry[1])
    rm_h = K2H_GAN.get(_rm[0], _rm[0]) + K2H_JI.get(_rm[1], _rm[1])
    rd_h = K2H_GAN.get(_rd[0], _rd[0]) + K2H_JI.get(_rd[1], _rd[1])
 
    klc_find = KoreanLunarCalendar()
 
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
 
    matched_list = []
 
    # 🚨 1800년부터 2050년까지 싹 다 뒤져서 1997, 1937년 등 모든 연도를 수집합니다!
    for y in range(2050, 1800, -1):
        klc_find.setSolarDate(y, 7, 1)
        gj_y = klc_find.getChineseGapJaString().split()
        if gj_y and gj_y[0][:2] == ry_h:
            curr_dt = dt_mod.date(y+1, 2, 28)
            while curr_dt >= dt_mod.date(y, 1, 1):
                klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                gj = klc_find.getChineseGapJaString().split()
                if len(gj) >= 3 and gj[0][:2] == ry_h and gj[1][:2] == rm_h and gj[2][:2] == rd_h:
                    rt_val = "시간 모름"
                    if rt:
                        clean_rt = rt.replace("시", "").strip()
                        if clean_rt:
                            ji_char = clean_rt[-1]
                            rt_h = K2H_JI.get(ji_char, ji_char)
                            rt_val = time_map.get(rt_h, "시간 모름")
 
                    is_leap_str = "윤달" if klc_find.isIntercalation else "평달"
                    display_str = f"양력 {curr_dt.year}년 {curr_dt.month}월 {curr_dt.day}일\n(음력 {klc_find.lunarYear}년 {klc_find.lunarMonth}월 {klc_find.lunarDay}일, {is_leap_str})"
 
                    matched_list.append({
                        "display": display_str,
                        "y": curr_dt.year,
                        "m": curr_dt.month,
                        "d": curr_dt.day,
                        "t": rt_val
                    })
                    break
                curr_dt -= dt_mod.timedelta(days=1)
 
    if not matched_list:
        st.session_state['rev_error_msg'] = "일치하는 날짜가 없습니다."
        st.session_state.pop('rev_success_msg', None)
        st.session_state.pop('u_matched_list', None)
    else:
        st.session_state.pop('rev_error_msg', None)
        st.session_state['u_matched_list'] = matched_list
        st.session_state['s_y'] = matched_list[0]['y']
        st.session_state['s_m'] = matched_list[0]['m']
        st.session_state['s_d'] = matched_list[0]['d']
        st.session_state['s_t'] = matched_list[0]['t']
 
        if len(matched_list) == 1:
            st.session_state['rev_success_msg'] = "✅ 자동입력 완료!"
        else:
            st.session_state['rev_success_msg'] = f"✅ {len(matched_list)}개의 날짜가 발견되었습니다. 아래에서 선택하세요."

def auto_fill_partner_ganji():
    st.session_state['app_running'] = False
 
    p_ry = st.session_state.get("p_ry_rev", "")
    p_rm = st.session_state.get("p_rm_rev", "")
    p_rd = st.session_state.get("p_rd_rev", "")
    p_rt = st.session_state.get("p_rt_rev", "")
 
    def _extract(text):
        if not text: return ""
        text = text.replace(" ", "").replace("년", "").replace("월", "").replace("일", "").replace("시", "")
        g_char, j_char = "?", "?"
        for c in text:
            if g_char == "?" and c in "甲乙丙丁戊己庚辛壬癸갑을병정무기경신임계":
                g_char = c; continue
            if j_char == "?" and c in "子丑寅卯辰巳午未申酉戌亥자축인묘진사오미신유술해":
                j_char = c
        return g_char + j_char
 
    _p_ry = _extract(p_ry)
    _p_rm = _extract(p_rm)
    _p_rd = _extract(p_rd)
 
    if not _p_ry or _p_ry == "??" or not _p_rm or _p_rm == "??" or not _p_rd or _p_rd == "??":
        st.session_state.pop('rev_p_success_msg', None)
        st.session_state['rev_p_error_msg'] = "간지를 2글자씩 정확히 입력하세요."
        return
 
    p_ry_h = K2H_GAN.get(_p_ry[0], _p_ry[0]) + K2H_JI.get(_p_ry[1], _p_ry[1])
    p_rm_h = K2H_GAN.get(_p_rm[0], _p_rm[0]) + K2H_JI.get(_p_rm[1], _p_rm[1])
    p_rd_h = K2H_GAN.get(_p_rd[0], _p_rd[0]) + K2H_JI.get(_p_rd[1], _p_rd[1])
 
    klc_find = KoreanLunarCalendar()
 
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
 
    matched_list = []
 
    for y in range(2050, 1800, -1):
        klc_find.setSolarDate(y, 7, 1)
        gj_y = klc_find.getChineseGapJaString().split()
        if gj_y and gj_y[0][:2] == p_ry_h:
            curr_dt = dt_mod.date(y+1, 2, 28)
            while curr_dt >= dt_mod.date(y, 1, 1):
                klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                gj = klc_find.getChineseGapJaString().split()
                if len(gj) >= 3 and gj[0][:2] == p_ry_h and gj[1][:2] == p_rm_h and gj[2][:2] == p_rd_h:
                    rt_val = "시간 모름"
                    if p_rt:
                        clean_p_rt = p_rt.replace("시", "").strip()
                        if clean_p_rt:
                            ji_char_p = clean_p_rt[-1]
                            p_rt_h = K2H_JI.get(ji_char_p, ji_char_p)
                            rt_val = time_map.get(p_rt_h, "시간 모름")
 
                    is_leap_str = "윤달" if klc_find.isIntercalation else "평달"
                    display_str = f"양력 {curr_dt.year}년 {curr_dt.month}월 {curr_dt.day}일\n(음력 {klc_find.lunarYear}년 {klc_find.lunarMonth}월 {klc_find.lunarDay}일, {is_leap_str})"
 
                    matched_list.append({
                        "display": display_str,
                        "y": curr_dt.year,
                        "m": curr_dt.month,
                        "d": curr_dt.day,
                        "t": rt_val
                    })
                    break
                curr_dt -= dt_mod.timedelta(days=1)
 
    if not matched_list:
        st.session_state['rev_p_error_msg'] = "일치하는 날짜가 없습니다."
        st.session_state.pop('rev_p_success_msg', None)
        st.session_state.pop('p_matched_list', None)
    else:
        st.session_state.pop('rev_p_error_msg', None)
        st.session_state['p_matched_list'] = matched_list
        st.session_state['p_y_in'] = matched_list[0]['y']
        st.session_state['p_m_in'] = matched_list[0]['m']
        st.session_state['p_d_in'] = matched_list[0]['d']
        st.session_state['p_t_key'] = matched_list[0]['t']
 
        if len(matched_list) == 1:
            st.session_state['rev_p_success_msg'] = "✅ 자동입력 완료!"
        else:
            st.session_state['rev_p_success_msg'] = f"✅ {len(matched_list)}개의 날짜가 발견되었습니다. 아래에서 선택하세요."

def search_dates_by_ganji(ry_h, rm_h, rd_h, rt_ji=None, base_year=None):
    if base_year is None:
        base_year = dt_mod.datetime.now().year
 
    ry_h = _to_hanja(ry_h[:1]) + _to_hanja_ji(ry_h[1:]) if len(ry_h)>=2 else ry_h
    rm_h = _to_hanja(rm_h[:1]) + _to_hanja_ji(rm_h[1:]) if len(rm_h)>=2 else rm_h
    rd_h = _to_hanja(rd_h[:1]) + _to_hanja_ji(rd_h[1:]) if len(rd_h)>=2 else rd_h
 
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
 
    target_time_str = time_map.get(rt_ji, "시간 모름") if rt_ji else "시간 모름"
    matched_results = []
    klc = KoreanLunarCalendar()
 
    ref_dt = dt_mod.date(1900, 1, 1)
    gan_list = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    ji_list = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
 
    target_d_idx = -1
    for idx in range(60):
        if (gan_list[idx % 10] + ji_list[idx % 12]) == rd_h:
            target_d_idx = idx
            break
 
    if target_d_idx == -1:
        return []
 
    start_date = dt_mod.date(1900, 1, 1)
    end_date = dt_mod.date(2050, 12, 31)
 
    offset = (target_d_idx - 10) % 60
    first_match = start_date + dt_mod.timedelta(days=offset)
 
    curr = first_match
    while curr <= end_date:
        y_p, m_p, _ = get_true_year_month_pillar(curr.year, curr.month, curr.day, 12, 0)
        if y_p == ry_h and m_p == rm_h:
            klc.setSolarDate(curr.year, curr.month, curr.day)
            s_sol_fmt = f"{curr.year}년 {curr.month:02d}월 {curr.day:02d}일"
            s_lun_fmt = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일"
            age_calc = base_year - curr.year + 1
 
            matched_results.append({
                "display": f"양력 {s_sol_fmt}\n(음력 {s_lun_fmt}, {age_calc}세)",
                "y": int(curr.year),
                "m": int(curr.month),
                "d": int(curr.day),
                "t": target_time_str
            })
        curr += dt_mod.timedelta(days=60)
 
    matched_results.sort(key=lambda item: abs(item["y"] - (base_year - 40)))
 
    return matched_results

def get_opposite_gender(gender): return "여성" if gender == "남성" else "남성"

def update_partner_gender(): st.session_state["f_g"] = get_opposite_gender(st.session_state.get("u_g", "남성"))

def update_user_gender(): st.session_state["u_g"] = get_opposite_gender(st.session_state.get("f_g", "여성"))

def get_age_prompt(age):
    if age < 20:
        return (
            f"신청자는 청소년기(10대, 현재 {age}세)입니다. "
            "학업 진학운과 부모 형제운을 최우선으로 상세히 분석하고 재물 사업운은 축소하십시오."
        )
    elif age < 40:
        return (
            f"신청자는 청년기(20~30대, 현재 {age}세) MZ세대입니다. "
            "고리타분한 명리 용어를 버리고 직업은 '스타트업, 프리랜서, 워라밸, 퍼스널 브랜딩', "
            "연애는 '소개팅, 썸, 연인 간의 소통' 등 2030 청년들이 100% 공감할 수 있는 "
            "세련되고 트렌디한 어휘로 통변하십시오."
        )
    elif age < 60:
        return (
            f"신청자는 중장년기(40~50대, 현재 {age}세)입니다. "
            "재성운과 관직 명예운에 집중하여 현실적인 자산 관리와 사회적 성취를 중심으로 서술하십시오."
        )
    else:
        return (
            f"신청자는 노년기(60대 이상, 현재 {age}세)입니다. "
            "건강운 및 심리적 평안, 노후 자산 안정을 최우선으로 깊이 다루십시오. "
            "육친(배우자, 자녀)을 통변할 때는 단순한 십성의 강약 공식을 그대로 적용하지 말고, "
            "오랜 세월 함께한 관계 속에서 감정 표현이 무언적으로 깊어지거나, "
            "기대와 현실의 누적된 간극이 심리적 상처로 남아있을 수 있다는 식으로, "
            "시간의 깊이와 관계의 구조화라는 차원을 반드시 함께 고려하여 서술하십시오. "
            "어투는 연세에 걸맞게 차분하고 존중하는 존댓말로 하되, "
            "'패가망신', '폭군', '초토화', '절대 자중'처럼 불안이나 거부감을 주는 센 단어는 그대로 옮기지 말고 "
            "'마음을 가라앉히고 천천히 움직이시면 좋겠습니다'처럼 순화하십시오. "
            "명리 키워드(학업원만, 당선, 신분상승 등)가 노년의 삶과 맞지 않으면 그대로 쓰지 말고 "
            "건강, 평안, 가족, 살림, 자산 관리 같은 현재 삶의 언어로 풀어 쓰십시오."
        )

def get_gender_prompt(gender):
    if gender == "여성": return "여성 내담자(여명)이므로 육친 적용 시 관성(官星)을 배우자/남편으로, 식상(食傷)을 자식으로 엄격히 적용하십시오."
    else: return "남성 내담자(남명)이므로 육친 적용 시 재성(財星)을 배우자/아내로, 관성(官星)을 자식으로 엄격히 적용하십시오."

def get_marital_prompt(gender, marital):
    if marital == "기혼": return f"현재 기혼 상태이므로 {'남편' if gender == '여성' else '아내'}과의 실질적인 가내 평안, 정서적 유대, 부부 관계 유지 전략에 집중하여 통변하십시오."
    elif marital == "돌싱": return "현재 이혼/사별(돌싱) 상태이므로 과거 인연에 대한 성찰과 함께 새로운 재혼 및 운명적 재기 인연에 집중하여 통변하십시오. 이혼인지 사별인지는 알 수 없으니 '이혼'이나 '사별'로 단정하지 말고 '지난 인연'이라고 표현하십시오."
    elif marital == "미혼": return f"현재 미혼 상태이므로 {'미래의 남편' if gender == '여성' else '미래의 아내'}이 될 인연의 도래 시기와 연애/결혼 준비 전략에 집중하여 통변하십시오."
    else: return "혼인 상태가 분명하지 않으므로 결혼 여부를 단정하지 말고, '배우자 인연'이라는 중립적인 표현으로 인연의 흐름과 관계 운을 통변하십시오."

def get_yukchin_rule(gender, marital):
    if gender == '남성':
        return (
            f"\n🚨 [육친 통변 특수부대 절대 규칙 (남성용)]:\n"
            f"- 본 내담자는 남성(현재 상태: {marital})입니다. 아래의 명리학적 육친 생극제화 및 대체 규칙을 100% 엄수하십시오.\n"
            f"1. 👨‍👩‍👦 [핵심 가족]:\n"
            f"   - 아내(부인) = 정재 (정재가 없으면 편재로 대체)\n"
            f"   - 애인(여친) = 편재 (편재가 없으면 정재로 대체)\n"
            f"   - 자녀 = 관성(정관/편관) 🚨(경고: 남명에서 '식상'을 자녀로 풀이하는 즉시 치명적 오류로 간주함!)\n"
            f"2. 👵👴 [부모 및 조부모]:\n"
            f"   - 아버지 = 편재 (없으면 정재) / 어머니 = 정인 (없으면 편인)\n"
            f"   - 조부(할아버지) = 편인 / 조모(할머니) = 상관\n"
            f"3. 🏠 [처가 및 형제]:\n"
            f"   - 장모(처가) = 식상 (아내를 생하는 기운)\n"
            f"   - 동성 형제(형/남동생) = 비견 / 이성 형제(누나/여동생) = 겁재\n"
            f"4. 🚨 [상태별 호칭 맞춤형 타겟팅]: 내담자의 현재 혼인 상태({marital})를 반드시 반영하십시오.\n"
            f"   - 기혼: '현재 아내/배우자'로 칭할 것.\n"
            f"   - 미혼: '미래의 인연'으로 칭할 것.\n"
            f"   - 🚨돌싱(이혼/사별): '과거의 인연(전처)'에 대한 성찰이나 '새로운 인연(재혼운)'으로 변환하여 카운슬링할 것.\n"
        )
    else:
        return (
            f"\n🚨 [육친 통변 특수부대 절대 규칙 (여성용)]:\n"
            f"- 본 내담자는 여성(현재 상태: {marital})입니다. 아래의 명리학적 육친 생극제화 및 대체 규칙을 100% 엄수하십시오.\n"
            f"1. 👩‍❤️‍👨 [핵심 가족]:\n"
            f"   - 남편 = 정관 (정관이 없으면 편관으로 대체)\n"
            f"   - 애인(남친) = 편관 (편관이 없으면 정관으로 대체)\n"
            f"   - 자녀 = 식상(식신/상관) 🚨(경고: 여명에서 '관성'을 자녀로 풀이하는 즉시 치명적 오류로 간주함!)\n"
            f"2. 👵👴 [부모 및 조부모]:\n"
            f"   - 아버지 = 편재 (없으면 정재) / 어머니 = 정인 (없으면 편인)\n"
            f"   - 조부(외할아버지) = 편인 / 조모(외할머니) = 상관\n"
            f"3. 🏠 [시댁 및 자매]:\n"
            f"   - 시어머니(시댁) = 재성 (남편을 생하는 기운)\n"
            f"   - 동성 형제(언니/여동생) = 비견 / 이성 형제(오빠/남동생) = 겁재\n"
            f"4. 🚨 [상태별 호칭 맞춤형 타겟팅]: 내담자의 현재 혼인 상태({marital})를 반드시 반영하십시오.\n"
            f"   - 기혼: '현재 남편/배우자'로 칭할 것.\n"
            f"   - 미혼: '미래의 인연'으로 칭할 것.\n"
            f"   - 🚨돌싱(이혼/사별): '과거의 인연(전 남편)'에 대한 성찰이나 '새로운 인연(재혼운)'으로 변환하여 카운슬링할 것.\n"
        )


# ==============================================================================
# PART 2. [1-x 개인 사주] 1-1 종합 · 1-2 올해 · 1-3 이달 · 1-4 이번주/일운
# ==============================================================================


# ---- 2-A. 체용(體用) 폭포수 : 대운 → 세운 → 월운 → 일운 (전/후반기 천간·지지 반영) ----

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

def get_dw_fact_str(dw_che, dw_yong, dw_kw):
    return f"체운(무대): {dw_che} / 용운(사건): {dw_yong} ➔ 도출 키워드: {dw_kw}"

# ---- 대운 체(體) 흐름 사실문 (신청자·상대방 공통 — app.py가 불러다 씁니다) ----
_CHE_GEN = {'비겁': '식상', '식상': '재성', '재성': '관성', '관성': '인성', '인성': '비겁'}
_CHE_CTRL = {'비겁': '재성', '식상': '관성', '재성': '인성', '관성': '비겁', '인성': '식상'}

def get_che_relation(a, b):
    """전반기 체(a)에서 후반기 체(b)로 이어지는 관계: 동기·순생·역생·순극·역극"""
    if a == b: return "동기"
    if _CHE_GEN.get(a) == b: return "순생"
    if _CHE_GEN.get(b) == a: return "역생"
    if _CHE_CTRL.get(a) == b: return "순극"
    if _CHE_CTRL.get(b) == a: return "역극"
    return "관계없음"

def get_daewun_che_flow_str(dw_list, dir_name=""):
    """대운 목록 → AI에게 넘기는 '대운 체 흐름' 사실문. 방향(순행·역행)을 주지 않으면 대운 천간이 +1씩 가는지로 직접 판정합니다."""
    if not dw_list:
        return "대운 체 흐름 정보 없음"
    if not dir_name:
        try:
            gi = [GAN.index(d['c_hangul']) for d in dw_list[:2]]
            dir_name = "순행" if (gi[1] - gi[0]) % 10 == 1 else "역행"
        except Exception:
            dir_name = ""
    cur = next((i for i, d in enumerate(dw_list) if d.get('is_current')), 0)
    parts = []
    for i, d in enumerate(dw_list):
        c1, c2 = get_group_ss(d['ss_gan']), get_group_ss(d['ss_ji'])
        mark = " [미래대운]" if i > cur else ""
        parts.append(f"{d['age_range']}({d['c_hanja']}{d['j_hanja']}): 전반기체({c1})/후반기체({c2}) / 전환관계({get_che_relation(c1, c2)}) / 대운 지지 12운성({d['un_sung']}){mark}")
    head = f"[대운 방향: {dir_name} — 대운 천간의 십성이 {'인성에서 비겁, 식상, 재성, 관성' if dir_name == '순행' else '관성에서 재성, 식상, 비겁, 인성'} 순서로 이어짐] " if dir_name else ""
    return head + " / ".join(parts)


def get_couple_daewun_overlap_str(m_info, f_info, base_year=None, max_segments=4):
    """남명·여명의 대운이 '실제 달력 연도' 기준으로 겹치는 구간(올해부터)을 사실문으로 만듭니다.
    두 사람의 나이가 다르므로 나이 숫자가 아니라 (양력 출생년 + 나이 - 1) 연도로 비교합니다.
    m_info / f_info = {'birth_year': 양력 출생년, 'dw': 대운 목록}"""
    base_year = base_year or dt_mod.date.today().year

    def _spans(info):
        out = []
        by = int(info['birth_year'])
        for d in info.get('dw', []):
            a, b = str(d['age_range']).split('~')
            s0, e0 = int(a), int(b.replace('세', ''))
            out.append((by + s0 - 1, by + e0 - 1, d))
        return out

    def _tag(d):
        c1, c2 = get_group_ss(d['ss_gan']), get_group_ss(d['ss_ji'])
        return (f"{d['c_hanja']}{d['j_hanja']}대운({d['age_range']}, 전반기체 {c1}/후반기체 {c2}, "
                f"전환관계 {get_che_relation(c1, c2)}, 12운성 {d['un_sung']})")

    try:
        ms, fs = _spans(m_info), _spans(f_info)
    except Exception:
        return "대운 교차 정보 없음"
    segs = []
    for a1, a2, md in ms:
        for b1, b2, fd in fs:
            s, e = max(a1, b1), min(a2, b2)
            if s <= e and e >= base_year:
                segs.append((s, e, md, fd))
    segs.sort(key=lambda x: x[0])
    lines = []
    for s, e, md, fd in segs[:max_segments]:
        when = "현재 진행" if s <= base_year else "앞으로 올 구간"
        lines.append(f"[{when}] {s}년~{e}년: 남명 {_tag(md)} / 여명 {_tag(fd)}")
    if not lines:
        return "대운 교차 정보 없음"
    return f"(달력 연도 기준, 올해 {base_year}년) " + " / ".join(lines)


def get_daewun_wave_compare(m_info, f_info, m_yong_text, f_yong_text, start_age=20, end_age=89):
    """두 사람의 대운을 달력 연도로 겹쳐 20~80대 인생 전체의 '파도 높이'를 비교합니다.
    파도 높이 = 십성·용신(45%) + 대운 지지 12운성(30%) + 대운 지지 12신살(25%).
    반환: (0~10점, AI 용 사실문). 비교할 연도가 모자라면 (None, 안내문)."""
    EL = {}
    for chars, el in (("甲乙寅卯", "목"), ("丙丁巳午", "화"), ("戊己辰戌丑未", "토"), ("庚辛申酉", "금"), ("壬癸亥子", "수")):
        for ch in chars:
            EL[ch] = el
    SS_Q = {'정인': 1.0, '식신': 1.0, '정재': 1.0, '편재': 1.0, '정관': 1.0, '비견': 0.6,
            '편인': 0.4, '편관': 0.4, '상관': 0.35, '겁재': 0.35}
    UN_P = {'건록': 1.0, '제왕': 1.0, '관대': 0.8, '장생': 0.8, '목욕': 0.5, '쇠': 0.5, '양': 0.5,
            '병': 0.3, '태': 0.3, '사': 0.1, '묘': 0.1, '절': 0.1}
    SHIN_P = {'장성살': 1.0, '반안살': 0.9, '지살': 0.6, '역마살': 0.6, '화개살': 0.6, '년살': 0.55,
              '망신살': 0.35, '육해살': 0.3, '월살': 0.3, '천살': 0.25, '재살': 0.2, '겁살': 0.2}

    def _shin(d):
        vals = []
        for key in ('y_shinsal', 'd_shinsal'):
            txt = str(d.get(key, ''))
            for name, p in SHIN_P.items():
                if name in txt:
                    vals.append(p)
                    break
        return sum(vals) / len(vals) if vals else 0.5

    def _waves(info, yong_text):
        ye = get_yongshin_elements(yong_text)
        good = {ye[k] for k in ("용신", "희신", "겸용") if k in ye}
        bad = {ye[k] for k in ("기신", "구신") if k in ye}
        has_y = bool(good or bad)
        by = int(info['birth_year'])
        wv = {}
        for d in info.get('dw', []):
            s0 = int(str(d['age_range']).split('~')[0])
            un = UN_P.get(d.get('un_sung'), 0.5)
            sh = _shin(d)
            for k in range(10):
                age = s0 + k
                if age < start_age or age > end_age:
                    continue
                first = k < 5      # 대운 앞 5년 = 천간, 뒤 5년 = 지지
                ss = SS_Q.get(d['ss_gan'] if first else d['ss_ji'], 0.6)
                if has_y:
                    el = EL.get(d['c_hanja'] if first else d['j_hanja'])
                    yo = 1.0 if el in good else (0.0 if el in bad else 0.5)
                    a = 0.5 * ss + 0.5 * yo
                else:
                    a = ss
                h = 0.45 * a + 0.30 * un + 0.25 * sh
                wv[by + age - 1] = max(-1.0, min(1.0, (h - 0.55) / 0.3))   # -1(바닥) ~ +1(꼭대기)
        return wv

    try:
        mw, fw = _waves(m_info, m_yong_text), _waves(f_info, f_yong_text)
    except Exception:
        return None, "대운 물결 비교 정보 없음"
    years = sorted(set(mw) & set(fw))
    if len(years) < 10:
        return None, "대운 물결 비교 정보 없음"

    def _pair(a, b):
        bonus = 0.5 * min(abs(a), abs(b)) if a * b < 0 else 0.0   # 한쪽이 높을 때 다른 쪽이 낮으면 받쳐 주는 가점
        return a + b + bonus

    avg = sum(_pair(mw[y], fw[y]) for y in years) / len(years)
    score = max(0.0, min(10.0, 6.8 + 3.0 * avg))

    def _lab(v):
        return "높음" if v > 0.25 else ("낮음" if v < -0.25 else "보통")

    both_high = sum(1 for y in years if _lab(mw[y]) == "높음" and _lab(fw[y]) == "높음")
    comp = sum(1 for y in years if {_lab(mw[y]), _lab(fw[y])} == {"높음", "낮음"})
    both_low = sum(1 for y in years if _lab(mw[y]) == "낮음" and _lab(fw[y]) == "낮음")

    blocks, prev_m, prev_f = [], None, None
    for i in range(0, len(years), 5):
        ys = years[i:i + 5]
        ma = sum(mw[y] for y in ys) / len(ys)
        fa = sum(fw[y] for y in ys) / len(ys)
        ml_lab, fl_lab = _lab(ma), _lab(fa)

        def _trend(cur, prev):
            if prev is None: return "시작"
            return "오름세" if cur - prev > 0.15 else ("내림세" if cur - prev < -0.15 else "비슷")
        mt, ft = _trend(ma, prev_m), _trend(fa, prev_f)
        prev_m, prev_f = ma, fa
        if ml_lab == "높음" and fl_lab == "높음": rel = "함께 높은 파도(동행)"
        elif ml_lab == "낮음" and fl_lab == "낮음": rel = "함께 낮은 파도(서로 의지가 필요)"
        elif {ml_lab, fl_lab} == {"높음", "낮음"}: rel = "높은 쪽이 낮은 쪽을 받쳐 주는 번갈아 보완"
        else: rel = "무난한 시기"
        blocks.append(f"{ys[0]}~{ys[-1]}년: 남명 {ml_lab}({mt}) / 여명 {fl_lab}({ft}) → {rel}")
    head = (f"(만 {start_age}~{end_age}세, 달력 연도 {years[0]}~{years[-1]}년 {len(years)}년 비교, "
            f"파도 높이=십성·용신+12운성+12신살) 함께 높은 해 {both_high}년 / 번갈아 보완하는 해 {comp}년 / 함께 낮은 해 {both_low}년 // ")
    return round(score, 1), head + " / ".join(blocks)

def _is_daewun_first_half(age, dw_start_age):
    """대운 진입 후 0~4년차(전반기,천간) / 5~9년차(후반기,지지) 판정"""
    year_in_dw = age - dw_start_age
    return 0 <= year_in_dw <= 4

def _is_sewun_first_half(target_dt):
    y = target_dt.year
    naive_dt = target_dt.replace(tzinfo=None) if target_dt.tzinfo else target_dt
    return dt_mod.datetime(y, 2, 4) <= naive_dt < dt_mod.datetime(y, 8, 7)

def _is_wolun_first_half(target_dt):
    """그 날짜가 속한 월주의 절입일부터 15일 안이면 전반기(천간), 아니면 후반기(지지)"""
    naive_dt = target_dt.replace(tzinfo=None) if target_dt.tzinfo else target_dt
    _, p_now, _ = get_true_year_month_pillar(naive_dt.year, naive_dt.month, naive_dt.day, 12, 0)
    start = naive_dt.date()
    for _ in range(40):
        prev = start - dt_mod.timedelta(days=1)
        _, p_prev, _ = get_true_year_month_pillar(prev.year, prev.month, prev.day, 12, 0)
        if p_prev != p_now:
            break
        start = prev
    return (naive_dt.date() - start).days < 15

def _is_ilun_first_half(hour, minute):
    """조자시(00:30)~오시 끝(13:29)이면 전반기(천간), 미시(13:30)~야자시면 후반기(지지)"""
    total_min = hour * 60 + minute
    return 30 <= total_min < 810

def get_woonse_analysis_facts(ds, db, dw_g_cur, dw_j_cur, sewun_g, sewun_j, wolun_g, wolun_j, ilun_g, ilun_j,
                                age=None, dw_start_age=None, target_dt=None, hour=None, minute=None):
    """
    폭포수 체용 분석 (전/후반기 분리 반영판)
    - 각 레벨(대운/세운/월운/일운)을 천간(전반기)/지지(후반기)로 분리 계산
    - 지금이 어느 반기인지 판정하여, 그 반기의 체(體) 값을 다음 단계 실행분석에 연결
    """
    ilju_lower_group = get_group_ss(get_ss(ds, db))
 
    # 1. 대운 — 천간(전반)/지지(후반) 체 각각 계산
    dw_che_1 = get_group_ss(get_ss(ds, dw_g_cur))   # 전반기(천간)
    dw_che_2 = get_group_ss(get_ss(ds, dw_j_cur))   # 후반기(지지)
    dw_is_first = _is_daewun_first_half(age, dw_start_age) if (age is not None and dw_start_age is not None) else True
    dw_che_active = dw_che_1 if dw_is_first else dw_che_2
 
    # 2. 세운 — 천간(전반)/지지(후반) 체 각각 계산, 세운의 실행은 대운의 '활성 체'와 대조
    sewun_che_1 = get_group_ss(get_ss(ds, sewun_g))
    sewun_che_2 = get_group_ss(get_ss(ds, sewun_j))
    sewun_is_first = _is_sewun_first_half(target_dt) if target_dt else True
    sewun_che_active = sewun_che_1 if sewun_is_first else sewun_che_2
    s_yong = get_execution_yong(sewun_che_active, ilju_lower_group)
    sewun_kw = get_matrix_keyword(dw_che_active, s_yong)
 
    # 3. 월운 — 천간(전반)/지지(후반) 체 각각 계산, 월운의 실행은 세운의 '활성 체'와 대조
    wolun_che_1 = get_group_ss(get_ss(ds, wolun_g))
    wolun_che_2 = get_group_ss(get_ss(ds, wolun_j))
    wolun_is_first = _is_wolun_first_half(target_dt) if target_dt else True
    wolun_che_active = wolun_che_1 if wolun_is_first else wolun_che_2
    w_yong = get_execution_yong(wolun_che_active, ilju_lower_group)
    wolun_kw = get_matrix_keyword(sewun_che_active, w_yong)
 
    # 4. 일운 — 천간(전반)/지지(후반) 체 각각 계산, 일운의 실행은 월운의 '활성 체'와 대조
    ilun_che_1 = get_group_ss(get_ss(ds, ilun_g))
    ilun_che_2 = get_group_ss(get_ss(ds, ilun_j))
    ilun_is_first = _is_ilun_first_half(hour, minute) if (hour is not None and minute is not None) else True
    ilun_che_active = ilun_che_1 if ilun_is_first else ilun_che_2
    i_yong = get_execution_yong(ilun_che_active, ilju_lower_group)
    ilun_kw = get_matrix_keyword(wolun_che_active, i_yong)
    # (추가) 하루의 전반기(천간)·후반기(지지) 키워드를 둘 다 계산
    ilun_kw_1 = get_matrix_keyword(wolun_che_active, get_execution_yong(ilun_che_1, ilju_lower_group))
    ilun_kw_2 = get_matrix_keyword(wolun_che_active, get_execution_yong(ilun_che_2, ilju_lower_group))
 
    woonse_fact_str = f"""
- [대운 체(전반기/천간): {dw_che_1}] / [대운 체(후반기/지지): {dw_che_2}] / 현재 활성: {dw_che_active} ({'전반기' if dw_is_first else '후반기'})
- [세운 체(전반기/천간): {sewun_che_1}] / [세운 체(후반기/지지): {sewun_che_2}] / 현재 활성: {sewun_che_active} + 실행({s_yong}) ➔ 키워드: [{sewun_kw}]
- [월운 체(전반기/천간): {wolun_che_1}] / [월운 체(후반기/지지): {wolun_che_2}] / 현재 활성: {wolun_che_active} + 실행({w_yong}) ➔ 키워드: [{wolun_kw}]
- [일운 체(전반기/천간): {ilun_che_1}] / [일운 체(후반기/지지): {ilun_che_2}] / 현재 활성: {ilun_che_active} + 실행({i_yong}) ➔ 키워드: [{ilun_kw}]
- [일운 하루 흐름] 전반기(00:30~13:29, 천간) 키워드: [{ilun_kw_1}] / 후반기(13:30~다음날 00:29, 지지) 키워드: [{ilun_kw_2}]
"""
    return {
        "dw_che": dw_che_active, "dw_che_1": dw_che_1, "dw_che_2": dw_che_2,
        "sewun_che": sewun_che_active, "sewun_yong": s_yong, "sewun_kw": sewun_kw,
        "wolun_che": wolun_che_active, "wolun_yong": w_yong, "wolun_kw": wolun_kw,
        "ilun_che": ilun_che_active, "ilun_yong": i_yong, "ilun_kw": ilun_kw,
        "ilun_kw_first": ilun_kw_1, "ilun_kw_second": ilun_kw_2,
        "woonse_fact_str": woonse_fact_str.strip()
    }

# ---- 2-B. [1-4] 이번 주 일운 · 주간 달력 ----

def get_weekly_calendar_data(target_date, ds_hanja, yb=None, db=None):
    """지정된 날짜가 속한 한 주(일~토)의 일별 간지/십성/12운성 데이터 생성"""
    target_dt = dt_mod.datetime(target_date.year, target_date.month, target_date.day)
    start_sun = target_dt - dt_mod.timedelta(days=(target_dt.weekday() + 1) % 7)
    weekday_kr = ['일', '월', '화', '수', '목', '금', '토']
    result = []
    for i in range(7):
        curr = start_sun + dt_mod.timedelta(days=i)
        _, _, d_pillar = get_ganji_from_date(curr.year, curr.month, curr.day)
        d_gan, d_ji = d_pillar[0], d_pillar[1]
        result.append({
            "day_num": curr.day,
            "weekday_kr": weekday_kr[i],
            "gan": d_gan,
            "ji": d_ji,
            "ss_gan": get_ss(ds_hanja, d_gan),
            "ss_ji": get_ss(ds_hanja, d_ji),
            "unsung": get_unsung(ds_hanja, d_ji),
            "y_shinsal": get_12_shinsal(yb, d_ji) if yb else "-",
            "d_shinsal": get_12_shinsal(db, d_ji) if db else "-",
            "is_today": (curr.date() == target_dt.date())
        })
    return result

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


# ---- 2-C. 신살 전/후반기 재해석 · 오행 결핍 보충 ----

SHINSAL_PHASE_REINTERPRET = {
    "나체도화": {
        "후반기": "노년기·기혼 상태에서는 성적 매력의 과시가 아니라, 심미안과 문화적 감수성으로 승화되어 발현되는 경향이 있음",
    },
    "고란살": {
        "후반기": "젊은 시절의 '자녀 복 약함'이라는 숙명적 해석보다는, 노년기에는 정신적 자산과 개인적 유산을 스스로 구축하는 자립성으로 재해석될 수 있음",
    },
}

def get_shinsal_phase_note(shinsal_name, is_first_half):
    """특정 신살이, 지금 활성화된 반기(전반기/후반기)에 따라 재해석 문구를 갖고 있으면 반환. 없으면 빈 문자열."""
    phase_key = "전반기" if is_first_half else "후반기"
    entry = SHINSAL_PHASE_REINTERPRET.get(shinsal_name, {})
    return entry.get(phase_key, "")

def get_dynamic_shinsal_fact_str(idx, gans, jjis, gender, is_daewun_first_half):
    """신살 목록을 계산하고, 반기별 재해석 문구가 있으면 함께 붙여서 텍스트로 반환 (연구용 4-1/4-2 전용)"""
    raw_list = get_general_shinsal_for_ai(idx, gans, jjis, gender)
    if not raw_list:
        return "특이 신살 없음"
    lines = []
    for item in raw_list:
        clean_name = re.sub(r'<[^>]+>', '', str(item))
        note = get_shinsal_phase_note(clean_name, is_daewun_first_half)
        if note:
            lines.append(f"- {clean_name}: (현재 대운 {'전반기' if is_daewun_first_half else '후반기'} 활성 → {note})")
        else:
            lines.append(f"- {clean_name}")
    return "\n".join(lines)

def _shinsal_base_names(idx, gans, jjis, gender):
    """신살 목록 → {이름: 원문} (괄호·설명 앞의 이름만 뽑아 중복 제거)"""
    names = {}
    for item in get_general_shinsal_for_ai(idx, gans, jjis, gender) or []:
        clean = re.sub(r'<[^>]+>', '', str(item)).strip()
        base = re.split(r'[\(\[:：]', clean)[0].strip()
        if base and base not in names:
            names[base] = clean
    return names

def get_couple_shinsal_compare_str(m_gans, m_jjis, f_gans, f_jjis, idx=1):
    """남명·여명의 신살 이름을 비교해 '공통 / 남명에만 / 여명에만'을 사실문으로 돌려줍니다."""
    try:
        m = _shinsal_base_names(idx, m_gans, m_jjis, "남성")
        f = _shinsal_base_names(idx, f_gans, f_jjis, "여성")
    except Exception:
        return "신살 비교 정보 없음"
    if not m and not f:
        return "비교할 신살 없음"
    common = [k for k in m if k in f]
    only_m = [k for k in m if k not in f]
    only_f = [k for k in f if k not in m]
    return (f"공통 신살: {', '.join(common) or '없음'} / 남명에만 있는 신살: {', '.join(only_m) or '없음'} / "
            f"여명에만 있는 신살: {', '.join(only_f) or '없음'}")

def get_couple_pillars_fact_str(m_gans, m_jjis, f_gans, f_jjis):
    """남명·여명의 네 기둥(년·월·일·시)을 자리 순서까지 고정한 사실문으로 돌려줍니다.
    목록 순서: 0=시, 1=일, 2=월, 3=년 (앱 전체 공통). 비어 있는 기둥은 '미상'으로 표시합니다."""
    def _one(g, j):
        def _p(i):
            try:
                a = str(g[i]).strip() if g[i] else ""
                b = str(j[i]).strip() if j[i] else ""
            except Exception:
                return "미상"
            return f"{a}{b}" if (a and b) else "미상"
        return f"년주 {_p(3)} / 월주 {_p(2)} / 일주 {_p(1)} / 시주 {_p(0)}"
    try:
        return f"남명 원국({_one(m_gans, m_jjis)}) / 여명 원국({_one(f_gans, f_jjis)})"
    except Exception:
        return "원국 정보 없음"

def get_couple_ji_rel_facts(m_jjis, f_jjis):
    """남명·여명 지지끼리의 관계(일지·년지·월지·시지) 사실문. 목록 순서: 0=시, 1=일, 2=월, 3=년 (앱 전체 공통)."""
    MEAN = {"충": "서로 부딪힘", "형": "서로 어긋나 틀어짐", "원진": "끌리면서도 서운함이 쌓이는 어긋남(애증)", "귀문": "마음이 예민해져 생각이 꼬이기 쉬움",
            "파": "서로 깨지듯 흔들림", "해": "서로 엇나감", "육합": "서로 당겨 묶임", "반합": "서로 당겨 힘을 모음",
            "방합": "같은 기운으로 이어짐", "방합(미완)": "같은 기운으로 이어짐", "암합": "속으로 은근히 끌림",
            "공합": "가운데 글자가 빠져 있어 힘이 약하게 이어짐", "공협": "가운데 글자가 빠져 있어 힘이 약하게 이어짐",
            "자형": "같은 글자라 스스로 부딪힘", "천라": "답답하게 얽힘", "지망": "답답하게 얽힘"}

    def _rel(a, b):
        a, b = _to_hanja_ji(a), _to_hanja_ji(b)
        if not a or not b or a not in JI or b not in JI:
            return "미상"
        rel = get_ji_rel_set(a, b)
        if rel == "-":
            return f"{a}–{b}: 특별한 합충 없이 무난함"
        tags = [t.strip() for t in rel.split(",")]
        return f"{a}–{b}: " + "·".join(tags) + "[" + " / ".join(MEAN.get(t, t) for t in tags) + "]"

    try:
        _ms = {_to_hanja_ji(x) for x in m_jjis if _to_hanja_ji(x) in JI}
        _fs = {_to_hanja_ji(x) for x in f_jjis if _to_hanja_ji(x) in JI}
        _done = []
        for _kind, _trios in (("삼합", _SAMHAP_TRIOS), ("방합", _BANGHAP_TRIOS)):
            for _t in _trios:
                if _t <= (_ms | _fs) and not _t <= _ms and not _t <= _fs:
                    _done.append(f"{''.join(sorted(_t, key=JI.index))} {_kind} 완성")
        _extra = (" / 두 분 지지를 합쳐 세 글자가 모두 모인 합: " + ", ".join(_done)) if _done else ""
        return (f"일지끼리(내면의 유대감) {_rel(m_jjis[1], f_jjis[1])} / 년지끼리(띠 겉궁합) {_rel(m_jjis[3], f_jjis[3])} / "
                f"월지끼리 {_rel(m_jjis[2], f_jjis[2])} / 시지끼리 {_rel(m_jjis[0], f_jjis[0])}" + _extra)
    except Exception:
        return "지지 관계 정보 없음"

def get_ohang_deficiency_supply_str(counts, level_phase_data):
    """
    원국에 결핍된 오행이, 대운/세운/월운/일운 각 단계의 '현재 활성화된 반기'에서 실제로 공급되고 있는지 정밀 판정.
    level_phase_data: [(레벨이름, 천간문자, 지지문자, 지금이_전반기인가_bool), ...]
    예: [("대운", dw_g_cur, dw_j_cur, _is_daewun_first_half(age, dw_start_age)), ...]
    """
    missing = [oh for oh, c in counts.items() if c == 0]
    if not missing:
        return "원국에 오행 결핍 없음 (모든 오행 보유)"
 
    lines = []
    for oh in missing:
        active_hits = []   # 지금 활성화된 반기에서 실제로 발동 중
        latent_hits = []   # 아직 비활성 반기에 잠재만 되어 있음
        for level_name, gan_char, ji_char, is_first_half in level_phase_data:
            active_char = gan_char if is_first_half else ji_char
            latent_char = ji_char if is_first_half else gan_char
            phase_label = "전반기(천간)" if is_first_half else "후반기(지지)"
            latent_phase_label = "후반기(지지)" if is_first_half else "전반기(천간)"
            if active_char and get_color(active_char) == oh:
                active_hits.append(f"{level_name} {phase_label}")
            if latent_char and get_color(latent_char) == oh:
                latent_hits.append(f"{level_name} {latent_phase_label}")
 
        if active_hits:
            lines.append(f"- 원국에 없는 {oh} 기운이 현재 {', '.join(dict.fromkeys(active_hits))}에서 실질적으로 활성화되어 발동 중임")
        elif latent_hits:
            lines.append(f"- 원국에 없는 {oh} 기운이 {', '.join(dict.fromkeys(latent_hits))}에 존재하나, 아직 활성화되지 않은 반기라 잠재된 상태이며 향후 그 반기가 도래하면 발동될 것")
        else:
            lines.append(f"- 원국에 없는 {oh} 기운이 현재 대운·세운·월운·일운 어디에도 없어 여전히 결핍 상태임")
    return "\n".join(lines)


# ---- 2-D. 묘고(墓庫) 입고/개고 · 삼형 동적 발동 ----

def check_samhyung_facts(jjis, dw_j=None, sewun_j=None, wolun_j=None, ilun_j=None):
    jjis_h = [_to_hanja(j) for j in jjis if j not in ["?", "-", " "]]
    results = []
 
    in_set = {'寅', '巳', '申'}
    sul_set = {'丑', '戌', '未'}
 
    won_in_present = in_set.intersection(set(jjis_h))
    won_sul_present = sul_set.intersection(set(jjis_h))
 
    if len(won_in_present) == 3:
        results.append("🔥 [원국 인사신(寅巳申) 삼형살 완성] 세 글자가 서로 얽혀 긴장과 압박이 높고, 일·관계에서 갑작스러운 변동이나 부딪힘이 생기기 쉬운 구조(무은지형: 도와준 일이 서운함으로 돌아오기 쉬운 형). 사건·질병을 단정하지 말 것.")
    elif len(won_in_present) == 2:
        missing = list(in_set - won_in_present)[0]
        results.append(f"⚠️ [원국 인사신(寅巳申) 가형(假刑) 상태] 원국에 {','.join(won_in_present)} 보유 중. 운에서 '{missing}'이 들어올 때 삼형살이 완성되니 갑작스러운 변동과 부딪힘에 유의.")
 
    if len(won_sul_present) == 3:
        results.append("🔥 [원국 축술미(丑戌未) 삼형살 완성] 원국에 이미 갖춰진 바탕으로, 그해 운의 글자와는 별개로 평소 깔려 있음(재물·건강·인간관계의 재편 및 정교한 조정 에너지가 내재됨). 운의 글자가 丑·戌·未일 때만 다시 흔들림.")
    elif len(won_sul_present) == 2:
        missing = list(sul_set - won_sul_present)[0]
        results.append(f"⚠️ [원국 축술미(丑戌未) 가형(假刑) 상태] 원국에 {','.join(won_sul_present)} 보유 중. 운에서 '{missing}'이 들어올 때 삼형살이 완성되니 재물·건강 조정 주의 요망.")
 
    hangun_list = []
    if dw_j and dw_j not in ["?", "-", " "]: hangun_list.append(("대운", _to_hanja(dw_j)))
    if sewun_j and sewun_j not in ["?", "-", " "]: hangun_list.append(("세운", _to_hanja(sewun_j)))
    if wolun_j and wolun_j not in ["?", "-", " "]: hangun_list.append(("월운", _to_hanja(wolun_j)))
    if ilun_j and ilun_j not in ["?", "-", " "]:
        _il = str(ilun_j).strip()
        hangun_list.append(("일운", _to_hanja(_il[-1] if len(_il) > 1 else _il)))   # '己未'처럼 두 글자가 와도 지지만 사용
 
    for u_type, u_j in hangun_list:
        combined_set = set(jjis_h + [u_j])
        if len(won_in_present) == 2 and in_set.issubset(combined_set) and u_j in in_set:
            results.append(f"🚨 [{u_type}({u_j}) 인사신 삼형 완성] {u_type} 지지({u_j})가 기폭제가 되어 인사신 삼형살 발동!")
 
        if len(won_sul_present) == 2 and sul_set.issubset(combined_set) and u_j in sul_set:
            results.append(f"🚨 [{u_type}({u_j}) 축술미 삼형 완성] {u_type} 지지({u_j})가 기폭제가 되어 축술미 삼형살 발동!")

        if len(won_sul_present) == 3 and u_j in sul_set:
            results.append(f"🚨 [{u_type}({u_j}) 축술미 삼형 재발동] 원국에 삼형이 이미 갖춰진 상태에서 {u_type} 지지({u_j})가 같은 계열이라 삼형이 다시 크게 흔들림!")

    return " / ".join(results) if results else "(없음 — 글에 쓰지 말 것. 시간대 팩트에 적힌 것만 따름)"

_UN_CHUNG = {frozenset(p) for p in ["子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥"]}
_UN_HAP = {frozenset(p) for p in ["子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未"]}
_UN_HAE = {frozenset(p) for p in ["子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌"]}
_UN_PA = {frozenset(p) for p in ["子酉", "丑辰", "寅亥", "卯午", "巳申", "未戌"]}
_UN_SAMHAP = [("申子辰", "水"), ("亥卯未", "木"), ("寅午戌", "火"), ("巳酉丑", "金")]
_UN_BANGHAP = [("寅卯辰", "木"), ("巳午未", "火"), ("申酉戌", "金"), ("亥子丑", "水")]
_GAN_HAP = {frozenset(x) for x in ["甲己", "乙庚", "丙辛", "丁壬", "戊癸"]}
_GAN_CHUNG = {frozenset(x) for x in ["甲庚", "乙辛", "丙壬", "丁癸"]}

def get_unun_gan_relation_facts(gans, u_g, u_type="세운"):
    """운의 천간이 원국 천간(시간·일간·월간·년간)과 맺는 합, 일간과의 충. gans=[시간, 일간, 월간, 년간]."""
    u = _to_hanja(str(u_g).strip()[-1]) if u_g else ""
    if not u or u in ("?", "-", " "):
        return ""
    out = []
    for nm, g in zip(["시간", "일간", "월간", "년간"], gans):
        h = _to_hanja(g) if g else ""
        if not h or h in ("?", "-", " "):
            continue
        if h == u:
            out.append(f"{u_type} 천간({u})이 원국 {nm}({h})와 같은 글자로 겹침(복음)")
            continue
        pair = frozenset((u, h))
        if pair in _GAN_HAP: out.append(f"{u_type} 천간({u})이 원국 {nm}({h})와 합")
        if pair in _GAN_CHUNG:
            if nm == "일간": out.append(f"{u_type} 천간({u})이 일간({h})을 충")
            else: out.append(f"{u_type} 천간({u})이 원국 {nm}({h})를 충")
    return " / ".join(out)

def get_gan_rel_facts(gans):
    """천간 합·충·극 팩트(격합·제어 설명 포함). gans=[시간, 일간, 월간, 년간]."""
    _OH = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    _GK = {('木','土'), ('土','水'), ('水','火'), ('火','金'), ('金','木')}
    _HP = [{'甲','己'}, {'乙','庚'}, {'丙','辛'}, {'丁','壬'}, {'戊','癸'}]
    _CH = [{'甲','庚'}, {'乙','辛'}, {'丙','壬'}, {'丁','癸'}]
    def _geuk(a, b):
        return (_OH[a], _OH[b]) in _GK
    gans = [_to_hanja(g) if g else "" for g in gans]
    names = ["시간", "일간", "월간", "년간"]
    out = []
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = gans[i], gans[j]
            if a not in _OH or b not in _OH:
                continue
            s = {a, b}
            nm = f"{names[i]}({a})-{names[j]}({b})"
            if j - i == 1:
                if s in _HP:
                    out.append(f"{nm} 붙어 있는 합")
                elif s in _CH:
                    out.append(f"{nm} 붙어 있는 충(천간끼리 정면으로 맞부딪침)")
                elif _geuk(a, b) or _geuk(b, a):
                    out.append(f"{nm} 붙어 있는 극(한쪽이 다른 쪽을 누름)")
            elif s in _HP:
                blk = [gans[k] for k in range(i + 1, j)
                       if gans[k] in _OH and any(_geuk(gans[k], m) for m in (a, b))]
                if blk:
                    out.append(f"{nm} 떨어진 격합이나, 사이의 {'·'.join(blk)}이 합하는 글자를 극하여 제어되어 합하지 못함")
                else:
                    out.append(f"{nm} 떨어진 격합(영향력이 약한 합. 합화·성합은 불가)")
    return " / ".join(out) if out else "원국 천간 사이에 특이한 합·충·극 없음"

def get_gan_wonguk_facts(gans):
    """원국 천간끼리의 합·충 팩트. gans=[시간, 일간, 월간, 년간]."""
    names = ["시간", "일간", "월간", "년간"]
    out = []
    for i in range(3):
        j = i + 1
        a = _to_hanja(gans[i]) if gans[i] else ""
        b = _to_hanja(gans[j]) if gans[j] else ""
        if not a or not b or a in ("?", "-", " ") or b in ("?", "-", " "):
            continue
        pair = frozenset((a, b))
        if pair in _GAN_HAP: out.append(f"{names[i]}({a})와 {names[j]}({b})가 붙어서 합")
        if pair in _GAN_CHUNG: out.append(f"{names[i]}({a})와 {names[j]}({b})가 붙어서 충")
    return " / ".join(out) if out else "원국 천간에 붙어 있는 합·충 없음(떨어진 격합·격충은 제외)"

def get_unun_relation_facts(jjis, u_j, u_type="일운", gans=None, u_g=None):
    """운(대운/세운/월운/일운)의 지지가 원국 지지(시·일·월·년)와 맺는 충·합·해·파·복음을 팩트 문장으로 만듭니다."""
    names = ["시지", "일지", "월지", "년지"]
    u = _to_hanja(str(u_j).strip()[-1])
    nat = [_to_hanja(j) for j in jjis]
    out = []
    for nm, j in zip(names, nat):
        if j in ["?", "-", " "]:
            continue
        pair = frozenset((u, j))
        if u == j:
            if u in "辰午酉亥":
                out.append(f"{u_type}({u})이 원국 {nm}({j})와 같은 글자로 겹침(복음, 자형에도 해당)")
            else:
                out.append(f"{u_type}({u})이 원국 {nm}({j})와 같은 글자로 겹침(복음)")
            continue
        if pair in _UN_CHUNG: out.append(f"{u_type}({u})이 원국 {nm}({j})와 충")
        if pair in _UN_HAP: out.append(f"{u_type}({u})이 원국 {nm}({j})와 육합")
        if pair in _UN_HAE: out.append(f"{u_type}({u})이 원국 {nm}({j})와 해")
        if pair in _UN_PA: out.append(f"{u_type}({u})이 원국 {nm}({j})와 파")
        if pair == frozenset("子卯"): out.append(f"{u_type}({u})이 원국 {nm}({j})와 자묘형")
        if pair in {frozenset(p) for p in ("寅巳", "巳申", "丑戌", "戌未")}: out.append(f"{u_type}({u})이 원국 {nm}({j})와 형")
    nat_set = {j for j in nat if j not in ["?", "-", " "]}
    ilji = nat[1] if len(nat) > 1 else ""
    for trio, oh in _UN_SAMHAP:
        if u not in trio:
            continue
        others = set(trio) - {u}
        have = others & nat_set
        # 책 기준: 운에서 삼합·반합이 성립하려면 일지가 그 안에 들어가야 함
        if ilji not in trio or ilji == "?":
            continue
        if len(have) == 2:
            out.append(f"{u_type}({u})이 원국과 {trio} {oh}국 삼합 완성(일지 포함)")
        elif len(have) == 1 and list(have)[0] == ilji and (u == trio[1] or ilji == trio[1]):
            out.append(f"{u_type}({u})이 원국 일지({ilji})와 {oh}국 반합")
    for trio, oh in _UN_BANGHAP:
        if u in trio and (set(trio) - {u}) <= nat_set:
            out.append(f"{u_type}({u})이 원국과 {trio} {oh}국 방합 완성")
    ji_txt = " / ".join(dict.fromkeys(out)) if out else ""
    gan_txt = get_unun_gan_relation_facts(gans, u_g, u_type) if (gans and u_g) else ""
    parts = [t for t in (gan_txt, ji_txt) if t]
    return " / ".join(parts) if parts else f"{u_type}({u})과 원국 사이에 특이한 충·합 없음"

def get_jaeseong_fact(ds, gans, jjis, gender="여성"):
    """재성(정재·편재)이 원국에 있는지와 관련 육친(아버지·아내 등)을 팩트로 만듭니다.
    gans=[시간, 월간, 년간], jjis=[시지, 일지, 월지, 년지]. 천간과 지지 본기 기준."""
    dm = get_color(ds)
    if not dm or dm not in _OHAENG_CYCLE:
        return "일간을 알 수 없어 재성 판정을 생략합니다."
    names = list(zip(["시간", "월간", "년간"], gans)) + list(zip(["시지", "일지", "월지", "년지"], jjis))
    jae = []
    for nm, c in names:
        h = _to_hanja(c) if c else ""
        if not h or h in ("?", "-", " "):
            continue
        if get_ss(ds, h) in ("정재", "편재"):
            jae.append(f"{nm}({h})")
    rel = "아버지·아내(배우자)" if str(gender).startswith("남") else "아버지(편재)·시어머니(정재)"
    if jae:
        return f"재성(정재·편재)이 원국에 있음: {', '.join(jae)} — 재물(수입·재산을 만드는 힘)과 관련 육친({rel}) 모두 이 재성으로 봄"
    # 겉(천간·지지 본기)에는 없지만 지장간 속에 숨어 있는지 확인
    hidden = []
    _role = ["초기의 아주 약한 기운", "중기의 약한 기운", "본기"]
    for nm, c in zip(["시지", "일지", "월지", "년지"], jjis):
        h = _to_hanja(c) if c else ""
        for idx, g in enumerate(JIJANGGAN.get(h, [])):
            if g != '-' and get_ss(ds, g) in ("정재", "편재"):
                hidden.append(f"{nm}({h}) 속 {g}({get_ss(ds, g)}, {_role[idx]})")
    if hidden:
        return (f"재성(정재·편재)이 겉으로는 드러나 있지 않고 지장간 속에 희미하게 숨어 있음: {', '.join(hidden)} — "
                f"모두 초기·중기의 약한 기운이라 재물의 힘이 크지 않음. 재물(수입·재산을 쌓는 기반)과 관련 육친({rel})의 인연은 겉으로는 약하게 보이고 속에는 희미하게 잠재해 있어, "
                f"스스로 활동으로 끌어내야 하고 운에서 재성이 들어올 때 비로소 또렷해질 수 있음. 숨은 재성의 힘을 크게 풀거나 재물 유형(유통형 등)을 단정하지 말 것")
    return (f"재성(정재·편재)이 원국에 전혀 없음 — 재물(수입·재산을 쌓는 기반)과 관련 육친({rel})의 인연이 모두 원국에서는 약하게 시작함. "
            f"운에서 재성이 들어올 때 재물 문제와 그 육친 문제가 함께 부각될 수 있음")

def get_inseong_fact(ds, gans, jjis):
    GAN_EL = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    YANG = set('甲丙戊庚壬')
    PRODUCER = {'木':'水','火':'木','土':'火','金':'土','水':'金'}
    HIDDEN = {'子':'壬癸','丑':'癸辛己','寅':'戊丙甲','卯':'甲乙','辰':'乙癸戊','巳':'戊庚丙',
              '午':'丙己丁','未':'丁乙己','申':'己壬庚','酉':'庚辛','戌':'辛丁戊','亥':'戊甲壬'}
    GAN_NM = ["시간", "일간", "월간", "년간"]
    JI_NM = ["시지", "일지", "월지", "년지"]
    if ds not in GAN_EL:
        return ""
    ins_el = PRODUCER[GAN_EL[ds]]
    def kind(g):
        return "편인" if ((g in YANG) == (ds in YANG)) else "정인"
    shown, hidden = [], []
    for i, g in enumerate(gans):
        if i != 1 and g in GAN_EL and GAN_EL[g] == ins_el:
            shown.append(f"{GAN_NM[i]} {g}({kind(g)})")
    for i, j in enumerate(jjis):
        for g in HIDDEN.get(j, ""):
            if GAN_EL[g] == ins_el:
                hidden.append(f"{JI_NM[i]} {j} 속 {g}({kind(g)})")
    if shown:
        return (f"문서·계약의 기운(인성, {ins_el})이 원국 천간에 드러나 있음: {', '.join(shown)}"
                + (f" / 지지 속에도 있음: {', '.join(hidden)}" if hidden else ""))
    if hidden:
        return (f"문서·계약의 기운(인성, {ins_el})이 천간에는 없고 지지 속에 숨어 있음: {', '.join(hidden)} "
                f"— 운에서 {ins_el} 글자가 들어올 때 문서·계약 기운이 활발해짐(창고가 열리는지는 별도의 창고 사실문 기준)")
    return (f"문서·계약의 기운(인성, {ins_el})이 원국에 전혀 없음 — 문서·자격·계약의 기반이 약하게 시작하며, "
            f"운에서 {ins_el} 글자가 들어올 때만 문서 기운이 생김")

def get_dosik_fact(ds, gans, jjis):
    """도식(효신탈식): 편인이 식신을 극해 식신의 기운이 눌리는 구조를 팩트로 만듭니다.
    gans=[시간, 월간, 년간], jjis=[시지, 일지, 월지, 년지] (일간 자신은 제외). 천간과 지지 본기의 십성 기준."""
    dm = get_color(ds)
    if not dm or dm not in _OHAENG_CYCLE:
        return "일간을 알 수 없어 도식 판정을 생략합니다."
    names = list(zip(["시간", "월간", "년간"], gans)) + list(zip(["시지", "일지", "월지", "년지"], jjis))
    pyeonin, siksin, jae = [], [], []
    for nm, c in names:
        h = _to_hanja(c) if c else ""
        if not h or h in ("?", "-", " "):
            continue
        ss = get_ss(ds, h)
        if ss == "편인": pyeonin.append(f"{nm}({h})")
        elif ss == "식신": siksin.append(f"{nm}({h})")
        elif ss in ("정재", "편재"): jae.append(f"{nm}({h})")
    if not pyeonin or not siksin:
        return f"도식(편인이 식신을 극하는 구조) 해당 없음: 원국에 편인 {'있음' if pyeonin else '없음'}, 식신 {'있음' if siksin else '없음'}"
    base = f"편인 {', '.join(pyeonin)} / 식신 {', '.join(siksin)}: 편인이 식신을 극하는 도식(효신탈식) 구조가 있어 식신의 표현력·활동성·자식 관련 기운이 눌릴 수 있음"
    if jae:
        return f"{base}. 다만 편인을 제압하는 재성이 원국에 있어({', '.join(jae)}) 도식이 풀릴 여지가 있음"
    return f"{base}. 편인을 제압하는 재성이 원국에 없어 도식이 풀리지 않고 그대로 작동함"

def get_text_year_relation_facts(text, jjis, birth_year=None, daewun_list=None, max_years=12, gans=None):
    """타 감명서 원문에 나온 연도(2019 등)와 간지년(己亥년 등)의 세운 지지가 원국 지지와 맺는
    충·합·삼합·방합 팩트를 만듭니다. jjis는 [시지, 일지, 월지, 년지] 순서.
    birth_year와 daewun_list(age_range·c_hanja·j_hanja)가 있으면 그 해의 나이와 대운도 함께 적습니다."""
    txt = str(text or "")
    years = []
    for m in re.finditer(r"(?<![\d,])(19\d{2}|20\d{2}|21\d{2})(?![\d,])(?!\s?(?:만|원|명|개|배|%|살|세|세기))", txt):
        y = int(m.group(1))
        if y not in years:
            years.append(y)
    lines, seen_gj = [], set()
    for y in years[:max_years]:
        base = (y - 1984) % 60
        gan = _to_hanja(GAN[base % 10]); ji = _to_hanja(JI[base % 12])
        seen_gj.add(gan + ji)
        head = f"{y}년({gan}{ji})"
        dw_rel = []
        if birth_year:
            try:
                age = y - int(birth_year) + 1
            except Exception:
                age = None
            if age and age > 0:
                head += f" {age}세"
                for dw in (daewun_list or []):
                    try:
                        a, b = [int(x) for x in re.findall(r"\d+", dw["age_range"])[:2]]
                    except Exception:
                        continue
                    if a <= age <= b:
                        head += f", {dw['c_hanja']}{dw['j_hanja']}대운"
                        dw_ji = _to_hanja(str(dw['j_hanja']).strip()[-1])
                        pair = frozenset((dw_ji, ji))
                        dw_gan = _to_hanja(str(dw['c_hanja']).strip()[-1])
                        found = []
                        if dw_ji == ji: found.append("같은 글자로 겹침(복음)")
                        if pair in _UN_CHUNG: found.append("충")
                        if pair in _UN_HAP: found.append("육합")
                        if pair in _UN_HAE: found.append("해")
                        if pair in _UN_PA: found.append("파")
                        if found:
                            dw_rel.append(f"세운 지지({ji})가 그 해 대운 지지({dw_ji})와 " + " · ".join(found))
                        gfound = []
                        gpair = frozenset((dw_gan, gan))
                        if dw_gan == gan: gfound.append("같은 글자로 겹침(복음)")
                        if gpair in _GAN_HAP: gfound.append("합")
                        if gpair in _GAN_CHUNG: gfound.append("충")
                        if gfound:
                            dw_rel.append(f"세운 천간({gan})이 그 해 대운 천간({dw_gan})과 " + " · ".join(gfound))
                        break
        lines.append(f"{head}: " + " / ".join(dw_rel + [get_unun_relation_facts(jjis, ji, "세운", gans, gan)]))
    for m in re.finditer(r"([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s?년", txt):
        gj = m.group(1)
        if gj in seen_gj or len(seen_gj) >= max_years:
            continue
        seen_gj.add(gj)
        lines.append(f"{gj}년(원문 표기): " + get_unun_relation_facts(jjis, gj[1], "세운", gans, gj[0]))
    return " / ".join(lines) if lines else "원문에 연도 표기 없음"

def get_yongshin_elements(yongshin_text):
    """get_yongshin_analysis가 만든 문장에서 용신·희신·기신·구신·한신(·겸용) 오행을 뽑아 사전으로 돌려줍니다."""
    out = {}
    txt = str(yongshin_text or "")
    for key, pat in [("용신", r"용신=([목화토금수])"),
                     ("희신", r"희신\([^)]*\)=([목화토금수])"),
                     ("기신", r"기신\([^)]*\)=([목화토금수])"),
                     ("구신", r"구신=([목화토금수])"),
                     ("한신", r"한신=([목화토금수])"),
                     ("겸용", r"겸용:([목화토금수])")]:
        m = re.search(pat, txt)
        if m:
            out[key] = m.group(1)
    return out

def get_unun_yongshin_status(yongshin_text, wolun_g, wolun_j, ilun_g, ilun_j):
    """이번 달(월운)·오늘(일운)의 천간·지지 오행이 용신·희신·겸용(도움) / 기신·구신(부담) / 그 외(중립) 중 무엇인지 사실문으로 돌려줍니다."""
    yong = get_yongshin_elements(yongshin_text)
    if not yong:
        return "월운·일운의 용신 관계 정보 없음"
    good = [yong.get(k) for k in ("용신", "희신", "겸용") if yong.get(k)]
    bad = [yong.get(k) for k in ("기신", "구신") if yong.get(k)]

    def tag(ch):
        oh = get_color(ch)
        if oh in good:
            return f"{ch}({oh}) 도움이 되는 기운"
        if oh in bad:
            return f"{ch}({oh}) 부담이 되는 기운"
        return f"{ch}({oh}) 중립"

    def cnt(a, b):
        sc = 0
        for ch in (a, b):
            oh = get_color(ch)
            sc += 1 if oh in good else (-1 if oh in bad else 0)
        return sc

    def verdict(sc):
        return "도움 쪽" if sc > 0 else ("부담 쪽" if sc < 0 else "도움과 부담이 엇비슷하거나 중립")

    w_sc, i_sc = cnt(wolun_g, wolun_j), cnt(ilun_g, ilun_j)
    return (f"[월운·일운 용신 관계 사실] 이번 달 월운 {wolun_g}{wolun_j}: 천간 {tag(wolun_g)}, 지지 {tag(wolun_j)} → 전체 {verdict(w_sc)}. "
            f"오늘 일운 {ilun_g}{ilun_j}: 천간 {tag(ilun_g)}, 지지 {tag(ilun_j)} → 전체 {verdict(i_sc)}. "
            "도움 기운이 겹치면 좋은 키워드를 그대로 살려 쓰고, 부담 기운이 겹치면 좋은 키워드도 '기회는 오지만 무리하면 부담이 따를 수 있다'는 조건부로 서술할 것.")

def _gan_rel_score(gans, u_gan, u_label):
    """운(월운·일진)의 천간이 원국 천간(시간·일간·월간·년간) 어느 자리와든 맺는 합·충을 점수와 짧은 메모로 돌려줍니다.
    합 +1 / 충: 일간 -2(무겁게), 그 밖의 자리 -1. 합화·합거로 단정하지 않고 사실만 적습니다."""
    u = _to_hanja(str(u_gan).strip()[-1]) if u_gan else ""
    if not gans or not u or u in ("?", "-", " "):
        return 0, [], False
    sc, notes, severe = 0, [], False
    for nm, g in zip(["시간", "일간", "월간", "년간"], gans):
        h = _to_hanja(g) if g else ""
        if not h or h in ("?", "-", " ") or h == u:
            continue
        pair = frozenset((u, h))
        if pair in _GAN_HAP:
            sc += 1; notes.append(f"{u_label}({u})이 원국 {nm}({h})와 합")
        if pair in _GAN_CHUNG:
            if nm == "일간":
                sc -= 2; severe = True
            else:
                sc -= 1
            notes.append(f"{u_label}({u})이 원국 {nm}({h})와 충")
    return sc, notes, severe

def _bokeum_score(jjis, gans, u_gan, u_ji):
    """운(월운·일진)의 글자가 원국과 겹치는 정도를 점수로 만듭니다.
    복음: 일지 -2(무겁게), 시·월·년지 -1 / 천지동복음(간지 전체가 한 기둥과 같음): 일주 -3(무겁게), 그 밖 -2 (복음 점수를 대신함)
    쌍복음(원국 두 곳 이상과 같은 글자): -1 추가, 일지가 포함되면 무겁게 / 자형(辰午酉亥): -1 추가
    jjis=[시지, 일지, 월지, 년지], gans=[시간, 일간, 월간, 년간]."""
    ji = _to_hanja(str(u_ji).strip()[-1]) if u_ji else ""
    gan = _to_hanja(str(u_gan).strip()[-1]) if u_gan else ""
    if not ji or ji in ("?", "-", " "):
        return 0, [], False
    names = ["시", "일", "월", "년"]
    hits = []        # 같은 지지가 있는 기둥 번호
    best = None      # (점수, 메모, 무겁게 여부)
    for i, nm in enumerate(names):
        j = _to_hanja(jjis[i]) if jjis[i] else ""
        if j != ji:
            continue
        hits.append(i)
        g = _to_hanja(gans[i]) if (gans and gans[i]) else ""
        if gan and g == gan:      # 천지동복음
            cand = (3 if nm == "일" else 2, f"원국 {nm}주와 간지가 똑같이 겹침(천지동복음)", nm == "일")
        else:                     # 복음
            cand = (2 if nm == "일" else 1, f"원국 {nm}지({j})와 같은 글자(복음)", nm == "일")
        if best is None or cand[0] > best[0]:
            best = cand
    if best is None:
        return 0, [], False
    sc, notes, severe = -best[0], [best[1]], best[2]
    if len(hits) >= 2:            # 쌍복음
        sc -= 1; notes.append("원국 두 곳 이상과 같은 글자(쌍복음)")
        if 1 in hits: severe = True
    if ji in "辰午酉亥":          # 자형
        sc -= 1; notes.append("같은 글자가 겹치는 자형")
    return sc, notes, severe

def get_year_month_facts(year, ds, db, ys, yb, jjis, cheon_eul_str, dw_j, yong=None, today=None, gans=None):
    """해당 연도 12개월의 월운 간지가 원국·세운과 맺는 충·파·해·삼형·공망·합·천을귀인과
    용신 오행을 따져 '기운이 도와주는 달'과 '서두르지 말 달'로 나눕니다.
    jjis는 [시지, 일지, 월지, 년지] 순서, dw_j는 현재 대운 지지입니다."""
    yong = yong or {}
    h2k = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}

    def oh_score(oh):
        if oh and oh in (yong.get("용신"), yong.get("희신"), yong.get("겸용")):
            return 1
        if oh and oh in (yong.get("기신"), yong.get("구신")):
            return -1
        return 0

    gm_day = calculate_gongmang(ds, db)
    gm_year = calculate_gongmang(ys, yb)
    guiin = [c for c in str(cheon_eul_str) if c in "子丑寅卯辰巳午未申酉戌亥"]
    sewun_raw = JI[(year - 1984) % 12]
    sj = _to_hanja(sewun_raw)
    good, bad = [], []
    cut = (today.year, today.month) if (today is not None and today.year == year) else None
    for tm in range(1, 13):
        try:
            _, m_p, _ = get_true_year_month_pillar(year, tm, 15, 12, 0)
        except Exception:
            continue
        gan, ji = _to_hanja(m_p[0]), _to_hanja(m_p[1])
        rel = get_unun_relation_facts(jjis, ji, "월운")
        sam = check_samhyung_facts(jjis, dw_j, sewun_j=sewun_raw, wolun_j=ji)
        score, notes, severe = 0, [], False
        if "와 충" in rel:
            _ch = re.findall(r"원국 (시지|일지|월지|년지)\(([^)]*)\)와 충", rel)
            score -= 2
            notes.append(("원국 " + "·".join(f"{n}({c})" for n, c in _ch) + "와 충") if _ch else "원국과 충")
            if re.search(r"(일지|월지)\([^)]*\)와 충", rel):
                severe = True
        if "와 형" in rel or "자묘형" in rel:
            score -= 2; notes.append("원국과 형")
            if re.search(r"(일지|월지)\([^)]*\)와 (?:자묘)?형", rel):
                severe = True
        if "와 파" in rel: score -= 1; notes.append("원국과 파")
        if "와 해" in rel: score -= 1; notes.append("원국과 해")
        _bs, _bn, _bsev = _bokeum_score(jjis, gans, gan, ji)
        score += _bs; notes.extend(_bn); severe = severe or _bsev
        if any(("월운(" in seg and "삼형 완성" in seg) for seg in re.split(r"\s*/\s*|\n", str(sam))):
            score -= 3; notes.append("삼형 완성"); severe = True
        if ji in gm_day: score -= 2; notes.append("일 기준 공망"); severe = True
        elif ji in gm_year: score -= 1; notes.append("년 기준 공망")
        if "육합" in rel:
            score += 2
            _m = re.findall(r"원국 (시지|일지|월지|년지)\(([^)]*)\)와 육합", rel)
            notes.append(("원국 " + "·".join(f"{n}({c})" for n, c in _m) + "와 육합") if _m else "원국과 육합")
        m = re.search(r"([木火土金水])국 삼합 완성", rel)
        if m:
            oh = h2k[m.group(1)]; score += oh_score(oh) * 2; notes.append(f"{oh}국 삼합 완성")
        else:
            m = re.search(r"([木火土金水])국 반합", rel)
            if m:
                oh = h2k[m.group(1)]; score += oh_score(oh); notes.append(f"{oh}국 반합")
        pair = frozenset((ji, sj))
        if ji != sj:
            if pair in _UN_CHUNG: score -= 1; notes.append("세운과 충")
            elif pair in _UN_HAP: score += 1; notes.append("세운과 육합")
        if ji in guiin: score += 2; notes.append("천을귀인")
        if gans:
            _gs, _gn, _gsev = _gan_rel_score(gans, gan, "월운 천간")
            score += _gs; notes.extend(_gn); severe = severe or _gsev
        e = oh_score(get_color(gan)) + oh_score(get_color(ji))
        if e > 0: score += e; notes.append("월운 오행이 이로움")
        elif e < 0: score += e; notes.append("월운 오행이 해로움")
        if not notes:
            continue
        tag = f"{tm}월 {gan}{ji}월: " + ", ".join(notes)
        if cut and (year, tm) < cut:
            tag += " [이미 지난 달]"
        if severe:
            bad.append((score, tm, tag))
        elif score >= 2:
            good.append((score, tm, tag))
    good = sorted(sorted(good, key=lambda x: (-x[0], x[1]))[:4], key=lambda x: x[1])
    bad = bad[:5]
    return (f"[{year}년 월별 팩트]\n[기운이 도와주는 달] " + (" / ".join(t for _, _, t in good) if good else "뚜렷한 달 없음")
            + "\n[서두르지 말 달] " + (" / ".join(t for _, _, t in bad) if bad else "뚜렷한 달 없음"))

def get_time_block_relation_facts(jjis, wolun_j=None, ilun_j=None, now=None):
    blocks = [("오전(05:30~11:29)", "卯辰巳"), ("오후(11:30~17:29)", "午未申"), ("저녁(17:30~23:29)", "酉戌亥")]
    _CLK = {"卯": "오전 5시 30분~7시 30분", "辰": "오전 7시 30분~9시 30분", "巳": "오전 9시 30분~11시 30분", "午": "11시 30분~오후 1시 30분", "未": "오후 1시 30분~3시 30분",
            "申": "오후 3시 30분~5시 30분", "酉": "오후 5시 30분~7시 30분", "戌": "오후 7시 30분~9시 30분", "亥": "오후 9시 30분~11시 30분"}
    _END = {"卯": 7*60+29, "辰": 9*60+29, "巳": 11*60+29, "午": 13*60+29, "未": 15*60+29,
            "申": 17*60+29, "酉": 19*60+29, "戌": 21*60+29, "亥": 23*60+29}
    _now_min = (now.hour * 60 + now.minute) if now is not None else None
    _SUL = {"丑", "戌", "未"}
    _base = {_to_hanja(x) for x in jjis} | {_to_hanja(x) for x in (wolun_j, ilun_j) if x}
    lines = []
    if _now_min is not None:
        lines.append(f"[지금 시각: {now.hour:02d}:{now.minute:02d} — '(이미 지난 시간)'이 붙은 시간대는 과거형으로만 짧게 말하고, 행동 권유는 지금 이후의 시간대에만 할 것]")
    for title, brs in blocks:
        parts = []
        for b in brs:
            tag = "(이미 지난 시간) " if (_now_min is not None and _now_min > _END[b]) else ""
            rel = get_unun_relation_facts(jjis, b, _CLK[b])
            if "특이한 충·합 없음" not in rel:
                parts.append(" / ".join(tag + s for s in rel.split(" / ")))
            if b in _SUL and _SUL <= (_base | {b}) and not (_SUL <= _base):
                _tg = ["일지"] if _to_hanja(jjis[1]) in _SUL else [n for n, x in (("월지", jjis[2]), ("시지", jjis[0])) if _to_hanja(x) in _SUL]
                parts.append(tag + f"{_CLK[b]}: 이 시간대의 글자({b})가 더해져 원국·월운과 함께 축술미 삼형 완성 — " + ("·".join(_tg) if _tg else "원국") + " 창고가 움직이는 시간(입고·개고는 그날의 날짜별 설명을 따름)")
        lines.append(f"[{title}] " + (" / ".join(parts) if parts else "원국과 특이한 충·합·형 없음"))
    return "\n".join(lines)

def get_year_wolun_che_flow_str(year, ds, db, today=None):
    """올해 1~12월 월운의 체용(폭포수) 키워드를 월별로 계산"""
    ilju_lower_group = get_group_ss(get_ss(ds, db))
    lines = []
    for tm in range(1, 13):
        try:
            term_day, _ = _get_term_day(year, tm)
            _, m_p, _ = get_true_year_month_pillar(year, tm, term_day + 3, 12, 0)
            w_gan, w_ji = _to_hanja(m_p[0]), _to_hanja(m_p[1])
            che_1 = get_group_ss(get_ss(ds, w_gan))
            che_2 = get_group_ss(get_ss(ds, w_ji))
            parts = []
            for label, che, offs in (("전반기", che_1, 3), ("후반기", che_2, 17)):
                dt0 = dt_mod.datetime(year, tm, min(term_day + offs, 28))
                sy = year if dt0 >= dt_mod.datetime(year, 2, 4) else year - 1
                sbase = (sy - 1984) % 60
                sg, sj = _to_hanja(GAN[sbase % 10]), _to_hanja(JI[sbase % 12])
                s_first = (sy == year) and (dt_mod.datetime(sy, 2, 4) <= dt0 < dt_mod.datetime(sy, 8, 7))
                s_che = get_group_ss(get_ss(ds, sg if s_first else sj))
                yong = get_execution_yong(che, ilju_lower_group)
                parts.append(f"{label}[체({che})→{get_matrix_keyword(s_che, yong)}]")
            tag = f"{tm}월 {w_gan}{w_ji}월: " + " / ".join(parts)
            if tm == 1:
                tag += " (전년도 세운 말기)"
            if today is not None and today.year == year and tm < today.month:
                tag += " [이미 지난 달]"
            lines.append(tag)
        except Exception:
            continue
    return f"[{year}년 월운 체용 흐름] " + " // ".join(lines) if lines else "월운 체용 정보 없음"


def get_yeonin_wolun_flow_str(year0, ds, db, gender, today=None, span=10, max_years=3):
    """이성 인연의 별(여성: 정관·편관 / 남성: 정재·편재)이 들어오거나 일지와 합이 되는 해를 고르고,
    그 해의 해당 달(월운)까지 사실문으로 만든다"""
    try:
        g = str(gender).strip().lower()
        is_f = g.startswith("여") or g in ("f", "female")
        star = ("정관", "편관") if is_f else ("정재", "편재")
        hap_map = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅', '卯': '戌', '戌': '卯',
                   '辰': '酉', '酉': '辰', '巳': '申', '申': '巳', '午': '未', '未': '午'}
        ilji = _to_hanja(db)
        hap = hap_map.get(ilji)
        picks = []
        for y in range(year0, year0 + span):
            sbase = (y - 1984) % 60
            sg, sj = _to_hanja(GAN[sbase % 10]), _to_hanja(JI[sbase % 12])
            why = []
            if get_ss(ds, sg) in star:
                why.append(f"세운 앞부분(2월 초~8월 초)에 이성 인연의 별({get_ss(ds, sg)}) 기운이 들어옴")
            if get_ss(ds, sj) in star:
                why.append(f"세운 뒷부분(8월 초~다음 해 2월 초)에 이성 인연의 별({get_ss(ds, sj)}) 기운이 들어옴")
            if hap and sj == hap:
                why.append(f"세운 뒷부분(8월 초~다음 해 2월 초)에 배우자 자리({ilji})와 합이 되는 글자({sj})가 들어옴")
            if why:
                picks.append((y, sg, sj, why))
        picks = picks[:max_years]
        if not picks:
            return "앞으로 10년 안에 이성 인연의 별이 들어오거나 배우자 자리와 합이 되는 해는 사실문에 없음"
        out = []
        for y, sg, sj, why in picks:
            months = []
            for tm in range(1, 13):
                if today is not None and today.year == y and tm < today.month:
                    continue
                try:
                    term_day, _ = _get_term_day(y, tm)
                    _, m_p, _ = get_true_year_month_pillar(y, tm, term_day + 3, 12, 0)
                    w_gan, w_ji = _to_hanja(m_p[0]), _to_hanja(m_p[1])
                    mw = []
                    if get_ss(ds, w_gan) in star:
                        mw.append(f"월 앞부분에 이성 인연의 별({get_ss(ds, w_gan)})")
                    if get_ss(ds, w_ji) in star:
                        mw.append(f"월 뒷부분에 이성 인연의 별({get_ss(ds, w_ji)})")
                    if hap and w_ji == hap:
                        mw.append(f"월 뒷부분에 배우자 자리({ilji})와 합")
                    if mw:
                        months.append(f"{tm}월 {w_gan}{w_ji}월({', '.join(mw)})")
                except Exception:
                    continue
            mtxt = " / ".join(months) if months else "이 해에는 따로 짚을 달 없음"
            out.append(f"{y}년 {sg}{sj}년: {' + '.join(why)} | 인연의 기운이 움직이는 달: {mtxt}")
        return "[인연 후보 해와 월운] " + " // ".join(out)
    except Exception:
        return "인연 후보 해 정보 없음"

_WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

def get_period_day_facts(start_date, days, ds, db, ys, yb, jjis, cheon_eul_str, yong=None, today=None, gans=None, keep_past=False):
    """날짜별 일진이 원국과 맺는 충·합·삼형·공망·천을귀인과 용신 오행을 따져
    '기운이 도와주는 날'과 '서두르지 말 날'로 나눕니다. jjis는 [시지, 일지, 월지, 년지] 순서."""
    yong = yong or {}
    if today is not None and today > start_date + dt_mod.timedelta(days=days - 1):
        return "[이미 지난 구간이라 날짜별 팩트를 생략함 — 이 구간은 지나온 흐름으로 과거형으로만 짧게 말하고 개별 날짜는 짚지 말 것]"
    h2k = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
    def oh_score(oh):
        if oh and oh in (yong.get("용신"), yong.get("희신"), yong.get("겸용")):
            return 1
        if oh and oh in (yong.get("기신"), yong.get("구신")):
            return -1
        return 0

    gm_day = calculate_gongmang(ds, db)      # 일 기준 공망
    gm_year = calculate_gongmang(ys, yb)     # 년 기준 공망
    guiin = [c for c in str(cheon_eul_str) if c in "子丑寅卯辰巳午未申酉戌亥"]
    good, bad, mild, calm = [], [], [], []
    _PROD = {"목": "수", "화": "목", "토": "화", "금": "토", "수": "금"}
    doc_el = _PROD.get(get_color(ds))
    doc_days = []
    grp_days = {"재성": [], "관성": [], "식상": [], "비겁": []}   # 인성은 doc_days 가 맡음
    cut = today if (today is not None and start_date <= today <= start_date + dt_mod.timedelta(days=days - 1)) else None
    for i in range(days):
        d = start_date + dt_mod.timedelta(days=i)
        if cut and d < cut and not keep_past:
            continue
        _, _wol, pil = get_ganji_from_date(d.year, d.month, d.day)
        gan, ji = _to_hanja(pil[0]), _to_hanja(pil[1])
        rel = get_unun_relation_facts(jjis, ji, "일운")
        sam = check_samhyung_facts(jjis, ilun_j=ji)
        score, notes, severe = 0, [], False
        if "와 충" in rel:
            _ch = re.findall(r"원국 (시지|일지|월지|년지)\(([^)]*)\)와 충", rel)
            score -= 2
            notes.append(("원국 " + "·".join(f"{n}({c})" for n, c in _ch) + "와 충") if _ch else "원국과 충")
            if re.search(r"(일지|월지)\([^)]*\)와 충", rel):
                severe = True                      # 일지·월지 충은 무겁게 본다
        if "와 형" in rel or "자묘형" in rel:
            score -= 2; notes.append("원국과 형")
            if re.search(r"(일지|월지)\([^)]*\)와 (?:자묘)?형", rel):
                severe = True                      # 일지·월지 형은 무겁게 본다
        for _kw, _sc in (("파", -1), ("해", -1)):
            _m = re.findall(r"원국 (시지|일지|월지|년지)\(([^)]*)\)와 " + _kw, rel)
            if _m: score += _sc; notes.append("원국 " + "·".join(f"{n}({c})" for n, c in _m) + "와 " + _kw)
            elif ("와 " + _kw) in rel: score += _sc; notes.append("원국과 " + _kw)
        _bs, _bn, _bsev = _bokeum_score(jjis, gans, gan, ji)
        score += _bs; notes.extend(_bn); severe = severe or _bsev
        if "일운(" in sam and "삼형 완성" in sam: score -= 3; notes.append("삼형 완성"); severe = True
        _wj = _to_hanja(_wol[1]) if len(str(_wol)) > 1 else ""
        _SUL = {"丑", "戌", "未"}
        _base = {_to_hanja(x) for x in jjis}
        if ji in _SUL and _SUL <= (_base | {_wj, ji}) and not (_SUL <= (_base | {_wj})):
            _tg = ["일지"] if _to_hanja(jjis[1]) in _SUL else [n for n, x in (("월지", jjis[2]), ("시지", jjis[0])) if _to_hanja(x) in _SUL]
            _gset = {_to_hanja(g) for g in (gans or [])}
            _pos = {"시지": 0, "일지": 1, "월지": 2, "년지": 3}
            _det = []
            for _n in (_tg if gans else []):
                _bj = _to_hanja(jjis[_pos[_n]])
                _jg = [g for g in JIJANGGAN.get(_bj, []) if g != "-"]
                _ent = [f"{g}({get_ss(ds, g)})" for g in _jg if g in _gset]
                _opn = [f"{g}({get_ss(ds, g)})" for g in _jg if g not in _gset]
                _part = []
                if _ent: _part.append("천간에 이미 드러난 " + "·".join(_ent) + "은 창고로 끌려 들어가는 입고")
                if _opn: _part.append("천간에 없던 " + "·".join(_opn) + "은 숨은 기운이 드러나는 개고")
                _det.append(f"{_n} {_bj} 창고: " + ", ".join(_part))
            score -= 3
            notes.append(f"월운({_wj})·일진({ji})이 모여 축술미 삼형 완성 — " + (" / ".join(_det) if _det else "원국 창고가 움직이는 날")); severe = True
        if ji in gm_day: score -= 2; notes.append("일 기준 공망"); severe = True
        elif ji in gm_year: score -= 1; notes.append("년 기준 공망")
        if "육합" in rel: score += 2; notes.append("원국과 육합")
        m = re.search(r"([木火土金水])국 삼합 완성", rel)
        if m:
            oh = h2k[m.group(1)]; score += oh_score(oh) * 2; notes.append(f"{oh}국 삼합 완성")
        else:
            m = re.search(r"([木火土金水])국 반합", rel)
            if m:
                oh = h2k[m.group(1)]; score += oh_score(oh); notes.append(f"{oh}국 반합")
        if ji in guiin: score += 2; notes.append("천을귀인")
        if gans:
            _gs, _gn, _gsev = _gan_rel_score(gans, gan, "일진 천간")
            if _gs > 0 and score < 0: _gs = 0   # 천간 합이 충·형·파의 감점을 덮어 주의일이 사라지지 않도록, 합 가산은 건너뜀
            score += _gs; notes.extend(_gn); severe = severe or _gsev
        e = oh_score(get_color(gan)) + oh_score(get_color(ji))
        if e > 0: score += e; notes.append("일진 오행이 이로움")
        elif e < 0: score += e; notes.append("일진 오행이 해로움")
        if doc_el and get_color(gan) == doc_el:
            _kind = "편인" if ((gan in "甲丙戊庚壬") == (ds in "甲丙戊庚壬")) else "정인"
            doc_days.append(f"{d.month}/{d.day}({_WEEKDAY_KR[d.weekday()]}) {gan}{ji}일 {gan}({_kind})" + (" — " + ", ".join(notes) if notes else " — 다른 충·합 특이사항 없음"))
        _grp = get_group_ss(get_ss(ds, gan))
        if _grp in grp_days:
            grp_days[_grp].append(f"{d.month}/{d.day}({_WEEKDAY_KR[d.weekday()]}) {gan}{ji}일 {gan}({get_ss(ds, gan)})" + (" — " + ", ".join(notes) if notes else " — 다른 충·합 특이사항 없음"))
        if not notes:
            calm.append(f"{d.month}/{d.day}({_WEEKDAY_KR[d.weekday()]}) {gan}{ji}일")
            continue
        tag = f"{d.month}/{d.day}({_WEEKDAY_KR[d.weekday()]}) {gan}{ji}일: " + ", ".join(notes)
        if severe or score <= -3:
            bad.append((score, i, tag))
        elif score >= 2:
            good.append((score, i, tag))
        elif score >= 1:
            mild.append((score, i, tag))
    good = sorted(sorted(good, key=lambda x: (-x[0], x[1]))[:5], key=lambda x: x[1])
    _bad_rank = sorted(bad, key=lambda x: (x[0], x[1]))      # 점수가 낮은(무거운) 날부터
    heavy = sorted(_bad_rank[:5], key=lambda x: x[1])         # 특히 조심할 날 최대 5일
    light = sorted(_bad_rank[5:], key=lambda x: x[1])         # 가볍게 살필 날(나머지)
    mild = mild[:4]
    calm = calm[:5]
    _grp_lines = "".join(
        f"\n[{k}({v}) 기운이 천간으로 들어오는 날] " + (" / ".join(grp_days[k]) if grp_days[k] else "없음")
        for k, v in (("재성", "재물·결실"), ("관성", "직장·책임"), ("식상", "표현·활동"), ("비겁", "동료·경쟁")))
    _today_line = (f"[오늘 기준일: {today.month}/{today.day}({_WEEKDAY_KR[today.weekday()]}) — 이 날짜보다 앞선 날만 이미 지난 날이고, 오늘과 그 이후의 날은 지금이거나 앞으로 올 날]\n" if today is not None else "")
    return (_today_line + "[기운이 도와주는 날] " + (" / ".join(t for _, _, t in good) if good else "뚜렷한 날 없음")
            + "\n[무난히 움직일 수 있는 날] " + (" / ".join(t for _, _, t in mild) if mild else "없음")
            + "\n[특별한 충돌 없이 무난한 날] " + (" / ".join(calm) if calm else "없음")
            + "\n[서두르지 말 날] " + (" / ".join(t for _, _, t in heavy) if heavy else "뚜렷한 날 없음")
            + "\n[그 밖에 가볍게 살필 날] " + (" / ".join(t for _, _, t in light) if light else "없음")
            + _grp_lines
            + "\n[문서 기운(인성) 글자가 천간으로 들어오는 날] " + (" / ".join(doc_days) if doc_days else "없음"))

def get_half_period_day_facts(period_str, ds, db, ys, yb, jjis, cheon_eul_str, yong=None, today=None, gans=None):
    """'2026년 10월 23일 ~ 2026년 11월 06일' 같은 문장에서 시작일·끝일을 읽어,
    그 기간의 날짜별 충·삼형·공망·합 팩트를 만듭니다. (월운 상반기/후반기용)"""
    found = re.findall(r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일', str(period_str))
    if len(found) < 2:
        return "[날짜 범위를 확인할 수 없음]"
    try:
        s = dt_mod.date(*map(int, found[0]))
        e = dt_mod.date(*map(int, found[1]))
    except ValueError:
        return "[날짜 범위를 확인할 수 없음]"
    days = (e - s).days + 1
    if days < 1 or days > 40:
        return "[날짜 범위를 확인할 수 없음]"
    return get_period_day_facts(s, days, ds, db, ys, yb, jjis, cheon_eul_str, yong=yong, today=today, gans=gans)

def get_wolun_month_day_facts(first_half, second_half, ds, db, ys, yb, jjis, cheon_eul_str, yong=None, today=None, gans=None):
    """월운 상반기·후반기 문장에서 절입일(시작)과 다음 절입 전날(끝)을 읽어,
    절기 기준 한 달 전체의 날짜별 팩트를 만듭니다. (달력 날짜가 아니라 절기월 기준)"""
    f1 = re.findall(r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일', str(first_half))
    f2 = re.findall(r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일', str(second_half))
    if not f1 or not f2:
        return "[날짜 범위를 확인할 수 없음]"
    try:
        s = dt_mod.date(*map(int, f1[0]))
        e = dt_mod.date(*map(int, f2[-1]))
    except ValueError:
        return "[날짜 범위를 확인할 수 없음]"
    days = (e - s).days + 1
    if days < 1 or days > 40:
        return "[날짜 범위를 확인할 수 없음]"
    return get_period_day_facts(s, days, ds, db, ys, yb, jjis, cheon_eul_str, yong=yong, today=today, gans=gans)

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
                    results.append(f"🚨 [입고(入庫) 주의] {ji} 무덤이 열려 천간의 {','.join(trapped_chars)} 기운이 수렴됩니다.")
                else:
                    results.append(f"💎 [개고(開庫) 발현] {ji} 금고가 열려 지장간의 숨은 보물이 세상에 드러납니다.")
    return results

# ==============================================================================
# 🆕 [책 4. 기타 간명법] 병약신(病藥神) · 상관견관(傷官見官) 팩트 (ver 88.7)
#   - 위치: check_vault_status 함수 바로 아래
#   - gans, jjis 순서는 엔진 공통: [시, 일, 월, 년]
#   - haeng_list: 행운(대운·세운 등) [(이름, 천간, 지지), ...]  없으면 원국만 봄
# ==============================================================================
_BYEONGYAK_TABLE = [
    # (오행, 국세 묶음들, 병 오행, 극을 받는 천간, 약신 천간, 약신 오행)
    ("목", [{'亥', '卯', '未'}, {'寅', '卯', '辰'}], "토", ['戊', '己'], '庚', "금"),
    ("화", [{'寅', '午', '戌'}, {'巳', '午', '未'}], "금", ['庚', '辛'], '壬', "수"),
    ("토", [{'辰', '戌', '丑', '未'}],               "수", ['壬', '癸'], '甲', "목"),
    ("금", [{'巳', '酉', '丑'}, {'申', '酉', '戌'}], "목", ['甲', '乙'], '丁', "화"),
    ("수", [{'申', '子', '辰'}, {'亥', '子', '丑'}], "화", ['丙', '丁'], '戊', "토"),
]
_PALACE4 = ["시주", "일주", "월주", "년주"]
_PALACE_MEAN = {"시주": "말년·자녀", "일주": "본인·배우자", "월주": "부모·직장·사회", "년주": "조상·어린 시절"}
 
def get_byeongyaksin_facts(gans, jjis, ds, haeng_list=None):
    """책 '병약신': 지지에 국세(합국)가 이루어지면 그 오행이 천간의 극제천간을 친다(병).
    병을 풀어 주는 약신이 천간·지장간·행운에 있으면 흉이 줄고, 없으면 병중무구."""
    try:
        gs = [_to_hanja(g) for g in gans]
        js = [_to_hanja(j) for j in jjis]
        ds = _to_hanja(ds)
        base_js = {j for j in js if j not in ("?", "-", " ")}
        base_gs = [g for g in gs if g not in ("?", "-", " ")]
        haeng_list = haeng_list or []
        lines = []
        for (oh, sets, byung_oh, gje, yak, yak_oh) in _BYEONGYAK_TABLE:
            for st in sets:
                nm = "·".join(sorted(st, key=lambda x: JI.index(x)))
                if st <= base_js:
                    when = "원국"
                    add_g, add_j = [], []
                else:
                    when = None
                    for (hn, hg, hj) in haeng_list:
                        hj = _to_hanja(hj); hg = _to_hanja(hg)
                        if st <= (base_js | {hj}) and hj in st:
                            when = hn; add_g, add_j = [hg], [hj]; break
                    if when is None:
                        continue
                # 극을 받는 천간 (일간은 체신이라 대상에서 제외: 시·월·년 천간만)
                hit = []
                for i in (0, 2, 3):
                    g = gs[i]
                    if g in gje:
                        hit.append(f"{_PALACE4[i]} {g}({get_ss(ds, g)}, {_PALACE_MEAN[_PALACE4[i]]})")
                head = f"[{when} {oh}({nm}) 국세]"
                if not hit:
                    continue   # 극을 받는 천간이 없으면 병이 아니므로 글감에 넣지 않음
                # 약신 찾기: 원국 천간(일간 포함) + 원국 지장간 + 행운 간지
                where = []
                for i, g in enumerate(gs):
                    if g == yak: where.append(f"{_PALACE4[i]} 천간")
                for i, j in enumerate(js):
                    if j in JIJANGGAN and yak in JIJANGGAN[j]: where.append(f"{_PALACE4[i]} 지장간")
                for hg in add_g:
                    if hg == yak: where.append(f"{when} 천간")
                for hj in add_j:
                    if hj in JIJANGGAN and yak in JIJANGGAN[hj]: where.append(f"{when} 지장간")
                for (hn, hg, hj) in haeng_list:
                    if hn != when and (_to_hanja(hg) == yak or yak in JIJANGGAN.get(_to_hanja(hj), [])):
                        where.append(f"{hn}")
                where = list(dict.fromkeys(where))
                if where:
                    lines.append(f"{head} {oh} 기운이 {byung_oh} 기운을 치는 병: " + ", ".join(hit)
                                 + f" / 약신 {yak}({yak_oh})이 {', '.join(where)}에 있어 흉화를 면하거나 크게 줄어듦")
                else:
                    lines.append(f"{head} {oh} 기운이 {byung_oh} 기운을 치는 병: " + ", ".join(hit)
                                 + f" / 약신 {yak}({yak_oh})이 원국·행운 어디에도 없어 병중무구(병은 있는데 풀어 줄 약이 없음) — 해당 십성과 육친, 그리고 {byung_oh}에 해당하는 몸의 기운을 조심할 것")
        return "\n".join(lines) if lines else "병약신 해당 없음(지지에 완성된 국세가 없음)"
    except Exception as e:
        return "병약신 해당 없음"
 
# 상관견관: 지지 본기는 책 도표 기준(부음포양: 子壬 亥癸 午丙 巳丁)
_BONGI_BOOK = {'子':'壬','丑':'己','寅':'甲','卯':'乙','辰':'戊','巳':'丁','午':'丙','未':'己','申':'庚','酉':'辛','戌':'戊','亥':'癸'}
 
def is_sanggwan_gyeongwan_pillar(ds, g, j):
    """간지 한 기둥이 상관견관인가: 천간과 지지 본기가 (상관, 정관) 한 쌍을 이룸 (책 도표 24개)"""
    ds, g, j = _to_hanja(ds), _to_hanja(g), _to_hanja(j)
    if g in ("?", "-", " ") or j not in _BONGI_BOOK: return False
    return {get_ss(ds, g), get_ss(ds, _BONGI_BOOK[j])} == {"상관", "정관"}
 
def get_sanggwan_gyeongwan_facts(gans, jjis, ds, gender, haeng_list=None):
    """책 '상관견관': 상관이 정관을 극하는 구조. 천간·지지 한 기둥이 도표에 해당하면 구조 성립,
    지지 지장간 속에 상관과 정관이 함께 있으면 '형태'. 행운 간지도 같은 방식으로 봄."""
    try:
        gs = [_to_hanja(g) for g in gans]
        js = [_to_hanja(j) for j in jjis]
        ds = _to_hanja(ds)
        lines = []
        for i in range(4):
            g, j = gs[i], js[i]
            if g in ("?", "-", " ") or j in ("?", "-", " "): continue
            if is_sanggwan_gyeongwan_pillar(ds, g, j):
                lines.append(f"[원국 상관견관 성립] {_PALACE4[i]} {g}{j}: 천간 {g}({get_ss(ds, g)})과 지지 {j}의 기운 {_BONGI_BOOK[j]}({get_ss(ds, _BONGI_BOOK[j])})이 한 기둥에서 만남 — {_PALACE_MEAN[_PALACE4[i]]} 자리")
            else:
                jg = [x for x in JIJANGGAN.get(j, []) if x != "-"]
                sg = [x for x in jg if get_ss(ds, x) == "상관"]
                gw = [x for x in jg if get_ss(ds, x) == "정관"]
                if sg and gw:
                    lines.append(f"[원국 상관견관 형태] {_PALACE4[i]} {j}의 지장간 속에 상관({sg[0]})과 정관({gw[0]})이 함께 들어 있음 — {_PALACE_MEAN[_PALACE4[i]]} 자리(속으로 품은 형태라 구조 성립보다 약함)")
        for (hn, hg, hj) in (haeng_list or []):
            if is_sanggwan_gyeongwan_pillar(ds, hg, hj):
                lines.append(f"[{hn} 상관견관] {hn} 간지 {_to_hanja(hg)}{_to_hanja(hj)}가 상관견관 기둥 — 그 시기에 구조가 건드려짐")
        if not lines:
            return "상관견관 해당 없음"
        # 관살태과면 상관이 오히려 병을 제거 (책: 관살태과에는 상관이 제거기병)
        gw_cnt = sum(1 for k in range(4) if k != 1 and gs[k] not in ("?", "-", " ") and get_ss(ds, gs[k]) in ("정관", "편관"))
        gw_cnt += sum(1 for j in js if j in _BONGI_BOOK and get_ss(ds, _BONGI_BOOK[j]) in ("정관", "편관"))
        if gw_cnt >= 4:
            lines.append("※ 관성(정관·편관)이 매우 많은 사주라 상관이 오히려 관성의 지나친 압박을 덜어 주는 역할도 함 — 흉하다고만 단정하지 말 것")
        if gender == "여성":
            lines.append("※ 여명의 상관견관 풀이 방향: 배우자 인연이 흔들리거나 혼인·자녀 인연의 시기가 어긋나기 쉬우므로 서로 존중하는 대화로 보완")
        else:
            lines.append("※ 남명의 상관견관 풀이 방향: 직장·직업을 옮기거나 일의 자리가 자주 바뀌기 쉬우므로 한 분야를 오래 다지는 것이 보완")
        return "\n".join(lines)
    except Exception:
        return "상관견관 해당 없음"

# ==============================================================================
# 🆕 [책 4-1) 개고설] 합반(合絆) 경고 (ver 88.8)
#   - 위치: get_sanggwan_gyeongwan_facts 함수 바로 아래 (또는 get_hang_un_vaults_str 위)
#   - 창고(辰戌丑未)가 충·형으로 열릴 때, 창고 속 글자가 천간(일간 포함)과 천간합으로 묶여 있으면 경고
#   - gans, jjis 순서: [시, 일, 월, 년]  /  haeng_list: [(이름, 천간, 지지), ...]
# ==============================================================================
_CHEONGAN_HAP = {'甲': '己', '己': '甲', '乙': '庚', '庚': '乙', '丙': '辛', '辛': '丙', '丁': '壬', '壬': '丁', '戊': '癸', '癸': '戊'}
_VAULT_CLASH = {'辰': '戌', '戌': '辰', '丑': '未', '未': '丑'}
_VAULT_HYUNG = {'丑', '戌', '未'}
_GAN_PALACE = ["시간", "일간", "월간", "년간"]
 
def _vault_opens(vj, oj):
    """창고 글자 vj 가 지지 oj 와 충 또는 형으로 부딪치는가 → '충' / '형' / ''"""
    if _VAULT_CLASH.get(vj) == oj: return "충"
    if vj in _VAULT_HYUNG and oj in _VAULT_HYUNG and oj != vj: return "형"
    return ""
 
def _yukchin_of(gender, ss):
    if ss in ("비견", "겁재"): return "형제·동료"
    if ss in ("정인", "편인"): return "어머니·학업"
    if ss in ("식신", "상관"): return "자녀·표현" if gender == "여성" else "표현·장모"
    if ss in ("정재", "편재"): return "아버지·재물" if gender == "여성" else "아내·재물"
    if ss in ("정관", "편관"): return "남편·직장" if gender == "여성" else "자녀·직장"
    return "해당 육친"
 
def get_hapban_warning_facts(gans, jjis, ds, gender, haeng_list=None):
    """창고가 열릴 때(충·형) 창고 속 글자가 천간과 합으로 묶여 있으면(합반) 육친·처신 경고 팩트를 만듭니다."""
    try:
        gs = [_to_hanja(g) for g in gans]
        js = [_to_hanja_ji(j) for j in jjis]
        ds = _to_hanja(ds)
        PAL = ["시주", "일주", "월주", "년주"]
        lines = []
 
        found = []   # (tag, 부딪힌 설명, 창고 글자, 십성, 천간 글자, 천간 자리, 창고 이름)
 
        def _pair_lines(tag, vault_label, vj, how_text):
            for x in [c for c in JIJANGGAN.get(vj, []) if c != "-"]:
                partner = _CHEONGAN_HAP.get(x)
                for p in range(4):
                    if gs[p] not in ("?", "-", " ") and gs[p] == partner:
                        found.append((tag, how_text, x, get_ss(ds, x), partner, "일간" if p == 1 else _GAN_PALACE[p], vault_label))
 
        # ① 원국 안에서 이미 열려 있는 창고
        for i, vj in enumerate(js):
            if vj not in _VAULT_CLASH: continue
            for k, oj in enumerate(js):
                if k == i or oj in ("?", "-", " ", ""): continue
                how = _vault_opens(vj, oj)
                if how:
                    _pair_lines("원국", f"{PAL[i]}", vj, f"{PAL[k]} {oj}({how})에 부딪혀")
                    break
        # ② 행운(대운·세운)이 원국 창고를 열 때 / 행운 자신이 창고일 때 원국 지지가 열 때
        for (hn, hg, hj) in (haeng_list or []):
            hj = _to_hanja_ji(hj)
            for i, vj in enumerate(js):
                if vj in _VAULT_CLASH:
                    how = _vault_opens(vj, hj)
                    if how:
                        _pair_lines(hn, f"원국 {PAL[i]}", vj, f"{hn} {hj}({how})에 부딪혀")
            if hj in _VAULT_CLASH:
                for k, oj in enumerate(js):
                    how = _vault_opens(hj, oj) if oj not in ("?", "-", " ", "") else ""
                    if how:
                        _pair_lines(hn, f"{hn}", hj, f"원국 {PAL[k]} {oj}({how})에 부딪혀")
                        break
        # 같은 내용은 한 줄로 합치기 (같은 부딪힘·같은 창고 속 글자·같은 천간 글자)
        merged = {}
        for (tag, how_text, x, ss, partner, who, vlabel) in found:
            key = (tag, how_text, x, ss, partner)
            d = merged.setdefault(key, {"vl": [], "who": []})
            if vlabel not in d["vl"]: d["vl"].append(vlabel)
            if who not in d["who"]: d["who"].append(who)
        for (tag, how_text, x, ss, partner), d in merged.items():
            lines.append(f"[합반 경고·{tag}] {'·'.join(d['vl'])} 창고가 {how_text} 열리는데, 창고 속 {x}({ss})이 {'·'.join(d['who'])} {partner}과 합으로 묶여 있음 — {_yukchin_of(gender, ss)} 쪽 인연이 흔들리거나 처신에 어려움이 생기기 쉬움")
        lines = list(dict.fromkeys(lines))
        return "\n".join(lines) if lines else "합반 경고 해당 없음"
    except Exception:
        return "합반 경고 해당 없음"

# ==============================================================================
# 🆕 [책 4-3) 상관의 작용] 상관상진 · 파료상관 팩트 (ver 88.8)
#   - 위치: get_hapban_warning_facts 함수 바로 아래
#   - 신강·신약은 엔진의 _judge_strength 를 그대로 사용 (중화는 판단하지 않음)
#   - 십성은 원국 천간 3개(시·월·년, 일간 제외) + 지지 본기 4개(책 도표 기준)로 센다
#   - gans, jjis 순서: [시, 일, 월, 년] / haeng_list: [(이름, 천간, 지지), ...]
# ==============================================================================
def _ten_god_slots(ds, gs, js):
    slots = []
    for i in (0, 2, 3):
        if gs[i] not in ("?", "-", " ", ""):
            slots.append(get_ss(ds, gs[i]))
    for j in js:
        if j in _BONGI_BOOK:
            slots.append(get_ss(ds, _BONGI_BOOK[j]))
    return slots
 
def _haeng_ten_gods(ds, hg, hj):
    out = []
    hg, hj = _to_hanja(hg), _to_hanja_ji(hj)
    if hg and hg not in ("?", "-", " "):
        out.append(get_ss(ds, hg))
    if hj in _BONGI_BOOK:
        out.append(get_ss(ds, _BONGI_BOOK[hj]))
    return out
 
def get_sangjin_paryo_facts(gans, jjis, ds, gender, haeng_list=None):
    """상관상진(신약 + 상관 많음 + 관성 없음) / 파료상관(신강 + 상관 있음 + 인성이 눌러 막음) 팩트"""
    try:
        gs = [_to_hanja(g) for g in gans]
        js = [_to_hanja_ji(j) for j in jjis]
        ds = _to_hanja(ds)
        counts = {'목': 0, '화': 0, '토': 0, '금': 0, '수': 0}
        for c in gs + js:
            oh = get_color(c)
            if oh in counts: counts[oh] += 1
        mb, db = js[2], js[1]
        strength = _judge_strength(counts, mb, ds, db)[0]
        if strength == "중화":
            return "상관상진·파료상관 해당 없음(일간의 강약이 팽팽해 판단하지 않음)"
        slots = _ten_god_slots(ds, gs, js)
        sang = slots.count("상관")
        siksang = sang + slots.count("식신")
        gwan = slots.count("정관") + slots.count("편관")
        inseong = slots.count("정인") + slots.count("편인")
        haeng = list(haeng_list or [])
        lines = []
 
        # ① 상관상진: 신약 + 상관 많음 + 관성 없음
        if strength == "신약" and sang >= 1 and siksang >= 2 and gwan == 0:
            lines.append(f"[상관상진 구조] 일간이 약한데 상관·식상이 많고(상관 {sang}개·식상 합 {siksang}개) 겉으로 드러난 관성(천간·지지 본기)이 하나도 없음 — 상관의 기운을 눌러 주는 인성·비겁 운에 크게 풀리는 구조")
            for (hn, hg, hj) in haeng:
                tg = _haeng_ten_gods(ds, hg, hj)
                if any(t in ("정관", "편관") for t in tg):
                    lines.append(f"[상관상진 {hn}] {hn}에 관성이 들어와 정돈된 구조가 흔들리기 쉬운 시기(관성 운을 만나면 길한 구조가 흉으로 바뀌기 쉬움)")
                elif any(t in ("정인", "편인", "비견", "겁재") for t in tg):
                    lines.append(f"[상관상진 {hn}] {hn}이 인성·비겁 운이라 상관의 기운이 정리되고 힘이 붙는 시기")
                elif any(t in ("식신", "상관") for t in tg):
                    lines.append(f"[상관상진 {hn}] {hn}이 식상 운이라 약한 일간의 기운이 더 빠지기 쉬운 시기")
 
        # ② 파료상관: 신강 + 상관 있음 + 인성이 상관을 눌러 막음
        if strength == "신강" and sang >= 1:
            if inseong >= 3:
                lines.append(f"[파료상관 구조] 일간이 강해 상관(재능·표현)을 써야 하는데 인성이 {inseong}개로 많아 상관의 길이 눌려 막히기 쉬운 구조")
            for (hn, hg, hj) in haeng:
                tg = _haeng_ten_gods(ds, hg, hj)
                if any(t in ("정인", "편인") for t in tg):
                    lines.append(f"[파료상관 {hn}] {hn}이 인성 운이라 상관의 길이 눌려 재능과 표현이 막히기 쉬운 시기")
 
        return "\n".join(lines) if lines else "상관상진·파료상관 해당 없음"
    except Exception:
        return "상관상진·파료상관 해당 없음"
 
def get_hang_un_vaults_str(dw_j, base_gans, base_jjis):
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
    jjis_clean = [_to_hanja(j) for j in jjis if j not in ["?", "-", " "]]
    vaults = [j for j in jjis_clean if j in ['辰', '戌', '丑', '未']]
    if not vaults:
        return "원국 내 진술축미(묘고) 글자 없음 (특수 입고 작용 미미함)"
    return f"원국 내 묘고 글자 보유: {', '.join(vaults)} (강력한 입고 및 개고 잠재력 내재)"


# ---- 2-E. [1-1] 종합 · 좌법/인종법 · 일주 마스터 DB 연동 ----

def get_universal_analysis(ds, mb, db, gans, jjis):
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
        results.append(f"[겉성격/좌법] 일지 {db_h} {ilji_palace}(宮) 환경 무대: 지장간 속 {qi}({ss})는 {qi_unsung}좌(坐)하여, 사회적 표상에서 {ss}의 기운이 {qi_unsung}의 주도적 파동으로 강렬하게 발현됨")
 
    all_gans = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    present_chars = [_to_hanja(c) for c in gans + jjis if _to_hanja(c) in all_gans]
    missing_gans = [g for g in all_gans if g not in present_chars]
 
    for m in missing_gans:
        ss = get_ss(ds_h, m)
        m_unsung = get_unsung(m, db_h)
        results.append(f"[속마음/인종법] 일지 {db_h} {ilji_palace}(宮) 속 무의식: 원국에 숨겨진 {m}({ss})를 인종하면 {m_unsung}종(從)에 해당하여, 내면 깊은 곳에 {ss}에 대한 {m_unsung}적 정신적/현실적 결핍과 갈망이 작용함")
    return results

def get_ilju_master_prompt_context(user_ilju_key, choyeon_db, gender=None):
    ilju_full_db = choyeon_db.get("ilju_full_master", {})
    ilju_master_data = ilju_full_db.get(user_ilju_key, {})
 
    if not ilju_master_data:
        return ""
 
    # 🚨 "family" 필드에 남명/여명 설명이 한 문장에 섞여 있는 경우, 신청자 성별에 맞는 부분만 추출
    family_raw = ilju_master_data.get('family', '')
    family_filtered = family_raw
    if gender and "남명" in family_raw and "여명" in family_raw:
        m_match = re.search(r'남명\s*[:：]\s*(.*?)(?=여명\s*[:：]|$)', family_raw)
        f_match = re.search(r'여명\s*[:：]\s*(.*)$', family_raw)
        m_part = m_match.group(1).strip() if m_match else ""
        f_part = f_match.group(1).strip() if f_match else ""
        if gender == "남성" and m_part:
            family_filtered = f"남명: {m_part}"
        elif gender == "여성" and f_part:
            family_filtered = f"여명: {f_part}"
 
    return f"""
🎯 [초연 시공명리의 뼈때리는 팩트폭격 - {user_ilju_key}일주 전용 마스터 비기]
- 물상 및 성향 요약: {ilju_master_data.get('summary', '')}
- 심리적 관점: {ilju_master_data.get('psychology', '')}
- 육친적 관점: {family_filtered}
- 사회적 관점: {ilju_master_data.get('society', '')}
- 지장간 좌법(座法) 분석: {ilju_master_data.get('jijanggan_zaBeob', '')}
- 인종법(引從法) 숨겨진 내면: {ilju_master_data.get('injong_beob', '')}
- 신살, 변곡점, 건강, 과숙/고신, 도망역: {ilju_master_data.get('shinsal_warnings', '')}
- 💥 뼈때리는 팩트폭격 핵심 비기: {ilju_master_data.get('choyeon_secret', '')}
 
🚨 [통변 절대 규칙]: 위 박사님의 '초연 시공명리의 뼈때리는 팩트폭격'에 담긴 통찰을 사주풀이 에세이에 녹여내어 깊이 있게 풀이하십시오. 
단, 지장간 좌법·인종법 용어(예: 왕좌왕궁, 록좌왕궁, 대좌대궁처럼 '○좌○궁'으로 쓴 표기)는 해설용 자료이므로 본문에 그대로 쓰지 말고 일상어로 풀어 쓰며, 지장간 속 글자를 세운·월운·일운의 천간과 혼동하지 마십시오. 
'패가망신', '폭군', '초토화'처럼 불안이나 거부감을 주는 센 표현은 신청자의 연령과 상황에 맞게 순화하십시오.
"""


# ---- 2-F. 시공명리 특수 파동 진단 (삼자조합 · 시공간 왜곡 · 우주중력 · 재물/연애 패턴 공통 재료) ----

def analyze_saju_facts_advanced(saju_data, current_dw, current_sewun):
    is_bokgeum = ((saju_data.get('day_ji') == saju_data.get('hour_ji')) or (saju_data.get('year_ji') == saju_data.get('month_ji')))
 
    vaults = ['辰', '戌', '丑', '未']
    has_vault = any(v in [saju_data.get('year_ji'), saju_data.get('month_ji'), saju_data.get('day_ji'), saju_data.get('hour_ji')] for v in vaults)
 
    advanced_flags = {
        "bokgeum_active": is_bokgeum,
        "vault_active": has_vault,
        "warning_message": "⚠️ [시공간 경고]: 복음 및 묘고 합화 파동에 따른 에너지 고갈 또는 신체 임계점 주의" if (is_bokgeum and has_vault) else "정상 시공간 흐름"
    }
 
    return None, None, advanced_flags

def analyze_spacetime_distortion_and_fukim(bazi_dict):
    branches = [bazi_dict.get('year_j'), bazi_dict.get('month_j'), bazi_dict.get('day_j'), bazi_dict.get('time_j')]
 
    results = {"distortion_score": 0, "fact_summary_text": []}
 
    wonjin_map = [('辰', '亥'), ('巳', '戌'), ('寅', '未'), ('子', '未'), ('丑', '午'), ('卯', '申')]
    for b1, b2 in wonjin_map:
        if (b1 in branches) and (b2 in branches):
            results["fact_summary_text"].append(f"[{b1}·{b2} 원진귀문 감지]: 시공간 파동의 꼬임 및 감정 정체.")
 
    results["summary_output"] = "\n".join(results["fact_summary_text"]) if results["fact_summary_text"] else "정순한 흐름."
    return results

def analyze_jijanggan_spacetime_dynamics(bazi_dict):
    branches = [bazi_dict.get('year_j'), bazi_dict.get('month_j'), bazi_dict.get('day_j'), bazi_dict.get('time_j')]
    results = {"fact_summary_text": []}
 
    if ('子' in branches) and ('丑' in branches):
        results["fact_summary_text"].append("[子·丑 탕화 파동 감지]: 가스/화재 사고 및 답답한 심리적 압박 주의.")
    if ('卯' in branches) and ('戌' in branches):
        results["fact_summary_text"].append("[卯·戌 합 파동 감지]: 아궁이 물상 및 희생/유흥 관련 파동.")
    if ('辰' in branches) and ('酉' in branches):
        results["fact_summary_text"].append("[辰·酉 합 파동 감지]: 자산 뻥튀기 대발 및 관재구설 주의.")
    if ('巳' in branches) and ('申' in branches):
        results["fact_summary_text"].append("[巳·申 합형 파동 감지]: 기계, 촬영 장비 물상 및 교통사고 리스크.")
 
    results["summary_output"] = "\n".join(results["fact_summary_text"]) if results["fact_summary_text"] else "특이 지장간 파동 없음."
    return results

def analyze_cosmic_gravity_and_samhyeong_patterns(bazi_dict):
    stems = [bazi_dict.get('year_g'), bazi_dict.get('month_g'), bazi_dict.get('day_g'), bazi_dict.get('time_g')]
    branches = [bazi_dict.get('year_j'), bazi_dict.get('month_j'), bazi_dict.get('day_j'), bazi_dict.get('time_j')]
 
    results = {"fact_summary_text": []}
    has_ding = ('丁' in stems) or ('午' in branches) or ('未' in branches)
    has_gui = ('癸' in stems) or ('子' in branches)
 
    if has_ding and has_gui:
        results["fact_summary_text"].append("[丁·癸 중력/척력 조절 파동 감지]: 고도의 이성적 조율 능력 및 사법/기획적 적성.")
 
    earth_count = sum(1 for b in branches if b in ['辰', '戌', '丑', '未'])
    if earth_count >= 2:
        results["fact_summary_text"].append(f"[토(土) 영역 확장 파동]: 부동산/토지 집착 및 영역 확장 욕구.")
 
    samhyeong_set = {'寅', '巳', '申'}
    if len(samhyeong_set.intersection(set(branches))) >= 2:
        results["fact_summary_text"].append("[寅巳申 형/충 파동 감지]: 수술, 교통사고, 관재구설 리스크 주의.")
 
    results["summary_output"] = "\n".join(results["fact_summary_text"]) if results["fact_summary_text"] else "시공간 특이 파동 없음."
    return results


# ==============================================================================
# PART 3. [2-x 테마별 상담] 2-1 재물 · 2-2 연애 · 2-3 진학 · 2-4 직업 · 2-5 건강 · 2-6 이사 · 2-7 개업
# ==============================================================================

# ---- 3-A. [2-1 재물운] ----

def get_jaeda_sinyak_fact(counts, mb, ds, db=None):
    """재물 감당력 사실문: 신강·신약 + 재성 개수 → 재다신약/신약재약/신강재약/신강재왕 등 유형과 비겁탈재 여부."""
    dm = get_color(ds)
    if not dm or dm not in _OHAENG_CYCLE:
        return "일간 오행을 알 수 없어 재물 감당력 판정을 생략합니다."
    strength, raw_support, raw_drain, support, drain, _n1, _n2 = _judge_strength(counts, mb, ds, db)
    jae = _oh_controls(dm)
    jae_cnt = counts.get(jae, 0)
    bigeop = max(0, counts.get(dm, 0) - 1)
    inseong = counts.get(_oh_prev(dm), 0)
    siksang = counts.get(_oh_next(dm), 0)
    if jae_cnt >= 3:
        jae_lv = "많음"
    elif jae_cnt == 2:
        jae_lv = "보통"
    else:
        jae_lv = "약함"
    if jae_cnt == 0:
        kind = f"재성 없음({strength}) - 재물을 직접 쥐는 기운이 원국에 없어 활동·관계로 재물을 만드는 구조"
    elif jae_lv == "많음" and strength == "신약":
        kind = "재다신약 - 재물 기운은 많으나 일간의 힘이 모자라 감당하기 벅찬 구조(무리한 확장 주의, 인성·비겁 보강이 도움)"
    elif jae_lv == "많음" and strength == "신강":
        kind = "신강재왕 - 재물 기운도 많고 일간도 힘이 있어 재물을 감당할 수 있는 구조"
    elif jae_lv == "많음":
        kind = "재성 많음, 중화 - 재물 기운과 일간의 힘이 팽팽한 구조"
    elif strength == "신강":
        kind = "신강재약 - 일간의 힘은 충분하나 재물 기운이 약해, 식상(재능·활동)으로 재물을 만들어야 하는 구조"
    elif strength == "신약":
        kind = "신약재약 - 재물 기운도 약하고 일간의 힘도 모자라, 무리한 확장보다 힘을 채우며 지키는 쪽이 맞는 구조"
    else:
        kind = "재성 약함, 중화 - 재물 기운은 약하나 일간의 힘은 균형을 이룬 구조"
    notes = []
    if bigeop > jae_cnt:
        notes.append(f"비겁({bigeop}개)이 재성({jae_cnt}개)보다 많아 재물을 나누거나 새기 쉬운 구조(비겁탈재 경향)")
    if siksang >= 1 and jae_cnt >= 1:
        notes.append("식상이 있어 버는 재능이 재물로 이어지는 길이 있음")
    return (f"[재물 감당력] 일간({ds}, {dm}) {strength}(지원 {support} vs 소모 {drain}), "
            f"재성({jae}) {jae_cnt}개({jae_lv}), 비겁 {bigeop}개, 인성 {inseong}개, 식상 {siksang}개 → 유형: {kind}"
            + (" / " + " / ".join(notes) if notes else ""))

def get_jaeseong_status_fact_str(ds_hanja, gans, jjis, yb, year_gongmang_sipseong, day_gongmang_sipseong, curr_samjae):
    """재물운 종합 팩트: 재성(정재·편재)의 궁위, 십이운성, 십이신살, 공망, 삼재 여부를 한 번에 산출."""
    palace_names = {0: "시주", 1: "일주", 2: "월주", 3: "년주"}
    parts = []
    for idx in range(4):
        g, j = gans[idx], jjis[idx]
        for label, char in [("천간", g), ("지지", j)]:
            ss = get_ss(ds_hanja, char)
            if ss in ("정재", "편재"):
                unsung = get_unsung(ds_hanja, j)
                shinsal = get_12_shinsal(yb, j)
                parts.append(f"{palace_names[idx]}({label} {char}, {ss}): 십이운성={unsung}, 십이신살={shinsal}")

    result = " / ".join(parts) if parts else "원국에 재성(정재·편재) 없음"

    gongmang_notes = []
    if year_gongmang_sipseong in ("정재", "편재"):
        gongmang_notes.append("년지공망이 재성 공망")
    if day_gongmang_sipseong in ("정재", "편재"):
        gongmang_notes.append("일지공망이 재성 공망")
    if gongmang_notes:
        result += " / " + ", ".join(gongmang_notes)

    result += f" / 삼재 여부: {curr_samjae}"
    return result

def get_vault_timing_fact_str(ds, jjis, gans, curr_year, dw_j, sewun_j, wolun_j, gender="남성"):
    """창고(辰戌丑未) 개고·입고 사실문 — 안태옥 박사 이론(일지 기준, 삼형은 연지 제외).
    jjis=[년지,월지,일지,시지], gans=[년간,월간,일간,시간]"""
    # 한글로 넘어와도 한자로 맞춤 (천간과 지지는 한글 '신'이 겹치므로 따로 변환)
    _G = {'갑': '甲', '을': '乙', '병': '丙', '정': '丁', '무': '戊',
          '기': '己', '경': '庚', '신': '辛', '임': '壬', '계': '癸'}
    _J = {'자': '子', '축': '丑', '인': '寅', '묘': '卯', '진': '辰', '사': '巳',
          '오': '午', '미': '未', '신': '申', '유': '酉', '술': '戌', '해': '亥'}
    _g = lambda x: _G.get(x, x)
    _j = lambda x: _J.get(x, x)
    ds = _g(ds)
    gans = [_g(x) for x in gans]
    jjis = [_j(x) for x in jjis]
    dw_j, sewun_j, wolun_j = _j(dw_j), _j(sewun_j), _j(wolun_j)
    yj, mj, dj, hj = (list(jjis) + ['-'] * 4)[:4]

    VNAME = {'辰': '水庫', '戌': '火庫', '丑': '金庫', '未': '木庫'}
    JJG = {'辰': ['乙', '癸', '戊'], '戌': ['辛', '丁', '戊'],
           '丑': ['癸', '辛', '己'], '未': ['丁', '乙', '己']}
    EL = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
    CHUNG = {'辰': '戌', '戌': '辰', '丑': '未', '未': '丑'}
    HYUNG = {'丑': ['戌', '未'], '戌': ['丑', '未'], '未': ['丑', '戌']}
    SAMHYUNG = {'丑', '戌', '未'}
    MONTH_OF = {'寅': '양력 2월', '卯': '양력 3월', '辰': '양력 4월', '巳': '양력 5월',
                '午': '양력 6월', '未': '양력 7월', '申': '양력 8월', '酉': '양력 9월',
                '戌': '양력 10월', '亥': '양력 11월', '子': '양력 12월', '丑': '양력 1월'}

    def _yuk(grp):
        m = {'비겁': '형제·동료', '식상': '재능·표현', '재성': '재물', '관성': '직장·명예', '인성': '어머니·학업'}
        if gender == "남성":
            m['재성'] = '재물·아내'
            m['관성'] = '직장·명예·자식'
        else:
            m['재성'] = '재물·아버지'
            m['관성'] = '직장·명예·남편'
            m['식상'] = '재능·자식'
        return m.get(grp, grp)

    # 대상 선정: 충은 일지만, 형(삼형)은 일지가 축술미면 일지, 아니면 월지·시지(연지 제외)
    targets = {}
    if dj in VNAME:
        targets.setdefault(('일지', dj), set()).add('충')
    if dj in HYUNG:
        targets.setdefault(('일지', dj), set()).add('형')
    else:
        for p, b in (('월지', mj), ('시지', hj)):
            if b in HYUNG:
                targets.setdefault((p, b), set()).add('형')

    head = "[창고 개고·입고 시기 — 일지 기준, 삼형은 연지 제외]"
    foot = ("※원칙: 충·형이 없으면 입고도 개고도 일어나지 않음. 대운은 방향을 암시하고 세운·월운이 겹칠 때 실행됨. "
            "천간에 이미 드러난 기운은 열릴 때 창고로 들어가고(입고, 불리), 천간에 없이 숨은 기운은 열릴 때 밖으로 나옴(개고). "
            "재성 창고의 개고는 대체로 길하고, 그 밖의 육친 창고의 입고·입묘는 흉화를 암시함.")
    if not targets:
        why = "일지가 창고(辰戌丑未)가 아니어서 충에 의한 개고·입고는 해당 없고, 월지·시지에도 삼형 대상(丑·戌·未)이 없어 해당 없음."
        return head + "\n" + why

    lines = []
    year_map = {}
    for (pos, b), modes in targets.items():
        enter, out = [], []
        for s in JJG[b]:
            ss = get_ss(ds, s)
            tag = f"{s}({ss}·{_yuk(get_group_ss(ss))})"
            if any(EL.get(x) == EL[s] for x in gans):
                enter.append(tag)
            else:
                out.append(tag)

        opens = []
        if '충' in modes:
            opens.append(f"{CHUNG[b]}(충)")
        if '형' in modes:
            opens.append("丑·戌·未 세 글자가 모두 갖춰져 삼형이 완성될 때")
        if '충' in modes:
            tend = "辰戌충은 흉화가 가중되는 경향" if b in ('辰', '戌') else "丑未충은 발복이 상승하는 경향"
        else:
            tend = "충이 아니라 삼형 조건이며, 세 글자 중 하나만으로는 열리지 않음"

        won = ""
        if '충' in modes and CHUNG[b] in (mj, hj):
            won = f" 원국에 이미 {CHUNG[b]}가 있어 원국지지충 상태이며 해당 글자가 다시 들어오는 운에 충발함."
        if '형' in modes and SAMHYUNG <= set(jjis):
            won += " 원국에 이미 丑·戌·未 세 글자가 모두 있어 삼형이 갖춰진 상태이며, 이 창고와 다른 글자(丑·戌·未)가 행운에서 들어올 때마다 창고가 다시 흔들려 열림."

        hits = []
        for y in range(curr_year, curr_year + 10):
            br = _j(JI[(y - 1984) % 12])
            why = None
            if '충' in modes and br == CHUNG[b]:
                why = f"{b}{br}충"
            elif '형' in modes and br in HYUNG[b] and SAMHYUNG <= (set(jjis) | {dw_j, br}):
                why = "축술미 삼형 성립"
            if why:
                hits.append(f"{y}년({br}, {why}, 절기상 {br}월 즉 {MONTH_OF[br]} 무렵에 실행)")
                year_map.setdefault((y, br), []).append(f"{pos} {b}")

        now = []
        for nm, v in (("현재 대운", dw_j), ("올해 세운", sewun_j), ("이번 달 월운", wolun_j)):
            if '충' in modes and v == CHUNG[b]:
                now.append(f"{nm} {v}: {b}{v}충")
            elif '형' in modes and v in HYUNG[b] and SAMHYUNG <= (set(jjis) | {dw_j, sewun_j, v}):
                now.append(f"{nm} {v}: 축술미 삼형 성립")

        lines.append(
            f"- {pos} {b}({VNAME[b]}, 판정방식: {'·'.join(sorted(modes))}): "
            f"창고 안 지장간 중 천간에 이미 드러난 기운(열리면 입고) = {', '.join(enter) if enter else '없음'} / "
            f"천간에 없이 숨어 있는 기운(열리면 개고) = {', '.join(out) if out else '없음'}. "
            f"여는 글자: {', '.join(opens)} ({tend}).{won} "
            f"앞으로 10년 중 열리는 해: {'; '.join(hits) if hits else '없음'}. "
            f"지금 상태: {', '.join(now) if now else '해당 없음'}"
        )
    summ = []
    for (y, br), ps in sorted(year_map.items()):
        summ.append(f"{y}년({br}): " + (f"{ps[0]} 창고 하나만 열림" if len(ps) == 1 else " 와 ".join(ps) + " 두 창고가 함께 열림"))
    ysum = ("\n[연도별 정리 — 이 정리에 적히지 않은 창고는 그 해에 열리지 않음] " + " / ".join(summ)) if summ else ""
    return head + "\n" + "\n".join(lines) + ysum + "\n" + foot

def analyze_super_wealth_patterns(bazi_dict):
    yg, yj = bazi_dict.get('year_g'), bazi_dict.get('year_j')
    mg, mj = bazi_dict.get('month_g'), bazi_dict.get('month_j')
    dg, dj = bazi_dict.get('day_g'), bazi_dict.get('day_j')
    hg, hj = bazi_dict.get('time_g'), bazi_dict.get('time_j')
 
    stems = [yg, mg, dg, hg]
    branches = [yj, mj, dj, hj]
 
    results = {
        "yi_bing_geng_flag": False,
        "ding_xin_ren_flag": False,
        "you_chou_chen_flag": False,
        "myogo_treasure_flag": False,
        "wealth_power_score": 0,
        "fact_summary_text": []
    }
 
    has_yi = ('乙' in stems) or ('卯' in branches) or ('辰' in branches) or ('未' in branches)
    has_bing = ('丙' in stems) or ('巳' in branches) or ('午' in branches)
    has_geng = ('庚' in stems) or ('申' in branches)
 
    if has_yi and has_bing and has_geng:
        results["yi_bing_geng_flag"] = True
        results["wealth_power_score"] += 35
        results["fact_summary_text"].append("[乙·丙·庚 삼자조합 감지]: 대형 사업/거부 파동.")
 
    has_ding = ('丁' in stems) or ('午' in branches) or ('未' in branches)
    has_xin = ('辛' in stems) or ('酉' in branches)
    has_ren = ('壬' in stems) or ('亥' in branches) or ('子' in branches)
 
    if has_ding and has_xin and has_ren:
        results["ding_xin_ren_flag"] = True
        results["wealth_power_score"] += 40
        results["fact_summary_text"].append("[丁·辛·壬 삼자조합 감지]: 자산 가열 후 단기 대발/돈벼락 파동.")
 
    if ('酉' in branches) and ('丑' in branches) and ('辰' in branches):
        results["you_chou_chen_flag"] = True
        results["wealth_power_score"] += 25
        results["fact_summary_text"].append("[酉·丑·辰 삼자조합 감지]: 한탕/부동산 재개발 뻥튀기 파동.")
 
    earth_count = sum(1 for b in branches if b in ['辰', '戌', '丑', '未'])
    if earth_count >= 2:
        results["myogo_treasure_flag"] = True
        results["wealth_power_score"] += (earth_count * 10)
        _vault_info = {
            '辰': ('水庫', '癸', '戌(辰戌충)'),
            '戌': ('火庫', '丁', '辰(辰戌충)·丑 또는 未(형)'),
            '丑': ('金庫', '辛', '未(丑未충)·戌(형)'),
            '未': ('木庫', '乙', '丑(丑未충)·戌(형)'),
        }
        _pos_names = ['년지', '월지', '일지', '시지']
        _vault_desc = []
        for _i, _b in enumerate(branches):
            if _b in _vault_info:
                _vname, _rep_gan, _trigger = _vault_info[_b]
                _grp = get_group_ss(get_ss(dg, _rep_gan)) if dg else "-"
                _vault_desc.append(f"{_pos_names[_i]} {_b}({_vname}, 일간 기준 {_grp}의 창고)")
        results["fact_summary_text"].append(
            f"[창고 글자 {earth_count}개 보유]: " + " / ".join(_vault_desc) +
            ". (창고가 열리거나 갇히는 판정과 시기는 별도의 '창고 개고·입고' 사실문에서만 확인할 것)"
        )
 
    results["summary_output"] = "\n".join(results["fact_summary_text"]) if results["fact_summary_text"] else "일반 재물 흐름."
    return results

def analyze_zishui_jiapja_and_gapwood_patterns(bazi_dict):
    yg, yj = bazi_dict.get('year_g'), bazi_dict.get('year_j')
    mg, mj = bazi_dict.get('month_g'), bazi_dict.get('month_j')
    dg, dj = bazi_dict.get('day_g'), bazi_dict.get('day_j')
    hg, hj = bazi_dict.get('time_g'), bazi_dict.get('time_j')
 
    stems = [yg, mg, dg, hg]
    branches = [yj, mj, dj, hj]
 
    results = {"special_risk_score": 0, "fact_summary_text": []}
 
    if ('子' in branches) and ('酉' in branches):
        results["fact_summary_text"].append("[酉·子 破 파동 감지]: 씨종자 가치 변질 및 한탕주의 리스크.")
    if ('子' in branches) and ('卯' in branches):
        results["fact_summary_text"].append("[子·卯 刑 파동 감지]: 성적 강박, 자궁/비뇨기 질환 주의.")
    if ('子' in branches) and ('丑' in branches) and ('卯' in branches):
        results["fact_summary_text"].append("[지지 夾字(협자) 비틀림 감지]: 卯木 생기 강제 압박 및 신체 정체.")
 
    has_gap = ('甲' in stems) or ('寅' in branches)
    has_ren = ('壬' in stems) or ('亥' in branches)
    has_bing = ('丙' in stems) or ('巳' in branches)
    has_gui = ('癸' in stems) or ('子' in branches)
    has_mu = ('戊' in stems) or ('辰' in branches) or ('戌' in branches)
 
    if has_gap and has_ren and has_bing:
        results["fact_summary_text"].append("[壬·甲·丙 삼자조합 감지]: 대기만성형 거부 및 고위공직 파동.")
    if has_gap and has_gui and has_mu:
        results["fact_summary_text"].append("[癸·甲·戊 삼자조합 감지]: 폭력, 구타, 수술, 관재구설 주의.")
 
    results["summary_output"] = "\n".join(results["fact_summary_text"]) if results["fact_summary_text"] else "특이 파동 없음."
    return results


# ---- 3-B. [2-2 연애운] (3-1 궁합과 공용) ----

def analyze_love_and_marriage_patterns(bazi_dict):
    yg, yj = bazi_dict.get('year_g'), bazi_dict.get('year_j')
    mg, mj = bazi_dict.get('month_g'), bazi_dict.get('month_j')
    dg, dj = bazi_dict.get('day_g'), bazi_dict.get('day_j')
    hg, hj = bazi_dict.get('time_g'), bazi_dict.get('time_j')
 
    branches = [yj, mj, dj, hj]
    results = {"love_risk_score": 0, "fact_summary_text": []}
 
    if branches.count(dj) >= 2:
        results["fact_summary_text"].append(f"[쌍복음(雙伏吟) 경고]: 배우자 궁({dj}) 중첩으로 애정 불안정 및 이별 리스크.")
    if ('酉' in branches) and ('子' in branches) and ('丑' in branches):
        results["fact_summary_text"].append("[酉·子·丑 삼자조합 감지]: 한탕주의, 강압적 인연 및 정서적 폭발 주의.")
    if ('子' in branches) and ('卯' in branches) and ('辰' in branches):
        results["fact_summary_text"].append("[子·卯·辰 삼자조합 감지]: 불임, 자궁 질환, 자식 인연 박약 파동.")
    if ('卯' in branches) and ('戌' in branches):
        results["fact_summary_text"].append("[卯·戌 합(合) 파동 감지]: 서로 끌리는 합이 있어 인연이 가까워지기 쉬운 구조. 상대의 나이나 혼인 상태 등은 사주만으로 단정하지 말 것.")
    if dj == '戌':
        results["fact_summary_text"].append("[일지 戌土 배우자 자리 감지]: 배우자 자리가 불의 기운을 갈무리하는 마감의 땅이라, 부부 사이에 열정이 겉으로 드러나기보다 안으로 갈무리되어 표현이 조심스럽거나 서로 온도 차가 생기기 쉬운 자리. 배우자의 건강·성 기능 등은 사주만으로 단정하지 말 것.")
 
    results["summary_output"] = "\n".join(results["fact_summary_text"]) if results["fact_summary_text"] else "특이 애정 리스크 없음."
    return results


_SAMHAP_TRIOS = [{'亥','卯','未'}, {'寅','午','戌'}, {'申','子','辰'}, {'巳','酉','丑'}]
_BANGHAP_TRIOS = [{'寅','卯','辰'}, {'巳','午','未'}, {'申','酉','戌'}, {'亥','子','丑'}]

def _has_complete_hap(jj, dj):
    """한 사람의 지지 네 글자 안에서 삼합·방합이 세 글자 모두 모였고, 그 안에 일지(dj)가 들어 있으면 True"""
    s = set(jj)
    for trio in _SAMHAP_TRIOS + _BANGHAP_TRIOS:
        if trio <= s and dj in trio:
            return True
    return False

def get_spouse_extra_flags(g, j, gender):
    """각자 사주의 배우자궁 그릇에 영향을 주는 추가 요소(복음·卯戌합·재성/관성 부재와 쏠림).
    g, j 는 [년, 월, 일, 시] 순서. 반환: [(감점, 사실문), ...] — 점수와 풀이 글이 같은 기준을 씁니다."""
    out = []
    try:
        jj = [_to_hanja_ji(x) for x in j]
        dj = jj[2] if len(jj) > 2 else ""
        if dj and dj in JI and jj.count(dj) >= 2:
            out.append((1, f"배우자궁({dj})과 같은 글자가 사주 안에서 반복되어(복음) 인연이 겹치고 불안정해지기 쉬움"))
        if '卯' in jj and '戌' in jj:
            out.append((0.5, "사주 안에 卯와 戌이 함께 있어 서로 끌리는 합 파동이 있음(상대의 나이나 혼인 상태 등은 사주만으로 단정하지 말 것)"))
        chars = [c for c in (list(g) + list(j)) if c and str(c).strip() not in ("", "?", "-")]
        if len(chars) >= 8:   # 여덟 글자가 모두 있을 때만 판단
            dg = _to_hanja(g[2])
            cnt = {'비겁': 0, '식상': 0, '재성': 0, '관성': 0, '인성': 0}
            for c in chars:
                grp = get_group_ss(get_ss(dg, _to_hanja(c)))
                if grp in cnt:
                    cnt[grp] += 1
            if gender == "남성":
                if cnt['재성'] == 0: out.append((1, "사주에 재성(아내별)이 보이지 않아 배우자 인연을 붙잡기 어려운 구조"))
                if cnt['비겁'] >= 4: out.append((1, "비겁이 4개 이상 몰려 경쟁·분산의 기운이 강해 배우자와 재물을 두고 다툼 소지"))
            else:
                if cnt['관성'] == 0: out.append((1, "사주에 관성(남편별)이 보이지 않아 배우자 인연을 붙잡기 어려운 구조"))
                if cnt['관성'] >= 4: out.append((1, "관성이 4개 이상 몰려 부담과 압박을 크게 느끼기 쉬운 구조"))
                if cnt['식상'] >= 4: out.append((1, "식상이 4개 이상 몰려 주관이 강해 남편별을 누르기 쉬운 구조"))
    except Exception:
        pass
    return out


def get_spouse_palace_facts(ds, gans, jjis, gender):
    """
    배우자궁(일지)의 안정성 팩트 문자열을 만듭니다. (gans, jjis 는 [시, 일, 월, 년] 순서)
    - 일지와 월지·년지·시지의 합충형파해, 일지의 십성(배우자별 유무), 일지 공망, 고신·과숙을 종합합니다.
    - 결과는 AI 에게 전달하는 '팩트'이며, 문장 안의 전문 용어는 AI 가 일상어로 풀어 쓰게 되어 있습니다.
    """
    ds = _to_hanja(ds)
    gans = [_to_hanja(g) for g in gans]
    jjis = [_to_hanja_ji(j) for j in jjis]
    if len(jjis) < 4 or not jjis[1] or jjis[1] not in JI:
        return "배우자궁 판정에 필요한 일지 정보가 부족함"
    dj = jjis[1]
    others = [("월지", jjis[2]), ("년지", jjis[3]), ("시지", jjis[0])]
    bad, good = [], []
    for nm, j in others:
        if not j or j not in JI:
            continue
        rel = get_ji_rel_set(dj, j)
        if rel == "-":
            continue
        tags = [x.strip() for x in rel.split(",")]
        neg = [t for t in tags if t in ("충", "형", "원진", "파", "해", "귀문")]
        pos = [t for t in tags if t in ("육합", "반합", "방합", "방합(미완)")]
        _MEAN = {"충": "서로 부딪힘", "형": "서로 어긋나 틀어짐", "원진": "끌리면서도 서운함이 쌓이는 어긋남(애증)", "귀문": "마음이 예민해져 생각이 꼬이기 쉬움",
                 "파": "서로 깨지듯 흔들림", "해": "서로 엇나감", "육합": "서로 당겨 묶임", "반합": "서로 당겨 힘을 모음", "방합": "같은 기운으로 이어짐", "방합(미완)": "같은 기운으로 이어짐"}
        if neg: bad.append(f"일지({dj})–{nm}({j}): {'·'.join(neg)}[{' / '.join(_MEAN[t] for t in neg)}]")
        if pos: good.append(f"일지({dj})–{nm}({j}): {'·'.join(pos)}[{' / '.join(_MEAN[t] for t in pos)}]")

    is_male = (gender == "남성")
    ss = get_ss(ds, dj)
    if is_male:
        if ss in ("정재", "편재"): good.append(f"배우자궁에 아내별({ss})이 자리해 인연이 직접적임")
        elif ss in ("비견", "겁재"): bad.append(f"배우자궁에 경쟁·분산의 기운({ss})이 앉아 재물·배우자 문제로 다툼 소지")
    else:
        if ss in ("정관", "편관"): good.append(f"배우자궁에 남편별({ss})이 자리해 인연이 직접적임")
        elif ss in ("상관", "식신"): bad.append(f"배우자궁에 남편별을 누르는 기운({ss})이 앉아 주관이 강해질 수 있음")

    # 일지 공망 (년주 기준 공망)
    try:
        if gans[3] and jjis[3]:
            gm = calculate_gongmang(gans[3], jjis[3])
            if gm and gm != "-" and dj in gm:
                bad.append(f"일지({dj})가 년주 기준 공망에 해당해 배우자 인연이 늦거나 허전함을 느끼기 쉬움")
    except Exception:
        pass

    # 고신·과숙
    try:
        gg_ji, gg_label = get_goshin_gwasook_ji(dj, gender)
        if gg_ji and gg_ji in jjis and gg_ji != dj:
            bad.append(f"{gg_label}({gg_ji})이 원국에 있어 외로움을 느끼기 쉬운 기운")
    except Exception:
        pass

    # 복음·卯戌합·십성 쏠림/부재 (점수와 같은 기준)
    try:
        for _pen, _txt in get_spouse_extra_flags([gans[3], gans[2], gans[1], gans[0]], [jjis[3], jjis[2], jjis[1], jjis[0]], gender):
            bad.append(_txt)
    except Exception:
        pass
    if not bad and not good:
        return "배우자궁(일지)이 다른 지지와 특별한 합충 없이 비교적 안정적인 흐름"

    parts = []
    if bad: parts.append("흔들릴 수 있는 요소: " + "; ".join(bad))
    if good: parts.append("받쳐주는 요소: " + "; ".join(good))
    verdict = "배우자궁이 흔들리기 쉬운 구조" if len(bad) >= 2 else ("배우자궁에 약간의 주의가 필요한 구조" if bad else "배우자궁이 비교적 안정적인 구조")
    return f"[{verdict}] " + " / ".join(parts)
def get_love_shinsal_risk_facts(gans, jjis, gender):
    """연애·이성 문제와 관련된 신살(홍염·음욕·도화·간여지동·고란 등)이 어느 기둥에 있는지 AI 용 팩트 문자열로 만듭니다.
    gans, jjis : [시, 일, 월, 년] 순서"""
    LOVE = ["홍염살", "음욕살", "도화살", "나체도화", "간여지동", "고란살", "의처의부", "남연살", "여연살", "비인살", "원진", "귀문"]
    pillar_names = ["시주", "일주", "월주", "년주"]
    found = []
    gans = [_to_hanja(g) for g in gans]
    jjis = [_to_hanja_ji(j) for j in jjis]
    try:
        for i in range(4):
            tags = [re.sub(r"<[^>]+>", "", x).strip() for x in get_general_shinsal_filtered(i, gans, jjis, gender)]
            hit = [t for t in tags if any(k in t for k in LOVE)]
            if hit:
                found.append(f"{pillar_names[i]}: " + ", ".join(dict.fromkeys(hit)))
    except Exception:
        return "연애 관련 신살 판정 정보 없음"
    if not found:
        return "연애·이성 문제와 관련해 특별히 두드러진 신살 없음"
    return "연애 관련 신살 분포 — " + " / ".join(found)


# ---- 3-C. [2-3 진학운] [2-4 직업운] : 전용 계산 함수 없음 (PART 1·2 공통 함수 사용) ----


# ---- 3-D. [2-5 건강운] 침식 4D · 종양 · 인지기능 · 식상 과다 ----

def analyze_health_erosion_4d(saju_data, daewun_list, sewun_10_list, curr_year):
    won_guk_ji = saju_data.get('ji', [])
    current_dw_ji = saju_data.get('current_dw_ji', '')
    current_sewun_ji = saju_data.get('current_sewun_ji', '')
 
    has_dry_earth = any(ji in won_guk_ji for ji in ['未', '戌'])
    has_water = any(ji in won_guk_ji for ji in ['亥', '子'])
    if has_dry_earth and has_water:
        fact_1_wonguk = "원국 내 조열한 흙(未·戌)이 생명수(亥·子)를 곁에서 말리는 구조적 취약성 내재."
    else:
        fact_1_wonguk = "원국 자체의 수기(水氣) 고갈 위험은 적으나, 대운/세운의 흐름에 따른 대비 필요."
 
    danger_dw_periods = []
    for idx, dw in enumerate(daewun_list):
        dw_ji = dw.get('j_hangul', '')
        if dw_ji in ['未', '戌', '午', '巳']:
            if idx < 3: period = "초년"
            elif idx < 6: period = "중년"
            else: period = "말년"
            dw_gan = dw.get('c_hangul', '')
            danger_dw_periods.append(f"{period}({dw_gan}{dw_ji}대운)")
 
    if danger_dw_periods:
        periods_str = ", ".join(list(dict.fromkeys(danger_dw_periods)))
        fact_2_daewun = f"생애 주기 중 {periods_str} 시기에 열기가 가중되며 선천적 조토극수 파동이 크게 증폭되는 거시적 변곡점 형성."
    else:
        fact_2_daewun = "평생 대운의 궤적에서 극심한 한난조습의 쏠림은 방어되고 있는 평온한 흐름."
 
    danger_years = []
    for sewun in sewun_10_list:
        year = sewun.get('year')
        sw_ji = sewun.get('ji', '')
        combined_ji = won_guk_ji + [current_dw_ji, sw_ji]
        if '未' in combined_ji and '戌' in combined_ji:
            danger_years.append(f"{year}년")
 
    if danger_years:
        fact_3_10years = f"현재 대운 내에서 향후 {', '.join(danger_years)}에 수기(水氣)가 심각하게 고갈 및 협자 압박이 가중되는 최대 주의 구간 도래."
    else:
        fact_3_10years = "향후 10년 내에 치명적인 조토극수 및 협자 압박 변곡점은 감지되지 않음."
 
    combined_curr = won_guk_ji + [current_dw_ji, current_sewun_ji]
    if '未' in combined_curr or '戌' in combined_curr or '午' in combined_curr:
        fact_4_current = f"당장 올해({curr_year}년)는 조열한 기운이 가세하여 만성 피로와 대사/신경계 무리가 현실화되기 쉬운 시점. 즉각적인 섭생 관리 요망."
    else:
        fact_4_current = f"올해({curr_year}년)는 조토극수 침식 파동의 직접적인 타격권에서 한 걸음 비껴가 있는 회복과 유지의 구간."
 
    return f"[1. 선천 원국]: {fact_1_wonguk}\n[2. 평생 궤적]: {fact_2_daewun}\n[3. 향후 10년]: {fact_3_10years}\n[4. 당장 올해]: {fact_4_current}"

def analyze_tumor_risk_facts(gans, jjis, daewun_list, sewun_10_list, curr_year, current_dw_j):
    """
    gans, jjis: [시(hour), 일(day), 월(month), 년(year)] 순서의 4글자 리스트.
    종괴(積聚)/암 관련 명리 파동을 4단계(원국/평생궤적/10년/올해)로 판정.
    """
    gans_h = [_to_hanja(g) for g in gans]
    jjis_h = [_to_hanja(j) for j in jjis]

    ilju = f"{gans_h[1]}{jjis_h[1]}"   # 일간+일지 (index 1 = 일)
    all_ganji = [f"{g}{j}" for g, j in zip(gans_h, jjis_h)]

    has_goegang = ilju in GOEGANG_ILJU
    has_baekho = any(gj in BAEKHO_GANJI for gj in all_ganji)

    if has_goegang or has_baekho:
        names = [n for n, flag in [("괴강살", has_goegang), ("백호대살", has_baekho)] if flag]
        fact_1 = f"원국에 {'·'.join(names)}이 존재하여, 응어리진 기운이 신체 특정 부위에 정체·축적되기 쉬운 체질적 취약성 내재."
    else:
        fact_1 = "원국 자체에 강한 응어리(종괴) 파동은 없으나, 대운/세운의 묘고 입고 흐름은 정기적으로 점검할 필요."

    danger_dw_periods = []
    for idx, dw in enumerate(daewun_list):
        dw_ji_h = _to_hanja(dw.get('j_hangul', ''))
        if any('입고' in v for v in check_vault_status(gans_h, jjis_h, dw_ji_h)):
            period = "초년" if idx < 3 else ("중년" if idx < 6 else "말년")
            danger_dw_periods.append(f"{period}({dw.get('c_hangul','')}{dw.get('j_hangul','')}대운)")

    if danger_dw_periods:
        fact_2 = f"생애 주기 중 {', '.join(dict.fromkeys(danger_dw_periods))} 시기에 묘고가 풀리지 않고 뭉치는 흐름이 반복되니, 이 시기 정기 건강검진이 특히 중요."
    else:
        fact_2 = "평생 대운의 궤적에서 묘고가 계속 입고만 되는 정체 흐름은 뚜렷하지 않은 안정적 구간."

    danger_years = []
    for sewun in sewun_10_list:
        sw_ji_h = _to_hanja(sewun.get('ji', ''))
        if any('입고' in v for v in check_vault_status(gans_h, jjis_h, sw_ji_h)):
            danger_years.append(f"{sewun.get('year')}년")

    if danger_years:
        fact_3 = f"현재 대운 내에서 향후 {', '.join(danger_years)}에 묘고 입고가 겹치니 이 시기 정밀 검진을 권장."
    else:
        fact_3 = "향후 10년 내에 뚜렷한 묘고 입고·정체 변곡점은 감지되지 않음."

    curr_dw_ji_h = _to_hanja(current_dw_j) if current_dw_j else ''
    is_danger_now = curr_dw_ji_h and any('입고' in v for v in check_vault_status(gans_h, jjis_h, curr_dw_ji_h))
    fact_4 = (f"당장 올해({curr_year}년)는 묘고 입고 기운이 작용해 몸 안에 정체된 것이 쌓이기 쉬운 시점. 정기 검진과 순환 관리 요망."
              if is_danger_now else f"올해({curr_year}년)는 묘고 입고로 인한 정체 파동에서 비교적 자유로운 구간.")

    return f"[1. 선천 원국]: {fact_1}\n[2. 평생 궤적]: {fact_2}\n[3. 향후 10년]: {fact_3}\n[4. 당장 올해]: {fact_4}"

def analyze_cognitive_decline_facts(won_guk_ji, daewun_list, sewun_10_list, curr_year, age):
    """
    水氣(전통적으로 뇌수·정신을 상징)의 고갈 여부를, 특히 말년(대략 60세 이후) 시기에 집중하여 판정.
    """
    has_water = any(ji in won_guk_ji for ji in ['亥', '子'])
    fact_1 = ("원국에 수기(水氣)가 자리하고 있어 정신적 균형을 지탱하는 바탕은 갖추어져 있으나, 대운의 흐름에 따라 기복이 있을 수 있음."
              if has_water else
              "원국에 수기(水氣)를 담당하는 글자가 없어, 나이가 들수록 총명함과 정신적 균형을 지켜주는 기운이 상대적으로 약한 편.")

    danger_dw_periods = []
    for idx, dw in enumerate(daewun_list):
        if idx >= 6 and dw.get('j_hangul', '') in ['未', '戌', '午', '巳']:
            danger_dw_periods.append(f"말년({dw.get('c_hangul','')}{dw.get('j_hangul','')}대운)")

    if danger_dw_periods and age >= 55:
        fact_2 = f"{', '.join(dict.fromkeys(danger_dw_periods))} 시기에 수기가 메마르는 흐름이 겹쳐, 이 시기 인지기능과 기억력 관리에 더욱 신경 써야 할 구간."
    else:
        fact_2 = "말년 대운의 궤적에서 뚜렷한 수기 고갈 변곡점은 아직 감지되지 않음."

    danger_years = [f"{sw.get('year')}년" for sw in sewun_10_list if sw.get('ji', '') in ['未', '戌']]
    fact_3 = (f"향후 10년 중 {', '.join(danger_years)}에 수기 고갈이 가중되는 구간이 있어, 이 무렵 인지건강 검진을 권장."
              if danger_years and age >= 60 else
              "향후 10년 내에 인지기능과 직결되는 뚜렷한 수기 고갈 변곡점은 감지되지 않음.")

    fact_4 = (f"올해({curr_year}년) 기준, 신청자의 나이({age}세)를 고려할 때 인지건강에 특별히 더 신경 써야 할 민감한 시기이니 꾸준한 두뇌 활동과 정서적 안정이 중요."
              if age >= 65 else
              f"올해({curr_year}년)는 예방적 관리 차원에서 꾸준한 생활 습관을 유지하면 충분한 시기.")

    return f"[1. 선천 원국]: {fact_1}\n[2. 평생 궤적]: {fact_2}\n[3. 향후 10년]: {fact_3}\n[4. 당장 올해]: {fact_4}"

def analyze_siksang_drain_facts(counts, mb, ds, daewun_list, sewun_10_list, curr_year, current_dw_j, age, db=None):
    """
    일간이 신약(身弱)한 상태에서 식상(食傷) 대운·세운이 겹쳐 들어와 기운이 과도하게 빠지는(설기) 시기를 판정.
    고령자는 원기 회복력이 약해 이 설기 효과가 더 크게 체감되므로 나이에 따라 경고 수위를 달리한다.
    """
    dm = get_color(ds)
    if not dm or dm not in _OHAENG_CYCLE:
        return "일간 오행을 판별할 수 없어 식상 설기 분석을 생략합니다."

    biguk, inseong = dm, _oh_prev(dm)
    siksang, jaeseong, gwanseong = _oh_next(dm), _oh_controls(dm), _oh_controlled_by(dm)

    strength = _judge_strength(counts, mb, ds, db)[0]
    is_weak = (strength != '신강')   # 신약·중화는 약한 쪽으로 봄(예전의 동점=약함과 같은 방식)

    if not is_weak:
        return ("[1. 선천 원국]: 일간이 신강(身强)하여 식상운이 겹쳐도 오히려 기운을 잘 발산시키는 흐름이니 크게 걱정할 필요 없음.\n"
                "[2. 평생 궤적]: 신강한 원국이라 식상 대운이 겹치는 시기라도 건강상 큰 소모 위험은 낮음.\n"
                "[3. 향후 10년]: 신강한 바탕 위에서 식상운이 오히려 활력으로 작용할 가능성이 높음.\n"
                f"[4. 당장 올해]: 올해({curr_year}년)도 기운이 과도하게 빠질 걱정은 적은 편.")

    fact_1 = "일간이 신약(身弱)한 원국이라, 식상운이 겹쳐 들어올 때 기운이 과도하게 빠져나가는 설기(泄氣)에 취약한 체질."

    danger_dw_periods = []
    for idx, dw in enumerate(daewun_list):
        dw_ji = dw.get('j_hangul', '')
        if get_color(dw_ji) == siksang:
            period = "초년" if idx < 3 else ("중년" if idx < 6 else "말년")
            danger_dw_periods.append(f"{period}({dw.get('c_hangul','')}{dw_ji}대운)")
    fact_2 = (f"생애 주기 중 {', '.join(dict.fromkeys(danger_dw_periods))} 시기에 식상 대운이 들어와 기운 소모가 커지는 흐름이 반복됨."
              if danger_dw_periods else "평생 대운의 궤적에서 식상운이 두드러지게 겹치는 시기는 뚜렷하지 않음.")

    curr_dw_is_siksang = get_color(current_dw_j) == siksang if current_dw_j else False
    danger_years = []
    for sewun in sewun_10_list:
        sw_ji = sewun.get('ji', '')
        if get_color(sw_ji) == siksang:
            tag = "(대운까지 겹침)" if curr_dw_is_siksang else ""
            danger_years.append(f"{sewun.get('year')}년{tag}")
    fact_3 = (f"현재 대운 내에서 향후 {', '.join(danger_years)}에 식상 기운이 가중되니 체력 관리가 중요."
              if danger_years else "향후 10년 내에 식상운이 두드러지게 겹치는 변곡점은 감지되지 않음.")

    is_danger_now = curr_dw_is_siksang or any(get_color(sw.get('ji', '')) == siksang and sw.get('year') == curr_year for sw in sewun_10_list)
    if is_danger_now:
        if age >= 65:
            age_note = " 특히 연세가 있으신 만큼 원기 회복력이 젊을 때보다 약해 이 흐름이 평소보다 크게 체감될 수 있으니, 무리한 활동을 삼가고 충분한 휴식이 꼭 필요."
        elif age >= 50:
            age_note = " 중년 이후이신 만큼 평소보다 체력 관리에 조금 더 신경 쓰시는 게 좋음."
        else:
            age_note = ""
        fact_4 = f"올해({curr_year}년)는 식상 기운이 강하게 작용해 기운이 빠지기 쉬운 시점.{age_note}"
    else:
        fact_4 = f"올해({curr_year}년)는 식상운의 직접적인 소모 파동에서 비교적 자유로운 구간."

    return f"[1. 선천 원국]: {fact_1}\n[2. 평생 궤적]: {fact_2}\n[3. 향후 10년]: {fact_3}\n[4. 당장 올해]: {fact_4}"


# ---- 3-E. [2-6 이사 택일] [2-7 개업 택일] ----

def get_best_moving_opening_days(start_date, end_date, user_gans, user_jjis, purpose, avoid_jis=None):
    import datetime as dt_mod
 
    day_gan = user_gans[1]
    day_ji = user_jjis[1]
 
    best_days = []
    curr_date = start_date
 
    while curr_date <= end_date:
        try:
            y_p, m_p, d_p = get_ganji_from_date(curr_date.year, curr_date.month, curr_date.day)
            d_gan, d_ji = d_p[0], d_p[1]
        except Exception:
            curr_date += dt_mod.timedelta(days=1)
            continue
 
        if avoid_jis and any("충" in get_ji_rel_set(pj, d_ji) for pj in avoid_jis):
            curr_date += dt_mod.timedelta(days=1)
            continue

        if d_p in _SIPAK_DAEPAE:   # 십악대패일은 이사·개업 후보에서 제외
            curr_date += dt_mod.timedelta(days=1)
            continue

        score = 70.0

        if d_p in _SIPAK_DAEPAE:   # 십악대패일은 이사·개업 후보에서 제외
            curr_date += dt_mod.timedelta(days=1)
            continue

        score = 70.0
 
        rel = get_ji_rel_set(day_ji, d_ji)
        if "충" in rel: score -= 20
        if "원진" in rel or "귀문" in rel: score -= 15
        if "형" in rel: score -= 10
        if "파" in rel or "해" in rel: score -= 5
 
        if purpose == "이사":
            if "육합" in rel: score += 15
            if "방합" in rel or "반합" in rel: score += 10
 
            if day_ji == '寅' and d_ji in ['寅', '巳', '申']: score -= 10
            if day_ji == '午' and d_ji in ['辰', '午', '丑']: score -= 10
            if day_ji == '丑' and d_ji in ['午', '未', '戌']: score -= 10
 
        else:
            day_ss = get_ss(day_gan, d_gan)
            day_ji_ss = get_ss(day_gan, d_ji)
            ss_group_g = get_group_ss(day_ss)
            ss_group_j = get_group_ss(day_ji_ss)
 
            if ss_group_g in ["재성", "식상"]: score += 10
            if ss_group_j in ["재성", "식상"]: score += 10
 
            if ss_group_g == "비겁" or ss_group_j == "비겁": score -= 10
 
            combined_gans = set(user_gans + [d_gan])
            if {'丁', '辛', '壬'}.issubset(combined_gans): score += 20
            if {'乙', '丙', '庚'}.issubset(combined_gans): score += 20
 
            combined_jjis = set(user_jjis + [d_ji])
            if {'酉', '丑', '辰'}.issubset(combined_jjis): score += 15
 
        best_days.append({
            'date': curr_date.strftime("%Y-%m-%d"),
            'ganji': d_p,
            'score': score
        })
        curr_date += dt_mod.timedelta(days=1)
 
    best_days.sort(key=lambda x: x['score'], reverse=True)
    return best_days[:3]


def get_sonupnun_days(start_date, end_date):
    import datetime as dt_mod
    out = []
    klc = KoreanLunarCalendar()
    cur = start_date
    while cur <= end_date:
        try:
            if klc.setSolarDate(cur.year, cur.month, cur.day) and klc.lunarDay % 10 in (9, 0):
                out.append(f"{cur.month}월 {cur.day}일(음력 {klc.lunarMonth}월 {klc.lunarDay}일)")
        except Exception:
            pass
        cur += dt_mod.timedelta(days=1)
    return out


def get_partner_clash_days(start_date, end_date, avoid_jis):
    import datetime as dt_mod
    out = []
    if not avoid_jis:
        return out
    curr = start_date
    while curr <= end_date:
        try:
            _, _, d_p = get_ganji_from_date(curr.year, curr.month, curr.day)
            d_gan, d_ji = d_p[0], d_p[1]
        except Exception:
            curr += dt_mod.timedelta(days=1)
            continue
        hit = [pj for pj in avoid_jis if "충" in get_ji_rel_set(pj, d_ji)]
        if hit:
            out.append(f"{curr.month}월 {curr.day}일 {d_gan}{d_ji}일")
        curr += dt_mod.timedelta(days=1)
    return out


# ==============================================================================
# PART 4. [3-x 궁합 · 택일] 3-1 궁합 · 3-2 결혼 택일 · 3-3 출산 택일
# ==============================================================================


# ---- 4-A. [3-1 궁합] 점수 산출 엔진 ----

class UniversalPrintableGunghap:
    def __init__(self, applicant, partner_name, male, female, m_dw_ji=None, f_dw_ji=None, dw_wave=None):
        self.app = applicant
        self.p_name = partner_name
        self.m_dw_ji = m_dw_ji
        self.f_dw_ji = f_dw_ji
        self.dw_wave = dw_wave   # 20~80대 대운 물결 비교 점수(0~10). 없으면 현재 대운 지지 비교로 대신함

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
        if s in [{'寅','卯'}, {'卯','辰'}, {'巳','午'}, {'午','未'}, {'申','酉'}, {'酉','戌'}, {'亥','子'}, {'子','丑'}]: return "방합"
        if s in [{'申','子'}, {'子','辰'}, {'寅','午'}, {'午','戌'}, {'亥','卯'}, {'卯','未'}, {'巳','酉'}, {'酉','丑'}]: return "반합"
        if s in [{'亥','未'}, {'寅','戌'}, {'申','辰'}, {'巳','丑'}]: return "공합"
        if s in [{'寅','辰'}, {'巳','未'}, {'申','戌'}, {'亥','丑'}]: return "공협"
        if s in [{'子','午'}, {'丑','未'}, {'寅','申'}, {'卯','酉'}, {'辰','戌'}, {'巳','亥'}]: return "충"
        if s in [{'子','未'}, {'丑','午'}, {'寅','酉'}, {'卯','申'}, {'辰','亥'}, {'巳','戌'}]: return "원진"
        if s in [{'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}, {'子','卯'}]: return "형"
        if s in [{'子','酉'}, {'丑','辰'}, {'寅','亥'}, {'卯','午'}, {'巳','申'}, {'未','戌'}]: return "파"
        if s in [{'子','未'}, {'丑','午'}, {'寅','巳'}, {'卯','辰'}, {'申','亥'}, {'酉','戌'}]: return "해"
        return "무"
 
    def get_spouse_palace_score(self, g, j, gender):
        """각자의 배우자궁(일지) 안정도를 0~10점으로 계산합니다. g, j 는 [년, 월, 일, 시] 순서"""
        jj = [_to_hanja_ji(x) for x in j]
        dj = jj[2]
        if not dj or dj not in JI:
            return 7   # 일지를 모를 때는 보통 점수
        score, plus = 10, 0
        for k in (1, 0, 3):   # 월지, 년지, 시지와의 관계
            oj = jj[k]
            if not oj or oj not in JI:
                continue
            rel = get_ji_rel_set(dj, oj)
            if rel == "-":
                continue
            for t in [x.strip() for x in rel.split(",")]:
                if t == "충": score -= 3
                elif t == "형": score -= 2
                elif t in ("원진", "귀문", "파", "해"): score -= 1
            # 합 가점: 육합 +1, 반합·방합(왕지 포함 두 글자) +0.5 (공합·공협은 가점 없음)
            _lab = self.get_ji_rel(dj, oj)
            if _lab == "육합": plus += 1
            elif _lab in ("반합", "방합"): plus += 0.5
        # 일지가 삼합·방합 완성(세 글자 모두)에 들어 있으면 +1
        if _has_complete_hap(jj, dj): plus += 1
        # 일지의 십성 (남: 재성 좋음/비겁 나쁨, 여: 관성 좋음/식상 나쁨)
        try:
            ss = get_ss(_to_hanja(g[2]), dj)
            if gender == "남성":
                if ss in ("정재", "편재"): plus += 1
                elif ss in ("비견", "겁재"): score -= 1
            else:
                if ss in ("정관", "편관"): plus += 1
                elif ss in ("상관", "식신"): score -= 1
        except Exception:
            pass
        # 일지가 년주 기준 공망이면 -2
        try:
            gy, jy = _to_hanja(g[0]), jj[0]
            if gy and jy:
                gm = calculate_gongmang(gy, jy)
                if gm and gm != "-" and dj in gm:
                    score -= 2
        except Exception:
            pass
        # 고신·과숙이 원국에 있으면 -1
        try:
            gg_ji, _gg_label = get_goshin_gwasook_ji(dj, gender)
            if gg_ji and gg_ji in jj and gg_ji != dj:
                score -= 1
        except Exception:
            pass
        for _pen, _txt in get_spouse_extra_flags(g, j, gender):
            score -= _pen       # 복음 -1, 卯戌합 -0.5, 재성/관성 부재·쏠림 각 -1
        score += min(2, plus)   # 합·좋은 십성의 가점은 최대 +2
        return max(0, min(10, score))

    def count_elements(self, gans, jjis):
        counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
        for char in gans + jjis:
            c = _to_hanja(char)
            if not c: continue   # 빈 기둥(시주 모름 등)은 세지 않음
            if c in "甲乙寅卯": counts['목'] += 1
            elif c in "丙丁巳午": counts['화'] += 1
            elif c in "戊己辰戌丑未": counts['토'] += 1
            elif c in "庚辛申酉": counts['금'] += 1
            elif c in "壬癸亥子": counts['수'] += 1
        return counts
 
    def get_johoo_harmony(self, m_ilgan, m_ec, f_ec):
        score = 0
        if m_ilgan in "丙丁":
            if f_ec['수'] >= 2: score += 5
        elif m_ilgan in "壬癸":
            if f_ec['화'] >= 2: score += 5
        return score
 
    def run_universal_logic(self):
        m_g, m_j, f_g, f_j = self.m_g, self.m_j, self.f_g, self.f_j
 
        # 🌟 삼합·방합 완성: 남명·여명 지지 8글자를 합쳐 세 글자가 모두 모였는지 확인 (한 분 혼자 완성된 합은 제외)
        _mset = {x for x in (_to_hanja(c) for c in m_j) if x and x != "?"}
        _fset = {x for x in (_to_hanja(c) for c in f_j) if x and x != "?"}
        _ilji2 = {_to_hanja(m_j[2]), _to_hanja(f_j[2])}
        _cplt_any, _cplt_ilji = False, False
        for _trio in _SAMHAP_TRIOS + _BANGHAP_TRIOS:
            if _trio <= (_mset | _fset) and not _trio <= _mset and not _trio <= _fset:
                _cplt_any = True
                if _ilji2 <= _trio: _cplt_ilji = True   # 두 분의 일지가 모두 그 합에 들어 있음

        # 🌟 삼합·방합 완성: 남명·여명 지지 8글자를 합쳐 세 글자가 모두 모였는지 확인 (한 분 혼자 완성된 합은 제외)
        _mset = {x for x in (_to_hanja(c) for c in m_j) if x and x != "?"}
        _fset = {x for x in (_to_hanja(c) for c in f_j) if x and x != "?"}
        _ilji2 = {_to_hanja(m_j[2]), _to_hanja(f_j[2])}
        _cplt_any, _cplt_ilji = False, False
        for _trio in _SAMHAP_TRIOS + _BANGHAP_TRIOS:
            if _trio <= (_mset | _fset) and not _trio <= _mset and not _trio <= _fset:
                _cplt_any = True
                if _ilji2 <= _trio: _cplt_ilji = True   # 두 분의 일지가 모두 그 합에 들어 있음

        il_rel = self.get_ji_rel(m_j[2], f_j[2])
        if il_rel == "육합": s1 = 25
        elif il_rel in ["방합", "반합"]: s1 = 21
        elif il_rel in ["공합", "공협"]: s1 = 18
        elif il_rel == "무": s1 = 17
        elif il_rel in ["파", "해"]: s1 = 12
        elif il_rel in ["형", "원진"]: s1 = 8
        elif il_rel == "충": s1 = 5
        else: s1 = 17
        if _cplt_ilji: s1 = 25   # 두 분의 일지가 삼합·방합 완성에 함께 들어 있으면 육합급
        p1 = int((s1 / 25) * 100)
 
        # 🌟 환경 조화 15점 = 년지(띠 겉궁합) 5 + 월지 5 + 시지 5 — 남명과 여명의 같은 자리끼리 비교
        _pos5 = {"육합": 5, "방합": 4, "반합": 4, "공합": 3.2, "공협": 3.2, "무": 3, "파": 2, "해": 2, "형": 1, "원진": 1, "충": 0}
        n_rel, w_rel, si_rel = self.get_ji_rel(m_j[0], f_j[0]), self.get_ji_rel(m_j[1], f_j[1]), self.get_ji_rel(m_j[3], f_j[3])
        s2 = _pos5.get(n_rel, 3) + _pos5.get(w_rel, 3) + _pos5.get(si_rel, 3)
        if _cplt_any and not _cplt_ilji: s2 += 2   # 일지가 아닌 자리로 삼합·방합이 완성되면 +2 (15점 만점 안에서)
        s2 = min(15, s2)
        p2 = int(round((s2 / 15) * 100))
 
        m_ec, f_ec = self.count_elements(m_g, m_j), self.count_elements(f_g, f_j)
        s3 = 5
        for e in ['목','화','토','금','수']:
            if m_ec[e] == 0 and f_ec[e] >= 2: s3 += 2
            if f_ec[e] == 0 and m_ec[e] >= 2: s3 += 2
            if m_ec[e] >= 4 and f_ec[e] >= 4: s3 -= 2
        s3 = max(0, min(10, s3))
        p3 = int((s3 / 10) * 100)
 
        s4 = 10
        RISK_SHINSAL = ["간여지동", "고란살", "구추방해", "백호대살", "신병", "음욕", "의처의부", "홍염", "괴강살", "양인살"]

        def _day_pillar_evil(g, j, gender):
            # get_general_shinsal_filtered는 [시,일,월,년] 순서를 요구하므로 변환
            reordered_g = [g[3], g[2], g[1], g[0]]
            reordered_j = [j[3], j[2], j[1], j[0]]
            return get_general_shinsal_filtered(1, reordered_g, reordered_j, gender)

        m_evil = _day_pillar_evil(m_g, m_j, "남성")
        f_evil = _day_pillar_evil(f_g, f_j, "여성")
        def _risk_hit_count(evil, extra):
            hit = [f for f in RISK_SHINSAL + [extra] if any(f in x for x in evil)]
            if "음양차착" in hit and "음양" in hit:
                hit.remove("음양")   # 음양차착 안에 '음양'이 들어 있어 두 번 세어지는 것을 막음
            return len(hit)
        s4 -= _risk_hit_count(m_evil, "남연살")
        s4 -= _risk_hit_count(f_evil, "여연살")

        # 음양 극단 치우침 (8글자 중 양/음 어느 한쪽으로 7개 이상 쏠림)
        _yang_chars = set("甲丙戊庚壬子寅辰午申戌")
        def _eum_yang_extreme(g, j):
            all_chars = [c for c in (_to_hanja(x) for x in (g + j)) if c]
            if len(all_chars) < 8:
                return False   # 여덟 글자가 모두 있을 때만 쏠림을 판단
            yang_cnt = sum(1 for c in all_chars if c in _yang_chars)
            return yang_cnt >= 7 or yang_cnt <= 1
        if _eum_yang_extreme(m_g, m_j): s4 -= 1
        if _eum_yang_extreme(f_g, f_j): s4 -= 1

        # 관살혼잡(여성) / 재성혼잡(남성)
        def _has_honjap(day_gan, chars, type_a, type_b):
            ss_list = [get_ss(day_gan, c) for c in chars]
            return (type_a in ss_list) and (type_b in ss_list)
        if _has_honjap(m_g[2], m_g + m_j, "정재", "편재"): s4 -= 1   # 남성 재성혼잡
        if _has_honjap(f_g[2], f_g + f_j, "정관", "편관"): s4 -= 1   # 여성 관살혼잡

        # 비겁·식상 폭주(브레이크 없음): 비겁+식상 5개 이상인데 관성·인성이 0개
        def _ss_count(day_gan, chars, ss_names):
            return sum(1 for c in chars if get_ss(day_gan, c) in ss_names)
        BIGYEOP_SIKSANG = ['비견', '겁재', '식신', '상관']
        GWAN_IN = ['정관', '편관', '편인', '정인']
        if _ss_count(m_g[2], m_g + m_j, BIGYEOP_SIKSANG) >= 5 and _ss_count(m_g[2], m_g + m_j, GWAN_IN) == 0: s4 -= 1
        if _ss_count(f_g[2], f_g + f_j, BIGYEOP_SIKSANG) >= 5 and _ss_count(f_g[2], f_g + f_j, GWAN_IN) == 0: s4 -= 1

        s4 = max(0, min(10, s4))
        p4 = int((s4 / 10) * 100)

        # 🌟 대운 기상도 조화: 두 사람의 현재 대운 지지 관계를 실제로 판정
        if self.m_dw_ji and self.f_dw_ji:
            dw_rel = self.get_ji_rel(self.m_dw_ji, self.f_dw_ji)
            if dw_rel == "육합": s5 = 10
            elif dw_rel in ["방합", "반합"]: s5 = 8
            elif dw_rel == "무": s5 = 6
            elif dw_rel in ["파", "해"]: s5 = 4
            elif dw_rel in ["형", "원진"]: s5 = 2
            elif dw_rel == "충": s5 = 1
            else: s5 = 6
        else:
            s5 = 6
        if self.dw_wave is not None:
            s5 = float(self.dw_wave)   # 20~80대 인생 물결 비교 점수로 대체
        p5 = int(round((s5 / 10) * 100))

        # 🌟 각자의 배우자궁 점수 (두 분 점수의 합, 20점 만점)
        m_sp = self.get_spouse_palace_score(m_g, m_j, "남성")
        f_sp = self.get_spouse_palace_score(f_g, f_j, "여성")
        s0 = m_sp + f_sp
        p0 = int(round(s0 / 20 * 100))

        # 기본 15 + 배우자궁 20 + 일지 25 + 환경 15 + 보완 10 + 특수 기운 5 + 대운 10 = 100
        BASE = 20
        sub_total = BASE + s0 + s1 + s2 + s3 + (s4 * 0.5) + s5
        self.final_score = max(40, min(100, int(sub_total)))

        if self.final_score >= 90: self.grade = "천생연분 (최고의 인연)"
        elif self.final_score >= 85: self.grade = "상생연분 (함께하면 좋은 인연)"
        elif self.final_score >= 80: self.grade = "동행연분 (편안하고 안정적인 인연)"
        elif self.final_score >= 70: self.grade = "보완연분 (서로를 채워주는 인연)"
        elif self.final_score >= 60: self.grade = "성장연분 (이해하며 맞춰가는 인연)"
        else: self.grade = "조율연분 (인내와 배려가 필요한 인연)"

        self.details = [
            {"label": "사주팔자 분석", "pct": p0, "color": "#e67e22"},
            {"label": "내면의 유대감", "pct": p1, "color": "#9b59b6"},
            {"label": "환경 조화", "pct": p2, "color": "#2ecc71"},
            {"label": "기운 상호보완", "pct": p3, "color": "#3498db"},
            {"label": "인생 흐름의 조화", "pct": p5, "color": "#8e44ad"},
            {"label": "특수 기운", "pct": p4, "color": "#f1c40f"}
        ]


def get_gunghap_harmony_facts(gh_engine):
    """궁합 점수 엔진의 6대 조화도(%)와 종합점수를 AI 용 팩트 문자열로 만듭니다. (harmony_index_facts)"""
    try:
        det = " / ".join(f"{d['label']} {d['pct']}%" for d in gh_engine.details)
        return f"궁합 종합 {gh_engine.final_score}점({gh_engine.grade}) — 조화도: {det}"
    except Exception:
        return "궁합 조화도 산출 정보 없음"


def get_gunghap_risk_facts(gh_engine):
    """두 사람 각자의 일주 흉살, 음양 치우침, 재성·관살 혼잡, 비겁·식상 폭주를 AI 용 팩트 문자열로 만듭니다. (shinsal_risk_facts)"""
    try:
        RISK = ["간여지동", "고란살", "구추방해", "백호대살", "신병", "음욕살", "의처의부", "홍염살", "괴강살", "양인살", "남연살", "여연살"]
        def _tags(g, j, gender):
            g = [_to_hanja(x) for x in g]
            j = [_to_hanja_ji(x) for x in j]
            lst = get_general_shinsal_filtered(1, [g[3], g[2], g[1], g[0]], [j[3], j[2], j[1], j[0]], gender)
            return [re.sub(r"<[^>]+>", "", x).strip() for x in lst]
        def _person(label, g, j, gender):
            g = [_to_hanja(x) for x in g]
            j = [_to_hanja_ji(x) for x in j]
            items = []
            ev = _tags(g, j, gender)
            hit = [t for t in ev if any(r[:2] in t for r in RISK)]
            if hit: items.append("일주의 주의 신살 — " + ", ".join(dict.fromkeys(hit)))
            yang = set("甲丙戊庚壬子寅辰午申戌")
            chars = [_to_hanja(c) for c in (g + j)]
            yc = sum(1 for c in chars if c in yang)
            if yc >= 7: items.append("양의 기운이 지나치게 치우침")
            elif yc <= 1: items.append("음의 기운이 지나치게 치우침")
            ss_list = [get_ss(g[2], c) for c in (g + j)]
            if gender == "남성" and "정재" in ss_list and "편재" in ss_list: items.append("재성 혼잡(정재·편재가 함께 있음)")
            if gender == "여성" and "정관" in ss_list and "편관" in ss_list: items.append("관살 혼잡(정관·편관이 함께 있음)")
            grp = [get_group_ss(s) for s in ss_list]
            if sum(1 for x in grp if x in ("비겁", "식상")) >= 5 and not any(x in ("관성", "인성") for x in grp):
                items.append("비겁·식상이 지나치게 많고 관성·인성의 브레이크가 없음")
            return f"{label}: " + ("; ".join(items) if items else "특별히 두드러진 위험 신살 없음")
        m = _person(f"남명({gh_engine.app})", gh_engine.m_g, gh_engine.m_j, "남성")
        f = _person(f"여명({gh_engine.p_name})", gh_engine.f_g, gh_engine.f_j, "여성")
        return m + " || " + f
    except Exception as e:
        return "신살 위험 요소 산출 정보 없음"


# ---- 4-B. [3-2 결혼 택일] : 전용 계산 함수 없음 (주간 달력 get_weekly_calendar_data 사용) ----


# ---- 4-C. [3-3 출산 택일] 아기 완성 사주 채점 → 추천일 TOP5 → AI 팩트 문자열 ----

# ── 합궁·분만 시기 의학 기준 (필요하면 이 숫자만 바꾸면 됩니다) ──
_FERTILE_DAYS_BEFORE_OVULATION = 5    # 정자는 몸 안에서 보통 3일·최대 5일 생존 → 배란 5일 전부터 임신 가능 (Wilcox 등, NEJM 1995: 임신은 배란일로 끝나는 6일 안에서만 발생, 확률 5일 전 10% → 배란 당일 33%)
_FERTILE_DAYS_AFTER_OVULATION = 1     # 난자는 배란 후 12~24시간 생존 + 달력 계산의 오차 여유 → 가임기간 = 배란 5일 전 ~ 배란 다음 날(7일)
_DELIVERY_AFTER_OVULATION_MIN = 259   # 임신 39주 0일 (배란일 + 259일) : 계획 분만(제왕절개·유도)은 보통 39주 이후
_DELIVERY_AFTER_OVULATION_MAX = 273   # 임신 41주 0일 (배란일 + 273일)

_DELIVERY_TIME_SLOTS = [
    {'time_str': '00:30 ~ 01:29 (조자)시', 'ji': '子', 'hm': (1, 0),  'daytime': False},
    {'time_str': '01:30 ~ 03:29 (축)시',   'ji': '丑', 'hm': (2, 30), 'daytime': False},
    {'time_str': '03:30 ~ 05:29 (인)시',   'ji': '寅', 'hm': (4, 30), 'daytime': False},
    {'time_str': '05:30 ~ 07:29 (묘)시',   'ji': '卯', 'hm': (6, 30), 'daytime': False},
    {'time_str': '07:30 ~ 09:29 (진)시',   'ji': '辰', 'hm': (8, 30), 'daytime': False},
    {'time_str': '09:30 ~ 11:29 (사)시',   'ji': '巳', 'hm': (10, 30), 'daytime': True},
    {'time_str': '11:30 ~ 13:29 (오)시',   'ji': '午', 'hm': (12, 30), 'daytime': True},
    {'time_str': '13:30 ~ 15:29 (미)시',   'ji': '未', 'hm': (14, 30), 'daytime': True},
    {'time_str': '15:30 ~ 17:29 (신)시',   'ji': '申', 'hm': (16, 30), 'daytime': True},
    {'time_str': '17:30 ~ 19:29 (유)시',   'ji': '酉', 'hm': (18, 30), 'daytime': False},
    {'time_str': '19:30 ~ 21:29 (술)시',   'ji': '戌', 'hm': (20, 30), 'daytime': False},
    {'time_str': '21:30 ~ 23:29 (해)시',   'ji': '亥', 'hm': (22, 30), 'daytime': False},
]

# 지지 관계 가감점 표 (일지끼리 / 띠끼리 / 시지·월지 대 부모 일지)
_REL_SCORE_ILJI = {'충': -8, '형': -5, '원진': -4, '파': -2, '해': -2, '자형': -2, '육합': 5, '반합': 3, '방합': 1.5}

_REL_SCORE_TTI  = {'충': -6, '형': -3, '원진': -3, '파': -1.5, '해': -1.5, '자형': -1, '육합': 4, '반합': 3, '방합': 1}

_REL_SCORE_SIJI = {'충': -4, '형': -3, '원진': -2, '파': -1, '해': -1, '자형': -1, '육합': 3, '반합': 2, '방합': 1}

_REL_SCORE_WOLJI = {'충': -4, '형': -2, '원진': -1.5, '파': -1, '해': -1, '자형': -1, '육합': 2, '반합': 1.5, '방합': 0.5}

# 아기 사주 내부 지지끼리 (충·형이 크게 감점)
_REL_SCORE_INNER = {'충': -7, '형': -4, '원진': -3, '파': -2, '해': -2, '자형': -1.5, '귀문': -1, '육합': 4, '반합': 3, '방합': 1.5, '암합': 1}

# 출산 시점 부모의 대운 지지 ↔ 아기 일지·월지
_REL_SCORE_DW = {'충': -5, '형': -3, '원진': -2, '파': -1, '해': -1, '자형': -1, '육합': 3, '반합': 2, '방합': 1}

_CHEONEUL_MAP = {'甲':'未丑','乙':'申子','丙':'酉亥','丁':'酉亥','戊':'未丑','己':'申子','庚':'未丑','辛':'午寅','壬':'卯巳','癸':'卯巳'}

_MUNCHANG_MAP = {'甲':'巳','乙':'午','丙':'申','丁':'酉','戊':'申','己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'}

_GEONROK_MAP  = {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}

_SIPAK_DAEPAE = ["甲辰", "乙巳", "丙申", "丁亥", "戊戌", "己丑", "庚辰", "辛巳", "壬申", "癸亥"]
_GWIMUN_PAIRS = {frozenset(p) for p in ('子酉', '丑午', '寅未', '卯申', '辰亥', '巳戌')}   # 귀문관살
_AMHAP_PAIRS = {frozenset(p) for p in ('寅丑', '午亥', '卯申', '子戌', '寅未')}
_INNER_PAIR_W = {(0, 1): 0.6, (0, 2): 0.8, (0, 3): 0.5, (1, 2): 1.0, (1, 3): 0.7, (2, 3): 0.9}   # 쌍별 비중 (월-일이 가장 큼)
_INNER_PAIR_NM = {(0, 1): '년지와 월지', (0, 2): '년지와 일지', (0, 3): '년지와 시지', (1, 2): '월지와 일지', (1, 3): '월지와 시지', (2, 3): '일지와 시지'}

def _delivery_hour_pillar(day_gan, hour_ji):
    """일간과 시지로 시주(時柱) 간지를 만듭니다. (갑기일=갑자시 시작 ... 오둔법)"""
    start_idx = {"甲":0, "己":0, "乙":2, "庚":2, "丙":4, "辛":4, "丁":6, "壬":6, "戊":8, "癸":8}.get(day_gan, 0)
    return GAN[(start_idx + JI.index(hour_ji)) % 10] + hour_ji

def _delivery_rel_tags(a, b):
    """두 지지의 관계를 태그 리스트로 반환 (같은 글자는 'same')"""
    a, b = _to_hanja(a), _to_hanja(b)
    if not a or not b: return []
    if a == b:
        return ['자형'] if a in "辰午酉亥" else ['same']
    r = get_ji_rel_set(a, b)
    return [] if r == "-" else [x.strip().replace("방합(미완)", "방합") for x in r.split(",")]

def _delivery_rel_effect(a, b, table, same_bonus=1.0):
    tags = _delivery_rel_tags(a, b)
    eff = 0.0
    for t in tags:
        if t == 'same': eff += same_bonus
        else: eff += table.get(t, 0.0)
    return eff, tags

def _delivery_count_oh(chars):
    cnt = {'목': 0, '화': 0, '토': 0, '금': 0, '수': 0}
    for c in chars:
        o = get_color(c)
        if o in cnt: cnt[o] += 1
    return cnt

def _delivery_parent_info(pack):
    """부모 한 명의 [시주, 일주, 월주, 년주] 리스트에서 필요한 지지·오행 정보를 뽑습니다."""
    pack = [str(p).strip() if p else "" for p in (list(pack) + ["", "", "", ""])[:4]]
    def ji(i): return pack[i][1] if len(pack[i]) >= 2 and pack[i][1] in JI else ""
    def gan(i): return pack[i][0] if len(pack[i]) >= 2 and pack[i][0] in GAN else ""
    chars = [c for c in ([gan(i) for i in range(4)] + [ji(i) for i in range(4)]) if c]
    return {
        'hour_ji': ji(0), 'day_ji': ji(1), 'month_ji': ji(2), 'year_ji': ji(3),
        'cnt': _delivery_count_oh(chars),
    }

# ── 출산택일 배점표 (합계 100점) : 일간을 기준으로 7글자를 궁위별로 평가합니다 ──
# 글자 7개(일지>월지>시지>월간>년지>시간>년간) 70 + 오행·조후·공망 10 + 대운 흐름 10 + 부모 조화 10(보조)
# 박사님이 숫자만 바꾸시면 됩니다 (아래 12개를 모두 더해 100이 되게 맞추세요)
_W_ILJI, _W_WOLJI, _W_SIJI = 30, 15, 9              # 지지 3개
_W_WOLGAN, _W_NYEONJI, _W_SIGAN, _W_NYEONGAN = 6, 5, 3, 2   # 월간 / 년지 / 시간 / 년간
_W_OHAENG, _W_JOHU, _W_GONGMANG = 4, 4, 2          # 오행 균형 / 조후(8글자 한난 균형) / 공망(해공 반영)
_W_DAEWUN = 10                                      # 대운 흐름
_W_PARENT = 10                                      # 부모와의 조화(보조 기준)

_UNSUNG_POWER = {'건록': 1.0, '제왕': 1.0, '관대': 0.8, '장생': 0.8, '목욕': 0.5, '쇠': 0.5, '양': 0.5,
                 '병': 0.3, '태': 0.3, '사': 0.1, '묘': 0.1, '절': 0.1}
_SS_GROUP = {'비견': '비겁', '겁재': '비겁', '식신': '식상', '상관': '식상', '편재': '재성', '정재': '재성',
             '편관': '관성', '정관': '관성', '편인': '인성', '정인': '인성'}
_SS_SUNYONG = ('정인', '식신', '정재', '편재', '정관')          # 財官印食 = 순용(자평진전)
_SS_JEHWA = {'편관': ('식신', '편인', '정인'), '상관': ('정인', '편인', '정재', '편재'), '겁재': ('정관', '편관'),
             '편인': ('편재',)}                                  # 殺傷梟刃 = 역용, 제화(다스림)되는 조건
_SS_QUALITY = {'정인': 1.0, '식신': 1.0, '정재': 1.0, '편재': 1.0, '정관': 1.0, '비견': 0.6,
               '편인': 0.4, '편관': 0.4, '상관': 0.35, '겁재': 0.35}   # 각 궁위에 놓인 십성의 길흉(일반 기준)
_SHIN12_SCORE = {'장성살': 1.0, '반안살': 1.0, '화개살': 0.7, '지살': 0.6, '역마살': 0.6, '년살': 0.5,
                 '천살': 0.4, '월살': 0.3, '육해살': 0.3, '망신살': 0.2, '겁살': 0.2, '재살': 0.2}   # 12신살의 길흉(기본값)
_YANGIN_MAP = {'甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子'}
_WOLDEOK_MAP = {'寅': '丙', '午': '丙', '戌': '丙', '申': '壬', '子': '壬', '辰': '壬', '亥': '甲', '卯': '甲', '未': '甲', '巳': '庚', '酉': '庚', '丑': '庚'}
# 월간(60월령) 적합도 규칙 — 계절별 월간 오행의 한난값
_WOLGAN_WINTER = {'화': 1.0, '토': 0.8, '목': 0.5, '금': 0.2, '수': 0.2}    # 동절기(해자축인월)
_WOLGAN_SUMMER = {'수': 1.0, '금': 0.7, '토': 0.4, '목': 0.3, '화': 0.0}   # 하절기(사오미월)
_OH_TEMP = {'화': 2, '목': 1, '토': 0, '금': -1, '수': -2}                         # 조후: 오행별 온도
_SAMHAP_GROUPS = ('申子辰', '亥卯未', '寅午戌', '巳酉丑')
_GONGMANG_BASE = {'월지': 1.2, '시지': 0.5, '년지': 0.3}                     # 공망이 걸린 곳별 감점(합 2.0 = 공망 만점)
_HAEGONG_FACTOR = {'충': 0.0, '삼합': 0.0, '육합': 0.5}                      # 해공 시 남는 감점 비율 (0 = 완전 해공)


def _delivery_clamp01(x):
    return max(0.0, min(1.0, x))


def _jo(word, with_batchim, without_batchim):
    """단어 끝 글자에 받침이 있으면 첫 번째, 없으면 두 번째 조사를 붙여 돌려줍니다. 예) _jo('편재', '이', '가') → '편재가'"""
    c = str(word)[-1:]
    has = bool(c) and '가' <= c <= '힣' and (ord(c) - 0xAC00) % 28 != 0
    return f"{word}{with_batchim if has else without_batchim}"


def _wolgan_tugan(mg, mj):
    """월간이 월지 지장간과 얼마나 같은가(투간): 본기 1.0·중기 0.8·여기 0.6, 음양만 다른 같은 오행 0.6·0.5·0.4"""
    j = JIJANGGAN.get(mj, [])
    pos = []
    if j:
        pos.append(('본', j[-1]))
        if len(j) == 3: pos.append(('중', j[1]))
        if len(j) > 1: pos.append(('여', j[0]))
    for k, v in pos:
        if mg == v: return {'본': 1.0, '중': 0.8, '여': 0.6}[k]
    best = 0.0
    for k, v in pos:
        if v != '-' and get_color(mg) == get_color(v): best = max(best, {'본': 0.6, '중': 0.5, '여': 0.4}[k])
    return best


def _wolgan_fit(mg, mj):
    """월간의 월령 적합도(0~1). 동절기는 따뜻한 월간(火·土)이나 근원 투간, 하절기는 서늘한 월간(水·金)이나 근원 투간이 좋음"""
    t = _wolgan_tugan(mg, mj); o = get_color(mg)
    if mj in '亥子丑寅': return max(_WOLGAN_WINTER.get(o, 0.5), 0.9 * t)
    if mj in '巳午未': return max(_WOLGAN_SUMMER.get(o, 0.5), t)
    return 0.6 + 0.4 * t


def _delivery_shin12(*bases_and_target):
    """12신살 길흉 점수(0~1)와 이름. 인자: (기준지지1, [기준지지2, ...], 대상지지) — 기준이 둘이면 평균."""
    *bases, target = bases_and_target
    vals, names = [], []
    for b in bases:
        try:
            nm = get_12_shinsal(b, target)
        except Exception:
            continue
        vals.append(_SHIN12_SCORE.get(nm, 0.5)); names.append(nm)
    return (sum(vals) / len(vals) if vals else 0.5), names


def _delivery_gui(dm, j, label, extra_pos=0.0):
    """한 지지(j)의 귀인·일반신살 점수(0~1)와 설명. (가점: 천을·문창·건록·학당 / 감점: 양인) ※ 공망은 별도 항목에서 봅니다"""
    pos, neg, good, warn = float(extra_pos), 0.0, [], []
    if j in _CHEONEUL_MAP.get(dm, ""): pos += 2; good.append(f"{label}에 천을귀인(귀인의 도움을 받는 기운)이 자리함")
    if j == _MUNCHANG_MAP.get(dm): pos += 2; good.append(f"{label}에 문창귀인(총명함과 학업 성취를 돕는 기운)이 자리함")
    if j == _GEONROK_MAP.get(dm): pos += 2; good.append(f"{label}에 건록(스스로 서는 든든한 힘)이 자리함")
    if get_unsung(dm, j) == '장생': pos += 2; good.append(f"{label}에 학당귀인(배움과 지혜를 돕는 기운)이 자리함")
    if j == _YANGIN_MAP.get(dm): neg += 2; warn.append(f"{label}에 양인(기운이 지나치게 강하고 날카로운 기운)이 있음")
    return _delivery_clamp01(0.5 + (pos - neg) / 6.0), good, warn


def _delivery_rel_frac(a, b):
    """두 지지의 충합 점수(0~1)와 설명 태그"""
    t = _delivery_rel_tags(a, b)
    if '충' in t: return 0.0, 'chung'
    if any(x in t for x in ('육합', '반합')): return 1.0, 'hap'
    if any(x in t for x in ('형', '원진', '해', '파')): return 0.3, 'bad'
    if '방합' in t: return 0.85, ''
    if 'same' in t: return 0.6, ''
    if '자형' in t: return 0.5, ''
    return 0.7, ''


def _delivery_gongmang(dm, dj, yj, mj, hj):
    """일주 기준 공망 점수(0~1)와 설명. 공망 지지가 충·합으로 풀리면(해공) 감점을 줄입니다."""
    gm = calculate_gongmang(dm, dj)
    good, warn = [], []
    if not gm or gm == "-":
        return 1.0, good, warn
    jis = {'년지': yj, '월지': mj, '일지': dj, '시지': hj}
    pen = 0.0
    for nm in ('월지', '시지', '년지'):
        x = jis[nm]
        if x not in gm:
            continue
        others = [v for k, v in jis.items() if k != nm]
        factor = 1.0
        if any('충' in _delivery_rel_tags(x, o) for o in others):
            factor = _HAEGONG_FACTOR['충']
        else:
            if any('육합' in _delivery_rel_tags(x, o) for o in others):
                factor = min(factor, _HAEGONG_FACTOR['육합'])
            for grp in _SAMHAP_GROUPS:
                if x in grp and all(c in others for c in grp if c != x):
                    factor = min(factor, _HAEGONG_FACTOR['삼합'])
        pen += _GONGMANG_BASE[nm] * factor
        if factor == 0.0: good.append(f"{nm}의 공망(비어 있는 자리)이 충·합으로 채워짐(해공)")
        elif factor < 1.0: warn.append(f"{nm}에 공망(비어 있는 자리)이 걸렸으나 합으로 일부 풀림")
        else: warn.append(f"{nm}에 공망(비어 있는 자리)이 걸림")
    return _delivery_clamp01(1.0 - pen / sum(_GONGMANG_BASE.values())), good, warn

def _delivery_inner_rel(jis):
    """아기 사주 지지 4개(년·월·일·시) 6쌍의 관계를 점수로 돌려줍니다. (월-일, 일-시 쌍의 합 가점은 일지 점수에 이미 있어 감점만 반영)"""
    pts, good, warn = 0.0, [], []
    for (i, j), w in _INNER_PAIR_W.items():
        a, b = jis[i], jis[j]
        tags = [t for t in _delivery_rel_tags(a, b) if t not in ('귀문', '암합')]
        pr = frozenset((a, b))
        if pr in _GWIMUN_PAIRS: tags.append('귀문')
        if pr in _AMHAP_PAIRS: tags.append('암합')
        e = 0.0
        for t in tags:
            e += -1.0 if t == 'same' else _REL_SCORE_INNER.get(t, 0.0)
        if (i, j) in ((1, 2), (2, 3)):
            e = min(e, 0.0)
        pts += e * w
        bad = [t for t in ('충', '형', '원진', '귀문', '파', '해') if t in tags]
        if bad: warn.append(f"{_INNER_PAIR_NM[(i, j)]} 사이에 {'·'.join(bad)} 관계가 있어 마찰의 기운이 있음")
        elif 'same' in tags: warn.append(f"{_INNER_PAIR_NM[(i, j)]}가 같은 글자({a})로 겹쳐 기운이 쏠림")
    return max(-12.0, min(3.0, pts)), good, warn

def _score_baby_chart(y_p, m_p, d_p, h_p, male_pack, female_pack, parent_dw=None):
    """아기 완성 사주(년·월·일·시)를 100점 만점으로 채점합니다. 일간을 기준으로 7글자를 궁위별로 평가합니다.
    반환: {'total': 합계, 'parts': {항목: 점수}, 'good': [...], 'warn': [...]}"""
    good, warn = [], []
    gans = [y_p[0], m_p[0], d_p[0], h_p[0]]
    jis = [y_p[1], m_p[1], d_p[1], h_p[1]]          # 년·월·일·시
    dm = d_p[0]
    yg, mg, hg = gans[0], gans[1], gans[3]
    yj, mj, dj, hj = jis
    cnt = _delivery_count_oh(gans + jis)

    # ═════════ 일지 (원안 35점 기준 세부 배점을 _W_ILJI 로 환산) ═════════
    un_d = get_unsung(dm, dj); zwa = _UNSUNG_POWER.get(un_d, 0.5)
    if zwa >= 0.8: good.append(f"일주의 일지에서 일간이 든든히 뿌리내림({un_d})")
    elif zwa <= 0.1: warn.append(f"일주의 일지에서 일간의 뿌리가 약함({un_d})")
    ss_d = get_ss(dm, dj); ilji_ss = _SS_QUALITY.get(ss_d, 0.5)
    if ilji_ss >= 1.0: good.append(f"일지에 {_jo(ss_d, '이', '가')} 자리해 배우자궁이 안정적")
    elif ilji_ss <= 0.4: warn.append(f"일지에 {_jo(ss_d, '이', '가')} 자리해 배우자궁에 주의가 필요함")
    sh_d, sh_names = _delivery_shin12(yj, dj)
    if sh_names and sh_names[0] in ('장성살', '반안살'): good.append(f"일지에 {sh_names[0]}(든든하고 안정된 기운)이 자리함")
    elif sh_names and sh_names[0] in ('망신살', '겁살', '재살'): warn.append(f"일지에 {sh_names[0]}(구설이나 손실에 유의할 기운)이 자리함")
    gui_d, g1, w1 = _delivery_gui(dm, dj, "일지"); good += g1; warn += w1
    flag = 1.0
    if d_p in _SIPAK_DAEPAE: flag = 0.0; warn.append("십악대패일에 해당하여 이 날은 피하는 것이 좋음")
    elif d_p in BAEKHO_GANJI: flag = 0.4; warn.append("백호대살 일주로 기운이 매우 거셈")
    elif d_p in GOEGANG_ILJU: flag = 0.5; warn.append("괴강 일주로 기운이 지나치게 강함")
    md, kmd = _delivery_rel_frac(mj, dj)
    if kmd == 'chung': warn.append("월지와 일지가 서로 충돌함")
    elif kmd == 'hap': good.append("월지와 일지가 서로 합하여 화합함")
    elif kmd == 'bad': warn.append("월지와 일지 사이에 마찰의 기운이 있음")
    dh, kdh = _delivery_rel_frac(dj, hj)
    if kdh == 'chung': warn.append("일지와 시지가 서로 충돌함")
    elif kdh == 'hap': good.append("일지와 시지가 서로 합하여 화합함")
    p_ilji = (_W_ILJI / 35.0) * (11 * zwa + 9 * ilji_ss + 7 * 4 / 9 * sh_d + 7 * 5 / 9 * gui_d + 3 * flag + 3.5 * md + 1.5 * dh)

    # ═════════ 월지 (원안 17점 기준) ═════════
    un_m = get_unsung(dm, mj); deuk = _UNSUNG_POWER.get(un_m, 0.5)
    if deuk >= 0.8: good.append(f"월령(태어난 달)에서 일간이 힘을 얻는 득령({un_m})")
    elif deuk <= 0.1: warn.append(f"월령(태어난 달)에서 일간의 힘이 약한 자리({un_m})")
    ss_m = get_ss(dm, mj)
    others_ss = [get_ss(dm, c) for c in (yg, mg, hg, yj, dj, hj)]
    if ss_m in _SS_SUNYONG:
        gyeok = 1.0; good.append(f"월지가 {_jo(ss_m, '이라', '라')} 격이 순하게 풀리는 순용격")
    elif ss_m == '비견':
        gyeok = 0.6
    elif ss_m in _SS_JEHWA:
        if any(x in others_ss for x in _SS_JEHWA[ss_m]):
            gyeok = 0.75; good.append(f"월지 {ss_m}의 거친 기운을 다스리는 짝(제화)이 사주 안에 있음")
        else:
            gyeok = 0.25; warn.append(f"월지 {ss_m}의 거친 기운을 다스릴 짝(제화)이 사주 안에 없음")
    else:
        gyeok = 0.5
    if ss_m in [get_ss(dm, g) for g in (yg, mg, hg)]:
        gyeok = min(1.0, gyeok + 0.1)       # 월지의 십성이 천간에 드러남(투출)
    sh_m, _n = _delivery_shin12(yj, dj, mj)
    gui_m, g2, w2 = _delivery_gui(dm, mj, "월지", extra_pos=2.0 if _WOLDEOK_MAP.get(mj) in gans else 0.0)
    if _WOLDEOK_MAP.get(mj) in gans: good.append("월덕귀인(조상의 덕과 복을 받는 기운)이 천간에 드러남")
    good += g2; warn += w2
    p_wolji = (_W_WOLJI / 17.0) * (7 * deuk + 7 * gyeok + 1.5 * sh_m + 1.5 * gui_m)

    # ═════════ 시지 (원안 10점 기준) ═════════
    un_h = get_unsung(dm, hj); pw_h = _UNSUNG_POWER.get(un_h, 0.5)
    if pw_h >= 0.8: good.append(f"시주(자녀궁·말년)에서 일간이 힘을 얻음({un_h})")
    q_hj = _SS_QUALITY.get(get_ss(dm, hj), 0.5)
    sh_h, _n = _delivery_shin12(yj, dj, hj)
    gui_h, g3, w3 = _delivery_gui(dm, hj, "시지"); good += g3; warn += w3
    p_siji = (_W_SIJI / 10.0) * (4 * pw_h + 4 * q_hj + 1 * sh_h + 1 * gui_h)

    # ═════════ 월간 (월령 적합 4 + 십성 2) ═════════
    fit_m = _wolgan_fit(mg, mj)
    q_mg = _SS_QUALITY.get(get_ss(dm, mg), 0.5)
    if fit_m >= 0.9: good.append(f"월간 {mg}이 월령({mj}월)에 꼭 맞는 기운(계절의 한난을 맞추거나 월지의 뿌리가 드러남)")
    elif fit_m <= 0.25: warn.append(f"월간 {mg}이 월령({mj}월)의 계절과 잘 맞지 않음")
    p_wolgan = (_W_WOLGAN / 6.0) * (4 * fit_m + 2 * q_mg)

    # ═════════ 년지 · 시간 · 년간 ═════════
    pw_y = _UNSUNG_POWER.get(get_unsung(dm, yj), 0.5)
    q_yj = _SS_QUALITY.get(get_ss(dm, yj), 0.5)
    gui_y, g4, w4 = _delivery_gui(dm, yj, "년지"); good += g4; warn += w4
    p_nyeonji = (_W_NYEONJI / 6.0) * (2 * pw_y + 2 * q_yj + 2 * gui_y)
    q_hg = _SS_QUALITY.get(get_ss(dm, hg), 0.5)
    root_h = _UNSUNG_POWER.get(get_unsung(hg, hj), 0.5)
    p_sigan = (_W_SIGAN / 4.0) * (2 * q_hg + 2 * root_h)
    q_yg = _SS_QUALITY.get(get_ss(dm, yg), 0.5)
    root_y = _UNSUNG_POWER.get(get_unsung(yg, yj), 0.5)
    p_nyeongan = (_W_NYEONGAN / 2.0) * (1 * q_yg + 1 * root_y)

    # ═════════ 오행 균형 · 조후(8글자 한난 균형) · 공망(해공) ═════════
    missing = sum(1 for v in cnt.values() if v == 0)
    bal = {0: 1.0, 1: 0.7, 2: 0.4}.get(missing, 0.1)
    mx = max(cnt.values())
    if mx >= 5: bal *= 0.4; warn.append("한 가지 오행이 5개 이상으로 지나치게 쏠림")
    elif mx == 4: bal *= 0.7
    if missing == 0: good.append("오행이 빠짐없이 고르게 갖춰짐")
    elif missing >= 3: warn.append("오행이 3가지 이상 비어 있어 한쪽으로 치우침")
    p_oh = _W_OHAENG * 0.5 * bal
    T = sum(_OH_TEMP.get(get_color(c), 0) for c in gans + jis)
    joh = _delivery_clamp01(1.0 - abs(T) / 8.0)
    if abs(T) <= 2: good.append("사주 전체의 차고 더움이 고르게 균형을 이룸")
    elif T <= -6: warn.append("사주 전체가 지나치게 차가운 쪽으로 치우침")
    elif T >= 6: warn.append("사주 전체가 지나치게 뜨거운 쪽으로 치우침")
    p_joh = _W_JOHU * 0.5 * joh
    gm_frac, g5, w5 = _delivery_gongmang(dm, dj, yj, mj, hj); good += g5; warn += w5
    p_gm = _W_GONGMANG * gm_frac

    # ═════════ 신강신약(4점): 월지>일지>시지·월간>년지·시간>년간 힘 배점, 신약이면 인성 받침 우대 ═════════
    _W7 = [(yg, 0.8), (mg, 1.2), (hg, 1.0), (yj, 1.0), (mj, 3.0), (dj, 1.5), (hj, 1.2)]
    _tot7 = sum(w for _c, w in _W7)
    _help7 = sum(w for c, w in _W7 if get_ss(dm, c) in ('비견', '겁재', '정인', '편인'))
    _in7 = sum(w for c, w in _W7 if get_ss(dm, c) in ('정인', '편인'))
    ratio = _help7 / _tot7
    in_share = _in7 / _tot7
    bal_s = max(0.0, 1.0 - abs(ratio - 0.5) / 0.5)
    if ratio >= 0.55:
        gangyak = '신강'; g_s = bal_s
        if ratio >= 0.70: warn.append("일간의 힘이 지나치게 강해 기운이 넘침(극신강)")
    elif ratio <= 0.45:
        gangyak = '신약'; g_s = 0.5 * bal_s + 0.5 * _delivery_clamp01(in_share / 0.25)
        if in_share >= 0.2: good.append("일간이 다소 여리지만 인성(어머니 같은 보살핌의 기운)이 든든히 받쳐 줌")
        else: warn.append("일간이 여린데 받쳐 줄 인성(보살핌의 기운)이 부족함")
    else:
        gangyak = '중화'; g_s = 1.0
        good.append("일간의 힘이 지나치지도 모자라지도 않은 중화")
    p_gy = 4.0 * g_s

    # ═════════ 부모와의 조화 (보조) ═════════
    parents = [('아버지', _delivery_parent_info(male_pack)), ('어머니', _delivery_parent_info(female_pack))]
    par_sum = 0.0
    for who, p in parents:
        if p['day_ji']:
            eff, tags = _delivery_rel_effect(dj, p['day_ji'], _REL_SCORE_ILJI, same_bonus=1.0)
            par_sum += eff
            if '충' in tags: warn.append(f"아기 일지가 {who} 일지와 충돌함")
            elif '육합' in tags or '반합' in tags: good.append(f"아기 일지가 {who} 일지와 합하여 정이 깊음")
            par_sum += _delivery_rel_effect(hj, p['day_ji'], _REL_SCORE_SIJI)[0]
            par_sum += _delivery_rel_effect(mj, p['day_ji'], _REL_SCORE_WOLJI)[0]
        if p['year_ji']:
            eff, tags = _delivery_rel_effect(yj, p['year_ji'], _REL_SCORE_TTI, same_bonus=0.5)
            par_sum += eff
            if '충' in tags: warn.append(f"아기 띠가 {who} 띠와 서로 충돌함")
            elif '육합' in tags or '반합' in tags: good.append(f"아기 띠가 {who} 띠와 잘 어울림")
    par_sum = max(-25.0, min(16.0, par_sum))
    lack_w = {k: 0 for k in cnt}; excess_w = {k: 0 for k in cnt}
    for _who, p in parents:
        for k, v in p['cnt'].items():
            if v == 0: lack_w[k] += 1
            if v >= 4: excess_w[k] += 1
    fill = 0.0
    for k in cnt:
        if lack_w[k] and cnt[k] >= 1: fill += 2.0 * lack_w[k]; good.append(f"부모에게 부족한 {k}(오행) 기운을 채워줌")
        if excess_w[k] and cnt[k] >= 3: fill -= 2.0 * excess_w[k]; warn.append(f"부모에게 이미 넘치는 {k}(오행) 기운이 더 쌓임")
    fill = max(-4.0, min(6.0, fill))
    dw_sum = 0.0
    for who, dji in (parent_dw or {}).items():
        if not dji: continue
        e1, t1 = _delivery_rel_effect(dj, dji, _REL_SCORE_DW, same_bonus=0.5)
        e2, _t2 = _delivery_rel_effect(mj, dji, _REL_SCORE_DW, same_bonus=0.0)
        dw_sum += e1 + 0.5 * e2
        if '충' in t1: warn.append(f"출산 시점 {who}의 대운({dji})이 아기 일지와 충돌함")
        elif '육합' in t1 or '반합' in t1: good.append(f"출산 시점 {who}의 대운({dji})이 아기 일지와 합하여 힘이 됨")
    dw_sum = max(-10.0, min(6.0, dw_sum))
    p_par = _W_PARENT * _delivery_clamp01(0.6 + (par_sum + fill + dw_sum) / 40.0)

    parts = {'일지': round(p_ilji, 1), '월지': round(p_wolji, 1), '시지': round(p_siji, 1), '월간': round(p_wolgan, 1),
             '년지': round(p_nyeonji, 1), '시간': round(p_sigan, 1), '년간': round(p_nyeongan, 1),
             '오행': round(p_oh, 1), '조후': round(p_joh, 1), '공망': round(p_gm, 1), '부모조화': round(p_par, 1)}

    # ═════════ 복음(같은 간지 기둥이 겹침) 감점: 겹친 쌍마다 -3점, 최대 -6점 ═════════
    _p4 = [y_p, m_p, d_p, h_p]
    _pairs = sum(1 for i in range(4) for j in range(i + 1, 4) if _p4[i] == _p4[j])
    fukeum = -min(_pairs, 2) * 3.0
    if _pairs:
        _dup = [p for p in dict.fromkeys(_p4) if _p4.count(p) >= 2]
        warn.append(f"{', '.join(_dup)} 같은 기둥이 겹쳐(복음) 기운이 한쪽으로 쏠리고 답답해질 수 있음")
    parts['복음'] = fukeum
    parts['신강신약'] = round(p_gy, 1)
    total = round(p_ilji + p_wolji + p_siji + p_wolgan + p_nyeonji + p_sigan + p_nyeongan + p_oh + p_joh + p_gm + p_par + p_gy + fukeum, 1)

    # ═════════ 지지 6쌍 관계(원진·귀문·암합 등) + 월주·시주의 백호·괴강 ═════════
    inner_pts, g_in, w_in = _delivery_inner_rel(jis)
    sin_pen, w_sin = 0.0, []
    for _nm, _pp in (('월주', m_p), ('시주', h_p)):
        if _pp in BAEKHO_GANJI: sin_pen -= 1.0; w_sin.append(f"{_nm}가 백호대살({_pp})로 기운이 매우 거셈")
        elif _pp in GOEGANG_ILJU: sin_pen -= 1.0; w_sin.append(f"{_nm}가 괴강({_pp})으로 기운이 지나치게 강함")
    parts['지지관계'] = round(inner_pts, 1)
    parts['신살'] = round(sin_pen, 1)
    total = round(total + inner_pts + sin_pen, 1)
    good += g_in
    warn[0:0] = w_in + w_sin      # 심각한 유의점이 AI에게 먼저 전달되도록 맨 앞에 넣음
    return {'total': total, 'parts': parts, 'gangyak': gangyak, 'good': list(dict.fromkeys(good)), 'warn': list(dict.fromkeys(warn))}

def evaluate_baby_chart(y_p, m_p, d_p, h_p, male_pack, female_pack, parent_dw=None):
    """(예전 호출 방식 호환) 합계 점수와 장점·유의점 목록만 돌려줍니다."""
    r = _score_baby_chart(y_p, m_p, d_p, h_p, male_pack, female_pack, parent_dw)
    return r['total'], r['good'], r['warn']

def _delivery_slot_charts(delivery_date):
    """해당 날짜의 12개 시간대별 아기 사주(년·월·일·시)를 만듭니다. (년·월주는 절기 기준)"""
    _, _, d_p = get_ganji_from_date(delivery_date.year, delivery_date.month, delivery_date.day)
    if not d_p or d_p[0] == "?":
        return []
    charts = []
    for slot in _DELIVERY_TIME_SLOTS:
        hh, mm = slot['hm']
        y_p, m_p, _lon = get_true_year_month_pillar(delivery_date.year, delivery_date.month, delivery_date.day, hh, mm)
        h_p = _delivery_hour_pillar(d_p[0], slot['ji'])
        charts.append((slot, y_p, m_p, d_p, h_p))
    return charts

def _delivery_parent_dw_at(parent_dw_info, delivery_dt):
    """출산일(세는 나이 기준) 시점의 부모 각자의 대운을 찾습니다.
    parent_dw_info = {'아버지': {'birth_year': 1993, 'dw': [{'age_range': '6~15세', 'c_hanja': '丁', 'j_hanja': '巳'}, ...]}, '어머니': {...}}"""
    out = {}
    for who, info in (parent_dw_info or {}).items():
        try:
            age = delivery_dt.year - int(info['birth_year']) + 1
            for dw in info['dw']:
                start = int(str(dw['age_range']).split('~')[0])
                if start <= age < start + 10:
                    out[who] = {'ji': dw['j_hanja'], 'gz': dw['c_hanja'] + dw['j_hanja'], 'age': age, 'range': dw['age_range']}
                    break
        except Exception:
            continue
    return out


def get_all_time_scores_for_date(delivery_date, male_pack, female_pack, parent_dw=None):
    """한 날짜의 12개 시간대를 각각 완성 사주로 채점하여 높은 순으로 반환합니다."""
    evaluated = []
    for slot, y_p, m_p, d_p, h_p in _delivery_slot_charts(delivery_date):
        _r = _score_baby_chart(y_p, m_p, d_p, h_p, male_pack, female_pack, parent_dw)
        sc, good, warn = _r['total'], _r['good'], _r['warn']
        evaluated.append({
            'time_str': slot['time_str'], 'ji': slot['ji'], 'score': sc, 'daytime': slot['daytime'], 'parts': _r['parts'],
            'pillars': f"{y_p}년 {m_p}월 {d_p}일 {h_p}시", 'time_pillar': h_p, 'year_pillar': y_p,
            'chart': (y_p, m_p, d_p, h_p), 'hm': slot['hm'],
            'good': good, 'warn': warn,
        })
    evaluated.sort(key=lambda x: x['score'], reverse=True)
    return evaluated

def get_optimized_delivery_days(start_date, end_date, male_pack, female_pack, last_period_date=None, period_cycle=30, top_n=5, min_gap_days=21, parent_dw_info=None, baby_gender='미정', delivery_mode='미정', csection_ji='巳午未申'):
    """
    출산 희망 기간(start_date~end_date) 안에서 명리적으로 가장 좋은 출산일·시간 TOP N을 찾습니다.
    - male_pack / female_pack : [시주, 일주, 월주, 년주] 순서의 간지 리스트 (예: ["壬子","戊寅","庚申","癸酉"])
    - last_period_date / period_cycle : 마지막 생리 시작일과 주기가 있으면, 배란 예정일에서 계산한
      현실적인 출산 가능 범위(임신 39주 0일~41주 0일, 계획 분만 기준)에 드는 날짜만 후보로 삼고 합궁 가임기간도 계산합니다.
      (생리 시작일을 1일차로 세고, 배란 예정일 = 다음 생리 시작 14일 전. 주기를 더할 때마다 달력상 생리 시작일이 조금씩 앞당겨지는 것도 자동으로 반영됩니다.)
    - 날짜 순위는 (전체 최고 시간대 점수 + 낮 시간대 최고 점수)의 평균으로 정합니다. (제왕절개 가능 시간 반영)
    """
    today = dt_mod.date.today()
    cycle = int(period_cycle) if period_cycle else 30
    windows = []   # (출산 가능 시작일, 출산 가능 종료일, 배란예정일, 그 주기의 생리 시작일)
    if last_period_date:
        k = 0
        while k < 40:
            cyc_start = last_period_date + dt_mod.timedelta(days=k * cycle)
            ovul = cyc_start + dt_mod.timedelta(days=cycle - 14)
            if ovul >= today:   # 이미 지나간 배란기는 제외
                windows.append((ovul + dt_mod.timedelta(days=_DELIVERY_AFTER_OVULATION_MIN),
                                ovul + dt_mod.timedelta(days=_DELIVERY_AFTER_OVULATION_MAX), ovul, cyc_start))
            if ovul + dt_mod.timedelta(days=_DELIVERY_AFTER_OVULATION_MIN) > end_date:
                break
            k += 1
 
    candidates = []
    cur = start_date
    while cur <= end_date:
        ovul, cyc_start = None, None
        if windows:
            for w_s, w_e, o, c_s in windows:
                if w_s <= cur <= w_e:
                    ovul, cyc_start = o, c_s; break
            if ovul is None:
                cur += dt_mod.timedelta(days=1); continue
        else:
            ovul = cur - dt_mod.timedelta(days=266)
 
        pdw = _delivery_parent_dw_at(parent_dw_info, cur)
        slots = get_all_time_scores_for_date(cur, male_pack, female_pack, {w: v['ji'] for w, v in pdw.items()})
        if not slots:
            cur += dt_mod.timedelta(days=1); continue
        best_any = slots[0]
        day_slots = [s for s in slots if s['ji'] in csection_ji]
        best_day = day_slots[0] if day_slots else best_any
        main_slot = best_day if delivery_mode == '제왕절개' else best_any   # 제왕절개면 수술 가능 시간 안의 최고 시각이 대표
        if delivery_mode == '제왕절개':
            rank_score = round(best_day['score'], 1)
        elif delivery_mode == '자연·유도분만':
            rank_score = round(best_any['score'], 1)
        else:
            rank_score = round((best_any['score'] + best_day['score']) / 2.0, 1)
 
        y_p = main_slot['year_pillar']
        candidates.append({
            'date': cur.strftime("%Y-%m-%d"),
            'delivery_dt': cur,
            'weekday_kr': ['월', '화', '수', '목', '금', '토', '일'][cur.weekday()],
            'score': rank_score,
            'four_pillars': main_slot['pillars'],
            'best_time': {'time_str': main_slot['time_str'], 'time_pillar': main_slot['time_pillar'], 'ji': main_slot['ji'], 'score': main_slot['score']},
            'best_any_time': {'time_str': best_any['time_str'], 'time_pillar': best_any['time_pillar'], 'ji': best_any['ji'], 'score': best_any['score'], 'pillars': best_any['pillars'],
                              'good': best_any['good'], 'warn': best_any['warn']},
            'delivery_mode': delivery_mode,
            'best_day_time': {'time_str': best_day['time_str'], 'time_pillar': best_day['time_pillar'], 'ji': best_day['ji'], 'score': best_day['score'], 'pillars': best_day['pillars'],
                              'good': best_day['good'], 'warn': best_day['warn'], 'parts': best_day.get('parts', {}),
                              'same_as_best': (best_day is best_any), 'score_gap': round(best_any['score'] - best_day['score'], 1)},
            'good': best_any['good'], 'warn': best_any['warn'],
            'conception_date': (ovul - dt_mod.timedelta(days=1)).strftime("%Y-%m-%d"),   # 합궁 최적일 = 배란 예정 전날
            'conception_start': (ovul - dt_mod.timedelta(days=_FERTILE_DAYS_BEFORE_OVULATION)).strftime("%Y-%m-%d"),
            'conception_end': (ovul + dt_mod.timedelta(days=_FERTILE_DAYS_AFTER_OVULATION)).strftime("%Y-%m-%d"),   # 가임기간 끝 = 배란 다음 날
            'ovulation_date': ovul.strftime("%Y-%m-%d"),
            'cycle_start': cyc_start.strftime("%Y-%m-%d") if cyc_start else None,            # 임신이 시작되는 주기의 생리 시작일
            'period_end': (cyc_start + dt_mod.timedelta(days=6)).strftime("%Y-%m-%d") if cyc_start else None,  # 생리 약 1주일(7일간)
            'next_period': (cyc_start + dt_mod.timedelta(days=cycle)).strftime("%Y-%m-%d") if cyc_start else None,  # 그 주기의 다음 생리 예정일
            'daeun_dir': ({'남아': '순행', '여아': '역행'} if y_p[0] in "甲丙戊庚壬" else {'남아': '역행', '여아': '순행'}),
            'all_time_slots': slots,
            'parent_dw': pdw,
        })
        cur += dt_mod.timedelta(days=1)
 
    # ── 2단계: 1차 점수 상위 후보에만 아기 대운 흐름(5점)을 더해 최종 순위를 정함 ──
    def _apply_flow(item):
        sb = next((x for x in item['all_time_slots'] if x['time_str'] == item['best_time']['time_str']), None)
        if not sb:
            return False
        flows = {}
        for g, key in (('남아', '남성'), ('여아', '여성')):
            bd = get_baby_daewun_info(sb['chart'], item['delivery_dt'], sb['hm'], key)
            sc_, steps_ = _daewun_flow_score(bd['list'], direction=bd['dir'])
            flows[g] = {'score': sc_, 'steps': steps_, 'info': bd}
        use = [g for g in ('남아', '여아') if baby_gender in ('미정', g)] or ['남아', '여아']
        flow_pts = round(sum(flows[g]['score'] for g in use) / len(use), 2)
        item['score_stage1'] = item['score']
        item['flow'] = flows
        item['flow_pts'] = flow_pts
        item['score'] = round(item['score'] + flow_pts, 1)
        return True

    candidates.sort(key=lambda x: x['score'], reverse=True)
    head = [c for c in candidates[:30] if _apply_flow(c)]
    head.sort(key=lambda x: x['score'], reverse=True)
    picked = []
    for item in head:
        if not any(abs((item['delivery_dt'] - s['delivery_dt']).days) < min_gap_days for s in picked):
            picked.append(item)
            if len(picked) >= top_n:
                break
    if len(picked) < top_n:       # 상위 30개가 한 시기에 몰려 5개를 못 채우면, 다음 후보들에서 이어서 채움
        for item in candidates[30:150]:
            if any(abs((item['delivery_dt'] - s['delivery_dt']).days) < min_gap_days for s in picked):
                continue
            if _apply_flow(item):
                picked.append(item)
                if len(picked) >= top_n:
                    break
        picked.sort(key=lambda x: x['score'], reverse=True)
    # 뽑힌 날짜에만 아기 대운표 데이터(남아·여아)를 계산해 붙임
    for item in picked:
        slot_best = next((x for x in item['all_time_slots'] if x['time_str'] == item['best_time']['time_str']), None)
        if slot_best:
            item['chart'] = slot_best['chart']
            item['baby_daewun'] = {g: item['flow'][g]['info'] for g in ('남아', '여아')}
            item['score_detail'] = dict(slot_best.get('parts', {}), 대운흐름=item.get('flow_pts', 0.0))
            item['first_samjae'] = get_baby_first_samjae_text(item['delivery_dt'].year, slot_best['chart'][0][1])
    for item in picked:                      # 순위 결정이 끝난 뒤에 표시용 점수로 환산
        item['score_raw'] = item['score']
        disp, top = _score_display(item['score'])
        item['score'] = disp
        item['top_pct'] = top
    return picked

# ── 대운 흐름: 나이대별로 어떤 십성(그룹)의 대운이 어울리는가 (0~1, 박사님이 숫자만 고치시면 됩니다) ──
# 예) 10대는 학업의 인성, 30~50대 활동기에는 식상·재성·관성(식재관·식재·재관), 20대에는 인비식 구조 등을 높게 봅니다.
_DAEWUN_AGE_PREF = {
    15: {'인성': 1.0, '비겁': 0.7, '관성': 0.5, '식상': 0.4, '재성': 0.2},     # 10대
    25: {'식상': 0.9, '비겁': 0.8, '인성': 0.7, '재성': 0.6, '관성': 0.6},     # 20대
    35: {'식상': 1.0, '재성': 1.0, '관성': 0.8, '비겁': 0.6, '인성': 0.5},     # 30대 (활동기)
    45: {'재성': 1.0, '관성': 1.0, '식상': 0.8, '인성': 0.6, '비겁': 0.5},     # 40대 (활동기)
    55: {'관성': 1.0, '재성': 0.9, '인성': 0.8, '식상': 0.7, '비겁': 0.5},     # 50대
}

# 역행 대운 아기용 나이대별 표 — 처음엔 순행 표와 같은 숫자입니다. 박사님이 역행 인생 곡선에 맞게 고치시면 됩니다.
_DAEWUN_AGE_PREF_REV = {k: dict(v) for k, v in _DAEWUN_AGE_PREF.items()}
_DAEWUN_AGE_PREF_REV[15]['관성'] = 0.8   # 역행: 10대 관성도 괜찮다 (박사님 기준)
_REV_FLOW_FACTOR = 1.0   # 역행의 '상생 흐름 구조' 가점 비율 (1.0 = 순행과 같음, 0.5 = 절반)
_DAEWUN_UNSUNG_W = 0.2   # 대운 지지 12운성이 점수에 미치는 비율 (0 = 반영 안 함, 0.2 = 운성이 약하면 최대 약 20% 감점)

_DAEWUN_AGE_WEIGHT = {15: 0.15, 25: 0.20, 35: 0.25, 45: 0.25, 55: 0.15}       # 나이대별 비중 (합 1.0)
_DAEWUN_CYCLE = ('인성', '비겁', '식상', '재성', '관성')                          # 일간 기준 상생의 순환
_DAEWUN_SHORT = {'인성': '인', '비겁': '비', '식상': '식', '재성': '재', '관성': '관'}

_SCORE_DISPLAY = "both"     # "both" = 원점수 + 상위 % 함께 표시 / "percentile" = 백분위로 환산해 표시 / "raw" = 원점수만 표시
_SCORE_REF_Q = [50.54, 56.20, 57.45, 58.17, 58.78, 59.38, 59.76, 60.24, 60.63, 60.97, 61.25, 61.46, 61.67, 61.91, 62.16, 62.35, 62.58, 62.82, 63.14, 63.34, 63.59, 63.82, 64.02, 64.19, 64.39, 64.55, 64.70, 64.88, 65.00, 65.16, 65.31, 65.46, 65.61, 65.76, 65.92, 66.09, 66.19, 66.34, 66.51, 66.64, 66.80, 66.95, 67.10, 67.20, 67.33, 67.44, 67.55, 67.69, 67.83, 67.99, 68.14, 68.25, 68.35, 68.50, 68.63, 68.78, 68.94, 69.05, 69.15, 69.31, 69.46, 69.63, 69.75, 69.85, 70.01, 70.13, 70.22, 70.39, 70.53, 70.68, 70.83, 70.96, 71.09, 71.19, 71.41, 71.61, 71.76, 71.95, 72.16, 72.36, 72.56, 72.80, 73.06, 73.23, 73.45, 73.65, 73.98, 74.23, 74.51, 74.88, 75.11, 75.42, 75.88, 76.19, 76.69, 77.22, 77.87, 78.50, 79.91, 81.16, 85.93]   # 10년치 날짜 2,700개(부모·대운 무작위)의 일 단위 원점수 분포 (0~100 백분위)


def _score_display(raw):
    """원점수를 '전체 출생 시각 중 몇 %에 해당하는가'로 환산한 표시 점수와 상위 %를 돌려줍니다. (순위 정렬에는 쓰지 않음)"""
    q = _SCORE_REF_Q
    if _SCORE_DISPLAY not in ("percentile", "both") or not q or len(q) < 3:
        return raw, None
    if raw <= q[0]: p = 0.0
    elif raw >= q[-1]: p = 100.0
    else:
        k = max(i for i in range(len(q) - 1) if q[i] <= raw)
        span = q[k + 1] - q[k]
        p = k + ((raw - q[k]) / span if span > 0 else 0.0)
    if _SCORE_DISPLAY == "both":
        return raw, round(100.0 - p, 1)
    return round(p, 1), round(100.0 - p, 1)


def _daewun_flow_score(dw_list, chart=None, direction='순행'):
    """아기 대운(10~50대)이 나이대별로 얼마나 알맞은 십성(일간 기준)으로 흐르는지 0~_W_DAEWUN점으로 채점합니다.
    각 대운은 천간 0.6 + 지지 0.4 비율로 보며, 상생으로 이어지는 3단계 이상 구조(식재관·인비식·비식재 등)가 나타나면 가점하고 설명에 알려줍니다. 구조는 순행·역행 어느 방향이든 같게 인정합니다.
    반환: (점수, 시기별 설명 목록)"""
    def seg_at(age):
        for dw in dw_list:
            try:
                s0 = int(str(dw['age_range']).split('~')[0])
            except Exception:
                continue
            if s0 <= age < s0 + 10:
                return dw
        return None

    total, steps, seq = 0.0, [], []
    _prefs = _DAEWUN_AGE_PREF_REV if direction == '역행' else _DAEWUN_AGE_PREF
    for age, pref in _prefs.items():
        seg = seg_at(age)
        if not seg:
            total += _DAEWUN_AGE_WEIGHT[age] * 0.5
            continue
        gg, jg = _SS_GROUP.get(seg['ss_gan']), _SS_GROUP.get(seg['ss_ji'])
        _un = seg.get('un_sung', '')
        _unf = (1 - _DAEWUN_UNSUNG_W) + _DAEWUN_UNSUNG_W * _UNSUNG_POWER.get(_un, 0.5)   # 12운성(힘의 크기)
        q = 0.5 * pref.get(gg, 0.5) + 0.5 * pref.get(jg, 0.5) * _unf   # 폭포수: 전반기(천간) 5년 + 후반기(지지) 5년, 운성은 후반기에만 반영
        total += _DAEWUN_AGE_WEIGHT[age] * q
        seq.append((age, gg))
        label = "매우 알맞음" if q >= 0.85 else ("알맞음" if q >= 0.65 else ("보통" if q >= 0.45 else "아쉬운 편"))
        steps.append(f"{age // 10 * 10}대 {seg['c_hanja']}{seg['j_hanja']}({gg}/{jg}, 운성 {_un}) {label}")
    # 상생으로 이어지는 구조 찾기 — 같은 십성이 이어지는 것은 한 단계로 보고, 인→비→식→재→관 순서로 한 방향으로 이어지면 구조로 인정
    # 시간 순서가 거꾸로(관→재→식→비→인)여도 같은 구조로 인정합니다 (순행·역행은 방향일 뿐 길흉이 아니므로)
    def _distinct(run):
        out = []
        for _, g in run:
            if g and (not out or out[-1] != g):
                out.append(g)
        return out

    def _scan(step):
        best, best_n, i = [], 1, 0
        while i < len(seq):
            run, j = [seq[i]], i + 1
            while j < len(seq):
                prev_g, cur_g = run[-1][1], seq[j][1]
                nxt = _DAEWUN_CYCLE[(_DAEWUN_CYCLE.index(prev_g) + step) % 5] if prev_g in _DAEWUN_CYCLE else None
                if cur_g == prev_g or cur_g == nxt:
                    run.append(seq[j]); j += 1
                else:
                    break
            if len(_distinct(run)) > best_n:
                best, best_n = run, len(_distinct(run))
            i = max(j, i + 1)
        return best, best_n

    fwd, n_f = _scan(+1)
    rev, n_r = _scan(-1)
    best, best_n, reverse = (fwd, n_f, False) if n_f >= n_r else (rev, n_r, True)
    bonus = 0.0
    if best:
        names = [_DAEWUN_SHORT[g] for g in _distinct(best)]      # 시간 순서 그대로 표시
        label = "".join(names) + (" (역행: 거슬러 올라가는 흐름)" if reverse else " (순행: 순탄하게 이어지는 흐름)")
        steps.insert(0, f"흐름 구조: {label} ({best[0][0] // 10 * 10}대~{best[-1][0] // 10 * 10}대에 상생으로 이어짐)")
        if best_n >= 3:                                   # 인비식·식재관·비식재 등 3단계 이상 상생 구조는 가점 (단계당 5%, 최대 20%)
            bonus = min(0.2, 0.05 * (best_n - 1)) * (_REV_FLOW_FACTOR if reverse else 1.0)
    return round(min(1.0, total + bonus) * _W_DAEWUN, 2), steps


def get_baby_daewun_info(chart, delivery_dt, hm, gender):
    """아기 완성 사주 chart=(년주, 월주, 일주, 시주)로 성별(gender='남성'/'여성')별 대운표 데이터를 만듭니다.
    반환: {'dir': '순행'/'역행', 'calc_d': 대운수, 'list': [대운 10개 정보]} (list 형식은 html_views.generate_daewun_layout 과 동일)"""
    y_p, m_p, d_p, _h_p = chart
    ys, yb, ms, mb, ds, db = y_p[0], y_p[1], m_p[0], m_p[1], d_p[0], d_p[1]
    order_dir = 1 if (GAN.index(ys) % 2 == 0) == (gender == '남성') else -1
    base_dt = dt_mod.datetime(delivery_dt.year, delivery_dt.month, delivery_dt.day, hm[0], hm[1])
    adj_mins = get_total_time_adjustment(base_dt)
    utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
    calc_d = get_daeun_su_accurate(utc_dt, order_dir)
    c_idx, j_idx = GAN.index(ms), JI.index(mb)
    items = []
    for i in range(10):
        c = GAN[(c_idx + (i + 1) * order_dir) % 10]
        j = JI[(j_idx + (i + 1) * order_dir) % 12]
        val = i * 10 + calc_d
        items.append({
            "age_range": f"{val}~{val + 9}세", "ss_gan": get_ss(ds, c), "c_hanja": c, "c_hangul": c,
            "j_hanja": j, "j_hangul": j, "ss_ji": get_ss(ds, j), "un_sung": get_unsung(ds, j),
            "y_shinsal": get_12_shinsal(yb, j), "d_shinsal": get_12_shinsal(db, j),
            "is_current": False, "is_first": (i == 0),
        })
    return {'dir': "순행" if order_dir == 1 else "역행", 'calc_d': calc_d, 'list': items}


def get_baby_first_samjae_text(birth_year, year_ji):
    """아기가 태어난 다음 해부터 처음 만나는 삼재(3년)의 연도를 알려줍니다. 예) '2036~2038년'"""
    for k in range(1, 13):
        y = birth_year + k
        if get_samjae(year_ji, JI[(y - 1984) % 60 % 12]) != "해당 없음":
            return f"{y}~{y + 2}년"
    return "해당 없음"


def get_earliest_delivery_start(last_period_date, period_cycle=30, today=None):
    """마지막 생리 시작일과 주기로, 앞으로 올 가장 가까운 배란기에 임신했을 때의 가장 이른 출산 가능일(임신 39주 0일)을 돌려줍니다.
    신혼부부·임신을 준비하는 부부의 '탐색 시작일' 기본값으로 쓰입니다."""
    today = today or dt_mod.date.today()
    cycle = int(period_cycle) if period_cycle else 30
    for k in range(0, 40):
        ovul = last_period_date + dt_mod.timedelta(days=k * cycle + cycle - 14)
        if ovul >= today:                      # 이미 지나간 배란기는 제외 (get_optimized_delivery_days 와 같은 기준)
            return ovul + dt_mod.timedelta(days=_DELIVERY_AFTER_OVULATION_MIN)
    return today


def _delivery_conception_text(d):
    """가임기간(임신 가능성이 높은 시기)을 '그 달 생리 시작 예상 → 배란 예정 → 가임기간 → 다음 생리 예정일' 순서로 연도까지 풀어씁니다."""
    def ymd(s):
        return f"{int(s[:4])}년 {int(s[5:7])}월 {int(s[8:10])}일"
    base = (f"가임기간 {ymd(d['conception_start'])} ~ {ymd(d['conception_end'])} (배란 예정일 {ymd(d['ovulation_date'])}, "
            f"임신 가능성이 가장 높은 날 {ymd(d['conception_date'])})")
    if d.get('cycle_start'):
        nxt = f", 다음 생리 예정일 {ymd(d['next_period'])}의 약 2주 전" if d.get('next_period') else ""
        base = (f"그 주기의 생리 시작 예상 {ymd(d['cycle_start'])}(약 1주일간 {ymd(d['cycle_start'])}~{ymd(d['period_end'])}) → ") + base + nxt
    return base


def get_delivery_facts_str(best_days):
    """AI에게 넘길 '엔진이 계산한 출산 추천일' 팩트 문자열을 만듭니다. (이 목록 밖의 날짜는 쓰지 못하게 하기 위함)"""
    if not best_days:
        return "(희망 기간 안에서 조건에 맞는 출산 추천일을 찾지 못했습니다. 기간 또는 마지막 생리일 입력을 다시 확인해 주세요.)"
    lines = []
    for i, d in enumerate(best_days, 1):
        dt = d['delivery_dt']
        lines.append(
            f"[{i}순위] {dt.year}년 {dt.month}월 {dt.day}일({d['weekday_kr']}) / 종합 {d['score']}점{(' (전체 출생 시각 중 상위 ' + str(d['top_pct']) + '%)') if d.get('top_pct') is not None else ''} / "
            f"자연분만 추천 {d['best_any_time']['time_str']} (완성 명식 {d['best_any_time']['pillars']}) / "
            f"제왕절개 추천 {d['best_day_time']['time_str']} (완성 명식 {d['best_day_time']['pillars']}) / "
            f"{_delivery_conception_text(d)} / "
            f"아기 대운 방향: 남아 {d['daeun_dir']['남아']}, 여아 {d['daeun_dir']['여아']} / "
            f"장점: {'; '.join(d['good'][:4]) if d['good'] else '특이 장점 없음'} / "
            f"유의점: {'; '.join(d['warn'][:3]) if d['warn'] else '특이 유의점 없음'}"
        )
        _bn, _bd = d.get('best_any_time'), d.get('best_day_time')
        lines.append(f"   └ 손님이 고른 분만 방식: {d.get('delivery_mode', '미정')} (위 '장점'·'유의점'은 {'제왕절개 추천' if d.get('delivery_mode') == '제왕절개' else '자연분만 추천'} 시각 기준)")
        if _bn and _bd:
            if _bd.get('same_as_best'):
                lines.append(f"   └ 시각 비교: 자연분만 추천 시각과 제왕절개 추천 시각이 같은 {_bn['time_str']}입니다.")
            else:
                lines.append(f"   └ 시각 비교: 자연분만 추천 {_bn['time_str']}(시주 {_bn['time_pillar']}, 원점수 {_bn['score']}) / 제왕절개 추천 {_bd['time_str']}(시주 {_bd['time_pillar']}, 원점수 {_bd['score']}) / 원점수 차이 {_bd['score_gap']}점")
                lines.append(f"   └ 자연분만 추천 시각의 장점: {'; '.join(_bn.get('good', [])[:3]) or '특이 장점 없음'} / 유의점: {'; '.join(_bn.get('warn', [])[:3]) or '특이 유의점 없음'}")
                lines.append(f"   └ 제왕절개 추천 시각의 장점: {'; '.join(_bd.get('good', [])[:3]) or '특이 장점 없음'} / 유의점: {'; '.join(_bd.get('warn', [])[:3]) or '특이 유의점 없음'}")
        if d.get('score_detail'):
            sd = d['score_detail']
            lines.append(f"   └ 점수 구성(만점): 일지 {sd.get('일지', 0)}/{_W_ILJI} · 월지 {sd.get('월지', 0)}/{_W_WOLJI} · 시지 {sd.get('시지', 0)}/{_W_SIJI} · 월간 {sd.get('월간', 0)}/{_W_WOLGAN} · "
                         f"년지 {sd.get('년지', 0)}/{_W_NYEONJI} · 시간 {sd.get('시간', 0)}/{_W_SIGAN} · 년간 {sd.get('년간', 0)}/{_W_NYEONGAN} · 오행 {sd.get('오행', 0)}/{_W_OHAENG} · "
                         f"조후 {sd.get('조후', 0)}/{_W_JOHU} · 공망 {sd.get('공망', 0)}/{_W_GONGMANG} · 대운흐름 {sd.get('대운흐름', 0)}/{_W_DAEWUN} · 부모조화 {sd.get('부모조화', 0)}/{_W_PARENT}")
        if d.get('flow'):
            for g in ('남아', '여아'):
                f_ = d['flow'][g]
                lines.append(f"   └ {g} 대운 흐름 점수 {f_['score']}/{_W_DAEWUN}: " + "; ".join(f_['steps']))
        if d.get('parent_dw'):
            lines.append("   └ 출산 시점 부모 대운: " + " / ".join(f"{w} {v['age']}세 (대운 {v['range']} {v['gz']})" for w, v in d['parent_dw'].items()))
        if d.get('baby_daewun'):
            for g in ('남아', '여아'):
                bd = d['baby_daewun'][g]
                seq = ", ".join(f"{x['age_range']} {x['c_hanja']}{x['j_hanja']}({x['ss_gan']}/{x['ss_ji']}, {x['un_sung']})" for x in bd['list'][:8])
                lines.append(f"   └ {g} 대운({bd['dir']}, 대운수 {bd['calc_d']}): {seq}")
    return "\n".join(lines)

# ─────────────────────────────────────────────────────────────
# 4-1 타 감명서 비교: 원문에 문장 번호 붙이기 / 보고서에서 번호 지우고 미대조 문장 찾기
# ─────────────────────────────────────────────────────────────
def 원문_번호붙이기(text):
    """타 감명서 원문을 문장 단위로 잘라 [원1], [원2]… 번호를 붙인다. (번호 붙인 글, 문장 개수)를 돌려준다."""
    t = (text or "").strip()
    if not t or t.startswith("(실제 제출된 외부 원문 없음"):
        return text, 0
    조각 = []
    for line in t.splitlines():
        line = line.strip()
        if not line:
            continue
        for s in re.split(r"(?<=[.!?。])\s+", line):
            s = s.strip(" -•·")
            if len(s) >= 3:
                조각.append(s)
    return "\n".join(f"[원{i}] {s}" for i, s in enumerate(조각, 1)), len(조각)

def 원문_번호_정리(ai_text, total):
    """보고서에서 (원3, 원4) 표시를 지우고, 한 번도 인용되지 않은 원문 번호 목록을 돌려준다."""
    pat = re.compile(r"\s*\(원\d+(?:\s*,\s*원\d+)*\)")
    cited = {int(n) for m in pat.finditer(ai_text) for n in re.findall(r"\d+", m.group())}
    missing = [i for i in range(1, total + 1) if i not in cited]
    return pat.sub("", ai_text), missing
