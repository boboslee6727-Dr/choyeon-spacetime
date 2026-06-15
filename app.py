import streamlit as st
import pandas as pd
import json
import os
import math
import calendar
import time  
import datetime as dt_mod
from datetime import datetime
from korean_lunar_calendar import KoreanLunarCalendar
import ephem
from google import genai
import pytz
import streamlit.components.v1 as components
import re

# ==============================================================================
# 🎯 [버전 컨트롤 타워]
# ==============================================================================
APP_VERSION = "Ver 48.0 (Master AI Optimized)"

# ==============================================================================
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS
# ==============================================================================
st.set_page_config(page_title=f"초연 시공명리 {APP_VERSION}", layout="wide")

st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");
    
    body, .stApp { background-color: #FFF8E1; }
    
    .report-page { width: 210mm; max-width: 100%; margin: 30px auto; background-color: #FFFFFF !important; padding: 15mm 10mm; box-shadow: 0 0 20px rgba(0,0,0,0.15); border-radius: 20px; box-sizing: border-box; }
    .report-page, .report-page * { font-family: 'Noto Serif KR', serif !important; color: #000000; }
    
    .vip-inset-frame { border: 2px solid #1A237E; border-radius: 15px; padding: 20px; background: transparent; box-sizing: border-box; width: 100%; overflow: hidden; word-break: keep-all; -webkit-box-decoration-break: clone; box-decoration-break: clone; }

    .cover-page .title-gothic { font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif !important; color: #0054FF !important; font-weight: 900 !important; }
    .cover-page .ver-gothic { font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif !important; color: #555555 !important; font-weight: 900 !important; }

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
    .color-무 { background-color: white !important; }
    
    .content-box-loose { line-height: 1.8; font-size: 15px; color: #111; text-align: justify; word-break: keep-all; font-family: 'Noto Serif KR', 'Nanum Myeongjo', serif !important; padding: 0 !important; }
    .content-box-loose .sub-title { text-indent: 0px !important; margin-top: 25px !important; margin-bottom: 10px !important; font-weight: 900 !important; display: block; color: #111 !important; }
    
    div[data-testid="stSidebar"] div.stButton > button:first-child,
    div.stButton > button[kind="primary"] { background-color: #D50000 !important; color: white !important; border: none !important; height: 45px !important; }
    
    div[data-testid="stSidebar"] div.stButton > button:first-child p,
    div.stButton > button[kind="primary"] p { font-weight: 900 !important; font-size: 15px !important; font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif !important; color: white !important; margin: 0 !important; }

    div[data-testid="stSidebar"] .navy-btn button { background-color: #1A237E !important; color: white !important; border: none !important; font-weight: 900 !important; height: 45px !important; }   
    
    @media print { 
        @page { size: A4 portrait; margin: 10mm; }
        .stSidebar, button, iframe, .print-hide, header { display: none !important; }
        body, .stApp { background-color: white !important; }
        
        .block-container, div[data-testid="stAppViewBlockContainer"] { padding-top: 0 !important; padding-bottom: 0 !important; margin-top: 0 !important; margin-bottom: 0 !important; }
        div[data-testid="stVerticalBlock"] { gap: 0 !important; }
        .element-container, .stMarkdown { margin-bottom: 0 !important; }
        
        .report-page { box-shadow: none; margin: 0 auto; padding: 0; page-break-after: always; border-radius: 0; width: 100%; max-width: 100%; }
        .report-page:last-of-type { page-break-after: auto; }
        .page-break-before { page-break-before: always; }
        .vip-inset-frame { border: 2px solid #000; border-radius: 20px; padding: 15px; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 0.5 [완전 무결점 하드코딩 DB]
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
        "癸酉": "봄비(癸)가 사찰의 종(酉)을 적시며 결실을 거두는 완연한 가을",
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

idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]

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
    _gemini_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as _api_e:
    st.error(f"🚨 Gemini API 키 오류: {_api_e}")
    _gemini_client = None

@st.cache_data(show_spinner=False, ttl=60) #ttl=600*24 시간 감명서 유효
def get_ai_response(prompt_text, model_name='gemini-2.5-flash'):
    if '1.5' in model_name:
        model_name = 'gemini-2.5-flash'
        
    if _gemini_client is None:
        return "<div style='color:red;'>🚨 Gemini 모델이 초기화되지 않았습니다.</div>"
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = _gemini_client.models.generate_content(model=model_name, contents=prompt_text)
            return response.text.strip()
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1); continue
            return f"<div style='color:red;'>🚨 AI 서버 장애: {e}</div>"

def call_gemini_api(prompt_text, max_tokens=8000):
    return get_ai_response(prompt_text, model_name='gemini-2.5-flash')

def call_light_api(prompt_text):
    return get_ai_response(prompt_text, model_name='gemini-2.5-flash')

JIJANGGAN = {'子': ['壬', '-', '癸'], '丑': ['癸', '辛', '己'], '寅': ['戊', '丙', '甲'], '卯': ['甲', '-', '乙'], '辰': ['乙', '癸', '戊'], '巳': ['戊', '庚', '丙'], '午': ['丙', '己', '丁'], '未': ['丁', '乙', '己'], '申': ['戊', '壬', '庚'], '酉': ['庚', '-', '辛'], '戌': ['辛', '丁', '戊'], '亥': ['戊', '甲', '壬'] }

def get_color(c):
    if c in "甲乙寅卯": return "목"
    if c in "丙丁巳午": return "화"
    if c in "戊己辰戌丑未": return "토"
    if c in "庚辛申酉": return "금"
    if c in "壬癸亥子": return "수"
    return "무"

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
    if ilgan in ["?"," ","-"] or ilji in ["?"," ","-"]: return "-"
    try:
        base = (list(JI).index(ilji) - list(GAN).index(ilgan) - 2) % 12
        return list(JI)[base] + "," + list(JI)[(base+1)%12]
    except: return "-"

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
    except Exception as e: 
        return 1

def get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, forbidden_list):
    import datetime as dt_mod
    from korean_lunar_calendar import KoreanLunarCalendar
    
    results = []
    curr = start_date
    
    # 합/충 판단용 기본 리스트
    hap_list = [{'자','축'}, {'인','해'}, {'묘','술'}, {'진','유'}, {'사','신'}, {'오','미'}]
    choong_list = [{'자','오'}, {'축','미'}, {'인','신'}, {'묘','유'}, {'진','술'}, {'사','해'}]
    
    while curr <= end_date:
        score = 80
        birth_d = curr + dt_mod.timedelta(days=280) # 출산일 역산
        b_klc = KoreanLunarCalendar()
        b_klc.setSolarDate(birth_d.year, birth_d.month, birth_d.day)
        b_gj = b_klc.getChineseGapJaString().split()
        
        if len(b_gj) >= 3:
            b_ilji = b_gj[2][1] # 태어날 아이의 일지
            
            # 부모 지지와 대조하여 동적 스코어링
            for p_ji in m_jjis + f_jjis:
                if p_ji == '?': continue
                pair = {b_ilji, p_ji}
                if pair in hap_list: score += 10    # 합이 되면 가점
                if pair in choong_list: score -= 15 # 충이 되면 감점
                
        results.append({'date': curr.strftime('%Y-%m-%d'), 'score': score})
        curr += dt_mod.timedelta(days=1)
        
    # 점수 높은 순으로 정렬 후 상위 3개만 추출
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:3]
# ==============================================================================
# 3. 프리미엄 궁합 분석 엔진 클래스
# ==============================================================================
def get_group_ss(ss_str):
    return {'비견':'비겁', '겁재':'비겁', '식신':'식상', '상관':'식상', '편재':'재성', '정재':'재성', '편관':'관성', '정관':'관성', '편인':'인성', '정인':'인성'}.get(ss_str, '비겁')

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

    def get_vault_harmony(self, base_gans, base_jjis, partner_jjis):
        results = []
        for p_ji in partner_jjis:
            results.extend(check_vault_status(base_gans, base_jjis, p_ji))
        return results

    def get_johoo_harmony(self, m_ilgan, m_ec, f_ec):
        score = 0
        if m_ilgan in "丙丁": 
            if f_ec['수'] >= 2: score += 5
        elif m_ilgan in "壬癸": 
            if f_ec['화'] >= 2: score += 5
        return score

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

# ==============================================================================
# 4. 사이드바 UI (Top-Down 동적 레이아웃)
# ==============================================================================
with st.sidebar:
    st.title("🏮초연 시공명리 연구소")
    st.caption(f"{APP_VERSION} Master (Base + Gunghap)")
    st.markdown("---")

    # 1. 본인 사주 역산 (통합 파싱 모듈)
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
            _ry, _rm, _rd = extract_ganji(ry), extract_ganji(rm), extract_ganji(rd)
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
                                    ji_char = extract_ganji(rt)[-1]
                                    rt_h = K2H_JI.get(ji_char, ji_char)
                                    if rt_h in time_map_rev: st.session_state.s_t = time_map_rev[rt_h]
                                found = True
                                st.success(f"✅ {curr_dt.year}년 {curr_dt.month:02d}월 {curr_dt.day:02d}일 입력완료!")
                                break
                            curr_dt -= dt_mod.timedelta(days=1)
                    if found: break
                if not found: st.error("일치하는 날짜가 없습니다.")
            else: st.warning("간지를 2글자씩 정확히 입력하세요.")

    st.markdown("---")
    u_product = st.selectbox("📋 분석 상품 선택", ["개인사주", "궁합", "타 감명서"])
    
    st.markdown("<div style='font-weight:900; color:#1A237E; margin-bottom:5px;'>👤 신청인 정보 (공통)</div>", unsafe_allow_html=True)
    u_name = st.text_input("이름", value="", key="u_n")
    u_gender = st.selectbox("성별", ["남성", "여성"], key="u_g")
    u_marital = st.selectbox("혼인여부", ["선택", "미혼", "기혼", "돌싱"], key="u_m_stat")
    u_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="u_c")
    
    col1, col2, col3 = st.columns(3)
    u_y = col1.number_input("년", 1900, 2050, value=2010, key="s_y")
    u_m = col2.number_input("월", 1, 12, value=1, key="s_m")
    u_d = col3.number_input("일", 1, 31, value=1, key="s_d")
    u_t = st.selectbox("태어난 시간", idx_list, key="s_t")
    
    # 🚨 [수술 완료] 어떤 조건에서도 에러가 나지 않도록 스위치 기본값 강제 선언!
    run_iljin_calc = False
    run_delivery_calc = False
    start_date = None
    end_date = None
    
    # 2. 상품별 동적 UI
    if u_product == "개인사주":
        # 패턴 1: 개인사주 -> 체크박스로 일진 추가
        run_iljin_calc = st.checkbox("🔮 일진 시공간 분석 추가 가동", value=False)
        if run_iljin_calc: 
            st.session_state['target_date'] = st.date_input("분석 일자", value=dt_mod.datetime.now().date())
            
    elif u_product == "타 감명서":
        # 패턴 2: 타 감명서 -> 원문 입력창
        other_reading_text = st.text_area("📄 타 감명서 원문", height=150, key="other_reading")
        
    elif u_product == "궁합":
        with st.expander("🔍 상대방 사주팔자 역산 검색", expanded=False):
            p_col_g1, p_col_g2 = st.columns(2)
            with p_col_g1: p_ry = st.text_input("상대방 년주", key="p_ry")
            with p_col_g2: p_rm = st.text_input("상대방 월주", key="p_rm")
            p_col_g3, p_col_g4 = st.columns(2)
            with p_col_g3: p_rd = st.text_input("상대방 일주", key="p_rd")
            with p_col_g4: p_rt = st.text_input("상대방 시주", key="p_rt")
            if st.button("🔍 상대방 생년월일 자동입력", use_container_width=True, key="p_rev_btn"):
                _pry, _prm, _prd = extract_ganji(p_ry), extract_ganji(p_rm), extract_ganji(p_rd)
                if len(_pry)==2 and len(_prm)==2 and len(_prd)==2:
                    p_ry_h = K2H_GAN.get(_pry[0], _pry[0]) + K2H_JI.get(_pry[1], _pry[1])
                    p_rm_h = K2H_GAN.get(_prm[0], _prm[0]) + K2H_JI.get(_prm[1], _prm[1])
                    p_rd_h = K2H_GAN.get(_prd[0], _prd[0]) + K2H_JI.get(_prd[1], _prd[1])
                    p_klc_find = KoreanLunarCalendar(); p_found = False
                    for y in range(2026, 1899, -1):
                        p_klc_find.setSolarDate(y, 7, 1); p_gj_y = p_klc_find.getChineseGapJaString().split()
                        if p_gj_y and p_gj_y[0][:2] == p_ry_h:
                            p_curr_dt = dt_mod.date(y+1, 2, 28)
                            while p_curr_dt >= dt_mod.date(y, 1, 1):
                                p_klc_find.setSolarDate(p_curr_dt.year, p_curr_dt.month, p_curr_dt.day)
                                p_gj = p_klc_find.getChineseGapJaString().split()
                                if len(p_gj) >= 3 and p_gj[0][:2] == p_ry_h and p_gj[1][:2] == p_rm_h and p_gj[2][:2] == p_rd_h:
                                    st.session_state.p_y_in, st.session_state.p_m_in, st.session_state.p_d_in = p_curr_dt.year, p_curr_dt.month, p_curr_dt.day
                                    time_map_rev = {'子':'00:30 ~ 01:29 (朝子)시','丑':'01:30 ~ 03:29 (丑)시','寅':'03:30 ~ 05:29 (寅)시','卯':'05:30 ~ 07:29 (卯)시','辰':'07:30 ~ 09:29 (辰)시','巳':'09:30 ~ 11:29 (巳)시','午':'11:30 ~ 13:29 (午)시','未':'13:30 ~ 15:29 (未)시','申':'15:30 ~ 17:29 (申)시','酉':'17:30 ~ 19:29 (酉)시','戌':'19:30 ~ 21:29 (戌)시','亥':'21:30 ~ 23:29 (亥)시'}
                                    if p_rt:
                                        p_ji_char = extract_ganji(p_rt)[-1]
                                        p_rt_h = K2H_JI.get(p_ji_char, p_ji_char)
                                        if p_rt_h in time_map_rev: st.session_state.p_t_key = time_map_rev[p_rt_h]
                                    p_found = True
                                    st.success(f"✅ 상대방 {p_curr_dt.year}년 {p_curr_dt.month:02d}월 {p_curr_dt.day:02d}일 입력완료!")
                                    break
                                p_curr_dt -= dt_mod.timedelta(days=1)
                        if p_found: break
                    if not p_found: st.error("일치하는 날짜가 없습니다.")
                else: st.warning("간지를 2글자씩 정확히 입력하세요.")
        
        st.markdown("<div style='font-weight:900; color:#D50000; margin-bottom:5px; margin-top:15px;'>👥 상대방 정보</div>", unsafe_allow_html=True)
        p_name = st.text_input("이름", value="", key="p_n")
        
        p_gender_options = ["여성", "남성"] if u_gender == "남성" else ["남성", "여성"]
        p_gender = st.selectbox("성별", p_gender_options, key="p_g")
        
        p_marital = st.selectbox("혼인여부", ["미혼", "기혼", "돌싱"], key="p_m_stat")
        p_cal = st.selectbox("달력", ["양력", "음력(평달)", "음력(윤달)"], key="p_c")
        
        p_col1, p_col2, p_col3 = st.columns(3)
        p_y = p_col1.number_input("년 (상대)", 1900, 2050, value=1980, key="p_y_in")
        p_m = p_col2.number_input("월 (상대)", 1, 12, value=1, key="p_m_in")
        p_d = p_col3.number_input("일 (상대)", 1, 31, value=1, key="p_d_in")
        
        p_t = st.selectbox("태어난 시간", idx_list, key="p_t_key")
        
        st.markdown("---")
        
        # 🚨 [박사님 의도 100% 반영] 패턴 3: 궁합 -> 체크박스로 출산택일 추가 (일진 분석과 완벽히 동일한 UI 전개)
        run_delivery_calc = st.checkbox("👶 출산택일 분석 추가 가동", value=False)
        if run_delivery_calc:
            baby_gender = st.radio("태아 성별", ["미정", "남아", "여아"])
            start_date = st.date_input("탐색 시작일", value=dt_mod.datetime.now().date())
            end_date = st.date_input("탐색 종료일", value=dt_mod.datetime.now().date() + dt_mod.timedelta(days=30))

    st.markdown("---")

    btn_single = st.button("🚀 초연 시공명리 사주풀이 가동", use_container_width=True, type="primary")

    components.html("""
    <script>
        function triggerPrint() {
            window.parent.print();
        }
    </script>
    <button onclick='triggerPrint()' style='width:95%; background-color:#2E7D32; color:white; border:none; font-weight:900; height:45px; border-radius:8px; cursor:pointer; font-size:15px; font-family:"Malgun Gothic", sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.15); margin:5px;'>
        🖨️ 풀이 결과 인쇄 / PDF 저장
    </button>
    """, height=70)

    if btn_single:
        # [0단계] 입력값 유효성 정밀 검증
        if not u_name.strip(): 
            st.warning("🚨 [입력 오류] 신청인의 이름이 누락되었습니다. 정확한 성명을 입력해 주십시오.")
            st.stop()
        elif len(u_name.strip()) > 10:
            st.warning("🚨 [입력 오류] 이름이 너무 깁니다. 10자 이내로 정확히 입력해 주십시오.")
            st.stop()
            
        if u_y < 1900 or u_y > 2050:
            st.warning("🚨 [입력 오류] 입력하신 출생 연도가 범위를 벗어났습니다. (허용 범위: 1900년 ~ 2050년)")
            st.stop()
            
        if u_product == "타 감명서" and not other_reading_text.strip():
            st.warning("🚨 [입력 오류] 타 감명서 원문을 입력해 주십시오.")
            st.stop()
            
        if u_product == "궁합" and not p_name.strip(): 
            st.warning("🚨 [입력 오류] 상대방의 이름을 입력해 주십시오.")
            st.stop()
            
        if "모름" in str(u_t) or not u_t:
            st.info("ℹ️ [안내] 태어난 시간을 입력하지 않으셨습니다. 시주(時柱)를 제외한 삼주육자(三柱六字)로 감명을 진행합니다.")
        
        st.session_state['app_running'] = True
        
        if u_product == "개인사주" and run_iljin_calc and st.session_state.get('saved_report_html'):
            st.session_state['need_calc'] = False
            st.session_state['run_waterfall'] = True
            if 'saved_report_iljin' in st.session_state: del st.session_state['saved_report_iljin']
            
        elif u_product == "타 감명서":
            st.session_state['need_calc'] = True
            st.session_state['run_waterfall'] = False
            st.session_state['run_delivery_only'] = False
            for key in ['saved_report_html', 'saved_report_2', 'saved_report_gh_cover', 'saved_report_gh_m', 'saved_report_gh_f', 'saved_report_gh_g', 'saved_report_del', 'saved_report_iljin']:
                if key in st.session_state: del st.session_state[key]
                
        elif u_product == "궁합" and run_delivery_calc and st.session_state.get('saved_report_gh_g'):
            st.session_state['need_calc'] = False
            st.session_state['run_delivery_only'] = True
            if 'saved_report_del' in st.session_state: del st.session_state['saved_report_del']
            
        else:
            st.session_state['need_calc'] = True
            st.session_state['run_waterfall'] = run_iljin_calc if u_product == "개인사주" else False 
            st.session_state['run_delivery_only'] = run_delivery_calc if u_product == "궁합" else False
            for key in ['saved_report_html', 'saved_report_2', 'saved_report_gh_cover', 'saved_report_gh_m', 'saved_report_gh_f', 'saved_report_gh_g', 'saved_report_del', 'saved_report_iljin', 'partner_bazi']:
                if key in st.session_state: del st.session_state[key]

# ==============================================================================
# 5. 분석 가동 로직 (need_calc 상태일 때만 무거운 연산 실행)
# ==============================================================================
if st.session_state.get('need_calc', False):
    spinner_msg = f"⏳ [초연 시공명리 분석({APP_VERSION}) 중....]"
    with st.spinner(spinner_msg):
        try:
            kst = pytz.timezone('Asia/Seoul')
            curr_dt_sys = dt_mod.datetime.now(kst)
            curr_y = curr_dt_sys.year
            curr_m = curr_dt_sys.month
            u_age = curr_y - u_y + 1
            base_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0)
            
            klc = KoreanLunarCalendar()
            if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
            elif u_cal == "음력(평달)": klc.setLunarDate(u_y, u_m, u_d, False)
            else: klc.setLunarDate(u_y, u_m, u_d, True)
            
            is_leap = getattr(klc, 'isIntercalary', False)
            leap_str = "윤달" if is_leap else "평달"
            sol_str = f"{klc.solarYear}년 {klc.solarMonth:02d}월 {klc.solarDay:02d}일"
            lun_str = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({leap_str})"
            
            true_ym, true_mm, _ = get_true_year_month_pillar(u_y, u_m, u_d, 12, 0)
            ys, yb = true_ym[0], true_ym[1]
            ms, mb = true_mm[0], true_mm[1]
            
            gj = klc.getChineseGapJaString().split()
            ds, db = gj[2][0], gj[2][1]
            hs, hb = get_time_ganji(ds, u_t, base_dt)
            
            gans, jjis = [hs, ds, ms, ys], [hb, db, mb, yb]
            applicant_bazi = [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"]

            st.session_state['global_gans'] = gans
            st.session_state['global_jjis'] = jjis
            st.session_state['global_ds'] = ds
            st.session_state['global_db'] = db

            adj_mins = get_total_time_adjustment(base_dt)
            utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
            order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
            calc_d = get_daeun_su_accurate(utc_dt, order)
            current_daewun_age = ((u_age - calc_d) // 10) * 10 + calc_d
            
            base_y_idx = (curr_y - 1984) % 60
            curr_y_ganji = GAN[base_y_idx % 10] + JI[base_y_idx % 12]
            time_str = f" {u_t.split('(')[0].strip()} ({hb})시" if u_t != "시간 모름" else ""
            
            def td(c, size="18px"): return f"<td class='color-{get_color(c)}' style='font-size:{size}; font-weight:900; border:1px solid #444 !important;'>{('?' if c in ['?',' ','-'] else c)}</td>"
            
            disp_name = u_name if u_name.strip() else "홍길동"
            p_icon = "♂️" if u_gender == "남성" else "♀️"
            p_color = "#1A237E" if u_gender == "남성" else "#D50000"
            today_str = (dt_mod.datetime.utcnow() + dt_mod.timedelta(hours=9)).strftime("%Y년 %m월 %d일")

            # ------------------------------------------------------------------
            # [모드 1] 개인사주 분석
            # ------------------------------------------------------------------
            if u_product in ["개인사주", "궁합", "타 감명서"]:
                past_months_html = ""

                cover_html = (
                        f"<div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>\n"
                        f"    <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>\n"
                        f"        <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>\n"
                        f"            <h1 class='title-gothic' style='font-size: 40px !important; margin:0 !important;'>초연 시공명리 사주팔자 풀이</h1>\n"
                        f"            <div style='text-align: right; margin-top: 10px;'>\n"
                        f"                <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px;'>{APP_VERSION}</span>\n"
                        f"            </div>\n"
                        f"        </div>\n"
                        f"        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>\n"
                        f"            <h2 style='font-size: 24px; font-weight: 800; color: {p_color}; margin-bottom: 20px;'>{p_icon} 신청인 : {u_name} 님</h2>\n"
                        f"            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>\n"
                        f"                <p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p>\n"
                        f"                <p style='margin: 5px 0 0 0; color: #D50000; white-space: nowrap;'>{time_str}</p>\n"
                        f"            </div>\n"
                        f"        </div>\n"
                        f"        <p style='font-size: 18px; margin-top: 50px; font-weight: 800;'>{today_str}</p>\n"
                        f"        <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 20px;'>초연 시공명리 연구소</p>\n"
                        f"    </div>\n"
                        f"</div>"
                    )
                st.session_state['saved_report_cover'] = cover_html

                ji_rel_rows = ""
                for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                    b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                    b_top = "0px solid transparent !important"
                    cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                    lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                    ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

                info_h = f"<div style='text-align:center; font-family:\"Malgun Gothic\", sans-serif; margin-bottom:15px; line-height:1.5;'><span style='font-size:18px; font-weight:900; color:{p_color}; white-space:nowrap;'>{p_icon} {disp_name}님 ({u_gender}, {u_marital}, {u_age}세)</span><br><span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>[양력: {sol_str} | 음력: {lun_str} {time_str}]</span></div>"

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
<tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>천간</td>{td(hs)}{td(ds)}{td(ms)}{td(ys)}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#E8EAF6; color:#1A237E; font-weight:900; font-size:14px !important;'>지지</td>{td(hb)}{td(db)}{td(mb)}{td(yb)}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(ds,hb)}</td><td style='border:1px solid #444;'>{get_ss(ds,db)}</td><td style='border:1px solid #444;'>{get_ss(ds,mb)}</td><td style='border:1px solid #444;'>{get_ss(ds,yb)}</td></tr>
<tr><td class='header-cell-main' style='padding:0; border:1px solid #444; background:#f5f5f5; font-weight:900; font-size:14px !important;'>지장간</td>{"".join([f"<td style='padding:0; border:1px solid #444;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
{ji_rel_rows}
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이운성</td>{"".join([f"<td style='color:#0D47A1; border:1px solid #444 !important;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>십이신살</td>{"".join([f"<td style='color:#C62828; border:1px solid #444 !important;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
<tr><td class='header-cell-main' style='border:1px solid #444 !important; background:#f5f5f5; font-weight:900; font-size:14px !important;'>일반신살</td>{"".join([f"<td style='vertical-align:top; padding:2px; border:1px solid #444 !important;'>{'<br>'.join(get_general_shinsal_filtered(i, gans, jjis, u_gender)) if get_general_shinsal_filtered(i, gans, jjis, u_gender) else '-'}</td>" for i in range(4)])}</tr>
</table>
"""
                calc_gyukgook, gyukgook_detail = get_gyukgook_detailed(ds, ys, ms, hs, mb)

                gen_shinsal_list = []
                for i in range(4):
                    raw_tags = get_general_shinsal_filtered(i, gans, jjis, u_gender)
                    for tag in raw_tags:
                        if ">" in tag and "<" in tag: gen_shinsal_list.append(tag.split('>')[1].split('<')[0])
                shinsal_str = ", ".join(list(dict.fromkeys(gen_shinsal_list))) if gen_shinsal_list else "특이 신살 없음"
                
                s12_list = [get_12_shinsal(yb, j) for j in jjis if get_12_shinsal(yb, j) != "-"]
                s12_str = ", ".join(list(dict.fromkeys(s12_list))) if s12_list else "특이 12신살 없음"
          
                samhyung_warn = ""
                has_in, has_sa, has_shin = '寅' in jjis, '巳' in jjis, '申' in jjis
                if sum([has_in, has_sa, has_shin]) == 2:
                    missing = [x for x, has in zip(['寅','巳','申'], [has_in, has_sa, has_shin]) if not has][0]
                    samhyung_warn += f"원국에 인사신 중 2글자가 있어 가형 상태입니다. 운에서 '{missing}'이 들어올 때 삼형살이 완성되니 주의 요망. "
                has_chuk, has_sul, has_mi = '丑' in jjis, '戌' in jjis, '未' in jjis
                if sum([has_chuk, has_sul, has_mi]) == 2:
                    missing = [x for x, has in zip(['丑','戌','未'], [has_chuk, has_sul, has_mi]) if not has][0]
                    samhyung_warn += f"원국에 축술미 중 2글자가 있어 가형 상태입니다. 운에서 '{missing}'이 들어올 때 삼형살이 완성되니 주의 요망. "
                if not samhyung_warn: samhyung_warn = "해당 없음"

                counts = {"목":0,"화":0,"토":0,"금":0,"수":0}
                for char in gans + jjis:
                    if char != "?": counts[get_color(char)] += 1
                
                guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 未','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
                guiin_str = guiin_map.get(ds, '없음')
                    
                direction_str = "순행" if order == 1 else "역행"
                n_gong = calculate_gongmang(ys, yb)
                i_gong = calculate_gongmang(ds, db)
                
                gongmang_targets = n_gong.split(',') + i_gong.split(',')
                gongmang_hits = []
                if yb in gongmang_targets: gongmang_hits.append(f"년지({yb})")
                if mb in gongmang_targets: gongmang_hits.append(f"월지({mb})")
                if db in gongmang_targets: gongmang_hits.append(f"일지({db})")
                if hb in gongmang_targets: gongmang_hits.append(f"시지({hb})")
                
                gongmang_actual = ", ".join(gongmang_hits) + "에 공망 작용함" if gongmang_hits else "사주 원국 내 공망 작용 없음"
                
                cur_samjae = get_samjae(yb, curr_y_ganji[1])
                samjae_color = "#C62828" if cur_samjae != "해당 없음" else "#555"
                
                master_bar_html = f"""
<div style='border:2px solid #3E2723; margin-top:20px; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px; white-space:nowrap;'>
    <div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div>
    <div>🌟 천을귀인: {guiin_str}</div>
    <div>🎯 공망: [년] {n_gong} / [일] {i_gong}</div>
    <div>🌪️ 삼재: <span style='color:{samjae_color};'>{cur_samjae}</span></div>
</div>
"""
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
                cur_wol_g = wol_gans[curr_m - 1]
                cur_wol_j = wol_jis[curr_m - 1]
                
                wol_html = f"<div style='margin-top:5px; margin-bottom:10px; font-size:18px; font-weight:900; color:#1A237E;'>[ 월운의 흐름 ({curr_y}년도 양력기준) ]</div><div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white; margin-bottom:5px;'>"
                for i in range(12):
                    tm, tc, tj = i + 1, wol_gans[i], wol_jis[i]
                    is_cur_m = (tm == curr_m)
                    bg_col = "#E8F5E9" if is_cur_m else "transparent"
                    b_left = "1px solid #ccc" if i != 11 else "none"
                    wol_html += f"<div style='flex:1; border-left:{b_left}; text-align:center; padding-bottom:3px; background-color:{bg_col};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:12px; border-bottom:1px solid #ccc;'>{tm}월</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:16px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:16px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:12px;'>{get_ss(ds,tj)}</div><div style='font-size:11px; border-top:1px solid #ccc;'>{get_unsung(ds,tj)}</div><div style='font-size:11px; color:#C62828; border-top:1px solid #ccc;'>{get_12_shinsal(yb, tj)}</div></div>"
                wol_html += "</div>"
                
                past_daewun_list = []
                for idx in range(cur_dw_idx):
                    val = idx * 10 + calc_d
                    d_gan = GAN[(GAN.index(ms) + (idx + 1) * order) % 10] if ms in GAN else "-"
                    d_ji = JI[(JI.index(mb) + (idx + 1) * order) % 12] if mb in JI else "-"
                    past_daewun_list.append(f"• {val}세~{val+9}세 ({d_gan}{d_ji}대운): ")
                past_daewun_html = "\n".join(past_daewun_list) if past_daewun_list else "• (첫 대운 시기이므로 이전 대운 생략)"

                curr_dw_start_year = u_y + current_daewun_age - 1
                sewun_start_calc = min(curr_dw_start_year, curr_y - 3)
                past_sewun_list = []
                for py in range(sewun_start_calc, curr_y):
                    base = (py - 1984) % 60
                    past_sewun_list.append(f"• {py}년({GAN[base%10]}{JI[base%12]}년): ")
                past_sewun_html = "\n".join(past_sewun_list) if past_sewun_list else "• (분석할 과거 세운 없음)"

                terms_name = {1:"소한", 2:"입춘", 3:"경칩", 4:"청명", 5:"입하", 6:"망종", 7:"소서", 8:"입추", 9:"백로", 10:"한로", 11:"입동", 12:"대설"}
                
                def get_term_day(y, m):
                    _, p1, _ = get_true_year_month_pillar(y, m, 1, 12, 0)
                    for d in range(2, 12):
                        _, pd, _ = get_true_year_month_pillar(y, m, d, 12, 0)
                        if pd != p1: return d, pd
                    return 5, p1

                past_wol_list = []
                prev_y_idx = (curr_y - 1 - 1984) % 60
                prev_y_ganji = GAN[prev_y_idx % 10] + JI[prev_y_idx % 12]
                
                for pm in range(1, curr_m):
                    tc, tj = wol_gans[pm-1], wol_jis[pm-1]
                    s_day, _ = get_term_day(curr_y, pm)
                    next_m = pm + 1 if pm < 12 else 1
                    next_y = curr_y if pm < 12 else curr_y + 1
                    e_day, _ = get_term_day(next_y, next_m)
                    t_start = terms_name[pm]
                    t_end = terms_name[next_m]
                    
                    year_prefix = f"{prev_y_ganji}년 " if pm == 1 else ""
                    past_wol_list.append(f"• {pm}월({tc}{tj}월): ({year_prefix}{pm}월 {s_day}일 {t_start} ~ {next_m}월 {e_day-1}일 {t_end} 전)")
                
                past_months_html = "\n".join(past_wol_list) if past_wol_list else "• (올해 첫 달이므로 작년 하반기 요약): "

                curr_term_day, curr_wol_pillar = get_term_day(curr_y, curr_m)
                next_m = curr_m + 1 if curr_m < 12 else 1
                next_y = curr_y if curr_m < 12 else curr_y + 1
                next_term_day, _ = get_term_day(next_y, next_m)
                
                curr_t_name = terms_name[curr_m]
                next_t_name = terms_name[next_m]

                if curr_m == 6:
                    sun = ephem.Sun()
                    haji_day = 21 
                    for d in range(20, 24):
                        dt_utc = dt_mod.datetime(curr_y, 6, d, 12, 0).astimezone(pytz.utc)
                        sun.compute(dt_utc)
                        if math.degrees(ephem.Ecliptic(sun).lon) % 360.0 >= 90.0:
                            haji_day = d
                            break
                    
                    prompt_first_half = f"▶ 이번 달 전반기 ({curr_m}월 {curr_term_day}일 {curr_t_name} ~ {curr_m}월 {haji_day-1}일 하지 전: {curr_wol_pillar})"
                    prompt_second_half = f"▶ 이번 달 후반기 ({curr_m}월 {haji_day}일 하지 ~ {next_m}월 {next_term_day-1}일 {next_t_name} 전: {curr_wol_pillar})"
                else:
                    mid_day = curr_term_day + 15
                    prompt_first_half = f"▶ 이번 달 전반기 ({curr_m}월 {curr_term_day}일 {curr_t_name} ~ {curr_m}월 {mid_day-1}일: {curr_wol_pillar})"
                    prompt_second_half = f"▶ 이번 달 후반기 ({curr_m}월 {mid_day}일 ~ {next_m}월 {next_term_day-1}일 {next_t_name} 전: {curr_wol_pillar})"

                closing_html = f"""<div style='margin-top: 30px;'>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>'사주팔자'는 태어날 때 부여받은 변하지 않는 바코드(bar-code)와 같지만, 우리가 살아가며 마주하는 스캐너(scanner)인 '운'은 늘 변화하며 흐릅니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 8px;'>따라서 오늘의 '초연 시공명리와의 인연'이 <b>{disp_name}님</b>의 삶이라는 긴 여정에서 길을 잃지 않게 돕는 '나침반'이 되기를 진심으로 기원합니다.</p>
<p style='text-indent: 15px; text-align: justify; line-height: 1.8; margin-bottom: 15px;'>앞으로 미래에 대한 더 깊은 시공명리의 지혜와 궁금증이 있으시면 언제든 <b>'초연 시공명리 연구소'</b>의 문을 두드려 주십시오.</p>
<p style='text-indent: 15px; font-size: 16px; line-height: 1.8; font-weight: bold; margin-bottom: 0px;'>오늘 닿은 귀한 인연에 다시 한 번 감사드립니다.</p>
<div style='text-align: right; margin-top: 30px;'>
<span style='font-weight: 900; font-size: 18px; color: #1A237E;'>- 초연 시공명리 연구소 드림 -</span>
</div>
</div>"""

                report_1_full_html = f"""{cover_html}
<div class='report-page' style='page-break-before: avoid;'>
<div class='vip-inset-frame' style='border:2px solid #1A237E; box-sizing: border-box; padding: 20px; border-radius:15px; margin-top: 0;'>

<h1 style='text-align:center;'>🎯[초연 시공명리 사주풀이]</h1>
{table_html}
{master_bar_html}
<div style='margin-top:20px;'>
{{full_content_clean_placeholder}}
</div>
</div>
</div>"""

                jeolip_day = 5
                prev_wol_pillar = ""
                curr_wol_pillar = ""
                _, p1, _ = get_true_year_month_pillar(curr_y, curr_m, 1, 12, 0)
                for d in range(2, 12):
                    _, pd, _ = get_true_year_month_pillar(curr_y, curr_m, d, 12, 0)
                    if pd != p1:
                        jeolip_day = d
                        prev_wol_pillar = p1
                        curr_wol_pillar = pd
                        break
                if not curr_wol_pillar:
                    curr_wol_pillar = p1
                    prev_wol_pillar = p1

                base_gans_list = [hs, ds, ms, ys]
                base_jjis_list = [hb, db, mb, yb]

                won_guk_vaults = []
                for attacker in base_jjis_list:
                    won_guk_vaults.extend(check_vault_status(base_gans_list, base_jjis_list, attacker))
                won_guk_vaults = list(dict.fromkeys(won_guk_vaults)) 
                won_guk_vaults_str = ", ".join(won_guk_vaults) if won_guk_vaults else "해당 없음"

                daewun_vaults = check_vault_status(base_gans_list, base_jjis_list, dw_j_cur)
                sewun_vaults = check_vault_status(base_gans_list, base_jjis_list, curr_y_ganji[1])
                wolwun_vaults = check_vault_status(base_gans_list, base_jjis_list, cur_wol_j)

                hang_un_vaults = list(dict.fromkeys(daewun_vaults + sewun_vaults + wolwun_vaults))
                hang_un_vaults_str = ", ".join(hang_un_vaults) if hang_un_vaults else "해당 없음"

                disp_first_name = disp_name[1:] if len(disp_name) > 2 else disp_name

                ipchun_day = 4
                _, p1_feb, _ = get_true_year_month_pillar(curr_y, 2, 1, 12, 0)
                for d in range(2, 10):
                    _, pd_feb, _ = get_true_year_month_pillar(curr_y, 2, d, 12, 0)
                    if pd_feb != p1_feb:
                        ipchun_day = d
                        break

                soseo_day = 7
                _, p1_jul, _ = get_true_year_month_pillar(curr_y, 7, 1, 12, 0)
                for d in range(2, 12):
                    _, pd_jul, _ = get_true_year_month_pillar(curr_y, 7, d, 12, 0)
                    if pd_jul != p1_jul:
                        soseo_day = d
                        break

                next_ipchun_day = 4
                _, p1_next_feb, _ = get_true_year_month_pillar(curr_y + 1, 2, 1, 12, 0)
                for d in range(2, 10):
                    _, pd_next_feb, _ = get_true_year_month_pillar(curr_y + 1, 2, d, 12, 0)
                    if pd_next_feb != p1_next_feb:
                        next_ipchun_day = d
                        break

                sewun_first_half_date = f"{curr_y}.02.{ipchun_day:02d}(입춘) ~ {curr_y}.07.{soseo_day:02d}(소서 전)"
                sewun_second_half_date = f"{curr_y}.07.{soseo_day:02d}(소서) ~ {curr_y + 1}.02.{next_ipchun_day:02d}(입춘 전)"
                
                age_prompt = ""
                if u_age < 20:
                    age_prompt = "내담자는 청소년기(10대)입니다. 학업 진학운과 부모 형제운을 최우선으로 상세히 분석하고 재물 사업운은 축소하십시오."
                elif 20 <= u_age < 40:
                    age_prompt = "내담자는 청년기(20~30대) MZ세대입니다. 고리타분한 명리 용어를 버리고 직업은 '스타트업, 프리랜서, 워라밸, 퍼스널 브랜딩', 연애는 '소개팅, 썸, 연인 간의 소통' 등 2030 청년들이 100% 공감할 수 있는 세련되고 트렌디한 어휘로 통변하십시오."
                elif 40 <= u_age < 60:
                    age_prompt = "내담자는 중장년기(40~50대)입니다. 재성운과 관직 명예운에 집중하여 현실적인 자산 관리와 사회적 성취를 중심으로 서술하십시오."
                else:
                    age_prompt = "내담자는 노년기(60대 이상)입니다. 건강운 및 심리적 평안, 노후 자산 안정을 최우선으로 깊이 다루십시오."

                gender_prompt = ""
                if u_gender == "남성":
                    gender_prompt = "남성 내담자입니다. 배우자운(재성)과 자식운(관성)을 남명 이론에 입각하여 해석하십시오."
                else:
                    gender_prompt = "여성 내담자입니다. 배우자운(관성)과 자식운(식상)을 여명 이론에 입각하여 해석하십시오."

                w_key = f"{ms}{mb}".strip()
                i_key = f"{ds}{db}".strip()

                w_val = choyeon_db.get("wolryeong", {}).get(w_key, f"[{w_key}] 시공간 데이터 없음")
                i_val = choyeon_db.get("ilju", {}).get(i_key, f"[{i_key}] 성품 데이터 없음")
                struct_data = choyeon_db.get("ilju_structure", {}).get(i_key, ["구조 미상", "유형 미상", "성향 미상"])
                s_name, s_type, s_desc = struct_data[0], struct_data[1], struct_data[2]

                choyeon_golden_text = f"""
<div style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000; margin-bottom: 20px;'>
    <p style='text-indent: 15px; margin-bottom: 5px;'>
        <b>{disp_name}님</b>은 '{w_val}'의 시공간에서, '{i_val}'의 성품을 가지고 태어나셨습니다.
    </p>
</div>
"""
                dw_start_age = current_daewun_age
                dw_mid_age   = current_daewun_age + 4
                dw_mid2_age  = current_daewun_age + 5
                dw_end_age   = current_daewun_age + 9
                                
                db_header = (
                    f"[시스템 강제 시간 인식: 현재 시점은 {curr_y}년 {curr_m}월 입니다.]\n"
                    "당신은 명리심리상담사 1급 자격을 갖춘 초연 박사입니다. \n"
                    f"- 내담자 성함: {disp_name}\n"
                    f"- 나이 / 성별: {u_age}세 / {u_gender}\n"
                    f"- marital_status: {u_marital}\n"
                    f"- 타고난 심리 구조 팩트: {s_name} ({s_type} - {s_desc})\n"
                    f"- 실제 타격받는 공망 궁위 팩트: {gongmang_actual}\n"
                    f"- 올해({curr_y}년) 삼재 여부: {cur_samjae}\n"  
                    f"- 원국 내부 묘고(입고/개고) 작용: {won_guk_vaults_str}\n"
                    f"- 현재 행운(대/세/월운) 외부 충격에 의한 묘고 작용: {hang_un_vaults_str}\n"
                    f"🚨 [AI 환각 및 UI 파괴 원천 차단 절대 규칙]\n"
                    f"1. 서론 철저 금지: '안녕하십니까', '기쁩니다' 등의 인사말이나 감성적인 도입부를 절대로 작성하지 마십시오.\n"
                    f"2. 호칭 절대 규칙: 각 대목차의 첫 문장은 반드시 '{disp_name}님은~'으로 격식있게 시작하고, 그 이후 본문에서는 친근하게 '{disp_first_name}님은~'으로 부르십시오.\n"
                    f"3. 🚨 공망 소설 금지: 위 '실제 타격받는 공망 궁위 팩트'에 명시된 자리만 공망으로 해석하십시오. 명시되지 않은 자리(예: 일지가 없는데 일지 공망이라고 하는 등)가 비어있다고 소설을 쓰면 즉시 치명적 시스템 오류로 간주합니다!\n"
                    f"4. 괄호 병기 금지: 에세이 작성 시 전문 용어나 한자를 괄호 안에 병기하는 행위를 금지합니다.\n"
                    f"5. HTML 훼손 금지: </div> 태그를 임의로 닫거나 마크다운 기호를 남발하지 마십시오.\n"
                )

                if u_gender == '남성':
                    yukchin_rule = f"""
🚨 [육친 통변 특수부대 절대 규칙 (남성용)]: 
- 본 내담자는 남성(현재 상태: {u_marital})입니다. 아래의 명리학적 육친 생극제화 및 대체 규칙을 100% 엄수하십시오.
1. 👨‍👩‍👦 [핵심 가족]: 
   - 아내(부인) = 정재 (정재가 없으면 편재로 대체)
   - 애인(여친) = 편재 (편재가 없으면 정재로 대체)
   - 자녀 = 관성(정관/편관) 🚨(경고: 남명에서 '식상'을 자녀로 풀이하는 즉시 치명적 오류로 간주함!)
2. 👵👴 [부모 및 조부모]: 
   - 아버지 = 편재 (없으면 정재) / 어머니 = 정인 (없으면 편인)
   - 조부(할아버지) = 편인 / 조모(할머니) = 상관
3. 🏠 [처가 및 형제]: 
   - 장모(처가) = 식상 (아내를 생하는 기운)
   - 동성 형제(형/남동생) = 비견 / 이성 형제(누나/여동생) = 겁재
4. 🚨 [상태별 호칭 맞춤형 타겟팅]: 내담자의 현재 혼인 상태({u_marital})를 반드시 반영하십시오. 
   - 기혼: '현재 아내/배우자'로 칭할 것.
   - 미혼: '미래의 아내/인연'으로 칭할 것.
   - 🚨돌싱(이혼/사별): '과거의 인연(전처)'에 대한 성찰이나 '새로운 인연(재혼운)'으로 변환하여 카운슬링할 것.
"""
                else:
                    yukchin_rule = f"""
🚨 [육친 통변 특수부대 절대 규칙 (여성용)]: 
- 본 내담자는 여성(현재 상태: {u_marital})입니다. 아래의 명리학적 육친 생극제화 및 대체 규칙을 100% 엄수하십시오.
1. 👩‍❤️‍👨 [핵심 가족]: 
   - 남편 = 정관 (정관이 없으면 편관으로 대체)
   - 애인(남친) = 편관 (편관이 없으면 정관으로 대체)
   - 자녀 = 식상(식신/상관) 🚨(경고: 여명에서 '관성'을 자녀로 풀이하는 즉시 치명적 오류로 간주함!)
2. 👵👴 [부모 및 조부모]: 
   - 아버지 = 편재 (없으면 정재) / 어머니 = 정인 (없으면 편인)
   - 조부(외할아버지) = 편인 / 조모(외할머니) = 상관
3. 🏠 [시댁 및 자매]: 
   - 시어머니(시댁) = 재성 (남편을 생하는 기운)
   - 동성 형제(언니/여동생) = 비견 / 이성 형제(오빠/남동생) = 겁재
4. 🚨 [상태별 호칭 맞춤형 타겟팅]: 내담자의 현재 혼인 상태({u_marital})를 반드시 반영하십시오. 
   - 기혼: '현재 남편/배우자'로 칭할 것.
   - 미혼: '미래의 남편/인연'으로 칭할 것.
   - 🚨돌싱(이혼/사별): '과거의 인연(전 남편)'에 대한 성찰이나 '새로운 인연(재혼운)'으로 변환하여 카운슬링할 것.
"""

                def get_group_ss_local(ss_name):
                    if not ss_name or ss_name in ["?", "-", " "]: return "비겁"
                    if "비" in ss_name or "겁" in ss_name: return "비겁"
                    if "식" in ss_name or "상" in ss_name: return "식상"
                    if "재" in ss_name: return "재성"
                    if "관" in ss_name: return "관성"
                    if "인" in ss_name: return "인성"
                    return "비겁"

                def get_execution_yong_local(upper_group, lower_group):
                    matrix = {
                        '비겁': {'비겁':'비겁', '식상':'식상', '재성':'재성', '관성':'관성', '인성':'인성'},
                        '식상': {'비겁':'인성', '식상':'비겁', '재성':'식상', '관성':'재성', '인성':'관성'},
                        '재성': {'비겁':'관성', '식상':'인성', '재성':'비겁', '관성':'식상', '인성':'재성'},
                        '관성': {'비겁':'재성', '식상':'관성', '재성':'인성', '관성':'비겁', '인성':'식상'},
                        '인성': {'비겁':'식상', '식상':'재성', '재성':'관성', '관성':'인성', '인성':'비겁'}
                    }
                    return matrix.get(upper_group, {}).get(lower_group, '비겁')

                def get_matrix_keyword_local(che_group, yong_group, matrix_text):
                    target_str = f"- 체({che_group})+용({yong_group}):"
                    for line in matrix_text.splitlines():
                        if line.startswith(target_str):
                            return line.split(":", 1)[1].strip()
                    return "변화 감지"

                che_yong_matrix_text = """
- 체(비겁)+용(비겁): 식상발흥, 직무개척, 건강호조, 출산운, 처가와 유정
- 체(비겁)+용(식상): 업무원만, 진취력, 건강호조, 원행, 발표, 여행
- 체(비겁)+용(재성): 손재, 소비, 이성난, 가정불화, 부친반목
- 체(비겁)+용(관성): 설화, 관재, 가족불화, 직장문제, 공명심
- 체(비겁)+용(인성): 의식주안정, 스카우트, 계약, 학업순성, 합격, 가정화목
- 체(식상)+용(비겁): 사업원만, 결과만족, 명진, 의기투합, 긍정심
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
- 체(인성)+용(인성): 비겁발흥, 명예, 명진, 칭찬, 주체성 확립, 학문성취
"""
                
                sewun_gan = curr_y_ganji[1][0] if len(curr_y_ganji[1]) > 0 else "-"
                sewun_ji = curr_y_ganji[1][1] if len(curr_y_ganji[1]) > 1 else "-"
                
                ilju_lower_group = get_group_ss_local(get_ss(ds, db)) 
                
                dw_che_group = get_group_ss_local(get_ss(ds, dw_g_cur)) 
                dw_upper_group = get_group_ss_local(get_ss(dw_g_cur, dw_j_cur))
                dw_yong = get_execution_yong_local(dw_upper_group, ilju_lower_group)
                dw_fact_keyword = get_matrix_keyword_local(dw_che_group, dw_yong, che_yong_matrix_text)
                dw_fact_str = f"체운(무대): {dw_che_group} / 용운(사건): {dw_yong} ➔ 도출 키워드: {dw_fact_keyword}"

                sewun_upper_group = get_group_ss_local(get_ss(sewun_gan, sewun_ji)) 
                sewun_yong = get_execution_yong_local(sewun_upper_group, ilju_lower_group)
                sewun_fact_keyword = get_matrix_keyword_local(dw_che_group, sewun_yong, che_yong_matrix_text)
                sewun_fact_str = f"체운(무대): {dw_che_group} / 용운(사건): {sewun_yong} ➔ 도출 키워드: {sewun_fact_keyword}"

                wol_upper_group = get_group_ss_local(get_ss(cur_wol_g, cur_wol_j))
                wol_yong = get_execution_yong_local(wol_upper_group, ilju_lower_group)
                sewun_che_for_wolwun = get_group_ss_local(get_ss(ds, sewun_gan)) 
                wol_fact_keyword = get_matrix_keyword_local(sewun_che_for_wolwun, wol_yong, che_yong_matrix_text)
                wol_fact_str = f"체운(무대): {sewun_che_for_wolwun} / 용운(사건): {wol_yong} ➔ 도출 키워드: {wol_fact_keyword}"

                try:
                    analysis_summary = "\n".join(get_universal_analysis(ds, mb, db, gans, jjis))
                except Exception:
                    analysis_summary = "- 사주 원국 지장간 및 인종법 분석 팩트"

                prompt = f"""
{db_header}
당신은 명리심리상담사 1급 자격을 갖춘 '초연 박사'입니다.

🚨 [시스템 절대 통제 헌법]
0. [내담자 사주 명조 팩트(절대 준수)]
- 명조: {ys}{yb}년, {ms}{mb}월, {ds}{db}일, {hs}{hb}시
🚨[사주 원국표 절대 팩트 (AI 자체 연산 절대 금지)]
- 년주({ys}{yb}): 천간십성({get_ss(ds, ys)}), 지지십성({get_ss(ds, yb)}), 12운성({get_unsung(ds, yb)}), 12신살({get_12_shinsal(yb, yb)})
- 월주({ms}{mb}): 천간십성({get_ss(ds, ms)}), 지지십성({get_ss(ds, mb)}), 12운성({get_unsung(ds, mb)}), 12신살({get_12_shinsal(yb, mb)})
- 일주({ds}{db}): 일간(본인), 지지십성({get_ss(ds, db)}), 12운성({get_unsung(ds, db)}), 12신살({get_12_shinsal(yb, db)})
- 시주({hs}{hb}): 천간십성({get_ss(ds, hs)}), 지지십성({get_ss(ds, hb)}), 12운성({get_unsung(ds, hb)}), 12신살({get_12_shinsal(yb, hb)})
(※ 위 명조 데이터가 유일한 진실입니다. 다른 데이터를 창조하지 마십시오.)

1. [일간 앵커링]: 본 사주의 일간(日干)은 '{ds}'이며, 이는 우주적 중심 팩트이다. 절대 변경하거나 역추산하지 마십시오.
2. [데이터 무결성]: 시스템이 제공한 팩트(년/월/일/시) 외에 없는 글자를 창조하거나 위치(근묘화실)를 조작하는 행위는 치명적 시스템 오류이다.
3. [자체 연산 엄금]: AI는 절대로 십성, 십이운성, 12신살, 격국을 스스로 계산하거나 유추하지 마십시오. 당신은 연산 능력이 없습니다.
4. [MZ 세대 맞춤형 어조]: 명리 전문 용어(십성, 신살 등)는 단일 인용부호('')로 묶어 시각적으로 강조한 뒤, 반드시 현대적이고 따뜻한 상담가의 구어체로 부드럽게 풀이하십시오.
6. [형식 통제 규칙]: 각 항목의 풀이 과정에서 통변 길이가 길어져 문단을 바꿀 때는, 반드시 `<p style='text-indent: 15px; margin-bottom: 8px;'>` 태그를 사용하여 첫 줄 들여쓰기 및 문단 간격을 강제 적용하십시오. 단순 `<br>`이나 탭(Tab) 사용을 금지합니다.
7. [관계 환각 억제 규칙]: AI는 원국이나 운의 지지(地支) 간 관계(예: 격각, 원진, 귀문 등)를 스스로 유추하거나 판단하지 마십시오. 오직 시스템이 분석하여 제공한 [합형충파해 및 원진/귀문 분석 결과] 텍스트 내에 명시된 팩트 용어만 100% 인용하여 에세이를 작성해야 합니다.

🚨 [문단 및 레이아웃 강제 규격]
1. 모든 에세이 '문단'은 반드시 <p style='text-indent: 1em;'> 태그로 감싸 초등학교 원고지처럼 첫 줄 들여쓰기를 적용하십시오.
2. 🚨[절대 성역]: 상단 '[CHOYEON_GOLDEN_TEXT_HERE]' 문장은 부연 설명 없이 원문 그대로 출력하십시오.
3. 🚨 [절대 금지]: 문단 사이와 문단과 제목사이에 '빈 줄(공백 줄)'을 넣지 마십시오. 엔터키(줄바꿈) 금지. 
4. [가독성 조절]: 문맥 전환 시 <br> 태그 하나만 단일 사용.
5. [계층별 규격]:
   - 부목차: <span class='sub-title' style='display: block; font-size: 20px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 15px; margin-bottom: 5px;'>...</span>
   - 소목차: <span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; line-height: 1.4; margin-top: 10px; margin-bottom: 5px;'>...</span>

🚨 [초연 시공명리 정석 통변 알고리즘 : 강제 수행 지침]
당신은 사주 원국 8글자(년월일시 간지) 전체를 완벽히 조망하며, 반드시 아래의 '정석(正石)' 알고리즘 순서대로만 통변 전개해야 합니다.
1. [7궁위 입체 분석]: 일간을 절대 기준으로 삼아, 나머지 7궁위에 배치된 '십성'과 '12운성'을 접목하십시오. 내담자의 삶을 1) 육친적, 2) 심리적, 3) 사회적 관점에서 입체적으로 풀이하십시오.
2. [신살의 가미]: 위 7궁위 분석 시, 시스템이 제공한 '12신살'과 '일반신살'의 역동성을 양념처럼 가미하여 구체적인 물상과 굴곡을 통변하십시오. (특히 3~10번 육친/사회적 목차 서술 시 적극 활용할 가치)
3. [공망의 3차원 통변]: 사주 내 '공망(空亡)'이 있다면, 그 결핍과 채우려는 욕망을 1) 육친적, 2) 심리적, 3) 사회적 관점으로 나누어 심도 있게 통변하십시오.

🚨 [데이터 무결성 및 환각 방지 절대 규칙]
1. [근묘화실 위치 및 팩트 조작 금지]: 원국에 없는 글자(비어있는 시주 등)를 창조하거나, 제공된 위치 팩트를 뒤섞는 행위를 엄격히 금지합니다.
2. 명리 용어 시각적 강조: 통변 중 핵심 명리 용어는 단일 인용부호(' ')나 괄호( )를 사용하십시오.

[분석 데이터 팩트]
{analysis_summary}

[내담자 맞춤형 정밀 타겟팅]
- {age_prompt}
- {gender_prompt}
- {yukchin_rule}
 
[통변 지시]
- 간지 표기 시 반드시 한자로 표기하십시오.
- 격국 팩트: {gyukgook_detail}
- 공망 팩트: {gongmang_actual}
- 일반신살: {shinsal_str} / 12신살: {s12_str}
- 입고/개고 팩트: 사주팔자의 역동적 관계 분석에 반드시 묘고 작용을 포함하십시오.

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>1. 사주팔자 구조 분석</h3>
<div class='content-box-loose'>
[CHOYEON_GOLDEN_TEXT_HERE]

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 내 삶의 무대와 타고난 기본 성향</span>
(※ 🚨AI 절대 지시: 가장 먼저 내담자의 사주 구조인 '격국({gyukgook_detail})'의 명칭과 그 의미를 상세히 풀이하십시오. 
이후 우주적 중심인 일간('{ds}')을 뼈대로 삼아, 이 격국의 특성이 7궁위의 어느 무대에서 12운성의 어떤 에너지 규모로 발현되는지 구체적이고 현실적으로 조언하십시오. 격국에 대한 통변을 누락하면 치명적 시스템 오류로 간주합니다.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 내 삶의 리듬과 에너지 균형</span>
(※ 🚨AI 전술 지시: 사주팔자 오행의 분포와 조후(온도/습도), 억부의 균형을 분석하십시오. 불균형이 있다면 이를 극복하기 위해 현실 삶에서 어떤 에너지를 추구하고 채워야 하는지 상세한 에세이로 작성하십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 내 삶의 역동성과 상호작용</span>
(※ 🚨AI 전술 지시: 단순 길흉 판단 금지! 다음 3대 역동성을 드라마틱하게 서술하십시오.
1. 천간과 지지의 [합충파해 연쇄반응]: 한 글자의 움직임이 다른 글자를 어떻게 자극하여 나비효과를 내는지 추적.
2. [묘고(墓庫) 작용]: 입고(入庫)와 개고(開庫) 타이밍을 짚어내어 삶의 반전과 수렴을 설명.
3. [격각(隔角)의 이탈]: 공간적 분리(이동, 독립)와 심리적 소외감(고독)을 입체적으로 풀어내십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>4) 내 삶의 숨겨진 강점과 잠재적 에너지</span>
(※ 🚨AI 전술 지시: 12신살({s12_str})과 일반신살({shinsal_str}), 삼재({cur_samjae})를 앵커(닻)로 삼되, 살(煞)의 공포를 조장하지 말고 현대 심리상담 관점의 고유한 강점으로 재해석하십시오.)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>2. 성격</h3>
<div class='content-box-loose'>
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 겉으로 드러난 성격</span>
(※ 🚨AI 절대 준수 규칙: 일간('{ds}')을 우주적 중심으로 삼으십시오. 
1. [표면적 기질]: 일간과 원국에 드러난 '십성', '12운성', '신살'의 상호작용을 통해 겉으로 드러난 페르소나를 풀이하십시오.
2. [일지 지장간 좌법(座法) 해부]: 일지 지장간 내부에 내장된 천간 성분들이 해당 왕궁(王宮) 내부에서 가지는 십이운성 리듬(좌법)을 기준으로, 내담자가 사회와 상호작용할 때 꺼내 쓰는 '현실적 행동 메커니즘'을 도출하십시오.
3. [7궁위 입체 분석]: 나머지 궁위에 배치된 기운을 접목하여 외부와 상호작용하는 방식을 육친적, 심리적, 사회적 관점으로 분석하십시오.)
   
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 감추어진 내 속마음</span>
(※ 🚨AI 절대 연산 규칙: 뜬구름 잡는 묘사를 금지하고 아래 2대 팩트로만 무의식을 타격하십시오.
1. [인종법(引從法)의 무의식 타격]: 원국 천간에 드러나지 않은(결핍된) 오행이나 십성을 일지로 인종(끌어와서 대조)하여, 겉으로는 드러나지 않았으나 내담자조차 모르는 깊은 무의식적 갈망을 구어체로 짚어내십시오.
2. [공망({gongmang_actual})의 현실 타격]: 공망이 걸린 오행/육친이 실제 생활에서 유발하는 심리적 공허함과 환경적 한계 조건을 날카로운 팩트로 기술하십시오.)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>3. 부모·형제운</h3><div class='content-box-loose'>
(※ 🚨AI 전술 지시: 년주(부모궁)와 월주(형제궁)에 배치된 십성과 12운성의 동태만 집중 분석하십시오.
 1) 육친적 덕의 유무, 2) 심리적 자양분 및 결핍을 현대적 구어체로 풀어내십시오.)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>4. 학업·진학운</h3><div class='content-box-loose'>
(※ 🚨AI 전술 지시: 인성(수용)과 식상(표출), 관성(통제)의 십성 관계만 분석하여 1) 심리적 호기심의 방향, 2) 학업 성취도를 이해하기 쉽게 조언하십시오.)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>5. 적성·직업운</h3><div class='content-box-loose'>
(※ 🚨AI 전술 지시: 원국의 주력 에너지를 분석하여 직업 방향성을 제시하되, 특정 글자의 십성 조합을 근거로 구체적 직업 물상(예: 유통, 의료기술, 교육, 특수교정 등)을 핀셋처럼 짚어주십시오.)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>6. 결혼·자녀운</h3><div class='content-box-loose'>
(※ 🚨AI 전술 지시: 일지(배우자궁)와 시주(자녀궁) 및 재성/관성/식상의 동태를 독립적으로 정밀 추적하십시오. 물리적/정서적 거리감이나 인연의 깊이를 팩트있게 통변하십시오.)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>7. 재성운</h3><div class='content-box-loose'>
(※ 🚨AI 전술 지시: 비겁의 조력과 식상생재 흐름을 분석하여 심리적 도전정신과 사회적 창업/확장성의 득실을 조언하십시오.)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>8. 사업운</h3><div class='content-box-loose'>
(※ 🚨AI 전술 지시: 비겁의 조력과 식상생재 흐름을 분석하여 심리적 도전정신과 사회적 창업/확장성의 득실을 조언하십시오.)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>9. 관직·명예운</h3><div class='content-box-loose'>
(※ 🚨AI 전술 지시: 관인상생 및 정관/편관의 상태를 바탕으로 사회적 승진, 명예 추구 욕구, 책임감의 크기를 구어체로 서술하십시오.)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>10. 건강운</h3><div class='content-box-loose'>
(※ 🚨AI 전술 지시: 오행의 과다/과소 및 조후 불균형을 분석하여 취약한 신체 질환을 명리적 물상으로 경고하고, 현실적인 에너지 관리법을 제시하십시오.)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>11. 운의 흐름</h3><div class='content-box-loose'>
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 대운의 흐름</span>
[DAEWUN_TABLE_HERE]
(※ 🚨AI 절대 지시: 위의 마커 '[DAEWUN_TABLE_HERE]'를 절대 지우거나 생략하지 말고, 반드시 텍스트 그대로 100% 똑같이 출력하십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 대운 분석</span>
{past_daewun_html}
[지나온 과거 각 대운 출력 템플릿]
• <b>OO세~OO세 (OO대운):</b> 
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 0px;'><b>1) 전통 명리 풀이:</b> (핵심 요약)</div>
    <div><b>2) 시공 명리 풀이: </b> (※ 대운을 체운으로 삼아 매트릭스 키워드 기반 간략 요약)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 현재 대운 전반기 상세 분석 ({dw_start_age}세~{dw_mid_age}세)</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> (상세 작성)</div>
    <div><b>2) 시공 명리 풀이: </b> (※ 대운을 체운으로 삼아 상세 통변)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 현재 대운 후반기 상세 분석 ({dw_mid2_age}세~{dw_end_age}세)</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> (상세 작성)</div>
    <div><b>2) 시공 명리 풀이:</b> (※ 대운을 체운으로 삼아 상세 통변)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 세운의 흐름</span>
[SEWUN_TABLE_HERE]
(※ 🚨AI 절대 지시: 위의 마커 '[SEWUN_TABLE_HERE]'를 절대 지우거나 생략하지 말고, 반드시 텍스트 그대로 100% 똑같이 출력하십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 세운 분석</span>
{past_sewun_html}
[지나온 과거 각 세운 출력 템플릿]
• <b>OOOO년(OO년):</b> 
<div style='padding-left: 20px; margin-top: 0px;'>
    <div style='margin-bottom: 0px;'><b>1) 전통 명리 풀이:</b> (핵심 요약)</div>
    <div><b>2) 시공 명리 풀이:</b> (※ 🚨체운=대운, 용운=세운 적용하여 간략 요약)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 올해 세운 전반기 상세 분석 ({sewun_first_half_date})</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> (상세 작성)</div>
    <div><b>2) 시공 명리 풀이:</b> (※ 🚨 위 '세운 팩트'의 '도출 키워드'를 기반으로 상세 통변)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 올해 세운 후반기 상세 분석 ({sewun_second_half_date})</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> (상세 작성)</div>
    <div><b>2) 시공 명리 풀이:</b> (※ 🚨 위 '세운 팩트'의 '도출 키워드'를 기반으로 상세 통변)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 월운의 흐름</span>
[WOLWUN_TABLE_HERE]
(※ 🚨AI 절대 지시: 위의 마커 '[WOLWUN_TABLE_HERE]'를 절대 지우거나 생략하지 말고, 반드시 텍스트 그대로 100% 똑같이 출력하십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▷ 지나온 과거 각 월운 분석</span>
{past_months_html}
(※ 🚨AI 절대 지시: 제공된 텍스트 그대로 100% 복사 출력. 들여쓰기 절대 금지.)
[지나온 과거 각 월운 출력 템플릿]
• <b>(파이썬이 제공한 월과 간지): (파이썬이 제공한 연도/날짜/절기 복사)</b> 
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> (핵심 요약)</div>
    <div><b>2) 시공 명리 풀이:</b> (※ 🚨체운=세운, 용운=월운 하향 전이 적용하여 간략 요약)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>{prompt_first_half}</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> (상세 작성)</div>
    <div><b>2) 시공 명리 풀이:</b> (※ 🚨체운=세운, 용운=월운 하향 전이 적용하여 상세 풀이)</div>
</div>

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>{prompt_second_half}</span>
<div style='padding-left: 20px; margin-top: 5px;'>
    <div style='margin-bottom: 5px;'><b>1) 전통 명리 풀이:</b> (상세 작성)</div>
    <div><b>2) 시공 명리 풀이:</b> (※ 🚨체운=세운, 용운=월운 하향 전이 적용하여 상세 풀이)</div>
</div>
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>12. 삶을 바꾸는 지혜로운 조언</h3>
<div class='content-box-loose'>
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 나를 돕는 에너지와 색상:</span>
(작성)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 신체 밸런스와 에너지 관리:</span>
(작성)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 공간의 흐름과 방위의 지혜:</span>
(작성)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 재능 효율을 높이는 직업적 지혜:</span>
(작성)
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 더 나은 내일을 위한 절제의 미학:</span>
(작성)
</div>

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'> 🎯 초연 시공명리 특별 개운 비법</h3>
<div class='content-box-loose'>
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 수호 천사의 기운 조언:</span>
(※ 🚨AI 지시: 사주원국 및 운(시간)의 흐름에 따른 천을귀인과 길신 등의 작용에 대한 상세한 에세이를 작성하시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 백년해로의 기운 조언:</span>
(※ 🚨AI 지시: 오행의 치우침, 원진, 고란살, 고신(남명), 과숙(여명) 등 이성 관계에 영향을 미치는 사주원국 및 운의 흐름을 분석하되, 전문 용어는 철저히 숨기십시오. 
이곳에서는 오직 '부부 및 연인 관계에서 발생할 수 있는 성격적/상황적 갈등 요소'와 이를 슬기롭게 극복하고 백년해로하기 위한 '실질적이고 따뜻한 개운 비법(마음가짐, 소통 방식, 행동 요령 등)'에만 100% 초점을 맞추어 카운슬러의 어조로 작성하십시오.)

<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>◈ 행운에 따른 기운 조언:</span>
(※ AI 지시: 운의 흐름에 따른 합형충파해와 진술축미의 입고와 개고, 도화(연살)/망신/역마살 작용에 따른 역동성과 재물과 대인관계 등 주의할 점에 대한 상세한 에세이를 작성하시오.)
</div>
"""
                try:
                    ai_text = call_gemini_api(prompt)
                    ai_text = "\n".join([line.lstrip() for line in ai_text.split("\n")])
                    
                    div_start = "<div class='content-box-loose'>"
                    target_sub = "1) 내 삶의 무대와 타고난 기본 성향"
                    
                    if target_sub in ai_text and div_start in ai_text:
                        parts = ai_text.split(target_sub)
                        top_clean = parts[0][:parts[0].find(div_start) + len(div_start)]
                        ai_text = top_clean + f"\n{choyeon_golden_text}\n<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>{target_sub}" + parts[1]
                    elif "[CHOYEON_GOLDEN_TEXT_HERE]" in ai_text:
                        ai_text = ai_text.replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)

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

                    if count_d == 0 and "table" not in clean_ai_text.lower():
                        clean_ai_text = clean_ai_text + f"<br><br><span style='color:red; font-weight:bold;'>⚠️ (AI 표 마커 누락으로 비상 출력된 운의 흐름표)</span><br>{un_html_clean}{se_html_clean}{wol_html_clean}"

                    full_content_clean = f"<div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #000000;'>{clean_ai_text}<br><br>{closing_html}</div>"

                    report_1_full_html = report_1_full_html.replace("{full_content_clean_placeholder}", full_content_clean)
                    st.session_state['saved_report_html'] = report_1_full_html
                    
                except Exception as e: 
                    st.error(f"AI 연산 오류: {e}")

            # ------------------------------------------------------------------
            # [2단계] 타 감명서 비교분석
            # ------------------------------------------------------------------
            if u_product == "타 감명서":
                try:
                    report_2_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#555;'><h2 style='text-align:center; color:#555; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; margin-bottom:20px;'>📜 타 감명서 원문</h2><div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #111; text-align: justify; word-break: keep-all;'>{other_reading_text.replace(chr(10), '<br>')}</div></div></div>"

                    other_cover_html = (
                        f"<div class='page-break-before'></div>\n"
                        f"<div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>\n"
                        f"    <div style='border: 4px solid #2E7D32; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>\n"
                        f"        <div style='border-bottom:4px double #2E7D32; padding-bottom:20px; margin-bottom:40px;'>\n"
                        f"            <h1 style='font-size: 40px !important; color: #1A237E !important; font-weight: 900 !important; margin:0 !important; font-family: \"Malgun Gothic\", sans-serif !important;'>초연 시공명리 타 감명서 비교</h1>\n"
                        f"            <div style='text-align: right; margin-top: 10px;'><span style='font-size: 14px; color: #555; font-weight: 600; letter-spacing: 1px;'>{APP_VERSION}</span></div>\n"
                        f"        </div>\n"
                        f"        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 30px 20px; border-radius: 15px;'>\n"
                        f"            <h2 style='font-size: 24px; font-weight: 800; color: #2E7D32; margin-bottom: 20px;'>👤 신청인 : {u_name} 님</h2>\n"
                        f"            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'><p style='margin: 0; white-space: nowrap;'>[양력] {sol_str} | [음력] {lun_str}</p></div>\n"
                        f"        </div>\n"
                        f"        <p style='font-size: 18px; margin-top: 50px; font-weight: 800;'>{today_str}</p>\n"
                        f"        <p style='font-size: 22px; font-weight: 800; color: #2E7D32; margin-top: 20px;'>초연 시공명리 연구소</p>\n"
                        f"    </div>\n"
                        f"</div>"
                    )

                    comp_prompt = f"""
    당신은 명리심리상담사 '초연 박사'를 보조하는 수석 분석관입니다.
    아래 [데이터]를 바탕으로 [초연 사주풀이]와 [타 감명서]를 1:1 대조 분석하십시오.

    🚨 [디자인 및 서식 절대 규칙]
    0. 🚨 [인사말 원천 차단]: 출력의 첫 글자는 반드시 <h3 style=...> 태그로 시작할 것.
    1. AI 임의의 목차 서식 생성을 절대 금지합니다.
    2. 목차 제목 출력 시, 반드시 명시된 태그 서식을 그대로 출력하십시오.
    3. 모든 본문 단락은 <p style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'> 로 감싸십시오.

    🚨 [내용 집중 대조 규칙]
    - 각 비교 항목의 도입부에는 반드시 [타 감명서 관점] vs [초연 시공명리 관점]을 1줄 요약으로 먼저 제시하십시오.
    - 타 감명서 원문이 다루고 있는 핵심 주제에 대해서만 초연 명리와 1:1 대조하십시오.
    - 🚨 [13번 총평 작성 지침]: 본문 분석과 별개로 반드시 500자 이상의 분량을 확보하여, 두 해석의 차이 발생 원인(정보 인지 여부, 해석 관점의 차이)을 명확히 규명하고 향후 초연 명리가 취해야 할 통변 전략을 제시하십시오.

    [데이터]
    - 사주 팩트: {gans}{jjis}
    - [1. 초연 사주풀이]: {full_content_clean}
    - [2. 타 감명서]: {other_reading_text}
    """
                    c_res = get_ai_response(comp_prompt, model_name='gemini-2.5-flash')
                    st.session_state['saved_report_2'] = other_cover_html + report_2_html + f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#2E7D32;'><h1 style='text-align:center; color:#2E7D32; font-size: 26px; font-weight: 800; border-bottom:2px solid #2E7D32; padding-bottom:15px;'>⚖️ 1:1 상세비교 본문 리포트</h1><div style='margin-top:20px;'>{c_res}</div></div></div>"

                except Exception as e:
                    st.error(f"2단계 비교 분석 중 오류 발생: {e}")

            # ------------------------------------------------------------------
            # [2.5 단계] 궁합 타 감명서 비교분석 (선택적 가동 모듈)
            # ------------------------------------------------------------------
            if u_product == "궁합" and st.session_state.get('run_comp_mode'):
                try:
                    comp_prompt = f"""
    당신은 명리심리상담사 '초연 박사'를 보조하는 수석 분석관입니다.
    [1. 초연 궁합 분석]과 [2. 타 감명서]를 1:1 대조 분석하십시오.
    
    [데이터]
    - 신청인(명주1) 사주: {full_content_clean}
    - 상대방(명주2) 사주: {partner_content_clean}
    - 타 감명서 원문: {st.session_state.get('other_reading_text')}
    """
                    c_res = get_ai_response(comp_prompt, model_name='gemini-2.5-flash')
                    st.session_state['saved_report_gh_comp'] = f"<div class='report-page'><div class='vip-inset-frame' style='border-color:#2E7D32;'><h1 style='text-align:center;'>⚖️ 궁합 1:1 상세비교 리포트</h1>{c_res}</div></div>"
                except Exception as e:
                    st.error(f"궁합 비교 분석 중 오류: {e}")

            # ==================================================================
            # 💕 [3단계] 궁합 풀이
            # ==================================================================
            if u_product == "궁합":
                try:
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
                    st.session_state['partner_bazi'] = partner_bazi # 🚨 출산택일 연산을 위해 영구 저장

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

                    curr_j = JI[((curr_y - 1984) % 60) % 12]

                    def get_counts(t_gans, t_jjis):
                        c = {"목":0,"화":0,"토":0,"금":0,"수":0}
                        for x in t_gans + t_jjis:
                            if x != "?": c[get_color(x)] += 1
                        return c

                    m_cnt, f_cnt = get_counts(m_gans, m_jjis), get_counts(f_gans, f_jjis)

                    m_name = m_name.replace("+", "").strip()
                    f_name = f_name.replace("+", "").strip()

                    def build_bazi_table(gender_icon, name, gender_str, marital_str, age, sol, lun, time, t_gans, t_jjis, t_ds, t_yb, counts, guiin, y_gong, d_gong, samjae, daeun_su, color):
                        ji_rel_rows = ""
                        for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                            b_bot = "1px solid #444 !important" if l_idx == 3 else "none !important"
                            cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(t_jjis[r_idx], t_jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:none !important; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+t_jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(t_jjis[r_idx], t_jjis[ci]))}</td>" for ci in range(4)])
                            lbl = f"<td rowspan='4' class='header-cell-main' style='border:1px solid #444 !important;'>합충형파해</td>" if l_idx==0 else ""
                            ji_rel_rows += f"<tr>{lbl}{cells}</tr>"

                        info_str = f"<div style='text-align:center; margin-bottom:15px; font-family:\"Malgun Gothic\", sans-serif;'><span style='font-size:18px; font-weight:900; color:#1A237E;'>{gender_icon} {name}님 ({gender_str}, {marital_str}, {age}세)</span><br><span style='font-size:14px; font-weight:900; color:#222;'>[양력] {sol} | [음력] {lun}{time}</span></div>"
                        
                        def td(c):
                            bg_style = "background-color: white;" if c in ['?',' ','-'] else ""
                            return f"<td class='color-{get_color(c)}' style='{bg_style} font-size:20px; font-weight:900; border:1px solid #444 !important;'>{('?' if c in ['?',' ','-'] else c)}</td>"

                        return (
                            f"{info_str}\n"
                            f"<table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>\n"
                            f"<tr class='top-header-cell'>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>구분</td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>시주</td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>일주</td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>월주</td>\n"
                            f"<td style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>년주</td>\n"
                            f"</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_gans[0])}</td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(t_ds,t_gans[2])}</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_gans[3])}</td></tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>천간</td>{td(t_gans[0])}{td(t_gans[1])}{td(t_gans[2])}{td(t_gans[3])}</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>지지</td>{td(t_jjis[0])}{td(t_jjis[1])}{td(t_jjis[2])}{td(t_jjis[3])}</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_jjis[0])}</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_jjis[1])}</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_jjis[2])}</td><td style='border:1px solid #444;'>{get_ss(t_ds,t_jjis[3])}</td></tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; padding:0; font-size:15px !important; white-space:nowrap;'>지장간</td>{''.join([f'<td style=\"border:1px solid #444; padding:0;\">{get_jijanggan_full(t_ds, t_jjis[i])}</td>' for i in range(4)])}</tr>\n"
                            f"{ji_rel_rows}\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>십이운성</td>{''.join([f'<td style=\"border:1px solid #444; color:#0D47A1; font-weight:bold;\">{get_unsung(t_ds, t_jjis[i])}</td>' for i in range(4)])}</tr>\n"
                            f"<tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; white-space:nowrap;'>십이신살</td>{''.join([f'<td style=\"border:1px solid #444; color:#C62828; font-weight:bold;\">{get_12_shinsal(t_yb, t_jjis[i])}</td>' for i in range(4)])}</tr>\n"
                            f"</table>\n"
                            f"<div style='border:2px solid {color}; margin-top:10px; margin-bottom:20px; padding:6px 8px; display:flex; justify-content:space-between; align-items:center; font-weight:900; font-size:11px; letter-spacing:-0.5px; border-radius:8px; background-color:#FAFAFA;'><div style='white-space:nowrap;'>🔢 대운수: {daeun_su}</div><div style='white-space:nowrap;'>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div style='white-space:nowrap;'>🌟 천을귀인: <span style='color:{color};'>{guiin}</span></div><div style='white-space:nowrap;'>🎯 공망: [년] <span style='color:#C62828;'>{y_gong}</span> [일] <span style='color:#C62828;'>{d_gong}</span></div><div style='white-space:nowrap;'>🌪️ 삼재: {samjae}</div></div>"
                        )

                    m_marital = u_marital if u_gender == "남성" else p_marital
                    f_marital = p_marital if u_gender == "남성" else u_marital
                    
                    guiin_map = {'甲':'丑, 未','乙':'子, 申','丙':'酉, 亥','丁':'酉, 亥','戊':'丑, 未','己':'子, 申','庚':'丑, 단','辛':'寅, 午','壬':'卯, 巳','癸':'卯, 巳'}
                    
                    m_tbl = build_bazi_table("♂️", m_name, "남명", m_marital, m_age, m_sol, m_lun, m_time, m_gans, m_jjis, m_ds, m_yb, m_cnt, guiin_map.get(m_ds, '-'), calculate_gongmang(m_ys, m_yb), calculate_gongmang(m_ds, m_db), get_samjae(m_yb, curr_j), m_calc_d, "#1A237E")
                    f_tbl = build_bazi_table("♀️", f_name, "여명", f_marital, f_age, f_sol, f_lun, f_time, f_gans, f_jjis, f_ds, f_yb, f_cnt, guiin_map.get(f_ds, '-'), calculate_gongmang(f_ys, f_yb), calculate_gongmang(f_ds, f_db), get_samjae(f_yb, curr_j), f_calc_d, "#D50000")
                    
                    def build_daewun_html(name, t_ds, t_ms, t_mb, t_yb, t_calc_d, t_order, age, color):
                        d_str = "순행" if t_order == 1 else "역행"
                        html = f"<div style='margin-bottom:10px;'><div style='font-size:15px; font-weight:900; color:#1A237E; margin-bottom:5px;'>[ {name}님 대운 흐름표 (대운수: {t_calc_d}), {d_str} ]</div>"
                        html += f"<div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white;'>"
                        for i in range(10):
                            val = i*10 + t_calc_d
                            tc = GAN[(GAN.index(t_ms)+(i+1)*t_order)%10]
                            tj = JI[(JI.index(t_mb)+(i+1)*t_order)%12]
                            bg = "#FFF9C4" if val <= age < val+10 else "transparent"
                            brd = "1px solid #ccc" if i != 9 else "none"
                            html += f"<div style='flex:1; border-left:{brd}; text-align:center; padding-bottom:3px; background-color:{bg};'><div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:11px; border-bottom:1px solid #ccc;'>{val}세</div><div style='padding:2px; font-size:11px;'>{get_ss(t_ds,tc)}</div><div class='color-{get_color(tc)}' style='font-size:15px; font-weight:900;'>{tc}</div><div class='color-{get_color(tj)}' style='font-size:15px; font-weight:900;'>{tj}</div><div style='padding:2px; font-size:11px;'>{get_ss(t_ds,tj)}</div><div style='font-size:10px; border-top:1px solid #eee;'>{get_unsung(t_ds,tj)}</div><div style='font-size:10px; color:#C62828; border-top:1px solid #eee;'>{get_12_shinsal(t_yb, tj)}</div></div>"
                        return html + "</div></div>"

                    m_page_un_html = build_daewun_html(m_name, m_ds, m_ms, m_mb, m_yb, m_calc_d, m_order, m_age, "#1A237E")
                    f_page_un_html = build_daewun_html(f_name, f_ds, f_ms, f_mb, f_yb, f_calc_d, f_order, f_age, "#1A237E")
                    
                    couple_daewun_tables = f"<div style='margin-bottom: 25px;'>{m_page_un_html}<div style='height:20px;'></div>{f_page_un_html}</div>"

                    m_w_val = choyeon_db.get("wolryeong", {}).get(m_ms+m_mb, "시공간 데이터 없음")
                    m_i_val = choyeon_db.get("ilju", {}).get(m_ds+m_db, "성품 데이터 없음")
                    # 🚨 [수술 적용 1] 골든 텍스트 여백을 개인사주와 동일하게 세팅
                    m_golden = f"<p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'><b>{m_name}님</b>은 '{m_w_val}'의 시공간에서, '{m_i_val}'의 성품을 지녔습니다.</p>"

                    f_w_val = choyeon_db.get("wolryeong", {}).get(f_ms+f_mb, "시공간 데이터 없음")
                    f_i_val = choyeon_db.get("ilju", {}).get(f_ds+f_db, "성품 데이터 없음")
                    f_golden = f"<p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'><b>{f_name}님</b>은 '{f_w_val}'의 시공간에서, '{f_i_val}'의 성품을 지녔습니다.</p>"
                    
                    gh_engine = UniversalPrintableGunghap(u_name, p_name, male_data_pack, female_data_pack, 10)
                    gh_engine.run_universal_logic()
                    
                    # 🚨 [수술 적용 2] 프롬프트 문단 간격 절대 강제 및 궁합 종합 분석 Deep Dive
                    essay_prompt = f"""[SYSTEM ROLE: CHOYEON SIGONG MASTER]
당신은 명리심리상담사 '초연 박사'입니다.

🚨 [출력 절대 형식 및 내용 생성 규칙 - 매우 중요!]
1. 각 소제목 아래에 절대로 '(축약 에세이)', '(에세이)' 등의 안내 문구를 그대로 복사해서 출력하지 마십시오!
2. 반드시 내담자의 명리적 특징을 분석하여 3~4문장 이상의 **실제 심층 통변 내용(해석)**을 직접 글로 작성해야 합니다.
3. 🚨 [문단 간격 강제]: 모든 통변 문단은 반드시 HTML 태그 `<p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'>` 로 감싸서 개인사주 풀이와 완벽히 동일한 쫀쫀한 문단 간격을 유지하십시오. 단순 `<br>`이나 탭(Tab) 사용을 금지합니다.

[MALE_START]
<h3 style='color:#1A237E; font-size: 24px; font-weight: 900; margin-top: 15px;'>1. 사주팔자의 요약</h3>
{m_golden}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(이곳에 남성의 명리적 성향을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>
(이곳에 남성의 오행 및 조후 에너지를 분석한 실제 에세이 작성)

<h3 style='color:#1A237E; font-size: 24px; font-weight: 900; margin-top: 35px;'>2. 성격 및 가치관</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
(이곳에 남성의 사회적 표면 성격을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>
(이곳에 남성의 내면과 무의식을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>3) 무의식이 갈망하는 반려자의 상</span>
(일지의 십성과 십이운성, 지장간의 포태법을 바탕으로 육친적, 심리적, 사회적 관점을 살려 남성의 연애 및 결혼관을 실제 에세이로 작성)
[MALE_END]

[FEMALE_START]
<h3 style='color:#D50000; font-size: 24px; font-weight: 900; margin-top: 15px;'>1. 사주팔자의 요약</h3>
{f_golden}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(이곳에 여성의 명리적 성향을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>
(이곳에 여성의 오행 및 조후 에너지를 분석한 실제 에세이 작성)

<h3 style='color:#D50000; font-size: 24px; font-weight: 900; margin-top: 35px;'>2. 성격 및 가치관</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
(이곳에 여성의 사회적 표면 성격을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>
(이곳에 여성의 내면과 무의식을 분석한 실제 에세이 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>3) 무의식이 갈망하는 반려자의 상</span>
(일지의 십성과 십이운성, 지장간의 포태법을 바탕으로 육친적, 심리적, 사회적 관점을 살려 여성의 연애 및 결혼관을 실제 에세이로 작성)
[FEMALE_END]

[GUNGHAP_START]
<h3 style='color: #1B5E20; font-size: 24px; font-weight: 900; margin-top: 10px;'>🍀 두 사람의 운명적 만남 총평</h3>
(두 사람의 사주 기운이 만나 형성하는 큰 틀의 인연, 만남의 의미와 전반적인 궁합 총평을 깊이 있게 통변한 실제 에세이 작성)

<h3 style='color: #1A237E; font-size: 24px; font-weight: 900; margin-top: 35px;'>🌈 커플의 인생 기상도 및 대운 교차 분석</h3>
[COUPLE_DAEWUN_TABLES_HERE]
(상하 대운표를 바탕으로, 두 사람의 운의 흐름이 어떤 시기에 서로 보완되고 상생하는지, 혹은 주의가 필요한지 교차 분석한 실제 에세이 작성)

<h3 style='color: #1A237E; font-size: 24px; font-weight: 900; margin-top: 35px;'>💞 초연 시공명리 심층 조화 분석</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 오행 및 조후의 상생 조화</span>
(서로의 사주에서 부족하거나 넘치는 기운(온습 및 오행)을 어떻게 채워주고 완충하는지 구체적으로 명시하여 작성)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 심리 및 가치관의 결속력</span>
(남명과 여명의 성격적/육친적 십성 구조가 현실 생활(의사소통, 재물관, 자녀관 등)에서 어떻게 융합되거나 부딪히는지 분석)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>3) 내면의 깊은 유대감 (속궁합)</span>
(일지(배우자궁)와 지장간의 합형충파해를 기반으로 한 육체적, 내적 유대감 및 은밀한 성향적 조화를 품격있게 풀이)

<h3 style='color: #D50000; font-size: 24px; font-weight: 900; margin-top: 35px;'>⚓ 백년해로를 위한 조율의 지혜</h3>
(단순한 조언을 넘어, 부부/연인 관계에서 필연적으로 겪게 될 위기 상황을 짚어주고, 이를 극복하기 위한 마음가짐, 소통 방식, 행동 지침 등 실질적인 타개책을 3문단 이상의 깊이 있는 에세이로 작성)
[GUNGHAP_END]
"""
                    res_text = call_gemini_api(essay_prompt, max_tokens=12000)
                    ai_clean = "\n".join([line.lstrip() for line in res_text.split("\n")])
                    
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
                    
                    g_ess, count = re.subn(r'\[\s*COUPLE_DAEWUN_TABLES_HERE\s*\]', couple_daewun_tables, g_ess, flags=re.IGNORECASE)
                    if count == 0:  
                        g_ess = re.sub(r'(<h3[^>]*>🌈 커플의 인생 기상도 분석</h3>)', r'\1\n<div style="margin-top:15px;">' + couple_daewun_tables + '</div>', g_ess)

                    def wrap_a4(content, title_color="#1A237E", title=f"[ 초연 시공명리 사주풀이 {APP_VERSION} ]"):  
                        return (
                            f"<div class='report-page'>\n"
                            f"<div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'>\n"
                            f"<h1 style='text-align:center; color:{title_color}; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; border-bottom:2px solid {title_color}; padding-bottom:15px; margin-bottom:30px;'>{title}</h1>\n"
                            f"{content}\n"
                            f"</div>\n"
                            f"</div>"
                        )

                    t_col = "#3498db" if gh_engine.final_score >= 70 else ("#f39c12" if gh_engine.final_score >= 60 else "#e74c3c")
                    bars = "".join([f"<div style='display:flex; align-items:center; margin-bottom:12px;'><div style='width:130px; font-size:13px; font-weight:bold; color:#555;'>{d['label']}</div><div style='flex:1; height:12px; margin:0 10px;'><svg width='100%' height='12'><rect width='100%' height='12' rx='6' ry='6' fill='#eee' /><rect width='{d['pct']}%' height='12' rx='6' ry='6' fill='{d['color']}' /></svg></div><div style='width:35px; font-size:12px; font-weight:bold;'>{d['pct']}%</div></div>" for d in gh_engine.details])
                    
                    closing_original = (
                        f"<div style='margin-top: 40px; padding-top: 30px; page-break-inside: avoid;'>\n"
                        f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333;'>&nbsp;&nbsp;&nbsp;&nbsp;두 분의 <b style='color:#1A237E;'>'만남'</b>은 결코 우연이 아닌, <b style='color:#1A237E;'>'셀 수 없이 많은 시간 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 바코드지만, <b style='color:#1A237E;'>'궁합(宮合)'</b>은 두 바코드가 만나 그려내는 새로운 <b style='color:#1A237E;'>'하모니(harmonie)'</b>입니다.</p>\n"
                        f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #333; margin-top: 10px;'>&nbsp;&nbsp;&nbsp;&nbsp;서로의 다름을 이해하고 채워주는 든든한 <b style='color:#1A237E;'>'동반자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 시공간의 축복이 가득하시길 소망합니다. </p>\n"
                        f"<div style='text-align: right; margin-top: 25px;'><span style='font-weight: 900; font-size: 16px; color: #1A237E; font-family: \"Nanum Myeongjo\", serif;'>- 초연 시공명리 연구소 드림 -</span></div>\n"
                        f"</div>"
                    )

                    g_full_content = (
                        f"<div class='choyeon-premium-report'>\n{g_ess}\n</div>\n"
                        f"<h2 style='text-align:center; margin-top:40px; font-size:22px; font-weight:900;'>📊 최종 궁합 점수</h2>\n"
                        f"<div style='display:flex; justify-content:center; align-items:center; margin:20px 0;'>\n"
                        f"<div style='width:130px; height:130px; border-radius:50%; background:conic-gradient({t_col} {gh_engine.final_score}%, #eee 0); display:flex; justify-content:center; align-items:center; -webkit-print-color-adjust: exact;'>\n"
                        f"<div style='width:98px; height:98px; background:#fff; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center;'>\n"
                        f"<span style='font-size:32px; font-weight:900; color:{t_col};'>{gh_engine.final_score}</span>\n"
                        f"<span style='font-size:10px; color:#888; font-weight:bold;'>SCORE</span>\n"
                        f"</div>\n"
                        f"</div>\n"
                        f"</div>\n"
                        f"<div style='text-align:center; margin-bottom:20px;'><span style='font-size:16px; font-weight:bold; color:#fff; background:{t_col}; padding:8px 32px; border-radius:30px; -webkit-print-color-adjust: exact;'>{gh_engine.grade}</span></div>\n"
                        f"<div style='max-width:500px; margin:0 auto;'>\n{bars}\n</div>\n"
                        f"{closing_original}"
                    )

                    cover_html = (
                        f"<div class='report-page cover-page' style='padding:0; margin:0; width:100%; height:297mm; display:flex; flex-direction:column; justify-content:center; align-items:center; page-break-after: always; -webkit-print-color-adjust: exact;'>\n"
                        f"    <div style='border: 4px solid #1A237E; padding: 50px 30px; border-radius: 20px; text-align: center; background: white; width: 80%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin: auto;'>\n"
                        f"        <div style='border-bottom:4px double #1A237E; padding-bottom:20px; margin-bottom:40px;'>\n"
                        f"            <h1 class='title-gothic' style='font-size: 40px !important; margin:0 !important;'>초연 시공명리 궁합풀이</h1>\n"
                        f"            <div style='text-align: right; margin-top: 10px;'>\n"
                        f"                <span class='ver-gothic' style='font-size: 14px; letter-spacing: 1px;'>{APP_VERSION}</span>\n"
                        f"            </div>\n"
                        f"        </div>\n"
                        f"        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 15px; margin-bottom: 20px;'>\n"
                        f"            <h2 style='font-size: 24px; font-weight: 800; color: #1A237E; margin-bottom: 15px;'>♂️ 남명 : {m_name} 님 <span style='font-size:16px; color:#555;'>( {m_age}세 )</span></h2>\n"
                        f"            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>\n"
                        f"                <p style='margin: 0; white-space: nowrap;'>[양력] {m_sol} | [음력] {m_lun}</p>\n"
                        f"            </div>\n"
                        f"        </div>\n"
                        f"        <div style='background:#F8F9FA; border: 1px solid #E8EAF6; padding: 25px 20px; border-radius: 15px;'>\n"
                        f"            <h2 style='font-size: 24px; font-weight: 800; color: #D50000; margin-bottom: 15px;'>♀️ 여명 : {f_name} 님 <span style='font-size:16px; color:#555;'>( {f_age}세 )</span></h2>\n"
                        f"            <div style='font-size: 15px; font-weight: 600; color: #555; line-height: 1.8;'>\n"
                        f"                <p style='margin: 0; white-space: nowrap;'>[양력] {f_sol} | [음력] {f_lun}</p>\n"
                        f"            </div>\n"
                        f"        </div>\n"
                        f"        <p style='font-size: 18px; margin-top: 40px; font-weight: 800;'>{today_str}</p>\n"
                        f"        <p style='font-size: 22px; font-weight: 800; color: #1A237E; margin-top: 15px;'>초연 시공명리 연구소</p>\n"
                        f"    </div>\n"
                        f"</div>"
                    )
                    st.session_state['saved_report_gh_cover'] = cover_html

                    m_page_content = f"{m_tbl}\n<div class='choyeon-premium-report' style='margin-top:20px;'>\n{m_ess}\n</div>"
                    f_page_content = f"{f_tbl}\n<div class='choyeon-premium-report' style='margin-top:20px;'>\n{f_ess}\n</div>"
                    
                    st.session_state['saved_report_gh_m'] = wrap_a4(m_page_content, "#1A237E", "[ 남명 사주팔자표 및 요약 ]")
                    st.session_state['saved_report_gh_f'] = wrap_a4(f_page_content, "#D50000", "[ 여명 사주팔자표 및 요약 ]")
                    st.session_state['saved_report_gh_g'] = wrap_a4(g_full_content, "#1B5E20", "[ 초연 시공명리 종합 궁합풀이 ]")
                    
                except Exception as e:
                    st.error(f"3단계 궁합 종합 분석 가동 장애: {e}")

            # 🚨 연산 종료 (스위치 끄기)
            st.session_state['need_calc'] = False

        except Exception as e: 
            st.error(f"시스템 연산 중 치명적 오류 발생: {e}")
            st.session_state['need_calc'] = False
            st.stop()

# ==============================================================================
# 🌊 7. [독립 모듈] 일진 시공간 분석 (결과 출력부)
# ==============================================================================
import datetime as dt_mod

if st.session_state.get('app_running', False) and st.session_state.get('run_waterfall', False) and 'global_gans' in st.session_state:
    
    if not st.session_state.get('saved_report_iljin'):
        if st.session_state.get('saved_report_html'):
            st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
            
        t_date = st.session_state['target_date']
        
        gans_list = st.session_state['global_gans']
        jjis_list = st.session_state['global_jjis']
        m_ilgan = st.session_state['global_ds']
        m_ilji = st.session_state['global_db']
        
        # 🚨 [수술 1] 박사님 명조 정보 추출 (배열: [시, 일, 월, 년])
        local_curr_y = dt_mod.datetime.now().year
        local_u_age = local_curr_y - u_y + 1
        myongjo_str = f"명조: {gans_list[3]}{jjis_list[3]}년 {gans_list[2]}{jjis_list[2]}월 {gans_list[1]}{jjis_list[1]}일 {gans_list[0]}{jjis_list[0]}시 ({u_gender}, {local_u_age}세)"
        
        from korean_lunar_calendar import KoreanLunarCalendar
        dklc = KoreanLunarCalendar()
        dklc.setSolarDate(t_date.year, t_date.month, t_date.day)
        gj_str = dklc.getChineseGapJaString()
        
        if gj_str:
            parts = gj_str.split()
            target_year = parts[0][:2]
            target_wol = parts[1][:2]
            target_il_gan = parts[2][0]
            target_il_ji = parts[2][1] 
            
            def get_execution_yong(upper_group, lower_group):
                matrix = {'비겁': {'비겁':'비겁', '식상':'식상', '재성':'재성', '관성':'관성', '인성':'인성'}, '식상': {'비겁':'인성', '식상':'비겁', '재성':'식상', '관성':'재성', '인성':'관성'}, '재성': {'비겁':'관성', '식상':'인성', '재성':'비겁', '관성':'식상', '인성':'재성'}, '관성': {'비겁':'재성', '식상':'관성', '재성':'인성', '관성':'비겁', '인성':'식상'}, '인성': {'비겁':'식상', '식상':'재성', '재성':'관성', '관성':'인성', '인성':'비겁'} }
                return matrix.get(upper_group, {}).get(lower_group, '비겁')

            ilju_lower_group = get_group_ss(get_ss(m_ilgan, m_ilji))
            
            m_che_first = get_group_ss(get_ss(m_ilgan, target_wol[0]))
            d_gan_ss = get_group_ss(get_ss(m_ilgan, target_il_gan))  
            am_yong = get_execution_yong(d_gan_ss, ilju_lower_group)
            
            m_che_second = get_group_ss(get_ss(m_ilgan, target_wol[1]))
            d_ji_ss = get_group_ss(get_ss(m_ilgan, target_il_ji))    
            pm_yong = get_execution_yong(d_ji_ss, ilju_lower_group)

            gan_desc = {"합(合)": "생각과 뜻이 맞고 긍정적 결속력이 생기는 하루입니다.", "충(沖)": "정신적인 대립이나 스트레스가 발생할 수 있습니다.", "극(剋)": "상황을 통제하느라 피로감이 따를 수 있습니다."}
            gan_res = []
            labels_gan = ["시간", "일간", "월간", "년간"]
            for idx, label in enumerate(labels_gan):
                g1, g2 = gans_list[idx], target_il_gan
                if g1 not in ["?", "-", " "]:
                    s = {g1, g2}
                    rel = "-"
                    if s in [{'甲','己'}, {'乙','庚'}, {'丙','辛'}, {'丁','壬'}, {'戊','癸'}]: rel = "합(合)"
                    elif s in [{'甲','庚'}, {'乙','辛'}, {'丙','壬'}, {'丁','癸'}, {'戊','甲'}, {'己','乙'}]: rel = "충(沖)"
                    elif {'甲':'戊', '乙':'己', '丙':'庚', '丁':'辛', '戊':'壬', '己':'癸', '庚':'甲', '辛':'乙', '壬':'丙', '癸':'丁'}.get(g1) == g2 or {'甲':'戊', '乙':'己', '丙':'庚', '丁':'辛', '戊':'壬', '己':'癸', '庚':'甲', '辛':'乙', '壬':'丙', '癸':'丁'}.get(g2) == g1: rel = "극(剋)"
                    
                    if rel != "-":
                        gan_res.append(f"☁️ <b>{label}({g1})</b> → <span style='color:#1976D2; font-weight:bold;'>천간 {rel}</span> <span style='color:#555; font-size:13px;'>( {g1}{g2}{rel}하여 {gan_desc.get(rel, '영향 발생')} )</span>")

            # 🚨 [수술 1] 박사님 지시 반영: 지지 파동 구체적 서술 딕셔너리 추가
            ji_desc_map = {
                "육합": "일이 순조롭게 풀리고 화합하는 기운입니다.",
                "방합": "같은 목적을 가진 세력이 강하게 결집하는 기운입니다.",
                "반합": "새로운 국면으로 전환되거나 목적을 위해 협력하는 기운입니다.",
                "충": "역동적인 변동이나 충돌, 혹은 이동수가 발생하기 쉽습니다.",
                "형": "의견 조율 과정에서 시비나 조정, 수술수 등의 변동이 따릅니다.",
                "원진": "사소한 오해나 심리적인 갈등, 원망이 생길 수 있으니 주의하십시오.",
                "귀문": "신경이 예민해지고 직관력이 극대화되는 묘한 기운입니다.",
                "파": "기존의 틀이나 약속이 깨지고 새로운 것을 모색하게 되는 기운입니다.",
                "해": "예상치 못한 방해나 심리적 섭섭함이 발생할 수 있습니다.",
                "암합": "보이지 않는 곳에서 은밀하게 뜻이 맞고 결속되는 기운입니다."
            }

            r_res = []
            labels_ji = ["시지", "일지", "월지", "년지"]
            for idx, label in enumerate(labels_ji):
                j1 = jjis_list[idx]
                rel_full = get_ji_rel_set(j1, target_il_ji) 
                if rel_full != "-":
                    main_rel = rel_full.split(',')[0].strip()
                    desc_text = ji_desc_map.get(main_rel, "미세한 환경적 파동과 변화가 감지됩니다.")
                    r_res.append(f"🌊 <b>{label}({j1})</b> → <span style='color:#D50000; font-weight:bold;'>{rel_full}</span> <span style='color:#555; font-size:13px;'>( {j1}{target_il_ji} {main_rel}하여 {desc_text} )</span>")

            gan_res_html = '<br>'.join(gan_res) if gan_res else '특이 천간 파동 없음'
            r_res_html = '<br>'.join(r_res) if r_res else '특이 지지 파동 없음'

            day_wunseong = get_unsung(m_ilgan, target_il_ji)
            day_12shinsal = get_12_shinsal(jjis_list[3], target_il_ji) 
            
            s_res_html = f"✨ <b>오늘의 핵심 에너지:</b> 십이운성[{day_wunseong}] / 12신살[{day_12shinsal}]"

            # 🚨 [수술 2] AI 환각 통제 및 시공명리(체용) 강제 프롬프트
            iljin_prompt = f"""
당신은 명리심리상담사 초연 박사입니다.
오늘의 시공간 파동을 바탕으로 핵심만을 간결하게 통변하십시오.

[핵심 팩트]
- 내담자: {m_ilgan}{m_ilji} / 일진: {t_date.month}월 {t_date.day}일
- 천간/지지 파동: {gan_res_html} / {r_res_html}
- 전반부 체용: {m_che_first}(무대) + {am_yong}(사건)
- 후반부 체용: {m_che_second}(무대) + {pm_yong}(사건)
- 오늘의 운성/신살: {day_wunseong} / {day_12shinsal}

🚨 [AI 통제 헌법]
1. 서론, 인사말, '연산 팩트' 등 기술적 문구 출력 절대 금지.
2. 마크다운 표 및 `**` 강조 기호 사용 절대 금지. 오직 HTML <b> 태그만 사용.
3. 🚨 가장 중요한 규칙: 감성적인 심리 묘사나 전통 명리적 통변을 철저히 배제하십시오! 오직 제공된 **[시공명리의 체(환경/무대)와 용(사건/행동)]**의 결합 원리만을 사용하여, 구체적이고 현실적인 **'사건과 실질적 결과'** 위주로 통변해야 합니다.

[출력 포맷]
<span style='font-size: 16px; font-weight: 900;'>▶ 오전(00:31~13:30):</span> [시공명리 체({m_che_first})+용({am_yong})]의 결합을 바탕으로 오전의 실제적인 업무/대인관계 사건을 1~2문장으로 직관적으로 통변.
<br><span style='font-size: 16px; font-weight: 900;'>▶ 오후(13:31~23:30):</span> [시공명리 체({m_che_second})+용({pm_yong})]의 결합을 바탕으로 오후의 실질적 사건 흐름을 1~2문장으로 통변.
<br><span style='font-size: 16px; font-weight: 900;'>✨ 오늘의 개운 조언:</span> 박사님의 일주와 오늘의 파동({day_wunseong}/{day_12shinsal})을 접목한 구체적이고 현실적인 행동 지침 1문장.
"""
            with st.spinner("⏳ 메인 사주풀이 보존 완료! 하단에 [일진 시공간 분석]을 추가 가동 중입니다..."):
                try:
                    ai_iljin_html = call_light_api(iljin_prompt).replace('\n', '<br>')
                except Exception as e:
                    ai_iljin_html = f"<div style='color:red; font-weight:bold; padding:10px;'>🚨 AI 일진 분석 장애: {e}</div>"

            # 🚨 [수술 3] 화면 출력부에 박사님 명조 정보 삽입
            html_output = (
                f"<div class='page-break-before'></div>\n"
                f"<div class='report-page'>\n"
                f"<div class='vip-inset-frame' style='border: 3px solid #1A237E;'>\n"
                f"<h1 style='text-align: center; color: #1A237E;'>🔮 일진 시공간 정밀 분석서</h1>\n"
                f"<div style='text-align: center; font-size: 16px; font-weight: bold; color: #555; margin-bottom: 20px;'>\n"
                f"{myongjo_str}<br>\n"
                f"대상일자: {t_date.year}년 {t_date.month}월 {t_date.day}일 ({target_year}년 {target_wol}월 {target_il_gan}{target_il_ji}일)\n"
                f"</div>\n"
                f"<div style='margin-bottom: 25px; background: #FFF8E1; padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6;'>\n"
                f"{gan_res_html}<br>{r_res_html}<br><br>{s_res_html}\n"
                f"</div>\n"
                f"<div class='content-box-loose' style='font-size: 15px; line-height: 1.8;'>\n"
                f"{ai_iljin_html}\n"
                f"</div>\n"
                f"</div>\n"
                f"</div>"
            )
            
            st.session_state['saved_report_iljin'] = html_output
            st.rerun()

# ==============================================================================
# 👶 8. [독립 모듈] 출산택일 정밀 분석
# ==============================================================================
if st.session_state.get('app_running', False) and st.session_state.get('run_delivery_only', False) and 'global_gans' in st.session_state:
    with st.spinner("⏳ [출산택일 분석실] 최적의 길일 연산 및 AI 통변 중... (기존 궁합풀이는 안전하게 보존 중입니다)"):
        try:
            gans = st.session_state.get('global_gans', ["?", "?", "?", "?"])
            jjis = st.session_state.get('global_jjis', ["?", "?", "?", "?"])
            p_bazi_context = st.session_state.get('partner_bazi', ["?", "?", "?", "?"])
            
            if u_gender == "남성":
                m_jjis, f_jjis = jjis, [b[1] if len(b)>1 else "?" for b in p_bazi_context]
                m_gans_str, f_gans_str = "".join(gans), "".join([b[0] if len(b)>0 else "?" for b in p_bazi_context])
            else:
                m_jjis, f_jjis = [b[1] if len(b)>1 else "?" for b in p_bazi_context], jjis
                m_gans_str, f_gans_str = "".join([b[0] if len(b)>0 else "?" for b in p_bazi_context]), "".join(gans)

            FORBIDDEN_LIST = ['병오', '임자', '계해', '신유', '경신']
            delivery_days = get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, FORBIDDEN_LIST)
            
            del_content = f"<h2 style='text-align:center;'>👶 새 생명 마중 길일 추천</h2>\n<p>부모님의 사주와 조화를 이루는 길일입니다.</p>\n"
            for day_info in delivery_days:
                del_content += f"<div>✅ {day_info['date']} (합 점수: {day_info['score']})</div>\n"
            
            del_content += f"<p style='line-height:1.8; color:#333; text-indent: 15px; margin-top: 15px; margin-bottom: 15px;'><span style='font-size:18px;'><b>💡 부부를 위한 임신 계획 가이드:</b>
</span><br><span style='font-size:15px;'>위의 출산 길일은 아이의 사주 기운을 우선으로 선정한 것입니다. 
의학적 평균 임신 기간(약 280일)을 고려할 때, <b>합궁 시기는 출산 예정일로부터 약 9개월 10일 전후</b>가 됩니다. 
부인분의 생리 주기와 배란일을 면밀히 고려하시어, 부부께서 상의하에 가장 건강한 시기를 계획하시길 바랍니다.</span></p>"
            
            delivery_prompt = f"""
당신은 명리심리상담사 및 출산택일 최고 권위자인 초연 박사입니다. 아래 부모의 사주 기운을 바탕으로, 태어날 아이의 선천적 명식과 부모간의 오행 상생 조화가 극대화되는 '최고의 프리미엄 출산 희망일 및 시간'을 선정하여 전통 명리 에세이로 풀어내십시오.

[부모의 사주 정보]
- 신청인: {u_gender} / 원국: {m_gans_str}{"".join(m_jjis)}
- 상대방: 원국 데이터: {f_gans_str}{"".join(f_jjis)}
- 탐색 지정 기간: {start_date} ~ {end_date} / 선호 태아 성별: {baby_gender}

🚨 [출력 절대 규칙]
선정된 상위 추천 일자별로 반드시 아래 규격화된 분리 통변 포맷을 100% 준수하여 작성하십시오.
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>▶ 추천 일자: OOOO년 OO월 OO일 (OO시)</span>
<br><b>1) 일반 명리 풀이:</b> (선정된 날짜와 시간의 오행 분포, 아이가 가질 선천적 격국의 강점 및 부모 사주와의 끈끈한 육친적 정서 조화 상태를 구어체로 상세 기술)
<br><b>2) 시공 명리 풀이:</b> (해당 시공간의 기운이 아이의 성장기 학업, 향후 성인이 되었을 때의 직업적/사회적 성취 및 자산 안정성에 미치는 장기적 운명의 궤도를 세련된 에세이로 기술)
"""
            ai_delivery_html = call_gemini_api(delivery_prompt)
                    
            # 🚨 [AI 환각 물리적 절단 (가위질)]
            # 1. '---' 마크다운 쓰레기 무조건 삭제
            ai_delivery_html = ai_delivery_html.replace('---', '')
            # 2. '▶ 추천 일자' 이전에 AI가 멋대로 떠든 인사말(존경하는 부모님께 등) 통째로 날림
            ai_delivery_html = re.sub(r'^.*?((?=<span class=\'sub-title\')|(?=▶))', '', ai_delivery_html, flags=re.DOTALL)
            # 3. '초연 박사 올림' 등 하단의 쓸데없는 맺음말 삭제
            ai_delivery_html = re.sub(r'존경하는 부모님.*|초연 박사 올림.*', '', ai_delivery_html, flags=re.DOTALL)
            # 4. 줄바꿈 제거하여 쫀쫀한 HTML 폼 유지
            ai_delivery_html = ai_delivery_html.replace('\n', '')

            del_content += f"<div class='content-box-loose' style='font-size:15px; line-height:1.8; margin-top:20px;'>\n{ai_delivery_html}\n</div>"

            def wrap_a4_del(content, title_color="#4A148C", title="초연 시공명리 출산택일"):
                return f"<div class='report-page'>\n<div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'>\n<div style='border-bottom:4px double {title_color}; padding-bottom:20px; margin-bottom:40px;'>\n<h1 style='text-align:center; font-size: 32px; color:{title_color}; font-weight: 900; margin:0; font-family:\"Malgun Gothic\", sans-serif;'>👶 {title}</h1>\n</div>\n{content}\n</div>\n</div>"

            st.session_state['saved_report_del'] = wrap_a4_del(del_content, "#4A148C", "초연 시공명리 출산택일")
            st.session_state['run_delivery_only'] = False
            st.rerun() 
            
        except Exception as e:
            st.error(f"출산택일 연산 장애: {e}")
            st.session_state['run_delivery_only'] = False

# ==============================================================================
# 9. 화면 출력부
# ==============================================================================
if st.session_state.get('app_running', False):
    
    # 1. 개인사주 출력
    if u_product == "개인사주":
        st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
        if st.session_state.get('saved_report_iljin'):
            st.markdown(st.session_state.get('saved_report_iljin', ''), unsafe_allow_html=True)
    
    # 2. 타 감명서 출력
    if u_product == "타 감명서":
        st.markdown(st.session_state.get('saved_report_html', ''), unsafe_allow_html=True)
        st.markdown(st.session_state.get('saved_report_2', ''), unsafe_allow_html=True)
        
    # 3. 궁합 출력
    if u_product == "궁합":
        # 3-1. 궁합 리포트 메인 출력
        if st.session_state.get('saved_report_gh_cover'):
            st.markdown(st.session_state.get('saved_report_gh_cover', ''), unsafe_allow_html=True)
            st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
            
        st.markdown(st.session_state.get('saved_report_gh_m', ''), unsafe_allow_html=True)
        st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
        st.markdown(st.session_state.get('saved_report_gh_f', ''), unsafe_allow_html=True)
        st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
        st.markdown(st.session_state.get('saved_report_gh_g', ''), unsafe_allow_html=True)

        # 3-2. 출산택일 연산 및 출력 (사이드바에서 택일 선택 시에만)
        if st.session_state.get('run_delivery_only', False) and start_date and end_date and not st.session_state.get('saved_report_del') and st.session_state.get('saved_report_gh_g'):
            
            # 박사님이 임시 설정하신 세션 관리 및 스피너 유지
            with st.spinner("⏳ 모래시계와 함께 출산택일 분석 중..."):
                try:
                    gans = st.session_state.get('global_gans', ["?", "?", "?", "?"])
                    jjis = st.session_state.get('global_jjis', ["?", "?", "?", "?"])
                    p_bazi_context = st.session_state.get('partner_bazi', ["?", "?", "?", "?"])
                    
                    if u_gender == "남성":
                        m_jjis = jjis
                        f_jjis = [b[1] if len(b)>1 else "?" for b in p_bazi_context]
                        m_gans_str = "".join(gans)
                        f_gans_str = "".join([b[0] if len(b)>0 else "?" for b in p_bazi_context])
                    else:
                        m_jjis = [b[1] if len(b)>1 else "?" for b in p_bazi_context]
                        f_jjis = jjis
                        m_gans_str = "".join([b[0] if len(b)>0 else "?" for b in p_bazi_context])
                        f_gans_str = "".join(gans)

                    H2K_MAP = {'甲':'갑','乙':'을','丙':'병','丁':'정','戊':'무','己':'기','庚':'경','辛':'신','壬':'임','癸':'계',
                               '子':'자','丑':'축','寅':'인','卯':'묘','辰':'진','巳':'사','午':'오','未':'미','申':'신','酉':'유','戌':'술','亥':'해'}
                    def h2k(text): return "".join([H2K_MAP.get(c, c) for c in text])
                    
                    m_saju_hanja = f"{m_gans_str[3]}{m_jjis[3]}년 {m_gans_str[2]}{m_jjis[2]}월 {m_gans_str[1]}{m_jjis[1]}일 {m_gans_str[0]}{m_jjis[0]}시"
                    f_saju_hanja = f"{f_gans_str[3]}{f_jjis[3]}년 {f_gans_str[2]}{f_jjis[2]}월 {f_gans_str[1]}{f_jjis[1]}일 {f_gans_str[0]}{f_jjis[0]}시"
                    m_saju_kor = h2k(m_saju_hanja)
                    f_saju_kor = h2k(f_saju_hanja)
                    m_ilgan_kor = h2k(m_gans_str[1])
                    f_ilgan_kor = h2k(f_gans_str[1])

                    del_content = f"<div style='border-bottom:4px double #4A148C; padding-bottom:15px; margin-bottom:30px;'><h1 style='text-align:center; font-size: 30px; color:#4A148C; font-weight: 900; margin:0; font-family:\"Malgun Gothic\", sans-serif;'>👶 초연 시공명리 출산택일</h1></div>\n"
                    del_content += f"<h2 style='text-align:center; color:#111; font-weight:900; font-size: 22px;'>👶 새 생명 마중 길일(출산 택일) 추천</h2>\n"
                    del_content += f"<p style='text-align:center; font-weight:bold; color:#4A148C; margin-bottom:15px;'>부모님의 사주와 조화를 이루는 합궁 길일입니다.</p>\n"
                    
                    FORBIDDEN_LIST = ['병오', '임자', '계해', '신유', '경신']
                    delivery_days = get_optimized_delivery_days(start_date, end_date, m_jjis, f_jjis, FORBIDDEN_LIST)
                    
                    # 🚨 [완전 동적 변경 1] 파이썬 연산기 결과에 연동된 날짜 및 한글 간지 자동 빌드
                    ai_target_days_facts = []
                    del_content += f"<div style='display:flex; flex-direction:column; align-items:center; margin-bottom:15px; background:#f9f9f9; padding:15px; border-radius:10px;'>\n"
                    if delivery_days:
                        f_d = dt_mod.datetime.strptime(delivery_days[0]['date'], '%Y-%m-%d')
                        l_d = dt_mod.datetime.strptime(delivery_days[-1]['date'], '%Y-%m-%d')
                        score = delivery_days[0]['score']
                        del_content += f"<div style='font-size:16px; font-weight:bold; margin-bottom:10px;'>✅ 합궁 추천 기간: {f_d.year}년 {f_d.month}월 {f_d.day}일 ~ {l_d.day}일 (합 점수: {score})</div>\n"
                        
                        for i in range(min(3, len(delivery_days))):
                            d_obj = dt_mod.datetime.strptime(delivery_days[i]['date'], '%Y-%m-%d')
                            birth_d = d_obj + dt_mod.timedelta(days=280) # 출산 예정일 계산
                            
                            b_ym, b_mm, _ = get_true_year_month_pillar(birth_d.year, birth_d.month, birth_d.day, 10, 30)
                            b_klc = KoreanLunarCalendar()
                            b_klc.setSolarDate(birth_d.year, birth_d.month, birth_d.day)
                            b_gj = b_klc.getChineseGapJaString().split()
                            b_ds, b_db = b_gj[2][0], b_gj[2][1]
                            b_hs, b_hb = get_time_ganji(b_ds, "09:30 ~ 11:29 (巳)시")
                            
                            # 한자 간지를 한글로 즉시 번역
                            full_bazi_kor = f"{h2k(b_ym)}년 {h2k(b_mm)}월 {h2k(b_ds+b_db)}일 {h2k(b_hs+b_hb)}시"
                            day_weeks = ["월", "화", "수", "목", "금", "토", "일"][birth_d.weekday()]
                            
                            fact_line = f"▶ 추천 일자: {birth_d.year}년 {birth_d.month:02d}월 {birth_d.day:02d}일 09:31~11:30 ({full_bazi_kor})"
                            ai_target_days_facts.append(fact_line)
                            del_content += f"<div style='font-size:15px; font-weight:bold; color:#4A148C;'>{fact_line}</div>\n"
                    del_content += "</div>\n"
                    
                    del_content += f"<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:15px;'><b>💡 부부를 위한 임신 계획 가이드:</b><br>아래의 출산 길일은 아이의 사주 기운을 우선으로 선정한 것입니다. 의학적 평균 임신 기간(약 280일)을 고려할 때, 합궁 시기는 출산 예정일로부터 약 9개월 10일 전후가 됩니다. 부인분의 생리 주기와 배란일을 면밀히 고려하시어, 부부께서 상의하에 가장 건강한 시기를 계획하시길 바랍니다.</p>"
                    
                    intro_essay = f"""<div style='margin-top:10px;'>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:8px;'>깊고 고요한 시간의 흐름 속에서, 새로운 생명의 탄생은 하늘과 땅, 그리고 부모의 염원이 조화롭게 어우러지는 기적과 같습니다. 귀한 부부께서 보내주신 소중한 사주 정보를 바탕으로, 장차 태어날 아기의 선천적 명식이 부모님과의 오행 상생 조화를 극대화하고, 나아가 아이 스스로 빛나는 삶의 궤적을 그려나갈 수 있도록 '최고의 프리미엄 출산 희망일과 시간'을 심혈을 기울여 선정하였습니다.</p>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:8px;'>부부의 사주를 살펴보니, 신청인 남성분({m_saju_kor})께서는 {m_ilgan_kor}토 일간으로 강한 금수(金水)의 기운이 특징적입니다. 총명하고 재물 운이 좋으며 실리적인 면모가 돋보이나, 다소 한습한 기운이 강하여 따뜻한 화(火) 기운의 보충이 절실합니다. 이는 정신적 안정และ 인성의 조화를 의미합니다. 상대방 여성분({f_saju_kor})께서는 정(丁)화 일간으로, 목화(木火)의 따뜻하고 밝은 기운이 충만하며 지혜롭고 활발한 에너지를 지니셨습니다.</p>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:8px;'>아기가 태어날 시공간은 부모의 사주에 부족한 오행을 채우고, 동시에 아이 자신이 타고난 길운(吉運)을 펼칠 수 있는 절묘한 지점을 찾아야 합니다. 특히 남성분의 한습한 기운을 보완하고, 부부 모두에게 긍정적인 상생의 흐름을 만들어낼 수 있는 따뜻한 화(火) 기운을 중심으로, 동시에 아이의 명식이 균형과 조화를 이루는 날들을 엄선하였습니다.</p>
<p style='font-size:15px; line-height:1.8; color:#000; text-indent: 15px; margin-top:0px; margin-bottom:8px;'>이제, 부부의 간절한 바람을 담아 선정한 세 가지 최적의 출산 희망일을 <b>초연 시공명리 궁합</b> 관점에서 자세히 풀어내어 올립니다. 부디 이 추천들이 아기의 밝은 미래를 여는 데 귀한 나침반이 되기를 바랍니다.</p>
</div>"""
                    del_content += intro_essay

                    # 🚨 파이썬 연산 결과 주입을 위한 변수 바인딩
                    ai_days_input_str = "\n".join(ai_target_days_facts)

                    # 🚨 [완전 동적 변경 2] 프롬프트 내부 하드코딩 완전 제거 및 성별 통변 지침 보강
                    delivery_prompt = f"""
당신은 명리심리상담사 및 출산택일 최고 권위자인 초연 박사입니다. 파이썬 시스템이 부모 사주를 교차 분석하여 도출해 낸 아래 [지정된 3가지 추천 일자]에 대해 정밀 통변 에세이를 작성하십시오.

[지정된 추천 일자 리스트]
{ai_days_input_str}

[선택된 태아 성별 조건]
- 현재 설정된 성별 조건: {baby_gender}

🚨 [출력 절대 통제 규칙]
1. 에세이 상단에 어떠한 제목도 일절 적지 마십시오.
2. 단락 구분에 '---' 같은 마크다운 구분선을 사용하면 시스템이 파괴되므로 절대 금지합니다.
3. 맺음말(감사합니다 등)은 생략하십시오.
4. 모든 문단은 무조건 `<p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'>` 태그로만 묶어 좁고 쫀쫀한 문단 간격을 사수하십시오. 빈 공백 줄(엔터) 출력을 전면 금지합니다.
5. 위 [지정된 추천 일자 리스트]에 명시된 날짜 포맷과 한글 간지 명식을 소제목에 토씨 하나 틀리지 말고 그대로 복사 출력한 뒤 그 아래에 통변을 전개하십시오.

🚨 [성별 맞춤형 통변 지침]
- 만약 성별이 '남아' 혹은 '여아'로 고정된 경우, 성별과 명식의 음양을 대조하여 대운의 순행/역행 경로를 확정 짓고 미래 10년 주기 운로를 분석하십시오.
- 만약 성별이 '미정'인 경우, 각 추천 일자마다 반드시 "만약 남아로 태어난다면 대운이 O행하여 ~한 성취를 이루고, 여아로 태어난다면 대운이 O행하여 ~한 복록을 누린다"는 식으로 성별에 따른 유불리와 운로의 차이점을 명확히 쪼개어 서술하십시오.

[출력 포맷 템플릿]
<span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111; margin-top:15px; margin-bottom:5px; display:block;'>시스템이 제공한 해당 순위 추천 일자 라인을 그대로 출력</span>
<div style='padding-left: 15px; margin-bottom: 15px;'>
    <div style='margin-bottom: 3px;'><b>1) 일반 명리 풀이:</b></div>
    <p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'> (통변 기재) </p>
    <div style='margin-bottom: 3px; margin-top:5px;'><b>2) 시공 명리 풀이:</b></div>
    <p style='text-indent: 15px; margin-top: 0px; margin-bottom: 8px;'> (통변 기재) </p>
</div>
"""
                    ai_delivery_html = call_gemini_api(delivery_prompt).replace('\n', '')
                    
                    closing_del_html = f"""<div style='margin-top: 20px;'>
<p style='font-size:15px; text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>사랑하는 부부님, 이 세 가지 출산 희망일은 각각 독특하고 고귀한 기운을 담고 있습니다. 하늘의 뜻과 부모님의 깊은 사랑, 그리고 제가 바친 노력이 한데 어우러져 귀한 아기가 이 세상에 가장 찬란하게 빛을 발하며 첫걸음을 내딛기를 진심으로 기원합니다.</p>
<p style='font-size:15px; text-indent: 15px; text-align: justify; line-height: 1.8; margin-top: 0px; margin-bottom: 8px;'>어떤 날을 선택하시든, 그 선택은 아기에게 최고의 축복이 될 것입니다. 아기의 탄생으로 가정이 더욱 행복하고 번창하시기를 간절히 축원합니다.</p>
<div style='text-align: right; margin-top: 25px;'>
<span style='font-weight: 900; font-size: 18px; color: #4A148C; font-family: \"Nanum Myeongjo\", serif;'>초연 시공명리 연구소</span>
</div>
</div>"""

                    del_content += f"<p style='line-height:1.8; color:#333; text-indent: 15px; margin-top: 15px; margin-bottom: 15px;'><span style='font-size:18px;'><b>💡 부부를 위한 임신 계획 가이드:</b></span><br><span style='font-size:15px;'>위의 출산 길일은 아이의 사주 기운을 우선으로 선정한 것입니다. 의학적 평균 임신 기간(약 280일)을 고려할 때, <b>합궁 시기는 출산 예정일로부터 약 9개월 10일 전후</b>가 됩니다. 부인분의 생리 주기와 배란일을 면밀히 고려하시어, 부부께서 상의하에 가장 건강한 시기를 계획하시길 바랍니다.</span></p>"

                    def wrap_a4_del(content, title_color="#4A148C"):
                        return f"<div class='report-page'>\n<div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'>\n{content}\n</div>\n</div>"

                    st.session_state['saved_report_del'] = wrap_a4_del(del_content)
                    st.session_state['run_delivery_only'] = False
                    st.rerun() 
                except Exception as e:
                    st.error(f"출산택일 연산 장애: {e}")
                    st.session_state['run_delivery_only'] = False

        # 3-3. 생성된 택일 리포트 결합 출력
        if st.session_state.get('saved_report_del'):
            st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
            st.markdown(st.session_state.get('saved_report_del', ''), unsafe_allow_html=True)
