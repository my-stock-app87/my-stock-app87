import streamlit as st
import pandas as pd
import yfinance as yf

# =========================
# 데이터 로딩
# =========================
def load_data(code):
    df = yf.download(code, period="3mo", interval="1d")
    df = df.dropna()
    df = df.sort_index()
    return df


# =========================
# 1. 특징 계산
# =========================
def build_features(df):

    returns = df["Close"].pct_change()

    sharp_up = (returns > 0.03).sum()
    sharp_down = (returns < -0.03).sum()
    momentum = sharp_up - sharp_down

    volatility = returns.std()

    vol_mean = df["Volume"].rolling(20).mean()
    vol_std = df["Volume"].rolling(20).std()
    volume_z = (df["Volume"].iloc[-1] - vol_mean.iloc[-1]) / (vol_std.iloc[-1] + 1e-9)

    support = df["Close"].rolling(20).min().iloc[-1]
    resistance = df["Close"].rolling(20).max().iloc[-1]
    price = df["Close"].iloc[-1]

    support_dist = (price - support) / price
    resistance_dist = (resistance - price) / price

    trend = df["Close"].pct_change().mean()

    return {
        "momentum": momentum,
        "volatility": volatility,
        "volume_z": volume_z,
        "support_dist": support_dist,
        "resistance_dist": resistance_dist,
        "trend": trend,
        "price": price
    }


# =========================
# 2. 점수
# =========================
def score(features):

    compression = max(0, 1 - features["volatility"] * 10)

    volume_score = min(100, abs(features["volume_z"]) * 20)

    structure_score = (
        (1 - features["support_dist"]) * 50 +
        (1 - features["resistance_dist"]) * 50
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
# 3. 해석
# =========================
def explain(score_dict):

    s = score_dict["final_score"]

    if s > 70:
        return "🟢 급등 가능 구간", "진입 타이밍 가능성 높음", "#00C853"

    elif s > 45:
        return "🟡 관찰 구간", "움직임 준비 중", "#FFD600"

    else:
        return "🔴 비활성 구간", "아직 에너지 부족", "#D50000"


# =========================
# 4. 분석 실행
# =========================
def run_analysis(code, df):

    if df is None or df.empty:
        return {"error": "데이터 없음"}

    features = build_features(df)
    scores = score(features)
    position, ai, color = explain(scores)

    return {
        "종목": code,
        "현재가": int(features["price"]),
        **features,
        **scores,
        "position": position,
        "ai": ai,
        "color": color
    }


# =========================
# 5. Streamlit UI
# =========================
st.title("📊 AI 주식 분석 시스템")

code = st.text_input("종목 코드 (예: AAPL, TSLA, 005930.KS)")

if st.button("분석하기"):

    if not code:
        st.warning("종목 코드를 입력하세요")
    else:
        df = load_data(code)

        result = run_analysis(code, df)

        if "error" in result:
            st.error(result["error"])
        else:
            st.subheader("분석 결과")
            st.write(result)

            st.markdown(
                f"<h3 style='color:{result['color']}'>{result['position']}</h3>",
                unsafe_allow_html=True
            )
