import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser
from streamlit_autorefresh import st_autorefresh

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="주식주신 PRO",
    layout="wide"
)

st_autorefresh(interval=5000, key="refresh")

# =========================================================
# 스타일
# =========================================================
st.markdown("""
<style>

.main-title{
    text-align:center;
    font-size:52px;
    font-weight:900;
    color:#ff2e2e;
    margin-bottom:10px;
}

.sub-title{
    text-align:center;
    color:gray;
    margin-bottom:30px;
}

.block{
    background:white;
    padding:18px;
    border-radius:18px;
    border:1px solid #eee;
    box-shadow:0 2px 10px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 타이틀
# =========================================================
st.markdown("""
<div class='main-title'>
🔥 주식주신 PRO
</div>

<div class='sub-title'>
AI 기반 급등주 / 반등주 분석 시스템
</div>
""", unsafe_allow_html=True)

# =========================================================
# 종목 리스트
# =========================================================
@st.cache_data(ttl=3600)
def stock_list():
    return fdr.StockListing("KRX")[["Code", "Name"]].dropna()

df_stock = stock_list()

names = df_stock["Name"].tolist()

def code(name):

    r = df_stock[df_stock["Name"] == name]

    return r["Code"].iloc[0] if not r.empty else None

# =========================================================
# 데이터
# =========================================================
@st.cache_data(ttl=10)
def get_price(c):

    return fdr.DataReader(str(c)).tail(120)

# =========================================================
# 뉴스
# =========================================================
@st.cache_data(ttl=300)
def get_news(name):

    url = f"https://news.google.com/rss/search?q={name}+주식&hl=ko&gl=KR&ceid=KR:ko"

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
def ind(df):

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
    )

    # 양봉 힘
    power = (
        (df["Close"] - df["Open"]) /
        (df["Open"] + 1e-10)
    ) * 100

    # 윗꼬리
    upper_tail = (
        (df["High"] - df["Close"]) /
        (df["High"] - df["Low"] + 1e-10)
    )

    # 세력 점수
    df["Whale"] = np.clip(
        vol * 45 +
        trend * 35 +
        power * 8 -
        upper_tail * 25,
        0,
        100
    )

    # 상승 예측
    std = df["Close"].rolling(5).std()

    df["Pred"] = np.clip(
        (df["Whale"] / 100) *
        (std / (df["Close"] + 1e-10)) * 100,
        0.5,
        25
    )

    # 적중률
    df["Acc"] = np.clip(
        70 + (100 - df["Whale"]) * 0.2,
        50,
        97
    )

    # 체결강도
    df["Strength"] = (
        (df["Close"] - df["Low"]) /
        (df["High"] - df["Low"] + 1e-10)
    ) * 100

    # RSI
    delta = df["Close"].diff()

    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)

    ma_up = up.rolling(14).mean()
    ma_down = down.rolling(14).mean()

    rs = ma_up / (ma_down + 1e-10)

    df["RSI"] = 100 - (100 / (1 + rs))

    # 평균 변동폭
    tr = df["High"] - df["Low"]

    avg_tr = tr.rolling(5).mean()

    # 매수 / 매도
    df["Buy"] = df["Close"] - (avg_tr * 0.35)

    df["Sell"] = df["Close"] + (avg_tr * 0.45)

    # 거래대금
    df["Money"] = (
        df["Close"] * df["Volume"]
    ) / 100000000

    return df.dropna()

# =========================================================
# 분석 멘트
# =========================================================
def analysis_text(l):

    if l["Whale"] > 70:
        return "🚀 강한 세력 매집 흐름 감지"

    elif l["RSI"] < 30:
        return "🎯 과매도 구간 → 반등 가능성"

    elif l["Close"] > l["Sell"]:
        return "⚠️ 단기 과열 가능성"

    else:
        return "📊 박스권 흐름"

# =========================================================
# 첫 화면 메뉴
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = ""

col1, col2, col3 = st.columns(3)

with col1:

    if st.button(
        "🧠 종합분석",
        use_container_width=True
    ):
        st.session_state.page = "analysis"

with col2:

    if st.button(
        "🚀 급등중",
        use_container_width=True
    ):
        st.session_state.page = "surge"

with col3:

    if st.button(
        "🎯 내일 반등",
        use_container_width=True
    ):
        st.session_state.page = "rebound"

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# 종합분석
# =========================================================
if st.session_state.page == "analysis":

    st.markdown("## 🧠 AI 종합분석")

    name = st.selectbox(
        "🔍 종목 선택",
        names
    )

    c = code(name)

    df = ind(get_price(c))

    if not df.empty:

        l = df.iloc[-1]
        p = df.iloc[-2]

        price = int(l["Close"])

        diff = price - int(p["Close"])

        pct = (
            diff / int(p["Close"])
        ) * 100

        color = "red" if diff > 0 else "blue"

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "현재가",
            f"{price:,}원",
            f"{pct:.2f}%"
        )

        col2.metric(
            "세력점수",
            f"{l['Whale']:.1f}"
        )

        col3.metric(
            "상승예측",
            f"{l['Pred']:.1f}%"
        )

        col4.metric(
            "RSI",
            f"{l['RSI']:.1f}"
        )

        st.markdown("### 📈 주가 차트")

        st.line_chart(df["Close"])

        st.markdown("### 🧠 종합 분석")

        st.info(analysis_text(l))

        st.markdown(f"""
        <div class='block'>

        📈 최고가 :
        <b style='color:red;'>
        {int(l['High']):,}원
        </b><br><br>

        📉 최저가 :
        <b style='color:blue;'>
        {int(l['Low']):,}원
        </b><br><br>

        📊 거래량 :
        <b>
        {int(l['Volume']):,}주
        </b><br><br>

        💰 거래대금 :
        <b>
        {int(l['Money'])}억
        </b>

        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📰 관련 뉴스")

        news = get_news(name)

        for n in news:

            st.markdown(
                f"- [{n['title']}]({n['link']})"
            )

# =========================================================
# 급등중
# =========================================================
elif st.session_state.page == "surge":

    st.markdown("## 🚀 실시간 급등포착")

    rows = []

    for n in names[:200]:

        try:

            c = code(n)

            d = ind(get_price(c))

            if d.empty:
                continue

            l2 = d.iloc[-1]
            p2 = d.iloc[-2]

            chg = (
                (l2["Close"] - p2["Close"]) /
                p2["Close"]
            ) * 100

            if (
                chg > 5 and
                l2["Money"] > 20 and
                l2["Close"] < 30000
            ):

                rows.append({
                    "종목": n,
                    "현재가": int(l2["Close"]),
                    "등락률": round(chg, 2),
                    "세력점수": round(l2["Whale"], 1),
                    "거래대금": f"{int(l2['Money'])}억",
                    "상승예측": round(l2["Pred"], 1)
                })

        except:
            continue

    result = (
        pd.DataFrame(rows)
        .sort_values(
            "등락률",
            ascending=False
        )
        .head(10)
    )

    st.dataframe(
        result,
        use_container_width=True
    )

# =========================================================
# 내일 반등
# =========================================================
elif st.session_state.page == "rebound":

    st.markdown("## 🎯 내일 반등 예상")

    rows = []

    for n in names[:200]:

        try:

            c = code(n)

            d = ind(get_price(c))

            if d.empty:
                continue

            l2 = d.iloc[-1]
            p2 = d.iloc[-2]

            chg = (
                (l2["Close"] - p2["Close"]) /
                p2["Close"]
            ) * 100

            score = (
                l2["Whale"] * 0.4 +
                (40 - l2["RSI"]) * 1.5 +
                max(-chg * 5, 0)
            )

            if (
                chg < -3 and
                l2["Whale"] > 50 and
                l2["RSI"] < 40 and
                l2["Money"] > 10 and
                l2["Close"] < 30000
            ):

                rows.append({
                    "종목": n,
                    "현재가": int(l2["Close"]),
                    "등락률": round(chg, 2),
                    "RSI": round(l2["RSI"], 1),
                    "세력점수": round(l2["Whale"], 1),
                    "반등점수": round(score, 1)
                })

        except:
            continue

    result = (
        pd.DataFrame(rows)
        .sort_values(
            "반등점수",
            ascending=False
        )
        .head(10)
    )

    st.dataframe(
        result,
        use_container_width=True
    )

# =========================================================
# 첫 화면 안내
# =========================================================
else:

    st.markdown("""
    <div class='block' style='text-align:center;'>

    <h2>
    👋 주식주신 PRO에 오신 것을 환영합니다
    </h2>

    <br>

    🧠 종합분석 :
    선택 종목 AI 분석

    <br><br>

    🚀 급등중 :
    실시간 강한 종목 포착

    <br><br>

    🎯 내일 반등 :
    눌림목 반등 예상 종목

    </div>
    """, unsafe_allow_html=True)