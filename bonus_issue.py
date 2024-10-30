import pandas as pd
import mysql.connector
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots

import streamlit as st

#-----------------------------------------------------------
# 환경변수 설정-로컬
#-----------------------------------------------------------
# # 인증키 설정
# import os
# from dotenv import load_dotenv
# # .env 파일 로드
# load_dotenv('C:/Users/170027/Documents/ad_hoc_issues/.env')


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

db_config = {
    'user': st.secrets["general"]["db_user"],
    'password': st.secrets["general"]["db_password"],
    'host': st.secrets["general"]["db_host"],
    'port': st.secrets["general"]["db_port"],
    'database': st.secrets["general"]["db_name"],
}

# # CRUD 작업에 사용하는 DB 정보를 불러오는 부분
# db_config_crud = {
#     'user': st.secrets["crud"]["db_user"],
#     'password': st.secrets["crud"]["db_password"],
#     'host': st.secrets["crud"]["db_host"],
#     'port': st.secrets["crud"]["db_port"],
# }

#-----------------------------------------------------------
# Streamlit UI 구성
#-----------------------------------------------------------
st.set_page_config(page_title='무상증자 Event Study', layout="wide")
st.title('무상증자 Event Study :sunglasses:')


#-----------------------------------------------------------
# 데이터베이스에서 데이터 받아오기
#-----------------------------------------------------------

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
            total_rows_query = "SELECT COUNT(*) FROM st_bonus_issue"
            total_cursor.execute(total_rows_query)
            total_rows = total_cursor.fetchone()[0]
            total_cursor.close()

            # 데이터 가져오기
            query = "SELECT * FROM st_bonus_issue"
            cursor.execute(query)

            # 데이터프레임 초기화
            disc = pd.DataFrame(columns=[desc[0] for desc in cursor.description])

            batch_size = 1000  # 한 번에 가져올 행의 수
            rows_fetched = 0  # 현재까지 가져온 행의 수

            # Progress bar 초기화
            # progress_bar = st.progress(0)
            
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                disc = pd.concat([disc, pd.DataFrame(rows, columns=disc.columns)], ignore_index=True)
                
                # 진행 상태 업데이트
                rows_fetched += len(rows)
                # progress_percentage = rows_fetched / total_rows
                # progress_bar.progress(progress_percentage)  # 진행 상태 업데이트

            # Progress bar 완료
            # progress_bar.progress(1.0)  # 100% 완료 표시
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
df = load_data_from_db()

#-----------------------------------------------------------
# 산점도 생성
#-----------------------------------------------------------
# 연도별로 색상을 다르게 지정하기 위해 연도 컬럼 추가
df['연도'] = pd.to_datetime(df['bddd']).dt.year

# 색상 맵핑 설정 (예: 연도별로 색상 다르게 설정)
colors = ['blue', 'green', 'red', 'purple']
years = df['연도'].unique()
color_map = {year: colors[i % len(colors)] for i, year in enumerate(years)}


# # 서브플롯 생성 (2개의 열로 구성)
# fig = make_subplots(rows=1, cols=2, subplot_titles=("발행비율 vs 당일 주가 수익률", "발행비율 vs 전후1일 주가 수익률"))


# # 1) 발행비율 vs 당일 주가 수익률 산점도 - 연도별로 색상을 다르게
# for year in years:
#     scatter = go.Scatter(
#         x=df[df['연도'] == year]["발행비율"],
#         y=df[df['연도'] == year]["당일_수익률"],
#         mode="markers",
#         marker=dict(size=6, color=color_map[year], opacity=0.7),
#         name=f"{year}년",
#         text=df[df['연도'] == year].apply(lambda row: f"종목코드: {row['stock_code']}<br>종목명: {row['corp_name']}<br>결정일: {str(row['bddd'])[:10]}<br>발행비율: {row['발행비율']}<br>수익률: {row['당일_수익률']}", axis=1),
#         hoverinfo="text"
#     )
#     fig.add_trace(scatter, row=1, col=1)

# # 2) 발행비율 vs 전후1일 주가 수익률 산점도 - 연도별로 색상을 다르게
# for year in years:
#     scatter = go.Scatter(
#         x=df[df['연도'] == year]["발행비율"],
#         y=df[df['연도'] == year]["전후1일_수익률"],
#         mode="markers",
#         marker=dict(size=6, color=color_map[year], opacity=0.7),
#         name=f"{year}년",
#         text=df[df['연도'] == year].apply(lambda row: f"종목코드: {row['stock_code']}<br>종목명: {row['corp_name']}<br>결정일: {str(row['bddd'])[:10]}<br>발행비율: {row['발행비율']}<br>수익률: {row['전후1일_수익률']}", axis=1),
#         hoverinfo="text"
#     )
#     fig.add_trace(scatter, row=1, col=2)


# # y=0에 굵은 색 선 추가
# fig.add_shape(
#     type="line", y0=0, y1=0, x0=min(df["발행비율"]), x1=max(df["발행비율"]),
#     line=dict(color="black", width=2), row=1, col=1
# )

# fig.add_shape(
#     type="line", y0=0, y1=0, x0=min(df["발행비율"]), x1=max(df["발행비율"]),
#     line=dict(color="black", width=2), row=1, col=2
# )

# # 레이아웃 설정
# fig.update_layout(
#     title="발행비율과 주가 수익률 비교",
#     xaxis_title="발행비율",
#     yaxis_title="당일 주가 수익률",
#     xaxis2_title="발행비율",
#     yaxis2_title="전후1일 주가 수익률",
#     template="plotly_white",
#     showlegend=True,
#     legend=dict(
#         title="연도",  # legend 제목 설정
#         x=1.05,  # legend의 x 위치 조정
#         y=1,     # legend의 y 위치 조정
#     )
# )

# # Streamlit에 Plotly 그래프 표시
# st.plotly_chart(fig, use_container_width=True)

# 연도 리스트를 내림차순으로 정렬
years = sorted(df['연도'].unique(), reverse=True)

# Streamlit UI에서 두 개의 Column을 생성합니다.
col1, col2 = st.columns(2)

# 발행비율 vs 당일 주가 수익률 산점도
with col1:
    fig1 = go.Figure()

    # 연도별로 다른 색상을 지정하여 단일 산점도 생성
    for year in years:
        fig1.add_trace(
            go.Scatter(
                x=df[df['연도'] == year]["발행비율"],
                y=df[df['연도'] == year]["당일_수익률"],
                mode="markers",
                marker=dict(size=6, color=color_map[year], opacity=0.7),
                name=f"{year}년",
                text=df[df['연도'] == year].apply(lambda row: f"종목코드: {row['stock_code']}<br>종목명: {row['corp_name']}<br>결정일: {str(row['bddd'])[:10]}<br>발행비율: {row['발행비율']}<br>수익률: {row['당일_수익률']}", axis=1),
                hoverinfo="text"
            )
        )

    fig1.update_layout(
        title="발행비율 vs 당일 주가 수익률",
        xaxis_title="발행비율",
        yaxis_title="당일 주가 수익률",
        template="plotly_white",
        showlegend=True,
        legend=dict(
            title="연도",
            x=1.05,
            y=1,
        )
    )

    fig1.add_shape(
        type="line", y0=0, y1=0, x0=min(df["발행비율"]), x1=max(df["발행비율"]),
        line=dict(color="black", width=2)
    )
    st.plotly_chart(fig1, use_container_width=True)

# 발행비율 vs 전후1일 주가 수익률 산점도
with col2:
    fig2 = go.Figure()

    # 연도별로 다른 색상을 지정하여 단일 산점도 생성
    for year in years:
        fig2.add_trace(
            go.Scatter(
                x=df[df['연도'] == year]["발행비율"],
                y=df[df['연도'] == year]["전후1일_수익률"],
                mode="markers",
                marker=dict(size=6, color=color_map[year], opacity=0.7),
                name=f"{year}년",
                text=df[df['연도'] == year].apply(lambda row: f"종목코드: {row['stock_code']}<br>종목명: {row['corp_name']}<br>결정일: {str(row['bddd'])[:10]}<br>발행비율: {row['발행비율']}<br>수익률: {row['전후1일_수익률']}", axis=1),
                hoverinfo="text"
            )
        )

    fig2.update_layout(
        title="발행비율 vs 전후1일 주가 수익률",
        xaxis_title="발행비율",
        yaxis_title="전후1일 주가 수익률",
        template="plotly_white",
        showlegend=True,
        legend=dict(
            title="연도",
            x=1.05,
            y=1,
        )
    )

    fig2.add_shape(
        type="line", y0=0, y1=0, x0=min(df["발행비율"]), x1=max(df["발행비율"]),
        line=dict(color="black", width=2)
    )
    st.plotly_chart(fig2, use_container_width=True)



#-----------------------------------------------------------
# 종목코드, 결의일 입력받기
#-----------------------------------------------------------

# Streamlit UI에서 종목코드 입력과 검색 버튼 추가
col1, col2 = st.columns([1, 5])  # 종목코드 입력과 검색 버튼을 나란히 배치

with col1:
    stock_code_input = st.text_input("종목코드 입력 (6자리)", max_chars=6)

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # 줄 간격 조절
    search_button = st.button("검색")
#-----------------------------------------------------------
# 대상정보 불러오기
#-----------------------------------------------------------
def load_filtered_data(stock_code):
    connection = None
    try:
        # 데이터베이스 연결
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor()

            # SQL 쿼리 작성 및 실행
            query = """
            SELECT * FROM st_bonus_issue_price 
            WHERE stock_code = %s
            """
            cursor.execute(query, (stock_code,))

            # 데이터프레임 초기화 및 데이터 로드
            result_df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

            # '날짜' 칼럼을 datetime으로 변환
            result_df['날짜'] = pd.to_datetime(result_df['날짜'])

            return result_df

    except mysql.connector.Error as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()  # 빈 데이터프레임 반환

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# 이후 검색 버튼 클릭 시 데이터 로드 및 '날짜'를 인덱스로 설정
if search_button and stock_code_input:
    df_url = df[df['stock_code'] == stock_code_input]
    list_url = df_url['rcept_no'].unique().tolist()
    for url in list_url:
        st.write(f'공시링크 : https://dart.fss.or.kr/dsaf001/main.do?rcpNo={url}')
    df_price = load_filtered_data(stock_code_input)
    # st.dataframe(df_price)
    
    # '날짜'를 datetime 형식으로 변환 후 인덱스로 설정
    if not pd.api.types.is_datetime64_any_dtype(df_price['날짜']):
        df_price['날짜'] = pd.to_datetime(df_price['날짜']).dt.date  # 날짜만 남기고 시간 제거
    df_price.set_index('날짜', inplace=True)
            
    #거래정지인경우 시가, 고가, 저가가 0으로 나타나므로, 종가로 대체해 주는 과정
    df_price['시가'] = np.where(df_price.시가 == 0, df_price.종가, df_price.시가)
    df_price['고가'] = np.where(df_price.고가 == 0, df_price.종가, df_price.고가)
    df_price['저가'] = np.where(df_price.저가 == 0, df_price.종가, df_price.저가)
    
    # '결의일' 및 '배정기준일'이 존재할 경우 datetime 형식으로 변환
    if '결의일' in df_price.columns:
        df_price['결의일'] = pd.to_datetime(df_price['결의일'], errors='coerce')
    
    if '배정기준일' in df_price.columns:
        df_price['배정기준일'] = pd.to_datetime(df_price['배정기준일'], errors='coerce')

    if not df_price.empty:
        # '결의일' 컬럼의 unique 값 확인(한 종목에 여러번 이벤트가능하므로)
        unique_dates = df_price['결의일'].unique()

        for date in unique_dates:
            df_loop = df_price[df_price['결의일'] == date]
            # 날짜를 기준으로 데이터 정렬
            df_loop = df_loop.sort_index()
            
            # 필요변수 설정
            corp_name = df_loop['corp_name'].iloc[0]
            descision_date = pd.Timestamp(df_loop['결의일'].iloc[0])
            criteria_date = pd.Timestamp(df_loop['배정기준일'].iloc[0])
            ratio = df_loop['발행비율'].iloc[0] * 100
            # 그래프 제목
            title = f"{corp_name} (결정일: {descision_date.strftime('%Y-%m-%d')}, 무증비율: {ratio:.1f}%)"

            # 서브플롯 생성
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.7, 0.3], 
                                vertical_spacing=0.1,
                                )

            # 캔들차트 추가
            fig.add_trace(
                go.Candlestick(
                    x=df_loop.index.strftime('%Y-%m-%d'),
                    open=df_loop['시가'],
                    high=df_loop['고가'],
                    low=df_loop['저가'],
                    close=df_loop['종가'],
                    increasing_line_color='red',
                    decreasing_line_color='blue',
                    showlegend=False
                ),
                row=1, col=1
            )

            # 거래량 차트 추가
            color_list = np.where(df_loop['거래량'].diff().fillna(0) >= 0, 'red', 'blue')
            fig.add_trace(
                go.Bar(
                    x=df_loop.index.strftime('%Y-%m-%d'),
                    y=df_loop['거래량'],
                    marker_color=color_list,
                    showlegend=False
                ),
                row=2, col=1
            )

            # 결의일 및 배정기준일을 문자열로 변환하여 x 축 범주와 일치하도록 설정
            descision_date_str = descision_date.strftime('%Y-%m-%d')
            criteria_date_str = criteria_date.strftime('%Y-%m-%d')
            
            # 결의일 및 배정기준일에 대한 세로선 추가 using add_shape
            fig.add_shape(type="line", x0=descision_date, x1=descision_date, y0=0, y1=1,
                          line=dict(color="red", width=2, dash="dash"), xref="x", yref="paper")
            fig.add_annotation(x=descision_date, y=-0.05, text="결의일", showarrow=False, xref="x", yref="paper", font=dict(color="red"))

            fig.add_shape(type="line", x0=criteria_date, x1=criteria_date, y0=0, y1=1,
                          line=dict(color="green", width=2, dash="dash"), xref="x", yref="paper")
            fig.add_annotation(x=criteria_date, y=-0.05, text="배정기준일", showarrow=False, xref="x", yref="paper", font=dict(color="green"))

            # 레이아웃 설정
            fig.update_layout(
                title=title,
                # xaxis_title='날짜',
                yaxis_title='가격',
                # xaxis2_title='날짜',
                yaxis2_title='거래량',
                template='plotly_white',
                xaxis_rangeslider_visible=False,
                height=700
            )

            # x축을 날짜 형식으로 지정
            fig.update_xaxes(type="date")
            # x축을 날짜 대신 카테고리로 설정하여 거래일만 포함하도록 변경
            # fig.update_xaxes(type="category", categoryarray=df_loop.index.strftime('%Y-%m-%d'))

            # fig.update_xaxes(type="category")
            
            # Streamlit에 Plotly 그래프 표시
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("해당 종목코드에 해당하는 데이터가 없습니다.")