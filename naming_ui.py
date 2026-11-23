# -*- coding: utf-8 -*-
"""
이름 풀이 및 짓기 화면 (naming_ui.py)  v1.1
- app.py 에서는 아래 두 줄만 부르면 된다.
    import naming_ui
    result = naming_ui.render_naming_product(u_product, yong_el, gender, name)   # yong_el = engine.get_yongshin_elements(...) 결과
- 화면 순서: 성씨 입력 → (돌림자) → 가운데 글자 고르기 → 끝 글자 고르기 → 판정표
- 기존 engine.py / 사주 화면은 건드리지 않는다.
"""
import os
import streamlit as st
from naming_engine import NamingEngine, yong_from_engine, rel

# 흔한 성씨 한자는 후보 맨 앞에 (예: '이' -> 李 가 먼저)
COMMON_SURNAME_HANJA = "金李朴崔鄭姜趙尹張林韓吳申徐權黃安宋柳洪全高文孫梁裵白曺許南劉盧沈河郭成車朱禹具辛任田閔愈"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'naming_db.json')
TIER_LABELS = ["흔한 글자 + 뜻 좋은 글자 (권장)", "뜻 좋은 글자 전체", "모든 글자 (인명용 한자 전체)"]


@st.cache_resource(show_spinner=False)
def get_neng():
    return NamingEngine(DB_PATH)


def _tier_exclude(neng, tier):
    if tier == 0:
        return [x['h'] for x in neng.hanja if not (x.get('g') and x.get('e'))]
    if tier == 1:
        return [x['h'] for x in neng.hanja if not x.get('g')]
    return []


def _hanja_label(x):
    hun = x['hun'].split('/')[0]
    return f"{x['h']}  {hun}  ({x['st']}획 · 자원{x['ja']} · 소리{x['bo']})"


# ------------------------------------------------------------------ 입력 부품
def pick_surname(neng, label, key, optional=False, pre=None):
    """한글 성씨 입력 → 한자 후보 고르기. 반환: 성씨 항목(없으면 None). pre = 신청서에서 받은 {'r','h'}"""
    if pre and f"{key}_rd" not in st.session_state:
        st.session_state[f"{key}_rd"] = pre['r']
    rd = st.text_input(label, key=f"{key}_rd", placeholder="예) 김, 이, 박, 남궁").strip()
    if not rd:
        return None
    cands = sorted(neng.find_surname(rd), key=lambda c: (COMMON_SURNAME_HANJA.find(c['h']) if c['h'] in COMMON_SURNAME_HANJA else 999))
    if not cands:
        st.warning(f"'{rd}' 성씨를 찾지 못했습니다. 한글 성씨를 다시 확인해 주세요.")
        return None
    if len(cands) == 1:
        c = cands[0]
        st.caption(f"성씨 한자: {c['h']} ({c['st']}획)")
        return c
    labels = [f"{c['h']}  ({c['st']}획)" for c in cands]
    if pre and f"{key}_hj" not in st.session_state:
        st.session_state[f"{key}_hj"] = next((j for j, c in enumerate(cands) if c['h'] == pre['h']), 0)
    i = st.radio("성씨 한자를 골라 주세요", range(len(cands)), format_func=lambda i: labels[i], key=f"{key}_hj", horizontal=True)
    return cands[i]


def pick_hanja(neng, label, key, help_text="", pre=None):
    """한글 한 글자 입력 → 한자 후보 선택. 반환: 한자 dict(없으면 None). pre = 신청서에서 받은 {'r','h'}"""
    if pre and f"{key}_rd" not in st.session_state:
        st.session_state[f"{key}_rd"] = pre['r']
    rd = st.text_input(label, key=f"{key}_rd", help=help_text, max_chars=1).strip()
    if not rd:
        return None
    cands = [x for x in neng.find_by_reading(rd) if x['h'] not in neng.bad]
    cands.sort(key=lambda x: (-int(bool(x.get('e'))), x['st']))
    if not cands:
        st.warning(f"'{rd}'로 읽는 한자를 찾지 못했습니다.")
        return None
    if pre and f"{key}_hj" not in st.session_state:
        st.session_state[f"{key}_hj"] = next((j for j, x in enumerate(cands) if x['h'] == pre['h']), 0)
    i = st.selectbox("한자를 골라 주세요", range(len(cands)), format_func=lambda i: _hanja_label(cands[i]), key=f"{key}_hj")
    return cands[i]

def _gyeok_table(an):
    rows = []
    for k, v in an['네격'].items():
        mark = '✅' if v['길흉'] == '길' else '⚠️'
        rows.append(f"| {k} ({v['때']}) | {v['수리']} | {v['격']} {v.get('한자', '')} | {v.get('상', '')} | {mark} {v['길흉']} |")
    return "| 격 | 수리 | 이름 | 상 | 길흉 |\n|---|---|---|---|---|\n" + "\n".join(rows)


_CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"


def _chain_text(an, kind):
    """오행 흐름을 글자와 함께 보여 준다. 예) 土(ㅇ) ─비화→ 土(ㅇ) ─극→ 水(ㅂ)"""
    el = an['소리배합'] if kind == '소리' else an['자원배합']
    rels = an['소리관계'] if kind == '소리' else an['자원관계']
    hj, rd = an['이름'], an['독음']
    if len(hj) != len(el) or len(rd) != len(el):
        return ' → '.join(el)          # 글자 수가 안 맞는 경우(부모 성 등)는 예전 방식 그대로
    marks = []
    for h, r in zip(hj, rd):
        c = ord(r) - 0xAC00
        marks.append(_CHO[c // 588] if 0 <= c < 11172 else r) if kind == '소리' else marks.append(h)
    out = f"{el[0]}({marks[0]})"
    for i in range(1, len(el)):
        out += f" ─{rels[i-1]}→ {el[i]}({marks[i]})"
    return out


def _book_note(an, kind):
    """125표의 '책의 풀이 요지'. 세 글자 배합일 때만 있음(외자는 없음)"""
    el = an['소리배합'] if kind == '소리' else an['자원배합']
    if len(el) != 3:
        return ""
    return get_neng().db.get('sound125_text', {}).get(''.join(el), "")


def show_analysis(an):
    st.markdown(f"### {an['이름']} ({an['독음']})")
    c1, c2 = st.columns(2)
    _n1, _n2 = _book_note(an, '소리'), _book_note(an, '자원')
    c1.markdown(f"**소리오행** {_chain_text(an, '소리')}  \n판정: **{an['소리판정']}**" + (f"  \n📖 {_n1}" if _n1 else ""))
    c2.markdown(f"**자원오행** {_chain_text(an, '자원')}  \n판정: **{an['자원판정']}**" + (f"  \n📖 {_n2}" if _n2 else ""))
    st.markdown(_gyeok_table(an))
    tag = []
    tag.append("중심오행(용신) 포함 ✅" if an['용신포함'] else "중심오행(용신) 미포함 ⚠️")
    if an['기신포함']:
        tag.append("피해야 할 오행 포함 ⚠️")
    tag.append(f"음양 {an['음양']}")
    st.caption(" · ".join(tag))


# ------------------------------------------------------------------ 상품별 화면
def _surname_block(neng, key):
    pre = st.session_state.get('nm_pre') or {}
    sur1 = pick_surname(neng, "성씨 (한글)", f"{key}_s1", pre=pre.get('sur'))
    sur2 = None
    st.session_state.setdefault(f"{key}_two", bool(pre.get('sur2')))
    if st.checkbox("성씨를 두 개 이어 씁니다 (예: 김이○○ 의 '김이')", key=f"{key}_two"):
        sur2 = pick_surname(neng, "이어 붙일 성씨 (한글) — 입력한 순서대로 붙습니다", f"{key}_s2", pre=pre.get('sur2'))
    if sur1 is None:
        return None
    ents = [sur1] + ([sur2] if sur2 else [])
    sur = neng.build_surname(ents)
    if sur2:
        st.caption(f"합친 성씨: {sur['h']} ({sur['st']}획)")
    return sur

def _flow_single(neng, sur, yong, key):
    """외자 이름(성 + 한 글자): 후보 중에서 한 글자 고르기"""
    order = st.radio("몇째 자녀입니까? (책 9장: 장자·차자 불용한자 가림)", ["첫째 (장자)", "둘째 이하 (차자)", "가리지 않음"], horizontal=True, index=2, key=f"{key}_order1")
    _ex = [x['h'] for x in neng.hanja if not x.get('e') or x['h'] in _NO_NAME] + _order_exclude(neng, order)
    cands = neng.single_candidates(sur, yong, exclude=_ex)
    if not cands:
        need = yong.get('용신')
        if need and rel(sur['ja'], need) == '극':
            st.warning(f"이 성씨의 자원오행({sur['ja']})과 사주의 중심오행({need})이 서로 극하는 사이라, 외자 이름으로는 두 가지를 함께 맞출 수 없습니다. 두 글자 이름을 권합니다.")
        else:
            st.warning("이 성씨는 외자 이름으로 네 격이 모두 길한 글자가 없습니다. 글자 범위를 넓히거나 두 글자 이름을 권합니다.")
        return None
    st.markdown(f"**이름 글자 고르기** — 후보 {len(cands)}자 (★ 은 초연 추천)")
    i = st.selectbox("이름 글자", range(len(cands)), key=f"{key}_one",
                     format_func=lambda i: ("★ " if cands[i]['추천'] else "") + _hanja_label(cands[i]))
    return neng.analyze_name(sur, cands[i], None, yong)

def _flow_new_name(neng, sur, yong, gender, key):
    """4-2 이름 바꾸기 / 4-3 신생아 이름짓기: 가운데 글자 → 끝 글자 고르기 (외자 선택 가능)"""
    neng.gender = gender
    pre = st.session_state.get('nm_pre') or {}
    if pre.get('script') == '한글 이름':
        st.warning("신청자가 '한글 이름'을 원하셨습니다. 한글 이름 짓기 화면은 아직 준비 중입니다. (한자 이름 화면은 지금 쓰실 수 없습니다)")
        return None
    st.session_state.setdefault(f"{key}_n", pre.get('n_new', 2))
    n = 1 if st.radio("외자 이름(성 + 한 글자)을 선호하십니까?", ["아니오 (두 글자 이름)", "예 (외자 이름)"], horizontal=True, key=f"{key}_n").startswith("예") else 2
    if n == 1:
        return _flow_single(neng, sur, yong, key)
    fixed_pos, fixed = None, None
    st.session_state.setdefault(f"{key}_dol", bool(pre.get('dol_pos')))
    if st.radio("집안의 돌림자를 꼭 써야 합니까?", ["아니오 (돌림자 없이)", "예 (돌림자가 있음)"], horizontal=True, key=f"{key}_dol").startswith("예"):
        if pre.get('dol_pos'):
            st.session_state.setdefault(f"{key}_dolpos", pre['dol_pos'])
        fixed_pos = st.radio("돌림자 위치", ["가운데 글자", "마지막 글자"], horizontal=True, key=f"{key}_dolpos")
        fixed = pick_hanja(neng, "돌림자 (한글 한 글자)", f"{key}_dolch", "집안의 돌림자를 한글로 한 글자 넣어 주세요", pre=pre.get('dol'))
        if fixed is None:
            st.info("돌림자를 입력하면 그 글자에 맞는 나머지 글자를 찾아 드립니다.")
            return None
    return _flow_auto_pick(neng, sur, yong, fixed_pos, fixed, key)

    if fixed_pos == "가운데 글자":
        first = fixed
    else:
        end_fixed = fixed if fixed_pos == "마지막 글자" else None
        mids = neng.middle_candidates(sur, yong, exclude=ex, fixed_end=end_fixed)
        if not mids:
            st.warning("이 조건에 맞는 가운데 글자가 없습니다. 글자 범위를 넓혀 보세요.")
            return None
        st.markdown(f"**① 가운데 글자 고르기** — 후보 {len(mids)}자 (★ 은 초연 추천)")
        i = st.selectbox("가운데 글자", range(len(mids)), key=f"{key}_mid",
                         format_func=lambda i: ("★ " if mids[i]['추천'] else "") + _hanja_label(mids[i]))
        first = mids[i]

    if fixed_pos == "마지막 글자":
        second = fixed
    else:
        ends = neng.end_candidates(sur, first, yong, exclude=ex)
        if not ends:
            st.warning(f"'{first['h']}' 글자와 어울리는 끝 글자가 없습니다. 다른 가운데 글자나 더 넓은 범위를 골라 보세요.")
            return None
        st.markdown(f"**② 끝 글자 고르기** — 후보 {len(ends)}자 (★ 은 초연 추천)")
        j = st.selectbox("끝 글자", range(len(ends)), key=f"{key}_end",
                         format_func=lambda j: ("★ " if ends[j]['추천'] else "") + _hanja_label(ends[j]))
        second = ends[j]
    return neng.analyze_name(sur, first, second, yong)


def _flow_check_name(neng, sur, yong, key):
    """4-1 이름 풀이: 지금 이름의 글자를 한자로 골라 판정"""
    st.markdown("**현재 이름의 한자를 골라 주세요** (성씨를 뺀 이름 글자)")
    pre = st.session_state.get('nm_pre') or {}
    cur = pre.get('cur') or [None, None]
    st.session_state.setdefault(f"{key}_n", pre.get('n_cur', 2))
    n = st.radio("이름 글자 수", [2, 1], format_func=lambda n: "두 글자 (예: 수연)" if n == 2 else "한 글자 (예: 솔)", horizontal=True, key=f"{key}_n")
    A = pick_hanja(neng, "이름 첫 글자 (한글)", f"{key}_c1", pre=cur[0])
    B = pick_hanja(neng, "이름 둘째 글자 (한글)", f"{key}_c2", pre=(cur[1] if len(cur) > 1 else None)) if n == 2 else None
    if A is None or (n == 2 and B is None):
        return None
    return neng.analyze_name(sur, A, B, yong)


def render_naming_product(u_product, yong_el, gender, name=""):
    """
    app 에서 부르는 입구.
    u_product : '4-1 …' / '4-2 …' / '4-3 …'
    yong_el   : engine.get_yongshin_elements(...) 사전 (한글 목화토금수)
    gender    : '남성' / '여성'
    반환       : 판정 결과 dict (아직 이름이 정해지지 않았으면 None)
    """
    neng = get_neng()
    yong = yong_from_engine(yong_el or {})
    g = '남' if str(gender).startswith('남') else '여'
    key = "nm_" + str(u_product)[:3]
    st.caption(f"사주의 중심오행(용신) {yong.get('용신') or '-'} · 보조오행(희신) {yong.get('희신') or '-'} · 피할 오행 {yong.get('기신') or '-'}")
    sur = _surname_block(neng, key)
    if sur is None:
        st.info("성씨를 한글로 입력해 주세요.")
        return None
    if str(u_product).startswith("4-1"):
        an = _flow_check_name(neng, sur, yong, key)
    else:
        an = _flow_new_name(neng, sur, yong, g, key)
    if an:
        show_analysis(an)
    return an


# ------------------------------------------------------------------ 사주 → 용신 (app.py 와 같은 방식, app 코드는 건드리지 않음)
def render_saju_block(engine, hv, cdb, sj, name, gender, b_year, b_month, b_day, b_time, u_cal):
    """입력 표 아래에 사주원국표 + 대운표 + 마스터바 + 황금글을 보여 준다 (app.py 1-1 과 같은 부품 사용)"""
    import datetime as _dt
    try:
        from zoneinfo import ZoneInfo
        curr_year = _dt.datetime.now(ZoneInfo('Asia/Seoul')).year
    except Exception:
        curr_year = _dt.datetime.now().year
    gans, jjis, counts = sj['gans'], sj['jjis'], sj['counts']
    hs, ds, ms, ys = gans
    hb, db, mb, yb = jjis
    from korean_lunar_calendar import KoreanLunarCalendar
    klc = KoreanLunarCalendar()
    if "음력" in u_cal:
        klc.setLunarDate(int(b_year), int(b_month), int(b_day), "윤달" in u_cal)
        sol_y, sol_m, sol_d = klc.solarYear, klc.solarMonth, klc.solarDay
        lun_str = f"{int(b_year)}년 {int(b_month):02d}월 {int(b_day):02d}일 ({'윤달' if '윤달' in u_cal else '평달'})"
    else:
        klc.setSolarDate(int(b_year), int(b_month), int(b_day))
        sol_y, sol_m, sol_d = int(b_year), int(b_month), int(b_day)
        lun_str = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({'윤달' if getattr(klc, 'isIntercalation', False) else '평달'})"
    sol_str = f"{sol_y}년 {sol_m:02d}월 {sol_d:02d}일"
    age = curr_year - sol_y + 1
    time_str = b_time if b_time != "시간 모름" else "시간 미상"
    marital = st.session_state.get('u_m_stat', '미혼')
    icon = "♂️" if str(gender).startswith('남') else "♀️"
    guiin_map = {'甲': '丑, 未', '乙': '子, 申', '丙': '酉, 亥', '丁': '酉, 亥', '戊': '丑, 未', '己': '子, 申', '庚': '丑, 未', '辛': '寅, 午', '壬': '卯, 巳', '癸': '卯, 巳'}
    n_gong = engine.calculate_gongmang(ys, yb) or "-"
    i_gong = engine.calculate_gongmang(ds, db) or "-"
    curr_y_ji = engine.JI[(curr_year - 1984) % 60 % 12]
    cur_samjae = engine.get_samjae(yb, curr_y_ji)
    samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"
    dw = engine.get_daeun_data_list(ms, mb, ds, yb, sj['order_dir'], sj['calc_d'], age, db)
    direction = "순행" if sj['order_dir'] == 1 else "역행"
    parts = [
        hv.get_info_header(icon, name, gender, marital, age, sol_str, lun_str, time_str),
        hv.generate_saju_table_data(gans, jjis, ds, gender, engine),
        hv.get_master_bar(sj['calc_d'], counts['목'], counts['화'], counts['토'], counts['금'], counts['수'],
                          guiin_map.get(ds, '없음'), n_gong, i_gong, samjae_color, cur_samjae, yongshin_text=sj['yong_text']),
        hv.generate_daewun_layout(dw, direction, sj['calc_d'], engine.get_oh_class),
    ]
    try:
        w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{db}".strip()
        w_val = cdb.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
        i_val = cdb.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
        sd = cdb.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
        gyuk, _ = engine.get_gyukgook_detailed(ds, ys, ms, hs, mb, jjis=[hb, db, mb, yb], gans=[hs, ds, ms, ys])
        parts.append(hv.get_golden_text(name, w_val, i_val, sd[0], sd[1], sd[2], mb=mb, gyuk_name=gyuk))
    except Exception as e:
        st.caption(f"(황금글은 표시하지 못했습니다: {e})")
    _html = "".join(str(p or "") for p in parts)
    st.markdown(_html, unsafe_allow_html=True)
    return _html

def saju_from_inputs(engine, b_year, b_month, b_day, b_time, u_cal, gender):
    """
    app.py 의 입력값(생년월일·시간·양/음력)으로 사주 여덟 글자와 용신을 구한다.
    반환: dict(gans, jjis, counts, yong_text, yong_el)   gans/jjis 순서는 [시, 일, 월, 년]
    """
    import re
    is_lunar = "음력" in u_cal
    is_leap = "윤달" in u_cal
    g_res = engine.get_ganji_from_date(int(b_year), int(b_month), int(b_day), is_lunar, is_leap)
    y_pillar, m_pillar, d_pillar = g_res[0], g_res[1], g_res[2]
    s_year, s_month, s_day = int(b_year), int(b_month), int(b_day)
    if is_lunar:
        s_year, s_month, s_day = engine.lunar_to_solar(s_year, s_month, s_day, is_leap)
    mt = re.search(r'(\d{2}):(\d{2})', b_time or '')
    h, m = (int(mt.group(1)), int(mt.group(2))) if (mt and "모름" not in b_time) else (0, 0)
    try:
        t_res = engine.get_true_year_month_pillar(s_year, s_month, s_day, h, m)
        if t_res and len(t_res) >= 2:
            y_pillar, m_pillar = t_res[0], t_res[1]
    except Exception:
        pass
    ds_hanja = engine.K2H_GAN.get(d_pillar[0], d_pillar[0])
    t_gan, t_ji = "", ""
    if "모름" not in (b_time or ''):
        mm = re.search(r'\((.*?)\)', b_time)
        raw_ji = mm.group(1).replace('朝', '').replace('夜', '') if mm else "子"
        t_ji = engine.K2H_JI.get(raw_ji, raw_ji)
        gan_arr = list('甲乙丙丁戊己庚辛壬癸'); ji_arr = list('子丑寅卯辰巳午未申酉戌亥')
        if ds_hanja in gan_arr and t_ji in ji_arr:
            t_gan = gan_arr[((gan_arr.index(ds_hanja) % 5) * 2 + ji_arr.index(t_ji)) % 10]
    gans = [t_gan or "-", d_pillar[0], m_pillar[0], y_pillar[0]]
    jjis = [t_ji or "-", d_pillar[1], m_pillar[1], y_pillar[1]]
    hs, ds, ms, ys = gans; hb, db, mb, yb = jjis
    counts = {'목': 0, '화': 0, '토': 0, '금': 0, '수': 0}
    for c in gans + jjis:
        oh = engine.get_color(c)
        if oh in counts:
            counts[oh] += 1
    txt = engine.get_yongshin_analysis(counts, mb, ds, db, gans=[hs, ds, ms, ys], jjis=[hb, db, mb, yb])
    # ---- 대운표 (app.py 와 같은 방식)
    import datetime as _dt
    base_dt = _dt.datetime(s_year, s_month, s_day, 12, 0)
    adj = engine.get_total_time_adjustment(base_dt)
    utc_dt = base_dt - _dt.timedelta(hours=9) + _dt.timedelta(minutes=adj)
    ys_idx = engine.GAN.index(ys) if ys in engine.GAN else 0
    order_dir = 1 if (ys_idx % 2 == 0) == (str(gender).startswith('남')) else -1
    calc_d = engine.get_daeun_su_accurate(utc_dt, order_dir)
    dw = engine.get_daeun_data_list(ms, mb, ds, yb, order_dir, calc_d, 0, db)
    return {'gans': gans, 'jjis': jjis, 'counts': counts, 'yong_text': txt, 'yong_el': engine.get_yongshin_elements(txt),
            'daewun': dw, 'calc_d': calc_d, 'order_dir': order_dir}


PROMPT_NAME = {"4-1": "프롬프트_N4_1_이름풀이", "4-2": "프롬프트_N4_2_이름바꾸기", "4-3": "프롬프트_N4_3_신생아이름짓기"}


class _SafeDict(dict):
    def __missing__(self, k):
        return ""


def build_naming_facts(an, yong=None):
    L = [f"이름: {an['이름']} (독음 {an['독음']})",
         f"소리오행: {' → '.join(an['소리배합'])} / 관계 {' · '.join(an['소리관계'])} / 판정 {an['소리판정']}" + (f" / 책의 풀이: {_book_note(an, '소리')}" if _book_note(an, '소리') else ""),
         f"자원오행: {' → '.join(an['자원배합'])} / 관계 {' · '.join(an['자원관계'])} / 판정 {an['자원판정']}" + (f" / 책의 풀이: {_book_note(an, '자원')}" if _book_note(an, '자원') else "")]
    for k, v in an['네격'].items():
        L.append(f"{k}({v['때']}): 수리 {v['수리']} · 격 이름 {v['격']} · 상 {v.get('상', '')} · 길흉 {v['길흉']} · 해설 {v.get('해설', '')}")
    _y = yong or {}
    _need = [o for o in (_y.get('용신'), _y.get('겸용')) if o]
    _hit = [str(x)[0] for x in an['자원배합'] if str(x)[0] in _need]
    _src = f"사주의 중심오행은 용신 {_y.get('용신') or '-'}, 겸용 {_y.get('겸용') or '-'}입니다. 이름 글자에 실제로 들어 있는 해당 오행: {', '.join(_hit) if _hit else '없음'}. 용신 {_y.get('용신') or '-'} 자체가 이름에 들어 있는지: {'예' if _y.get('용신') in _hit else '아니오'}. (풀이글에는 반드시 실제로 들어 있는 오행 이름으로 쓸 것)"
    L.append("중심오행 포함: " + ("예" if an['용신포함'] else "아니오") + " / " + _src)
    L.append("피할 오행 포함: " + ("예" if an['기신포함'] else "아니오"))
    L.append(f"음양: {an['음양']}")
    return "\n".join(L)

def build_golden_facts(engine, sj, cdb):
    """일주 성품·월령·구조·격 — 1-1 황금글과 같은 자료를 AI 에게 줄 사실 문장으로"""
    if not cdb:
        return ""
    hs, ds, ms, ys = sj['gans']
    hb, db, mb, yb = sj['jjis']
    w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{db}".strip()
    w_val = cdb.get("wolryeong", {}).get(w_key, "")
    i_val = cdb.get("ilju", {}).get(i_key, "")
    sd = cdb.get("ilju_structure", {}).get(i_key, ["", "", ""])
    try:
        gyuk, _ = engine.get_gyukgook_detailed(ds, ys, ms, hs, mb, jjis=[hb, db, mb, yb], gans=[hs, ds, ms, ys])
    except Exception:
        gyuk = ""
    return (f"일주({ds}{db}) 성품: {i_val}\n월령({ms}{mb}) 태어난 계절의 기운: {w_val}\n"
            f"타고난 구조: {sd[0]} / {sd[1]} / {sd[2]}\n격: {gyuk}")

def build_saju_facts(sj, yong):
    g, j = sj['gans'], sj['jjis']
    cnt = " ".join(f"{k}{v}" for k, v in sj['counts'].items())
    return (f"사주 여덟 글자: 시 {g[0]}{j[0]} · 일 {g[1]}{j[1]} · 월 {g[2]}{j[2]} · 년 {g[3]}{j[3]}\n"
            f"오행 개수: {cnt}\n"
            f"중심오행 {yong.get('용신') or '-'} · 보조오행 {yong.get('희신') or '-'} · 피할 오행 {yong.get('기신') or '-'}")

_STAGES = [("원격", "초년운", 1, 19), ("형격", "청년운", 20, 38), ("이격", "중년운", 39, 58), ("정격", "말년운", 59, 77)]
_OH = {'목': '木', '화': '火', '토': '土', '금': '金', '수': '水'}
_ROLE_PT = {'용신': 1, '희신': 1, '한신': 0, '구신': -1, '기신': -1, '': 0}


def _oh_role(oh_han, yong):
    for role in ('용신', '희신', '기신', '구신', '한신'):
        if yong.get(role) and yong[role] == oh_han:
            return role
    return ''


def build_daewun_facts(engine, sj, yong, an=None):
    """네 격(시기)마다 걸치는 대운을 모으고, 이름의 격(길흉)과 겹쳐 본 교차 판정까지 사실문으로 만든다."""
    out = [f"대운수 {sj['calc_d']} ({'순행' if sj['order_dir'] == 1 else '역행'})"]
    for gname, stage, a0, a1 in _STAGES:
        items, tot, w_sum = [], 0.0, 0
        for d in sj['daewun']:
            lo = int(str(d['age_range']).split('~')[0])
            hi = lo + 9
            if hi < a0 or lo > a1:
                continue
            w = min(hi, a1) - max(lo, a0) + 1
            c1, c2 = engine.get_group_ss(d['ss_gan']), engine.get_group_ss(d['ss_ji'])
            og = _OH.get(engine.get_color(d['c_hangul']), '')
            oj = _OH.get(engine.get_color(d['j_hangul']), '')
            rg, rj = _oh_role(og, yong), _oh_role(oj, yong)
            tot += w * (_ROLE_PT[rg] + _ROLE_PT[rj]) / 2.0
            w_sum += w
            items.append(
                f"{d['age_range']} {d['c_hanja']}{d['j_hanja']}대운 (하늘기운 {og}={rg or '해당없음'} · 땅기운 {oj}={rj or '해당없음'}) "
                f"앞 5년 체({c1}) → 뒤 5년 체({c2}), 전환 {engine.get_che_relation(c1, c2)}, 12운성 {d['un_sung']}")
        line = f"{gname}({stage}) {a0}~{a1}세에 걸친 대운: " + (" / ".join(items) if items else "해당 없음")
        if w_sum:
            sc = tot / w_sum
            power = "힘이 있음" if sc >= 0.25 else ("약함" if sc <= -0.25 else "보통")
            line += f" // 이 시기 대운의 힘: {power}"
            if an and gname in an['네격']:
                good = an['네격'][gname]['길흉'] == '길'
                if good and power != "약함":
                    cross = "이름의 격과 대운이 함께 힘을 줌"
                elif good:
                    cross = "대운은 약하지만 이름의 격이 받쳐 줌"
                elif power != "약함":
                    cross = "이름의 격은 아쉽지만 대운이 받쳐 줌"
                else:
                    cross = "이름의 격과 대운이 모두 약해 조심이 필요함"
                line += f" // 교차 판정: {cross}"
        out.append(line)
    return "\n".join(out)

def render_naming_page(engine, u_product, gender, name, b_year, b_month, b_day, b_time, u_cal, ai_func=None, prompts_mod=None, html_views=None, choyeon_db=None):
    """app.py 가 부르는 입구(권장). 입력 확인 → 사주 계산 → 작명 화면. 반환: 판정 결과 dict 또는 None"""
    st.subheader("이름 풀이 및 짓기")
    sig = f"{name}|{gender}|{u_cal}|{b_year}-{b_month}-{b_day}|{b_time}|{u_product}"
    st.markdown("**① 입력하신 정보를 확인해 주세요** (왼쪽 입력창에서 고칠 수 있습니다)")
    if html_views is None or choyeon_db is None:   # 사주표를 못 그릴 때만 간단한 표를 보여 줌
        st.markdown(
            f"| 이름 | 성별 | 생년월일 | 태어난 시간 |\n|---|---|---|---|\n"
            f"| {name} | {gender} | {u_cal} {b_year}년 {b_month}월 {b_day}일 | {b_time} |"
        )
    if "모름" in str(b_time):
        st.warning("태어난 시간을 모르면 시(時) 기둥 없이 세 기둥으로 용신을 정하므로 정확도가 낮아질 수 있습니다.")
    saju_html = ""
    if html_views is not None and choyeon_db is not None:
        try:
            saju_html = render_saju_block(engine, html_views, choyeon_db,
                              saju_from_inputs(engine, b_year, b_month, b_day, b_time, u_cal, gender),
                              name, gender, b_year, b_month, b_day, b_time, u_cal)
        except Exception as e:
            st.caption(f"(사주표를 표시하지 못했습니다: {e})")
    started = (st.session_state.get("nm_started_sig") == sig) or bool(st.session_state.get('nm_pre'))
    if not started:
        st.info("정보가 맞으면 아래 버튼을 눌러 작명을 시작하세요. 입력 정보를 바꾸면 다시 눌러야 합니다.")
        if st.button("✨ 이 정보로 작명 시작", key="nm_start_btn", type="primary"):
            st.session_state["nm_started_sig"] = sig
            st.rerun()
        return None
    try:
        sj = saju_from_inputs(engine, b_year, b_month, b_day, b_time, u_cal, gender)
    except Exception as e:
        st.error(f"사주를 계산하지 못했습니다. 생년월일과 시간을 확인해 주세요. ({e})")
        return None
    st.caption(f"사주 여덟 글자  시 {sj['gans'][0]}{sj['jjis'][0]} · 일 {sj['gans'][1]}{sj['jjis'][1]} · 월 {sj['gans'][2]}{sj['jjis'][2]} · 년 {sj['gans'][3]}{sj['jjis'][3]}")
    st.markdown("**② 성씨와 이름 글자를 골라 주세요**")
    an = render_naming_product(u_product, sj['yong_el'], gender, name)
    if an is None or ai_func is None or prompts_mod is None:
        return an
    if str(u_product).startswith("4-3"):
        render_onepage_43(engine, sj, name, gender, b_year, b_month, b_day, b_time, u_cal, ai_func, html_views, choyeon_db)
        return an
    st.divider()
    st.markdown("**③ 풀이글 받기**")
    rkey = f"{sig}|{an['이름']}"
    _have = st.session_state.get("nm_report")
    _auto = str(u_product).startswith("4-1") and bool(st.session_state.get('nm_pre')) and not (_have and _have[0] == rkey)
    if st.button("📜 이 이름 풀이글 받기", key="nm_report_btn", type="primary") or _auto:
        var = PROMPT_NAME.get(str(u_product)[:3])
        tpl = getattr(prompts_mod, var, "") if var else ""
        if not tpl:
            st.error(f"prompts.py 에 '{var}' 가 없습니다.")
        else:
            data = {"name": name, "golden_facts": build_golden_facts(engine, sj, choyeon_db),
                    "user_concern": str(st.session_state.get("user_concern", "") or "").strip(),
                    "saju_facts": build_saju_facts(sj, yong_from_engine(sj['yong_el'] or {})) + "\n" + engine.get_eumyang_facts(sj['gans'], sj['jjis']),
                    "naming_facts": build_naming_facts(an, yong_from_engine(sj['yong_el'] or {})),
                    "daewun_facts": build_daewun_facts(engine, sj, yong_from_engine(sj['yong_el'] or {}), an)}
            with st.spinner("풀이글을 쓰고 있습니다. 1~2분 걸립니다..."):
                text = ai_func(tpl.format_map(_SafeDict(data)))
            st.session_state["nm_report"] = (rkey, text)
    rep = st.session_state.get("nm_report")
    if rep and rep[0] == rkey:
        st.markdown(prepare_report_text(rep[1]))
        cover = make_cover(html_views, u_product, name, gender, b_year, b_month, b_day, b_time, u_cal)
        body = (saju_html
                + html_views.format_ai_text_to_html(prepare_report_text(rep[1]), "", name)
                + naming_notice_html(u_product, an)
                + naming_closing_html(name, html_views.get_choyeon_sign_html()))
        final_html = cover + html_views.get_final_report_box(body)
        st.session_state['saved_report_html'] = final_html
        gid = st.session_state.get('admin_proc_id')
        if gid:
            st.divider()
            st.markdown("**④ 신청자에게 보내기 준비**")
            if st.button("📤 이 결과를 발송 서랍장으로 보내기", key="nm_send_btn", type="primary"):
                st.session_state[f'html_{gid}'] = final_html
                st.session_state['app_running'] = False
                st.session_state['admin_proc_id'] = None
                st.rerun()
    return an

import re, datetime as _dtm

def split_paragraphs(text, per=2):
    """풀이글의 긴 문단을 문맥(문장) 단위로 2문장씩 끊어 줄바꿈한다. 제목 줄은 그대로 둔다."""
    out = []
    for raw in str(text or "").split("\n"):
        line = raw.strip()
        if not line:
            out.append("")
            continue
        is_head = bool(re.match(r'^(\d+[\.\)]|\(\d+\)|[①-⑩◆▶▷])\s*', line)) or len(line) < 45
        if is_head:
            out.append(line)
            continue
        sents = re.split(r'(?<=[다요죠함])\.\s+', line)
        sents = [s if s.endswith('.') else s + '.' for s in sents if s.strip()]
        chunks, buf = [], []
        for s in sents:
            buf.append(s)
            if len(buf) >= per:
                chunks.append(" ".join(buf)); buf = []
        if buf:
            if chunks and len(buf) == 1 and len(buf[0]) < 60:
                chunks[-1] += " " + buf[0]
            else:
                chunks.append(" ".join(buf))
        out.append("\n\n".join(chunks))
    return "\n".join(out)


def prepare_report_text(text):
    return split_paragraphs(text)


NAMING_TITLE = {"4-1": "이름 풀이 감명서", "4-2": "이름 바꾸기 감명서", "4-3": "신생아 이름짓기 감명서"}


def make_cover(hv, u_product, name, gender, b_year, b_month, b_day, b_time, u_cal):
    from korean_lunar_calendar import KoreanLunarCalendar
    klc = KoreanLunarCalendar()
    if "음력" in u_cal:
        klc.setLunarDate(int(b_year), int(b_month), int(b_day), "윤달" in u_cal)
        sol = f"{klc.solarYear}년 {klc.solarMonth:02d}월 {klc.solarDay:02d}일"
        lun = f"{int(b_year)}년 {int(b_month):02d}월 {int(b_day):02d}일"
    else:
        klc.setSolarDate(int(b_year), int(b_month), int(b_day))
        sol = f"{int(b_year)}년 {int(b_month):02d}월 {int(b_day):02d}일"
        lun = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일"
    tstr = b_time if b_time != "시간 모름" else "시간 미상"
    icon = "♂️" if str(gender).startswith('남') else "♀️"
    try:
        from zoneinfo import ZoneInfo
        now = _dtm.datetime.now(ZoneInfo('Asia/Seoul'))
    except Exception:
        now = _dtm.datetime.now()
    today = f"{now.year}년 {now.month}월 {now.day}일"
    title = NAMING_TITLE.get(str(u_product)[:3], "이름 풀이 감명서")
    return hv.get_personal_cover("초연 작명법", title, icon, name, sol, lun, tstr, today)


def naming_closing_html(name, sign_html=""):
    p = "style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'"
    b = "<span style='font-weight:600;'>"
    return f"""
    <div style='margin-top: 12px;'>
        <hr style='border: 0; border-top: 2px dashed #1A237E; margin: 18px 0 12px 0;'>
        <p {p}>이름은 하루에도 수없이 불리고 쓰이면서 {b}소리와 글자의 기운</span>이 삶에 조금씩 스며드는 것이라 봅니다. 그래서 초연 작명법은 이름 하나만 따로 보지 않고, 타고난 사주가 필요로 하는 기운과 평생의 흐름(대운)이 이름과 어떻게 만나는지를 함께 살펴 풀이했습니다.</p>
        <p {p}>다만 이름은 사주를 대신하는 것이 아니라 {b}사주를 곁에서 돕는 기운</span>입니다. 좋은 이름이 모든 일을 이루어 주지도, 아쉬운 이름이 삶을 가로막지도 않습니다. {b}{name}님</span>이 이 풀이를 이름과 삶을 가꾸는 하나의 참고로 삼아 주신다면 더없이 기쁘겠습니다.</p>
        <div style='page-break-inside: avoid; break-inside: avoid;'>
        <p {p}>이름에 관한 더 깊은 궁금증이나 앞으로의 고민이 있으시면 언제든 초연 시공명리를 다시 찾아 주십시오. {b}{name}님</span>의 앞날에 따뜻한 기운이 늘 함께하기를 바랍니다.</p>
        <div style='display: flex; justify-content: flex-end; align-items: center; gap: 18px; margin-top: 14px;'>
            <div style='text-align: right;'>
                <div style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 -</div>
                <div style='font-weight: 900; font-size: 18px; color: #1A237E; margin-top: 4px;'>사주박사 드림</div>
            </div>
            {sign_html}
        </div>
        </div>
    </div>
    """

# 이름 후보에서 뺄 글자: 열두 띠 글자와 돼지 뜻 글자 (박사님이 더 넣으려면 여기에 글자를 추가)
_NO_NAME = set('子丑寅卯辰巳午未申酉戌亥豚豕')


# 소리 내어 부르면 이상한 뜻이 되는 말 (성씨 + 이름 전체 독음에 들어 있으면 후보에서 뺌). 박사님이 계속 추가하십시오.
_BAD_READING = ('소심', '이리', '바보', '병신', '시발', '씨발', '개새', '똥', '방귀', '방구', '변태', '호구', '멍청',
                '죽어', '죽음', '자살', '꼴통', '돼지', '이년', '미친', '꺼져', '거지', '도둑', '찐따', '왕따', '쓰레기')

def _bad_reading(reading):
    return any(w in str(reading) for w in _BAD_READING)

def _order_exclude(neng, order):
    """몇째 자녀인가에 따라 책 9장의 장자/차자 불용한자를 뺄 글자 목록"""
    if str(order).startswith("첫째"):
        return [x['h'] for x in neng.hanja if x.get('j')]
    if str(order).startswith("둘째"):
        return [x['h'] for x in neng.hanja if x.get('c')]
    return []


def _cand_pools(neng, sur, yong, fixed, fixed_pos, n=5, order_ex=()):
    """뜻 좋은 교육용 글자 → 부족하면 교육용(흔히 쓰는) 글자 전체로 넓혀서 후보를 뽑고, (단계, 점수) 순서로 정렬"""
    pools = [
        [x['h'] for x in neng.hanja if not (x.get('g') and x.get('e'))],
        [x['h'] for x in neng.hanja if not x.get('e') or x['h'] in _NO_NAME],
    ]
    allc, seen = [], set()
    for ex in pools:
        ex = list(ex) + list(order_ex)
        r = neng.auto_candidates(sur, yong, fixed, fixed_pos, exclude=ex, n=n + 10)
        for c in r['후보']:
            if c['이름'] in seen or _bad_reading(c['독음']):
                continue
            seen.add(c['이름']); allc.append(c)
        if len([c for c in allc if c['단계'] == 0]) >= n:
            break
    allc.sort(key=lambda c: (c['단계'], -c['점수']))
    top = allc[:n]
    lv = max([c['단계'] for c in top], default=0)
    return {'후보': top, '완화단계': lv, '부족': len(top) < n}


def _flow_auto_pick(neng, sur, yong, fixed_pos, fixed, key):
    """후보 이름을 엔진이 우선순위대로 뽑아 보여 주고, 박사님이 하나를 고른다"""
    fp = {'가운데 글자': 'first', '마지막 글자': 'last'}.get(fixed_pos, 'last')
    order = st.radio("몇째 자녀입니까? (책 9장: 장자·차자 불용한자 가림)", ["첫째 (장자)", "둘째 이하 (차자)", "가리지 않음"], horizontal=True, index=2, key=f"{key}_order")
    oex = _order_exclude(neng, order)
    ck = f"{order}|{key}_cand|{sur['h']}|{sorted((k, v) for k, v in yong.items())}|{fixed['h'] if fixed else ''}|{fp}"
    if st.session_state.get('nm_cand_key') != ck:
        with st.spinner("후보 이름을 찾고 있습니다..."):
            with_f = _cand_pools(neng, sur, yong, fixed, fp, order_ex=oex) if fixed else None
            free = _cand_pools(neng, sur, yong, None, fp, order_ex=oex)
        st.session_state['nm_cand_key'] = ck
        st.session_state['nm_cand'] = (with_f, free)
    with_f, free = st.session_state['nm_cand']
    use = free
    if fixed is not None:
        worse = (with_f['완화단계'] > free['완화단계']) or (len(with_f['후보']) < min(5, len(free['후보'])))
        if worse:
            st.warning("돌림자를 쓰면 후보가 모자라거나 조건이 완화됩니다. 돌림자 없이 짓는 쪽이 더 좋을 수 있으니 두 가지를 비교해 보세요.")
        view = st.radio("보기", ["돌림자를 쓴 후보", "돌림자 없이 지은 후보"], horizontal=True, key=f"{key}_view")
        use = with_f if view == "돌림자를 쓴 후보" else free
    cands = use['후보']
    if not cands:
        st.warning("조건에 맞는 후보를 찾지 못했습니다. 돌림자나 이름 글자 수를 바꿔 보세요.")
        return None
    if use['완화단계'] > 0:
        st.info("소리·자원·수리가 모두 길한 후보가 부족하여 일부 조건을 완화했습니다. (수리 네 격의 길은 항상 지켰습니다.)")
    st.markdown("**추천 후보 (우선순위 순)**")
    rows, ans, warns = [], [], []
    for i, c in enumerate(cands):
        an = neng.analyze_name(sur, c['A'], c['B'], yong)
        ans.append(an)
        gy = ' · '.join(f"{v['수리']}{'✅' if v['길흉'] == '길' else '⚠️'}" for v in an['네격'].values())
        mean = f"{c['A']['hun'].split('/')[0]} + {c['B']['hun'].split('/')[0]}"
        _sf = ' → '.join(x[0] for x in an['소리배합']) + f" ({' · '.join(an['소리관계'])})"
        _rf = ' → '.join(x[0] for x in an['자원배합']) + f" ({' · '.join(an['자원관계'])})"
        _w = [f"{k['h']}:{k['dj']}" for k in (c['A'], c['B']) if k and k.get('dj')]
        _w += [f"{k['h']}({k['de']})" for k in (c['A'], c['B']) if k and k.get('de')]
        warns.append(f"{an['이름']} — " + ' / '.join(_w)) if _w else None
        rows.append(f"| {i + 1} | **{an['이름']}** ({an['독음']}){' ⚠️소리주의' if _w else ''} | {mean} | {_sf} {an['소리판정']} | {_rf} {an['자원판정']} | {gy} | {'포함' if an['용신포함'] else '미포함'} |")
    st.markdown("| 순위 | 이름 | 뜻 | 소리 | 자원 | 수리(원·형·이·정) | 중심오행 |\n|---|---|---|---|---|---|---|\n" + "\n".join(rows))
    st.session_state['nm_last_ans'] = [dict(a_, A=c_['A'], B=c_['B']) for a_, c_ in zip(ans, cands)]
    if warns:
        st.caption("⚠️ 소리주의 (책 9장 동자이음·동음이의): " + " ; ".join(warns))
    i = st.radio("이 후보로 풀이를 진행합니다", range(len(cands)), format_func=lambda i: f"{i + 1}순위  {ans[i]['이름']} ({ans[i]['독음']})", key=f"{key}_pick", horizontal=True)
    return ans[i]

# ======================================================================
# 4-3 신생아 이름짓기 : 한 장짜리 '작명서' (naming_ui.py 맨 아래에 붙여 넣기)
# ======================================================================
import re as _re

_OP_SECTIONS = [("성품", "타고난 성품과 이름의 기운", "4문장"),
                ("이름1", "추천 ① 풀이", "3~4문장"),
                ("이름2", "추천 ② 풀이", "3~4문장"),
                ("배우자궁", "배우자궁 · 인연", "3문장"),
                ("대운", "평생 흐름 (대운)", "3문장"),
                ("양육", "부모님께 드리는 양육 한마디", "3문장")]


def _onepage_prompt(name, gender, golden, saju, an1, an2, dw1, dw2, ilji):
    return f"""당신은 '초연 시공명리 연구소'의 사주박사입니다. 신생아(아기)에게 지어 줄 이름 두 개를 추천하는 한 장짜리 작명서의 풀이글을 씁니다.
부모님이 읽는 글이므로 쉬운 말로, 따뜻하고 품위 있게 씁니다. 아기를 '이 아기'라고 부르고 '당신'이라 하지 않습니다.
아래 [자료]에 없는 사실(오행, 수리, 뜻)은 지어내지 말고, 자료에 적힌 판정만 그대로 풀어 쓰십시오.

[자료]
아기 성별: {gender}
{saju}
{golden}
배우자궁(일지): {ilji}

[추천 ① 이름 자료]
{build_naming_facts(an1)}
{dw1}

[추천 ② 이름 자료]
{build_naming_facts(an2)}
{dw2}

[출력 형식 — 반드시 아래 6개 표지를 그대로 쓰고, 각 표지 다음 줄부터 본문만 쓰십시오. 제목·번호·마크다운·맺음말은 쓰지 않습니다.]
[[성품]]  (4문장: 일주·월령 성품, 사주에서 필요한 기운, 이름이 그것을 어떻게 채우는지)
[[이름1]] (3~4문장: 추천 ① 글자 뜻, 소리·자원오행 흐름, 수리 네 격의 길흉, 이름의 한 줄 장점)
[[이름2]] (3~4문장: 추천 ② 같은 방식. 추천 ①과 다른 점을 한 가지 밝힐 것)
[[배우자궁]] (3문장: 일지의 기운으로 본 배우자 인연, 이름이 돕는 점, 조심할 점 한 가지)
[[대운]] (3문장: 초년·중년·말년의 대운 흐름과 이름의 격이 만나는 모습. 대운 자료의 교차 판정을 따를 것)
[[양육]] (3문장: 이 아기를 키울 때의 마음가짐과 부족한 오행을 채워 주는 생활 습관)
"""


def _parse_onepage(text):
    got = {}
    for key, body in _re.findall(r"\[\[(\S+?)\]\]\s*(.*?)(?=\[\[\S+?\]\]|\Z)", str(text), flags=_re.S):
        got[key] = " ".join(body.split())
    return got


def onepage_html(html_views, name, gender, birth_txt, yong, an1, an2, sec, warn_txt, order_txt, today_txt):
    def _p(key):
        return sec.get(key) or "(풀이글을 받지 못했습니다. 다시 만들어 주십시오.)"

    def _card(rank, an):
        gy = "".join(f"<span>{k} {v['수리']} {v['길흉']}</span>" for k, v in an['네격'].items())
        names = " · ".join(k['hun'].split('/')[0] for k in (an.get('A'), an.get('B')) if k)
        return (f"<div class='op-nm'><span class='op-rk'>추천 {rank}</span><div class='op-h'>{an['이름']}</div>"
                f"<div class='op-k'>{an['독음']}</div><div class='op-m'>{names}<br>소리 {an['소리판정']} · 자원 {an['자원판정']}</div>"
                f"<div class='op-chips'>{gy}</div></div>")

    css = """<style>
    .op-wrap{display:flex;flex-direction:column;min-height:245mm;font-family:'Noto Serif KR',serif;color:#222}
    .op-t{text-align:center;color:#1A237E;font-size:34px;font-weight:900;letter-spacing:14px;margin:4px 0 2px}
    .op-s{text-align:center;color:#8a6d1f;font-size:13px;letter-spacing:3px;margin-bottom:12px}
    .op-who{text-align:center;font-size:14px;color:#444;border-top:1px solid #c9b46a;border-bottom:1px solid #c9b46a;padding:7px;margin-bottom:12px}
    .op-names{display:flex;gap:16px;margin-bottom:10px}
    .op-nm{flex:1;border:2px solid #1A237E;border-radius:10px;padding:10px;text-align:center;background:#fff}
    .op-rk{display:inline-block;background:#1A237E;color:#fff;border-radius:12px;padding:1px 12px;font-size:12px}
    .op-h{font-size:44px;font-weight:900;color:#1A237E;letter-spacing:6px;margin:2px 0 0}
    .op-k{font-size:20px;font-weight:700;margin-bottom:4px}
    .op-m{font-size:12px;color:#555;line-height:1.6}
    .op-chips{display:flex;gap:5px;justify-content:center;margin-top:7px;font-size:11px;flex-wrap:wrap}
    .op-chips span{background:#eef0fb;border-radius:10px;padding:2px 8px;color:#1A237E}
    .op-wrap h3{font-size:15px;color:#1A237E;margin:9px 0 4px;border-left:5px solid #c9a227;padding-left:8px}
    .op-wrap p{font-size:12.5px;line-height:1.7;margin:0 0 4px;text-align:justify;text-indent:10px}
    .op-row{display:flex;gap:14px}.op-row>div{flex:1}
    .op-box{background:#f5f7ff;border-radius:8px;padding:8px 12px}
    .op-ft{margin-top:auto;padding-top:8px;display:flex;justify-content:flex-end;align-items:center;gap:16px}
    .op-ft b{color:#1A237E;font-size:16px;display:block;text-align:right}
    </style>"""
    box = f"✔ 소리 주의: {warn_txt or '해당 글자 없음'} &nbsp; ✔ 불용한자: 책 9장 기준 적용 &nbsp; ✔ {order_txt}<br>✔ 도장·서명에는 한자 이름을 그대로 쓰시면 기운이 온전히 전해집니다."
    sign = html_views.get_choyeon_sign_html()
    inner = f"""{css}<div class='op-wrap'>
    <div class='op-t'>作 名 書</div><div class='op-s'>초연 시공명리 · 신생아 이름짓기</div>
    <div class='op-who'>{name} ({gender}) · {birth_txt} &nbsp;|&nbsp; 성씨 {an1['이름'][0]} &nbsp;|&nbsp; 중심오행 <b>{yong.get('용신') or '-'}</b> · 보조 <b>{yong.get('희신') or '-'}</b> · 피할 오행 {yong.get('기신') or '-'}</div>
    <div class='op-names'>{_card('①', an1)}{_card('②', an2)}</div>
    <h3>타고난 성품과 이름의 기운</h3><p>{_p('성품')}</p>
    <div class='op-row'><div><h3>추천 ① {an1['이름']} 풀이</h3><p>{_p('이름1')}</p></div>
    <div><h3>추천 ② {an2['이름']} 풀이</h3><p>{_p('이름2')}</p></div></div>
    <div class='op-row'><div><h3>배우자궁 · 인연</h3><p>{_p('배우자궁')}</p></div>
    <div><h3>평생 흐름 (대운)</h3><p>{_p('대운')}</p></div></div>
    <h3>부모님께 드리는 양육 한마디</h3><p>{_p('양육')}</p>
    <h3>이름 쓸 때 주의할 점</h3><div class='op-box'><p>{box}</p></div>
    <div class='op-ft'><div style='margin-right:auto;font-size:13px;color:#555'>발행일 &nbsp;{today_txt}</div>
    <div><b>- 초연 시공명리 연구소 -</b><b>사주박사 드림</b></div>{sign}</div>
    </div>"""
    return html_views.get_final_report_box(inner)


def render_onepage_43(engine, sj, name, gender, b_year, b_month, b_day, b_time, u_cal, ai_func, html_views, choyeon_db):
    """4-3: 위 후보 표에서 두 이름을 골라 한 장짜리 작명서를 만든다"""
    import datetime as _dt
    ans = st.session_state.get('nm_last_ans') or []
    if len(ans) < 2:
        st.info("추천 후보가 두 개 이상 나오면 한 장짜리 작명서를 만들 수 있습니다.")
        return
    st.divider()
    st.markdown("**③ 한 장 작명서에 올릴 추천 이름 2개 고르기** (처음에는 1·2순위가 선택되어 있습니다)")
    labels = [f"{i + 1}순위 {a['이름']} ({a['독음']})" for i, a in enumerate(ans)]
    pick = st.multiselect("추천 이름 두 개", labels, default=labels[:2], max_selections=2, key="op_pick")
    if len(pick) != 2:
        st.warning("이름을 정확히 2개 골라 주세요.")
        return
    an1, an2 = [ans[labels.index(p)] for p in pick]
    sig = f"{an1['이름']}|{an2['이름']}|{name}|{b_year}{b_month}{b_day}{b_time}"
    if st.button("📜 한 장 작명서 만들기", key="op_make_btn", type="primary"):
        yong = yong_from_engine(sj['yong_el'] or {})
        ilji = f"{sj['gans'][1]}{sj['jjis'][1]}일주의 일지 {sj['jjis'][1]}"
        prompt = _onepage_prompt(name, gender,
                                 build_golden_facts(engine, sj, choyeon_db),
                                 build_saju_facts(sj, yong) + "\n" + engine.get_eumyang_facts(sj['gans'], sj['jjis']),
                                 an1, an2, build_daewun_facts(engine, sj, yong, an1), build_daewun_facts(engine, sj, yong, an2), ilji)
        with st.spinner("작명서를 쓰고 있습니다. 1~2분 걸립니다..."):
            text = ai_func(prompt)
        st.session_state['op_text'] = (sig, text)
    got = st.session_state.get('op_text')
    if not got or got[0] != sig:
        return
    sec = _parse_onepage(got[1])
    yong = yong_from_engine(sj['yong_el'] or {})
    warns = []
    for an in (an1, an2):
        for k in (an.get('A'), an.get('B')):
            if k and k.get('dj'):
                warns.append(f"{k['h']}({k['dj']})")
            if k and k.get('de'):
                warns.append(f"{k['h']}({k['de']})")
    order_txt = {"첫째": "첫째(장자) 기준 적용", "둘째": "둘째 이하(차자) 기준 적용"}.get(str(st.session_state.get('nm_4-3_order', ''))[:2], "출생 순서는 가리지 않음")
    try:
        from zoneinfo import ZoneInfo
        today = _dt.datetime.now(ZoneInfo('Asia/Seoul'))
    except Exception:
        today = _dt.datetime.now()
    birth_txt = f"{u_cal} {b_year}년 {b_month}월 {b_day}일 {b_time}생"
    html = onepage_html(html_views, name, gender, birth_txt, yong, an1, an2, sec, ", ".join(dict.fromkeys(warns)), order_txt,
                        f"{today.year}년 {today.month}월 {today.day}일")
    st.session_state['saved_report_html'] = html
    st.markdown(html, unsafe_allow_html=True)
    gid = st.session_state.get('admin_proc_id')
    if gid:
        st.divider()
        st.markdown("**④ 신청자에게 보내기 준비**")
        if st.button("📤 이 결과를 발송 서랍장으로 보내기", key="op_send_btn", type="primary"):
            st.session_state[f"html_{gid}"] = html
            st.session_state['app_running'] = False
            st.session_state['admin_proc_id'] = None
            st.rerun()

