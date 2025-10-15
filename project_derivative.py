import streamlit as st
import pandas as pd
import os
import re
import streamlit.components.v1 as components

# 페이지 설정 - 와이드 레이아웃 사용
st.set_page_config(page_title="파생상품 데이터 점검", layout="wide")

# CSS 스타일 적용
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
    }
    .block-container {
        padding: 1rem 1rem;
        max-width: 100%;
    }
    .scrollable-text {
        height: 250px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 10px;
        background-color: #f9f9f9;
        white-space: pre-wrap;
        font-family: 'Malgun Gothic', sans-serif;
    }
    .markdown-content {
        height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 20px;
        background-color: #ffffff;
    }
   
    /* 스크롤바 스타일링 - 더 눈에 띄게 */
    .scrollable-text::-webkit-scrollbar,
    .markdown-content::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
   
    .scrollable-text::-webkit-scrollbar-track,
    .markdown-content::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 6px;
        border: 1px solid #ddd;
    }
   
    .scrollable-text::-webkit-scrollbar-thumb,
    .markdown-content::-webkit-scrollbar-thumb {
        background: #4a90e2;
        border-radius: 6px;
        border: 1px solid #357abd;
    }
   
    .scrollable-text::-webkit-scrollbar-thumb:hover,
    .markdown-content::-webkit-scrollbar-thumb:hover {
        background: #357abd;
    }
   
    /* Firefox 스크롤바 */
    .scrollable-text,
    .markdown-content {
        scrollbar-width: thick;
        scrollbar-color: #4a90e2 #f1f1f1;
    }
   
    div[data-testid="column"] {
        padding: 0 5px;
    }
    .main-header {
        padding: 10px 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 20px;
    }
    a:hover {
        text-decoration: underline !important;
        color: #0070f3 !important;
    }
    .year-trend-table {
        margin-top: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀
st.markdown('<div class="main-header"><h1>파생상품 데이터 점검</h1></div>', unsafe_allow_html=True)

# 파일 업로더
uploaded_file = st.file_uploader("Excel 파일을 업로드하세요", type=['xlsx', 'xls'])

if uploaded_file is not None:
    # 데이터 로드 - '5_전체통합데이터' 시트 읽기
    @st.cache_data
    def load_data(file):
        return pd.read_excel(file, sheet_name='5_전체통합데이터')
   
    df = load_data(uploaded_file)
   
    # RCEPT_NO_NEW 중복 제거된 데이터
    df_unique = df.drop_duplicates(subset=['RCEPT_NO_NEW']).reset_index(drop=True)
   
    # 섹션 1: 최상단 - 필터 및 데이터 선택
    st.subheader("📋 데이터 필터링")
   
    # 필터를 두 개의 컬럼으로 배치
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # FAILED_STEP 필터 - 정수와 소수점 값 모두 처리
        failed_steps = sorted(df_unique['FAILED_STEP'].unique())
        # 표시용 문자열 생성 (정수는 정수로, 소수점은 그대로)
        failed_steps_display = []
        for step in failed_steps:
            if pd.notna(step):
                if float(step) == int(step):
                    failed_steps_display.append(str(int(step)))
                else:
                    failed_steps_display.append(str(step))
            else:
                failed_steps_display.append(str(step))
        
        selected_failed_step = st.selectbox(
            "FAILED_STEP 선택:",
            options=['전체'] + failed_steps,
            format_func=lambda x: '전체' if x == '전체' else (str(int(x)) if pd.notna(x) and float(x) == int(x) else str(x)),
            key='failed_step_filter'
        )
    
    with filter_col2:
        # REPORT_YY 연도 필터 추가
        report_years = sorted(df_unique['REPORT_YY'].dropna().unique())
        selected_year = st.selectbox(
            "연도 선택:",
            options=['전체'] + [int(year) for year in report_years],
            key='year_filter'
        )
   
    # 필터링 적용
    df_filtered = df_unique.copy()
    
    if selected_failed_step != '전체':
        df_filtered = df_filtered[df_filtered['FAILED_STEP'] == selected_failed_step]
    
    if selected_year != '전체':
        df_filtered = df_filtered[df_filtered['REPORT_YY'] == selected_year]
    
    df_filtered = df_filtered.reset_index(drop=True)
   
    # 데이터프레임과 선택된 기업 정보를 3:1 비율로 배치
    col_left, col_right = st.columns([3, 1])
   
    with col_left:
        st.markdown("**🔍 기업을 선택하려면 아래 표에서 왼쪽 체크박스를 클릭하세요**")
       
        display_cols = ['RCEPT_NO_NEW', 'STOCK_CODE', 'CORP_NAME', 'REPORT_YY', 'REPORT_MM', 'FAILED_STEP']
       
        # STOCK_CODE를 6자리로 맞추기
        df_display = df_filtered.copy()
        # NaN이나 null 값 처리 - 빈 값이면 그대로 두고, 값이 있으면 6자리로 맞춤
        def format_stock_code(x):
            if pd.isna(x) or str(x).strip() == '' or str(x) == 'nan':
                return ''
            else:
                # 숫자 부분만 추출하여 6자리로 맞춤
                code = str(x).strip()
                # 숫자만 추출
                numeric_code = re.sub(r'[^0-9]', '', code)
                if numeric_code:
                    return numeric_code.zfill(6)
                return code  # 숫자가 없으면 원본 반환
       
        df_display['STOCK_CODE'] = df_display['STOCK_CODE'].apply(format_stock_code)
       
        # 선택 가능한 데이터프레임 표시
        event = st.dataframe(
            df_display[display_cols],
            use_container_width=True,
            height=250,
            on_select="rerun",
            selection_mode="single-row"
        )
   
    with col_right:
        st.markdown("**📊 필터링 결과**")
        st.metric("총 레코드 수", len(df_filtered))
       
        # 선택된 기업 정보를 여기에 표시
        if event.selection and len(event.selection['rows']) > 0:
            selected_idx = event.selection['rows'][0]
           
            if selected_idx < len(df_filtered):
                selected_row = df_filtered.iloc[selected_idx]  # 원본 데이터에서 가져오기
                selected_rcept = selected_row['RCEPT_NO_NEW']
               
                # 선택된 기업 정보 표시
                st.success(f"✅ **{selected_row['CORP_NAME']}**")
                st.caption(f"RCEPT_NO: {selected_rcept}")
               
                # URL 하이퍼링크 표시
                all_rows = df[df['RCEPT_NO_NEW'] == selected_rcept]
                if 'URL' in all_rows.columns and pd.notna(all_rows['URL'].iloc[0]):
                    url = all_rows['URL'].iloc[0]
                    st.markdown(f'<span style="font-size: 20px;">📄 <a href="{url}" target="_blank">공시 URL 접속</a></span>', unsafe_allow_html=True)
   
    # 기업별 연도별 추세 표 추가
    if event.selection and len(event.selection['rows']) > 0:
        selected_idx = event.selection['rows'][0]
        
        if selected_idx < len(df_filtered):
            selected_row = df_filtered.iloc[selected_idx]
            selected_corp_name = selected_row['CORP_NAME']
            
            # 연도별 추세 표 섹션
            st.markdown("---")
            st.subheader(f"📈 {selected_corp_name} - 연도별 파생상품 현황 (2009-2024)")
            
            # 해당 기업의 모든 연도 데이터 가져오기
            corp_all_years_data = df_unique[df_unique['CORP_NAME'] == selected_corp_name]
            
            # 연도별 데이터 집계
            years = list(range(2009, 2025))  # 2009부터 2024까지
            
            # 결과를 저장할 딕셔너리
            year_data = {
                'Failed Step': [],
                '파생상품 개수': []
            }
            
            for year in years:
                year_rows = corp_all_years_data[corp_all_years_data['REPORT_YY'] == year]
                
                if len(year_rows) > 0:
                    # 해당 연도의 failed_step 가져오기 - 문자열로 변환
                    failed_step = year_rows['FAILED_STEP'].iloc[0]
                    # 정수인 경우와 소수점이 있는 경우 구분
                    if pd.notna(failed_step):
                        if float(failed_step) == int(failed_step):
                            year_data['Failed Step'].append(str(int(failed_step)))
                        else:
                            year_data['Failed Step'].append(str(failed_step))
                    else:
                        year_data['Failed Step'].append('-')
                    
                    # failed_step이 0인 경우 파생상품 개수 계산
                    if failed_step == 0:
                        # 해당 RCEPT_NO_NEW의 모든 행 가져오기
                        rcept_no = year_rows['RCEPT_NO_NEW'].iloc[0]
                        all_rows_for_rcept = df[df['RCEPT_NO_NEW'] == rcept_no]
                        
                        # 파생상품 관련 칼럼
                        derivative_cols = [
                            'company_name', 'trade_purpose', 'derivative_category',
                            'currency_derivative_type', 'trade_type', 'buy_amount',
                            'sell_amount', 'buy_amount_unit', 'sell_amount_unit',
                            'buy_currency_unit', 'sell_currency_unit', 'other_unit', 'remarks'
                        ]
                        
                        if all([col in all_rows_for_rcept.columns for col in derivative_cols]):
                            # 파생상품 데이터가 있는 행 카운트
                            derivative_data = all_rows_for_rcept[derivative_cols]
                            mask = (derivative_data != '-').any(axis=1)
                            derivative_count = mask.sum()
                            year_data['파생상품 개수'].append(derivative_count)
                        else:
                            year_data['파생상품 개수'].append(0)
                    else:
                        year_data['파생상품 개수'].append('-')
                else:
                    year_data['Failed Step'].append('-')
                    year_data['파생상품 개수'].append('-')
            
            # DataFrame 생성 (연도를 컬럼으로, Failed Step과 파생상품 개수를 행으로)
            trend_df = pd.DataFrame({
                year: [year_data['Failed Step'][i], year_data['파생상품 개수'][i]] 
                for i, year in enumerate(years)
            }, index=['Failed Step', '파생상품 개수'])
            
            # 스타일링 함수 - 각 failed step별 다른 색상
            def style_trend_table(val):
                if val == '-':
                    return 'background-color: #f5f5f5; color: #999'
                # Failed Step 값에 따른 색상 (문자열로 비교)
                elif val == '0' or val == '0.0':
                    return 'background-color: #c8e6c9; color: #1b5e20; font-weight: bold'  # 녹색
                elif val == '1' or val == '1.0':
                    return 'background-color: #fff3e0; color: #e65100; font-weight: bold'  # 주황색
                elif val == '2' or val == '2.0':
                    return 'background-color: #ffebee; color: #b71c1c; font-weight: bold'  # 빨간색
                elif val == '3' or val == '3.0':
                    return 'background-color: #e1bee7; color: #4a148c; font-weight: bold'  # 보라색
                elif val == '4' or val == '4.0':
                    return 'background-color: #e0f2f1; color: #004d40; font-weight: bold'  # 청록색
                elif val == '5' or val == '5.0':
                    return 'background-color: #fce4ec; color: #880e4f; font-weight: bold'  # 분홍색
                elif val == '5.1':
                    return 'background-color: #f8bbd0; color: #ad1457; font-weight: bold'  # 진한 분홍색
                elif val == '5.2':
                    return 'background-color: #f48fb1; color: #c2185b; font-weight: bold'  # 더 진한 분홍색
                elif val == '6' or val == '6.0':
                    return 'background-color: #e3f2fd; color: #0d47a1; font-weight: bold'  # 파란색
                elif val == '6.1':
                    return 'background-color: #bbdefb; color: #1565c0; font-weight: bold'  # 진한 파란색
                elif val == '6.2':
                    return 'background-color: #90caf9; color: #1976d2; font-weight: bold'  # 더 진한 파란색
                elif val == '7' or val == '7.0':
                    return 'background-color: #f3e5f5; color: #311b92; font-weight: bold'  # 진한 보라색
                elif val == '7.1':
                    return 'background-color: #e1bee7; color: #4527a0; font-weight: bold'  # 중간 보라색
                elif val == '7.2':
                    return 'background-color: #ce93d8; color: #512da8; font-weight: bold'  # 진한 중간 보라색
                elif val == '8' or val == '8.0':
                    return 'background-color: #efebe9; color: #3e2723; font-weight: bold'  # 갈색
                elif val == '9' or val == '9.0':
                    return 'background-color: #eceff1; color: #263238; font-weight: bold'  # 회색
                elif val == '10' or val == '10.0':
                    return 'background-color: #fff9c4; color: #f57f17; font-weight: bold'  # 노란색
                elif str(val).replace('.', '').isdigit():
                    # 기타 숫자 값들 (10 초과 또는 소수점 있는 값들)
                    try:
                        num_val = float(val)
                        if num_val > 10:
                            return 'background-color: #ffcdd2; color: #d32f2f; font-weight: bold'  # 11 이상은 진한 빨간색
                        else:
                            # 기타 소수점 값들
                            return 'background-color: #ffe0b2; color: #ef6c00; font-weight: bold'
                    except:
                        pass
                # 파생상품 개수 (숫자인 경우)
                elif isinstance(val, (int, float)) and val >= 0:
                    if val == 0:
                        return 'background-color: #f5f5f5; color: #666'
                    elif val <= 5:
                        return 'background-color: #e8f5e9; color: #2e7d32'
                    elif val <= 10:
                        return 'background-color: #fff8e1; color: #f57c00'
                    else:
                        return 'background-color: #ffe0b2; color: #e65100; font-weight: bold'
                return ''
            
            # 테이블 표시
            styled_df = trend_df.style.applymap(style_trend_table)
            st.dataframe(styled_df, use_container_width=True, height=120)
            
            # 범례 표시
            with st.expander("📊 색상 범례 보기", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("""
                    **Failed Step 단계별 색상:**
                    - 🟢 Step 0: 파생상품 탐지 성공
                    - 🟠 Step 1: 주황색
                    - 🔴 Step 2: 빨간색
                    - 🟣 Step 3: 보라색
                    - 🟦 Step 4: 청록색
                    """)
                with col2:
                    st.markdown("""
                    **Failed Step 단계별 색상 (계속):**
                    - 🩷 Step 5, 5.1, 5.2: 분홍색 계열
                    - 🔵 Step 6, 6.1, 6.2: 파란색 계열
                    - 🟪 Step 7, 7.1, 7.2: 보라색 계열
                    - 🟫 Step 8: 갈색
                    - ⚫ Step 9+: 회색 계열
                    """)
                with col3:
                    st.markdown("""
                    **파생상품 개수:**
                    - ⚪ 0개: 회색
                    - 🟢 1-5개: 연녹색
                    - 🟡 6-10개: 연노란색
                    - 🟠 11개+: 진한 주황색
                    
                    **참고:** 소수점 단계(예: 5.1, 5.2)는 
                    같은 색상 계열의 다른 톤으로 표시
                    """)
   
    # 선택된 행 처리 - 상세 정보 표시
    if event.selection and len(event.selection['rows']) > 0:
        selected_idx = event.selection['rows'][0]
       
        if selected_idx < len(df_filtered):
            selected_row = df_filtered.iloc[selected_idx]  # 원본 데이터에서 가져오기
            selected_rcept = selected_row['RCEPT_NO_NEW']
           
            # 선택된 RCEPT_NO_NEW에 해당하는 모든 행 가져오기
            all_rows = df[df['RCEPT_NO_NEW'] == selected_rcept]
           
            # 스크롤 리셋을 위한 JavaScript 실행
            components.html(
                """
                <script>
                    // 모든 스크롤 가능한 요소를 찾아서 스크롤을 맨 위로
                    setTimeout(function() {
                        const scrollables = window.parent.document.querySelectorAll('.scrollable-text, .markdown-content');
                        scrollables.forEach(el => {
                            el.scrollTop = 0;
                        });
                    }, 100);
                </script>
                """,
                height=0,
            )
           
            st.markdown("---")
           
            # 섹션 2: 파생상품 상세 정보 (FAILED_STEP이 0인 경우)
            if selected_row['FAILED_STEP'] == 0:
                st.subheader("💹 파생상품 상세 정보")
               
                # 파생상품 관련 칼럼
                derivative_cols = [
                    'company_name', 'trade_purpose', 'derivative_category',
                    'currency_derivative_type', 'trade_type', 'buy_amount',
                    'sell_amount', 'buy_amount_unit', 'sell_amount_unit',
                    'buy_currency_unit', 'sell_currency_unit', 'other_unit', 'remarks'
                ]
               
                # 해당 칼럼들이 존재하는지 확인
                if all([col in all_rows.columns for col in derivative_cols]):
                    # 해당 칼럼들이 '-'가 아닌 행들만 필터링
                    derivative_data = all_rows[derivative_cols].copy()
                   
                    # '-'가 아닌 데이터가 있는 행만 필터링
                    mask = (derivative_data != '-').any(axis=1)
                    derivative_data_filtered = derivative_data[mask]
                   
                    if len(derivative_data_filtered) > 0:
                        # NaN 값을 '-'로 대체
                        derivative_data_filtered = derivative_data_filtered.fillna('-')
                       
                        # 칼럼명 한글화
                        column_mapping = {
                            'company_name': '회사명',
                            'trade_purpose': '거래목적',
                            'derivative_category': '파생상품분류',
                            'currency_derivative_type': '통화파생상품종류',
                            'trade_type': '거래유형',
                            'buy_amount': '매수금액',
                            'sell_amount': '매도금액',
                            'buy_amount_unit': '매수금액단위',
                            'sell_amount_unit': '매도금액단위',
                            'buy_currency_unit': '매수통화단위',
                            'sell_currency_unit': '매도통화단위',
                            'other_unit': '기타단위',
                            'remarks': '비고'
                        }
                       
                        derivative_data_filtered = derivative_data_filtered.rename(columns=column_mapping)
                       
                        # 매수금액, 매도금액에 천단위 콤마 추가
                        def format_amount(x):
                            if x == '-' or pd.isna(x) or str(x).strip() == '':
                                return x
                            try:
                                # 숫자 문자열을 float로 변환 후 천단위 콤마 추가
                                num_value = float(str(x).replace(',', ''))
                                # 정수인 경우 소수점 제거
                                if num_value.is_integer():
                                    return f"{int(num_value):,}"
                                else:
                                    return f"{num_value:,.2f}"
                            except:
                                return x
                       
                        if '매수금액' in derivative_data_filtered.columns:
                            derivative_data_filtered['매수금액'] = derivative_data_filtered['매수금액'].apply(format_amount)
                        if '매도금액' in derivative_data_filtered.columns:
                            derivative_data_filtered['매도금액'] = derivative_data_filtered['매도금액'].apply(format_amount)
                       
                        # 데이터프레임 표시
                        st.dataframe(
                            derivative_data_filtered,
                            use_container_width=True,
                            height=min(400, 50 + len(derivative_data_filtered) * 35)
                        )
                       
                        # 데이터 다운로드 버튼
                        csv = derivative_data_filtered.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 파생상품 데이터 다운로드 (CSV)",
                            data=csv,
                            file_name=f'derivative_data_{selected_rcept}.csv',
                            mime='text/csv'
                        )
                    else:
                        st.info("파생상품 상세 정보가 없습니다.")
                else:
                    st.info("파생상품 상세 칼럼이 데이터에 존재하지 않습니다.")
               
                st.markdown("---")
           
            # 섹션 3: 4분면 표시
            st.subheader("📑 섹션별 키워드 및 내용")
           
            col1, col2 = st.columns(2)
           
            with col1:
                st.markdown("**🔍 사업의내용 - 통화파생상품 키워드**")
                with st.expander("ℹ️ 설명 보기", expanded=False):
                    st.caption("""
                    ※ 목적: "사업의내용" 섹션에서 통화파생상품 관련 키워드 쌍의 근접 출현을 탐지
                   
                    ※ 탐지 기준:
                    - 단어집합1: 환, 외환, 외화, 통화, 달러, USD, EUR 등 통화 관련 키워드
                    - 단어집합2: 스왑, TRF, 선도, 선물, 옵션 등 파생상품 관련 키워드
                    - 근접도: 두 단어 집합의 키워드가 10자 이내에 함께 나타날 때 탐지
                    - 제외 패턴: "전환", "선도환율" 등 제외
                    """)
                if '파생섹션키워드' in all_rows.columns:
                    derivative_keywords = all_rows['파생섹션키워드'].iloc[0] if pd.notna(all_rows['파생섹션키워드'].iloc[0]) else '내용 없음'
                else:
                    derivative_keywords = '칼럼이 존재하지 않습니다'
                st.markdown(f'<div class="scrollable-text" id="deriv-keywords-{selected_rcept}">{derivative_keywords}</div>', unsafe_allow_html=True)
           
            with col2:
                st.markdown("**💰 재무에 관한 사항 - 통화파생상품 키워드**")
                with st.expander("ℹ️ 설명 보기", expanded=False):
                    st.caption("""
                    ※ 목적: "재무에 관한 사항" 섹션에서 통화파생상품 관련 키워드 쌍의 근접 출현을 탐지
                   
                    ※ 탐지 기준: 사업의 내용 키워드 추출방식과 동일
                    """)
                if '재무섹션키워드' in all_rows.columns:
                    financial_keywords = all_rows['재무섹션키워드'].iloc[0] if pd.notna(all_rows['재무섹션키워드'].iloc[0]) else '내용 없음'
                else:
                    financial_keywords = '칼럼이 존재하지 않습니다'
                st.markdown(f'<div class="scrollable-text" id="fin-keywords-{selected_rcept}">{financial_keywords}</div>', unsafe_allow_html=True)
           
            col3, col4 = st.columns(2)
           
            with col3:
                st.markdown("**📄 사업의내용 - 파생상품/위험관리 섹션**")
                with st.expander("ℹ️ 설명 보기", expanded=False):
                    st.caption("""
                    ※ 목적: 사업보고서의 "사업의내용" 섹션에서 파생상품 및 위험관리 관련 섹션을 추출
                   
                    ※ 추출 기준:
                    - 시작 키워드: "시장위험", "위험관리", "파생" (비파생 제외)을 포함하면서 30자 이내 줄바꿈이 존재
                    - 종료 조건: "주요계약", "경영계약", "연구개발" 등의 다음 섹션 제목이 나올 때까지
                    """)
                if '파생섹션파생내용' in all_rows.columns:
                    derivative_content = all_rows['파생섹션파생내용'].iloc[0] if pd.notna(all_rows['파생섹션파생내용'].iloc[0]) else '내용 없음'
                else:
                    derivative_content = '칼럼이 존재하지 않습니다'
                st.markdown(f'<div class="scrollable-text" id="deriv-content-{selected_rcept}">{derivative_content}</div>', unsafe_allow_html=True)
           
            with col4:
                st.markdown("**📈 재무에 관한 사항 - 파생상품/위험관리 섹션**")
                with st.expander("ℹ️ 설명 보기", expanded=False):
                    st.caption("""
                    ※ 목적: 사업보고서의 "재무에 관한 사항" 섹션에서 파생상품 및 위험관리 관련 하위 섹션을 추출
                   
                    ※ 추출 기준:
                    - 시작 키워드: 사업의 내용 섹션과 동일
                    - 종료 조건: 시작 위치부터 2000자까지만 추출
                    """)
                if '재무섹션파생내용' in all_rows.columns:
                    financial_content = all_rows['재무섹션파생내용'].iloc[0] if pd.notna(all_rows['재무섹션파생내용'].iloc[0]) else '내용 없음'
                else:
                    financial_content = '칼럼이 존재하지 않습니다'
                st.markdown(f'<div class="scrollable-text" id="fin-content-{selected_rcept}">{financial_content}</div>', unsafe_allow_html=True)
           
            st.markdown("---")
           
            # 섹션 4: Markdown Content
            st.subheader("📝 Markdown 내용")
            with st.expander("ℹ️ 설명 보기", expanded=False):
                st.caption("""
                ※ "사업의 내용 - 파생상품/위험관리 섹션"을 LLM으로 Markdown으로 변경요청한 내용
                """)
            if 'markdown_content' in all_rows.columns:
                markdown_content = all_rows['markdown_content'].iloc[0] if pd.notna(all_rows['markdown_content'].iloc[0]) else '내용 없음'
            else:
                markdown_content = '칼럼이 존재하지 않습니다'
           
            # Markdown을 HTML로 표시 - ID 추가로 스크롤 리셋
            st.markdown(f'<div class="markdown-content" id="markdown-{selected_rcept}">{markdown_content}</div>', unsafe_allow_html=True)
           
    else:
        st.info("👆 위 표에서 왼쪽 체크박스를 클릭하여 기업을 선택하면 상세 정보를 볼 수 있습니다.")
       
else:
    # 파일이 업로드되지 않은 경우
    st.info("📁 Excel 파일을 업로드하여 시작하세요.")
   
    # 사용 가이드
    with st.expander("사용 가이드"):
        st.markdown("""
        ### 📖 사용 방법
       
        1. **파일 업로드**: Excel 파일의 '5_전체통합데이터' 시트가 포함된 파일을 업로드하세요.
        2. **필터링**: 
           - FAILED_STEP: 실패 단계별로 필터링
           - 연도: REPORT_YY 기준으로 연도별 필터링
        3. **기업 선택**: 표의 왼쪽 체크박스를 클릭하여 원하는 기업을 선택하세요.
        4. **연도별 추세**: 선택된 기업의 2009-2024년 파생상품 현황을 확인할 수 있습니다.
        5. **정보 확인**:
           - 우측에서 선택된 기업 정보와 보고서 링크 확인
           - 연도별 failed_step과 파생상품 개수 추이 확인
           - FAILED_STEP이 0인 경우 파생상품 상세 정보 확인
           - 4개 섹션에서 추출된 키워드와 내용 확인
           - 각 섹션의 "ℹ️ 설명 보기"를 클릭하면 추출 기준 확인 가능
           - Markdown 형식의 상세 내용 확인
       
        ### 📊 데이터 구조
        - **RCEPT_NO_NEW**: 접수번호 (중복 제거됨)
        - **FAILED_STEP**: 실패 단계 (0: 성공, 그 외: 실패 단계)
        - **REPORT_YY**: 보고서 연도
        - **파생상품 정보**: FAILED_STEP이 0인 경우만 표시
       
        ### 📌 섹션 설명
        - **사업의내용 섹션**: 사업보고서의 "II. 사업의 내용" 부분에서 추출
        - **재무 섹션**: 사업보고서의 "III. 재무에 관한 사항" 부분에서 추출
        - **키워드**: 통화파생상품 관련 키워드 쌍의 근접 출현 탐지
        - **파생상품/위험관리**: 해당 섹션에서 추출한 전체 텍스트
        """)