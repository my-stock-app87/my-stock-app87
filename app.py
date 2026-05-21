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
    layout="centered"
)

st_autorefresh(interval=5000, key="refresh")

# =========================================================
# 모바일 스타일
# =========================================================
st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: Pretendard, sans-serif;
}

/* 전체 여백 */
.block-container{
    padding-top:1rem;
    padding-bottom:3rem;
    padding-left:0.7rem;
    padding-right:0.7rem;
}

/* 제목 */
.main-title{
    text-align:center;
    font-size:34px;
    font-weight:900;
    color:#ff2e2e;
    margin-bottom:5px;
}

/* 부제목 */
.sub-title{
    text-align:center;
    color:gray;
    font-size:14px;
    margin-bottom:25px;
}

/* 카드 */
.card{
    background:white;
    padding:16px;
    border-radius:18px;
    border:1px solid #ececec;
    box-shadow:0 2px 8px rgba(0,0,0,0.05);
    margin-bottom:14px;
}

/* 메뉴 버튼 */
div.stButton > button{
    width:100%;
    height:65px;
    border-radius:18px;
    border:none;
    font-size:18px;
    font-weight:800;
    background:#f5f5f5;
}

div.stButton > button:hover{
    background:#ffecec;
    color:red;
}

/* metric */
[data-testid="metric-container"]{
    border-radius:16px;
    padding:12px;
    background:white;
    border:1px solid #eee;
}

/* dataframe */
[data-testid="stDataFrame"]{
    border-radius:16px;
    overflow:hidden;
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
# 지표
# =========================================================
def ind(df):

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()

    vol = (
        df["Volume"] /
        (df["Volume"].rolling(20).mean() + 1e-10)
    )

    trend = (
        (df["Close"] - df["MA5"]) /
        (df["MA5"] + 1e-10)
    )

    power = (
        (df["Close"] - df["Open"]) /
        (df["Open"] + 1e-10)
    ) * 100

    upper_tail = (
        (df["High"] - df["Close"]) /
        (df["High"] - df["Low"] + 1e-10)
    )

    df["Whale"] = np.clip(
        vol * 45 +
        trend * 35 +
        power * 8 -
        upper_tail * 25,
        0,
        100
    )

    std = df["Close"].rolling(5).std()

    df["Pred"] = np.clip(
        (df["Whale"] / 100) *
        (std / (df["Close"] + 1e-10)) * 100,
        0.5,
        25
    )

    delta = df["Close"].diff()

    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)

    ma_up = up.rolling(14).mean()
    ma_down = down.rolling(14).mean()

    rs = ma_up / (ma_down + 1e-10)

    df["RSI"] = 100 - (100 / (1 + rs))

    df["Money"] = (
        df["Close"] * df["Volume"]
    ) / 100000000

    return df.dropna()

# =========================================================
# 분석멘트
# =========================================================
def analysis_text(l):

    if l["Whale"] > 70:
        return "🚀 강한 세력 매집 흐름"

    elif l["RSI"] < 30:
        return "🎯 과매도 반등 가능성"

    elif l["Pred"] > 10:
        return "🔥 단기 변동성 확대"

    else:
        return "📊 박스권 흐름"

# =========================================================
# 페이지 상태
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = ""

# =========================================================
# 메인 메뉴
# =========================================================
if st.session_state.page == "":

    st.markdown("""
    <div class='card'>

    <h3 style='text-align:center;'>
    📌 메뉴 선택
    </h3>

    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🧠 분석"):
            st.session_state.page = "analysis"

    with col2:
        if st.button("🚀 급등"):
            st.session_state.page = "surge"

    with col3:
        if st.button("🎯 반등"):
            st.session_state.page = "rebound"

# =========================================================
# 종합분석
# =========================================================
elif st.session_state.page == "analysis":

    if st.button("⬅️ 메인으로"):
        st.session_state.page = ""

    st.markdown("## 🧠 AI 종합분석")

    name = st.selectbox(
        "종목 선택",
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

        st.metric(
            "현재가",
            f"{price:,}원",
            f"{pct:.2f}%"
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "세력점수",
            f"{l['Whale']:.1f}"
        )

        col2.metric(
            "RSI",
            f"{l['RSI']:.1f}"
        )

        st.markdown(f"""
        <div class='card'>

        <h4>
        {analysis_text(l)}
        </h4>

        📈 최고가 :
        <b style='color:red;'>
        {int(l['High']):,}원
        </b>

        <br><br>

        📉 최저가 :
        <b style='color:blue;'>
        {int(l['Low']):,}원
        </b>

        <br><br>

        💰 거래대금 :
        <b>
        {int(l['Money'])}억
        </b>

        </div>
        """, unsafe_allow_html=True)

        st.line_chart(df["Close"])

        st.markdown("### 📰 관련 뉴스")

        news = get_news(name)

        for n in news:

            st.markdown(
                f"• [{n['title']}]({n['link']})"
            )

# =========================================================
# 급등중
# =========================================================
elif st.session_state.page == "surge":

    if st.button("⬅️ 메인으로"):
        st.session_state.page = ""

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
                    "등락률": round(chg, 2),
                    "세력": round(l2["Whale"], 1),
                    "거래대금": f"{int(l2['Money'])}억"
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
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# 내일 반등
# =========================================================
elif st.session_state.page == "rebound":

    if st.button("⬅️ 메인으로"):
        st.session_state.page = ""

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
                    "등락률": round(chg, 2),
                    "RSI": round(l2["RSI"], 1),
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
        use_container_width=True,
        hide_index=True
    )