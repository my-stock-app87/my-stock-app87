import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from streamlit_autorefresh import st_autorefresh

# =====================================================
# 설정 (레이아웃을 wide로 변경하여 대시보드 시각화 최적화)
# =====================================================
st.set_page_config(page_title="AI STOCK MASTER PRO", layout="wide")
st.title("🔥 AI STOCK MASTER PRO")

# 🔥 5초마다 자동 새로고침 활성화 (메트릭과 데이터 실시간 반영)
st_autorefresh(interval=5000, key="global_refresh")

# =====================================================
# 데이터 로드 및 최적화 캐싱
# =====================================================
@st.cache_data(ttl=3600)
def stock_list():
    try:
        df = fdr.StockListing("KRX")[["Code", "Name"]]
        return df.dropna().drop_duplicates(subset=["Name"])
    except:
        return pd.DataFrame({"Code": ["005930", "000660"], "Name": ["삼성전자", "SK하이닉스"]})

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    row = df_stock[df_stock["Name"] == name]
    if row.empty:
        return None
    # 🔴 수정 완료: 문자열 인덱서 오류를 방지하고 정확히 첫 번째 행의 Code를 가져옵니다.
    return row.iloc[0]["Code"]

@st.cache_data(ttl=10)
def get_price(c):
    try:
        if not c:
            return pd.DataFrame()
        df = fdr.DataReader(c)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except:
        return pd.DataFrame()

# =====================================================
# 지표 및 가격 가이드 연산공학
# =====================================================
def ind(df):
    if df is None or df.empty or len(df) < 25:
        return pd.DataFrame()

    df = df.copy()
    # 이동평균선 및 거래량 평형선
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    # RSI 지표 최적화 연산
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    # 변동성 채널(볼린저 밴드) 기반 명확한 가격 가이드 분리
    std20 = df["Close"].rolling(20).std()
    
    # 🟢 적정 매수가: 중심선에서 -1.5 표준편차 차감 (주가보다 항상 낮은 저점 가이드)
    df["Target_Buy"] = df["MA20"] - (std20 * 1.5)
    
    # 🔴 단기 목표 매도가: 중심선에서 +1.5 표준편차 가산 (주가보다 항상 높은 고점 가이드)
    df["Target_Sell"] = df["MA20"] + (std20 * 1.5)
    
    return df

# =====================================================
# UI 레이아웃 및 대시보드 시각화
# =====================================================
with st.sidebar:
    st.header("🔍 종목 및 기간 설정")
    selected_name = st.selectbox("분석할 종목을 선택하세요", names, index=names.index("삼성전자") if "삼성전자" in names else 0)
    period = st.slider("조회 기간 (거래일 기준)", min_value=30, max_value=500, value=120)

selected_code = code(selected_name)
raw_df = get_price(selected_code)
df_processed = ind(raw_df)

if not df_processed.empty:
    latest = df_processed.iloc[-1]
    prev = df_processed.iloc[-2]
    
    current_price = int(latest["Close"])
    prev_price = int(prev["Close"])
    price_diff = current_price - prev_price
    price_ratio = (price_diff / prev_price) * 100
    
    # 가이드 가격 데이터 정형화 (결측치 예외 처리 포함)
    target_buy_price = int(latest["Target_Buy"]) if not pd.isna(latest["Target_Buy"]) else current_price
    target_sell_price = int(latest["Target_Sell"]) if not pd.isna(latest["Target_Sell"]) else current_price
    
    # 1. 상단 핵심 실시간 메트릭 화면 설계
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("현재가", f"{current_price:,} 원", f"{price_diff:,} 원 ({price_ratio:.2f}%)")
    with col2:
        # 매수가까지 남은 하락폭 또는 괴리율 계산
        buy_gap = ((target_buy_price - current_price) / current_price) * 100
        st.metric("🟢 AI 추천 적정 매수가", f"{target_buy_price:,} 원", f"괴리율: {buy_gap:.1f}%", delta_color="inverse")
    with col3:
        # 목표 매도가까지 도달 시 기대할 수 있는 상승여력 계산
        sell_gap = ((target_sell_price - current_price) / current_price) * 100
        st.metric("🔴 단기 목표 매도가", f"{target_sell_price:,} 원", f"상승여력: +{sell_gap:.1f}%")
    with col4:
        rsi_val = latest["RSI"]
        rsi_status = "❌ 과매수 (분할매도)" if rsi_val >= 70 else "✨ 과매도 (분할매수)" if rsi_val <= 30 else "🟢 보통"
        st.metric("RSI (14)", f"{rsi_val:.2f}", rsi_status)

    st.markdown("---")

    # 기간 필터링 적용하여 차트 시각화
    df_visual = df_processed.tail(period)

    # 2. 메인 차트 영역 (주가 및 가격 가이드 라인)
    st.subheader(f"📈 {selected_name} ({selected_code}) 가격 가이드 및 주가 추이")
    chart_data = df_visual[["Close", "Target_Buy", "Target_Sell", "MA20"]]
    st.line_chart(chart_data)

    # 3. 서브 차트 영역 (거래량 및 RSI)
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        st.subheader("📊 거래량 변동")
        st.bar_chart(df_visual["Volume"])
    with sub_col2:
        st.subheader("⏱️ RSI 지표 추이")
        st.line_chart(df_visual["RSI"])

else:
    st.warning("⚠️ 데이터를 불러오지 못했거나 지표를 계산하기 위한 데이터량이 부족합니다. (최소 25거래일 이상 필요)")
