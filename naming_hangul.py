# -*- coding: utf-8 -*-
"""
순수 한글 이름 짓기·풀이 (naming_hangul.py)  v1.1  -- naming_ui.py 가 불러 쓰는 별도 파일
[박사님 확정 규칙 2026-11-24]
 * 한자가 들어가는 이름은 '운해본' 발음오행(기존), 순수 한글 이름은 '해례본' 발음오행을 쓴다
     해례본: ㄱㅋ 木 / ㄴㄷㄹㅌ 火 / ㅁㅂㅍ 土 / ㅅㅈㅊ 金 / ㅇㅎ 水   (운해본과 다른 곳은 입술소리 土, 목구멍소리 水)
 * 소리오행 세 글자 배합(성-첫자-끝자)은 기존 125 배합표를 그대로 쓴다 (글자별 오행만 해례본)
 * 순수 한글 이름에는 수리 4격·자원오행이 없다 → 소리오행 + 용신 포함 + 음양(모음)만 본다
 * 이름 후보는 AI가 사주에 맞춰 제안하고, 엔진이 해례본 소리오행으로 거른다
 * 성씨는 한자 그대로, 성씨의 소리오행도 해례본으로 계산한다 (두 글자 성은 마지막 글자)
"""
import re
from naming_engine import chain_ok, rel

HAERYE = {'ㄱ': '木', 'ㄲ': '木', 'ㅋ': '木',
          'ㄴ': '火', 'ㄷ': '火', 'ㄸ': '火', 'ㄹ': '火', 'ㅌ': '火',
          'ㅁ': '土', 'ㅂ': '土', 'ㅃ': '土', 'ㅍ': '土',
          'ㅅ': '金', 'ㅆ': '金', 'ㅈ': '金', 'ㅉ': '金', 'ㅊ': '金',
          'ㅇ': '水', 'ㅎ': '水'}
_CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
_JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
_YANG = set("ㅏㅐㅑㅒㅗㅘㅙㅚㅛ")
_EUM = set("ㅓㅔㅕㅖㅜㅝㅞㅟㅠ")
_INIT_BY_EL = {el: ' '.join(c for c in 'ㄱㅋㄴㄷㄹㅌㅁㅂㅍㅅㅈㅊㅇㅎ' if HAERYE[c] == el) for el in '木火土金水'}


def is_hangul_name(s):
    return bool(s) and all('가' <= c <= '힣' for c in s)


def cho(syl):
    c = ord(syl) - 0xAC00
    return _CHO[c // 588] if 0 <= c < 11172 else ''


def jung(syl):
    c = ord(syl) - 0xAC00
    return _JUNG[(c % 588) // 28] if 0 <= c < 11172 else ''


def sound_el(syl):
    """한 글자의 해례본 발음오행 (첫 자음 기준)"""
    return HAERYE.get(cho(syl), '')


def vowel_yy(syl):
    j = jung(syl)
    return '양' if j in _YANG else ('음' if j in _EUM else '중')


def _sur_last(sur):
    r = str(sur.get('r') or '')
    return r[-1] if r else ''


def analyze_hangul(sur, name, yong, relax=False):
    """순수 한글 이름 판정. naming_ui 의 다른 화면과 맞추려고 같은 이름의 칸을 채워 준다."""
    e0 = sound_el(_sur_last(sur))
    els = [e0] + [sound_el(s) for s in name]
    rels = tuple(rel(els[i], els[i + 1]) for i in range(len(els) - 1))
    if len(name) == 2:
        ok = chain_ok(*els)
    else:
        ok = rels[0] != '극'
    if relax and not ok:
        ok_relaxed = '극' not in rels
    else:
        ok_relaxed = ok
    need = {o for o in (yong.get('용신'), yong.get('겸용')) if o}
    bad = {o for o in (yong.get('기신'), yong.get('구신')) if o}
    nm_els = els[1:]
    yys = [vowel_yy(_sur_last(sur))] + [vowel_yy(s) for s in name]
    same = len(yys) == 3 and yys[0] == yys[1] == yys[2] and yys[0] in ('양', '음')
    return {
        '이름': f"{sur['h']}{name}", '독음': f"{sur['r']}{name}", '한글': True, '이름만': name,
        '소리배합': tuple(els), '소리관계': rels, '소리판정': '길' if ok else '흉',
        '자원배합': (), '자원관계': (), '자원판정': '해당 없음', '네격': {},
        '용신포함': bool(need & set(nm_els)), '기신포함': bool(bad & set(nm_els)),
        '음양': '모음 ' + ''.join(yys) + (' (같은 기운뿐이라 아쉬움)' if same else ' (균형)'),
        '음양같음': same, '소리통과': ok_relaxed, 'A': None, 'B': None, '글자뜻': '',
    }


def _parse(text):
    out = []
    for line in str(text).splitlines():
        m = re.match(r"\s*(?:\d+[.)]\s*)?([가-힣]{1,2})\s*[|｜]\s*(.*?)\s*[|｜]\s*(\d+(?:\.\d+)?)\s*$", line)
        if m:
            out.append((m.group(1), m.group(2).strip(), float(m.group(3))))
    return out


def _prompt(sur, yong, gender, saju, nchar, want, skip, fixed=None):
    e0 = sound_el(_sur_last(sur))
    yn = yong.get('용신') or ''
    gm = yong.get('겸용') or ''
    return f"""당신은 한국 성명학 전문가입니다. 한자가 없는 '순수 한글 이름'을 {want}개 제안하십시오.
- 아이 성별: {'여자아이' if gender == '여' else '남자아이'}
- 성씨: {sur['h']}({sur['r']}) / 이름 글자 수: {nchar}글자
{('- 돌림자: 이름의 ' + ('첫째' if fixed[0] == 0 else '둘째') + " 글자는 반드시 '" + fixed[1] + "'로 고정하고, 나머지 한 글자만 바꿔 완성된 두 글자 이름을 제안하십시오.") if fixed else ''}
- 순우리말(고유어)이나 뜻이 좋은 한글 이름이어야 하며, 놀림감이 되거나 발음이 어색한 이름, 실제 한자 뜻이 나쁜 소리는 제외합니다.
- 성별에 어울리는 이름만 제안합니다. 흔한 이름과 새로운 이름을 섞되 억지스러운 조합은 피합니다.
[소리오행 규칙 - 해례본] 이름 글자는 첫 자음으로 오행이 정해집니다: 木 {_INIT_BY_EL['木']} / 火 {_INIT_BY_EL['火']} / 土 {_INIT_BY_EL['土']} / 金 {_INIT_BY_EL['金']} / 水 {_INIT_BY_EL['水']}
- 성씨의 소리오행은 {e0}입니다. 사주에 필요한 오행은 {yn}{('(겸용 ' + gm + ')') if gm else ''}이므로, 이름 글자 중 하나 이상의 첫 자음이 그 오행이어야 합니다.
- 성씨 오행 → 첫째 글자 오행 → 둘째 글자 오행의 흐름이 서로 극(木土, 土水, 水火, 火金, 金木)하지 않게 하십시오.
{('[사주 내용 - 이 사주에 어울리는 뜻을 고르십시오]' + chr(10) + str(saju)[:1500]) if saju else ''}
{('이미 제안한 이름(중복 금지): ' + ', '.join(skip)) if skip else ''}
[출력 형식] 한 줄에 하나, 아래 형식만 쓰고 다른 설명은 쓰지 마십시오.
이름|뜻풀이(한 구절)|점수(10점 만점, 성별 적합성·뜻·사주 적합성을 엄격히 평가)
예) 하늘|넓고 맑은 하늘처럼 자라라|9
"""


def suggest(ai_func, sur, yong, gender, saju, n=5, nchar=2, bad_fn=None, pass_score=8.0, fixed=None):
    """AI가 제안 → 엔진이 해례본 소리오행·용신으로 거름. 반환 {'후보': [...], '완화단계': 0/1, '부족': bool}"""
    if ai_func is None:
        return {'후보': [], '완화단계': 0, '부족': True, '오류': 'AI 연결이 없습니다'}
    pool, seen = [], set()
    for rnd in range(3):
        try:
            text = ai_func(_prompt(sur, yong, gender, saju, nchar, 40, sorted(seen), fixed))
        except Exception as e:
            return {'후보': pool[:n], '완화단계': 0, '부족': True, '오류': str(e)}
        for nm, mean, sc in _parse(text):
            if nm in seen or len(nm) != nchar or not is_hangul_name(nm) or sc < pass_score:
                continue
            if fixed and nm[fixed[0]] != fixed[1]:
                continue
            seen.add(nm)
            if bad_fn and bad_fn(sur['r'] + nm):
                continue
            an = analyze_hangul(sur, nm, yong, relax=True)
            if not an['용신포함'] or an['기신포함'] and not an['소리판정'] == '길':
                continue
            lv = 0 if (an['소리판정'] == '길' and not an['음양같음']) else 1
            if lv == 1 and not an['소리통과']:
                continue
            an['글자뜻'] = mean
            pool.append({'이름': nm, '뜻풀이': mean, 'AI점수': sc, '단계': lv, 'an': an})
        if len([c for c in pool if c['단계'] == 0]) >= n:
            break
    pool.sort(key=lambda c: (c['단계'], -c['AI점수']))
    top = pool[:n]
    return {'후보': top, '완화단계': max([c['단계'] for c in top], default=0), '부족': len(top) < n}


def facts_hangul(an, yong=None):
    y = yong or {}
    need = [o for o in (y.get('용신'), y.get('겸용')) if o]
    hit = [e for e in an['소리배합'][1:] if e in need]
    L = [f"이름: {an['이름']} (독음 {an['독음']}) — 한자가 없는 '순수 한글 이름'",
         f"소리오행(해례본 기준): {' → '.join(an['소리배합'])} / 관계 {' · '.join(an['소리관계'])} / 판정 {an['소리판정']}",
         "자원오행·수리 4격: 한자가 없어 적용하지 않음 (풀이글에서 자원오행·수리·획수·한자 뜻을 지어내지 말 것)",
         f"사주의 중심오행은 용신 {y.get('용신') or '-'}, 겸용 {y.get('겸용') or '-'}입니다. 이름의 소리에 실제로 들어 있는 해당 오행: {', '.join(hit) if hit else '없음'}. 용신 자체가 들어 있는지: {'예' if y.get('용신') in hit else '아니오'}.",
         "중심오행 포함: " + ("예" if an['용신포함'] else "아니오"),
         "피할 오행 포함: " + ("예" if an['기신포함'] else "아니오"),
         f"음양: {an['음양']}"]
    if an.get('글자뜻'):
        L.append("우리말 뜻(풀이글에서 이름의 뜻과 어울림을 풀어 쓸 것): " + an['글자뜻'])
    else:
        L.append("우리말 뜻: 자료 없음 — 이름 소리에서 떠오르는 순우리말 뜻이 분명할 때만 조심스럽게 풀고, 모르면 쓰지 말 것")
    return "\n".join(L)


def show_hangul(st, an):
    st.markdown(f"### {an['이름']} ({an['독음']}) — 순수 한글 이름")
    parts = [f"{e}({s})" for e, s in zip(an['소리배합'], [_sur_last_of(an)] + list(an['이름만']))]
    chain = parts[0]
    for i in range(1, len(parts)):
        chain += f" ─{an['소리관계'][i - 1]}→ {parts[i]}"
    st.markdown(f"**소리오행(해례본)** {chain}  \n판정: **{an['소리판정']}**")
    tag = ["중심오행(용신) 포함 ✅" if an['용신포함'] else "중심오행(용신) 미포함 ⚠️"]
    if an['기신포함']:
        tag.append("피해야 할 오행 포함 ⚠️")
    tag.append(an['음양'])
    tag.append("자원오행·수리 4격은 한자가 없어 적용하지 않음")
    st.caption(" · ".join(tag))
    if an.get('글자뜻'):
        st.caption("뜻: " + an['글자뜻'])


def _sur_last_of(an):
    return an['독음'][len(an['독음']) - len(an['이름만']) - 1]


def flow_new(st, sur, yong, gender, key, ai_func, saju, bad_fn=None):
    """4-2 이름 바꾸기 / 4-3 신생아 이름짓기 의 순수 한글 후보 화면"""
    nchar = 1 if st.radio("순수 한글 이름 글자 수", ["두 글자 (예: 하늘)", "한 글자 (예: 솔)"], horizontal=True, key=f"{key}_hgn").startswith("한") else 2
    fixed = None
    if nchar == 2 and st.radio("집안의 돌림자를 꼭 써야 합니까?", ["아니오 (돌림자 없이)", "예 (돌림자가 있음)"], horizontal=True, key=f"{key}_hgdol").startswith("예"):
        _pos = st.radio("돌림자 위치", ["첫째 글자", "둘째 글자"], horizontal=True, key=f"{key}_hgdolpos")
        _syl = st.text_input("돌림자 (한글 한 글자)", key=f"{key}_hgdolch", max_chars=1).strip()
        if not (_syl and is_hangul_name(_syl)):
            st.info("돌림자를 한글 한 글자로 입력하면 그 글자에 맞는 나머지 글자를 찾아 드립니다.")
            return None, []
        fixed = (0 if _pos.startswith("첫") else 1, _syl)
    nshow = st.selectbox("보여 드릴 후보 수", [5, 10, 20], key=f"{key}_hgshow")
    ck = f"{nshow}|{nchar}|{sur['h']}|{sorted((k, v) for k, v in yong.items())}|{gender}|{hash(str(saju))}|{fixed}"
    if st.session_state.get('nm_hg_key') != ck:
        with st.spinner("순수 한글 이름 후보를 찾고 있습니다..."):
            res = suggest(ai_func, sur, yong, gender, saju, n=nshow, nchar=nchar, bad_fn=bad_fn, fixed=fixed)
        st.session_state['nm_hg_key'] = ck
        st.session_state['nm_hg_res'] = res
    res = st.session_state['nm_hg_res']
    cands = res['후보']
    if res.get('오류'):
        st.warning(f"후보를 만들지 못했습니다: {res['오류']}")
    if not cands:
        st.warning("조건에 맞는 순수 한글 이름을 찾지 못했습니다. 후보 수나 글자 수를 바꾸거나" + (" 돌림자 없이 지어 보세요." if fixed else " 다시 시도해 보세요."))
        return None, []
    if res['완화단계'] > 0:
        st.info("소리·모음이 모두 좋은 후보가 부족하여 일부 조건을 완화했습니다. (중심오행 포함은 항상 지켰습니다.)")
    if res['부족']:
        st.caption(f"조건에 맞는 후보가 {len(cands)}개뿐입니다.")
    st.markdown("**순수 한글 이름 추천 후보 (우선순위 순)**")
    rows, ans = [], []
    for i, c in enumerate(cands):
        a = c['an']
        ans.append(a)
        sf = ' → '.join(a['소리배합']) + f" ({' · '.join(a['소리관계'])})"
        rows.append(f"| {i + 1} | **{a['이름']}** ({a['독음']}) | {c['뜻풀이']} (AI {c['AI점수']:g}점) | {sf} {a['소리판정']} | {'포함' if a['용신포함'] else '미포함'} | {a['음양']} |")
    st.markdown("| 순위 | 이름 | 뜻 | 소리오행(해례본) | 중심오행 | 음양 |\n|---|---|---|---|---|---|\n" + "\n".join(rows))
    i = st.radio("이 후보로 풀이를 진행합니다", range(len(cands)), format_func=lambda i: f"{i + 1}순위  {ans[i]['이름']} ({ans[i]['독음']})", key=f"{key}_hgpick", horizontal=True)
    return ans[i], ans


def flow_check(st, sur, yong, key):
    """4-1 이름 풀이: 순수 한글 이름 입력"""
    st.markdown("**현재 이름을 한글로 입력해 주세요** (성씨를 뺀 이름, 한자가 없는 순수 한글 이름)")
    nm = st.text_input("이름 (성씨 제외, 1~2글자)", key=f"{key}_hgcur", max_chars=2).strip()
    if not nm:
        return None
    if not is_hangul_name(nm):
        st.warning("한글만 입력해 주세요.")
        return None
    return analyze_hangul(sur, nm, yong)


# ------------------------------------------------------------------ 현재 이름 ↔ 새 이름 비교 (4-2 이름 바꾸기)
def _summ(an):
    han = bool(an.get('한글'))
    bad_n = None if han else sum(1 for v in an['네격'].values() if v['길흉'] != '길')
    return {
        '이름': f"{an['이름']} ({an['독음']})" + (" · 순수 한글" if han else ""),
        '소리': ' → '.join(an['소리배합']) + f" {an['소리판정']}",
        '자원': '해당 없음 (한글)' if han else ' → '.join(an['자원배합']) + f" {an['자원판정']}",
        '수리': '해당 없음 (한글)' if han else ('모두 길' if not bad_n else f"흉한 격 {bad_n}개"),
        '용신': '포함' if an['용신포함'] else '미포함',
        '기신': '포함' if an['기신포함'] else '없음',
        '음양': an['음양'],
        '_bad_n': bad_n, '_han': han,
    }


def compare_changes(cur, new):
    """(좋아진 점 목록, 아쉬워진 점 목록)"""
    c, n = _summ(cur), _summ(new)
    better, worse = [], []

    def _cmp(label, a, b, good_when):
        if a == b:
            return
        (better if b == good_when else worse).append(f"{label}: {a} → {b}")
    _cmp("소리오행 판정", cur['소리판정'], new['소리판정'], '길')
    _cmp("중심오행(용신) 포함", c['용신'], n['용신'], '포함')
    _cmp("피해야 할 오행", c['기신'], n['기신'], '없음')
    if not c['_han'] and not n['_han']:
        _cmp("자원오행 판정", cur['자원판정'], new['자원판정'], '길')
        if c['_bad_n'] != n['_bad_n']:
            (better if n['_bad_n'] < c['_bad_n'] else worse).append(f"수리 4격 흉한 격: {c['_bad_n']}개 → {n['_bad_n']}개")
    return better, worse


def show_compare(st, cur, new):
    c, n = _summ(cur), _summ(new)
    st.markdown("**현재 이름과 새 이름 비교**")
    rows = [("이름", c['이름'], n['이름']), ("소리오행 흐름·판정", c['소리'], n['소리']), ("자원오행", c['자원'], n['자원']),
            ("수리 4격", c['수리'], n['수리']), ("중심오행(용신)", c['용신'], n['용신']), ("피해야 할 오행", c['기신'], n['기신']), ("음양", c['음양'], n['음양'])]
    st.markdown("| 항목 | 현재 이름 | 새 이름 |\n|---|---|---|\n" + "\n".join(f"| {a} | {b} | {d} |" for a, b, d in rows))
    better, worse = compare_changes(cur, new)
    if better:
        st.success("좋아진 점\n\n" + "\n".join(f"- {x}" for x in better))
    if worse:
        st.warning("아쉬워진 점\n\n" + "\n".join(f"- {x}" for x in worse))
    if not better and not worse:
        st.info("판정 항목에서는 현재 이름과 큰 차이가 없습니다. 이름의 뜻과 사주에 맞는 의미를 비교해 보세요.")
    if c['_han'] != n['_han']:
        st.caption("한자 이름과 순수 한글 이름은 판정 기준이 달라(순수 한글은 자원오행·수리 4격이 없음) 소리오행·중심오행·피할 오행만 견줍니다.")


def compare_facts(cur, new):
    """풀이글 AI에게 넘기는 비교 자료 (자료에 없는 내용은 지어내지 않도록 안내)"""
    c, n = _summ(cur), _summ(new)
    better, worse = compare_changes(cur, new)
    L = ["[현재 이름과 새 이름 비교 자료 — 풀이글에서 현재 이름의 아쉬운 점과 새 이름이 좋아진 점을 이 자료대로만 비교해 설명할 것]",
         f"현재 이름: {c['이름']} / 소리 {c['소리']} / 자원 {c['자원']} / 수리 {c['수리']} / 중심오행 {c['용신']} / 피할 오행 {c['기신']}",
         f"새 이름: {n['이름']} / 소리 {n['소리']} / 자원 {n['자원']} / 수리 {n['수리']} / 중심오행 {n['용신']} / 피할 오행 {n['기신']}",
         "좋아진 점: " + (" ; ".join(better) if better else "없음"),
         "아쉬워진 점: " + (" ; ".join(worse) if worse else "없음")]
    if c['_han'] != n['_han']:
        L.append("참고: 한자 이름과 순수 한글 이름은 판정 기준이 달라 자원오행·수리 4격은 비교하지 않음")
    return "\n".join(L)
