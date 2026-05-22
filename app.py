import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# 데이터
# =========================
def load_data(code):
    df = yf.download(code, period="6mo", interval="1d")
    if df is None or df.empty:
        return None
    return df.dropna()


# =========================
# 특징
# =========================
def build_features(df):

    close = df["Close"]
    volume = df["Volume"]

    returns = close.pct_change().dropna()

    momentum = (returns > 0.02).sum() - (returns < -0.02).sum()
    volatility = returns.std()

    vol_z = (volume.iloc[-1] - volume.rolling(20).mean().iloc[-1]) / (volume.rolling(20).std().iloc[-1] + 1e-9)

    support = close.rolling(20).min().iloc[-1]
    resistance = close.rolling(20).max().iloc[-1]
    price = close.iloc[-1]

    return {
        "price": price,
        "momentum": momentum,
        "volatility": volatility,
        "vol_z": vol_z,
        "support": support,
        "resistance": resistance
    }


# =========================
# 점수
# =========================
def score(f):

    compression = max(0, 1 - f["volatility"] * 10)
    volume_score = min(100, abs(f["vol_z"]) * 20)
    structure_score = (f["price"] - f["support"]) + (f["resistance"] - f["price"])

    final = compression*30 + volume_score*0.3 + structure_score*0.2 + f["momentum"]*5

    return round(final, 2)


# =========================
# 차트
# =========================
def plot_chart(df):

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Close"], label="Close Price")
    ax.set_title("Price Chart")
    ax.legend()

    st.pyplot(fig)


# =========================
# UI
# =========================
st.title("📊 진짜 전체 AI 분석 시스템")

code = st.text_input("종목 코드 (AAPL / TSLA / 005930.KS)")

if st.button("분석 실행"):

    df = load_data(code)

    if df is None:
        st.error("데이터 없음 (코드 확인)")
    else:

        f = build_features(df)
        s = score(f)

        # 차트
        plot_chart(df)

        # 결과
        st.subheader("📌 분석 결과")

        col1, col2, col3 = st.columns(3)
        col1.metric("현재가", f["price"])
        col2.metric("점수", s)
        col3.metric("변동성", round(f["volatility"], 4))

        st.write("상세 데이터")
        st.json(f)
