import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr

# =====================================================
# 설정
# =====================================================
st.set_page_config(page_title="AI HTS MASTER", layout="wide")

st.title("🚀 AI HTS 주식 분석 시스템")
st.caption("전 종목 스캔 기반 AI 매매 분석")

# =====================================================
# 종목 리스트
# =====================================================
@st.cache_data
def load_stock_list():
    return fdr.StockListing('KRX')[['Code', 'Name']]

stock_df = load_stock_list()

# =====================================================
# 공통 지표
# =====================================================
def prepare(df):

    df = df.copy().reset_index()

    # ✅ 날짜 한글 변환 (핵심 수정)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df['Date_kr'] = df['Date'].dt.strftime('%Y년 %m월 %d일')

    close = df['Close']
    volume = df['Volume']

    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    vol20 = volume.rolling(20).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rsi = 100 - (100 / (1 + (
        gain.rolling(14).mean() /
        (loss.rolling(14).mean() + 1e-9)
    )))

    std = close.rolling(20).std()
    upper = ma20 + std * 2
    lower = ma20 - std * 2

    return {
        "df": df,
        "ma5": ma5,
        "ma20": ma20,
        "vol20": vol20,
        "rsi": rsi,
        "upper": upper,
        "lower": lower
    }

# =====================================================
# 급등 TOP 3
# =====================================================
def top_gap(stock_df):

    res = []

    for i in range(len(stock_df)):

        try:
            code = stock_df.iloc[i]['Code']
            name = stock_df.iloc[i]['Name']

            df = fdr.DataReader(code)

            if len(df) < 60:
                continue

            df = df.tail(80).reset_index()

            ind = prepare(df)
            d = ind["df"]
            latest = d.iloc[-1]

            score = 0

            if latest['Volume'] > ind["vol20"].iloc[-1] * 2:
                score += 30

            if ind["ma5"].iloc[-1] > ind["ma20"].iloc[-1]:
                score += 25

            if latest['Close'] > latest['Open']:
                score += 15

            if ind["rsi"].iloc[-1] < 70 and ind["rsi"].iloc[-1] > 40:
                score += 15

            if latest['Close'] > ind["ma20"].iloc[-1]:
                score += 15

            res.append({
                "종목": name,
                "점수": score,
                "가격": int(latest['Close'])
            })

        except:
            continue

    return sorted(res, key=lambda x: x["점수"], reverse=True)[:3]

# =====================================================
# 세력 매집
# =====================================================
def accumulation(stock_df):

    res = []

    for i in range(len(stock_df)):

        try:
            code = stock_df.iloc[i]['Code']
            name = stock_df.iloc[i]['Name']

            df = fdr.DataReader(code)

            if len(df) < 60:
                continue

            df = df.tail(80).reset_index()

            ind = prepare(df)
            d = ind["df"]
            latest = d.iloc[-1]

            score = 0

            if abs(ind["ma5"].iloc[-1] - ind["ma20"].iloc[-1]) / latest['Close'] < 0.02:
                score += 35

            if latest['Volume'] > ind["vol20"].iloc[-1]:
                score += 25

            if ind["rsi"].iloc[-1] < 60:
                score += 20

            res.append({
                "종목": name,
                "점수": score,
                "가격": int(latest['Close'])
            })

        except:
            continue

    return sorted(res, key=lambda x: x["점수"], reverse=True)[:3]

# =====================================================
# 상한가
# =====================================================
def limit_up(stock_df):

    res = []

    for i in range(len(stock_df)):

        try:
            code = stock_df.iloc[i]['Code']
            name = stock_df.iloc[i]['Name']

            df = fdr.DataReader(code)

            if len(df) < 60:
                continue

            df = df.tail(80).reset_index()

            ind = prepare(df)
            d = ind["df"]
            latest = d.iloc[-1]

            score = 0

            if latest['Volume'] > ind["vol20"].iloc[-1] * 3:
                score += 35

            if (latest['Close'] - latest['Open']) / latest['Open'] > 0.03:
                score += 25

            if ind["ma5"].iloc[-1] > ind["ma20"].iloc[-1]:
                score += 20

            if ind["rsi"].iloc[-1] > 60:
                score += 20

            res.append({
                "종목": name,
                "점수": score,
                "가격": int(latest['Close'])
            })

        except:
            continue

    return sorted(res, key=lambda x: x["점수"], reverse=True)[:3]

# =====================================================
# 반등 1종목
# =====================================================
def rebound(stock_df):

    best = None
    best_score = -999

    for i in range(len(stock_df)):

        try:
            code = stock_df.iloc[i]['Code']
            name = stock_df.iloc[i]['Name']

            df = fdr.DataReader(code)

            if len(df) < 60:
                continue

            df = df.tail(80).reset_index()

            ind = prepare(df)
            d = ind["df"]
            latest = d.iloc[-1]

            score = 0

            if d['Close'].iloc[-3] > latest['Close']:
                score += 30

            if ind["rsi"].iloc[-1] < 35:
                score += 30

            if latest['Volume'] > ind["vol20"].iloc[-1] * 2:
                score += 20

            if latest['Close'] < ind["lower"].iloc[-1]:
                score += 20

            if score > best_score:
                best_score = score
                best = {
                    "종목": name,
                    "점수": score,
                    "가격": int(latest['Close'])
                }

        except:
            continue

    return best

# =====================================================
# UI
# =====================================================
st.subheader("🚀 AI HTS 핵심 스캐너")

if st.button("🔥 급등 TOP 3"):
    st.table(pd.DataFrame(top_gap(stock_df)))

if st.button("🧠 세력 매집 TOP 3"):
    st.table(pd.DataFrame(accumulation(stock_df)))

if st.button("💥 상한가 TOP 3"):
    st.table(pd.DataFrame(limit_up(stock_df)))

if st.button("🚀 급락 후 반등 1종목"):
    st.success(rebound(stock_df))