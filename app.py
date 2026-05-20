import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import FinanceDataReader as fdr

st.set_page_config(page_title="AI TRADING MASTER", layout="wide")

today = datetime.now().strftime("%Y-%m-%d")

st.title("🔥 AI TRADING MASTER PRO")
st.caption(f"실전 매수/매도 가격 + 설명 시스템 | {today}")

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
# 🔥 핵심: 매수 가격 계산 (이게 중요)
# =====================================================
def buy_price(df):
    l = df.iloc[-1]

    support = df["MA20"].iloc[-1]
    rsi = l["RSI"]

    if rsi < 30:
        return int(l["Close"] * 0.99), "🔥 과매도 → 즉시 분할매수 구간"
    if l["Close"] > l["MA5"] and l["Volume"] > l["VOL20"]:
        return int(l["Close"] * 1.00), "🟢 추세 상승 → 눌림 매수"
    return int(support * 1.01), "⚠️ 지지선 근처 대기 매수"

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
# 설명 (진짜 중요)
# =====================================================
def explain(df, stock):
    l = df.iloc[-1]
    p = power(df)

    text = f"""
📊 [{stock}] 현재 상태 분석

- 현재가 흐름: {int(l['Close'])}원 기준 단기 변동성 구간
- RSI: {l['RSI']:.1f} → {'과매도 반등 구간' if l['RSI'] < 30 else '중립~과열 구간'}
- 거래량: {'급증' if l['Volume'] > l['VOL20'] else '일반 흐름'}

🔥 세력 개입 확률: {p}%

👉 해석:
{'세력이 들어오는 초기 수급 가능성이 높음' if p > 70 else '개인 매매 중심 흐름'}

📌 전략:
- 매수: 눌림 또는 MA20 근처
- 매도: +8% 구간 또는 거래량 폭발 시
"""
    return text

# =====================================================
# UI
# =====================================================
tab1, tab2 = st.tabs(["💰 보유종목", "🔍 상세분석"])

# =====================================================
# TAB 1 (실제 매수/매도 가격)
# =====================================================
with tab1:

    st.subheader("💰 내 보유종목")

    name = st.selectbox("종목", names, key="p1")
    buy = st.number_input("매수가", value=50000)
    qty = st.number_input("수량", value=1)

    if "pf" not in st.session_state:
        st.session_state["pf"] = []

    if st.button("추가"):
        st.session_state["pf"].append({"name": name, "buy": buy, "qty": qty})

    for i, item in enumerate(st.session_state["pf"]):

        df = price(code(item["name"]))
        if df.empty:
            continue

        df = ind(df)
        l = df.iloc[-1]

        cur = l["Close"]
        profit = (cur - item["buy"]) / item["buy"] * 100

        bp, reason = buy_price(df)
        sp = sell_price(df)

        st.markdown(f"## 📦 {item['name']}")

        st.metric("현재가", f"{cur:,.0f}원")
        st.metric("수익률", f"{profit:.2f}%")

        st.success(f"🟢 추천 매수 가격: {bp:,}원")
        st.error(f"🔴 목표 매도 가격: {sp:,}원")

        st.info(f"📌 매수 이유: {reason}")

# =====================================================
# TAB 2 (상세 분석 + 설명)
# =====================================================
with tab2:

    stock = st.selectbox("종목 선택", names, key="d1")

    if st.button("분석 실행"):

        df = price(code(stock))

        if df.empty:
            st.error("데이터 없음")
        else:

            df = ind(df)

            st.metric("현재가", f"{df.iloc[-1]['Close']:,.0f}")
            st.metric("세력확률", f"{power(df)}%")

            st.subheader("📌 AI 상세 설명")
            st.write(explain(df, stock))

            st.subheader("📈 차트")
            st.line_chart(df.set_index("Date")[["Close", "MA5", "MA20"]])