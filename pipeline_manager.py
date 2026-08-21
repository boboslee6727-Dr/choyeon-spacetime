# ==============================================================================
# 🏮 사주박사: 신청접수 ~ 수동 입금승인 ~ 솔라피 자동발송 완결 파이프라인 (ver 75.3 찐최종)
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
import re

DB_FILE = "choyeon_orders.db"
LEDGER_FILE = "사주박사_비밀장부.csv"
ADMIN_PASSWORD = "boss!631201"  # 박사님 전용 관리자 암호
BASE_URL = "https://choyeon-spacetime.streamlit.app"
KAKAO_CHAT_URL = "http://pf.kakao.com/_xexizSX/chat"

# 12개 정식 상품 체계
U_PRODUCT_LIST = [
    "1-1. 사주팔자와 운세풀이 (정가 22,000원 ➡️ 추석특가 11,000원)",
    "1-2. 올 해 (특정 연도) 운세 상세분석 (정가 11,000원 ➡️ 추석특가 5,500원)",
    "1-3. 이번 달 (특정 월) 운세 상세분석 (정가 11,000원 ➡️ 추석특가 5,500원)",
    "1-4. 이번(특정) 주 및 일 운세 상세분석 (정가 4,400원 ➡️ 추석특가 2,200원)",
    "2-1. 재물운 특화 분석 (정가 22,000원 ➡️ 추석특가 11,000원)",
    "2-2. 직업/진학운 특화 분석 (정가 22,000원 ➡️ 추석특가 11,000원)",
    "2-3. 연애/결혼운 특화 분석 (정가 22,000원 ➡️ 추석특가 11,000원)",
    "2-4. 건강운 특화 분석 (정가 11,000원 ➡️ 추석특가 5,500원)",
    "2-5. 이사 및 개업 택일 (정가 11,000원 ➡️ 추석특가 5,500원)",
    "3-1. 연애/결혼운 (궁합) 풀이 (정가 44,000원 ➡️ 추석특가 22,000원)",
    "3-2. 결혼 택일 (정가 22,000원 ➡️ 추석특가 11,000원)",
    "3-3. 출산 택일 (정가 66,000원 ➡️ 추석특가 33,000원)"
]

idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", 
    "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", 
    "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", 
    "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]

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
# 📡 1. [손님용] 카카오 알림톡 자동 발송
# ------------------------------------------------------------------------------
def send_solapi_auto_message(to_phone, name, product, view_url):
    try:
        api_key = st.secrets.get("SOLAPI_API_KEY")
        api_secret = st.secrets.get("SOLAPI_API_SECRET")
        from_phone = st.secrets.get("SOLAPI_SENDER_PHONE")

        kakao_pf_id = st.secrets.get("KAKAO_PF_ID", "")
        kakao_template_id = st.secrets.get("KAKAO_TEMPLATE_ID", "")

        if not api_key or not api_secret or not from_phone:
            return False, "솔라피 설정 누락"

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

        payload = {"message": message_data}
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        res_data = res.json()

        if res.status_code == 200 and "groupId" in res_data:
            return True, f"고객님({to_phone}) 알림톡 발송 완료!"
        else:
            return False, f"솔라피 오류: {res_data.get('errorMessage', str(res_data))}"
    except Exception as e:
        return False, f"발송 장애: {e}"

# ------------------------------------------------------------------------------
# 📡 2. [사장님(관리자)용] 비상벨 알림 문자 발송
# ------------------------------------------------------------------------------
def send_solapi_admin_alert(now_str, name, product_summary, base_price, discount_amt, final_price):
    try:
        api_key = st.secrets.get("SOLAPI_API_KEY")
        api_secret = st.secrets.get("SOLAPI_API_SECRET")
        from_phone = st.secrets.get("SOLAPI_SENDER_PHONE") 
        admin_phone = "010-3857-6727" 
        
        if not api_key or not api_secret or not from_phone:
            return False, "솔라피 시크릿 설정 누락"

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
            return False, f"솔라피 응답 에러: {res_data.get('errorMessage')}"
    except Exception as e:
        return False, f"비상벨 통신 장애: {e}"

# ------------------------------------------------------------------------------
# 🗄️ [데이터베이스 초기화] (24개 필드 완벽 스키마)
# ------------------------------------------------------------------------------
def init_order_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 🚨 [박사님! 여기에 이 한 줄을 강제로 추가해 주십시오!] 🚨
    c.execute("DROP TABLE IF EXISTS orders")    
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            created_at TEXT,
            phone TEXT,
            email TEXT,
            name TEXT,
            gender TEXT,
            marital TEXT,
            u_cal TEXT,
            b_year INTEGER,
            b_month INTEGER,
            b_day INTEGER,
            b_time TEXT,
            u_product TEXT,
            f_name TEXT,
            f_gender TEXT,
            f_marital TEXT,
            f_cal TEXT,
            f_y INTEGER,
            f_m INTEGER,
            f_d INTEGER,
            f_t TEXT,
            user_concern TEXT,
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
# 1. 📱 [고객 모바일 접수 화면] (상품선택 끌어올리기 + 조건부 렌더링 적용)
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
        신청하신 <b>"{ord_info['product_desc']}"</b> 접수가 완료되었습니다.<br><br>
        아래 계좌로 복비를 입금해주시면 분석이 시작됩니다!
        </div>
        <div class='bank-info-box'>
        💳 <b>국민은행 231402-04-133221</b><br>
        👤 <b>예금주: 이 * 호</b><br>
        💰 <b>복비:</b> {price_display}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("➕ 새로운 사주풀이 추가 신청하기", use_container_width=True):
            del st.session_state["submitted_order"]
            st.rerun()
        return

    st.markdown("""
    <div class='promo-banner'>
        <b style='color:#E65100; font-size:17px;'>[ 8/18 ~ 9/30 ] 🌕 추석 맞이 반값 특가! 🌕</b><br>
        <span style='color:#424242; font-size:14px;'>기간 한정 <b>전 상품 50% 특별 할인</b> 진행 중!</span><br>
        <span style='color:#1A237E; font-size:13px; font-weight:bold;'>(※ 2개 이상 선택 시 추가 할인 적용!)</span>
    </div>
    """, unsafe_allow_html=True)

    with st.form("choyeon_customer_order_form_final"):
        # 1. 👤 본인 기본 정보 입력
        st.markdown("<b>1. 👤 신청자 본인 정보</b>", unsafe_allow_html=True)
        name = st.text_input("이름 *(필수)", placeholder="성함을 입력하세요")
        
        c_p1, c_p2, c_p3 = st.columns([1, 1.5, 1.5])
        with c_p1: st.text_input("국번", value="010", disabled=True)
        with c_p2: p_mid = st.text_input("연락처 중간 4자리 *(필수)", max_chars=4)
        with c_p3: p_end = st.text_input("연락처 끝 4자리 *(필수)", max_chars=4)
        
        memo_info = st.text_input("이메일 (선택사항)")
        
        c_g, c_m, c_c = st.columns(3)
        with c_g: gender = st.selectbox("성별", ["여성", "남성"])
        with c_m: marital = st.selectbox("결혼유무", ["미혼", "기혼", "돌싱", "기타"])
        with c_c: u_cal = st.selectbox("양/음력", ["양력", "음력 평달", "음력 윤달"])
        
        c_y, c_mo, c_d = st.columns(3)
        with c_y: b_year = st.text_input("생년(YYYY) *", max_chars=4, placeholder="1990")
        with c_mo: b_month = st.text_input("월(MM) *", max_chars=2, placeholder="06")
        with c_d: b_day = st.text_input("일(DD) *", max_chars=2, placeholder="15")
        
        b_time = st.selectbox("태어난 시간", idx_list)

        st.markdown("<hr>", unsafe_allow_html=True)

        # 2. 🛍️ 상품 선택 (위로 끌어올림!)
        st.markdown("<b>2. 🛍️ 상품 선택</b>", unsafe_allow_html=True)
        selected_products = st.multiselect("원하시는 상품을 모두 선택해주세요 *(필수)", U_PRODUCT_LIST)
        
        # 3. 👩‍❤️‍👨 상대방 정보 (조건부 렌더링)
        f_name, f_gender, f_marital, f_cal, f_t = "", "", "", "", "시간 모름"
        f_y, f_m, f_d = "", "", ""
        
        needs_partner = any("3-" in prod for prod in selected_products)
        
        if needs_partner:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("<b>3. 👩‍❤️‍👨 상대방 정보 (궁합 및 택일용 필수)</b>", unsafe_allow_html=True)
            f_name = st.text_input("상대방 이름 *(필수)")
            
            f_c_g, f_c_m, f_c_c = st.columns(3)
            with f_c_g: f_gender = st.selectbox("상대방 성별", ["남성", "여성"])
            with f_c_m: f_marital = st.selectbox("상대방 결혼유무", ["미혼", "기혼", "돌싱", "기타"])
            with f_c_c: f_cal = st.selectbox("상대방 양/음력", ["양력", "음력 평달", "음력 윤달"])
            
            f_c_y, f_c_mo, f_c_d = st.columns(3)
            with f_c_y: f_y = st.text_input("상대방 생년(YYYY) *", max_chars=4)
            with f_c_mo: f_m = st.text_input("상대방 월(MM) *", max_chars=2)
            with f_c_d: f_d = st.text_input("상대방 일(DD) *", max_chars=2)
            
            f_t = st.selectbox("상대방 태어난 시간", idx_list, key="partner_time")

        # 4. 📝 고민 사연
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<b>4. 📝 나의 현재 고민 털어놓기 (선택)</b>", unsafe_allow_html=True)
        user_concern_text = st.text_area("답답한 고민들을 편하게 털어놓아 보세요.", height=120)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        agree = st.checkbox("개인정보 수집 및 제공에 동의합니다. *(필수)")
        submitted = st.form_submit_button("🏮 사주풀이 신청하기 🏮", type="primary", use_container_width=True)
        
        if submitted:
            if not name.strip() or not p_mid.strip() or not p_end.strip():
                st.error("🚨 본인 이름과 연락처를 모두 입력해 주십시오.")
                return
            if not (b_year.isdigit() and b_month.isdigit() and b_day.isdigit()):
                st.error("🚨 본인 생년월일 숫자를 정확히 입력해 주십시오.")
                return
            if not selected_products:
                st.error("🚨 최소 1개 이상의 상품을 선택해 주십시오.")
                return
            if needs_partner:
                if not f_name.strip() or not (f_y.isdigit() and f_m.isdigit() and f_d.isdigit()):
                    st.error("🚨 궁합/택일 상품 선택 시 상대방 이름과 생년월일이 필수입니다.")
                    return
            if not agree:
                st.error("🚨 개인정보 제공에 동의해 주십시오.")
                return
            
            calc_result = calculate_package_price(selected_products)
            total_original, total_chuseok, pkg_rate_pct, total_rate_pct, final_price = calc_result
            discount_amt = total_original - final_price
            full_product_desc = " + ".join([p.split('.')[0] for p in selected_products]) + f" ({final_price:,}원)"
            
            order_id = str(uuid.uuid4())[:8]
            phone_full = f"010-{p_mid.strip()}-{p_end.strip()}"
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 24개 컬럼 완벽 INSERT
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (order_id, now_str, phone_full, memo_info, name.strip(), gender, marital, u_cal, b_year, b_month, b_day, b_time, full_product_desc, f_name, f_gender, f_marital, f_cal, f_y, f_m, f_d, f_t, user_concern_text, "입금대기", ""))
            conn.commit()
            conn.close()
            
            try:
                alert_ok, alert_msg = send_solapi_admin_alert(
                    now_str, name.strip(), full_product_desc, total_original, discount_amt, final_price
                )
            except Exception as e:
                pass 
            
            st.session_state["submitted_order"] = {
                "order_id": order_id, 
                "name": name.strip(), 
                "product_desc": full_product_desc,
                "total_raw": total_original,
                "discount_amt": discount_amt,
                "rate_pct": total_rate_pct,
                "final_price": final_price
            }
            st.rerun()

# ------------------------------------------------------------------------------
# 2. 👑 [박사님 관리자 패널] (수동 검수 및 수동 발송 체계로 완벽 분리!)
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
        
    tab1, tab2 = st.tabs(["⏳ 1단계: 입금 승인 및 리포트 생성", "✅ 2단계: 리포트 검수 및 수동 발송"])
    
    with tab1:
        pending_orders = df[df["status"] == "입금대기"]
        if pending_orders.empty:
            st.success("현재 입금 대기 중인 신청건이 없습니다.")
        else:
            for _, row in pending_orders.iterrows():
                with st.expander(f"📌 [{row['name']} 님] {row['u_product']} (신청일: {row['created_at']})", expanded=True):
                    st.write(f"- 연락처: **{row['phone']}** | 생년: **{row['b_year']}-{row['b_month']}-{row['b_day']} ({row['u_cal']})** | 시간: **{row['b_time']}**")
                    if row['email']: 
                        st.caption(f"📝 이메일: {row['email']}")
                    if row['user_concern']: 
                        st.caption(f"📝 고민사연: {row['user_concern']}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"💰 입금 확인 (리포트만 조용히 생성)", key=f"btn_pay_{row['order_id']}", use_container_width=True, type="primary"):
                            try:
                                with st.spinner(f"{row['name']}님의 정밀 분석 리포트를 생성 중입니다..."):
                                    
                                    # 💡 [핵심] 24개 심장(DB 스키마) 데이터를 어댑터 없이 100% 직결!!
                                    html_result = generator_func(row)
                                    
                                    # DB 에러 방지 다림질
                                    clean_html = str(html_result).replace("```html", "").replace("```markdown", "").replace("```", "")
                                    safe_lines = [line.strip() for line in clean_html.split("\n")]
                                    final_clean_html = "\n".join(safe_lines)
                                    
                                    # DB에 '분석완료' 상태로 저장
                                    conn = sqlite3.connect(DB_FILE)
                                    c = conn.cursor()
                                    c.execute("UPDATE orders SET status='분석완료', result_html=? WHERE order_id=?", (final_clean_html, row['order_id']))
                                    conn.commit()
                                    conn.close()
                                    
                                    st.success(f"✅ 리포트 생성 완료! [검수 및 수동 발송] 탭으로 이동되었습니다.")
                                    time.sleep(1)
                                    st.rerun()
                                    
                            except Exception as e:
                                st.error(f"🚨 [감명 엔진 에러] 원인: {e}")
                                
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
                with st.expander(f"✅ [{row['name']} 님] 리포트 대기중 (열람코드: {row['order_id']})", expanded=True):
                    st.write(f"- 연락처: **{row['phone']}** | 상품: **{row['u_product']}**")
                    
                    # 💡 [핵심] 박사님이 돋보기 들고 확인하실 수 있는 버튼
                    st.write(f"🔍 **1단계:** [👉 여기를 눌러 AI가 쓴 리포트를 먼저 검수하세요]({view_url})")
                    
                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    
                    # 💡 [핵심] 검수 완료 후, 박사님이 허락할 때만 고객한테 날아갑니다.
                    if st.button(f"📩 2단계: {row['name']}님께 카톡/문자 발송 쏘기!", key=f"btn_send_{row['order_id']}", type="primary"):
                        with st.spinner("고객님께 알림톡을 발송 중입니다..."):
                            safe_product_name = row['u_product']
                            if "+" in safe_product_name:
                                safe_product_name = safe_product_name.split("+")[0].strip() + " 외 다수"
                                
                            send_ok, send_msg = send_solapi_auto_message(row['phone'], row['name'], safe_product_name, view_url)
                            
                            if send_ok: 
                                st.success(f"✅ {send_msg}")
                            else: 
                                st.warning(f"⚠️ 발송 실패: {send_msg}")

# ------------------------------------------------------------------------------
# 3. 📜 [고객 전용 결과 열람창] (깔끔한 인쇄 CSS 마법 적용)
# ------------------------------------------------------------------------------
def render_view_page(order_id):
    import streamlit as st
    import sqlite3
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 💡 u_product 로 안전하게 불러오기
    c.execute("SELECT name, u_product, status, result_html FROM orders WHERE order_id=?", (order_id,))
    res = c.fetchone()
    conn.close()
    
    if not res:
        st.error("존재하지 않거나 만료된 링크입니다.")
        return
        
    name, u_product, status, result_html = res
    if status != "분석완료" or not result_html:
        st.warning(f"열일 중! 💦 뚝딱뚝딱~ 현재 {name}님의 사주를 제가 꼼꼼하게 분석하고 있어요. 🧐✨ 입금 확인 후 하루(24시간) 안에는 무조건 도착하니 쪼금만 기다려주세요! 완성되면 카톡으로 알림 팍! 쏴드릴게요! 🚀")
        return

    final_html = str(result_html).strip()
    
    # 💡 인쇄할 때 웹페이지의 잡다한 메뉴와 버튼을 안 보이게 숨기는 마법 CSS
    st.markdown("""
        <style>
        @media print {
            header {visibility: hidden;} 
            footer {visibility: hidden;} 
            .stApp [data-testid="stToolbar"] {display: none;} 
            button {display: none !important;} 
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<button type="button" style="display:block; width:100%; background-color:#c9a764; color:white; padding:15px; border-radius:10px; border:none; font-weight:bold; margin-bottom:15px; cursor:pointer;" onclick="window.print();">📄 평생 소장용 PDF 다운로드</button>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray; font-size:12px; margin-top:-10px; margin-bottom:15px;'>💡 인쇄 창이 뜨면 대상을 <b>'PDF로 저장'</b>으로 선택해 주세요.</p>", unsafe_allow_html=True)
    
    st.markdown(final_html, unsafe_allow_html=True)
    
    st.markdown('<button type="button" style="display:block; width:100%; background-color:#c9a764; color:white; padding:15px; border-radius:10px; border:none; font-weight:bold; margin-top:15px; cursor:pointer;" onclick="window.print();">📄 리포트 하단 PDF 다운로드</button>', unsafe_allow_html=True)

# ==============================================================================
# 🚪 [URL 라우팅 문지기] - 고객, 관리자, 뷰어를 분리하는 핵심 로직
# ==============================================================================
def run_pipeline_router(generator_func):
    """
    URL mode를 감지해서 고객 폼, 관리자 패널, 뷰어로 안내하는 통합 문지기
    """
    import streamlit as st
    
    # URL에서 mode 값과 code(주문번호) 값을 안전하게 가져옵니다.
    mode = st.query_params.get("mode", "")
    order_code = st.query_params.get("code", "")

    # 1️⃣ 고객 신청 폼 (?mode=order)
    if mode == "order":
        render_customer_order_form()
        st.stop()  # 메인 공장 로딩 차단

    # 2️⃣ 관리자 패널 (?mode=admin)
    elif mode == "admin":
        render_admin_panel(generator_func)
        st.stop()  # 메인 공장 로딩 차단

    # 3️⃣ 고객 결과 열람 뷰어 (?mode=view&code=주문번호)
    elif mode == "view":
        if order_code:
            render_view_page(order_code)
        else:
            st.warning("⚠️ 주문번호가 없습니다. 올바른 링크로 접속해 주세요.")
        st.stop()  # 메인 공장 로딩 차단
