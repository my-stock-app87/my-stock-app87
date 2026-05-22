import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import datetime
import requests
import json
from bs4 import BeautifulSoup

# ==========================================
# 0. 앱 설정
# ==========================================
st.set_page_config(
    page_title="주식주신PRO",
    page_icon="🔥",
    layout="centered"
)

# ==========================================
# 1. 스타일
# ==========================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to bottom, #0F172A, #111827);
    color: white;
}

.stButton>button {
    background-color: #FF4B4B;
    color: white;
    border-radius: 10px;
    height: 45px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 세션
# ==========================================
if "page" not in st.session_state:
    st.session_state.page = "intro"

# ==========================================
# 3. 종목 데이터 (기본 고정 맵)
# ==========================================
STOCK_MAP = {
    "삼성전자": "005930",
    "카카오": "035720",
    "네이버": "035420",
    "sk하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "현대차": "005380",
    "기아": "000270",
    "삼성바이오로직스": "207940"
}

# ==========================================
# 4. 종목 코드 및 실제 이름 변환 함수 (수정 반영)
# ==========================================
def resolve_stock_code_and_name(user_input):
    user_input = user_input.strip()

    # 1. 사용자가 이미 6자리 숫자를 입력한 경우 (네이버 검색을 통해 실제 종목명 조회)
    if user_input.isdigit() and len(user_input) == 6:
        try:
            url = f"https://naver.com{user_input}&q_enc=utf-8&st=111&frm=stock&r_format=json"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                items = data.get("items", [[]])[0]
                if items:
                    # 네이버 반환 구조: [[["종목명", "코드", "초성", ...]]]
                    return items[0][0][0], user_input
        except Exception:
            pass
        return user_input, user_input

    # 2. 고정 맵(STOCK_MAP)에 등록되어 있는 이름인 경우 우선 처리
    if user_input in STOCK_MAP:
        return user_input, STOCK_MAP[user_input]

    # 3. [핵심] 네이버 금융 검색 API 연동 (에러 완벽 방지 및 실시간 매칭)
    try:
        url = f"https://naver.com{user_input}&q_enc=utf-8&st=111&frm=stock&r_format=json"
        res = requests.get(url, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            items = data.get("items", [[]])[0]  # 검색결과 리스트 추출
            
            if items:
                # 검색어와 가장 연관성 높은 첫 번째 항목의 실제 이름과 코드 매칭
                actual_name = items[0][0][0]
                stock_code = items[0][1][0]
                return actual_name, stock_code
    except Exception:
        pass

    return None, None

# ==========================================
# 5. 데이터 로딩
# ==========================================
@st.cache_data(ttl=60)
def get_stock_data(code):
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=30)
    try:
        df = fdr.DataReader(code, start, end)
        return df if not df.empty else None
    except Exception:
        return None

# ==========================================
# 6. 실시간 뉴스 크롤링 함수
# ==========================================
@st.cache_data(ttl=300)
def get_realtime_news(code):
    try:
        url = f"https://naver.com{code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        titles = soup.select(".title a")
        sources = soup.select(".info")
        dates = soup.select(".date")
        
        news_list = []
        for i in range(min(5, len(titles))):
            title_text = titles[i].get_text(strip=True)
            link = "https://finance.naver.com" + titles[i]["href"]
            source_text = sources[i].get_text(strip=True) if i < len(sources) else "알 수 없음"
            date_text = dates[i].get_text(strip=True) if i < len(dates) else ""
            
            news_list.append({
                "title": title_text,
                "link": link,
                "source": source_text,
                "date": date_text
            })
        return news_list
    except Exception:
        return []

# ==========================================
# 7. 페이지 전환 함수
# ==========================================
def move_page(page_name):
    st.session_state.page = page_name
    st.rerun()

# ==========================================
# 8. 인트로 페이지 (intro)
# ==========================================
if st.session_state.page == "intro":
    st.title("🔥 주식주신 PRO")
    st.subheader("스마트한 실시간 주가 조회의 시작")
    st.write("종목명 또는 6자리 종목코드를 입력하여 실시간 차트와 최신 뉴스를 확인하세요.")
    
    user_input = st.text_input("종목 입력 (예: 삼성전자, 현대차, 000660)", key="stock_search_input")
    
    if st.button("주가 조회하기"):
        if user_input:
            name, code = resolve_stock_code_and_name(user_input)
            if code and name:
                st.session_state.selected_code = code
                st.session_state.selected_name = name  # 추출한 '실제 주식이름' 저장
                move_page("main")
            else:
                st.error("올바른 종목명 또는 종목코드를 입력해 주세요.")
        else:
            st.warning("검색어를 입력해 주세요.")

# ==========================================
# 9. 메인 대시보드 페이지 (main)
# ==========================================
elif st.session_state.page == "main":
    code = st.session_state.get("selected_code")
    name = st.session_state.get("selected_name")
    
    # 수정 핵심: 번호로 검색해도 정확한 이름과 함께 타이틀 출력
    st.title(f"📈 {name} ({code}) 분석 리포트")
    
    if st.button("🏠 홈으로 돌아가기"):
        move_page("intro")
        
    # 데이터 로드
    df = get_stock_data(code)
    
    if df is not None:
        st.subheader("📊 최근 30일 주가 추이")
        st.line_chart(df["Close"])
        
        with st.expander("전체 데이터 보기"):
            st.dataframe(df.tail(10))
    else:
        st.warning("주가 데이터를 불러오지 못했습니다.")
        
    # 뉴스 로드
    st.markdown("---")
    st.subheader("📰 최신 관련 뉴스")
    news_data = get_realtime_news(code)
    
    if news_data:
        for news in news_data:
            st.markdown(f"**[{news['title']}]({news['link']})**")
            st.caption(f"{news['source']} | {news['date']}")
            st.write("")
    else:
        st.write("가져올 수 있는 최신 뉴스가 없습니다.")
