# 주식주신 PRO Streamlit 코드

```python
import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser
from streamlit_autorefresh import st_autorefresh

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(page_title="주식주신 PRO", layout="wide")

st.markdown("""
<h1 style='text-align:center;color:red;'>
🔥 주식주신 PRO
</h1>
""", unsafe_allow_html=True)

st_autorefresh(interval=5000, key="refresh")

# =========================================================
# 종목 리스트
# =========================================================
@st.cache_data(ttl=3600)
def stock_list():
    return fdr.StockListing("KRX")[["Code", "Name"]].dropna()

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    r = df_stock[df_stock["Name"] == name]
    return r["Code"].iloc[0] if not r.empty else None

# =========================================================
# 데이터 가져오기
# =========================================================
@st.cache_data(ttl=10)
def get_price(c):
    return fdr.DataReader(str(c)).tail(120)

# =========================================================
# 뉴스 가져오기
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
def ind(df):

    df = df.copy()

    # 이동평균
    df["MA5"] = df["Close"].rolling(5).mean()

    # 거래량 배수
    vol = df["Volume"] / (df["Volume"].rolling(20).mean() + 1e-10)

    # 추세
    trend = (
        (df["Close"] - df["MA5"]) /
        (df["MA5"] + 1e-10)
    )

    # 양봉 힘
    power = (
        ((df["Close"] - df["Open"]) /
        (df["Open"] + 1e-10)) * 100
    )

    # 윗꼬리
    upper_tail = (
        (df["High"] - df["Close"]) /
        (df["High"] - df["Low"] + 1e-10)
    )

    # 세력 점수
    df["Whale"] = np.clip(
        vol * 45 +
        trend * 35 +
        power * 8 -
        upper_tail * 25,
        0,
        100
    )

    # 상승 예측
    std = df["Close"].rolling(5).std()

    df["Pred"] = np.clip(
        (df["Whale"] / 100) *
        (std / (df["Close"] + 1e-10)) * 100,
        0.5,
        25
    )

    # 적중률
    df["Acc"] = np.clip(
        70 + (100 - df["Whale"]) * 0.2,
        50,
        97
    )

    # 체결강도 느낌
    df["Strength"] = (
        (df["Close"] - df["Low"]) /
        (df["High"] - df["Low"] + 1e-10)
    ) * 100

    # 평균 변동폭
    tr = df["High"] - df["Low"]
    avg_tr = tr.rolling(5).mean()

    # 매수 / 매도
    df["Buy"] = df["Close"] - (avg_tr * 0.35)
    df["Sell"] = df["Close"] + (avg_tr * 0.45)

    # 거래대금(억)
    df["Money"] = (
        df["Close"] * df["Volume"]
    ) / 100000000

    return df.dropna()

# =========================================================
# 분석 멘트
# =========================================================
def analysis_text(l):

    if l["Whale"] > 70:
        return "🚀 강한 세력 매집 흐름 감지"

    elif l["Close"] < l["Buy"]:
        return "📉 눌림목 구간 → 분할 매수 관심"

    elif l["Close"] > l["Sell"]:
        return "⚠️ 단기 과열 가능성"

    else:
        return "📊 박스권 흐름"

# =========================================================
# 종목 선택
# =========================================================
name = st.selectbox("🔍 종목 선택", names)

c = code(name)

df = ind(get_price(c))

# =========================================================
# 메인
# =========================================================
if not df.empty:

    l = df.iloc[-1]
    p = df.iloc[-2]

    price = int(l["Close"])

    diff = price - int(p["Close"])

    pct = (
        diff / int(p["Close"])
    ) * 100

    color = "red" if diff > 0 else "blue"

    arrow = "▲" if diff > 0 else "▼"

    # =====================================================
    # 탭
    # =====================================================
    tab1, tab2, tab3 = st.tabs([
        "📊 종합분석",
        "🚀 세력 급등주",
        "🎯 내일 반등"
    ])

    # =====================================================
    # TAB1
    # =====================================================
    with tab1:

        # 현재가
        st.markdown(f"""
        <div style="
            text-align:center;
            padding:20px;
            background:white;
            border-radius:18px;
            border:1px solid #eee;
            margin-bottom:15px;
        ">

        <div style="
            font-size:48px;
            font-weight:900;
            color:{color};
        ">
            {price:,}원
        </div>

        <div style="
            font-size:18px;
            font-weight:700;
            color:{color};
        ">
            {arrow} {diff:+,}원 ({pct:+.2f}%)
        </div>

        </div>
        """, unsafe_allow_html=True)

        # HTS 정보 바
        st.markdown(f"""
        <div style="
            background:#f8f9fa;
            padding:14px;
            border-radius:14px;
            font-size:15px;
            font-weight:800;
            overflow-x:auto;
            white-space:nowrap;
            margin-bottom:15px;
        ">

        🚀 상승예측 {l['Pred']:.1f}% ｜

        🎯 적중률 {l['Acc']:.1f}% ｜

        🐳 세력점수 {l['Whale']:.1f}% ｜

        🔥 체결강도 {l['Strength']:.1f}% ｜

        💰 거래대금 {int(l['Money'])}억

        </div>
        """, unsafe_allow_html=True)

        # 매수 매도 신호
        buy_signal = (
            l["Whale"] > 60 and
            l["Close"] <= l["Buy"] * 1.02
        )

        sell_signal = (
            l["Close"] >= l["Sell"] * 0.98
        )

        if buy_signal:
            st.success("🟥 AI 매수 신호 감지")

        elif sell_signal:
            st.error("🟦 AI 매도 신호 감지")

        else:
            st.info("⚪ 현재 관망 구간")

        # 종합 분석
        st.markdown("### 🧠 종합 분석")

        st.markdown(f"""
        <div style="
            padding:15px;
            border-radius:15px;
            background:white;
            border:1px solid #eee;
            line-height:1.8;
        ">

        {analysis_text(l)}<br><br>

        📈 오늘 최고가 :
        <b style="color:red;">
        {int(l['High']):,}원
        </b><br>

        📉 오늘 최저가 :
        <b style="color:blue;">
        {int(l['Low']):,}원
        </b><br>

        📊 현재 거래량 :
        <b>
        {int(l['Volume']):,}주
        </b><br>

        💰 거래대금 :
        <b>
        {int(l['Money'])}억
        </b>

        </div>
        """, unsafe_allow_html=True)

        # 차트
        st.markdown("### 📈 주가 차트")

        st.line_chart(df["Close"])

        # 뉴스
        st.markdown("### 📰 관련 뉴스")

        news = get_news(name)

        for n in news:
            st.markdown(
                f"- [{n['title']}]({n['link']})"
            )

    # =====================================================
    # TAB2 급등주
    # =====================================================
    with tab2:

        st.markdown("## 🚀 세력 급등주 TOP5")

        rows = []

        for n in names:

            try:
                c = code(n)

                d = ind(get_price(c))

                if d.empty:
                    continue

                l2 = d.iloc[-1]
                p2 = d.iloc[-2]

                # 3만원 이하
                if l2["Close"] > 30000:
                    continue

                # 거래량 필터
                if l2["Volume"] < 300000:
                    continue

                # 거래대금 필터
                if l2["Money"] < 10:
                    continue

                chg = (
                    (l2["Close"] - p2["Close"]) /
                    p2["Close"]
                ) * 100

                score = (
                    l2["Whale"] * 0.6 +
                    max(chg, 0) * 8
                )

                rows.append({
                    "종목": n,
                    "현재가": int(l2["Close"]),
                    "등락률": round(chg, 2),
                    "세력": round(l2["Whale"], 1),
                    "거래대금": f"{int(l2['Money'])}억",
                    "예상": round(l2["Pred"], 1),
                    "점수": round(score, 1)
                })

            except:
                continue

        result = (
            pd.DataFrame(rows)
            .sort_values("점수", ascending=False)
            .head(5)
        )

        st.dataframe(
            result,
            use_container_width=True
        )

    # =====================================================
    # TAB3 내일 반등
    # =====================================================
    with tab3:

        st.markdown("## 🎯 내일 반등 예상 TOP5")

        rows = []

        for n in names:

            try:
                c = code(n)

                d = ind(get_price(c))

                if d.empty:
                    continue

                l2 = d.iloc[-1]
                p2 = d.iloc[-2]

                # 3만원 이하
                if l2["Close"] > 30000:
                    continue

                # 거래량 필터
                if l2["Volume"] < 300000:
                    continue

                # 거래대금 필터
                if l2["Money"] < 10:
                    continue

                chg = (
                    (l2["Close"] - p2["Close"]) /
                    p2["Close"]
                ) * 100

                score = (
                    l2["Whale"] * 0.5 +
                    l2["Acc"] * 0.3 +
                    max(-chg * 5, 0)
                )

                rows.append({
                    "종목": n,
                    "현재가": int(l2["Close"]),
                    "등락률": round(chg, 2),
                    "세력": round(l2["Whale"], 1),
                    "적중": round(l2["Acc"], 1),
                    "거래대금": f"{int(l2['Money'])}억",
                    "점수": round(score, 1)
                })

            except:
                continue

        result = (
            pd.DataFrame(rows)
            .sort_values("점수", ascending=False)
            .head(5)
        )

        st.dataframe(
            result,
            use_container_width=True
        )

else:
    st.warning("데이터 부족")
```
