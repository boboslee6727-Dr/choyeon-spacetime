def render_admin_panel(generator_func):
    st.subheader("👑 사주박사 관리자 장부 및 감명 발송 패널")
    pwd = st.sidebar.text_input("관리자 비밀번호", type="password")
    if pwd != ADMIN_PASSWORD:
        st.warning("🔒 관리자 암호를 입력하여 주십시오.")
        return

    # 💡 [정석]: 테이블이 없으면 자동 생성하고, 안전하게 연결하여 조회합니다.
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            name TEXT,
            gender TEXT,
            marital TEXT,
            calendar_type TEXT,
            birth_date TEXT,
            birth_time TEXT,
            phone TEXT,
            email TEXT,
            product TEXT,
            status TEXT,
            created_at TEXT,
            report_html TEXT
        )
    """)
    conn.commit()
    
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
                        if st.button(f"💰 입금 확인 (리포트 생성 및 발송)", key=f"btn_pay_{row['order_id']}", use_container_width=True, type="primary"):
                            try:
                                with st.spinner(f"{row['name']}님의 정밀 분석 리포트를 생성 중입니다..."):
                                    if generator_func:
                                        report_html = generator_func(row.to_dict())
                                        save_report_to_db(row['order_id'], report_html)
                                        update_order_status(row['order_id'], "분석완료")
                                        st.success(f"✅ {row['name']}님 리포트 생성 및 저장 완료!")
                                        st.rerun()
                                    else:
                                        st.error("🚨 리포트 생성 엔진(generator_func)이 연결되지 않았습니다.")
                            except Exception as e:
                                st.error(f"🚨 [에러] 원인: {e}")
                                
                    with c2:
                        st.caption("⚠️ 미입금 안내 문자:")
                        st.code(f"[{row['name']}님] 사주박사 입금 계좌 안내 (생략)", language="text")

    with tab2:
        completed_orders = df[df["status"] == "분석완료"]
        if completed_orders.empty:
            st.info("아직 분석 완료된 내역이 없습니다.")
        else:
            for _, row in completed_orders.iterrows():
                view_url = f"/?mode=view&code={row['order_id']}"
                with st.expander(f"✅ [{row['name']} 님] (열람코드: {row['order_id']})", expanded=True):
                    st.write(f"- 연락처: **{row['phone']}** | [리포트 바로보기]({view_url})")
