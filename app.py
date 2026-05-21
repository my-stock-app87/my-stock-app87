import streamlit as st
import pandas as pd

# =====================================================
# (필수) 데이터가 이미 있다고 가정
# df_stock, get_price 는 위에서 정의되어 있어야 함
# =====================================================

# ✅ 종목 리스트 생성 (이게 없어서 에러 발생한 것)
names = df_stock["Name"].dropna().unique().tolist()


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
# 사이드바
# =====================================================
with st.sidebar:
    st.header("🔍 종목 및 기간 설정")

    index = names.index("삼성전자") if "삼성전자" in names else 0
    selected_name = st.selectbox("종목 선택", names, index=index)

    period = st.slider("조회 기간", 30, 500, 120)


# =====================================================
# 데이터 처리
# =====================================================
selected_code = code(selected_name)

if selected_code is None:
    st.error("종목 코드 없음")
    st.stop()

raw_df = get_price(selected_code)
df_processed = ind(raw_df)

if df_processed is None or df_processed.empty:
    st.warning("데이터 없음")
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
# UI
# =====================================================
col1, col2 = st.columns(2)

with col1:
    st.metric("현재가", f"{current_price:,}", f"{diff:,} ({ratio:.2f}%)")

with col2:
    rsi_val = float(latest["RSI"]) if pd.notna(latest["RSI"]) else 0
    status = "🔴 과매수" if rsi_val >= 70 else "🔵 과매도" if rsi_val <= 30 else "🟢 보통"
    st.metric("RSI", f"{rsi_val:.2f}", status)


st.markdown("---")

df_visual = df_processed.tail(period)

st.line_chart(df_visual[["Close", "MA5", "MA20"]])
st.bar_chart(df_visual["Volume"])
st.line_chart(df_visual["RSI"])