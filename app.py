import streamlit as st
import pandas as pd
import FinanceDataReader as fdr  # ◀ 패키지 추가
import os

# =====================================================
# 1. 데이터 로딩 (안전한 경로 처리)
# =====================================================
current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
file_path = os.path.join(current_dir, "stock_list.csv")

try:
    df_stock = pd.read_csv(file_path)
except FileNotFoundError:
    st.error(f"⚠️ '{file_path}' 파일을 찾을 수 없습니다. 깃허브 업로드 및 경로를 확인해주세요.")
    st.stop()

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
    return str(row.iloc[0]["Code"]).zfill(6) # ◀ 6자리 자릿수 맞춤 (예: 005930)


# =====================================================
# 4. 가격 데이터 가져오기 (FinanceDataReader 연동)
# =====================================================
def get_price(code, period_days=500):
    """
    FinanceDataReader를 사용해 주가 데이터를 가져옵니다.
    지표 계산(MA, RSI)을 위해 사용자가 조회할 기간보다 넉넉하게 데이터를 가져옵니다.
    """
    # 현재 날짜 기준 과거 데이터를 넉넉히 가져옴
    end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
    start_date = (pd.Timestamp.now() - pd.Timedelta(days=period_days)).strftime('%Y-%m-%d')
    
    df = fdr.DataReader(code, start_date, end_date)
    return df


# =====================================================
# 5. 기술지표 계산 (RSI 및 이동평균선 추가)
# =====================================================
@st.cache_data(ttl=10)
def ind(df):
    if df.empty or len(df) < 20: # 최소 이동평균을 위한 데이터 개수 확인
        return df
        
    df = df.copy()

    # ◀ 이동평균선(MA) 계산 코드 추가 (10번, 11번 UI 에러 방지)
    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA20"] = df["Close"].rolling(window=20).mean()

    # RSI 계산
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

# 가격 데이터 로딩 (조회 기간 슬라이더 값보다 조금 더 여유있게 가져옵니다)
try:
    raw_df = get_price(selected_code, period_days=period + 100)
except Exception as e:
    st.error(f"데이터 로딩 실패: {e}")
    st.stop()

df_processed = ind(raw_df)

# MA20과 RSI 계산을 위해 최소 20개 이상의 데이터가 유효해야 함
if df_processed.empty or len(df_processed) < 20:
    st.warning("데이터가 부족합니다 (계산을 위해 최소 20개 이상의 거래일 필요)")
    st.stop()


# =====================================================
# 8. 최신 데이터 추출
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
# 10. 이동평균 (에러 방지를 위해 결측치 처리 추가)
# =====================================================
col3, col4 = st.columns(2)

with col3:
    ma5_val = f"{int(latest['MA5']):,} 원" if pd.notna(latest['MA5']) else "계산중"
    st.metric("MA5", ma5_val)

with col4:
    ma20_val = f"{int(latest['MA20']):,} 원" if pd.notna(latest['MA20']) else "계산중"
    st.metric("MA20", ma20_val)


st.markdown("---")


# =====================================================
# 11. 차트
# =====================================================
df_visual = df_processed.tail(period)

st.subheader(f"📈 {selected_name} ({selected_code})")

st.line_chart(df_visual[["Close", "MA5", "MA20"]])
st.bar_chart(df_visual["Volume"])
st.line_chart(df_visual["RSI"])
