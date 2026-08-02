def get_execution_yong(upper_group, lower_group):
    """
    상위 그룹(행운)과 하위 그룹(일간 기준 일지 십성)을 교차하여 
    실행 용운(用運) 그룹을 도출하는 5x5 매트릭스 연산 함수입니다.
    """
    matrix = {
        '비겁': {'비겁':'비겁', '식상':'식상', '재성':'재성', '관성':'관성', '인성':'인성'},
        '식상': {'비겁':'인성', '식상':'비겁', '재성':'식상', '관성':'재성', '인성':'관성'},
        '재성': {'비겁':'관성', '식상':'인성', '재성':'비겁', '관성':'식상', '인성':'재성'},
        '관성': {'비겁':'재성', '식상':'관성', '재성':'인성', '관성':'비겁', '인성':'식상'},
        '인성': {'비겁':'식상', '식상':'재성', '재성':'관성', '관성':'인성', '인성':'비겁'}
    }
    return matrix.get(upper_group, {}).get(lower_group, '비겁')

def get_matrix_keyword(che_group, yong_group):
    """
    체(體) 그룹과 용(用) 그룹 조합에 해당하는 임상 키워드를 텍스트에서 매핑합니다.
    """
    target_str = f"- 체({che_group})+용({yong_group}):"
    for line in CHE_YONG_MATRIX_TEXT.splitlines():
        if line.startswith(target_str):
            return line.split(":", 1)[1].strip()
    return "변화 감지"

# ==============================================================================
# 초연 시공명리 운세 분석 전용 통합 팩트 추출 엔진 (오류 원천 차단 완정본)
# ==============================================================================
def get_woonse_analysis_facts(ds, db, dw_g_cur, dw_j_cur, sewun_g, sewun_j, wolun_g, wolun_j, ilun_g, ilun_j):
    """
    일주(ds, db)와 대운/세운/월운/일운 간지를 바탕으로
    체운(體運), 용운(用運), 임상 키워드를 연쇄 도출합니다.
    """
    # 1. 하위 그룹 (일간 기준 일지의 십성) - 박사님 명쾌한 통찰 반영
    ilju_ss = get_ss(ds, db)
    ilju_lower_group = ilju_ss if isinstance(ilju_ss, str) else (ilju_ss[0] if isinstance(ilju_ss, (list, tuple)) and len(ilju_ss) > 0 else '비겁')
    
    # 2. 대운 체용 연산
    dw_upper_ss = get_ss(ds, dw_g_cur)
    dw_che = get_group_ss(dw_upper_ss) if 'get_group_ss' in globals() else str(dw_upper_ss)
    dw_yong = get_execution_yong(dw_che, ilju_lower_group)
    dw_kw = get_matrix_keyword(dw_che, dw_yong)
    
    # 3. 세운 체용 연산
    sewun_upper_ss = get_ss(ds, sewun_g)
    sewun_che = get_group_ss(sewun_upper_ss) if 'get_group_ss' in globals() else str(sewun_upper_ss)
    s_yong = get_execution_yong(sewun_che, ilju_lower_group)
    sewun_kw = get_matrix_keyword(dw_che, s_yong)
    
    # 4. 월운 체용 연산
    wolun_upper_ss = get_ss(ds, wolun_g)
    wolun_che = get_group_ss(wolun_upper_ss) if 'get_group_ss' in globals() else str(wolun_upper_ss)
    w_yong = get_execution_yong(wolun_che, ilju_lower_group)
    wolun_kw = get_matrix_keyword(sewun_che, w_yong)
    
    # 5. 일운 체용 연산
    ilun_upper_ss = get_ss(ds, ilun_g)
    ilun_che = get_group_ss(ilun_upper_ss) if 'get_group_ss' in globals() else str(ilun_upper_ss)
    i_yong = get_execution_yong(ilun_che, ilju_lower_group)
    ilun_kw = get_matrix_keyword(wolun_che, i_yong)
    
    # 팩트 스트링 조립
    woonse_fact_str = f"""
- [대운 체용 파동]: 體({dw_che}) + 用({dw_yong}) ➔ 핵심 키워드: [{dw_kw}]
- [세운 체용 파동]: 體({dw_che}) + 用({s_yong}) ➔ 핵심 키워드: [{sewun_kw}]
- [월운 체용 파동]: 體({sewun_che}) + 用({w_yong}) ➔ 핵심 키워드: [{wolun_kw}]
- [일운 체용 파동]: 體({wolun_che}) + 用({i_yong}) ➔ 핵심 키워드: [{ilun_kw}]
"""
    return {
        "dw_che": dw_che, "dw_yong": dw_yong, "dw_kw": dw_kw,
        "sewun_che": sewun_che, "sewun_yong": s_yong, "sewun_kw": sewun_kw,
        "wolun_che": wolun_che, "wolun_yong": w_yong, "wolun_kw": wolun_kw,
        "ilun_che": ilun_che, "ilun_yong": i_yong, "ilun_kw": ilun_kw,
        "woonse_fact_str": woonse_fact_str.strip()
    }
