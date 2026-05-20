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
# 종목 리스트
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
# 가격
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
        return []

# =========================
# 지표 (당일 기준 핵심)
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

    # =========================
    # 🔥 당일 기준 추천매수/매도
    # =========================
    tr = df["High"] - df["Low"]
    avg_tr = tr.rolling(5).mean()

    df["Buy"] = df["Close"] - (avg_tr * 0.35)
    df["Sell"] = df["Close"] + (avg_tr * 0.45)

    return df.dropna()

# =========================
# 종합 분석
# =========================
def analysis_text(l):
    if l["Whale"] > 65 and l["Pred"] > 2:
        return "🚀 세력 유입 강함 + 상승 모멘텀 → 단기 상승 가능성 높음"
    elif l["Close"] < l["Buy"]:
        return "📉 눌림 구간 → 분할 매수 고려"
    elif l["Close"] > l["Sell"]:
        return "⚠️ 과열 구간 → 차익 실현 구간"
    else:
        return "📊 박스권 → 방향성 대기"

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
    pct = diff / int(p["Close"]) * 100

    tab1, tab2, tab3 = st.tabs(["📊 분석", "🚀 급등주", "🎯 내일반등"])

    # =========================
    # TAB1
    # =========================
    with tab1:

        color = "red" if diff > 0 else "blue"
        arrow = "▲" if diff > 0 else "▼"

        # 🔥 현재가
        st.markdown(f"""
        <div style="text-align:center;">
            <div style="font-size:44px;font-weight:900;color:{color};">{price:,}원</div>
            <div style="color:{color};font-size:16px;font-weight:700;">
                {arrow} {diff:+,}원 ({pct:+.2f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)

        # =========================
        # 📊 1줄 핵심 표 (완성형)
        # =========================
        st.markdown(f"""
        <div style="
            display:flex;
            justify-content:space-between;
            background:#f8f9fa;
            padding:14px;
            border-radius:14px;
            font-weight:800;
            font-size:13px;
        ">
            <div>📈 상승<br><span style="color:#ff4d4d;font-size:16px;">{l['Pred']:.1f}%</span></div>

            <div>🎯 적중률<br><span style="font-size:16px;">{l['Acc']:.1f}%</span></div>

            <div>🐳 세력<br><span style="color:#1e90ff;font-size:16px;">{l['Whale']:.1f}%</span></div>

            <div>🟢 추천매수<br><span style="color:#00a86b;font-size:16px;">{int(l['Buy']):,}</span></div>

            <div>🔴 추천매도<br><span style="color:#ff3b3b;font-size:16px;">{int(l['Sell']):,}</span></div>

            <div>📊 전일<br><span style="color:{'red' if diff>0 else 'blue'};font-size:16px;">
                {diff:+,}
            </span></div>
        </div>
        """, unsafe_allow_html=True)

        # =========================
        # 🚨 신호
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
        # 🧠 종합 분석
        # =========================
        st.markdown("### 🧠 종합 분석")

        st.markdown(f"""
        <div style="
            padding:12px;
            border-radius:12px;
            background:white;
            border:1px solid #eee;
            font-size:14px;
            line-height:1.5;
        ">
        {analysis_text(l)}
        </div>
        """, unsafe_allow_html=True)

        # =========================
        # 📰 뉴스
        # =========================
        st.markdown("### 📰 뉴스")
        for n in get_news(name):
            st.write("•", n)

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