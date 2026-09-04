# ==============================================================================
# 🏮 사주박사: 신청접수 ~ AI 감명 ~ 카톡 마케팅 완결 마스터 파이프라인 (ver 86.6)
# ==============================================================================
import streamlit as st
import sqlite3
import os
import uuid
import pandas as pd
from datetime import datetime, date, timedelta
import datetime as dt_mod
import time
import hmac
import hashlib
import json
import requests
import re
import pytz
import html_views
DB_FILE = "choyeon_orders.db"

ADMIN_PASSWORD = "boss!631201"
BASE_URL = "https://choyeon-spacetime.streamlit.app"
KAKAO_CHAT_URL = "http://pf.kakao.com/_xexizSX/chat"

# 💡 [핵심] 신버전 AI와 연동하기 위한 PRODUCT_MAP 정의 (DB 무결성 보호 + 감명서 타이틀 '풀이/추천' 적용)
PRODUCT_MAP = {
    "1-1. 사주팔자 및 총운세 풀이 (정가 22,000원➡️특가 11,000원)": "사주팔자 및 총 운세 풀이",
    "1-2. 올 해 운세 풀이 (정가 11,000원➡️특가 5,500원)": "올 해 운세 풀이",
    "1-3. 이번 달 운세 풀이 (정가 11,000원➡️특가 5,500원)": "이번 달 운세 풀이",
    "1-4. 주간/일일 운세 풀이 (정가 5,500원➡️특가 0원)": "주간 및 일일 운세 풀이",
    "2-1. 재물운 풀이 (정가 22,000원➡️특가 11,000원)": "재물운 특화 풀이",
    "2-2. 직업/진학운 풀이 (정가 22,000원➡️특가 11,000원)": "직업/진학운 특화 풀이",
    "2-3. 연애/결혼운 풀이 (정가 22,000원➡️특가 11,000원)": "연애/결혼운 특화 풀이",
    "2-4. 건강운 풀이 (정가 11,000원➡️특가 5,500원)": "건강운 특화 풀이",
    "2-5. 이사/개업 택일 (정가 11,000원➡️특가 5,500원)": "이사/개업 택일 추천",
    "3-1. 부부/연인 궁합 풀이 (정가 44,000원➡️특가 22,000원)": "연애/결혼운 (궁합) 풀이",
    "3-2. 결혼 택일 추천 (정가 22,000원➡️특가 11,000원)": "결혼 택일 추천",
    "3-3. 출산 택일 추천 (정가 66,000원➡️특가 33,000원)": "출산 택일 추천"
}

U_PRODUCT_LIST = list(PRODUCT_MAP.keys())

TIME_OPTIONS = [
    "시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", 
    "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", 
    "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"
]

# ------------------------------------------------------------------------------
# 🗄️ [데이터베이스 구조 - 24 Columns 신형 장부 엔진]
# ------------------------------------------------------------------------------
def get_db_connection(): return sqlite3.connect(DB_FILE)

def ensure_db_table_exists():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY, created_at TEXT, phone TEXT, email TEXT, name TEXT, gender TEXT,
            marital TEXT, u_cal TEXT, b_year INTEGER, b_month INTEGER, b_day INTEGER, b_time TEXT,
            u_product TEXT, f_name TEXT, f_gender TEXT, f_marital TEXT, f_cal TEXT, f_y INTEGER,
            f_m INTEGER, f_d INTEGER, f_t TEXT, user_concern TEXT, status TEXT, result_html TEXT
        )
    ''')
    try:
        c.execute("ALTER TABLE orders ADD COLUMN pdf_url TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def save_report_to_db(order_id, result_html):
    get_supabase_client().table("orders").update({"result_html": result_html}).eq("order_id", order_id).execute()

def update_order_status(order_id, status):
    get_supabase_client().table("orders").update({"status": status}).eq("order_id", order_id).execute()

def save_pdf_url_to_db(order_id, pdf_url):
    get_supabase_client().table("orders").update({"pdf_url": pdf_url}).eq("order_id", order_id).execute()

def get_supabase_client():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def generate_pdf_bytes(result_html):
    """감명서 HTML을 PDF 바이트로 변환합니다 (미리보기 전용, 저장고 업로드 없음)."""
    from weasyprint import HTML
    font_link = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;900&family=Nanum+Gothic:wght@400;700;800;900&family=Nanum+Myeongjo:wght@400;700;800&display=swap">'
    full_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">{font_link}{html_views.get_global_css()}</head><body>{result_html}</body></html>"""
    return HTML(string=full_html).write_pdf()

def generate_and_upload_pdf(order_id, name, result_html):
    """감명서 HTML을 실제 PDF 파일로 변환하여 Supabase Storage에 저장하고, 공개 다운로드 주소를 반환합니다."""
    try:
        pdf_bytes = generate_pdf_bytes(result_html)
        from supabase import create_client
        supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        file_path = f"{order_id}.pdf"
        supabase.storage.from_("reports").upload(
            file_path, pdf_bytes,
            {"content-type": "application/pdf", "x-upsert": "true"}
        )
        public_url = supabase.storage.from_("reports").get_public_url(file_path)
        return public_url
    except Exception as e:
        st.error(f"🚨 PDF 생성/업로드 오류: {e}")
        return None

# ------------------------------------------------------------------------------
# 📡 [솔라피 (Solapi) 발송 엔진] 
# ------------------------------------------------------------------------------
def get_solapi_auth_header(api_key, api_secret):
    date_str = datetime.now().astimezone().isoformat()
    salt = str(uuid.uuid4().hex)
    combined = date_str + salt
    signature = hmac.new(api_secret.encode('utf-8'), combined.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"HMAC-SHA256 apiKey={api_key}, date={date_str}, salt={salt}, signature={signature}"

def send_solapi_admin_alert(now_str, name, product_summary, base_price, discount_amt, final_price):
    try:
        api_key = st.secrets["SOLAPI_API_KEY"]
        api_secret = st.secrets["SOLAPI_API_SECRET"]
        admin_phone = "01038576727"
        short_time = now_str[:16]
        short_prod = product_summary.split('(')[0].strip()
        msg_body = f"{short_time}/{name}/{short_prod}/{base_price}/{final_price}"
        res = requests.post("https://api.solapi.com/messages/v4/send", 
            headers={"Authorization": get_solapi_auth_header(api_key, api_secret), "Content-Type": "application/json"}, 
            json={"message": {"to": admin_phone, "from": admin_phone, "text": msg_body}}
        )
        return True, "알림 발송 완료"
    except Exception as e:
        return False, str(e)

def send_solapi_custom_message(to_phone, name, msg_body):
    try:
        api_key = st.secrets["SOLAPI_API_KEY"]
        api_secret = st.secrets["SOLAPI_API_SECRET"]
        res = requests.post("https://api.solapi.com/messages/v4/send", 
            headers={"Authorization": get_solapi_auth_header(api_key, api_secret), "Content-Type": "application/json"}, 
            json={"message": {"to": to_phone.replace("-", ""), "from": "01038576727", "text": msg_body}}
        )
        return (True, "발송 성공") if res.status_code == 200 else (False, f"발송 실패: {res.text}")
    except Exception as e: 
        return False, str(e)

# ------------------------------------------------------------------------------
# 0. 🧮 [패키지 연산 엔진]
# ------------------------------------------------------------------------------
def calculate_package_price(selected_products):
    if not selected_products: return 0, 0, 0, 0, 0
    total_original = 0
    total_chuseok = 0
    for item in selected_products:
        prices = re.findall(r'([\d,]+)원', item)
        if len(prices) >= 2:
            total_original += int(prices[0].replace(',', ''))
            total_chuseok += int(prices[1].replace(',', ''))
    return total_original, total_chuseok, 0, int(((total_original - total_chuseok) / total_original) * 100) if total_original > 0 else 0, total_chuseok

# ------------------------------------------------------------------------------
# 🎯 [자동화 마케팅 메시지 제네레이터]
# ------------------------------------------------------------------------------
def generate_smart_marketing_text(row, view_url):
    name, product, concern = row.get('name', '고객'), row.get('u_product', ''), str(row.get('user_concern', '')).replace(' ', '')
    clean_product = re.sub(r'\d-\d\.\s*', '', product).split('(')[0].strip()
    if '+' in clean_product: clean_product = clean_product.split('+')[0].strip() + " 외 패키지"
    
    msg = f"💌 {name}님! 오래 기다리셨습니다.\n마침내 {name}님만을 위한 [{clean_product}] 정밀 분석 감명서가 완성되었어요! 🎉\n\n"
    msg += f"아래 링크를 꾹 눌러서, 인생의 나침반이 되어줄 평생 소장용 리포트를 바로 확인해 보세요.\n(※ 우측 상단의 'PDF 다운로드' 버튼을 누르시면 폰에 평생 간직하실 수 있답니다 📱✨)\n\n"
    msg += f"🔗 감명서 열어보기: {view_url}\n\n"
    msg += f"🎁 [깜짝 후기 이벤트!]\n감명서가 마음에 쏙 드셨다면 따뜻한 후기 한 줄 부탁드려요! 후기 링크를 남겨주시면, 사주박사가 직접 [1개월 정밀 월운 감명서(11,000원 상당)]를 추가로 무료 분석해 드립니다. 🥰 놓치지 마세요!\n\n"
    msg += f"💡 [사주박사의 따뜻한 추가 제안]\n"
    
    if any(kw in concern for kw in ["직업", "취업", "이직", "진로", "시험", "합격"]): msg += f"적어주신 진로와 직업 고민들, 꼼꼼히 읽어보았습니다. [2-2. 직업/진학운 특화 분석]을 통해 내게 가장 잘 맞는 길과 합격운의 타이밍을 찾아보아요! 🎯"
    elif any(kw in concern for kw in ["돈", "재물", "빚", "투자", "사업", "금전"]): msg += f"적어주신 금전에 대한 답답한 고민들, 다 읽어보았습니다. [2-1. 재물운 특화 분석]을 통해 확실한 타개책을 사주박사와 함께 찾아보아요! 💪"
    elif any(kw in concern for kw in ["건강", "수술", "아파", "질병"]): msg += f"무엇보다 가장 중요한 건 건강이랍니다. 내 몸의 취약점과 운기의 흐름을 짚어주는 [2-4. 건강운 특화 분석]도 꼭 챙겨보시길 바라요. 🌿"
    elif any(kw in concern for kw in ["이사", "개업", "오픈"]): msg += f"새로운 시작을 앞두고 계시는군요! 복이 굴러들어오는 완벽한 날을 잡아주는 [2-5. 이사/개업 택일]을 통해 가장 좋은 기운을 끌어당겨 보세요! 🏡✨"
    elif "1-1" in product: msg += f"사주 그릇을 확인하셨으니, 올해 남은 운기가 어떻게 흘러갈지 [1-2. 올 해 운세 상세분석]으로 다가올 기회를 꽉! 잡아보세요. 🍀"
    elif "1-2" in product: msg += f"올해의 큰 흐름을 파악하셨다면, 이번 달의 디테일한 길흉화복을 짚어볼 차례예요! [1-3. 이번 달 운세 상세분석]으로 계획을 세워보세요. 🗓️"
    elif "2-3" in product: msg += f"나의 연애/결혼운을 확인하셨다면, 이제 나와 상대방의 진짜 속마음과 합을 맞춰볼 시간이에요! [3-1. 궁합 풀이]를 강력 추천해 드립니다! 💑"
    elif "3-1" in product: msg += f"두 분의 인연이 참으로 소중합니다. 평생의 복을 좌우할 완벽한 날, [3-2. 결혼 택일]로 가장 눈부신 시작을 준비해 보시는 건 어떨까요? 🕊️"
    elif "3-2" in product: msg += f"두 분의 아름다운 출발을 축하드립니다! 🥳 예쁜 천사를 맞이할 준비가 되셨다면 [3-3. 출산 택일]도 사주박사가 함께할게요! 👶🍼"
    else: msg += f"나의 전체적인 사주 그릇을 확인하셨으니, 올해 남은 운기가 어떻게 흘러갈지 [1-2. 올 해 연운 상세분석]으로 기회를 꽉! 잡아보세요. 🍀"
        
    msg += "\n\n 🔮사주박사🔮를 찾아주셔서 진심으로 감사합니다. 앞으로 펼쳐질 눈부신 날들을 온 마음 다해 응원할게요! 늘 꽃길만 걸으세요! 🌸✨"
    return msg

# ------------------------------------------------------------------------------
# 1. 📱 [고객 모바일 접수 화면]
# ------------------------------------------------------------------------------
def render_customer_order_form():
    ensure_db_table_exists()
    
    EVENT_PERIOD = "[ 8/18 ~ 9/30 ]"
    EVENT_TITLE = "🌕 추석 및 새학기 맞이 반값 특가! 🌕"
    EVENT_DESC_1 = "학생과 청년들의 힘찬 새 출발을 응원하며,<br>기간 한정 <b style='letter-spacing:-0.3px;'>전 상품 50% 특별 할인</b>을 진행합니다."
    EVENT_DESC_2 = "(※ 2개 이상 선택 시 추가 20~30% 패키지 할인!)"

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Nanum+Myeongjo:wght@700&family=Nanum+Pen+Script&display=swap');
        .mobile-box { max-width: 480px; margin: 0 auto; background: #FFFFFF; border: 3px solid #1A237E; border-radius: 15px; padding: 20px; }
        .m-title { font-family: 'Nanum Pen Script', cursive; font-size: 38px; color: #1A237E; text-align: center; margin-bottom: 20px; border-bottom: 2px dashed #1A237E; padding-bottom: 10px; }
        .guide-box { background: #FCFCFD; border: 2px solid #3F51B5; border-radius: 12px; padding: 22px; margin-top: 15px; line-height: 1.8; color: #2D3748; font-family: 'Gowun Dodum', sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .pay-title { font-size: 20px; font-weight: bold; color: #1A237E; text-align: center; margin-bottom: 12px; }
        .bank-info-box { font-family: 'Nanum Myeongjo', serif; background: #F4F6F9; padding: 14px; border-radius: 8px; border-left: 4px solid #1A237E; font-size: 16px; line-height: 1.9; margin: 12px 0; }
        .share-card { background: #FFFDF5; border: 1.5px solid #FFE082; border-radius: 12px; padding: 20px; font-family: 'Gowun Dodum', sans-serif; font-size: 16px; line-height: 1.8; color: #2D3748; }
        .promo-banner { background: #FFF3E0; border: 2px solid #FF9800; border-radius: 12px; padding: 15px; margin-bottom: 20px; text-align: center; font-family: 'Gowun Dodum', sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    </style>
    """, unsafe_allow_html=True)
    
    page_title = "🔮 사주박사 신청완료 🔮" if "submitted_order" in st.session_state else "🔮 사주박사 신청서 🔮"
    st.markdown(f"<div class='m-title'>{page_title}</div>", unsafe_allow_html=True)
    
    if "submitted_order" in st.session_state:
        ord_info = st.session_state["submitted_order"]

        if ord_info["discount_amt"] > 0:
            price_display = f"<s style='color:#757575;'>{ord_info['total_raw']:,}원</s> ➡️ <b style='color:#D50000; font-size:18px;'>{ord_info['final_price']:,}원</b> <span style='color:#2E7D32; font-size:13px; font-weight:bold;'>({ord_info['rate_pct']}% 특가)</span>"
        else:
            price_display = f"<b style='font-size:17px;'>{ord_info['final_price']:,}원</b>"

        st.markdown(f"""
<div class='guide-box'>
<div class='pay-title'>[ 🌸 신청 접수 완료 ! 🌸 ]</div>
<b style='color:#1A237E; font-size:17px;'>{ord_info['name']}</b>님, 소중한 인연에 감사합니다! <br>
신청한 <b>"{ord_info['product_desc']}"</b> 접수가 완벽하게 끝났어요.<br><br>
아래 계좌로 🥰복비를 입금해 주시면 입금확인 후 곧바로 정성껏 사주풀이하여 바로 받아 보실 수 있어용~ 💕
</div>
""", unsafe_allow_html=True)

        display_price_1line = price_display.replace("특가 할인", "특가")

        st.markdown(f"""
<div style='background-color: #F8F9FA; border: 1px solid #E0E0E0; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top: 15px;'>
<div style='font-size: 15.5px; line-height: 1.8; color: #31333F; letter-spacing: -0.5px;'>
💳 <b>국민은행  231 402 - 04 - 133 221</b><br>
👤 <b>예금주: 이 * 호</b><br>
<div style='white-space: nowrap;'>💰 <b>복비:</b> <span style='color: #E53935; font-weight: bold;'>{display_price_1line}</span></div>
</div>
<hr style='border: 0; border-top: 1px dashed #BDBDBD; margin: 15px 0;'>
<div style='text-align: center; color: #E53935; font-weight: bold; font-size: 13.5px; margin-bottom: 12px;'>
※ 신청자 이름과 입금자 이름이 다르면<br>반드시 아래 "카톡 채팅"으로 알려주세요!
</div>
<a href='{KAKAO_CHAT_URL}' target='_blank' style='text-decoration:none;'>
<div style='background-color:#FEE500; color:#191919; text-align:center; padding:12px 15px; border-radius:8px; font-weight:bold; font-size:14.5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); width: 100%;'>
💬 사주박사 카톡 1:1 채팅 문의하기
</div>
</a>
</div>
""", unsafe_allow_html=True)

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.markdown("""
<style>
div.stButton > button { background-color: #4CAF50 !important; color: #FFFFFF !important; border: 1px solid #388E3C !important; font-weight: bold !important; border-radius: 8px !important; }
div.stButton > button:hover, div.stButton > button:active { background-color: #388E3C !important; color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

        if st.button("➕ 새로운 사주풀이 추가 신청하기", use_container_width=True):
            del st.session_state["submitted_order"]
            st.rerun()

        ref_order_link = f"{BASE_URL}/?mode=order&ref={ord_info['order_id']}"
        share_msg = f"친구에게 '사주박사'를 소개하고 너도 한번 봐봐! 👀\\n친구 소개로 같이 신청하면 우리 둘 다 20% 할인 쿠폰 득템 혜택받는다구! ㅎㅎ💥🎉\\n\\n👇 아래 링크에서 신청해봐!\\n{ref_order_link}"

        st.markdown(f"""
<div style='background-color: #FFFDF5; border: 1.5px solid #FFE082; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top: 20px; margin-bottom: 20px;'>
<div style='text-align: center; margin-bottom: 12px;'>
<span style='font-size: 17px; font-weight: bold; color: #E53935;'>🎁 [ Win-Win 친구 소개 이벤트 ]</span>
</div>
<div style='font-size: 14.5px; color: #31333F; line-height: 1.6; text-align: center; margin-bottom: 15px;'>
친구에게 '사주박사'를 소개하고 <br> 너도 한번 봐봐! 👀 친구 소개로 같이 신청하면 <br> 우리 둘 다 <b>20% 할인 쿠폰</b> 득템 혜택받는다구! 💥🎉
</div>
<a href="sms:?&body={share_msg}" style='display:block; text-decoration:none;'>
<div style='background-color:#FEE500; color:#191919; text-align:center; padding:14px 20px; border-radius:10px; font-weight:bold; font-size:15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); width: 100%;'>
🟡 친구에게 카톡/문자 바로 보내기
</div>
</a>
</div>
""", unsafe_allow_html=True)
        return

    st.markdown(f"""
    <div class='promo-banner'>
        <b style='color:#E65100; font-size:17px; letter-spacing:-0.5px;'>{EVENT_PERIOD} <br> {EVENT_TITLE}</b><br>
        <div style='height: 6px;'></div>
        <span style='color:#424242; font-size:14px; line-height: 1.5; letter-spacing:-0.4px;'>
            {EVENT_DESC_1}
        </span><br>
        <span style='color:#1A237E; font-size:13px; font-weight:bold;'>
            {EVENT_DESC_2}
        </span>
    </div>
    """, unsafe_allow_html=True)

    with st.form("choyeon_customer_order_form_final"):
        st.info("👤 **1. 신청자 정보**")
        name = st.text_input("이름 *(필수)", placeholder="이름을 입력하세요")
        st.markdown("""
        <style>
        div[data-testid="stTextInput"] input[disabled] {
            -webkit-text-fill-color: #31333F !important;
            color: #31333F !important;
            opacity: 1 !important;
            background-color: transparent !important;
            cursor: default !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        c_p1, c_p2, c_p3 = st.columns([1, 1.5, 1.5])
        with c_p1: st.text_input("국번", value="010", disabled=True)
        with c_p2: p_mid = st.text_input("연락처 중간 4자리 *(필수)", max_chars=4, placeholder="1234")
        with c_p3: p_end = st.text_input("연락처 끝 4자리 *(필수)", max_chars=4, placeholder="5678")
        memo_info = st.text_input("이메일 (선택사항)", placeholder="예: cy1234@example.com")
        c_g, c_m, c_c = st.columns(3)
        with c_g: gender = st.selectbox("성별", ["여성", "남성"])
        with c_m: marital = st.selectbox("결혼유무", ["미혼", "기혼", "돌싱", "기타"])
        with c_c: u_cal = st.selectbox("양/음력", ["양력", "음력 평달", "음력 윤달"])
        c_y, c_mo, c_d = st.columns(3)
        with c_y: b_year = st.text_input("생년(YYYY) *", max_chars=4, placeholder="1990")
        with c_mo: b_month = st.text_input("월(MM) *", max_chars=2, placeholder="06")
        with c_d: b_day = st.text_input("일(DD) *", max_chars=2, placeholder="15")
        b_time = st.selectbox("태어난 시간", TIME_OPTIONS)

        st.markdown("""
        <style>
        div[data-baseweb="select"] * { white-space: normal !important; word-break: keep-all !important; text-overflow: clip !important; overflow: visible !important; letter-spacing: -1.8px !important; font-size: 13.5px !important; }
        div[data-baseweb="select"] > div { height: auto !important; min-height: 48px !important; padding-top: 6px !important; padding-bottom: 6px !important; padding-left: 4px !important; padding-right: 4px !important; }
        ul[role="listbox"] li, ul[role="listbox"] li * { white-space: normal !important; word-break: keep-all !important; height: auto !important; min-height: 45px !important; text-overflow: clip !important; letter-spacing: -1.8px !important; font-size: 13.5px !important; }
        </style>
        """, unsafe_allow_html=True)

        label_text = "상담 상품 선택  \n:red[*(원하시는 상품을 1개만 선택해 주세요) (필수)*]"
        st.success("🛍️ **2. 상품 선택**")
        
        def format_product_name(item):
            if " (" in item:
                formatted = item.replace(" (", "  \n(")
                formatted = formatted.replace("➡️", ") ➡️ ")
                if formatted.endswith(")"): formatted = formatted[:-1]
                return formatted
            return item

        selected_single = st.radio(
            label=label_text, 
            options=U_PRODUCT_LIST,
            format_func=format_product_name,
            index=0
        )
        
        selected_products = [selected_single]
        
        f_name, f_gender, f_marital, f_cal, f_t = "", "", "", "", "시간 모름"
        f_y, f_m, f_d = "", "", ""
        
        p_tackil_purpose = "이사"
        p_moving_start = date.today()
        p_moving_end = date.today() + timedelta(days=30)
        p_other_text = ""
        
        check_prod = PRODUCT_MAP.get(selected_single, selected_single)
        
        if "2-5" in check_prod:
            st.info("🗓️ **택일 상세 정보 (필수)**")
            p_tackil_purpose = st.radio("택일 목적", ["이사", "개업"])
            col_start, col_end = st.columns(2)
            p_moving_start = col_start.date_input("희망 시작일")
            p_moving_end = col_end.date_input("희망 종료일")
            
        if "4-" in check_prod:
            st.info("📄 **타 감명서 원문 입력 (필수)**")
            p_other_text = st.text_area("비교할 감명서(사주/궁합) 내용을 붙여넣어 주세요.", height=150)

        if any("3-" in PRODUCT_MAP.get(prod, prod) for prod in selected_products) or "4-2" in check_prod:
            st.error("👩‍❤️‍👨 **3. 상대방 정보 (궁합 및 비교용 필수)**")
            f_name = st.text_input("상대방 이름 *(필수)")
            f_c_g, f_c_m, f_c_c = st.columns(3)
            with f_c_g: f_gender = st.selectbox("상대방 성별", ["남성", "여성"])
            with f_c_m: f_marital = st.selectbox("상대방 결혼유무", ["미혼", "기혼", "돌싱", "기타"])
            with f_c_c: f_cal = st.selectbox("상대방 양/음력", ["양력", "음력 평달", "음력 윤달"])
            f_c_y, f_c_mo, f_c_d = st.columns(3)
            with f_c_y: f_y = st.text_input("상대방 생년(YYYY) *", max_chars=4)
            with f_c_mo: f_m = st.text_input("상대방 월(MM) *", max_chars=2)
            with f_c_d: f_d = st.text_input("상대방 일(DD) *", max_chars=2)
            f_t = st.selectbox("상대방 태어난 시간", TIME_OPTIONS)

        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background: #F4F6F9; border-radius: 12px; padding: 20px; border-left: 4px solid #FFCA28; margin-bottom: 15px;'>
            <b style='color:#1A237E; font-size: 16px;'>💡 [ 사주박사 1:1 비밀상담소 ]</b>
            <p style='font-size: 14px; color: #424242; line-height: 1.7; margin-top: 8px; margin-bottom: 0;'>
            혼자 끙끙 앓지 말고, 답답한 고민들을<br> 솔직하게 털어놓아 보세요.<br>
            명리학적 원인 분석과 함께 <br><b>'명쾌한 솔루션'</b>을 알려드릴께요!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        user_concern = st.text_area("✍️ 나만의 고민 털어놓기 (선택사항)", height=100, max_chars=500, placeholder="속상한 일이나 궁금한 점을 자유롭게 적어요~")

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        agree = st.checkbox("개인정보 수집 및 감명 제공에 동의합니다. *(필수)")
        submitted = st.form_submit_button("🏮 사주풀이 신청하기 ", type="primary", use_container_width=True)
        
        if submitted:
            inflow_code = "직접접속"
            try:
                src_val = st.query_params.get("src", "")
                if src_val == "insta": inflow_code = "인스타그램"
                elif src_val == "x" or src_val == "twitter": inflow_code = "트위터(X)"
                elif src_val == "kmong": inflow_code = "크몽"
            except: pass
            
            final_concern = f"[{inflow_code}] {user_concern}" if inflow_code != "직접접속" else user_concern

            meta_data = {}
            if "2-5" in check_prod:
                meta_data['tackil_purpose'] = p_tackil_purpose
                meta_data['moving_start'] = p_moving_start.isoformat()
                meta_data['moving_end'] = p_moving_end.isoformat()
            if "4-" in check_prod:
                meta_data['other_text'] = p_other_text
                
            if meta_data:
                final_concern += f"\n\n---META_START---\n{json.dumps(meta_data)}\n---META_END---"

            if not name.strip() or not p_mid.strip() or not p_end.strip() or not b_year.isdigit() or not selected_products or not agree:
                st.error("🚨 필수 입력값을 확인해 주십시오.")
                return
            
            calc_result = calculate_package_price(selected_products)
            total_original, total_chuseok, pkg_rate_pct, total_rate_pct, final_price = calc_result
            discount_amt = total_original - final_price
            effective_rate = total_rate_pct if total_original > 0 else 0
            base_price_to_show = total_original

            db_product_codes = " + ".join(selected_products)
            clean_ui_names = [re.sub(r'\d-\d\.\s*', '', PRODUCT_MAP.get(p, p)) for p in selected_products]
            ui_product_desc = " + ".join(clean_ui_names) + f" ({final_price:,}원)"
            order_id = str(uuid.uuid4())[:8]
            phone_full = f"010-{p_mid.strip()}-{p_end.strip()}"
            
            kst = pytz.timezone('Asia/Seoul')
            now_str = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')
            
            supply_amount_calc = round(final_price / 1.1)
            vat_amount_calc = final_price - supply_amount_calc

            insert_result = get_supabase_client().table("orders").insert({
                "order_id": order_id, "created_at": now_str, "phone": phone_full, "email": memo_info,
                "name": name.strip(), "gender": gender, "marital": marital, "u_cal": u_cal,
                "b_year": int(b_year), "b_month": int(b_month), "b_day": int(b_day), "b_time": b_time,
                "u_product": db_product_codes, "f_name": f_name, "f_gender": f_gender, "f_marital": f_marital,
                "f_cal": f_cal, "f_y": f_y if f_y else 0, "f_m": f_m if f_m else 0, "f_d": f_d if f_d else 0,
                "f_t": f_t, "user_concern": final_concern, "status": "입금대기", "result_html": "",
                "final_price": final_price, "supply_amount": supply_amount_calc, "vat_amount": vat_amount_calc,
            }).execute()
            
            # 🚨 [테스트용] 실전 발송 전까지는 주석 처리해두셔도 무방합니다.
            # send_solapi_admin_alert(now_str, name.strip(), ui_product_desc, base_price_to_show, discount_amt, final_price)
            
            st.session_state["submitted_order"] = {
                "order_id": order_id, 
                "name": name.strip(), 
                "product_desc": ui_product_desc, 
                "total_raw": base_price_to_show, 
                "discount_amt": discount_amt, 
                "rate_pct": effective_rate, 
                "final_price": final_price
            }
            st.rerun()

# ------------------------------------------------------------------------------
# 2. 👑 [박사님 전용 중앙 통제실 - 3단 서랍장 SPA 로직]
# ------------------------------------------------------------------------------
def render_admin_panel():
    ensure_db_table_exists()
    st.markdown("""
    <style>
        [data-testid="stExpander"] { background-color: #FAFAFC !important; border: 1px solid #E0E7FF !important; border-radius: 12px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.03) !important; margin-bottom: 18px !important; }
        [data-testid="stExpander"] details summary { background-color: #EDF2F9 !important; color: #1E293B !important; font-size: 16px !important; font-weight: 800 !important; border-radius: 12px !important; padding: 10px 15px !important; }
        [data-testid="stExpander"] details[open] summary { border-radius: 12px 12px 0 0 !important; border-bottom: 1.5px dashed #CBD5E1 !important; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("<h3 style='text-align:center;'>👑 관리자 로그인</h3>", unsafe_allow_html=True)
        pwd = st.text_input("관리자 비밀번호", type="password", key="admin_pwd_input")
        
    admin_pwd = st.secrets.get("ADMIN_PASSWORD", ADMIN_PASSWORD) if hasattr(st, "secrets") else ADMIN_PASSWORD
    if pwd == admin_pwd: st.session_state['admin_logged_in'] = True
    if not st.session_state.get('admin_logged_in', False):
        st.info("👈 좌측 사이드바에 관리자 암호를 입력하여 주십시오.")
        return

    st.subheader("👑 초연명리 통합 상황실 (URL 이동 없음)")
    
    resp = get_supabase_client().table("orders").select("*").order("created_at", desc=True).execute()
    df = pd.DataFrame(resp.data) if resp.data else pd.DataFrame(columns=["order_id","created_at","phone","email","name","gender","marital","u_cal","b_year","b_month","b_day","b_time","u_product","f_name","f_gender","f_marital","f_cal","f_y","f_m","f_d","f_t","user_concern","status","result_html","pdf_url","final_price","supply_amount","vat_amount"])
    
    active_gid, active_row = None, None
    pending_orders = df[df["status"] == "입금대기"]
    for _, row in pending_orders.iterrows():
        if f"html_{row['order_id']}" in st.session_state:
            active_gid = row['order_id']
            active_row = row
            break
            
    with st.expander("📊 [서랍장 1] 영업 장부 및 대기열 (항상 유지)", expanded=True):
        col1, col2 = st.columns(2)
        with col1: st.download_button("💾 [1] 고객 기초 장부 (전체 DB)", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="basic_orders.csv", mime="text/csv", use_container_width=True)
        with col2: 
            crm_df = df[['created_at', 'name', 'phone', 'u_product', 'user_concern', 'b_year']].copy()
            st.download_button("💾 [2] 영업 마케팅 타겟 장부 (CRM용)", data=crm_df.to_csv(index=False).encode('utf-8-sig'), file_name="crm_marketing.csv", mime="text/csv", use_container_width=True)
        
        st.markdown("---")
        if pending_orders.empty:
            st.success("대기 중인 신규 주문이 없습니다.")
        else:
            for _, row in pending_orders.iterrows():
                r_oid = row['order_id']
                r_name = row['name']
                r_prod = row['u_product']
                engine_prod = PRODUCT_MAP.get(r_prod.split('+')[0].strip(), "1-1. 사주팔자 및 운세 분석")
                
                with st.container():
                    st.markdown(f"**📌 [{r_name}]** | 📝 상품: {r_prod.split('+')[0][:15]}... | 🕒 신청일: {row['created_at']} | 💬 고민: {row['user_concern']}")
                    
                    if st.session_state.get('app_running') and st.session_state.get('admin_proc_id') == r_oid:
                        st.info(f"⏳ [{r_name}]님의 감명서를 맹렬히 작성 중입니다. 화면을 끄지 마시고 잠시만 대기해 주십시오...")
                    elif active_gid == r_oid:
                        st.success(f"✅ [{r_name}]님 감명 완료! 아래 서랍장 2번, 3번을 열어주세요.")
                    else:
                        btn_col1, btn_col2 = st.columns([1, 1])
                        
                        with btn_col1:
                            if st.button(f"💰 입금 확인 (무소음 감명 시작) - {r_name}", key=f"pay_{r_oid}"):
                                st.session_state['u_n'], st.session_state['u_g'], st.session_state['u_m_stat'], st.session_state['u_c'] = r_name, row['gender'], row['marital'], row['u_cal']
                                st.session_state['s_y'], st.session_state['s_m'], st.session_state['s_d'] = int(row['b_year']), int(row['b_month']), int(row['b_day'])
                                st.session_state['s_t'], st.session_state['s_t_select'] = row['b_time'], row['b_time']
                                
                                if "3-" in engine_prod or "4-2" in engine_prod:
                                    st.session_state['f_n'], st.session_state['f_g'] = row['f_name'], row['f_gender']
                                    st.session_state['f_m_stat'], st.session_state['f_c'] = row.get('f_marital', '선택'), row.get('f_cal', '양력') 
                                    st.session_state['p_y_in'], st.session_state['p_m_in'], st.session_state['p_d_in'], st.session_state['p_t_key'] = int(row.get('f_y', 1980)), int(row.get('f_m', 1)), int(row.get('f_d', 1)), row.get('f_t', '시간 모름')
                                
                                u_concern = str(row.get('user_concern', ''))
                                clean_concern = u_concern
                                if "---META_START---" in u_concern:
                                    try:
                                        parts = u_concern.split("---META_START---")
                                        clean_concern = parts[0].strip()
                                        meta_json = parts[1].split("---META_END---")[0].strip()
                                        meta = json.loads(meta_json)
                                        
                                        if 'tackil_purpose' in meta:
                                            st.session_state['tackil_purpose'] = meta['tackil_purpose']
                                            st.session_state['moving_start'] = date.fromisoformat(meta['moving_start'])
                                            st.session_state['moving_end'] = date.fromisoformat(meta['moving_end'])
                                            
                                        if 'other_text' in meta:
                                            if "4-1" in engine_prod: st.session_state['text_4_1'] = meta['other_text']
                                            elif "4-2" in engine_prod: st.session_state['text_4_2'] = meta['other_text']
                                    except Exception:
                                        pass
                                
                                st.session_state['user_concern'] = clean_concern

                                r_prod_first = r_prod.split('+')[0].strip()
                                
                                if "1-" in r_prod_first: st.session_state['main_category'], st.session_state['sub_category_1'] = "1. 개인 사주팔자 풀이 (종합)", r_prod_first
                                elif "2-" in r_prod_first: st.session_state['main_category'], st.session_state['sub_category_2'] = "2. 테마별 특성화 상담", r_prod_first
                                elif "3-" in r_prod_first: st.session_state['main_category'], st.session_state['sub_category_3'] = "3. 커플 연애/결혼운 (궁합) 풀이", r_prod_first
                                elif "4-" in r_prod_first: st.session_state['main_category'], st.session_state['sub_category_4'] = "4. 타 감명서 비교", r_prod_first
                                
                                st.session_state['admin_proc_id'] = r_oid
                                st.session_state['app_running'] = True
                                st.rerun()

                        with btn_col2:
                            if st.button(f"🔔 미입금 안내 톡 쏘기 - {r_name}", key=f"remind_{r_oid}"):
                                remind_msg = f"💌 [사주박사 안내]\n{r_name}님, 신청하신 감명 접수가 보류 중입니다. 혹시 바쁘셔서 잊으셨을까 봐 안내해 드려요! 😊\n\n💳 국민은행 231402-04-133221 (이*호)\n\n위 계좌로 복비가 입금되면 즉시 박사님의 정밀 분석이 시작됩니다. (입금자명이 다르다면 카톡 부탁드려요!) 🌸"
                                if row['phone']:
                                    # 🚨 [테스트용] 실전 발송 전까지는 주석 처리해두셔도 무방합니다.
                                    # send_solapi_custom_message(row['phone'], r_name, remind_msg)
                                    st.toast(f"✅ {r_name}님께 미입금 안내 문자를 발송했습니다!")

    if active_gid:
        gid = active_gid
        row = active_row
        with st.expander(f"🔍 [서랍장 2] 감명서 미리보기 및 AI 수정 스튜디오 ({row['name']}님)", expanded=True):
            st.components.v1.html(st.session_state[f"html_{gid}"], height=500, scrolling=True)
            st.markdown("---")
            st.markdown("#### 📝 AI 수정 지시사항 (선택)")
            st.caption("AI의 문투나 내용이 맘에 들지 않으면 아래에 지시사항(ex: '직업운 부분을 더 긍정적으로 써줘')을 적어주세요.")
            feedback_text = st.text_input("지시사항 입력", key=f"fb_{gid}", placeholder="예: 재물운 파트에 투자 유의 내용을 강조해 줘")
            
            if st.session_state.get('app_running') and st.session_state.get('admin_proc_id') == gid:
                st.warning("⏳ AI가 지시사항을 100% 반영하여 감명서를 다시 쓰고 있습니다. 잠시만 대기해 주십시오...")
            else:
                if st.button("🔴 AI 감명서 재생성 해! ", type="secondary"):
                    st.session_state['ai_feedback_prompt'] = feedback_text
                    st.session_state['app_running'] = True
                    st.session_state['admin_proc_id'] = gid
                    st.rerun() 

            st.markdown("---")
            if st.button("📄 PDF 미리보기 생성", key=f"pdf_preview_btn_{gid}"):
                with st.spinner("📄 실제 PDF 결과물을 만드는 중... (저장고에는 저장되지 않습니다)"):
                    try:
                        st.session_state[f"pdf_preview_{gid}"] = generate_pdf_bytes(st.session_state[f"html_{gid}"])
                        st.success("✅ PDF 생성 완료! 아래 버튼으로 다운로드해서 확인하세요.")
                    except Exception as e:
                        st.error(f"🚨 PDF 미리보기 생성 오류: {e}")

            if f"pdf_preview_{gid}" in st.session_state:
                st.download_button(
                    label="⬇️ 미리보기 PDF 다운로드",
                    data=st.session_state[f"pdf_preview_{gid}"],
                    file_name=f"{row['name']}_미리보기.pdf",
                    mime="application/pdf",
                    key=f"pdf_download_{gid}"
                )
                
        with st.expander(f"💌 [서랍장 3] 카톡 마케팅 발송소 ({row['name']}님)", expanded=True):
            if f"sms_{gid}" not in st.session_state:
                view_url = f"{BASE_URL}/?mode=view&code={gid}"
                st.session_state[f"sms_{gid}"] = generate_smart_marketing_text(row, view_url)
            
            st.markdown("#### 💡 영업부가 작성해 온 [맞춤형 1:1 타겟팅 영업 문자] 입니다.")
            st.info(st.session_state[f"sms_{gid}"])
            
            if st.button("🟢 최종 발송 및 완료 처리 해!", type="primary"):
                save_report_to_db(gid, st.session_state[f"html_{gid}"])
                update_order_status(gid, "분석완료")

                with st.spinner("📄 PDF 파일을 만들어 저장고에 안전하게 저장하는 중..."):
                    pdf_url = generate_and_upload_pdf(gid, row['name'], st.session_state[f"html_{gid}"])
                if pdf_url:
                    save_pdf_url_to_db(gid, pdf_url)
                    st.success(f"📄 PDF 저장 완료: {pdf_url}")
                else:
                    st.warning("⚠️ PDF 생성에 실패했습니다. 기존 링크 문자로 발송됩니다.")

                if row['phone']:
                    st.toast("⏳ 발송 중입니다...")
                    if pdf_url:
                        final_msg = f"[초연 시공명리] {row['name']}님, 감명서가 완성되었습니다.\n아래 파일을 눌러 바로 확인하세요.\n{pdf_url}"
                    else:
                        final_msg = st.session_state[f"sms_{gid}"]
                    # 🚨 [테스트용] 실전 발송 전까지는 주석 처리해두셔도 무방합니다.
                    # send_solapi_custom_message(row['phone'], row['name'], final_msg)
                
                st.session_state.pop(f"html_{gid}", None)
                st.session_state.pop(f"sms_{gid}", None)
                st.session_state.pop(f"pdf_preview_{gid}", None)
                st.session_state.pop('ai_feedback_prompt', None)
                st.session_state.pop('admin_proc_id', None)
                st.success(f"✅ [{row['name']}]님 발송 완료!")
                time.sleep(2)
                st.rerun()

# ------------------------------------------------------------------------------
# 3. 📜 [고객 전용 결과 열람창] 
# ------------------------------------------------------------------------------
def render_view_page(order_id):
    resp = get_supabase_client().table("orders").select("*").eq("order_id", order_id).execute()
    df = pd.DataFrame(resp.data)

    if df.empty: st.error("존재하지 않거나 만료된 링크입니다."); return
    row = df.iloc[0]
    if row.get('status', '') != "분석완료" or not row.get('result_html', ''):
        st.warning(f"열일 중! 💦 뚝딱뚝딱~ 현재 {row.get('name','고객')}님의 사주를 제가 꼼꼼하게 분석하고 있어요. 🧐✨ 입금 확인 후 하루(24시간) 안에는 무조건 도착하니 쪼금만 기다려주세요! 완성되면 카톡/문자로 알림 팍! 쏴드릴게요! 🚀")
        return
    import html_views
    st.markdown(html_views.get_global_css(), unsafe_allow_html=True)
    st.markdown("<style>@media print { header {visibility: hidden;} footer {visibility: hidden;} .stApp [data-testid='stToolbar'] {display: none;} button {display: none !important;} }</style>", unsafe_allow_html=True)
    st.markdown('<button type="button" style="display:block; width:100%; background-color:#c9a764; color:white; padding:15px; border-radius:10px; border:none; font-weight:bold; margin-bottom:15px; cursor:pointer;" onclick="window.print();">📄 평생 소장용 PDF 다운로드</button>', unsafe_allow_html=True)
    st.markdown(str(row['result_html']).strip(), unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 💡 최상위 라우터
# ------------------------------------------------------------------------------
def get_safe_query_param(key):
    try:
        if hasattr(st, "query_params"):
            val = st.query_params.get(key, "")
            if isinstance(val, list): return str(val[0]) if len(val) > 0 else ""
            return str(val)
        else:
            params = st.experimental_get_query_params()
            if key in params: return str(params[key][0]) if len(params[key]) > 0 else ""
            return ""
    except Exception: return ""

def run_pipeline_router():
    mode = get_safe_query_param("mode")
    code = get_safe_query_param("code")
    
    if mode == "order": 
        render_customer_order_form()
        st.stop()
    elif mode == "admin": 
        render_admin_panel()
        if st.session_state.get('app_running', False):
            return 
        st.stop()
    elif mode == "view": 
        if code: render_view_page(code)
        else: st.warning("⚠️ 올바른 링크로 접속해 주세요.")
        st.stop()
