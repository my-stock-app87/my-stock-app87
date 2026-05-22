import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import datetime

# ==========================================
# 0. 앱 설정
# ==========================================
st.set_page_config(
    page_title="주식주신PRO",
    page_icon="🔥",
    layout="centered"
)

# ==========================================
# 1. 스타일
# ==========================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to bottom, #0F172A, #111827);
    color: white;
}

.stButton>button {
    background-color: #FF4B4B;
    color: white;
    border-radius: 10px;
    height: 45px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 세션
# ==========================================
if "page" not in st.session_state:
    st.session_state.page = "intro"

# ==========================================
# 3. 종목 매핑
# ==========================================
STOCK_MAP = {
    "삼성전자": "005930",
    "카카오": "035720",
    "네이버": "035420",
    "sk하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "현대차": "005380",
    "기아": "000270",
    "삼성바이오로직스": "207940"
}

# ==========================================
# 4. 종목 코드 변환 (한글 검색 해결)
# ==========================================
def resolve_stock_code(user_input):

    if not user_input:
        return None

    clean = str(user_input).strip().replace(" ", "")

    if clean.isdigit() and len(clean) == 6:
        return clean

    for name, code in STOCK_MAP.items():
        if name.replace(" ", "") == clean:
            return code

    return None

# ==========================================
# 5. 데이터
# ==========================================
@st.cache_data(ttl=60)
def get_stock_data(code):
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=30)

    df = fdr.DataReader(code, start, end)
    return df if not df.empty else None

# ==========================================
# 6. 분석 로직
# ==========================================
def analyze(df):

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    current = int(latest["Close"])
    prev_close = int(prev["Close"])

    high = int(latest["High"])
    low = int(latest["Low"])
    volume = int(latest["Volume"])

    change = current - prev_close
    change_pct = round((change / prev_close) * 100, 2)

    avg_vol = df["Volume"].tail(5).mean()
    vol_score = min(max(int(volume / avg_vol * 50), 10), 95)

    price_pos = (current - low) / max(high - low, 1) * 100
    up_score = min(max(int(price_pos * 0.7 + change_pct * 5), 5), 98)

    # ==========================================
    # 거래 집중도 해석
    # ==========================================
    if vol_score >= 80:
        vol_state = "🔥 과열 (거래 폭발)"
    elif vol_score >= 50:
        vol_state = "👍 활발 (정상 이상)"
    else:
        vol_state = "😴 한산 (관심 저조)"

    # ==========================================
    # 상승 가능성 해석
    # ==========================================
    if up_score >= 75:
        up_state = "🚀 강한 상승 흐름"
    elif up_score >= 50:
        up_state = "📈 상승 가능성 있음"
    else:
        up_state = "⚠ 약세 / 불확실"

    # ==========================================
    # 포지션
    # ==========================================
    if up_score >= 70:
        position = "🔥 상승 우세"
        color = "#FF4B4B"
    elif up_score <= 35:
        position = "⚠ 약세"
        color = "#1F77B4"
    else:
        position = "👀 관망"
        color = "#FFA500"

    # ==========================================
    # AI 코멘트
    # ==========================================
    if up_score >= 70:
        ai = "거래량 증가 + 상승 흐름 유지. 눌림 매수 전략 유효."
    elif up_score <= 35:
        ai = "하락 압력 존재. 신규 진입은 보수적으로."
    else:
        ai = "횡보 구간. 방향성 확인 필요."

    return {
        "current": current,
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
        "ai": ai,
        "buy": int(low * 1.003),
        "sell": int(high * 0.997)
    }

# ==========================================
# 7. INTRO
# ==========================================
if st.session_state.page == "intro":

    st.markdown("<h1 style='text-align:center;'>🔥 주식주신 PRO</h1>", unsafe_allow_html=True)

    if st.button("분석 시작"):
        st.session_state.page = "analysis"
        st.rerun()

# ==========================================
# 8. ANALYSIS
# ==========================================
else:

    if st.button("🏠 홈"):
        st.session_state.page = "intro"
        st.rerun()

    st.title("📊 주식 분석실")

    user_input = st.text_input("종목명 또는 6자리 코드 입력")
    btn = st.button("🚀 분석 시작")

    if btn and user_input:

        code = resolve_stock_code(user_input)

        if code is None:
            st.error("종목명을 정확히 입력하세요 (예: 삼성전자, 카카오, 005930)")
            st.stop()

        df = get_stock_data(code)

        if df is None:
            st.error("데이터를 불러올 수 없습니다.")
            st.stop()

        result = analyze(df)

        # ==========================================
        # 현재가 + 포지션 (같은 줄)
        # ==========================================
        col1, col2 = st.columns([2, 1])

        with col1:
            st.metric(
                "현재가",
                f"{result['current']:,}원",
                f"{result['change']:,} ({result['change_pct']}%)"
            )

        with col2:
            st.markdown(
                f"<div style='color:{result['color']}; font-size:18px; font-weight:bold; margin-top:30px;'>"
                f"{result['position']}</div>",
                unsafe_allow_html=True
            )

        st.write("")

        # ==========================================
        # 핵심 분석 지표
        # ==========================================
        st.subheader("📊 핵심 분석 지표")

        st.dataframe(pd.DataFrame({
            "항목": ["고가", "저가", "거래량", "거래 집중도", "상승 가능성"],
            "값": [
                f"{result['high']:,}",
                f"{result['low']:,}",
                f"{result['volume']:,}",
                f"{result['vol_score']}% ({result['vol_state']})",
                f"{result['up_score']}% ({result['up_state']})"
            ]
        }), hide_index=True)

        # ==========================================
        # 시장 체크 포인트
        # ==========================================
        st.subheader("🎯 시장 체크 포인트")

        st.write(f"• 추천 매수가: {result['buy']:,}원")
        st.write(f"• 추천 매도가: {result['sell']:,}원")
        st.write(f"• 단기 지지선: {result['low']:,}원")
        st.write(f"• 단기 저항선: {result['high']:,}원")

        st.write("")

        # ==========================================
        # 최근 5일 차트
        # ==========================================
        st.subheader("📈 최근 5일 주가 흐름")

        recent = df.tail(5).copy()
        recent.index = recent.index.strftime("%m/%d")

        chart = recent[["Close"]]
        chart.columns = ["종가"]

        st.line_chart(chart)

        st.caption("최근 5거래일 기준")

        # ==========================================
        # 거래 집중도 카드
        # ==========================================
        st.markdown("### 📊 거래 집중도")
        st.write(f"현재: **{result['vol_score']}%**")
        st.write(result["vol_state"])
        st.progress(result["vol_score"] / 100)

        # ==========================================
        # 상승 가능성 카드
        # ==========================================
        st.markdown("### 📈 상승 가능성")
        st.write(f"현재: **{result['up_score']}%**")
        st.write(result["up_state"])
        st.progress(result["up_score"] / 100)

        # ==========================================
        # AI 코멘트
        # ==========================================
        st.subheader("💡 AI 분석 코멘트")
        st.info(result["ai"])

        # ==========================================
        # 뉴스
        # ==========================================
        st.subheader("📰 시장 뉴스")
        st.write(f"• [{code}] 거래량 및 변동성 체크")
        st.write("• 기관/외국인 수급 흐름 확인 필요")
        st.write("• 최근 5일 추세 기반 방향성 분석")