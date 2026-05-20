import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from datetime import datetime
import FinanceDataReader as fdr

# -------------------------------------------------
# 기본 설정
# -------------------------------------------------
st.set_page_config(
    page_title="👑 주식 AI 통합 분석기",
    page_icon="👑",
    layout="wide"
)

st.title("👑 주식 AI 통합 분석기")
st.caption("전체 한국 주식 실시간 AI 분석 시스템")

# -------------------------------------------------
# 전체 종목 리스트
# -------------------------------------------------
@st.cache_data(ttl=3600)
def load_stock_list():

    krx = fdr.StockListing('KRX')

    return krx[['Code', 'Name']]

stock_df = load_stock_list()

stock_names = stock_df['Name'].tolist()

# -------------------------------------------------
# 종목 코드 찾기
# -------------------------------------------------
def get_code(name):

    row = stock_df[
        stock_df['Name'] == name
    ]

    if not row.empty:
        return row.iloc[0]['Code']

    return None

# -------------------------------------------------
# 주가 데이터
# -------------------------------------------------
@st.cache_data(ttl=300)
def load_price(code):

    try:
        df = fdr.DataReader(code)

        if df.empty:
            return pd.DataFrame()

        df = df.tail(120).reset_index()

        return df

    except:
        return pd.DataFrame()

# -------------------------------------------------
# 보조지표
# -------------------------------------------------
def add_indicator(df):

    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()

    df['Vol20'] = df['Volume'].rolling(20).mean()

    # RSI
    delta = df['Close'].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / (avg_loss + 1e-9)

    df['RSI'] = 100 - (100 / (1 + rs))

    return df.dropna()

# -------------------------------------------------
# 세력 탐지
# -------------------------------------------------
def detect_signal(df):

    latest = df.iloc[-1]

    volume_burst = (
        latest['Volume'] > latest['Vol20'] * 2
    )

    ma_break = latest['Close'] > latest['MA5']

    bullish = latest['Close'] > latest['Open']

    if volume_burst and ma_break and bullish:
        return "🚨 세력 매집 강력 의심"

    elif volume_burst:
        return "🔥 거래량 급등 포착"

    elif latest['RSI'] < 30:
        return "📉 과매도 구간"

    else:
        return "💤 일반 흐름"

# -------------------------------------------------
# 세션
# -------------------------------------------------
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = []

# -------------------------------------------------
# 탭
# -------------------------------------------------
tab0, tab1, tab2, tab3 = st.tabs([
    "💰 내 보유주식",
    "🔍 상세분석",
    "⚖️ 닮은꼴 분석",
    "🔮 AI 추천주"
])

# =================================================
# TAB 0
# =================================================
with tab0:

    st.subheader("💰 내 보유주식")

    with st.expander("➕ 보유주식 추가"):

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

    # 출력
    if len(st.session_state['portfolio']) == 0:

        st.info("등록된 종목 없음")

    else:

        total = 0

        for idx, item in enumerate(
            st.session_state['portfolio']
        ):

            code = get_code(item['name'])

            df = load_price(code)

            if df.empty:
                continue

            df = add_indicator(df)

            latest = df.iloc[-1]

            now_price = latest['Close']

            eval_price = now_price * item['qty']

            buy_total = item['buy'] * item['qty']

            profit = eval_price - buy_total

            rate = (
                profit / (buy_total + 1e-9)
            ) * 100

            total += eval_price

            st.markdown("---")

            st.markdown(
                f"### 📦 {item['name']}"
            )

            a, b, c, d = st.columns(4)

            a.metric(
                "현재가",
                f"{now_price:,.0f}원"
            )

            b.metric(
                "평가금액",
                f"{eval_price:,.0f}원"
            )

            c.metric(
                "수익률",
                f"{rate:.2f}%"
            )

            d.write(
                detect_signal(df)
            )

            if st.button(
                f"삭제 {idx}"
            ):
                st.session_state['portfolio'].pop(idx)
                st.rerun()

        st.success(
            f"💵 총 평가자산: {total:,.0f}원"
        )

# =================================================
# TAB 1
# =================================================
with tab1:

    st.subheader("🔍 1종목 상세분석")

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

            st.write(
                detect_signal(df)
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

# =================================================
# TAB 3
# =================================================
with tab3:

    st.subheader("🔮 AI 추천 급등주")

    now = datetime.now()

    st.info(
        f"현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    if st.button("🔮 AI 추천 시작"):

        result = []

        sample = stock_df.sample(200)

        progress = st.progress(0)

        for idx, row in enumerate(
            sample.iterrows()
        ):

            try:

                code = row[1]['Code']
                name = row[1]['Name']

                df = load_price(code)

                if len(df) < 30:
                    continue

                df = add_indicator(df)

                latest = df.iloc[-1]

                score = 0

                # 거래량 폭발
                if latest['Volume'] > (
                    latest['Vol20'] * 3
                ):
                    score += 40

                # 5일선 돌파
                if latest['Close'] > latest['MA5']:
                    score += 20

                # 정배열
                if latest['MA5'] > latest['MA20']:
                    score += 20

                # RSI
                if 40 < latest['RSI'] < 70:
                    score += 20

                if score >= 70:

                    result.append({
                        "종목": name,
                        "현재가": int(latest['Close']),
                        "AI점수": score,
                        "RSI": round(
                            latest['RSI'], 1
                        )
                    })

            except:
                continue

            progress.progress(
                (idx + 1) / 200
            )

        if len(result) == 0:

            st.warning("추천 종목 없음")

        else:

            result_df = pd.DataFrame(result)

            result_df = result_df.sort_values(
                by='AI점수',
                ascending=False
            )

            st.success(
                "🎯 AI 추천 완료"
            )

            st.dataframe(
                result_df.head(20)
            )