import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr

# =====================================================
# 설정 (모바일 최적화)
# =====================================================
st.set_page_config(page_title="AI STOCK MASTER PRO", layout="centered")

st.title("🔥 AI STOCK MASTER PRO")
st.caption("모바일 최적화 트레이딩 분석 시스템")

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

@st.cache_data(ttl=120)
def get_price(c):
    return fdr.DataReader(c)

# =====================================================
# 지표
# =====================================================
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

# =====================================================
# 분석 로직
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

def buy_price(df):
    l = df.iloc[-1]

    if l["RSI"] < 30:
        return int(l["Close"] * 0.99), "과매도 반등"
    if l["Close"] > l["MA5"]:
        return int(l["Close"]), "상승 추세"
    return int(l["MA20"] * 1.01), "MA20 지지"

def sell_price(df):
    l = df.iloc[-1]
    return int(l["Close"] * 1.08)

# =====================================================
# 1주 분석
# =====================================================
def week(df):
    d = df.tail(5)
    return {
        "1주 최고": int(d["Close"].max()),
        "1주 최저": int(d["Close"].min()),
        "변동폭(%)": round((d["Close"].max() - d["Close"].min()) / d["Close"].min() * 100, 2)
    }

# =====================================================
# AI 점수
# =====================================================
def ai_score(df):
    l = df.iloc[-1]
    score = 0

    if l["Close"] > l["MA5"]:
        score += 20
    if l["Close"] > l["MA20"]:
        score += 20
    if l["Volume"] > l["VOL20"] * 2:
        score += 30
    if 40 < l["RSI"] < 70:
        score += 20

    return min(score, 100)

# =====================================================
# 시장 스캔
# =====================================================
def scan():
    result = []

    for n in names[:60]:  # 속도 안정
        try:
            c = code(n)
            df = get_price(c)

            if df.empty:
                continue

            df = ind(df)
            if df.empty:
                continue

            result.append({
                "종목": n,
                "AI점수": ai_score(df)
            })

        except:
            continue

    return pd.DataFrame(result).sort_values("AI점수", ascending=False)

# =====================================================
# 테마
# =====================================================
theme_map = {
    "AI": ["네이버", "카카오", "삼성"],
    "2차전지": ["에코", "포스코", "LG"],
    "반도체": ["삼성전자", "SK하이닉스"],
    "로봇": ["레인보우", "두산"]
}

def theme():
    out = []

    for t, keys in theme_map.items():
        for n in names:
            if any(k in n for k in keys):
                out.append({"테마": t, "종목": n})

    return pd.DataFrame(out)

# =====================================================
# UI
# =====================================================
selected = st.selectbox("📊 종목 선택", names)

if st.button("🔄 새로고침"):
    st.cache_data.clear()
    st.rerun()

# =====================================================
# 실행
# =====================================================
c = code(selected)

if c:
    df = get_price(c)

    if not df.empty:
        df = ind(df)

        if not df.empty:
            l = df.iloc[-1]

            # =====================
            # 📱 핵심 카드 UI
            # =====================
            st.subheader("📊 현재 상태")

            col1, col2, col3 = st.columns(3)
            col1.metric("현재가", f"{int(l['Close']):,}")
            col2.metric("RSI", round(l["RSI"], 1))
            col3.metric("세력", power(df))

            st.markdown("---")

            # =====================
            # 📈 1주
            # =====================
            w = week(df)

            st.subheader("📈 1주 분석")
            st.write(w)

            st.markdown("---")

            # =====================
            # 📊 5일 데이터
            # =====================
            with st.expander("📊 최근 5일 데이터"):
                st.dataframe(df.tail(5)[["Close", "Volume", "RSI"]])

            # =====================
            # 🧠 AI 해석
            # =====================
            with st.expander("🧠 AI 분석"):
                bp, reason = buy_price(df)
                sp = sell_price(df)

                st.write(f"""
- 전략: {reason}
- 매수가: {bp:,}
- 목표가: {sp:,}
                """)

# =====================================================
# 🚀 급등주
# =====================================================
if st.button("🚀 AI 급등주 TOP 10"):
    st.dataframe(scan().head(10))

# =====================================================
# 📊 테마
# =====================================================
if st.button("📊 테마주"):
    st.dataframe(theme())