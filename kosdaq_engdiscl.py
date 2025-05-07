import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time
import mysql.connector

# 페이지 설정 (wide 모드로 설정)
st.set_page_config(
    page_title="오늘의 코스닥 번역대상 공시",
    layout="wide",  # 화면을 넓게 사용
    initial_sidebar_state="collapsed"  # 사이드바 초기 상태를 접힌 상태로 설정
)

# 제목 설정
st.title('오늘의 코스닥 번역대상 공시')

#-----------------------------------------------------------
# 환경변수 설정-streamlit
#-----------------------------------------------------------
db_config = {
    'user': st.secrets["general"]["db_user"],
    'password': st.secrets["general"]["db_password"],
    'host': st.secrets["general"]["db_host"],
    'port': st.secrets["general"]["db_port"],
    'database': st.secrets["general"]["db_name"],
}

# 데이터사용
def load_data_from_db():
    connection = None
    try:
        # 데이터베이스 연결
        connection = mysql.connector.connect(**db_config)

        if connection.is_connected():
            print("Connected to MySQL database")

            # 커서 생성
            cursor = connection.cursor()

            # 데이터 가져오기
            query = "SELECT * FROM kosdaq_report"
            cursor.execute(query)

            # 데이터프레임 초기화
            disc = pd.DataFrame(columns=[desc[0] for desc in cursor.description])

            # 배치로 데이터를 가져오는 로직 (이 부분은 그대로 유지)
            batch_size = 1000  # 한 번에 가져올 행의 수
            rows_fetched = 0

            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                disc = pd.concat([disc, pd.DataFrame(rows, columns=disc.columns)], ignore_index=True)

                rows_fetched += len(rows)

            return disc

    except mysql.connector.Error as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()  # 빈 데이터프레임 반환

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

# SQL 데이터를 최초 1회만 로드
# 지원대상 데이터 리스트 (df_data 정의)
df_data = load_data_from_db()

# 컬럼명 설정
df_data.columns = ["서식코드", "서식명", "대분류", "구분", "업데이트일"]

# DataFrame 설정
df_svc = df_data

# 데이터사용
def load_data_from_db_name():
    connection = None
    try:
        # 데이터베이스 연결
        connection = mysql.connector.connect(**db_config)

        if connection.is_connected():
            print("Connected to MySQL database")

            # 커서 생성
            cursor = connection.cursor()

            # 데이터 가져오기
            query = "SELECT * FROM kosdaq_companies"
            cursor.execute(query)

            # 데이터프레임 초기화
            disc = pd.DataFrame(columns=[desc[0] for desc in cursor.description])

            # 배치로 데이터를 가져오는 로직 (이 부분은 그대로 유지)
            batch_size = 1000  # 한 번에 가져올 행의 수
            rows_fetched = 0

            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                disc = pd.concat([disc, pd.DataFrame(rows, columns=disc.columns)], ignore_index=True)

                rows_fetched += len(rows)

            return disc

    except mysql.connector.Error as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()  # 빈 데이터프레임 반환

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

# SQL 데이터를 최초 1회만 로드
# 지원대상 데이터 리스트 (df_data 정의)
df_data = load_data_from_db_name()

# 컬럼명 설정
df_data.columns = ["회사코드", "회사명", "상장여부", "업데이트일"]

# DataFrame 생성
df_listed = df_data

# 세션 상태에 df_listed 저장 (초기 로드 시)
if 'df_listed' not in st.session_state:
    st.session_state.df_listed = df_listed.copy()

# 회사 추가 콜백 함수
def add_company():
    if st.session_state.company_code and st.session_state.company_name:
        # 새 행 추가
        new_row = pd.DataFrame({
            "회사코드": [st.session_state.company_code],
            "회사명": [st.session_state.company_name],
            "상장여부": ["상장"]
        })
        # 세션 상태의 데이터프레임에 추가
        st.session_state.df_listed = pd.concat([st.session_state.df_listed, new_row], ignore_index=True)
        # 입력 필드 초기화
        st.session_state.company_code = ""
        st.session_state.company_name = ""

# 3개의 칼럼 생성
col1, col2, col3 = st.columns(3)

# 세션 상태에 df_svc 저장 (초기 로드 시)
if 'df_svc' not in st.session_state:
    st.session_state.df_svc = df_svc.copy()

# 첫번째 칼럼: 지원대상공시서식기준
with col1:
    st.subheader('지원대상 공시서식')
    # 세션 상태의 df_svc를 사용
    if 'df_svc' in st.session_state:
        st.write(str(len(st.session_state.df_svc))+'개')
        st.dataframe(st.session_state.df_svc)
    else:
        st.write(str(len(df_svc))+'개')
        st.dataframe(df_svc)

# 두번째 칼럼: 지원대상 회사목록
with col2:
    st.subheader('지원대상 회사 목록')
    st.write(str(len(st.session_state.df_listed))+'사')
    st.dataframe(st.session_state.df_listed)

# 세번째 칼럼: 파일 업로드 및 DB 저장 기능
with col3:
    st.subheader('지원대상 서식 업로드')
    
    # 1. 지원대상 공시서식 업로드 섹션
    st.markdown("##### 칼럼이 4개짜리인 엑셀파일로 올려주세요")
    st.markdown("##### ('업데이트일'칼럼 삭제필수)")

    disclosure_file = st.file_uploader("공시서식 Excel 파일 업로드", type=["xlsx", "xls"], key="disclosure_uploader")
    
    if disclosure_file is not None:
        try:
            # Excel 파일 읽기
            df_disc = pd.read_excel(disclosure_file, dtype=str)
            
            # 오늘날짜 설정
            today = (datetime.today()).strftime('%Y%m%d')
            df_disc['update_date'] = today
            
            # 칼럼명 설정
            df_disc.columns = ['서식코드', '서식명', '대분류', '구분', 'update_date']
            
            # 데이터 미리보기 표시
            st.write("업로드된 공시서식 데이터:")
            st.dataframe(df_disc)
            
            # 업로드 확인 버튼
            if st.button("공시서식 임시 적용하기", key="apply_disclosure"):
                # 세션 상태에 df_svc 업데이트
                st.session_state.df_svc = df_disc.copy()
                st.success("지원대상 공시서식이 임시 업데이트되었습니다.")
                st.rerun()  # 페이지 새로고침
                
            # DB에 영구반영하기 버튼
            if st.button("공시서식 DB에 영구반영하기", key="save_disclosure_to_db"):
                try:
                    # Create a connection to the database
                    connection = mysql.connector.connect(**db_config)

                    if connection.is_connected():
                        st.info("MySQL 데이터베이스에 연결되었습니다.")

                        # Create a cursor object to interact with the database
                        cursor = connection.cursor()
                        
                        # 스키마 이용
                        cursor.execute("USE englishkind")
                        
                        cursor.execute("DROP TABLE IF EXISTS kosdaq_report")
                        
                        # 유가 번역대상 보고서 테이블 생성
                        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS kosdaq_report (
                            form_code VARCHAR(5) PRIMARY KEY,
                            form_name VARCHAR(255) NOT NULL,
                            form_type VARCHAR(255) NOT NULL,
                            institution VARCHAR(255) NOT NULL,
                            update_date VARCHAR(8) NOT NULL
                        )
                        """)
                        
                        # Insert the data from the DataFrame into the table using parameterized queries
                        insert_query = """INSERT INTO kosdaq_report (
                        form_code, form_name, form_type, institution, update_date) 
                        VALUES (%s, %s, %s, %s, %s)
                        """
                        
                        # Streamlit용 진행 표시줄
                        progress_bar = st.progress(0)
                        for i, (_, row) in enumerate(df_disc.iterrows()):
                            row = row.fillna("-")
                            cursor.execute(insert_query, (row['서식코드'], row['서식명'], row['대분류'], row['구분'], row['update_date']))
                            progress_bar.progress((i + 1) / len(df_disc))

                        # Commit the changes
                        connection.commit()
                        st.success("공시서식 데이터가 데이터베이스에 성공적으로 저장되었습니다!")

                except mysql.connector.Error as e:
                    st.error(f"오류: {e}")

                finally:
                    if connection.is_connected():
                        cursor.close()
                        connection.close()
                        st.info("MySQL 연결이 종료되었습니다.")
                
        except Exception as e:
            st.error(f"파일 처리 중 오류 발생: {e}")
    
    # 구분선 추가
    st.markdown("---")
    
    # 2. 지원대상 회사 업로드 섹션
    st.markdown("### 지원대상 회사 업로드")
    st.markdown("##### 칼럼이 3개짜리인 엑셀파일로 올려주세요")
    st.markdown("##### ('업데이트일'칼럼 삭제필수)")
    
    companies_file = st.file_uploader("회사 목록 Excel 파일 업로드", type=["xlsx", "xls"], key="companies_uploader")
    
    if companies_file is not None:
        try:
            # Excel 파일 읽기
            df_disc = pd.read_excel(companies_file, dtype=str)
            
            # 회사코드 포맷팅 (5자리로 맞추고 앞에 0 채우기)
            df_disc['회사코드'] = df_disc['회사코드'].apply(lambda x: str(x).rjust(5, '0'))
            
            # 오늘날짜 설정
            today = (datetime.today()).strftime('%Y%m%d')
            df_disc['update_date'] = today
            
            # 칼럼명 설정
            df_disc.columns = ['회사코드', '회사명', '상장여부', 'update_date']
            
            # 데이터 미리보기 표시
            st.write("업로드된 회사 데이터:")
            st.dataframe(df_disc)
            
            # 업로드 확인 버튼
            if st.button("회사 데이터 임시 적용하기", key="apply_companies"):
                # 세션 상태에 df_listed 업데이트
                st.session_state.df_listed = df_disc.copy()
                st.success("지원대상 회사 목록이 임시 업데이트되었습니다.")
                st.rerun()  # 페이지 새로고침
                
            # DB에 영구반영하기 버튼
            if st.button("회사 데이터 DB에 영구반영하기", key="save_companies_to_db"):
                try:
                    # Create a connection to the database
                    connection = mysql.connector.connect(**db_config)

                    if connection.is_connected():
                        st.info("MySQL 데이터베이스에 연결되었습니다.")

                        # Create a cursor object to interact with the database
                        cursor = connection.cursor()
                        
                        # 데이터베이스 이용
                        cursor.execute("USE englishkind")
                        
                        cursor.execute("DROP TABLE IF EXISTS kosdaq_companies")
                        
                        # 유가 번역대상 보고서 테이블 생성
                        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS kosdaq_companies (
                            company_code VARCHAR(5) PRIMARY KEY,
                            company_name VARCHAR(255) NOT NULL,
                            listed VARCHAR(255) NOT NULL,
                            update_date VARCHAR(8) NOT NULL
                        )
                        """)
                        
                        # Insert the data from the DataFrame into the table using parameterized queries
                        insert_query = """INSERT INTO kosdaq_companies (
                        company_code, company_name, listed, update_date) 
                        VALUES (%s, %s, %s, %s)
                        """
                        
                        # Streamlit용 진행 표시줄
                        progress_bar = st.progress(0)
                        for i, (_, row) in enumerate(df_disc.iterrows()):
                            row = row.fillna("-")
                            cursor.execute(insert_query, (row['회사코드'], row['회사명'], row['상장여부'], row['update_date']))
                            progress_bar.progress((i + 1) / len(df_disc))

                        # Commit the changes
                        connection.commit()
                        st.success("회사 데이터가 데이터베이스에 성공적으로 저장되었습니다!")

                except mysql.connector.Error as e:
                    st.error(f"오류: {e}")

                finally:
                    if connection.is_connected():
                        cursor.close()
                        connection.close()
                        st.info("MySQL 연결이 종료되었습니다.")
                
        except Exception as e:
            st.error(f"파일 처리 중 오류 발생: {e}")

    



# 필터링에 사용될 df_listed 업데이트
df_svc = st.session_state.df_svc
df_listed = st.session_state.df_listed

# 날짜 계산 함수
def get_default_date():
    today = datetime.today()
    if today.weekday() in [5, 6]:  # 토요일(5) 또는 일요일(6)
        return (today - timedelta(days=today.weekday() - 4)).strftime("%Y-%m-%d")  # 직전 금요일
    return today.strftime("%Y-%m-%d")  # 오늘 날짜

# 제목
st.subheader('조회일자 선택')

# 날짜 선택 위젯 추가
selected_date = st.date_input(
    "조회할 날짜를 선택하세요",
    value=datetime.strptime(get_default_date(), "%Y-%m-%d"),
    min_value=datetime(2020, 1, 1),  # 최소 선택 가능 날짜
    max_value=datetime.today()       # 최대 선택 가능 날짜
)

# 선택된 날짜를 YYYY-MM-DD 형식으로 변환
today_date = selected_date.strftime("%Y-%m-%d")
        
# 버튼 생성
if st.button('코스닥 영문공시 지원대상 공시조회'):
    # 로딩 표시
    with st.spinner('데이터를 가져오는 중입니다...'):
        
        # 모든 페이지의 데이터를 저장할 빈 리스트
        all_data = []
        
        # 페이지별 데이터 수집 함수
        def get_page_data(page_num):
            url = 'https://kind.krx.co.kr/disclosure/todaydisclosure.do'
            params = {
                "method": "searchTodayDisclosureSub",
                "currentPageSize": 100,
                "pageIndex": page_num,
                "orderMode": 0,
                "orderStat": "D",
                "marketType": 2,
                "forward": "todaydisclosure_sub",
                "searchMode": "",
                "searchCodeType": "",
                "chose": "S",
                "todayFlag": "Y",
                "repIsuSrtCd": "",
                "kosdaqSegment": "",
                "selDate": today_date,
                "searchCorpName": "",
                "copyUrl": ""
            }

            try:
                response = requests.post(url, params=params)
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                st.error(f"페이지 {page_num} 요청 중 오류 발생: {e}")
                return None

        # 데이터 파싱 함수
        def parse_table(soup):
            data = []
            table = soup.find('table', class_='list type-00 mt10')
            
            if table and table.find('tbody'):
                for row in table.find('tbody').find_all('tr'):
                    cols = row.find_all('td')
                    
                    if len(cols) >= 5:
                        # 필요한 데이터 추출 (원본 코드와 동일)
                        time = cols[0].text.strip()
                        
                        company_a_tag = cols[1].find('a', id='companysum')
                        company = company_a_tag.text.strip() if company_a_tag else ""
                        
                        company_code = ""
                        if company_a_tag and company_a_tag.has_attr('onclick'):
                            onclick_attr = company_a_tag['onclick']
                            code_match = re.search(r"companysummary_open\('([A-Za-z0-9]+)'\)", onclick_attr)
                            if code_match:
                                company_code = code_match.group(1)
                        
                        title_a_tag = cols[2].find('a')
                        title = ""
                        note = ""
                        
                        if title_a_tag:
                            title = title_a_tag.get('title', "").strip()
                            
                            font_tags = title_a_tag.find_all('font')
                            if font_tags:
                                notes = []
                                for font_tag in font_tags:
                                    notes.append(font_tag.text.strip())
                                note = "_".join(notes)
                        
                        submitter = cols[3].text.strip()
                        
                        discl_url = ""
                        if title_a_tag and title_a_tag.has_attr('onclick'):
                            onclick_attr = title_a_tag['onclick']
                            match = re.search(r"openDisclsViewer\('(\d+)'", onclick_attr)
                            if match:
                                acptno = match.group(1)
                                discl_url = f"https://kind.krx.co.kr/common/disclsviewer.do?method=search&acptno={acptno}&docno=&viewerhost=&viewerport="
                        
                        data.append({
                            '시간': time,
                            '회사코드': company_code,
                            '회사명': company,
                            '비고': note,
                            '공시제목': title,
                            '제출인': submitter,
                            '상세URL': discl_url
                        })
            return data

        # 첫 페이지 요청 및 데이터 처리
        url = 'https://kind.krx.co.kr/disclosure/todaydisclosure.do'
        params = {
            "method": "searchTodayDisclosureSub",
            "currentPageSize": 100,
            "pageIndex": 1,
            "orderMode": 0,
            "orderStat": "D",
            "marketType": 1,
            "forward": "todaydisclosure_sub",
            "searchMode": "",
            "searchCodeType": "",
            "chose": "S",
            "todayFlag": "Y",
            "repIsuSrtCd": "",
            "kosdaqSegment": "",
            "selDate": today_date,
            "searchCorpName": "",
            "copyUrl": ""
        }

        response = requests.post(url, params=params)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 총 건수와 페이지 수 추출
        total_items_element = soup.select_one('.info.type-00 em')
        total_pages_text = soup.select_one('.info.type-00').text.strip()
        total_pages_match = re.search(r'(\d+)/(\d+)', total_pages_text)

        if total_items_element and total_pages_match:
            total_items = int(total_items_element.text.strip().replace(",",""))
            total_pages = int(total_pages_match.group(2))
            
            st.info(f"조회일에 총 {total_items}건의 공시가 있습니다. (총 {total_pages}페이지)    지원대상 공시는 아래 표를 참고해주세요.")
        else:
            st.warning("페이지 정보를 찾을 수 없습니다.")
            total_pages = 1

        # 첫 페이지 데이터 처리
        all_data.extend(parse_table(soup))

        # 페이지가 여러 개인 경우 나머지 페이지 처리
        if total_pages > 1:
            # Streamlit 진행 표시줄
            progress_bar = st.progress(0)
            
            for i, page in enumerate(range(2, total_pages + 1)):
                page_soup = get_page_data(page)
                if page_soup:
                    page_data = parse_table(page_soup)
                    all_data.extend(page_data)
                
                # 진행률 업데이트
                progress = (i + 1) / (total_pages - 1)
                progress_bar.progress(progress)
                
                # 서버 부하를 줄이기 위한 대기 시간
                time.sleep(0.5)

        # 데이터프레임 생성
        df_discl = pd.DataFrame(all_data)
        
        # 필터링 (지원 대상 서식만 필터)
        form_names = df_svc['서식명'].unique().tolist()
        
        def is_contained(title):
            for form_name in form_names:
                if form_name in title:
                    return True
            return False
        
        # 첫 번째 필터링: 지원 대상 서식만 필터
        filtered_df = df_discl[df_discl['공시제목'].apply(is_contained)]
        
        # 두 번째 필터링: 지정된 회사 코드만 필터
        listed_company_codes = df_listed['회사코드'].tolist()
        filtered_df = filtered_df[filtered_df['회사코드'].isin(listed_company_codes)]
        
        # 결과 표시
        st.subheader('코스닥 지원대상 공시 목록')
        
        if filtered_df.empty:
            st.warning("조건에 맞는 공시 데이터가 없습니다.")
        else:
            st.write(f"총 {len(filtered_df)}건의 지원대상 공시가 있습니다.")
            
            # URL을 클릭 가능한 링크로 표시
            st.dataframe(
                filtered_df,
                column_config={
                    "상세URL": st.column_config.LinkColumn("상세URL"),
                },
                hide_index=True
            )
