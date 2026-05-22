import streamlit as st
import pandas as pd
import yfinance as yf

# ==========================================
# 0. 기본 설정
# ==========================================
st.set_page_config(
    page_title="주식주신PRO",
    page_icon="🔥",
    layout="centered"
)

# ==========================================
# 1. 상태
# ==========================================
if "page" not in st.session_state:
    st.session_state.page = "main"

# ==========================================
# 2. 한글 종목 매핑
# ==========================================
STOCK_MAP = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "카카오": "035720.KS",
    "네이버": "035420.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS"
}

# ==========================================
# 3. 데이터 로딩
# ==========================================
@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="10d", interval="1d")
    df = df.dropna()
    return df

# ==========================================
# 4. 한글 검색 해결 함수
# ==========================================
def resolve_stock(user):
    user = user.strip().replace(" ", "")

    if user in STOCK_MAP:
        return STOCK_MAP[user], user

    for k in STOCK_MAP:
        if k in user:
            return STOCK_MAP[k], k

    if user.isdigit() and len(user) == 6:
        return user + ".KS", user

    return None, None

# ==========================================
# 5. 분석 로직 (전체 데이터 유지)
# ==========================================
def analyze(df):

    if df is None or df.empty or len(df) < 2:
        return None

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    close = int(latest["Close"])
    prev_close = int(prev["Close"])

    high = int(df["High"].max())
    low = int(df["Low"].min())
    volume = int(latest["Volume"])

    change = close - prev_close
    change_pct = round(change / prev_close * 100, 2)

    # 거래 집중도
    avg_vol = df["Volume"].mean()
    vol_score = min(max(int(volume / avg_vol * 50), 10), 95)

    vol_state = "🔥 과열" if vol_score >= 80 else "👍 활발" if vol_score >= 50 else "😴 약함"

    # 상승 가능성
    price_pos = (close - low) / max(high - low, 1) * 100
    up_score = min(max(int(price_pos * 0.6 + change_pct * 5 + 40), 5), 98)

    up_state = "🚀 강한 상승" if up_score >= 75 else "📈 상승 가능" if up_score >= 50 else "⚠ 약세"

    # 포지션
    if up_score >= 70:
        position = "🔥 매수 우세"
        color = "#FF4B4B"
    elif up_score <= 35:
        position = "🛑 약세"
        color = "#1F77B4"
    else:
        position = "👀 관망"
        color = "#FFA500"

    ai = f"""
거래 집중도: {vol_state}
상승 가능성: {up_state}

현재 단기 흐름은 {"상승 압력" if up_score >= 70 else "중립/조정"} 구간입니다.
"""

    return {
        "close": close,
        "change": change,
        "change_pct": change_pct,
        "high": high,
        "low": low,
        "volume": volume,
        "vol_score": vol_score,
        "vol_state": vol_state,
        "up_score": up_score,
        "up_state": up_state,
        "position": position,
        "color": color,
        "ai": ai
    }

# ==========================================
# 6. UI
# ==========================================
st.title("🔥 주식주신 PRO")

user = st.text_input("종목명 또는 6자리 코드 입력")

if user:

    ticker, name = resolve_stock(user)

    if ticker is None:
        st.error("삼성전자 / 카카오 / 네이버 / 6자리 코드만 가능")
        st.stop()

    df = get_data(ticker)

    if df is None or df.empty or len(df) < 2:
        st.error("데이터 부족")
        st.stop()

    res = analyze(df)

    if res is None:
        st.error("분석 실패")
        st.stop()

    # ==========================================
    # 현재가 + 포지션
    # ==========================================
    col1, col2 = st.columns([2, 1])

    with col1:
        st.metric(
            "현재가",
            f"{res['close']:,}원",
            f"{res['change']:,} ({res['change_pct']}%)"
        )

    with col2:
        st.markdown(
            f"<div style='color:{res['color']};font-size:20px;font-weight:bold;margin-top:25px;'>"
            f"{res['position']}</div>",
            unsafe_allow_html=True
        )

    # ==========================================
    # 📊 전체 데이터
    # ==========================================
    st.subheader("📊 전체 분석 데이터")

    st.dataframe(pd.DataFrame({
        "항목": [
            "현재가",
            "고가",
            "저가",
            "거래량",
            "거래 집중도",
            "상승 가능성"
        ],
        "값": [
            f"{res['close']:,}",
            f"{res['high']:,}",
            f"{res['low']:,}",
            f"{res['volume']:,}",
            f"{res['vol_score']}% ({res['vol_state']})",
            f"{res['up_score']}% ({res['up_state']})"
        ]
    }), hide_index=True)

    # ==========================================
    # 📈 5일 차트
    # ==========================================
    st.subheader("📈 최근 5일 흐름")
    st.line_chart(df["Close"].tail(5))

    # ==========================================
    # 📊 거래 집중도
    # ==========================================
    st.subheader("📊 거래 집중도")
    st.progress(res["vol_score"] / 100)
    st.write(res["vol_state"])

    # ==========================================
    # 📈 상승 가능성
    # ==========================================
    st.subheader("📈 상승 가능성")
    st.progress(res["up_score"] / 100)
    st.write(res["up_state"])

    # ==========================================
    # 💡 AI 분석
    # ==========================================
    st.subheader("💡 AI 분석")
    st.info(res["ai"])