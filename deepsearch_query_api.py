import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import pandas as pd
import time
from tqdm import tqdm
import mysql.connector
from datetime import datetime
import numpy as np


# InsecureRequestWarning 비활성화
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#-----------------------------------------------------------
# 환경변수 설정
#-----------------------------------------------------------
# 인증키 설정
import os
from dotenv import load_dotenv
# .env 파일 로드
load_dotenv()

# 환경 변수에서 API 키 불러오기
api_key = os.getenv("API_KEY")


#접속정보-CRUD
# Database configuration
db_config_crud = {
    'user': os.getenv("DB_USER_CRUD"),
    'password': os.getenv("DB_PASSWORD_CRUD"),
    'host': os.getenv("DB_HOST"),
    'port': os.getenv("DB_PORT"),
    'database': os.getenv("DB_NAME"),
}

#접속정보-일반
# Database configuration
db_config = {
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'host': os.getenv("DB_HOST"),
    'port': os.getenv("DB_PORT"),
    'database': os.getenv("DB_NAME"),
}

# 인증 헤더에 API 키 적용
headers = {
    'Authorization': f'Basic {api_key}'
}

# API 호출 URL
url_base = 'https://api.deepsearch.com/v1/compute?input='


#-----------------------------------------------------------
# 딥서치로 상장사 목록 불러오기
#-----------------------------------------------------------

# 상장시장구분코드 (1=코스피, 2=코스닥, 3=코넥스, 4=제3시장, 9=대상아님)
# 빈데이터프레임
listed_df = pd.DataFrame()

for mkt in range(1, 4):
    query = f"""
    FindEntity("Financial","{mkt}" ,fields=["market_id"])
    """
    url = f'{url_base}{query}'.replace('\n','')

    # SSL 인증서 검증 비활성화하고 GET 요청 보내기
    response = requests.get(url, headers=headers, verify=False)
    
    # 응답 출력
    print(response.status_code)
    
    # 응답 데이터를 JSON으로 변환하여 저장
    response_data = response.json()
    
    # 'data' 추출
    data_dict = response_data['data']['pods'][1]['content']['data']
    loop_df = pd.DataFrame(data_dict)
    mkt_name = np.where(mkt == 1, 'KOSPI', 
                        np.where(mkt == 2, 'KOSDAQ',
                                 np.where(mkt ==3, 'KONEX',
                                          '기타시장')))
    loop_df['mkt'] = mkt_name
    listed_df = pd.concat([listed_df, loop_df])
    

# 기업별 개황 받아오는 과정(NICE코드와 사업자등록번호용)
#빈데이터프레임
summary_df = pd.DataFrame()

# KeyError 발생한 symbol을 저장할 리스트
key_error_symbols = []

# symbol 리스트에 대해 tqdm 적용
for symbol in tqdm(list(listed_df['symbol']), desc="Fetching data"):
    
    query = f"""
    GetEntitySummary({symbol})
    """
    
    url = f'{url_base}{query}'.replace('\n','')
    
    max_retries = 5  # 최대 재시도 횟수
    retries = 0
    
    while retries < max_retries:
        try:
            # SSL 인증서 검증 비활성화하고 GET 요청 보내기
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 발생
            break  # 성공하면 while 루프 탈출
            
        except requests.exceptions.RequestException as e:
            retries += 1
            if retries >= max_retries:
                print(f"Failed to retrieve data for {symbol} after {max_retries} attempts. Error: {e}")
                break  # 최대 재시도 횟수에 도달하면 루프 탈출
            else:
                print(f"Attempt {retries} failed for {symbol}. Retrying in 5 seconds...")
                time.sleep(5)  # 5초 대기

    if retries < max_retries:
        # 응답 데이터를 JSON으로 변환하여 저장
        response_data = response.json()
        
        # 'data'와 'pods' 존재 여부 확인
        if 'data' in response_data and 'pods' in response_data['data'] and len(response_data['data']['pods']) > 1:
            # 'data' 추출
            try:
                data_dict = response_data['data']['pods'][1]['content']['data']
                loop_df = pd.DataFrame(data_dict)
                summary_df = pd.concat([summary_df, loop_df])
            except KeyError as e:
                print(f"KeyError for {symbol}: {e}")
                key_error_symbols.append(symbol)  # KeyError 발생 시 symbol 저장
        else:
            print(f"No valid data for {symbol}")

# 소속시장 정보 합쳐주기
summary_df2 = pd.merge(summary_df, listed_df[['symbol','mkt']],
                              how = 'left',
                              on = 'symbol')

#오늘날짜 설정
today = (datetime.today()).strftime('%Y%m%d')

#업데이트일 추가
summary_df2['last_update'] = today

summary_df = summary_df2

#-----------------------------------------------------------
#판다스를 SQL로 저장하기
#-----------------------------------------------------------


# Initialize connection variable
connection = None

# 집어넣기
try:
    # Create a connection to the database
    connection = mysql.connector.connect(**db_config_crud)

    if connection.is_connected():
        print("Connected to MySQL database")

        # Create a cursor object to interact with the database
        cursor = connection.cursor()
        
        # Drop the table if it exists
        drop_table_query = "DROP TABLE IF EXISTS ds_entitysummary"
        cursor.execute(drop_table_query)
        print("Table 'ds_entitysummary' dropped")
    
        # Define the SQL CREATE TABLE statement
        create_table_query = """
        CREATE TABLE ds_entitysummary (
            symbol VARCHAR(100) COMMENT '종목 심볼', 
            entity_name VARCHAR(100) COMMENT '업체명', 
            symbol_nice VARCHAR(100) COMMENT 'NICE심볼', 
            ceo VARCHAR(100) COMMENT '대표이사', 
            business_rid VARCHAR(100) COMMENT '사업자번호', 
            company_rid VARCHAR(100) COMMENT '법인등록번호', 
            tel VARCHAR(100) COMMENT '전화번호', 
            fax VARCHAR(100) COMMENT '팩스번호', 
            website VARCHAR(100) COMMENT '홈페이지', 
            email VARCHAR(100) COMMENT '대표이메일', 
            zipcode VARCHAR(100) COMMENT '우편번호', 
            address_land_lot VARCHAR(200) COMMENT '주소1', 
            address_road_name VARCHAR(200) COMMENT '주소2', 
            company_type_l1 VARCHAR(100) COMMENT '기업형태 ( 1: 일반법인 2: 공공기관, 3: 비영리법인, 8:기타법인, 9:개인, 이외:기타 )', 
            company_type_l2 VARCHAR(100) COMMENT '기업상세코드(하단의 기업 상세 코드 정보 참조)', 
            company_type_size VARCHAR(100) COMMENT '기업규모(1=대기업, 2=중소기업, 3=중견기업, 0=기타)', 
            market_id VARCHAR(100) COMMENT '상장시장구분코드 (1=코스피, 2=코스닥, 3=코넥스, 4=제3시장, 9=대상아님)', 
            is_external_audit VARCHAR(100) COMMENT '외부감사여부', 
            conglomerate_id VARCHAR(100) COMMENT '그룹ID', 
            industry_id VARCHAR(100) COMMENT '산업분류 (10차 통계청 산업분류 기)', 
            industry_name VARCHAR(100) COMMENT '산업명', 
            fs_type VARCHAR(100) COMMENT '재무제표구분 (00=제조, AA=은행, BB=증권, CC=생보, DD=손보, EE=신용금고, FF=종금, GG=투신, HH=리스, II=카드, JJ=창투, KK=할부금융, ZZ=기타)', fiscal_year_end VARCHAR(100) COMMENT '결산', 
            business_area VARCHAR(200) COMMENT '사업영역', date_founded VARCHAR(100) COMMENT '창업일', 
            date_listed VARCHAR(100) COMMENT '상장일', 
            is_alive VARCHAR(100) COMMENT '기업존속여부 (True/False)', 
            is_closed VARCHAR(100) COMMENT '기업폐쇄여부', 
            status VARCHAR(100) COMMENT '상태', 
            mkt VARCHAR(10) COMMENT '시장',
            last_update VARCHAR(8) COMMENT '업데이트된 날짜'
        )
        """

        # Create the table
        cursor.execute(create_table_query)
        print("Table 'ds_entitysummary' created successfully")

        # Insert the data from the DataFrame into the table using parameterized queries
        insert_query = """INSERT INTO ds_entitysummary (
        symbol, entity_name, symbol_nice, ceo, business_rid, company_rid, tel, 
        fax, website, email, zipcode, address_land_lot, address_road_name, 
        company_type_l1, company_type_l2, company_type_size, market_id, 
        is_external_audit, conglomerate_id, industry_id, industry_name, fs_type, 
        fiscal_year_end, business_area, date_founded, date_listed, is_alive, 
        is_closed, status, mkt, last_update
        ) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # tqdm 적용하여 진행 상황 표시
        for _, row in tqdm(summary_df.iterrows(), total=summary_df.shape[0], desc="Inserting data"):
            cursor.execute(insert_query, (
                    row['symbol'],row['entity_name'],row['symbol_nice'],
                    row['ceo'],row['business_rid'],row['company_rid'],row['tel'],
                    row['fax'],row['website'],row['email'],row['zipcode'],
                    row['address_land_lot'],row['address_road_name'],
                    row['company_type_l1'],row['company_type_l2'],
                    row['company_type_size'],row['market_id'],
                    row['is_external_audit'],row['conglomerate_id'],
                    row['industry_id'],row['industry_name'],row['fs_type'],
                    row['fiscal_year_end'],row['business_area'],
                    row['date_founded'],row['date_listed'],row['is_alive'],
                    row['is_closed'],row['status'],row['mkt'],row['last_update']
            ))

        # Commit the changes
        connection.commit()
        print("Data inserted successfully")

except mysql.connector.Error as e:
    print(f"Error: {e}")

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")
        
#-----------------------------------------------------------
#데이터 받아오기
#-----------------------------------------------------------

# Initialize connection variable
connection = None

try:
    # Create a connection to the database
    connection = mysql.connector.connect(**db_config)

    if connection.is_connected():
        print("Connected to MySQL database")

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Total rows query with a separate cursor
        total_cursor = connection.cursor()
        total_rows_query = "SELECT COUNT(*) FROM ds_entitysummary"
        total_cursor.execute(total_rows_query)
        total_rows = total_cursor.fetchone()[0]
        total_cursor.close()

        # Execute your SQL query here
        query = "SELECT * FROM ds_entitysummary"
        cursor.execute(query)

        # Initialize an empty DataFrame
        disc = pd.DataFrame(columns=[desc[0] for desc in cursor.description])

        # Fetch the rows in chunks and update the progress bar
        batch_size = 1000  # Number of rows to fetch at a time

        with tqdm(total=total_rows, desc="Fetching data") as pbar:
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                # Append the fetched rows to the DataFrame
                disc = pd.concat([disc, pd.DataFrame(rows, columns=disc.columns)], ignore_index=True)
                pbar.update(len(rows))

except mysql.connector.Error as e:
    print(f"Error: {e}")

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")


#-----------------------------------------------------------
#뉴스데이터 받아오기
#-----------------------------------------------------------

#기업개황데이터 이름 변경
search_list_df = summary_df


#뉴스 페이지 카운트
current_page = 1

# 쿼리 생성 함수
def generate_url(page):
    query = f"""
    DocumentSearch(["news"],[""],"'매출' and publisher.raw:('한국경제' or '매일경제') and created_at:['2024-08-13T13:00:00' to '2024-09-03T16:00:00']", count=100, page={page})
    """
    return f'{url_base}{query}'.replace('\n','')

# 요청 함수 (재시도 로직 포함)
def make_request(url, headers, max_retries=5):
    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()  # HTTPError 발생 시 예외 처리
            return response
        except requests.exceptions.RequestException as e:
            attempt += 1
            print(f"Request failed: {e}. Attempt {attempt} of {max_retries}. Retrying in 5 seconds...")
            time.sleep(5)
    raise Exception("Max retries exceeded")

# 초기 요청
url = generate_url(current_page)
response = make_request(url, headers, max_retries)
print(response.status_code)

# 응답 데이터를 JSON으로 변환하여 저장
response_data = response.json()

# 'docs' 배열 추출 및 DataFrame 변환
docs = response_data['data']['pods'][1]['content']['data']['docs']
df_list = [pd.json_normalize(docs)]

# 마지막 페이지 추출
last_page = response_data['data']['pods'][1]['content']['data']['last_page']

# 루프를 통해 모든 페이지의 데이터 수집
while current_page < last_page:
    current_page += 1
    url = generate_url(current_page)
    response = make_request(url, headers, max_retries)
    print(response.status_code)
    
    # 응답 데이터를 JSON으로 변환하여 저장
    response_data = response.json()
    
    # 'docs' 배열 추출 및 DataFrame으로 변환 후 리스트에 추가
    docs = response_data['data']['pods'][1]['content']['data']['docs']
    df_list.append(pd.json_normalize(docs))

# 모든 DataFrame을 하나로 병합
df = pd.concat(df_list, ignore_index=True)



#-----------------------------------------------------------
#검색대상 기업이 언급된 뉴스만 필터하기
#-----------------------------------------------------------



# identified_list를 관리하기 위한 빈 리스트는 각 행에서 새롭게 리셋
def filter_df(row):
    identified_list = []
    matched = False
    
    # securities, entities, named_entities 칼럼을 순회하며 매칭 여부 확인
    for col in ['securities', 'entities', 'named_entities']:
        for entry in row[col]:
            identified = None
            # 각 entry를 search_list_df의 각 열과 비교
            if 'symbol' in entry: 
                if entry['symbol'] in search_list_df['symbol'].values:
                    matched = True
                    identified = search_list_df[search_list_df['symbol'] == entry['symbol']]['entity_name'].iloc[0]
            elif 'symbol' in entry :
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

# df의 각 행에 대해 filter_df 함수를 적용하여 매칭된 여부와 identified_symbols 값을 동시에 얻습니다.
filtered_df = df.apply(filter_df, axis=1)
filtered_df.columns = ['matched', 'identified_symbols']

# matched가 True인 행만 필터링합니다.
filtered_df2 = df[filtered_df['matched']].copy()

# identified_symbols 열을 추가합니다.
filtered_df2['identified_symbols'] = filtered_df['identified_symbols']


# 필요한 열만 남기기
filtered_df3 = filtered_df2[['section', 'publisher', 'author', 'title',
                             'content','identified_symbols','content_url']]


