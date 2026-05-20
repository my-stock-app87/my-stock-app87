import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from datetime import datetime

# 설치 필요:
# pip install streamlit pykrx finance-datareader scipy

from pykrx import stock
import FinanceDataReader as fdr

# -------------------------------------------------
# 기본 설정
# -------------------------------------------------
st.set_page_config(
    page_title="👑 주식 AI 통합 예측기",
    page_icon="👑",
    layout="wide"
)

st.title("👑 나만의 주식 AI 통합 예측기")
st.caption("실시간 한국 전체 주식 분석 시스템")

# -------------------------------------------------
# 전체 종목 불러오기
# -------------------------------------------------
@st.cache_data(ttl=3600)
def get_all_stocks():

    kospi = stock.get_market_ticker_list(market="KOSPI")
    kosdaq = stock.get_market_ticker_list(market="KOSDAQ")

    all_tickers = kospi + kosdaq

    rows = []

    for ticker in all_tickers:
        try:
            rows.append({
                "code": ticker,
                "name": stock.get_market_ticker_name(ticker)
            })
        except:
            continue

    return pd.DataFrame(rows)

all_stock_df = get_all_stocks()

stock_names = all_stock_df['name'].tolist()

# -------------------------------------------------
# 종목 코드 찾기
# -------------------------------------------------
def get_stock_code(name):

    row = all_stock_df[
        all_stock_df['name'] == name
    ]

    if not row.empty:
        return row.iloc[0]['code']

    return None

# -------------------------------------------------
# 주가 데이터
# -------------------------------------------------
@st.cache_data(ttl=300)
def get_stock_df(code):

    try:
        df = fdr.DataReader(code)

        if df.empty:
            return pd.DataFrame()

        df = df.tail(120).reset_index()

        return df

    except:
        return pd.DataFrame()

# -------------------------------------------------
# 보조지표 계산
# -------------------------------------------------
def add_indicators(df):

    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()

    df['Vol_MA20'] = df['Volume'].rolling(20).mean()

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
def detect_power(df):

    latest = df.iloc[-1]

    volume_burst = latest['Volume'] > latest['Vol_MA20'] * 2

    strong_close = latest['Close'] > latest['Open']

    ma_break = latest['Close'] > latest['MA5']

    if volume_burst and strong_close and ma_break:
        return "🚨 세력 매집 강하게 의심됩니다."

    elif volume_burst:
        return "🔥 거래량 급증 포착."

    elif latest['RSI'] < 30:
        return "📉 과매도 구간 접근."

    else:
        return "💤 특별한 수급 이상 없음."

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
    "🔍 1종목 상세분석",
    "⚖️ 2종목 닮은꼴",
    "🔮 AI 급등주 추천"
])

# =================================================
# TAB 0
# =================================================
with tab0:

    st.subheader("💰 내 보유주식 관리")

    with st.expander("➕ 보유주식 추가"):

        c1, c2, c3 = st.columns(3)

        with c1:
            selected_stock = st.selectbox(
                "종목 선택",
                stock_names
            )

        with c2:
            buy_price = st.number_input(
                "매수가",
                value=50000
            )

        with c3:
            quantity = st.number_input(
                "수량",
                value=1
            )

        if st.button("📥 포트폴리오 추가"):

            st.session_state['portfolio'].append({
                "name": selected_stock,
                "buy_price": buy_price,
                "qty": quantity
            })

            st.success("추가 완료")

    # 보유 종목 출력
    if len(st.session_state['portfolio']) == 0:

        st.info("보유 종목이 없습니다.")

    else:

        total_asset = 0

        for idx, item in enumerate(st.session_state['portfolio']):

            code = get_stock_code(item['name'])

            df = get_stock_df(code)

            if df.empty:
                continue

            df = add_indicators(df)

            latest = df.iloc[-1]

            current_price = latest['Close']

            eval_amount = current_price * item['qty']

            buy_amount = item['buy_price'] * item['qty']

            profit = eval_amount - buy_amount

            profit_rate = (
                profit / (buy_amount + 1e-9)
            ) * 100

            total_asset += eval_amount

            st.markdown("---")

            st.markdown(
                f"### 📦 {item['name']}"
            )

            a, b, c, d = st.columns(4)

            a.metric(
                "현재가",
                f"{current_price:,.0f}원"
            )

            b.metric(
                "평가금액",
                f"{eval_amount:,.0f}원"
            )

            c.metric(
                "손익",
                f"{profit:,.0f}원",
                f"{profit_rate:.2f}%"
            )

            signal = detect_power(df)

            d.write(signal)

            if st.button(
                f"삭제 {item['name']}",
                key=idx
            ):
                st.session_state['portfolio'].pop(idx)
                st.rerun()

        st.success(
            f"💵 총 평가자산: {total_asset:,.0f}원"
        )

# =================================================
# TAB 1
# =================================================
with tab1:

    st.subheader("🔍 1종목 상세분석")

    selected = st.selectbox(
        "분석할 종목",
        stock_names,
        key="detail"
    )

    if st.button("🔍 분석 시작"):

        code = get_stock_code(selected)

        df = get_stock_df(code)

        if df.empty:

            st.error("데이터 없음")

        else:

            df = add_indicators(df)

            latest = df.iloc[-1]

            st.metric(
                "현재가",
                f"{latest['Close']:,.0f}원"
            )

            st.write(detect_power(df))

            st.line_chart(
                df.set_index('Date')[
                    ['Close', 'MA5', 'MA20']
                ]
            )

            st.dataframe(df.tail(20))

# =================================================
# TAB 2
# =================================================
with tab2:

    st.subheader("⚖️ 닮은꼴 시뮬레이터")

    c1, c2 = st.columns(2)

    with c1:
        stock_a = st.selectbox(
            "기준 종목",
            stock_names,
            key="a"
        )

    with c2:
        stock_b = st.selectbox(
            "비교 종목",
            stock_names,
            key="b"
        )

    if st.button("⚖️ 비교 시작"):

        code_a = get_stock_code(stock_a)
        code_b = get_stock_code(stock_b)

        df_a = get_stock_df(code_a)
        df_b = get_stock_df(code_b)

        if df_a.empty or df_b.empty:

            st.error("데이터 부족")

        else:

            df_a = df_a[['Date', 'Close']]
            df_b = df_b[['Date', 'Close']]

            merged = pd.merge(
                df_a,
                df_b,
                on='Date',
                suffixes=('_A', '_B')
            )

            corr, _ = pearsonr(
                merged['Close_A'],
                merged['Close_B']
            )

            similarity = (
                (corr + 1) / 2
            ) * 100

            st.metric(
                "차트 유사도",
                f"{similarity:.2f}%"
            )

            merged['A'] = (
                merged['Close_A']
                / merged['Close_A'].iloc[0]
                - 1
            ) * 100

            merged['B'] = (
                merged['Close_B']
                / merged['Close_B'].iloc[0]
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

    st.subheader("🔮 AI 급등주 추천")

    now = datetime.now()

    st.info(
        f"현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    if now.hour >= 12:
        st.success(
            "🔥 오후 12시 이후 AI 추천 활성화"
        )

    if st.button("🔮 AI 추천 시작"):

        result = []

        tickers = stock.get_market_ticker_list(
            market="ALL"
        )

        progress = st.progress(0)

        for idx, ticker in enumerate(tickers[:200]):

            try:

                df = get_stock_df(ticker)

                if len(df) < 30:
                    continue

                df = add_indicators(df)

                latest = df.iloc[-1]

                score = 0

                # 거래량 폭발
                if latest['Volume'] > (
                    latest['Vol_MA20'] * 3
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
                        "종목": stock.get_market_ticker_name(ticker),
                        "현재가": int(latest['Close']),
                        "AI점수": score,
                        "RSI": round(latest['RSI'], 1)
                    })

            except:
                continue

            progress.progress(
                (idx + 1) / 200
            )

        if len(result) == 0:

            st.warning(
                "조건 만족 종목 없음"
            )

        else:

            result_df = pd.DataFrame(result)

            result_df = result_df.sort_values(
                by='AI점수',
                ascending=False
            )

            st.success(
                "🎯 AI 추천 완료"
            )

            st.dataframe(result_df.head(20))