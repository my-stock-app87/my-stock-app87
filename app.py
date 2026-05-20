import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser
from streamlit_autorefresh import st_autorefresh

# =========================
st.set_page_config(page_title="주식주신 PRO", layout="wide")
st.title("🔥 주식주신 PRO")

st_autorefresh(interval=5000, key="refresh")

# =========================
@st.cache_data(ttl=3600)
def stock_list():
    return fdr.StockListing("KRX")[["Code", "Name"]].dropna()

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    r = df_stock[df_stock["Name"] == name]
    return r["Code"].iloc[0] if not r.empty else None

# =========================
@st.cache_data(ttl=5)
def get_price(c):
    return fdr.DataReader(str(c)).tail(120)

# =========================
def ind(df):
    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()

    vol = df["Volume"] / (df["Volume"].rolling(20).mean() + 1e-10)
    trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)

    df["Whale"] = np.clip(vol * 60 + trend * 50, 0, 100)

    std = df["Close"].rolling(5).std()
    df["Pred"] = np.clip((df["Whale"]/100) * (std/(df["Close"]+1e-10)) * 100, 0.5, 25)

    df["Acc"] = np.clip(70 + (100 - df["Whale"])*0.2, 50, 97)

    tr = df["High"] - df["Low"]
    avg_tr = tr.rolling(5).mean()

    df["Buy"] = df["Close"] - (avg_tr * 0.35)
    df["Sell"] = df["Close"] + (avg_tr * 0.45)

    return df.dropna()

# =========================
def analysis_text(l):
    if l["Whale"] > 65 and l["Pred"] > 2:
        return "🚀 세력 유입 강함 → 상승 가능성 높음"
    elif l["Close"] < l["Buy"]:
        return "📉 눌림 구간 → 분할 매수 구간"
    elif l["Close"] > l["Sell"]:
        return "⚠️ 과열 구간 → 차익 실현"
    else:
        return "📊 박스권 흐름"

# =========================
name = st.selectbox("종목", names)
c = code(name)

df = ind(get_price(c))

if not df.empty:
    l, p = df.iloc[-1], df.iloc[-2]

    price = int(l["Close"])
    diff = price - int(p["Close"])
    pct = diff / int(p["Close"]) * 100

    tab1, tab2, tab3 = st.tabs(["📊 분석", "🚀 급등주", "🎯 내일반등"])

    # =========================
    # TAB1
    # =========================
    with tab1:

        color = "red" if diff > 0 else "blue"
        arrow = "▲" if diff > 0 else "▼"

        # =========================
        # 🔥 현재가
        # =========================
        st.markdown(f"""
        <div style="text-align:center;">
            <div style="font-size:44px;font-weight:900;color:{color};">{price:,}원</div>
            <div style="color:{color};font-size:16px;font-weight:700;">
                {arrow} {diff:+,}원 ({pct:+.2f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)

        # =========================
        # 🔥 1줄 HTS 바 (절대 안 깨짐)
        # =========================
        st.markdown(f"""
        <div style="
            background:#f8f9fa;
            padding:12px;
            border-radius:12px;
            font-weight:800;
            font-size:14px;
            white-space:nowrap;
            overflow-x:auto;
        ">
        📈 상승 {l['Pred']:.1f}% ｜ 
        🎯 적중 {l['Acc']:.1f}% ｜ 
        🐳 세력 {l['Whale']:.1f}% ｜ 
        🟢 매수 {int(l['Buy']):,} ｜ 
        🔴 매도 {int(l['Sell']):,} ｜ 
        📊 전일 {diff:+,}
        </div>
        """, unsafe_allow_html=True)

        # =========================
        # 신호
        # =========================
        buy_signal = l["Whale"] > 60 and l["Close"] <= l["Buy"]*1.02
        sell_signal = l["Close"] >= l["Sell"]*0.98

        if buy_signal:
            st.markdown("🟥 매수 신호")
        elif sell_signal:
            st.markdown("🟦 매도 신호")
        else:
            st.info("⚪ 관망")

        # =========================
        # 종합 분석
        # =========================
        st.markdown("### 🧠 종합 분석")
        st.markdown(f"""
        <div style="
            padding:12px;
            border-radius:12px;
            background:white;
            border:1px solid #eee;
        ">
        {analysis_text(l)}
        </div>
        """, unsafe_allow_html=True)

    # =========================
    # TAB2 급등주
    # =========================
    with tab2:
        st.markdown("### 🚀 급등주 TOP10")

        rows = []
        for n in names[:10]:
            c = code(n)
            d = ind(get_price(c))
            if d.empty: continue

            l2, p2 = d.iloc[-1], d.iloc[-2]
            chg = (l2["Close"] - p2["Close"]) / p2["Close"] * 100

            score = l2["Whale"]*0.6 + max(chg,0)*8

            rows.append({
                "종목": n,
                "현재": int(l2["Close"]),
                "전일": int(p2["Close"]),
                "등락": round(chg,2),
                "세력": round(l2["Whale"],1),
                "점수": round(score,1)
            })

        st.dataframe(pd.DataFrame(rows).sort_values("점수", ascending=False))

    # =========================
    # TAB3 내일반등
    # =========================
    with tab3:
        st.markdown("### 🎯 내일 반등 TOP10")

        rows = []
        for n in names[:10]:
            c = code(n)
            d = ind(get_price(c))
            if d.empty: continue

            l2, p2 = d.iloc[-1], d.iloc[-2]
            chg = (l2["Close"] - p2["Close"]) / p2["Close"] * 100

            score = l2["Whale"]*0.5 + l2["Acc"]*0.3 + max(-chg*4,0)

            rows.append({
                "종목": n,
                "현재": int(l2["Close"]),
                "전일": int(p2["Close"]),
                "등락": round(chg,2),
                "세력": round(l2["Whale"],1),
                "점수": round(score,1)
            })

        st.dataframe(pd.DataFrame(rows).sort_values("점수", ascending=False))

else:
    st.warning("데이터 부족")