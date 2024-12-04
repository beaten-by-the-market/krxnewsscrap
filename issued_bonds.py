import requests
import pandas as pd
from xml_to_dict import XMLtoDict
import streamlit as st

# XMLtoDict 객체 초기화 (XML 파싱용)
xd = XMLtoDict()

# Streamlit Secrets에서 API 키 불러오기
api_key = st.secrets["general"]["seibro_api_key"]

# 오늘 날짜를 기본값으로 설정
issue_dt = st.date_input("발행 날짜를 선택하세요", pd.to_datetime("today"))

# Seibro API에서 채권 발행 정보를 가져오는 함수
def get_issued_bonds(issue_dt):
    # API URL 구성
    url = f'http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={api_key}&apiId=getBondIssuInfo&params=ISSU_DT:{issue_dt}'    
    # API로부터 데이터 요청
    raw = requests.get(url, verify=False)
    # XML 데이터를 파싱하여 딕셔너리 형태로 변환
    data_dict = xd.parse(raw.content.decode('utf-8'))
    result = data_dict['SeibroAPI']['vector']['@result']
    
    # API 결과에 따라 처리
    if result == '0':
        # 결과가 0이면 데이터가 없음 -> 빈 DataFrame 반환
        df_all = pd.DataFrame()
    elif result == '1':
        # 결과가 1이면 데이터가 하나만 있음 -> 해당 데이터로 DataFrame 생성
        data_list = data_dict['SeibroAPI']['vector']['data']
        df_all = pd.DataFrame(data_list['result'])
    else:
        # 결과가 2 이상일 경우 여러 개의 데이터 있음 -> 각 데이터를 DataFrame으로 변환
        data_list = data_dict['SeibroAPI']['vector']['data']
        df_all = pd.DataFrame([{k: v['@value'] for k, v in item['result'].items()} for item in data_list])
    return df_all

# 사용자가 선택한 발행 날짜 표시
st.write(f"선택한 발행 날짜: {issue_dt}")

# 채권 데이터를 API로부터 가져오기
df_bonds = get_issued_bonds(issue_dt)

# 채권 데이터가 있으면 화면에 DataFrame으로 출력, 없으면 "발행된 채권 없음" 메시지 출력
if not df_bonds.empty:
    st.write(f"{issue_dt}에 발행된 채권 목록:", df_bonds)
else:
    st.write(f"{issue_dt}에 발행된 채권이 없습니다.")
