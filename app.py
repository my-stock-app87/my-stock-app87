import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

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
# 2. 한글 → 티커 매핑
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
# 3. 데이터 가져오기 (안정형)
# ==========================================
@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="10d", interval="1d")
    return df

# ==========================================
# 4. 분석 로직
# ==========================================
def analyze(df):

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    close = int(latest["Close"])
    prev_close = int(prev["Close"])

    high = int(latest["High"])
    low = int(latest["Low"])
    volume = int(latest["Volume"])

    change = close - prev_close
    change_pct = round((change / prev_close) * 100, 2)

    # 거래 집중도
    avg_vol = df["Volume"].mean()
    vol_score = min(max(int(volume / avg_vol * 50), 10), 95)

    if vol_score >= 80:
        vol_state = "🔥 과열"
    elif vol_score >= 50:
        vol_state = "👍 활발"
    else:
        vol_state = "😴 약함"

    # 상승 가능성
    price_pos = (close - low) / max(high - low, 1) * 100
    up_score = min(max(int(price_pos * 0.6 + change_pct * 5 + 40), 5), 98)

    if up_score >= 75:
        up_state = "🚀 강한 상승"
    elif up_score >= 50:
        up_state = "📈 상승 가능"
    else:
        up_state = "⚠ 약세"

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

    # AI 코멘트
    ai = f"""
    거래 집중도: {vol_state}, 상승 가능성: {up_state} 기반 분석입니다.
    단기 흐름은 {'상승 압력 우세' if up_score >= 70 else '중립 또는 조정 구간'}입니다.
    """

    return {
        "close": close,
        "change": change,
        "change_pct": change_pct,
        "high": high,
        "low": low,
        "volume": int(volume),
        "vol_score": vol_score,
        "vol_state": vol_state,
        "up_score": up_score,
        "up_state": up_state,
        "position": position,
        "color": color,
        "ai": ai
    }

# ==========================================
# 5. UI
# ==========================================
st.title("🔥 주식주신 PRO")

user = st.text_input("종목명 또는 코드 입력")

if user:

    # 한글 처리
    if user in STOCK_MAP:
        ticker = STOCK_MAP[user]
        name = user
    elif user.endswith(".KS") or user.isdigit():
        ticker = user
        name = user
    else:
        st.error("지원 종목: 삼성전자, 카카오, 네이버 또는 6자리 코드")
        st.stop()

    df = get_data(ticker)

    if df is None or df.empty:
        st.error("데이터 없음")
        st.stop()

    res = analyze(df)

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
    # 핵심 지표
    # ==========================================
    st.subheader("📊 핵심 분석")

    st.dataframe(pd.DataFrame({
        "항목": ["고가", "저가", "거래량", "거래 집중도", "상승 가능성"],
        "값": [
            f"{res['high']:,}",
            f"{res['low']:,}",
            f"{res['volume']:,}",
            f"{res['vol_score']}% ({res['vol_state']})",
            f"{res['up_score']}% ({res['up_state']})"
        ]
    }), hide_index=True)

    # ==========================================
    # 5일 차트
    # ==========================================
    st.subheader("📈 최근 5일")

    chart = df["Close"].tail(5)
    st.line_chart(chart)

    # ==========================================
    # 거래 집중도
    # ==========================================
    st.subheader("📊 거래 집중도")
    st.progress(res["vol_score"] / 100)
    st.write(res["vol_state"])

    # ==========================================
    # 상승 가능성
    # ==========================================
    st.subheader("📈 상승 가능성")
    st.progress(res["up_score"] / 100)
    st.write(res["up_state"])

    # ==========================================
    # AI
    # ==========================================
    st.subheader("💡 AI 분석")
    st.info(res["ai"])