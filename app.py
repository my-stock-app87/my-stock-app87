
import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser
from streamlit_autorefresh import st_autorefresh

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(page_title="주식주신 PRO", layout="centered")
st_autorefresh(interval=5000, key="refresh")

# =========================================================
# UI 스타일
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

    df["Whale"] = np.clip(vol * 45 + trend * 35 + power * 8, 0, 100)

    df["Pred"] = np.clip(df["Whale"] * 0.2, 0, 25)

    df["RSI"] = 50

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

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧠 종합분석"):
            st.session_state.page = "analysis"

    with col2:
        if st.button("⚡ 단타 TOP5"):
            st.session_state.page = "scalp"

# =========================================================
# 🧠 종합분석 (UI 개선 버전)
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

        buy_price = int(price * 0.98)
        sell_price = int(price * 1.04)

        whale = l["Whale"]

        vol_now = int(l["Volume"])
        vol_yest = int(p["Volume"])
        vol_pct = (vol_now - vol_yest) / (vol_yest + 1e-10) * 100

        up_prob = np.clip(whale * 0.7, 0, 95)
        predict = "📈 상승 예상" if up_prob > 50 else "📉 하락 예상"

        # =====================================================
        # 상단
        # =====================================================
        col1, col2 = st.columns([2, 1])

        with col1:
            st.metric("현재가", f"{price:,}원", f"{pct:+.2f}%")

        with col2:
            if whale >= 65 and vol_pct > 0:
                st.success("🟥 매수 추천")
            elif whale < 35:
                st.error("🟦 매도 추천")
            else:
                st.info("⚪ 관망")

        # =====================================================
        # 핵심 카드 (한 화면 정리)
        # =====================================================
        col1, col2, col3 = st.columns(3)
        col1.metric("고가", f"{int(l['High']):,}원")
        col2.metric("저가", f"{int(l['Low']):,}원")
        col3.metric("세력이 있다", f"{whale:.1f}%")

        col4, col5, col6 = st.columns(3)
        col4.metric("매수", f"{buy_price:,}원")
        col5.metric("매도", f"{sell_price:,}원")
        col6.metric("예측", f"{up_prob:.1f}%")

        st.markdown("---")

        col1, col2 = st.columns(2)
        col1.metric("거래량", f"{vol_now:,}주", f"{vol_pct:+.1f}%")
        col2.metric("AI", predict)

        # =====================================================
        # AI 전략
        # =====================================================
        if whale >= 70 and vol_pct > 10:
            ai_plan = "🚀 세력 + 거래량 증가 → 단기 급등 가능"
        elif whale >= 60:
            ai_plan = "📊 세력 유입 → 추세 확인"
        elif l["RSI"] < 30:
            ai_plan = "🎯 과매도 → 반등 가능"
        elif vol_pct < -10:
            ai_plan = "⚠️ 거래량 감소 → 관망"
        else:
            ai_plan = "⚪ 방향 없음 → 관망"

        st.markdown("### 🤖 AI 전략")

        st.markdown(f"""
        <div class='card'>{ai_plan}</div>
        """, unsafe_allow_html=True)

        # 뉴스
        st.markdown("### 📰 뉴스")
        for n in get_news(name):
            st.markdown(f"- {n['title']}")

# =========================================================
# ⚡ 단타 TOP5 (초고속 버전)
# =========================================================
elif st.session_state.page == "scalp":

    if st.button("⬅️ 뒤로"):
        st.session_state.page = ""

    st.markdown("## ⚡ 단타 TOP5 (2만원 이하)")

    base = df_stock.sample(80)

    rows = []

    for _, r in base.iterrows():

        try:
            c = r["Code"]
            name = r["Name"]

            df = get_price(c)
            if df.empty:
                continue

            l = df.iloc[-1]
            p = df.iloc[-2]

            price = int(l["Close"])

            if price > 20000:
                continue

            if l["Volume"] < 100000:
                continue

            vol_pct = (l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10) * 100

            chg = (l["Close"] - p["Close"]) / p["Close"] * 100

            score = l["Whale"] * 0.6 + vol_pct * 0.3 + max(chg, 0) * 4

            rows.append({
                "종목": name,
                "현재가": f"{price:,}원",
                "등락률": round(chg, 2),
                "거래량": f"{int(l['Volume']):,}",
                "세력": round(l["Whale"], 1),
                "점수": round(score, 1)
            })

        except:
            continue

    result = pd.DataFrame(rows).sort_values("점수", ascending=False).head(5)

    st.dataframe(result, use_container_width=True)

    st.info("⚡ 2만원 이하 + 거래량 + 세력 + 상승률 기반 TOP5")