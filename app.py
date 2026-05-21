import streamlit as st
import pandas as pd

# =====================================================
# 종목 코드 찾기
# =====================================================
def code(name):
    row = df_stock[df_stock["Name"] == name]
    if row.empty:
        return None
    return row.iloc[0]["Code"]


# =====================================================
# RSI 계산
# =====================================================
@st.cache_data(ttl=10)
def ind(df):
    delta = df["Close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df


# =====================================================
# 사이드바 UI
# =====================================================
with st.sidebar:
    st.header("🔍 종목 및 기간 설정")

    index = names.index("삼성전자") if "삼성전자" in names else 0
    selected_name = st.selectbox("종목 선택", names, index=index)

    period = st.slider("조회 기간", 30, 500, 120)


# =====================================================
# 데이터 로딩
# =====================================================
selected_code = code(selected_name)

if selected_code is None:
    st.error("종목 코드를 찾을 수 없습니다.")
    st.stop()

raw_df = get_price(selected_code)
df_processed = ind(raw_df)


# 데이터 부족 방지
if df_processed is None or df_processed.empty or len(df_processed) < 2:
    st.warning("데이터가 부족합니다 (최소 2개 이상 필요)")
    st.stop()


# =====================================================
# 최신 데이터
# =====================================================
latest = df_processed.iloc[-1]
prev = df_processed.iloc[-2]

current_price = int(latest["Close"])
prev_price = int(prev["Close"])

diff = current_price - prev_price
ratio = (diff / prev_price) * 100


# =====================================================
# 상단 메트릭
# =====================================================
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "현재가",
        f"{current_price:,} 원",
        f"{diff:,} 원 ({ratio:.2f}%)"
    )

with col2:
    rsi_val = latest["RSI"]
    rsi_val = float(rsi_val) if pd.notna(rsi_val) else 0

    if rsi_val >= 70:
        rsi_status = "🔴 과매수"
    elif rsi_val <= 30:
        rsi_status = "🔵 과매도"
    else:
        rsi_status = "🟢 보통"

    st.metric("RSI(14)", f"{rsi_val:.2f}", rsi_status)


# =====================================================
# 이동평균
# =====================================================
col3, col4 = st.columns(2)

with col3:
    st.metric("적정매수가(MA5)", f"{int(latest['MA5']):,} 원")

with col4:
    st.metric("단기목표(MA20)", f"{int(latest['MA20']):,} 원")


st.markdown("---")


# =====================================================
# 차트
# =====================================================
df_visual = df_processed.tail(period)

st.subheader(f"📈 {selected_name} ({selected_code})")

st.line_chart(df_visual[["Close", "MA5", "MA20"]])

st.subheader("📊 거래량")
st.bar_chart(df_visual["Volume"])

st.subheader("⏱️ RSI")
st.line_chart(df_visual["RSI"])