import pandas as pd
import streamlit as st
from tqdm import tqdm
import requests
from datetime import datetime

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
# 데이터를 API로 받아오기
#-----------------------------------------------------------
#빈 데이터프레임
df_data = pd.DataFrame()
#에러리스트 생성
error_list = []
no_data_list = []

# 증권상품(8번 유형)이 아닌 것들을 loop 돌리기, tqdm 추가
for stock_code in tqdm(search_list_df_original[search_list_df_original['company_type_l1'] != '8']['symbol'], desc="Processing stocks"):

    # 검색어
    url = url_base + f'GetCompanyDividends({stock_code})'
    
    # 검색해오기
    response = make_request(url, headers)    
    
    try:
        response_data = response.json()
        if response_data['success'] == True:
            docs = response_data['data']['pods'][1]['content']['data']
            df = pd.DataFrame(docs)
        
            # 필요한 행만 추리기
            filter_list = ['회기', '당기순이익(천원)', '주당순이익(원)', '배당성향(%)', 
                           '보통주현금배당액', '보통주주식배당액(원)', 
                           '주당현금배당액(대주주,보통주)(원)', '주당현금배당액(소주주,보통주)(원)', 
                           '주당현금배당액(대주주,우선주)(원)', '주당현금배당액(소주주,우선주)(원)', 
                           '주당무상배당액(대주주,보통주)(원)', '주당무상배당액(소주주,보통주)(원)', 
                           '주당무상배당액(대주주,우선주)(원)', '주당무상배당액(소주주,우선주)(원)']
            
            df_2 = df[df['dividend_type_name'].isin(filter_list)]
        
            # pivot_table을 사용하여 데이터 변환
            pivot_df = df_2.pivot_table(
                index=['symbol', 'date',  'entity_name', 'accounting_type'],  # 나머지 칼럼들
                columns='dividend_type_name',  # unique 값을 칼럼으로 변환
                values='amount',  # amount를 값으로 사용
                aggfunc='sum'  # 중복된 값이 있을 때는 합산 (필요에 따라 다른 함수 사용 가능)
            ).reset_index()
            
            # date 칼럼에서 연도 추출
            pivot_df['year'] = pd.to_datetime(pivot_df['date']).dt.year
            
            # 각 연도의 행 개수에 따라 중간배당여부(mid_dividend) 값 설정
            pivot_df['mid_dividend'] = pivot_df['year'].map(pivot_df['year'].value_counts())
            pivot_df['mid_dividend'] = pivot_df['mid_dividend'].apply(lambda x: 'Y' if x > 1 else 'N')
            
            # 데이터 합치기
            df_data = pd.concat([df_data, pivot_df])
        else:
            no_data_list.append(stock_code)
    except:
        error_list.append(stock_code)
        pass
    
#오늘날짜 설정
today = (datetime.today()).strftime('%Y%m%d')

#업데이트일 추가
df_data['last_update'] = today

# df_data의 칼럼순서를 변경하는 코드
df_data = df_data[['symbol', 'date', 'entity_name', 'accounting_type', '당기순이익(천원)','주당순이익(원)',
       '배당성향(%)', '보통주현금배당액', '보통주주식배당액(원)', '주당현금배당액(대주주,우선주)(원)',
       '주당현금배당액(소주주,보통주)(원)', '주당현금배당액(대주주,보통주)(원)', '주당현금배당액(소주주,우선주)(원)',
       '주당무상배당액(대주주,보통주)(원)','주당무상배당액(소주주,보통주)(원)', 
       '주당무상배당액(대주주,우선주)(원)', '주당무상배당액(소주주,우선주)(원)',
        '회기', 'year','mid_dividend', 'last_update']]

# df_data의 칼럼명을 변경하는 코드
df_data.columns = [
    'symbol', 'date', 'entity_name', 'accounting_type', 'net_income', 'EPS',  
    'div_payout_ratio', 'div_amount_ord_share', 'stock_div_amount_ord_share', 'DPS_major_ord_share',
    'DPS_ord_ord_share', 'DPS_major_pref_share', 'DPS_ord_pref_share',
    'div_DPS_major_ord_share', 'div_DPS_ord_ord_share', 'div_DPS_major_pref_share', 'div_DPS_ord_pref_share',
    'accounting_period', 'year', 'mid_dividend', 'last_update'
]




# 데이터프레임의 NaN 값을 None으로 변환
df_data = df_data.astype(object).where(pd.notnull(df_data), None)


# # 에러에 대해서는 데이터가 없음을 확인
# df_ex = search_list_df_original[search_list_df_original['symbol'].isin(error_list)]

# stock_code_ex = 'KRX:377480'
# # 검색어
# url_ex = url_base + f'GetCompanyDividends({stock_code_ex})'

# # 검색해오기
# response_ex = make_request(url_ex, headers)    


# response_data_ex = response_ex.json()
# docs_ex = response_data_ex['data']['pods'][1]['content']['data']
# df_test = pd.DataFrame(docs_ex)
#-----------------------------------------------------------
#판다스를 SQL로 저장하기
#-----------------------------------------------------------
#접속정보
# Database configuration
db_config = {
    'user': 'data01',
    'password': 'epdlxj01',
    'host': 'krxdb1.mysql.database.azure.com',
    'port': 3306,
    'database': 'opendart',
}

# Initialize connection variable
connection = None

try:
    # Create a connection to the database
    connection = mysql.connector.connect(**db_config)

    if connection.is_connected():
        print("Connected to MySQL database")

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Drop the table if it exists
        drop_table_query = "DROP TABLE IF EXISTS ds_dividend"
        cursor.execute(drop_table_query)
        print("Table 'ds_dividend' dropped")
    
        # Define the SQL CREATE TABLE statement
        create_table_query = """
        CREATE TABLE ds_dividend (
            symbol VARCHAR(100) COMMENT '종목 심볼', 
            date VARCHAR(100) COMMENT '일자',
            entity_name VARCHAR(100) COMMENT '업체명', 
            accounting_type VARCHAR(2) COMMENT '1결산 2반기 4Q1 5Q3',
            net_income BIGINT COMMENT '당기순이익(천원)', 
            EPS FLOAT COMMENT '주당순이익(원)', 
            div_payout_ratio FLOAT COMMENT '배당성향(%)', 
            div_amount_ord_share FLOAT COMMENT '보통주현금배당액', 
            stock_div_amount_ord_share FLOAT COMMENT '보통주주식배당액(원)', 
            DPS_major_ord_share FLOAT COMMENT '주당현금배당액(대주주,보통주)(원)',
            DPS_ord_ord_share FLOAT COMMENT '주당현금배당액(소주주,보통주)(원)', 
            DPS_major_pref_share FLOAT COMMENT '주당현금배당액(대주주,우선주)(원)', 
            DPS_ord_pref_share FLOAT COMMENT '주당현금배당액(소주주,우선주)(원)', 
            div_DPS_major_ord_share FLOAT COMMENT '주당무상배당액(대주주,보통주)(원)', 
            div_DPS_ord_ord_share FLOAT COMMENT '주당무상배당액(소주주,보통주)(원)', 
            div_DPS_major_pref_share FLOAT COMMENT '주당무상배당액(대주주,우선주)(원)', 
            div_DPS_ord_pref_share FLOAT COMMENT '주당무상배당액(소주주,우선주)(원)',
            accounting_period INT COMMENT '회기', 
            year INT COMMENT '회계연도',
            mid_dividend VARCHAR(1) COMMENT '중간배당여부',
            last_update VARCHAR(8) COMMENT '업데이트된 날짜'
        )
        """

        # Create the table
        cursor.execute(create_table_query)
        print("Table 'ds_dividend' created successfully")

        # Insert the data from the DataFrame into the table using parameterized queries
        insert_query = """INSERT INTO ds_dividend (
        symbol, date, entity_name, accounting_type, net_income, EPS, 
        div_payout_ratio, div_amount_ord_share, stock_div_amount_ord_share, 
        DPS_major_ord_share, DPS_ord_ord_share, DPS_major_pref_share, DPS_ord_pref_share,
        div_DPS_major_ord_share, div_DPS_ord_ord_share, div_DPS_major_pref_share, div_DPS_ord_pref_share,
        accounting_period, year, mid_dividend, last_update
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,  
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # tqdm 적용하여 진행 상황 표시
        for _, row in tqdm(df_data.iterrows(), total=df_data.shape[0], desc="Inserting data"):
            cursor.execute(insert_query, (
                    row['symbol'], row['date'], row['entity_name'], row['accounting_type'],
                    row['net_income'], row['EPS'], row['div_payout_ratio'], row['div_amount_ord_share'],  # Fixed missing value
                    row['stock_div_amount_ord_share'], row['DPS_major_ord_share'], row['DPS_ord_ord_share'], 
                    row['DPS_major_pref_share'], row['DPS_ord_pref_share'], row['div_DPS_major_ord_share'], 
                    row['div_DPS_ord_ord_share'], row['div_DPS_major_pref_share'], row['div_DPS_ord_pref_share'], 
                    row['accounting_period'], row['year'], row['mid_dividend'], row['last_update']
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
            total_rows_query = "SELECT COUNT(*) FROM ds_dividend"
            total_cursor.execute(total_rows_query)
            total_rows = total_cursor.fetchone()[0]
            total_cursor.close()

            # 데이터 가져오기
            query = "SELECT * FROM ds_dividend"
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
df_data = load_data_from_db()



#-----------------------------------------------------------
# 데이터 사용
#-----------------------------------------------------------
# accounting_type =1 (연간배당)

df_data_annual = df_data[df_data['accounting_type'] == '1']

# 기업별로 그룹화하고 연도 순으로 정렬
df_data_annual = df_data_annual.sort_values(by=['symbol', 'year'])

#-----------------------------------------------------------
# 연속배당 순수증가
# 연속배당증가햇수 칼럼을 추가할 빈 리스트
streak_list = []

# 각 기업별로 그룹화하여 처리
for symbol, group in df_data_annual.groupby('symbol'):
    streak = 0  # 연속 증가 카운트
    prev_dps = None  # 이전 배당금 저장
    for idx, row in group.iterrows():
        current_dps = row['DPS_ord_ord_share']
        if prev_dps is not None and current_dps > prev_dps:
            streak += 1  # 증가한 경우 카운트 증가
        else:
            streak = 0  # 감소했거나 같은 경우 리셋
        streak_list.append(streak)
        prev_dps = current_dps  # 현재 배당금을 이전 값으로 저장

# 결과를 데이터프레임에 추가
df_data_annual['연속배당증가'] = streak_list


#-----------------------------------------------------------
# 연속배당 증가 또는 유지
# 연속배당증가햇수 칼럼을 추가할 빈 리스트
streak_list = []

# 각 기업별로 그룹화하여 처리
for symbol, group in df_data_annual.groupby('symbol'):
    streak = 0  # 연속 증가 카운트
    prev_dps = None  # 이전 배당금 저장
    for idx, row in group.iterrows():
        current_dps = row['DPS_ord_ord_share']
        if prev_dps is not None and current_dps >= prev_dps and current_dps !=0 :
            streak += 1  # 증가하거나 같은 경우 카운트 증가(대신 현재 dps가 0은 아니어야함)
        else:
            streak = 0  # 감소했거나 같은 경우 리셋
        streak_list.append(streak)
        prev_dps = current_dps  # 현재 배당금을 이전 값으로 저장

# 결과를 데이터프레임에 추가
df_data_annual['배당증가유지'] = streak_list

#-----------------------------------------------------------
# 최근연도 기준 데이터만 표출. 배당증가유지 순서
df_test = df_data_annual[df_data_annual['year'] == 2023].sort_values('배당증가유지', ascending = False)

# 특정 기업 기준 데이터만 표출. 연도 순서.
df_test = df_data_annual[df_data_annual['entity_name'] == 'NICE평가정보'].sort_values('year', ascending = False)
