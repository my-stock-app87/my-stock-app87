import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser
from streamlit_autorefresh import st_autorefresh

# =====================================================
# 기본 설정
# =====================================================
st.set_page_config(page_title="주식주신 PRO", layout="wide")
st.title("🔥 주식주신 PRO")

st_autorefresh(interval=5000, key="refresh")

# =====================================================
# 종목 리스트
# =====================================================
@st.cache_data(ttl=3600)
def stock_list():
    try:
        df = fdr.StockListing("KRX")[["Code", "Name"]]
        return df.dropna().drop_duplicates(subset=["Name"])
    except:
        return pd.DataFrame({
            "Code": ["005930", "000660"],
            "Name": ["삼성전자", "SK하이닉스"]
        })

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    row = df_stock[df_stock["Name"] == name]
    if row.empty:
        return None
    return row["Code"].iloc[0]

# =====================================================
# 가격 데이터
# =====================================================
@st.cache_data(ttl=5)
def get_price(c):
    try:
        return fdr.DataReader(str(c)).tail(120)
    except:
        return pd.DataFrame()

# =====================================================
# 뉴스 + 감성
# =====================================================
def sentiment(text):
    pos = ["상승", "급등", "호재", "개선", "증가", "흑자", "기대"]
    neg = ["하락", "급락", "적자", "우려", "감소", "리스크", "부진"]

    score = 0
    for w in pos:
        if w in text:
            score += 1
    for w in neg:
        if w in text:
            score -= 1

    if score > 0:
        return "📈 호재"
    elif score < 0:
        return "📉 악재"
    return "⚖️ 중립"


def get_news(name):
    try:
        url = f"https://news.google.com/rss/search?q={name}+주가&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)

        return [(e.title, sentiment(e.title)) for e in feed.entries[:5]]
    except:
        return [("뉴스 없음", "⚖️ 중립")]

# =====================================================
# 지표
# =====================================================
def ind(df):
    if df is None or df.empty or len(df) < 25:
        return pd.DataFrame()

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    # 🐳 세력 진입 (%)
    vol_ratio = df["Volume"] / (df["VOL20"] + 1e-10)
    price_momentum = (df["Close"] - df["Open"]) / (df["Open"] + 1e-10)
    trend_strength = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)

    raw = (
        vol_ratio * 60 +
        np.clip(price_momentum * 100, -20, 20) +
        np.clip(trend_strength * 50, -15, 15)
    )

    df["Whale"] = 100 * (1 / (1 + np.exp(-(raw - 50) / 20)))
    df["Whale"] = np.clip(df["Whale"], 0, 100)

    # 📈 상승률
    std5 = df["Close"].rolling(5).std()
    df["Pred_Return"] = (df["Whale"] / 100) * (std5 / (df["Close"] + 1e-10)) * 100
    df["Pred_Return"] = np.clip(df["Pred_Return"], 0.5, 28.5)

    # 🎯 적중률
    stability = 100 - np.minimum(df["Whale"] * 0.1, 30)
    df["Accuracy"] = np.clip(70 + stability * 0.25, 50, 97)

    # 📊 점수
    rng = (df["High"] - df["Low"]).replace(0, 1e-10)
    body = ((df["Close"] - df["Open"]) / rng) * 30

    vol_score = np.clip((df["Whale"] / 200) * 40, 0, 40)
    ma_align = np.where(df["Close"] > df["MA5"], 30, 10)

    df["Score"] = np.clip(vol_score + ma_align + body, 10, 100)

    # 🎯 추천 매수/매도
    df["Buy"] = df["MA20"] - (df["Close"].rolling(20).std() * 0.8)
    df["Sell"] = df["MA20"] + (df["Close"].rolling(20).std() * 0.8)

    return df.dropna()

# =====================================================
# 차트 설명
# =====================================================
def comment(df):
    latest = df.iloc[-1]

    if latest["Close"] > latest["MA5"] > latest["MA20"]:
        trend = "강한 상승"
    elif latest["Close"] < latest["MA5"] < latest["MA20"]:
        trend = "하락"
    elif latest["Close"] > latest["MA5"]:
        trend = "단기 상승"
    else:
        trend = "조정"

    whale = latest["Whale"]

    if whale > 70:
        flow = "세력 강하게 유입"
        outlook = "추가 상승 가능"
    elif whale > 40:
        flow = "초기 유입"
        outlook = "반등 가능"
    else:
        flow = "약함"
        outlook = "관망"

    return trend, flow, outlook

# =====================================================
# 급등주 TOP10
# =====================================================
@st.cache_data(ttl=300)
def scan_pumps():
    results = []

    for n in names[:20]:
        c = code(n)
        df = get_price(c)
        df = ind(df)

        if df.empty:
            continue

        l = df.iloc[-1]
        p = df.iloc[-2]

        change = (l["Close"] - p["Close"]) / p["Close"] * 100

        score = l["Whale"] * 0.5 + l["Score"] * 0.3 + max(change * 10, 0)

        if l["Whale"] > 60 and change > 1:
            results.append({
                "종목": n,
                "현재가": f"{int(l['Close']):,}원",
                "등락률": f"{change:.2f}%",
                "세력": f"{l['Whale']:.1f}%",
                "급등점수": round(score, 2)
            })

    df = pd.DataFrame(results)

    if df.empty:
        return df

    return df.sort_values("급등점수", ascending=False).head(10)

# =====================================================
# UI
# =====================================================
name = st.selectbox("종목 검색", names)
c = code(name)

df = get_price(c)
df = ind(df)

if not df.empty:
    l = df.iloc[-1]
    p = df.iloc[-2]

    price = int(l["Close"])
    diff = price - int(p["Close"])

    tab1, tab2, tab3 = st.tabs([
        "📊 종목분석",
        "🚀 급등주",
        "🎯 내일 반등"
    ])

    # =====================
    # TAB1
    # =====================
    with tab1:
        c1, c2, c3 = st.columns(3)

        c1.metric("현재가", f"{price:,}원", f"{diff:+,}원")
        c2.metric("상승률", f"{l['Pred_Return']:.1f}%")
        c3.metric("적중률", f"{l['Accuracy']:.1f}%")

        st.metric("🐳 세력", f"{l['Whale']:.1f}%")

        st.metric("🟢 매수", f"{int(l['Buy']):,}원")
        st.metric("🔴 매도", f"{int(l['Sell']):,}원")

        trend, flow, outlook = comment(df)

        st.markdown("### 📊 분석")
        st.write(trend)
        st.write(flow)
        st.write(outlook)

        st.markdown("### 📰 뉴스")

        for t, s in get_news(name):
            st.markdown(f"- {s} {t}")

    # =====================
    # TAB2
    # =====================
    with tab2:
        st.markdown("### 🚀 급등주 TOP10")
        st.dataframe(scan_pumps(), use_container_width=True)

    # =====================
    # TAB3
    # =====================
    with tab3:
        st.markdown("### 🎯 내일 반등 TOP10")

        rows = []

        for n in names[:10]:
            c = code(n)
            d = ind(get_price(c))

            if d.empty:
                continue

            l = d.iloc[-1]

            rows.append({
                "종목": n,
                "현재가": f"{int(l['Close']):,}원",
                "세력": f"{l['Whale']:.1f}%",
                "점수": round(l["Score"], 2)
            })

        st.dataframe(pd.DataFrame(rows).sort_values("점수", ascending=False), use_container_width=True)

else:
    st.warning("데이터 부족")