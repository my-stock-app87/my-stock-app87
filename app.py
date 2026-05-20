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
    # 🟢 원본과 똑같이 0번째 행의 "Code" 컬럼을 가져오도록 원상복구했습니다.
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
