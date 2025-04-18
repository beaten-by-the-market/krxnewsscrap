import pandas as pd
import requests
from io import BytesIO
import streamlit as st
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(
    page_title="KRX 당일채권 상장종목",
    page_icon="📊",
    layout="wide"
)

# 날짜 계산 함수
def get_default_date():
    today = datetime.today()
    if today.weekday() in [5, 6]:  # 토요일(5) 또는 일요일(6)
        return (today - timedelta(days=today.weekday() - 4)).strftime("%Y-%m-%d")  # 직전 금요일
    return today.strftime("%Y-%m-%d")  # 오늘 날짜

# 데이터 로딩 함수 (캐싱 적용 - 유효시간 10분)
@st.cache_data(ttl=600)
def load_bond_data():
    try:
        # 거래소 홈페이지에서 불러오기
        # 화면번호 [14011] 상장채권 상세검색
        gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
        gen_otp_data = {
            "locale": "ko_KR",
            "tboxisurCd_finder_bndordisu0_0": "전체",
            "isurCd": "",
            "isurCd2": "",
            "codeNmisurCd_finder_bndordisu0_0": "",
            "param1isurCd_finder_bndordisu0_0": "",
            "bndTpCd": "",
            "tboxbndClssCd_finder_bndclss0_0": "",
            "bndClssCd": "",
            "bndClssCd2": "",
            "codeNmbndClssCd_finder_bndclss0_0": "",
            "param1bndClssCd_finder_bndclss0_0": "",
            "endrTyp": "",
            "spbTyp": "",
            "opbTyp": "0",
            "irtPayMth": "",
            "refundNm": "",
            "strtDd1": "",
            "endDd1": "",
            "strtDd2": "",
            "endDd2": "",
            "crdtAssInst": "",
            "crdtAssRk": "",
            "strtDd3": "",
            "endDd3": "",
            "currTpCd": "",
            "rankTpCd": "",
            "money": "2",
            "csvxls_isNo": "false",
            "name": "fileDown",
            "url": "dbms/MDC/STAT/standard/MDCSTAT10801"
        }

        headers = {
            'Referer': 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC03010201',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        otp = requests.post(gen_otp_url, gen_otp_data, headers=headers).text
        down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
        down_content = requests.post(down_url, {'code': otp}, headers=headers)
        
        # CSV 데이터 로드 및 상장일 칼럼 날짜 변환 (날짜만 추출)
        bonds = pd.read_csv(BytesIO(down_content.content), encoding='EUC-KR')
        bonds['상장일'] = pd.to_datetime(bonds['상장일'], format='%Y/%m/%d').dt.date
        return bonds
    except Exception as e:
        st.error(f"데이터 로딩 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 메인 애플리케이션
def main():
    st.title('KRX 당일채권 상장종목')
    
    # 제목
    st.subheader('조회일자 선택')

    # 날짜 선택 위젯 추가
    selected_date = st.date_input(
        "조회할 날짜를 선택하세요",
        value=datetime.strptime(get_default_date(), "%Y-%m-%d"),
        min_value=datetime(2020, 1, 1),  # 최소 선택 가능 날짜
        max_value=datetime.today()       # 최대 선택 가능 날짜
    )

    # 선택된 날짜를 date 객체로 변환
    today_date = selected_date.strftime("%Y-%m-%d")
    
    # 데이터 로딩 표시
    with st.spinner('KRX 정보데이터시스템에서 채권 데이터를 불러오는 중입니다...'):
        bonds = load_bond_data()
        
        if not bonds.empty:
            # 선택된 날짜로 필터링
            filtered_bonds = bonds[bonds['상장일'] == selected_date]
            
            # 결과 표시
            st.subheader(f'{today_date} 상장된 채권 목록')
            
            if len(filtered_bonds) == 0:
                st.info(f'{today_date}에 상장된 채권이 없습니다.')
            else:
                st.success(f'총 {len(filtered_bonds)}개의 채권이 상장되었습니다.')
                st.dataframe(filtered_bonds)
            
            # 추가 기능: 날짜 범위 선택 옵션
            st.subheader('날짜 범위로 조회')
            use_date_range = st.checkbox('날짜 범위로 조회하기')
            
            if use_date_range:
                col1, col2 = st.columns(2)
                
                with col1:
                    start_date = st.date_input(
                        "시작 날짜",
                        value=selected_date - timedelta(days=7),
                        min_value=datetime(2020, 1, 1).date(),
                        max_value=selected_date
                    )
                
                with col2:
                    end_date = st.date_input(
                        "종료 날짜",
                        value=selected_date,
                        min_value=start_date,
                        max_value=datetime.today().date()
                    )
                
                # 날짜 범위로 필터링
                range_filtered_bonds = bonds[(bonds['상장일'] >= start_date) & (bonds['상장일'] <= end_date)]
                
                st.subheader(f'{start_date.strftime("%Y-%m-%d")} ~ {end_date.strftime("%Y-%m-%d")} 상장된 채권 목록')
                
                if len(range_filtered_bonds) == 0:
                    st.info('해당 기간에 상장된 채권이 없습니다.')
                else:
                    st.success(f'총 {len(range_filtered_bonds)}개의 채권이 상장되었습니다.')
                    st.dataframe(range_filtered_bonds)
                    
                    # 데이터 분석 차트 추가
                    if len(range_filtered_bonds) > 1:
                        st.subheader('일자별 상장 채권 수')
                        # 날짜 그룹화를 위해 상장일 컬럼을 문자열로 변환
                        range_filtered_bonds['상장일_문자열'] = range_filtered_bonds['상장일'].astype(str)
                        date_counts = range_filtered_bonds.groupby('상장일_문자열').size().reset_index(name='채권수')
                        
                        # 정렬을 위해 다시 날짜로 변환하고 정렬 후 문자열로 변환
                        date_counts['정렬용_날짜'] = pd.to_datetime(date_counts['상장일_문자열'])
                        date_counts = date_counts.sort_values('정렬용_날짜')
                        
                        # 차트 표시
                        st.bar_chart(date_counts.set_index('상장일_문자열')['채권수'])

if __name__ == "__main__":
    main()
