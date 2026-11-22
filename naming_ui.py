# -*- coding: utf-8 -*-
"""
이름 풀이 및 짓기 화면 (naming_ui.py)  v0.1
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
def pick_surname(neng, label, key, optional=False):
    """한글 성씨 입력 → 한자 후보 고르기. 반환: 성씨 항목(없으면 None)"""
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
    i = st.radio("성씨 한자를 골라 주세요", range(len(cands)), format_func=lambda i: labels[i], key=f"{key}_hj", horizontal=True)
    return cands[i]


def pick_hanja(neng, label, key, help_text=""):
    """한글 한 글자 입력 → 한자 후보 선택. 반환: 한자 dict(없으면 None)"""
    rd = st.text_input(label, key=f"{key}_rd", help=help_text, max_chars=1).strip()
    if not rd:
        return None
    cands = [x for x in neng.find_by_reading(rd) if x['h'] not in neng.bad]
    cands.sort(key=lambda x: (-int(bool(x.get('e'))), x['st']))
    if not cands:
        st.warning(f"'{rd}'로 읽는 한자를 찾지 못했습니다.")
        return None
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
    sur1 = pick_surname(neng, "성씨 (한글)", f"{key}_s1")
    sur2 = None
    if st.checkbox("어머니 성씨도 이어 붙이기 (예: 김이○○)", key=f"{key}_two"):
        sur2 = pick_surname(neng, "이어 붙일 성씨 (한글) — 입력한 순서대로 붙습니다", f"{key}_s2")
    if sur1 is None:
        return None
    ents = [sur1] + ([sur2] if sur2 else [])
    sur = neng.build_surname(ents)
    if sur2:
        st.caption(f"합친 성씨: {sur['h']} ({sur['st']}획)")
    return sur

def _flow_single(neng, sur, yong, key):
    """외자 이름(성 + 한 글자): 후보 중에서 한 글자 고르기"""
    tier = st.selectbox("글자 범위", range(3), format_func=lambda i: TIER_LABELS[i], key=f"{key}_tier1")
    cands = neng.single_candidates(sur, yong, exclude=_tier_exclude(neng, tier))
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
    n = st.radio("이름 글자 수", [2, 1], format_func=lambda n: "두 글자 (예: 수연)" if n == 2 else "한 글자 외자 (예: 호)", horizontal=True, key=f"{key}_n")
    if n == 1:
        return _flow_single(neng, sur, yong, key)
    fixed_pos, fixed = None, None
    if st.checkbox("돌림자가 있습니다", key=f"{key}_dol"):
        fixed_pos = st.radio("돌림자 위치", ["가운데 글자", "마지막 글자"], horizontal=True, key=f"{key}_dolpos")
        fixed = pick_hanja(neng, "돌림자 (한글 한 글자)", f"{key}_dolch", "집안의 돌림자를 한글로 한 글자 넣어 주세요")
        if fixed is None:
            st.info("돌림자를 입력하면 그 글자에 맞는 나머지 글자를 찾아 드립니다.")
            return None
    tier = st.selectbox("글자 범위", range(3), format_func=lambda i: TIER_LABELS[i], key=f"{key}_tier")
    ex = _tier_exclude(neng, tier)

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
    n = st.radio("이름 글자 수", [2, 1], format_func=lambda n: "두 글자 (예: 수연)" if n == 2 else "한 글자 (예: 솔)", horizontal=True, key=f"{key}_n")
    A = pick_hanja(neng, "이름 첫 글자 (한글)", f"{key}_c1")
    B = pick_hanja(neng, "이름 둘째 글자 (한글)", f"{key}_c2") if n == 2 else None
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


def build_naming_facts(an):
    L = [f"이름: {an['이름']} (독음 {an['독음']})",
         f"소리오행: {' → '.join(an['소리배합'])} / 관계 {' · '.join(an['소리관계'])} / 판정 {an['소리판정']}" + (f" / 책의 풀이: {_book_note(an, '소리')}" if _book_note(an, '소리') else ""),
         f"자원오행: {' → '.join(an['자원배합'])} / 관계 {' · '.join(an['자원관계'])} / 판정 {an['자원판정']}" + (f" / 책의 풀이: {_book_note(an, '자원')}" if _book_note(an, '자원') else "")]
    for k, v in an['네격'].items():
        L.append(f"{k}({v['때']}): 수리 {v['수리']} · 격 이름 {v['격']} · 상 {v.get('상', '')} · 길흉 {v['길흉']} · 해설 {v.get('해설', '')}")
    L.append("중심오행 포함: " + ("예" if an['용신포함'] else "아니오"))
    L.append("피할 오행 포함: " + ("예" if an['기신포함'] else "아니오"))
    L.append(f"음양: {an['음양']}")
    return "\n".join(L)


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

def render_naming_page(engine, u_product, gender, name, b_year, b_month, b_day, b_time, u_cal, ai_func=None, prompts_mod=None):
    """app.py 가 부르는 입구(권장). 입력 확인 → 사주 계산 → 작명 화면. 반환: 판정 결과 dict 또는 None"""
    st.subheader("이름 풀이 및 짓기")
    sig = f"{name}|{gender}|{u_cal}|{b_year}-{b_month}-{b_day}|{b_time}|{u_product}"
    st.markdown("**① 입력하신 정보를 확인해 주세요** (왼쪽 입력창에서 고칠 수 있습니다)")
    st.markdown(
        f"| 이름 | 성별 | 생년월일 | 태어난 시간 |\n|---|---|---|---|\n"
        f"| {name} | {gender} | {u_cal} {b_year}년 {b_month}월 {b_day}일 | {b_time} |"
    )
    if "모름" in str(b_time):
        st.warning("태어난 시간을 모르면 시(時) 기둥 없이 세 기둥으로 용신을 정하므로 정확도가 낮아질 수 있습니다.")
    started = st.session_state.get("nm_started_sig") == sig
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
    st.divider()
    st.markdown("**③ 풀이글 받기**")
    rkey = f"{sig}|{an['이름']}"
    if st.button("📜 이 이름 풀이글 받기", key="nm_report_btn", type="primary"):
        var = PROMPT_NAME.get(str(u_product)[:3])
        tpl = getattr(prompts_mod, var, "") if var else ""
        if not tpl:
            st.error(f"prompts.py 에 '{var}' 가 없습니다.")
        else:
            data = {"name": name,
                    "saju_facts": build_saju_facts(sj, yong_from_engine(sj['yong_el'] or {})) + "\n" + engine.get_eumyang_facts(sj['gans'], sj['jjis']),
                    "naming_facts": build_naming_facts(an),
                    "daewun_facts": build_daewun_facts(engine, sj, yong_from_engine(sj['yong_el'] or {}), an)}
            with st.spinner("풀이글을 쓰고 있습니다. 1~2분 걸립니다..."):
                text = ai_func(tpl.format_map(_SafeDict(data)))
            st.session_state["nm_report"] = (rkey, text)
    rep = st.session_state.get("nm_report")
    if rep and rep[0] == rkey:
        st.markdown(rep[1])
    return an
