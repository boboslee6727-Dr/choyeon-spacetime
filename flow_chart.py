# -*- coding: utf-8 -*-
"""
flow_chart.py  —  [ 십성의 흐름 ] 그래프 (새 파일)
- 대운(천간·지지 십성 × 일간 기준 12운성) + 세운(같은 방식)을 원국 위에 더해
  해마다 비겁·식상·재성·관성·인성 힘을 구해 부드러운 곡선으로 그립니다.
- 추가 설치 없음(순수 파이썬 + SVG). 화면과 PDF 모두 같은 모양으로 나옵니다.
- 기존 대운표·세운표·월운표는 건드리지 않습니다.
"""
import math
import re

GROUPS = ["비겁", "식상", "재성", "관성", "인성"]
# 앱 사주표의 오행색과 동일 (html_views .color-목/화/토/금/수)
EL_COLOR = {"목": "#2E7D32", "화": "#C62828", "토": "#F9A825", "금": "#9E9E9E", "수": "#212121"}
EL_HANJA = {"목": "木", "화": "火", "토": "土", "금": "金", "수": "水"}

# 12운성 점수표 (박사님 확정, 0~100)
SCORE12 = {"장생": 70, "목욕": 50, "관대": 80, "건록": 90, "제왕": 100, "쇠": 55,
           "병": 30, "사": 15, "묘": 25, "절": 10, "태": 30, "양": 40}
COEF_UNIT = 1.5      # 점수 100 = 1.5배
W_DAEWUN = 10.0      # 대운 천간/지지 기본 힘
W_SEWUN = 4.0        # 세운 천간/지지 기본 힘
W_CHAR = 10.0        # 원국 글자 하나의 힘
W_WOLJI = 15.0       # 월지(월령)는 1.5배
SCALE_CHARS = 85.0   # 8자 기준 고정 눈금 (원국 합계 85점 = 평균 100)
BLANK = ("-", "?", " ", "", None)


def _coef(un):
    return SCORE12.get(un, 60) / 100.0 * COEF_UNIT


def _grp(engine, ds, ch):
    if ch in BLANK:
        return None
    ss = engine.get_ss(ds, ch)
    if not ss or ss == "-":
        return None
    return engine.get_group_ss(ss)


def _add(v, g, w):
    if g in v:
        v[g] += w


def _group_elements(engine, ds):
    """일간 기준 각 십성 그룹의 오행(한글: 목화토금수)"""
    dm = engine.get_color(ds)
    m = {"비겁": dm, "식상": engine._oh_next(dm), "재성": engine._oh_controls(dm),
         "관성": engine._oh_controlled_by(dm), "인성": engine._oh_prev(dm)}
    return m   # {그룹: 오행(한글)}


def compute_series(engine, ds, gans, jjis, birth_year, daewun_list, y_from, y_to):
    """해마다 5그룹 점수. 반환: {연도: {그룹: 점수}} (8자 기준 눈금)"""
    scale = 100.0 / (SCALE_CHARS / 5.0)
    base = {g: 0.0 for g in GROUPS}
    for ch in gans:
        _add(base, _grp(engine, ds, ch), W_CHAR)
    for i, ch in enumerate(jjis):
        _add(base, _grp(engine, ds, ch), W_WOLJI if i == 2 else W_CHAR)   # [시,일,월,년] 중 월지

    # 대운 구간: 시작 연도 = 출생년 + 대운수 - 1 (앱의 나이 계산과 동일)
    periods = []
    for dw in daewun_list or []:
        m = re.match(r"\s*(\d+)", str(dw.get("age_range", "")))
        if not m:
            continue
        st_y = int(birth_year) + int(m.group(1)) - 1
        periods.append((st_y, st_y + 9, dw))

    out = {}
    for y in range(y_from, y_to + 1):
        v = dict(base)
        for st_y, en_y, dw in periods:
            if st_y <= y <= en_y:
                c = _coef(dw.get("un_sung"))
                _add(v, engine.get_group_ss(dw.get("ss_gan")), W_DAEWUN * c)
                _add(v, engine.get_group_ss(dw.get("ss_ji")), W_DAEWUN * c)
        sg, sj = engine.GAN[(y - 4) % 10], engine.JI[(y - 4) % 12]
        c = _coef(engine.get_unsung(ds, sj))
        _add(v, _grp(engine, ds, sg), W_SEWUN * c)
        _add(v, _grp(engine, ds, sj), W_SEWUN * c)
        out[y] = {g: v[g] * scale for g in GROUPS}
    return out, periods


def _smooth(vals, sigma=1.0, radius=3):
    ker = [math.exp(-(k * k) / (2 * sigma * sigma)) for k in range(-radius, radius + 1)]
    n = len(vals)
    res = []
    for i in range(n):
        s = w = 0.0
        for k, kv in zip(range(-radius, radius + 1), ker):
            j = min(max(i + k, 0), n - 1)
            s += vals[j] * kv
            w += kv
        res.append(s / w)
    return res


def _path(pts, ymin, ymax):
    """점들을 부드러운 곡선(Catmull-Rom → 베지어)으로 잇는 SVG path"""
    if len(pts) < 2:
        return ""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        c1y = min(max(c1[1], ymin), ymax)
        c2y = min(max(c2[1], ymin), ymax)
        d += f" C{c1[0]:.1f},{c1y:.1f} {c2[0]:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def build_flow_html(engine, ds, gans, jjis, birth_year, daewun_list, curr_year,
                    title="[ 십성의 흐름 ]", max_age=100, mode="life"):
    """대운표 아래에 붙일 HTML(SVG 포함). 문제가 생기면 빈 문자열을 돌려줘서 화면이 깨지지 않게 합니다."""
    try:
        by = int(birth_year)
        y0 = by                      # 1세
        y1 = by + int(max_age) - 1   # 100세
        if mode == "daewun":         # 현재 대운 10년만 크게 (1-2 올해 운세용)
            for _st, _en, _dw in compute_series(engine, ds, gans, jjis, by, daewun_list, by, by)[1]:
                if _st <= curr_year <= _en:
                    y0, y1 = max(_st, by), _en
                    break
        els = _group_elements(engine, ds)
        pad = 4
        data, periods = compute_series(engine, ds, gans, jjis, by, daewun_list, y0 - pad, y1 + pad)
        ys = list(range(y0 - pad, y1 + pad + 1))
        sm = {g: _smooth([data[y][g] for y in ys]) for g in GROUPS}
        idx0, idx1 = pad, len(ys) - 1 - pad

        vmax = max(max(sm[g][idx0:idx1 + 1]) for g in GROUPS)
        ymax_v = max(250, int(math.ceil(vmax * 1.08 / 50.0)) * 50)

        W, H = 760, 420
        L, R, T, B = 40, 16, 16, 94
        pw, ph = W - L - R, H - T - B

        def X(y):
            return L + pw * (y - y0) / float(max(1, y1 - y0))

        def Y(v):
            return T + ph * (1 - min(max(v, 0), ymax_v) / float(ymax_v))

        s = [f"<svg viewBox='0 0 {W} {H}' width='100%' xmlns='http://www.w3.org/2000/svg' "
             f"style='display:block; font-family:\"Noto Sans CJK KR\",\"Malgun Gothic\",sans-serif;'>"]
        COL = {g: EL_COLOR.get(els[g], "#555") for g in GROUPS}
        s.append(f"<rect x='{L}' y='{T}' width='{pw}' height='{ph}' fill='#FFFDF0' stroke='#cfc8b8'/>")
        # 가로 눈금
        step = 50 if ymax_v <= 300 else 100
        for gv in range(0, ymax_v + 1, step):
            yy = Y(gv)
            s.append(f"<line x1='{L}' x2='{L + pw}' y1='{yy:.1f}' y2='{yy:.1f}' stroke='#ececec' stroke-width='1'/>")
            s.append(f"<text x='{L - 6}' y='{yy + 4:.1f}' font-size='11' fill='#6b6458' text-anchor='end'>{gv}</text>")
        # 평균선 100
        s.append(f"<line x1='{L}' x2='{L + pw}' y1='{Y(100):.1f}' y2='{Y(100):.1f}' stroke='#B8902F' stroke-width='1.2' stroke-dasharray='5,4'/>")
        # 대운 경계
        for st_y, en_y, dw in periods:
            if y0 < st_y <= y1:
                s.append(f"<line x1='{X(st_y):.1f}' x2='{X(st_y):.1f}' y1='{T}' y2='{T + ph + 82}' stroke='#8a8372' stroke-width='1'/>")
        # 선
        for g in GROUPS:
            pts = [(X(ys[i]), Y(sm[g][i])) for i in range(idx0, idx1 + 1)]
            s.append(f"<path d='{_path(pts, T, T + ph)}' fill='none' stroke='{COL[g]}' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'/>")
        # 올해 선
        if y0 <= curr_year <= y1:
            cx = X(curr_year)
            s.append(f"<line x1='{cx:.1f}' x2='{cx:.1f}' y1='{T}' y2='{T + ph}' stroke='#E0A800' stroke-width='2.4'/>")
            lab_x = cx + 5 if cx < L + pw - 70 else cx - 5
            anc = "start" if cx < L + pw - 70 else "end"
            s.append(f"<text x='{lab_x:.1f}' y='{T + 14}' font-size='12' font-weight='700' fill='#8a6a00' text-anchor='{anc}'>올해 {curr_year}</text>")
        # 가로축 글자: 대운이 바뀌는 곳마다 나이와 연도 (1세 시작점도 표시)
        if mode == "daewun":
            for yy_ in range(y0, y1 + 1):
                _cur = (yy_ == curr_year)
                s.append(f"<text x='{X(yy_):.1f}' y='{T + ph + 16}' font-size='{11.5 if _cur else 10}' font-weight='{900 if _cur else 500}' fill='{'#8a6a00' if _cur else '#555'}' text-anchor='middle'>{yy_}</text>")
                s.append(f"<text x='{X(yy_):.1f}' y='{T + ph + 29}' font-size='9.5' fill='#888' text-anchor='middle'>{yy_ - by + 1}세</text>")
                if yy_ in (y0, y1):
                    s.append(f"<text x='{X(yy_):.1f}' y='{T + ph + 42}' font-size='10' font-weight='700' fill='#3E2723' text-anchor='middle'>{'대운 시작' if yy_ == y0 else '대운 끝'}</text>")
                if _cur:
                    _g, _j = engine.GAN[(yy_ - 4) % 10], engine.JI[(yy_ - 4) % 12]
                    _hk = dict(zip('甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥', list('갑을병정무기경신임계자축인묘진사오미신유술해')))
                    s.append(f"<text x='{X(yy_):.1f}' y='{T + ph + 43}' font-size='12' font-weight='900' fill='#8a6a00' text-anchor='middle'>{_hk.get(_g, _g)}{_hk.get(_j, _j)}</text>")
        else:
            s.append(f"<text x='{X(y0):.1f}' y='{T + ph + 16}' font-size='10.5' fill='#555' text-anchor='middle'>1세</text>")
            s.append(f"<text x='{X(y0):.1f}' y='{T + ph + 29}' font-size='9.5' fill='#888' text-anchor='middle'>{y0}</text>")
        for st_y, en_y, dw in periods:
            if mode != "daewun" and y0 < st_y <= y1:
                s.append(f"<text x='{X(st_y):.1f}' y='{T + ph + 16}' font-size='10.5' fill='#333' font-weight='700' text-anchor='middle'>{st_y - by + 1}세</text>")
                s.append(f"<text x='{X(st_y):.1f}' y='{T + ph + 29}' font-size='9.5' fill='#888' text-anchor='middle'>{st_y}</text>")
        # 대운 간지 (구간 가운데)
        for st_y, en_y, dw in periods:
            a, b = max(st_y, y0), min(en_y + 1, y1)
            if b - a >= 4 and (mode != "daewun" or a <= curr_year <= b):
                mid = (X(a) + X(b)) / 2.0
                cur = st_y <= curr_year <= en_y
                s.append(f"<text x='{mid:.1f}' y='{T + ph + 62}' font-size='{16 if cur else 13}' font-weight='{900 if cur else 600}' "
                         f"fill='{'#3E2723' if cur else '#8a7a5a'}' text-anchor='middle'>{dw.get('c_hanja', '')}{dw.get('j_hanja', '')}</text>")
                s.append(f"<text x='{mid:.1f}' y='{T + ph + 77}' font-size='9' fill='#999' text-anchor='middle'>{st_y - by + 1}~{en_y - by + 1}세</text>")
        s.append("</svg>")

        legend = "".join(
            f"<span style='margin:0 8px; white-space:nowrap; font-size:13px; font-weight:700; color:{COL[g] if els[g] != "토" else "#B07800"};'>"
            f"<span style='display:inline-block; width:10px; height:10px; background:{COL[g]}; margin-right:4px;'></span>{EL_HANJA.get(els[g], '')} {g}</span>"
            for g in GROUPS)

        cur_vals = ""
        if y0 <= curr_year <= y1:
            i = ys.index(curr_year)
            cur_vals = (f"<div style='text-align:center; font-size:13px; color:#3E2723; margin-top:4px;'>"
                        f"<b>{curr_year}년 · {curr_year - by + 1}세</b> &nbsp; "
                        + " &nbsp; ".join(f"<span style='color:{COL[g] if els[g] != "토" else "#B07800"}; font-weight:700;'>{g} {int(round(data[curr_year][g]))}</span>" for g in GROUPS)
                        + "</div>")
        no_hs = (gans and gans[0] in BLANK) or (jjis and jjis[0] in BLANK)
        note = ("<div style='text-align:center; font-size:11px; color:#888; margin-top:3px;'>"
                "※ 점수 = 원국 + 대운·세운(12운성 반영), 점선 100 = 기준선"
                + (" · 시주 없음(6자) 사주는 8자 기준 눈금으로 표시" if no_hs else "") + "</div>")

        return (f"<div style='margin-top:12px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>{title}</div>"
                f"<div style='width:100%; border:2px solid #3E2723; background:white; margin-bottom:8px; padding:8px 6px 6px 6px; box-sizing:border-box; page-break-inside:avoid;'>"
                f"<div style='text-align:center; margin-bottom:4px;'>{legend}</div>{''.join(s)}{cur_vals}{note}</div>")
    except Exception:
        return ""
