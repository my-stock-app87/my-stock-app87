import streamlit as st
import pandas as pd

# =====================================================
# 1. 데이터 로딩 (무조건 최상단)
# =====================================================
# ⚠️ 파일명은 본인 환경에 맞게 수정
df_stock = pd.read_csv("stock_list.csv")

# =====================================================
# 2. 종목 리스트 생성
# =====================================================
names = df_stock["Name"].dropna().unique().tolist()


# =====================================================
# 3. 종목 코드 찾기 함수
# =====================================================
def code(name):
    row = df_stock[df_stock["Name"] == name]
    if row.empty:
        return None
    return row.iloc[0]["Code"]


# =====================================================
# 4. 가격 데이터 가져오기 (이미 있다고 가정)
# =====================================================
def get_price(code):
    """
    ⚠️ 여기 함수는 너 기존 코드 그대로 사용해야 함
    (API / yfinance / DB 등)
    """
    raise NotImplementedError("get_price()를 구현하세요")


# =====================================================
# 5. RSI 계산
# =====================================================
@st.cache_data(ttl=10)
def ind(df):
    df = df.copy()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df


# =====================================================
# 6. UI (사이드바)
# =====================================================
with st.sidebar:
    st.header("🔍 종목 설정")

    index = names.index("삼성전자") if "삼성전자" in names else 0
    selected_name = st.selectbox("종목 선택", names, index=index)

    period = st.slider("조회 기간", 30, 500, 120)


# =====================================================
# 7. 데이터 처리
# =====================================================
selected_code = code(selected_name)

if selected_code is None:
    st.error("종목 코드를 찾을 수 없습니다.")
    st.stop()

# ⚠️ 가격 데이터 로딩
try:
    raw_df = get_price(selected_code)
except Exception as e:
    st.error(f"데이터 로딩 실패: {e}")
    st.stop()

df_processed = ind(raw_df)

if df_processed.empty or len(df_processed) < 2:
    st.warning("데이터가 부족합니다 (최소 2개 이상 필요)")
    st.stop()


# =====================================================
# 8. 최신 데이터
# =====================================================
latest = df_processed.iloc[-1]
prev = df_processed.iloc[-2]

current_price = int(latest["Close"])
prev_price = int(prev["Close"])

diff = current_price - prev_price
ratio = (diff / prev_price) * 100


# =====================================================
# 9. UI 메트릭
# =====================================================
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "현재가",
        f"{current_price:,} 원",
        f"{diff:,} ({ratio:.2f}%)"
    )

with col2:
    rsi_val = float(latest["RSI"]) if pd.notna(latest["RSI"]) else 0

    if rsi_val >= 70:
        status = "🔴 과매수"
    elif rsi_val <= 30:
        status = "🔵 과매도"
    else:
        status = "🟢 보통"

    st.metric("RSI (14)", f"{rsi_val:.2f}", status)


# =====================================================
# 10. 이동평균
# =====================================================
col3, col4 = st.columns(2)

with col3:
    st.metric("MA5", f"{int(latest['MA5']):,} 원")

with col4:
    st.metric("MA20", f"{int(latest['MA20']):,} 원")


st.markdown("---")


# =====================================================
# 11. 차트
# =====================================================
df_visual = df_processed.tail(period)

st.subheader(f"📈 {selected_name} ({selected_code})")

st.line_chart(df_visual[["Close", "MA5", "MA20"]])
st.bar_chart(df_visual["Volume"])
st.line_chart(df_visual["RSI"])