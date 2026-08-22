# ==============================================================================
# pipeline_manager.py (ver 75.5 - 고객 오리지널 UI 100% 복원 및 스키마 방탄)
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
ADMIN_PASSWORD = "boss!631201"
BASE_URL = "https://choyeon-spacetime.streamlit.app"

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
# 🛠️ [필수 DB 헬퍼 함수]
# ------------------------------------------------------------------------------
def get_db_connection():
    return sqlite3.connect(DB_FILE)

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

def ensure_db_table_exists():
    conn = get_db_connection()
    c = conn.cursor()
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
# 📡 [솔라피 (Solapi) 발송 함수]
# ------------------------------------------------------------------------------
def get_solapi_auth_header(api_key, api_secret):
    date_str = datetime.now().astimezone().isoformat()
    salt = str(uuid.uuid4().hex)
    combined = date_str + salt
    signature = hmac.new(api_secret.encode('utf-8'), combined.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"HMAC-SHA256 apiKey={api_key}, date={date_str}, salt={salt}, signature={signature}"

def send_solapi_auto_message(to_phone, name, product, view_url):
    try:
        api_key = st.secrets.get("SOLAPI_API_KEY")
        api_secret = st.secrets.get("SOLAPI_API_SECRET")
        from_phone = st.secrets.get("SOLAPI_SENDER_PHONE")
        if not api_key or not api_secret or not from_phone: return False, "설정 누락"

        msg_body = f"{name}님, 신청하신 사주 분석이 완료되었습니다.\n\n🔮 신청 상품: {product}\n\n아래 링크를 눌러 소름 돋는 인생 스포일러(사주 리포트)를 바로 확인해 보세요!\n\n결과 확인하기:\n{view_url}"
        
        headers = {"Authorization": get_solapi_auth_header(api_key, api_secret), "Content-Type": "application/json; charset=utf-8"}
        payload = {"message": {"to": to_phone.replace("-", "").strip(), "from": from_phone.replace("-", "").strip(), "text": msg_body, "subject": f"[사주박사] {name}님 사주 리포트 도착", "type": "LMS"}}
        res = requests.post("https://api.solapi.com/messages/v4/send", headers=headers, json=payload, timeout=10)
        return (True, "발송 완료") if res.status_code == 200 else (False, "발송 실패")
    except Exception as e:
        return False, str(e)

def send_solapi_admin_alert(now_str, name, product_summary, base_price, discount_amt, final_price):
    try:
        api_key = st.secrets.get("SOLAPI_API_KEY")
        api_secret = st.secrets.get("SOLAPI_API_SECRET")
        from_phone = st.secrets.get("SOLAPI_SENDER_PHONE")
        if not api_key: return False, "설정 누락"

        short_time = now_str.replace("-", "/").rsplit(":", 1)[0]
        admin_msg = f"{short_time}/ {name.strip()}님 / {product_summary} / {base_price:,}원 -> {discount_amt:,}원 -> {final_price:,}원"
        headers = {"Authorization": get_solapi_auth_header(api_key, api_secret), "Content-Type": "application/json"}
        payload = {"message": {"to": "01038576727", "from": from_phone.replace("-", "").strip(), "text": admin_msg, "type": "SMS"}}
        requests.post("https://api.solapi.com/messages/v4/send", headers=headers, json=payload, timeout=5)
        return True, "성공"
    except Exception as e:
        return False, str(e)

# ------------------------------------------------------------------------------
# 🧮 [패키지 할인 연산]
# ------------------------------------------------------------------------------
def calculate_package_price(selected_products):
    if not selected_products: return 0, 0, 0, 0, 0
    total_original = sum(int(item.split('정가')[-1].split('원')[0].replace(',', '').strip()) for item in selected_products)
    total_chuseok = sum(int(item.split('추석특가')[-1].replace('원)', '').replace(',', '').strip()) for item in selected_products)
    
    count = len(selected_products)
    rate = 0.30 if count >= 3 or all(p.split('.')[0] in ["3-1", "3-3"] for p in selected_products) else (0.20 if count > 1 else 0)
    final_price = int(round(total_chuseok * (1 - rate), -3))
    total_rate_pct = int(((total_original - final_price) / total_original) * 100) if total_original > 0 else 0
    return total_original, total_chuseok, int(rate*100), total_rate_pct, final_price

# ------------------------------------------------------------------------------
# 1. 📱 [고객 모바일 접수 화면] (박사님 오리지널 UI 100% 복원!)
# ------------------------------------------------------------------------------
def render_customer_order_form():
    ensure_db_table_exists()
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
        <b style='color:#E65100; font-size:17px;'>[ 8/18 ~ 9/30 ] <br>🌕 추석 맞이 반값 특가! 🌕</b><br>
        <span style='color:#424242; font-size:14px;'>기간 한정 <b>전 상품 50% 특별 할인</b> 진행 중!</span><br>
        <span style='color:#1A237E; font-size:13px; font-weight:bold;'>(※ 2개 이상 선택 시 추가 할인 적용!)</span>
    </div>
    """, unsafe_allow_html=True)

    with st.form("choyeon_customer_order_form_final"):
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
        st.markdown("<b>2. 🛍️ 상품 선택</b>", unsafe_allow_html=True)
        selected_products = st.multiselect("원하시는 상품을 모두 선택해주세요 *(필수)", U_PRODUCT_LIST)
        
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
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (order_id, now_str, phone_full, memo_info, name.strip(), gender, marital, u_cal, int(b_year), int(b_month), int(b_day), b_time, full_product_desc, f_name, f_gender, f_marital, f_cal, f_y, f_m, f_d, f_t, user_concern_text, "입금대기", ""))
            conn.commit()
            conn.close()
            
            send_solapi_admin_alert(now_str, name.strip(), full_product_desc, total_original, discount_amt, final_price)
            
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
# 2. 👑 [박사님 관리자 패널] (과거 DB 완벽 호환/방탄)
# ------------------------------------------------------------------------------
def render_admin_panel():
    ensure_db_table_exists()
    st.subheader("👑 사주박사 관리자 장부 및 감명 발송 패널")
    
    pwd = st.sidebar.text_input("관리자 비밀번호", type="password")
    admin_pwd = st.secrets.get("ADMIN_PASSWORD", ADMIN_PASSWORD) if hasattr(st, "secrets") else ADMIN_PASSWORD
    if pwd != admin_pwd:
        st.warning("🔒 관리자 암호를 입력하여 주십시오.")
        return

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM orders ORDER BY created_at DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("현재 접수된 신청 내역이 없습니다.")
        return
        
    tab1, tab2 = st.tabs(["⏳ [입금대기] 승인 및 감명 처리", "✅ [분석완료] 발송 결과 및 링크 관리"])
    
    with tab1:
        pending_orders = df[df["status"] == "입금대기"] if "status" in df.columns else df
        if pending_orders.empty:
            st.success("현재 입금 대기 중인 신청건이 없습니다.")
        else:
            for _, row in pending_orders.iterrows():
                r_name = row.get('name', '고객')
                r_prod = row.get('u_product', row.get('product', '사주 분석'))
                r_date = row.get('created_at', '날짜 미상')
                r_oid = row.get('order_id', '')
                r_cal = row.get('u_cal', row.get('calendar_type', '양력'))
                r_btime = row.get('b_time', row.get('birth_time', '시간 모름'))
                
                with st.expander(f"📌 [{r_name}] {r_prod} (신청일: {r_date})", expanded=True):
                    st.write(f"- 연락처: {row.get('phone', '')} | 생일: {row.get('b_year')}-{row.get('b_month')}-{row.get('b_day')} ({r_cal}) | 시간: {r_btime}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"💰 입금 확인 (리포트 자동생성 시작)", key=f"pay_{r_oid}", type="primary", use_container_width=True):
                            with st.spinner("AI 엔진 장전 중..."):
                                st.session_state['u_n'] = r_name
                                st.session_state['u_g'] = row.get('gender', '여성')
                                st.session_state['u_m_stat'] = row.get('marital', '선택')
                                st.session_state['u_c'] = r_cal
                                st.session_state['s_y'] = int(row.get('b_year', 1980))
                                st.session_state['s_m'] = int(row.get('b_month', 1))
                                st.session_state['s_d'] = int(row.get('b_day', 1))
                                st.session_state['s_t'] = r_btime
                                st.session_state['s_t_select'] = r_btime
                                
                                # 상대방 정보 주입 (궁합용)
                                if "3-" in r_prod:
                                    st.session_state['f_n'] = row.get('f_name', '상대방')
                                    st.session_state['f_g'] = row.get('f_gender', '남성')
                                    st.session_state['p_y_in'] = int(row.get('f_y', 1980))
                                    st.session_state['p_m_in'] = int(row.get('f_m', 1))
                                    st.session_state['p_d_in'] = int(row.get('f_d', 1))
                                    st.session_state['p_t_key'] = row.get('f_t', '시간 모름')
                                
                                # 상품 매핑
                                if "1-" in r_prod:
                                    st.session_state['main_category'] = "1. 사주팔자 및 운세 풀이 (종합)"
                                    st.session_state['sub_category_1'] = r_prod
                                elif "2-" in r_prod:
                                    st.session_state['main_category'] = "2. 테마별 특성화 상담"
                                    st.session_state['sub_category_2'] = r_prod
                                elif "3-" in r_prod:
                                    st.session_state['main_category'] = "3. 연애/결혼운 (궁합) 풀이"
                                    st.session_state['sub_category_3'] = r_prod
                                
                                st.session_state['ghost_order_id'] = r_oid
                                st.session_state['app_running'] = True
                                st.query_params.clear()
                                st.rerun()

    with tab2:
        completed_orders = df[df["status"] == "분석완료"] if "status" in df.columns else pd.DataFrame()
        if completed_orders.empty:
            st.info("아직 분석 완료된 내역이 없습니다.")
        else:
            for _, row in completed_orders.iterrows():
                r_oid = row.get('order_id', '')
                view_url = f"/?mode=view&code={r_oid}"
                with st.expander(f"✅ [{row.get('name', '')}] (열람코드: {r_oid})", expanded=True):
                    st.write(f"- 연락처: {row.get('phone', '')} | [리포트 바로보기]({view_url})")

# ------------------------------------------------------------------------------
# 3. 📜 [고객 전용 결과 열람창] 
# ------------------------------------------------------------------------------
def render_view_page(order_id):
    ensure_db_table_exists()
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM orders WHERE order_id='{order_id}'", conn)
    conn.close()
    
    if df.empty:
        st.error("존재하지 않거나 만료된 링크입니다.")
        return
        
    row = df.iloc[0]
    if row.get('status', '') != "분석완료" or not row.get('result_html', ''):
        st.warning(f"열일 중! 💦 현재 {row.get('name','고객')}님의 사주를 꼼꼼하게 분석하고 있습니다. 완료 시 카톡 알림을 드립니다! 🚀")
        return

    # 인쇄할 때 웹페이지의 잡다한 메뉴와 버튼을 안 보이게 숨기는 마법 CSS
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

    st.markdown(str(row['result_html']).strip(), unsafe_allow_html=True)

# ==============================================================================
# 🚪 [URL 라우팅 문지기]
# ==============================================================================
def run_pipeline_router():
    mode = st.query_params.get("mode", "")
    order_code = st.query_params.get("code", "")

    if mode == "order":
        render_customer_order_form()
        st.stop()
    elif mode == "admin":
        render_admin_panel()
        st.stop()
    elif mode == "view":
        if order_code:
            render_view_page(order_code)
        else:
            st.warning("⚠️ 올바른 링크로 접속해 주세요.")
        st.stop()
