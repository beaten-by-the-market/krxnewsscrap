import streamlit as st
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import pandas as pd
from datetime import datetime
from io import BytesIO
from krx_data_api import fetch

# 페이지 설정
st.set_page_config(
    page_title="기업 재무 분석 대시보드",
    page_icon="📊",
    layout="wide"
)

# InsecureRequestWarning 비활성화
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 세션 상태 초기화
if 'df_listed' not in st.session_state:
    st.session_state.df_listed = None

# DeepSearch API 설정
API_KEY = st.secrets["general"]["api_key"]
API_HEADERS = {'Authorization': f'Basic {API_KEY}'}
API_BASE_URL = 'https://api.deepsearch.com/v1/compute?input='

# 종목 정보 로드 함수
@st.cache_data
def load_stock_list():
    """KRX에서 전체 종목 리스트를 가져오는 함수 (krx-data-api 패키지 사용)"""
    try:
        df_listed = fetch("listed_stocks")
        df_listed = df_listed.rename(columns={'단축코드': 'stock_code'})
        return df_listed
    except Exception as e:
        st.error(f"종목 정보 로드 중 오류 발생: {str(e)}")
        return None

def calculate_date_ranges():
    """재무 데이터 조회를 위한 날짜 범위 계산"""
    today = datetime.now()
    
    # 첫번째 쿼리: 8분기 데이터
    current_quarter = (today.month - 1) // 3 + 1
    
    if current_quarter == 1:
        prev_quarter_end = datetime(today.year - 1, 12, 31)
    else:
        prev_quarter_end_month = (current_quarter - 1) * 3
        if prev_quarter_end_month == 3:
            prev_quarter_end = datetime(today.year, 3, 31)
        elif prev_quarter_end_month == 6:
            prev_quarter_end = datetime(today.year, 6, 30)
        else:  # 9월
            prev_quarter_end = datetime(today.year, 9, 30)
    
    # 8분기 전 시작일 계산 (8분기 = 24개월)
    months_back = 24
    start_year = prev_quarter_end.year
    start_month = prev_quarter_end.month - months_back + 1
    
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    
    start_date = datetime(start_year, start_month, 1)
    
    # 두번째 쿼리: 6개월 전부터 현재까지
    six_months_ago = today - pd.DateOffset(months=6)
    
    return {
        'financial_start': start_date.strftime('%Y-%m-%d'),
        'financial_end': prev_quarter_end.strftime('%Y-%m-%d'),
        'consensus_start': six_months_ago.strftime('%Y-%m-%d'),
        'consensus_end': today.strftime('%Y-%m-%d')
    }

def fetch_financial_data(stock_code):
    """기본주당순이익, 당기순이익 데이터 조회"""
    try:
        date_ranges = calculate_date_ranges()
        
        query = f'KRX:{stock_code} {date_ranges["financial_start"]}-{date_ranges["financial_end"]} 분기 당기순이익 분기 기본주당순이익'
        url = f'{API_BASE_URL}{query}'.replace('\n','')
        
        response = requests.get(url, headers=API_HEADERS, verify=False)
        response_data = response.json()
        
        data_dict = response_data['data']['pods'][1]['content']['data']
        df_financial = pd.DataFrame(data_dict)
        df_financial.columns = ['date', 'symbol', 'entity_name', '당기순이익','기본주당순이익']
        
        # date에서 'T00:00:00' 제거
        df_financial['date'] = df_financial['date'].str.replace('T00:00:00', '', regex=False)
        
        # symbol에서 'KRX:' 제거하면서 동시에 칼럼명을 stock_code로 변경
        df_financial['stock_code'] = df_financial['symbol'].str.replace('KRX:', '', regex=False)
        
        # 기존 symbol 칼럼 삭제
        df_financial = df_financial.drop(columns=['symbol'])
        
        
        return df_financial
    except Exception as e:
        st.error(f"재무 데이터 조회 중 오류 발생: {str(e)}")
        return None

def fetch_consensus_data(stock_code):
    """애널리스트 예측치 데이터 조회"""
    try:
        date_ranges = calculate_date_ranges()
        
        query = f'SearchFirmFundamentalsForecasts(KRX:{stock_code}, last_only=True, date_from={date_ranges["consensus_start"]}, date_to={date_ranges["consensus_end"]})'
        url = f'{API_BASE_URL}{query}'.replace('\n','')
        
        response = requests.get(url, headers=API_HEADERS, verify=False)
        response_data = response.json()
        
        data_dict = response_data['data']['pods'][1]['content']['data']
        df_consensus = pd.DataFrame(data_dict)
        
        # 필요 컬럼만 추출
        df_consensus = df_consensus[['stock_code', 'forecast_date', 'accounting_type', 'inst_code',
                                   'name_ko', 'date','csd_net_income','net_income','csd_eps', 'eps', 'seq','unit_code']].copy()
        
        return df_consensus
    except Exception as e:
        st.error(f"컨센서스 데이터 조회 중 오류 발생: {str(e)}")
        return None

def main():
    st.title("📊 기업 재무 실적 및 컨센서스 조회")
    st.markdown("---")
    
    # 종목 정보 로드
    if st.session_state.df_listed is None:
        with st.spinner("종목 정보를 불러오는 중..."):
            st.session_state.df_listed = load_stock_list()
    
    if st.session_state.df_listed is None:
        st.error("종목 정보를 불러올 수 없습니다. 네트워크 연결을 확인해주세요.")
        return
    
    # 사이드바: 종목 검색
    st.sidebar.subheader("📊 종목 선택")
    
    # 검색 방식 선택
    search_method = st.sidebar.radio(
        "검색 방식",
        ["회사명으로 검색", "종목코드로 검색"]
    )
    
    selected_stock = None
    selected_company_name = None
    
    if search_method == "회사명으로 검색":
        company_name = st.sidebar.text_input("회사명을 입력하세요 (예: 삼성전자)")
        if company_name:
            matching_stocks = st.session_state.df_listed[
                st.session_state.df_listed['한글 종목약명'].str.contains(company_name, na=False)
            ]
            if not matching_stocks.empty:
                stock_options = []
                for _, row in matching_stocks.iterrows():
                    stock_options.append(f"{row['한글 종목약명']} ({row['stock_code']})")
                
                selected_option = st.sidebar.selectbox("종목을 선택하세요", stock_options)
                if selected_option:
                    selected_stock = selected_option.split('(')[1].split(')')[0]
                    selected_company_name = selected_option.split('(')[0].strip()
    
    else:  # 종목코드로 검색
        stock_code = st.sidebar.text_input("종목코드를 입력하세요 (예: 005930)")
        if stock_code:
            matching_stock = st.session_state.df_listed[
                st.session_state.df_listed['stock_code'] == stock_code
            ]
            if not matching_stock.empty:
                company_name = matching_stock['한글 종목약명'].iloc[0]
                st.sidebar.success(f"선택된 종목: {company_name} ({stock_code})")
                selected_stock = stock_code
                selected_company_name = company_name
            else:
                st.sidebar.error("해당 종목코드를 찾을 수 없습니다.")
    
    # 메인 화면: 데이터 표시
    if selected_stock:
        st.subheader(f"🏢 {selected_company_name} ({selected_stock}) 재무 분석")
        
        # 데이터 조회 버튼
        if st.button("📈 데이터 조회", type="primary"):
            col1, col2 = st.columns(2)
            
            # 재무 데이터 조회
            with col1:
                st.subheader("📊 분기별 재무 실적 데이터")
                with st.spinner("재무 데이터를 조회하는 중..."):
                    df_financial = fetch_financial_data(selected_stock)
                
                if df_financial is not None and not df_financial.empty:
                    st.dataframe(df_financial, use_container_width=True)
                    
                    # 다운로드 버튼
                    csv_financial = df_financial.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="💾 재무 데이터 CSV 다운로드",
                        data=csv_financial,
                        file_name=f"{selected_company_name}_재무데이터.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("재무 데이터를 찾을 수 없습니다.")
            
            # 컨센서스 데이터 조회
            with col2:
                st.subheader("🔮 애널리스트 예측 데이터")
                with st.spinner("컨센서스 데이터를 조회하는 중..."):
                    df_consensus = fetch_consensus_data(selected_stock)
                
                if df_consensus is not None and not df_consensus.empty:
                    st.dataframe(df_consensus, use_container_width=True)
                    st.write('Accounting Type 설명:')
                    st.write('K - annual, F - March, X - June, Y - September, Z - December')
                    # 다운로드 버튼
                    csv_consensus = df_consensus.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="💾 컨센서스 데이터 CSV 다운로드",
                        data=csv_consensus,
                        file_name=f"{selected_company_name}_컨센서스데이터.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("컨센서스 데이터를 찾을 수 없습니다.")
    else:
        st.info("👈 사이드바에서 종목을 선택해주세요.")

if __name__ == "__main__":
    main()
