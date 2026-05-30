import streamlit as st
import pandas as pd
import json
import os
import math
import datetime as dt_mod  # 기존 박사님 코드 호환용
from datetime import datetime # 🚨 필수: 시간 연산용
from korean_lunar_calendar import KoreanLunarCalendar
import ephem
import google.generativeai as genai
import pytz
import streamlit.components.v1 as components
import re

# 🎯 [버전 컨트롤 타워]
APP_VERSION = "Ver 40.0 (Gemini 2.5-Pro Mode)"

# ==============================================================================
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS
# ==============================================================================
st.set_page_config(page_title=f"초연 시공명리 사주 {APP_VERSION}", layout="wide")

st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");
    
    body, .stApp { background-color: #FFF8E1; }
    
    .report-page { width: 210mm; max-width: 100%; margin: 30px auto; background-color: #FFFFFF !important; padding: 15mm 10mm; box-shadow: 0 0 20px rgba(0,0,0,0.15); border-radius: 20px; box-sizing: border-box; }
    .report-page, .report-page * { font-family: 'Noto Serif KR', serif !important; color: #000000; }
    
    .vip-inset-frame { border: 2px solid #1A237E; border-radius: 15px; padding: 20px; background: transparent; box-sizing: border-box; width: 100%; overflow: hidden; word-break: keep-all; -webkit-box-decoration-break: clone; box-decoration-break: clone; }

    .report-page h1 { font-size: 26px !important; margin-bottom: 15px !important; color: #1A237E !important; font-weight: 900 !important; }
    .report-page h2 { font-size: 22px !important; margin-bottom: 15px !important; font-weight: 900 !important; }
    .report-page h3 { font-size: 22px !important; margin-top: 25px !important; margin-bottom: 8px !important; border-bottom: 2px solid #1A237E; padding-bottom: 5px; color: #1A237E !important; font-weight: 900 !important; }
    .report-page h4 { font-size: 18px !important; margin-top: 15px !important; margin-bottom: 8px !important; font-weight: 900 !important; }
    
    .result-table { width: 100%; border-collapse: collapse; border: 3px solid #3E2723; margin-bottom: 15px; table-layout: fixed; }
    .result-table td { border: 1px solid #444; padding: 1px; text-align: center; vertical-align: middle; font-weight: 900; font-size: 13px; line-height: 1.2; word-wrap: break-word; }
    
    .no-border-row td { border-top: none !important; border-bottom: none !important; }
    .no-border-row:last-of-type td { border-bottom: 1px solid #444 !important; }
    
    .header-cell-main { background-color: #E8EAF6 !important; color: #1A237E !important; font-weight: 900 !important; font-size: 15px !important; border: 1px solid #444 !important; }
    
    .top-header-cell { background-color: #1A237E !important; height: 30px !important; }
    .top-header-cell td, .top-header-cell span { color: #FFFFFF !important; font-weight: 900 !important; font-size: 16px !important; }
    
    .color-목 { background-color: #2E7D32 !important; color: white !important; }
    .color-화 { background-color: #C62828 !important; color: white !important; }
    .color-토 { background-color: #F9A825 !important; color: black !important; }
    .color-금 { background-color: #9E9E9E !important; color: white !important; }
    .color-수 { background-color: #212121 !important; color: white !important; }
    
    /* 특수기호(▶, •, ◈) 소제목 및 일반 본문 제어 구역 */
    .content-box-loose { line-height: 1.8; font-size: 15px; color: #111; text-align: justify; word-break: keep-all; font-family: 'Noto Serif KR', 'Nanum Myeongjo', serif !important; padding: 0 !important; }
    
    .content-box-loose .sub-title { text-indent: 0px !important; margin-top: 25px !important; margin-bottom: 10px !important; font-weight: 900 !important; display: block; color: #111 !important; }
    
    /* 사이드바 버튼 색상 */    
    div[data-testid="stSidebar"] div.stButton > button:first-child { background-color: #D50000; color: white; border: none; font-weight: 900; height: 45px; }
    div[data-testid="stSidebar"] .navy-btn button { background-color: #1A237E !important; color: white !important; border: none !important; font-weight: 900 !important; height: 45px; }
    
    @media print { 
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; }
        .report-page { box-shadow: none; margin: 0 auto; padding: 0; page-break-after: always; border-radius: 0; width: 100%; max-width: 100%; }
        .report-page:last-of-type { page-break-after: auto; }
        .page-break-before { page-break-before: always; }
        .vip-inset-frame { border: 2px solid #000; border-radius: 20px; padding: 15px; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 0.5 [완전 무결점 하드코딩 DB] - 파일 시스템 원천 차단
# ==============================================================================
choyeon_db = {
    "wolryeong": {
        "甲子": "천둥번개 우뢰(甲)가 꽁꽁 얼어붙은 검은 연못(子)의 정적을 거세게 깨우는 완연한 한겨울",
        "乙丑": "찬 바람(乙)이 꽁꽁 얼어붙은 버드나무 언덕(丑)을 매섭게 휘감아 도는 가장 추운 겨울",
        "丙寅": "태양(丙)이 넓은 들판(寅)의 찬 기운을 녹이며 환히 비추는, 추위가 남아 있는 이른 봄",
        "丁卯": "영롱한 별빛(丁)이 옥 같이 아름다운 숲(卯)의 어둠을 밝히는 완연한 봄",
        "戊辰": "노을(戊)이 풀이 우거진 늪지(辰) 위로 내려앉아 수분이 차오르는 봄과 여름의 환절기",
        "己巳": "구름(己)이 큰 역(巳) 위로 머무르며 열기를 품기 시작하는 이른 여름",
        "庚午": "달빛(庚)이 횟불 신호대(午)의 정적 속에 고고하게 빛을 쏟아내는 완연한 여름",
        "辛未": "서리(辛)가 화원(未)의 열기를 식히지만 가장 무더운 여름",
        "壬申": "이슬(壬)이 대도시(申)의 마른 풀끝을 적시는 서늘한 이른 가을",
        "癸酉": "봄비(癸)가 사찰의 종(酉)을 적시며 결실을 거두는 완연 가을",
        "甲戌": "우뢰(甲)가 불태운 들판(戌)에 진동하며 결실을 저장하는 가을과 겨울의 환절기",
        "乙亥": "바람(乙)이 쏟아지는 강물(亥) 위를 스치며 추위가 스며드는 이른 겨울",
        "丙子": "태양(丙)이 검은 연못(子)을 비추는 깊어지는 한겨울",
        "丁丑": "별(丁)이 버드나무 언덕(丑)의 시린 어둠을 밝히는 가장 추운 겨울",
        "戊寅": "노을(戊)이 들판(寅)을 온화하게 감싸 안는 이른 봄",
        "己卯": "구름(己)이 아름다운 숲(卯) 위를 감싸는 완연한 봄",
        "庚辰": "달빛(庚)이 우거진 늪지(辰) 위로 쏟아지는 봄과 여름의 환절기",
        "辛巳": "서리(辛)가 큰 역(巳) 위로 내려앉는 이른 여름",
        "壬午": "이슬(壬)이 횃불 신호대(午) 위로 맺히는 완연한 여름",
        "癸未": "봄비(癸)가 화원(未)을 적시는 가장 무더운 여름",
        "甲申": "우뢰(甲)가 대도시(申)를 진동시키는 이른 가을",
        "乙酉": "바람(乙)이 사찰의 종(酉)을 울리는 완연한 가을",
        "丙戌": "태양(丙)이 불태운 들판(戌)을 비추는 가을과 겨울의 환절기",
        "丁亥": "별(丁)이 쏟아지는 강물(亥) 위를 밝히는 이른 겨울",
        "戊子": "노을(戊)이 검은 연못(子)의 정적을 비추는 한겨울",
        "己丑": "구름(己)이 버드나무 언덕(丑)을 덮어주는 가장 추운 겨울",
        "庚寅": "달빛(庚)이 넓은 들판(寅)의 정적을 비추는 이른 봄",
        "辛卯": "서리(辛)가 아름다운 숲(卯)에 내리는 완연한 봄",
        "壬辰": "이슬(壬)이 늪지(辰)를 적시는 봄과 여름의 환절기",
        "癸巳": "봄비(癸)가 큰 역(巳) 위로 내리는 이른 여름",
        "甲午": "우뢰(甲)가 횃불 신호대(午)를 진동시키는 완연한 여름",
        "乙未": "바람(乙)이 화원(未) 위를 스치는 가장 무더운 여름",
        "丙申": "태양(丙)이 대도시(申)를 환히 비추는 이른 가을",
        "丁酉": "별(丁)이 사찰의 종(酉)을 은은히 비추는 완연한 가을",
        "戊戌": "노을(戊)이 불태운 들판(戌)을 덮는 가을과 겨울의 환절기",
        "己亥": "구름(己)이 쏟아지는 강물(亥) 위에 머무는 이른 겨울",
        "庚子": "달빛(庚)이 검은 연못(子)을 비추는 한겨울",
        "辛丑": "서리(辛)가 버드나무 언덕(丑)에 내리는 가장 추운 겨울",
        "壬寅": "이슬(壬)이 들판(寅)을 적시는 이른 봄",
        "癸卯": "봄비(癸)가 아름다운 숲(卯)을 적시는 완연한 봄",
        "甲辰": "우뢰(甲)가 늪지(辰)를 진동시키는 봄과 여름의 환절기",
        "乙巳": "바람(乙)이 큰 역(巳) 위를 스치는 이른 여름",
        "丙午": "태양(丙)이 횟불 신호대(午)를 비추는 완연한 여름",
        "丁未": "영롱한 별빛(丁)이 화원(未)을 비추는 가장 무더운 여름",
        "戊申": "붉은 노을(戊)이 유명한 대도시(申)를 감싸는 이른 가을",
        "己酉": "포근한 구름(己)이 사찰의 종(酉) 위에 머무는 완연한 가을",
        "庚戌": "서늘한 달빛(庚)이 불태우는 근원(戌)을 비추는 가을과 겨울의 환절기",
        "辛亥": "하얀 서리(辛)가 쏟아지는 강물(亥) 위에 내리는 이른 겨울",
        "壬子": "가을이슬(壬)이 검은 연못(子)을 비추는 한겨울",
        "癸丑": "봄비(癸)가 버드나무 언덕(丑)을 적시는 가장 추운 겨울",
        "甲寅": "천둥번개 우뢰(甲)가 넓은 들판(寅)을 진동시키는 이른 봄",
        "乙卯": "바람(乙)이 옥 같이 아름다운 숲(卯)을 스치는 완연한 봄",
        "丙辰": "태양(丙)이 풀이 우거진 늪지(辰)를 비추는 봄과 여름의 환절기",
        "丁巳": "영롱한 별빛(丁)이 큰 역(巳)을 밝히는 이른 여름",
        "戊午": "붉은 노을(戊)이 횟불 신호대(午)를 덮는 완연한 여름",
        "己未": "포근한 구름(己)이 화원(未) 위에 머무는 가장 무더운 여름",
        "庚申": "서늘한 달빛(庚)이 유명한 대도시(申)를 비추는 이른 가을",
        "辛酉": "하얀 서리(辛)가 사찰의 종(酉) 위에 내리는 완연한 가을",
        "壬戌": "가을이슬(壬)이 불태우는 근원(戌) 위에 맺히는 가을과 겨울의 환절기",
        "癸亥": "봄비(癸)가 쏟아지는 강물(亥)을 적시는 이른 겨울"
    },
    "ilju": {
        "甲子": "검은 연못(子) 위에 울려 퍼지는 우레(甲)의 형상",
        "乙丑": "버드나무 언덕(丑)에 불어오는 바람(乙)의 형상",
        "丙寅": "넓은 들판(寅)을 비추는 태양(丙)의 형상",
        "丁卯": "옥 같이 아름다운 숲(卯) 위에 떠있는 밤하늘 별(丁)의 형상",
        "戊辰": "우거진 늪지(辰)에 드리워진 노을(戊)의 형상",
        "己巳": "커다란 역(巳) 위에 떠도는 구름(己)의 형상",
        "庚午": "봉화대(午) 위에 떠있는 밤하늘 달(庚)의 형상",
        "辛未": "아름다운 화원(未) 위에 내려앉은 서리(辛)의 형상",
        "壬申": "대도시(申)를 적시는 가을이슬(壬)의 형상",
        "癸酉": "사찰의 종(酉) 위에 내리는 봄비(癸)의 형상",
        "甲戌": "불 태우는 근원(戌) 위에 울려 퍼지는 우레(甲)의 형상",
        "乙亥": "거대한 강물(亥)에 불어오는 바람(乙)의 형상",
        "丙子": "검은 연못(子)을 비추는 태양(丙)의 형상",
        "丁丑": "버드나무 언덕(丑) 위에 떠있는 밤하늘 별(丁)의 형상",
        "戊寅": "넓은 들판(寅) 위에 드리워진 노을(戊)의 형상",
        "己卯": "옥 같이 아름다운 숲(卯)에 떠도는 구름(己)의 형상",
        "庚辰": "우거진 늪지(辰) 위에 떠있는 밤하늘 달(庚)의 형상",
        "辛巳": "대도시(巳)에 내려앉은 서리(辛)의 형상",
        "壬午": "봉화대(午)에 맺혀진 가을이슬(壬)의 형상",
        "癸未": "아름다운 화원(未)을 적셔주는 봄비(癸)의 형상",
        "甲申": "대도시(申)에 울려 퍼지는 우레(甲)의 형상",
        "乙酉": "사찰의 종(酉)을 스치는 바람(乙)의 형상",
        "丙戌": "불 태우는 근원(戌)를 비추는 태양(丙)의 형상",
        "丁亥": "거대한 강물(亥)를 비치는 밤하늘 별(丁)의 형상",
        "戊子": "검은 연못(子) 위에 드리워진 노을(戊)의 형상",
        "己丑": "버드나무 언덕(丑) 위에 떠도는 구름(己)의 형상",
        "庚寅": "넓은 들판(寅)을 비추는 밤하늘 달(庚)의 형상",
        "辛卯": "옥 같이 아름다운 숲(卯) 위에 내려앉은 서리(辛)의 형상",
        "壬辰": "우거진 늪지(辰) 위에 맺혀진 가을이슬(壬)의 형상",
        "癸巳": "커다란 역(巳)을 적시는 봄비(癸)의 형상",
        "甲午": "봉화대(午) 위에 울려 퍼지는 우레(甲)의 형상",
        "乙未": "아름다운 화원(未)에 불어오는 바람(乙)의 형상",
        "丙申": "대도시(申)를 비추는 태양(丙)의 형상",
        "丁酉": "사찰의 종(酉)을 비추는 밤하늘 별(丁)의 형상",
        "戊戌": "불태우는 근원(戌) 위에 드리워진 노을(戊)의 형상",
        "己亥": "거대한 강물(亥) 위를 떠도는 구름(己)의 형상",
        "庚子": "검은 연못(子) 위에 떠있는 밤하늘 달(庚)의 형상",
        "辛丑": "버드나무 언덕(丑) 위에 내리앉은 서리(辛)의 형상",
        "壬寅": "넓은 들판(寅) 위에 맺혀진 가을이슬(壬)의 형상",
        "癸卯": "옥 같이 아름다운 숲(卯)을 적셔주는 봄비(癸)의 형상",
        "甲辰": "우거진 늪지(辰) 위에 울려 퍼지는 우레(甲)의 형상",
        "乙巳": "커다란 역(巳)으로 불어오는 바람(乙)의 형상",
        "丙午": "봉화대(午) 위에 떠있는 태양(丙)의 형상",
        "丁未": "아름다운 화원(未)를 비추는 밤하늘 별(丁)의 형상",
        "戊申": "대도시(申) 위에 드리워진 노을(戊)의 형상",
        "己酉": "사찰의 종(酉) 위를 떠도는 구름(己)의 형상",
        "庚戌": "불태우는 근원(戌) 위에 떠있는 밤하늘 달(庚)의 형상",
        "辛亥": "거대한 강물(亥)에 내려앉은 서리(辛)의 형상",
        "壬子": "검은 연못(子) 위로 맺혀진 가을이슬(壬)의 형상",
        "癸丑": "버드나무 언덕(丑) 위에 내리는 진눈개비(癸)의 형상",
        "甲寅": "넓은 들판(寅) 위에 울려 퍼지는 우레(甲)의 형상",
        "乙卯": "옥 같이 아름다운 숲(卯)에 불어오는 바람(乙)의 형상",
        "丙辰": "갯벌(辰) 위를 비추는 태양(丙)의 형상",
        "丁巳": "커다란 역(巳)을 비추는 밤하늘 별(丁)의 형상",
        "戊午": "봉화대(午)에 드리워진 노을(戊)의 형상",
        "己未": "아름다운 화원(未) 위를 떠도는 구름(己)의 형상",
        "庚申": "대도시(申) 위에 떠있는 밤하늘 달(庚)의 형상",
        "辛酉": "사찰의 종(酉) 위에 내려 앉은 서리(辛)의 형상",
        "壬戌": "불태우는 근원(戌) 위에 맺혀진 가을이슬(壬)의 형상",
        "癸亥": "거대한 강물(亥) 위에 새차게 내리는 봄비(癸)의 형상"
    },
    "ilju_structure": {
        "甲子": ["인성구조", "자기몰입형", "자의식 발달하여 발상의 전환이 빠르고 임사즉결"],
        "乙丑": ["재관인구조", "출세지향형", "편법적 사고와 신속한 결과를 추구하며 앞서가는 경향"],
        "丙寅": ["인비식구조", "자기중심형", "감정기복이 심하고 매사를 주도하는 구조"],
        "丁卯": ["인성구조", "자기몰입형", "자의식 발달하여 발상의 전환이 빠르고 임사즉결"],
        "戊辰": ["비재관구조", "결과집착형", "원칙을 추구하며 결과를 중시하는 노력파"],
        "己巳": ["인비식구조", "자기중심형", "감정기복이 심하고 매사를 주도하는 구조"],
        "庚午": ["관인구조", "순리중시형", "주어진 환경에 적응하며 자기만족을 느끼며 최선을 다함"],
        "辛未": ["재관인구조", "출세지향형", "편법적 사고와 신속한 결과를 추구하며 앞서가는 경향"],
        "壬申": ["관인비구조", "원칙중시형", "원칙적 삶에 얽매여 노력하며 끊임없는 갈등구조"],
        "癸酉": ["인성구조", "자기몰입형", "자의식 발달하여 발상의 전환이 빠르고 임사즉결"],
        "甲戌": ["식재관구조", "현실타파형", "원칙타파 및 현상개선의 자유주의"],
        "乙亥": ["인비재구조", "자기만족형", "목표 지향적이며 계산적 경제관념이 분명"],
        "丙子": ["관성구조", "자기억제형", "주변 의식하고 내면의 갈등을 억제하여 정제된 삶 추구"],
        "丁丑": ["식재관구조", "현실타파형", "원칙타파 및 현상개선의 자유주의"],
        "戊寅": ["관인비구조", "원칙중시형", "원칙적 삶에 얽매여 노력하며 끊임없는 갈등구조"],
        "己卯": ["관성구조", "자기억제형", "주변 의식하고 내면의 갈등을 억제하여 정제된 삶 추구"],
        "庚辰": ["식재인구조", "다재다능형", "다재다능하고 창조적 감성표출의 달인"],
        "辛巳": ["관인비구조", "원칙중시형", "원칙적 삶에 얽매여 노력하며 끊임없는 갈등구조"],
        "壬午": ["재관구조", "실리추구형", "현실적 이익과 명예를 추구하는 계산된 실속파"],
        "癸未": ["식재관구조", "현실타파형", "원칙타파 및 현상개선의 자유주의"],
        "甲申": ["재관인구조", "출세지향형", "편법적 사고와 신속한 결과를 추구하며 앞서가는 경향"],
        "乙酉": ["관성구조", "자기억제형", "주변 의식하고 내면의 갈등을 억제하여 정제된 삶 추구"],
        "丙戌": ["비식재구조", "분주다망형", "목표추구의 자기주도와 적극적 대외활동"],
        "丁亥": ["식관인구조", "현실동조형", "일처리에 능숙하고 변동과 변화에 초연한 심리"],
        "戊子": ["재성구조", "이재추구형", "결과의 명확성을 추구하며 기민하고 분주하게 활동"],
        "己丑": ["비식재구조", "분주다망형", "목표추구의 자기주도와 적극적 대외활동"],
        "庚寅": ["재관인구조", "출세지향형", "편법적 사고와 신속한 결과를 추구하며 앞서가는 경향"],
        "辛卯": ["재성구조", "이재추구형", "결과의 명확성을 추구하며 기민하고 분주하게 활동"],
        "壬辰": ["비식관구조", "조직봉사형", "조직과 봉사활동을 통해 정체성을 추구"],
        "癸巳": ["재관인구조", "출세지향형", "편법적 사고와 신속한 결과를 추구하며 앞서가는 경향"],
        "甲午": ["식재구조", "자기과시형", "내실보다 외형을 중시하고 다소 무모한 결과를 추구"],
        "乙未": ["비식재구조", "분주다망형", "목표추구의 자기주도와 적극적 대외활동"],
        "丙申": ["식재관구조", "현실타파형", "원칙타파 및 현상개선의 자유주의"],
        "丁酉": ["재성구조", "이재추구형", "결과의 명확성을 추구하며 기민하고 분주하게 활동"],
        "戊戌": ["인비식구조", "자기중심형", "감정기복이 심하고 매사를 주도하는 구조"],
        "己亥": ["비재관구조", "결과집착형", "원칙을 추구하며 결과를 중시하는 노력파"],
        "庚子": ["식상구조", "현실추구형", "능수능란한 수단으로 매사를 주도하며 활로 모색"],
        "辛丑": ["인비식구조", "자기중심형", "감정기복이 심하고 매사를 주도하는 구조"],
        "壬寅": ["식재관구조", "현실타파형", "원칙타파 및 현상개선의 자유주의"],
        "癸卯": ["식상구조", "현실추구형", "능수능란한 수단으로 매사를 주도하며 활로 모색"],
        "甲辰": ["인비재구조", "자기만족형", "목표 지향적이며 계산적 경제관념이 분명"],
        "乙巳": ["식재관구조", "현실타파형", "원칙타파 및 현상개선의 자유주의"],
        "丙午": ["비식구조", "자기주도형", "비교우위에 서고자 매사를 적극적으로 주도하며 외향적"],
        "丁未": ["인비식구조", "자기중심형", "감정기복이 심하고 매사를 주도하는 구조"],
        "戊申": ["비식재구조", "분주다망형", "목표추구의 자기주도와 적극적 대외활동"],
        "己酉": ["식상구조", "현실추구형", "능수능란한 수단으로 매사를 주도하며 활로 모색"],
        "庚戌": ["관인비구조", "원칙중시형", "원칙적 삶에 얽매여 노력하며 끊임없는 갈등구조"],
        "辛亥": ["식재인구조", "다재다능형", "다재다능하고 창조적 감성표출의 달인"],
        "壬子": ["비겁구조", "의지분출형", "독자적 활로 모색과 배타적 자력갱생"],
        "癸丑": ["관인비구조", "원칙중시형", "원칙적 삶에 얽매여 노력하며 끊임없는 갈등구조"],
        "甲寅": ["비식재구조", "분주다망형", "목표추구의 자기주도와 적극적 대외활동"],
        "乙卯": ["비겁구조", "의지분출형", "독자적 활로 모색과 배타적 자력갱생"],
        "丙辰": ["식관인구조", "현실동조형", "일처리에 능숙하고 변동과 변화에 초연한 심리"],
        "丁巳": ["비식재구조", "분주다망형", "목표추구의 자기주도와 적극적 대외활동"],
        "戊午": ["인비구조", "주도면밀형", "치밀하게 이해득실을 추구하는 자기발전형"],
        "己未": ["관인비구조", "원칙중시형", "원칙적 삶에 얽매여 노력하며 끊임없는 갈등구조"],
        "庚申": ["인비식구조", "자기중심형", "감정기복이 심하고 매사를 주도하는 구조"],
        "辛酉": ["비겁구조", "의지분출형", "독자적 활로 모색과 배타적 자력갱생"],
        "壬戌": ["재관인구조", "출세지향형", "편법적 사고와 신속한 결과를 추구하며 앞서가는 경향"],
        "癸亥": ["비식관구조", "조직봉사형", "조직과 봉사활동을 통해 정체성을 추구"]
    }
}

# ==============================================================================
# 1. 시스템 변수 세팅 및 써머타임 엔진
# ==============================================================================
def get_total_time_adjustment(dt):
    adj = -30
    if dt_mod.datetime(1954, 3, 21) <= dt <= dt_mod.datetime(1961, 8, 9, 23, 59): adj = 0
    si = [(dt_mod.datetime(1948,5,31), dt_mod.datetime(1948,9,22)), (dt_mod.datetime(1949,3,31), dt_mod.datetime(1949,9,30)), (dt_mod.datetime(1950,4,1), dt_mod.datetime(1950,9,10)), (dt_mod.datetime(1951,5,6), dt_mod.datetime(1951,9,9)), (dt_mod.datetime(1954,3,21), dt_mod.datetime(1954,5,5)), (dt_mod.datetime(1955,4,6), dt_mod.datetime(1955,9,22)), (dt_mod.datetime(1956,5,20), dt_mod.datetime(1956,9,30)), (dt_mod.datetime(1957,5,5), dt_mod.datetime(1957,9,22)), (dt_mod.datetime(1958,5,4), dt_mod.datetime(1958,9,21)), (dt_mod.datetime(1959,5,4), dt_mod.datetime(1959,9,20)), (dt_mod.datetime(1960,5,1), dt_mod.datetime(1960,9,18)), (dt_mod.datetime(1987,5,10,2), dt_mod.datetime(1987,10,11,3)), (dt_mod.datetime(1988,5,8,2), dt_mod.datetime(1988,10,9,3))]
    for s, e in si:
        if s <= dt <= e: adj -= 60; break
    return adj

# 십천간 / 십이지지 리스트 전역 선언
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

def get_true_year_month_pillar(year, month, day, hour, minute):
    """
    [초연 시공명리 천문 엔진]
    ephem 모듈을 사용하여 태양의 황경(24절기)을 정밀 계산 후 정확한 년주와 월주를 반환합니다.
    """
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
    y_gan = GAN[year_idx % 10]
    y_ji = JI[year_idx % 12]
    
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
    m_gan = GAN[(start_month_gan_idx + m_offset) % 10]
    
    return f"{y_gan}{y_ji}", f"{m_gan}{JI[m_ji_idx]}", lon

components.html("""
<script>
    const doc = window.parent.document;
    doc.addEventListener('keyup', function(e) {
        if (e.target.tagName !== 'INPUT' || e.target.type !== 'text') return;
        let label = e.target.getAttribute('aria-label') || "";
        if (label.includes('년주') || label.includes('월주') || label.includes('일주')) {
            if (e.key === ' ' || e.target.value.includes('년') || e.target.value.includes('월') || e.target.value.includes('일') || e.target.value.includes('시')) {
                let inputs = Array.from(doc.querySelectorAll('input[type="text"]'));
                let idx = inputs.indexOf(e.target);
                if (idx > -1 && idx < inputs.length - 1) inputs[idx + 1].focus();
            }
        }
    });
</script>
""", height=0, width=0)

# ==============================================================================
# 2. AI 및 명리 연산 엔진
# ==============================================================================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as _api_e:
    st.error(f"🚨 Gemini API 키 오류: {_api_e}")
    model = None

def call_claude_api(prompt_text, max_tokens=8000):
    if model is None:
        return "<div style='color:red;'>🚨 Gemini 모델이 초기화되지 않았습니다. API 키를 확인하세요.</div>"
    try:
        response = model.generate_content(prompt_text)
        return response.text.strip()
    except Exception as e:
        return f"<div style='color:red;'>🚨 Gemini AI 서버 통신 장애: {e}</div>"

JIJANGGAN = {'子': ['壬', '-', '癸'], '丑': ['癸', '辛', '己'], '寅': ['戊', '丙', '甲'], '卯': ['甲', '-', '乙'], '辰': ['乙', '癸', '戊'], '巳': ['戊', '庚', '丙'], '午': ['丙', '己', '丁'], '未': ['丁', '乙', '己'], '申': ['戊', '壬', '庚'], '酉': ['庚', '-', '辛'], '戌': ['辛', '丁', '戊'], '亥': ['戊', '甲', '壬'] }

def get_color(c):
    if c in "甲乙寅卯": return "목"
    if c in "丙丁巳午": return "화"
    if c in "戊己辰戌丑未": return "토"
    if c in "庚辛申酉": return "금"
    if c in "壬癸亥子": return "수"
    return "토"

def get_current_saju_data():
    try:
        gans = st.session_state.get('saju_gans', ['?', '?', '?', '?'])
        jjis = st.session_state.get('saju_jjis', ['?', '?', '?', '?'])
        return gans, jjis
    except:
        return ['?', '?', '?', '?'], ['?', '?', '?', '?']

def get_ss(dg, tc):
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
    if ji in ["?", " ", "-"]: return "-"
    table = {'甲':"亥子丑寅卯辰巳午未申酉戌",'丙':"寅卯辰巳午未申酉戌亥子丑",'戊':"寅卯辰巳午未申酉戌亥子丑",'庚':"巳午未申酉戌亥子丑寅卯辰",'壬':"申酉戌亥子丑寅卯辰巳午未",'乙':"午巳辰卯寅丑子亥戌酉申未",'丁':"酉申未午巳辰卯寅丑子亥戌",'己':"酉申未午巳辰卯寅丑子亥戌",'辛':"子亥戌酉申未午巳辰卯寅丑",'癸':"卯寅丑子亥戌酉申未午巳辰"}
    idx = table.get(dg, "").find(ji)
    return ["장생","목욕","관대","건록","제왕","쇠","병","사","묘","절","태","양"][idx] if idx != -1 else "-"

def get_12_shinsal(year_ji, target_ji):
    if target_ji in ["?", " ", "-"] or not year_ji or year_ji == "?": return "-"
    s_map = {"申":"巳","子":"巳","辰":"巳", "寅":"亥","午":"亥","戌":"亥", "巳":"寅","酉":"寅","丑":"寅", "亥":"申","卯":"申","未":"申"}
    s_idx = (list(JI).index(target_ji) - list(JI).index(s_map.get(year_ji, "巳")) + 12) % 12
    return ["겁살","재살","천살","지살","년살","월살","망신살","장성살","반안살","역마살","육해살","화개살"][s_idx]

def get_samjae(year_ji, target_ji):
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
    me = gans[idx]; res = []
    if me in ["-", "?", " "]: return "-"
    for i, other in enumerate(gans):
        if i == idx or other in ["-", "?", " "]: continue
        s = {me, other}
        if s in [{'甲','己'}, {'乙','庚'}, {'丙','辛'}, {'丁','壬'}, {'戊','癸'}]: res.append("합")
        if s in [{'甲','庚'}, {'乙','辛'}, {'丙','壬'}, {'丁','癸'}, {'戊','甲'}, {'己','乙'}]: res.append("충")
    return "".join(list(set(res))) if res else "-"

def get_ji_rel_set(me, target):
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

def get_general_shinsal_filtered(idx, gans, jjis, gender="남성"):
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
    if ji in ["?", "-", " "]: return "-"
    raw = {'子':['壬','-','癸'],'丑':['癸','辛','己'],'寅':['戊','丙','甲'],'卯':['甲','-','乙'],'辰':['乙','癸','戊'],'巳':['戊','庚','丙'],'午':['丙','己','丁'],'未':['丁','乙','己'],'申':['戊','壬','庚'],'酉':['庚','-','辛'],'戌':['辛','丁','戊'],'亥':['戊','甲','壬']}.get(ji, ['-','-','-'])
    res = "<div style='display:flex; flex-direction:column; height:100%; min-height:65px; gap:2px; padding:2px 0; margin:0;'>"
    for j in raw:
        if j != '-':
            ss_label = get_ss(dg, j)[:2]; color_key = get_color(j)
            bg = {'목':'#2E7D32','화':'#C62828','토':'#F9A825','금':'#9E9E9E','수':'#212121'}.get(color_key, '#888')
            tc = 'white' if color_key != '토' else 'black'
            res += f"<div style='flex-grow:1; display:flex; align-items:center; justify-content:center; background:{bg}; color:{tc}; width:95%; margin:0 auto; font-size:12px; font-weight:900; border-radius:3px;'>{j} ({ss_label})</div>"
        else: 
            res += "<div style='flex-grow:1; display:flex; align-items:center; justify-content:center; background:#f9f9f9; width:95%; margin:0 auto; color:#bbb; border-radius:3px; border:1px dashed #ddd;'>-</div>"
    return res + "</div>"

def check_vault_status(base_gans, base_jjis, attacker_ji):
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
    # 1. 안전한 지장간 가져오기
    jg = JIJANGGAN.get(mb, [])
    if not jg: return "알수없음격", "지장간 정보가 없습니다."

    # 2. 안전한 get_ss 호출을 위한 래퍼(Wrapper) 함수
    def safe_get_ss(day_gan, target_char):
        if not target_char or target_char == "?": return "무명"
        return get_ss(day_gan, target_char)

    # 3. 자오묘유 격국 (안전하게 처리)
    if mb in ["子", "午", "卯", "酉"]:
        core_ss = safe_get_ss(ds, mb)
        return core_ss + "격", f"월지 {mb}의 순수한 기운인 {core_ss}을 그대로 격으로 삼습니다."
    
    target_gans = [ys, ms, hs] 
    main_qi = jg[-1]
    
    # 4. 지장간의 투출 확인 (인덱스 오류 방지)
    # 정기 확인
    if main_qi in target_gans:
        return safe_get_ss(ds, main_qi) + "격", f"월지 {mb}의 정기(본기)인 {main_qi}이 천간에 투출하여 {safe_get_ss(ds, main_qi)}격이 되었습니다."
    
    # 중기 확인 (길이 체크)
    if len(jg) >= 2 and jg[1] in target_gans:
        return safe_get_ss(ds, jg[1]) + "격", f"월지 {mb}의 중기인 {jg[1]}이 천간에 투출하여 {safe_get_ss(ds, jg[1])}격이 되었습니다."
    
    # 여기 확인
    if len(jg) >= 1 and jg[0] in target_gans:
        return safe_get_ss(ds, jg[0]) + "격", f"월지 {mb}의 여기인 {jg[0]}이 천간에 투출하여 {safe_get_ss(ds, jg[0])}격이 되었습니다."
        
    return safe_get_ss(ds, main_qi) + "격", f"월지 {mb}의 지장간이 투출하지 않아 정기(본기)인 {main_qi}를 기준으로 {safe_get_ss(ds, main_qi)}격으로 정합니다."

def calculate_gongmang(ilgan, ilji):
    if ilgan in ["?"," ","-"] or ilji in ["?"," ","-"]: return "-"
    try:
        base = (list(JI).index(ilji) - list(GAN).index(ilgan) - 2) % 12
        return list(JI)[base] + "," + list(JI)[(base+1)%12]
    except: return "-"

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

def get_daeun_su_accurate(utc_dt, order):
    try:
        sun = ephem.Sun()
        def get_lon(dt):
            sun.compute(dt)
            return math.degrees(ephem.Ecliptic(sun).lon) % 360.0

        start_lon = get_lon(utc_dt)
        jeol_lons = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]
        
        # 1. 목표 절기의 각도를 360도 누적 개념으로 추출
        if order == 1:
            t_lon_unwrapped = min([l for l in jeol_lons if l > start_lon] + [l + 360 for l in jeol_lons if l <= start_lon])
        else:
            t_lon_unwrapped = max([l for l in jeol_lons if l <= start_lon] + [l - 360 for l in jeol_lons if l > start_lon])
            
        search_dt = utc_dt
        # 2. 10분 단위 탐색으로 효율과 범위 극대화
        step = dt_mod.timedelta(minutes=10) if order == 1 else dt_mod.timedelta(minutes=-10)
        
        # 3. 6000회 탐색 (10분 * 6000 = 약 41.6일 커버)
        for _ in range(6000):
            search_dt += step
            curr_lon = get_lon(search_dt)
            
            # 360도 경계선 회전 보정 (Unwrapping)
            if order == 1 and curr_lon < start_lon and (start_lon - curr_lon) > 180:
                curr_lon += 360
            elif order == -1 and curr_lon > start_lon and (curr_lon - start_lon) > 180:
                curr_lon -= 360
                
            if (order == 1 and curr_lon >= t_lon_unwrapped) or (order == -1 and curr_lon <= t_lon_unwrapped):
                break
                
        # 4. 일수 계산 및 대운수 반올림
        total_days = abs((search_dt - utc_dt).total_seconds()) / 86400.0
        d_su = int(round(total_days / 3.0))
        
        # 5. 전통 명리학 보정
        if d_su == 0: d_su = 1
        elif d_su > 10: d_su = 10
        
        return d_su
    except Exception as e: 
        return 1

# ==============================================================================
# 3. 프리미엄 궁합 분석 엔진 클래스 (ver 38.0 통합 업그레이드본)
# ==============================================================================
def get_group_ss(ss_str):
    return {'비견':'비겁', '겁재':'비겁', '식신':'식상', '상관':'식상', '편재':'재성', '정재':'재성', '편관':'관성', '정관':'관성', '편인':'인성', '정인':'인성'}.get(ss_str, '비겁')

class UniversalPrintableGunghap:
    def __init__(self, applicant, partner_name, male, female, daeun_score=10):
        self.app, self.p_name, self.daeun_score = applicant, partner_name, daeun_score
        
        # 기본에 충실한 데이터 정제
        male = [m if m and len(m) >= 2 else "  " for m in (list(male) + ["  ", "  ", "  ", "  "])][:4]
        female = [f if f and len(f) >= 2 else "  " for f in (list(female) + ["  ", "  ", "  ", "  "])][:4]
        
        # [원상 복구 완료] 박사님의 오리지널 배열 인덱스 (3, 2, 1, 0)
        self.m_g = [male[3][0], male[2][0], male[1][0], male[0][0]]
        self.m_j = [male[3][1], male[2][1], male[1][1], male[0][1]]
        self.f_g = [female[3][0], female[2][0], female[1][0], female[0][0]]
        self.f_j = [female[3][1], female[2][1], female[1][1], female[0][1]]
        
        self.logic_flags, self.details = {}, []

    def get_ji_rel(self, j1, j2):
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
        for c in gans + jjis:
            if c in "甲乙寅卯": counts['목'] += 1
            elif c in "丙丁巳午": counts['화'] += 1
            elif c in "戊己辰戌丑未": counts['토'] += 1
            elif c in "庚辛申酉": counts['금'] += 1
            elif c in "壬癸亥子": counts['수'] += 1
        return counts

    def run_universal_logic(self):
        m_g, m_j, f_g, f_j = self.m_g, self.m_j, self.f_g, self.f_j
        il_rel = self.get_ji_rel(m_j[1], f_j[1])
        
        if il_rel == "육합": s1 = 25
        elif il_rel in ["방합", "반합"]: s1 = 21
        elif il_rel == "무": s1 = 17
        elif il_rel in ["파", "해"]: s1 = 12
        elif il_rel in ["형", "원진"]: s1 = 8
        elif il_rel == "충": s1 = 5
        else: s1 = 17
        p1 = int((s1 / 25) * 100)

        s2 = 5 
        n_rel, w_rel, si_rel = self.get_ji_rel(m_j[3], f_j[3]), self.get_ji_rel(m_j[2], f_j[2]), self.get_ji_rel(m_j[0], f_j[0]) 
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
        m_ilju, f_ilju = m_g[1] + m_j[1], f_g[1] + f_j[1]
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
        
        m_ss, f_ss = count_ss_groups(m_g[1], m_g + m_j), count_ss_groups(f_g[1], f_g + f_j)
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

    def generate_ai_report(self, m_ctx, f_ctx):
        m_ec, f_ec = self.count_elements(self.m_g, self.m_j), self.count_elements(self.f_g, self.f_j)

        def get_patho(ec):
            w = []
            if ec['목'] >= 3: w.append("목다화식/토붕")
            if ec['화'] >= 3: w.append("화다토조/금용")
            if ec['토'] >= 3: w.append("토다금매/수색")
            if ec['금'] >= 3: w.append("금다수탁/목절")
            if ec['수'] >= 3: w.append("수다목표/화멸")
            return ", ".join(w) if w else "오행구족(조화)"

        m_patho, f_patho = get_patho(m_ec), get_patho(f_ec)
        
        # 내담자의 일간(본신)을 자동으로 추출하는 범용 변수
        m_ilgan = self.m_g[1]
        m_ilju = f"{self.m_g[1]}{self.m_j[1]}"
        f_ilgan = self.f_g[1]
        f_ilju = f"{self.f_g[1]}{self.f_j[1]}"

        m_pillars = f"년주:{self.m_g[3]}{self.m_j[3]}, 월주:{self.m_g[2]}{self.m_j[2]}, 일주:{m_ilju}, 시주:{self.m_g[0]}{self.m_j[0]}"
        f_pillars = f"년주:{self.f_g[3]}{self.f_j[3]}, 월주:{self.f_g[2]}{self.f_j[2]}, 일주:{f_ilju}, 시주:{self.f_g[0]}{self.f_j[0]}"

        detail_scores_text = "\n".join([f"  * {d['label']}: {d['pct']}점" for d in self.details])

        prompt = f"""[SYSTEM ROLE: CHOYEON SIGONG MASTER]
당신은 명리심리상담사 '초연 박사'입니다. 아래 내담자의 정확한 사주 명조 데이터를 바탕으로 교차 분석 궁합 에세이를 작성하십시오.

[🗝️ 명리 통변의 대원칙 지시]
1. 사주 분석의 핵심 주체(본신)는 항상 '일간(日干)'을 기준으로 삼아야 합니다. 월간이나 년간의 세력이 강하더라도 이를 본신으로 오인하여 서술하지 마십시오.
2. 남성({m_ctx.get('u_name', '')})의 본신(일간)은 '{m_ilgan}'이며, 여성({f_ctx.get('u_name', '')})의 본신(일간)은 '{f_ilgan}'입니다. 모든 통변은 이 두 일간의 조화와 상생/상극을 중심으로 풀어나가십시오.
3. 임의의 사주 글자를 지어내거나 추측하는 행위(Hallucination)를 엄격히 배제하고, 제공된 사주 4기둥에 있는 글자만 대조하여 분석하십시오.

[남성 사주 명조]: {m_pillars} (오행 분포: {m_ec}, 병리: {m_patho})
[여성 사주 명조]: {f_pillars} (오행 분포: {f_ec}, 병리: {f_patho})

[📊 알고리즘 최종 점수 동기화 지시]
시스템이 산출한 두 사람의 '최종 궁합 점수는 {self.final_score}점'이며, 세부 항목은 다음과 같습니다.
{detail_scores_text}
(※ 주의: 점수 숫자 자체는 본문에 절대 노출하지 마십시오.)

<div class='choyeon-premium-report' style='line-height:1.9;'>
  <h3 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 24px; font-weight: bold; color: #1B5E20; border-bottom: 3px double #1B5E20; padding-bottom: 10px; margin-top: 10px;'>🍀 두 사람의 운명적 만남에 대하여</h3>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>('{m_ilgan}' 일간의 남성과 '{f_ilgan}' 일간의 여성이라는 본질을 바탕으로 인연의 총평을 구어체로 서술)</p>
  
  <h4 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 20px; font-weight: bold; color: #1A237E; margin-top: 40px;'>🌈 커플의 인생 기상도 분석</h4>
  <div style='margin: 10px 0 5px 0;'>[[COUPLE_DAEUN_TABLES]]</div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(대운 교차점에 따른 상생/보완 에세이를 구어체로 작성)</p>

  <h4 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 20px; font-weight: bold; color: #1A237E; margin-top: 40px;'>💞 커플의 5대 심층 조화도 분석</h4>
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>[내면의 유대감] - 속 궁합</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(남성의 일지와 여성의 일지를 대조하여 심리적 친밀감을 서술)</p>
  
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>[사회적 환경 조화] - 겉 궁합</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(남성의 월지와 여성의 월지를 대조하여 사회적, 현실적 조화를 서술)</p>
  
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>[기운의 상호 보완] - 오행 궁합</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(서로에게 부족한 기운을 어떻게 채워주는지 오행과 조후를 바탕으로 서술)</p>

  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>[특수 기운] - 신살 작용</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(실제 존재하는 신살만 정확히 파악하여 관계에 미치는 영향을 서술)</p>

  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 17px;'>[리스크 방어력] - 갈등 극복과 조율</span></div>
  <p style='text-indent: 15px; text-align: justify; word-break: keep-all; margin-bottom: 12px;'>(갈등 발생 시 두 사람이 이를 극복할 수 있는 내성 및 개운 처방 서술)</p>
</div>
※ 엄격한 주의사항: 본문(<p>) 작성 시 'font-family' 속성을 임의로 추가하지 마십시오. 전체 글꼴이 파괴됩니다.
"""
        return call_claude_api(prompt, max_tokens=12000)

    def get_graphic_html(self, ai_text, closing_text=""):
        c = "#3498db" if self.final_score >= 70 else ("#f39c12" if self.final_score >= 60 else "#e74c3c")
        
        bars_html = ""
        for item in self.details:
            bars_html += f"""
            <div style='display:flex; align-items:center; margin-bottom:12px;'>
                <div style='width:130px; font-size:13px; font-weight:bold; color:#555;'>{item['label']}</div>
                <div style='flex:1; height:12px; margin:0 10px;'>
                    <svg width='100%' height='12' style='display:block;'>
                        <rect width='100%' height='12' rx='6' ry='6' fill='#eeeeee' />
                        <rect width='{item['pct']}%' height='12' rx='6' ry='6' fill='{item['color']}' />
                    </svg>
                </div>
                <div style='width:35px; font-size:12px; font-weight:bold;'>{item['pct']}%</div>
            </div>"""
        
        gunghap_closing = f"""
        <div style='margin-top: 40px; padding-top: 30px; page-break-inside: avoid;'>
            <p style='font-size: 15px; line-height: 1.8; color: #333; font-family: "Noto Serif KR", serif;'>
                &nbsp;&nbsp;&nbsp;&nbsp;두 분의 <b style='color:#1A237E;'>'만남'</b>은 결코 우연이 아닌, <b style='color:#1A237E;'>'셀 수 없이 많은 시간 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 
                사주팔자는 각자의 바코드지만, <b style='color:#1A237E;'>'궁합(宮合)'</b>은 두 바코드가 만나 그려내는 새로운 <b style='color:#1A237E;'>'하모니(harmonie)'</b>입니다.
            </p>
            <p style='font-size: 15px; line-height: 1.8; color: #333; margin-top: 10px; font-family: "Noto Serif KR", serif;'>
                &nbsp;&nbsp;&nbsp;&nbsp;서로의 다름을 이해하고 채워주는 든든한 <b style='color:#1A237E;'>'동반자'</b>가 되시기를 진심으로 기원하며, 
                두 분의 앞날에 늘 시공간의 축복이 가득하시길 소망합니다. 
            </p>
            <div style='text-align: right; margin-top: 25px;'>
                <span style='font-weight: 900; font-size: 16px; color: #1A237E; font-family: "Noto Serif KR", serif;'>- 초연 시공명리 연구소 드림 -</span>
            </div>
        </div>
        """

        return f"""
        <div class='report-page' style='padding:40px; background:#fff;'>
            <div style='text-align:center; border-bottom:4px double #3E2723; padding-bottom:15px; margin-bottom:30px;'>
                <h1 style='margin:0; color:#3E2723; font-family: "Malgun Gothic", sans-serif; font-weight: 900;'>💞 초연 시공명리 종합 궁합풀이</h1>
            </div>
            <div style='background-color: #FAFAFA; padding: 40px; border: 2px solid #1A237E; border-radius: 15px; margin-bottom: 40px; -webkit-box-decoration-break: clone; box-decoration-break: clone;'>
                <div class='content-box-loose' style='margin-bottom: 50px;'>
                    {ai_text}
                </div>
                <h2 style='text-align:center; margin-top:0; color:#333; font-family: "Malgun Gothic", sans-serif; font-weight: 900; font-size: 22px; margin-bottom: 25px;'>📊 최종 궁합 점수</h2>
                <div style='display:flex; justify-content:center; align-items:center; margin-bottom:20px;'>
                    <div style='width:130px; height:130px; border-radius:50%; background:conic-gradient({c} {self.final_score}%, #f0f0f0 0); display:flex; justify-content:center; align-items:center; -webkit-print-color-adjust: exact;'>
                        <div style='width:98px; height:98px; background:#fff; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
                            <span style='font-size:32px; font-weight:900; color:{c};'>{self.final_score}</span>
                            <span style='font-size:10px; color:#888; font-weight:bold;'>SCORE</span>
                        </div>
                    </div>
                </div>
                <div style='text-align:center; margin-bottom:25px;'>
                    <span style='font-size:16px; font-weight:bold; color:#fff; background:{c}; padding:8px 32px; border-radius:30px; display: inline-block; -webkit-print-color-adjust: exact;'>{self.grade}</span>
                </div>
                <div style='max-width:500px; margin:0 auto; margin-bottom: 20px;'>
                    {bars_html}
                </div>
                {gunghap_closing}
            </div>
        </div>"""

# ==============================================================================
# 4. 사이드바 UI
# ==============================================================================
with st.sidebar:
    st.title("🏮초연 시공명리 연구소")
    st.caption(f"{APP_VERSION} Master (Base + Gunghap)")
    st.markdown("---")

    with st.expander("🔍 사주팔자 역산 검색", expanded=False):
        col_g1, col_g2 = st.columns(2)
        with col_g1: ry = st.text_input("년주", value="")
        with col_g2: rm = st.text_input("월주", value="")
        col_g3, col_g4 = st.columns(2)
        with col_g3: rd = st.text_input("일주", value="")
        with col_g4: rt = st.text_input("시주", value="")
        
        K2H_GAN = {'갑':'甲','을':'乙','병':'丙','정':'丁','무':'戊','기':'己','경':'庚','신':'辛','임':'壬','계':'癸'}
        K2H_JI = {'자':'子','축':'丑','인':'寅','묘':'卯','진':'辰','사':'巳','오':'午','미':'未','신':'申','유':'酉','술':'戌','해':'亥'}
        
        if st.button("🔍 생년월일 자동입력", use_container_width=True):
            _ry, _rm, _rd = ry.replace("년","").replace(" ","")[:2], rm.replace("월","").replace(" ","")[:2], rd.replace("일","").replace(" ","")[:2]
            if len(_ry)==2 and len(_rm)==2 and len(_rd)==2:
                ry_h = K2H_GAN.get(_ry[0], _ry[0]) + K2H_JI.get(_ry[1], _ry[1])
                rm_h = K2H_GAN.get(_rm[0], _rm[0]) + K2H_JI.get(_rm[1], _rm[1])
                rd_h = K2H_GAN.get(_rd[0], _rd[0]) + K2H_JI.get(_rd[1], _rd[1])
                klc_find = KoreanLunarCalendar(); found = False
                for y in range(2026, 1899, -1):
                    klc_find.setSolarDate(y, 7, 1); gj_y = klc_find.getChineseGapJaString().split()
                    if gj_y and gj_y[0][:2] == ry_h:
                        curr_dt = dt_mod.date(y+1, 2, 28)
                        while curr_dt >= dt_mod.date(y, 1, 1):
                            klc_find.setSolarDate(curr_dt.year, curr_dt.month, curr_dt.day)
                            gj = klc_find.getChineseGapJaString().split()
                            if len(gj) >= 3 and gj[0][:2] == ry_h and gj[1][:2] == rm_h and gj[2][:2] == rd_h:
                                st.session_state.s_y, st.session_state.s_m, st.session_state.s_d = curr_dt.year, curr_dt.month, curr_dt.day
                                time_map_rev = {'子':'00:30 ~ 01:29 (朝子)시','丑':'01:30 ~ 03:29 (丑)시','寅':'03:30 ~ 05:29 (寅)시','卯':'05:30 ~ 07:29 (卯)시','辰':'07:30 ~ 09:29 (辰)시','巳':'09:30 ~ 11:29 (巳)시','午':'11:30 ~ 13:29 (午)시','未':'13:30 ~ 15:29 (未)시','申':'15:30 ~ 17:29 (申)시','酉':'17:30 ~ 19:29 (酉)시','戌':'19:30 ~ 21:29 (戌)시','亥':'21:30 ~ 23:29 (亥)시'}
                                if rt:
                                    ji_char = rt.replace("시","").replace(" ","")[-1]
                                    rt_h = K2H_JI.get(ji_char, ji_char)
                                    if rt_h in time_map_rev: st.session_state.s_t = time_map_rev[rt_h]
                                found = True
                                is_leap = getattr(klc_find, 'isIntercalary', False)
                                leap_str = "윤달" if is_leap else "평달"
                                st.success(f"✅ [양력] {curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일 / [음력] {klc_find.lunarYear}년 {klc_find.lunarMonth:02d}월 {klc_find.lunarDay:02d}일 ({leap_str}) 입력완료!")
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                        if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

    st.markdown("---")
    u_product = st.selectbox("📋 분석 상품 선택", ["개인사주", "궁합", "타 감명서"])
    
    st.markdown("<div style='font-weight:900; color:#1A237E; margin-bottom:5px;'>👤 신청인 정보 (공통)</div>", unsafe_allow_html=True)
    u_name = st.text_input("이름", value="", placeholder="홍길동", key="u_n")
    u_gender = st.selectbox("성별", ["남성", "여성"], key="u_g")
    u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
    u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")
    
    col1, col2, col3 = st.columns(3)
    u_y = col1.number_input("년", 1900, 2050, key="s_y")
    u_m = col2.number_input("월", 1, 12, key="s_m")
    u_d = col3.number_input("일", 1, 31, key="s_d")
    
    idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]
    u_t = st.selectbox("태어난 시간", idx_list, key="s_t")
    
    p_name, p_gender, p_marital, p_cal, p_y, p_m, p_d, p_t = "", "여성", "미혼", "양력", 1967, 9, 24, "시간 모름"
    other_reading_text = ""
    run_delivery_calc = False  # [중요] 변수 사전 정의

    if u_product == "궁합":
        st.markdown("---")
        st.markdown("<div style='font-weight:900; color:#C62828; margin-bottom:5px;'>💕 상대방 정보</div>", unsafe_allow_html=True)
        p_name = st.text_input("이름", value="", placeholder="이영희", key="p_n")
        p_gender_default = "여성" if u_gender == "남성" else "남성"
        p_gender = st.selectbox("성별", ["남성", "여성"], index=["남성", "여성"].index(p_gender_default), key="p_g")
        p_marital = st.selectbox("혼인여부", ["미혼", "기혼", "돌싱"], index=1, key="p_m_stat")
        p_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="p_c")
        
        p_col1, p_col2, p_col3 = st.columns(3)
        p_y = p_col1.number_input("년", 1900, 2050, value=1967, key="p_y_in")
        p_m = p_col2.number_input("월", 1, 12, value=9, key="p_m_in")
        p_d = p_col3.number_input("일", 1, 31, value=24, key="p_d_in")
        p_t = st.selectbox("태어난 시간", idx_list, key="p_t_key")
        
        # ------------------------------------------------------------------
        # 👶 [VIP 전용 옵션] 출산 가능 연령(여성 49세 이하) 스마트 필터
        # ------------------------------------------------------------------
        import datetime
        current_year = datetime.datetime.now().year  # 실시간 현재 연도로 자동 동기화
        f_year = u_y if u_gender == "여성" else p_y
                    
        # 🚨 [중요] 여성 나이가 50세 이상이라 expander가 안 열릴 때를 대비한 기본값(에러 원천 차단)
        run_delivery_calc = False
        start_date = None
        end_date = None
                    
        if (current_year - f_year + 1) <= 49:
            with st.expander("👶 [VIP 심층 분석] 프리미엄 출산택일", expanded=False):
                baby_gender = st.radio("태아 성별", ["미정", "남아", "여아"], index=0)
                start_date = st.date_input("탐색 시작일")
                end_date = st.date_input("탐색 종료일")
                run_delivery_calc = st.checkbox("출산택일 리포트 생성")

    elif u_product == "타 감명서":
        st.markdown("---")
        st.markdown("<div style='font-weight:900; color:#2E7D32; margin-bottom:5px;'>📄 타 감명서 원문 입력</div>", unsafe_allow_html=True)
        other_reading_text = st.text_area("타 감명서 원문", height=250, placeholder="여기에 내용을 붙여넣기 하세요...", key="other_reading")
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_single = st.button("🚀 초연 시공명리 사주풀이 가동", use_container_width=True, type="primary")
    
    components.html("""
    <div style='padding: 0; margin: 0;'>
        <button id='sidebar-pdf-print-btn' style='width:100%; background-color:#2E7D32; color:white; border:none; font-weight:900; height:45px; border-radius:8px; cursor:pointer; font-size:15px; font-family:"Malgun Gothic", sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.15); transition: all 0.3s;'>
            🖨️ 풀이 결과 인쇄 / PDF 저장
        </button>
        <script>
            document.getElementById('sidebar-pdf-print-btn').addEventListener('click', () => {
                window.parent.print();
            });
        </script>
    </div>
    """, height=55)
# ==============================================================================
# 5. 분석 가동 및 출력 (Ver 34.5 직렬 구조 - 프로모델 최종 판본)
# ==============================================================================
if btn_single:
    # 1. 유효성 검사 (박사님 지시 순서 완전 동기화)
    if not u_name.strip(): 
        st.warning("⚠️ 신청인의 이름을 입력해 주세요.")
    elif u_product == "타 감명서" and not other_reading_text.strip():
        st.warning("⚠️ 타 감명서 원문을 입력해 주세요.")
    elif u_product == "궁합" and not p_name.strip(): 
        st.warning("⚠️ 상대방의 이름을 입력해 주세요.")
    else:
        # 스피너 가동 및 직렬 엔진 시작
        spinner_msg = f"⏳ [초연 시공명리 분석({APP_VERSION}) 중....]"
        with st.spinner(spinner_msg):
            

            # ==================================================================
            # [1단계] 공통 사주 엔진 (모든 변수 선언 및 천문 엔진 동기화)
            # ==================================================================
            try:
                # 1. 시스템 날짜 및 사용자 날짜 기초 변수 정의 (절대 누락 방지)
                curr_dt_sys = dt_mod.datetime.now()
                curr_y = curr_dt_sys.year
                curr_m = curr_dt_sys.month
                u_age = curr_y - u_y + 1
                base_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0)
                
                # 2. 날짜 세팅 및 윤달 판별 (KoreanLunarCalendar)
                klc = KoreanLunarCalendar()
                if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
                elif u_cal == "음력(평달)": klc.setLunarDate(u_y, u_m, u_d, False)
                else: klc.setLunarDate(u_y, u_m, u_d, True)
                
                # 3. 출력용 문자열 변수 정의
                is_leap = getattr(klc, 'isIntercalary', False)
                leap_str = "윤달" if is_leap else "평달"
                sol_str = f"{klc.solarYear}년 {klc.solarMonth:02d}월 {klc.solarDay:02d}일"
                lun_str = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({leap_str})"
                
                # 4. [엔진 교체] 정통 천문 엔진을 통한 년/월주 강제 교정
                true_ym, true_mm, _ = get_true_year_month_pillar(u_y, u_m, u_d, 12, 0)
                ys, yb = true_ym[0], true_ym[1]
                ms, mb = true_mm[0], true_mm[1]
                
                # 5. 일주/시주 세팅
                gj = klc.getChineseGapJaString().split()
                ds, db = gj[2][0], gj[2][1]
                hs, hb = get_time_ganji(ds, u_t, base_dt)
                
                # 6. 사주 리스트 및 주요 데이터 구성
                gans, jjis = [hs, ds, ms, ys], [hb, db, mb, yb]
                applicant_bazi = [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"]

                # 7. 대운 계산 로직
                adj_mins = get_total_time_adjustment(base_dt)
                utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
                order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
                calc_d = get_daeun_su_accurate(utc_dt, order)
                current_daewun_age = ((u_age - calc_d) // 10) * 10 + calc_d
                dw_start_age = current_daewun_age
                
                # 8. 연간지 로직 및 기타
                base_y_idx = (curr_y - 1984) % 60
                curr_y_ganji = GAN[base_y_idx % 10] + JI[base_y_idx % 12]
                time_str = f" {u_t.split('(')[0].strip()} ({hb})시" if u_t != "시간 모름" else ""
                
                # 9. HTML 출력용 함수 정의
                def td(c, size="18px"): return f"<td class='color-{get_color(c)}' style='font-size:{size}; font-weight:900; border:1px solid #444 !important;'>{('?' if c in ['?',' ','-'] else c)}</td>"
                
                intro_html = f"""
<div style='font-family: "Noto Serif KR", serif; font-size: 16px; font-weight: 600; color: #333; text-align: justify; line-height: 1.8; padding-bottom: 0px; margin-bottom: 25px;'>
    <p style='text-indent: 15px; margin: 0 0 5px 0;'>기존 전통 명리학 사주풀이는 1년에 한 번 돌아오는 '12월지'와 '60일주'의 조합으로 720가지의 유형으로 시작합니다만,</p>
    <p style='text-indent: 15px; margin: 0 0 5px 0;'>본 초연 시공명리 사주풀이는 5년에 한 번 돌아오는 '60월령'과 '60일주'의 조합으로 3,600가지의 유형으로 보다 더 정밀한 분석이 가능합니다.</p>
    <p style='text-indent: 15px; margin: 0;'>기존 전통명리학에 비교하면 '5배', 요즘 유행하는 MBTI의 16가지 유형과 비교하면 무려 '225배' 더 세분화된 정밀한 사주풀이 분석입니다.</p>
</div>
"""
                past_months_html = ""
                p_icon = "♂️" if u_gender == "남성" else "♀️"
                p_color = "#1A237E" if u_gender == "남성" else "#D50000"
                today_str = (dt_mod.datetime.utcnow() + dt_mod.timedelta(hours=9)).strftime("%Y년 %m월 %d일")

                cover_html = f"""
                <div class='report-page cover-page' style='padding:0; margin:0 auto; background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); display:flex; flex-direction:column; justify-content:center; align-items:center; min-height:100vh; page-break-after: always; -webkit-print-color-adjust: exact;'>
                    <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 85%; max-width: 750px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>
                        <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>
                            <h1 style='font-size: 32px; color: #1A237E; font-weight: 900; margin:0; font-family:"Malgun Gothic", sans-serif;'>🏮 초연 시공명리 사주팔자 풀이</h1>
                        </div>
                        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>
                            <h2 style='font-size: 24px; font-weight: 900; color: {p_color}; margin-bottom: 20px; font-family:"Malgun Gothic", sans-serif;'>{p_icon} 신청인 : {u_name} 님</h2>
                            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>
                                <p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p>
                                <p style='margin: 5px 0 0 0; color: #D50000; white-space: nowrap;'>{time_str}</p>
                            </div>
                        </div>
                        <p style='font-size: 18px; margin-top: 50px; font-weight: bold;'>{today_str}</p>
                        <p style='font-size: 22px; font-weight: 900; color: #1A237E; margin-top: 20px; font-family:"Malgun Gothic", sans-serif;'>초연 시공명리 연구소</p>
                    </div>
                </div>
                """
                ji_rel_rows = ""
                for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                    b_bot = "1px solid #444 !important" if l_idx == 3 else "none !important"
                    cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border:1px solid #444 !important; border-bottom:{b_bot};'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                    lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important;'>합충형파해</td>" if l_idx==0 else ""
                    ji_rel_rows += f"<tr>{lbl}{cells}</tr>"
                disp_name = u_name if u_name.strip() else "홍길동"
                info_h = f"""
                <div style='text-align:center; font-family:"Malgun Gothic", sans-serif; margin-bottom:15px; line-height:1.5;'>
                    <span style='font-size:18px; font-weight:900; color:#1A237E; white-space:nowrap;'>
                        {p_icon} {u_name}님 ({u_gender}, {u_marital}, {u_age}세)
                </span><br>
                <span style='font-size:14px; font-weight:900; color:#222; white-space:nowrap;'>
                    [양력] {sol_str} | [음력] {lun_str}{time_str}
                </span>
                </div>
                """

                table_html = f"""<div style='text-align:center; margin-bottom:10px;'>{info_h}</div>
    <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
    <tr class='top-header-cell'>
    <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>구분</td>
    <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>시주</td>
    <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>일주</td>
    <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>월주</td>
    <td style='border:1px solid #444; color:#FFFFFF !important; font-weight:900;'>년주</td>
    </tr>
    <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간합충</td>{"".join([f"<td style='border:1px solid #444;'>{get_gan_rel_all(i, gans)}</td>" for i in range(4)])}</tr>
    <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(ds,hs)}</td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(ds,ms)}</td><td style='border:1px solid #444;'>{get_ss(ds,ys)}</td></tr>
    <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:16px !important;'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
    <tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:16px !important;'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
    <tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(ds,hb)}</td><td style='border:1px solid #444;'>{get_ss(ds,db)}</td><td style='border:1px solid #444;'>{get_ss(ds,mb)}</td><td style='border:1px solid #444;'>{get_ss(ds,yb)}</td></tr>
    <tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
    {ji_rel_rows}
    <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이운성</td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
    <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이신살</td>{"".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
    <tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis, u_gender)) if get_general_shinsal_filtered(i, gans, jjis, u_gender) else '-'}</td>" for i in range(4)])}</tr>
    </table>
    """
                calc_gyukgook, gyukgook_detail = get_gyukgook_detailed(ds, mb, ys, ms, hs)

                gen_shinsal_list = []
                for i in range(4):
                    raw_tags = get_general_shinsal_filtered(i, gans, jjis, u_gender)
                    for tag in raw_tags:
                        if ">" in tag and "<" in tag: gen_shinsal_list.append(tag.split('>')[1].split('<')[0])
                shinsal_str = ", ".join(list(dict.fromkeys(gen_shinsal_list))) if gen_shinsal_list else "특이 신살 없음"
                
                s12_list = [get_12_shinsal(yb, j) for j in jjis if get_12_shinsal(yb, j) != "-"]
                s12_str = ", ".join(list(dict.fromkeys(s12_list))) if s12_list else "특이 12신살 없음"

                counts = {"목":0,"화":0,"토":0,"금":0,"수":0}
                for char in gans + jjis:
                    if char != "?": counts[get_color(char)] += 1
                
                guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
           
                guiin_str = guiin_map.get(ds, '없음')
                direction_str = "순행" if order == 1 else "역행"
                n_gong = calculate_gongmang(ys, yb)
                i_gong = calculate_gongmang(ds, db)
                cur_samjae = get_samjae(yb, curr_y_ganji[1])
                samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"
                
                master_bar_html = f"<div style='border:2px solid #3E2723; margin-top:20px; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap;'><div>⏳ 대운수: {calc_d}</div><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin_str}</div><div>🎯 공망: [일] {i_gong}</div><div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div></div>"                
                
                daewun_info = []
                un_html = f"<div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 대운의 흐름 (대운수: {calc_d}, {direction_str}) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(10):
                    val, c, j = i*10+calc_d, GAN[(GAN.index(ms)+(i+1)*order)%10] if ms in GAN else "-", JI[(JI.index(mb)+(i+1)*order)%12] if mb in JI else "-"
                    daewun_info.append(f"{val}세:{c}{j}")
                    is_active = val <= u_age < val+10
                    bg_col = "#FFF9C4" if is_active else "transparent"
                    b_left = "1px solid #ccc" if i != 9 else "none"
                    un_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{val}세</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,c)}</div><div class='color-{get_color(c)}' style='font-size:16px; font-weight:900;'>{c}</div><div class='color-{get_color(j)}' style='font-size:16px; font-weight:900;'>{j}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,j)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,j)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, j)}</div></div>"
                un_html += "</div>"

                cur_dw_idx = max(0, (u_age - calc_d) // 10)
                dw_g_cur = GAN[(GAN.index(ms) + (cur_dw_idx+1)*order)%10] if ms in GAN else "-"
                dw_j_cur = JI[(JI.index(mb) + (cur_dw_idx+1)*order)%12] if mb in JI else "-"
                current_daewun_age = cur_dw_idx * 10 + calc_d
                start_year = u_y + current_daewun_age - 1
                
                sewun_info = []
                se_html = f"<div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 세운의 흐름 ({dw_g_cur}{dw_j_cur}대운 기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(10):
                    ty = start_year + i
                    tage = current_daewun_age + i
                    base = (ty - 1984) % 60
                    tc, tj = GAN[base % 10], JI[base % 12]
                    sewun_info.append(f"{ty}년({tc}{tj})")
                    is_cur_yr = (ty == curr_y)
                    bg_col = "#E1F5FE" if is_cur_yr else "transparent"
                    b_left = "1px solid #ccc" if i != 9 else "none"
                    se_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; line-height:1.2; border-bottom:1px solid #ccc;'>{ty}년<br>({tage}세)</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div></div>"
                se_html += "</div>"

                wol_gans = ["己", "庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚"]
                wol_jis = ["丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子"]

                wol_html = f"<div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 월운의 흐름 ({curr_y}년도 양력기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(12):
                    tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
                    is_cur_m = (tm == curr_m)
                    bg_col = "#E8F5E9" if is_cur_m else "transparent"
                    b_left = "1px solid #ccc" if i != 11 else "none"
                    wol_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{tm}월</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div></div>"
                wol_html += "</div>"
                
                closing_html = f"""<div style='margin-top: 30px;'>
    <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드와 같지만, 우리가 살아가며 마주하는 스캐너인 운은 늘 변화하며 흐릅니다.</p>
    <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 초연 전통명리와의 인연이 <b>{disp_name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 나침반이 되기를 진심으로 기원합니다.</p>
    <p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 전통명리의 지혜와 궁금증이 있으시면 언제든 초연 전통명리 연구소의 문을 두드려 주십시오.</p>
    <p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
    <div style='text-align: right; margin-top: 30px;'>
    <span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
    </div>
    </div>"""

                w_key = f"{ms}{mb}".strip()
                i_key = f"{ds}{db}".strip()
                w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
                i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
                struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
                s_name, s_type, s_desc = struct_data[0], struct_data[1], struct_data[2]
                choyeon_golden_text = "<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000; margin-bottom: 20px;'><p style='text-indent: 15px; margin-bottom: 5px;'><b>" + disp_name + "님</b>은 '" + w_val + "'의 시공간에서, '" + i_val + "'의 성품을 가지고 태어나셨습니다.</p></div>"

                dw_mid_age   = current_daewun_age + 4
                dw_mid2_age  = current_daewun_age + 5
                dw_end_age   = current_daewun_age + 9
                
                # ------------------------------------------------------------------
                # [모드 1] 개인사주 전용 마크다운 호출 (궁합/비교 모드가 아닐 때만 실행)
                # ------------------------------------------------------------------
                if u_product in ["개인사주", "타 감명서"]:
                    
                    if u_age < 30:
                        age_prompt = "내담자는 청년기(학업, 진로, 취업, 연애 고민)에 있으므로 현실적인 직업과 이성운에 초점을 맞출 것."
                    elif u_age < 55:
                        age_prompt = "내담자는 중장년기(사회적 안정, 재물 축적, 가정)에 있으므로 재물운, 사업/직장운, 가정의 안정에 초점을 맞출 것."
                    else:
                        age_prompt = "내담자는 노년기(은퇴, 건강, 노후)에 있으므로 건강운과 심리적 평안, 노후 자산 안정에 초점을 맞출 것."
                        
                    gender_prompt = f"내담자는 {u_gender}이므로, {u_gender}의 심리적/사회적 특성을 섬세하게 고려하여 카운슬링할 것."
                    yukchin_rule = "- 육친 통변 규칙: 남명의 경우 재성을 배우자로, 관성을 자식으로 통변. 여명의 경우 관성을 배우자로, 식상을 자식으로 통변할 것."

                    wol_info_str = ", ".join([f"{i+1}월({wol_gans[i]}{wol_jis[i]})" for i in range(12)])
                    daewun_info_str = ", ".join(daewun_info)

                    # 🚨 [수정 포인트 2] db_header 내 년주 공망 삭제 및 오행 팩트 추가
                    db_header = (
                        f"[시스템 강제 시간 인식: 현재 시점은 {curr_y}년 {curr_m}월 입니다.]\n"
                        "당신은 명리심리상담사 1급 자격을 갖춘 초연 박사입니다. \n"
                        f"- 내담자 성함: {disp_name}\n"
                        f"- 나이 / 성별: {u_age}세 / {u_gender}\n"
                        f"- 🚨 [절대 기준 명조(사주팔자)]: 년주({ys}{yb}), 월주({ms}{mb}), 일주({ds}{db}), 시주({hs}{hb})\n"
                        f"- 🚨 [절대 기준 일간(본신)]: {ds} (모든 통변의 주체는 무조건 '{ds}' 일간을 기준으로 작성할 것)\n"
                        f"- 🚨 [오행 분포 팩트]: 목({counts['목']}), 화({counts['화']}), 토({counts['토']}), 금({counts['금']}), 수({counts['수']})\n"
                        f"- marital_status: {u_marital}\n"
                        f"- 타고난 심리 구조 팩트: {s_name} ({s_type} - {s_desc})\n"
                        f"- 공망 팩트: [일주 기준] {i_gong} (※ 반드시 일주 기준 공망만 사용하여 통변할 것)\n"
                    )

                    prompt = f"""
    {db_header}
    
    # 🚨 [제1규칙: 고객 맞춤형 페르소나 및 문체 자동 변환 지침 - 엄격 준수]
    # 현재 입력된 내담자의 프로필은 [연령대: {u_age}, 성별: {u_gender}, 혼인여부: {u_marital}] 입니다. 이 데이터를 절대 기준으로 삼아, 아래의 타기팅 규칙에 따라 서술의 톤앤매너(Tone & Manner)와 집중 분석 영역을 자동 조절하십시오.
    1. 연령별 문체(Tone): 
       - [2030 세대]: 스마트폰으로 읽기 편한 트렌디하고 다정한 '멘토형 구어체(~해요, ~합니다)'. 자존감을 끌어올리는 동기부여 문장 적극 구사.
       - [4050 세대 이상]: 인생의 굴곡을 이해하는 중후하고 품격 있는 '전문가형 경어체(~습니다, ~하십시오)'. '위기관리'와 '인생 2막 컨설팅'에 초점.
    2. 생애주기별 타격(Focus) 포인트:
       - [2030 미혼]: 천직과 커리어 우상향, 연애 성향 및 인연, 자산 형성(시드머니) 타이밍.
       - [3040 기혼]: 부동산 및 자산 증식, 자녀 기질 파악 및 교육, 부부 상생 개운법.
       - [50대 이상]: 건강 리스크 관리, 사회적 명예 유지, 자산 수성과 상속 흐름.
    3. 현대적 성별 유연성: 관성(官星)을 '사회적 무대와 권력'으로, 재성(財星)을 '목표 달성 능력과 재무 통제력'으로 입체화하여 구시대적 남녀 차별 해석을 배제하십시오.
    4. 따뜻한 상담가 마인드: 명리학 강의를 하듯 가르치려 들지 말고, 내담자의 삶을 깊이 이해하고 어루만져 주는 친절하고 세련된 카운슬러의 어조(현대적 구어체)로 모든 글을 전개하십시오.

    # 🚨 [제2규칙: 명리 용어 하이브리드(Hybrid) 표기 규칙 - 엄격 준수]
    통변의 전체적인 흐름은 대중이 읽기 편한 '현대적이고 감각적인 구어체'로 전개하되, 서술의 뼈대가 되는 전통 명리 용어(격국, 용신, 십성, 합형충파해 등)는 현대적 해석 직후 반드시 괄호 ( ) 안에 병기하여 학술적 깊이를 노출시키십시오. (예: "당신의 안정적인 자산 관리 능력(정재격)을 바탕으로...")
    - 특히, 내담자의 핵심 재능(월지 지장간) 투출을 분석하여 첫머리에 괄호 형태로 격국을 먼저 표기하십시오. (예: [정재격])

    # 🚨 [제3규칙: 운의 흐름에 따른 합충형해파(合沖刑害破) 정밀 타격 로직 (초연 핵심 비급)]
    AI는 사주 원국의 고정된 분석에 머무르지 말고, 반드시 [대운-세운-월운]의 흐름이 진입하며 일으키는 화학 반응을 시계열적으로 통변하십시오.

   🚨 [초연 시공명리 특화: 합충형해파(合沖刑害破) 및 행운(行運) 동기화 절대 규칙 - 엄격 준수]
    AI는 사주 원국(선천적 체명)의 고정된 분석에만 머무르지 마십시오. 반드시 [대운-세운-월운]의 흐름(후천적 용운)이 원국에 진입하며 일으키는 합충형해파의 역동적인 화학 반응을 추적하여 "언제, 어떤 일이 터지는지" 시계열적으로 통변하십시오. (명리 용어는 반드시 괄호 병기)

    1. 천간(정신)과 지지(현실)의 체용(體用) 철저 분리:
       - [천간 충극]: 대운/세운의 천간이 원국을 칠 때, 절대 물리적 사건으로 과장하지 말고 '가치관 혼란, 심리적 스트레스' 등 내면적 변화로만 서술하십시오.
       - [지지 요동]: 운명의 실질적 파괴와 생성(이직, 파재, 횡재 등)은 오직 '행운(대운/세운)의 지지가 원국 지지와 맺는 합충형해파'만을 근거로 삼아 예리하게 타격하십시오.

    2. 대운/세운에 따른 합(合)의 역동성과 顚倒(전도) 현상:
       - [연간합]: 행운 작용을 논하지 말고 초년기의 심리 상태로만 끝내십시오.
       - [일간 용봉/합봉]: 원국에 일간합이 있는데 대운/세운에서 똑같은 글자가 들어와 쟁합/투합이 발생하면, 기능이 묶이는 '용봉(用封)'으로 규정하여 해당 시기의 수성(守城)을 경고하십시오.
       - [일지합 동요]: 행운(대운/세운)이 원국의 일지합을 건드릴 때, 노력 대비 성과가 적은 '중구경득(重求輕得)'의 답답한 시기로 통변하십시오.

    3. 지지충(地支沖)의 위치적 차별화 및 장간 동요 정밀 분석:
       - [연지충 vs 일지충 철저 구분]: 원국의 '연지충(연지-월지)'은 초년의 심리적 갈등으로만 국한하고 개고를 논하지 마십시오. 모든 파괴력 있는 흉화와 충발(沖發), 행운충은 오직 '일지(日支)'를 기준으로 발생함을 명심하십시오.
       - [왕신발(旺神發)과 쇠자발(衰者拔)]: 행운충 발생 시, 약한 기운이 뽑히는 치명적 흉화(쇠자발)와 반대로 강한 기운이 충을 맞아 극적으로 대발복하는(왕신발) 세력의 길흉 전도를 명확히 묘사하십시오.
       - [사고(四庫)의 개고/입고 vs 생왕(生旺)의 개지]: 진술축미 충형 시에는 기물이 튀어나오는 개고(開庫)와 기존 천간 오행이 무덤에 갇히는 입고(入庫)의 치명적 리스크를 함께 경고하십시오. 단, 인신사해/자오묘유 충 시에는 무덤이 아니므로 입고를 논하지 말고, 지장간이 튀어나오는 '개지(開地)' 현상만을 십성의 성패로 통변하십시오.
       - [6충(六沖)의 질병 및 현실 물상]: 금목상쟁(寅申, 卯酉, 丑未)은 현실적 질병(간담, 뼈, 관절, 위장)과 직주 이동으로, 수화상전(巳亥, 子午, 辰戌)은 정신적/신경계 질환(공황, 스트레스, 심장, 혈액)과 원진/귀문관살의 흉화로 분류하여 경고하십시오.

    4. 🚨 운의 흐름에 따른 형해파(刑害破)의 정밀 타격과 스위치 작용 (초연 핵심 비급):
       - [형(刑)의 자화자초(自禍自招)와 4대 분류 타격]: 형살은 오만과 통제욕이 부른 '자화자초'입니다. 살생대권(殺生大權) 직업을 통한 '업상대체'를 최우선 해결책으로 제시하되, 아래 4분류를 엄격히 적용하십시오.
         ① 寅巳申: 독주와 권력욕. 배신/수술/교통사고 경고.
         ② 子卯: 규범 무시. 치명적인 이성 문제(도화의 난)와 대인관계 구설 경고.
         ③ 丑戌未: 고독지명. 재물은 크게 얻으나(개고) 육친의 아픔(입고)이 따르므로 활인업 수양 조언.
         ④ 자형(辰辰,午午,酉酉,亥亥): 강박과 편집증. 복음(伏吟) 운 동착 시 사기수(詐欺數)와 정신적 질환 주의.

       - [파(破)의 국면 전환과 왕지/협파(挾破) 타격]:
         ① 파살은 궤도를 강제로 이탈시키는 '스위치'입니다. 기존 운이 흉(凶)했다면 파운에 오히려 길(吉)로 전도되는 극적인 반전을 서술하십시오.
         ② (삼합 왕지 타격): 파가 성립하면 파살이 속한 삼합의 중심(왕지: 子午卯酉) 십성에 숨겨진 흉화가 발생함을 포착하십시오.
         ③ (협파 발현): 두 파살 지지 사이에 낀 숨은 지지(협파 지지)가 천간에 투출되어 있다면 해당 십성의 예기치 못한 타격을 경고하십시오. (투출되지 않았다면 생략)
         ④ (예외 규칙): 寅亥(인해)와 申巳(신사)는 파(破)이면서 합(合)이므로, 운에서 동착 시 파의 흉화는 멈추고 합의 길복으로 전도됨을 명시하십시오.

       - [해(害)의 미시적 훼방과 합극(合剋) 정지 작용]: 
         ① 해살은 육합을 와해시켜 일을 지연시키고 목전에서 실패(유시무종)하게 만드는 흉살로 묘사하되, 실질적 흉화는 '일지' 해살을 기준으로 판단하십시오. 
         ② (기능 정지 비급): 행운(대운/세운)에서 해살 지지와 '합(合)이나 극(剋)'하는 운이 오면 해살의 흉화가 일시적으로 정지되고, 오히려 원래의 육합(六合) 십성이 긍정적으로 발현되는 반전을 반드시 짚어내십시오.

    [절대 통제 명령]   
    1. 🚨[절대 성역]: 단, 문서 상단에 주입되는 '[CHOYEON_GOLDEN_TEXT_HERE]' (자의형상) 문장은 초연 박사의 고유한 선언문이므로 절대 이 지시의 영향을 받지 않으며, 부연 설명 없이 원문 그대로 100% 출력해야 합니다.
    2. 🚨 초연 시공명리 3대 관점의 입체적 풀이: 사주를 단편적으로 해석하지 마십시오. 모든 통변을 전개할 때는 반드시 1) 육친적 관점, 2) 심리적 관점, 3) 사회적 관점이라는 세 가지 차원을 유기적으로 융합하여 매우 심도 있고 입체적인 에세이를 작성하십시오.
    3. 🚨 외래어 및 외국어 혼용 철저 금지: 문맥에 맞지 않는 영어나 알파벳(예: teori 등)을 절대 섞어 쓰지 마십시오. 오직 자연스러운 표준 한국어로만 작성하십시오.
    
    [문단 통제 명령]
    1. 모든 통변 에세이 문장은 반드시 <p style='text-indent: 1em;'> 태그로 감싸십시오.
    2. 적절한 지점에서는 반드시 단락 나누기를 집행하십시오.
    3. 🚨 [계층별 글자 크기 및 상하 간격 강제 규격화] 가독성을 위해 목차의 성격에 따라 아래의 태그를 토씨 하나 틀리지 말고 적용하십시오! (반드시 display: block; 을 유지해야 상하 여백이 작동합니다)
    
       [지시 3-1] '1), 2)' 형태의 부목차는 20px 크기와 넓은 간격 적용:
       <span class='sub-title' style='display: block; font-size: 20px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 35px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
    
       [지시 3-2] '▶, ▷, ◈, •' 형태의 세부 소목차는 18px 크기와 좁은 간격 적용:
       <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 25px; margin-bottom: 5px;'>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</span>
       <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 25px; margin-bottom: 5px;'>• {dw_start_age}세~{dw_mid_age}세 대운:</span>
       <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 25px; margin-bottom: 5px;'>◈ 나를 돕는 에너지와 색상:</span>
    
    4. 별표 2개를 사용하여 글씨를 굵게 만드는 행위를 금지합니다.
    5. 🚨 호칭 강제: 내담자를 지칭할 때는 오직 '{disp_name}님'만 사용하십시오. ('선생님', '당신' 절대 사용 금지)
    6. 🚨 인사말 철저 금지: "안녕하십니까", "반갑습니다", "초연입니다" 등 쓸데없는 인사말이나 오지랖 멘트를 절대 작성하지 마십시오. 시작부터 바로 본론(사주 분석)으로 진입하십시오.
    7. 🚨 전통명리 이론 기반 통변: AI가 임의로 지어내는 문학적 비유를 철저히 금지합니다. 오직 사주 원국 간지의 물상 형상 등 정통 명리학 이론에 입각하여 이해하기 쉬운 구어체로 설명하십시오.
    8. 🚨 표(Table) 생성 절대 금지: AI가 임의로 마크다운 표(|---|)나 HTML <table>을 생성하는 것을 엄격히 금지합니다. 대운/세운/월운의 연도별 분석은 반드시 도트 기호(•)를 사용한 텍스트로만 작성하십시오.
    
    [내담자 맞춤형 정밀 타겟팅]
    - {age_prompt}
    - {gender_prompt}
    - {yukchin_rule}
    
    [통변 지시]
    - 모든 명리 용어는 대중이 이해하기 쉬운 현대적 구어체 표현 뒤에 괄호 형태로 병기하십시오.
    - 🚨 간지 및 지지 표기 규칙: 지지를 표기할 때 '巳화', '辰토'처럼 한글과 한자를 섞지 말고, 오직 巳(사), 辰(진)처럼 순수 한자 또는 괄호 병기 형태로만 일관되게 표기하십시오.
    - 격국 팩트: {gyukgook_detail}
    - 공망 팩트: 일주 기준 {i_gong}
    - 일반신살: {shinsal_str} / 12신살: {s12_str}
    - 입고/개고 팩트: 위 헤더에 제공된 원국 및 행운의 묘고 작용을 반드시 사주팔자의 역동적 관계 분석에 포함하십시오.
    """
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>1. 사주팔자 구조 분석</h3>
    <div class='content-box-loose'>
    [CHOYEON_GOLDEN_TEXT_HERE]
    (※ AI 지시: 위 마커 자리에 들어갈 문장은 초연 박사가 직접 작성한 절대적인 원문이므로 절대 건드리지 마십시오. 
    어떠한 부연 설명이나 사족도 덧붙이지 말고, 즉시 아래 '1) 타고난 삶의 무대와 나의 주력 무기' 분석으로 넘어가십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 타고난 삶의 무대와 기본 성향</span>
    (※ AI 지시: 내담자의 사주구조({gyukgook_detail})를 바탕으로 사회적 무대와 기본 성향을 에세이로 작성하십시오.
    🚨특히, 내담자의 핵심 재능(월지 지장간)이 어느 위치(연간, 월간, 시간)로 투출(뻗어 나갔는지)하였는지를 분석하여 괄호안에 격국을 먼저 표시하고,  
    "나의 재능이 어느 시기에(조기/즉각/대기만성), 어느 정도 규모의 무대(전국구/직장/개인)에서 어떻게 발현되는지"를 일반인이 이해하기 쉬운 현대적 구어체로 아주 구체적으로 풀어서 조언하십시오.)

    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 내 삶의 리듬과 에너지 균형</span>
    (※ AI 지시 🚨[오행 환각 절대 금지]: 반드시 헤더에 제공된 '🚨 [오행 분포 팩트]'의 실제 개수를 확인하십시오! 
    없는 오행(0개)을 강하다고 하거나, 있는 오행을 없다고 지어내는 소설을 엄격히 금지합니다. 
    실제 팩트 기반으로 사주팔자 오행의 분포와 계절적 조후, 억부의 균형 상태를 분석하고 삶에서 어떤 에너지를 추구해야 하는지 에세이를 작성하십시오.)

    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 사주팔자의 역동적 관계 분석</span>
    (※ AI 지시: 사주 원국의 합충형파해, 진술축미 입/개고, 일반신살 및 포태법의 명리적 원리를 철저히 분석하십시오. 
    🚨단, 절대 (丑丑), (卯丑)처럼 사주 원국의 한자나 명리 전문 용어를 괄호 안에 병기하거나 표면적으로 노출하지 마십시오. 
    오직 이 원리들을 바탕으로 내담자의 '전체적인 삶의 굴곡, 대인관계의 역동성, 직업적 변동성'에 초점을 맞추어 일반인이 이해하기 쉬운 구어체 에세이로만 작성하십시오. 
    이성운/부부운에 대한 언급은 제외하십시오.)
    </div>
    
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>2. 성격</h3>
    <div class='content-box-loose'>
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 겉으로 드러난 성격</span>
    (※ AI 지시: 일주의 십성 및 십이운성과 십이신살을 중심으로 육친적, 심리적, 사회적, 표면적으로 드러나는 성격과 기질을 구체적이고 현대적인 구어체로 작성하십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 감추어진 내 속마음</span>
    (※ AI 지시: 오행의 과다/과소 및 조후를 바탕으로 내면의 스트레스, 무의식적 욕구, 심리적 방어기제, 공망 등을 상세히 분석하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>3. 부모·형제운</h3><div class='content-box-loose'>
    (※ AI 지시: 사주 원국의 연주·월주 및 인성과 비겁의 상태를 분석하여 에세이를 작성하십시오. 1) 육친적으로 부모·형제와의 정서적 유대감과 덕의 유무를 살피고, 2) 심리적으로 이들이 내담자 내면의 자양분 혹은 결핍에 미친 영향을 진단하며, 3) 사회적으로 유년기 환경이 삶의 기반에 어떤 작용을 했는지 현대적 구어체로 친절하게 풀어내십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>4. 학업·진학운</h3><div class='content-box-loose'>
    (※ AI 지시: 인성과 식상의 관계, 관성의 통제력을 바탕으로 에세이를 작성하십시오. 1) 심리적으로 지적 호기심과 집중력의 방향성을 파악하고, 2) 육친적으로 학업 과정에서 주변 환경의 지지나 방해 요소를 보며, 3) 사회적으로 최종 학위나 전공이 현실적인 커리어와 어떻게 연결되는지 그 성패를 이해하기 쉽게 조언하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>5. 적성·직업운</h3><div class='content-box-loose'>
    (※ AI 지시: 원국의 구조와 주력 에너지를 바탕으로 에세이를 작성하십시오. 1) 심리적으로 어떤 직무나 환경에서 가장 큰 성취감과 동기를 얻는지, 2) 사회적으로 탄탄한 조직(직장)형 기질인지 개인 독립(전문직/사업)형 기질인지를 짚어 구체적인 직업적 방향성을 제안하고, 3) 육친적인 대인관계 협업 스타일까지 종합하여 세련된 구어체로 작성하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>6. 결혼·자녀운</h3><div class='content-box-loose'>
    (※ AI 지시: 일지와 시주, 재성/관성 및 식상의 동태를 분석하여 에세이를 작성하십시오. 1) 육친적으로 배우자 및 자녀 인연의 깊이와 형태를 살피되, 배우자 성(별)이 시주에 있다고 해서 무조건 '늦게 만난다'고 한정 짓지 말고 평생을 함께하는 든든한 동반자의 관점에서 유연하게 서술하십시오. 2) 심리적으로 내담자가 내면에서 바라는 이상적인 가정상과 정서적 정착 과정을 진단하며, 3) 사회적으로 가정을 꾸리는 것이 현실적 삶의 안정도에 미치는 변화를 카운슬러의 어조로 따뜻하게 서술하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>7. 재성운</h3><div class='content-box-loose'>
    (※ AI 지시: 재성의 유무와 상태, 식상의 생조 여부를 파악하여 에세이를 작성하십시오. 1) 심리적으로 돈과 물질을 대하는 가치관과 집착도를 진단하여 내담자 성향에 맞는 '재물 관리 스타일(투자형 vs 저축형)'을 정립해 주고, 2) 사회적으로 평생의 자산 규모와 경제적 성패의 흐름을 예측하며, 3) 육친적으로 재물로 인해 주변 사람들과 상생하거나 갈등하는 역동성을 조언하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>8. 사업운</h3><div class='content-box-loose'>
    (※ AI 지시: 식상생재의 흐름과 편재, 비겁의 조력 여부를 분석하여 에세이를 작성하십시오. 1) 심리적으로 위험을 감수하는 도전 정신과 시장을 읽는 직관력을 진단하고, 2) 사회적으로 독자적인 창업이나 사업체 운영의 적합성 및 규모 확장성을 예측하며, 3) 육친적으로 동업자, 직원, 고객을 끌어당기는 대인관계 리더십의 강점과 약점을 조언하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>9. 관직·명예운</h3><div class='content-box-loose'>
    (※ AI 지시: 관인상생 및 정관/편관의 상태를 바탕으로 에세이를 작성하십시오. 1) 사회적으로 조직 내에서의 승진, 명예, 라이선스(자격증) 취득 및 감투운을 평가하고, 2) 심리적으로 권력이나 자존심을 추구하는 욕구와 책임감의 크기를 분석하며, 3) 육친적으로 윗사람이나 대중, 사회적 시스템으로부터 인정받는 흐름을 매끄러운 구어체로 서술하십시오.)
    </div>
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>10. 건강운</h3><div class='content-box-loose'>
    (※ AI 지시: 오행의 분포와 과다/과소, 그리고 계절적 조후의 균형 상태를 분석하여 에세이를 작성하십시오. 1) 심리적 스트레스나 과로가 취약한 신체 기관(질환)으로 발현되는 원리를 명리적 물상과 연결하여 경고하고, 2) 사회 활동을 건강하게 지속하기 위한 현실적인 에너지 관리법을 제시하며, 3) 육친적 환경이 내담자의 정서적 안정과 건강에 미치는 영향까지 고려하여 친절하게 서술하십시오.)
    </div>
    
<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>11. 운의 흐름</h3>
    <div class='content-box-loose'>
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 대운의 흐름</span>
    (🚨 대운 간지 및 방향 팩트: 대운 방향은 {direction_str}이며, 각 대운의 흐름은 [{daewun_info_str}] 입니다.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 대운 분석</span>
    (※ AI 지시 🚨[대운 환각 및 총평 절대 금지]: 바로 위에 제공된 '대운 간지 및 방향 팩트' 데이터를 반드시 확인하십시오. 절대 두 개 이상의 대운을 하나로 묶어서 서술하지 마십시오! 반드시 10년 단위로 끊어서 개별 항목으로 나열하십시오. 항목 제목은 **• {calc_d}세~{calc_d+9}세 대운:** 과 같이 마크다운 굵은 글씨로 강조하십시오. 표 생성 절대 금지. 🚨중요: 분석 내용 출력 직후 반드시 [DAEWUN_TABLE_HERE] 마커를 원형 그대로 출력하십시오.)
    
    [DAEWUN_TABLE_HERE]

    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 현재 대운 전반기 상세 분석 ({dw_start_age}세~{dw_mid_age}세)</span>
    (※ AI 지시 🚨[진술축미 묘고 작용 필수 통변]: 현재 진입한 대운의 지지와 사주 원국의 지지가 만나 진(辰), 술(戌), 축(丑), 미(未)의 충(沖)이나 형(刑)으로 인한 입고(入庫) 및 개고(開庫) 작용이 발생한다면, 이로 인한 삶의 극적인 변화(재물, 대인관계, 환경 등)를 반드시 상세히 통변하십시오. 대운 한가운데를 지나고 있다는 등 시기적 착각을 절대 금지합니다.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</span>
    (※ AI 지시: 현재 대운 후반기의 십성과 오행 기운이 내담자의 삶에 미치는 심리적, 사회적 변화를 상세히 카운슬링하십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 세운의 흐름</span>
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 세운 분석</span>
    (※ AI 지시: 최근 지나온 과거 각 세운들을 하나씩 나열하되, 항목의 제목은 반드시 **• 2024년(甲辰년):** 과 같이 간지를 한자로 표기하고 마크다운 굵은 글씨로 강조하여 요약하십시오. 표 생성 절대 금지. 🚨중요: 분석 내용 출력 직후 반드시 [SEWUN_TABLE_HERE] 마커를 원형 그대로 출력하십시오.)
    
    [SEWUN_TABLE_HERE]

    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 올해 세운 전반기 상세 분석</span>
    (※ AI 지시: 올해 세운 전반기(양력2월~7월)의 십성과 오행 기운을 상세히 카운슬링하십시오.)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 올해 세운 후반기 상세 분석</span>
    (※ AI 지시: 올해 세운 후반기(양력8월~다음년도 1월)의 십성과 오행 기운을 상세히 카운슬링하십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 월운의 흐름</span>
    (🚨 올해 월운 간지 팩트: {wol_info_str})
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 월운 분석</span>
    {past_months_html}
    (※ AI 지시 🚨[월운 환각 절대 금지]: 올해 지나온 각 과거 월운들을 하나씩 나열하되, 항목의 제목은 반드시 **• 2월(해당간지월):** 과 같이 마크다운 굵은 글씨(**)로 강조하여 2~3줄씩 요약하십시오. 
    🚨단, 명리학적 기준(입춘)에 따라 양력 1월은 작년도 세운의 음력 12월(己丑월)에 해당하므로, 1월 분석 시 반드시 이 점을 맞추어 작년의 기운이 마무리되는 흐름으로 풀이하십시오. 표 생성 절대 금지. 🚨중요: 분석 내용 출력 직후 반드시 [WOLWUN_TABLE_HERE] 마커를 원형 그대로 출력하십시오.)
    
    [WOLWUN_TABLE_HERE]

    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 이번 달 전반기(5일~19일) 상세 분석</span>
    (※ AI 지시: 해당하는 월의 전반기(5일~19일)를 구체적인 조후와 기운의 흐름을 조언하십시오.)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 이번 달 후반기(20일~다음달 4일) 상세 분석</span>
    (※ AI 지시: 해당하는 월의 후반기(20일~다음 달 4일까지)를 구체적인 조후와 기운의 흐름을 조언하십시오.)
    
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 행운에 따른 종합 기운 조언</span>
    (※ AI 지시: 대운, 세운, 월운이 융합되어 일으키는 역동적인 변화와 내담자가 취해야 할 최종 삶의 태도를 따뜻하게 서술하며 마무리하십시오.)
    </div>

    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>12. 삶을 바꾸는 지혜로운 조언</h3>
    <div class='content-box-loose'>
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 나를 돕는 에너지와 색상:</span>
    (※ AI 지시: 에세이 작성)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 신체 밸런스와 에너지 관리:</span>
    (※ AI 지시: 에세이 작성)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 공간의 흐름과 방위의 지혜:</span>
    (※ AI 지시: 에세이 작성)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 재능 효율을 높이는 직업적 지혜:</span>
    (※ AI 지시: 에세이 작성)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 더 나은 내일을 위한 절제의 미학:</span>
    (※ AI 지시: 에세이 작성)
    </div>
    
    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'> 🎯 초연 시공명리 특별 개운 비법</h3>
    <div class='content-box-loose'>
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 수호 천사의 기운:</span>
    (※ AI 지시: 사주원국 및 운(시간)의 흐름에 따른 천을귀인과 길신 등의 작용에 대한 상세한 에세이를 작성하시오.)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 백년해로의 기운:</span>
    (※ AI 지시: 오행의 치우침, 원진, 고란살, 고신(남명), 과숙(여명) 등 이성 관계에 영향을 미치는 사주원국 및 운의 흐름을 분석하되, 전문 용어는 철저히 숨기십시오. 
    이곳에서는 오직 '부부 및 연인 관계에서 발생할 수 있는 성격적/상황적 갈등 요소'와 이를 슬기롭게 극복하고 백년해로하기 위한 
    '실질적이고 따뜻한 개운 비법(마음가짐, 소통 방식, 행동 요령 등)'에만 100% 초점을 맞추어 카운슬러의 어조로 작성하십시오.)
    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 행운에 따른 기운:</span>
    (※ AI 지시: 운의 흐름에 따른 합형충파해와 진술축미의 입고와 개고, 도화(연살)/망신/역마살 작용에 따른 역동성과 재물과 대인관계 등 주의할 점에 대한 상세한 에세이를 작성하시오.)
    </div>
    """
                res_text = call_claude_api(prompt, max_tokens=12000)
                ai_text = "\n".join([line.lstrip() for line in res_text.split("\n")])
                
                if "[CHOYEON_GOLDEN_TEXT_HERE]" in ai_text:
                    ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)
                else:
                    target_marker = "1) 타고난 삶의 무대와 기본 성향"
                    if target_marker in ai_text:
                        parts = ai_text.split(target_marker)
                        div_marker = "<div class='content-box-loose'>"
                        if div_marker in parts[0]:
                            top_clean = parts[0][:parts[0].find(div_marker) + len(div_marker)]
                            ai_text = top_clean + f"\n{choyeon_golden_text}\n<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>" + target_marker + parts[1]

                un_html_clean = un_html.replace("\n", " ").replace("\r", "")
                se_html_clean = se_html.replace("\n", " ").replace("\r", "")
                wol_html_clean = wol_html.replace("\n", " ").replace("\r", "")

                clean_ai_text = ai_text

                daeoun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{un_html_clean}</div>"
                sewun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{se_html_clean}</div>"
                wolwun_target = f"<div style='margin: 15px 0; overflow-x: auto;'>{wol_html_clean}</div>"

                clean_ai_text, count_d = re.subn(r'[\#\*\_\s]*\[\s*DAEWUN_TABLE_HERE\s*\][\#\*\_\s]*', daeoun_target, clean_ai_text, flags=re.IGNORECASE)
                clean_ai_text, count_s = re.subn(r'[\#\*\_\s]*\[\s*SEWUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                clean_ai_text, count_w = re.subn(r'[\#\*\_\s]*\[\s*WOLWUN_TABLE_HERE\s*\][\#\*\_\s]*', wolwun_target, clean_ai_text, flags=re.IGNORECASE)

                clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*CHAM_DAEOUN_TABLE_HERE\s*\][\#\*\_\s]*', daeoun_target, clean_ai_text, flags=re.IGNORECASE)
                clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*CHAM_SEEUN_TABLE_HERE\s*\][\#\*\_\s]*', sewun_target, clean_ai_text, flags=re.IGNORECASE)
                clean_ai_text = re.sub(r'[\#\*\_\s]*\[\s*CHAM_WOLEUN_TABLE_HERE\s*\][\#\*\_\s]*', wolwun_target, clean_ai_text, flags=re.IGNORECASE)

                if count_d == 0 and "table" not in clean_ai_text.lower():
                    clean_ai_text = clean_ai_text + f"<br><br><span style='color:red; font-weight:bold;'>⚠️ (AI 표 마커 누락으로 비상 출력된 운의 흐름표)</span><br>{un_html_clean}{se_html_clean}{wol_html_clean}"

                full_content_clean = f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000;'>{clean_ai_text}<br><br>{closing_html}</div>"

                # [수정 완료] 본문 내 중복 인쇄 버튼 삭제 및 깔끔한 레이아웃 결합
                report_1_full_html = f"{cover_html}<div class='report-page'><div class='vip-inset-frame' style='border-color:#1A237E; box-sizing: border-box; padding: 20px;'><h1 style='text-align:center;'>🎯[초연 시공명리 사주풀이]</h1>{table_html}{master_bar_html}<div style='margin-top:20px;'>{full_content_clean}</div></div></div>"
                
                # [화면 출력] 1단계가 무조건 화면에 렌더링 됩니다.
                st.markdown(report_1_full_html, unsafe_allow_html=True)
                
            except Exception as e: 
                st.error(f"1단계 사주풀이 AI 연산 오류: {e}")
                st.stop() # 1단계에서 꼬이면 다음 단계로 진행하지 않도록 완벽 차단

            # ==================================================================
            # 🚀 [2단계] 타 감명서 비교분석 (선택적)
            # ==================================================================
            if u_product == "타 감명서":
                try:
                    st.info("▶ [타 감명서] 원본 출력 및 상세 비교 분석 중...") 
                    comp_text = other_reading_text

                    report_2_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#555;'><h2 style='text-align:center; color:#555; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; margin-bottom:20px;'>📜 타 감명서 원문</h2><div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #111;'>{comp_text.replace(chr(10), '<br>')}</div></div></div>"
                    st.markdown(report_2_html, unsafe_allow_html=True)
                    
                    # 💡 [NameError 방어] 사주 정보 변수 자동 탐색
                    saju_info_str = locals().get('saju_text') or locals().get('ganji_str') or locals().get('saju_info') or locals().get('user_saju') or st.session_state.get('saju_info', "현재 입력된 내담자 명조")
                        
                    comp_prompt = f"""
    당신은 명리심리상담사 '초연 박사'를 보조하는 수석 분석관입니다.
    아래 [사주 팩트]를 절대 기준으로 삼고, [1. 초연 사주풀이]와 [2. 타 감명서]의 내용을 인사말이나 서론 없이, 곧바로 대조 포맷 규칙에 의거하여 분석하십시오.

    🚨 [절대 사주 팩트 - 환각 방지용 족쇄]
    - 내담자 명조 팩트: {saju_info_str}
    - 본 명조와 무관한 다른 일간이나 존재하지 않는 신살, 합형충파해를 언급할 경우 치명적인 시스템 오류로 간주합니다.

    🚨 [출력 및 서식 절대 규칙]
    1. "네, 분석을 시작합니다" 등의 서론 멘트를 철저히 금지합니다. 첫 글자는 무조건 제목 태그로 시작해야 합니다.
    2. 차이점 기술 시 반드시 <b>&lt;초연&gt;</b> 및 <b>&lt;타 감명&gt;</b> 마커를 문단 앞에 기입하고 공통점도 빠짐없이 발굴하십시오.
    3. 통변 근거 제시 시 반드시 명리적 근거(십성, 합형충파해, 신살 등)를 기반으로 논증하십시오.
    4. (유연한 목차 구성) 타 감명서의 목차와 논리 흐름을 면밀히 분석하여, 해당 감명서가 다루고 있는 핵심 주제들에 맞추어 AI가 유연하게 비교 항목(목차)을 도출하십시오.

    5. 🚨 [초연 시공명리 분석 주도권 및 4대 개선청구서 지침 - 엄격 준수]
       - 격국 판별 규칙: <초연>의 '1) 타고난 삶의 무대와 기본 성향' 분석은 첫 문장의 유려한 흐름에 전혀 영향을 주지 않으면서도, 내부적으로 철저한 전통명리학적 격국 판별을 마친 상태입니다. (※ 전통 규칙: 월지의 지장간이 천간에 투출한 십성을 격국으로 정하되, 투출하지 못했을 때는 월지 자체의 본기 십성을 격국으로 판별함). AI는 이 원칙을 인지하고 <초연>의 내재된 격국적 깊이를 <타 감명>의 단순한 격국 선언과 날카롭게 비교·평가해야 합니다.
       - 자의형상 및 7궁위 분석 규칙: <초연>의 10천간 자의형상 해석은 도입부(첫 문장)의 강렬한 시공간적 이미지를 구축하는 것으로 역할을 다하며 충분히 만족합니다. 그 이후의 분석은 일간을 제외한 '나머지 7궁위'의 전통명리학적 십성과 12운성(運星)의 배치를 기반으로 하여, 내담자의 육친적 관계, 심리적 심층 구조, 사회적 확장성을 일반 감명서보다 훨씬 심도 있게 풀어내고 있음을 논리적으로 입증하십시오.
       
       - 🚨 [총평 및 향후 개선점 작성 시 필수 반영할 4대 고차원 연산 규칙]:
         마지막 '총평 및 향후 개선점' 목차에서는 상호보완이라는 물타기를 전면 금지하고 양측의 장단점을 혹독하게 지적하되, <초연>의 프롬프트 엔진을 미래지향적으로 업그레이드하기 위해 아래의 4가지 고차원 명리 분석 요소를 **반드시 명확한 '개선 청구서 목록' 형태로 도출**하십시오.
         
         * 1) [형살 삼형살의 물상대체 연산]: 원국의 형살이 세운/대운에서 특정 글자를 만나 삼형살(예: 寅巳申)을 가동하는 구체적인 위험 타이밍을 매섭게 경고하고, 이에 대응하는 '건강검진, 법규 준수, 구설 방지' 등 실천적 물상대체(物象代替) 솔루션을 매핑하는 로직의 보완점을 지적할 것.
         * 2) [초구체적 액션 플랜 개운법]: 원론적인 조언을 넘어, 부족한 희신 오행을 보강할 즉각적인 액션 플랜(예: 인테리어 소품의 색상/메탈 등 소재 지정, 구체적인 자격증/공부 분야 제안, 정확한 여행 길방(方向) 등)을 목록화하는 기능의 필요성을 청구할 것.
         * 3) [무관 사주의 대운 득관(得官) 현상]: 원국에 관성이 없는 사주가 대운에서 강력한 관성을 맞이할 때 일어나는 '인생의 새로운 무대 개막'이라는 극적인 패러다임 변화를 포착하고, 사회적 명예/직책의 성취와 그 이면에 따르는 심리적 중압감/스트레스를 입체적으로 쪼개어 분석하는 로직을 청구할 것.
         * 4) [붕충개고(崩衝開庫)의 양면성 분석]: 형충으로 인해 재물 창고(진술축미)가 열리는 개고 운을 다룰 때, 자산 증식의 기회만 다루지 말고 '가족 간 재산 분쟁, 건강 악화에 따른 목돈 지출, 투자 리스크' 등 이면에 도사린 치명적인 리스크를 동시에 경고하는 통합 위기관리 분석의 보완을 요구할 것.

    [목차 HTML 서식 정의]
    각 비교 항목의 제목을 출력할 때는 반드시 아래의 HTML 태그 구조를 그대로 복사하여 사용하되, 숫자와 항목 이름만 상황에 맞게 변경하십시오.
    <h3 style='color:#1A237E; font-size: 22px; font-weight: 900; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 25px; margin-bottom: 8px; display:block;'>1. [도출된 비교 항목 이름]</h3>
    
    가장 마지막 결론인 총평을 작성할 때만 아래의 붉은색 태그를 사용하십시오.
    <h3 style='color:#D50000; font-size: 22px; font-weight: 900; border-bottom: 2px solid #D50000; padding-bottom: 5px; margin-top: 35px; margin-bottom: 8px; display:block;'>[마지막 번호]. 총평 및 향후 개선점</h3>

    =========================================
    [1. 초연 사주풀이 원문]
    {full_content_clean}  

    [2. 타 감명서 원문]
    {comp_text}
    =========================================
    """
                    c_res = call_claude_api(comp_prompt, max_tokens=10000)
                    report_3_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#D50000;'><h1 style='text-align:center; color:#D50000; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; margin-bottom:25px;'>⚖️ 1:1 상세비교 리포트</h1><div style='margin-top:20px;'>{c_res}</div></div></div>"
                    st.markdown(report_3_html, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"2단계 비교 분석 장애: {e}")

# ==================================================================
            # [최종 복원] 출산택일 최적 길일 산출 엔진 (살성 필터링 및 합궁 기간 연산)
            # ==================================================================
            def get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, forbidden_list):
                import datetime
                from korean_lunar_calendar import KoreanLunarCalendar
                
                if not start_date or not end_date: return []
                
                def get_ji_relation_info(j1, j2):
                    if not j1 or not j2 or j1 == "?" or j2 == "?": return 0, ""
                    s = {j1, j2}
                    if s in [{'子','丑'}, {'寅','亥'}, {'卯','戌'}, {'辰','酉'}, {'巳','申'}, {'午','未'}]: return 5, "육합(六合)을 이루어 유대감이 매우 깊고"
                    if s in [{'寅','卯'}, {'卯','辰'}, {'寅','辰'}, {'巳','午'}, {'午','未'}, {'巳','未'}, {'申','酉'}, {'酉','戌'}, {'申','戌'}, {'亥','子'}, {'子','丑'}, {'亥','丑'}]: return 3, "방합(方合)을 이루어 끈끈한 기운을 나누며"
                    if s in [{'申','子'}, {'子','辰'}, {'申','辰'}, {'寅','午'}, {'午','戌'}, {'寅','戌'}, {'亥','卯'}, {'卯','未'}, {'亥','未'}, {'巳','酉'}, {'酉','丑'}, {'巳','丑'}]: return 3, "삼합(三合)을 이루어 결속력이 강하고"
                    if s in [{'子','午'}, {'丑','未'}, {'寅','申'}, {'卯','酉'}, {'辰','戌'}, {'巳','亥'}]: return -5, "충(沖)이 발생하여 탈락"
                    if s in [{'子','未'}, {'丑','午'}, {'寅','酉'}, {'卯','申'}, {'辰','亥'}, {'巳','戌'}]: return -3, "원진(怨嗔)이 발생하여 탈락"
                    if s in [{'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}, {'子','卯'}]: return -4, "형(刑)이 발생하여 탈락"
                    return 0, "무난한 조화를 이루며"
        
                results = []
                curr_d = start_date
                
                while curr_d <= end_date:
                    klc = KoreanLunarCalendar()
                    klc.setSolarDate(curr_d.year, curr_d.month, curr_d.day)
                    gapja = klc.getChineseGapJaString().split()
                    
                    if len(gapja) >= 3:
                        b_year = gapja[0][:2]
                        b_month = gapja[1][:2]
                        b_day = gapja[2][:2]
                        ilju = gapja[2]
                        
                        # 🚨 박사님 지정 흉일 원천 차단
                        if ilju not in forbidden_list:
                            b_j = b_day[1]
                            score = 80
                            reason_parts = []
                            is_bad = False
                            
                            if f_jjis and len(f_jjis) >= 4:
                                s, txt = get_ji_relation_info(b_j, f_jjis[1])
                                if s < 0: is_bad = True
                                else: 
                                    score += s * 2
                                    if s > 0: reason_parts.append(f"엄마({f_jjis[1]})와 {txt}")
                                    
                            if m_jjis and len(m_jjis) >= 4:
                                s, txt = get_ji_relation_info(b_j, m_jjis[1])
                                if s < 0: is_bad = True
                                else: 
                                    score += s * 2
                                    if s > 0: reason_parts.append(f"아빠({m_jjis[1]})와 {txt}")
                            
                            if not is_bad and score >= 80:
                                # 💡 출생일에서 280일 역산 후 ±4일의 합궁 권장 기간 설정
                                conception_center = curr_d - datetime.timedelta(days=280)
                                c_start = conception_center - datetime.timedelta(days=4)
                                c_end = conception_center + datetime.timedelta(days=4)
                                
                                reason_str = " ".join(reason_parts)
                                if not reason_str: reason_str = "부모님과 오행의 흐름이 원만하여 가족이 화목하게 지낼 수 있는"
                                reason_str += " 평안하고 좋은 길일입니다."
                                
                                results.append({
                                    'birth_date': curr_d.strftime("%Y년 %m월 %d일"), 
                                    'conception_date': f"{c_start.strftime('%Y년 %m월 %d일')} ~ {c_end.strftime('%m월 %d일')}",
                                    'bazi': f"{b_year}년 {b_month}월 {b_day}일", 
                                    'score': score,
                                    'reason': f"신생아의 일지({b_j})가 {reason_str}"
                                })
                    
                    curr_d += datetime.timedelta(days=1)
                    
                results.sort(key=lambda x: x['score'], reverse=True)
                return results[:5]

            # ==================================================================
            # 💕 [3단계] 궁합 풀이 (Ver 35.1 - 완벽 레이아웃/에세이 복원 판본)
            # ==================================================================
            if u_product == "궁합":
                try:
                    # 3-1. 상대방(여명 또는 파트너) 정밀 역산 연산 시스템 가동
                    p_klc = KoreanLunarCalendar()
                    if p_cal == "양력": p_klc.setSolarDate(p_y, p_m, p_d)
                    elif p_cal == "음력(평달)": p_klc.setLunarDate(p_y, p_m, p_d, False)
                    else: p_klc.setLunarDate(p_y, p_m, p_d, True)
                    
                    p_is_leap = getattr(p_klc, 'isIntercalary', False)
                    p_leap_str = "윤달" if p_is_leap else "평달"
                    p_sol_str = f"{p_klc.solarYear}년 {p_klc.solarMonth:02d}월 {p_klc.solarDay:02d}일"
                    p_lun_str = f"{p_klc.lunarYear}년 {p_klc.lunarMonth:02d}월 {p_klc.lunarDay:02d}일 ({p_leap_str})"
                    p_age = curr_y - p_y + 1
                    
                    p_base_dt = dt_mod.datetime(p_y, p_m, p_d, 12, 0)
                    p_gj = p_klc.getChineseGapJaString().split()
                    p_ys, p_yb, p_ms, p_mb, p_ds, p_db = p_gj[0][0], p_gj[0][1], p_gj[1][0], p_gj[1][1], p_gj[2][0], p_gj[2][1]
                    p_hs, p_hb = get_time_ganji(p_ds, p_t, p_base_dt)
                    partner_bazi = [f"{p_hs}{p_hb}", f"{p_ds}{p_db}", f"{p_ms}{p_mb}", f"{p_ys}{p_yb}"]

                    # 3-2. 남명/여명 데이터 대칭 배정 (모든 변수 완벽 맵핑)
                    if u_gender == "남성":
                        m_name, m_sol, m_lun, m_time, m_age = u_name, sol_str, lun_str, time_str, u_age
                        m_gans, m_jjis = gans, jjis
                        m_ys, m_yb, m_ms, m_mb, m_ds, m_db, m_hs, m_hb = ys, yb, ms, mb, ds, db, hs, hb
                        m_calc_d, m_order = calc_d, order
                        
                        f_name, f_sol, f_lun, f_time, f_age = p_name, p_sol_str, p_lun_str, f" {p_t.split('(')[0].strip()} ({p_hb})시" if p_t != "시간 모름" else "", p_age
                        f_gans, f_jjis = [p_hs, p_ds, p_ms, p_ys], [p_hb, p_db, p_mb, p_yb]
                        f_ys, f_yb, f_ms, f_mb, f_ds, f_db, f_hs, f_hb = p_ys, p_yb, p_ms, p_mb, p_ds, p_db, p_hs, p_hb
                        p_utc_dt = p_base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=get_total_time_adjustment(p_base_dt))
                        p_order = 1 if (GAN.index(p_ys)%2==0) == (p_gender=='남성') else -1
                        f_calc_d, f_order = get_daeun_su_accurate(p_utc_dt, p_order), p_order
                        
                        male_data_pack, female_data_pack = applicant_bazi, partner_bazi
                    else:
                        m_name, m_sol, m_lun, m_time, m_age = p_name, p_sol_str, p_lun_str, f" {p_t.split('(')[0].strip()} ({p_hb})시" if p_t != "시간 모름" else "", p_age
                        m_gans, m_jjis = [p_hs, p_ds, p_ms, p_ys], [p_hb, p_db, p_mb, p_yb]
                        m_ys, m_yb, m_ms, m_mb, m_ds, m_db, m_hs, m_hb = p_ys, p_yb, p_ms, p_mb, p_ds, p_db, p_hs, p_hb
                        p_utc_dt = p_base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=get_total_time_adjustment(p_base_dt))
                        p_order = 1 if (GAN.index(p_ys)%2==0) == (p_gender=='남성') else -1
                        m_calc_d, m_order = get_daeun_su_accurate(p_utc_dt, p_order), p_order
                        
                        f_name, f_sol, f_lun, f_time, f_age = u_name, sol_str, lun_str, time_str, u_age
                        f_gans, f_jjis = gans, jjis
                        f_ys, f_yb, f_ms, f_mb, f_ds, f_db, f_hs, f_hb = ys, yb, ms, mb, ds, db, hs, hb
                        f_calc_d, f_order = calc_d, order
                        
                        male_data_pack, female_data_pack = partner_bazi, applicant_bazi

                    # 3-3. 올해 간지 공통 변수
                    curr_j = JI[((curr_y - 1984) % 60) % 12]

                    def get_counts(gans, jjis):
                        c = {"목":0,"화":0,"토":0,"금":0,"수":0}
                        for x in gans + jjis:
                            if x != "?": c[get_color(x)] += 1
                        return c

                    m_cnt, f_cnt = get_counts(m_gans, m_jjis), get_counts(f_gans, f_jjis)

                    # 3-4. 사주표 생성 함수 (인적사항 및 테이블 양식)
                    def build_bazi_table(gender_icon, name, gender_str, marital_str, age, sol, lun, time, gans, jjis, ds, yb, counts, guiin, gong, samjae, color):
                        ji_rel_rows = ""
                        for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                            b_bot = "1px solid #444 !important" if l_idx == 3 else "none !important"
                        
                            # '-' 기호가 나올 경우 화면에 빈칸으로 처리하여 깔끔하게 표시
                            cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:none !important; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else (get_ji_rel_set(jjis[r_idx], jjis[ci]) if get_ji_rel_set(jjis[r_idx], jjis[ci]) != '-' else ''))}</td>" for ci in range(4)])
                            lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important;'>합충형파해</td>" if l_idx==0 else ""
                        
                            # ✅ 해결: 루프 안에서 이 한 줄이 반드시 들어가야 화면에 표출됩니다.
                            ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

                        info_str = f"<div style='text-align:center; margin-bottom:15px; font-family:\"Malgun Gothic\", sans-serif;'><span style='font-size:18px; font-weight:900; color:{color};'>{gender_icon} {name}님 ({gender_str}, {marital_str}, {age}세)</span><br><span style='font-size:14px; font-weight:900; color:#222;'>[양력] {sol} | [음력] {lun}{time}</span></div>"
                        
                        return f"""{info_str}
<table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
<tr class='top-header-cell'>
<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>구분</td>
<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>시주</td>
<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>일주</td>
<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>월주</td>
<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>년주</td>
</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(ds,gans[0])}</td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(ds,gans[2])}</td><td style='border:1px solid #444;'>{get_ss(ds,gans[3])}</td></tr>
<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>천간</td>{td(gans[0])}{td(gans[1])}{td(gans[2])}{td(gans[3])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>지지</td>{td(jjis[0])}{td(jjis[1])}{td(jjis[2])}{td(jjis[3])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(ds,jjis[0])}</td><td style='border:1px solid #444;'>{get_ss(ds,jjis[1])}</td><td style='border:1px solid #444;'>{get_ss(ds,jjis[2])}</td><td style='border:1px solid #444;'>{get_ss(ds,jjis[3])}</td></tr>
<tr><td class='header-cell-main' style='border:1px solid #444; padding:0; font-size:15px !important; white-space:nowrap;'>지장간</td>{"".join([f"<td style='border:1px solid #444; padding:0;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
{ji_rel_rows}
<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>십이운성</td>{"".join([f"<td style='border:1px solid #444; color:#0D47A1;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>십이신살</td>{"".join([f"<td style='border:1px solid #444; color:#C62828;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
</table>
<div style='border:2px solid #3E2723; margin-top:10px; margin-bottom:20px; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px;'><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin}</div><div>🎯 공망: [일] {gong}</div><div>🌪️ 삼재: {samjae}</div></div>
"""

                    m_marital = u_marital if u_gender == "남성" else p_marital
                    f_marital = p_marital if u_gender == "남성" else u_marital
                    
                    m_tbl = build_bazi_table("♂️", m_name, "남성", m_marital, m_age, m_sol, m_lun, m_time, m_gans, m_jjis, m_ds, m_yb, m_cnt, guiin_map.get(m_ds, '-'), calculate_gongmang(m_ds, m_db), get_samjae(m_yb, curr_j), "#1A237E")
                    f_tbl = build_bazi_table("♀️", f_name, "여성", f_marital, f_age, f_sol, f_lun, f_time, f_gans, f_jjis, f_ds, f_yb, f_cnt, guiin_map.get(f_ds, '-'), calculate_gongmang(f_ds, f_db), get_samjae(f_yb, curr_j), "#1A237E")

                    # 3-5. 궁합 페이지용 상하 대운표 생성기 (3페이지 전용)
                    def build_daewun_html(name, ds, ms, mb, yb, calc_d, order, age, color):
                        d_str = "순행" if order == 1 else "역행"
                        html = f"<div style='margin-bottom:10px;'><div style='font-size:15px; font-weight:900; color:{color}; margin-bottom:5px;'>[ {name}님 대운 흐름표 (대운수: {calc_d}), {d_str} ]</div>"
                        html += f"<div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white;'>"
                        for i in range(10):
                            val = i*10 + calc_d
                            tc = GAN[(GAN.index(ms)+(i+1)*order)%10]
                            tj = JI[(JI.index(mb)+(i+1)*order)%12]
                            bg = "#FFF9C4" if val <= age < val+10 else "transparent"
                            brd = "1px solid #ccc" if i != 9 else "none"
                            # 최상단 바탕색을 {color}에서 #3E2723(진한 갈색)으로 변경 및 하단 줄눈 추가
                            html += f"<div style='flex:1; border-left:{brd}; text-align:center; padding-bottom:3px; background-color:{bg};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:11px; border-bottom:1px solid #ccc;'>{val}세</div><div style='padding:2px; font-size:11px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:15px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:15px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:11px;'>{get_ss(ds,tj)}</div><div style='font-size:10px; border-top:1px solid #eee;'>{get_unsung(ds,tj)}</div><div style='font-size:10px; color:#C62828; border-top:1px solid #eee;'>{get_12_shinsal(yb, tj)}</div></div>"
                        return html + "</div></div>"

                    m_page_un_html = build_daewun_html(m_name, m_ds, m_ms, m_mb, m_yb, m_calc_d, m_order, m_age, "#1A237E")
                    f_page_un_html = build_daewun_html(f_name, f_ds, f_ms, f_mb, f_yb, f_calc_d, f_order, f_age, "#1A237E")
                    
                    couple_daewun_tables = f"<div style='margin-bottom: 25px;'>{m_page_un_html}<div style='height:20px;'></div>{f_page_un_html}</div>"

                    # 3-6. AI 에세이 가동 (프롬프트 통제 강화) & 💡 캐싱 시스템 도입
                    current_cache_key = f"gunghap_{u_name}_{curr_y}_{p_name}_{p_age}"

                    if st.session_state.get('gh_cache_key') == current_cache_key:
                        # 💡 [캐시 적중] 이미 분석한 커플이면 AI 재호출 없이 메모리에서 0.1초 만에 불러옵니다.
                        m_ess = st.session_state.get('gh_m_ess', "")
                        f_ess = st.session_state.get('gh_f_ess', "")
                        g_full_content = st.session_state.get('gh_g_full_content', "")
                        m_jjis_for_calc = st.session_state.get('gh_m_jjis')
                        f_jjis_for_calc = st.session_state.get('gh_f_jjis')
                    else:
                        # 💡 [캐시 없음] 최초 실행 시 정상적으로 AI 엔진을 가동합니다.
                        m_w_val = choyeon_db.get("wolryeong", {}).get(m_ms+m_mb, "시공간")
                        m_i_val = choyeon_db.get("ilju", {}).get(m_ds+m_db, "성품")
                        m_golden = f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em;'><b>{m_name}님</b>은 '{m_w_val}'의 시공간에서, '{m_i_val}'의 성품을 지녔습니다.</p>"

                        f_w_val = choyeon_db.get("wolryeong", {}).get(f_ms+f_mb, "시공간")
                        f_i_val = choyeon_db.get("ilju", {}).get(f_ds+f_db, "성품")
                        f_golden = f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em;'><b>{f_name}님</b>은 '{f_w_val}'의 시공간에서, '{f_i_val}'의 성품을 지녔습니다.</p>"
                        
                        gh_engine = UniversalPrintableGunghap(u_name, p_name, applicant_bazi if u_gender=="남성" else partner_bazi, partner_bazi if u_gender=="남성" else applicant_bazi, m_calc_d)
                        gh_engine.run_universal_logic()
                        
                        essay_prompt = f"""[SYSTEM ROLE: CHOYEON SIGONG MASTER]
당신은 명리심리상담사 '초연 박사'입니다.

🚨 [출력 절대 형식 및 내용 생성 규칙 - 매우 중요!]
1. 각 소제목 아래에 절대로 '(축약 에세이)', '(에세이)' 등의 안내 문구를 그대로 복사해서 출력하지 마십시오!
2. 반드시 내담자의 명리적 특징을 분석하여 3~4문장 분량의 **실제 통변 내용(해석)**을 직접 글로 작성해야 합니다.
3. 일반인이 쉽게 이해할 수 있도록 어려운 한자성어나 명리 전문 용어는 최대한 배제하고, 일상적이고 따뜻한 현대적 구어체(~해요, ~합니다)로 풀어서 부드럽게 설명하십시오. (단, 특수 기운 설명 시에는 해당 신살 명칭 사용 가능)
4. 모든 통변 문장은 HTML 태그 <p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'> 로 감싸십시오.

[MALE_START]
<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; margin-top: 15px;'>1. 사주팔자의 요약</h3>
{m_golden}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(이곳에 남성의 명리적 성향을 분석한 실제 에세이를 구어체로 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>
(이곳에 남성의 오행 및 조후 에너지를 분석한 실제 에세이를 구어체로 작성)

<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; margin-top: 35px;'>2. 성격 및 가치관</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
(이곳에 남성의 사회적 표면 성격을 분석한 실제 에세이를 구어체로 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>
(이곳에 남성의 내면과 무의식을 분석한 실제 에세이를 구어체로 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>3) 무의식이 갈망하는 반려자의 상</span>
(일지의 십성과 지장간을 바탕으로 남성의 연애 및 결혼관을 실제 에세이로 구어체로 작성)
[MALE_END]

[FEMALE_START]
<h3 style='color:#D50000; font-size: 22px; font-weight: 900; margin-top: 15px;'>1. 사주팔자의 요약</h3>
{f_golden}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(이곳에 여성의 명리적 성향을 분석한 실제 에세이를 구어체로 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>
(이곳에 여성의 오행 및 조후 에너지를 분석한 실제 에세이를 구어체로 작성)

<h3 style='color:#D50000; font-size: 22px; font-weight: 900; margin-top: 35px;'>2. 성격 및 가치관</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
(이곳에 여성의 사회적 표면 성격을 분석한 실제 에세이를 구어체로 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>
(이곳에 여성의 내면과 무의식을 분석한 실제 에세이를 구어체로 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>3) 무의식이 갈망하는 반려자의 상</span>
(일지의 십성과 지장간을 바탕으로 여성의 연애 및 결혼관을 실제 에세이로 구어체로 작성)
[FEMALE_END]

[GUNGHAP_START]
<h3 style='color: #1B5E20; font-size: 22px; font-weight: 900; margin-top: 10px;'>🍀 두 사람의 운명적 만남에 대하여</h3>
(이곳에 두 사람의 인연 총평을 깊이 있게 통변한 실제 에세이를 구어체로 작성)

<h3 style='color: #1A237E; font-size: 22px; font-weight: 900; margin-top: 35px;'>🌈 커플의 인생 기상도</h3>
[COUPLE_DAEWUN_TABLES_HERE]
(🚨경고: 위 마커는 파이썬 엔진이 대운 흐름표를 꽂아 넣을 절대 성역입니다. 임의로 지우지 마십시오. 마커 바로 아래에 대운 교차점에 따른 상생/보완 에세이를 현대적 구어체로 작성하십시오.)

<h4 style='color: #1A237E; font-size: 18px; font-weight: 900; margin-top: 35px;'>💞 6대 심층 조화도 분석</h4>
<span class='sub-title' style='display: block; font-size: 16px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 내면의 유대감 (속궁합)</span>
(두 사람의 일지를 대조하여 심리적, 육체적 친밀감과 소통의 조화를 구어체로 작성)

<span class='sub-title' style='display: block; font-size: 16px; font-weight: 900; color: #111; margin-top: 20px; margin-bottom: 5px;'>2) 환경 조화 (겉궁합)</span>
(두 사람의 월지를 대조하여 사회적, 가정적 가치관과 현실적 환경의 조화를 구어체로 작성)

<span class='sub-title' style='display: block; font-size: 16px; font-weight: 900; color: #111; margin-top: 20px; margin-bottom: 5px;'>3) 기운 상호보완</span>
(오행과 조후를 바탕으로 서로에게 부족한 기운을 어떻게 채워주는지 구어체로 작성)

<span class='sub-title' style='display: block; font-size: 16px; font-weight: 900; color: #111; margin-top: 20px; margin-bottom: 5px;'>4) 특수 기운</span>
(고란살, 간여지동, 음양차착살 등 특수 신살이 두 사람의 관계와 결혼 생활에 미치는 영향을 분석하여 구어체로 작성)

<span class='sub-title' style='display: block; font-size: 16px; font-weight: 900; color: #111; margin-top: 20px; margin-bottom: 5px;'>5) 커플의 인생 기상도</span>
(서로의 대운 흐름이 어떻게 맞물리며 시너지를 내는지 분석하여 구어체로 작성)

<span class='sub-title' style='display: block; font-size: 16px; font-weight: 900; color: #111; margin-top: 20px; margin-bottom: 5px;'>6) 리스크 방어력</span>
(갈등 발생 시 두 사람이 이를 극복하고 방어할 수 있는 내성 및 개운 처방을 담아 구어체로 작성)
[GUNGHAP_END]
"""
                        res_text = call_claude_api(essay_prompt, max_tokens=12000)
                        ai_clean = "\n".join([line.lstrip() for line in res_text.split("\n")])
                        
                        # 3-7. 강력한 마커 파싱 시스템 (에러 방지)
                        import re
                        m_ess, f_ess, g_ess = "", "", ai_clean
                        
                        m_match = re.search(r'\[MALE_START\](.*?)\[MALE_END\]', ai_clean, re.DOTALL)
                        if m_match: m_ess = m_match.group(1).strip()
                        
                        f_match = re.search(r'\[FEMALE_START\](.*?)\[FEMALE_END\]', ai_clean, re.DOTALL)
                        if f_match: f_ess = f_match.group(1).strip()
                        
                        g_match = re.search(r'\[GUNGHAP_START\](.*?)\[GUNGHAP_END\]', ai_clean, re.DOTALL)
                        if g_match: 
                            g_ess = g_match.group(1).strip()
                        else:
                            g_ess = ai_clean.replace(m_ess, "").replace(f_ess, "").replace("[MALE_START]", "").replace("[MALE_END]", "").replace("[FEMALE_START]", "").replace("[FEMALE_END]", "")
                        
                        # 대운표 마커 조립
                        g_ess = g_ess.replace("[COUPLE_DAEWUN_TABLES_HERE]", couple_daewun_tables)

                        # 3-9. 클로징 멘트 오리지널 복원 및 스코어 바 가시화
                        t_col = "#3498db" if gh_engine.final_score >= 70 else ("#f39c12" if gh_engine.final_score >= 60 else "#e74c3c")
                        bars = "".join([f"<div style='display:flex; align-items:center; margin-bottom:12px;'><div style='width:130px; font-size:13px; font-weight:bold; color:#555;'>{d['label']}</div><div style='flex:1; height:12px; margin:0 10px;'><svg width='100%' height='12'><rect width='100%' height='12' rx='6' ry='6' fill='#eee' /><rect width='{d['pct']}%' height='12' rx='6' ry='6' fill='{d['color']}' /></svg></div><div style='width:35px; font-size:12px; font-weight:bold;'>{d['pct']}%</div></div>" for d in gh_engine.details])
                        
                        closing_original = "<div style='margin-top: 40px; padding-top: 30px; page-break-inside: avoid;'><p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333;'>&nbsp;&nbsp;&nbsp;&nbsp;두 분의 <b style='color:#1A237E;'>'만남'</b>은 결코 우연이 아닌, <b style='color:#1A237E;'>'셀 수 없이 많은 시간 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 바코드지만, <b style='color:#1A237E;'>'궁합(宮合)'</b>은 두 바코드가 만나 그려내는 새로운 <b style='color:#1A237E;'>'하모니(harmonie)'</b>입니다.</p><p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333; margin-top: 10px;'>&nbsp;&nbsp;&nbsp;&nbsp;서로의 다름을 이해하고 채워주는 든든한 <b style='color:#1A237E;'>'동반자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 시공간의 축복이 가득하시길 소망합니다. </p><div style='text-align: right; margin-top: 25px;'><span style='font-weight: 900; font-size: 16px; color: #1A237E; font-family: \"Nanum Myeongjo\", serif;'>- 초연 시공명리 연구소 드림 -</span></div></div>"

                        g_full_content = f"""
                        <div class='choyeon-premium-report'>{g_ess}</div>
                        <h2 style='text-align:center; margin-top:40px; font-size:22px; font-weight:900;'>📊 최종 궁합 점수</h2>
                        <div style='display:flex; justify-content:center; align-items:center; margin:20px 0;'>
                            <div style='width:130px; height:130px; border-radius:50%; background:conic-gradient({t_col} {gh_engine.final_score}%, #eee 0); display:flex; justify-content:center; align-items:center; -webkit-print-color-adjust: exact;'>
                                <div style='width:98px; height:98px; background:#fff; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
                                    <span style='font-size:32px; font-weight:900; color:{t_col};'>{gh_engine.final_score}</span>
                                    <span style='font-size:10px; color:#888; font-weight:bold;'>SCORE</span>
                                </div>
                            </div>
                        </div>
                        <div style='text-align:center; margin-bottom:20px;'><span style='font-size:16px; font-weight:bold; color:#fff; background:{t_col}; padding:8px 32px; border-radius:30px; -webkit-print-color-adjust: exact;'>{gh_engine.grade}</span></div>
                        <div style='max-width:500px; margin:0 auto;'>{bars}</div>
                        {closing_original}
                        """

                        # 🚨 [메모리 영구 박제] 새로고침해도 날아가지 않게 저장
                        m_jjis_for_calc = gh_engine.m_j
                        f_jjis_for_calc = gh_engine.f_j

                        st.session_state['gh_cache_key'] = current_cache_key
                        st.session_state['gh_m_ess'] = m_ess
                        st.session_state['gh_f_ess'] = f_ess
                        st.session_state['gh_g_full_content'] = g_full_content
                        st.session_state['gh_m_jjis'] = m_jjis_for_calc
                        st.session_state['gh_f_jjis'] = f_jjis_for_calc

                    # 3-8. A4 규격 컨테이너 및 대제목 밑줄 래퍼 함수 (항상 선언)
                    def wrap_a4(content, title_color="#1A237E", title="[ 초연 시공명리 사주풀이 ]"):
                        return f"<div class='report-page'><div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'><h1 style='text-align:center; color:{title_color}; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; border-bottom:2px solid {title_color}; padding-bottom:15px; margin-bottom:30px;'>{title}</h1>{content}</div></div>"

                    # 3-10. 화면 최종 렌더링 (1P 남명, 2P 여명, 3P 궁합)
                    st.markdown(wrap_a4(f"{m_tbl}<div class='choyeon-premium-report' style='margin-top:20px;'>{m_ess}</div>", "#1A237E"), unsafe_allow_html=True)
                    st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
                    
                    st.markdown(wrap_a4(f"{f_tbl}<div class='choyeon-premium-report' style='margin-top:20px;'>{f_ess}</div>", "#D50000"), unsafe_allow_html=True)
                    st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
                    
                    st.markdown(wrap_a4(g_full_content, "#1B5E20", "[ 초연 시공명리 궁합풀이 ]"), unsafe_allow_html=True)

                    # ==================================================================
                    # [최종 복원] 출산택일 최적 길일 산출 엔진 (살성 필터링 및 합궁 기간 연산)
                    # ==================================================================
                    def get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, forbidden_list):
                        import datetime
                        from korean_lunar_calendar import KoreanLunarCalendar
                        
                        if not start_date or not end_date: return []
                        
                        def get_ji_relation_info(j1, j2):
                            if not j1 or not j2 or j1 == "?" or j2 == "?": return 0, ""
                            s = {j1, j2}
                            if s in [{'子','丑'}, {'寅','亥'}, {'卯','戌'}, {'辰','酉'}, {'巳','申'}, {'午','未'}]: return 5, "육합(六合)을 이루어 유대감이 매우 깊고"
                            if s in [{'寅','卯'}, {'卯','辰'}, {'寅','辰'}, {'巳','午'}, {'午','未'}, {'巳','未'}, {'申','酉'}, {'酉','戌'}, {'申','戌'}, {'亥','子'}, {'子','丑'}, {'亥','丑'}]: return 3, "방합(方合)을 이루어 끈끈한 기운을 나누며"
                            if s in [{'申','子'}, {'子','辰'}, {'申','辰'}, {'寅','午'}, {'午','戌'}, {'寅','戌'}, {'亥','卯'}, {'卯','未'}, {'亥','未'}, {'巳','酉'}, {'酉','丑'}, {'巳','丑'}]: return 3, "삼합(三合)을 이루어 결속력이 강하고"
                            if s in [{'子','午'}, {'丑','未'}, {'寅','申'}, {'卯','酉'}, {'辰','戌'}, {'巳','亥'}]: return -5, "충(沖)이 발생하여 탈락"
                            if s in [{'子','未'}, {'丑','午'}, {'寅','酉'}, {'卯','申'}, {'辰','亥'}, {'巳','戌'}]: return -3, "원진(怨嗔)이 발생하여 탈락"
                            if s in [{'寅','巳'}, {'巳','申'}, {'寅','申'}, {'丑','戌'}, {'戌','未'}, {'丑','未'}, {'子','卯'}]: return -4, "형(刑)이 발생하여 탈락"
                            return 0, "무난한 조화를 이루며"
        
                        results = []
                        curr_d = start_date
                        
                        while curr_d <= end_date:
                            klc = KoreanLunarCalendar()
                            klc.setSolarDate(curr_d.year, curr_d.month, curr_d.day)
                            gapja = klc.getChineseGapJaString().split()
                            
                            if len(gapja) >= 3:
                                b_year = gapja[0][:2]
                                b_month = gapja[1][:2]
                                b_day = gapja[2][:2]
                                ilju = gapja[2]
                                
                                # 🚨 박사님 지정 흉일 원천 차단
                                if ilju not in forbidden_list:
                                    b_j = b_day[1]
                                    score = 80
                                    reason_parts = []
                                    is_bad = False
                                    
                                    if f_jjis and len(f_jjis) >= 4:
                                        s, txt = get_ji_relation_info(b_j, f_jjis[1])
                                        if s < 0: is_bad = True
                                        else: 
                                            score += s * 2
                                            if s > 0: reason_parts.append(f"엄마({f_jjis[1]})와 {txt}")
                                            
                                    if m_jjis and len(m_jjis) >= 4:
                                        s, txt = get_ji_relation_info(b_j, m_jjis[1])
                                        if s < 0: is_bad = True
                                        else: 
                                            score += s * 2
                                            if s > 0: reason_parts.append(f"아빠({m_jjis[1]})와 {txt}")
                                    
                                    if not is_bad and score >= 80:
                                        # 💡 출생일에서 280일 역산 후 ±4일의 합궁 권장 기간 설정
                                        conception_center = curr_d - datetime.timedelta(days=280)
                                        c_start = conception_center - datetime.timedelta(days=4)
                                        c_end = conception_center + datetime.timedelta(days=4)
                                        
                                        reason_str = " ".join(reason_parts)
                                        if not reason_str: reason_str = "부모님과 오행의 흐름이 원만하여 가족이 화목하게 지낼 수 있는"
                                        reason_str += " 평안하고 좋은 길일입니다."
                                        
                                        results.append({
                                            'birth_date': curr_d.strftime("%Y년 %m월 %d일"), 
                                            'conception_date': f"{c_start.strftime('%Y년 %m월 %d일')} ~ {c_end.strftime('%m월 %d일')}",
                                            'bazi': f"{b_year}년 {b_month}월 {b_day}일", 
                                            'score': score,
                                            'reason': f"신생아의 일지({b_j})가 {reason_str}"
                                        })
                            
                            curr_d += datetime.timedelta(days=1)
                            
                        results.sort(key=lambda x: x['score'], reverse=True)
                        return results[:5]
                    
                    # =====================================================================
                    # [긴급 복원 완료] 4단계: 출산택일 리포트 파이프라인 접합 (최종 디자인)
                    # =====================================================================
                    if run_delivery_calc:  
                        st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
                        
                        with st.spinner("⏳ 👶 최적의 출생일 탐색 및 합궁일 역산 분석 중..."):
                            
                            # 🚨 박사님 금기 리스트 (백호, 괴강, 양인, 비인살 대거 추가)
                            FORBIDDEN_LIST = [
                                '병오', '임자', '계해', '신유', '경신', # 기존 흉살
                                '갑진', '을미', '병술', '정축', '무진', '임술', '계축', # 백호대살
                                '경진', '경술', '임진', '무술', # 괴강살 (중복 제외)
                                '무오', # 양인살 (중복 제외)
                                '병자', '무자', '기축', '임오', '계미' # 비인살 (중복 제외)
                            ]
                            
                            delivery_days = get_optimized_delivery_days(
                                start_date, 
                                end_date, 
                                m_jjis_for_calc, f_jjis_for_calc, FORBIDDEN_LIST
                            )
                            
                            del_content = "<h2 style='text-align:center; color:#4A148C; font-weight:900;'>👶 새 생명 마중 길일 추천</h2>"
                            del_content += "<p style='text-align:center;'>목표 출생일에 맞춘 최적의 합궁일(임신 계획 기간) 안내입니다.</p>"
                            
                            if delivery_days:
                                for i, day_info in enumerate(delivery_days):
                                    bg_color = '#F8F9FA' if i % 2 == 0 else '#FFFFFF'
                                    del_content += f"<div style='padding:15px; border-bottom:1px solid #ddd; background-color:{bg_color};'>"
                                    del_content += f"<div style='margin-bottom:8px;'>🎯 <b style='font-size:16px; color:#1B5E20;'>[출산 목표일] {day_info['birth_date']}</b> 👉 💞 <b style='font-size:16px; color:#D50000;'>[합궁 권장 기간] {day_info['conception_date']}</b> (합 점수: <span style='font-weight:900;'>{day_info['score']}점</span>)</div>"
                                    del_content += f"<div style='margin-bottom:5px; margin-left: 28px;'><span style='color:#1A237E; font-weight:bold;'>👶 신생아 사주(3주): {day_info['bazi']}</span></div>"
                                    del_content += f"<div style='margin-left: 28px; font-size:14px; color:#444; line-height:1.5;'><b>💡 초연 박사의 택일 사유:</b> {day_info['reason']}</div>"
                                    del_content += f"</div>"
                            else:
                                del_content += "<div style='color:red; text-align:center; font-weight:bold; padding:20px;'>해당 기간 내에 추천할 완벽한 길일이 없습니다. 살성과 충/원진을 피하기 위해 탐색 기간을 조금 더 넓혀주세요.</div>"
                            
                            # 💡 본문과 이질감 없는 안내 가이드 및 초연 박사님 낙인 추가
                            del_content += "<br><hr style='opacity:0.3;'>"
                            del_content += "<div style='background-color:#F8F9FA; padding:20px; border-radius:8px; margin-top:15px; border: 1px solid #E0E0E0;'>"
                            del_content += "<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333; margin:0; text-align: justify;'>"
                            del_content += "<b style='color:#4A148C;'>💡 부부를 위한 임신 계획 가이드:</b><br>"
                            del_content += "위의 출산 길일은 아이의 사주 기운을 우선으로 선정한 것입니다. "
                            del_content += "의학적 평균 임신 기간(약 280일)을 고려할 때, 합궁 시기는 출산 예정일로부터 약 9개월 10일(40주, 280일) 전후가 됩니다. "
                            del_content += "부인분의 생리 주기와 배란일을 면밀히 고려하시어, 부부께서 상의하에 가장 건강한 시기를 계획하시길 바랍니다."
                            del_content += "</p></div>"
                            
                            del_content += "<div style='text-align: right; margin-top: 30px; page-break-inside: avoid;'><span style='font-weight: 900; font-size: 16px; color: #4A148C; font-family: \"Nanum Myeongjo\", serif;'>- 초연 시공명리 연구소 -</span></div>"
                            
                        st.markdown(wrap_a4(del_content, "#4A148C", "[ 초연 시공명리 출산택일 ]"), unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"3단계 궁합 종합 분석 가동 장애: {e}")
