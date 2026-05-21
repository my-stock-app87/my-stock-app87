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
st_autorefresh(interval=15000, key="refresh")

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
    padding:14px;
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

    return df.dropna()

# =========================================================
# 상태
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = ""

# =========================================================
# 메뉴
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
# 🧠 종합분석 (HTS 표 스타일 완성본)
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

        # =====================================================
        # 상태
        # =====================================================
        if whale >= 65 and vol_pct > 0:
            status = "🟥 매수구간"
        elif whale < 35:
            status = "🟦 매도구간"
        else:
            status = "⚪ 관망"

        up_prob = np.clip(whale * 0.7, 0, 95)

        # =====================================================
        # HTS 스타일 표
        # =====================================================
        st.markdown(f"""
        <div class="card">

        <table style="width:100%; border-collapse:collapse; font-size:14px;">

            <tr style="background:#f7f7f7;">
                <td style="padding:10px; font-weight:800;">현재가</td>
                <td style="padding:10px; text-align:right;">
                    {price:,}원 ({pct:+.2f}%)
                </td>
                <td style="text-align:right; font-weight:900;">{status}</td>
            </tr>

            <tr>
                <td style="padding:10px; font-weight:800;">매수추천</td>
                <td colspan="2" style="padding:10px; text-align:right; color:#ff4d4d; font-weight:800;">
                    {buy_price:,}원
                </td>
            </tr>

            <tr style="background:#f7f7f7;">
                <td style="padding:10px; font-weight:800;">매도추천</td>
                <td colspan="2" style="padding:10px; text-align:right; color:#4d79ff; font-weight:800;">
                    {sell_price:,}원
                </td>
            </tr>

            <tr>
                <td style="padding:10px; font-weight:800;">세력</td>
                <td colspan="2" style="padding:10px; text-align:right;">
                    {whale:.1f}%
                </td>
            </tr>

            <tr style="background:#f7f7f7;">
                <td style="padding:10px; font-weight:800;">거래량 변화</td>
                <td colspan="2" style="padding:10px; text-align:right;">
                    {vol_pct:+.1f}%
                </td>
            </tr>

            <tr>
                <td style="padding:10px; font-weight:800;">예측확률</td>
                <td colspan="2" style="padding:10px; text-align:right;">
                    {up_prob:.1f}%
                </td>
            </tr>

        </table>

        </div>
        """, unsafe_allow_html=True)

        # =====================================================
        # AI 전략 (3~5줄 이상)
        # =====================================================
        st.markdown("### 🤖 AI 전략")

        if whale >= 70 and vol_pct > 10:
            ai = """
✔ 세력 강한 유입 확인  
✔ 거래량 동반 상승  
✔ 단기 급등 가능성 높음  
✔ 눌림 시 분할 매수 전략 유효  
✔ 단타 대응 중심
"""
        elif whale >= 60:
            ai = """
✔ 세력 유입 초기 단계  
✔ 방향성 아직 불확실  
✔ 추격 매수 위험 존재  
✔ 지지선 확인 후 진입 필요  
✔ 관망 + 대기 전략
"""
        elif whale < 35:
            ai = """
✔ 약세 흐름 진행 중  
✔ 매도 압력 우세  
✔ 반등 신호 부족  
✔ 리스크 관리 필요  
✔ 비중 축소 권장
"""
        else:
            ai = """
✔ 횡보 구간 진행 중  
✔ 뚜렷한 방향 없음  
✔ 돌파 여부 중요  
✔ 단기 대응 금지  
✔ 관망 유지
"""

        st.markdown(f"<div class='card' style='white-space:pre-line;'>{ai}</div>", unsafe_allow_html=True)

        # 뉴스
        st.markdown("### 📰 뉴스")
        for n in get_news(name):
            st.markdown(f"- {n['title']}")

# =========================================================
# ⚡ 단타 TOP5 (테마 + 고속)
# =========================================================
elif st.session_state.page == "scalp":

    if st.button("⬅️ 뒤로"):
        st.session_state.page = ""

    st.markdown("## ⚡ 단타 테마 TOP5")

    themes = ["AI", "로봇", "반도체", "2차전지", "전력", "바이오"]

    df = df_stock.copy()
    pool = df[df["Name"].str.contains("|".join(themes), na=False)]

    if len(pool) < 50:
        pool = df.sample(200)

    base = pool.sample(25)

    rows = []

    progress = st.progress(0)

    for i, (_, r) in enumerate(base.iterrows()):

        try:
            c = r["Code"]
            dfp = get_price(c)

            if dfp.empty:
                continue

            l = dfp.iloc[-1]
            p = dfp.iloc[-2]

            price = int(l["Close"])

            if price > 20000:
                continue

            if l["Volume"] < 100000:
                continue

            vol_pct = (l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10) * 100

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

    if rows:
        result = pd.DataFrame(rows).sort_values("점수", ascending=False).head(5)
        st.dataframe(result, use_container_width=True)
    else:
        st.warning("조건 없음")