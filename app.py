import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import FinanceDataReader as fdr

# =====================================================
# 기본 설정
# =====================================================
st.set_page_config(page_title="👑 AI 주식 마스터 PRO", layout="wide")

st.title("👑 AI 주식 마스터 PRO")
st.caption("전종목 AI 분석 + 급등/매집/반등/닮은꼴 통합 시스템")

# =====================================================
# 종목 리스트
# =====================================================
@st.cache_data(ttl=3600)
def load_stock_list():
    return fdr.StockListing('KRX')[['Code', 'Name']]

stock_df = load_stock_list()
stock_names = stock_df['Name'].tolist()

# =====================================================
# 코드 찾기
# =====================================================
def get_code(name):
    row = stock_df[stock_df['Name'] == name]
    return row.iloc[0]['Code'] if not row.empty else None

# =====================================================
# 가격 데이터 (안정화)
# =====================================================
@st.cache_data(ttl=300)
def load_price(code):
    try:
        df = fdr.DataReader(code)
        if df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        df = df.sort_values("Date")
        return df.tail(200)
    except:
        return pd.DataFrame()

# =====================================================
# 지표
# =====================================================
def add_indicator(df):

    df = df.copy()

    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['Vol20'] = df['Volume'].rolling(20).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()

    df['MACD'] = ema12 - ema26
    df['MACD_SIGNAL'] = df['MACD'].ewm(span=9).mean()

    return df.dropna().reset_index(drop=True)

# =====================================================
# AI 점수
# =====================================================
def ai_score(df):
    l = df.iloc[-1]
    score = 0

    if l['Volume'] > l['Vol20'] * 1.5:
        score += 25
    if l['MA5'] > l['MA20']:
        score += 20
    if l['MACD'] > l['MACD_SIGNAL']:
        score += 20
    if l['RSI'] < 70:
        score += 20
    if l['Close'] > l['Open']:
        score += 15

    return min(score, 100)

# =====================================================
# 세력 확률
# =====================================================
def power_probability(df):
    l = df.iloc[-1]
    score = 0

    if l['Volume'] > l['Vol20'] * 1.5:
        score += 30
    if l['Close'] > l['MA5']:
        score += 25
    if l['MACD'] > l['MACD_SIGNAL']:
        score += 25
    if l['RSI'] < 70:
        score += 20

    return min(score, 100)

# =====================================================
# 전략
# =====================================================
def buy_signal(df):
    l = df.iloc[-1]
    if l['RSI'] < 30:
        return "🔥 과매도 반등 가능"
    if l['MACD'] > l['MACD_SIGNAL']:
        return "🟢 눌림목 매수"
    return "⚠️ 관망"

def sell_signal(df):
    l = df.iloc[-1]
    if l['RSI'] > 75:
        return "🔥 과열 매도"
    if l['Close'] < l['MA5']:
        return "⚠️ 약세"
    return "✅ 홀딩"

def water_signal(df):
    l = df.iloc[-1]
    if l['RSI'] < 35:
        return "🟢 물타기 가능"
    return "⚠️ 신중"

# =====================================================
# 보유종목
# =====================================================
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = []

tab0, tab1, tab2, tab3 = st.tabs([
    "💰 보유주식",
    "🔍 상세분석",
    "⚖️ 닮은꼴",
    "🚀 AI 추천"
])

# =====================================================
# TAB 0
# =====================================================
with tab0:

    st.subheader("보유종목")

    with st.expander("추가"):

        sel = st.selectbox("종목", stock_names)
        buy = st.number_input("매수가", value=50000)
        qty = st.number_input("수량", value=1)

        if st.button("추가"):
            st.session_state['portfolio'].append({
                "name": sel,
                "buy": buy,
                "qty": qty
            })

    for i, item in enumerate(st.session_state['portfolio']):

        code = get_code(item['name'])
        df = load_price(code)

        if df.empty:
            continue

        df = add_indicator(df)
        l = df.iloc[-1]

        price = l['Close']
        rate = (price - item['buy']) / item['buy'] * 100

        st.markdown(f"## {item['name']}")
        st.metric("현재가", f"{price:,.0f}")
        st.metric("수익률", f"{rate:.2f}%")
        st.metric("AI 점수", ai_score(df))

        st.info(buy_signal(df))
        st.warning(sell_signal(df))
        st.success(water_signal(df))

# =====================================================
# TAB 1
# =====================================================
with tab1:

    name = st.selectbox("종목", stock_names)

    if st.button("분석"):

        df = load_price(get_code(name))

        if df.empty:
            st.error("데이터 없음")
        else:
            df = add_indicator(df)

            st.metric("AI 점수", ai_score(df))
            st.metric("세력확률", f"{power_probability(df)}%")

            st.line_chart(df.set_index("Date")[["Close"]])

# =====================================================
# TAB 2 (안정 닮은꼴)
# =====================================================
with tab2:

    a = st.selectbox("A", stock_names)
    b = st.selectbox("B", stock_names)

    if st.button("비교"):

        df_a = load_price(get_code(a))
        df_b = load_price(get_code(b))

        if df_a.empty or df_b.empty:
            st.error("데이터 부족")
        else:

            df_a = df_a[['Date', 'Close']].dropna()
            df_b = df_b[['Date', 'Close']].dropna()

            min_len = min(len(df_a), len(df_b))

            df_a = df_a.tail(min_len)
            df_b = df_b.tail(min_len)

            corr, _ = pearsonr(df_a['Close'], df_b['Close'])

            st.metric("유사도", f"{(corr+1)/2*100:.2f}%")

# =====================================================
# TAB 3 (AI 추천 TOP)
# =====================================================
with tab3:

    st.subheader("🚀 AI 추천 종목 TOP")

    if st.button("추천 실행"):

        results = []

        for name in stock_names[:100]:

            code = get_code(name)
            df = load_price(code)

            if df.empty:
                continue

            df = add_indicator(df)
            score = ai_score(df)

            results.append({
                "종목": name,
                "점수": score
            })

        df_r = pd.DataFrame(results)
        df_r = df_r.sort_values("점수", ascending=False).head(5)

        st.table(df_r)