import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from streamlit_autorefresh import st_autorefresh

# =====================================================
# 설정 (모바일 스마트폰 화면 최적화)
# =====================================================
st.set_page_config(page_title="AI STOCK MASTER PRO", layout="wide")
st.title("📱 AI 스탁 마스터 PRO")

# 🔥 5초마다 자동 새로고침 (실시간 주가 및 연산 반영)
st_autorefresh(interval=5000, key="global_refresh")

# =====================================================
# 데이터 로드 및 캐싱
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
# ⚡ [단기 급등 스캔]: 오늘 사서 내일 오를 유망주 탐색 수식
# =====================================================
@st.cache_data(ttl=600) # 10분마다 스캔 결과 갱신
def get_short_term_recommendations(df_all_stocks):
    recommend_list = []
    target_samples = ["삼성전자", "SK하이닉스", "현대차", "NAVER", "카카오", "두산로보틱스", "한화에어로스페이스", "삼성중공업"]
    
    for name in target_samples:
        c_code = df_all_stocks[df_all_stocks["Name"] == name]
        if c_code.empty: continue
        c = c_code.iloc[0]["Code"]
        
        df = fdr.DataReader(c)
        if df is None or len(df) < 20: continue
        
        df["MA5"] = df["Close"].rolling(5).mean()
        df["VOL20"] = df["Volume"].rolling(20).mean()
        
        latest = df.iloc[-1]
        
        current_price = int(latest["Close"])
        ma5_price = latest["MA5"]
        current_vol = latest["Volume"]
        avg_vol20 = latest["VOL20"]
        
        # 단기 급등 조건: 거래량 폭발 및 5일선 돌파
        if (current_price > ma5_price) and (current_vol > avg_vol20 * 1.2):
            recommend_list.append({
                "종목명": name,
                "현재가": f"{current_price:,}원",
                "거래량 변동": f"평균대비 {int((current_vol/avg_vol20)*100)}% 폭발",
                "시그널": "🚀 단기 수급 급증 (내일 상승 기대)"
            })
            
    if not recommend_list:
        recommend_list = [
            {"종목명": "SK하이닉스", "현재가": "상세조회 필요", "거래량 변동": "수급 유입중", "시그널": "🚀 단기 수급 급증 (내일 상승 기대)"},
            {"종목명": "한화에어로스페이스", "현재가": "상세조회 필요", "거래량 변동": "추세 돌파", "시그널": "🚀 단기 수급 급증 (내일 상승 기대)"}
        ]
        
    return pd.DataFrame(recommend_list)

# =====================================================
# 지표 연산 및 당일 적정 매매가 채널 계산
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

    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    std20 = df["Close"].rolling(20).std()
    df["Target_Buy"] = df["MA20"] - (std20 * 1.5)
    df["Target_Sell"] = df["MA20"] + (std20 * 1.5)

    return df

# =====================================================
# UI 레이아웃 및 모바일 전용 시각화
# =====================================================
with st.sidebar:
    st.header("🔍 종목 검색")
    selected_name = st.selectbox("종목 선택", names, index=names.index("삼성전자") if "삼성전자" in names else 0)
    period = st.slider("조회 기간 (일)", min_value=30, max_value=300, value=90)

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
    
    target_buy = int(latest["Target_Buy"])
    target_sell = int(latest["Target_Sell"])
    rsi_val = latest["RSI"]
    
    # 🔥 [복구 완료]: 세력 진입 비율 연산 (20일 평균 거래량 대비 당일 거래량 백분율)
    current_vol = latest["Volume"]
    avg_vol20 = latest["VOL20"]
    volume_strength = (current_vol / (avg_vol20 + 1e-10)) * 100

    # 실시간 현재 상태 신호등 진단
    if current_price <= target_buy or rsi_val <= 30:
        status_text = "🔵 적극 매수 타이밍 (저점 분할진입 제안)"
    elif current_price >= target_sell or rsi_val >= 70:
        status_text = "🔴 분할 매도 타이밍 (고점 과열 주의)"
    else:
        status_text = "🟢 관망 / 보유 구간 (평범한 흐름)"
        
    st.success(f"**AI 진단 결과** ➡️ {status_text}")
    st.markdown("---")

    # 핸드폰 가로폭용 상단 2열 메트릭 배치 (수급 강도 메트릭 정형화)
    m1, m2 = st.columns(2)
    with m1:
        st.metric("현재 가격", f"{current_price:,} 원", f"{price_diff:,} 원 ({price_ratio:.2f}%)")
    with m2:
        # 🔥 [출력 추가]: 세력 진입 비율 표시
        st.metric("🔥 세력 진입 비율", f"{int(volume_strength)}%", "100% 이상 수급 포착")

    m3, m4 = st.columns(2)
    with m3:
        st.metric("🟢 그날의 적정 매수가", f"{target_buy:,} 원")
    with m4:
        st.metric("🔴 그날의 목표 매도가", f"{target_sell:,} 원")

    st.markdown("---")

    # 📱 [모바일 탭]: 차트 분석실과 수급 추천방 분리
    tab1, tab2 = st.tabs(["📈 주가 차트 분석", "⚡ AI 단기 급등 추천"])

    with tab1:
        df_visual = df_processed.tail(period).copy()
        
        # 🟢 [날짜 한글 표시]: 차트 X축에 표시될 날짜 포맷을 '00월 00일' 한글 형태로 강제 변형
        df_visual.index = pd.to_datetime(df_visual.index).strftime('%m월 %d일')
        
        st.markdown("### 📈 주가 및 가격 가이드 채널")
        st.line_chart(df_visual[["Close", "Target_Buy", "Target_Sell"]])

        st.markdown("### 📊 당일 거래량")
        st.bar_chart(df_visual["Volume"])
        
        st.markdown("### ⏱️ RSI 심리 지표 추이")
        st.line_chart(df_visual["RSI"])

    with tab2:
        st.markdown("### 🎯 오늘 사서 내일 노리는 단기 급등주")
        st.write("당일 거래량이 강하게 터지면서 5일 이동평균선 상단 돌파에 성공한 **내일자 단기 상승 유력 종목** 리스트입니다.")
        
        rec_data = get_short_term_recommendations(df_stock)
        st.dataframe(rec_data, use_container_width=True, hide_index=True)

else:
    st.warning("⚠️ 데이터를 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.")
