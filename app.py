```python id="f0x8s2"
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from datetime import datetime
import FinanceDataReader as fdr

# =================================================
# 기본 설정
# =================================================
st.set_page_config(
    page_title="👑 AI 주식 마스터",
    page_icon="👑",
    layout="wide"
)

st.title("👑 AI 주식 마스터")
st.caption("실시간 한국 전체 주식 AI 분석 시스템")

# =================================================
# 전체 종목 로딩
# =================================================
@st.cache_data(ttl=3600)
def load_stock_list():

    krx = fdr.StockListing('KRX')

    return krx[['Code', 'Name']]

stock_df = load_stock_list()

stock_names = stock_df['Name'].tolist()

# =================================================
# 종목 코드 찾기
# =================================================
def get_code(name):

    row = stock_df[
        stock_df['Name'] == name
    ]

    if not row.empty:
        return row.iloc[0]['Code']

    return None

# =================================================
# 가격 데이터
# =================================================
@st.cache_data(ttl=300)
def load_price(code):

    try:

        df = fdr.DataReader(code)

        if df.empty:
            return pd.DataFrame()

        df = df.tail(180).reset_index()

        return df

    except:

        return pd.DataFrame()

# =================================================
# 보조지표
# =================================================
def add_indicator(df):

    # 이동평균
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()

    # 거래량 평균
    df['Vol20'] = df['Volume'].rolling(20).mean()

    # RSI
    delta = df['Close'].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / (avg_loss + 1e-9)

    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()

    df['MACD'] = ema12 - ema26
    df['MACD_SIGNAL'] = df['MACD'].ewm(span=9).mean()

    # 볼린저밴드
    df['STD'] = df['Close'].rolling(20).std()

    df['Upper'] = (
        df['MA20']
        + (df['STD'] * 2)
    )

    df['Lower'] = (
        df['MA20']
        - (df['STD'] * 2)
    )

    return df.dropna()

# =================================================
# 세력 확률
# =================================================
def power_probability(df):

    latest = df.iloc[-1]

    score = 0

    if latest['Volume'] > latest['Vol20'] * 2:
        score += 35

    if latest['Close'] > latest['Open'] * 1.03:
        score += 20

    if latest['Close'] > latest['MA5']:
        score += 20

    if latest['MACD'] > latest['MACD_SIGNAL']:
        score += 15

    if 45 <= latest['RSI'] <= 70:
        score += 10

    return min(score, 100)

# =================================================
# AI 종합 점수
# =================================================
def ai_score(df):

    latest = df.iloc[-1]

    score = 0

    if latest['Volume'] > latest['Vol20'] * 2:
        score += 25

    if latest['MA5'] > latest['MA20']:
        score += 20

    if latest['MACD'] > latest['MACD_SIGNAL']:
        score += 20

    if latest['Close'] > latest['Open']:
        score += 15

    if 40 <= latest['RSI'] <= 70:
        score += 20

    return min(score, 100)

# =================================================
# 목표가
# =================================================
def target_price(df):

    latest = df.iloc[-1]

    return int(latest['Close'] * 1.08)

# =================================================
# 손절라인
# =================================================
def stop_loss(df):

    latest = df.iloc[-1]

    return int(latest['MA20'] * 0.97)

# =================================================
# 리스크
# =================================================
def risk_level(df):

    latest = df.iloc[-1]

    if latest['RSI'] > 80:
        return "🚨 매우 위험"

    elif latest['RSI'] > 70:
        return "⚠️ 단기 과열"

    else:
        return "🟢 정상 흐름"

# =================================================
# MACD 분석
# =================================================
def macd_signal(df):

    latest = df.iloc[-1]

    if latest['MACD'] > latest['MACD_SIGNAL']:

        return "🟢 MACD 골든크로스"

    return "🔴 MACD 하락 흐름"

# =================================================
# 볼린저 분석
# =================================================
def bollinger_signal(df):

    latest = df.iloc[-1]

    if latest['Close'] > latest['Upper']:

        return "🔥 과열 가능성"

    elif latest['Close'] < latest['Lower']:

        return "🟢 저점 반등 가능성"

    return "📊 정상 밴드 흐름"

# =================================================
# AI 브리핑
# =================================================
def ai_briefing(df):

    latest = df.iloc[-1]

    score = ai_score(df)

    text = []

    if score >= 80:

        text.append(
            "🔥 강한 상승 흐름."
        )

    elif score >= 60:

        text.append(
            "📈 상승 우세 흐름."
        )

    else:

        text.append(
            "📉 보수적 접근 필요."
        )

    if latest['RSI'] > 70:

        text.append(
            "⚠️ 단기 과열."
        )

    elif latest['RSI'] < 30:

        text.append(
            "🟢 과매도 반등 가능."
        )

    return " ".join(text)

# =================================================
# 매수 타이밍
# =================================================
def buy_timing(df):

    latest = df.iloc[-1]

    if (
        latest['Close'] > latest['MA5']
        and latest['MACD'] > latest['MACD_SIGNAL']
    ):

        return "🟢 눌림목 매수 가능"

    elif latest['RSI'] < 30:

        return "🔥 과매도 반등 매수 가능"

    return "⚠️ 관망 추천"

# =================================================
# 매도 타이밍
# =================================================
def sell_timing(df):

    latest = df.iloc[-1]

    if latest['RSI'] > 75:

        return "🔥 과열권 분할매도 추천"

    elif latest['Close'] < latest['MA5']:

        return "⚠️ 단기 이탈 주의"

    return "✅ 홀딩 가능"

# =================================================
# 물타기
# =================================================
def water_timing(df):

    latest = df.iloc[-1]

    if latest['RSI'] < 35:

        return "🟢 분할 물타기 가능"

    elif latest['Close'] > latest['MA20']:

        return "❌ 고점 물타기 위험"

    return "🟡 애매한 위치"

# =================================================
# 닮은꼴 설명
# =================================================
def similarity_comment(sim):

    if sim >= 80:

        return (
            "🔥 매우 유사한 흐름."
            " 같은 테마 수급 가능성."
        )

    elif sim >= 60:

        return (
            "📈 비슷한 흐름."
        )

    return (
        "📉 흐름 차이가 큼."
    )

# =================================================
# 세션
# =================================================
if 'portfolio' not in st.session_state:

    st.session_state['portfolio'] = []

# =================================================
# 탭
# =================================================
tab0, tab1, tab2 = st.tabs([
    "💰 내 보유주식",
    "🔍 상세분석",
    "⚖️ 닮은꼴 분석"
])

# =================================================
# TAB 0
# =================================================
with tab0:

    st.subheader("💰 내 보유주식")

    with st.expander("➕ 종목 추가"):

        c1, c2, c3 = st.columns(3)

        with c1:

            selected = st.selectbox(
                "종목 선택",
                stock_names
            )

        with c2:

            buy_price = st.number_input(
                "매수가",
                value=50000
            )

        with c3:

            qty = st.number_input(
                "수량",
                value=1
            )

        if st.button("📥 추가"):

            st.session_state['portfolio'].append({
                "name": selected,
                "buy": buy_price,
                "qty": qty
            })

            st.success("추가 완료")

    # 보유종목 출력
    if len(st.session_state['portfolio']) == 0:

        st.info("보유종목 없음")

    else:

        for idx, item in enumerate(
            st.session_state['portfolio']
        ):

            code = get_code(item['name'])

            df = load_price(code)

            if df.empty:
                continue

            df = add_indicator(df)

            latest = df.iloc[-1]

            current = latest['Close']

            rate = (
                (current - item['buy'])
                / item['buy']
            ) * 100

            st.markdown("---")

            st.markdown(
                f"## 📦 {item['name']}"
            )

            a, b, c = st.columns(3)

            a.metric(
                "현재가",
                f"{current:,.0f}원"
            )

            b.metric(
                "수익률",
                f"{rate:.2f}%"
            )

            c.metric(
                "AI 점수",
                f"{ai_score(df)}점"
            )

            st.success(
                f"🎯 목표가: {target_price(df):,}원"
            )

            st.error(
                f"🛑 손절가: {stop_loss(df):,}원"
            )

            st.info(
                f"🤖 매도 타이밍: {sell_timing(df)}"
            )

            st.warning(
                f"💧 물타기 타이밍: {water_timing(df)}"
            )

            st.write(
                ai_briefing(df)
            )

            if st.button(
                f"삭제 {idx}"
            ):
                st.session_state['portfolio'].pop(idx)
                st.rerun()

# =================================================
# TAB 1
# =================================================
with tab1:

    st.subheader("🔍 상세분석")

    stock_name = st.selectbox(
        "종목 선택",
        stock_names,
        key="detail"
    )

    if st.button("🔍 분석 시작"):

        code = get_code(stock_name)

        df = load_price(code)

        if df.empty:

            st.error("데이터 없음")

        else:

            df = add_indicator(df)

            latest = df.iloc[-1]

            st.metric(
                "현재가",
                f"{latest['Close']:,.0f}원"
            )

            st.metric(
                "🤖 AI 종합 점수",
                f"{ai_score(df)}점"
            )

            st.metric(
                "🚨 세력 개입 확률",
                f"{power_probability(df)}%"
            )

            st.success(
                f"🎯 목표가: {target_price(df):,}원"
            )

            st.error(
                f"🛑 손절가: {stop_loss(df):,}원"
            )

            st.warning(
                risk_level(df)
            )

            st.info(
                ai_briefing(df)
            )

            st.write(
                macd_signal(df)
            )

            st.write(
                bollinger_signal(df)
            )

            st.success(
                buy_timing(df)
            )

            st.line_chart(
                df.set_index('Date')[
                    ['Close', 'MA5', 'MA20']
                ]
            )

            st.dataframe(
                df.tail(20)
            )

# =================================================
# TAB 2
# =================================================
with tab2:

    st.subheader("⚖️ 닮은꼴 분석")

    c1, c2 = st.columns(2)

    with c1:

        stock_a = st.selectbox(
            "기준 종목",
            stock_names,
            key="A"
        )

    with c2:

        stock_b = st.selectbox(
            "비교 종목",
            stock_names,
            key="B"
        )

    if st.button("⚖️ 비교 시작"):

        code_a = get_code(stock_a)
        code_b = get_code(stock_b)

        df_a = load_price(code_a)
        df_b = load_price(code_b)

        if df_a.empty or df_b.empty:

            st.error("데이터 부족")

        else:

            df_a = df_a[['Date', 'Close']]
            df_b = df_b[['Date', 'Close']]

            merged = pd.merge(
                df_a,
                df_b,
                on='Date'
            )

            corr, _ = pearsonr(
                merged['Close_x'],
                merged['Close_y']
            )

            sim = (
                (corr + 1) / 2
            ) * 100

            st.metric(
                "유사도",
                f"{sim:.2f}%"
            )

            st.info(
                similarity_comment(sim)
            )

            merged['A'] = (
                merged['Close_x']
                / merged['Close_x'].iloc[0]
                - 1
            ) * 100

            merged['B'] = (
                merged['Close_y']
                / merged['Close_y'].iloc[0]
                - 1
            ) * 100

            st.line_chart(
                merged.set_index('Date')[
                    ['A', 'B']
                ]
            )
```
