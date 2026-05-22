import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import datetime
import requests
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
    width: 100%;
}
.news-box {
    background-color: #1E293B;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.news-title {
    font-size: 16px;
    font-weight: bold;
    color: #F8FAFC;
    text-decoration: none;
}
.news-info {
    font-size: 12px;
    color: #94A3B8;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 세션 및 상태 관리
# ==========================================
if "page" not in st.session_state:
    st.session_state.page = "intro"
if "selected_code" not in st.session_state:
    st.session_state.selected_code = None
if "selected_name" not in st.session_state:
    st.session_state.selected_name = ""

# ==========================================
# 3. 전종목 마스터 데이터 로딩 (한글 검색용 핵심 추가)
# ==========================================
@st.cache_data(ttl=86400) # 하루 동안 캐싱
def load_all_krx_stocks():
    try:
        # KRX 전체 상장 종목 리스트 가져오기 (코스피, 코스닥, 코넥스 포함)
        df_krx = fdr.StockListing('KRX')
        # 필요한 컬럼(종목코드, 종목명)만 추출하여 딕셔너리로 변환
        # 검색 효율을 위해 종목명 양끝 공백을 제거하고 대문자로 변환하여 저장
        stock_dict = {str(row['Name']).strip().upper(): str(row['Code']) for _, row in df_krx.iterrows()}
        return stock_dict
    except Exception as e:
        st.error(f"종목 마스터 데이터를 불러오는 데 실패했습니다: {e}")
        return {}

# 앱 시작 시 마스터 데이터 로드
KRX_STOCKS = load_all_krx_stocks()

# ==========================================
# 4. 종목 코드 변환 함수 (전체 종목 대응하도록 수정)
# ==========================================
def resolve_stock_code(user_input):
    user_input = user_input.strip()
    
    # 1. 사용자가 이미 6자리 숫자를 입력한 경우
    if user_input.isdigit() and len(user_input) == 6:
        return user_input, None
    
    # 2. 한글/영문 종목명을 입력한 경우 (대소문자 구분 없음)
    search_name = user_input.upper()
    if search_name in KRX_STOCKS:
        return KRX_STOCKS[search_name], user_input
    
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
    except:
        return None

# ==========================================
# 6. 실시간 뉴스 크롤링 함수
# ==========================================
@st.cache_data(ttl=300)
def get_realtime_news(code):
    try:
        url = f"https://naver.com{code}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        
        news_list = []
        titles = soup.select(".title a")
        info_sources = soup.select(".info")
        info_dates = soup.select(".date")
        
        for i in range(min(5, len(titles))):
            title_text = titles[i].get_text(strip=True)
            link = titles[i]['href']
            if link.startswith('/'):
                link = "https://naver.com" + link
                
            source = info_sources[i].get_text(strip=True) if i < len(info_sources) else "언론사"
            date = info_dates[i].get_text(strip=True) if i < len(info_dates) else ""
            
            news_list.append({
                "title": title_text,
                "link": link,
                "source": source,
                "date": date
            })
        return news_list
    except Exception as e:
        return []

# ==========================================
# 7. 페이지 랜더링 로직
# ==========================================

# --- 인트로 페이지 ---
if st.session_state.page == "intro":
    st.title("🔥 주식주신 PRO")
    st.subheader("대한민국 모든 상장 종목을 한글로 검색하세요.")
    
    user_search = st.text_input("검색어 입력 (예: 삼성전자, 에코프로, 카카오뱅크, 005930)", placeholder="종목명 또는 코드를 입력하세요...")
    search_btn = st.button("주가 분석 및 뉴스 보기")
    
    if search_btn and user_search:
        code, matched_name = resolve_stock_code(user_search)
        if code:
            # 코드로 검색했을 경우 역으로 종목명을 찾아옴
            if not matched_name:
                matched_name = next((k for k, v in KRX_STOCKS.items() if v == code), code)
            
            st.session_state.selected_code = code
            st.session_state.selected_name = matched_name
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("존재하지 않는 종목명이거나 잘못된 코드입니다. 대소문자 및 띄어쓰기를 확인해 주세요.")

# --- 대시보드 페이지 ---
elif st.session_state.page == "dashboard":
    code = st.session_state.selected_code
    name = st.session_state.selected_name
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"📊 {name} ({code})")
    with col2:
        if st.button("처음으로"):
            st.session_state.page = "intro"
            st.rerun()
            
    # 주가 데이터 로드 및 차트 출력
    with st.spinner("주가 데이터를 가져오는 중..."):
        df = get_stock_data(code)
        
    if df is not None and not df.empty:
        st.subheader("📈 최근 30일 주가 추이")
        st.line_chart(df['Close'])
    else:
        st.warning("주가 데이터를 가져오지 못했습니다. (거래정지 종목이거나 코드 오류일 수 있습니다.)")
        
    # 실시간 뉴스 로드 및 출력
    st.subheader("📰 실시간 주요 뉴스")
    with st.spinner("최신 뉴스를 긁어오는 중..."):
        news_items = get_realtime_news(code)
        
    if news_items:
        for item in news_items:
            st.markdown(f"""
            <div class="news-box">
                <a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a>
                <div class="news-info">{item['source']} | {item['date']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("관련 뉴스를 찾을 수 없거나 불러오는데 실패했습니다.")
