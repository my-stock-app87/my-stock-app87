import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# =========================
# 데이터 로딩
# =========================
def load_data(code):
    try:
        df = yf.download(code, period="6mo", interval="1d")

        if df is None or df.empty:
            return None

        df = df.dropna()
        df = df.sort_index()

        return df

    except:
        return None


# =========================
# 특징 계산
# =========================
def build_features(df):

    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)

    returns = close.pct_change().dropna()

    if len(returns) == 0:
        return None

    momentum = float((returns > 0.02).sum() - (returns < -0.02).sum())

    volatility = float(returns.std()) if not np.isnan(returns.std()) else 0.0

    vol_mean = volume.rolling(20).mean().iloc[-1]
    vol_std = volume.rolling(20).std().iloc[-1]

    volume_z = 0.0
    if vol_std and not np.isnan(vol_std):
        volume_z = (volume.iloc[-1] - vol_mean) / (vol_std + 1e-9)

    support = float(close.rolling(20).min().iloc[-1])
    resistance = float(close.rolling(20).max().iloc[-1])
    price = float(close.iloc[-1])

    support_dist = (price - support) / price
    resistance_dist = (resistance - price) / price

    trend = float(returns.mean())

    return {
        "momentum": momentum,
        "volatility": volatility,
        "volume_z": float(volume_z),
        "support_dist": float(support_dist),
        "resistance_dist": float(resistance_dist),
        "trend": trend,
        "price": price
    }


# =========================
# 점수
# =========================
def score(features):

    if features is None:
        return None

    vol = features["volatility"]

    compression = max(0.0, 1 - vol * 10)

    volume_score = min(100.0, abs(features["volume_z"]) * 20)

    structure_score = (
        max(0.0, 1 - features["support_dist"]) * 50 +
        max(0.0, 1 - features["resistance_dist"]) * 50
    )

    momentum_score = features["momentum"] * 10
    trend_score = features["trend"] * 1000

    final_score = (
        compression * 30 +
        volume_score * 0.25 +
        structure_score * 0.2 +
        momentum_score * 0.15 +
        trend_score * 0.1
    )

    return {
        "compression": round(compression, 3),
        "volume_score": round(volume_score, 2),
        "structure_score": round(structure_score, 2),
        "momentum_score": round(momentum_score, 2),
        "trend_score": round(trend_score, 2),
        "final_score": round(final_score, 2)
    }


# =========================
# 해석
# =========================
def explain(s):

    if s > 70:
        return "🟢 강세 구간", "#00C853"
    elif s > 45:
        return "🟡 관찰 구간", "#FFD600"
    else:
        return "🔴 약세 구간", "#D50000"


# =========================
# 분석 실행
# =========================
def run_analysis(code, df):

    if df is None:
        return {"error": "데이터 없음 (종목 코드 확인)"}

    features = build_features(df)

    if features is None:
        return {"error": "특징 계산 실패"}

    scores = score(features)

    if scores is None:
        return {"error": "점수 계산 실패"}

    label, color = explain(scores["final_score"])

    return {
        "종목": code,
        "현재가": features["price"],
        **features,
        **scores,
        "상태": label,
        "color": color
    }


# =========================
# UI
# =========================
st.title("📊 AI 주식 분석 엔진 (안정화 버전)")

code = st.text_input("종목 코드 (예: AAPL / TSLA / 005930.KS)")

if st.button("분석하기"):

    if not code:
        st.warning("종목 코드를 입력하세요")

    else:
        df = load_data(code)

        if df is None:
            st.error("데이터를 불러올 수 없습니다. 종목 코드를 확인하세요.")
        else:
            result = run_analysis(code, df)

            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader("결과")
                st.write(result)

                st.markdown(
                    f"<h2 style='color:{result['color']}'>{result['상태']}</h2>",
                    unsafe_allow_html=True
                )
