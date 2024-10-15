import streamlit as st
import datetime
import pandas as pd
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
import time

# InsecureRequestWarning 비활성화
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#-----------------------------------------------------------
# 환경변수 설정-로컬
#-----------------------------------------------------------
# # 인증키 설정
# import os
# from dotenv import load_dotenv
# # .env 파일 로드
# load_dotenv()

# # 환경 변수에서 API 키 불러오기
# api_key = os.getenv("API_KEY")

# # DB 연결 정보도 환경 변수에서 불러오기
# db_config = {
#     'user': os.getenv("DB_USER"),
#     'password': os.getenv("DB_PASSWORD"),
#     'host': os.getenv("DB_HOST"),
#     'port': os.getenv("DB_PORT"),
#     'database': os.getenv("DB_NAME"),
# }


#-----------------------------------------------------------
# 환경변수 설정-streamlit
#-----------------------------------------------------------
# Streamlit Secrets에서 API 키 불러오기
# 기본 API 키와 DB 정보를 불러오는 부분
api_key = st.secrets["general"]["api_key"]

db_config = {
    'user': st.secrets["general"]["db_user"],
    'password': st.secrets["general"]["db_password"],
    'host': st.secrets["general"]["db_host"],
    'port': st.secrets["general"]["db_port"],
    'database': st.secrets["general"]["db_name"],
}

# CRUD 작업에 사용하는 DB 정보를 불러오는 부분
db_config_crud = {
    'user': st.secrets["crud"]["db_user"],
    'password': st.secrets["crud"]["db_password"],
    'host': st.secrets["crud"]["db_host"],
    'port': st.secrets["crud"]["db_port"],
}

#-----------------------------------------------------------
# 헤더 및 URL
#-----------------------------------------------------------
# 인증 헤더에 API 키 적용
headers = {
    'Authorization': f'Basic {api_key}'
}

# API 검색 URL
url_base = 'https://api.deepsearch.com/v1/compute?input='

#-----------------------------------------------------------
# 함수정의
#-----------------------------------------------------------
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
# Streamlit 페이지 구성
#-----------------------------------------------------------

# 페이지 설정 - wide 레이아웃 사용
st.set_page_config(page_title="기업발굴 필터링 서비스", layout="wide")

# 제목 설정
st.title("🚀 KRX 기업발굴 필터링 from DeepSearch 데이터")
st.write("큰 예산과 인력을 들여 기업 재무정보 데이터를 취급하는 국내 데이터사업자는 두 곳입니다.(NICE평가정보, 상장사협의회/FnGuide)")
st.write("KRX는 상장사 재무데이터를 갖고 있지 않기 때문에, 이중 NICE평가정보의 데이터를 활용하여 상장기업 발굴 서비스를 구현하였습니다.")
st.write("Deepsearch Enterprise 웹서비스의 부분 Replica이며, 데이터 호출은 DeepSearch API를 활용합니다.")

# 필터 입력 레이아웃 설정
with st.form(key='filter_form'):
    
    # 거래소 섹션
    market_filter = st.selectbox("🌐 시장 선택", ["코스피", "코스닥", "코스피 및 코스닥"], key='market')
    
    # 시장 섹션
    st.header("📈 시장데이터")
    
    # 시장 섹션 내 날짜 선택 추가
    selected_date = st.date_input("📅 기준 날짜 선택", value=datetime.date.today(), key='selected_date')
    selected_date_str = selected_date.strftime('%Y-%m-%d')

    col1, col2, col3= st.columns([1, 1, 1])
    
    with col1:
        st.subheader("거래대금")
        거래대금_min = st.text_input('이상', placeholder="금액 (억 원)", key='거래대금_min')
        거래대금_max = st.text_input('이하', placeholder="금액 (억 원)", key='거래대금_max')

        st.subheader("시가총액")
        시가총액_min = st.text_input('이상', placeholder="금액 (억 원)", key='시가총액_min')
        시가총액_max = st.text_input('이하', placeholder="금액 (억 원)", key='시가총액_max')

    
    with col2:
        st.subheader("PER")
        PER_min = st.text_input('이상', placeholder="배수 (X)", key='PER_min')
        PER_max = st.text_input('이하', placeholder="배수 (X)", key='PER_max')
        
        st.subheader("PBR")
        PBR_min = st.text_input('이상', placeholder="배수 (X)", key='PBR_min')
        PBR_max = st.text_input('이하', placeholder="배수 (X)", key='PBR_max')

    with col3:
        st.subheader("시가배당률")
        divyield_min = st.text_input('이상', placeholder="수치(%)", key='divyield_min')
        divyield_max = st.text_input('이하', placeholder="수치(%)", key='divyield_max')
        
    
    # 재무 섹션
    st.header("🧾 재무데이터")
    col4, col5 = st.columns([1, 1])

    with col4:    
        # 연결/개별 선택 옵션
        financial_option = st.selectbox("📑 재무기준 선택(연결/개별)", ["연결", "개별"], key='financial_option')

    with col5:
        # 연도 선택 콤보박스 추가 (2018 ~ 2023, 기본값 2023)
        selected_year = st.selectbox("📆 사업연도 선택", options=[2023, 2022, 2021, 2020, 2019, 2018], index=0, key='selected_year')


    col6, col7, col8 = st.columns([1, 1, 1])

    with col6:
        st.subheader('매출')
        매출_min = st.text_input('이상', placeholder="금액 (억 원)", key='매출_min')
        매출_max = st.text_input('이하', placeholder="금액 (억 원)", key='매출_max')
        
        st.subheader('영업이익')
        영업이익_min = st.text_input('이상', placeholder="금액 (억 원)", key='영업이익_min')
        영업이익_max = st.text_input('이하', placeholder="금액 (억 원)", key='영업이익_max')
        
        st.subheader('당기순이익')
        당기순이익_min = st.text_input('이상', placeholder="금액 (억 원)", key='당기순이익_min')
        당기순이익_max = st.text_input('이하', placeholder="금액 (억 원)", key='당기순이익_max')

    with col7:        
        st.subheader('영업이익률')
        영업이익률_min = st.text_input('이상', placeholder="수치(%)", key='영업이익률_min')
        영업이익률_max = st.text_input('이하', placeholder="수치(%)", key='영업이익률_max')
        
        st.subheader('당기순이익률')
        당기순이익률_min = st.text_input('이상', placeholder="수치(%)", key='당기순이익률_min')
        당기순이익률_max = st.text_input('이하', placeholder="수치(%)", key='당기순이익률_max')
        
    with col8:                
        st.subheader('자산')
        자산_min = st.text_input('이상', placeholder="금액 (억 원)", key='자산_min')
        자산_max = st.text_input('이하', placeholder="금액 (억 원)", key='자산_max')
        
        st.subheader('부채비율(부채/자본)')
        부채비율_min = st.text_input('이상', placeholder="수치(%)", key='부채비율_min')
        부채비율_max = st.text_input('이하', placeholder="수치(%)", key='부채비율_max')

    # 키워드 섹션
    st.header("🏢 검색 키워드")
    
    col9, col10 = st.columns([1, 1])

    with col9:
        st.subheader('산업 키워드')
        산업_키워드 = st.text_input('통계청 산업분류에서 찾으려는 키워드가 존재하는 기업들을 검색합니다. 통계청 산업분류의 경우 삼성전자와 같이 휴대폰, 반도체 등 여러 사업을 하고 있는 회사를 설명하기 어려울 수 있기 때문에 결과가 만족스럽지 않을 때는 "사업 키워드" 검색 조건을 이용해 주세요.', placeholder="키워드", key='산업_키워드')
        
    with col10:
        st.subheader('사업 키워드')
        사업_키워드 = st.text_input('정기보고서의 사업현황 정보에 찾으려는 키워드가 존재하는 기업들을 검색합니다. 예를 들어 반도체를 제조하는 회사가 아니더라도, 반도체가 부품으로 포함되어 있어서 반도체 수급 등에 영향을 받는다는 내용이 사업현황에 기재되어 있다면, 이를 검색해줍니다.', placeholder="키워드", key='사업_키워드')

    
    
    # 검색 버튼 추가
    submitted = st.form_submit_button("🔍 검색")

# 쿼리 생성
if submitted:
    query = []

    # 거래소 쿼리 생성
    if market_filter != "코스피 및 코스닥":
        query.append(f"('{market_filter}' 상장 기업)")
    elif market_filter == "코스피 및 코스닥":
        query.append("(('코스피' 상장 기업) or ('코스닥' 상장 기업))")

    # 시장 쿼리 생성
    if 거래대금_min and 거래대금_max:
        query.append(f"({거래대금_min}00000000 <= {selected_date_str} 거래대금 <= {거래대금_max}00000000)")
    elif 거래대금_min:
        query.append(f"({selected_date_str} 거래대금 >= {거래대금_min}00000000)")
    elif 거래대금_max:
        query.append(f"({selected_date_str} 거래대금 <= {거래대금_max}00000000)")

    if 시가총액_min and 시가총액_max:
        query.append(f"({시가총액_min}00000000 <= {selected_date_str} 시가총액 <= {시가총액_max}00000000)")
    elif 시가총액_min:
        query.append(f"({selected_date_str} 시가총액 >= {시가총액_min}00000000)")
    elif 시가총액_max:
        query.append(f"({selected_date_str} 시가총액 <= {시가총액_max}00000000)")

    if PER_min and PER_max : 
        query.append(f"({PER_min} <= {selected_date_str} PER <= {PER_max})")        
    elif PER_min:
        query.append(f"({selected_date_str} PER >= {PER_min})")
    elif PER_max:
        query.append(f"({selected_date_str} PER <= {PER_max})")

    if PBR_min and PBR_max:
        query.append(f"({PBR_min} <= {selected_date_str} PBR <= {PBR_max})")        
    elif PBR_min:
        query.append(f"({selected_date_str} PBR >= {PBR_min})")
    elif PBR_max:
        query.append(f"({selected_date_str} PBR <= {PBR_max})")
        
    if divyield_min and divyield_max :
        divyield_min = str(float(divyield_min)/100)
        divyield_max = str(float(divyield_max)/100)
        query.append(f"({divyield_min} <= {selected_date_str} DPS/주가 <= {divyield_max})")
    elif divyield_min:
        divyield_min = str(float(divyield_min)/100)
        query.append(f"({selected_date_str} DPS/주가 >= {divyield_min})")
    elif divyield_max:
        divyield_max = str(float(divyield_max)/100)
        query.append(f"({selected_date_str} DPS/주가 <= {divyield_max})")

    # 재무 쿼리 생성 (연결/개별 옵션 추가)
    if 매출_min and 매출_max:
        query.append(f"({매출_min}00000000 <= {selected_year} {financial_option} 매출 <= {매출_max}00000000)")
    elif 매출_min:
        query.append(f"({selected_year} {financial_option} 매출 >= {매출_min}00000000)")
    elif 매출_max:
        query.append(f"({selected_year} {financial_option} 매출 <= {매출_max}00000000)")

    if 영업이익_min and 영업이익_max:
        query.append(f"({영업이익_min}00000000 <= {selected_year} {financial_option} 영업이익 <= {영업이익_max}00000000)")
    elif 영업이익_min:
        query.append(f"({selected_year} {financial_option} 영업이익 >= {영업이익_min}00000000)")
    elif 영업이익_max:
        query.append(f"({selected_year} {financial_option} 영업이익 <= {영업이익_max}00000000)")

    if 당기순이익_min and 당기순이익_max:
        query.append(f"({당기순이익_min}00000000 <= {selected_year} {financial_option} 당기순이익 <= {당기순이익_max}00000000)")
    elif 당기순이익_min:
        query.append(f"({selected_year} {financial_option} 당기순이익 >= {당기순이익_min}00000000)")
    elif 당기순이익_max:
        query.append(f"({selected_year} {financial_option} 당기순이익 <= {당기순이익_max}00000000)")
        
    if 자산_min and 자산_max:
        query.append(f"({자산_min}00000000 <= {selected_year} {financial_option} 자산 <= {자산_max}00000000)")
    elif 자산_min:
        query.append(f"({selected_year} {financial_option} 자산 >= {자산_min}00000000)")
    elif 자산_max:
        query.append(f"({selected_year} {financial_option} 자산 <= {자산_max}00000000)")

    if 영업이익률_min and 영업이익률_max :
        영업이익률_min = str(float(영업이익률_min)/100)
        영업이익률_max = str(float(영업이익률_max)/100)
        query.append(f"({영업이익률_min} <= {selected_year} {financial_option} 영업이익률 <= {영업이익률_max})")
    elif 영업이익률_min:
        영업이익률_min = str(float(영업이익률_min)/100)
        query.append(f"({selected_year} {financial_option} 영업이익률 >= {영업이익률_min})")
    elif 영업이익률_max:
        영업이익률_max = str(float(영업이익률_max)/100)
        query.append(f"({selected_year} {financial_option} 영업이익률 <= {영업이익률_max})")

    if 당기순이익률_min and 당기순이익률_max:
        당기순이익률_min = str(float(당기순이익률_min)/100)
        당기순이익률_max = str(float(당기순이익률_max)/100)
        query.append(f"({당기순이익률_min} <= {selected_year} {financial_option} 당기순이익률 <= {당기순이익률_max})")
    elif 당기순이익률_min:
        당기순이익률_min = str(float(당기순이익률_min)/100)
        query.append(f"({selected_year} {financial_option} 당기순이익률 >= {당기순이익률_min})")
    elif 당기순이익률_max:
        당기순이익률_max = str(float(당기순이익률_max)/100)
        query.append(f"({selected_year} {financial_option} 당기순이익률 <= {당기순이익률_max})")
        
    if 부채비율_min and 부채비율_max:
        부채비율_min = str(float(부채비율_min)/100)
        부채비율_max = str(float(부채비율_max)/100)
        query.append(f"({부채비율_min} <= {selected_year} {financial_option} 부채비율 <= {부채비율_max})")
    elif 부채비율_min:
        부채비율_min = str(float(부채비율_min)/100)
        query.append(f"({selected_year} {financial_option} 부채비율 >= {부채비율_min})")
    elif 부채비율_max:
        부채비율_max = str(float(부채비율_max)/100)
        query.append(f"({selected_year} {financial_option} 부채비율 <= {부채비율_max})")
        
    #키워드 반영    
    if 산업_키워드 :
        query.append(f"('{산업_키워드}' 산업 기업)")

    if 사업_키워드 : 
        query.append(f"(SearchCompanyBusinessSummary('{사업_키워드}'))")

        

    # 최종 쿼리 출력
    final_query = " and ".join(query)
    
    st.write(f"DeepSearch 쿼리 : {final_query}")
    
    # 검색 URL 생성
    url = url_base + final_query

    # Spinner 추가: 데이터 검색 시 로딩 메시지 출력
    with st.spinner('데이터를 불러오는 중입니다...'):
        # 검색해오기
        response = make_request(url, headers)
        response_data = response.json()
        if response_data['success'] == True:
            docs = response_data['data']['pods'][1]['content']['data']
            df = pd.DataFrame(docs)

        # 검색된 데이터가 있는지 확인
        if not df.empty:
            # 검색 결과 출력
            st.write('조회된 상장사 수 : ' + str(len(df)) + '사')
            st.dataframe(df.reset_index(drop=True), use_container_width=False)
        else:
            st.write("데이터가 없습니다.")
