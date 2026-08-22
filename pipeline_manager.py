# ==============================================================================
# pipeline_manager.py (ver 82.1 Master - KST 한국시간 동기화 및 무소음 통합)
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
import pytz  # 💡 [핵심 패치] 한국 시간을 맞추기 위해 타임존 모듈 추가!

DB_FILE = "choyeon_orders.db"
ADMIN_PASSWORD = "boss!631201"

PRODUCT_MAP = {
    "1-1. 사주팔자와 운세풀이 (정가 22,000원 ➡️ 추석특가 11,000원)": "1-1. 사주팔자 및 운세 분석",
    "1-2. 올 해 (특정 연도) 운세 상세분석 (정가 11,000원 ➡️ 추석특가 5,500원)": "1-2. 올 해 (특정 년도) 운세 상세분석",
    "1-3. 이번 달 (특정 월) 운세 상세분석 (정가 11,000원 ➡️ 추석특가 5,500원)": "1-3. 이번 달 (특정 월) 운세 상세분석",
    "1-4. 이번(특정) 주 및 일 운세 상세분석 (정가 4,400원 ➡️ 추석특가 2,200원)": "1-4. 이번(특정) 주간/일 운세 상세분석",
    "2-1. 재물운 특화 분석 (정가 22,000원 ➡️ 추석특가 11,000원)": "2-1. 재물운 특화 분석",
    "2-2. 직업/진학운 특화 분석 (정가 22,000원 ➡️ 추석특가 11,000원)": "2-2. 직업/진학운 특화 분석",
    "2-3. 연애/결혼운 특화 분석 (정가 22,000원 ➡️ 추석특가 11,000원)": "2-3. 커플 연애/결혼운 특화 분석",
    "2-4. 건강운 특화 분석 (정가 11,000원 ➡️ 추석특가 5,500원)": "2-4. 건강운 특화 분석",
    "2-5. 이사 및 개업 택일 (정가 11,000원 ➡️ 추석특가 5,500원)": "2-5. 이사/개업 택일 특화 분석",
    "3-1. 연애/결혼운 (궁합) 풀이 (정가 44,000원 ➡️ 추석특가 22,000원)": "3-1. 커플 연애/결혼운 (궁합) 분석",
    "3-2. 결혼 택일 (정가 22,000원 ➡️ 추석특가 11,000원)": "3-2. 결혼 택일 특화 분석",
    "3-3. 출산 택일 (정가 66,000원 ➡️ 추석특가 33,000원)": "3-3. 출산 택일 특화 분석"
}

U_PRODUCT_LIST = list(PRODUCT_MAP.keys())
idx_list = ["시간 모름", "00:30 ~ 01:29 (朝子)시", "01:30 ~ 03:29 (丑)시", "03:30 ~ 05:29 (寅)시", "05:30 ~ 07:29 (卯)시", "07:30 ~ 09:29 (辰)시", "09:30 ~ 11:29 (巳)시", "11:30 ~ 13:29 (午)시", "13:30 ~ 15:29 (未)시", "15:30 ~ 17:29 (申)시", "17:30 ~ 19:29 (酉)시", "19:30 ~ 21:29 (戌)시", "21:30 ~ 23:29 (亥)시", "23:30 ~ 00:29 (夜子)시"]

def get_db_connection(): return sqlite3.connect(DB_FILE)
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
            order_id TEXT PRIMARY KEY, created_at TEXT, phone TEXT, email TEXT, name TEXT, gender TEXT,
            marital TEXT, u_cal TEXT, b_year INTEGER, b_month INTEGER, b_day INTEGER, b_time TEXT,
            u_product TEXT, f_name TEXT, f_gender TEXT, f_marital TEXT, f_cal TEXT, f_y INTEGER,
            f_m INTEGER, f_d INTEGER, f_t TEXT, user_concern TEXT, status TEXT, result_html TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ------------------------------------------------------------------------------
# 📡 🚨 [솔라피 (Solapi) 무과금 테스트 모드 유지] 🚨
# ------------------------------------------------------------------------------
def send_solapi_custom_message(to_phone, name, msg_body):
    try:
        # 박사님 테스트 시 비용 청구를 막기 위해 API 강제 차단!
        time.sleep(0.5) 
        return True, "[테스트 모드] 솔라피 실과금 없이 가상 발송 성공"
    except Exception as e: return False, str(e)

def send_solapi_admin_alert(now_str, name, product_summary, final_price):
    try:
        time.sleep(0.5)
        return True, "성공"
    except Exception as e: return False, str(e)

def calculate_package_price(selected_products):
    if not selected_products: return 0, 0, 0, 0, 0
    total_original = sum(int(item.split('정가')[-1].split('원')[0].replace(',', '').strip()) for item in selected_products)
    total_chuseok = sum(int(item.split('추석특가')[-1].replace('원)', '').replace(',', '').strip()) for item in selected_products)
    count = len(selected_products)
    rate = 0.30 if count >= 3 or any("3-" in PRODUCT_MAP[p] for p in selected_products) else (0.20 if count > 1 else 0)
    final_price = int(round(total_chuseok * (1 - rate), -3))
    total_rate_pct = int(((total_original - final_price) / total_original) * 100) if total_original > 0 else 0
    return total_original, total_chuseok, int(rate*100), total_rate_pct, final_price

def generate_smart_marketing_text(row, view_url):
    name, product, concern = row.get('name', '고객'), row.get('u_product', ''), str(row.get('user_concern', '')).replace(' ', '')
    b_year = int(row.get('b_year', 1980))
    age = datetime.now().year - b_year + 1
    clean_product = re.sub(r'\d-\d\.\s*', '', product).split('(')[0].strip()
    if '+' in clean_product: clean_product = clean_product.split('+')[0].strip() + " 외 패키지"
    
    msg = f"{name}님, 오래 기다리셨습니다. 신청하신 [{clean_product}] 정밀 분석이 완료되었습니다.\n\n🔗 감명서 확인하기: {view_url}\n\n"
    msg += f"🎁 [정성 후기 이벤트]\n감명서가 마음에 드셨다면 따뜻한 후기 부탁드립니다! 후기 링크를 주시면 박사님께서 직접 [1개월 정밀 월운 감명서(11,000원 상당)]를 무료로 분석해 드립니다.\n\n💡 [박사님의 추천]\n"
    
    if "궁합" in product or "3-1" in product: msg += "두 분의 인연법이 깊습니다. 완벽한 날, [3-2. 결혼 택일 특화 분석]으로 최고의 시작을 준비해 보세요."
    elif "1-2" in product or "올 해" in product: msg += "올해 운의 큰 흐름을 잡으셨다면, 이제 내게 꼭 맞는 금전운의 맥점을 짚을 차례입니다. [2-1. 재물운 특화 분석]을 강력 추천합니다."
    elif any(kw in concern for kw in ["돈", "재물", "빚", "투자", "금전"]): msg += "말씀하신 재물 흐름에 대한 갈증, [2-1. 재물운 특화 분석]에서 확실한 타개책을 짚어드립니다."
    elif age >= 50 or any(kw in concern for kw in ["건강", "수술", "질병"]): msg += "무엇보다 건강이 최고입니다. 내 몸의 취약점과 운기를 파악하는 [2-4. 건강운 특화 분석]을 확인해 보세요."
    elif age <= 39 and any(kw in concern for kw in ["연애", "결혼", "이성"]): msg += "평생을 함께할 귀인, [2-3. 커플 연애/결혼운 특화 분석]을 통해 인연법을 확인해 보세요."
    else: msg += "올해 나의 운기가 어떻게 흘러가는지 [1-2. 올해 연운 상세분석]으로 확인하여 다가올 기회를 꽉 잡으세요!"
    msg += "\n\n초연 시공명리 연구소를 찾아주셔서 감사합니다."
    return msg

# ------------------------------------------------------------------------------
# 1. 📱 [고객 모바일 접수 화면] 
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
        price_display = f"<b style='font-size:17px;'>{ord_info['final_price']:,}원</b>"
        st.markdown(f"""
        <div class='guide-box'>
        <div class='pay-title'>[ 🏮 신청 접수 완료! 🏮 ]</div>
        <b>{ord_info['name']}</b>님, 환영합니다!<br>
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

    st.markdown("<div class='promo-banner'><b style='color:#E65100; font-size:17px;'>[ 8/18 ~ 9/30 ] <br>🌕 추석 맞이 반값 특가! 🌕</b></div>", unsafe_allow_html=True)

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
        if any("3-" in PRODUCT_MAP[prod] for prod in selected_products):
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("<b>3. 👩‍❤️‍👨 상대방 정보 (궁합/택일)</b>", unsafe_allow_html=True)
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
        user_concern_text = st.text_area("답답한 고민들을 편하게 털어놓아 보세요.", height=100)
        agree = st.checkbox("개인정보 수집 및 제공에 동의합니다. *(필수)")
        submitted = st.form_submit_button("🏮 사주풀이 신청하기 🏮", type="primary", use_container_width=True)
        
        if submitted:
            if not name.strip() or not p_mid.strip() or not p_end.strip() or not b_year.isdigit() or not selected_products or not agree:
                st.error("🚨 필수 입력값을 확인해 주십시오.")
                return
            calc_result = calculate_package_price(selected_products)
            total_original, total_chuseok, pkg_rate_pct, total_rate_pct, final_price = calc_result
            db_product_codes = " + ".join(selected_products)
            clean_ui_names = [re.sub(r'\d-\d\.\s*', '', PRODUCT_MAP[p]) for p in selected_products]
            ui_product_desc = " + ".join(clean_ui_names) + f" ({final_price:,}원)"
            order_id = str(uuid.uuid4())[:8]
            phone_full = f"010-{p_mid.strip()}-{p_end.strip()}"
            
            # 💡 [핵심 패치] KST(한국 표준시)로 정확하게 DB에 기록합니다.
            kst = pytz.timezone('Asia/Seoul')
            now_str = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', 
                      (order_id, now_str, phone_full, memo_info, name.strip(), gender, marital, u_cal, int(b_year), int(b_month), int(b_day), b_time, db_product_codes, f_name, f_gender, f_marital, f_cal, f_y, f_m, f_d, f_t, user_concern_text, "입금대기", ""))
            conn.commit()
            conn.close()
            send_solapi_admin_alert(now_str, name.strip(), ui_product_desc, final_price)
            st.session_state["submitted_order"] = {"order_id": order_id, "name": name.strip(), "product_desc": ui_product_desc, "total_raw": total_original, "discount_amt": total_original-final_price, "rate_pct": total_rate_pct, "final_price": final_price}
            st.rerun()

# ------------------------------------------------------------------------------
# 👑 [박사님 전용 중앙 통제실 - 3단 서랍장 SPA 로직]
# ------------------------------------------------------------------------------
def render_admin_panel():
    ensure_db_table_exists()
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
            
    # =========================================================================
    # 🔽 [서랍장 1] 영업 장부 및 대기열
    # =========================================================================
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
                        if st.button(f"💰 입금 확인 (무소음 감명 시작) - {r_name}", key=f"pay_{r_oid}"):
                            st.session_state['u_n'], st.session_state['u_g'], st.session_state['u_m_stat'], st.session_state['u_c'] = r_name, row['gender'], row['marital'], row['u_cal']
                            st.session_state['s_y'], st.session_state['s_m'], st.session_state['s_d'] = int(row['b_year']), int(row['b_month']), int(row['b_day'])
                            st.session_state['s_t'], st.session_state['s_t_select'] = row['b_time'], row['b_time']
                            if "3-" in engine_prod:
                                st.session_state['f_n'], st.session_state['f_g'] = row['f_name'], row['f_gender']
                                st.session_state['p_y_in'], st.session_state['p_m_in'], st.session_state['p_d_in'], st.session_state['p_t_key'] = int(row.get('f_y', 1980)), int(row.get('f_m', 1)), int(row.get('f_d', 1)), row.get('f_t', '시간 모름')
                            
                            if "1-" in engine_prod: st.session_state['main_category'], st.session_state['sub_category_1'] = "1. 사주팔자 및 운세 풀이 (종합)", engine_prod
                            elif "2-" in engine_prod: st.session_state['main_category'], st.session_state['sub_category_2'] = "2. 테마별 특성화 상담", engine_prod
                            elif "3-" in engine_prod: st.session_state['main_category'], st.session_state['sub_category_3'] = "3. 연애/결혼운 (궁합) 풀이", engine_prod
                            
                            st.session_state['admin_proc_id'] = r_oid
                            st.session_state['app_running'] = True
                            st.rerun()

    # =========================================================================
    # 🔽 [서랍장 2 & 3] 감명 완료 시 해당 화면 아래에 즉시 출현
    # =========================================================================
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
                view_url = f"https://choyeon-spacetime.streamlit.app/?mode=view&code={gid}"
                st.session_state[f"sms_{gid}"] = generate_smart_marketing_text(row, view_url)
            
            st.markdown("#### 💡 영업부가 작성해 온 [맞춤형 1:1 타겟팅 영업 문자] 입니다.")
            st.caption("고객의 나이, 고민거리, 구매 상품을 분석하여 가장 확률 높은 문구를 자동 세팅했습니다.")
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
# 📜 [고객 전용 결과 열람창] 
# ------------------------------------------------------------------------------
def render_view_page(order_id):
    ensure_db_table_exists()
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM orders WHERE order_id='{order_id}'", conn)
    conn.close()
    if df.empty: st.error("존재하지 않거나 만료된 링크입니다."); return
    row = df.iloc[0]
    if row.get('status', '') != "분석완료" or not row.get('result_html', ''):
        st.warning(f"열일 중! 💦 현재 {row.get('name','고객')}님의 사주를 꼼꼼하게 분석하고 있습니다.")
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
