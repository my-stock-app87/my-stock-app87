import streamlit as st
import pandas as pd
import numpy as np
from pykrx import stock
from datetime import datetime

# =========================
# 페이지 설정
# =========================
st.set_page_config(page_title="주식주신 PRO", layout="wide")
st.title("🔥 주식주신 PRO (완전 안정 버전)")

# =========================
# 종목
# =========================
stocks = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "현대차": "005380",
    "NAVER": "035420",
    "카카오": "035720",
    "LG에너지솔루션": "373220"
}

name = st.selectbox("종목 선택", list(stocks.keys()))
code = stocks[name]

# =========================
# 데이터 로딩 (절대안죽음)
# =========================
@st.cache_data(ttl=60)
def load_data(code):
    try:
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

    except:
        return pd.DataFrame()

# =========================
# 지표 계산 (완전 방어)
# =========================
def calc(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    df["Close"] = df["Close"].ffill().fillna(0)
    df["Open"] = df["Open"].ffill().fillna(0)
    df["Volume"] = df["Volume"].fillna(0)

    df["MA5"] = df["Close"].rolling(5, min_periods=1).mean()
    df["MA20"] = df["Volume"].rolling(20, min_periods=1).mean()

    vol_ratio = df["Volume"] / (df["MA20"] + 1e-10)
    trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)
    power = (df["Close"] - df["Open"]) / (df["Open"] + 1e-10)

    df["Whale"] = np.nan_to_num(vol_ratio * 30 + trend * 30 + power * 20)

    return df

# =========================
# 실행
# =========================
df = load_data(code)
df = calc(df)

# =========================
# 🔥 무조건 화면 유지
# =========================
if df is None or df.empty or len(df) < 2:
    st.error("데이터 없음 (pykrx 문제 or 휴장일)")
    st.stop()

# =========================
# 최신 데이터
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
# 🔥 UI (Streamlit native - 안정)
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("현재가", f"{price:,}원", f"{pct:+.2f}%")
col2.metric("매수추천", f"{buy:,}원")
col3.metric("매도추천", f"{sell:,}원")

st.markdown("---")

st.subheader("📊 세력 분석")
st.progress(min(int(whale), 100) / 100)

st.write(f"세력지수: {whale:.1f}")
st.write(f"상태: {status}")

# =========================
# AI 전략
# =========================
st.subheader("🤖 AI 전략")

if whale > 60:
    st.success("세력 강한 유입 → 단기 상승 가능성")
elif whale < 30:
    st.warning("약세 구간 → 관망")
else:
    st.info("중립 구간 → 방향 없음")