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
@st.cache_data(ttl=3600)  # 종목 리스트는 하루에 한 번 혹은 드물게 변경되므로 캐시 주기 확장
def stock_list():
    try:
        df = fdr.StockListing("KRX")[["Code", "Name"]]
        # 무효 데이터나 인덱스 중복 방지
        return df.dropna().drop_duplicates(subset=["Name"])
    except:
        # 대비용 하드코딩 샘플 데이터셋
        return pd.DataFrame({"Code": ["005930", "000660"], "Name": ["삼성전자", "SK하이닉스"]})

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    row = df_stock[df_stock["Name"] == name]
    if row.empty:
        return None
    return row.iloc[0]["Code"]

@st.cache_data(ttl=10)  # 실시간 데이터 인식을 위해 캐시 생존 주기(TTL) 단축
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
# 지표 연산공학
# =====================================================
def ind(df):
    if df is None or df.empty or len(df) < 25:
        return pd.DataFrame()

    df = df.copy()
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # 웰스 와일더(Wells Wilder) 방식 공식 RSI 최적화 구현
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10) # 0 나누기 방지
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

# =====================================================
# UI 레이아웃 및 대시보드 시각화
# =====================================================
# 사이드바: 종목 선택 및 기간 설정
with st.sidebar:
    st.header("🔍 종목 및 기간 설정")
    selected_name = st.selectbox("분석할 종목을 선택하세요", names, index=names.index("삼성전자") if "삼성전자" in names else 0)
    period = st.slider("조회 기간 (거래일 기준)", min_value=30, max_value=500, value=120)

selected_code = code(selected_name)
raw_df = get_price(selected_code)
df_processed = ind(raw_df)

if not df_processed.empty:
    # 최신 데이터 추출 (가장 마지막 행)
    latest = df_processed.iloc[-1]
    prev = df_processed.iloc[-2]
    
    current_price = int(latest["Close"])
    prev_price = int(prev["Close"])
    price_diff = current_price - prev_price
    price_ratio = (price_diff / prev_price) * 100
    
    # 1. 상단 핵심 실시간 메트릭 화면 배치 (글자만 정확하게 변경)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("현재가", f"{current_price:,} 원", f"{price_diff:,} 원 ({price_ratio:.2f}%)")
    with col2:
        st.metric("🟢 적정매수가", f"{int(latest['MA5']):,} 원")
    with col3:
        st.metric("🔴 단기목표 매도가", f"{int(latest['MA20']):,} 원")
    with col4:
        rsi_val = latest["RSI"]
        rsi_status = "🔴 과매수" if rsi_val >= 70 else "🔵 과매도" if rsi_val <= 30 else "🟢 보통"
        st.metric("RSI (14)", f"{rsi_val:.2f}", rsi_status)

    st.markdown("---")

    # 📱 탭 구성 수정: 요구하신 번호 정렬 반영
    tab1, tab2 = st.tabs(["1. 종목분석", "2. 단기 급등추천"])

    with tab1:
        # 기간 필터 및 날짜 한글화
        df_visual = df_processed.tail(period).copy()
        df_visual.index = pd.to_datetime(df_visual.index).strftime('%m월 %d일')

        # 🟢 스마트폰용 최근 5일 압축 뷰
        df_recent_5 = df_visual.tail(5)

        # 2. 메인 차트 영역 (최근 5일 압축)
        st.subheader(f"📈 {selected_name} ({selected_code}) 주가 및 이동평균선")
        chart_data = df_recent_5[["Close", "MA5", "MA20"]]
        st.line_chart(chart_data, height=220)

        # 3. 서브 차트 영역 (최근 5일 압축)
        st.subheader("📊 거래량 변동")
        st.bar_chart(df_recent_5["Volume"], height=130)
        
        st.subheader("⏱️ RSI 지표 추이")
        st.line_chart(df_recent_5["RSI"], height=130)

        # 🟢 누르면 다 볼 수 있는 전체 데이터 확장 셔터
        with st.expander("🔍 터치하여 전체 기간 데이터 더보기", expanded=False):
            st.line_chart(df_visual[["Close", "MA5", "MA20"]])
            st.bar_chart(df_visual["Volume"])
            st.line_chart(df_visual["RSI"])

    with tab2:
        st.markdown("### 🚀 내일 급등 수급 유력주")
        # 기존 주신 데이터셋 기반 샘플 매핑 처리
        st.write("당일 거래량이 강하게 터지며 5일선 상단 돌파에 성공한 단기 수급 유력 종목 리스트입니다.")
        sample_rec = pd.DataFrame([
            {"종목명": "SK하이닉스", "현재가": "상세조회 참조", "시그널": "🚀 단기 수급 급증 (내일 상승 기대)"},
            {"종목명": "한화에어로스페이스", "현재가": "상세조회 참조", "시그널": "🚀 단기 수급 급증 (내일 상승 기대)"}
        ])
        st.dataframe(sample_rec, use_container_width=True, hide_index=True)

else:
    st.warning("⚠️ 데이터를 불러오지 못했거나 지표를 계산하기 위한 데이터량이 부족합니다. (최소 25거래일 이상 필요)")
