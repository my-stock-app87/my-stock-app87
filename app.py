import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr

# =====================================================
# 설정
# =====================================================
st.set_page_config(page_title="AI STOCK MASTER", layout="wide")

today = "2026년 5월 21일"

st.title("🔥 AI STOCK MASTER PRO")
st.caption(f"실시간 트레이딩 분석 시스템 | {today}")

# =====================================================
# 데이터 로드
# =====================================================
@st.cache_data(ttl=300)
def stock_list():
    return fdr.StockListing("KRX")[["Code", "Name"]]

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    row = df_stock[df_stock["Name"] == name]
    return row.iloc[0]["Code"] if not row.empty else None

@st.cache_data(ttl=60)
def get_raw_price(c):
    return fdr.DataReader(c)

# =====================================================
# 지표 계산
# =====================================================
def ind(df):
    if len(df) < 20:
        return pd.DataFrame()

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["VOL20"] = df["Volume"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    return df.tail(120).reset_index()

# =====================================================
# 매수/매도/세력
# =====================================================
def buy_price(df):
    l = df.iloc[-1]

    if l["RSI"] < 30:
        return int(l["Close"] * 0.99), "과매도 반등"
    if l["Close"] > l["MA5"]:
        return int(l["Close"]), "상승 추세"
    return int(l["MA20"] * 1.01), "MA20 지지"

def sell_price(df):
    l = df.iloc[-1]
    return int(l["Close"] * 1.08)

def power(df):
    l = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else l

    s = 0

    if (l["Volume"] > l["VOL20"] * 2) and (l["Close"] > prev["Close"]):
        s += 40
    if l["Close"] > l["MA20"]:
        s += 25
    if l["RSI"] < 70:
        s += 20
    if l["Close"] > l["MA5"]:
        s += 15

    return min(s, 100)

# =====================================================
# 1주 고점/저점
# =====================================================
def week_high_low(df):
    last = df.tail(5)

    return {
        "1주 최고가": int(last["Close"].max()),
        "1주 최저가": int(last["Close"].min()),
        "변동폭(%)": round(
            (last["Close"].max() - last["Close"].min())
            / last["Close"].min() * 100, 2
        )
    }

# =====================================================
# AI 점수
# =====================================================
def ai_score(df):
    l = df.iloc[-1]
    score = 0

    if l["Close"] > l["MA5"]:
        score += 20
    if l["Close"] > l["MA20"]:
        score += 20
    if l["Volume"] > l["VOL20"] * 2:
        score += 30
    if 40 < l["RSI"] < 70:
        score += 20

    return min(score, 100)

# =====================================================
# 시장 스캔 (급등주)
# =====================================================
def scan_market():
    result = []

    for name in names[:80]:  # 속도 제한
        try:
            c = code(name)
            df = get_raw_price(c)

            if df.empty:
                continue

            df = ind(df)
            if df.empty:
                continue

            score = ai_score(df)

            result.append({
                "종목": name,
                "AI점수": score
            })

        except:
            continue

    return pd.DataFrame(result).sort_values("AI점수", ascending=False)

# =====================================================
# 테마주
# =====================================================
theme_map = {
    "AI": ["네이버", "카카오", "삼성"],
    "2차전지": ["에코", "포스코", "LG"],
    "반도체": ["삼성전자", "SK하이닉스"],
    "로봇": ["레인보우", "두산"]
}

def theme_stocks():
    result = []

    for theme, keys in theme_map.items():
        for name in names:
            if any(k in name for k in keys):
                result.append({
                    "테마": theme,
                    "종목": name
                })

    return pd.DataFrame(result)

# =====================================================
# UI
# =====================================================
st.subheader("📊 종목 선택")

col1, col2 = st.columns([4, 1])

with col1:
    selected = st.selectbox("종목", names)

with col2:
    refresh = st.button("🔄 새로고침")

if refresh:
    st.cache_data.clear()
    st.rerun()

# =====================================================
# 실행
# =====================================================
target = code(selected)

if target:
    raw = get_raw_price(target)

    if raw.empty:
        st.error("데이터 없음")
    else:
        df = ind(raw)

        if df.empty:
            st.warning("데이터 부족")
        else:
            table = {
                "종목": selected,
                "현재가": int(df.iloc[-1]["Close"]),
                "RSI": round(df.iloc[-1]["RSI"], 1),
                "세력점수": power(df),
                "추천매수가": buy_price(df)[0],
                "목표매도가": sell_price(df)
            }

            st.success("AI 분석 완료")
            st.dataframe(pd.DataFrame([table]), use_container_width=True)

            # 1주 분석
            st.subheader("📈 1주 변동")
            st.table(pd.DataFrame([week_high_low(df)]))

            st.markdown(f"""
            ### 📌 해석
            - RSI: {table['RSI']}
            - 세력점수: {table['세력점수']}%
            - 전략: {buy_price(df)[1]}
            """)

# =====================================================
# AI 급등주
# =====================================================
if st.button("🚀 AI 급등주 TOP 10"):
    st.subheader("🔥 급등 예상 종목")
    st.dataframe(scan_market().head(10), use_container_width=True)

# =====================================================
# 테마주
# =====================================================
if st.button("📊 테마주 보기"):
    st.subheader("🔥 테마 종목")
    st.dataframe(theme_stocks(), use_container_width=True)