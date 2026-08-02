else:
                # 💡 [VIP 스마트 누적 아키텍처 적용]
                is_vip_active = st.session_state.get("is_vip_package_val", False)
                
                if 'report_essays' not in st.session_state:
                    st.session_state['report_essays'] = {}
                if 'vip_base_fact' not in st.session_state:
                    st.session_state['vip_base_fact'] = ""

                # 최초 1회 또는 비-VIP 모드일 때 사주 명식/대운 팩트 박스 고정 저장
                if not st.session_state['vip_base_fact'] or not is_vip_active:
                    st.session_state['vip_base_fact'] = part_1_fact + part_2_intro + part_3_golden

                # 현재 상품의 AI 통변 포장 (1-4번은 표 깨짐 방지 압축 예외 처리 적용)
                if "1-4." in u_product:
                    current_ai_block = f"<div style='margin-top: 20px;'>{ai_output_html}</div>" if ai_output_html else ""
                else:
                    cleaned_ai = re.sub(r'>\s+<', '><', ai_output_html.replace('\n', '')).strip() if ai_output_html and 're' in globals() else ai_output_html
                    current_ai_block = f"<div style='margin-top: 20px;'>{cleaned_ai}</div>" if cleaned_ai else ""

                if is_vip_active:
                    # VIP 모드: 기존 항목은 유지하고 현재 선택한 상품의 통변 내용만 추가/갱신
                    st.session_state['report_essays'][u_product] = current_ai_block
                else:
                    # 일반 모드: 현재 단일 상품만 리셋 저장
                    st.session_state['report_essays'] = {u_product: current_ai_block}

                # 표지 출력
                st.markdown(cover_html, unsafe_allow_html=True)

                # 📚 [최종 종합 보고서 조립 및 렌더링]
                # 1. 앞단에 웅장한 사주 명식 및 대운·기본 팩트 단 1회 고정 배치
                master_composite_report = st.session_state['vip_base_fact']

                # 2. 사용자가 가동한 모든 세부 통변 항목들을 아래로 차곡차곡 결합
                for prod_name, essay_block in st.session_state['report_essays'].items():
                    master_composite_report += essay_block

                # 3. 마지막에 클로징 맺음말 장착
                master_composite_report += part_5_closing

                # 4. 최종 완성본 단일 상자에 담아 렌더링 (1-4번 표 깨짐 방지 분기 포함)
                if "1-4." in u_product:
                    st.markdown(html_views.get_final_report_box(master_composite_report), unsafe_allow_html=True)
                else:
                    st.markdown(html_views.get_final_report_box(master_composite_report), unsafe_allow_html=True)
