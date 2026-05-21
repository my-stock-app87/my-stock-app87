import streamlit as st
import pandas as pd
import numpy as np
from pykrx import stock
import streamlit.components.v1 as components
from datetime import datetime, timedelta

# =========================
# 페이지 설정
# =========================
st.set_page_config(page_title="주식주신 PRO", layout="centered")
st.markdown("## 🔥 주식주신 PRO (안정버전)")

# =========================
# 종목 리스트 (KRX 기준)
# =========================
BUILTIN_STOCKS = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "삼성바이오로직스": "207940",
    "현대차": "005380",
    "기아": "000270",
    "셀트리온": "068270",
    "카카오": "035720",
    "NAVER": "035420",
    "에코프로비엠": "247540"
}

names = list(BUILTIN_STOCKS.keys())

# =========================
# 데이터 로딩 (pykrx - 안정형)
# =========================
@st.cache_data(ttl=60)
def get_data(code):
    try:
        end = datetime.today().strftime("%Y%m%d")
        start = (datetime.today() - timedelta(days=180)).strftime("%Y%m%d")

        df = stock.get_market_ohlcv_by_date(start, end, code)

        if df is None or len(df) == 0:
            return pd.DataFrame()

        df = df.reset_index()
        df.rename(columns={
            "시가": "Open",
            "종가": "Close",
            "거래량": "Volume"
        }, inplace=True)

        return df

    except:
        return pd.DataFrame()

# =========================
# 기술적 지표 (안정형)
# =========================
def ind(df):
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    df["Close"] = df["Close"].fillna(method="ffill")
    df["Open"] = df["Open"].fillna(method="ffill")
    df["Volume"] = df["Volume"].fillna(0)

    df["MA5"] = df["Close"].rolling(5, min_periods=1).mean()
    df["MA20_Vol"] = df["Volume"].rolling(20, min_periods=1).mean()

    vol = df["Volume"] / (df["MA20_Vol"] + 1e-10)
    trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)
    power = (df["Close"] - df["Open"]) / (df["Open"] + 1e-10)

    df["Whale"] = np.clip(vol * 35 + trend * 30 + power * 20, 0, 100)

    return df

# =========================
# UI
# =========================
st.markdown("## 🧠 종합분석")

name = st.selectbox("종목 선택", names)
code = BUILTIN_STOCKS[name]

df = get_data(code)
df = ind(df)

# =========================
# 데이터 체크 (무조건 UI 유지)
# =========================
if df is None or df.empty or len(df) < 2:
    st.error("⚠️ 데이터 부족 (pykrx 조회 실패)")
    st.write(df)
    st.stop()

# =========================
# 최신 데이터
# =========================
l = df.iloc[-1]
p = df.iloc[-2]

price = int(l["Close"])
pct = ((price - p["Close"]) / (p["Close"] + 1e-10)) * 100

buy_price = int(price * 0.98)
sell_price = int(price * 1.04)

whale = float(l["Whale"])
vol_pct = ((l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10)) * 100
up_prob = np.clip(whale * 0.7, 0, 95)

# =========================
# 상태 판단
# =========================
if whale >= 65 and vol_pct > 0:
    status = "🟥 매수구간"
    color = "#ff4d4d"
elif whale < 35:
    status = "🟦 매도구간"
    color = "#4d79ff"
else:
    status = "⚪ 관망"
    color = "#888888"

# =========================
# HTML UI (안정형)
# =========================
html_code = f"""
<table style="width:100%; border-collapse:collapse; font-family:sans-serif; border:1px solid #ddd; border-radius:10px; overflow:hidden;">

<tr style="background:#f7f7f7;">
    <td style="padding:10px; font-weight:800;">현재가</td>
    <td style="padding:10px; text-align:right;">
        {price:,}원 ({pct:+.2f}%)
    </td>
    <td style="text-align:right; font-weight:900; color:{color};">{status}</td>
</tr>

<tr>
    <td style="padding:10px; font-weight:800;">매수추천</td>
    <td colspan="2" style="padding:10px; text-align:right; color:#ff4d4d; font-weight:800;">
        {buy_price:,}원
    </td>
</tr>

<tr style="background:#f7f7f7;">
    <td style="padding:10px; font-weight:800;">매도추천</td>
    <td colspan="2" style="padding:10px; text-align:right; color:#4d79ff; font-weight:800;">
        {sell_price:,}원
    </td>
</tr>

<tr>
    <td style="padding:10px; font-weight:800;">세력유입</td>
    <td colspan="2" style="padding:10px; text-align:right;">
        {whale:.1f}%
    </td>
</tr>

<tr style="background:#f7f7f7;">
    <td style="padding:10px; font-weight:800;">상승확률</td>
    <td colspan="2" style="padding:10px; text-align:right; color:#e67e22;">
        {up_prob:.1f}%
    </td>
</tr>

</table>
"""

components.html(html_code, height=320, scrolling=True)

# =========================
# AI 전략
# =========================
st.markdown("### 🤖 AI 투자 전략")

if whale >= 70:
    ai = "🚀 세력 강한 유입 → 단기 급등 가능성 매우 높음"
elif whale >= 60:
    ai = "📊 세력 초기 유입 → 분할매수 전략"
elif whale < 35:
    ai = "📉 약세 → 관망 / 손절 우선"
else:
    ai = "⚪ 횡보 → 기다림 구간"

st.info(ai)