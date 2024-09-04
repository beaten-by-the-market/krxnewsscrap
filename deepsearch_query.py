import pandas as pd
import streamlit as st

import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
import time
import mysql.connector

# InsecureRequestWarning 비활성화
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 인증키 설정
headers = {
    'Authorization': 'Basic ZWU4MjcyYmI1ODAwNGE3Nzk1YmJjNjgwM2YyOTRjZDY6NjgwNGY3YTg1ZjAyYmM1ZjQ4OWMxMWVmMWIzMmFkZjQ5NWYyYzMzMTRkMTE2ZmVlMzVmMzcyY2Q3YmQwYjJlMQ=='
}

# API 검색 URL
url_base = 'https://api.deepsearch.com/v1/compute?input='

#-----------------------------------------------------------
# 함수정의
#-----------------------------------------------------------
# API 돌릴 때 page가 여러개인 경우 page별로 URL 만드는 함수
def generate_url(page):
    query = final_query_all.replace('page = 1', f'page = {page}')
    return f'{url_base}{query}'.replace('\n', '')

# API로 문서 검색하는 함수
def make_request(url, headers, max_retries=5):
    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            attempt += 1
            print(f"Request failed: {e}. Attempt {attempt} of {max_retries}. Retrying in 5 seconds...")
            time.sleep(5)
    raise Exception("Max retries exceeded")
    
#-----------------------------------------------------------
# Streamlit UI 구성
#-----------------------------------------------------------
st.set_page_config(layout="wide")
st.title('KRX 상장사 문서검색기 :sunglasses:')
st.markdown("*by :blue[Data Leaders]*:blossom:")



#-----------------------------------------------------------
# 데이터베이스에서 데이터 받아오기
#-----------------------------------------------------------
# 접속정보
db_config = {
    'user': 'krx01',
    'password': 'rjfoth01',
    'host': 'krxdb1.mysql.database.azure.com',
    'port': 3306,
    'database': 'opendart',
}

# 데이터를 캐싱하여 재사용
@st.cache_data
def load_data_from_db():
    connection = None
    try:
        # 데이터베이스 연결
        connection = mysql.connector.connect(**db_config)

        if connection.is_connected():
            print("Connected to MySQL database")

            # 커서 생성
            cursor = connection.cursor()

            # 총 행 수 가져오기
            total_cursor = connection.cursor()
            total_rows_query = "SELECT COUNT(*) FROM ds_entitysummary"
            total_cursor.execute(total_rows_query)
            total_rows = total_cursor.fetchone()[0]
            total_cursor.close()

            # 데이터 가져오기
            query = "SELECT * FROM ds_entitysummary"
            cursor.execute(query)

            # 데이터프레임 초기화
            disc = pd.DataFrame(columns=[desc[0] for desc in cursor.description])

            # Streamlit의 프로그레스 바 설정
            progress_bar = st.progress(0)
            batch_size = 1000  # 한 번에 가져올 행의 수
            rows_fetched = 0

            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                disc = pd.concat([disc, pd.DataFrame(rows, columns=disc.columns)], ignore_index=True)

                # 프로그레스 바 업데이트
                rows_fetched += len(rows)
                progress_bar.progress(min(rows_fetched / total_rows, 1.0))

            return disc

    except mysql.connector.Error as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()  # 빈 데이터프레임 반환

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

# SQL 데이터를 최초 1회만 로드
search_list_df_original = load_data_from_db()

#-----------------------------------------------------------
# 선택지 설정
#-----------------------------------------------------------
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
    '증권사보고서': ['전체', '경제 보고서', '기업 보고서', '산업 보고서', '시장 전망', '채권 보고서', '투자전략'],
    'research': ['None', '["economy"]', '["company"]', '["industry"]', '["market"]', '["bond"]', '["strategy"]']
}
df_anal_report = pd.DataFrame(anal_report_dict)

disc_ir_dict = {
    '공시_IR': ['전체', 'IR', '공시', ],
    'company': ['None', '["ir"]', '["disclosure"]']
}
df_disc_ir = pd.DataFrame(disc_ir_dict)

news_comp_dict = {
    '언론사': [
        '전체', '중앙일간지', '중앙경제지', 
        '중앙일간지 및 경제지', '석간지', '종합일간지, 지방지'
    ],
    'publisher': [
        "publisher.raw :('경향신문' or '국민일보' or '동아일보' or '서울신문' or '세계일보' or '아시아투데이' or '조선일보' or '중앙일보' or '한겨레' or '한국일보' or '뉴스토마토' or '디지털타임스' or '매일경제' or '머니투데이' or '서울경제' or '아주경제' or '이데일리' or '이투데이' or '전자신문' or '파이낸셜뉴스' or '한국경제' or '내일신문' or '문화일보' or '아시아경제' or '지역내일신문' or '헤럴드경제' or '중소기업뉴스' or '메트로경제' or '국제신문' or '부산일보')",
        "publisher.raw :('경향신문' or '국민일보' or '동아일보' or '서울신문' or '세계일보' or '아시아투데이' or '조선일보' or '중앙일보' or '한겨레' or '한국일보')",
        "publisher.raw :('뉴스토마토' or '디지털타임스' or '매일경제' or '머니투데이' or '서울경제' or '아주경제' or '이데일리' or '이투데이' or '전자신문' or '파이낸셜뉴스' or '한국경제')",
        "publisher.raw :('경향신문' or '국민일보' or '동아일보' or '서울신문' or '세계일보' or '아시아투데이' or '조선일보' or '중앙일보' or '한겨레' or '한국일보' or '뉴스토마토' or '디지털타임스' or '매일경제' or '머니투데이' or '서울경제' or '아주경제' or '이데일리' or '이투데이' or '전자신문' or '파이낸셜뉴스' or '한국경제')",
        "publisher.raw :('내일신문' or '문화일보' or '아시아경제' or '지역내일신문' or '헤럴드경제')",
        "publisher.raw :('메트로경제' or '국제신문' or '부산일보')"
    ]
}
df_news_comp = pd.DataFrame(news_comp_dict)

listed_comp_dict = {
    '상장사': ['유가/코스닥/코넥스','유가', '코스닥', '코넥스'],
    'listedcompany': ["ALL","KOSPI", "KOSDAQ", "KONEX"]
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



#-----------------------------------------------------------
# 사이드바 설정
#-----------------------------------------------------------

# Sidebar로 UI 이동
st.sidebar.title('검색 조건')

# 문서 구분 선택
doc_cat_selection = st.sidebar.selectbox('문서구분', df_doc_cat['문서구분'])
doc_cat_query = df_doc_cat[df_doc_cat['문서구분'] == doc_cat_selection]['category'].values[0]


# 뉴스 선택시 상세구분
if doc_cat_selection == '국내뉴스':
    # 언론사 선택
    st.sidebar.subheader('언론사를 선택하세요')

    domestic_news_selection = st.sidebar.selectbox('뉴스 섹션', df_domestic_news['국내뉴스'])
    domestic_news_query = df_domestic_news[df_domestic_news['국내뉴스'] == domestic_news_selection]['news'].values[0]

    # 언론사 선택
    news_comp_selection = st.sidebar.selectbox('언론사 구분', df_news_comp['언론사'])
    all_publishers = df_news_comp[df_news_comp['언론사'] == '전체']['publisher'].values[0]
    all_publisher_list = all_publishers.replace("publisher.raw :(", "").replace(")", "").replace("'", "").split(" or ")

    # '언론사 구분'을 변경했을 때 상태 초기화
    if 'last_news_comp_selection' not in st.session_state or st.session_state.last_news_comp_selection != news_comp_selection:
        
        publishers = df_news_comp[df_news_comp['언론사'] == news_comp_selection]['publisher'].values[0]
        publisher_list = publishers.replace("publisher.raw :(", "").replace(")", "").replace("'", "").split(" or ")
        st.session_state.publisher_options = all_publisher_list
        st.session_state.selected_publishers = publisher_list
        st.session_state.last_news_comp_selection = news_comp_selection

    # 새로운 언론사 추가
    additional_publisher = st.sidebar.text_input("추가할 언론사를 입력하세요")
    if additional_publisher:
        if additional_publisher not in st.session_state.selected_publishers:
            st.session_state.selected_publishers.append(additional_publisher)

    # 사용자 추가를 반영한 multiselect (한 번만 검색)
    selected_publishers = st.sidebar.multiselect('', options=st.session_state.publisher_options, 
                                                 default=st.session_state.selected_publishers,
                                                 label_visibility='collapsed')

    # 선택한 언론사 업데이트
    st.session_state.selected_publishers = selected_publishers

    if selected_publishers:
        news_comp_query = " or ".join([f"'{publisher}'" for publisher in selected_publishers])
        news_comp_query = f"publisher.raw :({news_comp_query})"
    else:
        news_comp_query = ''
else:
    domestic_news_query = ''
    news_comp_query = ''

# 증권사 보고서 선택
if doc_cat_selection == '증권사보고서':
    anal_report_selection = st.sidebar.selectbox('증권사보고서 구분', df_anal_report['증권사보고서'])
    anal_report_query = df_anal_report[df_anal_report['증권사보고서'] == anal_report_selection]['research'].values[0]
else:
    anal_report_query = ''

# 공시_IR 선택
if doc_cat_selection == '공시 및 IR':
    disc_ir_selection = st.sidebar.selectbox('공시_IR 구분', df_disc_ir['공시_IR'])
    disc_ir_query = df_disc_ir[df_disc_ir['공시_IR'] == disc_ir_selection]['company'].values[0]
else:
    disc_ir_query = ''

# 키워드 선택
st.sidebar.subheader('검색할 키워드를 확인하세요')
keyword_selection = st.sidebar.selectbox('키워드 구분', df_keyword['키워드구분'])

# 키워드 선택시 상세구분
single_keywords = df_keyword[df_keyword['키워드구분'] == '키워드단독']['keyword'].values[0]
single_keyword_list = single_keywords.replace("(", "").replace(")", "").replace("'", "").split(" or ")

multi_keywords = df_keyword[df_keyword['키워드구분'] == '키워드조합']['keyword'].values[0]
multi_keyword_list = multi_keywords.replace("((", "(").replace("))", ")").replace("'", "").split(" or ")

all_keyword_list = single_keyword_list + multi_keyword_list

# '키워드 구분'을 변경했을 때 상태 초기화
if 'last_keyword_selection' not in st.session_state or st.session_state.last_keyword_selection != keyword_selection:
    keywords = df_keyword[df_keyword['키워드구분'] == keyword_selection]['keyword'].values[0]
    if keyword_selection == '키워드단독':
        keyword_list = single_keyword_list
    else:
        keyword_list = multi_keyword_list

    st.session_state.keyword_options = all_keyword_list
    st.session_state.selected_keywords = keyword_list
    st.session_state.last_keyword_selection = keyword_selection

# 새로운 키워드 추가
additional_keyword = st.sidebar.text_input("추가할 키워드를 입력하세요")
st.sidebar.write('단어조합 검색 예시: (사기 and 부정거래)')
if additional_keyword:
    if additional_keyword not in st.session_state.keyword_options:
        st.session_state.keyword_options.append(additional_keyword)
    if additional_keyword not in st.session_state.selected_keywords:
        st.session_state.selected_keywords.append(additional_keyword)

# 사용자 추가를 반영한 multiselect (한 번만 검색)
selected_keywords = st.sidebar.multiselect('', options=st.session_state.keyword_options, 
                                           default=st.session_state.selected_keywords,
                                           label_visibility='collapsed')

# 선택한 키워드 업데이트
st.session_state.selected_keywords = selected_keywords

if selected_keywords:
    keyword_query = " or ".join([f"'{keyword}'" for keyword in selected_keywords])
    keyword_query = f"({keyword_query})"
else:
    keyword_query = ''

# 날짜 및 시간 칼럼 생성
st.sidebar.subheader("날짜 및 시간 설정")
col1, col2 = st.sidebar.columns(2)

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
    start_date = st.sidebar.date_input('시작일', key='start_date')
    end_date = st.sidebar.date_input('종료일', key='end_date')
    if start_date and end_date:
        date_query = f'date_from={start_date.strftime("%Y%m%d")} , date_to={end_date.strftime("%Y%m%d")}'
    else:
        date_query = ''
else:
    date_query = ''

# 날짜 및 시간 기준이 선택된 경우의 처리
if use_datetime:
    datetime_start_date = st.sidebar.date_input('시작 날짜', key='datetime_start_date')
    datetime_start_time = st.sidebar.slider('시작 시간', 0, 24, 0, key='datetime_start_time')
    datetime_end_date = st.sidebar.date_input('종료 날짜', key='datetime_end_date')
    datetime_end_time = st.sidebar.slider('종료 시간', 0, 24, 0, key='datetime_end_time')
    if datetime_start_date and datetime_end_date:
        datetime_start = f"{datetime_start_date}T{datetime_start_time:02}:00:00"
        datetime_end = f"{datetime_end_date}T{datetime_end_time:02}:00:00"
        datetime_query = f'created_at:[\\"{datetime_start}\\" to \\"{datetime_end}\\"]'
    else:
        datetime_query = ''
else:
    datetime_query = ''


#-----------------------------------------------------------
# 사이드바에서 검색버튼
#-----------------------------------------------------------
# 쿼리 생성 버튼을 항상 사이드바에 표시
if st.sidebar.button('검색'):
    if not use_date and not use_datetime:
        st.sidebar.error("기간은 반드시 선택해야 합니다. 짧을 수록 빨리 검색됩니다.")
    else:
        query_parts = [doc_cat_query]
        query_parts_and = []
        query_parts_comma = []
    
        if doc_cat_selection == '국내뉴스':
            if domestic_news_query:
                query_parts.append(domestic_news_query)
            if news_comp_query:
                query_parts_and.append(news_comp_query)
    
        if doc_cat_selection == '증권사보고서':
            if anal_report_query:
                query_parts.append(anal_report_query)
    
        if doc_cat_selection == '공시 및 IR':
            if disc_ir_query:
                query_parts.append(disc_ir_query)
    
        if keyword_query:
            query_parts_and.append(keyword_query)
    
        if date_query:
            query_parts_comma.append(date_query)
    
        if datetime_query:
            query_parts_and.append(datetime_query)
    
        query_parts = [part for part in query_parts if part and part != 'None']
        query_parts_and = [part for part in query_parts_and if part and part != 'None']
        query_parts_comma = [part for part in query_parts_comma if part and part != 'None']
    
        intro = 'DocumentSearch('
        outro = ', count = 100, page = 1)'
        final_query_category = ' , '.join(query_parts)
        final_query_condition = ' and '.join(query_parts_and)
        final_query_comma = ' , '.join(query_parts_comma)
        final_query_all = intro + final_query_category + (' , "' + final_query_condition + '"' if final_query_condition else '') + ((' , ' if final_query_comma else '') + final_query_comma) + outro

        # 현재 페이지 설정
        current_page = 1
    
        #사전에 생성한 함수로 URL생성
        url = generate_url(current_page)
        
        # 검색해오기
        response = make_request(url, headers)
        response_data = response.json()
        docs = response_data['data']['pods'][1]['content']['data']['docs']
        df_list = [pd.json_normalize(docs)]
        
        # 검색해온 API에서 총 페이지 수 획득
        last_page = response_data['data']['pods'][1]['content']['data']['last_page']
        
        progress_bar = st.progress(0)
        
        # 총 페이지 동안 loop돌면서 검색해오기
        while current_page < last_page:
            current_page += 1
            url = generate_url(current_page)
            response = make_request(url, headers)
            response_data = response.json()
    
            docs = response_data['data']['pods'][1]['content']['data']['docs']
            df_list.append(pd.json_normalize(docs))
    
            progress = int(current_page / last_page * 100)
            progress_bar.progress(progress)
    
        df = pd.concat(df_list, ignore_index=True)
        # 표출할 데이터프레임에서 중복칼럼 제거
        df_show = df.loc[:, ~df.columns.duplicated()]

        # 표출할 데이터프레임에서 필요한 칼럼만 남기기
        df_show = df[['section', 'publisher', 'author', 'title', 'content', 'content_url']]
        
        st.write("작성한 쿼리", final_query_all)
        st.write("검색한 문서목록")
        
        # Streamlit에서 Styled DataFrame을 interactive하게 표시
        st.dataframe(df_show, use_container_width=True)

        
        # 데이터프레임을 세션 상태에 저장
        st.session_state.df = df


#-----------------------------------------------------------
# 메인화면 설정
#-----------------------------------------------------------
# '필터' 버튼이 눌렸을 때 세션 상태에 있는 df를 사용
if 'df' in st.session_state:
    df = st.session_state.df

# Streamlit Session State를 사용하여 선택한 값을 유지
if 'selected_listed_comp' not in st.session_state:
    st.session_state.selected_listed_comp = df_listed_comp['상장사'][0]  # 초기 값을 첫 번째 옵션으로 설정

# 데이터 검색 시 사용되는 데이터프레임
if 'search_list_df' not in st.session_state:
    st.session_state.search_list_df = search_list_df_original


#-----------------------------------------------------------
# 필터 수행
#-----------------------------------------------------------
# '필터' 버튼을 눌러서 필터기능 수행
if 'df' in st.session_state:
    # 상장사 선택 UI
    selected_listed_comp = st.selectbox('검색결과에서 필터할 조건을 선택하고 "필터" 버튼을 누르세요',
        df_listed_comp['상장사'],
        index=df_listed_comp['상장사'].tolist().index(st.session_state.selected_listed_comp)
    )

    # 선택된 값이 변경될 때마다 상태 업데이트
    if selected_listed_comp != st.session_state.selected_listed_comp:
        # 선택항목 업데이트
        st.session_state.selected_listed_comp = selected_listed_comp
        # 선택항목에 따른 검색대상 상장사 업데이트
        if selected_listed_comp == '유가/코스닥/코넥스':
            st.session_state.search_list_df = search_list_df_original
        else:
            sel = df_listed_comp[df_listed_comp['상장사'] == st.session_state.selected_listed_comp]['listedcompany'].iloc[0]
            st.session_state.search_list_df = search_list_df_original[search_list_df_original['mkt'] == sel]


    df = st.session_state.df

    # '필터' 버튼 클릭 시 필터링 수행
    if st.button('필터'):
        search_list_df  = st.session_state.search_list_df

        if search_list_df.empty:
            st.write("선택한 조건에 맞는 데이터가 없습니다.")
        else:            
            # filter_df 함수를 그대로 사용
            # 검색된 내역에서 securities, entities, named_entities 칼럼에서 상장사에 해당하는게 있으면 검색하여 리스트 생성
            def filter_df(row):
                # identified_list를 관리하기 위한 빈 리스트는 각 행에서 새롭게 리셋
                identified_list = []
                matched = False
                
                # securities, entities, named_entities 칼럼을 순회하며 매칭 여부 확인
                for col in ['securities', 'entities', 'named_entities']:
                    # 각 entry를 search_list_df의 각 열과 비교
                    for entry in row[col]:
                        identified = None
                        if 'symbol' in entry: 
                            if entry['symbol'] in search_list_df['symbol'].values:
                                matched = True
                                identified = search_list_df[search_list_df['symbol'] == entry['symbol']]['entity_name'].iloc[0]
                        elif 'symbol' in entry:
                            if entry['symbol'] in search_list_df['symbol_nice'].values:
                                matched = True
                                identified = search_list_df[search_list_df['symbol_nice'] == entry['symbol']]['entity_name'].iloc[0]
                        elif 'name' in entry:
                            if entry['name'] in search_list_df['entity_name'].values:
                                matched = True
                                identified = entry['name']
                        elif 'business_rid' in entry:
                            if entry['business_rid'].replace('-','') in search_list_df['business_rid'].values:
                                matched = True
                                identified = search_list_df[search_list_df['business_rid'] == entry['business_rid'].replace('-','')]['entity_name'].iloc[0]
                        elif 'company_rid' in entry:
                            if entry['company_rid'].replace('-','') in search_list_df['company_rid'].values:
                                matched = True
                                identified = search_list_df[search_list_df['company_rid'] == entry['company_rid'].replace('-','')]['entity_name'].iloc[0]
            
                        if identified:
                            identified_list.append(identified)
            
                # 중복된 값을 제거하고 None 값 제거
                identified_list = list(set(filter(None, identified_list)))
                # 매칭된 값들을 반환
                return pd.Series([matched, identified_list])
            filtered_df = df.apply(filter_df, axis=1)
            filtered_df.columns = ['matched', 'identified_symbols']
            filtered_df2 = df[filtered_df['matched']].copy()
            filtered_df2['identified_symbols'] = filtered_df['identified_symbols']
            filtered_df3 = filtered_df2[['section', 'publisher', 'title', 'content','identified_symbols','content_url']]

            # 
            st.dataframe(filtered_df3, use_container_width=True)


else:
    st.write("먼저 '검색' 버튼을 눌러 데이터를 불러오세요.")
    
    
    

# #아나콘다 프롬프트에서 실행하는 코드
# #cd C:\Users\170027\Documents\krxnewsscrap
# #streamlit run deepsearch_query.py
