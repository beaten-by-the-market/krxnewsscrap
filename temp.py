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

#검색어
url= url_base+'GetCompanyDividends(KRX:005930)'


response = requests.get(url, headers=headers, verify=False)

response_data = response.json()

docs = response_data['data']['pods'][1]['content']['data']
df = pd.DataFrame(docs)

# pivot_table을 사용하여 데이터 변환
pivot_df = df.pivot_table(
    index=['symbol', 'date', 'type', 'entity_name', 'accounting_type'],  # 나머지 칼럼들
    columns='dividend_type_name',  # unique 값을 칼럼으로 변환
    values='amount',  # amount를 값으로 사용
    aggfunc='sum'  # 중복된 값이 있을 때는 합산 (필요에 따라 다른 함수 사용 가능)
).reset_index()

