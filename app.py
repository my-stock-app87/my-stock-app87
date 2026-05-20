import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import FinanceDataReader as fdr

st.set_page_config(page_title="AI STOCK MASTER", layout="wide")

# =====================================================
# 📅 한글 날짜
# =====================================================
now = datetime.now()
today = f"{now.year}년 {now.month}월 {now.day}일"

st.title("🔥 AI STOCK MASTER PRO")
st.caption(f"실전 매수/매도 추천 시스템 | {today}")

# =====================================================
# 데이터
# =====================================================
@st.cache_data(ttl=3600)
def stock_list():
    return fdr.StockListing("KRX")[["Code", "Name"]]

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    row = df_stock[df_stock["Name"] == name]
    return row.iloc[0]["Code"] if not row.empty else None

@st.cache_data(ttl=300)
def price(c):
    df = fdr.DataReader(c)
    if df.empty:
        return df
    return df.reset_index().tail(200)

# =====================================================
# 지표
# =====================================================
def ind(df):
    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df.dropna().reset_index(drop=True)

# =====================================================
# 🔥 매수 가격
# =====================================================
def buy_price(df):
    l = df.iloc[-1]

    if l["RSI"] < 30:
        return int(l["Close"] * 0.99), "🔥 과매도 반등 구간 → 즉시 분할매수"
    if l["Close"] > l["MA5"] and l["Volume"] > l["VOL20"]:
        return int(l["Close"]), "🟢 상승추세 → 눌림목 매수"
    return int(l["MA20"] * 1.01), "⚠️ MA20 지지 확인 후 매수"

# =====================================================
# 매도 가격
# =====================================================
def sell_price(df):
    l = df.iloc[-1]
    return int(l["Close"] * 1.08)

# =====================================================
# 세력 확률
# =====================================================
def power(df):
    l = df.iloc[-1]
    s = 0

    if l["Volume"] > l["VOL20"] * 2:
        s += 40
    if l["Close"] > l["MA20"]:
        s += 25
    if l["RSI"] < 70:
        s += 20
    if l["Close"] > l["MA5"]:
        s += 15

    return min(s, 100)

# =====================================================
# 설명
# =====================================================
def explain(df, name):
    l = df.iloc[-1]
    p = power(df)

    return f"""
📊 {name} 분석 리포트 ({today})

- 현재가: {int(l['Close'])}원
- RSI: {l['RSI']:.1f}
- 거래량: {"급증" if l["Volume"] > l["VOL20"] else "보통"}

🔥 세력 개입 확률: {p}%

👉 해석:
{'세력 유입 가능성 높음' if p > 70 else '개인 매매 중심 흐름'}

📌 전략:
- 매수: MA20 근처 또는 눌림
- 매도: +8% 또는 거래량 급증 구간
"""

# =====================================================
# 🚀 AI 추천 종목 (핵심)
# =====================================================
def recommend():
    results = []

    for name in names[:40]:  # 속도 제한
        df = price(code(name))
        if df.empty:
            continue

        df = ind(df)

        l = df.iloc[-1]

        score = 0
        if l["Volume"] > l["VOL20"] * 2:
            score += 40
        if l["Close"] > l["MA5"]:
            score += 20
        if l["RSI"] < 70:
            score += 20
        if l["Close"] > l["MA20"]:
            score += 20

        if score >= 70:
            bp, _ = buy_price(df)
            sp = sell_price(df)

            results.append((name, score, bp, sp))

    return sorted(results, key=lambda x: x[1], reverse=True)

# =====================================================
# TAB
# =====================================================
tab1, tab2 = st.tabs([
    "🔍 상세분석",
    "🚀 AI 추천"
])

# =====================================================
# 상세분석
# =====================================================
with tab1:

    stock = st.selectbox("종목 선택", names)

    if st.button("분석 실행"):

        df = price(code(stock))

        if df.empty:
            st.error("데이터 없음")
        else:

            df = ind(df)

            st.metric("현재가", f"{df.iloc[-1]['Close']:,.0f}")
            st.metric("세력확률", f"{power(df)}%")

            bp, reason = buy_price(df)

            st.success(f"🟢 추천 매수 가격: {bp:,}원")
            st.error(f"🔴 목표 매도 가격: {sell_price(df):,}원")

            st.info(f"📌 매수 이유: {reason}")

            st.write(explain(df, stock))

            st.line_chart(df.set_index("Date")[["Close", "MA5", "MA20"]])

# =====================================================
# AI 추천
# =====================================================
with tab2:

    st.subheader(f"🚀 AI 추천 TOP 종목 ({today})")

    rec = recommend()

    if not rec:
        st.warning("추천 없음")
    else:
        for r in rec[:10]:

            st.markdown("---")

            st.write(f"📈 종목: {r[0]}")
            st.write(f"🔥 점수: {r[1]}점")
            st.write(f"🟢 추천 매수가: {r[2]:,}원")
            st.write(f"🔴 목표 매도가: {r[3]:,}원")