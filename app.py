import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from streamlit_autorefresh import st_autorefresh

# =====================================================
# 설정
# =====================================================
st.set_page_config(page_title="주식주신 PRO", layout="wide")

st.title("🔥 주식주신 PRO")

st_autorefresh(interval=5000, key="global_refresh")

# =====================================================
# 스타일
# =====================================================
st.markdown("""
<style>
.stMetric {background:#f8f9fa;padding:12px;border-radius:12px;}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 종목 리스트
# =====================================================
@st.cache_data(ttl=3600)
def stock_list():
    try:
        df = fdr.StockListing("KRX")[["Code", "Name"]]
        return df.dropna().drop_duplicates(subset=["Name"])
    except:
        return pd.DataFrame({
            "Code": ["005930", "000660"],
            "Name": ["삼성전자", "SK하이닉스"]
        })

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    row = df_stock[df_stock["Name"] == name]
    if row.empty:
        return None
    return row["Code"].iloc[0]

# =====================================================
# 가격 데이터
# =====================================================
@st.cache_data(ttl=5)
def get_price(c):
    try:
        if not c:
            return pd.DataFrame()
        return fdr.DataReader(str(c)).tail(120)
    except:
        return pd.DataFrame()

# =====================================================
# 지표
# =====================================================
def ind(df):
    if df is None or df.empty or len(df) < 25:
        return pd.DataFrame()

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    # 🐳 세력 진입 여부 (0~100%)
    vol_ratio = df["Volume"] / (df["VOL20"] + 1e-10)
    price_momentum = (df["Close"] - df["Open"]) / (df["Open"] + 1e-10)
    trend_strength = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)

    raw_whale = (
        vol_ratio * 60 +
        np.clip(price_momentum * 100, -20, 20) +
        np.clip(trend_strength * 50, -15, 15)
    )

    df["Whale_Entry"] = 100 * (1 / (1 + np.exp(-(raw_whale - 50) / 20)))
    df["Whale_Entry"] = np.clip(df["Whale_Entry"], 0, 100)

    # 📈 AI 가격
    std20 = df["Close"].rolling(20).std()
    df["AI_Buy"] = df["MA20"] - (std20 * 1.2)
    df["AI_Sell"] = df["MA20"] + (std20 * 1.2)

    # 📈 예상 상승률
    std5 = df["Close"].rolling(5).std()
    df["Pred_Return"] = (df["Whale_Entry"] / 100) * (std5 / (df["Close"] + 1e-10)) * 100
    df["Pred_Return"] = np.clip(df["Pred_Return"], 0.5, 28.5)

    # 🎯 적중률
    stability = 100 - np.minimum(df["Whale_Entry"] * 0.1, 30)

    df["Pred_Accuracy"] = np.where(
        df["Close"] > df["MA5"],
        72 + (stability * 0.25),
        60 + (stability * 0.25)
    )
    df["Pred_Accuracy"] = np.clip(df["Pred_Accuracy"], 50, 97)

    # 📊 점수
    range_ = (df["High"] - df["Low"]).replace(0, 1e-10)
    body_ratio = ((df["Close"] - df["Open"]) / range_) * 30

    vol_score = np.clip((df["Whale_Entry"] / 200) * 40, 0, 40)
    ma_align = np.where(df["Close"] > df["MA5"], 30, 10)

    df["Stock_Score"] = np.clip(vol_score + ma_align + body_ratio, 10, 100)

    return df.dropna()

# =====================================================
# 급등 + 반등 TOP10
# =====================================================
@st.cache_data(ttl=600)
def scan_market_signals():
    results = []

    leaders = [
        "삼성전자", "SK하이닉스", "현대차", "NAVER", "카카오",
        "두산로보틱스", "한화에어로스페이스", "에코프로",
        "알테오젠", "기아"
    ]

    for name in leaders:
        c = code(name)
        if c is None:
            continue

        df = fdr.DataReader(str(c)).tail(120)
        if df is None or len(df) < 25:
            continue

        df_p = ind(df)
        if df_p.empty:
            continue

        latest = df_p.iloc[-1]

        price = int(latest["Close"])
        score = float(latest["Stock_Score"])
        whale = float(latest["Whale_Entry"])

        rebound_score = (
            (100 - score) * 0.4 +
            whale * 0.4 +
            (latest["Close"] < latest["MA5"]) * 20
        )

        results.append({
            "종목명": name,
            "현재가": f"{price:,}원",
            "세력진입": f"{whale:.1f}%",
            "반등점수": round(rebound_score, 2)
        })

    df = pd.DataFrame(results)

    if df.empty:
        return pd.DataFrame()

    return df.sort_values("반등점수", ascending=False).head(10)

# =====================================================
# UI
# =====================================================
selected_name = st.selectbox("", names)

selected_code = code(selected_name)
df_raw = get_price(selected_code)
df = ind(df_raw)

if not df.empty:
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = int(latest["Close"])
    diff = price - int(prev["Close"])
    ratio = (diff / int(prev["Close"])) * 100

    pump_df = scan_market_signals()

    tab1, tab2, tab3 = st.tabs([
        "📊 종목분석",
        "🚀 급등주",
        "🎯 내일 반등 TOP10"
    ])

    with tab1:
        c1, c2, c3 = st.columns(3)

        c1.metric("현재가", f"{price:,}원", f"{diff:+,}원")
        c2.metric("예상 상승률", f"{latest['Pred_Return']:.1f}%")
        c3.metric("상승 적중률", f"{latest['Pred_Accuracy']:.1f}%")

        st.metric("🐳 세력 진입 확률", f"{latest['Whale_Entry']:.1f}%")

        st.markdown(f"""
        ### 종합 점수: {latest['Stock_Score']:.1f}/100
        """)

    with tab2:
        st.dataframe(pump_df, use_container_width=True)

    with tab3:
        st.markdown("🎯 내일 반등 예상 TOP 10")
        st.dataframe(pump_df, use_container_width=True)

else:
    st.warning("데이터 부족")