if meta_data:
            final_concern += f"\n\n---META_START---\n{json.dumps(meta_data)}\n---META_END---"

        if not phone_full:
            st.error("🚨 휴대폰 번호를 010으로 시작하는 숫자 11자리로 입력해 주세요. (예: 01012345678)")
            return

        if not name.strip() or not b_year.isdigit() or not selected_products or not agree:
            st.error("🚨 필수 입력값을 확인해 주십시오.")
            return

        try:
            kst_today = datetime.now(pytz.timezone('Asia/Seoul')).date()
            birth_y = int(b_year)
            birth_m = int(b_month) if b_month.isdigit() else 1
            birth_d = int(b_day) if b_day.isdigit() else 1
            calc_age = kst_today.year - birth_y - ((kst_today.month, kst_today.day) < (birth_m, birth_d))
        except Exception:
            calc_age = 99

        if calc_age < 14:
            st.error("🚨 만 14세 미만은 법정대리인의 동의 없이 서비스를 이용하실 수 없습니다. 카카오 채팅으로 문의해 주세요.")
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
