import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import feedparser
from streamlit_autorefresh import st_autorefresh

# =========================================================
# 설정
# =========================================================
st.set_page_config(page_title="주식주신 PRO", layout="centered")
st_autorefresh(interval=15000, key="refresh")  # ⚡ 속도 최적화 (5초 → 15초)

# =========================================================
# 스타일
# =========================================================
st.markdown("""
<style>

.block-container{
    padding: 1rem;
}

.title{
    text-align:center;
    font-size:34px;
    font-weight:900;
    color:#ff2e2e;
}

.card{
    background:white;
    padding:16px;
    border-radius:16px;
    border:1px solid #eee;
    margin-bottom:12px;
}

div.stButton > button{
    width:100%;
    height:60px;
    font-size:18px;
    font-weight:800;
    border-radius:16px;
}

</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🔥 주식주신 PRO</div>", unsafe_allow_html=True)

# =========================================================
# 데이터
# =========================================================
@st.cache_data(ttl=3600)
def stock_list():
    return fdr.StockListing("KRX")[["Code", "Name"]].dropna()

df_stock = stock_list()
names = df_stock["Name"].tolist()

def code(name):
    r = df_stock[df_stock["Name"] == name]
    return r["Code"].iloc[0] if not r.empty else None

# ⚡ 속도 핵심 (120 → 80 줄이기)
@st.cache_data(ttl=20)
def get_price(c):
    return fdr.DataReader(str(c)).tail(80)

@st.cache_data(ttl=300)
def get_news(name):
    url = f"https://news.google.com/rss/search?q={name}+주식&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    return [{"title": e.title, "link": e.link} for e in feed.entries[:5]]

# =========================================================
# 지표
# =========================================================
def ind(df):

    df = df.copy()

    df["MA5"] = df["Close"].rolling(5).mean()

    vol = df["Volume"] / (df["Volume"].rolling(20).mean() + 1e-10)

    trend = (df["Close"] - df["MA5"]) / (df["MA5"] + 1e-10)

    power = (df["Close"] - df["Open"]) / (df["Open"] + 1e-10) * 100

    df["Whale"] = np.clip(vol * 45 + trend * 35 + power * 8, 0, 100)

    df["Pred"] = df["Whale"] * 0.2

    df["RSI"] = 50

    df["Money"] = df["Close"] * df["Volume"] / 1e8

    return df.dropna()

# =========================================================
# 페이지 상태
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = ""

# =========================================================
# 메인
# =========================================================
if st.session_state.page == "":

    st.markdown("<div class='card' style='text-align:center;'>메뉴 선택</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧠 종합분석"):
            st.session_state.page = "analysis"

    with col2:
        if st.button("⚡ 단타 TOP5"):
            st.session_state.page = "scalp"

# =========================================================
# 🧠 종합분석 (HTS 스타일)
# =========================================================
elif st.session_state.page == "analysis":

    if st.button("⬅️ 뒤로"):
        st.session_state.page = ""

    st.markdown("## 🧠 종합분석")

    name = st.selectbox("종목 선택", names)

    c = code(name)

    df = ind(get_price(c))

    if not df.empty:

        l = df.iloc[-1]
        p = df.iloc[-2]

        price = int(l["Close"])
        pct = (price - p["Close"]) / p["Close"] * 100

        buy_price = int(price * 0.98)
        sell_price = int(price * 1.04)

        whale = l["Whale"]

        vol_pct = (l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10) * 100

        up_prob = np.clip(whale * 0.7, 0, 95)
        predict = "📈 상승" if up_prob > 50 else "📉 하락"

        # =====================================================
        # 상단 (현재가 + 매수/매도)
        # =====================================================
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.metric("현재가", f"{price:,}원", f"{pct:+.2f}%")

        with col2:
            st.metric("매수추천", f"{buy_price:,}원")

        with col3:
            st.metric("매도추천", f"{sell_price:,}원")

        # =====================================================
        # 핵심 지표
        # =====================================================
        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        col1.metric("세력이있다", f"{whale:.1f}%")
        col2.metric("거래량", f"{int(l['Volume']):,}", f"{vol_pct:+.1f}%")
        col3.metric("오늘의 예측", f"{up_prob:.1f}%")

        col4, col5, col6 = st.columns(3)
        col4.metric("최고가", f"{int(l['High']):,}원")
        col5.metric("최저가", f"{int(l['Low']):,}원")
        col6.metric("AI의 의견", predict)

        # =====================================================
        # 상태
        # =====================================================
        st.markdown("---")

        if whale >= 65 and vol_pct > 0:
            st.success("🟥 매수 구간")
        elif whale < 35:
            st.error("🟦 매도 구간")
        else:
            st.info("⚪ 관망")

        # =====================================================
        # AI 전략 (3~5줄 리포트)
        # =====================================================
        st.markdown("### 🤖 AI 전략")

        if whale >= 70 and vol_pct > 10:
            ai_plan = """
1️⃣ 세력 매집 강한 구간  
2️⃣ 거래량 동반 상승  
3️⃣ 단기 급등 가능성  
4️⃣ 눌림 매수 전략 유리
"""
        elif whale >= 60:
            ai_plan = """
1️⃣ 세력 유입 초기  
2️⃣ 방향성 확인 필요  
3️⃣ 추격 매수 위험  
4️⃣ 지지 확인 후 진입
"""
        elif l["RSI"] < 30:
            ai_plan = """
1️⃣ 과매도 구간  
2️⃣ 반등 가능성 존재  
3️⃣ 분할 매수 전략  
4️⃣ 손절 기준 필수
"""
        else:
            ai_plan = """
1️⃣ 횡보 구간  
2️⃣ 방향성 없음  
3️⃣ 관망 필요  
4️⃣ 돌파 확인 후 대응
"""

        st.markdown(f"""
        <div class='card' style="white-space:pre-line; line-height:1.7;">
        {ai_plan}
        </div>
        """, unsafe_allow_html=True)

        # 뉴스
        st.markdown("### 📰 뉴스")

        for n in get_news(name):
            st.markdown(f"- {n['title']}")

# =========================================================
# ⚡ 단타 TOP5 (초고속)
# =========================================================
elif st.session_state.page == "scalp":

    if st.button("⬅️ 뒤로"):
        st.session_state.page = ""

    st.markdown("## ⚡ 단타 TOP5 (2만원 이하)")

    base = df_stock.sample(30)  # ⚡ 속도 핵심 (50 → 30)

    rows = []

    progress = st.progress(0)

    for i, (_, r) in enumerate(base.iterrows()):

        try:
            c = r["Code"]

            df = get_price(c)

            if df.empty:
                continue

            l = df.iloc[-1]
            p = df.iloc[-2]

            price = int(l["Close"])

            if price > 20000:
                continue

            if l["Volume"] < 120000:
                continue

            vol_pct = (l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10) * 100

            if vol_pct < -20:
                continue

            chg = (l["Close"] - p["Close"]) / p["Close"] * 100

            whale = l["Whale"]

            score = whale * 0.7 + vol_pct * 0.2 + max(chg, 0) * 3

            rows.append({
                "종목": r["Name"],
                "현재가": f"{price:,}원",
                "등락률": round(chg, 2),
                "거래량": f"{int(l['Volume']):,}",
                "세력": round(whale, 1),
                "점수": round(score, 1)
            })

        except:
            continue

        progress.progress((i + 1) / len(base))

    progress.empty()

    if len(rows) == 0:
        st.warning("조건 만족 종목 없음")
    else:
        result = pd.DataFrame(rows).sort_values("점수", ascending=False).head(5)
        st.dataframe(result, use_container_width=True)

    st.info("⚡ 속도 최적화: 30종목 + 필터 + 캐시 + 진행바")