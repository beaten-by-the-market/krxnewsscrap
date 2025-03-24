import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from io import BytesIO
from datetime import datetime
import plotly.io as pio
pio.json.config.default_engine = 'json'  # orjson 대신 기본 json 사용


# 페이지 설정
st.set_page_config(page_title="NXT vs KRX", layout="wide")

# 타이틀
st.title("NXT vs KRX")

# 날짜 입력 받기 (사이드바)
st.sidebar.header("조회일자 선택")

# 날짜 선택
selected_date = st.sidebar.date_input(
    "조회할 날짜를 선택하세요",
    datetime.today()
)

# 조회하기 버튼
query_button = st.sidebar.button("📊 데이터 조회하기", type="primary", use_container_width=True)

# 세션 상태 초기화 (앱이 처음 실행될 때)
if 'input_date' not in st.session_state:
    st.session_state.input_date = None
    st.session_state.data_loaded = False

# 버튼 클릭 시 날짜 업데이트 및 데이터 로드 플래그 설정
if query_button:
    st.session_state.input_date = selected_date.strftime('%Y%m%d')
    st.session_state.data_loaded = True
    
    # 사용자에게 로딩 중임을 알림
    st.sidebar.success(f"NXT와 KRX의 홈페이지에서 공개하고 있는 📅 {selected_date.strftime('%Y년 %m월 %d일')} 데이터를 조회합니다! Cache는 5분간 유효합니다.")

# 메인 컨텐츠 영역
if st.session_state.data_loaded:
    # 여기서 input_date 대신 st.session_state.input_date 사용
    input_date = st.session_state.input_date
    

    # 데이터 로딩 표시
    with st.spinner('NXT와 KRX의 홈페이지를 방문하여 데이터를 확인중입니다...'):
        # 넥스트레이드 데이터 가져오기
        @st.cache_data(ttl=300)
        def get_nxt_data(date):
            url = 'https://www.nextrade.co.kr/brdinfoTime/brdinfoTimeList.do'
            
            params = {
                "_search": False,
                "nd": 1741120157913,
                "pageUnit": 900,
                "pageIndex": 1,
                "sidx": "",
                "sord": "asc",
                "scAggDd": date,
                "scMktId": "",
                "searchKeyword": ""
            }
            
            response = requests.post(url, params=params)
            data = response.json()
            
            # 필요한 데이터 리스트 추출
            brdinfo_list = data.get("brdinfoTimeList", [])
            
            # 데이터프레임 전환
            df1 = pd.DataFrame(brdinfo_list)
            
            # 데이터가 없는 경우 처리
            if df1.empty:
                return pd.DataFrame(), None
                
            df_nxt = df1[['isuSrdCd', 'isuAbwdNm', 'mktNm', 'curPrc', 'contrastPrc', 'upDownRate', 
                         'oppr', 'hgpr', 'lwpr', 'accTdQty', 'accTrval', 'tdhlYn']]
            
            df_nxt.columns = ['종목코드', '종목명', '시장구분', '현재가', '대비', '등락률', 
                             '시가', '고가', '저가', '거래량', '거래대금', '거래정지']
            
            # 종목코드 A 제거
            df_nxt['종목코드'] = df_nxt['종목코드'].str.replace('A', '', regex=True)
            
            # 필요한 칼럼만 남기기
            df_nxt = df_nxt[['종목코드', '종목명', '시장구분', '현재가', '등락률', '거래량', '거래대금']]
            
            # 칼럼명 변경
            df_nxt = df_nxt.rename(columns={'현재가': 'NXT현재가', '등락률': 'NXT등락률', 
                                           '거래량': 'NXT거래량', '거래대금':'NXT거래대금'})
            
            # 날짜 정보 가져오기
            now_date = data.get("setTime", "날짜 정보 없음")
            
            return df_nxt, now_date
        
        # KRX 데이터 가져오기
        @st.cache_data(ttl=300)
        def get_krx_data(date):
            gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
            gen_otp = {
                'locale' : 'ko_KR',
                'mktId': 'ALL',
                'trdDd': date,
                'share': '1',
                'money': '1',
                'csvxls_isNo': 'false',
                'name': 'fileDown',
                'url': 'dbms/MDC/STAT/standard/MDCSTAT01501'
            }
            
            headers = {
                'Referer' : 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020201',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            try:
                otp = requests.post(gen_otp_url, gen_otp, headers=headers).text
                down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
                down_content = requests.post(down_url, {'code': otp}, headers=headers)
                
                df_krx = pd.read_csv(BytesIO(down_content.content), encoding='EUC-KR')
                df_krx['시장구분'] = df_krx['시장구분'].replace('KOSDAQ GLOBAL', 'KOSDAQ')
                
                # 필요한 칼럼만 남기기
                df_krx = df_krx[['종목코드', '종가', '등락률', '거래량', '거래대금', '시가총액']]
                
                # 칼럼명 변경하기
                df_krx = df_krx.rename(columns={'종가': 'KRX종가','등락률': 'KRX종가등락률', 
                                              '거래량': 'KRX거래량', '거래대금': 'KRX거래대금'})
                
                return df_krx
            except Exception as e:
                st.error(f"KRX 데이터를 가져오는 중 오류가 발생했습니다: {e}")
                return pd.DataFrame()
        
        # 데이터 가져오기
        df_nxt, now_date = get_nxt_data(input_date)
        
        if df_nxt.empty:
            st.error(f"{input_date} 날짜에 대한 NXT 데이터가 없습니다. 다른 날짜를 선택해주세요.")
            st.stop()
        
        df_krx = get_krx_data(input_date)
        
        if df_krx.empty:
            st.error(f"{input_date} 날짜에 대한 KRX 데이터가 없습니다. 다른 날짜를 선택해주세요.")
            st.stop()
        
        # 데이터 병합 및 비중 계산
        df_agg = pd.merge(df_nxt, df_krx, on='종목코드', how='left')
        df_agg['비중(NXT/KRX)'] = 100 * (df_agg['NXT거래량'] / df_agg['KRX거래량'])
        df_agg['전체거래량'] =df_agg['NXT거래량'] + df_agg['KRX거래량']
        df_agg = df_agg[['종목코드', '종목명', '시장구분', '전체거래량','NXT거래량', 'KRX거래량', '비중(NXT/KRX)', '시가총액']].sort_values(by='비중(NXT/KRX)', ascending=False)
        
        # 전체 거래량 합산 및 비율 계산
        total_nxt_vol = df_agg['NXT거래량'].sum()
        total_krx_vol = df_agg['KRX거래량'].sum()
        nxt_vs_krx_ratio = (total_nxt_vol / total_krx_vol) * 100 if total_krx_vol > 0 else 0
    
    # 데이터 요약 정보 표시
    st.header("데이터 요약")
    st.info(f"📌 {now_date} NXT는 KRX의 거래량 대비 **{nxt_vs_krx_ratio:.2f}%**를 기록했습니다.")
    
    # 데이터프레임 표시
    st.header("종목별 거래량 비교")
    
    # 시장 필터 (라디오 버튼으로 구현)
    market_option = st.radio(
        "시장 선택:",
        ["KOSPI+KOSDAQ", "KOSPI", "KOSDAQ"],
        horizontal=True
    )
    
    # 선택에 따라 필터링
    if market_option == "KOSPI+KOSDAQ":
        filtered_df = df_agg.copy()  # 모든 데이터
    elif market_option == "KOSPI":
        filtered_df = df_agg[df_agg['시장구분'] == 'KOSPI']
    else:  # "KOSDAQ"
        filtered_df = df_agg[df_agg['시장구분'] == 'KOSDAQ']
    
    # 종목 수 표시 (이모티콘 추가)
    st.write(f"📊 종목 수: {len(filtered_df)}개")
    
    # 정렬 안내문 (굵은 글씨로 강조)
    st.markdown("""
    <div style="background-color:#f0f2f6; padding:10px; border-radius:5px; margin:10px 0;">
        <strong style="color:#0066cc; font-size:16px;">📌 표의 칼럼명을 클릭하시면 오름차순/내림차순 정렬할 수 있습니다.</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # 단위 변경
    formatted_df = filtered_df.copy()
    formatted_df['시가총액'] = formatted_df['시가총액'] / 100000000  # 억원 단위로 변환
    
    # st.dataframe에 column_config 적용
    st.dataframe(
        formatted_df,
        column_config={
            'NXT거래량': st.column_config.NumberColumn('NXT거래량', format="%d", help="천 단위 구분자 적용"),
            'KRX거래량': st.column_config.NumberColumn('KRX거래량', format="%d", help="천 단위 구분자 적용"),
            '비중(NXT/KRX)': st.column_config.NumberColumn('비중(NXT/KRX)', format="%.2f", help="소수점 2자리까지 표시"),
            '시가총액': st.column_config.NumberColumn('시가총액(억원)', format="%d", help="억원 단위")
        },
        height=400,
        use_container_width=True
    )
    
    # CSV 다운로드 버튼
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="CSV 데이터 다운로드",
        data=csv,
        file_name=f'nxt_krx_comparison_{input_date}.csv',
        mime='text/csv',
    )
    
    # Plotly 차트 생성
    st.header("KRX 대비 NXT 거래량 비중")
    
    # 차트 옵션
    chart_type = st.radio(
        "차트 유형 선택:",
        ["전체 데이터", "상위 20개 종목만 보기"],
        horizontal=True
    )
    
    # 시장 필터 (라디오 버튼으로 변경)
    market_option_plot = st.radio(
        "(그래프) 시장 선택:",
        ["KOSPI+KOSDAQ", "KOSPI", "KOSDAQ"],
        horizontal=True
    )
    
    # 선택에 따라 필터링
    if market_option_plot == "KOSPI+KOSDAQ":
        filtered_df_plot = df_agg.copy()  # 모든 데이터
    elif market_option_plot == "KOSPI":
        filtered_df_plot = df_agg[df_agg['시장구분'] == 'KOSPI']
    else:  # "KOSDAQ"
        filtered_df_plot = df_agg[df_agg['시장구분'] == 'KOSDAQ']
    
    
    if chart_type == "상위 20개 종목만 보기":
        chart_df = filtered_df_plot.head(20)
    else:
        chart_df = filtered_df_plot
    
    # # 전체 시장 데이터 표시
    market_row = pd.DataFrame({
        '종목명': ['NXT 전체'],
        '시장구분': ['ALL'],
        '비중(NXT/KRX)': [nxt_vs_krx_ratio]
    })
    
    plot_df = pd.concat([market_row[['종목명', '시장구분', '비중(NXT/KRX)']], 
                          chart_df[['종목명', '시장구분', '비중(NXT/KRX)']]])
    
    
    # 색상 맵 설정
    color_map = {'KOSPI': 'crimson', 'KOSDAQ': '#734F96', 'ALL': 'darkgreen'}
    
    # Plotly 바 차트 생성
    fig = px.bar(
        plot_df,
        y='종목명',
        x='비중(NXT/KRX)',
        color='시장구분',
        color_discrete_map=color_map,
        title=f'종목별 KRX 대비 NXT 거래량 비중 ({now_date} 기준)',
        labels={'비중': 'KRX 대비 NXT 거래량 비중 (%)', '종목명': '종목명'},
        height=800,
        template='plotly_white'
    )
    
    # 차트 레이아웃 설정
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title="KRX 대비 NXT 거래량 비중 (%)",
        yaxis_title="종목명",
        font=dict(size=12),
        legend_title="시장구분",
        hovermode="y unified"
    )
    
    # 데이터 레이블 추가
    fig.update_traces(
        texttemplate='%{x:.1f}%',
        textposition='outside'
    )
    
    # 차트 표시
    st.plotly_chart(fig, use_container_width=True)
    
    # 시장별 거래량 분석 추가
    st.header("시장별 NXT 거래량 분석")
    
    # 시장별 거래량 집계
    market_vol = df_agg.groupby('시장구분').agg(
        NXT거래량=('NXT거래량', 'sum'),
        KRX거래량=('KRX거래량', 'sum')
    ).reset_index()
    
    market_vol['비중(NXT/KRX)'] = 100 * (market_vol['NXT거래량'] / market_vol['KRX거래량'])
    
    # 파이 차트
    fig_pie = px.pie(
        market_vol, 
        values='NXT거래량', 
        names='시장구분',
        title='시장별 NXT 거래량 분포',
        color='시장구분',
        color_discrete_map=color_map,
        hover_data=['비중(NXT/KRX)']
    )
    
    fig_pie.update_traces(textinfo='percent+label', hovertemplate='시장: %{label}<br>거래량 비중: %{customdata[0]:.2f}%')
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # 시장별 지표 표시
    cols = st.columns(len(market_vol))
    for i, (_, row) in enumerate(market_vol.iterrows()):
        with cols[i]:
            st.metric(
                f"KRX 대비 NXT의 {row['시장구분']} 거래량 비중", 
                f"{row['비중(NXT/KRX)']:.2f}%",
                delta=None
            )

# 푸터
st.markdown("---")
st.caption("데이터 출처: 넥스트레이드(NXT), 한국거래소(KRX)")
