import pandas as pd
import streamlit as st
import mysql.connector
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
# 페이지구성
#-----------------------------------------------------------

# 페이지 레이아웃을 넓게 설정
st.set_page_config(page_title='한국의 배당계급', layout="wide")

# # Streamlit 앱 시작
# st.title('국내상장사별 배당계급은?')
# 상단 여백을 없애는 CSS 스타일을 적용
st.markdown(
    """
    <style>
        .main {
            padding-top: 0px !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# 이모지를 추가하는 방식으로 수정
st.markdown(
    """
    <h5 style="color: #1f4e79;">아셨나요? 미국상장사에는 배당계급이 존재합니다</h5>
    """,
    unsafe_allow_html=True
)


# 각 항목을 이모지와 함께 굵은 파란 글씨로 표시
st.markdown(
    """
    <p style="font-size: 15px; font-weight: bold; color: #1f4e79;">
        👑 배당 왕 (Dividend Kings): 
        <span style="font-size: 12px; font-weight: normal; color: black;">50년 이상 연속 배당 증가 (대표 기업: P&G, 로우스, 존슨앤드존슨)</span>
    </p>
    <p style="font-size: 15px; font-weight: bold; color: #1f4e79;">
        🎖 배당 귀족 (Dividend Aristocrats): 
        <span style="font-size: 12px; font-weight: normal; color: black;">25년 이상 연속 배당 증가기업이면서 S&P500 편입기업 (대표 기업: 코카콜라, P&G, 3M)</span>
    </p>
    <p style="font-size: 15px; font-weight: bold; color: #1f4e79;">
        🏆 배당 챔피언 (Dividend Champions): 
        <span style="font-size: 12px; font-weight: normal; color: black;">25년 이상 연속 배당 증가 (대표 기업: 애보트 래버러토리, 페덱스, 코카콜라)</span>
    </p>
    <p style="font-size: 15px; font-weight: bold; color: #1f4e79;">
        🏅 배당 도전자 (Dividend Contenders): 
        <span style="font-size: 12px; font-weight: normal; color: black;">10~24년 연속 배당 증가 (대표 기업: 텍사스 인스트루먼트, 애플, 마이크로소프트)</span>
    </p>
    <p style="font-size: 15px; font-weight: bold; color: #1f4e79;">
        🚀 배당 신규 진입자 (Dividend Challengers): 
        <span style="font-size: 12px; font-weight: normal; color: black;">5~9년 연속 배당 증가 (대표 기업: 브로드컴, 페이팔, 디즈니)</span>
    </p>
    """,
    unsafe_allow_html=True
)
    

st.markdown(
    """
    <br/>
    <h5 style="color: #1f4e79;">그렇다면 국내상장사의 배당계급은?</h5>
    """,
    unsafe_allow_html=True
)


#최초 로딩까지 시간이 걸리므로 안내문구 표출
with st.spinner('잠시만 기다려 주세요... 데이터 로드 중입니다.'):
        
    #-----------------------------------------------------------
    # 데이터베이스에서 데이터 받아오기
    #-----------------------------------------------------------

    
    # 데이터를 캐싱하여 재사용
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
                total_rows_query = "SELECT COUNT(*) FROM ds_dividend"
                total_cursor.execute(total_rows_query)
                total_rows = total_cursor.fetchone()[0]
                total_cursor.close()
    
                # 데이터 가져오기
                query = "SELECT * FROM ds_dividend"
                cursor.execute(query)
    
                # 데이터프레임 초기화
                disc = pd.DataFrame(columns=[desc[0] for desc in cursor.description])
    
                # 배치로 데이터를 가져오는 로직 (이 부분은 그대로 유지)
                batch_size = 1000  # 한 번에 가져올 행의 수
                rows_fetched = 0
    
                while True:
                    rows = cursor.fetchmany(batch_size)
                    if not rows:
                        break
                    disc = pd.concat([disc, pd.DataFrame(rows, columns=disc.columns)], ignore_index=True)
    
                    rows_fetched += len(rows)
    
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
    
#최초 로딩까지 시간이 걸리므로 안내문구 표출
with st.spinner('데이터 가공 중입니다.'):    
    # 데이터 가공 및 캐싱
    @st.cache_data
    def process_data(df):
        df_data_annual = df[df['accounting_type'] == '1'].sort_values(by=['symbol', 'year'])
    
        # 연속배당증가 및 배당증가유지 계산
        streak_list = []
        maintain_list = []
        
        # 각 기업별로 그룹화하여 처리
        for symbol, group in df_data_annual.groupby('symbol'):
            streak, maintain = 0, 0
            prev_dps = None
            for idx, row in group.iterrows():
                current_dps = row['DPS_ord_ord_share']
                # 연속배당 순수증가
                if prev_dps is not None and current_dps > prev_dps:
                    streak += 1
                else:
                    streak = 0
                
                # 연속배당 증가 또는 유지
                if prev_dps is not None and current_dps >= prev_dps and current_dps != 0:
                    maintain += 1
                else:
                    maintain = 0
    
                streak_list.append(streak)
                maintain_list.append(maintain)
                prev_dps = current_dps
    
        df_data_annual['연속배당증가'] = streak_list
        df_data_annual['배당증가유지'] = maintain_list
        
        #-----------------------------------------------------------
        # 특정해를 기준으로 최근 5년 배당추이 확인하는 칼럼 만들기
        
        # 최근 5년 DPS를 리스트형태로 만드는 함수
        def calculate_recent_dps_fixed(df):
            recent_dps = []
            
            # Group the data by 'symbol' to calculate the 5-year history for each entity
            for symbol, group in df.groupby('symbol'):
                group = group.copy()
                dps_list = group['DPS_ord_ord_share'].tolist()
                history = []
                for i in range(len(dps_list)):
                    # 현재연도를 포함해서 최근5년 값을 리스트로 저장
                    start_idx = max(0, i - 4)  # Index to start, max ensures we don't go below 0
                    last_5_years = dps_list[start_idx:i+1]
                    
                    # 만약 5년이 안되는 기간이라면 빈 기간은 0으로 채움
                    if len(last_5_years) < 5:
                        last_5_years = [0] * (5 - len(last_5_years)) + last_5_years
                    
                    history.append(last_5_years)
                
                group['최근배당추이'] = history
                recent_dps.append(group)
            
            return pd.concat(recent_dps)
        
        # 함수 적용
        df_data_annual2 = calculate_recent_dps_fixed(df_data_annual)
        
        #-----------------------------------------------------------
        # 웹페이지 표출을 위해 필요한 열만 남기고 이름 수정하기
        df_data_annual3 = df_data_annual2[['symbol', 'entity_name', 'year', 
                                           'net_income', 'EPS',
                                           'div_payout_ratio', 
                                           'DPS_ord_ord_share', 'DPS_ord_pref_share',
                                           'mid_dividend', '연속배당증가',
                                           '배당증가유지', '최근배당추이']]
        
        df_data_annual3.columns = ['종목코드', '회사명', '기준연도', '당기순이익', 'EPS', '배당성향(%)',
                                   'DPS(보통주)', 'DPS(우선주)', '중간배당 여부', 
                                   '연속배당증가', '배당증가유지', '최근배당추이']
        
        # 종목코드의 앞자리 KRX:를 제외하기
        df_data_annual3['종목코드'] = df_data_annual3['종목코드'].apply(lambda x : x[4:])
        
        # 연도를 숫자형이 아닌 텍스트화하기
        df_data_annual3['기준연도'] = df_data_annual3['기준연도'].astype(str)
        
        return df_data_annual3

    # 데이터 가공
    df_data_annual3 = process_data(df_data)
    
    
    
    
#-----------------------------------------------------------
# 최근연도 기준 데이터만 표출. 배당증가유지 순서
df_show_by_rank = df_data_annual3[df_data_annual3['기준연도'] == '2023'].sort_values('연속배당증가', ascending = False)

# 에러방지를 위해 데이터형태 변경
# 데이터프레임의 데이터 타입을 Python 기본 타입으로 변환하는 함수
def convert_to_python_types(df):
    for col in df.columns:
        if df[col].dtype == 'int64':  # int64 -> int
            df[col] = df[col].astype(float)
        elif df[col].dtype == 'float64':  # float64 -> float
            df[col] = df[col].astype(float)
        elif df[col].dtype == 'object':
            # '최근배당추이' 컬럼처럼 리스트 형태인 경우에 대한 변환 처리
            if isinstance(df[col].iloc[0], list):
                df[col] = df[col].apply(lambda x: [float(item) for item in x])  # 리스트 내의 값들을 int로 변환
    return df

# 데이터 타입을 변환한 후 사용
df_show_by_rank = convert_to_python_types(df_show_by_rank)

# # 최근배당추이 컬럼의 리스트 안 데이터 타입을 int64에서 int로 변환
df_show_by_rank['최근배당추이'] = df_show_by_rank['최근배당추이'].apply(lambda lst: [float(x) for x in lst])


max_increase = df_show_by_rank['연속배당증가'].max()
max_increase_maintain = df_show_by_rank['배당증가유지'].max()



# '최근배당추이' 칼럼을 막대 그래프로 표현
st.dataframe(
    df_show_by_rank.reset_index(drop = True),
    column_config={
        '연속배당증가': st.column_config.ProgressColumn(
            "연속배당증가 햇수",  # 컬럼 제목
            help="연속으로 배당이 증가한 햇수",  # 도움말 텍스트
            min_value = 0,
            max_value= max_increase,  # 최대값 설정 
            format="%d",
        ),
        '배당증가유지': st.column_config.ProgressColumn(
            "배당증가세 유지 햇수",  # 컬럼 제목
            help="배당Cut이 발생하지 않고, 배당이 같거나 증가한 햇수",  # 도움말 텍스트
            min_value = 0,
            max_value= max_increase_maintain,  # 최대값 설정 
            format="%d",
        ),
        '최근배당추이': st.column_config.BarChartColumn(
            "최근 5년 배당 추이",  # 컬럼의 제목
            help="최근 5년간 배당 지급 이력",  # 도움말 텍스트
        ),
    },
    use_container_width=False  # 데이터프레임이 화면 크기에 맞게 표시되도록 설정
)

#-----------------------------------------------------------
# 종목코드 입력란 및 검색 버튼 추가
#-----------------------------------------------------------
st.markdown(
    """
    <h5 style="color: #1f4e79;">개별 종목코드 여섯자리를 입력 후 엔터키를 누르세요</h5>
    """,
    unsafe_allow_html=True
)
# 사용자에게 종목코드를 입력받기 위한 텍스트 입력란
search_code_input = st.text_input("", max_chars=6, label_visibility="collapsed")

# 종목코드가 입력되었을 때 데이터 처리
if search_code_input and len(search_code_input) == 6 and search_code_input.isdigit():
    search_code = search_code_input  # 유효한 종목코드일 경우 search_code 변수에 저장

    # 종목코드로 데이터를 필터링하여 정렬
    df_show_by_company = df_data_annual3[df_data_annual3['종목코드'] == search_code].sort_values('기준연도', ascending=False)

    # '최근배당추이' 열을 제거한 새로운 데이터프레임을 반환
    df_show_by_company = df_show_by_company.drop('최근배당추이', axis=1)

    # 검색된 데이터가 있는지 확인
    if not df_show_by_company.empty:
        # 검색 결과 출력
        st.dataframe(df_show_by_company.reset_index(drop=True),
                     use_container_width=False)  # 인덱스를 제거하고 데이터프레임 출력
    else:
        # 검색된 데이터가 없을 때의 메시지
        st.warning(f"입력하신 종목코드 '{search_code}'에 해당하는 데이터가 없습니다.")
else:
    # 유효하지 않은 종목코드를 입력했을 때 에러 메시지 출력
    if search_code_input:
        st.error("종목코드 여섯자리를 정확히 입력하세요.")

# # 검색 버튼으로 동작
# if st.button('검색'):
#     # 사용자가 입력한 종목코드가 여섯 자리 숫자인지 확인
#     if len(search_code_input) == 6 and search_code_input.isdigit():
#         search_code = search_code_input  # 유효한 종목코드일 경우 search_code 변수에 저장

#         # 종목코드로 데이터를 필터링하여 정렬
#         df_show_by_company = df_data_annual3[df_data_annual3['종목코드'] == search_code].sort_values('기준연도', ascending=False)
#         df_show_by_company = df_show_by_company.drop('최근배당추이', axis=1)

#         # 검색된 데이터가 있는지 확인
#         if not df_show_by_company.empty:
#             # 검색 결과 출력
#             st.dataframe(df_show_by_company.reset_index(drop = True))
#         else:
#             # 검색된 데이터가 없을 때의 메시지
#             st.warning(f"입력하신 종목코드 '{search_code}'에 해당하는 데이터가 없습니다.")
#     else:
#         # 유효하지 않은 종목코드를 입력했을 때 에러 메시지 출력
#         st.error("종목코드 여섯자리를 입력하세요.")

st.write('※데이터 : NICE평가정보 "기업 - 기업 일반 정보 - 주주 및 배당"')



# #아나콘다 프롬프트에서 실행하는 코드
# #cd C:\Users\170027\Documents\krxnewsscrap
# #streamlit run dividend_class.py