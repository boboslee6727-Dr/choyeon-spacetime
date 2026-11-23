# -*- coding: utf-8 -*
"""
초연 작명법 엔진 (naming_engine.py)  v1.1  -- 기존 engine.py와 완전히 별개 파일
- 사주 계산(용신/희신/기신)은 기존 engine.py 결과를 받아서 쓴다. 이 파일은 사주를 계산하지 않는다.
- 한자 자료는 naming_db.json (인명용 한자 5,829자 + 81수리) 에서 읽는다.
- 이름 구조: 성(1글자) + 이름 2글자 (두 글자 성, 외자 이름은 다음 단계에서 추가)

[박사님 확정 규칙]
 * 용신(중심오행)이 자원오행에 포함되어야 함 (최우선)
 * 소리오행/자원오행: 순생(金→水)이 기본, 역생(土→金)도 허용
 * 원·형·이·정 네 격이 모두 길수
 * 삼원오행은 적용하지 않음
[임시 규칙 - 박사님 확인 대기]
 * 이웃한 오행에 '상극'이 없어야 함(비화=같은 오행은 허용), 세 글자가 모두 같은 오행이면 제외
 * 획수 음양이 성·첫자·끝자 모두 같으면(음음음/양양양) 제외
"""
import json, os, collections

OH = '木火土金水'
GEN = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}   # A가 B를 생함
KO2HJ = {'목': '木', '화': '火', '토': '土', '금': '金', '수': '水'}  # 엔진 문장(목화토금수) -> 한자 오행


def rel(a, b):
    """앞 글자 a, 뒤 글자 b 의 오행 관계: 순생/역생/비화/극"""
    if a == b:
        return '비화'
    if GEN[a] == b:
        return '순생'
    if GEN[b] == a:
        return '역생'
    return '극'


_SOUND = {}   # 박사님 제공 125 배합표(길=1/흉=0). NamingEngine 시작할 때 채워짐


def chain_ok(e1, e2, e3):
    """성-첫자-끝자 오행 배합이 허용되는가: 125 배합표가 있으면 표대로, 없으면 임시 규칙"""
    if _SOUND:
        return _SOUND.get(e1 + e2 + e3, 0) == 1
    if rel(e1, e2) == '극' or rel(e2, e3) == '극':
        return False
    if e1 == e2 == e3:
        return False
    return True


def chain_score(e1, e2, e3):
    """순생 2점, 역생 1점, 비화 0점 (두 쌍 합계, 최대 4)"""
    pt = {'순생': 2, '역생': 1, '비화': 0}
    return pt[rel(e1, e2)] + pt[rel(e2, e3)]


def wrap81(n):
    while n > 82:      # 책 기준: 82수까지 해설이 있고, 83부터는 80을 뺌
        n -= 80
    return n

class NamingEngine:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'naming_db.json')
        with open(db_path, encoding='utf-8') as f:
            self.db = json.load(f)
        _SOUND.clear()
        _SOUND.update(self.db.get('sound125', {}))
        self.hanja = self.db['hanja']
        self.good = {int(k) for k, v in self.db['suri81'].items() if v['길']}
        # 뜻이 나쁜 글자(키워드 자동분류 초안)는 기본으로 후보에서 뺀다
        self.bad = {x['h'] for x in self.hanja if x.get('x')}
        # (발음오행, 자원오행, 획수) 같은 글자끼리 묶어 계산을 빠르게 함
        self.cls = collections.defaultdict(list)
        for x in self.hanja:
            self.cls[(x['bo'], x['ja'], x['st'])].append(x)

    # ---------- 한자 찾기 ----------
    def find_by_reading(self, reading):
        """한글 한 글자 -> 한자 후보 목록 (성씨·돌림자·현재이름 입력용)"""
        return [x for x in self.hanja if x['r'] == reading]

    def get_hanja(self, h):
        for x in self.hanja:
            if x['h'] == h:
                return x
        return None

    # ---------- 수리 ----------
    def suri_good(self, n):
        return wrap81(n) in self.good

    def four_gyeok(self, S, a, b):
        """원격=a+b(초년) 형격=S+a(청년) 이격=S+b(중년) 정격=S+a+b(말년)"""
        return {'원격': a + b, '형격': S + a, '이격': S + b, '정격': S + a + b}

    def four_ok(self, S, a, b):
        return all(self.suri_good(v) for v in self.four_gyeok(S, a, b).values())

    @staticmethod
    def yinyang_ok(S, a, b):
        return not (S % 2 == a % 2 == b % 2)

    def bonus(self, x):
        """같은 점수일 때의 순서: 교육용(흔한 글자) +0.5, 뜻 좋은 글자 +0.5, 성별에 어울리는 뜻 +0.7 (반대 성별 느낌은 -0.7)"""
        b = 0.5 * (1 if x.get('e') else 0) + 0.5 * (1 if x.get('g') else 0)
        g = getattr(self, 'gender', None)
        if g in ('남', '여'):
            tag = gender_tag(x)
            if tag == g:
                b += 0.7
            elif tag in ('남', '여'):
                b -= 0.7
        # 사주가 한쪽 음양으로 크게 쏠렸으면(양팔통 등) 반대 음양 글자를 우대한다
        t = getattr(self, 'saju_tilt', None)
        if t in ('양', '음') and x.get('yy') == ('陰' if t == '양' else '陽'):
            b += 0.6
        return b

    # ---------- 핵심: 조합 검사/점수 ----------
    def combo_score(self, sur, A, B, yong):
        """
        sur, A, B : 한자 dict (성, 이름 첫자, 이름 끝자)
        yong : {'용신':'水','겸용':None,'희신':'金','기신':'火','구신':'土'}  (한자 오행)
        통과하면 점수(정수), 탈락이면 None
        """
        S, a, b = sur['st'], A['st'], B['st']
        if not self.four_ok(S, a, b) or not self.yinyang_ok(S, a, b):
            return None
        if not chain_ok(sur['bo'], A['bo'], B['bo']):
            return None
        if not chain_ok(sur['ja'], A['ja'], B['ja']):
            return None
        need = {o for o in (yong.get('용신'), yong.get('겸용')) if o}
        if need and not ({A['ja'], B['ja']} & need):
            return None
        sc = chain_score(sur['bo'], A['bo'], B['bo']) + chain_score(sur['ja'], A['ja'], B['ja'])
        for g in (A, B):
            if g['ja'] == yong.get('용신'):
                sc += 3
            elif g['ja'] == yong.get('겸용'):
                sc += 2
            if g['ja'] == yong.get('희신'):
                sc += 1
            if g['ja'] in (yong.get('기신'), yong.get('구신')):
                sc -= 2
        return sc

    def _classes(self, exclude=()):
        ex = set(exclude) | self.bad
        for key, lst in self.cls.items():
            lst2 = [x for x in lst if x['h'] not in ex]
            if lst2:
                yield key, lst2

    def count_summary(self, sur, yong, exclude=()):
        """화면용: 전체 수리조합 수 / 흉운 없는 조합 수 / 오행 조건까지 만족하는 조합 수"""
        total = ok_suri = ok_all = 0
        S = sur['st']
        cl = list(self._classes(exclude))
        for (b1, j1, s1), l1 in cl:
            for (b2, j2, s2), l2 in cl:
                n = len(l1) * len(l2)
                total += n
                if not (self.four_ok(S, s1, s2) and self.yinyang_ok(S, s1, s2)):
                    continue
                ok_suri += n
                A = {'bo': b1, 'ja': j1, 'st': s1}
                B = {'bo': b2, 'ja': j2, 'st': s2}
                if self.combo_score(sur, A, B, yong) is not None:
                    ok_all += n
        return {'전체조합': total, '수리길조합': ok_suri, '오행까지만족': ok_all}

    # ---------- 3-1 가운데(첫) 글자 후보 ----------
    def middle_candidates(self, sur, yong, exclude=(), fixed_end=None):
        """
        성과 어울리고, 끝 글자를 어떻게든 완성할 수 있는 첫 글자 전부.
        반환: 점수 높은 순. 각 항목에 '최고점', '완성가능수' 포함. 상위 2개에 추천=True
        fixed_end: 돌림자가 끝 글자로 정해진 경우 그 한자 dict
        """
        out = []
        ex = set(exclude) | self.bad
        cl = list(self._classes(exclude))
        for x in self.hanja:
            if x['h'] in ex:
                continue
            best, cnt = None, 0
            if fixed_end is not None:
                s = self.combo_score(sur, x, fixed_end, yong)
                if s is not None:
                    best, cnt = s, 1
            else:
                for (b2, j2, s2), l2 in cl:
                    B = {'bo': b2, 'ja': j2, 'st': s2}
                    s = self.combo_score(sur, x, B, yong)
                    if s is not None:
                        cnt += len(l2)
                        best = s if best is None else max(best, s)
            if cnt:
                out.append(dict(x, 최고점=best, 완성가능수=cnt, 가산=self.bonus(x)))
        out.sort(key=lambda d: (-(d['최고점'] + d['가산']), -d['완성가능수']))
        for i, d in enumerate(out):
            d['추천'] = i < 2
        return out

    # ---------- 3-2 끝 글자 후보 ----------
    def end_candidates(self, sur, first, yong, exclude=()):
        """선택한 첫 글자와 어울리는 끝 글자 전부. 점수 높은 순, 상위 2개 추천"""
        out = []
        ex = set(exclude) | self.bad
        for x in self.hanja:
            if x['h'] in ex:
                continue
            s = self.combo_score(sur, first, x, yong)
            if s is not None:
                out.append(dict(x, 점수=s, 가산=self.bonus(x)))
        out.sort(key=lambda d: -(d['점수'] + d['가산']))
        for i, d in enumerate(out):
            d['추천'] = i < 2
        return out


# ---------- 기존 engine.py 결과를 받는 연결 부품 ----------
def yong_from_engine(elements_dict):
    """
    기존 engine.get_yongshin_elements(yongshin_fact_str) 가 돌려주는 사전
    {'용신':'수','희신':'금','기신':'화',...} 를 한자 오행으로 바꿔 줌.
    """
    out = {}
    for k in ('용신', '희신', '기신', '구신', '한신', '겸용'):
        v = elements_dict.get(k)
        out[k] = KO2HJ.get(v) if v else None
    return out


# ---------- 두 글자 성씨 (남궁, 선우, 황보 …) ----------
def make_surname(parts, sound_from='last', resource_from='last'):
    """
    parts: 성씨 한자 dict 목록. 한 글자 성이면 [金], 두 글자 성이면 [南, 宮].
    획수는 두 글자의 합(남궁 9+10=19)으로 쓴다 (박사님 확정).
    소리오행/자원오행은 두 글자 중 어느 글자를 쓸지 아직 미정 -> 임시로 '이름과 이웃한 마지막 글자'.
      sound_from / resource_from : 'first' 또는 'last'
    """
    pick = lambda which: parts[0] if which == 'first' else parts[-1]
    return {
        'h': ''.join(p['h'] for p in parts),
        'st': sum(p['st'] for p in parts),
        'bo': pick(sound_from)['bo'],
        'ja': pick(resource_from)['ja'],
        'parts': parts,
    }


# ---------- 성씨 찾기 / 부모 성 이어붙이기 ----------
def _find_surname(self, reading):
    """한글 성씨 -> 후보 목록 (예: '이' -> 李, 伊, 二, 異 ...). 신청자가 고른다."""
    return [s for s in self.db.get('surnames', []) if s['r'] == reading]


def _build_surname(self, entries, sound_from='last', resource_from='last'):
    """
    entries : 성씨 항목(find_surname 결과에서 고른 것) 1개 이상.
      - 일반: [김]            -> 한 글자 성
      - 두 글자 성: [남궁]    -> 남궁 (획수는 두 글자 합)
      - 부모 성 이어붙이기: [아빠성, 엄마성] -> 예) [김, 이] = 金+李 = 15획
        (이어붙이는 순서는 신청자가 정한 대로 넣는다. 한 쪽이 두 글자 성이어도 됨)
    획수는 모든 글자의 합. 소리오행·자원오행은 sound_from / resource_from('first'|'last')로 고른 글자 기준
    (두 글자 성과 같은 방식. 박사님 기준 확정 전까지 임시로 'last').
    """
    parts = []
    for en in entries:
        parts.extend(en['parts'])
    pick = lambda which: parts[0] if which == 'first' else parts[-1]
    return {
        'h': ''.join(p['h'] for p in parts),
        'r': ''.join(en['r'] for en in entries),
        'st': sum(p['st'] for p in parts),
        'bo': pick(sound_from)['bo'],
        'ja': pick(resource_from)['ja'],
        'parts': parts,
        'combined': len(entries) > 1,
    }


NamingEngine.find_surname = _find_surname
NamingEngine.build_surname = _build_surname


# ---------- 속자·약자 제외 / 외자 이름 / 돌림자 ----------
def _init_variants(self):
    """속자·약자 표시 글자는 정자만 남기기 위해 후보에서 제외 (통용자는 그대로 둠)"""
    self.variant = {x['h'] for x in self.hanja if ('속자' in x['hun'] or '약자' in x['hun'])}
    self.bad |= self.variant


_orig_init = NamingEngine.__init__


def _new_init(self, db_path=None):
    _orig_init(self, db_path)
    _init_variants(self)


NamingEngine.__init__ = _new_init


def pair_ok(e1, e2):
    """외자 이름: 성-이름 두 칸은 상극만 아니면 됨 (생·비화 허용) -- 기본안"""
    return rel(e1, e2) != '극'


def _single_four(self, S, a):
    """외자 이름 네 격: 원격=a+1, 형격=S+a, 이격=S+1, 정격=S+a (성명학 통례, 기본안)"""
    return {'원격': a + 1, '형격': S + a, '이격': S + 1, '정격': S + a}


def _single_candidates(self, sur, yong, exclude=(), fixed=None):
    """외자 이름 후보 (예: 김 수). 용신 포함, 네 격 길수, 소리·자원 상극 없음. 점수순, 상위 2개 추천"""
    out = []
    ex = set(exclude) | self.bad
    need = {o for o in (yong.get('용신'), yong.get('겸용')) if o}
    for x in self.hanja:
        if x['h'] in ex or (fixed and x['h'] != fixed['h']):
            continue
        if not all(self.suri_good(v) for v in self.single_four(sur['st'], x['st']).values()):
            continue
        if not (pair_ok(sur['bo'], x['bo']) and pair_ok(sur['ja'], x['ja'])):
            continue
        if need and x['ja'] not in need:
            continue
        pt = {'순생': 2, '역생': 1, '비화': 0}
        sc = pt[rel(sur['bo'], x['bo'])] + pt[rel(sur['ja'], x['ja'])]
        sc += 3 if x['ja'] == yong.get('용신') else (2 if x['ja'] == yong.get('겸용') else 0)
        sc += 1 if x['ja'] == yong.get('희신') else 0
        sc -= 2 if x['ja'] in (yong.get('기신'), yong.get('구신')) else 0
        out.append(dict(x, 점수=sc, 가산=self.bonus(x)))
    out.sort(key=lambda d: -(d['점수'] + d['가산']))
    for i, d in enumerate(out):
        d['추천'] = i < 2
    return out


NamingEngine.single_four = _single_four
NamingEngine.single_candidates = _single_candidates


# ---------- 성별에 어울리는 글자 (뜻 키워드 자동분류 초안 -- 박사님 검토 필요) ----------
_F_WORDS = "아름다 고울 곱 어여 맑을 향기 꽃 구슬 옥 어질 부드 사랑 곱다 예쁠 우아 정숙 단아 온화 따뜻 은혜 슬기로 진주 보배 달 별 이슬 비단 샘 연꽃 난초 매화 봄 노래 즐거 기쁠 화할 화평 편안 평안 정성 순할 착할 깨끗 빛날 환할 아리따울 영롱".split()
_M_WORDS = "굳셀 클 큰 높을 용 호랑이 강할 씩씩 용맹 장수 무사 호걸 바위 산 뫼 큰바위 웅 영웅 으뜸 어른 뛰어날 걸출 우뚝 우레 불꽃 곧을 바를 지킬 다스릴 이룰 나아갈 오를 창성 번성 넓을 깊을 무 군사 병사 칼".split()


def gender_tag(x):
    """첫 번째 뜻이 여성적이면 '여', 남성적이면 '남', 둘 다 아니면 None"""
    import re
    first = x['hun'].split('/')[0]
    first = re.sub(r'^성씨\s*', '', first.strip())
    mean = first.rsplit(' ', 1)[0] if ' ' in first else first
    f = any(mean == k if len(k) == 1 else mean.startswith(k) for k in _F_WORDS)
    m = any(mean == k if len(k) == 1 else mean.startswith(k) for k in _M_WORDS)
    if f and not m: return '여'
    if m and not f: return '남'
    return None


# ---------- 이름 판정 (5-1 이름 풀이, 5-2 개명의 '현재 이름' 점검, 최종 선택 이름 점검) ----------
def _analyze_name(self, sur, A, B, yong):
    """
    sur: build_surname 결과, A/B: 이름 첫 글자/끝 글자 한자 dict (외자면 B=None)
    반환: 소리·자원 배합 판정, 네 격(수리·격이름·길흉), 음양, 용신 포함 여부
    """
    S, a = sur['st'], A['st']
    out = {'이름': sur['h'] + A['h'] + (B['h'] if B else ''), '독음': sur['r'] + A['r'] + (B['r'] if B else '')}
    if B:
        b = B['st']
        out['소리배합'] = (sur['bo'], A['bo'], B['bo'])
        out['자원배합'] = (sur['ja'], A['ja'], B['ja'])
        out['소리판정'] = '길' if chain_ok(sur['bo'], A['bo'], B['bo']) else '흉'
        out['자원판정'] = '길' if chain_ok(sur['ja'], A['ja'], B['ja']) else '흉'
        out['소리관계'] = (rel(sur['bo'], A['bo']), rel(A['bo'], B['bo']))
        out['자원관계'] = (rel(sur['ja'], A['ja']), rel(A['ja'], B['ja']))
        gy = self.four_gyeok(S, a, b)
        out['음양'] = '균형' if self.yinyang_ok(S, a, b) else '치우침'
        ja_set = {A['ja'], B['ja']}
    else:
        out['소리배합'] = (sur['bo'], A['bo'])
        out['자원배합'] = (sur['ja'], A['ja'])
        out['소리판정'] = '길' if pair_ok(sur['bo'], A['bo']) else '흉'
        out['자원판정'] = '길' if pair_ok(sur['ja'], A['ja']) else '흉'
        out['소리관계'] = (rel(sur['bo'], A['bo']),)
        out['자원관계'] = (rel(sur['ja'], A['ja']),)
        gy = self.single_four(S, a)
        out['음양'] = '-'
        ja_set = {A['ja']}
    _yy = lambda n: '양' if n % 2 else '음'
    _parts = [('성', S), ('첫 글자', a)] + ([('끝 글자', B['st'])] if B else [])
    out['글자음양'] = ' · '.join(f"{lab} {_yy(n)}({n}획)" for lab, n in _parts)
    stages = {'원격': '초년운', '형격': '청년운', '이격': '중년운', '정격': '말년운'}
    out['네격'] = {}
    for k, v in gy.items():
        n = wrap81(v)
        info = self.db['suri81'][str(n)]
        out['네격'][k] = {'때': stages[k], '수리': v, '적용수': n, '격': info['격'], '한자': info.get('한자', ''), '상': info.get('상', ''), '해설': info.get('해설', ''), '길흉': '길' if info['길'] else '흉'}
    need = {o for o in (yong.get('용신'), yong.get('겸용')) if o}
    out['용신포함'] = bool(ja_set & need) if need else None
    out['기신포함'] = bool(ja_set & {yong.get('기신'), yong.get('구신')} - {None})
    out['흉격수'] = sum(1 for v in out['네격'].values() if v['길흉'] == '흉')
    return out

NamingEngine.analyze_name = _analyze_name

# ---------- 자동 후보 선정 (엔진이 상위 5개를 뽑고 박사님이 2개를 승인) ----------
# 완화 순서(박사님 확정): 수리 4격(항상 지킴) > 자원오행(용신 포함, 상생) > 소리오행(가장 먼저 풀어줌)
#   0단계: 수리4격 길 + 음양 + 소리 길 + 자원 길 + 용신 포함   (모두 만족)
#   1단계: 소리오행만 완화 (수리4격·자원 길·용신 포함은 지킴)
#   2단계: 자원 배합까지 완화 (수리4격·용신 포함은 지킴)
_LEVEL_TEXT = {0: '소리·자원·수리 모두 길', 1: '소리오행만 완화(수리·자원은 길)', 2: '자원오행만 완화(수리·소리는 길)', 3: '소리·자원 배합 완화(수리 4격·용신 포함은 지킴)'}
 
 
def _chain_pts(e1, e2, e3):
    """순생 2 / 역생 1 / 비화 0 / 극 -1 (완화 단계에서 극이 섞여도 계산되도록)"""
    pt = {'순생': 2, '역생': 1, '비화': 0, '극': -1}
    return pt[rel(e1, e2)] + pt[rel(e2, e3)]
 
 
def _common(x):
    """흔히 쓰는 글자(교육용) 또는 뜻 좋은 글자는 후보 순서에서 앞세움"""
    return 1.5 if (x.get('e') or x.get('g')) else 0.0
 
 
def _score_level(self, sur, A, B, yong, level):
    S, a, b = sur['st'], A['st'], B['st']
    if not self.four_ok_strict(S, a, b) or not self.yinyang_ok(S, a, b):
        return None
    need = {o for o in (yong.get('용신'), yong.get('겸용')) if o}
    if need and not ({A['ja'], B['ja']} & need):
        return None
    sound_ok = chain_ok(sur['bo'], A['bo'], B['bo'])
    res_ok = chain_ok(sur['ja'], A['ja'], B['ja'])
    if level == 0 and not (sound_ok and res_ok):
        return None
    if level == 1 and not res_ok:
        return None
    if level == 2 and not sound_ok:
        return None
    sc = _chain_pts(sur['bo'], A['bo'], B['bo']) + _chain_pts(sur['ja'], A['ja'], B['ja'])
    for g in (A, B):
        if g['ja'] == yong.get('용신'):
            sc += 3
        elif g['ja'] == yong.get('겸용'):
            sc += 2
        if g['ja'] == yong.get('희신'):
            sc += 1
        if g['ja'] in (yong.get('기신'), yong.get('구신')):
            sc -= 2
    if not sound_ok:
        sc -= 3
    if not res_ok:
        sc -= 6
    return sc
 
 
def _level_pairs(self, sur, yong, level, exclude, fixed, fixed_pos, per_class=4):
    """한 단계에서 통과하는 (점수, A, B) 목록"""
    ex = set(exclude) | self.bad
    out = []
    if fixed is not None:
        for x in self.hanja:
            if x['h'] in ex or x['h'] == fixed['h']:
                continue
            A, B = (fixed, x) if fixed_pos == 'first' else (x, fixed)
            s = self._score_level(sur, A, B, yong, level)
            if s is not None:
                out.append((s + self.bonus(x) + _common(x), A, B))
        return out
    cl = []
    for key, lst in self.cls.items():
        lst2 = sorted([x for x in lst if x['h'] not in ex], key=lambda x: -(self.bonus(x) + _common(x)))[:per_class]
        if lst2:
            cl.append((key, lst2))
    for (b1, j1, s1), l1 in cl:
        for (b2, j2, s2), l2 in cl:
            s = self._score_level(sur, {'bo': b1, 'ja': j1, 'st': s1}, {'bo': b2, 'ja': j2, 'st': s2}, yong, level)
            if s is None:
                continue
            for A in l1:
                for B in l2:
                    if A['h'] != B['h']:
                        out.append((s + self.bonus(A) + self.bonus(B) + _common(A) + _common(B), A, B))
    return out
 
 
def _auto_candidates(self, sur, yong, fixed=None, fixed_pos='last', exclude=(), n=5):
    """
    후보 이름 n개를 자동으로 뽑는다.
      fixed     : 돌림자 한자 dict (없으면 None = 두 글자 모두 자유)
      fixed_pos : 돌림자 자리 'first'(가운데) / 'last'(끝)
    반환 {'후보':[...], '완화단계':가장 낮은 단계, '부족':True/False, '안내':문장}
      후보 항목: 이름·독음·A·B·점수·단계·단계설명 (판정은 analyze_name 으로 따로)
    같은 독음 이름은 한 번만, 같은 첫글자·끝글자 독음은 각각 최대 2번까지 (다양하게).
    """
    picked, seen_name, cnt_a, cnt_b = [], set(), {}, {}
    used_level = 0
    for level in (0, 1, 2, 3):
        pairs = self._level_pairs(sur, yong, level, exclude, fixed, fixed_pos)
        pairs.sort(key=lambda t: -t[0])
        for sc, A, B in pairs:
            if len(picked) >= n:
                break
            name = A['r'] + B['r']
            if name in seen_name or cnt_a.get(A['r'], 0) >= 2 or cnt_b.get(B['r'], 0) >= 2:
                continue
            if any(p['A']['h'] == A['h'] and p['B']['h'] == B['h'] for p in picked):
                continue
            seen_name.add(name)
            cnt_a[A['r']] = cnt_a.get(A['r'], 0) + 1
            cnt_b[B['r']] = cnt_b.get(B['r'], 0) + 1
            picked.append({'이름': sur['h'] + A['h'] + B['h'], '독음': sur['r'] + name, 'A': A, 'B': B,
                           '점수': round(sc, 1), '단계': level, '단계설명': _LEVEL_TEXT[level]})
            used_level = max(used_level, level)
        if len(picked) >= n:
            break
    short = len(picked) < n
    if not picked:
        note = '조건에 맞는 후보를 찾지 못했습니다.'
    elif used_level == 0 and not short:
        note = '소리·자원·수리가 모두 길한 후보 %d개입니다.' % len(picked)
    elif short:
        note = '후보가 %d개뿐입니다(%s까지 완화).' % (len(picked), _LEVEL_TEXT[used_level])
    else:
        note = '모두 길한 후보가 부족하여 %s 단계까지 완화했습니다.' % _LEVEL_TEXT[used_level]
    return {'후보': picked, '완화단계': used_level, '부족': short, '안내': note}
 
 
def _compare_fixed_and_free(self, sur, yong, fixed, fixed_pos='last', exclude=(), n=5):
    """돌림자를 쓴 경우와 쓰지 않은 경우를 나란히 (박사님 승인 화면용)"""
    with_f = self.auto_candidates(sur, yong, fixed, fixed_pos, exclude, n)
    free = self.auto_candidates(sur, yong, None, fixed_pos, exclude, n)
    worse = (with_f['완화단계'] > free['완화단계']) or (len(with_f['후보']) < min(n, len(free['후보'])))
    msg = ''
    if worse:
        msg = '돌림자를 쓰면 후보가 모자라거나 완화 단계가 높아집니다. 돌림자 없이 짓는 쪽이 더 좋을 수 있습니다.'
    return {'돌림자씀': with_f, '돌림자없이': free, '돌림자불리': worse, '안내': msg}
 
 
NamingEngine._score_level = _score_level
NamingEngine._level_pairs = _level_pairs
NamingEngine.auto_candidates = _auto_candidates
NamingEngine.compare_fixed_and_free = _compare_fixed_and_free

# ---------- 이견 수리 (책 표는 길이나 타 학파는 반길·흉으로 보는 수) ----------
DISPUTED = {38: '반길', 51: '반길', 71: '반길', 75: '반길', 77: '반길', 76: '흉'}
DISPUTED_NOTE = {
    '반길': '본 연구소 기준으로는 길수이나, 일부 학파에서는 장단점이 공존하는 반길수로 보기도 합니다.',
    '흉': '본 연구소 기준으로는 인내와 베풂으로 복을 이루는 길수이나, 타 학파에서는 흉수로 보기도 하는 수리입니다.',
}

def _four_ok_strict(self, S, a, b):
    """네 격이 모두 길이면서 이견 수리가 없어야 통과 (자동 추천용)"""
    for v in self.four_gyeok(S, a, b).values():
        n = wrap81(v)
        if n not in self.good or n in DISPUTED:
            return False
    return True

_orig_analyze = NamingEngine.analyze_name

def _analyze_name_v2(self, sur, A, B, yong):
    out = _orig_analyze(self, sur, A, B, yong)
    for k, v in out['네격'].items():
        d = DISPUTED.get(v['적용수'], '')
        v['이견'] = d
        v['이견안내'] = DISPUTED_NOTE.get(d, '')
    out['이견격'] = [k for k, v in out['네격'].items() if v['이견']]
    return out

NamingEngine.four_ok_strict = _four_ok_strict
NamingEngine.analyze_name = _analyze_name_v2
