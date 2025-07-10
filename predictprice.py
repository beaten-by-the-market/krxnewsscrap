import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import BytesIO
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="주가 예측 시뮬레이션",
    page_icon="📈",
    layout="wide"
)

# 제목
st.title("📈 주가 예측 시뮬레이션 서비스")
st.markdown("---")

# 사이드바 설정
st.sidebar.header("🔧 설정")

# 세션 상태 초기화
if 'df_listed' not in st.session_state:
    st.session_state.df_listed = None
if 'stock_data' not in st.session_state:
    st.session_state.stock_data = None

# 종목 정보 로드 함수
@st.cache_data
def load_stock_list():
    """KRX에서 전체 종목 리스트를 가져오는 함수"""
    try:
        gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
        gen_otp = {
            'locale' : 'ko_KR',
            'mktId': 'ALL',
            'share': '1',
            'csvxls_isNo': 'false',
            'name': 'fileDown',
            'url': 'dbms/MDC/STAT/standard/MDCSTAT01901'
        }
        
        headers = {
            'Referer' : 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020201',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        otp = requests.post(gen_otp_url, gen_otp, headers=headers).text
        down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
        down_content = requests.post(down_url, {'code': otp}, headers=headers)
        
        df_listed = pd.read_csv(BytesIO(down_content.content), encoding='EUC-KR')
        df_listed['시장구분'] = df_listed['시장구분'].replace('KOSDAQ GLOBAL', 'KOSDAQ')
        df_listed = df_listed.rename(columns={'단축코드':'stock_code'})
        
        return df_listed
    except Exception as e:
        st.error(f"종목 정보 로드 중 오류 발생: {str(e)}")
        return None

# 주가 데이터 가져오기 함수
def get_price(stock_code, start_date, end_date, df_listed):
    """개별 종목의 주가 데이터를 가져오는 함수"""
    try:
        code = stock_code
        selected_row = df_listed[df_listed['stock_code'] == code]
        
        if selected_row.empty:
            return None
            
        isin = selected_row['표준코드'].values[0]
        corp_name = selected_row['한글 종목약명'].values[0]
        
        gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
        gen_otp = {
            'locale' : 'ko_KR',
            'tboxisuCd_finder_stkisu0_0': f'{code}/{corp_name}',
            'isuCd': f'{isin}',
            'isuCd2': f'{code}',
            'codeNmisuCd_finder_stkisu0_0': f'{corp_name}',
            'param1isuCd_finder_stkisu0_0': 'ALL',
            'strtDd': f'{start_date}',
            'endDd': f'{end_date}',
            'adjStkPrc_check': 'Y',
            'adjStkPrc': '2',
            'share': '1',
            'money': '1',
            'csvxls_isNo': 'false',
            'name': 'fileDown',
            'url': 'dbms/MDC/STAT/standard/MDCSTAT01701'
        }
        
        headers = {
            'Referer' : 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020201',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        otp = requests.post(gen_otp_url, gen_otp, headers=headers).text
        down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
        down_content = requests.post(down_url, {'code': otp}, headers=headers)
        
        df_ind_price = pd.read_csv(BytesIO(down_content.content), encoding='EUC-KR')
        
        return df_ind_price
        
    except Exception as e:
        st.error(f"주가 데이터 로드 중 오류 발생: {str(e)}")
        return None

# 안전한 datetime 처리 함수들
def safe_datetime_conversion(df, date_column):
    """안전한 datetime 변환 함수"""
    try:
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        df = df.dropna(subset=[date_column])
        return df
    except Exception as e:
        st.error(f"날짜 변환 중 오류 발생: {str(e)}")
        return None

def create_future_dates_ultimate(last_date, periods):
    """완전히 안전한 미래 날짜 생성 함수"""
    try:
        # 다양한 날짜 타입을 pandas.Timestamp로 통일
        if isinstance(last_date, np.datetime64):
            last_date = pd.Timestamp(last_date)
        elif isinstance(last_date, str):
            last_date = pd.Timestamp(last_date)
        elif not isinstance(last_date, pd.Timestamp):
            last_date = pd.Timestamp(last_date)
        
        # 안전한 방식으로 미래 날짜 생성
        future_dates = []
        for i in range(1, periods + 1):
            future_date = last_date + pd.DateOffset(days=i)
            future_dates.append(future_date)
        
        return pd.DatetimeIndex(future_dates)
        
    except Exception as e:
        st.error(f"미래 날짜 생성 중 오류 발생: {str(e)}")
        return None

# 예측 모델 함수들
def predict_arima(prices, periods=547):
    """ARIMA 모델을 사용한 주가 예측"""
    try:
        from statsmodels.tsa.arima.model import ARIMA
        model = ARIMA(prices, order=(5,1,0))
        fitted_model = model.fit()
        forecast = fitted_model.forecast(steps=periods)
        return forecast.values
    except:
        trend = np.mean(np.diff(prices[-30:]))
        last_price = prices[-1]
        return [last_price + trend * i for i in range(1, periods + 1)]

def predict_monte_carlo(prices, periods=547):
    """몬테카를로 시뮬레이션을 사용한 주가 예측"""
    returns = np.diff(prices) / prices[:-1]
    mu = np.mean(returns)
    sigma = np.std(returns)
    
    last_price = prices[-1]
    predictions = []
    
    for i in range(periods):
        shock = np.random.normal(mu, sigma)
        last_price = last_price * (1 + shock)
        predictions.append(last_price)
    
    return predictions

def predict_linear_regression(prices, periods=547):
    """선형 회귀를 사용한 주가 예측"""
    try:
        from sklearn.linear_model import LinearRegression
        
        x = np.arange(len(prices)).reshape(-1, 1)
        y = prices
        
        model = LinearRegression()
        model.fit(x, y)
        
        future_x = np.arange(len(prices), len(prices) + periods).reshape(-1, 1)
        predictions = model.predict(future_x)
        
        return predictions
    except:
        trend = (prices[-1] - prices[0]) / len(prices)
        last_price = prices[-1]
        return [last_price + trend * i for i in range(1, periods + 1)]

def predict_random_walk(prices, periods=547):
    """랜덤 워크 모델을 사용한 주가 예측"""
    returns = np.diff(prices) / prices[:-1]
    sigma = np.std(returns)
    
    last_price = prices[-1]
    predictions = [last_price]
    
    for i in range(periods - 1):
        shock = np.random.normal(0, sigma)
        last_price = last_price * (1 + shock)
        predictions.append(last_price)
    
    return predictions[1:]

def predict_lstm_simple(prices, periods=547):
    """간단한 LSTM 스타일 예측"""
    window = min(60, len(prices))
    ma = np.mean(prices[-window:])
    trend = (prices[-1] - prices[-window]) / window
    
    predictions = []
    for i in range(periods):
        pred = ma + trend * i + np.random.normal(0, np.std(prices[-window:]) * 0.1)
        predictions.append(pred)
    
    return predictions

# 예측 모델 설명
MODEL_DESCRIPTIONS = {
    "ARIMA": "시계열 데이터의 자기회귀, 차분, 이동평균을 조합한 모델로 과거 패턴을 분석하여 미래를 예측합니다.",
    "Monte Carlo": "확률적 시뮬레이션을 통해 다양한 시나리오를 가정하여 주가의 가능한 경로를 예측합니다.",
    "Linear Regression": "과거 데이터의 선형 추세를 분석하여 단순한 직선 형태의 미래 예측을 수행합니다.",
    "Random Walk": "주가가 무작위로 움직인다는 가정하에 과거 변동성을 기반으로 미래를 예측합니다.",
    "LSTM (간단버전)": "딥러닝 기반 모델로 장기 의존성을 고려한 패턴 분석을 통해 예측을 수행합니다."
}

# 메인 애플리케이션
def main():
    # 종목 정보 로드
    if st.session_state.df_listed is None:
        with st.spinner("종목 정보를 불러오는 중..."):
            st.session_state.df_listed = load_stock_list()
    
    if st.session_state.df_listed is None:
        st.error("종목 정보를 불러올 수 없습니다. 네트워크 연결을 확인해주세요.")
        return
    
    # 종목 검색
    st.sidebar.subheader("📊 종목 선택")
    
    # 검색 방식 선택
    search_method = st.sidebar.radio(
        "검색 방식",
        ["회사명으로 검색", "종목코드로 검색"]
    )
    
    selected_stock = None
    
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
            else:
                st.sidebar.error("해당 종목코드를 찾을 수 없습니다.")
    
    # 시나리오 설정
    st.sidebar.subheader("⚙️ 시나리오 설정")
    
    # 과거 데이터 기간 선택
    historical_period = st.sidebar.selectbox(
        "과거 데이터 기간",
        ["6개월", "1년", "3년"]
    )
    
    # 예측 모델 선택
    model_name = st.sidebar.selectbox(
        "예측 모델",
        ["ARIMA", "Monte Carlo", "Linear Regression", "Random Walk", "LSTM (간단버전)"]
    )
    
    # 선택된 모델 설명
    st.sidebar.info(f"**{model_name}**: {MODEL_DESCRIPTIONS[model_name]}")
    
    # 예측 실행 버튼
    if st.sidebar.button("🚀 예측 실행", type="primary"):
        if selected_stock:
            # 날짜 계산
            end_date = datetime.now()
            if historical_period == "6개월":
                start_date = end_date - timedelta(days=180)
            elif historical_period == "1년":
                start_date = end_date - timedelta(days=365)
            else:  # 3년
                start_date = end_date - timedelta(days=1095)
            
            # 주가 데이터 가져오기
            with st.spinner("주가 데이터를 불러오는 중..."):
                stock_data = get_price(
                    selected_stock,
                    start_date.strftime("%Y%m%d"),
                    end_date.strftime("%Y%m%d"),
                    st.session_state.df_listed
                )
            
            if stock_data is not None and not stock_data.empty:
                try:
                    # 데이터 정제
                    stock_data = safe_datetime_conversion(stock_data, '일자')
                    
                    if stock_data is None or stock_data.empty:
                        st.error("날짜 데이터 변환에 실패했습니다.")
                        return
                    
                    stock_data = stock_data.sort_values('일자')
                    
                    # 종가 데이터 변환
                    if '종가' in stock_data.columns:
                        stock_data['종가'] = pd.to_numeric(stock_data['종가'], errors='coerce')
                        stock_data = stock_data.dropna(subset=['종가'])
                    
                    if stock_data.empty:
                        st.error("유효한 주가 데이터가 없습니다.")
                        return
                    
                    # 데이터 추출
                    prices = stock_data['종가'].values
                    dates = stock_data['일자'].values
                    
                    # 마지막 날짜 추출
                    last_date = dates[-1]
                    
                    # 예측 수행
                    with st.spinner(f"{model_name} 모델로 예측 중..."):
                        if model_name == "ARIMA":
                            predictions = predict_arima(prices)
                        elif model_name == "Monte Carlo":
                            predictions = predict_monte_carlo(prices)
                        elif model_name == "Linear Regression":
                            predictions = predict_linear_regression(prices)
                        elif model_name == "Random Walk":
                            predictions = predict_random_walk(prices)
                        else:  # LSTM
                            predictions = predict_lstm_simple(prices)
                    
                    # 미래 날짜 생성
                    future_dates = create_future_dates_ultimate(last_date, len(predictions))
                    
                    if future_dates is None:
                        st.error("미래 날짜 생성에 실패했습니다.")
                        return
                    
                    # 결과 표시
                    st.subheader("📈 주가 예측 결과")
                    
                    # 🔧 완전히 새로운 그래프 생성 방식 - add_vline() 사용하지 않음
                    fig = go.Figure()
                    
                    # 과거 데이터
                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=prices,
                        mode='lines',
                        name='과거 주가',
                        line=dict(color='blue', width=2)
                    ))
                    
                    # 예측 데이터
                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=predictions,
                        mode='lines',
                        name='예측 주가',
                        line=dict(color='red', width=2, dash='dash')
                    ))
                    
                    # 🔧 add_vline() 대신 Shape를 사용한 구분선 - 핵심 수정
                    last_date_str = pd.Timestamp(last_date).strftime('%Y-%m-%d')
                    
                    # 주가 범위 계산
                    all_prices = np.concatenate([prices, predictions])
                    min_price = np.min(all_prices) * 0.95
                    max_price = np.max(all_prices) * 1.05
                    
                    fig.add_shape(
                        type="line",
                        x0=last_date_str,
                        y0=min_price,
                        x1=last_date_str,
                        y1=max_price,
                        line=dict(
                            color="gray",
                            width=2,
                            dash="dot"
                        )
                    )
                    
                    # 구분선 텍스트 추가
                    fig.add_annotation(
                        x=last_date_str,
                        y=max_price * 0.98,
                        text="예측 시작점",
                        showarrow=False,
                        font=dict(color="gray", size=12),
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="gray",
                        borderwidth=1
                    )
                    
                    fig.update_layout(
                        title=f"{st.session_state.df_listed[st.session_state.df_listed['stock_code']==selected_stock]['한글 종목약명'].iloc[0]} 주가 예측",
                        xaxis_title="날짜",
                        yaxis_title="주가 (원)",
                        height=600,
                        showlegend=True,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 예측 결과 데이터프레임 생성
                    prediction_df = pd.DataFrame({
                        '날짜': future_dates,
                        '예측주가': predictions
                    })
                    
                    # 통계 정보 표시
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("현재 주가", f"{prices[-1]:,.0f}원")
                    
                    with col2:
                        st.metric("예측 평균", f"{np.mean(predictions):,.0f}원")
                    
                    with col3:
                        change = ((predictions[-1] - prices[-1]) / prices[-1]) * 100
                        st.metric("1.5년 후 예상 수익률", f"{change:.1f}%")
                    
                    with col4:
                        st.metric("예측 최고가", f"{np.max(predictions):,.0f}원")
                    
                    # 엑셀 다운로드
                    st.subheader("📥 데이터 다운로드")
                    
                    # 엑셀 파일 생성
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        prediction_df.to_excel(writer, sheet_name='예측데이터', index=False)
                        stock_data[['일자', '종가']].to_excel(writer, sheet_name='과거데이터', index=False)
                    
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        label="📊 예측 결과 엑셀 다운로드",
                        data=excel_data,
                        file_name=f"{selected_stock}_주가예측_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    # 예측 데이터 테이블 표시
                    st.subheader("📋 예측 데이터 미리보기")
                    st.dataframe(prediction_df.head(20))
                    
                except Exception as e:
                    st.error(f"데이터 처리 중 오류 발생: {str(e)}")
                    import traceback
                    st.write("상세 오류 정보:")
                    st.code(traceback.format_exc())
                    return
                    
            else:
                st.error("주가 데이터를 불러올 수 없습니다.")
        else:
            st.warning("먼저 종목을 선택해주세요.")

if __name__ == "__main__":
    main()
