import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit.components.v1 as components

# =========================
# 페이지 설정
# =========================
st.set_page_config(page_title="주식주신 PRO", layout="centered")
st.markdown("## 🔥 주식주신 PRO")

# =========================
# 종목 리스트
# =========================
BUILTIN_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "셀트리온": "068270.KS",
    "카카오": "035720.KS",
    "NAVER": "035420.KS",
    "에코프로비엠": "247540.KQ"
}

names = list(BUILTIN_STOCKS.keys())

# =========================
# 데이터 로딩 (안정 버전)
# =========================
@st.cache_data(ttl=30)
def get_price_safe(ticker):
    try:
        df = yf.Ticker(ticker).history(period="1y", interval="1d")

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.dropna(subset=["Close"])
        return df

    except:
        return pd.DataFrame()

# =========================
# 기술적 지표 (완전 방어형)
# =========================
def ind(df):
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # 결측 방어
    df["Close"] = df["Close"].ffill()
    df["Open"] = df["Open"].ffill()
    df["Volume"] = df["Volume"].fillna(0)

    if len(df) < 20:
        return pd.DataFrame()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20_Vol"] = df["Volume"].rolling(20).mean()

    vol = df["Volume"] / (df["MA20_Vol"] + 1e-10)
    trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)
    power = (df["Close"] - df["Open"]) / (df["Open"] + 1e-10) * 100

    df["Whale"] = np.clip(vol * 40 + trend * 30 + power * 10, 0, 100)
    df["Pred"] = np.clip(df["Whale"] * 0.2, 0, 25)

    return df.dropna()

# =========================
# UI
# =========================
st.markdown("## 🧠 종합분석")

name = st.selectbox("종목 선택", names)
ticker = BUILTIN_STOCKS[name]

raw_data = get_price_safe(ticker)
df = ind(raw_data)

# =========================
# 데이터 체크
# =========================
if df is None or df.empty or len(df) < 2:
    st.warning("⚠️ 데이터 부족 (yfinance 결측 또는 종목 제한)")
    st.write("raw_data:", raw_data.tail())
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
# UI 테이블
# =========================
html_code = f"""
<table width="100%" style="border-collapse:collapse;
background-color:white;
border:1px solid #ddd;
border-radius:12px;
font-family:sans-serif;">
<tr style="background:#f7f7f7;">
<td><b>현재가</b></td>
<td align="right">{price:,}원 ({pct:+.2f}%)</td>
<td align="right" style="color:{color}; font-weight:bold;">{status}</td>
</tr>

<tr>
<td><b>매수추천</b></td>
<td colspan="2" align="right" style="color:#ff4d4d;">{buy_price:,}원</td>
</tr>

<tr style="background:#f7f7f7;">
<td><b>매도추천</b></td>
<td colspan="2" align="right" style="color:#4d79ff;">{sell_price:,}원</td>
</tr>

<tr>
<td><b>세력유입</b></td>
<td colspan="2" align="right">{whale:.1f}%</td>
</tr>

<tr>
<td><b>상승확률</b></td>
<td colspan="2" align="right" style="color:#e67e22;">{up_prob:.1f}%</td>
</tr>
</table>
"""

components.html(html_code, height=320, scrolling=True)

# =========================
# AI 전략
# =========================
st.markdown("### 🤖 AI 투자 전략")

if whale >= 70:
    ai = "🚀 세력 강한 유입 → 단기 급등 가능성"
elif whale >= 60:
    ai = "📊 세력 초기 유입 → 분할매수 구간"
elif whale < 35:
    ai = "📉 약세 → 관망 / 손절 우선"
else:
    ai = "⚪ 횡보 구간 → 기다림 필요"

st.info(ai)