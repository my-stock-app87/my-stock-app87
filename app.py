import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from streamlit_autorefresh import st_autorefresh

# =========================
# 설정
# =========================
st.set_page_config(page_title="AI STOCK MASTER PRO", layout="centered")
st.title("🔥 AI STOCK MASTER PRO")

# 🔥 5초마다 자동 새로고침 (실시간 가격용)
st_autorefresh(interval=5000, key="refresh")

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
    if row.empty:
        return None
    return row.iloc[0]["Code"]

@st.cache_data(ttl=60)
def get_price(c):
    try:
        if c is None:
            return pd.DataFrame()

        df = fdr.DataReader(c)
        if df is None or df.empty:
            return pd.DataFrame()

        return df
    except:
        return pd.DataFrame()

# =========================
# 지표
# =========================
def ind(df):
    if df is None or df.empty or len(df) < 20:
        return pd.DataFrame()

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.ewm(alpha=1/14).mean() / (loss.ewm(alpha=1/14).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    df = df.dropna()

    return df.tail(120)

# =========================
# 추천 점수
# =========================
def recommendation_score(df):
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
# 상승 점수
# =========================
def tomorrow_up_probability(df):
    l = df.iloc[-1]
    s = 0

    if l["Close"] > l["MA5"]:
        s += 25
    if l["Close"] > l["MA20"]:
        s += 20
    if l["Volume"] > l["VOL20"] * 1.5:
        s += 20
    if 40 < l["RSI"] < 70:
        s += 20
    if df["Close"].iloc[-1] > df["Close"].iloc[-2]:
        s += 15

    return min(s, 95)

# =========================
# 세력 점수
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

# =========================
# 🔥 5일 상세 (날짜 FIX 완료)
# =========================
def five_day(df):
    if df is None or df.empty:
        return pd.DataFrame()

    d = df.tail(5).copy()
    d.index = pd.to_datetime(d.index)

    return pd.DataFrame({
        "날짜": d.index.strftime("%Y-%m-%d"),
        "시가": d["Open"].astype(int),
        "고가": d["High"].astype(int),
        "저가": d["Low"].astype(int),
        "종가": d["Close"].astype(int),
        "거래량": d["Volume"].astype(int)
    })

# =========================
# 시장 스캔
# =========================
def scan_market():
    res = []

    for n in names[:60]:
        try:
            c = code(n)
            if c is None:
                continue

            df = get_price(c)
            if df.empty:
                continue

            df = ind(df)
            if df.empty or len(df) < 2:
                continue

            res.append({
                "종목": n,
                "추천점수": recommendation_score(df)
            })

        except:
            continue

    df = pd.DataFrame(res)

    if df.empty:
        return df

    return df.sort_values("추천점수", ascending=False)

# =========================
# 테마주
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

    df = pd.DataFrame(out)
    return df.drop_duplicates()

# =========================
# 탭
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 종목분석",
    "🚀 급등주",
    "📊 테마주",
    "🧠 AI 내일추천"
])

# =========================
# 1. 종목분석 (🔥 실시간 가격 포함)
# =========================
with tab1:
    selected = st.selectbox("종목 선택", names)

    stock_code = code(selected)

    if stock_code is None:
        st.error("종목 코드 없음")
        st.stop()

    df_raw = get_price(stock_code)

    if df_raw.empty:
        st.warning("데이터 없음")
        st.stop()

    df = ind(df_raw)

    if df.empty or len(df) < 2:
        st.warning("데이터 부족")
        st.stop()

    l = df.iloc[-1]

    # 🔥 실시간 현재가 (매 5초 자동 갱신)
    realtime_df = fdr.DataReader(stock_code)
    realtime_price = realtime_df["Close"].iloc[-1] if not realtime_df.empty else l["Close"]

    st.subheader("💰 실시간 가격")
    st.metric("현재가", f"{int(realtime_price):,}")

    st.subheader("📈 5일 상세 분석")
    st.dataframe(five_day(df_raw), use_container_width=True)

    st.subheader("🧠 추천점수")
    st.metric("점수", f"{recommendation_score(df)} / 100")

    st.subheader("🧠 내일 상승 점수")
    prob = tomorrow_up_probability(df)
    st.metric("점수", f"{prob}%")

    if prob >= 80:
        st.success("🔥 강한 상승 가능성")
    elif prob >= 60:
        st.info("📈 상승 가능성 있음")
    else:
        st.warning("⚠️ 관망")

    bp, reason = buy_price(df)
    sp = sell_price(df)

    st.subheader("💰 매수/매도")
    st.write(f"- 매수: {bp:,}")
    st.write(f"- 매도: {sp:,}")
    st.write(f"- 전략: {reason}")

    st.subheader("📊 세력 점수")
    st.write(f"{power(df)}%")

# =========================
# 2. 급등주
# =========================
with tab2:
    st.subheader("🚀 급등주 TOP 10")
    st.dataframe(scan_market().head(10), use_container_width=True)

# =========================
# 3. 테마주
# =========================
with tab3:
    st.subheader("📊 테마주")
    st.dataframe(theme_list(), use_container_width=True)

# =========================
# 4. AI 추천
# =========================
with tab4:
    st.subheader("🧠 내일 추천 TOP 5")

    rec = scan_market().head(5)
    rec["추천이유"] = "추세 + 거래량 + RSI 기반"

    st.dataframe(rec, use_container_width=True)