# =========================================================
# 주식주신 PRO - AI 전체시장 스캐너
# 모바일 최적화 버전
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser
from concurrent.futures import ThreadPoolExecutor
from streamlit_autorefresh import st_autorefresh

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="주식주신 PRO",
    layout="wide"
)

st_autorefresh(interval=10000, key="refresh")

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>

html, body, [class*="css"]{
    font-family:Pretendard, sans-serif;
}

.block-container{
    padding-top:1rem;
    padding-left:0.8rem;
    padding-right:0.8rem;
    padding-bottom:3rem;
}

/* 타이틀 */
.main-title{
    text-align:center;
    font-size:42px;
    font-weight:900;
    color:#ff2e2e;
    margin-bottom:5px;
}

.sub-title{
    text-align:center;
    color:gray;
    font-size:15px;
    margin-bottom:30px;
}

/* 카드 */
.card{
    background:white;
    padding:18px;
    border-radius:20px;
    border:1px solid #ececec;
    box-shadow:0 2px 10px rgba(0,0,0,0.05);
    margin-bottom:16px;
}

/* 버튼 */
div.stButton > button{
    width:100%;
    height:70px;
    border-radius:18px;
    border:none;
    background:#f5f5f5;
    font-size:18px;
    font-weight:800;
}

div.stButton > button:hover{
    background:#ffeaea;
    color:red;
}

/* metric */
[data-testid="metric-container"]{
    border-radius:16px;
    padding:12px;
    background:white;
    border:1px solid #eee;
}

/* dataframe */
[data-testid="stDataFrame"]{
    border-radius:18px;
    overflow:hidden;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 타이틀
# =========================================================
st.markdown("""
<div class='main-title'>
🔥 주식주신 PRO
</div>

<div class='sub-title'>
AI 기반 급등주 / 반등주 탐색 시스템
</div>
""", unsafe_allow_html=True)

# =========================================================
# 종목 리스트
# =========================================================
@st.cache_data(ttl=86400)
def stock_list():

    df = fdr.StockListing("KRX")

    return df[["Code", "Name"]].dropna()

df_stock = stock_list()

# =========================================================
# 데이터 가져오기
# =========================================================
@st.cache_data(ttl=30)
def get_price(code):

    try:
        df = fdr.DataReader(str(code)).tail(120)

        if df.empty:
            return pd.DataFrame()

        return df

    except:
        return pd.DataFrame()

# =========================================================
# 뉴스
# =========================================================
@st.cache_data(ttl=300)
def get_news(name):

    url = f"https://news.google.com/rss/search?q={name}+주식&hl=ko&gl=KR&ceid=KR:ko"

    feed = feedparser.parse(url)

    result = []

    for e in feed.entries[:5]:

        result.append({
            "title": e.title,
            "link": e.link
        })

    return result

# =========================================================
# 지표 계산
# =========================================================
def make_indicator(df):

    if len(df) < 30:
        return pd.DataFrame()

    df = df.copy()

    # 이동평균
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()

    # 거래량 평균
    df["VOL20"] = df["Volume"].rolling(20).mean()

    # 거래량 세력
    volume_power = (
        df["Volume"] /
        (df["VOL20"] + 1e-10)
    )

    # 추세
    trend = (
        (df["Close"] - df["MA5"]) /
        (df["MA5"] + 1e-10)
    ) * 100

    # 캔들 파워
    power = (
        (df["Close"] - df["Open"]) /
        (df["Open"] + 1e-10)
    ) * 100

    # RSI
    delta = df["Close"].diff()

    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)

    avg_up = up.rolling(14).mean()
    avg_down = down.rolling(14).mean()

    rs = avg_up / (avg_down + 1e-10)

    df["RSI"] = 100 - (100 / (1 + rs))

    # 거래대금
    df["Money"] = (
        df["Close"] * df["Volume"]
    ) / 100000000

    # 세력점수
    df["Whale"] = np.clip(
        volume_power * 45 +
        trend * 35 +
        power * 12,
        0,
        100
    )

    # 변동성
    std = df["Close"].rolling(5).std()

    # 상승예측
    df["Pred"] = np.clip(
        std / (df["Close"] + 1e-10) * 100 * 5,
        0,
        25
    )

    # 반등 점수
    df["Rebound"] = np.clip(
        (40 - df["RSI"]) * 1.8 +
        df["Whale"] * 0.5,
        0,
        100
    )

    return df.dropna()

# =========================================================
# 종합 분석 멘트
# =========================================================
def analysis_text(l):

    if l["Whale"] > 75:
        return "🚀 강한 세력 매집 흐름 감지"

    elif l["RSI"] < 30:
        return "🎯 과매도 반등 가능성"

    elif l["Pred"] > 12:
        return "🔥 단기 급등 변동성 확대"

    elif l["RSI"] > 80:
        return "⚠️ 단기 과열 주의"

    else:
        return "📊 박스권 흐름"

# =========================================================
# 분석 함수
# =========================================================
def analyze_stock(row):

    try:
        code = row["Code"]
        name = row["Name"]

        raw = get_price(code)

        if raw.empty:
            return None

        df = make_indicator(raw)

        if df.empty:
            return None

        l = df.iloc[-1]
        p = df.iloc[-2]

        pct = (
            (l["Close"] - p["Close"]) /
            p["Close"]
        ) * 100

        return {
            "종목": name,
            "현재가": int(l["Close"]),
            "등락률": round(pct, 2),
            "세력점수": round(l["Whale"], 1),
            "RSI": round(l["RSI"], 1),
            "거래대금": round(l["Money"], 1),
            "상승예측": round(l["Pred"], 1),
            "반등점수": round(l["Rebound"], 1),
            "분석": analysis_text(l)
        }

    except:
        return None

# =========================================================
# 메뉴
# =========================================================
menu = st.radio(
    "메뉴",
    [
        "🚀 급등주",
        "🎯 반등주",
        "🧠 AI 종합분석"
    ],
    horizontal=True
)

# =========================================================
# 분석 시작
# =========================================================
MAX_STOCK = 250

stocks = df_stock.head(MAX_STOCK)

results = []

progress = st.progress(0)

status = st.empty()

# =========================================================
# 멀티스레드 분석
# =========================================================
with ThreadPoolExecutor(max_workers=10) as executor:

    futures = []

    for idx, row in stocks.iterrows():

        futures.append(
            executor.submit(analyze_stock, row)
        )

    for i, future in enumerate(futures):

        result = future.result()

        if result is not None:
            results.append(result)

        progress.progress((i + 1) / len(futures))

        status.text(
            f"AI 분석중... {i+1}/{len(futures)}"
        )

# =========================================================
# 결과
# =========================================================
if len(results) == 0:

    st.warning("데이터 부족")
    st.stop()

df_result = pd.DataFrame(results)

# =========================================================
# 급등주
# =========================================================
if menu == "🚀 급등주":

    st.markdown("## 🚀 실시간 급등주 TOP10")

    surge = df_result[
        (df_result["등락률"] > 3) &
        (df_result["세력점수"] > 60) &
        (df_result["거래대금"] > 20)
    ]

    surge = surge.sort_values(
        "등락률",
        ascending=False
    ).head(10)

    st.dataframe(
        surge,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# 반등주
# =========================================================
elif menu == "🎯 반등주":

    st.markdown("## 🎯 반등 예상 TOP10")

    rebound = df_result[
        (df_result["등락률"] < -2) &
        (df_result["RSI"] < 40) &
        (df_result["세력점수"] > 50)
    ]

    rebound = rebound.sort_values(
        "반등점수",
        ascending=False
    ).head(10)

    st.dataframe(
        rebound,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# 종합분석
# =========================================================
elif menu == "🧠 AI 종합분석":

    st.markdown("## 🧠 AI 종합분석 TOP20")

    total = df_result.sort_values(
        "세력점수",
        ascending=False
    ).head(20)

    st.dataframe(
        total,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# 뉴스
# =========================================================
st.markdown("## 📰 실시간 시장 뉴스")

top_stock = df_result.sort_values(
    "세력점수",
    ascending=False
).iloc[0]["종목"]

news = get_news(top_stock)

for n in news:

    st.markdown(
        f"- [{n['title']}]({n['link']})"
    )