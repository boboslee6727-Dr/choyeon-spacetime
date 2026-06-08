if btn_single:
        if not u_name.strip(): 
            st.warning("⚠️ 신청인의 이름을 입력해 주세요.")
        elif u_product == "타 감명서" and not other_reading_text.strip():
            st.warning("⚠️ 타 감명서 원문을 입력해 주세요.")
        elif u_product == "궁합" and not p_name.strip(): 
            st.warning("⚠️ 상대방의 이름을 입력해 주세요.")
        else:
            st.session_state['app_running'] = True
            
            # 🚨 1. 궁합 보호 & 택일 단독 가동 (누락된 스위치 추가 수술 완료)
            if u_product == "궁합" and run_delivery_calc and st.session_state.get('saved_report_gh_g'):
                st.session_state['need_calc'] = False # 궁합 재연산 건너뛰기
                st.session_state['run_delivery_only'] = True # 🚨 누락되었던 택일 가동 스위치 온!
                if 'saved_report_del' in st.session_state: del st.session_state['saved_report_del']
            
            # 🚨 2. 개인사주 보호 & 일진 분석 단독 가동 (토큰 증발 완벽 차단)
            elif u_product == "개인사주" and run_iljin_calc and st.session_state.get('saved_report_html'):
                st.session_state['need_calc'] = False # 메인 사주풀이 재연산 건너뛰기!
                st.session_state['run_waterfall'] = True # 일진 모듈만 단독 가동 스위치 온!
                if 'saved_report_iljin' in st.session_state: del st.session_state['saved_report_iljin'] # 이전 일진 기록만 삭제
            
            # 🚨 3. 완전 초기화 후 전체 풀 가동 (처음 실행하거나 대상이 바뀔 때)
            else:
                st.session_state['need_calc'] = True # 전체 풀 가동
                st.session_state['run_waterfall'] = run_iljin_calc if u_product == "개인사주" else False 
                st.session_state['run_delivery_only'] = run_delivery_calc if u_product == "궁합" else False # 스위치 초기화
                # 기존 캐시 모조리 삭제 (새로운 분석을 위해)
                for key in ['saved_report_html', 'saved_report_2', 'saved_report_gh_cover', 'saved_report_gh_m', 'saved_report_gh_f', 'saved_report_gh_g', 'saved_report_del', 'saved_report_iljin']:
                    if key in st.session_state: del st.session_state[key]
