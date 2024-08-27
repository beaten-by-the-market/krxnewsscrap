import pandas as pd
import streamlit as st

# 데이터 프레임 설정
doc_cat_dict = {
    '문서구분': ['국내뉴스', '증권사보고서', '공시 및 IR', '특허'],
    'category': ['["news"]', '["research"]', '["company"]', '["patent"]']
}
df_doc_cat = pd.DataFrame(doc_cat_dict)

domestic_news_dict = {
    '국내뉴스': ['전체', '경제', '기술/IT', '문화', '사설', '사회', '세계', '연예', '정치'],
    'news': ['[""]', '["economy"]', '["tech"]', '["culture"]', '["opinion"]', '["society"]', '["world"]', '["entertainment"]', '["politics"]']
}
df_domestic_news = pd.DataFrame(domestic_news_dict)

anal_report_dict = {
    '증권사보고서': ['경제 보고서', '기업 보고서', '산업 보고서', '시장 전망', '채권 보고서', '투자전략', '전체'],
    'research': ['["economy"]', '["company"]', '["industry"]', '["market"]', '["bond"]', '["strategy"]', 'None']
}
df_anal_report = pd.DataFrame(anal_report_dict)

disc_ir_dict = {
    '공시_IR': ['IR', '공시', '전체'],
    'company': ['["ir"]', '["disclosure"]', 'None']
}
df_disc_ir = pd.DataFrame(disc_ir_dict)

news_comp_dict = {
    '언론사': [
        '전체', '중앙일간지', '중앙경제지', 
        '중앙일간지 및 경제지', '석간지', '종합일간지, 지방지'
    ],
    'publisher': [
        "publisher :('경향신문' or '국민일보' or '동아일보' or '서울신문' or '세계일보' or '아시아투데이' or '조선일보' or '중앙일보' or '한겨레' or '한국일보' or '뉴스토마토' or '디지털타임스' or '매일경제' or '머니투데이' or '서울경제' or '아주경제' or '이데일리' or '이투데이' or '전자신문' or '파이낸셜뉴스' or '한국경제' or '내일신문' or '문화일보' or '아시아경제' or '지역내일신문' or '헤럴드경제' or '중소기업뉴스' or '메트로경제' or '국제신문' or '부산일보')",
        "publisher :('경향신문' or '국민일보' or '동아일보' or '서울신문' or '세계일보' or '아시아투데이' or '조선일보' or '중앙일보' or '한겨레' or '한국일보')",
        "publisher :('뉴스토마토' or '디지털타임스' or '매일경제' or '머니투데이' or '서울경제' or '아주경제' or '이데일리' or '이투데이' or '전자신문' or '파이낸셜뉴스' or '한국경제')",
        "publisher :('경향신문' or '국민일보' or '동아일보' or '서울신문' or '세계일보' or '아시아투데이' or '조선일보' or '중앙일보' or '한겨레' or '한국일보' or '뉴스토마토' or '디지털타임스' or '매일경제' or '머니투데이' or '서울경제' or '아주경제' or '이데일리' or '이투데이' or '전자신문' or '파이낸셜뉴스' or '한국경제')",
        "publisher :('내일신문' or '문화일보' or '아시아경제' or '지역내일신문' or '헤럴드경제')",
        "publisher :('메트로경제' or '국제신문' or '부산일보')"
    ]
}
df_news_comp = pd.DataFrame(news_comp_dict)

listed_comp_dict = {
    '상장사': ['유가', '코스닥', '코넥스'],
    'listedcompany': ["securities.market:('KOSPI')", "securities.market:('KOSDAQ')", "securities.market:('KONEX')"]
}
df_listed_comp = pd.DataFrame(listed_comp_dict)

keyword_dict = {
    '키워드구분': ['키워드단독', '키워드조합'],
    'keyword': [
        '(공시 or 수주 or 계약 or 인수 or 합병 or 분할 or 영업양도 or 영업양수 or 엠앤에이 or 출자 or 투자 or 매출 or 실적 or 이익 or 배당 or 증자 or 감자 or 주식교환 or 주식이전 or 우회상장 or 상장폐지 or 관리종목 or 자본잠식 or 비적정 or 의견거절 or 회계처리 or 분식 or 소송 or 횡령 or 배임 or 부도 or 파산 or 회생 or 공소 or 기소 or 혐의)',
        '((수주 and 체결) or (수주 and 공급) or (계약 and 체결) or (계약 and 공급) or 인수 or 합병 or 분할 or 영업양도 or 영업양수 or 엠앤에이 or 출자 or 투자 or (매출 and 발표) or (매출 and 공표) or (매출 and 결정) or (매출 and 기록) or (매출 and 달성) or (매출 and 공시) or (실적 and 발표) or (실적 and 공표) or (실적 and 결정) or (실적 and 기록) or (실적 and 달성) or (실적 and 공시) or (이익 and 발표) or (이익 and 공표) or (이익 and 결정) or (이익 and 기록) or (이익 and 달성) or (이익 and 공시) or (배당 and 발표) or (배당 and 공표) or (배당 and 결정) or (배당 and 기록) or (배당 and 달성) or (배당 and 공시) or 증자 or 감자 or 주식교환 or 주식이전 or 우회상장 or 상장폐지 or 관리종목 or 자본잠식 or (비적정 and 감사) or (비적정 and 회계법인) or (의견거절 and 감사) or (의견거절 and 회계법인) or (회계처리 and 위반) or 분식 or 소송 or 횡령 or 배임 or 부도 or 파산 or 회생 or (공소 and 대표이사) or (공소 and 임원) or (공소 and 이사) or (기소 and 대표이사) or (기소 and 임원) or (기소 and 이사) or (혐의 and 대표이사) or (혐의 and 임원) or (혐의 and 이사))'
    ]
}
df_keyword = pd.DataFrame(keyword_dict)

# Streamlit UI 구성
st.title('DeepSearch 쿼리 생성기')

# 문서 구분 선택
doc_cat_selection = st.selectbox('문서구분', df_doc_cat['문서구분'])
doc_cat_query = df_doc_cat[df_doc_cat['문서구분'] == doc_cat_selection]['category'].values[0]

# 뉴스 선택시 상세구분
if doc_cat_selection == '국내뉴스':
    domestic_news_selection = st.selectbox('국내뉴스 구분', df_domestic_news['국내뉴스'])
    domestic_news_query = df_domestic_news[df_domestic_news['국내뉴스'] == domestic_news_selection]['news'].values[0]
    
    # 언론사 선택
    news_comp_selection = st.selectbox('언론사 구분', df_news_comp['언론사'])
    
    # '언론사 구분'을 변경했을 때 상태 초기화
    if 'last_news_comp_selection' not in st.session_state or st.session_state.last_news_comp_selection != news_comp_selection:
        publishers = df_news_comp[df_news_comp['언론사'] == news_comp_selection]['publisher'].values[0]
        publisher_list = publishers.replace("publisher :(", "").replace(")", "").replace("'", "").split(" or ")
        st.session_state.publisher_options = publisher_list
        st.session_state.selected_publishers = publisher_list
        st.session_state.last_news_comp_selection = news_comp_selection
    
    # 새로운 언론사 추가
    additional_publisher = st.text_input("추가할 언론사를 입력하세요")
    if additional_publisher:
        if additional_publisher not in st.session_state.publisher_options:
            st.session_state.publisher_options.append(additional_publisher)
        if additional_publisher not in st.session_state.selected_publishers:
            st.session_state.selected_publishers.append(additional_publisher)
    
    # 사용자 추가를 반영한 multiselect (한 번만 호출)
    selected_publishers = st.multiselect('언론사를 선택하세요', options=st.session_state.publisher_options, default=st.session_state.selected_publishers)

    if selected_publishers:
        news_comp_query = " or ".join([f"'{publisher}'" for publisher in selected_publishers])
        news_comp_query = f"publisher :({news_comp_query})"
    else:
        news_comp_query = ''
else:
    domestic_news_query = ''
    news_comp_query = ''


# 증권사 보고서 선택
if doc_cat_selection == '증권사보고서':
    anal_report_selection = st.selectbox('증권사보고서 구분', df_anal_report['증권사보고서'])
    anal_report_query = df_anal_report[df_anal_report['증권사보고서'] == anal_report_selection]['research'].values[0]
else:
    anal_report_query = ''

# 공시_IR 선택
if doc_cat_selection == '공시 및 IR':
    disc_ir_selection = st.selectbox('공시_IR 구분', df_disc_ir['공시_IR'])
    disc_ir_query = df_disc_ir[df_disc_ir['공시_IR'] == disc_ir_selection]['company'].values[0]
else:
    disc_ir_query = ''

# 상장사 선택
listed_comp_selection = st.selectbox('상장사 구분', df_listed_comp['상장사'])
listed_comp_query = df_listed_comp[df_listed_comp['상장사'] == listed_comp_selection]['listedcompany'].values[0]

# 키워드 선택
keyword_selection = st.selectbox('키워드 구분', df_keyword['키워드구분'])
keyword_query = df_keyword[df_keyword['키워드구분'] == keyword_selection]['keyword'].values[0]

# 날짜 및 시간 칼럼 생성
col1, col2 = st.columns(2)

# 선택한 날짜 기준 및 날짜 및 시간 기준을 저장할 변수
use_date = False
use_datetime = False

# 날짜 기준 칼럼
with col1:
    if st.checkbox('날짜 기준 사용', key='use_date_checkbox'):
        use_date = True

# 날짜 및 시간 기준 칼럼
with col2:
    if not use_date and st.checkbox('날짜 및 시간 기준 사용', key='use_datetime_checkbox'):
        use_datetime = True

# 날짜 기준이 선택된 경우의 처리
if use_date:
    start_date = st.date_input('시작일', key='start_date')
    end_date = st.date_input('종료일', key='end_date')
    if start_date and end_date:
        date_query = f'date_from={start_date.strftime("%Y%m%d")} , date_to={end_date.strftime("%Y%m%d")}'
    else:
        date_query = ''
else:
    date_query = ''

# 날짜 및 시간 기준이 선택된 경우의 처리
if use_datetime:
    datetime_start_date = st.date_input('시작 날짜', key='datetime_start_date')
    datetime_start_time = st.slider('시작 시간', 0, 24, 0, key='datetime_start_time')
    datetime_end_date = st.date_input('종료 날짜', key='datetime_end_date')
    datetime_end_time = st.slider('종료 시간', 0, 24, 0, key='datetime_end_time')
    if datetime_start_date and datetime_end_date:
        datetime_start = f"{datetime_start_date}T{datetime_start_time:02}:00:00"
        datetime_end = f"{datetime_end_date}T{datetime_end_time:02}:00:00"
        datetime_query = f'created_at:[\\"{datetime_start}\\" to \\"{datetime_end}\\"]'
    else:
        datetime_query = ''
else:
    datetime_query = ''

# 쿼리 생성 버튼
if st.button('쿼리생성'):
    # 기본 쿼리 리스트 초기화
    query_parts = [doc_cat_query]
    
    # 'AND' 조건으로 추가될 쿼리 부분 초기화
    query_parts_and = []
    
    # 콤마 조건으로 추가될 쿼리 부분 초기화
    query_parts_comma = []

    # 국내뉴스 선택 시에만 신문 영역 및 언론사 쿼리 추가
    if doc_cat_selection == '국내뉴스':
        if domestic_news_query:  # 빈 값이 아닌 경우에만 추가
            query_parts.append(domestic_news_query)
        if news_comp_query:  # 빈 값이 아닌 경우에만 추가
            query_parts_and.append(news_comp_query)
    
    # 증권사 보고서 쿼리 추가
    if doc_cat_selection == '증권사보고서':
        if anal_report_query:  # 빈 값이 아닌 경우에만 추가
            query_parts.append(anal_report_query)
    
    # 공시_IR 쿼리 추가
    if doc_cat_selection == '공시 및 IR':
        if disc_ir_query:  # 빈 값이 아닌 경우에만 추가
            query_parts.append(disc_ir_query)
    
    # 상장사 쿼리 추가
    if listed_comp_query:  # 빈 값이 아닌 경우에만 추가
        query_parts_and.append(listed_comp_query)
    
    # 키워드 쿼리 추가
    if keyword_query:  # 빈 값이 아닌 경우에만 추가
        query_parts_and.append(keyword_query)

    # 날짜 및 시간 쿼리 추가
    if date_query:  # 빈 값이 아닌 경우에만 추가
        query_parts_comma.append(date_query)
    
    if datetime_query:  # 빈 값이 아닌 경우에만 추가
        query_parts_and.append(datetime_query)

    # 'None' 문자열이 포함되지 않도록 필터링
    query_parts = [part for part in query_parts if part and part != 'None']
    query_parts_and = [part for part in query_parts_and if part and part != 'None']
    query_parts_comma = [part for part in query_parts_comma if part and part != 'None']

    # 최종 쿼리 생성 
    intro = 'DocumentSearch('
    outro = ', count = 100, page = 1)'
    final_query_category = ' , '.join(query_parts)
    final_query_condition = ' and '.join(query_parts_and)
    final_query_comma = ' , '.join(query_parts_comma)
    final_query_all = intro +\
        final_query_category +\
            (' , "' + final_query_condition + '"' if final_query_condition else '') +\
                ((' , ' if final_query_comma else '') + final_query_comma) +\
                    outro

    # 백슬래시 포함된 쿼리 출력
    st.write('생성된 쿼리(복사하여 krx.deepsearch.com 에 붙여넣으세요):')
    st.code(final_query_all)
