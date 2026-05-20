import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser
from streamlit_autorefresh import st_autorefresh

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="주식주신 PRO", layout="wide")
st.title("🔥 주식주신 PRO")

st_autorefresh(interval=5000, key="refresh")

# =========================
# 종목 데이터
# =========================
@st.cache_data(ttl=3600)
def stock_list():
    df = fdr.StockListing("KRX")[["Code", "Name"]]
    return df.dropna().drop_duplicates()

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    r = df_stock[df_stock["Name"] == name]
    return r["Code"].iloc[0] if not r.empty else None

# =========================
# 가격 데이터
# =========================
@st.cache_data(ttl=5)
def get_price(c):
    return fdr.DataReader(str(c)).tail(120)

# =========================
# 뉴스
# =========================
def get_news(name):
    try:
        url = f"https://news.google.com/rss/search?q={name}+주가&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        return [e.title for e in feed.entries[:5]]
    except:
        return ["뉴스 없음"]

# =========================
# 지표
# =========================
def ind(df):
    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    vol = df["Volume"] / (df["VOL20"] + 1e-10)
    trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)

    df["Whale"] = np.clip(vol * 60 + trend * 50, 0, 100)

    std = df["Close"].rolling(5).std()
    df["Pred"] = np.clip((df["Whale"]/100) * (std/(df["Close"]+1e-10)) * 100, 0.5, 25)

    df["Acc"] = np.clip(70 + (100 - df["Whale"])*0.2, 50, 97)

    df["Buy"] = df["MA20"] - df["Close"].rolling(20).std()*0.8
    df["Sell"] = df["MA20"] + df["Close"].rolling(20).std()*0.8

    return df.dropna()

# =========================
# 분석
# =========================
def comment(l):
    if l["Close"] > l["MA5"]:
        trend = "상승"
    else:
        trend = "조정"

    flow = "강함" if l["Whale"] > 60 else "보통"
    outlook = "상승 가능" if l["Whale"] > 50 else "관망"

    return trend, flow, outlook

# =========================
# 급등주
# =========================
def scan_pump():
    rows = []

    for n in names[:20]:
        c = code(n)
        df = ind(get_price(c))
        if df.empty: continue

        l, p = df.iloc[-1], df.iloc[-2]
        chg = (l["Close"] - p["Close"]) / p["Close"] * 100

        score = l["Whale"]*0.5 + chg*10

        if l["Whale"] > 60 and chg > 1:
            rows.append({
                "종목": n,
                "현재가": f"{int(l['Close']):,}",
                "전일가": f"{int(p['Close']):,}",
                "등락": f"{chg:+.2f}%",
                "세력": f"{l['Whale']:.1f}%",
                "점수": round(score,2)
            })

    return pd.DataFrame(rows).sort_values("점수", ascending=False).head(10)

# =========================
# UI
# =========================
name = st.selectbox("종목", names)
c = code(name)

df = ind(get_price(c))

if not df.empty:
    l, p = df.iloc[-1], df.iloc[-2]

    price = int(l["Close"])
    diff = price - int(p["Close"])
    base = price - diff
    pct = diff / base * 100 if base != 0 else 0

    tab1, tab2, tab3 = st.tabs(["📊 분석", "🚀 급등주", "🎯 내일반등"])

    # =========================
    # TAB1
    # =========================
    with tab1:

        color = "red" if diff > 0 else "blue"
        arrow = "▲" if diff > 0 else "▼"

        st.markdown(f"""
        <div style="text-align:center;">
            <div style="font-size:44px;font-weight:900;color:{color};">{price:,}원</div>
            <div style="color:{color};font-size:16px;font-weight:700;">
                {arrow} {diff:+,}원 ({pct:+.2f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(pd.DataFrame([
            {"상승": f"{l['Pred']:.1f}%", "적중": f"{l['Acc']:.1f}%", "세력": f"{l['Whale']:.1f}%"},
            {"매수": f"{int(l['Buy']):,}", "매도": f"{int(l['Sell']):,}", "전일": f"{diff:+,}"}
        ]), use_container_width=True, hide_index=True)

        buy = l["Whale"] > 60 and l["Close"] <= l["Buy"]*1.02
        sell = l["Close"] >= l["Sell"]*0.98

        if buy:
            st.markdown("🟥 매수 신호")
        elif sell:
            st.markdown("🟦 매도 신호")
        else:
            st.info("⚪ 관망")

        trend, flow, outlook = comment(l)

        st.write("•", trend)
        st.write("•", flow)
        st.write("•", outlook)

        st.markdown("### 📰 뉴스")
        for n in get_news(name):
            st.write("•", n)

    # =========================
    # TAB2
    # =========================
    with tab2:
        st.markdown("### 🚀 급등주 TOP10")
        st.dataframe(scan_pump(), use_container_width=True)

    # =========================
    # TAB3
    # =========================
    with tab3:
        st.markdown("### 🎯 내일 반등 TOP10")

        rows = []

        for n in names[:20]:
            c = code(n)
            df2 = ind(get_price(c))
            if df2.empty: continue

            l2, p2 = df2.iloc[-1], df2.iloc[-2]

            chg = (l2["Close"] - p2["Close"]) / p2["Close"] * 100

            score = l2["Whale"]*0.4 + l2["Acc"]*0.4 + max(-chg*5,0)

            rows.append({
                "종목": n,
                "현재": f"{int(l2['Close']):,}",
                "전일": f"{int(p2['Close']):,}",
                "등락": f"{chg:+.2f}%",
                "세력": f"{l2['Whale']:.1f}%",
                "점수": round(score,2)
            })

        st.dataframe(pd.DataFrame(rows).sort_values("점수", ascending=False), use_container_width=True)

else:
    st.warning("데이터 부족")