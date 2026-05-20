import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import FinanceDataReader as fdr

# =====================================================
# 설정
# =====================================================
st.set_page_config(page_title="AI STOCK MASTER", layout="wide")

today = datetime.now().strftime("%Y-%m-%d")

st.title("👑 AI STOCK MASTER PRO")
st.caption(f"실시간 분석 시스템 | {today}")

# =====================================================
# 데이터 로드
# =====================================================
@st.cache_data(ttl=3600)
def get_stock_list():
    return fdr.StockListing('KRX')[['Code', 'Name']]

stock_df = get_stock_list()
stock_names = stock_df['Name'].tolist()

def get_code(name):
    row = stock_df[stock_df['Name'] == name]
    return row.iloc[0]['Code'] if not row.empty else None

@st.cache_data(ttl=300)
def get_price(code):
    df = fdr.DataReader(code)
    if df.empty:
        return df
    df = df.reset_index()
    return df.tail(200)

# =====================================================
# 보조지표
# =====================================================
def add_ind(df):
    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df.dropna()

# =====================================================
# 1️⃣ 보유종목 매도 타이밍
# =====================================================
def sell_signal(df):
    l = df.iloc[-1]

    if l["RSI"] > 75:
        return "🔥 과열 → 분할매도"
    if l["Close"] < l["MA5"]:
        return "⚠️ 추세 약화 → 매도 고려"
    if l["Volume"] > l["VOL20"] * 2:
        return "📊 급등 거래량 → 분할익절"
    return "✅ 홀딩"

# =====================================================
# 2️⃣ 세력 확률
# =====================================================
def power_score(df):
    l = df.iloc[-1]
    score = 0

    if l["Volume"] > l["VOL20"] * 2:
        score += 35
    if l["Close"] > l["MA5"]:
        score += 25
    if l["Close"] > l["MA20"]:
        score += 20
    if l["RSI"] < 70:
        score += 20

    return min(score, 100)

# =====================================================
# 3️⃣ 매수 타이밍
# =====================================================
def buy_signal(df):
    l = df.iloc[-1]

    if l["RSI"] < 30:
        return "🔥 과매도 반등 구간"
    if l["Close"] > l["MA5"] and l["Volume"] > l["VOL20"]:
        return "🟢 눌림목 매수"
    return "⚠️ 관망"

# =====================================================
# 4️⃣ 내일 급등 후보 (확률형)
# =====================================================
def top_pick(df):
    l = df.iloc[-1]
    score = 0

    if l["Volume"] > l["VOL20"] * 2:
        score += 40
    if l["RSI"] < 60:
        score += 20
    if l["Close"] > l["MA5"]:
        score += 20
    if l["Close"] > l["MA20"]:
        score += 20

    return min(score, 100)

# =====================================================
# 5️⃣ 테마주
# =====================================================
themes = {
    "AI / 반도체": ["삼성전자", "SK하이닉스"],
    "2차전지": ["에코프로비엠", "포스코퓨처엠"],
    "바이오": ["셀트리온", "HLB"],
    "방산": ["한화에어로스페이스", "LIG넥스원"]
}

# =====================================================
# TAB
# =====================================================
tab1, tab2, tab3 = st.tabs([
    "💰 보유종목",
    "🔍 상세분석",
    "🚀 추천/테마"
])

# =====================================================
# TAB 1
# =====================================================
with tab1:

    st.subheader("보유종목")

    name = st.selectbox("종목 선택", stock_names, key="p1")
    buy = st.number_input("매수가", value=50000)
    qty = st.number_input("수량", value=1)

    if "portfolio" not in st.session_state:
        st.session_state["portfolio"] = []

    if st.button("추가"):
        st.session_state["portfolio"].append({
            "name": name,
            "buy": buy,
            "qty": qty
        })

    for i, item in enumerate(st.session_state["portfolio"]):

        df = get_price(get_code(item["name"]))
        if df.empty:
            continue

        df = add_ind(df)
        l = df.iloc[-1]

        price = l["Close"]
        profit = (price - item["buy"]) / item["buy"] * 100

        st.markdown(f"## 📦 {item['name']}")
        st.metric("현재가", f"{price:,.0f}")
        st.metric("수익률", f"{profit:.2f}%")

        st.info("📤 매도: " + sell_signal(df))

# =====================================================
# TAB 2
# =====================================================
with tab2:

    stock = st.selectbox("종목", stock_names, key="d1")

    if st.button("분석"):

        df = get_price(get_code(stock))

        if df.empty:
            st.error("데이터 없음")
        else:
            df = add_ind(df)

            st.metric("세력확률", f"{power_score(df)}%")
            st.info("매수: " + buy_signal(df))
            st.warning("매도: " + sell_signal(df))

            st.line_chart(df.set_index("Date")[["Close"]])

            st.write("📊 설명: 거래량 + 추세 + RSI 기반 단기 분석")

# =====================================================
# TAB 3
# =====================================================
with tab3:

    st.subheader("🚀 내일 급등 후보 TOP")

    results = []

    for name in stock_names[:30]:  # 너무 많으면 느려서 제한
        df = get_price(get_code(name))
        if df.empty:
            continue

        df = add_ind(df)

        score = top_pick(df)

        if score > 70:
            results.append((name, score))

    results = sorted(results, key=lambda x: x[1], reverse=True)

    st.success(f"📅 {today} 기준 급등 후보")

    for r in results[:10]:
        st.write(f"🚀 {r[0]} : {r[1]}점")

    st.subheader("🔥 테마주")

    for t, lst in themes.items():
        st.write(f"### {t}")
        st.write(", ".join(lst))