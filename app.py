import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import datetime
import requests
from bs4 import BeautifulSoup

# ==========================================
# 0. 설정
# ==========================================
st.set_page_config(
    page_title="주식주신 PRO",
    page_icon="🔥",
    layout="centered"
)

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
# 1. 종목 데이터
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

stock_names = list(STOCK_MAP.keys())

def resolve_stock_code(name):
    return STOCK_MAP.get(name)

# ==========================================
# 2. 데이터
# ==========================================
@st.cache_data(ttl=60)
def get_stock_data(code):
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=30)
    df = fdr.DataReader(code, start, end)
    return df if not df.empty else None

# ==========================================
# 3. 뉴스
# ==========================================
@st.cache_data(ttl=300)
def get_realtime_news(code):
    try:
        url = f"https://finance.naver.com/item/news.naver?code={code}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        news = []
        titles = soup.select("td.title a")

        for t in titles[:3]:
            news.append({
                "title": t.get_text(strip=True),
                "link": "https://finance.naver.com" + t["href"]
            })

        return news
    except:
        return []

# ==========================================
# 4. 분석
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

    prev_volume = int(df.iloc[-2]["Volume"])
    vol_trend = "📈 증가" if volume > prev_volume else "📉 감소" if volume < prev_volume else "➖ 동일"

    vol_score = min(max(int(volume / avg_vol * 50), 10), 95)

    price_pos = (current - low) / max(high - low, 1) * 100
    up_score = min(max(int(price_pos * 0.7 + change_pct * 5), 5), 98)

    # 세력 유입
    volume_ratio = volume / avg_vol
    force_score = (
        min(volume_ratio * 40, 60) +
        min(max(change_pct * 2, 0), 40)
    )
    force_score = round(min(max(force_score, 0), 100), 1)

    # 포지션
    if up_score >= 70:
        position = "🔥 상승 우세"
        color = "#FF4B4B"
        ai = "거래량 증가 + 상승 흐름 유지"
    elif up_score <= 35:
        position = "⚠ 약세"
        color = "#1F77B4"
        ai = "하락 압력 존재"
    else:
        position = "👀 관망"
        color = "#FFA500"
        ai = "횡보 구간"

    return {
        "current": current,
        "change": change,
        "change_pct": change_pct,
        "high": high,
        "low": low,
        "volume": volume,
        "vol_trend": vol_trend,
        "vol_score": vol_score,
        "up_score": up_score,
        "force_score": force_score,
        "position": position,
        "color": color,
        "ai": ai,
        "buy": int(low * 1.003),
        "sell": int(high * 0.997),
        "estimated_target": int(current * (1 + up_score / 100 * 0.05))
    }

# ==========================================
# 5. UI
# ==========================================
st.title("📊 주식 분석실")

# 🔥 한글 검색 + 자동완성
search = st.text_input("종목 검색 (한글)")

filtered = [name for name in stock_names if search in name] if search else []

selected_name = st.selectbox(
    "종목 선택",
    filtered if filtered else stock_names
)

btn = st.button("🚀 분석 시작")

# ==========================================
# 6. 실행
# ==========================================
if btn:

    code = resolve_stock_code(selected_name)

    df = get_stock_data(code)

    if df is None:
        st.error("데이터 없음")
        st.stop()

    result = analyze(df)

    # 현재가
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

    # 핵심 지표
    st.subheader("📊 핵심 분석 지표")

    st.dataframe(pd.DataFrame({
        "항목": [
            "고가", "저가", "거래량", "거래량 변화",
            "거래 집중도", "상승 점수", "세력 유입", "예상 상승가"
        ],
        "값": [
            f"{result['high']:,}",
            f"{result['low']:,}",
            f"{result['volume']:,} ({result['vol_trend']})",
            result['vol_trend'],
            f"{result['vol_score']}%",
            f"{result['up_score']}%",
            f"{result['force_score']}%",
            f"{result['estimated_target']:,}원"
        ]
    }), hide_index=True)

    # 시장 체크
    st.subheader("🎯 시장 체크 포인트")
    st.write(f"• 매수가: {result['buy']:,}원")
    st.write(f"• 매도가: {result['sell']:,}원")
    st.write(f"• 지지선: {result['low']:,}원")
    st.write(f"• 저항선: {result['high']:,}원")

    # 세력 유입
    st.subheader("🧠 세력 유입 가능성")

    if result["force_score"] >= 70:
        st.markdown(f"🔥 강한 유입 ({result['force_score']}%)")
    elif result["force_score"] >= 40:
        st.markdown(f"👀 중간 유입 ({result['force_score']}%)")
    else:
        st.markdown(f"😐 약한 유입 ({result['force_score']}%)")

    # 차트
    st.subheader("📈 최근 5일")
    recent = df.tail(5)
    recent.index = pd.to_datetime(recent.index).strftime("%m/%d")
    st.line_chart(recent["Close"])

    # AI
    st.subheader("💡 AI 분석")
    st.info(result["ai"])

    # 뉴스
    st.subheader("📰 뉴스")

    news = get_realtime_news(code)

    if news:
        for n in news:
            st.markdown(f"• [{n['title']}]({n['link']})")
    else:
        st.write("뉴스 없음")