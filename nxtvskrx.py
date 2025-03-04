import streamlit as st
import pandas as pd
import requests

# NXT 데이터 가져오는 함수
def get_nxt_data():
    url = 'https://www.nextrade.co.kr/brdinfoTime/brdinfoTimeList.do'
    params = {
        "_search": False,
        "nd": 1741074199874,
        "pageUnit": 900,
        "pageIndex": 1,
        "sidx": "",
        "sord": "asc"
    }
    
    response = requests.post(url, params=params)
    data = response.json()
    
    if data.get("brdinfoTimeList"):
        now_date = data["brdinfoTimeList"][0].get("nowDd", "날짜 없음")
        now_time = data["brdinfoTimeList"][0].get("nowTime", "시간 없음")
    else:
        now_date, now_time = "날짜 없음", "시간 없음"
    
    df_nxt = pd.DataFrame(data.get("brdinfoTimeList", []))
    return df_nxt, now_date, now_time

# KRX 데이터 가져오는 함수
def get_krx_data():
    url = 'https://data.krx.co.kr/comm/fileDn/downloadCsv/download.cmd'
    params = {
        "code": "all"  # 예제 코드, 실제 사용 시 적절한 코드로 변경 필요
    }
    
    response = requests.post(url, params=params)
    df_krx = pd.read_csv(response.content.decode("euc-kr"))
    return df_krx

# KRX와 NXT 데이터 병합 함수
def merge_data():
    df_nxt, date, time = get_nxt_data()
    df_krx = get_krx_data()
    
    df_agg = pd.merge(df_krx, df_nxt, left_on='종목코드', right_on='isuSrdCd', how='inner')
    return df_agg, date, time

# Streamlit 앱 생성
st.title("KRX vs NXT 비교")

if st.button("오늘의 KRXvsNXT비교"):
    df_agg, date, time = merge_data()
    st.write(f"NXT 가격 기준 시각: {date} {time}")
    st.dataframe(df_agg)
