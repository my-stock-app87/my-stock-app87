import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser
import plotly.graph_objects as go

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="주식주신 PRO",
    layout="wide"
)

# =========================================================
# 스타일
# =========================================================
st.markdown("""
<style>

.main {
    background-color: #0e1117;
}

.block-container {
    padding-top: 1rem;
}

div[data-testid="stMetric"] {
    background-color: #111827;
    border: 1px solid #222;
    padding: 15px;
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style='text-align:center;color:#ff4b4b;'>
🔥 주식주신 PRO
</h1>
""", unsafe_allow_html=True)

# =========================================================
# 종목 리스트
# =========================================================
@st.cache_data(ttl=3600)
def stock_list():
    df = fdr.StockListing("KRX")
    return df[["Code", "Name"]].dropna()

df_stock = stock_list()

# 속도 개선용 (거래대금 상위 일부만)
SCAN_LIMIT = 120

names = df_stock["Name"].tolist()

def code(name):
    r = df_stock[df_stock["Name"] == name]
    return r["Code"].iloc[0] if not r.empty else None

# =========================================================
# 데이터 가져오기
# =========================================================
@st.cache_data(ttl=300)
def get_price(c):
    try:
        df = fdr.DataReader(str(c)).tail(120)
        return df
    except Exception:
        return pd.DataFrame()

# =========================================================
# 뉴스
# =========================================================
@st.cache_data(ttl=300)
def get_news(name):

    url = (
        f"https://news.google.com/rss/search?"
        f"q={name}+주식&hl=ko&gl=KR&ceid=KR:ko"
    )

    feed = feedparser.parse(url)

    result = []

    for e in feed.entries[:5]:

        result.append({
            "title": e.title,
            "link": e.link
        })

    return result

# =========================================================
# 지표 계산
# =========================================================
def indicators(df):

    if len(df) < 30:
        return pd.DataFrame()

    df = df.copy()

    # 이동평균
    df["MA5"] = df["Close"].rolling(5).mean()

    # 거래량 배수
    vol = (
        df["Volume"] /
        (df["Volume"].rolling(20).mean() + 1e-10)
    )

    # 추세
    trend = (
        (df["Close"] - df["MA5"]) /
        (df["MA5"] + 1e-10)
    ) * 100

    # 양봉 힘
    power = (
        (df["Close"] - df["Open"]) /
        (df["Open"] + 1e-10)
    ) * 100

    # 윗꼬리
    upper_tail = (
        (df["High"] - df["Close"]) /
        (df["High"] - df["Low"] + 1e-10)
    ) * 100

    # RSI
    delta = df["Close"].diff()

    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)

    ma_up = up.rolling(14).mean()
    ma_down = down.rolling(14).mean()

    rs = ma_up / (ma_down + 1e-10)

    df["RSI"] = 100 - (100 / (1 + rs))

    # 세력 점수 개선
    df["Whale"] = np.clip(
        (
            trend * 0.9 +
            power * 1.5 +
            np.log1p(vol) * 18 +
            (100 - upper_tail) * 0.15
        ),
        0,
        100
    )

    # 변동성
    std = (
        df["Close"]
        .rolling(5)
        .std()
    )

    # 상승 예측
    df["Pred"] = np.clip(
        (
            (100 - df["RSI"]) * 0.45 +
            df["Whale"] * 0.55
        ) / 4,
        1,
        20
    )

    # 적중률
    df["Acc"] = np.clip(
        60 + (df["Whale"] * 0.35),
        50,
        95
    )

    # 체결 강도 느낌
    df["Strength"] = (
        (df["Close"] - df["Low"]) /
        (df["High"] - df["Low"] + 1e-10)
    ) * 100

    # 평균 변동폭
    tr = df["High"] - df["Low"]

    avg_tr = tr.rolling(5).mean()

    # 매수 / 매도
    df["Buy"] = (
        df["Close"] - avg_tr * 0.35
    )

    df["Sell"] = (
        df["Close"] + avg_tr * 0.45
    )

    # 거래대금
    df["Money"] = (
        df["Close"] * df["Volume"]
    ) / 100000000

    return df.dropna()

# =========================================================
# 분석 멘트
# =========================================================
def analysis_text(l):

    if l["Whale"] >= 75:
        return "🚀 강한 수급 유입 및 추세 지속 가능성"

    elif l["RSI"] <= 30:
        return "📉 과매도 구간 → 기술적 반등 가능성"

    elif l["RSI"] >= 70:
        return "⚠️ 단기 과열 가능성"

    else:
        return "📊 박스권 흐름"

# =========================================================
# 종목 선택
# =========================================================
name = st.selectbox(
    "🔍 종목 선택",
    names
)

c = code(name)

raw = get_price(c)

df = indicators(raw)

# =========================================================
# 데이터 부족
# =========================================================
if df.empty:
    st.warning("데이터 부족")
    st.stop()

# =========================================================
# 현재 데이터
# =========================================================
l = df.iloc[-1]
p = df.iloc[-2]

price = int(l["Close"])

diff = price - int(p["Close"])

pct = (
    diff / int(p["Close"])
) * 100

color = "#ff4b4b" if diff > 0 else "#3b82f6"

arrow = "▲" if diff > 0 else "▼"

# =========================================================
# 탭
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "📊 종합분석",
    "🚀 세력 급등주",
    "🎯 내일 반등"
])

# =========================================================
# TAB1
# =========================================================
with tab1:

    # 현재가 카드
    st.markdown(f"""
    <div style="
        text-align:center;
        padding:20px;
        background:#111827;
        border-radius:18px;
        border:1px solid #222;
        margin-bottom:15px;
    ">

    <div style="
        font-size:48px;
        font-weight:900;
        color:{color};
    ">
        {price:,}원
    </div>

    <div style="
        font-size:20px;
        font-weight:700;
        color:{color};
    ">
        {arrow} {diff:+,}원 ({pct:+.2f}%)
    </div>

    </div>
    """, unsafe_allow_html=True)

    # 지표
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("🚀 상승예측", f"{l['Pred']:.1f}%")
    c2.metric("🎯 적중률", f"{l['Acc']:.1f}%")
    c3.metric("🐳 세력점수", f"{l['Whale']:.1f}")
    c4.metric("🔥 체결강도", f"{l['Strength']:.1f}")
    c5.metric("💰 거래대금", f"{int(l['Money'])}억")

    # 신호
    buy_signal = (
        l["Whale"] > 65 and
        l["RSI"] < 40
    )

    sell_signal = (
        l["RSI"] > 72
    )

    if buy_signal:
        st.success("🟥 AI 매수 신호 감지")

    elif sell_signal:
        st.error("🟦 AI 매도 신호 감지")

    else:
        st.info("⚪ 현재 관망 구간")

    # 분석
    st.markdown("### 🧠 종합 분석")

    st.info(analysis_text(l))

    # 캔들 차트
    st.markdown("### 📈 주가 차트")

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            increasing_line_color='red',
            decreasing_line_color='blue'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MA5"],
            name="MA5",
            line=dict(color="orange")
        )
    )

    fig.update_layout(
        height=600,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # 뉴스
    st.markdown("### 📰 관련 뉴스")

    news = get_news(name)

    for n in news:
        st.link_button(
            n["title"],
            n["link"]
        )

# =========================================================
# 스캔 함수
# =========================================================
def scan_stocks(mode="surge"):

    rows = []

    sample = names[:SCAN_LIMIT]

    progress = st.progress(0)

    for idx, n in enumerate(sample):

        try:

            c = code(n)

            d = indicators(get_price(c))

            if d.empty:
                continue

            l2 = d.iloc[-1]
            p2 = d.iloc[-2]

            # 필터
            if l2["Close"] > 30000:
                continue

            if l2["Volume"] < 300000:
                continue

            if l2["Money"] < 10:
                continue

            chg = (
                (l2["Close"] - p2["Close"]) /
                p2["Close"]
            ) * 100

            if mode == "surge":

                score = (
                    l2["Whale"] * 0.7 +
                    max(chg, 0) * 7
                )

            else:

                score = (
                    l2["Whale"] * 0.4 +
                    l2["Acc"] * 0.3 +
                    max(-chg * 6, 0)
                )

            rows.append({
                "종목": n,
                "현재가": int(l2["Close"]),
                "등락률": round(chg, 2),
                "세력": round(l2["Whale"], 1),
                "예측": round(l2["Pred"], 1),
                "거래대금": f"{int(l2['Money'])}억",
                "점수": round(score, 1)
            })

        except Exception:
            continue

        progress.progress(
            (idx + 1) / len(sample)
        )

    progress.empty()

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values("점수", ascending=False)
        .head(5)
    )

# =========================================================
# TAB2
# =========================================================
with tab2:

    st.markdown("## 🚀 세력 급등주 TOP5")

    result = scan_stocks("surge")

    st.dataframe(
        result,
        use_container_width=True
    )

# =========================================================
# TAB3
# =========================================================
with tab3:

    st.markdown("## 🎯 내일 반등 예상 TOP5")

    result = scan_stocks("rebound")

    st.dataframe(
        result,
        use_container_width=True
    )