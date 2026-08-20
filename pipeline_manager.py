# ==============================================================================
# 🏮 사주박사: 신청접수 ~ 수동 입금승인 ~ 솔라피 자동발송 완결 파이프라인 (ver 75.1)
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
import urllib.parse

DB_FILE = "choyeon_orders.db"
LEDGER_FILE = "사주박사_비밀장부.csv"
ADMIN_PASSWORD = "boss!631201"  # 박사님 전용 관리자 암호
BASE_URL = "https://choyeon-spacetime.streamlit.app"
KAKAO_CHAT_URL = "http://pf.kakao.com/_xexizSX/chat"

# 12개 정식 상품 체계 (추석특가 50% 할인 적용 - 앵커링 효과)
PRODUCT_LIST = [
    "1-1. 사주팔자 및 평생 총운 풀이 (정가 22,000원 ➡️ 추석특가 11,000원)",
    "1-2. 올 해 (특정 연도) 운세 상세분석 (정가 11,000원 ➡️ 추석특가 5,500원)",
    "1-3. 이번 달 (특정 월) 운세 상세분석 (정가 11,000원 ➡️ 추석특가 5,500원)",
    "1-4. 이번 주간 및 일진 운세 (정가 4,400원 ➡️ 추석특가 2,200원)",
    "2-1. 재물운 & 자산 축적 타이밍 특화 (정가 22,000원 ➡️ 추석특가 11,000원)",
    "2-2. 직업/진로/이직/승진운 특화 (정가 22,000원 ➡️ 추석특가 11,000원)",
    "2-3. 연애/결혼운 & 사전 흉화예방 특화 (정가 22,000원 ➡️ 추석특가 11,000원)",
    "2-4. 건강운 & 조토극수 체질분석 특화 (정가 11,000원 ➡️ 추석특가 5,500원)",
    "2-5. 이사 및 개업 택일 특화 (정가 11,000원 ➡️ 추석특가 5,500원)",
    "3-1. 부부/연인 정밀 궁합 풀이 (정가 44,000원 ➡️ 추석특가 22,000원)",
    "3-2. 백년가약 결혼 택일 (정가 22,000원 ➡️ 추석특가 11,000원)",
    "3-3. 명품 출산 택일 (Top 5 길일) (정가 66,000원 ➡️ 추석특가 33,000원)"
]

TIME_OPTIONS = [
    "시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시",
    "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시",
    "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시",
    "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시",
    "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"
]

# ------------------------------------------------------------------------------
# 📡 [솔라피 (Solapi) 공통 암호화 함수]
# ------------------------------------------------------------------------------
def get_solapi_auth_header(api_key, api_secret):
    date_str = datetime.now().astimezone().isoformat()
    salt = str(uuid.uuid4().hex)
    combined = date_str + salt
    signature = hmac.new(api_secret.encode('utf-8'), combined.encode('utf-8'), hashlib.sha256).hexdigest()
    auth_header = f"HMAC-SHA256 apiKey={api_key}, date={date_str}, salt={salt}, signature={signature}"
    return auth_header

# ------------------------------------------------------------------------------
# 📡 1. [손님용] 카카오 알림톡 우선 발송 + 실패 시 문자(LMS) 우회 엔진
# ------------------------------------------------------------------------------
def send_solapi_auto_message(to_phone, name, product, view_url):
    try:
        api_key = st.secrets.get("SOLAPI_API_KEY")
        api_secret = st.secrets.get("SOLAPI_API_SECRET")
        from_phone = st.secrets.get("SOLAPI_SENDER_PHONE")

        kakao_pf_id = st.secrets.get("KAKAO_PF_ID", "")
        kakao_template_id = st.secrets.get("KAKAO_TEMPLATE_ID", "")

        if not api_key or not api_secret or not from_phone:
            return False, "솔라피 설정이 Streamlit Secrets에 누락되었습니다."

        clean_to_phone = to_phone.replace("-", "").strip()
        clean_from_phone = from_phone.replace("-", "").strip()

        msg_body = f"""{name}님, 신청하신 사주 분석이 완료되었습니다.

🔮 신청 상품: {product}

아래 링크를 눌러 소름 돋는 인생 스포일러(사주 리포트)를 바로 확인해 보세요!

결과 확인하기:
{view_url}"""

        url = "https://api.solapi.com/messages/v4/send"
        headers = {
            "Authorization": get_solapi_auth_header(api_key, api_secret),
            "Content-Type": "application/json; charset=utf-8"
        }
        
        message_data = {
            "to": clean_to_phone,
            "from": clean_from_phone,
            "text": msg_body,
            "subject": f"[사주박사] {name}님 사주 리포트 도착",
            "type": "LMS" 
        }

        if kakao_pf_id and kakao_template_id:
            message_data["kakaoOptions"] = {
                "pfId": kakao_pf_id,
                "templateId": kakao_template_id
            }

        payload = {
            "message": message_data
        }

        res = requests.post(url, headers=headers, json=payload, timeout=10)
        res_data = res.json()

        if res.status_code == 200 and "groupId" in res_data:
            return True, f"고객님({to_phone}) 카톡(또는 대체 문자) 발송 완료!"
        else:
            err_msg = res_data.get("errorMessage", str(res_data))
            return False, f"솔라피 응답 오류: {err_msg}"

    except Exception as e:
        return False, f"발송 연동 장애: {e}"

# ------------------------------------------------------------------------------
# 📡 2. [사장님(관리자)용] 비상벨 알림 문자(SMS) 발송 함수
# ------------------------------------------------------------------------------
def send_solapi_admin_alert(now_str, name, product_summary, base_price, discount_amt, final_price):
    try:
        api_key = st.secrets.get("SOLAPI_API_KEY")
        api_secret = st.secrets.get("SOLAPI_API_SECRET")
        from_phone = st.secrets.get("SOLAPI_SENDER_PHONE") 
        
        admin_phone = "010-3857-6727" 
        
        if not api_key or not api_secret or not from_phone:
            return False, "솔라피 시크릿 설정 누락 (API_KEY, API_SECRET, SENDER_PHONE)"

        short_time = now_str.replace("-", "/").rsplit(":", 1)[0]
        admin_msg = f"{short_time}/ {name.strip()}님 / {product_summary} / {base_price:,}원 -> {discount_amt:,}원 -> {final_price:,}원"

        auth_header = get_solapi_auth_header(api_key, api_secret)
        headers = {"Authorization": auth_header, "Content-Type": "application/json"}
        data = {
            "message": {
                "to": admin_phone.replace("-", "").strip(),
                "from": from_phone.replace("-", "").strip(),
                "text": admin_msg,
                "type": "SMS"
            }
        }
        res = requests.post("https://api.solapi.com/messages/v4/send", headers=headers, json=data, timeout=5)
        res_data = res.json()
        
        if res.status_code == 200 and "groupId" in res_data:
            return True, "비상벨 SMS 발송 성공"
        else:
            err_msg = res_data.get("errorMessage", str(res_data))
            return False, f"솔라피 응답 에러: {err_msg}"
            
    except Exception as e:
        return False, f"비상벨 통신 장애: {e}"

# ------------------------------------------------------------------------------
# 🗄️ [데이터베이스 초기화]
# ------------------------------------------------------------------------------
def init_order_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            created_at TEXT,
            name TEXT,
            phone TEXT,
            email TEXT,
            birth_date TEXT,
            birth_time TEXT,
            gender TEXT,
            calendar_type TEXT,
            marital TEXT,
            product TEXT,
            status TEXT,
            result_html TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ------------------------------------------------------------------------------
# 0. 🧮 [패키지 복수 선택 할인 연산 엔진]
# ------------------------------------------------------------------------------
DISCOUNT_POLICY = {
    "two_item_rate": 0.20,      
    "three_plus_rate": 0.30,    
    "premium_rate": 0.30,
    "premium_combination": ["3-1", "3-3"]
}

def calculate_package_price(selected_products):
    if not selected_products:
        return 0, 0, 0, 0, 0
        
    total_original = 0
    total_chuseok = 0
    codes = []
    
    for item in selected_products:
        code = item.split('.')[0].strip()
        codes.append(code)
        
        orig_str = item.split('정가')[-1].split('원')[0].replace(',', '').strip()
        total_original += int(orig_str)
        
        chu_str = item.split('추석특가')[-1].replace('원)', '').replace(',', '').strip()
        total_chuseok += int(chu_str)
        
    count = len(selected_products)
    
    if count <= 1:
        pkg_rate_pct = 0
        final_price = total_chuseok
        
    else:
        if count >= 3 or all(p in codes for p in DISCOUNT_POLICY["premium_combination"]):
            rate = DISCOUNT_POLICY["three_plus_rate"]
        else:
            rate = DISCOUNT_POLICY["two_item_rate"]
            
        pkg_rate_pct = int(rate * 100)
        calculated_price = total_chuseok * (1 - rate)
        final_price = int(round(calculated_price, -3))
        
    if total_original > 0:
        total_rate_pct = int(((total_original - final_price) / total_original) * 100)
    else:
        total_rate_pct = 0
    
    return total_original, total_chuseok, pkg_rate_pct, total_rate_pct, final_price

# ------------------------------------------------------------------------------
# 1. 📱 [고객 모바일 접수 화면]
# ------------------------------------------------------------------------------
def render_customer_order_form():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Nanum+Myeongjo:wght@700&family=Nanum+Pen+Script&display=swap');
        .mobile-box { max-width: 480px; margin: 0 auto; background: #FFFFFF; border: 3px solid #1A237E; border-radius: 15px; padding: 20px; }
        .m-title { font-family: 'Nanum Pen Script', cursive; font-size: 34px; color: #1A237E; text-align: center; margin-bottom: 20px; border-bottom: 1.5px dashed #1A237E; }
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
            price_display = f"<s style='color:#757575;'>{ord_info['total_raw']:,}원</s> ➡️ <b style='color:#D50000; font-size:18px;'>{ord_info['final_price']:,}원</b> <span style='color:#2E7D32; font-size:13px; font-weight:bold;'>({ord_info['rate_pct']}% 패키지 할인)</span>"
        else:
            price_display = f"<b style='font-size:17px;'>{ord_info['final_price']:,}원</b>"

        st.markdown(f"""
<div class='guide-box'>
<div class='pay-title'>[ 🏮 신청 접수 완료! 🏮 ]</div>
<b>{ord_info['name']}</b>님, 환영합니다! 🎉<br>
신청하신 <b>"{ord_info['product_desc']}"</b> 접수가 완벽하게 끝났어요.<br><br>
이제 아래 계좌로 복비를 쏴주시면,<br>
제가 바로 🔍돋보기 들고 내 인생 스포일러 👀분석에 들어갑니다!
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
<span style='color:#1A237E; font-weight:bold;'>※ 신청자 이름이랑 입금자 이름이 다르면 카톡 채널로 알려주세요!</span><br>
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

    st.markdown("""
    <div class='promo-banner'>
        <b style='color:#E65100; font-size:17px; letter-spacing:-0.5px;'>[ 8/18 ~ 9/30 ] <br> 🌕 추석 및 새학기 맞이 반값 특가! 🌕</b><br>
        <div style='height: 6px;'></div>
        <span style='color:#424242; font-size:14px; line-height: 1.5; letter-spacing:-0.4px;'>
            학생과 청년들의 힘찬 새 출발을 응원하며,<br>
            기간 한정 <b style='letter-spacing:-0.3px;'>전 상품 50% 특별 할인</b>을 진행합니다.
        </span><br>
        <span style='color:#1A237E; font-size:13px; font-weight:bold;'>
            (※ 2개 이상 선택 시 추가 20~30% 할인 적용!)
        </span>
    </div>
    """, unsafe_allow_html=True)

    label_text = "상담 상품 선택  \n:red[*(2개 이상 복수 선택 시 20~30% 특별할인!) (필수)*]"
    selected_products = st.multiselect(label=label_text, options=PRODUCT_LIST, placeholder="상담 상품 선택", key="user_selected_products")
    
    has_partner_product = any(p.startswith("3-") for p in selected_products)

    with st.form("choyeon_customer_order_form_v3"):
        st.markdown("<b>👤 신청자 본인 정보</b>", unsafe_allow_html=True)
        name = st.text_input("성명 *(필수)", placeholder="성함을 입력하세요")
        
        c_p1, c_p2, c_p3 = st.columns([1.1, 1.5, 1.5])
        with c_p1: st.text_input("국번", value="010", disabled=True)
        with c_p2: p_mid = st.text_input("중간 4자리 *(필수)", max_chars=4, placeholder="1234")
        with c_p3: p_end = st.text_input("끝 4자리 *(필수)", max_chars=4, placeholder="5678")
        
        email = st.text_input("이메일 (선택)", placeholder="ch1234@example.com")
        
        c_y, c_m, c_d = st.columns(3)
        with c_y: b_year = st.text_input("생년 (YYYY) *", max_chars=4, placeholder="1990")
        with c_m: b_month = st.text_input("월 (MM) *", max_chars=2, placeholder="06")
        with c_d: b_day = st.text_input("일 (DD) *", max_chars=2, placeholder="15")
        
        c_g, c_c, c_m_stat = st.columns(3)
        with c_g: gender = st.selectbox("성별 *", ["여성", "남성"])
        with c_c: cal_type = st.selectbox("양력 또는 음력 *", ["양력", "음력", "음력(윤달)"])
        with c_m_stat: marital = st.selectbox("혼인 상태 *", ["미혼", "기혼", "돌싱"])
        
        b_time = st.selectbox("태어난 시간 *(필수)", TIME_OPTIONS)
        
        partner_name = ""
        p_b_year, p_b_month, p_b_day = "", "", ""
        partner_gender, partner_cal, partner_marital, partner_time = "남성", "양력", "미혼", "시간 모름"
        
        if has_partner_product:
            st.markdown("<hr style='border: 0; border-top: 1px dashed #3F51B5; margin: 15px 0;'>", unsafe_allow_html=True)
            st.markdown("<b>👩‍❤️‍👨 상대방 사주 정보 (궁합/택일 필수)</b>", unsafe_allow_html=True)
            partner_name = st.text_input("상대방 성명 *(필수)", placeholder="상대방 성함을 입력하세요")
            
            c_py, c_pm, c_pd = st.columns(3)
            with c_py: p_b_year = st.text_input("상대방 생년 (YYYY) *", max_chars=4, placeholder="1992")
            with c_pm: p_b_month = st.text_input("상대방 월 (MM) *", max_chars=2, placeholder="08")
            with c_pd: p_b_day = st.text_input("상대방 일 (DD) *", max_chars=2, placeholder="20")
            
            c_pg, c_pc, c_pm_stat = st.columns(3)
            with c_pg: partner_gender = st.selectbox("상대방 성별 *", ["남성", "여성"])
            with c_pc: partner_cal = st.selectbox("상대방 양/음력 *", ["양력", "음력", "음력(윤달)"])
            with c_pm_stat: partner_marital = st.selectbox("상대방 혼인 상태 *", ["미혼", "기혼", "돌싱"])
            partner_time = st.selectbox("상대방 태어난 시간 *", TIME_OPTIONS)

        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background: #F4F6F9; border-radius: 12px; padding: 20px; border-left: 4px solid #3F51B5; margin-bottom: 15px;'>
            <b style='color:#1A237E; font-size: 16px;'>💡 [ 사주박사 1:1 비밀상담소 ]</b>
            <p style='font-size: 14px; color: #424242; line-height: 1.7; margin-top: 8px; margin-bottom: 0;'>
            혼자 끙끙 앓지 말고, 답답한 고민들을 편하게 털어놓아 보세요.<br>
            명리학적 원인 분석과 함께 <b>'현실적인 솔루션'</b>을 담아드립니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        user_concern = st.text_area("✍️ 나의 현재 고민 털어놓기 (선택사항)", height=100, max_chars=500, placeholder="현재의 상황이나 궁금한 점을 자유롭게 적어주세요.")

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        agree = st.checkbox("개인정보 수집 및 감명 제공에 동의합니다. *(필수)")
        submitted = st.form_submit_button("🏮 사주풀이 신청하기 ", use_container_width=True)
        
        if submitted:
            actual_selected = st.session_state.get("user_selected_products", selected_products)

            if not name.strip():
                st.error("🚨 본인 이름을 입력해 주십시오.")
                return
            if len(p_mid.strip()) != 4 or len(p_end.strip()) != 4 or not (p_mid.isdigit() and p_end.isdigit()):
                st.error("🚨 핸드폰 번호 4자리를 숫자로 정확히 입력해 주십시오.")
                return
            if not (b_year.isdigit() and b_month.isdigit() and b_day.isdigit()):
                st.error("🚨 본인 생년월일 숫자를 정확히 입력해 주십시오.")
                return
            if not actual_selected or len(actual_selected) == 0:
                st.error("🚨 최소 1개 이상의 상담 상품을 선택해 주십시오.")
                return
                
            if has_partner_product:
                if not partner_name.strip():
                    st.error("🚨 궁합/택일 상품을 선택하셨습니다. 상대방 성함을 입력해 주십시오.")
                    return
                if not (p_b_year.isdigit() and p_b_month.isdigit() and p_b_day.isdigit()):
                    st.error("🚨 상대방 생년월일 숫자를 정확히 입력해 주십시오.")
                    return

            if not agree:
                st.error("🚨 개인정보 제공에 동의해 주십시오.")
                return
            
            calc_result = calculate_package_price(actual_selected)
            if len(calc_result) == 5:
                total_original, total_chuseok, pkg_rate_pct, total_rate_pct, final_price = calc_result
                discount_amt = total_original - final_price
                effective_rate = total_rate_pct
                base_price_to_show = total_original
            else:
                total_original, total_chuseok, pkg_rate_pct, final_price = calc_result
                discount_amt = total_original - final_price
                effective_rate = pkg_rate_pct
                base_price_to_show = total_original
                
            product_names_summary = " + ".join([p.split('.')[0] for p in actual_selected])
            full_product_desc = f"{product_names_summary} ({final_price:,}원)"
            
            order_id = str(uuid.uuid4())[:8]
            phone_full = f"010-{p_mid.strip()}-{p_end.strip()}"
            birth_full = f"{b_year.strip()}-{b_month.strip().zfill(2)}-{b_day.strip().zfill(2)}"
            
            memo_parts = []
            if email.strip(): memo_parts.append(email.strip())
            if has_partner_product:
                p_birth_full = f"{p_b_year.strip()}-{p_b_month.strip().zfill(2)}-{p_b_day.strip().zfill(2)}"
                memo_parts.append(f"[상대방: {partner_name.strip()} / {p_birth_full} / {partner_time} / {partner_gender} / {partner_cal} / {partner_marital}]")
            if user_concern.strip():
                memo_parts.append(f"[고민사연: {user_concern.strip()}]")
                
            memo_info = " | ".join(memo_parts)
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, now_str, name.strip(), phone_full, memo_info, birth_full, b_time, gender, cal_type, marital, full_product_desc, "입금대기", ""))
            conn.commit()
            conn.close()
            
            # 💡 [사장님 비상벨 타격 온!] - 즉각 발송 및 모니터링
            try:
                alert_ok, alert_msg = send_solapi_admin_alert(
                    now_str=now_str, 
                    name=name.strip(), 
                    product_summary=product_names_summary, 
                    base_price=base_price_to_show, 
                    discount_amt=discount_amt, 
                    final_price=final_price
                )
                if not alert_ok:
                    print(f"[관리자 비상벨 전송 경고] {alert_msg}")
            except Exception as e:
                print(f"[관리자 비상벨 치명적 예외] {e}")
            
            st.session_state["submitted_order"] = {
                "order_id": order_id, 
                "name": name.strip(), 
                "product_desc": full_product_desc,
                "selected_products": actual_selected,
                "total_raw": base_price_to_show,
                "discount_amt": discount_amt,
                "rate_pct": effective_rate,
                "final_price": final_price
            }
            st.rerun()

# ------------------------------------------------------------------------------
# 2. 👑 [박사님 관리자 패널]
# ------------------------------------------------------------------------------
def render_admin_panel(generator_func):
    st.subheader("👑 사주박사 관리자 장부 및 감명 발송 패널")
    pwd = st.sidebar.text_input("관리자 비밀번호", type="password")
    if pwd != ADMIN_PASSWORD:
        st.warning("🔒 관리자 암호를 입력하여 주십시오.")
        return

    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM orders ORDER BY created_at DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("현재 접수된 신청 내역이 없습니다.")
        return
        
    tab1, tab2 = st.tabs(["⏳ [입금대기] 승인 및 감명 처리", "✅ [분석완료] 발송 결과 및 링크 관리"])
    
    with tab1:
        pending_orders = df[df["status"] == "입금대기"]
        if pending_orders.empty:
            st.success("현재 입금 대기 중인 신청건이 없습니다.")
        else:
            for _, row in pending_orders.iterrows():
                with st.expander(f"📌 [{row['name']} 님] {row['product']} (신청일: {row['created_at']})", expanded=True):
                    st.write(f"- 연락처: **{row['phone']}** | 생년월일: **{row['birth_date']} ({row['calendar_type']})** | 시간: **{row['birth_time']}**")
                    if row['email']:
                        st.caption(f"📝 메모 및 고민내용: {row['email']}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"💰 입금 확인 (감명생성 + 발송)", key=f"btn_pay_{row['order_id']}", use_container_width=True, type="primary"):
                            with st.spinner(f"{row['name']}님의 정밀 분석 리포트를 생성 중입니다..."):
                                html_result = generator_func(row)
                                
                                conn = sqlite3.connect(DB_FILE)
                                c = conn.cursor()
                                c.execute("UPDATE orders SET status='분석완료', result_html=? WHERE order_id=?", (html_result, row['order_id']))
                                conn.commit()
                                conn.close()
                                
                                view_url = f"{BASE_URL}/?mode=view&code={row['order_id']}"
                                send_ok, send_msg = send_solapi_auto_message(row['phone'], row['name'], row['product'], view_url)
                                
                                if send_ok: st.success(f"✅ {row['name']}님 리포트 생성 및 {send_msg}")
                                else: st.warning(f"⚠️ 리포트는 완성되었으나 문자 실패: {send_msg}")
                                    
                                time.sleep(1)
                                st.rerun()
                                
                    with c2:
                        st.caption("⚠️ 미입금 안내 문자:")
                        st.code("입금 안내 문구 (생략)", language="text")

    with tab2:
        completed_orders = df[df["status"] == "분석완료"]
        if completed_orders.empty:
            st.info("아직 분석 완료된 내역이 없습니다.")
        else:
            for _, row in completed_orders.iterrows():
                view_url = f"{BASE_URL}/?mode=view&code={row['order_id']}"
                with st.expander(f"✅ [{row['name']} 님] (열람코드: {row['order_id']})", expanded=True):
                    st.write(f"- 연락처: **{row['phone']}** | [리포트 바로보기]({view_url})")

# ------------------------------------------------------------------------------
# 3. 📜 [고객 전용 결과 열람창] (뷰어 엔진 정상화 및 모바일 감성 카드 적용)
# ------------------------------------------------------------------------------
def render_view_page(order_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, product, status, result_html FROM orders WHERE order_id=?", (order_id,))
    res = c.fetchone()
    conn.close()
    
    if not res:
        st.error("존재하지 않거나 만료된 링크입니다.")
        return
        
    name, product, status, result_html = res
    if status != "분석완료" or not result_html:
        st.warning(f"열일 중! 💦 뚝딱뚝딱~ 현재 {name}님의 사주를 제가 꼼꼼하게 분석하고 있어요. 🧐✨ 입금 확인 후 하루(24시간) 안에는 무조건 도착하니 쪼금만 기다려주세요! 완성되면 카톡으로 알림 팍! 쏴드릴게요! 🚀")
        return

    # [수정 1] 모바일 감성 카드 UI 및 인쇄(PDF)용 CSS 주입
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
        
        /* 모바일 최적화 배경 */
        .report-container {
            max-width: 480px; 
            margin: 0 auto; 
            font-family: 'Noto Sans KR', sans-serif;
            background-color: #f7f9f9;
            padding: 15px;
        }
        /* 미리캔버스 스타일 카드 박스 */
        .saju-card {
            background: #ffffff;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            border: 1px solid #eaeaea;
            line-height: 1.8;
            color: #333;
            font-size: 16px;
        }
        /* PDF 다운로드 버튼 */
        .btn-pdf {
            display: block;
            width: 100%;
            background-color: #c9a764; /* 고급스러운 골드 */
            color: white !important;
            text-align: center;
            padding: 15px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        /* 실제 인쇄(PDF 저장) 시 버튼 숨기기 및 여백 제거 */
        @media print {
            .btn-pdf { display: none !important; }
            .report-container { background-color: #ffffff; padding: 0; }
            .saju-card { box-shadow: none; border: 1px solid #ccc; page-break-inside: avoid; }
        }
    </style>
    """, unsafe_allow_html=True)
    오후 6:39 2026-08-20오후 6:39 2026-08-20
    # [수정 2] 월운표 마커 미치환 버그 임시 방어 (감명기에서 누락되었을 경우를 대비)
    if "[WOLUN_TABLE_HEAR]" in result_html or "[WOLUN_TABLE_HERE]" in result_html:
        result_html = result_html.replace("[WOLUN_TABLE_HEAR]", "<div style='color:#c9a764; font-weight:bold;'>[월운표 세부 분석 데이터 렌더링 영역]</div>")
        result_html = result_html.replace("[WOLUN_TABLE_HERE]", "<div style='color:#c9a764; font-weight:bold;'>[월운표 세부 분석 데이터 렌더링 영역]</div>")

    # [수정 2.5] 어떤 형태의 AI 껍질이든 100% 분쇄하는 강력한 제거 로직
    result_html = result_html.replace("```html", "")
    result_html = result_html.replace("```markdown", "")
    result_html = result_html.replace("```xml", "")
    result_html = result_html.replace("```", "")
    result_html = result_html.strip() # 앞뒤 쓸데없는 공백/줄바꿈 완전 제거

    # [수정 3] 상단 PDF 소장 버튼
    st.markdown('<a href="javascript:window.print()" class="btn-pdf">📄 평생 소장용 PDF 다운로드</a>', unsafe_allow_html=True)
    
    # [수정 4] 사주원국 HTML 렌더링 정상화 및 카드 레이아웃 래핑
    st.markdown(f"""
    <div class="report-container">
        <div class="saju-card">
            {result_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 하단 PDF 소장 버튼
    st.markdown('<a href="javascript:window.print()" class="btn-pdf">📄 리포트 하단 PDF 다운로드</a>', unsafe_allow_html=True)
