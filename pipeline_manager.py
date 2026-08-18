# ==============================================================================
# pipeline_manager🏮 초연 시공명리: 신청접수 ~ 수동 입금승인 ~ 최종 분석 파이프라인 (ver 360.5 웹 전환본)
# ==============================================================================
import streamlit as st
import sqlite3
import os
import uuid
import pandas as pd
from datetime import datetime

DB_FILE = "choyeon_orders.db"
LEDGER_FILE = "초연시공_비밀장부.csv"
ADMIN_PASSWORD = "choyeon_master_pass" # 박사님 전용 관리자 암호 (자유 변경 가능)

# 12개 정식 상품 체계
PRODUCT_LIST = [
    "1-1. 사주팔자 및 평생 총운 풀이 (33,000원)",
    "1-2. 올 해 (특정 연도) 운세 상세분석 (22,000원)",
    "1-3. 이번 달 (특정 월) 운세 상세분석 (11,000원)",
    "1-4. 이번 주간 및 일진 운세 (무료/5,000원)",
    "2-1. 재물운 & 자산 축적 타이밍 특화 (22,000원)",
    "2-2. 직업/진로/이직/승진운 특화 (22,000원)",
    "2-3. 연애/결혼운 & 사전 흉화예방 특화 (22,000원)",
    "2-4. 건강운 & 조토극수 체질분석 특화 (22,000원)",
    "2-5. 이사 및 개업 택일 특화 (22,000원)",
    "3-1. 부부/연인 정밀 궁합 풀이 (33,000원)",
    "3-2. 백년가약 결혼 택일 (33,000원)",
    "3-3. 명품 출산 택일 (Top 5 길일) (55,000원)"
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
# 1. 📱 [고객 모바일 접수 화면] (ver 360.5 이식)
# ------------------------------------------------------------------------------
def render_customer_order_form():
    st.markdown("""
    <style>
        .mobile-box { max-width: 480px; margin: 0 auto; background: #FFFFFF; border: 3px solid #1A237E; border-radius: 15px; padding: 20px; font-family: 'Nanum Myeongjo', serif; }
        .m-title { font-size: 22px; font-weight: 900; color: #1A237E; text-align: center; border-bottom: 2px double #1A237E; padding-bottom: 8px; margin-bottom: 15px; }
        .req { color: #D50000; font-weight: bold; }
        .guide-box { background: #FAFAFA; border: 2px solid #6D4C41; border-radius: 10px; padding: 20px; margin-top: 15px; line-height: 1.8; color: #111; }
        .pay-title { font-size: 20px; font-weight: 900; color: #1A237E; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='m-title'>🏮 초연 시공명리 감명 신청서</div>", unsafe_allow_html=True)
    
    with st.form("choyeon_order_form"):
        name = st.text_input("성명 *(필수)", placeholder="성함을 입력하세요")
        
        c_p1, c_p2, c_p3 = st.columns([1.2, 1.5, 1.5])
        with c_p1: st.text_input("통신사/국번", value="010", disabled=True)
        with c_p2: p_mid = st.text_input("중간 4자리 *(필수)", max_chars=4, placeholder="1234")
        with c_p3: p_end = st.text_input("끝 4자리 *(필수)", max_chars=4, placeholder="5678")
        
        email = st.text_input("이메일 (선택)", placeholder="choyeon@example.com")
        
        c_y, c_m, c_d = st.columns(3)
        with c_y: b_year = st.text_input("생년 (YYYY) *", max_chars=4, placeholder="1980")
        with c_m: b_month = st.text_input("월 (MM) *", max_chars=2, placeholder="05")
        with c_d: b_day = st.text_input("일 (DD) *", max_chars=2, placeholder="15")
        
        c_g, c_c, c_m_stat = st.columns(3)
        with c_g: gender = st.selectbox("성별 *", ["여성", "남성"])
        with c_c: cal_type = st.selectbox("양/음력 *", ["양력", "음력", "음력(윤달)"])
        with c_m_stat: marital = st.selectbox("혼인 상태 *", ["미혼", "기혼"])
        
        b_time = st.selectbox("태어난 시간 *(필수)", TIME_OPTIONS)
        product = st.selectbox("상담 상품 선택 *(필수)", PRODUCT_LIST)
        
        agree = st.checkbox("개인정보 수집 및 감명 제공에 동의합니다. *(필수)")
        
        submitted = st.form_submit_button("🏮 감명 신청서 제출하기 (복비 안내)", use_container_width=True)
        
        if submitted:
            # ver 360.5 엄격 검증 로직
            if not name.strip():
                st.error("🚨 성명을 입력해 주십시오.")
                return
            if len(p_mid.strip()) != 4 or len(p_end.strip()) != 4 or not (p_mid.isdigit() and p_end.isdigit()):
                st.error("🚨 휴대전화 번호 4자리를 숫자로 정확히 입력해 주십시오.")
                return
            if not (b_year.isdigit() and b_month.isdigit() and b_day.isdigit()):
                st.error("🚨 생년월일 숫자를 정확히 입력해 주십시오.")
                return
            if not agree:
                st.error("🚨 개인정보 제공에 동의해 주십시오.")
                return
            
            order_id = str(uuid.uuid4())[:8]
            phone_full = f"010-{p_mid.strip()}-{p_end.strip()}"
            birth_full = f"{b_year.strip()}-{b_month.strip().zfill(2)}-{b_day.strip().zfill(2)}"
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # DB 저장 (입금대기 상태 - AI 호출 0원)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, now_str, name.strip(), phone_full, email.strip(), birth_full, b_time, gender, cal_type, marital, product, "입금대기", ""))
            conn.commit()
            conn.close()
            
            st.session_state["submitted_order"] = {
                "order_id": order_id, "name": name.strip(), "product": product
            }
            st.rerun()

    # 신청 완료 및 입금 안내 화면 (ver 360.5 100% 반영)
    if "submitted_order" in st.session_state:
        ord_info = st.session_state["submitted_order"]
        st.markdown(f"""
        <div class='guide-box'>
            <div class='pay-title'>[ 🏮 신청 접수 완료 ]</div>
            <b>{ord_info['name']}</b>님 안녕하세요. 😊<br>
            신청번호: <b>{ord_info['order_id']}</b><br>
            <b>"{ord_info['product']}"</b> 분석 신청이 정상 접수되었습니다.<br><br>
            아래 계좌로 복비를 입금해 주시면, 박사님 확인 즉시 정밀 감명이 시작됩니다.<br><br>
            <b>국민은행</b><br>
            <b>231402-04-13322*</b><br>
            <b>예금주: 이 * 호</b><br>
            <b>복비: {ord_info['product'].split('(')[-1].replace(')', '')}</b><br><br>
            <span style='color:#D50000; font-weight:bold;'>※ 신청자와 입금자 성명이 다를 경우 카카오톡 채널로 알려주세요.</span><br><br>
            <b>초연 시공명리 연구소</b>
        </div>
        """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. 👑 [박사님 전용 관리자 수동 승인 패널] (?mode=admin)
# ------------------------------------------------------------------------------
def render_admin_panel(generator_func):
    st.subheader("👑 초연 시공명리 관리자 장부 및 감명 승인 패널")
    
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
        
    st.dataframe(df[["order_id", "created_at", "name", "phone", "birth_date", "birth_time", "product", "status"]])
    
    st.markdown("---")
    st.markdown("### 💰 입금 확인 및 감명 생성 처리")
    
    pending_orders = df[df["status"] == "입금대기"]
    if pending_orders.empty:
        st.success("모든 대기열의 감명이 완료되었습니다.")
    else:
        for _, row in pending_orders.iterrows():
            c1, c2, c3 = st.columns([2, 1.5, 1.5])
            with c1:
                st.write(f"**[{row['name']} 님]** ({row['phone']}) - {row['product']}")
            with c2:
                if st.button(f"💰 입금 확인 (감명 생성)", key=f"btn_pay_{row['order_id']}"):
                    with st.spinner(f"{row['name']}님의 ver 73.0 정밀 감명서를 생성 중입니다..."):
                        # 백그라운드 AI 엔진 풀가동
                        html_result = generator_func(row)
                        
                        # DB 완료 업데이트
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("UPDATE orders SET status='분석완료', result_html=? WHERE order_id=?", (html_result, row['order_id']))
                        conn.commit()
                        conn.close()
                        
                        # CSV 장부 기록 (ver 360.5 비밀장부 동기화)
                        ledger_row = {
                            '접수일시': [row['created_at']], '성명': [row['name']], '연락처': [row['phone']],
                            '생년월일': [row['birth_date']], '태어난시간': [row['birth_time']],
                            '신청상품': [row['product']], '진행상태': ['분석완료']
                        }
                        df_led = pd.DataFrame(ledger_row)
                        if os.path.exists(LEDGER_FILE):
                            df_led.to_csv(LEDGER_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
                        else:
                            df_led.to_csv(LEDGER_FILE, mode='w', header=True, index=False, encoding='utf-8-sig')
                            
                        st.success(f"✅ {row['name']}님 감명서 생성 완료!")
                        st.rerun()
            with c3:
                # 미입금 안내 문자 복사 기능
                msg = f"[초연시공명리] {row['name']}님, 신청하신 {row['product'].split(' (')[0]} 복비 입금이 확인되지 않아 안내드립니다. 국민은행 231402-04-13322* 이*호"
                st.code(msg, language="text")

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
        st.warning(f"현재 {name}님의 감명서를 정밀 분석 중입니다. 입금 확인 후 1일 이내에 완료됩니다.")
        return
        
    st.markdown(result_html, unsafe_allow_html=True)
