import streamlit as st
import pandas as pd
import json
import os
import math
import datetime as dt_mod
from korean_lunar_calendar import KoreanLunarCalendar
import ephem
import google.generativeai as genai
import pytz
import streamlit.components.v1 as components
import re

# 🎯 [버전 컨트롤 타워]
APP_VERSION = "Ver 35.1 (Gemini 2.5-Pro Mode)"

# ==============================================================================
# 0. VIP 인셋 프레임 및 초강력 프린트 CSS
# ==============================================================================
st.set_page_config(page_title=f"초연 시공명리 사주풀이 {APP_VERSION}", layout="wide")

st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&display=swap");
    
    body, .stApp { background-color: #FFF8E1; }
    
    .report-page { width: 210mm; max-width: 100%; margin: 30px auto; background-color: #FFFFFF !important; padding: 15mm 10mm; box-shadow: 0 0 20px rgba(0,0,0,0.15); border-radius: 20px; box-sizing: border-box; }
    .report-page, .report-page * { font-family: 'Noto Serif KR', serif !important; color: #000000; }
    
    .vip-inset-frame { 
    border: 2px solid #1A237E; 
    border-radius: 15px; 
    padding: 20px; 
    background: transparent; 
    box-sizing: border-box;        /* 1. 박스 크기를 고정(padding 포함) */
    width: 100%;                   /* 2. 가로폭 100% 강제 */
    overflow: hidden;              /* 3. 삐져나온 내용물 강제 차단 */
    word-break: keep-all;          /* 4. 한글 단어 단위 줄바꿈 */
    -webkit-box-decoration-break: clone; 
    box-decoration-break: clone; 
}
    
    .report-page h1 { font-size: 26px !important; margin-bottom: 15px !important; color: #1A237E !important; font-weight: 900 !important; }
    .report-page h2 { font-size: 22px !important; margin-bottom: 15px !important; font-weight: 900 !important; }
    .report-page h3 { font-size: 22px !important; margin-top: 25px !important; margin-bottom: 8px !important; border-bottom: 2px solid #1A237E; padding-bottom: 5px; color: #1A237E !important; font-weight: 900 !important; }
    .report-page h4 { font-size: 18px !important; margin-top: 15px !important; margin-bottom: 8px !important; font-weight: 900 !important; }
    
    .result-table { width: 100%; border-collapse: collapse; border: 3px solid #3E2723; margin-bottom: 15px; table-layout: fixed; }
    .result-table td { border: 1px solid #444; padding: 1px; text-align: center; vertical-align: middle; font-weight: 900; font-size: 13px; line-height: 1.2; word-wrap: break-word; }
    
    .no-border-row td { border-top: none !important; border-bottom: none !important; }
    .no-border-row:last-of-type td { border-bottom: 1px solid #444 !important; }
    
    .header-cell-main { background-color: #E8EAF6 !important; color: #1A237E !important; font-weight: 900 !important; font-size: 12px !important; height: 22px !important; }
    
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
    """Gemini API 호출 함수 (Claude 전환 전 임시)"""
    if model is None:
        return "<div style='color:red;'>🚨 Gemini 모델이 초기화되지 않았습니다. API 키를 확인하세요.</div>"
    try:
        response = model.generate_content(prompt_text)
        return response.text.strip()
    except Exception as e:
        return f"<div style='color:red;'>🚨 Gemini AI 서버 통신 장애: {e}</div>"

GAN, JI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"

JIJANGGAN = {'子': ['壬', '-', '癸'], '丑': ['癸', '辛', '己'], '寅': ['戊', '丙', '甲'], '卯': ['甲', '-', '乙'], '辰': ['乙', '癸', '戊'], '巳': ['戊', '庚', '丙'], '午': ['丙', '己', '丁'], '未': ['丁', '乙', '己'], '申': ['戊', '壬', '庚'], '酉': ['庚', '-', '辛'], '戌': ['辛', '丁', '戊'], '亥': ['戊', '甲', '壬'] }

def get_color(c):
    if c in "甲乙寅卯": return "목"
    if c in "丙丁巳午": return "화"
    if c in "戊己辰戌丑未": return "토"
    if c in "庚辛申酉": return "금"
    if c in "壬癸亥子": return "수"
    return "토"

def get_current_saju_data():
    # 세션 상태에 저장된 역산 결과값이 있다고 가정합니다.
    # 만약 변수명이 다르다면 박사님의 실제 변수명으로 교체하십시오.
    try:
        # 역산 결과가 들어있는 session_state 변수들
        # 예: st.session_state['saju_gans'] = ['癸', '丁', '乙', '戊']
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
    
    # 4. 투출 확인 (인덱스 오류 방지)
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
            {"label": "대운 조화", "pct": p5, "color": "#8e44ad"},
            {"label": "리스크 방어력", "pct": p6_safety, "color": "#e74c3c"}]

    def generate_ai_report(self, m_ctx, f_ctx):
        m_ec, f_ec = self.count_elements(self.m_g, self.m_j), self.count_elements(self.f_g, self.f_j)
        detail_scores_text = "\n".join([f"  * {d['label']}: {d['pct']}점" for d in self.details])

        prompt = f"""[SYSTEM ROLE: CHOYEON SIGONG MASTER]
당신은 명리심리상담사 '초연 박사'의 수석 분석관입니다. 두 사람의 정보를 1:1 대칭 저울에 올려 정밀 교차 분석 에세이를 생성하십시오.

🚨 [출력 절대 형식 규칙 - 인사말 원천 삭제 명령]
1. "안녕하세요", "분석을 시작합니다" 등의 서론, 인사말, 확인 멘트를 절대 작성하지 마십시오.
2. 출력 텍스트는 오직 아래 명시된 마커 구조([MALE_START] 등)로만 이루어져야 하며, 그 외의 껍데기 문장은 모두 차단하십시오.
3. 모든 통변 문장은 반드시 <p style='font-family: "Nanum Myeongjo", "바탕체", Batang, serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'> 태그로 감싸십시오.

🚨 [분량 및 목차 통제 명령]
- 남명과 여명의 개별 사주 통변은 정해진 목차(1. 사주팔자 구조 분석, 2. 성격) 외에는 절대 확장하지 마십시오.
- 각 개인별 통변 내용은 A4 2페이지 분량 안으로 알맞게 들어갈 수 있도록 밀도 있고 간결하게 축약하여 서술하십시오.

[MALE_START]
<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 25px; margin-bottom: 8px; display:block;'>1. 사주팔자 구조 분석</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(남성 {m_ctx['u_name']}님의 격국과 자의물상을 기반으로 한 현대적 핵심 성향을 3~4문장으로 축약 서술)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>
(남성 {m_ctx['u_name']}님의 오행 분포와 억부 조후의 조화 상태를 고려한 에너지 관리법 축약 서술)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>3) 사주팔자의 역동적 관계 분석</span>
(남성 {m_ctx['u_name']}님의 원국 합충형파해 및 신살의 역동성을 일상적인 언어로 핵심만 조언)

<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 35px; margin-bottom: 8px; display:block;'>2. 성격</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
(남성 {m_ctx['u_name']}님의 사회적 기질 및 표면적 성격 축약 서술)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>
(남성 {m_ctx['u_name']}님의 방어기제, 무의식적 본능 및 공망의 심리 상태 축약 서술)
[MALE_END]

[FEMALE_START]
<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 25px; margin-bottom: 8px; display:block;'>1. 사주팔자 구조 분석</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(여성 {f_ctx['u_name']}님의 격국과 자의물상을 기반으로 한 현대적 핵심 성향을 3~4문장으로 축약 서술)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 내 삶의 리듬และ 에너지 균형</span>
(여성 {f_ctx['u_name']}님의 오행 분포와 억부 조후의 조화 상태를 고려한 에너지 관리법 축약 서술)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>3) 사주팔자의 역동적 관계 분석</span>
(여성 {f_ctx['u_name']}님의 원국 합충형파해 및 신살의 역동성을 일상적인 언어로 핵심만 조언)

<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 35px; margin-bottom: 8px; display:block;'>2. 성격</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
(여성 {f_ctx['u_name']}님의 사회적 기질 및 표면적 성격 축약 서술)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>
(여성 {f_ctx['u_name']}님의 방어기제, 무의식적 본능 및 공망의 심리 상태 축약 서술)
[FEMALE_END]

[GUNGHAP_START]
<div class='choyeon-premium-report' style='line-height:1.9;'>
  <h3 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 22px; font-weight: bold; color: #1B5E20; border-bottom: 2px solid #1B5E20; padding-bottom: 5px; margin-top: 10px;'>🍀 두 사람의 운명적 만남에 대하여</h3>
  <p>(두 사람의 원국 조화와 인연의 본질에 대한 깊이 있는 총평 에세이 서술)</p>
  
  <h3 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 22px; font-weight: bold; color: #1A237E; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 35px;'>🌈 커플의 인생 기상도 분석</h3>
  [COUPLE_DAEWUN_TABLES_HERE]
  (🚨경고: 위 마커는 파이썬 엔진이 대운 흐름표를 상하로 나란히 꽂아 넣을 절대 성역입니다. AI가 임의로 표를 지워버리거나 스스로 표를 그리는 만행을 절대 금지합니다. 마커를 그대로 둔 상태로, 바로 아래에서 두 사람의 대운 교차점에 따른 상생/보완 에세이를 깊이 있게 통변하십시오.)
  
  <h4 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 18px; font-weight: bold; color: #1A237E; margin-top: 35px;'>🗝️ 커플의 사주팔자 비교 분석</h4>
  <div style='margin-top: 15px; margin-bottom: 10px;'><span style='color: #1A237E; font-weight: 900; font-size: 16px;'>▶ 음양오행과 사주구조의 결합</span></div>
  <p>(오행 상생 분석 서술)</p>
  
  <div style='margin-top: 20px; margin-bottom: 10px;'><span style='color: #1A237E; font-weight: 900; font-size: 16px;'>▶ 자기 성향과 사회적 관계의 호흡</span></div>
  <p>(사회적 호흡 서술)</p>
  
  <div style='margin-top: 20px; margin-bottom: 10px;'><span style='color: #1A237E; font-weight: 900; font-size: 16px;'>▶ 시공의 충돌에 따른 삶의 변화</span></div>
  <p>(시공 변화 및 조율 서술)</p>

  <h4 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 18px; font-weight: bold; color: #1A237E; margin-top: 40px;'>💞 커플의 상생과 조화 궁합 분석</h4>
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 16px;'>[내면의 유대감] - 속 궁합</span></div>
  <p>(일지 결합 및 정서적 안정감 서술)</p>
  
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 16px;'>[사회적 환경 조화] - 겉 궁합</span></div>
  <p>(연지, 월지 조화 및 현실적 궁합 서술)</p>
  
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 16px;'>[기운의 상호 보완] - 오행 궁합</span></div>
  <p>(서로의 결핍 오행 보충 관계 서술)</p>

  <h4 style='font-family: "Malgun Gothic", sans-serif !important; font-size: 18px; font-weight: bold; color: #1A237E; margin-top: 40px;'>⚓ 더 깊은 인연을 위한 조율의 지혜</h4>
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 16px;'>[환경의 차이와 포용]</span></div>
  <p>(갈등 극복을 위한 행동 지침 서술)</p>
  
  <div style='margin-top: 25px; margin-bottom: 15px;'><span style='color: #1A237E; font-weight: 900; font-size: 16px;'>[에너지의 균형]</span></div>
  <p>(최종 조율 및 축복의 개운 처방 서술)</p>
</div>
[GUNGHAP_END]
"""
        return call_claude_api(prompt, max_tokens=12000)

    def get_graphic_html(self, ai_text):
        import re
        b3 = chr(96) + chr(96) + chr(96)
        clean_ai = re.sub(b3 + "html|" + b3, "", ai_text).strip()

        c = "#3498db" if self.final_score >= 70 else ("#f39c12" if self.final_score >= 60 else "#e74c3c")
        
        bars_html = ""
        for item in self.details:
            bars_html += f"<div style='display:flex; align-items:center; margin-bottom:12px;'><div style='width:130px; font-size:13px; font-weight:bold; color:#555;'>{item['label']}</div><div style='flex:1; height:12px; margin:0 10px;'><svg width='100%' height='12' style='display:block;'><rect width='100%' height='12' rx='6' ry='6' fill='#eeeeee' /><rect width='{item['pct']}%' height='12' rx='6' ry='6' fill='{item['color']}' /></svg></div><div style='width:35px; font-size:12px; font-weight:bold;'>{item['pct']}%</div></div>"
            
        closing = "<div style='margin-top: 40px; padding-top: 30px; page-break-inside: avoid;'><p style='font-size: 15px; line-height: 1.8; color: #333; font-family: \"Noto Serif KR\", serif;'>&nbsp;&nbsp;&nbsp;&nbsp;두 분의 <b style='color:#1A237E;'>'만남'</b>은 결코 우연이 아닌, <b style='color:#1A237E;'>'셀 수 없이 많은 시간 속에서 기적처럼 찾아온 귀한 인연'</b>입니다. 사주팔자는 각자의 바코드지만, <b style='color:#1A237E;'>'궁합(宮合)'</b>은 두 바코드가 만나 그려내는 새로운 <b style='color:#1A237E;'>'하모니(harmonie)'</b>입니다.</p><p style='font-size: 15px; line-height: 1.8; color: #333; margin-top: 10px; font-family: \"Noto Serif KR\", serif;'>&nbsp;&nbsp;&nbsp;&nbsp;서로의 다름을 이해하고 채워주는 든든한 <b style='color:#1A237E;'>'동반자'</b>가 되시기를 진심으로 기원하며, 두 분의 앞날에 늘 시공간의 축복이 가득하시길 소망합니다. </p><div style='text-align: right; margin-top: 25px;'><span style='font-weight: 900; font-size: 16px; color: #1A237E; font-family: \"Noto Serif KR\", serif;'>- 초연 시공명리 연구소 드림 -</span></div></div>"
        
        # 본 리턴 구역은 클래스 외부(Step 3 Engine)에서 마커 분할 및 조립이 이루어지므로 본래 양식을 유지합니다.
        return clean_ai, c, bars_html, closing

# ==============================================================================
# 4. 사이드바 UI
# ==============================================================================
with st.sidebar:
    st.title("🏮초연 시공명리 연구소")
    st.caption(f"{APP_VERSION} Master (Base + Gunghap)")
    
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
        p_t = st.selectbox("00:30 ~ 01:29 (朝子)시", idx_list, key="p_t_key")

    elif u_product == "타 감명서":
        st.markdown("---")
        st.markdown("<div style='font-weight:900; color:#2E7D32; margin-bottom:5px;'>📄 타 감명서 원문 입력</div>", unsafe_allow_html=True)
        st.caption("다른 역술가의 감명서 내용을 아래에 붙여넣기 하세요.")
        other_reading_text = st.text_area("타 감명서 원문", height=250, placeholder="여기에 타 감명서 내용을 붙여넣기 하세요...", key="other_reading")
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_single = st.button("🚀 초연 시공명리 사주풀이 가동", use_container_width=True, type="primary")

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
        # 2. 메시지 영역 사전 할당 및 강제 갱신
        status_area = st.empty()
        status_area.info("⏳ [초연 시공명리 분석을 시작합니다. 잠시만 기다려 주십시오...]")
        import time
        time.sleep(0.5)

        # 3. 스피너 가동 및 직렬 엔진 시작
        spinner_msg = f"⏳ [초연 시공명리 분석({APP_VERSION}) 중....]"
        with st.spinner(spinner_msg):
            
            # ==================================================================
            # [1단계] 공통 사주 엔진 (개인사주 및 타 모드 기반 무조건 실행)
            # ==================================================================
            try:
                klc = KoreanLunarCalendar()
                if u_cal == "양력": klc.setSolarDate(u_y, u_m, u_d)
                elif u_cal == "음력(평달)": klc.setLunarDate(u_y, u_m, u_d, False)
                else: klc.setLunarDate(u_y, u_m, u_d, True)
                is_leap = getattr(klc, 'isIntercalary', False)
                leap_str = "윤달" if is_leap else "평달"
                
                sol_str = f"{klc.solarYear}년 {klc.solarMonth:02d}월 {klc.solarDay:02d}일"
                lun_str = f"{klc.lunarYear}년 {klc.lunarMonth:02d}월 {klc.lunarDay:02d}일 ({leap_str})"
                
                curr_dt_sys = dt_mod.datetime.now()
                curr_y = curr_dt_sys.year
                curr_m = curr_dt_sys.month
                u_age = curr_y - u_y + 1

                base_dt = dt_mod.datetime(u_y, u_m, u_d, 12, 0)
                gj = klc.getChineseGapJaString().split()
                ys, yb, ms, mb, ds, db = gj[0][0], gj[0][1], gj[1][0], gj[1][1], gj[2][0], gj[2][1]

                hs, hb = get_time_ganji(ds, u_t, base_dt)
                gans, jjis = [hs, ds, ms, ys], [hb, db, mb, yb]
                
                applicant_bazi = [f"{hs}{hb}", f"{ds}{db}", f"{ms}{mb}", f"{ys}{yb}"]

                adj_mins = get_total_time_adjustment(base_dt)
                utc_dt = base_dt - dt_mod.timedelta(hours=9) + dt_mod.timedelta(minutes=adj_mins)
                order = 1 if (GAN.index(ys)%2==0) == (u_gender=='남성') else -1
                calc_d = get_daeun_su_accurate(utc_dt, order)
                current_daewun_age = ((u_age - calc_d) // 10) * 10 + calc_d
                dw_start_age = current_daewun_age                

                base_y_idx = (curr_y - 1984) % 60
                curr_y_ganji = GAN[base_y_idx % 10] + JI[base_y_idx % 12]            
                
                time_str = f" {u_t.split('(')[0].strip()} ({hb})시" if u_t != "시간 모름" else ""
                
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
                    b_bot = "1px solid #444 !important" if l_idx == 3 else "0px solid transparent !important"
                    b_top = "0px solid transparent !important"
                    cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:{b_top}; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                    lbl = f"<td rowspan='4' class='header-cell-main' style='border-right: 1px solid #444 !important; border-left: 1px solid #444 !important; border-bottom: 1px solid #444 !important; border-top: 0px solid transparent !important; font-size:14px !important;'>합충형파해</td>" if l_idx==0 else ""
                    ji_rel_rows += f"<tr style='border:none;'>{lbl}{cells}</tr>"

                disp_name = u_name if u_name.strip() else "홍길동"
                info_h = f"""
                <div style='text-align:center; font-family:"Malgun Gothic", sans-serif; margin-bottom:15px; line-height:1.5;'>
                    <span style='font-size:18px; font-weight:900; color:#1A237E; white-space:nowrap;'>
                        {p_icon} {u_name}님 ({u_gender}, {u_marital}, {u_age}세)
                </span><br>
                <span style='font-size:14px; font-weight:bold; color:#555; white-space:nowrap;'>
                    [양력: {sol_str} | 음력: {lun_str} {time_str}]
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
                if u_product == "개인사주":
                    db_header = (
                        f"[시스템 강제 시간 인식: 현재 시점은 {curr_y}년 {curr_m}월 입니다.]\n"
                        "당신은 명리심리상담사 1급 자격을 갖춘 초연 박사입니다. \n"
                        f"- 내담자 성함: {disp_name}\n"
                        f"- 나이 / 성별: {u_age}세 / {u_gender}\n"
                        f"- marital_status: {u_marital}\n"
                        f"- 타고난 심리 구조 팩트: {s_name} ({s_type} - {s_desc})\n"
                        f"- 공망 팩트: [년주] {n_gong}, [일주] {i_gong}\n"
                    )
                    prompt = f"""{db_header}
                    [종합 특별지시 사항 : 대중을 위한 현대적 통변 원칙]
                    1. 모든 통변 에세이 문장은 반드시 <p style='text-indent: 1em;'> 태그로 감싸십시오.
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>1. 사주팔자 구조 분석</h3>
                    <div class='content-box-loose'>
                    [CHOYEON_GOLDEN_TEXT_HERE]
                    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 타고난 삶의 무대와 기본 성향</span>
                    (상세 에세이)
                    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 내 삶의 리듬과 에너지 균형</span>
                    (상세 에세이)
                    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>3) 사주팔자의 역동적 관계 분석</span>
                    (상세 에세이)
                    </div>
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>2. 성격</h3>
                    <div class='content-box-loose'>
                    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>1) 겉으로 드러난 성격</span>
                    (상세 에세이)
                    <span class='sub-title' style='font-size: 18px; font-weight: 900; color: #111;'>2) 감추어진 내 속마음</span>
                    (상세 에세이)
                    </div>
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>3. 부모·형제운</h3><div class='content-box-loose'>(에세이)</div>
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>4. 학업·진학운</h3><div class='content-box-loose'>(에세이)</div>
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>5. 적성·직업운</h3><div class='content-box-loose'>(에세이)</div>
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>6. 결혼·자녀운</h3><div class='content-box-loose'>(에세이)</div>
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>7. 재성운</h3><div class='content-box-loose'>(에세이)</div>
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>8. 사업운</h3><div class='content-box-loose'>(에세이)</div>
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>9. 관직·명예운</h3><div class='content-box-loose'>(에세이)</div>
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>10. 건강운</h3><div class='content-box-loose'>(에세이)</div>
                    <h3 style='color:#1A237E; font-size: 24px; font-weight: 900;'>11. 운의 흐름</h3>
                    <div class='content-box-loose'>
                    [DAEWUN_TABLE_HERE][SEWUN_TABLE_HERE][WOLWUN_TABLE_HERE]
                    </div>
                    """
                    res_text = call_claude_api(prompt, max_tokens=12000)
                    ai_text = "\n".join([line.lstrip() for line in res_text.split("\n")]).replace("[CHOYEON_GOLDEN_TEXT_HERE]", choyeon_golden_text)
                    un_html_clean = un_html.replace("\n", " ")
                    se_html_clean = se_html.replace("\n", " ")
                    wol_html_clean = wol_html.replace("\n", " ")
                    clean_ai_text = ai_text.replace("[DAEWUN_TABLE_HERE]", un_html_clean).replace("[SEWUN_TABLE_HERE]", se_html_clean).replace("[WOLWUN_TABLE_HERE]", wol_html_clean)
                    full_content_clean = f"<div style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #000;'>{clean_ai_text}<br><br>{closing_html}</div>"
                    report_1_full_html = f"{cover_html}<div class='report-page'><div class='vip-inset-frame' style='border-color:#1A237E; padding: 20px;'><h1 style='text-align:center;'>🎯[초연 시공명리 사주풀이]</h1>{table_html}{master_bar_html}<div style='margin-top:20px;'>{full_content_clean}</div></div></div>"
                    st.markdown(report_1_full_html, unsafe_allow_html=True)
                else:
                    # 궁합이나 타감명서 모드일 때는 1단계 호출 생략(변수 및 레이아웃 충돌 방지용)
                    clean_ai_text = "[개인 원본 데이터 보유]"
                    
            except Exception as e: 
                st.error(f"1단계 기본 엔진 가동 실패: {e}")
                st.stop()

            # ==================================================================
            # 🚀 [2단계] 타 감명서 비교분석 (선택적)
            # ==================================================================
            if u_product == "타 감명서":
                try:
                    st.info("▶ [타 감명서] 원본 출력 및 상세 비교 분석 중...") 
                    comp_text = other_reading_text

                    report_2_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#555;'><h2 style='text-align:center; color:#555; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; margin-bottom:20px;'>📜 타 감명서 원문</h2><div style='font-family: \"Nanum Myeongjo\", \"바탕체\", Batang, serif; font-size: 15px; line-height: 1.8; color: #111;'>{comp_text.replace(chr(10), '<br>')}</div></div></div>"
                    st.markdown(report_2_html, unsafe_allow_html=True)
                        
                    comp_prompt = f"""
    당신은 명리심리상담사 '초연 박사'를 보조하는 수석 분석관입니다.
    아래 [1. 초연 사주풀이]와 [2. 타 감명서]의 내용을 인사말이나 서론 없이, 곧바로 대조 포맷 규칙에 의거하여 출력하십시오.

    🚨 [출력 및 서식 절대 규칙]
    1. "네, 분석을 시작합니다" 등의 서론 멘트를 철저히 금지합니다. 첫 글자는 무조건 제목 태그로 시작해야 합니다.
    2. 차이점 기술 시 반드시 <b>&lt;초연&gt;</b> 및 <b>&lt;타 감명&gt;</b> 마커를 문단 앞에 기입하고 공통점도 빠짐없이 발굴하십시오.
    3. 통변 근거 제시 시 반드시 명리적 근거(십성, 합형충파해, 신살 등)를 기반으로 논증하십시오.
    4. 1번부터 13번(총평)까지 단 하나의 대목차 유실 없이 전체를 배분하여 성실히 완주하십시오.

    [목차 규격 정의]
    <h3 style='color:#1A237E; font-size: 22px; font-weight: 900; border-bottom: 2px solid #1A237E; padding-bottom: 5px; margin-top: 25px; margin-bottom: 8px; display:block;'>1. 사주팔자 구조 및 성격 비교</h3>
    ...
    <h3 style='color:#D50000; font-size: 22px; font-weight: 900; border-bottom: 2px solid #D50000; padding-bottom: 5px; margin-top: 35px; margin-bottom: 8px; display:block;'>13. 총평 및 향후 개선점</h3>
    """
                    c_res = call_claude_api(comp_prompt, max_tokens=10000)
                    report_3_html = f"<div class='page-break-before'></div><div class='report-page'><div class='vip-inset-frame' style='border-color:#D50000;'><h1 style='text-align:center; color:#D50000; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; margin-bottom:25px;'>⚖️ 1:1 상세비교 리포트</h1><div style='margin-top:20px;'>{c_res}</div></div></div>"
                    st.markdown(report_3_html, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"2단계 비교 분석 장애: {e}")

            # ==================================================================
            # 💕 [3단계] 궁합 풀이 (Ver 35.2 - 인쇄/PDF 및 격자·색상 정밀 보정판)
            # ==================================================================
            if u_product == "궁합":
                # --- [1단계: 안전 변수 선언부] ---
                gh_engine = None
                couple_daewun_tables = ""
                m_tbl, f_tbl = "", ""
                m_ess, f_ess, g_ess = "", "", ""
                try:
                    st.info("▶ [종합 궁합] 남명/여명 사주 정보 동기화 및 3단계 직렬 통합 분석 가동 중...")
                    
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

                    # 3-2. 남명/여명 데이터 대칭 및 혼인 기부 정보 완벽 바인딩
                    if u_gender == "남성":
                        m_marital, f_marital = u_marital, p_marital
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
                        m_marital, f_marital = p_marital, u_marital
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

                    def get_counts(gans, jjis):
                        c = {"목":0,"화":0,"토":0,"금":0,"수":0}
                        for x in gans + jjis:
                            if x != "?": c[get_color(x)] += 1
                        return c

                    m_cnt, f_cnt = get_counts(m_gans, m_jjis), get_counts(f_gans, f_jjis)

                    # 3-3. 사주팔자표 빌더 (지시하신 가로 격자눈 제거 및 세로 구분열 확대 적용)
                    def build_bazi_table(gender_icon, name, gender_str, marital_str, age, sol, lun, time, gans, jjis, ds, yb, counts, guiin, gong, samjae):
                        ji_rel_rows = ""
                        for l_idx, r_idx in enumerate([1, 2, 0, 3]):
                            b_bot = "1px solid #444 !important" if l_idx == 3 else "none !important"
                            cells = "".join([f"<td style='color:{('#D50000' if ci==r_idx else ('#000' if get_ji_rel_set(jjis[r_idx], jjis[ci])!='-' else '#BBB'))}; font-weight:900; border-top:none !important; border-bottom:{b_bot}; border-left:1px solid #444 !important; border-right:1px solid #444 !important;'>{('←('+jjis[r_idx]+')→' if ci==r_idx else get_ji_rel_set(jjis[r_idx], jjis[ci]))}</td>" for ci in range(4)])
                            lbl = f"<td rowspan='4' class='header-cell-main' style='border-left:1px solid #444 !important; border-right:1px solid #444 !important; border-top:1px solid #444 !important; border-bottom:1px solid #444 !important; font-size:15px !important; font-weight:900;'>합충형파해</td>" if l_idx==0 else ""
                            ji_rel_rows += f"<tr style='border-top:none !important; border-bottom:{b_bot};'>{cells if l_idx>0 else lbl+cells}</tr>"

                        info_str = f"""<div style='text-align:center; margin-bottom:15px; font-family:\"Malgun Gothic\", sans-serif;'>
                            <span style='font-size:18px; font-weight:900;'>{gender_icon} <span style='color:#1A237E;'>{name}</span>님 ({gender_str}, {marital_str}, {age}세)</span><br>
                            <span style='font-size:14px; color:#555;'>[양력] {sol} | [음력] {lun} {time}</span>
                        </div>"""
                        
                        return f"""
                        {info_str}
                        <table class='result-table' style='width:100%; border-collapse:collapse; text-align:center;'>
                        <tr class='top-header-cell'><td style='border:1px solid #444; font-size:15px !important; font-weight:900;'>구분</td><td style='border:1px solid #444;'>시주</td><td style='border:1px solid #444;'>일주</td><td style='border:1px solid #444;'>월주</td><td style='border:1px solid #444;'>년주</td></tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; font-weight:900;'>천간십성</td><td style='border:1px solid #444;'>{get_ss(ds,gans[0])}</td><td style='border:1px solid #444;'><span style='color:#D50000; font-weight:900;'>日元</span></td><td style='border:1px solid #444;'>{get_ss(ds,gans[2])}</td><td style='border:1px solid #444;'>{get_ss(ds,gans[3])}</td></tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; font-weight:900;'>천간</td>{td(gans[0])}{td(gans[1])}{td(gans[2])}{td(gans[3])}</tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; font-weight:900;'>지지</td>{td(jjis[0])}{td(jjis[1])}{td(jjis[2])}{td(jjis[3])}</tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; font-weight:900;'>지지십성</td><td style='border:1px solid #444;'>{get_ss(ds,jjis[0])}</td><td style='border:1px solid #444;'>{get_ss(ds,jjis[1])}</td><td style='border:1px solid #444;'>{get_ss(ds,jjis[2])}</td><td style='border:1px solid #444;'>{get_ss(ds,jjis[3])}</td></tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; font-weight:900; padding:0;'>지장간</td>{"".join([f"<td style='border:1px solid #444; padding:0;'>{get_jijanggan_full(ds, jjis[i])}</td>" for i in range(4)])}</tr>
                        {ji_rel_rows}
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; font-weight:900;'>십이운성</td>{"".join([f"<td style='border:1px solid #444; color:#0D47A1;'>{get_unsung(ds, jjis[i])}</td>" for i in range(4)])}</tr>
                        <tr><td class='header-cell-main' style='border:1px solid #444; font-size:15px !important; font-weight:900;'>십이신살</td>{"".join([f"<td style='border:1px solid #444; color:#C62828;'>{get_12_shinsal(yb, jjis[i])}</td>" for i in range(4)])}</tr>
                        </table>
                        <div style='border:2px solid #3E2723; margin-top:10px; margin-bottom:20px; padding:8px; display:flex; justify-content:space-between; font-weight:900; font-size:12px; border-radius:8px;'><div>💥 오행: 木({counts['목']}) 火({counts['화']}) 土({counts['토']}) 金({counts['금']}) 水({counts['수']})</div><div>🌟 천을귀인: {guiin}</div><div>🎯 공망: [일] {gong}</div><div>🌪️ 삼재: {samjae}</div></div>
                        """

                    m_tbl = build_bazi_table("♂️", m_name, "남성", m_marital, m_age, m_sol, m_lun, m_time, m_gans, m_jjis, m_ds, m_yb, m_cnt, guiin_map.get(m_ds, '-'), calculate_gongmang(m_ds, m_db), get_samjae(m_yb, curr_j))
                    f_tbl = build_bazi_table("♀️", f_name, "여성", f_marital, f_age, f_sol, f_lun, f_time, f_gans, f_jjis, f_ds, f_yb, f_cnt, guiin_map.get(f_ds, '-'), calculate_gongmang(f_ds, f_db), get_samjae(f_yb, curr_j))

                    # 3-5. 프리미엄 궁합 에세이 분석 가동
                    # [2단계: 대운표 생성 및 에세이 분석의 순차적 격리]
                    try:
                        m_page_un_html = build_daewun_html(m_name, m_ds, m_ms, m_mb, m_yb, m_calc_d, m_order, m_age)
                        f_page_un_html = build_daewun_html(f_name, f_ds, f_ms, f_mb, f_yb, f_calc_d, f_order, f_age)
                        couple_daewun_tables = f"<div style='margin-bottom: 25px;'>{m_page_un_html}<div style='height:15px;'></div>{f_page_un_html}</div>"
                    except Exception as e:
                        couple_daewun_tables = f"<div style='color:red;'>대운표 생성 중 오류 발생</div>"

                    # 3-5. 프리미엄 궁합 에세이 분석 가동
                    gh_engine = UniversalPrintableGunghap(u_name, p_name, male_data_pack, female_data_pack, m_calc_d)
                    gh_engine.run_universal_logic()
                    
                    m_w_val = choyeon_db.get("wolryeong", {}).get(m_ms+m_mb, "시공간")
                    m_i_val = choyeon_db.get("ilju", {}).get(m_ds+m_db, "성품")
                    m_golden = f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em;'><b>{m_name}님</b>은 '{m_w_val}'의 시공간에서, '{m_i_val}'의 성품을 지녔습니다.</p>"

                    f_w_val = choyeon_db.get("wolryeong", {}).get(f_ms+f_mb, "시공간")
                    f_i_val = choyeon_db.get("ilju", {}).get(f_ds+f_db, "성품")
                    f_golden = f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em;'><b>{f_name}님</b>은 '{f_w_val}'의 시공간에서, '{f_i_val}'의 성품을 지녔습니다.</p>"
                    
                    essay_prompt = f"""[SYSTEM ROLE: CHOYEON SIGONG MASTER]
당신은 명리심리상담사 '초연 박사'입니다. 각 목차에 대해 실제 통변 에세이를 작성하십시오.

[MALE_START]
<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; margin-top: 15px;'>1. 사주팔자의 요약</h3>{m_golden}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px;'>1) 타고난 삶의 무대와 기본 성향</span><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>남성 {m_name}님의 격국과 자의형상을 분석하여 삶의 무대를 실제 통변하십시오.</p>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px;'>2) 내 삶의 리듬과 에너지 균형</span><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>남성의 오행 분포와 조후를 기반으로 에너지 리듬을 실제 통변하십시오.</p>
<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; margin-top: 35px;'>2. 성격</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px;'>1) 겉으로 드러난 성격</span><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>남성의 사회적 표면 성격을 실제 통변하십시오.</p>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px;'>2) 감추어진 내 속마음</span><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>남성의 내면과 무의식 기질을 실제 통변하십시오.</p>[MALE_END]
[FEMALE_START]
<h3 style='color:#D50000; font-size: 22px; font-weight: 900; margin-top: 15px;'>1. 사주팔자의 요약</h3>{f_golden}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px;'>1) 타고난 삶의 무대와 기본 성향</span><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>여성 {f_name}님의 삶의 무대를 실제 통변하십시오.</p>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px;'>2) 내 삶의 리듬과 에너지 균형</span><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>여성의 에너지 리듬을 실제 통변하십시오.</p>
<h3 style='color:#D50000; font-size: 22px; font-weight: 900; margin-top: 35px;'>2. 성격</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px;'>1) 겉으로 드러난 성격</span><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>여성의 사회적 표면 성격을 실제 통변하십시오.</p>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px;'>2) 감추어진 내 속마음</span><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>여성의 내면 기질을 실제 통변하십시오.</p>[FEMALE_END]
[GUNGHAP_START]
<h3 style='color: #1B5E20; font-size: 22px; font-weight: 900; margin-top: 10px;'>🍀 두 사람의 운명적 만남에 대하여</h3><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>두 분의 인연을 종합하여 조화로운 만남을 실제 통변하십시오.</p>
<h3 style='color: #1A237E; font-size: 22px; font-weight: 900; margin-top: 35px;'>🌈 커플의 인생 기상도 분석</h3>[COUPLE_DAEWUN_TABLES_HERE]<p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>대운표의 흐름을 보완 관점에서 실제 통변하십시오.</p>
<h4 style='color: #1A237E; font-size: 18px; font-weight: 900; margin-top: 35px;'>💞 커플의 상생과 조화 궁합 분석</h4><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>상생과 조화의 궁합을 실제 통변하십시오.</p>
<h4 style='color: #1A237E; font-size: 18px; font-weight: 900; margin-top: 35px;'>⚓ 조율의 지혜</h4><p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'>인연을 위한 조율의 지혜를 실제 통변하십시오.</p>[GUNGHAP_END]
"""
                    res_text = call_claude_api(essay_prompt, max_tokens=12000)
                    ai_clean = "\n".join([line.lstrip() for line in res_text.split("\n")])
                    
                    import re
                    m_ess, f_ess, g_ess = "", "", ai_clean
                    m_m = re.search(r'\[MALE_START\](.*?)\[MALE_END\]', ai_clean, re.DOTALL)
                    if m_m: m_ess = m_m.group(1).strip()
                    f_m = re.search(r'\[FEMALE_START\](.*?)\[FEMALE_END\]', ai_clean, re.DOTALL)
                    if f_m: f_ess = f_m.group(1).strip()
                    g_m = re.search(r'\[GUNGHAP_START\](.*?)\[GUNGHAP_END\]', ai_clean, re.DOTALL)
                    g_ess = g_m.group(1).strip() if g_m else ai_clean.replace(m_ess, "").replace(f_ess, "")
                    g_ess = g_ess.replace("[COUPLE_DAEWUN_TABLES_HERE]", couple_daewun_tables)

                    # 3-6. 대운 흐름표 빌더 (상하 정렬용 - 타이틀 남색, 상단 바탕 갈색, 십이운성 청색 통일)
                    def build_daewun_html(name, ds, ms, mb, yb, calc_d, order, age):
                        d_str = "순행" if order == 1 else "역행"
                        html = f"<div style='margin-bottom:10px;'><div style='font-size:15px; font-weight:900; color:#1A237E; margin-bottom:5px;'>[ {name}님 대운 흐름표 (대운수: {calc_d}), {d_str} ]</div>"
                        html += f"<div style='display:flex; flex-direction:row-reverse; width:100%; border:2px solid #3E2723; background:white;'>"
                        for i in range(10):
                            val = i*10 + calc_d
                            tc = GAN[(GAN.index(ms)+(i+1)*order)%10]
                            tj = JI[(JI.index(mb)+(i+1)*order)%12]
                            bg = "#FFF9C4" if val <= age < val+10 else "transparent"
                            brd = "1px solid #ccc" if i != 9 else "none"
                            html += f"""<div style='flex:1; border-left:{brd}; text-align:center; padding-bottom:3px; background-color:{bg};'>
                                <div style='background-color:#3E2723; color:#FFFFFF; font-weight:900; padding:4px 0; font-size:11px;'>{val}세</div>
                                <div style='padding:2px; font-size:11px;'>{get_ss(ds,tc)}</div>
                                <div class='color-{get_color(tc)}' style='font-size:15px; font-weight:900;'>{tc}</div>
                                <div class='color-{get_color(tj)}' style='font-size:15px; font-weight:900;'>{tj}</div>
                                <div style='padding:2px; font-size:11px;'>{get_ss(ds,tj)}</div>
                                <div style='font-size:10px; color:#0D47A1; border-top:1px solid #eee; font-weight:bold;'>{get_unsung(ds,tj)}</div>
                                <div style='font-size:10px; color:#C62828; border-top:1px solid #eee;'>{get_12_shinsal(yb, tj)}</div>
                            </div>"""
                        return html + "</div></div>"

                    # 3-6 직후, 파싱 전 안전 선언
                    couple_daewun_tables = "<div style='color:red;'>대운 흐름표 생성 오류</div>"
                    try:
                        m_page_un_html = build_daewun_html(m_name, m_ds, m_ms, m_mb, m_yb, m_calc_d, m_order, m_age)
                        f_page_un_html = build_daewun_html(f_name, f_ds, f_ms, f_mb, f_yb, f_calc_d, f_order, f_age)
                        couple_daewun_tables = f"<div style='margin-bottom: 25px;'>{m_page_un_html}<div style='height:15px;'></div>{f_page_un_html}</div>"
                    except Exception as e:
                        st.error(f"대운표 생성 실패: {e}")

                    # 3-7. AI 프리미엄 심층 에세이 연산 기동
                    m_w_val = choyeon_db.get("wolryeong", {}).get(m_ms+m_mb, "시공간")
                    m_i_val = choyeon_db.get("ilju", {}).get(m_ds+m_db, "성품")
                    m_golden = f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em;'><b>{m_name}님</b>은 '{m_w_val}'의 시공간에서, '{m_i_val}'의 성품을 지녔습니다.</p>"

                    f_w_val = choyeon_db.get("wolryeong", {}).get(f_ms+f_mb, "시공간")
                    f_i_val = choyeon_db.get("ilju", {}).get(f_ds+f_db, "성품")
                    f_golden = f"<p style='font-family: \"Nanum Myeongjo\", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em;'><b>{f_name}님</b>은 '{f_w_val}'의 시공간에서, '{f_i_val}'의 성품을 지녔습니다.</p>"
                    
                    essay_prompt = f"""[SYSTEM ROLE: CHOYEON SIGONG MASTER]
당신은 명리심리상담사 '초연 박사'입니다.

🚨 [출력 절대 형식 및 내용 생성 규칙]
1. 각 소제목 아래에 절대로 '(축약 에세이)', '(이곳에 작성)' 등의 지시용 안내 문구를 그대로 출력하는 행위를 엄격히 금지합니다.
2. 반드시 각 내담자의 오행과 격국, 자의형상을 깊이 통변한 3~4문장 이상의 온전한 실제 분석 내용(해석)을 글로 풀어 쓰십시오.
3. 모든 통변 문장은 HTML 태그 <p style='font-family: "Nanum Myeongjo", serif; font-size: 15px; line-height: 1.8; color: #000; text-indent: 1em; text-align: justify;'> 로 감싸십시오.

[MALE_START]
<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; margin-top: 15px;'>1. 사주팔자의 요약</h3>
{m_golden}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(여기에 남성의 실제 성향 명리 통변 서술)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>
(여기에 남성의 실제 에너지 관리방안 명리 통변 서술)

<h3 style='color:#1A237E; font-size: 22px; font-weight: 900; margin-top: 35px;'>2. 성격</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
(여기에 남성의 표면적 기질 사회적 성격 실제 서술)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>
(여기에 남성의 무의식과 심리적 방어기제 실제 서술)
[MALE_END]

[FEMALE_START]
<h3 style='color:#D50000; font-size: 22px; font-weight: 900; margin-top: 15px;'>1. 사주팔자의 요약</h3>
{f_golden}
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 타고난 삶의 무대와 기본 성향</span>
(여기에 여성의 실제 성향 명리 통변 서술)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 내 삶의 리듬과 에너지 균형</span>
(여기에 여성의 실제 에너지 관리방안 명리 통변 서술)

<h3 style='color:#D50000; font-size: 22px; font-weight: 900; margin-top: 35px;'>2. 성격</h3>
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 15px; margin-bottom: 5px;'>1) 겉으로 드러난 성격</span>
(여기에 여성의 표면적 기질 사회적 성격 실제 서술)
<span class='sub-title' style='display: block; font-size: 18px; font-weight: 900; color: #111; margin-top: 25px; margin-bottom: 5px;'>2) 감추어진 내 속마음</span>
(여기에 여성의 무의식과 심리적 방어기제 실제 서술)
[FEMALE_END]

[GUNGHAP_START]
<h3 style='color: #1B5E20; font-size: 22px; font-weight: 900; margin-top: 10px;'>🍀 두 사람의 운명적 만남에 대하여</h3>
(여기에 두 사람의 인연의 본질에 대한 조화로운 종합 서술)

<h3 style='color: #1A237E; font-size: 22px; font-weight: 900; margin-top: 35px;'>🌈 커플의 인생 기상도 분석</h3>
[COUPLE_DAEWUN_TABLES_HERE]
(여기에 상하 대운표의 흐름을 상호 보완 관점에서 연동 분석한 실제 심층 에세이 서술)

<h4 style='color: #1A237E; font-size: 18px; font-weight: 900; margin-top: 35px;'>💞 커플의 상생과 조화 궁합 분석</h4>
(여기에 겉궁합 속궁합 오행조화를 집대성한 실제 통변 서술)

<h4 style='color: #1A237E; font-size: 18px; font-weight: 900; margin-top: 35px;'>⚓ 조율의 지혜</h4>
(여기에 갈등 인내 극복 및 현실 개운 처방 실제 서술)
[GUNGHAP_END]
"""
                    res_text = call_claude_api(essay_prompt, max_tokens=12000)
                    ai_clean = "\n".join([line.lstrip() for line in res_text.split("\n")])
                    
                    # 3-8. 마커 파싱 시스템 방어막 가동
                    import re
                    m_ess, f_ess, g_ess = "", "", ai_clean
                    
                    # 3-8. 마커 파싱 및 데이터 안전 확보 (방어 로직)
                    m_ess, f_ess, g_ess = "남성 사주 분석 데이터가 준비 중입니다.", "여성 사주 분석 데이터가 준비 중입니다.", ai_clean
                    
                    import re
                    m_m = re.search(r'\[MALE_START\](.*?)\[MALE_END\]', ai_clean, re.DOTALL)
                    if m_m: m_ess = m_m.group(1).strip()
                    
                    f_m = re.search(r'\[FEMALE_START\](.*?)\[FEMALE_END\]', ai_clean, re.DOTALL)
                    if f_m: f_ess = f_m.group(1).strip()
                    
                    g_m = re.search(r'\[GUNGHAP_START\](.*?)\[GUNGHAP_END\]', ai_clean, re.DOTALL)
                    if g_m:
                        g_ess = g_m.group(1).strip()
                    else:
                        g_ess = "궁합 분석 데이터가 준비 중입니다."
                    
                    g_ess = g_ess.replace("[COUPLE_DAEWUN_TABLES_HERE]", couple_daewun_tables)

                    # A4 래퍼 함수 (밑줄 포함 규격 정렬)
                    def wrap_a4(content, title_color="#1A237E", title="[ 초연 시공명리 사주풀이 ]"):
                        return f"<div class='report-page'><div class='vip-inset-frame' style='border-color:{title_color}; padding:20px;'><h1 style='text-align:center; color:{title_color}; font-family:\"Malgun Gothic\", sans-serif; font-weight:900; border-bottom:2px solid {title_color}; padding-bottom:15px; margin-bottom:30px;'>{title}</h1>{content}</div></div>"

                    # 3-9. 스코어 가시화 및 원본 클로징 멘트 복구
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

                    # 3-10. 렌더링 검증 및 최종 출력 (메인 try 블록 내부 유지)
                    try:
                        st.markdown(wrap_a4(f"{m_tbl}<div class='choyeon-premium-report' style='margin-top:20px;'>{m_ess or '내용을 준비 중입니다.'}</div>", "#1A237E", "[ 초연 시공명리 사주풀이 ]"), unsafe_allow_html=True)
                        st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
                        
                        st.markdown(wrap_a4(f"{f_tbl}<div class='choyeon-premium-report' style='margin-top:20px;'>{f_ess or '내용을 준비 중입니다.'}</div>", "#D50000", "[ 초연 시공명리 사주풀이 ]"), unsafe_allow_html=True)
                        st.markdown("<div class='page-break-before'></div>", unsafe_allow_html=True)
                        
                        st.markdown(wrap_a4(g_full_content, "#1B5E20", "[ 초연 시공명리 궁합풀이 ]"), unsafe_allow_html=True)
                    
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🖨️ 초연 시공명리 PDF 저장 및 리포트 인쇄", use_container_width=True, type="secondary"):
                            st.components.v1.html("<script>window.print();</script>", height=0, width=0)

                    except Exception as e:
                        st.error(f"3단계 궁합 종합 분석 가동 장애: {e}")

            # 🚨 드디어 찾은 진범: 바깥쪽 거대 try를 안전하게 닫아주는 문구입니다.
            except Exception as main_e:
                st.error(f"시스템 분석 중 치명적 오류가 발생했습니다: {main_e}")
