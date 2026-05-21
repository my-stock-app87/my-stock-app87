import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import FinanceDataReader as fdr
from concurrent.futures import ThreadPoolExecutor

# =========================================================
# 설정
# =========================================================
st.set_page_config(page_title="KRX 전체시장 FULL", layout="wide")
st.title("🔥 KRX 전체시장 FULL 스캐너 + 검색")

# =========================================================
# KRX 전체 종목
# =========================================================
@st.cache_data(ttl=86400)
def load_krx():
    df = fdr.StockListing("KRX")[["Code", "Name"]].dropna()
    df["Ticker"] = df["Code"].astype(str).str.zfill(6) + ".KS"
    return df

stocks = load_krx()

# =========================================================
# 데이터
# =========================================================
@st.cache_data(ttl=60)
def get_data(ticker):
    try:
        return yf.Ticker(ticker).history(period="6mo").dropna()
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
def analyze(row):

    df = get_data(row["Ticker"])
    df = make(df)

    if df is None or df.empty:
        return None

    l = df.iloc[-1]
    p = df.iloc[-2]

    change = (l["Close"] - p["Close"]) / p["Close"] * 100

    return {
        "종목": row["Name"],
        "현재가": int(l["Close"]),
        "등락률": round(change, 2),
        "세력": round(l["Whale"], 1),
        "RSI": round(l["RSI"], 1),
    }

# =========================================================
# 🔥 FULL 스캔 (느리지만 전체)
# =========================================================
LIMIT = st.slider("스캔 종목 수 (전체=느림)", 100, 2000, 300)

progress = st.progress(0)
results = []

with ThreadPoolExecutor(max_workers=10) as ex:

    futures = []
    for i, row in stocks.head(LIMIT).iterrows():
        futures.append(ex.submit(analyze, row))

    for i, f in enumerate(futures):
        r = f.result()
        if r:
            results.append(r)
        progress.progress((i+1)/len(futures))

df = pd.DataFrame(results)

# =========================================================
# 📊 시장 요약
# =========================================================
st.subheader("📊 시장 전체 요약")

col1, col2, col3 = st.columns(3)

col1.metric("상승", len(df[df["등락률"] > 0]))
col2.metric("하락", len(df[df["등락률"] < 0]))
col3.metric("세력", len(df[df["세력"] > 70]))

# =========================================================
# 🔍 검색 기능 (핵심)
# =========================================================
st.subheader("🔍 종목 검색")

q = st.text_input("종목명 검색 (예: 삼성, NAVER, 에코)")

if q:
    filtered = df[df["종목"].str.contains(q)]
    st.dataframe(filtered, use_container_width=True)

# =========================================================
# 전체 테이블
# =========================================================
st.subheader("📊 전체 종목 데이터")

st.dataframe(
    df.sort_values("세력", ascending=False),
    use_container_width=True
)

# =========================================================
# 🚀 급등
# =========================================================
st.subheader("🚀 급등")

st.dataframe(
    df.sort_values("등락률", ascending=False).head(20)
)

# =========================================================
# 🎯 반등
# =========================================================
st.subheader("🎯 반등")

st.dataframe(
    df[df["RSI"] < 35].sort_values("세력", ascending=False).head(20)
)