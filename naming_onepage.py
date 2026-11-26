# -*- coding: utf-8 -*-
"""
naming_onepage.py  -  4-3 신생아 '한 장 작명서' (시안 4 확정판, 2026-11-25)
naming_ui.py 와 같은 폴더에 두고, naming_ui.py 에서 import naming_onepage as op 로 불러 씁니다.

들어 있는 것
  parse()          AI 가 쓴 글에서 [[표지]]별 본문을 나눔
  spouse_facts()   배우자와의 인연 사실(피할 띠·좋은 띠·피할 생월·색상)을 코드로 계산
  prompt()         한 장 작명서 풀이글을 AI 에게 시키는 글
  onepage_html()   A4 한 장 모양(둥근 이중 테두리, 서술형, 우측 정렬 + 낙인)
"""
import re as _re
from html import escape as _esc

_JI = '子丑寅卯辰巳午未申酉戌亥'
_ANIMAL = dict(zip(_JI, ['쥐', '소', '호랑이', '토끼', '용', '뱀', '말', '양', '원숭이', '닭', '개', '돼지']))
_JI_OH = dict(zip(_JI, '水土木木土火火土金金土水'))
_MONTH_OF = dict(zip('寅卯辰巳午未申酉戌亥子丑', range(1, 13)))           	# 월지 → 음력 월
_OH_MONTH = {'水': '子', '木': '卯', '火': '午', '金': '酉'}              		# 오행이 가장 순수한 달
_COLOR = {'木': '초록·청색', '火': '붉은색', '土': '노랑·황토색', '金': '흰색·은색', '水': '검정·남색'}
_SIX_HAP = [('子', '丑'), ('寅', '亥'), ('卯', '戌'), ('辰', '酉'), ('巳', '申'), ('午', '未')]
_SAM_HAP = ['申子辰', '亥卯未', '寅午戌', '巳酉丑']
_HYUNG = [('子', '卯'), ('寅', '巳'), ('巳', '申'), ('寅', '申'), ('丑', '戌'), ('戌', '未'), ('丑', '未')]
_GAN_K = dict(zip('甲乙丙丁戊己庚辛壬癸', '갑을병정무기경신임계'))
_JI_K = dict(zip(_JI, '자축인묘진사오미신유술해'))
_JI_TIME = dict(zip(_JI, ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해']))


def parse(text):
    """[[성품]] 같은 표지로 나뉜 글을 {표지: 본문} 으로"""
    got = {}
    for key, body in _re.findall(r"\[\[(\S+?)\]\]\s*(.*?)(?=\[\[\S+?\]\]|\Z)", str(text), flags=_re.S):
        got[key] = " ".join(body.split())
    return got


def _animals(chars):
    return "·".join(f"{_ANIMAL[c]}띠" for c in chars)


def spouse_facts(sj, yong):
    """
    일지(배우자 자리)로 피할 띠·좋은 띠·피할 생월·색상을 계산한다.
    yong : yong_from_engine() 결과 {'용신':'火', '희신':'木', '기신':'水', '구신':'金', ...}  (한자 오행)
    반환 : (dict, 글)
    """
    db = sj['jjis'][1]                       # 일지
    i = _JI.index(db)
    chung = _JI[(i + 6) % 12]
    hyung = {b if a == db else a for a, b in _HYUNG if db in (a, b)}
    avoid = [chung] + sorted(hyung - {chung}, key=_JI.index)
    bad_oh = {yong.get('기신'), yong.get('구신')} - {None, ''}
    good_oh = [o for o in (yong.get('용신'), yong.get('희신')) if o]
    good = []
    for a, b in _SIX_HAP:
        if db in (a, b):
            good.append(b if a == db else a)
    for g in _SAM_HAP:
        if db in g:
            good += [c for c in g if c != db]
    good = [c for c in dict.fromkeys(good) if c not in avoid and _JI_OH[c] not in bad_oh][:3]
    months = {_MONTH_OF[chung]}
    for o in bad_oh:
        if o in _OH_MONTH:
            months.add(_MONTH_OF[_OH_MONTH[o]])
    months = sorted(months)[:3]
    bad_colors = [_COLOR[o] for o in (yong.get('기신'), yong.get('구신')) if o in _COLOR]
    good_colors = [_COLOR[o] for o in good_oh if o in _COLOR]
    d = {'일지': db, '피할띠': avoid, '좋은띠': good, '피할생월': months, '피할색': bad_colors, '좋은색': good_colors}
    txt = (f"배우자 자리(일지): {db}({_ANIMAL[db]}띠)\n"
           f"결혼할 때 피할 띠: {_animals(avoid)} (일지와 충·형이 되는 띠)\n"
           f"좋은 띠: {_animals(good) if good else '특별히 꼽지 않음'} (일지와 합이 되는 띠)\n"
           f"상대의 생월에서 피할 달: 음력 {'월·'.join(str(m) for m in months)}월\n"
           f"옷이나 소지품에서 피할 색: {', '.join(bad_colors) if bad_colors else '특별히 없음'}\n"
           f"가까이하면 좋은 색: {', '.join(good_colors) if good_colors else '특별히 없음'}")
    return d, txt


def prompt(name, gender, golden, saju, facts1, facts2, dw1, dw2, ilji, spouse_txt):
    """한 장 작명서 풀이글 요청문. facts1/2 = build_naming_facts(an) 결과, dw1/2 = build_daewun_facts 결과"""
    return f"""당신은 '초연 시공명리 연구소'의 사주박사입니다. 신생아(아기)에게 지어 줄 이름 두 개를 추천하는 한 장짜리 작명서의 글을 씁니다.
부모님이 읽는 글이므로 쉬운 말로, 따뜻하고 품위 있게 씁니다. 아기를 '이 아기'라고 부르고 '당신'이라 하지 않습니다.
'용신·희신·기신·구신' 같은 전문 용어는 쓰지 말고 '사주에 꼭 필요한 기운', '피해야 할 기운'처럼 풀어 씁니다.
아래 [자료]에 없는 사실(오행, 수리, 뜻, 띠, 달, 색)은 지어내지 말고, 자료에 적힌 판정만 그대로 풀어 씁니다.
나이 숫자, 이혼·사별 같은 불길한 단정은 쓰지 않습니다. 글은 모두 이어지는 서술형 문장으로 씁니다(목록·표 금지).

[자료]
아기 성별: {gender}
{saju}
{golden}
배우자 자리(일지): {ilji}

[배우자와의 인연 자료 — 이 안의 띠·달·색만 그대로 쓸 것]
{spouse_txt}

[추천 ① 이름 자료]
{facts1}
{dw1}

[추천 ② 이름 자료]
{facts2}
{dw2}

[출력 형식 — 반드시 아래 4개 표지를 그대로 쓰고, 각 표지 다음 줄부터 본문만 쓰십시오. 제목·번호·마크다운·맺음말은 쓰지 않습니다.]
[[성품]]  (3문장: 일주와 월령으로 본 타고난 성품, 사주에 꼭 필요한 기운, 이름이 그 기운을 어떻게 채우는지)
[[이름1]] (3문장: ①글자들이 합쳐 이루는 뜻 한 문장 ②소리·자원·수리의 판정을 근거로 한 운세 한 문장 ③초년과 중년 이후의 대운을 이름의 격과 연결한 한 문장 — 대운 자료의 교차 판정을 따를 것)
[[이름2]] (3문장: 추천 ② 같은 방식. 추천 ①과 다른 점이 드러나게 쓸 것)
[[배우자]] (4~5문장: 일지의 기운으로 본 배우자 인연 한 문장, 이어서 피할 띠, 좋은 띠, 피할 생월, 피할 색과 가까이하면 좋은 색을 위 자료 그대로 자연스러운 문장으로)
"""


def _kor_time(b_time):
    """'07:30 ~ 09:29 (辰)' → '오전 7시 30분~9시 29분 진시(辰時)'"""
    s = str(b_time or '')
    if '모름' in s or not s.strip():
        return '시간 미상'
    m = _re.findall(r'(\d{1,2}):(\d{2})', s)
    mj = _re.search(r'\((.*?)\)', s)
    ji = ''
    if mj:
        ji = mj.group(1).replace('朝', '').replace('夜', '').strip()
    if not m:
        return s
    def f(h, mi, ap):
        h, mi = int(h), int(mi)
        hh = h % 12 or 12
        return (f"{'오전' if h < 12 else '오후'} " if ap else '') + f"{hh}시" + (f" {mi}분" if mi else '')
    a = f(*m[0], True)
    out = a if len(m) == 1 else a + '~' + f(*m[1], False).replace('시 ', '시 ')
    if ji and ji in _JI:
        out += f" {_JI_TIME[ji]}시({ji}時)"
    return out


def birth_lines(sj, gender, u_cal, b_year, b_month, b_day, b_time):
    """맨 위 두 줄: ①양력(음력)·시·성별 ②간지"""
    try:
        from korean_lunar_calendar import KoreanLunarCalendar
        k = KoreanLunarCalendar()
        if "음력" in str(u_cal):
            k.setLunarDate(int(b_year), int(b_month), int(b_day), "윤달" in str(u_cal))
            sol = (k.solarYear, k.solarMonth, k.solarDay)
            lun = (int(b_year), int(b_month), int(b_day), "윤달" in str(u_cal))
        else:
            k.setSolarDate(int(b_year), int(b_month), int(b_day))
            sol = (int(b_year), int(b_month), int(b_day))
            lun = (k.lunarYear, k.lunarMonth, k.lunarDay, bool(getattr(k, 'isIntercalation', False)))
        lun_txt = f"{'윤' if lun[3] else ''}{lun[1]}월 {lun[2]}일"
        sol_txt = f"{sol[0]}년 {sol[1]}월 {sol[2]}일"
    except Exception:
        sol_txt, lun_txt = f"{b_year}년 {b_month}월 {b_day}일", ''
    boy = str(gender).startswith('남')
    gtxt = '남아(乾命)' if boy else '여아(坤命)'
    l1 = (f"<b>양력</b> {sol_txt}" + (f" (<b>음력</b> {lun_txt})" if lun_txt else '') +
          f" · {_kor_time(b_time)} · {gtxt}")
    gans, jjis = sj['gans'], sj['jjis']                       # [시, 일, 월, 년]
    def pil(g, j, tail):
        if g in ('', '-', None) or j in ('', '-', None):
            return ''
        return f"{_GAN_K.get(g, g)}{_JI_K.get(j, j)}({g}{j}){tail}"
    parts = [pil(gans[3], jjis[3], '년'), pil(gans[2], jjis[2], '월'), pil(gans[1], jjis[1], '일'), pil(gans[0], jjis[0], '시')]
    l2 = " &nbsp;".join(p for p in parts if p)
    return l1, l2


def _name_box(rank, an):
    nm = an['이름']
    chain = lambda t: '→'.join(t) if t else ''
    if an.get('한글'):
        big = "".join(f"<div><b>{_esc(c)}</b></div>" for c in nm)
        chips = [f"소리 {chain(an.get('소리배합'))} {an.get('소리판정', '')}", f"음양 {an.get('음양', '')}", "순수 한글 이름"]
        kr = " ".join(nm)
    else:
        A, B = an.get('A'), an.get('B')
        rd = an.get('독음', '')
        cells = []
        if A:                                   # 보통: 성씨는 독음만, 이름 글자는 음·훈
            n_after = 2 if B else 1
            for i, ch in enumerate(nm[:-n_after]):
                cells.append((ch, rd[i] if i < len(rd) else ''))
            for k in (A, B):
                if k:
                    cells.append((k['h'], str(k['hun']).split('/')[0]))
        else:                                   # A/B 가 없으면 글자와 독음만
            for i, ch in enumerate(nm):
                cells.append((ch, rd[i] if i < len(rd) else ''))
        big = "".join(f"<div><b>{_esc(h)}</b><small>{_esc(s)}</small></div>" for h, s in cells)
        suri = an.get('네격') or {}
        nums = "·".join(str(v['수리']) for v in suri.values())
        suri_ok = '길' if suri and all(v.get('길흉') == '길' for v in suri.values()) else '흉 포함'
        chips = [f"소리 {chain(an.get('소리배합'))} {an.get('소리판정', '')}",
                 f"자원 {chain(an.get('자원배합'))} {an.get('자원판정', '')}",
                 f"수리 {nums} {suri_ok}"]
        kr = " ".join(rd)
    chip_html = "".join(f"<span>{_esc(c)}</span>" for c in chips)
    return (f"<div class='op2-nm'><span class='op2-rk'>추천 {rank}</span><div class='op2-hj'>{big}</div>"
            f"<div class='op2-kr'>{_esc(kr)}</div><div class='op2-ch'>{chip_html}</div></div>")


_CSS = """<style>
@page{size:A4;margin:8mm}
.op2-page{max-width:194mm;margin:0 auto;font-family:'Noto Serif KR','Noto Serif CJK KR',serif;color:#222;box-sizing:border-box}
.op2-page *{box-sizing:border-box}
.op2-frame{border:2.4px solid #1A237E;border-radius:18px;padding:5px;background:#fff;min-height:277mm}
.op2-inner{border:1px solid #b8962e;border-radius:13px;padding:7mm 12mm 6mm;display:flex;flex-direction:column;min-height:calc(277mm - 12px);background:linear-gradient(#fff,#fffdf6)}
.op2-orn{text-align:center;color:#b8962e;letter-spacing:6px;font-size:11px;line-height:1}
.op2-t{text-align:center;color:#1A237E;font-size:42px;font-weight:900;letter-spacing:22px;margin:4px 0 12px 22px;line-height:1.1}
.op2-rule{height:0;border-top:1px solid #b8962e;border-bottom:1px solid #b8962e;padding-top:2px;margin:0 0 11px}
.op2-birth{text-align:center;line-height:1.9;font-size:14.5px;margin-bottom:13px}
.op2-birth b{color:#1A237E}
.op2-birth .gj{font-size:15.5px;font-weight:700;color:#1A237E;letter-spacing:1px}
.op2-names{display:flex;gap:12px;margin-bottom:6px}
.op2-nm{flex:1;border:1.6px solid #1A237E;border-radius:12px;padding:12px 6px 9px;text-align:center;background:#fff;position:relative}
.op2-rk{position:absolute;top:-9px;left:50%;transform:translateX(-50%);background:#1A237E;color:#fff;border-radius:11px;padding:0 15px;font-size:11px;letter-spacing:2px;white-space:nowrap}
.op2-hj{display:flex;justify-content:center;gap:14px;margin-top:4px}
.op2-hj div{display:flex;flex-direction:column;align-items:center}
.op2-hj b{font-size:46px;line-height:1.05;color:#111;font-weight:900}
.op2-hj small{font-size:10.5px;color:#6b5a1e;margin-top:2px;white-space:nowrap}
.op2-kr{font-size:17px;font-weight:700;color:#1A237E;letter-spacing:6px;margin-top:5px}
.op2-ch{display:flex;gap:3px;justify-content:center;flex-wrap:wrap;margin-top:8px}
.op2-ch span{font-size:10px;background:#eef0fb;color:#1A237E;border-radius:9px;padding:1px 6px;white-space:nowrap}
.op2-page h3{font-size:15.5px;color:#1A237E;margin:12px 0 5px;border-left:4px solid #b8962e;padding-left:8px;letter-spacing:1px}
.op2-page p{margin:0 0 6px;font-size:13.6px;line-height:1.9;text-align:justify;text-indent:12px}
.op2-page p em{font-style:normal;color:#1A237E;font-weight:700}
.op2-sg{margin-top:auto;padding-top:4px;padding-bottom:7mm}
.op2-pl{text-align:center;font-size:14.5px;color:#333;letter-spacing:3px;margin-bottom:12px}
.op2-sgr{display:flex;justify-content:flex-end}
.op2-sgi{text-align:right;padding-right:2mm}
.op2-d{font-size:12.5px;letter-spacing:2px;color:#444}
.op2-o{font-size:17px;color:#1A237E;font-weight:900;letter-spacing:5px;margin-top:5px}
.op2-n{position:relative;font-size:17px;color:#1A237E;font-weight:900;letter-spacing:4px;margin-top:4px;padding-right:16mm}
.op2-seal{position:absolute;right:-3mm;top:0.5mm;width:21mm;height:21mm;transform:rotate(-4deg);opacity:.93;mix-blend-mode:multiply}
@media screen and (max-width:640px){
 .op2-names{flex-direction:column;gap:16px}
 .op2-inner{padding:6mm 5mm 6mm}
 .op2-t{font-size:32px;letter-spacing:12px;margin-left:12px}
 .op2-hj b{font-size:40px}
}
@media print{.op2-page{max-width:none;width:194mm;page-break-inside:avoid;break-inside:avoid}}
</style>"""


def _seal_src(html_views):
    try:
        m = _re.search(r'src="([^"]+)"', html_views.get_choyeon_sign_html())
        return m.group(1) if m else ''
    except Exception:
        return ''


def onepage_html(html_views, sj, gender, an1, an2, sec, birth_args, today_txt):
    """
    birth_args : (u_cal, b_year, b_month, b_day, b_time)
    today_txt  : '2026년 11월 25일'
    """
    def _p(key):
        return _esc(sec.get(key) or "(풀이글을 받지 못했습니다. 다시 만들어 주십시오.)")
    l1, l2 = birth_lines(sj, gender, *birth_args)
    seal = _seal_src(html_views)
    seal_tag = f"<img class='op2-seal' src=\"{seal}\">" if seal else ""
    n1, n2 = _esc(an1['이름']), _esc(an2['이름'])
    inner = f"""{_CSS}<div class='op2-page'><div class='op2-frame'><div class='op2-inner'>
<div class='op2-orn'>◆ ◇ ◆ ◇ ◆</div>
<div class='op2-t'>作名書</div>
<div class='op2-rule'></div>
<div class='op2-birth'><div>{l1}</div><div class='gj'>{l2}</div></div>
<div class='op2-names'>{_name_box('①', an1)}{_name_box('②', an2)}</div>
<h3>타고난 성품과 이름의 기운</h3><p>{_p('성품')}</p>
<h3>이름의 뜻과 운세</h3>
<p><em>{n1}({_esc(an1.get('독음', ''))})</em> {_p('이름1')}</p>
<p><em>{n2}({_esc(an2.get('독음', ''))})</em> {_p('이름2')}</p>
<h3>배우자와의 인연</h3><p>{_p('배우자')}</p>
<div class='op2-sg'><div class='op2-pl'>이와 같이 이름을 지어 드립니다.</div>
<div class='op2-sgr'><div class='op2-sgi'><div class='op2-d'>{_esc(today_txt)}</div>
<div class='op2-o'>초연 시공명리 연구소</div><div class='op2-n'>사주박사{seal_tag}</div></div></div></div>
</div></div></div>"""
    return inner

def notice_html(an1, an2, order_txt=""):
    """풀이 끝에 붙는 '이름 쓸 때 주의할 점' 상자 (한 장 작명서에서 옮겨 온 내용)"""
    warns = []
    for an in (an1, an2):
        for k in (an.get('A'), an.get('B')):
            if k and k.get('dj'):
                warns.append(f"{k['h']}({k['dj']})")
            if k and k.get('de'):
                warns.append(f"{k['h']}({k['de']})")
    warn_txt = ", ".join(dict.fromkeys(warns)) or "해당 글자 없음"
    items = [f"소리 주의: {warn_txt}",
             "불용한자: 책 9장 기준을 적용했습니다",
             order_txt or "출생 순서는 가리지 않았습니다",
             "도장·서명에는 한자 이름을 그대로 쓰시면 기운이 온전히 전해집니다"]
    li = "".join(f"<li>{_esc(x)}</li>" for x in items)
    return (f"<div style='margin-top:14px; padding:12px 16px; border:2px solid #1A237E; border-radius:8px; background:#F5F7FF; "
            f"page-break-inside: avoid; break-inside: avoid;'><div style='font-weight:900; color:#1A237E; font-size:16px; margin-bottom:6px;'>"
            f"이름 쓸 때 주의할 점</div><ul style='margin:0 0 0 18px; line-height:1.8;'>{li}</ul></div>")


def page_break_html(inner):
    """앞 내용과 다른 쪽에서 시작하게 감싸 준다"""
    return f"<div style='page-break-before: always; break-before: page;'>{inner}</div>"
