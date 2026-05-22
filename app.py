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

if "result" not in st.session_state:
    st.session_state.result = None

# ==========================================
# 2. 종목 매핑
# ==========================================
STOCK_MAP = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "카카오": "035720.KS",
    "네이버": "035420.KS",
    "현대차": "005380.KS"
}

# ==========================================
# 3. 데이터
# ==========================================
@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="10d", interval="1d")
    df = df.dropna()
    return df

# ==========================================
# 4. 한글 검색 (완전 안정)
# ==========================================
def resolve_stock(user):
    user = str(user).strip().replace(" ", "").replace("\n", "")

    if user in STOCK_MAP:
        return STOCK_MAP[user], user

    for k in STOCK_MAP:
        if k.replace(" ", "") in user:
            return STOCK_MAP[k], k

    if user.isdigit() and len(user) == 6:
        return user + ".KS", user

    return None, None

# ==========================================
# 5. 분석
# ==========================================
def analyze(df):
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    close = float(latest["Close"])
    prev_close = float(prev["Close"])

    high = float(df["High"].max())
    low = float(df["Low"].min())
    volume = float(latest["Volume"])

    change = close - prev_close
    change_pct = round(change / prev_close * 100, 2)

    avg_vol = df["Volume"].mean()
    vol_score = min(max(int(volume / avg_vol * 50), 10), 95)

    price_pos = (close - low) / max(high - low, 1) * 100
    up_score = min(max(int(price_pos * 0.6 + change_pct * 5 + 40), 5), 98)

    if up_score >= 70:
        position = "🔥 매수 우세"
        color = "#FF4B4B"
    elif up_score <= 35:
        position = "🛑 약세"
        color = "#1F77B4"
    else:
        position = "👀 관망"
        color = "#FFA500"

    return {
        "close": close,
        "change": change,
        "change_pct": change_pct,
        "high": high,
        "low": low,
        "volume": volume,
        "vol_score": vol_score,
        "up_score": up_score,
        "position": position,
        "color": color
    }

# ==========================================
# 6. UI
# ==========================================
st.title("🔥 주식주신 PRO")

user = st.text_input("종목명 또는 6자리 코드 입력")

# ==========================================
# 🔥 분석 시작 버튼 (핵심)
# ==========================================
if st.button("📊 분석 시작"):

    ticker, name = resolve_stock(user)

    if ticker is None:
        st.error("삼성전자 / 카카오 / 네이버 / 6자리 코드만 가능")
        st.stop()

    df = get_data(ticker)

    if df is None or len(df) < 2:
        st.error("데이터 부족")
        st.stop()

    st.session_state.result = {
        "df": df,
        "name": name,
        "ticker": ticker,
        "res": analyze(df)
    }

# ==========================================
# 7. 결과 출력
# ==========================================
if st.session_state.result:

    data = st.session_state.result
    res = data["res"]
    df = data["df"]
    name = data["name"]

    # 현재가 + 포지션
    col1, col2 = st.columns([2, 1])

    with col1:
        st.metric(
            f"{name} 현재가",
            f"{res['close']:.0f}원",
            f"{res['change']:.0f} ({res['change_pct']}%)"
        )

    with col2:
        st.markdown(
            f"<div style='color:{res['color']};font-size:20px;font-weight:bold;margin-top:25px;'>"
            f"{res['position']}</div>",
            unsafe_allow_html=True
        )

    # 전체 데이터
    st.subheader("📊 전체 분석 데이터")

    st.dataframe(pd.DataFrame({
        "항목": ["현재가","고가","저가","거래량","거래 집중도","상승 가능성"],
        "값": [
            f"{res['close']:.0f}",
            f"{res['high']:.0f}",
            f"{res['low']:.0f}",
            f"{res['volume']:.0f}",
            f"{res['vol_score']}%",
            f"{res['up_score']}%"
        ]
    }), hide_index=True)

    # 5일 차트
    st.subheader("📈 최근 5일")
    st.line_chart(df["Close"].tail(5))

    # 지표
    st.subheader("📊 거래 집중도")
    st.progress(res["vol_score"] / 100)

    st.subheader("📈 상승 가능성")
    st.progress(res["up_score"] / 100)