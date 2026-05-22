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
# 대표 종목
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
        "기아": "000270"
    }


# =========================
# 종목 검색
# =========================
def search_stock(query, ticker_dict):

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
# 글로벌 시장
# =========================
@st.cache_data(ttl=3600)
def load_global_markets():

    indices = {
        "🇺🇸 NASDAQ": "^IXIC",
        "🇺🇸 S&P500": "^GSPC",
        "🇰🇷 KOSPI": "^KS11",
        "🇰🇷 KOSDAQ": "^KQ11",
        "🇯🇵 Nikkei": "^N225"
    }

    results = []

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

                change = (
                    (current - prev)
                    / prev
                ) * 100

                results.append({
                    "시장": name,
                    "현재가": current,
                    "등락률": change
                })

        except:
            continue

    return results


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

    except:
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

        # 상승 에너지
        momentum = float(
            (returns > 0.02).sum()
            -
            (returns < -0.02).sum()
        )

        # 변동성
        volatility = float(
            returns.std()
        )

        # 거래량 변화율
        prev_volume = float(volume.iloc[-2])
        current_volume = float(volume.iloc[-1])

        volume_change_pct = 0.0

        if prev_volume > 0:

            volume_change_pct = (
                (current_volume - prev_volume)
                / prev_volume
            ) * 100

        # 추세
        trend = float(
            returns.mean()
        )

        # 현재가
        price = float(close.iloc[-1])

        return {
            "price": price,
            "momentum": momentum,
            "volatility": volatility,
            "trend": trend,
            "volume_change_pct": volume_change_pct
        }

    except:
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

    momentum_score = (
        features["momentum"] * 10
    )

    trend_score = (
        features["trend"] * 1000
    )

    volume_score = min(
        100,
        abs(features["volume_change_pct"])
    )

    final_score = (
        compression * 40
        +
        momentum_score * 0.2
        +
        trend_score * 0.2
        +
        volume_score * 0.2
    )

    return {
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
        **features,
        **scores,
        "상태": label,
        "color": color
    }


# =========================
# UI
# =========================
st.title("📊 AI 주식 분석 엔진")

# 글로벌 시장
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
    "종목명 또는 종목코드 입력"
)

# 버튼
if st.button("분석하기"):

    if not query:

        st.warning("종목을 입력하세요.")

    else:

        with st.spinner("AI 분석 중..."):

            code, name = search_stock(
                query,
                ticker_dict
            )

            if code is None:

                st.error("종목을 찾을 수 없습니다.")

            else:

                df, final_ticker = load_stock_data(code)

                if df is None:

                    st.error(
                        "데이터를 불러올 수 없습니다."
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

                        left, center, right = st.columns([1,2,1])

                        # =========================
                        # 왼쪽 지표
                        # =========================
                        with left:

                            st.subheader("📈 핵심 지표")

                            # 상승 흐름 해석
                            if result["momentum"] > 0:
                                momentum_text = "🔥 상승 흐름 강함"

                            elif result["momentum"] < 0:
                                momentum_text = "❄️ 하락 압력 강함"

                            else:
                                momentum_text = "⚖️ 중립 흐름"

                            # 거래량 해석
                            if result["volume_change_pct"] > 0:

                                volume_text = (
                                    f"📈 +{result['volume_change_pct']:.1f}%"
                                )

                            else:

                                volume_text = (
                                    f"📉 {result['volume_change_pct']:.1f}%"
                                )

                            st.metric(
                                "현재가",
                                f"{int(result['price']):,}원"
                            )

                            st.metric(
                                "AI 종합 점수",
                                f"{result['final_score']}점"
                            )

                            st.metric(
                                "시장 흐름",
                                momentum_text
                            )

                            st.metric(
                                "변동성",
                                f"{result['volatility'] * 100:.2f}%"
                            )

                            st.metric(
                                "전일 대비 거래량",
                                volume_text
                            )

                            st.metric(
                                "추세 방향",
                                f"{result['trend'] * 100:.2f}%"
                            )

                        # =========================
                        # 가운데 차트
                        # =========================
                        with center:

                            st.subheader(
                                f"📊 {result['종목명']} 주가 차트"
                            )

                            st.line_chart(
                                df["Close"]
                            )

                        # =========================
                        # 오른쪽 AI 진단
                        # =========================
                        with right:

                            st.subheader("🤖 AI 진단")

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

<h1>{int(result['price']):,}원</h1>

<h2 style="color:{result['color']}">
{result['상태']}
</h2>

<h1>
AI SCORE
<br>
{result['final_score']}
</h1>

</div>
                                """,
                                unsafe_allow_html=True
                            )
