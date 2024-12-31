import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from time import sleep

# 페이지 레이아웃 설정
st.set_page_config(page_title="Yieldmax ETF 분석", layout="wide")

# 기본 ETF 목록
default_etf_name = ['nvdy', 'tsly', 'ybit-bitcoin-option-income-etf', 'ymax', 'plty', 'msty', 'aiyy']

# Streamlit 인터페이스
st.title("Yieldmax ETF별 주당배당금(DPS) 추이")
st.write("기본 ETF 목록에 추가하거나 제거한 후, '검색' 버튼을 눌러 데이터를 확인하세요.")

# 사용자 입력: ETF 이름 목록
etf_name = st.text_input("추가할 ETF 이름 (쉼표로 구분)", value=", ".join(default_etf_name))
etf_name = [etf.strip() for etf in etf_name.split(",")]

# 검색 버튼
if st.button("검색"):
    st.write("데이터를 수집 중입니다. 잠시만 기다려 주세요.")
    progress_bar = st.progress(0)
    
    # 빈 데이터프레임 생성
    all_df = pd.DataFrame()

    for idx, i in enumerate(etf_name):
        try:
            url = f'https://www.yieldmaxetfs.com/our-etfs/{i}'
            req = requests.get(url, verify=False)
            all_soup = BeautifulSoup(req.text, 'html.parser')

            # 모든 table 태그를 선택
            tables = all_soup.find_all('table')

            # "ex date" 문자열을 포함하는 table 필터링
            filtered_tables = []
            for table in tables:
                if "ex date" in table.text.lower():
                    filtered_tables.append(table)

            # 첫 번째 테이블
            if filtered_tables:
                target_table = filtered_tables[0]

                # 테이블에서 헤더 추출
                headers = [th.text.strip() for th in target_table.find_all('th')]

                # 테이블에서 데이터 추출
                rows = []
                for row in target_table.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if cells:  # 데이터가 있는 행만 처리
                        rows.append([cell.text.strip() for cell in cells])

                # 판다스 데이터프레임 생성
                df = pd.DataFrame(rows, columns=headers)

                # 필요한 칼럼만 남기기
                if all(col in df.columns for col in ['ticker_name', 'Distribution per Share', 'ex date']):
                    df = df[['ticker_name', 'Distribution per Share', 'ex date']]

                    # 각 데이터프레임에 고유 접미사 추가
                    df.columns = [f"{col}_{i}" for col in df.columns]

                    # 데이터프레임 가로 결합
                    all_df = pd.concat([all_df, df], axis=1)
            
            # 진행률 업데이트
            progress_bar.progress((idx + 1) / len(etf_name))
            sleep(1)
        
        except Exception as e:
            st.error(f"ETF '{i}' 정보를 가져오는 중 오류 발생: {e}")
    
    progress_bar.progress(1.0)

    # 데이터 출력
    if not all_df.empty:
        st.write("ETF 데이터 결과:")
        st.dataframe(all_df, use_container_width=True)  # 화면 좌우로 꽉 차게 출력
    else:
        st.write("검색 결과가 없습니다.")
