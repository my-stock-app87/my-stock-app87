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
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 세션
# ==========================================
if "page" not in st.session_state:
    st.session_state.page = "intro"

# ==========================================
# 3. 종목 데이터
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
# 4. 종목 코드 변환 함수 (핵심)
# ==========================================
def resolve_stock_code(user_input):

    user_input = user_input.strip()

    if user_input.isdigit() and len(user_input) == 6:
        return user_input

    if user_input in STOCK_MAP:
        return STOCK_MAP[user_input]

    return None

# ==========================================
# 5. 데이터 로딩
# ==========================================
@st.cache_data(ttl=60)
def get_stock_data(code):
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=30)

    df = fdr.DataReader(code, start, end)
    return df if not df.empty else None

# ==========================================
# 6. 실시간 뉴스 크롤링 함수 (추가)
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
        
        for title in titles[:3]:  # 상위 3개 뉴스만 추출
            text = title.get_text(strip=True)
            href = title["href"]
            # 네이버 금융 뉴스 링크 주소 완성
            link = f"https://naver.com{href}"
            news_list.append({"title": text, "link": link})
            
        return news_list
    except:
        return []

# ==========================================
# 7. 분석 로직
# ==========================================
def analyze(df):

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    current = int(latest["Close"])
    prev_close = int(prev["Close"])

    high = int(latest["High"])
    low = int(latest["Low"])
    volume = int(latest["Volume"])

    change = current - prev_close
    change_pct = round((change / prev_close) * 100, 2)

    avg_vol = df["Volume"].tail(5).mean()
    vol_score = min(max(int(volume / avg_vol * 50), 10), 95)

    price_pos = (current - low) / max(high - low, 1) * 100
    up_score = min(max(int(price_pos * 0.7 + change_pct * 5), 5), 98)

    # 포지션
    if up_score >= 70:
        position = "🔥 상승 우세"
        color = "#FF4B4B"
    elif up_score <= 35:
        position = "⚠ 약세"
        color = "#1F77B4"
    else:
        position = "👀 관망"
        color = "#FFA500"

    # AI 코멘트
    if "상승" in position:
        ai = "거래량 증가 + 상승 흐름 유지. 눌림 매수 전략 유효."
    elif "약세" in position:
        ai = "하락 압력 존재. 신규 진입은 보수적으로."
    else:
        ai = "횡보 구간. 거래량 변화 확인 필요."

    # [수정] 예상 상승가 계산 로직 추가 (상승 점수와 최근 변동성을 기반으로 산출)
    estimated_target = int(current * (1 + (up_score / 100) * 0.05))

    return {
        "current": current,
        "change": change,
        "change_pct": change_pct,
        "high": high,
        "low": low,
        "volume": volume,
        "vol_score": vol_score,
        "up_score": up_score,
        "position": position,
        "color": color,
        "ai": ai,
        "buy": int(low * 1.003),
        "sell": int(high * 0.997),
        "estimated_target": estimated_target  # 반환 값에 추가
    }

# ==========================================
# 8. INTRO
# ==========================================
if st.session_state.page == "intro":

    st.markdown("<h1 style='text-align:center;'>🔥 주식주신 PRO</h1>", unsafe_allow_html=True)

    if st.button("분석 시작"):
        st.session_state.page = "analysis"
        st.rerun()

# ==========================================
# 9. ANALYSIS
# ==========================================
else:

    if st.button("🏠 홈"):
        st.session_state.page = "intro"
        st.rerun()

    st.title("📊 주식 분석실")

    user_input = st.text_input("종목명 또는 6자리 코드 입력")
    btn = st.button("🚀 분석 시작")

    if btn and user_input:

        # ==============================
        # 코드 변환 (한글 검색 지원)
        # ==============================
        code = resolve_stock_code(user_input)

        if code is None:
            st.error("종목명을 정확히 입력하세요 (예: 삼성전자, 카카오, 005930)")
            st.stop()

        df = get_stock_data(code)

        if df is None:
            st.error("데이터를 불러올 수 없습니다.")
            st.stop()

        result = analyze(df)

        # ==============================
        # 현재가
        # ==============================
        st.metric(
            "현재가",
            f"{result['current']:,}원",
            f"{result['change']:,} ({result['change_pct']}%)"
        )

        st.markdown(
            f"<div style='color:{result['color']}; font-size:20px;'>"
            f"{result['position']}</div>",
            unsafe_allow_html=True
        )

        st.write("")

        # ==============================
        # 핵심 지표 (예상 상승가 항목 추가)
        # ==============================
        st.subheader("📊 핵심 분석 지표")

        st.dataframe(pd.DataFrame({
            "항목": ["고가", "저가", "거래량", "거래 집중도", "상승 점수", "예상 상승가"],
            "값": [
                f"{result['high']:,}",
                f"{result['low']:,}",
                f"{result['volume']:,}",
                f"{result['vol_score']}%",
                f"{result['up_score']}%",
                f"{result['estimated_target']:,}원"  # 데이터 테이블에 반영
            ]
        }), hide_index=True)

        # ==============================
        # 시장 체크 포인트 (핵심지표 아래)
        # ==============================
        st.subheader("🎯 시장 체크 포인트")

        st.write(f"• 추천 매수가: {result['buy']:,}원")
        st.write(f"• 추천 매도가: {result['sell']:,}원")
        st.write(f"• 단기 지지선: {result['low']:,}원")
        st.write(f"• 단기 저항선: {result['high']:,}원")

        st.write("")

        # ==============================
        # 최근 5일 차트
        # ==============================
        st.subheader("📈 최근 5일 주가 흐름")

        recent = df.tail(5).copy()
        recent.index = pd.to_datetime(recent.index).strftime("%m/%d")

        chart = recent[["Close"]]
        chart.columns = ["종가"]

        st.line_chart(chart)

        st.caption("최근 5거래일 기준")

        # ==============================
        # AI 코멘트
        # ==============================
        st.subheader("💡 AI 분석 코멘트")

        st.info(result["ai"])

        # ==============================
        # 뉴스 (실시간 크롤링 연동)
        # ==============================
        st.subheader("📰 시장 뉴스")

        # [수정] 네이버 금융에서 해당 종목 실시간 뉴스를 긁어와 노출
        news_data = get_realtime_news(code)
        
        if news_data:
            for item in news_data:
                st.markdown(f"• [{item['title']}]({item['link']})")
        else:
            st.write("• 실시간 관련 뉴스를 불러올 수 없습니다.")
