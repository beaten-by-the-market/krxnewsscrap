import streamlit as st
import pandas as pd
import requests
from time import sleep
from datetime import timedelta, datetime
from xml_to_dict import XMLtoDict
from io import BytesIO
import urllib.parse
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from krx_data_api import fetch
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# HTTPS 인증서 경고 무시
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 페이지 설정
st.set_page_config(
    page_title="희석주식수 분석 서비스",
    page_icon="📊",
    layout="wide"
)

# XML 파서 초기화
xd = XMLtoDict()

# API 키 설정
api_key = st.secrets["general"]["api_key"]

# 캐시된 데이터 로딩 함수들
@st.cache_data(ttl=3600)  # 1시간 캐시
def load_basic_data():
    """기본 데이터 로딩 (df_inte)"""
    
    # 예탁원 데이터 수집
    mkt_list = ['11', '12']
    df_stock_cust = pd.DataFrame()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, mkt in enumerate(mkt_list):
        status_text.text(f'시장별 종목 데이터 수집 중... ({i+1}/{len(mkt_list)})')
        
        url = f'http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={api_key}&apiId=getShotnByMart&params=MART_TPCD:{mkt}'
        
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            try:
                sleep(1)
                raw = requests.get(url, verify=False, timeout=30)
                raw.raise_for_status()
                
                data_dict = xd.parse(raw.content.decode('utf-8'))
                data_list = data_dict['SeibroAPI']['vector']['data']
                
                records = []
                for item in data_list:
                    record = {
                        'SHOTN_ISIN': item['result']['SHOTN_ISIN']['@value'],
                        'KOR_SECN_NM': item['result']['KOR_SECN_NM']['@value'],
                        'ISSUCO_CUSTNO': item['result']['ISSUCO_CUSTNO']['@value']
                    }
                    records.append(record)
                
                df_stock_cust_loop = pd.DataFrame(records)
                df_stock_cust = pd.concat([df_stock_cust, df_stock_cust_loop])
                success = True
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    sleep(attempt + 1)
                else:
                    st.error(f"시장 {mkt} 데이터 수집 실패")
        
        progress_bar.progress((i + 1) / len(mkt_list) * 0.5)
    
    # 보통주만 필터링
    df_stock_cust_f = df_stock_cust[df_stock_cust['SHOTN_ISIN'].str.endswith('0')].reset_index(drop=True)
    
    # KRX 데이터 수집 (krx-data-api 패키지가 OTP/인증을 처리)
    status_text.text('KRX 종목 정보 수집 중...')

    max_retries = 3
    success = False
    for attempt in range(max_retries):
        try:
            df_listed = fetch("listed_stocks")
            df_listed = df_listed.rename(columns={'단축코드': 'stock_code'})
            success = True
            break
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(attempt + 1)
            else:
                st.error("KRX 데이터 수집 실패")
    
    progress_bar.progress(1.0)
    
    # 데이터 통합
    df_inte = pd.merge(df_stock_cust_f, df_listed, how='left', left_on='SHOTN_ISIN', right_on='stock_code')
    
    status_text.text('데이터 로딩 완료!')
    progress_bar.empty()
    status_text.empty()
    
    return df_inte

def setup_session():
    """크롤링을 위한 세션 설정"""
    # 세션 객체 생성
    session = requests.Session()
    
    # SSL 검증 비활성화 
    session.verify = False
    
    # 공통 헤더 설정
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    
    # 메인 페이지 방문하여 세션 설정
    main_url = "https://seibro.or.kr/websquare/control.jsp?w2xPath=/IPORTAL/user/bond/BIP_CNTS03004V.xml&menuNo=415"
    response = session.get(main_url)
    print(f"메인 페이지 접근 상태: {response.status_code}")
    
    return session

def get_stock_isu_bond(ISU_CD, api_key):
    """주식관련사채 정보 조회"""
    url = f'http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={api_key}&apiId=getXrcStkStatInfo&params=XRC_STK_ISIN:{ISU_CD}'
    raw = requests.get(url, verify=False)
    sleep(0.2)
    data_dict = xd.parse(raw.content.decode('utf-8'))
    result = data_dict['SeibroAPI']['vector']['@result']
    
    if result == '0':
        df_stock_isu_b = pd.DataFrame()
    elif result == '1':
        data_list = data_dict['SeibroAPI']['vector']['data']
        df_stock_isu_b = pd.DataFrame(data_list['result'])
        df_stock_isu_b.rename(columns={'XRC_STK_ISIN': 'ISU_CD'}, inplace=True)
    else:
        data_list = data_dict['SeibroAPI']['vector']['data']
        df_stock_isu_b = pd.DataFrame([{k: v['@value'] for k, v in item['result'].items()} for item in data_list])
        df_stock_isu_b.rename(columns={'XRC_STK_ISIN': 'ISU_CD'}, inplace=True)
    
    return df_stock_isu_b

def get_df_from_xml(response):
    """XML 응답에서 데이터프레임 생성"""
    try:
        data_dict = xd.parse(response.content.decode('utf-8'))
        vector_result = data_dict['vector'].get('@result', '0')
        
        if vector_result == '0':
            return pd.DataFrame()
        elif vector_result == '1':
            data_section = data_dict['vector']['data']
            if isinstance(data_section, list):
                all_records = []
                for data_item in data_section:
                    result_data = data_item['result']
                    record = {k: v['@value'] for k, v in result_data.items()}
                    all_records.append(record)
                return pd.DataFrame(all_records)
            else:
                result_data = data_section['result']
                record = {k: v['@value'] for k, v in result_data.items()}
                return pd.DataFrame([record])
        else:
            data_section = data_dict['vector']['data']
            if isinstance(data_section, list):
                all_records = []
                for data_item in data_section:
                    result_data = data_item['result']
                    record = {k: v['@value'] for k, v in result_data.items()}
                    all_records.append(record)
                return pd.DataFrame(all_records)
            else:
                result_data = data_section['result']
                record = {k: v['@value'] for k, v in result_data.items()}
                return pd.DataFrame([record])
    except Exception as e:
        st.error(f"XML 파싱 오류: {e}")
        return pd.DataFrame()

def get_deposit(cust_no, api_key):
    """보호예수 정보 조회"""
    end_dt_tmp = datetime.today()
    end_dt = end_dt_tmp.strftime('%Y%m%d')
    start_dt_tmp = end_dt_tmp.replace(year=end_dt_tmp.year - 1) + timedelta(days=1)
    start_dt = start_dt_tmp.strftime('%Y%m%d')
    
    end_dt2_tmp = start_dt_tmp - timedelta(days=1)
    end_dt2 = end_dt2_tmp.strftime('%Y%m%d')
    start_dt2_tmp = end_dt2_tmp.replace(year=end_dt2_tmp.year - 1) + timedelta(days=1)
    start_dt2 = start_dt2_tmp.strftime('%Y%m%d')
    
    end_dt3_tmp = start_dt2_tmp - timedelta(days=1)
    end_dt3 = end_dt3_tmp.strftime('%Y%m%d')
    start_dt3_tmp = end_dt3_tmp.replace(year=end_dt3_tmp.year - 1) + timedelta(days=1)
    start_dt3 = start_dt3_tmp.strftime('%Y%m%d')
    
    start_date_list = [start_dt, start_dt2, start_dt3]
    end_date_list = [end_dt, end_dt2, end_dt3]
    
    biz_list = ['1', '2']
    df_dict = {'code': ['00', '01', '02', '03', '04', '43', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '44', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '48', '41', '42', '45', '46', '49', '47', '50', '51', '52', '90', '99', '53', '54', '55'],
               '보호예수사유': ['해당없음', '일반', '모집(전매제한)', '최대주주(상장)', '최대주주(코스닥)', '최대주주(기술성장기업)', '투자회사(상장)', '초과유상증자', '지정취소', '질권담보', '등록주선인', '외국인양수(변동제한)', '벤처금융', '기관투자가', '합병(상장)', '합병(코스닥)', '부동산(상장)', '부동산(코스닥)', '법원M&A', '주식교환(코스닥)', '벤처금융(주식교환)', '벤처금융(합병)', '기관투자가(합병)', '기관투자가(코넥스)', '기관투자가(주식교환)', '제3자배정최대주주(코스닥)', '선박(상장)', '채권기관협의회', '주식교환(상장)', '영업자산양도&제3자배정(상장)', '영업자산양도&제3자배정(코스닥)', '제3자배정유상증자(상장)', '제3자배정유상증자(코스닥)', '최대주주(제3자배정)', 'SPAC(상장)', 'SPAC(코스닥)', 'SPAC합병(상장)', 'SPAC합병(코스닥)', '명목회사(상장)', '명목회사(코스닥)', '자발적보호예수', '우회상장', '상장주선인(국내기업)', '상장주선인(외국기업)', '전매제한', '기타(특정금전신탁편입등)', '크라우드펀딩', '크라우드펀딩(최대주주)', '모집(전매제한)-크라우드펀딩전문투자자', '주관회사(금투협)', '상장주선인(50%미만)', '상장주선인(50%이상)', '최대주주변경(법인또는', '기타의무예수', '기타', '상장적격성실질심사', '기타보호예시필요주주', '주식매수선택권']}
    df_code_list = pd.DataFrame(df_dict)
    
    df_deposit_f = pd.DataFrame()
    
    for biz in biz_list:
        for start_dt, end_dt in zip(start_date_list, end_date_list):
            url = f'http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={api_key}&apiId=getSafeDpDutyDepoStatus&params=ISSUCO_CUSTNO:{cust_no},BEGIN_DT:{start_dt},EXPRY_DT:{end_dt},BIZ_TPCD:{biz}'
            raw = requests.get(url, verify=False)
            data_dict = xd.parse(raw.content.decode('utf-8'))
            result = data_dict['SeibroAPI']['vector']['@result']
            
            if result == '0':
                df_deposit = pd.DataFrame()
            elif result == '1':
                data_list = data_dict['SeibroAPI']['vector']['data']
                df_deposit = pd.DataFrame(data_list['result'])
            else:
                data_list = data_dict['SeibroAPI']['vector']['data']
                df_deposit = pd.DataFrame([{k: v['@value'] for k, v in item['result'].items()} for item in data_list])
            
            if len(df_deposit) > 0:
                df_deposit = pd.merge(df_deposit, df_code_list, how='left', left_on='DUTY_SAFEDP_RACD', right_on='code')
                df_deposit.drop('DUTY_SAFEDP_RACD', axis=1, inplace=True)
                
                df_deposit['종목종류'] = df_deposit['SECN_KACD']
                df_deposit['단축코드'] = df_deposit['SHOTN_ISIN']
                df_deposit['시장구분'] = np.where(df_deposit['MART_TPCD'] == '11', '유가',
                                                 np.where(df_deposit['MART_TPCD'] == '12', '코스닥',
                                                          np.where(df_deposit['MART_TPCD'] == '14', '코넥스', df_deposit['MART_TPCD'])))
                df_deposit['업무구분'] = np.where(df_deposit['OCCR_SEQ'] == '1', '예수',
                                                 np.where(df_deposit['OCCR_SEQ'] == '2', '반환', df_deposit['OCCR_SEQ']))
                df_deposit['예수일'] = df_deposit['SAFEDP_DT']
                df_deposit['예수주식수'] = df_deposit['SAFEDP_QTY']
                df_deposit['반환일'] = df_deposit['RETURN_DT']
                df_deposit['반환주식수'] = df_deposit['RETURN_QTY']
                df_deposit['총발행주식수'] = df_deposit['TOTAL_STK_CNT']
                
                df_deposit = df_deposit[['ISSUCO_CUSTNO', '단축코드', 'KOR_SECN_NM', '종목종류', '시장구분', '업무구분', '보호예수사유', '예수일', '예수주식수', '반환일', '반환주식수', '총발행주식수']]
                
                int_col = ['예수주식수', '반환주식수', '총발행주식수']
                date_col = ['예수일', '반환일']
                
                df_deposit[date_col] = df_deposit[date_col].applymap(lambda x: pd.to_datetime(x, format='%Y%m%d', errors='ignore'))
                df_deposit[int_col] = df_deposit[int_col].astype(np.int64, errors='ignore')
                
                df_deposit_f = pd.concat([df_deposit_f, df_deposit])
    
    return df_deposit_f

def stock_change(stock_code, api_key):
    """주식증감내역 조회"""
    url = f'http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={api_key}&apiId=getStkIncdecDetails&params=SHOTN_ISIN:{stock_code}'
    raw = requests.get(url, verify=False)
    sleep(0.2)
    data_dict = xd.parse(raw.content.decode('utf-8'))
    result = data_dict['SeibroAPI']['vector']['@result']
    
    if result == '0':
        df_stock_change = pd.DataFrame()
    elif result == '1':
        data_list = data_dict['SeibroAPI']['vector']['data']
        df_stock_change = pd.DataFrame(data_list['result'])
    else:
        data_list = data_dict['SeibroAPI']['vector']['data']
        df_stock_change = pd.DataFrame([{k: v['@value'] for k, v in item['result'].items()} for item in data_list])
    
    return df_stock_change

def create_pie_chart(selected_stock, df_pipeline2, df_deposit_data, chart_type):
    """파이차트 생성 함수"""
    try:
        total_shares = int(selected_stock['상장주식수'])
        
        # 예수주식수 합계 계산
        if not df_deposit_data.empty and '예수주식수' in df_deposit_data.columns:
            total_deposit_shares = int(df_deposit_data['의무보유중_주식수'].sum())
            
            # 데이터 검증: 예수주식수가 상장주식수를 초과하는지 확인
            if total_deposit_shares > total_shares:
                st.warning("⚠️ 데이터 확인 필요: 예수주식수가 상장주식수를 초과합니다.")
                return None
        else:
            total_deposit_shares = 0
        
        # 전환가능주식수 계산
        xrc_shares = 0
        if not df_pipeline2.empty and '전환/행사가능_수량' in df_pipeline2.columns:
            xrc_shares = int(df_pipeline2['전환/행사가능_수량'].sum())
        
        # 파이차트 데이터 준비
        labels = []
        values = []
        colors = []
        hover_texts = []
        
        # 자유유통주식수
        free_float_shares = total_shares - total_deposit_shares - xrc_shares
        if free_float_shares > 0:
            labels.append('유통주식')
            values.append(free_float_shares)
            colors.append('#636EFA')
            hover_texts.append(f'유통주식: {free_float_shares:,}주')
        
        # 전환가능주식수 (개별 사채별로)
        if not df_pipeline2.empty and '전환/행사가능_수량' in df_pipeline2.columns:
            color_palette = ['#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692']
            for i, (idx, row) in enumerate(df_pipeline2.iterrows()):
                if pd.notna(row['전환/행사가능_수량']) and row['전환/행사가능_수량'] > 0:
                    labels.append(f"전환가능주식({row['종목명'][:10]}...)")
                    values.append(int(row['전환/행사가능_수량']))
                    colors.append(color_palette[i % len(color_palette)])
                    hover_texts.append(f"{row['종목명']}: {int(row['전환/행사가능_수량']):,}주")
        
        # 의무보유주식수
        if total_deposit_shares > 0:
            chart_label = "의무보유주식" if chart_type == "필터 없이 조회" else "의무보유주식(장기제외)"
            labels.append(chart_label)
            values.append(total_deposit_shares)
            colors.append('#FECB52')
            hover_texts.append(f'{chart_label}: {total_deposit_shares:,}주')
        
        if not values:
            st.info("표시할 데이터가 없습니다.")
            return None
        
        # 파이차트 생성
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            textinfo='label+percent',
            hovertext=hover_texts,
            hoverinfo='text'
        )])
        
        fig.update_layout(
            title=f"📊 {selected_stock['한글 종목약명']} 주식구조 분석 ({chart_type})",
            title_x=0.5,
            showlegend=True,
            height=500
        )
        
        return fig
        
    except Exception as e:
        st.error(f"파이차트 생성 중 오류 발생: {str(e)}")
        return None

# 메인 앱
def main():
    st.title("📊 희석주식수 분석 서비스")
    st.markdown("---")
    
    # 세션 상태 초기화
    if 'analysis_completed' not in st.session_state:
        st.session_state.analysis_completed = False
    
    # 데이터 로딩
    if 'df_inte' not in st.session_state:
        with st.spinner('기본 데이터를 로딩하는 중...'):
            st.session_state.df_inte = load_basic_data()
    
    df_inte = st.session_state.df_inte
    
    # 메인 페이지에서 검색 옵션 제공
    st.subheader("🔍 종목 검색")
    
    # 검색 방식 선택
    search_method = st.selectbox(
        "검색 방식을 선택하세요:",
        ["회사명으로 검색", "종목코드로 검색"]
    )
    
    # 검색 입력
    if search_method == "종목코드로 검색":
        search_query = st.text_input("종목코드를 입력하세요 (예: 000020):", "")
        if search_query:
            filtered_df = df_inte[df_inte['SHOTN_ISIN'].str.contains(search_query, na=False)]
    else:
        search_query = st.text_input("회사명을 입력하세요 (예: 삼성전자):", "")
        if search_query:
            filtered_df = df_inte[df_inte['한글 종목약명'].str.contains(search_query, na=False)]
    
    # 검색 결과 표시
    if search_query:
        if len(filtered_df) == 0:
            st.warning("검색 결과가 없습니다.")
        else:
            st.subheader("🔍 검색 결과")
            
            # 검색 결과 선택
            if len(filtered_df) == 1:
                selected_stock = filtered_df.iloc[0]
                st.success(f"**{selected_stock['한글 종목약명']} ({selected_stock['SHOTN_ISIN']})**")
            else:
                st.info(f"총 {len(filtered_df)}개의 종목이 검색되었습니다.")
                
                # 선택 옵션 생성
                options = []
                for idx, row in filtered_df.iterrows():
                    options.append(f"{row['한글 종목약명']} ({row['SHOTN_ISIN']})")
                
                selected_option = st.selectbox("분석할 종목을 선택하세요:", options)
                
                if selected_option:
                    selected_idx = options.index(selected_option)
                    selected_stock = filtered_df.iloc[selected_idx]
            
            # 기본 정보 표시
            if 'selected_stock' in locals():
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("상장일", selected_stock['상장일'])
                with col2:
                    st.metric("시장구분", selected_stock['시장구분'])
                with col3:
                    st.metric("상장주식수", f"{selected_stock['상장주식수']:,}주")
                
                # 희석주식수 확인 버튼
                if st.button("🔍 희석주식수 확인", type="primary"):
                    with st.spinner('희석주식수 정보를 조회하는 중...'):
                        try:
                            # 필요한 데이터 수집
                            search_item = selected_stock['SHOTN_ISIN']
                            search_item_isin = selected_stock['표준코드']
                            cust_no_dep = selected_stock['ISSUCO_CUSTNO']
                            
                            # 주식관련사채 정보
                            df_stock_isu_b = get_stock_isu_bond(search_item_isin, api_key)
                            
                            if not df_stock_isu_b.empty:
                                # 크롤링을 위한 세션 설정 (필수)
                                session = setup_session()
                                
                                # 기본정보 수집
                                df_basic = pd.DataFrame()
                                df_xrc_stock = pd.DataFrame()
                                
                                for secn_isin, secn_nm_kor in zip(df_stock_isu_b['BOND_ISIN'], df_stock_isu_b['BOND_SECN_NM']):
                                    # 종목명 인코딩
                                    secn_nm = urllib.parse.quote(secn_nm_kor)
                                    
                                    # 기본정보 API 호출
                                    api_url = "https://seibro.or.kr/websquare/engine/proworks/callServletService.jsp"
                                    api_headers = {
                                        "Content-Type": 'application/xml; charset="UTF-8"',
                                        "Accept": "application/xml",
                                        "Origin": "https://seibro.or.kr",
                                        "Referer": "https://seibro.or.kr/websquare/control.jsp?w2xPath=/IPORTAL/user/bond/BIP_CNTS03004V.xml&menuNo=415",
                                        "Submissionid": "submission_issuInfoViewEL1"
                                    }
                                    xml_data = f'<reqParam action="issuInfoViewEL1" task="ksd.safe.bip.cnts.bone.process.BondSecnDetailPTask"><ISIN value="{secn_isin}"/></reqParam>'
                                    
                                    try:
                                        response = session.post(api_url, headers=api_headers, data=xml_data.encode("utf-8"), timeout=30)
                                        response.raise_for_status()
                                        df_loop = get_df_from_xml(response)
                                        df_basic = pd.concat([df_basic, df_loop])
                                        sleep(0.5)
                                    except Exception as e:
                                        print(f"기본정보 API 호출 실패: {e}")
                                        pass
                                    
                                    # 주식옵션 API 호출
                                    api_headers_xrc = {
                                        "Content-Type": 'application/xml; charset="UTF-8"',
                                        "Accept": "application/xml",
                                        "Origin": "https://seibro.or.kr",
                                        "Referer": f"https://seibro.or.kr/websquare/control.jsp?w2xPath=/IPORTAL/user/bond/BIP_CNTS03004V.xml&ISIN={secn_isin}&KOR_SECN_NM={secn_nm}&menuNo=415",
                                        "Submissionid": "submission_exerInfoView"
                                    }
                                    xml_data_xrc = f'<reqParam action="exerInfoView" task="ksd.safe.bip.cnts.bone.process.BondSecnDetailPTask"><ISIN value="{secn_isin}"/></reqParam>'
                                    
                                    try:
                                        response = session.post(api_url, headers=api_headers_xrc, data=xml_data_xrc.encode("utf-8"), timeout=30)
                                        response.raise_for_status()
                                        df_loop = get_df_from_xml(response)
                                        df_loop['BOND_ISIN'] = secn_isin
                                        df_xrc_stock = pd.concat([df_xrc_stock, df_loop])
                                        sleep(0.5)
                                    except Exception as e:
                                        print(f"주식옵션 API 호출 실패: {e}")
                                        pass
                                
                                # 데이터 통합
                                if not df_basic.empty:
                                    df_basic.rename(columns={'ISIN': 'BOND_ISIN'}, inplace=True)
                                    df_pipeline = df_stock_isu_b.merge(df_basic, how='left', on='BOND_ISIN')
                                    df_pipeline = df_pipeline.merge(df_xrc_stock, how='left', on='BOND_ISIN')
                                    
                                    df_pipeline2 = df_pipeline[['BOND_ISIN', 'BOND_SECN_NM', 'BOND_KIND_NM',
                                                                'ISSU_DT', 'XPIR_DT', 'RECU_WHCD_NM',
                                                                'PARTICUL_BOND_KIND', 'ISU_CD',
                                                                'FIRST_ISSU_AMT', 'ISSU_REMA', 'XRC_PRICE_y']].copy()
                                    
                                    # 전환가능 주식수 계산
                                    if 'XRC_PRICE_y' in df_pipeline2.columns and 'ISSU_REMA' in df_pipeline2.columns:
                                        df_pipeline2['XRC_NUM_STOCK'] = df_pipeline2['ISSU_REMA'].astype(float) // df_pipeline2['XRC_PRICE_y'].astype(float)
                                        
                                    # 필요한 칼럼만 남기기
                                    df_pipeline2 = df_pipeline2[['BOND_SECN_NM', 'RECU_WHCD_NM', 'PARTICUL_BOND_KIND', 'ISSU_DT', 'XPIR_DT',
                                           'FIRST_ISSU_AMT',
                                           'ISSU_REMA', 'XRC_PRICE_y', 'XRC_NUM_STOCK']]
                                    
                                    # 칼럼명 수정
                                    df_pipeline2.columns = ['종목명','발행방법','종류','발행일','만기일','발행금액','미상환잔액','전환/행사가','전환/행사가능_수량']

                                else:
                                    df_pipeline2 = pd.DataFrame()
                            else:
                                df_pipeline2 = pd.DataFrame()
                            
                            # 의무보유 정보 수집
                            df_depo = get_deposit(cust_no_dep, api_key)
                            
                            if not df_depo.empty:
                                # 예수/반환 분리
                                # 예수와 반환을 별도로 처리한 후 병합
                                # 예수 데이터만 추출
                                df_deposit = df_depo[df_depo['업무구분'] == '예수'].copy()
                                
                                # 반환 데이터만 추출  
                                df_return = df_depo[df_depo['업무구분'] == '반환'].copy()
                                
                                # 숫자 변환 (예수 데이터)
                                df_deposit['예수주식수'] = pd.to_numeric(df_deposit['예수주식수'], errors='coerce').fillna(0)
                                
                                # 숫자 변환 (반환 데이터)
                                df_return['반환주식수'] = pd.to_numeric(df_return['반환주식수'], errors='coerce').fillna(0)
                                
                                # 예수 데이터 그룹화
                                df_deposit_grouped = df_deposit.groupby(['보호예수사유', '예수일']).agg({
                                    '예수주식수': 'sum',
                                    'ISSUCO_CUSTNO': 'first',
                                    '단축코드': 'first', 
                                    'KOR_SECN_NM': 'first',
                                    '종목종류': 'first',
                                    '시장구분': 'first'
                                }).reset_index()
                                
                                # 반환 데이터 그룹화 (반환일 기준)
                                df_return_grouped = df_return.groupby(['보호예수사유', '예수일']).agg({
                                    '반환주식수': 'sum'
                                }).reset_index()
                                
                                
                                # 반환데이터를 예수일에 맞게 합치기
                                df_depo2 = pd.merge(
                                    df_deposit_grouped,
                                    df_return_grouped,
                                    how = 'left',
                                    left_on=['예수일', '보호예수사유'],
                                    right_on=['예수일', '보호예수사유'],
                                    suffixes=('_예수', '_반환')
                                )
                                
                                # 반환주식수가 없는 경우 0으로 채우기
                                df_depo2['반환주식수'] = df_depo2['반환주식수'].fillna(0)
                                
                                # 반환 후 잔여수량
                                df_depo2['의무보유중_주식수'] = df_depo2['예수주식수'] -df_depo2['반환주식수']

                                # 오늘 날짜 설정
                                today = datetime.now()
                                
                                # 예수일 컬럼을 datetime 타입으로 변환
                                df_depo2['예수일'] = pd.to_datetime(df_depo2['예수일'])
                                
                                # 예수일로부터 오늘까지 기간 계산 (일 단위)
                                df_depo2['기간_일수'] = (today - df_depo2['예수일']).dt.days
                                
                                # 조건: 기간이 365일 초과
                                # 통상 의무보유기간이 1년을 넘는 경우가 없으므로, 
                                # 1년을 넘은 것을 판별(넉넉히 380일로 함)
                                condition1 = (df_depo2['기간_일수'] > 380)&(df_depo2['의무보유중_주식수'] != 0)
                                
                                # 장기미반환 칼럼추가
                                df_depo2['장기미반환 여부'] = condition1.apply(lambda x: '장기미반환' if x else '-')
                                
                                # 기간_일수 컬럼 제거
                                df_depo2 = df_depo2.drop('기간_일수', axis=1)
                                
                                # 칼럼 형태 변경
                                df_depo2['예수일'] = df_depo2['예수일'].dt.strftime('%Y-%m-%d')
                                
                                # 필요한 칼럼만 남기기
                                df_depo2 = df_depo2[['장기미반환 여부', '보호예수사유', '예수일', '예수주식수',  '반환주식수', '의무보유중_주식수']]
                                
                                # 장기미반환 제외한 데이터프레임
                                df_depo_safe = df_depo2[df_depo2['장기미반환 여부']== '-']
                                
                                # 주식증감내역 확인
                                if len(df_depo2) - len(df_depo_safe) > 0:
                                    df_s_change = stock_change(search_item, api_key)
                                    decrease_list = ['자본감소', '무상소각', '이익소각', '액면병합', '액면분할']
                                    df_s_change_fil = df_s_change[df_s_change['SECN_ISSU_NM'].isin(decrease_list)]
                                    # 필요한 칼럼만 남기기
                                    df_s_change_fil = df_s_change_fil[['SECN_ISSU_NM', 'SECN_ISSU_NTIMES', 'ISSU_DT','LIST_DT','ISSU_QTY']]
                                    # 칼럼명 수정
                                    df_s_change_fil.columns = ['발행사유','발행회차','발행일','상장일','발행수량']
                                else:
                                    df_s_change_fil = pd.DataFrame()
                            else:
                                df_depo2 = pd.DataFrame()
                                df_depo_safe = pd.DataFrame()
                                df_s_change_fil = pd.DataFrame()
                            
                            # 분석 데이터를 세션 상태에 저장 (항상 업데이트)
                            st.session_state.analysis_data = {
                                'df_pipeline2': df_pipeline2,
                                'df_depo2': df_depo2,
                                'df_depo_safe':df_depo_safe,
                                'df_s_change_fil': df_s_change_fil,
                                'selected_stock': selected_stock
                            }
                            st.session_state.analysis_completed = True
                            
                        except Exception as e:
                            st.error(f"희석주식수 분석 중 오류가 발생했습니다: {str(e)}")
                
                # 분석이 완료된 경우 결과 표시 (버튼 밖에서)
                if st.session_state.analysis_completed and 'analysis_data' in st.session_state:
                    st.markdown("---")
                    st.subheader("📊 희석주식수 분석 결과")
                    
                    # 세션 상태에서 데이터 가져오기
                    analysis_data = st.session_state.analysis_data
                    df_pipeline2 = analysis_data['df_pipeline2']
                    df_depo2 = analysis_data['df_depo2'] 
                    df_depo_safe = analysis_data['df_depo_safe'] 
                    df_s_change_fil = analysis_data['df_s_change_fil']
                    stored_selected_stock = analysis_data['selected_stock']
                    
                    # 라디오 버튼으로 차트 옵션 선택
                    chart_option = st.radio(
                        "📈 분석 옵션을 선택하세요:",
                        ["필터 없이 조회", "장기 미반환 데이터 제거 후 조회"],
                        horizontal=True,
                        key="chart_option_radio"
                    )
                    
                    # 선택된 옵션에 따라 파이차트 생성
                    if chart_option == "필터 없이 조회":
                        fig = create_pie_chart(stored_selected_stock, df_pipeline2, df_depo2, chart_option)
                    else:
                        fig = create_pie_chart(stored_selected_stock, df_pipeline2, df_depo_safe, chart_option)
                    
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # 주식관련 사채권 발행 현황
                    st.markdown("### 📈 주식관련 사채권 발행 현황")
                    if not df_pipeline2.empty:
                        st.dataframe(df_pipeline2, use_container_width=True)
                    else:
                        st.info("주식관련 사채권 발행 현황이 없습니다.")
                    
                    # 의무보유 관련 데이터 - 항상 표시
                    st.markdown("### 🔒 의무보유 관련 정보")
                    
                    # 선택된 차트 옵션에 따라 다른 데이터 표시
                    st.markdown("#### 전체 의무보유 데이터(최근 3년)")
                    if not df_depo2.empty:
                        st.dataframe(df_depo2, use_container_width=True)
                    else:
                        st.info("의무보유 중인 주식수가 없습니다.")
                    
                    # 주식증감내역은 장기 미반환 데이터가 있을 때만 표시
                    if len(df_depo2) - len(df_depo_safe) > 0:
                        st.markdown("#### 주식증감내역(장기미반환 검증용)")
                        st.write('(참고) 예탁원 데이터에서는 자본감소, 액면병합 등이 있을 때 기존 의무보유 데이터는 그대로 남고, 새로운 의무보유 데이터가 생성됩니다.')
                        if not df_s_change_fil.empty:
                            st.dataframe(df_s_change_fil, use_container_width=True)
                        else:
                            st.info("주식감소 이벤트가 없습니다.")
    
    # 앱 정보
    st.markdown("---")
    st.markdown("**💡 사용 가이드**")
    st.markdown("1. 검색 방식을 선택하세요")
    st.markdown("2. 종목코드 또는 회사명을 입력하여 검색하세요")
    st.markdown("3. 검색 결과에서 원하는 종목을 선택하세요")
    st.markdown("4. '희석주식수 확인' 버튼을 클릭하여 상세 분석을 확인하세요")

if __name__ == "__main__":
    main()
