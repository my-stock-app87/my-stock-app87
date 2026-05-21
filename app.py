import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

# =========================================================
# 설정
# =========================================================
st.set_page_config(page_title="시장 전체현황", layout="wide")
st.title("🔥 전체 시장 현황 스캐너")

# =========================================================
# 핵심 종목 (실제 서비스도 이 방식 씀)
# =========================================================
STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "셀트리온": "068270.KS",
    "POSCO홀딩스": "005490.KS",
    "에코프로": "086520.KQ",
    "에코프로비엠": "247540.KQ",
    "HLB": "028300.KQ",
    "한화에어로스페이스": "012450.KS",
    "두산에너빌리티": "034020.KS",
}

# =========================================================
# 데이터
# =========================================================
@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.Ticker(ticker).history(period="6mo", interval="1d")
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

    # RSI
    delta = df["Close"].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)

    rs = up.rolling(14).mean() / (down.rolling(14).mean() + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    # 세력
    vol_power = df["Volume"] / (df["VOL20"] + 1e-10)

    trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)

    candle = (df["Close"] - df["Open"]) / (df["Open"] + 1e-10)

    df["Whale"] = np.clip(
        vol_power * 40 +
        trend * 50 +
        candle * 10,
        0, 100
    )

    return df.dropna()

# =========================================================
# 분석 함수
# =========================================================
def analyze(name, ticker):

    df = get_data(ticker)
    df = make(df)

    if df is None or df.empty:
        return None

    l = df.iloc[-1]
    p = df.iloc[-2]

    change = ((l["Close"] - p["Close"]) / p["Close"]) * 100

    # 시장 분류
    if l["Whale"] > 75 and change > 3:
        status = "🚀 급등"
    elif l["RSI"] < 35 and change < 0:
        status = "🎯 반등"
    elif l["RSI"] > 80:
        status = "⚠️ 과열"
    elif l["Whale"] > 70:
        status = "🐳 세력유입"
    else:
        status = "⚪ 관망"

    return {
        "종목": name,
        "현재가": int(l["Close"]),
        "등락률": round(change, 2),
        "세력": round(l["Whale"], 1),
        "RSI": round(l["RSI"], 1),
        "상태": status
    }

# =========================================================
# 실행
# =========================================================
results = []

with ThreadPoolExecutor(max_workers=8) as ex:
    futures = [
        ex.submit(analyze, name, ticker)
        for name, ticker in STOCKS.items()
    ]

    for f in futures:
        r = f.result()
        if r:
            results.append(r)

df = pd.DataFrame(results)

# =========================================================
# 시장 요약
# =========================================================
st.subheader("📊 시장 요약")

up = len(df[df["등락률"] > 0])
down = len(df[df["등락률"] < 0])

st.metric("상승 종목", up)
st.metric("하락 종목", down)

# =========================================================
# 분류 테이블
# =========================================================
st.subheader("🚀 급등 / 🎯 반등 / 🐳 세력 / ⚠️ 과열")

st.dataframe(df.sort_values("세력", ascending=False), use_container_width=True)

# =========================================================
# 급등
# =========================================================
st.subheader("🚀 급등 TOP")

st.dataframe(
    df[df["상태"] == "🚀 급등"]
    .sort_values("등락률", ascending=False)
)

# =========================================================
# 반등
# =========================================================
st.subheader("🎯 반등 TOP")

st.dataframe(
    df[df["상태"] == "🎯 반등"]
    .sort_values("RSI")
)

# =========================================================
# 과열
# =========================================================
st.subheader("⚠️ 과열")

st.dataframe(
    df[df["상태"] == "⚠️ 과열"]
    .sort_values("RSI", ascending=False)
)