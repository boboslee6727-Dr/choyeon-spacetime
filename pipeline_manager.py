# ==============================================================================
# 🏮 박사사주: 신청접수 ~ 수동 입금승인 ~ 솔라피 자동발송 완결 파이프라인
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
LEDGER_FILE = "박사사주_비밀장부.csv"
ADMIN_PASSWORD = "boss!631201"  # 박사님 전용 관리자 암호
BASE_URL = "https://choyeon-spacetime.streamlit.app"

# 12개 정식 상품 체계
PRODUCT_LIST = [
    "1-1. 사주팔자 및 평생 총운 풀이 (11,000원)",
    "1-2. 올 해 (특정 연도) 운세 상세분석 (5,500원)",
    "1-3. 이번 달 (특정 월) 운세 상세분석 (5,500원)",
    "1-4. 이번 주간 및 일진 운세 (무료/2,200원)",
    "2-1. 재물운 & 자산 축적 타이밍 특화 (11,000원)",
    "2-2. 직업/진로/이직/승진운 특화 (11,000원)",
    "2-3. 연애/결혼운 & 사전 흉화예방 특화 (11,000원)",
    "2-4. 건강운 & 조토극수 체질분석 특화 (5,500원)",
    "2-5. 이사 및 개업 택일 특화 (5,500원)",
    "3-1. 부부/연인 정밀 궁합 풀이 (22,000원)",
    "3-2. 백년가약 결혼 택일 (11,000원)",
    "3-3. 명품 출산 택일 (Top 5 길일) (33,000원)"
]

TIME_OPTIONS = [
    "시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시",
    "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시",
    "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시",
    "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시",
    "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"
]

def init_order_db():
    """주문 데이터베이스 초기화"""
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
# 📡 [솔라피 (Solapi) 자동 발송 엔진]
# ------------------------------------------------------------------------------
def get_solapi_auth_header(api_key, api_secret):
    """솔라피 API 규격 HMAC-SHA256 인증 헤더 생성"""
    date_str = datetime.now().astimezone().isoformat()
    salt = str(uuid.uuid4().hex)
    combined = date_str + salt
    signature = hmac.new(api_secret.encode('utf-8'), combined.encode('utf-8'), hashlib.sha256).hexdigest()
    auth_header = f"HMAC-SHA256 apiKey={api_key}, date={date_str}, salt={salt}, signature={signature}"
    return auth_header

def send_solapi_auto_message(to_phone, name, product, view_url):
    """1순위: 고객 스마트폰으로 열람 링크 자동 전송"""
    try:
        api_key = st.secrets.get("SOLAPI_API_KEY")
        api_secret = st.secrets.get("SOLAPI_API_SECRET")
        from_phone = st.secrets.get("SOLAPI_SENDER_PHONE")

        if not api_key or not api_secret or not from_phone:
            return False, "솔라피 API Key 또는 발신번호가 Streamlit Secrets에 설정되지 않았습니다. (수동 복사창 이용)"

        clean_to_phone = to_phone.replace("-", "").strip()
        clean_from_phone = from_phone.replace("-", "").strip()

        msg_body = f"""[박사사주]
짠! {name}님, 기다리던 사주 풀이가 도착했어요! 😎

아래 링크를 누르면 내 인생 스포일러(사주 감명서)를 바로 볼 수 있어요. (PDF 저장도 완전 가능!)

📜 내 사주 결과 확인하기:
{view_url}

---

🎁 [박사사주 폼 미친 이벤트] 🎁

1️⃣ 플친 맺고 '오늘의 운세' 공짜로 받기!
'박사사주' 카톡 채널 추가하면 일주일 동안 매일 아침 내 맞춤형 일진(운세)을 카톡으로 보내드려요. 하루 시작 전에 운세 체크는 필수! ✔️
👉 채널 추가: [카톡 채널 URL 삽입]

2️⃣ 리얼 후기 쓰고 30% 할인 쿠폰 득템!
풀이 보고 소름 돋았다면? 카톡 채널에 찐 후기를 남겨주세요!
연애운, 떡상 재물운, 취업/진로 등 다른 테마 분석할 때 쓸 수 있는 [30% 할인 쿠폰] 팍팍 쏩니다! 💸

---

🔮 고민 있을 땐? 박사사주 메뉴판!
• 종합운: 내 평생 운세, 올해/이번달 팩트 폭행
• 테마운: 썸/연애/결혼운, 재물운, 취업/이직운 - 진짜루 개인고민도 싹다 풀어줘요!
• 궁합/택일: 커플 찰떡 궁합, 이사/개업/결혼 날짜 픽!

고민 생기면 혼자 끙끙 앓지 말고 언제든 찾아주세요!

- 박사사주 올림 -"""

        url = "https://api.solapi.com/messages/v4/send"
        headers = {
            "Authorization": get_solapi_auth_header(api_key, api_secret),
            "Content-Type": "application/json; charset=utf-8"
        }
        
        payload = {
            "message": {
                "to": clean_to_phone,
                "from": clean_from_phone,
                "text": msg_body,
                "subject": f"[박사사주] {name}님 감명 완료 안내"
            }
        }

        kakao_pf_id = st.secrets.get("SOLAPI_KAKAO_PF_ID")
        kakao_tpl_id = st.secrets.get("SOLAPI_KAKAO_TEMPLATE_ID")
        if kakao_pf_id and kakao_tpl_id:
            payload["message"]["kakaoOptions"] = {
                "pfId": kakao_pf_id,
                "templateId": kakao_tpl_id,
                "variables": {
                    "#{고객명}": name,
                    "#{상품명}": product.split(' (')[0],
                    "#{열람URL}": view_url
                }
            }

        res = requests.post(url, headers=headers, json=payload, timeout=10)
        res_data = res.json()

        if res.status_code == 200 and "groupId" in res_data:
            return True, f"고객님 핸드폰(카톡)({to_phone})으로 발송이 완료되었습니다."
        else:
            err_msg = res_data.get("errorMessage", str(res_data))
            return False, f"솔라피 응답 오류: {err_msg}"

    except Exception as e:
        return False, f"발송 연동 장애: {e}"

# ------------------------------------------------------------------------------
# 0. 🧮 [패키지 복수 선택 할인 정책 및 연산 엔진]
# ------------------------------------------------------------------------------
DISCOUNT_POLICY = {
    "default_rate": 0.20,       # 기본 2개 이상 패키지 할인 20%
    "three_plus_rate": 0.25,    # 3개 이상 신청 시 25% 할인
    "premium_rate": 0.30,       # 프리미엄 조합(3-1 + 3-3)은 30% 할인
    "premium_combination": ["3-1", "3-3"]
}

def calculate_package_price(selected_products):
    """상품 목록에 따른 원가, 할인액, 할인율, 최종금액 산출"""
    if not selected_products:
        return 0, 0, 0, 0
        
    total_raw_price = 0
    codes = []
    
    for item in selected_products:
        code = item.split('.')[0].strip()
        codes.append(code)
        price_str = item.split('(')[-1].replace('원)', '').replace(',', '').strip()
        total_raw_price += int(price_str)
        
    count = len(selected_products)
    if count <= 1:
        return total_raw_price, 0, 0, total_raw_price
        
    # 1. 프리미엄 조합 체크 (3-1과 3-3 동시 포함)
    if all(p in codes for p in DISCOUNT_POLICY["premium_combination"]):
        rate = DISCOUNT_POLICY["premium_rate"]
    # 2. 3개 이상 신청
    elif count >= 3:
        rate = DISCOUNT_POLICY["three_plus_rate"]
    # 3. 기본 2개 신청
    else:
        rate = DISCOUNT_POLICY["default_rate"]
        
    final_price = int(total_raw_price * (1 - rate))
    # 10원 단위 절사
    final_price = (final_price // 10) * 10
    discount_amount = total_raw_price - final_price
    
    return total_raw_price, discount_amount, int(rate * 100), final_price

# ------------------------------------------------------------------------------
# 1. 📱 [고객 모바일 접수 화면]
# ------------------------------------------------------------------------------
def render_customer_order_form():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Nanum+Myeongjo:wght@700&family=Nanum+Pen+Script&display=swap');
        
        .mobile-box { max-width: 480px; margin: 0 auto; background: #FFFFFF; border: 3px solid #1A237E; border-radius: 15px; padding: 20px; }
        
        .m-title { 
            font-family: 'Nanum Pen Script', cursive;
            font-size: 34px; 
            font-weight: normal; 
            color: #1A237E; 
            text-align: center; 
            letter-spacing: 1px;
            padding-bottom: 5px; 
            margin-bottom: 20px;
            border-bottom: 1.5px dashed #1A237E;
        }
        
        .guide-box {
            background: #FCFCFD;
            border: 2px solid #3F51B5;
            border-radius: 12px;
            padding: 22px;
            margin-top: 15px;
            line-height: 1.8;
            color: #2D3748;
            font-family: 'Gowun Dodum', sans-serif;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        .pay-title {
            font-size: 20px;
            font-weight: bold;
            color: #1A237E;
            text-align: center;
            margin-bottom: 12px;
        }
        .bank-info-box {
            font-family: 'Nanum Myeongjo', serif;
            background: #F4F6F9;
            padding: 14px;
            border-radius: 8px;
            border-left: 4px solid #1A237E;
            font-size: 16px;
            line-height: 1.9;
            color: #111;
            margin: 12px 0;
        }
        .share-card {
            background: #FFFDF5;
            border: 1.5px solid #FFE082;
            border-radius: 12px;
            padding: 20px;
            font-family: 'Gowun Dodum', sans-serif;
            font-size: 16px;
            line-height: 1.8;
            color: #2D3748;
        }
        
        span[data-baseweb="tag"] {
            cursor: default !important;
        }
        span[data-baseweb="tag"] > span[role="presentation"],
        span[data-baseweb="tag"] svg {
            cursor: pointer !important;
            pointer-events: auto !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='m-title'>🔮박사사주 신청서🔮</div>", unsafe_allow_html=True)
    
    # 1. 상품 선택 (폼 외부 배치로 3-* 선택 시 즉시 감지)
    label_text = "상담 상품 선택  \n:red[*(2개 이상 복수 선택 시 20~30% 특별할인!) (필수)*]"
    selected_products = st.multiselect(
        label=label_text,
        options=PRODUCT_LIST,
        placeholder="상담 상품 선택",
        key="user_selected_products"
    )
    
    has_partner_product = any(p.startswith("3-") for p in selected_products)

    # 2. 단일 고유 키 적용 (중복 에러 원천 방지)
    with st.form("choyeon_customer_order_form_v2"):
        # --- 1. 신청자 본인 정보 ---
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
        
        # --- 2. 3-* 계열 상품 선택 시에만 노출되는 상대방 사주 정보 ---
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

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        agree = st.checkbox("개인정보 수집 및 감명 제공에 동의합니다. *(필수)")
        
        submitted = st.form_submit_button("🏮 사주풀이 신청하기 ", use_container_width=True)
        
        # --- 3. 제출 검증 및 DB 저장 ---
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
            
            total_raw, discount_amt, rate_pct, final_price = calculate_package_price(actual_selected)
            product_names_summary = " + ".join([p.split('.')[0] for p in actual_selected])
            full_product_desc = f"{product_names_summary} ({final_price:,}원)"
            
            order_id = str(uuid.uuid4())[:8]
            phone_full = f"010-{p_mid.strip()}-{p_end.strip()}"
            birth_full = f"{b_year.strip()}-{b_month.strip().zfill(2)}-{b_day.strip().zfill(2)}"
            
            if has_partner_product:
                p_birth_full = f"{p_b_year.strip()}-{p_b_month.strip().zfill(2)}-{p_b_day.strip().zfill(2)}"
                partner_info_str = f"[상대방: {partner_name.strip()} / {p_birth_full} / {partner_time} / {partner_gender} / {partner_cal} / {partner_marital}]"
                memo_info = f"{email.strip()} | {partner_info_str}" if email.strip() else partner_info_str
            else:
                memo_info = email.strip()

            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, now_str, name.strip(), phone_full, memo_info, birth_full, b_time, gender, cal_type, marital, full_product_desc, "입금대기", ""))
            conn.commit()
            conn.close()
            
            st.session_state["submitted_order"] = {
                "order_id": order_id, 
                "name": name.strip(), 
                "product_desc": full_product_desc,
                "selected_products": actual_selected,
                "total_raw": total_raw,
                "discount_amt": discount_amt,
                "rate_pct": rate_pct,
                "final_price": final_price
            }
            st.rerun()

    # 3. 신청 완료 화면 (문단별 분리)
    if "submitted_order" in st.session_state:
        ord_info = st.session_state["submitted_order"]
        order_link = f"{BASE_URL}/?mode=order"

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
초연박사님이 바로 🔍돋보기 들고 내 인생 스포일러 👀분석에 들어갑니다!
</div>
""", unsafe_allow_html=True)

        st.markdown(f"""
<div class='bank-info-box'>
💳 <b>국민은행 231402-04-133221</b><br>
👤 <b>예금주: 이 * 호</b><br>
💰 <b>복비:</b> {price_display}
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class='guide-box' style='margin-top:10px;'>
<span style='color:#1A237E; font-weight:bold;'>※ 앗! 신청자 이름이랑 입금자 이름이 다르면 박사님이 헷갈려요 ㅠㅠ 다를 경우 꼭 카톡 채널로 알려주세요!</span><br><br>
<hr style='border: 0; border-top: 1px dashed #BDBDBD; margin: 12px 0;'>
🎁 <b>[ 윈-윈 친구 소개 이벤트 ]</b><br>
좋은 건 나눠야지요! 친구에게 '박사사주'를 소개해 주세요.<br>
소개받은 친구와 나 <b>두 사람 모두에게</b> 다음 테마 분석 시 쓸 수 있는 <b>[30% 할인 쿠폰]</b>을 팍팍 쏩니다! 💸<br><br>
<div style='text-align: right; font-weight: bold;'>- 박사사주 올림 -</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        ref_order_link = f"{BASE_URL}/?mode=order&ref={ord_info['order_id']}"
        share_title = "🔮 박사사주 - 내 인생 스포일러"
        share_msg = f"소름 돋는 인생 스포일러, 너도 한번 봐봐! 👀\n친구 소개로 같이 신청하면 우리 둘 다 30% 할인 쿠폰 득템 혜택! 🎁\n\n👇 아래 링크에서 신청해봐!\n{ref_order_link}"
        encoded_msg = urllib.parse.quote(share_msg)

        st.markdown(f"""
<div style='text-align:center; font-family: "Gowun Dodum", sans-serif; font-size:18px; font-weight:bold; margin-bottom:10px; color:#1A237E;'>
💬 친구에게 박사사주 공유하고 함께 혜택 받기
</div>
<div class='share-card'>
🔮 [ 박사사주 ] 🔮<br>
소름 돋는 인생 스포일러, 너도 한번 봐봐! 👀<br>
친구 소개로 같이 신청하면 우리 둘 다 30% 할인 쿠폰 득템 혜택! 🎁<br><br>

<div style='text-align:center; margin: 15px 0;'>
    <a href="sms:?&body={encoded_msg}" 
       onclick="
           if (navigator.share) {{
               event.preventDefault();
               navigator.share({{
                   title: '{share_title}',
                   text: `{share_msg}`,
                   url: '{ref_order_link}'
               }}).catch(function(e){{}});
           }}
       " 
       style='display:block; text-decoration:none; background-color:#FEE500; color:#191919; border-radius:10px; padding:14px 20px; font-size:16px; font-weight:bold; box-shadow: 0 2px 5px rgba(0,0,0,0.1); font-family: \"Gowun Dodum\", sans-serif;'>
        🟡 터치해서 친구에게 카톡/문자 바로 보내기
    </a>
</div>

<span style='color:#757575; font-size:13px;'>※ 터치 시 현재 화면은 그대로 유지되며 카카오톡/문자 전송 창이 열립니다.</span><br><br>
<div style='text-align: right; font-weight: bold;'>- 박사사주 올림 -</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. 👑 [박사님 관리자 패널: 자동발송 + 2중 백업 복사창] (?mode=admin)
# ------------------------------------------------------------------------------
def render_admin_panel(generator_func):
    st.subheader("👑 박사사주 관리자 장부 및 감명 발송 패널")
    
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
    
    # 탭 1: 입금 대기 목록
    with tab1:
        pending_orders = df[df["status"] == "입금대기"]
        if pending_orders.empty:
            st.success("현재 입금 대기 중인 신청건이 없습니다.")
        else:
            for _, row in pending_orders.iterrows():
                with st.expander(f"📌 [{row['name']} 님] {row['product']} (신청일: {row['created_at']})", expanded=True):
                    st.write(f"- 핸드폰 번호: **{row['phone']}** | 생년월일: **{row['birth_date']} ({row['calendar_type']})** | 시간: **{row['birth_time']}**")
                    if row['email']:
                        st.caption(f"📝 메모/궁합상대: {row['email']}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"💰 입금 확인 (감명생성 + 자동발송)", key=f"btn_pay_{row['order_id']}", use_container_width=True, type="primary"):
                            with st.spinner(f"{row['name']}님의 정밀 감명서를 생성 중입니다..."):
                                html_result = generator_func(row)
                                
                                conn = sqlite3.connect(DB_FILE)
                                c = conn.cursor()
                                c.execute("UPDATE orders SET status='분석완료', result_html=? WHERE order_id=?", (html_result, row['order_id']))
                                conn.commit()
                                conn.close()
                                
                                ledger_row = {
                                    '접수일시': [row['created_at']], '이름': [row['name']], '핸드폰 번호': [row['phone']],
                                    '생년월일': [row['birth_date']], '태어난시간': [row['birth_time']],
                                    '신청상품': [row['product']], '진행상태': ['분석완료']
                                }
                                df_led = pd.DataFrame(ledger_row)
                                if os.path.exists(LEDGER_FILE):
                                    df_led.to_csv(LEDGER_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
                                else:
                                    df_led.to_csv(LEDGER_FILE, mode='w', header=True, index=False, encoding='utf-8-sig')
                                
                                view_url = f"{BASE_URL}/?mode=view&code={row['order_id']}"
                                send_ok, send_msg = send_solapi_auto_message(row['phone'], row['name'], row['product'], view_url)
                                
                                if send_ok:
                                    st.success(f"✅ {row['name']}님 감명서 생성 및 {send_msg}")
                                else:
                                    st.warning(f"⚠️ 감명서는 완성되었으나 자동문자 실패: {send_msg}")
                                    
                                time.sleep(1)
                                st.rerun()
                                
                    with c2:
                        unpaid_msg = f"""[박사사주]
혹시 잊으신 건 아니죠? 🥺
{row['name']}님, 신청하신 "{row['product'].split(' (')[0]}" 복비 입금이 아직 안 돼서 초연박사님이 대기 타고 계셔요! 

■ 국민은행 231402-04-133221 (예금주: 이*호)
■ 복비: {row['product'].split('(')[-1].replace(')', '')}

입금 호다닥 해주시면 바로 소름 돋는 사주 분석 시작합니다 🚀

🏮 내 신청서 다시 보기:
{BASE_URL}/?mode=order

- 박사사주 올림 -"""
                        st.caption("⚠️ 미입금 안내 문자:")
                        st.code(unpaid_msg, language="text")

    # 탭 2: 분석 완료 및 2중 백업 수동 복사창
    with tab2:
        completed_orders = df[df["status"] == "분석완료"]
        if completed_orders.empty:
            st.info("아직 분석 완료된 내역이 없습니다.")
        else:
            for _, row in completed_orders.iterrows():
                view_url = f"{BASE_URL}/?mode=view&code={row['order_id']}"
                
                complete_msg = f"""[박사사주]
짠! {row['name']}님, 기다리던 사주 풀이가 도착했어요! 😎

아래 링크를 누르면 내 인생 스포일러(사주 감명서)를 바로 볼 수 있어요. (PDF 저장도 완전 가능!)

📜 내 사주 결과 확인하기:
{view_url}

---

🎁 [박사사주 폼 미친 이벤트] 🎁

1️⃣ 플친 맺고 '오늘의 운세' 공짜로 받기!
'박사사주' 카톡 채널 추가하면 일주일 동안 매일 아침 내 맞춤형 일진(운세)을 카톡으로 보내드려요. 하루 시작 전에 운세 체크는 필수! ✔️
👉 채널 추가: [카톡 채널 URL 삽입]

2️⃣ 리얼 후기 쓰고 30% 할인 쿠폰 득템!
풀이 보고 소름 돋았다면? 카톡 채널에 찐 후기를 남겨주세요!
연애운, 떡상 재물운, 취업/진로 등 다른 테마 분석할 때 쓸 수 있는 [30% 할인 쿠폰] 팍팍 쏩니다! 💸

---

🔮 고민 있을 땐? 박사사주 메뉴판!
• 종합운: 내 평생 운세, 올해/이번달 팩트 폭행
• 테마운: 썸/연애/결혼운, 재물운, 취업/이직운 - 진짜루 개인고민도 싹다 풀어줘요!
• 궁합/택일: 커플 찰떡 궁합, 이사/개업/결혼 날짜 픽!

고민 생기면 혼자 끙끙 앓지 말고 언제든 찾아주세요!

- 박사사주 올림 -"""

                with st.expander(f"✅ [{row['name']} 님] {row['product']} (열람코드: {row['order_id']})", expanded=True):
                    st.write(f"- 연락처: **{row['phone']}** | 열람 링크: [감명서 바로보기]({view_url})")
                    
                    c_send, c_copy = st.columns([1, 2])
                    with c_send:
                        if st.button("📲 솔라피 알림톡/문자 즉시 재발송", key=f"btn_resend_{row['order_id']}"):
                            s_ok, s_msg = send_solapi_auto_message(row['phone'], row['name'], row['product'], view_url)
                            if s_ok: st.success(s_msg)
                            else: st.error(s_msg)
                    
                    with c_copy:
                        st.caption("💌 비상용 백업: 카카오톡/문자 수동 복사창")
                        st.code(complete_msg, language="text")

# ------------------------------------------------------------------------------
# 3. 📜 [고객 전용 감명서 결과 열람창] (?mode=view&code=XXXX)
# ------------------------------------------------------------------------------
def render_view_page(order_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, product, status, result_html FROM orders WHERE order_id=?", (order_id,))
    res = c.fetchone()
    conn.close()
    
    if not res:
        st.error("존재하지 않거나 만료된 감명서 링크입니다.")
        return
        
    name, product, status, result_html = res
    if status != "분석완료" or not result_html:
        st.warning(f"열일 중! 💦 뚝딱뚝딱~ 현재 {name}님의 사주를 초연박사님이 영혼을 갈아 넣어 꼼꼼하게 분석하고 있어요. 🧐✨ 입금 확인 후 하루(24시간) 안에는 무조건 도착하니 쪼금만 기다려주세요! 완성되면 카톡으로 알림 팍! 쏴드릴게요! 🚀")
        return
        
    st.markdown(result_html, unsafe_allow_html=True)
