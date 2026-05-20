import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr

# =========================
# 설정
# =========================
st.set_page_config(page_title="AI STOCK MASTER PRO", layout="centered")
st.title("🔥 AI STOCK MASTER PRO")

# =========================
# 데이터
# =========================
@st.cache_data(ttl=300)
def stock_list():
    return fdr.StockListing("KRX")[["Code", "Name"]]

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    row = df_stock[df_stock["Name"] == name]
    return row.iloc[0]["Code"] if not row.empty else None

@st.cache_data(ttl=120)
def get_price(c):
    return fdr.DataReader(c)

# =========================
# 지표
# =========================
def ind(df):
    if len(df) < 20:
        return pd.DataFrame()

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df.tail(120).reset_index(drop=True)

# =========================
# 분석 로직
# =========================
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

def buy_price(df):
    l = df.iloc[-1]

    if l["RSI"] < 30:
        return int(l["Close"] * 0.99), "과매도 반등"
    if l["Close"] > l["MA5"]:
        return int(l["Close"]), "상승 추세"
    return int(l["MA20"] * 1.01), "MA20 지지"

def sell_price(df):
    return int(df.iloc[-1]["Close"] * 1.08)

def ai_score(df):
    l = df.iloc[-1]
    s = 0

    if l["Close"] > l["MA5"]:
        s += 20
    if l["Close"] > l["MA20"]:
        s += 20
    if l["Volume"] > l["VOL20"] * 2:
        s += 30
    if 40 < l["RSI"] < 70:
        s += 20

    return min(s, 100)

# =========================
# 시장 스캔
# =========================
def scan_market():
    res = []

    for n in names[:60]:
        try:
            df = get_price(code(n))
            if df.empty:
                continue

            df = ind(df)
            if df.empty:
                continue

            res.append({
                "종목": n,
                "AI점수": ai_score(df)
            })
        except:
            continue

    return pd.DataFrame(res).sort_values("AI점수", ascending=False)

# =========================
# 테마
# =========================
theme_map = {
    "AI": ["네이버", "카카오", "삼성"],
    "2차전지": ["에코", "포스코", "LG"],
    "반도체": ["삼성전자", "SK하이닉스"],
    "로봇": ["레인보우", "두산"]
}

def theme_list():
    out = []
    for t, keys in theme_map.items():
        for n in names:
            if any(k in n for k in keys):
                out.append({"테마": t, "종목": n})
    return pd.DataFrame(out)

# =========================
# 탭 UI
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 종목분석",
    "🚀 급등주",
    "📊 테마주",
    "🧠 AI 내일 추천"
])

# =========================
# 1️⃣ 종목분석
# =========================
with tab1:
    st.subheader("📊 종목 선택")
    selected = st.selectbox("종목", names)

    df = get_price(code(selected))

    if not df.empty:
        df = ind(df)

        if not df.empty:
            l = df.iloc[-1]

            st.subheader("💰 실시간 가격")
            st.metric("현재가", f"{int(l['Close']):,}")

            st.subheader("📈 5일 분석")
            st.dataframe(df.tail(5)[["Close", "Volume", "RSI"]])

            st.subheader("🧠 AI 분석")
            st.write(f"AI 점수: {ai_score(df)} / 100")

            bp, reason = buy_price(df)
            sp = sell_price(df)

            st.subheader("📌 매수/매도")
            st.write(f"- 매수: {bp:,}")
            st.write(f"- 매도: {sp:,}")
            st.write(f"- 전략: {reason}")

            st.subheader("📊 세력 유입 확률")
            st.write(f"{power(df)}%")

# =========================
# 2️⃣ 급등주
# =========================
with tab2:
    st.subheader("🚀 AI 급등주 TOP 10")
    st.dataframe(scan_market().head(10), use_container_width=True)

# =========================
# 3️⃣ 테마주
# =========================
with tab3:
    st.subheader("📊 테마 종목")
    st.dataframe(theme_list(), use_container_width=True)

# =========================
# 4️⃣ AI 내일 추천
# =========================
with tab4:
    st.subheader("🧠 AI 내일 추천주")

    rec = scan_market().head(5).copy()
    rec["추천이유"] = "AI 점수 + 거래량 + 추세 기반"

    st.dataframe(rec, use_container_width=True)