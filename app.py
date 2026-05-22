import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# =========================
# 페이지 설정
# =========================
st.set_page_config(
    page_title="AI 주식 분석 엔진",
    layout="wide"
)

# =========================
# 한국 대표 종목 매핑
# =========================
@st.cache_data(ttl=86400)
def load_krx_tickers():

    return {
        "삼성전자": "005930",
        "SK하이닉스": "000660",
        "현대차": "005380",
        "네이버": "035420",
        "카카오": "035720",
        "LG에너지솔루션": "373220",
        "셀트리온": "068270",
        "기아": "000270",
        "POSCO홀딩스": "005490",
        "삼성바이오로직스": "207940"
    }


# =========================
# 종목 검색
# =========================
def search_korean_code(query, ticker_dict):

    query = str(query).strip()

    if not query:
        return None, None

    # 숫자 입력
    if query.isdigit():

        code = query.zfill(6)

        name = next(
            (k for k, v in ticker_dict.items() if v == code),
            "알 수 없는 종목"
        )

        return code, name

    # 정확 일치
    if query in ticker_dict:
        return ticker_dict[query], query

    # 부분 검색
    matched = [
        k for k in ticker_dict.keys()
        if query.lower() in k.lower()
    ]

    if matched:
        best = matched[0]
        return ticker_dict[best], best

    # 미국 주식
    if query.isalpha():
        return query.upper(), query.upper()

    return None, None


# =========================
# 글로벌 지수
# =========================
@st.cache_data(ttl=3600)
def load_global_markets():

    indices = {
        "🇺🇸 NASDAQ": "^IXIC",
        "🇺🇸 S&P500": "^GSPC",
        "🇰🇷 KOSPI": "^KS11",
        "🇰🇷 KOSDAQ": "^KQ11",
        "🇯🇵 Nikkei": "^N225",
        "🇩🇪 DAX": "^GDAXI"
    }

    result = []

    for name, ticker in indices.items():

        try:
            df = yf.download(
                ticker,
                period="5d",
                interval="1d",
                auto_adjust=True,
                progress=False
            )

            if df is None or df.empty:
                continue

            close = df["Close"].values.flatten()

            if len(close) >= 2:

                current = float(close[-1])
                prev = float(close[-2])

                rate = ((current - prev) / prev) * 100

                result.append({
                    "시장": name,
                    "현재가": current,
                    "등락률": rate
                })

        except:
            continue

    return result


# =========================
# 데이터 로딩
# =========================
def load_stock_data(code):

    try:

        candidates = []

        # 한국 주식
        if code.isdigit():

            candidates = [
                f"{code}.KS",
                f"{code}.KQ"
            ]

        else:
            candidates = [code]

        for ticker in candidates:

            df = yf.download(
                ticker,
                period="6mo",
                interval="1d",
                auto_adjust=True,
                progress=False
            )

            if df is not None and not df.empty:

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]

                df.columns = [
                    str(col).capitalize()
                    for col in df.columns
                ]

                if "Close" not in df.columns:
                    continue

                if "Volume" not in df.columns:
                    continue

                df = df.dropna()

                return df, ticker

        return None, None

    except Exception as e:

        st.error(f"데이터 로딩 오류: {e}")

        return None, None


# =========================
# 특징 계산
# =========================
def build_features(df):

    try:

        close = pd.Series(
            df["Close"].values.flatten()
        ).astype(float)

        volume = pd.Series(
            df["Volume"].values.flatten()
        ).astype(float)

        returns = close.pct_change().dropna()

        if len(returns) < 20:
            return None

        momentum = float(
            (returns > 0.02).sum()
            -
            (returns < -0.02).sum()
        )

        volatility = float(
            returns.std()
        )

        vol_mean = float(
            volume.rolling(20).mean().iloc[-1]
        )

        vol_std = float(
            volume.rolling(20).std().iloc[-1]
        )

        volume_z = 0.0

        if vol_std > 0:
            volume_z = (
                volume.iloc[-1] - vol_mean
            ) / (vol_std + 1e-9)

        support = float(
            close.rolling(20).min().iloc[-1]
        )

        resistance = float(
            close.rolling(20).max().iloc[-1]
        )

        price = float(close.iloc[-1])

        support_dist = (
            (price - support) / price
        )

        resistance_dist = (
            (resistance - price) / price
        )

        trend = float(
            returns.mean()
        )

        return {
            "price": price,
            "momentum": momentum,
            "volatility": volatility,
            "volume_z": volume_z,
            "support_dist": support_dist,
            "resistance_dist": resistance_dist,
            "trend": trend
        }

    except Exception as e:

        st.error(f"특징 계산 오류: {e}")

        return None


# =========================
# 점수 계산
# =========================
def score(features):

    if features is None:
        return None

    compression = max(
        0.0,
        1 - features["volatility"] * 10
    )

    volume_score = min(
        100.0,
        abs(features["volume_z"]) * 20
    )

    structure_score = (
        max(0.0, 1 - features["support_dist"]) * 50
        +
        max(0.0, 1 - features["resistance_dist"]) * 50
    )

    momentum_score = (
        features["momentum"] * 10
    )

    trend_score = (
        features["trend"] * 1000
    )

    final_score = (
        compression * 30
        +
        volume_score * 0.25
        +
        structure_score * 0.2
        +
        momentum_score * 0.15
        +
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
def explain(score_value):

    if score_value > 70:
        return "🟢 강세 구간", "#00C853"

    elif score_value > 45:
        return "🟡 관찰 구간", "#FFD600"

    else:
        return "🔴 약세 구간", "#D50000"


# =========================
# 분석 실행
# =========================
def run_analysis(code, name, df):

    features = build_features(df)

    if features is None:
        return None

    scores = score(features)

    if scores is None:
        return None

    label, color = explain(
        scores["final_score"]
    )

    return {
        "종목명": name,
        "티커": code,
        "현재가": features["price"],
        **features,
        **scores,
        "상태": label,
        "color": color
    }


# =========================
# UI
# =========================
st.title("📊 AI 주식 분석 엔진")

# 글로벌 지수
st.subheader("🌐 글로벌 시장")

markets = load_global_markets()

if markets:

    cols = st.columns(len(markets))

    for i, m in enumerate(markets):

        with cols[i]:

            sign = "+" if m["등락률"] >= 0 else ""

            st.metric(
                label=m["시장"],
                value=f"{m['현재가']:.2f}",
                delta=f"{sign}{m['등락률']:.2f}%"
            )

st.markdown("---")

# 종목 검색
st.subheader("🇰🇷 한국 / 미국 주식 분석")

ticker_dict = load_krx_tickers()

query = st.text_input(
    "종목명 또는 종목코드 입력 (예: 삼성전자 / 005930 / AAPL)"
)

# 버튼
if st.button("분석하기"):

    if not query:

        st.warning("종목을 입력하세요.")

    else:

        with st.spinner("데이터 분석 중..."):

            code, name = search_korean_code(
                query,
                ticker_dict
            )

            if code is None:

                st.error("종목을 찾을 수 없습니다.")

            else:

                df, final_ticker = load_stock_data(code)

                if df is None:

                    st.error(
                        f"{query} 데이터를 불러올 수 없습니다."
                    )

                else:

                    result = run_analysis(
                        final_ticker,
                        name,
                        df
                    )

                    if result is None:

                        st.error("분석 실패")

                    else:

                        left, right = st.columns(2)

                        with left:

                            st.subheader("📈 상세 분석")

                            display = {
                                "종목명": result["종목명"],
                                "티커": result["티커"],
                                "현재가": round(result["현재가"], 2),
                                "최종점수": result["final_score"],
                                "변동성": result["volatility"],
                                "거래량Z": result["volume_z"],
                                "모멘텀": result["momentum"]
                            }

                            st.dataframe(
                                pd.DataFrame(
                                    display.items(),
                                    columns=["항목", "값"]
                                )
                            )

                            st.line_chart(df["Close"])

                        with right:

                            st.subheader("🤖 AI 진단")

                            if ".K" in result["티커"]:
                                price_text = f"{int(result['현재가']):,}원"
                            else:
                                price_text = f"${result['현재가']:.2f}"

                            st.markdown(
                                f"""
<div style="
padding:30px;
border-radius:15px;
background:#f3f4f6;
text-align:center;
">

<h2>{result['종목명']}</h2>

<h4>{result['티커']}</h4>

<h1>{price_text}</h1>

<h2 style="color:{result['color']}">
{result['상태']}
</h2>

<h1>
AI SCORE: {result['final_score']}
</h1>

</div>
                                """,
                                unsafe_allow_html=True
                            )
