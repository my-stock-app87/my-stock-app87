import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import FinanceDataReader as fdr

# =====================================================
# 설정
# =====================================================
st.set_page_config(page_title="AI STOCK MASTER", layout="wide")

today = "2026년 5월 21일"

st.title("🔥 AI STOCK MASTER PRO")
st.caption(f"실시간 트레이딩 분석 시스템 | {today}")

# =====================================================
# 데이터
# =====================================================
@st.cache_data(ttl=300)
def stock_list():
    return fdr.StockListing("KRX")[["Code", "Name"]]

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    row = df_stock[df_stock["Name"] == name]
    return row.iloc[0]["Code"] if not row.empty else None

@st.cache_data(ttl=60)  # 🔥 실시간 느낌
def price(c):
    df = fdr.DataReader(c)
    if df.empty:
        return df
    return df.reset_index().tail(120)

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
# 매수 / 매도 / 세력
# =====================================================
def buy_price(df):
    l = df.iloc[-1]

    if l["RSI"] < 30:
        return int(l["Close"] * 0.99), "과매도 반등"
    if l["Close"] > l["MA5"]:
        return int(l["Close"]), "상승 추세 눌림"
    return int(l["MA20"] * 1.01), "MA20 지지 매수"

def sell_price(df):
    l = df.iloc[-1]
    return int(l["Close"] * 1.08)

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
# 🚀 실시간 테이블 생성
# =====================================================
def make_table(df, name):

    l = df.iloc[-1]
    bp, reason = buy_price(df)
    sp = sell_price(df)
    p = power(df)

    return {
        "종목": name,
        "현재가": int(l["Close"]),
        "RSI": round(l["RSI"], 1),
        "거래량": int(l["Volume"]),
        "세력확률(%)": p,
        "추천매수가": bp,
        "목표매도가": sp,
        "매수이유": reason
    }

# =====================================================
# UI
# =====================================================
st.subheader("📊 실시간 트레이딩 테이블")

col1, col2 = st.columns(2)

with col1:
    selected = st.selectbox("종목 선택", names)

with col2:
    refresh = st.button("🔄 실시간 업데이트")

if refresh:
    st.rerun()

# =====================================================
# 단일 분석
# =====================================================
if st.button("📌 분석 실행"):

    df = price(code(selected))

    if df.empty:
        st.error("데이터 없음")

    else:
        df = ind(df)

        table = make_table(df, selected)

        st.success("📊 AI 트레이딩 결과")

        st.table(pd.DataFrame([table]))

        st.markdown("### 📌 해석")
        st.write(f"""
- 현재 {selected}는 RSI {table['RSI']} 상태
- 세력 개입 확률 {table['세력확률(%)']}%
- 추천 매수가 {table['추천매수가']}원 근처
- 목표가는 {table['목표매도가']}원

👉 결론: {table['매수이유']} 전략 구간
""")