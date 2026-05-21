import streamlit as st
import pandas as pd
import numpy as np
from pykrx import stock
from datetime import datetime

# =========================
# 페이지 설정
# =========================
st.set_page_config(page_title="주식주신 PRO DEBUG", layout="wide")
st.title("🔥 주식주신 PRO (DEBUG 최종버전)")

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
# 🔥 STEP 1: 무조건 실행 확인
# =========================
st.write("🟢 STEP 1: APP START OK")

# =========================
# 데이터 로딩
# =========================
def load_data(code):
    try:
        df = stock.get_market_ohlcv_by_date(
            "20240101",
            datetime.today().strftime("%Y%m%d"),
            code
        )

        st.write("🟡 STEP 2: RAW DATA CALL DONE")

        if df is None or df.empty:
            st.write("❌ RAW DF EMPTY")
            return pd.DataFrame()

        df = df.reset_index()
        df.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]

        st.write("🟢 STEP 3: DATA LOADED OK")
        return df

    except Exception as e:
        st.write("❌ ERROR:", e)
        return pd.DataFrame()

# =========================
# 계산
# =========================
def calc(df):
    st.write("🟡 STEP 4: CALC START")

    if df is None or df.empty:
        st.write("❌ CALC INPUT EMPTY")
        return df

    df = df.copy()

    df["Close"] = df["Close"].ffill().fillna(0)
    df["Open"] = df["Open"].ffill().fillna(0)
    df["Volume"] = df["Volume"].fillna(0)

    df["MA5"] = df["Close"].rolling(5, min_periods=1).mean()
    df["MA20"] = df["Volume"].rolling(20, min_periods=1).mean()

    vol = df["Volume"] / (df["MA20"] + 1e-10)
    trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)
    power = (df["Close"] - df["Open"]) / (df["Open"] + 1e-10)

    df["Whale"] = np.nan_to_num(vol * 30 + trend * 30 + power * 20)

    st.write("🟢 STEP 5: CALC DONE")
    return df

# =========================
# 실행
# =========================
df = load_data(code)

st.write("📊 RAW DF SHAPE:", df.shape)

df = calc(df)

st.write("📊 FINAL DF SHAPE:", df.shape)

# =========================
# 🔥 핵심: 무조건 출력
# =========================
if df is None or df.empty:
    st.error("🚨 최종 데이터 없음 (여기서 문제 발생)")
    st.stop()

# =========================
# 최신값
# =========================
last = df.iloc[-1]
prev = df.iloc[-2]

price = int(last["Close"])
pct = ((price - prev["Close"]) / prev["Close"]) * 100

whale = float(last["Whale"])

buy = int(price * 0.98)
sell = int(price * 1.04)

# =========================
# 상태
# =========================
if whale > 60:
    status = "🟥 매수구간"
elif whale < 30:
    status = "🟦 매도구간"
else:
    status = "⚪ 관망"

# =========================
# UI (Streamlit 기본 - 100% 안정)
# =========================
st.markdown("---")

col1, col2, col3 = st.columns(3)

col1.metric("현재가", f"{price:,}원", f"{pct:+.2f}%")
col2.metric("매수", f"{buy:,}원")
col3.metric("매도", f"{sell:,}원")

st.markdown("---")

st.subheader("📊 세력지수")
st.write(whale)

st.progress(min(int(whale), 100) / 100)

st.subheader("🤖 상태")
st.info(status)

# =========================
# 데이터 확인
# =========================
st.subheader("📦 RAW DATA DEBUG")
st.dataframe(df.tail(10))