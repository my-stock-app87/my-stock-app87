import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

# =========================================================
# 설정
# =========================================================
st.set_page_config(page_title="전체시장 스캐너", layout="wide")
st.title("🔥 KRX 전체시장 실시간 스캐너")

# =========================================================
# KRX 전체 종목 가져오기 (진짜 전체)
# =========================================================
@st.cache_data(ttl=86400)
def load_krx():
    df = fdr.StockListing("KRX")
    df = df[["Code", "Name"]].dropna()
    df["Ticker"] = df["Code"].astype(str).str.zfill(6) + ".KS"
    return df

stocks = load_krx()

# =========================================================
# 데이터
# =========================================================
@st.cache_data(ttl=60)
def get_price(ticker):
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
def analyze(row):

    code = row["Ticker"]
    name = row["Name"]

    df = get_price(code)
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
# 필터 (전체 돌리면 느리니까 현실적 필터)
# =========================================================
stocks = stocks.head(300)   # ← 실전 핵심 (속도 필터)

results = []

progress = st.progress(0)

with ThreadPoolExecutor(max_workers=10) as ex:

    futures = [
        ex.submit(analyze, row)
        for _, row in stocks.iterrows()
    ]

    for i, f in enumerate(futures):

        r = f.result()

        if r:
            results.append(r)

        progress.progress((i+1)/len(futures))

# =========================================================
# 결과
# =========================================================
df = pd.DataFrame(results)

st.subheader("📊 전체 시장 현황")

col1, col2, col3 = st.columns(3)

col1.metric("상승", len(df[df["등락률"] > 0]))
col2.metric("하락", len(df[df["등락률"] < 0]))
col3.metric("세력강함", len(df[df["세력"] > 70]))

# =========================================================
# 전체 테이블
# =========================================================
st.dataframe(
    df.sort_values("세력", ascending=False),
    use_container_width=True
)

# =========================================================
# 급등 TOP
# =========================================================
st.subheader("🚀 급등 TOP")

st.dataframe(
    df.sort_values("등락률", ascending=False).head(20),
    use_container_width=True
)

# =========================================================
# 세력 TOP
# =========================================================
st.subheader("🐳 세력 TOP")

st.dataframe(
    df.sort_values("세력", ascending=False).head(20),
    use_container_width=True
)

# =========================================================
# 반등 TOP
# =========================================================
st.subheader("🎯 반등 TOP")

st.dataframe(
    df[df["RSI"] < 35].sort_values("세력", ascending=False).head(20),
    use_container_width=True
)