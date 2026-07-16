import math
import datetime as dt_mod
from datetime import datetime
import pytz
import ephem
import re
from korean_lunar_calendar import KoreanLunarCalendar

# ==============================================================================
# 1. 시스템 변수 및 기초 상수
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
    if not char: return char
    return K2H_GAN.get(char, K2H_JI.get(char, char))

# ==============================================================================
# 2. 핵심 사주 역산 및 만세력 로직
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
    
    if 315 <= lon < 345: m_ji_idx = 2    # 寅(인)월
    elif 345 <= lon or lon < 15: m_ji_idx = 3  # 卯(묘)월
    elif 15 <= lon < 45: m_ji_idx = 4    # 辰(진)월
    elif 45 <= lon < 75: m_ji_idx = 5    # 巳(사)월
    elif 75 <= lon < 105: m_ji_idx = 6   # 午(오)월
    elif 105 <= lon < 135: m_ji_idx = 7  # 未(미)월
    elif 135 <= lon < 165: m_ji_idx = 8  # 申(신)월
    elif 165 <= lon < 195: m_ji_idx = 9  # 酉(유)월
    elif 195 <= lon < 225: m_ji_idx = 10 # 戌(술)월
    elif 225 <= lon < 255: m_ji_idx = 11 # 亥(해)월
    elif 255 <= lon < 285: m_ji_idx = 0  # 子(자)월
    elif 285 <= lon < 315: m_ji_idx = 1  # 丑(축)월
    
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

def get_saju_fact_sheet(ys, yb, ms, mb, ds, db, hs, hb, name, age, gender, marital, dw_g_cur=None, dw_j_cur=None, curr_y_ganji=None, cur_wol_g=None, cur_wol_j=None, **kwargs):
    """
    모든 명리적 팩트와 체용 매트릭스 분석 결과를 딕셔너리로 통합 반환합니다.
    """
    
    # 1. 기본 팩트 산출 (기존 로직 유지)
    ss_unsung_str = f"년주:{get_ss(ds, ys)}{get_ss(ds, yb)}({get_unsung(ds, yb)}) / 월주:{get_ss(ds, ms)}{get_ss(ds, mb)}({get_unsung(ds, mb)}) / 일주:{ds}(본인){get_ss(ds, db)}({get_unsung(ds, db)}) / 시주:{get_ss(ds, hs)}{get_ss(ds, hb)}({get_unsung(ds, hb)})"
    gyukgook, gyukgook_detail = get_gyukgook_detailed(ds, ys, ms, hs, mb)
    counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
    for c in [ys, yb, ms, mb, ds, db, hs, hb]: counts[get_color(c)] += 1
    oheng_str = f"목:{counts['목']} 화:{counts['화']} 토:{counts['토']} 금:{counts['금']} 수:{counts['수']}"

    # 2. 체용 매트릭스 연산
    ilju_lower_group = get_group_ss(get_ss(ds, db))
    
    dw_fact_str = "대운 정보 없음"
    if dw_g_cur and dw_j_cur:
        dw_che = get_group_ss(get_ss(ds, dw_g_cur))
        dw_yong = get_execution_yong(get_group_ss(get_ss(dw_g_cur, dw_j_cur)), ilju_lower_group)
        dw_fact_str = f"체운(무대): {dw_che} / 용운(사건): {dw_yong} ➔ 도출 키워드: {get_matrix_keyword(dw_che, dw_yong)}"

    sewun_fact_str = "세운 정보 없음"
    if curr_y_ganji:
        s_gan, s_ji = curr_y_ganji[1][0], curr_y_ganji[1][1]
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

    # 3. 팩트 시트 통합
    fact_data = {
        "ys": ys, "yb": yb, "ms": ms, "mb": mb, "ds": ds, "db": db, "hs": hs, "hb": hb,
        "ss_unsung_str": ss_unsung_str, "gyukgook_detail": gyukgook_detail,
        "gongmang_actual": calculate_gongmang(ds, db),
        "shinsal_str": ", ".join(get_general_shinsal_filtered(2, [hs, ds, ms, ys], [hb, db, mb, yb], gender)),
        "s12_str": get_all_12_shinsal(yb, yb, mb, db, hb),
        "won_guk_vaults_str": " ".join(check_vault_status([ys, ms, ds, hs], [yb, mb, db, hb], mb)),
        "oheng_counts_str": oheng_str,
        "samjae_str": get_samjae(yb, "현재년지"), 
        "cheon_eul": {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}.get(ds, '없음'),
        "curr_y": dt_mod.datetime.now().year,
        "curr_m": dt_mod.datetime.now().month,
        "disp_name": name, "u_age": age, "u_gender": gender, "u_marital": marital,
        "yukchin_rule": get_yukchin_rule(gender, marital),
        "dw_fact_str": dw_fact_str, "sewun_fact_str": sewun_fact_str, "wol_fact_str": wol_fact_str
    }
    
    # [비결] kwargs를 통해 넘어온 데이터(other_report, ilju, wolryeong 등)를 팩트 시트에 병합
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
# 3. 명리 이론 연산 로직
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
    dg, ji = _to_hanja(dg), _to_hanja(ji)
    if ji in ["?", " ", "-"]: return "-"
    table = {'甲':"亥子丑寅卯辰巳午未申酉戌",'丙':"寅卯辰巳午未申酉戌亥子丑",'戊':"寅卯辰巳午未申酉戌亥子丑",'庚':"巳午未申酉戌亥子丑寅卯辰",'壬':"申酉戌亥子丑寅卯辰巳午未",'乙':"午巳辰卯寅丑子亥戌酉申未",'丁':"酉申未午巳辰卯寅丑子亥戌",'己':"酉申未午巳辰卯寅丑子亥戌",'辛':"子亥戌酉申未午巳辰卯寅丑",'癸':"卯寅丑子亥戌酉申未午巳辰"}
    idx = table.get(dg, "").find(ji)
    return ["장생","목욕","관대","건록","제왕","쇠","병","사","묘","절","태","양"][idx] if idx != -1 else "-"

def get_12_shinsal(year_ji, target_ji):
    year_ji, target_ji = _to_hanja(year_ji), _to_hanja(target_ji)
    if target_ji in ["?", " ", "-"] or not year_ji: return "-"
    
    ji_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    try:
        t_idx = ji_list.index(target_ji)
        s_map = {"申":"巳","子":"巳","辰":"巳", "寅":"亥","午":"亥","戌":"亥", "巳":"寅","酉":"寅","丑":"寅", "亥":"申","卯":"申","未":"申"}
        s_start = s_map.get(year_ji, "巳")
        s_start_idx = ji_list.index(s_start)
        
        s_idx = (t_idx - s_start_idx + 12) % 12
        return ["겁살","재살","천살","지살","년살","월살","망신살","장성살","반안살","역마살","육해살","화개살"][s_idx]
    except:
        return "-"

def get_all_12_shinsal(yb_unused, yb, mb, db, hb):
    """
    인자를 5개 받도록 수정했습니다. 첫 번째 인자는 무시(unused)합니다.
    """
    results = [
        get_12_shinsal(yb, yb), # 년지 신살
        get_12_shinsal(yb, mb), # 월지 신살
        get_12_shinsal(yb, db), # 일지 신살
        get_12_shinsal(yb, hb)  # 시지 신살
    ]
    return ", ".join(results)

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

def get_universal_analysis(ds, mb, db, gans, jjis):
    jg_list = JIJANGGAN.get(mb, [])
    
    def get_info(gan, target_char, base_ji):
        ss = get_ss(gan, target_char) 
        twelve = get_unsung(target_char, base_ji) 
        return ss, twelve
        
    results = []
    for qi in jg_list:
        ss, twelve = get_info(ds, qi, mb)
        results.append(f"{qi}({ss}): {twelve}좌")
        
    all_present = list(gans)
    for j in jjis:
        if j not in ["?", " ", "-"]:
            all_present.extend(JIJANGGAN.get(j, [])) 
            
    missing = [elem for elem in ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'] if elem not in all_present]
    for m in missing:
        ss, twelve = get_info(ds, m, db)
        results.append(f"{m}({ss}): 인종법 적용 - {twelve}종")
    return results

def get_group_ss(ss_str):
    return {'비견':'비겁', '겁재':'비겁', '식신':'식상', '상관':'식상', '편재':'재성', '정재':'재성', '편관':'관성', '정관':'관성', '편인':'인성', '정인':'인성'}.get(ss_str, '비겁')

def get_yukchin_rule(gender, marital):
    """내담자의 성별과 혼인 상태에 따른 육친 통변 규칙을 반환합니다."""
    if gender == '남성':
        return f"""
🚨 [육친 통변 특수부대 절대 규칙 (남성용)]: 
- 본 내담자는 남성(현재 상태: {marital})입니다.
1. 👨‍👩‍👦 [핵심 가족]: 
   - 아내 = 정재 (없으면 편재) / 애인 = 편재 (없으면 정재)
   - 자녀 = 관성(정관/편관) 🚨(경고: 식상으로 풀이 시 치명적 오류)
2. 👵👴 [부모 및 조부모]: 아버지 = 편재(없으면 정재) / 어머니 = 정인(없으면 편인)
   - 조부 = 편인 / 조모 = 상관
3. 🏠 [처가 및 형제]: 장모 = 식상 / 형제(남) = 비견 / 형제(여) = 겁재
4. 🚨 [상태별 타겟팅]: 내담자 상태({marital})에 따라 인연(아내/재혼운 등)으로 카운슬링할 것.
"""
    else: # 여성
        return f"""
🚨 [육친 통변 특수부대 절대 규칙 (여성용)]: 
- 본 내담자는 여성(현재 상태: {marital})입니다.
1. 👩‍❤️‍👨 [핵심 가족]: 
   - 남편 = 정관 (없으면 편관) / 애인 = 편관 (없으면 정관)
   - 자녀 = 식상(식신/상관) 🚨(경고: 관성으로 풀이 시 치명적 오류)
2. 👵👴 [부모 및 조부모]: 아버지 = 편재(없으면 정재) / 어머니 = 정인(없으면 편인)
   - 조부 = 편인 / 조모 = 상관
3. 🏠 [시댁 및 자매]: 시어머니 = 재성 / 자매 = 비견 / 형제 = 겁재
4. 🚨 [상태별 타겟팅]: 내담자 상태({marital})에 따라 인연(남편/재혼운 등)으로 카운슬링할 것.
"""
def get_group_ss(ss_name):
    if not ss_name or ss_name in ["?", "-", " "]: return "비겁"
    if "비" in ss_name or "겁" in ss_name: return "비겁"
    if "식" in ss_name or "상" in ss_name: return "식상"
    if "재" in ss_name: return "재성"
    if "관" in ss_name: return "관성"
    if "인" in ss_name: return "인성"
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
    # che_yong_matrix_text는 engine.py 상단에 상수로 정의하거나 이 함수 내부에서 관리
    target_str = f"- 체({che_group})+용({yong_group}):"
    for line in CHE_YONG_MATRIX_TEXT.splitlines():
        if line.startswith(target_str):
            return line.split(":", 1)[1].strip()
    return "변화 감지"

# ==============================================================================
# 4. 출산택일 및 궁합 연산 로직
# ==============================================================================
def get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, forbidden_list=None):
    if forbidden_list is None: forbidden_list = []
        
    OHENG_MAP = {
        '갑':'목', '을':'목', '인':'목', '묘':'목',
        '병':'화', '정':'화', '사':'화', '오':'화',
        '무':'토', '기':'토', '축':'토', '진':'토', '미':'토', '술':'토',
        '경':'금', '신':'금', '유':'금',
        '임':'수', '계':'수', '자':'수', '해':'수'
    }
    
    KILL_SWITCH = {'병오', '임자', '신유', '경신', '을묘', '무오', '무술', '정축', '갑진', '을미', '병술', '무진', '임술', '계축'}
    if forbidden_list: KILL_SWITCH.update(forbidden_list)
        
    hap_list = [{'자', '축'}, {'인', '해'}, {'묘', '술'}, {'진', '유'}, {'사', '신'}, {'오', '미'}]
    choong_list = [{'자', '오'}, {'축', '미'}, {'인', '신'}, {'묘', '유'}, {'진', '술'}, {'사', '해'}]
    
    H2K_MAP = {'甲':'갑','乙':'을','丙':'병','丁':'정','戊':'무','己':'기','庚':'경','辛':'신','壬':'임','癸':'계',
               '子':'자','丑':'축','寅':'인','卯':'묘','辰':'진','巳':'사','午':'오','未':'미','申':'신','酉':'유','戌':'술','亥':'해'}
    def h2k(text): return "".join([H2K_MAP.get(c, c) for c in text])

    TIME_SLOTS = [
        ("자", "23:30~01:29"), ("축", "01:30~03:29"), ("인", "03:30~05:29"),
        ("묘", "05:30~07:29"), ("진", "07:30~09:29"), ("사", "09:30~11:29"),
        ("오", "11:30~13:29"), ("미", "13:30~15:29"), ("신", "15:30~17:29"),
        ("유", "17:30~19:29"), ("술", "19:30~21:29"), ("해", "21:30~23:29")
    ]
    TIME_STEM_START = {'갑':'갑', '기':'갑', '을':'병', '경':'병', '병':'무', '신':'무', '정':'경', '임':'경', '무':'임', '계':'임'}
    GAN_LIST = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계']

    raw_candidates = []
    curr = start_date
    
    HOT_JI = ['사', '오', '미', '술']
    COLD_JI = ['해', '자', '축', '진']
    
    while curr <= end_date:
        birth_d = curr + dt_mod.timedelta(days=280)
        
        b_klc = KoreanLunarCalendar()
        b_klc.setSolarDate(birth_d.year, birth_d.month, birth_d.day)
        b_gj = b_klc.getChineseGapJaString().split()
        
        if len(b_gj) >= 3:
            b_gj_kor = [h2k(pillar) for pillar in b_gj[:3]] 
            b_year, b_month, b_day = b_gj_kor[0], b_gj_kor[1], b_gj_kor[2]
            
            if b_year in KILL_SWITCH or b_month in KILL_SWITCH or b_day in KILL_SWITCH:
                curr += dt_mod.timedelta(days=1); continue
            if b_year == b_month or b_month == b_day or b_year == b_day:
                curr += dt_mod.timedelta(days=1); continue
            
            ym_score = 25 
            y_ji = b_year[1]
            m_ji = b_month[1]
            
            if y_ji in HOT_JI:
                if m_ji in COLD_JI or m_ji in ['신', '유']: ym_score += 20
                elif m_ji in HOT_JI: ym_score -= 20
            elif y_ji in COLD_JI:
                if m_ji in HOT_JI or m_ji in ['인', '묘']: ym_score += 20
                elif m_ji in COLD_JI: ym_score -= 20
            else:
                ym_score += 10 
                
            ym_score = max(0, min(45, ym_score))
            
            b_day_stem = b_day[0]
            start_stem = TIME_STEM_START.get(b_day_stem, '갑')
            start_idx = GAN_LIST.index(start_stem)

            best_time_score = -999
            best_time_data = {}

            for t_idx, (t_ji, t_time_str) in enumerate(TIME_SLOTS):
                t_gan = GAN_LIST[(start_idx + t_idx) % 10]
                b_time = f"{t_gan}{t_ji}"

                if b_time in KILL_SWITCH or b_time in [b_year, b_month, b_day]: continue

                four_pillars = [b_year, b_month, b_day, b_time]
                characters = []
                for pillar in four_pillars: characters.extend([pillar[0], pillar[1]])
                    
                oheng_counts = {'목': 0, '화': 0, '토': 0, '금': 0, '수': 0}
                for char in characters:
                    oh = OHENG_MAP.get(char)
                    if oh: oheng_counts[oh] += 1
                    
                present_types = [t for t, c in oheng_counts.items() if c > 0]
                dt_score = len(present_types) * 5 
                for t, c in oheng_counts.items():
                    if c >= 3: dt_score -= 10 
                
                dt_score = max(0, min(25, dt_score))
                baby_score = ym_score + dt_score 
                
                parent_score = 15
                b_ilji = b_day[1]
                for p_ji in m_jjis + f_jjis:
                    if p_ji == '?': continue
                    pair = {b_ilji, p_ji}
                    if pair in hap_list: parent_score += 10
                    if pair in choong_list: parent_score -= 10
                parent_score = max(0, min(30, parent_score))
                
                tie_breaker = ((32 - birth_d.day) * 0.001) + (t_idx * 0.0001)
                total_score = baby_score + parent_score + tie_breaker

                if total_score > best_time_score:
                    best_time_score = total_score
                    best_time_data = {'time_pillar': b_time, 'time_str': t_time_str, 'score': total_score, 'ym_score': ym_score}

            if best_time_data:
                raw_candidates.append({
                    'date': curr.strftime('%Y-%m-%d'),
                    'month': curr.strftime('%Y-%m'),
                    'score': best_time_data['score'],
                    'ym_score': best_time_data['ym_score'],
                    'best_time': best_time_data
                })
                
        curr += dt_mod.timedelta(days=1)
        
    month_best_bucket = {}
    for item in raw_candidates:
        m_key = item['month']
        if m_key not in month_best_bucket or item['score'] > month_best_bucket[m_key]['score']:
            month_best_bucket[m_key] = item
            
    sorted_months = sorted(month_best_bucket.values(), key=lambda x: x['score'], reverse=True)
    return sorted_months[:3]

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

    # [수정] 한글 시간 문자열(예: 진시)을 파싱하여 숫자와 한자로 분리하는 로직
    def get_time_ganji_fixed(day_gan, time_str):
        if "시간 모름" in time_str or "모름" in time_str: return "", ""
        
        # 괄호 안의 글자만 추출 (예: 진시)
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
        # 시간 추출 로직 (개인사주와 동일한 정수 추출)
        h, m_val = 0, 0
        if ":" in t:
            col_idx = t.find(":")
            try:
                h = int(t[col_idx-2:col_idx].strip())
                m_val = int(t[col_idx+1:col_idx+3].strip())
            except: pass

        y_pillar, m_pillar, _ = get_true_year_month_pillar(y, m, d, h, m_val)
        _, _, d_pillar = get_ganji_from_date(y, m, d)
        
        # [중요] 일주 기반 시주 계산 로직 적용
        t_gan, t_ji = get_time_ganji_fixed(d_pillar[0], t)
        
        gans, jjis = [t_gan, d_pillar[0], m_pillar[0], y_pillar[0]], [t_ji, d_pillar[1], m_pillar[1], y_pillar[1]]
        ys, yb = y_pillar[0], y_pillar[1]
        ms, mb = m_pillar[0], m_pillar[1]
        ds, db = d_pillar[0], d_pillar[1]        
        
        # 1. 먼저 order_dir을 결정합니다.
        order_dir = 1 if (GAN.index(ys) % 2 == 0) == (gender == '남성') else -1
        
        # 2. 결정된 order_dir을 사용하여 calc_d를 계산합니다.
        calc_d = get_daeun_su_accurate(datetime(y, m, d), order_dir)

        curr_year = datetime.now().year
        age = curr_year - y + 1

        # 3. 이후 대운 리스트를 생성합니다.
        direction_str = "순행" if order_dir == 1 else "역행"
        daewun_data_list = get_daeun_data_list(ms, mb, ds, yb, order_dir, calc_d, age)
        daewun = (daewun_data_list, direction_str, calc_d, get_oh_class)

        counts = {'목':0, '화':0, '토':0, '금':0, '수':0}
        for c in gans + jjis:
            oh = get_color(c)
            if oh in counts: counts[oh] += 1
        
        info_h = f"<div style='text-align:center;'>{name}님</div>"
        gan_rel = "".join([f"<td style='border:1px solid #444;'>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])
        gan_ss = f"<td style='border:1px solid #444;'>{get_ss(ds,gans[0])}</td><td style='border:1px solid #444; font-weight:900;'>일원</td><td style='border:1px solid #444;'>{get_ss(ds,gans[2])}</td><td style='border:1px solid #444;'>{get_ss(ds,gans[3])}</td>"
        gan_row = "".join([f"<td class='{get_oh_class(g)}' style='border:1px solid #444; font-size:24px; font-weight:900;'>{g}</td>" for g in gans])
        ji_row = "".join([f"<td class='{get_oh_class(j)}' style='border:1px solid #444; font-size:24px; font-weight:900;'>{j}</td>" for j in jjis])
        ji_ss = "".join([f"<td style='border:1px solid #444;'>{get_ss(ds,j)}</td>" for j in jjis])
        jijanggan = "".join([f"<td>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])
        
        ji_rel_rows = ""
        # 순서: 월(1), 일(2), 년(0), 시(3)
        for l_idx, r_idx in enumerate([1, 2, 0, 3]):
            b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
            
            # [최종] 각 지지별 실제 한자를 가져와 박사님께서 지시하신 방향 포맷에 삽입합니다.
            current_ji = jjis[r_idx]
            if r_idx == 0: dir_label = f"←({current_ji})"
            elif r_idx == 1: dir_label = f"←({current_ji})→"
            elif r_idx == 2: dir_label = f"←({current_ji})→"
            else: dir_label = f"({current_ji})→"
            
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

        return {"table": [None, gan_rel, gan_ss, gan_row, ji_row, ji_ss, jijanggan, ji_rel_rows, unsung, shinsal, gen_shinsal], "master": master, "daewun": daewun}

    m_res = _get_person_data(s_y, s_m, s_d, s_t, "남성", "신청인", m_marital)
    w_res = _get_person_data(f_y, f_m, f_d, f_t, "여성", "상대방", f_marital)
    
    return {
        "m_table": m_res["table"], "m_master": m_res["master"], "m_daewun": m_res["daewun"],
        "w_table": w_res["table"], "w_master": w_res["master"], "w_daewun": w_res["daewun"],
        
        # 프롬프트 매핑용 데이터
        "m_ds": m_res["master"][0],
        "m_db": m_res["master"][1],
        "m_gongmang_actual": m_res["master"][7],
        
        "f_ds": w_res["master"][0],
        "f_db": w_res["master"][1],
        "f_gongmang_actual": w_res["master"][7],
        
        "m_golden": f"{m_res['master'][0]}일간 중심의 성향 분석",
        "f_golden": f"{w_res['master'][0]}일간 중심의 성향 분석",
        
        "calc_gyukgook": "시공명리 격국 분석",
        "db_header": "초연 시공명리 심층 궁합 분석 리포트",
        "ai_saju_mapping": "시공간의 교차점 분석",
        "yukchin_rule": "육친 및 십이운성 상생법 적용",
        "marital_info": marital_status
    }

def get_gunghap_report(res):
    return "두 분의 사주 에너지는 시공간의 조화를 이루고 있습니다. 정밀 분석 결과..."

