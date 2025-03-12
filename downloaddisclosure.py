from xml.etree import ElementTree as ET
import pandas as pd
import OpenDartReader

#기업용IP에서 사용하는 API KEY
api_key = 'b98ee0e4dde92e1594591515396ff41e688e99dd'
dart = OpenDartReader(api_key)



#----------------------------------------------------------------
#대상 문서 선택
rcp_no = '20240229001864'
#----------------------------------------------------------------




#DART에서 XML문서 가져오기
doc = dart.document(rcp_no)

# XML을 파싱하여 ElementTree 객체 생성
root = ET.fromstring(doc)

#----------------------------------------------------------------
#청약 및 배정현황
#----------------------------------------------------------------
# 대상추출
table_group = root.find(".//TABLE-GROUP[@ACLASS='DST_CD']")
table = table_group.find(".//TABLE[@ACLASS='EXTRACTION'][@AFIXTABLE='N']")

#열이름 설정
#멀티칼럼인데, 활용을 편하게 하기 위해 싱글칼럼으로 만들어봄
columns = ['구분', '최초배정_수량','최초배정_비율',
           '청약현황_건수','청약현황_수량','청약현황_금액','청약현황_비율',
           '최종배정_건수','최종배정_수량','최종배정_금액','최종배정_비율']
#행으로 사용될 빈 리스트 생성
rows = []

# TBODY에서 행 데이터 추출
for tr in table.findall('.//TBODY/TR'):
    row = []
    # 모든 자식 요소 순회
    for child in tr:
        # 요소가 TD 또는 TE 태그인 경우에만 처리
        if child.tag in ['TD', 'TE']:
            cell_text = child.text.strip() if child.text else ''
            row.append(cell_text)
    rows.append(row)
    
# DataFrame 생성
df_assignment = pd.DataFrame(rows, columns=columns)

#----------------------------------------------------------------
#인수기관별 인수금액
#----------------------------------------------------------------
# 대상추출
table_group = root.find(".//TABLE-GROUP[@ACLASS='ACC_AMT']")
table = table_group.find(".//TABLE[@ACLASS='EXTRACTION'][@AFIXTABLE='N']")

#열이름 설정
columns = ['인수기관', '인수수량','인수금액','비율','비고']
#행으로 사용될 빈 리스트 생성
rows = []
				

# TBODY에서 행 데이터 추출
for tr in table.findall('.//TBODY/TR'):
    row = []
    # 모든 자식 요소 순회
    for child in tr:
        # 요소가 TD 또는 TE 태그인 경우에만 처리
        if child.tag in ['TD', 'TE']:
            cell_text = child.text.strip() if child.text else ''
            row.append(cell_text)
    rows.append(row)
    
# DataFrame 생성
df_underwriter = pd.DataFrame(rows, columns=columns)

#----------------------------------------------------------------
#자금조달내용
#----------------------------------------------------------------
# 대상추출
table_group = root.find(".//TABLE-GROUP[@ACLASS='INC_SL']")
table = table_group.find(".//TABLE[@ACLASS='EXTRACTION'][@AFIXTABLE='N']")

#열이름 설정
#멀티칼럼인데, 활용을 편하게 하기 위해 싱글칼럼으로 만들어봄
columns = ['구분', '주식구분','신고서상_발행예정총액',
           '실제조달_발행가액','실제조달_수량','실제조달_발행총액','비고']

#행으로 사용될 빈 리스트 생성
rows = [] 

# TBODY에서 행 데이터 추출
for tr in table.findall('.//TBODY/TR'):
    row = []

    #ROWSPAN, COLSPAN 보유여부
    has_rowspan = any(child.get('ROWSPAN') for child in tr if child.tag in ['TD', 'TE'])
    has_colspan = any(child.get('COLSPAN') for child in tr if child.tag in ['TD', 'TE'])
    
    #'모집' '매출' 정보가 있는 행인경우(행 병합된 케이스)
    if has_rowspan:
        # 모든 자식 요소 순회
        for child in tr:
            # 요소가 TD 또는 TE 태그인 경우에만 처리
            if child.tag in ['TD', 'TE']:
                if child.get('ROWSPAN'):
                    #반복할 셀 지정
                    repeated_cell_row = child.text.strip() if child.text else ''
                #모든 셀 집어넣기
                cell_text = child.text.strip() if child.text else ''
                row.append(cell_text)


    #'총계' 정보가 있는 행인경우(열 병합된 케이스)
    elif has_colspan:
        # 모든 자식 요소 순회
        for child in tr:
            # 요소가 TD 또는 TE 태그인 경우에만 처리
            if child.tag in ['TD', 'TE']:
                if child.get('COLSPAN'):
                    #반복할 셀 지정하고 집어넣기
                    repeated_cell_col = child.text.strip() if child.text else ''
                    row.append(repeated_cell_col)
                #이후 모든 셀 집어넣기
                cell_text = child.text.strip() if child.text else ''
                row.append(cell_text)
    
    #일반 행은 행병합된 것을 추가하면 됨
    else:
        #반복행 집어넣기
        row.append(repeated_cell_row)
        # 모든 자식 요소 순회
        for child in tr:
            #모든 셀 집어넣기
            cell_text = child.text.strip() if child.text else ''
            row.append(cell_text)
    rows.append(row)

# DataFrame 생성
df_capital_raised = pd.DataFrame(rows, columns=columns)
