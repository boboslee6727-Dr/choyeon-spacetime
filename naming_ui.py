# -*- coding: utf-8 -*-
"""
이름 풀이 및 짓기 화면 (naming_ui.py)  v1.5
- app.py 에서는 아래 두 줄만 부르면 된다.
    import naming_ui
    result = naming_ui.render_naming_product(u_product, yong_el, gender, name)   # yong_el = engine.get_yongshin_elements(...) 결과
- 화면 순서: 성씨 입력 → (돌림자) → 가운데 글자 고르기 → 끝 글자 고르기 → 판정표
- 기존 engine.py / 사주 화면은 건드리지 않는다.
"""
import os
import streamlit as st
from naming_engine import NamingEngine, yong_from_engine, rel
import naming_onepage as op
import naming_hangul as hg

# 흔한 성씨 한자는 후보 맨 앞에 (예: '이' -> 李 가 먼저)
COMMON_SURNAME_HANJA = "金李朴崔鄭姜趙尹張林韓吳申徐權黃安宋柳洪全高文孫梁裵白曺許南劉盧沈河郭成車朱禹具辛任田閔愈"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'naming_db.json')
TIER_LABELS = ["흔한 글자 + 뜻 좋은 글자 (권장)", "뜻 좋은 글자 전체", "모든 글자 (인명용 한자 전체)"]


@st.cache_resource(show_spinner=False)
def get_neng():
    _ne = NamingEngine(DB_PATH)
    for _x in _ne.hanja:
        if _x['h'] in _NAME_OK:
            _x['e'] = 1
            _x['g'] = 1
    return _ne

def _tier_exclude(neng, tier):
    if tier == 0:
        return [x['h'] for x in neng.hanja if not (x.get('g') and x.get('e'))]
    if tier == 1:
        return [x['h'] for x in neng.hanja if not x.get('g')]
    return []


def _hanja_label(x):
    hun = x['hun'].split('/')[0]
    return f"{x['h']}  {hun}  ({x['st']}획 · 자원{x['ja']} · 소리{x['bo']})" + (" ⚠️피해야 할 불용한자" if x.get('x') else (" ⚠️" + x['ex'] if x.get('ex') else ""))


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


def pick_hanja(neng, label, key, help_text="", allow_bad=False, pre=None):
    """한글 한 글자 입력 → 한자 후보 선택. 반환: 한자 dict(없으면 None). pre = 신청서에서 받은 {'r','h'}"""
    if pre and f"{key}_rd" not in st.session_state:
        st.session_state[f"{key}_rd"] = pre['r']
    rd = st.text_input(label, key=f"{key}_rd", help=help_text, max_chars=1).strip()
    if not rd:
        return None
    cands = [x for x in neng.find_by_reading(rd) if allow_bad or x['h'] not in neng.bad]
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
    if an.get('한글'):
        return hg.show_hangul(st, an)
    st.markdown(f"### {an['이름']} ({an['독음']})")
    c1, c2 = st.columns(2)
    _n1, _n2 = _book_note(an, '소리'), _book_note(an, '자원')
    c1.markdown(f"**소리오행** {_chain_text(an, '소리')}  \n판정: **{an['소리판정']}**" + (f"  \n📖 {_n1}" if _n1 else ""))
    c2.markdown(f"**자원오행** {_chain_text(an, '자원')}  \n판정: **{an['자원판정']}**" + (f"  \n📖 {_n2}" if _n2 else ""))
    _el = an['소리배합']
    if len(an['독음']) == len(_el):
        _cho = [(_CHO[(ord(r) - 0xAC00) // 588] if 0 <= ord(r) - 0xAC00 < 11172 else r) for r in an['독음']]
        st.caption("초성 오행: " + " · ".join(f"{r} {c}({e})" for r, c, e in zip(an['독음'], _cho, _el)))
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
    order = st.radio("몇째 자녀입니까? (책 9장: 장자·차자 불용한자 가림)", ["첫째 (장자/장녀)", "둘째 이하 (차자/차녀)", "가리지 않음"], horizontal=True, index=2, key=f"{key}_order1")
    _ex = [x['h'] for x in neng.hanja if not x.get('e') or x['h'] in _NO_NAME] + _order_exclude(neng, order)
    cands = neng.single_candidates(sur, yong, exclude=_ex)
    cands = _ai_filter_single(cands, sur)
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
    an = neng.analyze_name(sur, cands[i], None, yong)
    an['글자뜻'] = _meaning_line(cands[i], None)
    return an

def _flow_new_name(neng, sur, yong, gender, key):
    """4-2 이름 바꾸기 / 4-3 신생아 이름짓기: 가운데 글자 → 끝 글자 고르기 (외자 선택 가능)"""
    neng.gender = gender
    neng.set_want(None)      # 오행 직접 지정은 '기존 방식'의 후보 뽑기에서만 쓴다
    pre = st.session_state.get('nm_pre') or {}
    
    if st.radio("이름을 정하는 방법", ["기존 방식 (조건에 맞는 한자부터 고르기)", "한글 이름을 먼저 고르고 한자 찾기"], horizontal=True, key=f"{key}_how").startswith("한글"):
        return _flow_hangul_pick(neng, sur, yong, gender, key)
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
    _bd = [f"{k['h']}({k['hun'].split('/')[0]})" for k in (A, B) if k and (k.get('x') or k.get('ex'))]
    if _bd:
        st.warning("책 9장 '피해야 할 불용한자'가 들어 있습니다: " + ", ".join(_bd) + " — 뜻이 좋지 않아 이름에 쓰지 않도록 권하는 글자입니다.")
    an = neng.analyze_name(sur, A, B, yong)
    an['글자뜻'] = _meaning_line(A, B)
    an['불용한자'] = ", ".join(_bd)
    return an


def _flow_check_name(neng, sur, yong, key):
    """4-1 이름 풀이: 지금 이름의 글자를 한자로 골라 판정"""
    st.markdown("**현재 이름의 한자를 골라 주세요** (성씨를 뺀 이름 글자)")
    pre = st.session_state.get('nm_pre') or {}
    cur = pre.get('cur') or [None, None]
    st.session_state.setdefault(f"{key}_n", pre.get('n_cur', 2))
    n = st.radio("이름 글자 수", [2, 1], format_func=lambda n: "두 글자 (예: 수연)" if n == 2 else "한 글자 (예: 솔)", horizontal=True, key=f"{key}_n")
    A = pick_hanja(neng, "이름 첫 글자 (한글)", f"{key}_c1", allow_bad=True)
    B = pick_hanja(neng, "이름 둘째 글자 (한글)", f"{key}_c2", allow_bad=True) if n == 2 else None
    if A is None or (n == 2 and B is None):
        return None
    _bd = [f"{k['h']}({k['hun'].split('/')[0]})" for k in (A, B) if k and (k.get('x') or k.get('ex'))]
    if _bd:
        st.warning("책 9장 '피해야 할 불용한자'가 들어 있습니다: " + ", ".join(_bd) + " — 뜻이 좋지 않아 이름에 쓰지 않도록 권하는 글자입니다.")
    an = neng.analyze_name(sur, A, B, yong)
    an['글자뜻'] = _meaning_line(A, B)
    an['불용한자'] = ", ".join(_bd)
    return an


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
    is41 = str(u_product).startswith("4-1")
    is42 = str(u_product).startswith("4-2")
    _pre = st.session_state.get('nm_pre') or {}
    cur = None
    if is42:
        st.markdown("**현재 이름** (새 이름과 비교하기 위해 입력합니다)")
        _ct = st.radio("현재 이름", ["입력 안 함", "한자가 있는 이름", "순수 한글 이름"], horizontal=True, key=f"{key}_curtype")
        if _ct.startswith("한자"):
            cur = _flow_check_name(neng, sur, yong, f"{key}_cur")
        elif _ct.startswith("순수"):
            cur = hg.flow_check(st, sur, yong, f"{key}_cur")
        if cur:
            st.markdown("**현재 이름 판정**")
            show_analysis(cur)
    _modes = ["한글(한자) 이름", "순수 한글 이름"] + ([] if is41 else ["한글(한자) 이름 + 순수 한글 이름 둘 다"])
    mode = st.radio("어떤 이름을 원하십니까?", _modes, index=1 if _pre.get('script') == '한글 이름' else 0, horizontal=True, key=f"{key}_mode")
    _sj = _AI.get('saju', '')
    _bad = lambda rd: _bad_reading(rd)
    if mode.startswith("순수"):
        if is41:
            an = hg.flow_check(st, sur, yong, key)
        else:
            an, _l = hg.flow_new(st, sur, yong, g, key, _AI.get('f'), _sj, _bad)
            st.session_state['nm_last_ans'] = _l
    elif mode.startswith("한글(한자) 이름 +"):
        st.session_state['nm_last_ans'] = []
        st.markdown("#### ⓐ 한글(한자) 이름 후보")
        an_h = _flow_new_name(neng, sur, yong, g, key)
        _lh = list(st.session_state.get('nm_last_ans') or [])
        st.markdown("#### ⓑ 순수 한글 이름 후보")
        an_g, _lg = hg.flow_new(st, sur, yong, g, key, _AI.get('f'), _sj, _bad)
        st.session_state['nm_last_ans'] = _lh + _lg
        _opt = [x for x, a_ in (("한글(한자) 이름", an_h), ("순수 한글 이름", an_g)) if a_]
        if not _opt:
            return None
        _w = st.radio("풀이에 쓸 이름", _opt, horizontal=True, key=f"{key}_which")
        an = an_h if _w.startswith("한글(한자)") else an_g
    else:
        an = _flow_check_name(neng, sur, yong, key) if is41 else _flow_new_name(neng, sur, yong, g, key)
    if an:
        show_analysis(an)
    if cur and an:
        hg.show_compare(st, cur, an)
    st.session_state['nm_cmp_facts'] = hg.compare_facts(cur, an) if (cur and an) else ''
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
    _b43 = str(st.session_state.get('sub_category_4', '')).startswith("4-3")
    _hdr = hv.get_info_header(icon, "신생아" if _b43 else name, gender, marital, age, sol_str, lun_str, time_str)
    if _b43: _hdr = _hdr.replace(f", {marital},", ",")
    parts = [
        _hdr,
        hv.generate_saju_table_data(gans, jjis, ds, gender, engine),
        hv.get_master_bar(sj['calc_d'], counts['목'], counts['화'], counts['토'], counts['금'], counts['수'],
                          guiin_map.get(ds, '없음'), n_gong, i_gong, samjae_color, cur_samjae, yongshin_text=sj['yong_text']),
        hv.generate_daewun_layout(dw, direction, sj['calc_d'], engine.get_oh_class),
    ]
    # [추가] 4-1 이름 풀이: 대운표 아래에 십성 흐름 그림
    if str(st.session_state.get('sub_category_4', '')).startswith("4-1"):
        try:
            import flow_chart
            parts.append(flow_chart.build_flow_html(engine, ds, gans, jjis, int(sol_y), dw, curr_year))
        except Exception as _fe:
            st.warning(f"⚠️ [십성의 흐름] 그림표를 만들지 못했습니다: {type(_fe).__name__}: {_fe}")
    try:
        w_key, i_key = f"{ms}{mb}".strip(), f"{ds}{db}".strip()
        w_val = cdb.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
        i_val = cdb.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
        sd = cdb.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
        gyuk, _ = engine.get_gyukgook_detailed(ds, ys, ms, hs, mb, jjis=[hb, db, mb, yb], gans=[hs, ds, ms, ys])
        parts.append(hv.get_golden_text("신생아" if _b43 else name, w_val, i_val, sd[0], sd[1], sd[2], mb=mb, gyuk_name=gyuk))
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
    if an.get('한글'):
        return hg.facts_hangul(an, yong)
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
    if an.get('불용한자'):
        L.append("피해야 할 불용한자 포함(책 9장): " + an['불용한자'] + " — 뜻이 좋지 않은 글자이므로 풀이글에서 반드시 짚을 것")
    if an.get('글자뜻'):
        L.append("한자 뜻 (풀이글에 글자별 뜻과 두 글자를 합친 뜻을 반드시 풀어 쓸 것): " + an['글자뜻'])
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

_STAGES = [("원격", "초년운", 1, 19), ("형격", "청년운", 20, 38), ("이격", "중년운", 39, 57), ("정격", "말년운", 58, 77)]
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
    _AI['f'] = ai_func
    _AI['g'] = gender
    st.subheader("이름 풀이 및 짓기")
    sig = f"{name}|{gender}|{u_cal}|{b_year}-{b_month}-{b_day}|{b_time}|{u_product}"
    st.markdown("**① 입력하신 정보를 확인해 주세요** (왼쪽 입력창에서 고칠 수 있습니다)")
    if html_views is None or choyeon_db is None:   # 사주표를 못 그릴 때만 간단한 표를 보여 줌
        st.markdown(
            f"{'| 신청인 | 신생아 성별 | 신생아 생년월일 | 신생아 태어난 시간 |' if str(u_product).startswith('4-3') else '| 이름 | 성별 | 생년월일 | 태어난 시간 |'}\n|---|---|---|---|\n"
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
        render_onepage_43b(engine, sj, name, gender, b_year, b_month, b_day, b_time, u_cal, ai_func, html_views, choyeon_db,
                           prompts_mod, saju_html, u_product)
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
                    "naming_facts": build_naming_facts(an, yong_from_engine(sj['yong_el'] or {})) + "\n" + str(st.session_state.get('nm_cmp_facts') or ''),
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
_NO_NAME = set('子丑寅卯辰巳午未申酉戌亥豚豕殺殊殘墓冥沒罪賊敵訟拘擊打討衝暴爆假妄罔惑虛無莫勿免窮短薄慢鈍緩忙忘失落脫捨離別寂獨寒冷涼夜霧辛臭醉嫌逆抵拒却鼻口耳舌毛髮脚肝肺肉乳齒額皮革烏蟲螢鷄色欲媒姻婚碑煙燒燃炭軟賣買貸賃費錢兵軍旅卒帥二三四五六七八十兩雙數半父母祖姪靈皇王君尊仙神天佛馬魚鳥鹿龍象雁羊燕蝶鴻')
_NAME_OK = set('彬妍炫瑛琳瑞娟嬉姬婉媛怡煐熙潾苑蓉漣允宥侑洵燦蕙鎬旭赫勳燮炳')   # 교육용 밖이지만 이름에 쓰는 글자 (박사님 승인 2026-11-24)

# 소리 내어 부르면 이상한 뜻이 되는 말 (성씨 + 이름 전체 독음에 들어 있으면 후보에서 뺌). 박사님이 계속 추가하십시오.
_BAD_READING = ('협녹', '소심', '이리', '바보', '병신', '빙신', '시발', '씨발', '씹',
                '좆', '지랄', '개새', '새끼', '쌍놈', '쌍년', '이년', '저년',
                '미친', '미쳤', '또라이', '돌아이', '등신', '머저리', '얼간', '멍청',
                '팔푼', '찐따', '찌질', '꼴통', '호구', '무식', '한심', '거지',
                '도둑', '사기', '구라', '쓰레기', '변태', '치한', '색골', '음란',
                '방귀', '방구', '똥', '오줌', '변소', '변기', '설사', '구토',
                '죽어', '죽음', '자살', '사망', '장례', '상여', '무덤', '송장',
                '귀신', '유령', '악마', '마귀', '마녀', '방정', '주책', '청승',
                '궁상', '호들갑', '변덕', '심술', '천박', '상스', '잡놈', '못난',
                '못된', '못생', '추남', '추녀', '뚱뚱', '돼지', '대머리', '곰보',
                '절름', '장님', '벙어리', '애꾸', '난쟁이', '꼽추', '문둥', '고자',
                '불알', '자지', '보지', '꺼져', '닥쳐', '죽여', '망나니', '망할',
                '썩을', '왕따', '꼰대', '김치', '김밥', '이불', '이빨', '신발',
                '양말', '팬티', '고구마', '감자', '두부', '만두', '고추',
                '번데기', '깍두기', '소시지', '순대',
                '개나', '소나', '개소', '개똥', '개년', '개놈', '걸레', '걸려', '콜걸', '발기', '가려워')
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
        [x['h'] for x in neng.hanja if not (x.get('g') and x.get('e')) or x['h'] in _NO_NAME],
        [x['h'] for x in neng.hanja if not x.get('e') or x['h'] in _NO_NAME],
    ]
    allc, seen = [], set()
    for ex in pools:
        ex = list(ex) + list(order_ex)
        r = neng.auto_candidates(sur, yong, fixed, fixed_pos, exclude=ex, n=n * 3 + 10)
        for c in r['후보']:
            if c['이름'] in seen or _bad_reading(c['독음']):
                continue
            seen.add(c['이름']); allc.append(c)
        if len([c for c in allc if c['단계'] == 0]) >= n:
            break
    allc.sort(key=lambda c: (c['단계'], -c['점수']))
    top = _ai_filter(allc, sur, n)
    lv = max([c['단계'] for c in top], default=0)
    return {'후보': top, '완화단계': lv, '부족': len(top) < n}


def _flow_auto_pick(neng, sur, yong, fixed_pos, fixed, key):
    """후보 이름을 엔진이 우선순위대로 뽑아 보여 주고, 박사님이 하나를 고른다"""
    fp = {'가운데 글자': 'first', '마지막 글자': 'last'}.get(fixed_pos, 'last')
    order = st.radio("몇째 자녀입니까? (책 9장: 장자·차자 불용한자 가림)", ["첫째 (장자/장녀)", "둘째 이하 (차자/차녀)", "가리지 않음"], horizontal=True, index=2, key=f"{key}_order")
    oex = _order_exclude(neng, order)
    nshow = st.selectbox("보여 드릴 후보 수", [5, 10, 20], key=f"{key}_nshow")
    want = {}
    with st.expander("⚙️ 오행 직접 지정 (전문가용 · 성씨 칸은 고정, 비워 두면 자동)"):
        st.caption(f"성씨 {sur['h']} : 소리오행 {sur['bo']} · 자원오행 {sur['ja']} (고정). 이름 두 글자의 오행만 바꿀 수 있고, 수리 네 격·음양·용신 포함 조건은 그대로 지킵니다.")
        _EL = ["자동", "木", "火", "土", "金", "水"]
        _c1, _c2 = st.columns(2)
        want['s1'] = _c1.selectbox("소리오행 · 가운데 글자", _EL, key=f"{key}_w_s1")
        want['s2'] = _c2.selectbox("소리오행 · 끝 글자", _EL, key=f"{key}_w_s2")
        want['j1'] = _c1.selectbox("자원오행 · 가운데 글자", _EL, key=f"{key}_w_j1")
        want['j2'] = _c2.selectbox("자원오행 · 끝 글자", _EL, key=f"{key}_w_j2")
        want = {k: (None if v == "자동" else v) for k, v in want.items()}
    neng.set_want(want)
    ck = f"{nshow}|{order}|{key}_cand|{sur['h']}|{sorted((k, v) for k, v in yong.items())}|{fixed['h'] if fixed else ''}|{fp}|{sorted((k, v or '') for k, v in want.items())}"
    if st.session_state.get('nm_cand_key') != ck:
        with st.spinner("후보 이름을 찾고 있습니다..."):
            with_f = _cand_pools(neng, sur, yong, fixed, fp, n=nshow, order_ex=oex) if fixed else None
            free = _cand_pools(neng, sur, yong, None, fp, n=nshow, order_ex=oex)
        st.session_state['nm_cand_key'] = ck
        st.session_state['nm_cand'] = (with_f, free)
    with_f, free = st.session_state['nm_cand']
    if st.session_state.get('nm_cnt_key') != ck:      # 📊 통계 한 줄 (계산은 한 번만)
        try:
            _ex = [x['h'] for x in neng.hanja if not x.get('e') or x['h'] in _NO_NAME] + list(oex)
            st.session_state['nm_cnt'] = neng.count_summary(sur, yong, exclude=_ex)
        except Exception:
            st.session_state['nm_cnt'] = None
        st.session_state['nm_cnt_key'] = ck
    _cs = st.session_state.get('nm_cnt')
    if _cs:
        st.caption(f"📊 흔히 쓰는 한자로 만들 수 있는 이름 {_cs['전체조합']:,}가지 중 수리 네 격·음양이 맞는 것 {_cs['수리길조합']:,}가지, "
                   f"소리·자원오행·용신까지 모두 맞는 것 {_cs['오행까지만족']:,}가지입니다.")
    use = free
    if fixed is not None:
        worse = (with_f['완화단계'] > free['완화단계']) or (len(with_f['후보']) < min(nshow, len(free['후보'])))
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
        an['글자뜻'] = _meaning_line(c['A'], c['B'])
        if c.get('뜻풀이'):
            an['글자뜻'] += f" (AI 뜻풀이: {c['뜻풀이']})"
        ans.append(an)
        gy = ' · '.join(f"{v['수리']}{'✅' if v['길흉'] == '길' else '⚠️'}" for v in an['네격'].values())
        mean = f"{c['A']['hun'].split('/')[0]} + {c['B']['hun'].split('/')[0]}"
        if c.get('뜻풀이'):
            mean += f" — {c['뜻풀이']} (AI {c.get('AI점수', '-')}점)"
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
        names = an.get('글자뜻', '') if an.get('한글') else " · ".join(k['hun'].split('/')[0] for k in (an.get('A'), an.get('B')) if k)
        return (f"<div class='op-nm'><span class='op-rk'>추천 {rank}</span><div class='op-h'>{an['이름']}</div>"
                f"<div class='op-k'>{an['독음']}</div><div class='op-m'>{names}<br>소리 {an['소리판정']} · {'순수 한글 이름' if an.get('한글') else '자원 ' + an['자원판정']}</div>"
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
    <div class='op-who'>신청인 {name}님 · 신생아 {gender}아 · {birth_txt} &nbsp;|&nbsp; 성씨 {an1['이름'][0]} &nbsp;|&nbsp; 중심오행 <b>{yong.get('용신') or '-'}</b> · 보조 <b>{yong.get('희신') or '-'}</b> · 피할 오행 {yong.get('기신') or '-'}</div>
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


def render_onepage_43b(engine, sj, name, gender, b_year, b_month, b_day, b_time, u_cal, ai_func, html_views, choyeon_db,
                       prompts_mod, saju_html, u_product):
    """4-3: 추천 이름 두 개를 고르면 '작명서 풀이(여러 쪽)'와 '한 장 작명서'를 함께 만든다"""
    import datetime as _dt
    ans = st.session_state.get('nm_last_ans') or []
    if len(ans) < 2:
        st.info("추천 후보가 두 개 이상 나오면 작명서를 만들 수 있습니다.")
        return
    st.divider()
    st.markdown("**③ 작명서에 올릴 추천 이름 2개 고르기** (처음에는 1·2순위가 선택되어 있습니다)")
    labels = [f"{i + 1}순위 {a['이름']} ({a['독음']})" for i, a in enumerate(ans)]
    pick = st.multiselect("추천 이름 두 개", labels, default=labels[:2], max_selections=2, key="op_pick")
    if len(pick) != 2:
        st.warning("이름을 정확히 2개 골라 주세요.")
        return
    an1, an2 = [ans[labels.index(p)] for p in pick]
    sig = f"{an1['이름']}|{an2['이름']}|{name}|{b_year}{b_month}{b_day}{b_time}"
    yong = yong_from_engine(sj['yong_el'] or {})
    if st.button("📜 작명서 만들기 (풀이 + 한 장 작명서)", key="op_make_btn", type="primary"):
        var = PROMPT_NAME.get("4-3")
        tpl = getattr(prompts_mod, var, "") if var else ""
        if not tpl:
            st.error(f"prompts.py 에 '{var}' 가 없습니다.")
            return
        sp_d, sp_txt = op.spouse_facts(sj, yong)
        saju_facts = build_saju_facts(sj, yong) + "\n" + engine.get_eumyang_facts(sj['gans'], sj['jjis'])
        golden = build_golden_facts(engine, sj, choyeon_db)
        ilji = f"{sj['gans'][1]}{sj['jjis'][1]}일주의 일지 {sj['jjis'][1]}"
        f1, f2 = build_naming_facts(an1, yong), build_naming_facts(an2, yong)
        d1, d2 = build_daewun_facts(engine, sj, yong, an1), build_daewun_facts(engine, sj, yong, an2)
        with st.spinner("작명서 풀이를 쓰고 있습니다. 1~2분 걸립니다..."):
            data = {"name": name, "name1": f"{an1['이름']}({an1['독음']})", "name2": f"{an2['이름']}({an2['독음']})",
                    "golden_facts": golden, "saju_facts": saju_facts, "spouse_facts": sp_txt,
                    "user_concern": str(st.session_state.get("user_concern", "") or "").strip(),
                    "naming_facts": "[추천 ① 이름]\n" + f1 + "\n\n[추천 ② 이름]\n" + f2,
                    "daewun_facts": "[추천 ① 이름 기준]\n" + d1 + "\n\n[추천 ② 이름 기준]\n" + d2}
            report_text = ai_func(tpl.format_map(_SafeDict(data)))
        with st.spinner("한 장 작명서를 쓰고 있습니다. 1분쯤 걸립니다..."):
            one_text = ai_func(op.prompt(name, gender, golden, saju_facts, f1, f2, d1, d2, ilji, sp_txt))
        st.session_state['op_text'] = (sig, one_text)
        st.session_state['op_report'] = (sig, report_text)
    got, rep = st.session_state.get('op_text'), st.session_state.get('op_report')
    if not got or not rep or got[0] != sig or rep[0] != sig:
        return
    sec = op.parse(got[1])
    order_txt = {"첫째": "첫째(장자/장녀) 기준을 적용했습니다", "둘째": "둘째 이하(차자/차녀) 기준을 적용했습니다"}.get(
        str(st.session_state.get('nm_4-3_order', ''))[:2], "")
    try:
        from zoneinfo import ZoneInfo
        today = _dt.datetime.now(ZoneInfo('Asia/Seoul'))
    except Exception:
        today = _dt.datetime.now()
    one_html = op.onepage_html(html_views, sj, gender, an1, an2, sec, (u_cal, b_year, b_month, b_day, b_time),
                               f"{today.year}년 {today.month}월 {today.day}일")
    cover = make_cover(html_views, u_product, name, gender, b_year, b_month, b_day, b_time, u_cal)
    body = (saju_html
            + html_views.format_ai_text_to_html(prepare_report_text(rep[1]), "", "신생아")
            + op.notice_html(an1, an2, order_txt)
            + naming_closing_html("신생아", html_views.get_choyeon_sign_html()))
    final_html = cover + html_views.get_final_report_box(body) + op.page_break_html(one_html)
    st.session_state['saved_report_html'] = final_html
    st.markdown(prepare_report_text(rep[1]))
    st.markdown(op.notice_html(an1, an2, order_txt), unsafe_allow_html=True)
    st.markdown("**한 장 작명서**")
    st.markdown(one_html, unsafe_allow_html=True)
    gid = st.session_state.get('admin_proc_id')
    if gid:
        st.divider()
        st.markdown("**④ 신청자에게 보내기 준비**")
        if st.button("📤 이 결과를 발송 서랍장으로 보내기", key="op_send_btn", type="primary"):
            st.session_state[f"html_{gid}"] = final_html
            st.session_state['app_running'] = False
            st.session_state['admin_proc_id'] = None
            st.rerun()

def _meaning_line(A, B):
    """이름 글자들의 한자 뜻을 '秉 잡을 병 + 鎬 호경 호' 형태로"""
    return ' + '.join(f"{k['h']} {k['hun'].split('/')[0]}" for k in (A, B) if k)

# ======================================================================
# 이름 후보 AI 뜻 심사 v2 - 점수제 (naming_ui.py 맨 아래, 옛 '이름 후보 AI 뜻 심사' 구간을 통째로 바꿈)
# ======================================================================
_AI = {'f': None, 'g': '', 'saju': ''}
_AI_PASS = 8          # AI 점수(10점 만점)가 이 점수 이상이어야 후보로 보여 줌


def _with_saju(prompt):
    """사주 내용이 있으면 AI 심사 기준에 '이 사주에 맞는 이름인가'를 더한다"""
    sj = str(_AI.get('saju') or '').strip()
    if not sj:
        return prompt
    blk = ("[사주 적합성 - 반드시 반영]\n"
           "아래는 이 아이의 사주 내용입니다. 이름 글자의 뜻과 오행이 이 사주의 약한 곳을 채우고 치우친 곳을 달래 주는지 함께 심사하십시오.\n"
           "- 사주에 이미 넘치는 기운을 더 키우는 뜻의 글자가 중심이면 6점 이하 (예: 불이 넘치는 사주에 炎 炫 燦 같은 불 글자)\n"
           "- 사주에 부족하거나 필요한 기운을 도와주는 뜻이면 가점\n"
           "- 사주의 성격·구조와 이름의 뜻이 정반대로 부딪치면 감점\n"
           "- 감점 사유에는 사주와 어떻게 안 맞는지 한 구절을 쓰십시오\n"
           "[사주 내용]\n" + sj[:1800] + "\n\n")
    key = '[뜻풀이 규칙]'
    return prompt.replace(key, blk + key, 1) if key in prompt else blk + prompt


def _ai_review(items, gender):
    """items: [(이름한자, 독음, '글자별 훈음')] → {번호: (점수, 한줄뜻풀이)}. AI 호출이 안 되면 None"""
    f = _AI.get('f')
    if not f or not items:
        return None
    lines = "\n".join(f"{i + 1}|{h}|{r}|{m}" for i, (h, r, m) in enumerate(items))
    prompt = f"""당신은 한국 성명학 전문가입니다. 아래는 {gender or '성별 미정'}에게 지어 줄 이름 후보입니다. (번호|한자이름|한글독음|글자별 훈음)
각 이름을 엄격하게 심사해 10점 만점으로 점수를 매기십시오. 점수는 다음 기준으로 정합니다.
[감점 기준]
1) 한자 두 글자(외자는 성+한 글자)의 뜻을 합쳐 읽을 때 말이 안 되거나 어색하면 4점 이하
2) 한글 소리가 성(姓)과 이어질 때 욕설·비속어·성적 연상·놀림감·흔한 관용구가 되면 2점 이하 (예: 박개나→개나 소나, 박걸려→걸레, 기남→발기)
3) 성별 적합성: 여아·여성 이름에 굳셈·용맹·크기·권력·무예·법도·모범·받들기·검소·상쾌함 같은 남성적이거나 딱딱한 뜻의 글자가 하나라도 있으면 5점 이하 (예: 男 特 巨 雄 武 規 模 範 奉 儉 萬 快 等). 남아·남성 이름에 곱고 어여쁨을 뜻하는 글자(麗 娥 嬌 姬 妍 등)가 있으면 5점 이하
4) 한자 뜻이 부정적이거나 재물·외모·몸 따위를 직접 드러내 천박하면 4점 이하
5) 요즘 어른 이름으로 쓰기에 구식이거나 부자연스러우면 6점 이하
6) 글자별 훈음에 '(동자이음·동음이의 주의)'가 붙은 글자가 있어 읽기가 헷갈릴 수 있으면 6점 이하
7) 두 글자의 뜻이 같은 방향(덕목·재물·강함 등)으로 겹쳐 이름값이 지나치게 크게 느껴지면 6점 이하
[가점 기준] 뜻이 곱고 밝고 이름답게 자연스러우며 소리도 부드러우면 8~10점
[뜻풀이 규칙] 뜻풀이는 반드시 위에 주어진 '글자별 훈음' 안의 뜻만 써서 15자 안팎으로 쓰십시오. 훈음에 없는 뜻이나 독음을 절대 지어내지 마십시오.
출력은 반드시 한 줄에 하나씩 '번호|점수(숫자만)|뜻풀이 또는 감점 사유' 형식만 쓰고, 다른 말은 쓰지 마십시오.

{lines}"""
    try:
        text = f(_with_saju(prompt))
    except Exception:
        return None
    out = {}
    for ln in str(text or '').splitlines():
        p = [x.strip() for x in ln.strip().split('|')]
        if len(p) >= 3 and p[0].isdigit():
            try:
                sc = float(p[1])
            except ValueError:
                continue
            out[int(p[0])] = (sc, '|'.join(p[2:]))
    return out or None


def _all_hun(k):
    """DB에 적힌 훈음 전체 (AI가 이 안에서만 뜻을 풀도록)"""
    return f"{k['h']}[{k['hun']}]" + ("(동자이음·동음이의 주의)" if (k.get('dj') or k.get('de')) else "")


def _ai_filter(allc, sur, n):
    """정렬된 후보 allc 를 AI가 점수로 심사 → 기준 점수 이상만, (단계, 점수+AI점수) 순으로 n개. 심사가 불가하면 앞 n개"""
    if not _AI.get('f'):
        return allc[:n]
    cache = st.session_state.setdefault('nm_ai_cache', {})
    g = _AI.get('g', '')
    pool = allc[:60]
    ok = True
    for s in range(0, len(pool), 20):
        todo = [c for c in pool[s:s + 20] if (g, c['이름']) not in cache]
        if not todo:
            continue
        items = [(c['이름'], c['독음'], ' + '.join(_all_hun(k) for k in (c['A'], c.get('B')) if k)) for c in todo]
        res = _ai_review(items, g)
        if res is None:
            ok = False
            break
        for i, c in enumerate(todo):
            if (i + 1) in res:
                cache[(g, c['이름'])] = res[i + 1]
        if len([1 for c in pool[:s + 20] if cache.get((g, c['이름']), (0,))[0] >= _AI_PASS]) >= n * 2:
            break
    keep = []
    for c in pool:
        v = cache.get((g, c['이름']))
        if v and v[0] >= _AI_PASS:
            keep.append(dict(c, 뜻풀이=v[1], AI점수=v[0]))
    if not ok and not keep:
        st.caption("※ AI 뜻 심사를 하지 못해 소리·자원·수리 기준으로만 보여 드립니다.")
        return allc[:n]
    keep.sort(key=lambda c: (c['단계'], -(c['점수'] + c['AI점수'])))
    if len(keep) < n:
        st.caption(f"※ AI 심사({_AI_PASS}점 이상)를 통과한 후보가 {len(keep)}개뿐입니다. 이 성씨는 조건에 맞는 좋은 이름이 많지 않습니다.")
    return keep[:n]


def _ai_filter_single(cands, sur):
    """외자 이름 후보(성 + 한 글자)를 AI가 점수로 심사해 기준 점수 이상만 남기고 뜻풀이를 붙인다. 심사가 불가하면 그대로"""
    if not _AI.get('f') or not cands:
        return cands
    cache = st.session_state.setdefault('nm_ai_cache', {})
    g = _AI.get('g', '')
    pool = cands[:40]
    todo = [c for c in pool if (g, sur['h'] + c['h']) not in cache]
    if todo:
        items = [(sur['h'] + c['h'], sur['r'] + c['r'], _all_hun(c)) for c in todo]
        res = _ai_review(items, g)
        if res is None:
            st.caption("※ AI 뜻 심사를 하지 못해 소리·자원·수리 기준으로만 보여 드립니다.")
            return cands
        for i, c in enumerate(todo):
            if (i + 1) in res:
                cache[(g, sur['h'] + c['h'])] = res[i + 1]
    keep = []
    for c in pool:
        v = cache.get((g, sur['h'] + c['h']))
        if v and v[0] >= _AI_PASS:
            keep.append(dict(c, 뜻풀이=v[1], AI점수=v[0]))
    keep.sort(key=lambda d: -(d['점수'] + d['가산'] + d['AI점수']))
    for i, d in enumerate(keep):
        d['추천'] = i < 2
    return keep

def naming_notice_html(u_product, an):
    """4-1 이름 풀이에서 이름에 아쉬운 점이 있을 때만 붙이는 개명 안내 고정문구"""
    if not str(u_product).startswith("4-1") or not an:
        return ""
    why = []
    if an.get('흉격수'):
        why.append("수리 네 격 중 흉한 격이 있음")
    if an.get('이견격'):
        why.append("수리에 학설 이견이 있는 격이 있음")
    if an.get('소리판정') == '흉' or an.get('자원판정') == '흉':
        why.append("소리·자원 오행의 흐름이 매끄럽지 않음")
    if an.get('기신포함'):
        why.append("피해야 할 오행이 이름에 들어 있음")
    if not an.get('용신포함'):
        why.append("사주가 필요로 하는 오행이 이름에 부족함")
    if not why:
        return ""
    items = "".join(f"<li>{w}</li>" for w in why)
    return f"""
    <div style='margin-top:14px; padding:12px 16px; border:2px solid #1A237E; border-radius:8px; background:#F5F7FF; page-break-inside: avoid; break-inside: avoid;'>
        <div style='font-weight:900; color:#1A237E; font-size:16px; margin-bottom:6px;'>📌 개명 안내</div>
        <ul style='margin:0 0 8px 18px; line-height:1.7;'>{items}</ul>
        <p style='margin:0; line-height:1.8; text-align:justify;'>위와 같은 아쉬운 점이 있으나, 이름은 사주를 곁에서 돕는 기운일 뿐 삶을 정하는 것은 아닙니다. 다만 아쉬운 부분을 보완하고 싶으시면 초연 시공명리의 <b>이름 바꾸기(개명) 풀이</b>로 사주에 맞는 새 이름 후보를 우선순위대로 받아 보실 수 있습니다.</p>
    </div>
    """

# ======================================================================
# 한글 이름을 먼저 고르고 한자 찾기 (naming_ui.py 맨 아래에 붙여 넣기)
# ======================================================================
# 인기 이름: 2025년 출생신고 기준 (대법원 전자가족관계등록시스템 집계, 유가크루 정리). 박사님이 고치거나 더하실 수 있습니다.
_POP_NAMES = {   # 앞의 20개는 2026년 순위(11월 4일 기준), 그 뒤는 2025년에만 있던 이름
    '여': "서윤 서아 하윤 하린 이서 지안 아윤 시아 아린 윤서 지유 유주 유나 수아 유하 지우 도아 채원 지아 채이 채아 예린".split(),
    '남': "도윤 이준 시우 하준 이안 서준 수호 태오 우주 유준 도현 선우 지호 이현 도하 은호 주원 윤우 시윤 우진 은우".split(),
}

_HG_SKIP = set('丫吝亜衙枒稰閠閏䦞鈗荺橍補鴈眼莪児廈珥李而杝飴庶墅尔兒鋆胤奫')   # 이름에 쓰지 않을 한자
_NO_NAME |= _HG_SKIP   # 기존 방식(한자부터 고르기)에도 같은 글자를 뺍니다

def _hangul_combos(neng, sur, yong, r1, r2, max_st=16, ex=()):
    """한글 두 글자(r1, r2)에 맞는 한자 조합을 전부 만들어 판정한다.
    반환: (조합 목록, 통계). 조합은 (단계, 점수) 순서. 단계 0 = 수리·음양·소리·자원 모두 길, 단계 1 = 수리·음양만 길"""
    exs = set(ex) | neng.bad
    pa = [x for x in neng.find_by_reading(r1) if x['h'] not in exs and x['st'] <= max_st]
    pb = [x for x in neng.find_by_reading(r2) if x['h'] not in exs and x['st'] <= max_st]
    S = sur['st']
    st_ = {'전체': len(pa) * len(pb), '수리음양통과': 0, '소리자원까지': 0, '동파제외': 0}
    out = []
    for a in pa:
        for b in pb:
            if not (neng.four_ok(S, a['st'], b['st']) and neng.yinyang_ok(S, a['st'], b['st'])):
                continue
            if a.get('dp') and b.get('dp'):
                st_['동파제외'] += 1
                continue
            st_['수리음양통과'] += 1
            an = neng.analyze_name(sur, a, b, yong)
            tier = 0 if (an['소리판정'] == '길' and an['자원판정'] == '길') else 1
            if tier == 0:
                st_['소리자원까지'] += 1
            sc = (3 if an['용신포함'] else 0) - (2 if an['기신포함'] else 0) + neng.bonus(a) + neng.bonus(b) \
                 + 1.5 * (bool(a.get('g')) + bool(b.get('g'))) + 1.0 * (bool(a.get('e')) + bool(b.get('e')))   # 뜻 좋은 글자·흔한 글자를 위로
            out.append((tier, -sc, a, b, an))
    out.sort(key=lambda t: (t[0], t[1]))
    return [dict(단계=t, 점수=-s, A=a, B=b, an=an) for t, s, a, b, an in out], st_


def _flow_hangul_pick(neng, sur, yong, gender, key):
    """한글 이름을 먼저 고르고(인기 이름 선택 또는 직접 입력), 그 소리에 맞는 한자 조합을 찾아 보여 준다"""
    pop = _POP_NAMES.get(gender, [])
    opts = ["직접 입력"] + [(f"2026년 {i + 1}위 {n}" if i < 20 else f"2025년 {n}") for i, n in enumerate(pop)]
    sel = st.selectbox("한글 이름 고르기 (2025년 인기 이름에서 고르거나 직접 입력)", opts, key=f"{key}_hpop")
    if sel == "직접 입력":
        nm = st.text_input("한글 이름 두 글자 (성씨는 빼고)", max_chars=2, key=f"{key}_hnm").strip()
    else:
        nm = sel.split()[-1]
    if len(nm) != 2 or not all('가' <= c <= '힣' for c in nm):
        st.info("한글 이름 두 글자를 고르거나 입력해 주세요.")
        return None
    full = str(sur.get('r', '')) + nm
    if _bad_reading(full):
        st.warning(f"'{full}'은(는) 소리 내어 부르면 좋지 않은 뜻이 들어 있는 말입니다. 다른 이름을 권합니다.")
    c2, c3 = st.columns(2)
    order = c2.radio("몇째 자녀입니까?", ["첫째 (장자/장녀)", "둘째 이하 (차자/차녀)", "가리지 않음"], index=2, key=f"{key}_horder")
    nshow = c3.selectbox("보여 드릴 후보 수", [10, 20, 30], key=f"{key}_hshow")
    ex = set(_order_exclude(neng, order)) | {h for h in _NO_NAME if h not in _NAME_OK} | _HG_SKIP
    ck = f"{full}|{order}|{sur['h']}|{sorted((k, v) for k, v in yong.items())}|{gender}"
    if st.session_state.get('nm_hg_key') != ck:
        with st.spinner("한자 조합을 찾고 있습니다..."):
            st.session_state['nm_hg'] = _hangul_combos(neng, sur, yong, nm[0], nm[1], 99, ex)
        st.session_state['nm_hg_key'] = ck
    combos, stat = st.session_state['nm_hg']
    st.caption(f"{full}: 한자 조합 {stat['전체']}가지 중 수리·음양이 맞는 것 {stat['수리음양통과']}가지, "
               f"소리·자원오행까지 모두 길한 것 {stat['소리자원까지']}가지 (불용한자·동자이음·동음이의·동파한자는 자동으로 뺐습니다)")
    if not combos:
        st.warning(f"'{full}'에 맞는 한자 조합이 없습니다. 최대 획수를 늘리거나 다른 한글 이름을 골라 보세요.")
        return None
    good = [c for c in combos if c['단계'] == 0]
    base = [dict(c, 이름=c['an']['이름'], 독음=c['an']['독음']) for c in (good or combos)]
    with st.spinner("AI가 두 글자를 합친 뜻을 풀이하고 있습니다..."):
        use = _ai_filter(base, sur, nshow)
    if not use:
        st.info("AI 뜻 심사를 통과한 조합이 없어, 소리·자원·수리 기준 순서대로 보여 드립니다.")
        use = base[:nshow]
    if not good:
        st.info("소리·자원오행까지 모두 길한 조합이 없어, 수리·음양이 맞는 조합 중에서 보여 드립니다. 소리나 자원이 흉일 수 있습니다.")
    st.markdown("**한자 조합 후보 (우선순위 순)**")
    rows, ans = [], []
    for i, c in enumerate(use):
        an = c['an']
        an['글자뜻'] = _meaning_line(c['A'], c['B'])
        if c.get('뜻풀이'):
            an['글자뜻'] += f" (AI 뜻풀이: {c['뜻풀이']})"
        ans.append(an)
        gy = ' · '.join(f"{v['수리']}{'✅' if v['길흉'] == '길' else '⚠️'}" for v in an['네격'].values())
        mean = f"{c['A']['hun'].split('/')[0]} + {c['B']['hun'].split('/')[0]}"
        if c.get('뜻풀이'):
            mean += f" — {c['뜻풀이']} (AI {c.get('AI점수', '-')}점)"
        sf = ' → '.join(x[0] for x in an['소리배합']) + f" ({' · '.join(an['소리관계'])})"
        rf = ' → '.join(x[0] for x in an['자원배합']) + f" ({' · '.join(an['자원관계'])})"
        rows.append(f"| {i + 1} | **{an['이름']}** ({an['독음']}) | {mean} | {sf} {an['소리판정']} | {rf} {an['자원판정']} | {gy} | {'포함' if an['용신포함'] else '미포함'} |")
    st.markdown("| 순위 | 이름 | 뜻 | 소리 | 자원 | 수리(원·형·이·정) | 중심오행 |\n|---|---|---|---|---|---|---|\n" + "\n".join(rows))
    st.session_state['nm_last_ans'] = [dict(a_, A=c_['A'], B=c_['B']) for a_, c_ in zip(ans, use)]
    i = st.radio("이 한자 조합으로 풀이를 진행합니다", range(len(use)), format_func=lambda i: f"{i + 1}순위  {ans[i]['이름']} ({ans[i]['독음']})",
                 key=f"{key}_hpick", horizontal=True)
    return ans[i]
