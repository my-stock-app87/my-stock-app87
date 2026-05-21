import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

# =========================================================
# 설정
# =========================================================
st.set_page_config(page_title="전체시장 HTS", layout="wide")
st.title("🔥 전체시장 실시간 대시보드")

# =========================================================
# 현실적인 전체시장 (KRX 대표군)
# =========================================================
STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "POSCO홀딩스": "005490.KS",
    "에코프로": "086520.KQ",
    "에코프로비엠": "247540.KQ",
    "HLB": "028300.KQ",
    "한화에어로": "012450.KS",
    "두산에너빌리티": "034020.KS",
}

# =========================================================
# 데이터
# =========================================================
@st.cache_data(ttl=60)
def get_data(ticker):
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        return df.dropna()
    except:
        return pd.DataFrame()

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
# 분석
# =========================================================
def analyze(name, ticker):

    df = get_data(ticker)
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
        "상태": (
            "🚀 급등" if l["Whale"] > 75 and change > 3 else
            "🎯 반등" if l["RSI"] < 35 else
            "⚠️ 과열" if l["RSI"] > 80 else
            "🐳 세력" if l["Whale"] > 70 else
            "⚪ 관망"
        )
    }

# =========================================================
# 전체 스캔
# =========================================================
results = []

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(analyze, n, t) for n, t in STOCKS.items()]

    for f in futures:
        r = f.result()
        if r:
            results.append(r)

df = pd.DataFrame(results)

# =========================================================
# 📊 시장 상태
# =========================================================
st.subheader("📊 시장 전체 현황")

col1, col2, col3 = st.columns(3)

col1.metric("상승", len(df[df["등락률"] > 0]))
col2.metric("하락", len(df[df["등락률"] < 0]))
col3.metric("세력", len(df[df["세력"] > 70]))

# =========================================================
# 전체 테이블
# =========================================================
st.dataframe(df.sort_values("세력", ascending=False), use_container_width=True)

# =========================================================
# 🔥 급등
# =========================================================
st.subheader("🚀 급등")

st.dataframe(
    df[df["상태"] == "🚀 급등"]
    .sort_values("등락률", ascending=False)
)

# =========================================================
# 🎯 반등
# =========================================================
st.subheader("🎯 반등")

st.dataframe(
    df[df["상태"] == "🎯 반등"]
    .sort_values("RSI")
)

# =========================================================
# ⚠️ 과열
# =========================================================
st.subheader("⚠️ 과열")

st.dataframe(
    df[df["RSI"] > 80].sort_values("RSI", ascending=False)
)