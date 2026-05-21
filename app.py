import streamlit as st
import pandas as pd
import numpy as np
from pykrx import stock
import streamlit.components.v1 as components
from datetime import datetime

# =========================
# 페이지 설정
# =========================
st.set_page_config(page_title="주식주신 PRO", layout="centered")
st.title("🔥 주식주신 PRO (절대안죽는버전)")

# =========================
# 종목
# =========================
stocks = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "현대차": "005380",
    "NAVER": "035420",
    "카카오": "035720"
}

name = st.selectbox("종목 선택", list(stocks.keys()))
code = stocks[name]

# =========================
# 데이터 로딩 (절대안죽는버전)
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

    except Exception as e:
        st.write("데이터 오류:", e)
        return pd.DataFrame()

# =========================
# 지표 계산 (절대안죽는 구조)
# =========================
def calc(df):
    if df is None or df.empty:
        return df

    df = df.copy()

    df["Close"] = df["Close"].fillna(method="ffill")
    df["Open"] = df["Open"].fillna(method="ffill")
    df["Volume"] = df["Volume"].fillna(0)

    df["MA5"] = df["Close"].rolling(5, min_periods=1).mean()
    df["MA20"] = df["Volume"].rolling(20, min_periods=1).mean()

    # 🔥 NaN 방지 핵심
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
# 🔥 핵심: 무조건 화면 출력
# =========================
if df is None or df.empty or len(df) < 2:

    st.error("⚠️ 데이터 부족 (하지만 앱은 정상 실행됨)")

    st.info("👉 pykrx에서 데이터가 안 들어오는 상태입니다.")
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
    color = "red"
elif whale < 30:
    status = "🟦 매도구간"
    color = "blue"
else:
    status = "⚪ 관망"
    color = "gray"

# =========================
# UI
# =========================
html = f"""
<table style="width:100%; border-collapse:collapse; font-family:sans-serif;">

<tr style="background:#f7f7f7;">
<td style="padding:10px;"><b>현재가</b></td>
<td style="padding:10px; text-align:right;">
{price:,}원 ({pct:+.2f}%)
</td>
<td style="padding:10px; text-align:right; color:{color}; font-weight:bold;">
{status}
</td>
</tr>

<tr>
<td style="padding:10px;"><b>매수</b></td>
<td colspan="2" style="padding:10px; text-align:right; color:red;">
{buy:,}원
</td>
</tr>

<tr style="background:#f7f7f7;">
<td style="padding:10px;"><b>매도</b></td>
<td colspan="2" style="padding:10px; text-align:right; color:blue;">
{sell:,}원
</td>
</tr>

<tr>
<td style="padding:10px;"><b>세력지수</b></td>
<td colspan="2" style="padding:10px; text-align:right;">
{whale:.1f}
</td>
</tr>

</table>
"""

components.html(html, height=300)

# =========================
# AI 해석
# =========================
st.subheader("🤖 AI 분석")

if whale > 60:
    st.success("세력 유입 강함 → 단기 상승 가능성")
elif whale < 30:
    st.warning("약세 구간 → 관망 필요")
else:
    st.info("중립 구간 → 방향 없음")