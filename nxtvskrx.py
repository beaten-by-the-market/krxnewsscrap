import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Streamlit 앱 생성
st.title("KRX vs NXT 비교")

if st.button("오늘의 KRXvsNXT비교"):
    # NXT 데이터 요청
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
    data = response.json()  # JSON 데이터 변환

    if data.get("brdinfoTimeList"):
        now_date = data["brdinfoTimeList"][0].get("nowDd", "날짜 없음")
        now_time = data["brdinfoTimeList"][0].get("nowTime", "시간 없음")
    else:
        now_date, now_time = "날짜 없음", "시간 없음"

    brdinfo_list = data.get("brdinfoTimeList", [])
    
    df_nxt = pd.DataFrame(brdinfo_list)[['isuSrdCd', 'isuAbwdNm', 'mktNm', 'curPrc', 'upDownRate', 'oppr', 'hgpr', 'lwpr', 'accTdQty', 'accTrval', 'tdhlYn']]
    
    df_nxt.columns = ['종목코드', '종목명', '시장구분', '현재가', '등락률', '시가', '고가', '저가', '거래량', '거래대금', '거래정지']
    
    df_nxt['종목코드'] = df_nxt['종목코드'].str.replace('A', '', regex=True)
    
    df_nxt = df_nxt[['종목코드', '종목명', '시장구분', '현재가', '등락률', '거래량', '거래대금']]
    
    df_nxt = df_nxt.rename(columns={'현재가': 'NXT현재가', '등락률': 'NXT등락률', '거래량': 'NXT거래량', '거래대금':'NXT거래대금'})
        
    # KRX 데이터 요청
    gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
    gen_otp = {
        'locale' : 'ko_KR',
        'mktId': 'ALL',
        'trdDd': '20250304',
        'share': '1',
        'money': '1',
        'csvxls_isNo': 'false',
        'name': 'fileDown',
        'url': 'dbms/MDC/STAT/standard/MDCSTAT01501'
    }
    
    headers = {'Referer' : 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020201',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    otp = requests.post(gen_otp_url, gen_otp, headers=headers).text
    down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
    down_content = requests.post(down_url, {'code': otp}, headers=headers)
    
    df_krx = pd.read_csv(BytesIO(down_content.content), encoding='EUC-KR')
    df_krx['시장구분'] = df_krx['시장구분'].replace('KOSDAQ GLOBAL', 'KOSDAQ')
    df_krx = df_krx.rename(columns={'단축코드': '종목코드'})
    
    df_krx = df_krx[['종목코드', '종가', '등락률', '거래량', '거래대금', '시가총액']]
    
    df_krx = df_krx.rename(columns={'종가': 'KRX종가', '등락률': 'KRX종가등락률', '거래량': 'KRX거래량', '거래대금': 'KRX거래대금'})
        
    # 데이터 합치기
    df_agg = pd.merge(df_nxt, df_krx, on='종목코드', how='left')
    
    # KRX 대비 NXT의 거래량 비중을 %로 계산하여 '비중' 칼럼 추가
    df_agg['비중'] = 100 * (df_agg['NXT거래량'] / df_agg['KRX거래량'])
    
    # **추가: 전체 거래량 합산 및 비율 계산**
    total_nxt_vol = df_agg['NXT거래량'].sum()
    total_krx_vol = df_agg['KRX거래량'].sum()
    nxt_vs_krx_ratio = (total_nxt_vol / total_krx_vol) * 100 if total_krx_vol > 0 else 0

    # 상단에 정보 추가
    st.write(f"📌 오늘 NXT는 KRX의 거래량 대비 **{nxt_vs_krx_ratio:.2f}%**를 기록했습니다.")
    st.write(f"📅 NXT 가격 기준 시각: {now_date} {now_time}")
    
    st.dataframe(df_agg)
