import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(page_title="주식 전체 + 검색", layout="wide")
st.title("🔥 전체시장 + 종목검색 실시간 대시보드")

# =========================================================
# 대표 종목 (시장 전체 분위기용)
# =========================================================
STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "POSCO홀딩스": "005490.KS",
    "에코프로": "086520.KQ",
    "에코프로비엠": "247540.KQ",
    "HLB": "028300.KQ",
}

# =========================================================
# 데이터
# =========================================================
@st.cache_data(ttl=60)
def get_price(ticker):
    df = yf.Ticker(ticker).history(period="6mo")
    return df.dropna() if not df.empty else pd.DataFrame()

# =========================================================
# 지표
# =========================================================
def make(df):
    if len(df) < 30:
        return None

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)

    rs = up.rolling(14).mean() / (down.rolling(14).mean() + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    df["Whale"] = np.clip(
        (df["Volume"] / (df["VOL20"] + 1e-10)) * 40 +
        ((df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)) * 50,
        0, 100
    )

    return df.dropna()

# =========================================================
# 시장 스캔
# =========================================================
def scan(name, ticker):
    df = get_price(ticker)
    df = make(df)

    if df is None or df.empty:
        return None

    l = df.iloc[-1]
    p = df.iloc[-2]

    change = (l["Close"] - p["Close"]) / p["Close"] * 100

    return {
        "종목": name,
        "현재가": int(l["Close"]),
        "등락률": round(change, 2),
        "세력": round(l["Whale"], 1),
        "RSI": round(l["RSI"], 1),
    }

# =========================================================
# 1️⃣ 전체 시장 분석
# =========================================================
results = []

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(scan, n, t) for n, t in STOCKS.items()]
    for f in futures:
        r = f.result()
        if r:
            results.append(r)

df = pd.DataFrame(results)

st.subheader("📊 시장 전체 현황")

col1, col2 = st.columns(2)
col1.metric("상승 종목", len(df[df["등락률"] > 0]))
col2.metric("하락 종목", len(df[df["등락률"] < 0]))

st.dataframe(df, use_container_width=True)

# =========================================================
# 2️⃣ 종목 검색 기능 (핵심)
# =========================================================
st.subheader("🔍 종목 검색")

query = st.text_input("종목명 입력 (예: 삼성전자, NAVER, TSLA)")

if query:

    ticker_map = {
        "삼성전자": "005930.KS",
        "SK하이닉스": "000660.KS",
        "NAVER": "035420.KS",
        "카카오": "035720.KS",
        "현대차": "005380.KS",
        "기아": "000270.KS",
        "테슬라": "TSLA",
        "애플": "AAPL",
    }

    ticker = ticker_map.get(query)

    if ticker:

        d = get_price(ticker)

        if not d.empty:

            last = d.iloc[-1]
            prev = d.iloc[-2]

            price = int(last["Close"])
            pct = (price - prev["Close"]) / prev["Close"] * 100

            st.success(f"""
            📌 {query} 현재가: {price:,}  
            📈 등락률: {pct:+.2f}%  
            📊 거래량: {int(last['Volume']):,}
            """)

            st.line_chart(d["Close"])

    else:
        st.warning("지원되지 않는 종목입니다 (현재는 일부만 가능)")