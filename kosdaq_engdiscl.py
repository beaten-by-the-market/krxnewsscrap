import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time

# 페이지 설정 (wide 모드로 설정)
st.set_page_config(
    page_title="오늘의 코스닥 번역대상 공시",
    layout="wide",  # 화면을 넓게 사용
    initial_sidebar_state="collapsed"  # 사이드바 초기 상태를 접힌 상태로 설정
)

# 제목 설정
st.title('오늘의 코스닥 번역대상 공시')

# 지원대상 데이터 리스트 (df_data 정의)
df_data = [
    ["11301","부도발생","수시공시","금감원"],
    ["11302","은행거래정지ㆍ금지","수시공시","금감원"],
    ["11303","영업정지","수시공시","금감원"],
    ["11304","회생절차개시신청","수시공시","금감원"],
    ["11305","해산사유발생","수시공시","금감원"],
    ["11306","유상증자결정","수시공시","금감원"],
    ["11307","무상증자결정","수시공시","금감원"],
    ["11308","유무상증자결정","수시공시","금감원"],
    ["11309","감자결정","수시공시","금감원"],
    ["11310","채권은행등의관리절차개시","수시공시","금감원"],
    ["11312","소송등의제기","수시공시","금감원"],
    ["11313","해외증권시장주권등상장결정","수시공시","금감원"],
    ["11314","해외증권시장주권등상장폐지결정","수시공시","금감원"],
    ["11315","해외증권시장주권등상장","수시공시","금감원"],
    ["11316","해외증권시장주권등상장폐지","수시공시","금감원"],
    ["11317","해외증권시장주권등매매거래정지등조치","수시공시","금감원"],
    ["11318","외국법인등의외국법령등변경","수시공시","금감원"],
    ["11319","외국법인등의주식등에대한외국에서의공개매수","수시공시","금감원"],
    ["11320","외국법인등의주식등에대한외국에서의안정조작등","수시공시","금감원"],
    ["11321","외국법인등의해외법규위반으로인한조치","수시공시","금감원"],
    ["11322","외국법인등의외국거래소로부터매매거래정지ㆍ해제","수시공시","금감원"],
    ["11323","외국법인등의외국거래소로부터상장폐지","수시공시","금감원"],
    ["11324","전환사채권발행결정","수시공시","금감원"],
    ["11325","신주인수권부사채권발행결정","수시공시","금감원"],
    ["11326","교환사채권발행결정","수시공시","금감원"],
    ["11327","채권은행등의관리절차중단","수시공시","금감원"],
    ["11328","전환형 조건부자본증권 발행결정","수시공시","금감원"],
    ["11329","상각형 조건부자본증권 발행결정","수시공시","금감원"],
    ["11330","전환형 조건부자본증권의 주식전환 사유 발생","수시공시","금감원"],
    ["11331","상각형 조건부자본증권의 채무재조정 사유 발생","수시공시","금감원"],
    ["11332","자기주식 취득 결정","수시공시","금감원"],
    ["11333","자기주식 처분 결정","수시공시","금감원"],
    ["11334","자기주식취득 신탁계약 체결 결정","수시공시","금감원"],
    ["11335","자기주식취득 신탁계약 해지 결정","수시공시","금감원"],
    ["11336","영업양수 결정","수시공시","금감원"],
    ["11337","영업양도 결정","수시공시","금감원"],
    ["11338","유형자산 양수 결정","수시공시","금감원"],
    ["11339","유형자산 양도 결정","수시공시","금감원"],
    ["11340","타법인 주식 및 출자증권 양수결정","수시공시","금감원"],
    ["11341","타법인 주식 및 출자증권 양도결정","수시공시","금감원"],
    ["11342","주권 관련 사채권 양수 결정","수시공시","금감원"],
    ["11343","주권 관련 사채권 양도 결정","수시공시","금감원"],
    ["11344","회사합병 결정","수시공시","금감원"],
    ["11345","회사분할 결정","수시공시","금감원"],
    ["11346","회사분할합병 결정","수시공시","금감원"],
    ["11347","주식교환ㆍ이전 결정","수시공시","금감원"],
    ["11348","자본으로 인정되는 채무증권 발행결정","수시공시","금감원"],
    ["70008","횡령ㆍ배임혐의발생","수시공시","거래소"],
    ["70009","횡령ㆍ배임사실확인","수시공시","거래소"],
    ["70010","소송등의제기ㆍ신청(자율공시:일정금액미만의청구)","수시공시","거래소"],
    ["70011","소송등의판결ㆍ결정(자율공시:일정금액미만의청구)","수시공시","거래소"],
    ["70012","단일판매ㆍ공급계약체결(자율공시)","수시공시","거래소"],
    ["70013","단일판매ㆍ공급계약해지(자율공시)","수시공시","거래소"],
    ["70014","유형자산취득결정(자율공시)","수시공시","거래소"],
    ["70015","유형자산처분결정(자율공시)","수시공시","거래소"],
    ["70016","매출액 또는 손익구조 30%(대규모법인은 15%)미만 변동(자율공시)","수시공시","거래소"],
    ["70017","파생상품 거래 손실발생(자율공시)","수시공시","거래소"],
    ["70018","거래처와의거래중단(자율공시)","수시공시","거래소"],
    ["70019","벌금등의부과(자율공시)","수시공시","거래소"],
    ["70020","횡령ㆍ배임 혐의발생(자율공시)","수시공시","거래소"],
    ["70021","횡령ㆍ배임 사실확인(자율공시)","수시공시","거래소"],
    ["70022","출자법인의부도등발생(자율공시)","수시공시","거래소"],
    ["70023","출자법인의해산사유발생(자율공시)","수시공시","거래소"],
    ["70024","출자법인의회생및파산절차관련사실등발생(자율공시)","수시공시","거래소"],
    ["70025","피보증(담보제공포함)법인의부도등발생(자율공시)","수시공시","거래소"],
    ["70026","피보증(담보제공포함)법인의해산사유발생(자율공시)","수시공시","거래소"],
    ["70027","피보증(담보제공포함)법인의회생및파산절차관련사실등발생(자율공시)","수시공시","거래소"],
    ["70028","금전가지급결정(자율공시)","수시공시","거래소"],
    ["70029","금전대여결정(자율공시)","수시공시","거래소"],
    ["70030","증권대여결정(자율공시)","수시공시","거래소"],
    ["70031","채무면제결정(자율공시)","수시공시","거래소"],
    ["70032","채무인수결정(자율공시)","수시공시","거래소"],
    ["70033","생산중단(자율공시)","수시공시","거래소"],
    ["70034","생산재개(자율공시)","수시공시","거래소"],
    ["70035","영업정지(자율공시)","수시공시","거래소"],
    ["70036","재해발생(자율공시)","수시공시","거래소"],
    ["70037","제품에대한수거ㆍ파기등결정(자율공시)","수시공시","거래소"],
    ["70038","타인에 대한 담보제공 결정(자율공시)","수시공시","거래소"],
    ["70039","타인에 대한 채무보증 결정(자율공시)","수시공시","거래소"],
    ["70040","신규시설투자등(자율공시)","수시공시","거래소"],
    ["70041","타법인주식및출자증권취득결정(자율공시)","수시공시","거래소"],
    ["70042","타법인주식및출자증권처분결정(자율공시)","수시공시","거래소"],
    ["70043","단기차입금증가결정(자율공시)","수시공시","거래소"],
    ["70050","기업설명회(IR) 개최","신고사항","거래소"],
    ["70051","단기차입금감소결정(자율공시)","수시공시","거래소"],
    ["70054","소송등의제기ㆍ신청(자율공시:합병ㆍ분할 등 관련 무효ㆍ취소)","수시공시","거래소"],
    ["70055","소송등의판결ㆍ결정(자율공시:합병ㆍ분할 등 관련 무효ㆍ취소)","수시공시","거래소"],
    ["70056","중간(분기)배당을위한주주명부폐쇄(기준일)결정","수시공시","거래소"],
    ["70057","횡령ㆍ배임 혐의 진행사항","수시공시","거래소"],
    ["70058","횡령ㆍ배임 혐의 진행사항(자율공시)","수시공시","거래소"],
    ["70060","사채원리금미지급발생(자율공시)","수시공시","거래소"],
    ["70061","시설외 투자 등","수시공시","거래소"],
    ["70062","시설외 투자 등(자율공시)","수시공시","거래소"],
    ["70065","증권 발행결과(자율공시)","수시공시","거래소"],
    ["70070","소송등의제기ㆍ신청(일정금액 이상의 청구)","수시공시","거래소"],
    ["70071","소송등의판결ㆍ결정(일정금액 이상의 청구)","수시공시","거래소"],
    ["70072","소송등의판결ㆍ결정","수시공시","거래소"],
    ["70073","소송 등의 제기ㆍ신청(경영권 분쟁 소송)","수시공시","거래소"],
    ["70108","전환가액의조정","신고사항","거래소"],
    ["70109","전환청구권행사","신고사항","거래소"],
    ["70113","신주인수권행사가액의조정","신고사항","거래소"],
    ["70114","신주인수권행사","신고사항","거래소"],
    ["70118","교환가액의조정","신고사항","거래소"],
    ["70119","교환청구권행사","신고사항","거래소"],
    ["70123","증권예탁증권(DR) 원주청구권 행사","신고사항","거래소"],
    ["70128","주식분할결정","수시공시","거래소"],
    ["70129","주식병합결정","수시공시","거래소"],
    ["70135","전환사채(해외전환사채포함)발행후만기전사채취득","신고사항","거래소"],
    ["70136","신주인수권부사채(해외신주인수권부사채포함)발행후만기전사채취득","신고사항","거래소"],
    ["70137","교환사채(해외교환사채포함)발행후만기전사채취득","신고사항","거래소"],
    ["70180","채권은행 등의 관리절차 개시 신청","수시공시","거래소"],
    ["70181","채권은행 등의 관리절차 개시 신청취하","수시공시","거래소"],
    ["70182","채권은행등의관리절차해제","수시공시","거래소"],
    ["70183","벌금등의부과","수시공시","거래소"],
    ["70184","채권은행 등의 관리절차 개시(기업구조조정 촉진법에 해당하지 않는 경우)","수시공시","거래소"],
    ["70190","계열회사변경(자율공시)","수시공시","거래소"],
    ["70191","주요주주변경(자율공시)","수시공시","거래소"],
    ["70193","가족친화 인증ㆍ유효기간 연장ㆍ인증취소(자율공시)","수시공시","거래소"],
    ["70194","가족친화 경영정보 관련 과태료 부과 조치(자율공시)","수시공시","거래소"],
    ["70203","채권은행 등의 관리절차 중단(기업구조조정 촉진법에 해당하지 않는 경우)","수시공시","거래소"],
    ["70247","거래처와의거래중단","수시공시","거래소"],
    ["70248","증여 결정(자율공시)","수시공시","거래소"],
    ["70249","수증(자율공시)","수시공시","거래소"],
    ["70282","피보증(담보제공포함)법인의부도등발생","수시공시","거래소"],
    ["70294","피보증(담보제공포함)법인의해산사유발생","수시공시","거래소"],
    ["70295","금전가지급결정","수시공시","거래소"],
    ["70296","금전대여결정","수시공시","거래소"],
    ["70297","증권대여결정","수시공시","거래소"],
    ["70298","출자법인의부도등발생","수시공시","거래소"],
    ["70299","선급금 지급 결정","수시공시","거래소"],
    ["70300","매출채권 이외의 채권에서 발생한 손상차손","수시공시","거래소"],
    ["70310","출자법인의해산사유발생","수시공시","거래소"],
    ["70311","채무인수결정","수시공시","거래소"],
    ["70312","채무면제결정","수시공시","거래소"],
    ["70316","피보증(담보제공포함)법인의회생절차 및 파산절차 관련 사실 등 발생","수시공시","거래소"],
    ["70321","출자법인의회생절차및파산절차관련사실등발생","수시공시","거래소"],
    ["70325","채무면제이익발생(자율공시)","수시공시","거래소"],
    ["70330","회생절차 개시신청 기각","수시공시","거래소"],
    ["70331","회생절차개시결정 취소","수시공시","거래소"],
    ["70332","회생계획 인가","수시공시","거래소"],
    ["70333","회생계획 불인가","수시공시","거래소"],
    ["70340","파산신청","수시공시","거래소"],
    ["70341","파산신청 기각","수시공시","거래소"],
    ["70342","파산선고","수시공시","거래소"],
    ["70343","어음 위ㆍ 변조 발생","수시공시","거래소"],
    ["70344","사채원리금미지급발생","수시공시","거래소"],
    ["70345","대출원리금 연체사실 발생","수시공시","거래소"],
    ["70346","대출원리금 연체사실 발생(자율공시)","수시공시","거래소"],
    ["70361","자원개발 진행사항(자율공시)","수시공시","거래소"],
    ["70362","자원개발 중단(자율공시)","수시공시","거래소"],
    ["70368","자원개발 투자 결정(자율공시)","수시공시","거래소"],
    ["70369","자원개발의 경제성 판명(자율공시)","수시공시","거래소"],
    ["70370","단일판매ㆍ공급계약체결","수시공시","거래소"],
    ["70371","단일판매ㆍ공급계약해지","수시공시","거래소"],
    ["70379","유형자산취득결정","수시공시","거래소"],
    ["70380","유형자산처분결정","수시공시","거래소"],
    ["70387","상호저축은행 과점주주 지위 획득 또는 변동(자율공시)","수시공시","거래소"],
    ["70390","상장외국법인의 본국 증권거래소에 대한 신고","수시공시","거래소"],
    ["70391","상장외국법인의 본국 거래소 관련 조회공시사항","수시공시","거래소"],
    ["70392","상장외국법인의 본국 거래소에 대한 매매거래정지 요청 등","수시공시","거래소"],
    ["70431","파생상품 거래 이익 발생(자율공시)","수시공시","거래소"],
    ["70432","파생상품거래손실발생","수시공시","거래소"],
    ["70443","매출액 또는 손익구조 30%(대규모법인은 15%)이상 변동","수시공시","거래소"],
    ["70471","주주총회소집결의","수시공시","거래소"],
    ["70476","기타 주요경영사항","수시공시","거래소"],
    ["70478","지주회사의자회사편입ㆍ탈퇴","수시공시","거래소"],
    ["70479","외국지주회사의 자회사 편입ㆍ탈퇴","수시공시","거래소"],
    ["70481","임시주주총회결과","수시공시","거래소"],
    ["70482","정기주주총회결과","수시공시","거래소"],
    ["70499","주식매수선택권행사","신고사항","거래소"],
    ["70567","감사보고서 제출","수시공시","거래소"],
    ["70568","금융기관 경영개선 등의 조치(자율공시)","수시공시","거래소"],
    ["70631","기타 경영사항(자율공시)","수시공시","거래소"],
    ["70634","최대주주의 상호저축은행 과점주주 지위 획득(자율공시)","수시공시","거래소"],
    ["70635","최대주주의 상호저축은행 과점주주 지위 변경(자율공시)","수시공시","거래소"],
    ["70636","관계상호저축은행의 자기자본비율 8% 미만(자율공시)","수시공시","거래소"],
    ["70637","관계상호저축은행의 분기 재무제표 확정(자율공시)","수시공시","거래소"],
    ["70640","공정거래 자율준수프로그램 운영현황","수시공시","거래소"],
    ["70642","회계처리기준위반행위로인한검찰기소","수시공시","거래소"],
    ["70643","회계처리기준위반행위로인한증권선물위원회의검찰고발등","수시공시","거래소"],
    ["70644","관계상호저축은행 관련 소송의 제기(자율공시)","수시공시","거래소"],
    ["70647","증권예탁증권(DR)분할결정","수시공시","거래소"],
    ["70648","증권예탁증권(DR)병합결정","수시공시","거래소"],
    ["70649","감자주식의취득완료또는취득기간종료","신고사항","거래소"],
    ["70650","감자완료","신고사항","거래소"],
    ["70651","유상증자1차발행가액결정","신고사항","거래소"],
    ["70652","유상증자최종발행가액확정","신고사항","거래소"],
    ["70653","단수주및실권주처리","신고사항","거래소"],
    ["70654","전환사채전환가액결정","신고사항","거래소"],
    ["70655","신주인수권부사채행사가액결정","신고사항","거래소"],
    ["70656","대표이사변경","수시공시","거래소"],
    ["70657","주주명부폐쇄기간 또는 기준일 설정","신고사항","거래소"],
    ["70659","상호변경안내","신고사항","거래소"],
    ["70660","본점소재지변경","신고사항","거래소"],
    ["70661","결산기변경안내","신고사항","거래소"],
    ["70662","기타신고사항","신고사항","거래소"],
    ["70664","교환사채 교환가액결정","신고사항","거래소"],
    ["70667","상장폐지승인을위한의안상정결정","수시공시","거래소"],
    ["70671","증권관련 집단소송의 제기ㆍ소송 허가신청","수시공시","거래소"],
    ["70672","증권관련 집단소송의 허가결정","수시공시","거래소"],
    ["70673","증권관련 집단소송의 판결ㆍ결정에 대한 항고 등 불복신청","수시공시","거래소"],
    ["70674","증권관련 집단소송 관련 소취하 등 허가신청","수시공시","거래소"],
    ["70675","증권관련 집단소송관련 소취하 등 허가신청에 대한 결정","수시공시","거래소"],
    ["70676","증권관련 집단소송에 대한 판결ㆍ결정","수시공시","거래소"],
    ["70677","증권관련 집단소송의 불허가결정","수시공시","거래소"],
    ["70684","조회공시요구(풍문또는보도)에대한답변(부인)","수시공시","거래소"],
    ["70685","조회공시요구(풍문또는보도)에대한답변(미확정)","수시공시","거래소"],
    ["70686","조회공시요구(현저한시황변동)에대한답변(중요정보 없음)","수시공시","거래소"],
    ["70687","조회공시요구(현저한시황변동)에대한답변(미확정)","수시공시","거래소"],
    ["70689","반기 검토(감사)의견 부적정등 사실확인(자본잠식률 100분의 50이상 또는 자기자본 10억원 미만 포함)","수시공시","거래소"],
    ["70910","유동성공급계약의 체결","신고사항","거래소"],
    ["70911","유동성공급계약의 해지","신고사항","거래소"],
    ["70912","유동성공급계약의 변경","신고사항","거래소"],
    ["70940","결산실적공시 예고","신고사항","거래소"],
    ["70951","장래사업ㆍ경영 계획(공정공시)","공정공시","거래소"],
    ["70952","영업실적 등에 대한 전망(공정공시)","공정공시","거래소"],
    ["70953","영업(잠정)실적(공정공시)","공정공시","거래소"],
    ["70954","수시공시의무관련사항(공정공시)","공정공시","거래소"],
    ["70956","연결재무제표 기준 영업(잠정)실적(공정공시)","공정공시","거래소"],
    ["70957","연결재무제표 기준 영업실적 등에 대한 전망(공정공시)","공정공시","거래소"],
    ["71121","증권예탁증권(DR)발행결정","수시공시","거래소"],
    ["71131","주식소각 결정","수시공시","거래소"],
    ["71145","해외증권거래소 등의 조회공시사항 국내신고","수시공시","거래소"],
    ["71146","해외증권거래소 등에 요청한 매매거래정지 등 국내신고","수시공시","거래소"],
    ["71147","해외증권거래소등에신고한주요공시사항의국내신고","수시공시","거래소"],
    ["71152","단기차입금증가결정","수시공시","거래소"],
    ["71178","회생절차개시결정","수시공시","거래소"],
    ["71184","회생절차 종결신청","수시공시","거래소"],
    ["71185","회생절차 종결결정","수시공시","거래소"],
    ["71186","회생절차 폐지신청","수시공시","거래소"],
    ["71187","회생절차 폐지결정","수시공시","거래소"],
    ["71197","상장폐지결정","수시공시","거래소"],
    ["71202","경영정상화계획의이행약정체결","수시공시","거래소"],
    ["71207","최대주주 변경을 수반하는 주식양수도 계약 체결","수시공시","거래소"],
    ["71208","경영권 변경 등에 관한 계약 체결","수시공시","거래소"],
    ["71209","최대주주변경","수시공시","거래소"],
    ["71210","최대주주인 명목회사·조합 등의 최대주주 변경","신고사항","거래소"],
    ["71241","생산중단","수시공시","거래소"],
    ["71245","재해발생","수시공시","거래소"],
    ["71246","제품에대한수거ㆍ파기등결정","수시공시","거래소"],
    ["71251","기업인수목적회사의정관변경결정","수시공시","거래소"],
    ["71252","기업인수목적회사의임원선임결정","수시공시","거래소"],
    ["71253","기업인수목적회사의임원해임결정","수시공시","거래소"],
    ["71254","기업인수목적회사의임원사임","수시공시","거래소"],
    ["71255","기업인수목적회사관련합병취소ㆍ부인사실발생","수시공시","거래소"],
    ["71256","기업인수목적회사의예치ㆍ신탁계약내용변경","수시공시","거래소"],
    ["71257","기업인수목적회사의예치ㆍ신탁비율변경","수시공시","거래소"],
    ["71258","기업인수목적회사의예치ㆍ신탁자금인출사실발생","수시공시","거래소"],
    ["71313","타인에대한담보제공결정","수시공시","거래소"],
    ["71314","타인에대한채무보증결정","수시공시","거래소"],
    ["71361","신규시설투자등","수시공시","거래소"],
    ["71364","녹색기술ㆍ사업에 대한 인증ㆍ인증취소(자율공시)","수시공시","거래소"],
    ["71365","녹색전문기업의 확인ㆍ확인취소(자율공시)","수시공시","거래소"],
    ["71366","온실가스ㆍ에너지 관리업체 지정ㆍ지정취소(자율공시)","수시공시","거래소"],
    ["71367","녹색경영정보 관련 개선명령 등 조치(자율공시)","수시공시","거래소"],
    ["71368","녹색기업의 지정ㆍ지정취소(자율공시)","수시공시","거래소"],
    ["71369","온실가스 배출권의 취득(자율공시)","수시공시","거래소"],
    ["71370","온실가스 배출권의 처분(자율공시)","수시공시","거래소"],
    ["71374","기타 녹색경영정보 관련 공시(자율공시)","수시공시","거래소"],
    ["71381","타법인주식및출자증권취득결정","수시공시","거래소"],
    ["71382","타법인주식및출자증권처분결정","수시공시","거래소"],
    ["71474","주식배당결정","수시공시","거래소"],
    ["71479","액면주식ㆍ무액면주식 전환 결정","수시공시","거래소"],
    ["71500","현금ㆍ현물배당 결정","수시공시","거래소"],
    ["71568","대표집행임원 변경","수시공시","거래소"],
    ["71570","영업전부의임대ㆍ경영위임등결정","수시공시","거래소"],
    ["71571","영업전부의임대ㆍ경영위임등의계약변경ㆍ해지결정","수시공시","거래소"],
    ["71573","해외증권거래소등에신고한사업보고서등의국내신고","수시공시","거래소"],
    ["71575","신탁계약등에의해취득한자기주식의장외처분결정","수시공시","거래소"],
    ["71612","자산재평가결과(자율공시)","수시공시","거래소"],
    ["71735","채권은행 등의 관리절차 중단(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71736","부도발생(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71737","은행거래 정지ㆍ금지(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71738","영업정지(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71739","회생절차 개시신청(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71740","해산사유 발생(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71741","유상증자결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71742","무상증자결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71743","유무상증자 결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71744","감자 결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71745","채권은행 등의 관리절차 개시(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71747","소송 등의 제기(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71748","해외 증권시장 주권등 상장 결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71749","해외 증권시장 주권등 상장폐지 결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71750","해외 증권시장 주권등 상장(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71751","해외 증권시장 주권등 상장폐지(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71752","해외 증권시장 주권등 매매거래정지 등 조치(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71759","교환사채권 발행결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71760","유형자산 취득결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71761","유형자산 처분결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71762","타법인 주식 및 출자증권 취득결정(종속회사의 주요경영사항) ","수시공시","거래소"],
    ["71763","타법인 주식 및 출자증권 처분결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71764","영업양수 결정(종속회사의 주요경영사항) ","수시공시","거래소"],
    ["71765","영업양도 결정(종속회사의 주요경영사항) ","수시공시","거래소"],
    ["71766","주식교환ㆍ이전 결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71767","회사분할 결정(종속회사의 주요경영사항) ","수시공시","거래소"],
    ["71768","회사분할합병 결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71769","회사합병 결정(종속회사의 주요경영사항) ","수시공시","거래소"],
    ["71770","기타 주요경영사항(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71771","부도발생(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71772","은행거래 정지ㆍ금지(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71773","영업정지(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71774","회생절차 개시신청(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71775","해산사유 발생(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71776","유상증자결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71777","무상증자결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71778","유무상증자 결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71779","감자 결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71780","채권은행 등의 관리절차 개시(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71782","소송 등의 제기(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71783","해외 증권시장 주권등 상장 결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71784","해외 증권시장 주권등 상장폐지 결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71785","해외 증권시장 주권등 상장(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71786","해외 증권시장 주권등 상장폐지(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71787","해외 증권시장 주권등 매매거래정지 등 조치(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71795","유형자산 취득결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71796","유형자산 처분결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71797","타법인 주식 및 출자증권 취득결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71798","타법인 주식 및 출자증권 처분결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71799","영업양수 결정(자율공시)(종속회사의 주요경영사항) ","수시공시","거래소"],
    ["71800","영업양도 결정(자율공시)(종속회사의 주요경영사항) ","수시공시","거래소"],
    ["71801","주식교환ㆍ이전 결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71802","회사분할 결정(자율공시)(종속회사의 주요경영사항) ","수시공시","거래소"],
    ["71803","회사분할합병 결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71804","회사합병 결정(자율공시)(종속회사의 주요경영사항) ","수시공시","거래소"],
    ["71805","기타 경영사항(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71806","채권은행 등의 관리절차 중단(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["71960","상장외국법인의 외국주식예탁증권 취득 결정","수시공시","거래소"],
    ["71961","상장외국법인의 외국주식예탁증권 처분 결정","수시공시","거래소"],
    ["71963","상장외국법인의기타주요경영사항","수시공시","거래소"],
    ["71964","내부결산시점 관리종목 지정ㆍ형식적 상장폐지ㆍ상장적격성 실질심사 사유 발생","수시공시","거래소"],
    ["71972","가장납입 혐의 발생","수시공시","거래소"],
    ["71974","가장납입 사실 확인","수시공시","거래소"],
    ["71980","유상증자 또는 주식관련사채 등의 청약결과(자율공시)","수시공시","거래소"],
    ["71981","자산재평가 실시 결정(자율공시)","수시공시","거래소"],
    ["71982","가장납입혐의 진행사항","수시공시","거래소"],
    ["71988","주권 관련 사채권의 취득결정","수시공시","거래소"],
    ["71989","주권 관련 사채권의 취득결정(자율공시)","수시공시","거래소"],
    ["71990","주권 관련 사채권의 처분결정","수시공시","거래소"],
    ["71991","주권 관련 사채권의 처분결정(자율공시)","수시공시","거래소"],
    ["71992","회계처리기준 위반에 따른 임원의 해임권고 조치","수시공시","거래소"],
    ["71993","최대주주 변경을 수반하는 주식 담보제공 계약 체결","수시공시","거래소"],
    ["71994","최대주주 변경을 수반하는 주식 담보제공 계약 해제ㆍ취소 등","수시공시","거래소"],
    ["71995","상장외국법인의 자회사에 대한 외화송금 제한 사실 발생","수시공시","거래소"],
    ["71996","풍문 또는 보도에 대한 해명","수시공시","거래소"],
    ["71997","풍문 또는 보도에 대한 해명(미확정)","수시공시","거래소"],
    ["71998","금융기관 임원의 해임권고 등 제재(자율공시)","수시공시","거래소"],
    ["71999","최대주주 변경을 수반하는 주식 양수도 계약 해제ㆍ취소 등","수시공시","거래소"],
    ["72002","주권 관련 사채권의 취득결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["72003","주권 관련 사채권의 취득결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["72004","주권 관련 사채권의 처분결정(종속회사의 주요경영사항)","수시공시","거래소"],
    ["72005","주권 관련 사채권의 처분결정(자율공시)(종속회사의 주요경영사항)","수시공시","거래소"],
    ["72006","영업양수 결정","수시공시","거래소"],
    ["72007","영업양도 결정","수시공시","거래소"],
    ["72008","유형자산 양수 결정","수시공시","거래소"],
    ["72009","유형자산 양도 결정","수시공시","거래소"],
    ["72010","타법인 주식 및 출자증권 양수결정","수시공시","거래소"],
    ["72011","타법인 주식 및 출자증권 양도결정","수시공시","거래소"],
    ["72012","주권 관련 사채권 양수 결정","수시공시","거래소"],
    ["72013","주권 관련 사채권 양도 결정","수시공시","거래소"],
    ["72014","회사합병 결정","수시공시","거래소"],
    ["72015","회사분할 결정","수시공시","거래소"],
    ["72016","회사분할합병 결정","수시공시","거래소"],
    ["72017","주식교환ㆍ이전 결정","수시공시","거래소"],
    ["72018","부도발생","수시공시","거래소"],
    ["72019","은행거래정지ㆍ금지","수시공시","거래소"],
    ["72020","영업정지","수시공시","거래소"],
    ["72021","회생절차개시신청","수시공시","거래소"],
    ["72022","해산사유발생","수시공시","거래소"],
    ["72023","유상증자결정","수시공시","거래소"],
    ["72024","무상증자결정","수시공시","거래소"],
    ["72025","유무상증자결정","수시공시","거래소"],
    ["72026","감자결정","수시공시","거래소"],
    ["72027","채권은행등의관리절차개시","수시공시","거래소"],
    ["72028","소송등의제기","수시공시","거래소"],
    ["72029","해외증권시장주권등상장결정","수시공시","거래소"],
    ["72030","해외증권시장주권등상장폐지결정","수시공시","거래소"],
    ["72031","해외증권시장주권등상장","수시공시","거래소"],
    ["72032","해외증권시장주권등상장폐지","수시공시","거래소"],
    ["72033","해외증권시장주권등매매거래정지등조치","수시공시","거래소"],
    ["72034","전환사채권발행결정","수시공시","거래소"],
    ["72035","신주인수권부사채권발행결정","수시공시","거래소"],
    ["72036","교환사채권발행결정","수시공시","거래소"],
    ["72037","채권은행등의관리절차중단","수시공시","거래소"],
    ["72038","상각형 조건부자본증권 발행결정","수시공시","거래소"],
    ["72039","전환형 조건부자본증권의 주식전환 사유 발생","수시공시","거래소"],
    ["72040","상각형 조건부자본증권의 채무재조정 사유 발생","수시공시","거래소"],
    ["72041","자기주식 취득 결정","수시공시","거래소"],
    ["72042","자기주식 처분 결정","수시공시","거래소"],
    ["72043","자기주식취득 신탁계약 체결 결정","수시공시","거래소"],
    ["72044","자기주식취득 신탁계약 해지 결정","수시공시","거래소"],
    ["72045","전환형 조건부자본증권 발행결정","수시공시","거래소"],
    ["72050","투자판단 관련 주요경영사항","수시공시","거래소"],
    ["72058","정보보호 현황(자율공시)","수시공시","거래소"],
    ["72059","기업인수목적회사의 피합병법인 관련 주요경영사항(자율공시)","수시공시","거래소"],
    ["72060","지속가능경영보고서 등 관련사항(자율공시)","수시공시","거래소"],
    ["72066","주주총회 집중일 개최 사유 신고","신고사항","거래소"],
    ["72067","최대주주 변경 관련 의무보유내역(명목회사ㆍ조합 등)","신고사항","거래소"],
    ["72072","코스닥시장상장외국법인 외부감사인 선임ㆍ해임 신고서","수시공시","거래소"],
    ["72073","근무혁신 우수기업 선정(자율공시)","수시공시","거래소"],
    ["72078","이사회의 성별 구성의무 준수 현황(자율공시)","수시공시","거래소"],
    ["72086","반기 또는 분기 매출액 미달 사실 발생","수시공시","거래소"],
    ["72087","현금ㆍ현물배당을 위한 주주명부폐쇄(기준일) 결정","수시공시","거래소"],
    ["72093","투자판단 관련 주요경영사항(임상시험 계획 승인신청)","수시공시","거래소"],
    ["72094","투자판단 관련 주요경영사항(임상시험 계획 승인 등 결정)","수시공시","거래소"],
    ["72095","투자판단 관련 주요경영사항(임상시험 결과)","수시공시","거래소"],
    ["72096","투자판단 관련 주요경영사항(임상시험계획 자진취하 등)","수시공시","거래소"],
    ["72097","투자판단 관련 주요경영사항(임상시험계획 변경승인신청)","수시공시","거래소"],
    ["72098","투자판단 관련 주요경영사항(임상시험계획 변경승인)","수시공시","거래소"]
]

# 컬럼명 설정
columns = ["서식코드", "서식명", "대분류", "구분"]

# DataFrame 생성
df_svc = pd.DataFrame(df_data, columns=columns)

# 지원대상 데이터 리스트 (df_data 정의)
df_data_comp = [
    ["34821","넥스틴","상장"],
    ["31966","피에스케이","상장"],
    ["29349","카카오게임즈","상장"],
    ["09199","셀트리온헬스케어","상장폐지"],
    ["27229","이녹스첨단소재","상장"],
    ["16609","하나머티리얼즈","상장"],
    ["26375","펄어비스","상장"],
    ["00338","하림지주","상장"],
    ["27828","천보","상장"],
    ["26798","매일유업","상장"],
    ["09561","테스","상장"],
    ["23769","에스티팜","상장"],
    ["24307","휴온스","상장"],
    ["14502","휴젤","상장"],
    ["24754","에코프로비엠","상장"],
    ["24081","원익IPS","상장"],
    ["23036","에코마케팅","상장"],
    ["21342","덕산네오룩스","상장"],
    ["21520","메가스터디교육","상장"],
    ["21500","골프존","상장"],
    ["21445","파마리서치","상장"],
    ["21415","클래시스","상장"],
    ["19617","알테오젠","상장"],
    ["20013","콜마비앤에이치","상장"],
    ["19594","HK이노엔","상장"],
    ["13740","피엔티","상장"],
    ["02210","포스코DX","상장폐지"],
    ["08437","유진테크","상장"],
    ["18330","코미코","상장"],
    ["13129","티에스이","상장"],
    ["06025","NHN KCP","상장"],
    ["06731","하나마이크론","상장"],
    ["09846","고영","상장"],
    ["05619","에스에프에이","상장"],
    ["07460","원익QnC","상장"],
    ["06908","웹젠","상장"],
    ["06697","엘앤에프","상장폐지"],
    ["08485","아이티엠반도체","상장"],
    ["04689","서울반도체","상장"],
    ["14108","리가켐바이오","상장"],
    ["03590","JYP Ent.","상장"],
    ["03693","주성엔지니어링","상장"],
    ["03683","솔브레인홀딩스","상장"],
    ["08645","동국제약","상장"],
    ["03903","이오테크닉스","상장"],
    ["03576","CJ ENM","상장"],
    ["04907","인탑스","상장"],
    ["05847","리노공업","상장"],
    ["09170","파트론","상장"],
    ["06476","티씨케이","상장"]
]

# 컬럼명 설정
columns_comp = ["회사코드", "회사명", "상장여부"]

# DataFrame 생성
df_listed = pd.DataFrame(df_data_comp, columns=columns_comp)


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

# 첫번째 칼럼: 지원대상공시서식기준
with col1:
    st.subheader('지원대상 공시서식 (2025.3.12 기준)')
    st.dataframe(df_svc)

# 두번째 칼럼: 지원대상 회사목록
with col2:
    st.subheader('지원대상 회사 목록')
    st.dataframe(st.session_state.df_listed)

# 세번째 칼럼: 회사코드, 회사명, 지원대상법인 추가 버튼(세로로 배열)
with col3:
    st.subheader('지원대상법인 추가')
    
    # 세션 상태 키로 필드 추적
    st.text("""※ '지원대상법인 추가' 기능은 '임시추가'용도입니다.
   따라서 페이지가 새로고침되면 다시 입력해야 합니다.
   영구적으로 추가하려면 담당자에게 문의부탁드립니다.""")
    company_code = st.text_input("회사코드", max_chars=5, key="company_code")
    st.text("""※ 회사코드는 종목코드(숫자 여섯자리)가 아니라 회사코드입니다. 
   회사코드는 대부분 종목코드 여섯자리의 앞 5개이긴하지만, 
   외국법인/DR의 회사코드는 알파벳이 포함되어 있습니다.""")
    company_name = st.text_input("회사명", key="company_name")
    
    # 버튼 클릭 시 콜백 함수 호출
    if st.button("지원대상법인 추가", on_click=add_company):
        st.success(f"{st.session_state.company_name} 회사가 추가되었습니다.")

# 필터링에 사용될 df_listed 업데이트
df_listed = st.session_state.df_listed

# 버튼 생성
if st.button('금일 코스닥 영문공시 지원대상 공시조회'):
    # 로딩 표시
    with st.spinner('데이터를 가져오는 중입니다...'):
        # 오늘 날짜를 YYYY-MM-DD 형식으로 변환
        today_date = datetime.today().strftime("%Y-%m-%d")
        
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

        response = requests.post(url, params=params)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 총 건수와 페이지 수 추출
        total_items_element = soup.select_one('.info.type-00 em')
        total_pages_text = soup.select_one('.info.type-00').text.strip()
        total_pages_match = re.search(r'(\d+)/(\d+)', total_pages_text)

        if total_items_element and total_pages_match:
            total_items = int(total_items_element.text.strip().replace(",",""))
            total_pages = int(total_pages_match.group(2))
            
            st.info(f"총 {total_items}건의 공시 데이터가 있습니다. (총 {total_pages}페이지)")
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
        st.subheader('금일 코스닥 지원대상 공시 목록')
        
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
