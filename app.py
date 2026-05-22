import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# =========================
# 데이터 로딩 (최신 yfinance 대응)
# =========================
def load_data(code):
    try:
        # group_by="column" 옵션을 추가하여 데이터 구조가 깨지는 현상을 방지합니다.
        df = yf.download(code, period="6mo", interval="1d", group_by="column")

        if df is None or df.empty:
            return None

        # 다중 인덱스로 데이터가 들어올 경우, 최하단 단일 열(Close, Volume 등)만 남기고 정리합니다.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(-1)

        df = df.dropna(subset=["Close", "Volume"])
        df = df.sort_index()

        return df

    except Exception as e:
        st.error(f"데이터 로드 중 에러 발생: {e}")
        return None


# =========================
# 특징 계산 (안전한 숫자형 변환 추가)
# =========================
def build_features(df):
    try:
        # 단일 열 추출 후 1차원 numpy 배열(values)로 다루어 TypeError를 원천 차단합니다.
        close = df["Close"].squeeze().astype(float)
        volume = df["Volume"].squeeze().astype(float)

        returns = close.pct_change().dropna()

        if len(returns) == 0:
            return None

        # .values를 명시하여 2차원 DataFrame 크기 비교 오류(TypeError)를 해결합니다.
        pos_count = int((returns.values > 0.02).sum())
        neg_count = int((returns.values < -0.02).sum())
        momentum = float(pos_count - neg_count)

        volatility = float(returns.std()) if not np.isnan(returns.std()) else 0.0

        # rolling 연산 후 마지막 값을 안전하게 단일 숫자로 가져옵니다.
        vol_mean = float(volume.rolling(20).mean().iloc[-1])
        vol_std = float(volume.rolling(20).std().iloc[-1])

        volume_z = 0.0
        if vol_std and not np.isnan(vol_std):
            last_vol = float(volume.iloc[-1])
            volume_z = (last_vol - vol_mean) / (vol_std + 1e-9)

        support = float(close.rolling(20).min().iloc[-1])
        resistance = float(close.rolling(20).max().iloc[-1])
        price = float(close.iloc[-1])

        support_dist = float((price - support) / price)
        resistance_dist = float((resistance - price) / price)

        trend = float(returns.mean())

        return {
            "momentum": momentum,
            "volatility": volatility,
            "volume_z": volume_z,
            "support_dist": support_dist,
            "resistance_dist": resistance_dist,
            "trend": trend,
            "price": price
        }
    except Exception as e:
        st.error(f"특징 계산 중 에러 발생: {e}")
        return None


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
