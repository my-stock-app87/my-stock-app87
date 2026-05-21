import streamlit as st
import pandas as pd
import numpy as np
from pykrx import stock
from datetime import datetime
import time

# =========================
# 페이지 설정
# =========================
st.set_page_config(page_title="주식주신 PRO LIVE", layout="wide")
st.title("🔥 주식주신 PRO (LIVE 모드)")

# =========================
# 자동 새로고침 (핵심)
# =========================
st.markdown("⏱️ 5초마다 자동 갱신 중...")
st_autorefresh = st.empty()

# JS처럼 강제 리런 효과
time.sleep(0.5)

# =========================
# 종목
# =========================
stocks = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "현대차": "005380",
    "NAVER": "035420",
    "카카오": "035720"
}

name = st.selectbox("종목 선택", list(stocks.keys()))
code = stocks[name]

# =========================
# 데이터
# =========================
@st.cache_data(ttl=5)
def get_data(code):
    df = stock.get_market_ohlcv_by_date(
        "20240101",
        datetime.today().strftime("%Y%m%d"),
        code
    )

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.reset_index()
    df.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
    return df

df = get_data(code)

if df.empty:
    st.error("데이터 없음")
    st.stop()

# =========================
# 지표
# =========================
df["MA5"] = df["Close"].rolling(5, min_periods=1).mean()
df["MA20"] = df["Volume"].rolling(20, min_periods=1).mean()

vol = df["Volume"] / (df["MA20"] + 1e-10)
trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)

df["Whale"] = np.nan_to_num(vol * 30 + trend * 30)

last = df.iloc[-1]
prev = df.iloc[-2]

price = int(last["Close"])
pct = ((price - prev["Close"]) / prev["Close"]) * 100
whale = float(last["Whale"])

buy = int(price * 0.98)
sell = int(price * 1.03)

# =========================
# 상태
# =========================
if whale > 60:
    status = "🟥 강세 (세력 유입)"
elif whale < 30:
    status = "🟦 약세"
else:
    status = "⚪ 중립"

# =========================
# LIVE UI
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("현재가", f"{price:,}원", f"{pct:+.2f}%")
col2.metric("매수", f"{buy:,}원")
col3.metric("매도", f"{sell:,}원")

st.markdown("---")

st.subheader("📊 실시간 세력 지수")
st.progress(min(int(whale), 100) / 100)
st.write(f"Whale Index: {whale:.2f}")
st.write(f"상태: {status}")

st.markdown("---")

st.subheader("📈 최근 데이터")
st.dataframe(df.tail(10))