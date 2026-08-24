# ==============================================================================
# 🏮 사주박사: 신청접수 ~ AI 감명 ~ 카톡 마케팅 완결 마스터 파이프라인 (ver 85.0)
# ==============================================================================
import streamlit as st
import sqlite3
import os
import uuid
import pandas as pd
from datetime import datetime
import time
import hmac
import hashlib
import json
import requests
import re
import pytz

DB_FILE = "choyeon_orders.db"
ADMIN_PASSWORD = "boss!631201"
BASE_URL = "https://choyeon-spacetime.streamlit.app"
KAKAO_CHAT_URL = "http://pf.kakao.com/_xexizSX/chat"

# 💡 [핵심] 신버전 AI와 연동하기 위한 PRODUCT_MAP 정의 (구버전의 PRODUCT_LIST 통합)
PRODUCT_MAP = {
    "사주팔자 및 운세 (정가 22,000원➡️특가 11,000원)": "사주팔자 및 운세 분석",
    "올 해 운세 (정가 11,000원➡️특가 5,500원)": "올 해 운세 상세분석",
    "이번 달 운세 (정가 11,000원➡️특가 5,500원)": "이번 달 운세 상세분석",
    "주간/일일 운세 (정가 4,400원➡️특가 2,200원)": "이번 주간/일 운세",
    "재물운 (정가 22,000원➡️특가 11,000원)": "재물운 특화",
    "직업/진학운 (정가 22,000원➡️특가 11,000원)": "직업/진학운 특화",
    "연애/결혼운 (정가 22,000원➡️특가 11,000원)": "연애/결혼운 특화",
    "건강운 (정가 11,000원➡️특가 5,500원)": "건강운 특화",
    "이사/개업 택일 (정가 11,000원➡️특가 5,500원)": "이사/개업 택일",
    "부부/연인 궁합 (정가 44,000원➡️특가 22,000원)": "연애/결혼운 (궁합)",
    "결혼 택일 (정가 22,000원➡️특가 11,000원)": "결혼 택일 특화",
    "출산 택일 (정가 66,000원➡️특가 33,000원)": "출산 택일 특화"
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
    conn.commit()
    conn.close()

def save_report_to_db(order_id, result_html):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE orders SET result_html = ? WHERE order_id = ?", (result_html, order_id))
    conn.commit()
    conn.close()

def update_order_status(order_id, status):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
    conn.commit()
    conn.close()

# ------------------------------------------------------------------------------
# 📡 [솔라피 (Solapi) 발송 엔진] 
# 💡 스위치 조작법: 
#    - 실전 발송이 필요할 땐 ⛔[테스트 모드] 구역을 전체 주석(#) 처리하고, 
#    - 🟢[실전 모드] 구역의 주석(#)을 전부 해제해 주십시오.
# ------------------------------------------------------------------------------
def get_solapi_auth_header(api_key, api_secret):
    import hmac, hashlib
    date_str = datetime.now().astimezone().isoformat()
    salt = str(uuid.uuid4().hex)
    combined = date_str + salt
    signature = hmac.new(api_secret.encode('utf-8'), combined.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"HMAC-SHA256 apiKey={api_key}, date={date_str}, salt={salt}, signature={signature}"

def send_solapi_admin_alert(now_str, name, product_summary, base_price, discount_amt, final_price):
    # 🟢 [관리자 알림 실전 모드] 고객 신청 시 박사님 폰으로 즉시 문자 발송!
    try:
        import requests
        import streamlit as st
        api_key = st.secrets["SOLAPI_API_KEY"]
        api_secret = st.secrets["SOLAPI_API_SECRET"]
        admin_phone = "01038576727" # 박사님 핸드폰 번호
        
        msg_body = f"[신규접수] {name}님 / {product_summary} / 청구액: {final_price:,}원"
        
        res = requests.post("https://api.solapi.com/messages/v4/send", 
            headers={"Authorization": get_solapi_auth_header(api_key, api_secret), "Content-Type": "application/json"}, 
            json={"message": {"to": admin_phone, "from": admin_phone, "text": msg_body}}
        )
        return True, "알림 발송 완료"
    except Exception as e:
        return False, str(e)

def send_solapi_admin_alert(now_str, name, product_summary, base_price, discount_amt, final_price):
    return True, "성공" # 관리자 알림은 비용 절감을 위해 현재 단순히 패스하도록 처리
    # ==============================================================================
    # ⛔ [테스트 모드] (현재 켜짐) : 돈이 나가지 않고 발송 흉내만 냅니다.
    # ==============================================================================
    # try:
    #     time.sleep(0.5) # 테스트용 딜레이
    #     return True, "[테스트 모드] 발송 성공 (비용 미청구)"
    # except Exception as e: 
    #     return False, str(e)

def send_solapi_custom_message(to_phone, name, msg_body):
    # 🟢 [고객 발송 실전 모드] 서랍장 3번에서 버튼 클릭 시 고객에게 마케팅 문자 발송!
    try:
        import requests
        import streamlit as st
        api_key = st.secrets["SOLAPI_API_KEY"]
        api_secret = st.secrets["SOLAPI_API_SECRET"]
        
        res = requests.post("https://api.solapi.com/messages/v4/send", 
            headers={"Authorization": get_solapi_auth_header(api_key, api_secret), "Content-Type": "application/json"}, 
            json={"message": {"to": to_phone.replace("-", ""), "from": "01038576727", "text": msg_body}}
        )
        return (True, "🟢 [실전 모드] 실제 발송 성공!") if res.status_code == 200 else (False, f"발송 실패: {res.text}")
    except Exception as e: 
        return False, str(e)

# ------------------------------------------------------------------------------
# 0. 🧮 [패키지 연산 엔진 - 다중 할인 삭제 & 단순 합산 버젼 (업셀링 전략)]
# ------------------------------------------------------------------------------
def calculate_package_price(selected_products):
    if not selected_products: return 0, 0, 0, 0, 0
    total_original = 0
    total_chuseok = 0
    
    import re

    for item in selected_products:
        # 💡 상품명 안에서 '원' 글자 바로 앞에 있는 숫자 덩어리를 찾습니다.
        prices = re.findall(r'([\d,]+)원', item)
        
        if len(prices) >= 2:
            orig_str = prices[0].replace(',', '')  # 정가
            chu_str = prices[1].replace(',', '')   # 특가(할인가)
            
            # 단순 합산 누적
            total_original += int(orig_str)
            total_chuseok += int(chu_str)
        
    # 💡 다중상품 추가 할인(20~30%) 로직 완전 삭제! 
    # 패키지 할인율(pkg_rate_pct)은 무조건 0으로 세팅하고, 최종 가격은 특가 합산 금액으로 픽스합니다.
    pkg_rate_pct = 0
    final_price = total_chuseok 
        
    # (참고) 원래 정가 다 합친 것 대비 현재 특가가 얼마나 싼지 '총 할인율'만 보여줍니다.
    total_rate_pct = int(((total_original - final_price) / total_original) * 100) if total_original > 0 else 0
    
    return total_original, total_chuseok, pkg_rate_pct, total_rate_pct, final_price

# ------------------------------------------------------------------------------
# 🎯 [자동화 마케팅 메시지 제네레이터 - 2030 감성 & 사주박사 브랜드 통일]
# ------------------------------------------------------------------------------
def generate_smart_marketing_text(row, view_url):
    name, product, concern = row.get('name', '고객'), row.get('u_product', ''), str(row.get('user_concern', '')).replace(' ', '')
    b_year = int(row.get('b_year', 1980))
    age = datetime.now().year - b_year + 1
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
# 1. 📱 [고객 모바일 접수 화면] (할인 + 공유 + 감성UI + 유입추적 통합 마스터)
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
    
    st.markdown("<div class='m-title'>🔮 사주박사 신청서 🔮</div>", unsafe_allow_html=True)
    
    if "submitted_order" in st.session_state:
        ord_info = st.session_state["submitted_order"]
        if ord_info["discount_amt"] > 0:
            price_display = f"<s style='color:#757575;'>{ord_info['total_raw']:,}원</s> ➡️ <b style='color:#D50000; font-size:18px;'>{ord_info['final_price']:,}원</b> <span style='color:#2E7D32; font-size:13px; font-weight:bold;'>({ord_info['rate_pct']}% 특가 할인)</span>"
        else:
            price_display = f"<b style='font-size:17px;'>{ord_info['final_price']:,}원</b>"

        st.markdown(f"""
        <div class='guide-box'>
        <div class='pay-title'>[ 🌸 신청이 예쁘게 접수 완료! 🌸 ]</div>
        <b style='color:#1A237E; font-size:17px;'>{ord_info['name']}</b>님, 소중한 인연에 감사합니다! 🥰<br>
        신청하신 <b>"{ord_info['product_desc']}"</b> 접수가 완벽하게 끝났어요.<br><br>
        박사님께서 정성껏 사주를 분석하실 수 있도록, 아래 계좌로 복비를 입금해 주시면 확인 후 곧바로 정밀 감명이 시작됩니다! 조금만 기다려 주세요~ 💕
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='bank-info-box'>
        💳 <b>국민은행 231402-04-133221</b><br>
        👤 <b>예금주: 이 * 호</b><br>
        💰 <b>복비:</b> {price_display}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='guide-box' style='margin-top:10px;'>
        <span style='color:#1A237E; font-weight:bold;'>※ 신청자 이름이랑 입금자 이름이 다르면 <br> 카톡 채널로 알려주세요!</span><br>
        <div style='margin-top: 10px; margin-bottom: 8px;'>
            <a href='{KAKAO_CHAT_URL}' target='_blank' style='text-decoration:none;'>
                <div style='background-color:#FEE500; color:#191919; text-align:center; padding:10px 15px; border-radius:8px; font-weight:bold; font-size:14px; box-shadow: 0 2px 4px rgba(0,0,0,0.08);'>
                    💬 사주박사 카톡 1:1 채팅 문의하기
                </div>
            </a>
        </div>
        <hr style='border: 0; border-top: 1px dashed #BDBDBD; margin: 12px 0;'>
        🎁 <b>[ Win-Win 친구 소개 이벤트 ]</b><br>
        친구에게 '사주박사'를 소개해 주세요. 소개받은 친구와 나 <b>두 사람 모두에게</b> <b>[30% 할인 쿠폰]</b>을 팍팍 쏩니다! 💸
        </div>
        """, unsafe_allow_html=True)

        ref_order_link = f"{BASE_URL}/?mode=order&ref={ord_info['order_id']}"
        share_title = "🔮 사주박사 - 내 인생 스포일러"
        share_msg = f"소름 돋는 인생 스포일러, 너도 한번 봐봐! 👀\\n친구 소개로 같이 신청하면 우리 둘 다 30% 할인 쿠폰 득템 혜택! 🎁\\n\\n👇 아래 링크에서 신청해봐!\\n{ref_order_link}"

        st.markdown(f"""
        <div style='height: 10px;'></div>
        <div style='text-align:center; font-family: "Gowun Dodum", sans-serif; font-size:18px; font-weight:bold; margin-bottom:10px; color:#1A237E;'>
        💬 친구에게 사주박사 공유하고 함께 혜택 받기
        </div>
        <div class='share-card'>
        <div style='text-align:center; margin: 15px 0;'>
            <button type="button" 
               onclick="
                    if (navigator.share) {{
                        navigator.share({{
                            title: '{share_title}',
                            text: `{share_msg}`,
                            url: '{ref_order_link}'
                        }}).catch(function(e){{}});
                    }} else {{
                        window.open('sms:?&body=' + encodeURIComponent(`{share_msg}`));
                    }}
               " 
               style='display:block; width:100%; border:none; background-color:#FEE500; color:#191919; border-radius:10px; padding:14px 20px; font-size:16px; font-weight:bold; box-shadow: 0 2px 5px rgba(0,0,0,0.1); font-family: \"Gowun Dodum\", sans-serif; cursor:pointer;'>
                🟡 터치해서 친구에게 카톡/문자 바로 보내기
            </button>
        </div>
        <span style='color:#757575; font-size:13px;'>※ 신청 후 우측 아래의 "크라운 왕관"을 터치하여 "링크 복사"하여 카톡/문자를 베프에게 보내세요.</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        if st.button("➕ 새로운 사주풀이 추가 신청하기", use_container_width=True):
            del st.session_state["submitted_order"]
            st.rerun()
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
        name = st.text_input("이름 *(필수)", placeholder="성함을 입력하세요")
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

        # (박사님이 찾으신 부분을 이 코드로 통째로 덮어쓰세요!)
        label_text = "상담 상품 선택 \n:red[*(원하시는 상품을 1개만 선택해 주세요) (필수)*]"
        st.success("🛍️ **2. 상품 선택**")
        
        # 💡 selectbox는 기본적으로 무언가 1개를 무조건 고르게 하므로, 첫 줄에 '안내 문구'를 넣습니다.
        options_with_placeholder = ["상담 상품을 선택해 주세요 (클릭)"] + U_PRODUCT_LIST
        selected_single = st.selectbox(label=label_text, options=options_with_placeholder)
        
        # 💡 뒷단(계산기, DB)이 고장 나지 않도록 고른 1개를 리스트[]로 포장해 줍니다.
        if selected_single != "상담 상품을 선택해 주세요 (클릭)":
            selected_products = [selected_single]
        else:
            selected_products = []
        
        f_name, f_gender, f_marital, f_cal, f_t = "", "", "", "", "시간 모름"
        f_y, f_m, f_d = "", "", ""
        
        if any("3-" in PRODUCT_MAP.get(prod, prod) for prod in selected_products):
            st.error("👩‍❤️‍👨 **3. 상대방 정보 (궁합 및 택일용 필수)**")
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
            # 🚀 [유입 경로 추적 로직]
            inflow_code = "직접접속"
            try:
                src_val = st.query_params.get("src", "")
                if src_val == "insta": inflow_code = "인스타그램"
                elif src_val == "x" or src_val == "twitter": inflow_code = "트위터(X)"
                elif src_val == "kmong": inflow_code = "크몽"
            except: pass
            
            final_concern = f"[{inflow_code}] {user_concern}" if inflow_code != "직접접속" else user_concern

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
            
            conn = get_db_connection()
            c = conn.cursor()
            # 💡 [핵심] 24-Column DB (AI 엔진용) 데이터 삽입
            c.execute('INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
                      (order_id, now_str, phone_full, memo_info, name.strip(), gender, marital, u_cal, int(b_year), int(b_month), int(b_day), b_time, db_product_codes, f_name, f_gender, f_marital, f_cal, f_y if f_y else 0, f_m if f_m else 0, f_d if f_d else 0, f_t, final_concern, "입금대기", ""))
            conn.commit()
            conn.close()
            send_solapi_admin_alert(now_str, name.strip(), ui_product_desc, base_price_to_show, discount_amt, final_price)
            
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
    
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM orders ORDER BY created_at DESC", conn)
    conn.close()
    
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
                        # 💡 [버튼 2개 나란히 배치] 입금확인 버튼 & 미입금 알림 버튼
                        btn_col1, btn_col2 = st.columns([1, 1])
                        
                        with btn_col1:
                            if st.button(f"💰 입금 확인 (무소음 감명 시작) - {r_name}", key=f"pay_{r_oid}"):
                                st.session_state['u_n'], st.session_state['u_g'], st.session_state['u_m_stat'], st.session_state['u_c'] = r_name, row['gender'], row['marital'], row['u_cal']
                                st.session_state['s_y'], st.session_state['s_m'], st.session_state['s_d'] = int(row['b_year']), int(row['b_month']), int(row['b_day'])
                                st.session_state['s_t'], st.session_state['s_t_select'] = row['b_time'], row['b_time']
                                if "3-" in engine_prod:
                                    st.session_state['f_n'], st.session_state['f_g'] = row['f_name'], row['f_gender']
                                    st.session_state['f_m_stat'], st.session_state['f_c'] = row.get('f_marital', '선택'), row.get('f_cal', '양력') 
                                    st.session_state['p_y_in'], st.session_state['p_m_in'], st.session_state['p_d_in'], st.session_state['p_t_key'] = int(row.get('f_y', 1980)), int(row.get('f_m', 1)), int(row.get('f_d', 1)), row.get('f_t', '시간 모름')
                                
                                if "1-" in engine_prod: st.session_state['main_category'], st.session_state['sub_category_1'] = "1. 사주팔자 및 운세 풀이 (종합)", engine_prod
                                elif "2-" in engine_prod: st.session_state['main_category'], st.session_state['sub_category_2'] = "2. 테마별 특성화 상담", engine_prod
                                elif "3-" in engine_prod: st.session_state['main_category'], st.session_state['sub_category_3'] = "3. 연애/결혼운 (궁합) 풀이", engine_prod
                                
                                st.session_state['admin_proc_id'] = r_oid
                                st.session_state['app_running'] = True
                                st.rerun()

                        with btn_col2:
                            # 💡 [핵심 추가] 미입금 고객 콕 찌르기 버튼
                            if st.button(f"🔔 미입금 안내 톡 쏘기 - {r_name}", key=f"remind_{r_oid}"):
                                remind_msg = f"💌 [사주박사 안내]\n{r_name}님, 신청하신 감명 접수가 보류 중입니다. 혹시 바쁘셔서 잊으셨을까 봐 안내해 드려요! 😊\n\n💳 국민은행 231402-04-133221 (이*호)\n\n위 계좌로 복비가 입금되면 즉시 박사님의 정밀 분석이 시작됩니다. (입금자명이 다르다면 카톡 부탁드려요!) 🌸"
                                if row['phone']:
                                    send_solapi_custom_message(row['phone'], r_name, remind_msg)
                                    st.toast(f"✅ {r_name}님께 미입금 안내 문자를 발송했습니다!")

    if active_gid:
        gid = active_gid
        row = active_row
        
        with st.expander(f"🔍 [서랍장 2] 감명서 미리보기 및 AI 조련소 ({row['name']}님)", expanded=True):
            st.components.v1.html(st.session_state[f"html_{gid}"], height=500, scrolling=True)
            st.markdown("---")
            st.markdown("#### 📝 AI 수정 지시사항 (선택)")
            st.caption("AI의 문투나 내용이 맘에 들지 않으면 아래에 지시사항(ex: '직업운 부분을 더 긍정적으로 써줘')을 적어주세요.")
            feedback_text = st.text_input("지시사항 입력", key=f"fb_{gid}", placeholder="예: 재물운 파트에 투자 유의 내용을 강조해 줘")
            
            if st.session_state.get('app_running') and st.session_state.get('admin_proc_id') == gid:
                st.warning("⏳ AI가 지시사항을 100% 반영하여 감명서를 다시 쓰고 있습니다. 잠시만 대기해 주십시오...")
            else:
                if st.button("🔴 AI 다시 돌려! (지시사항 반영 재생성)", type="secondary"):
                    st.session_state['ai_feedback_prompt'] = feedback_text
                    st.session_state['app_running'] = True
                    st.session_state['admin_proc_id'] = gid
                    st.rerun() 
                
        with st.expander(f"💌 [서랍장 3] 카톡 마케팅 발송소 ({row['name']}님)", expanded=True):
            if f"sms_{gid}" not in st.session_state:
                view_url = f"{BASE_URL}/?mode=view&code={gid}"
                st.session_state[f"sms_{gid}"] = generate_smart_marketing_text(row, view_url)
            
            st.markdown("#### 💡 영업부가 작성해 온 [맞춤형 1:1 타겟팅 영업 문자] 입니다.")
            st.info(st.session_state[f"sms_{gid}"])
            
            if st.button("🟢 영업부 일 잘했네! 최종 발송 및 완료 처리", type="primary"):
                save_report_to_db(gid, st.session_state[f"html_{gid}"])
                update_order_status(gid, "분석완료")
                if row['phone']:
                    st.toast("⏳ [테스트 모드] 발송 중입니다...")
                    send_solapi_custom_message(row['phone'], row['name'], st.session_state[f"sms_{gid}"])
                
                st.session_state.pop(f"html_{gid}", None)
                st.session_state.pop(f"sms_{gid}", None)
                st.session_state.pop('ai_feedback_prompt', None)
                st.session_state.pop('admin_proc_id', None)
                st.success(f"✅ [{row['name']}]님 발송 완료! (테스트 모드로 비용 미청구)")
                time.sleep(2)
                st.rerun()

# ------------------------------------------------------------------------------
# 3. 📜 [고객 전용 결과 열람창] 
# ------------------------------------------------------------------------------
def render_view_page(order_id):
    ensure_db_table_exists()
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM orders WHERE order_id='{order_id}'", conn)
    conn.close()
    if df.empty: st.error("존재하지 않거나 만료된 링크입니다."); return
    row = df.iloc[0]
    if row.get('status', '') != "분석완료" or not row.get('result_html', ''):
        st.warning(f"열일 중! 💦 뚝딱뚝딱~ 현재 {row.get('name','고객')}님의 사주를 제가 꼼꼼하게 분석하고 있어요. 🧐✨ 입금 확인 후 하루(24시간) 안에는 무조건 도착하니 쪼금만 기다려주세요! 완성되면 카톡으로 알림 팍! 쏴드릴게요! 🚀")
        return
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
