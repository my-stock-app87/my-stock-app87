
import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser
from streamlit_autorefresh import st_autorefresh

# =========================================================
# 설정
# =========================================================
st.set_page_config(page_title="주식주신 PRO", layout="centered")
st_autorefresh(interval=5000, key="refresh")

# =========================================================
# 스타일 (모바일)
# =========================================================
st.markdown("""
<style>

.block-container{
    padding: 1rem;
}

.title{
    text-align:center;
    font-size:34px;
    font-weight:900;
    color:#ff2e2e;
}

.card{
    background:white;
    padding:16px;
    border-radius:16px;
    border:1px solid #eee;
    margin-bottom:12px;
}

div.stButton > button{
    width:100%;
    height:60px;
    font-size:18px;
    font-weight:800;
    border-radius:16px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 타이틀
# =========================================================
st.markdown("<div class='title'>🔥 주식주신 PRO</div>", unsafe_allow_html=True)

# =========================================================
# 데이터
# =========================================================
@st.cache_data(ttl=3600)
def stock_list():
    return fdr.StockListing("KRX")[["Code", "Name"]].dropna()

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    r = df_stock[df_stock["Name"] == name]
    return r["Code"].iloc[0] if not r.empty else None

@st.cache_data(ttl=10)
def get_price(c):
    return fdr.DataReader(str(c)).tail(120)

@st.cache_data(ttl=300)
def get_news(name):
    url = f"https://news.google.com/rss/search?q={name}+주식&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    return [{"title": e.title, "link": e.link} for e in feed.entries[:5]]

# =========================================================
# 지표
# =========================================================
def ind(df):

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()

    vol = df["Volume"] / (df["Volume"].rolling(20).mean() + 1e-10)

    trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)

    power = (df["Close"] - df["Open"]) / (df["Open"] + 1e-10) * 100

    df["Whale"] = np.clip(
        vol * 45 + trend * 35 + power * 8,
        0,
        100
    )

    df["Pred"] = np.clip(df["Whale"] * 0.2, 0, 25)

    df["RSI"] = 50  # 단순 안정값 (에러 방지용)

    df["Money"] = df["Close"] * df["Volume"] / 1e8

    return df.dropna()

# =========================================================
# 페이지 상태
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = ""

# =========================================================
# 메인 메뉴
# =========================================================
if st.session_state.page == "":

    st.markdown("<div class='card' style='text-align:center;'>메뉴 선택</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🧠 종합분석"):
            st.session_state.page = "analysis"

    with col2:
        if st.button("🚀 급등"):
            st.session_state.page = "surge"

    with col3:
        if st.button("🎯 반등"):
            st.session_state.page = "rebound"

# =========================================================
# 🧠 종합분석
# =========================================================
elif st.session_state.page == "analysis":

    if st.button("⬅️ 뒤로"):
        st.session_state.page = ""

    st.markdown("## 🧠 종합분석")

    name = st.selectbox("종목 선택", names)

    c = code(name)

    df = ind(get_price(c))

    if not df.empty:

        l = df.iloc[-1]
        p = df.iloc[-2]

        price = int(l["Close"])
        diff = price - int(p["Close"])
        pct = diff / p["Close"] * 100

        buy = int(price * 0.98)
        sell = int(price * 1.04)

        whale = l["Whale"]

        vol_now = int(l["Volume"])
        vol_yest = int(p["Volume"])

        vol_pct = (vol_now - vol_yest) / (vol_yest + 1e-10) * 100

        up_prob = np.clip(whale * 0.7, 0, 95)

        predict = "📈 상승" if up_prob > 50 else "📉 하락"

        st.metric("현재가", f"{price:,}", f"{pct:+.2f}%")

        st.markdown(f"""
        <div class='card'>

        📈 최고가: {int(l['High']):,}<br>
        📉 최저가: {int(l['Low']):,}<br><br>

        🟢 매수: {buy:,}<br>
        🔴 매도: {sell:,}<br><br>

        🐳 세력: {whale:.1f}%<br><br>

        📊 거래량: {vol_now:,}주<br>
        변화: {vol_pct:+.1f}%<br><br>

        🎯 예측: {predict} ({up_prob:.1f}%)

        </div>
        """, unsafe_allow_html=True)

        if whale > 60:
            st.success("🟥 매수 가능")
        elif whale < 40:
            st.error("🟦 매도")
        else:
            st.info("⚪ 관망")

        st.markdown("### 📰 뉴스")

        for n in get_news(name):
            st.markdown(f"- [{n['title']}]({n['link']})")

# =========================================================
# 🚀 급등
# =========================================================
elif st.session_state.page == "surge":

    if st.button("⬅️ 뒤로"):
        st.session_state.page = ""

    st.markdown("## 🚀 급등")

    st.info("간단 버전 (안정형)")

# =========================================================
# 🎯 반등
# =========================================================
elif st.session_state.page == "rebound":

    if st.button("⬅️ 뒤로"):
        st.session_state.page = ""

    st.markdown("## 🎯 반등")

    st.info("간단 버전 (안정형)")