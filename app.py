import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import datetime

# ==========================================
# 0. 앱 기본 설정
# ==========================================
st.set_page_config(
    page_title="주식주신PRO",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 1. 기본 스타일
# ==========================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to bottom, #0F172A, #111827);
    color: white;
}

div[data-testid="metric-container"] {
    background-color: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 15px;
    border-radius: 15px;
}

.stButton>button {
    background-color: #FF4B4B;
    color: white;
    border-radius: 10px;
    border: none;
    height: 45px;
    font-weight: bold;
}

.stButton>button:hover {
    background-color: #ff2b2b;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 세션 상태
# ==========================================
if "page" not in st.session_state:
    st.session_state.page = "intro"

# ==========================================
# 3. 종목 코드 매핑
# ==========================================
STOCK_MAP = {
    "삼성전자": "005930",
    "sk하이닉스": "000660",
    "카카오": "035720",
    "네이버": "035420",
    "LG에너지솔루션": "373220"
}

# ==========================================
# 4. 실시간 데이터 함수
# ==========================================
@st.cache_data(ttl=60)
def get_stock_data(code):

    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=30)

    df = fdr.DataReader(code, start, end)

    if df.empty:
        return None

    return df

# ==========================================
# 5. 분석 함수
# ==========================================
def calculate_signal(df):

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    current_price = int(latest["Close"])
    prev_close = int(prev["Close"])

    high_price = int(latest["High"])
    low_price = int(latest["Low"])

    volume = int(latest["Volume"])

    change = current_price - prev_close
    change_percent = round((change / prev_close) * 100, 2)

    # 거래량 평균
    avg_volume = int(df["Volume"].tail(5).mean())

    volume_score = min(
        max(int((volume / avg_volume) * 50), 10),
        95
    )

    # 상승 점수
    price_position = (
        (current_price - low_price)
        / max((high_price - low_price), 1)
    ) * 100

    up_score = min(
        max(int(price_position * 0.7 + change_percent * 5), 5),
        98
    )

    # 추천 포지션
    if up_score >= 70 and change_percent > 1:
        position = "🔥 상승 우세"
        pos_color = "#FF4B4B"

    elif up_score <= 35:
        position = "⚠ 약세 구간"
        pos_color = "#1F77B4"

    else:
        position = "👀 관망 구간"
        pos_color = "#FFA500"

    # AI 조언
    if position == "🔥 상승 우세":
        ai_advice = (
            "현재 거래량이 평균 대비 증가하며 "
            "단기 상승 흐름이 유지되고 있습니다. "
            "추격 매수보다는 눌림 구간 확인 후 접근이 유리합니다."
        )

    elif position == "⚠ 약세 구간":
        ai_advice = (
            "단기 하락 압력이 확인됩니다. "
            "추가 진입보다는 지지선 확인이 우선입니다."
        )

    else:
        ai_advice = (
            "현재 방향성이 강하지 않은 박스권 흐름입니다. "
            "거래량 증가 여부를 함께 확인하는 전략이 좋습니다."
        )

    return {
        "current_price": current_price,
        "change": change,
        "change_percent": change_percent,
        "high_price": high_price,
        "low_price": low_price,
        "volume": volume,
        "volume_score": volume_score,
        "up_score": up_score,
        "position": position,
        "pos_color": pos_color,
        "ai_advice": ai_advice
    }

# ==========================================
# 6. 입구 화면
# ==========================================
if st.session_state.page == "intro":

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown(
        "<h1 style='text-align:center; font-size:90px;'>🔥</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<h1 style='text-align:center; color:#FFD700;'>주식주신 PRO</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center; color:gray;'>"
        "실시간 데이터 기반 AI 주식 분석"
        "</p>",
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,2,1])

    with c2:
        if st.button("📊 분석 시작", use_container_width=True):
            st.session_state.page = "analysis"
            st.rerun()

# ==========================================
# 7. 분석 화면
# ==========================================
elif st.session_state.page == "analysis":

    col1, col2 = st.columns([1,5])

    with col1:
        if st.button("🏠 홈"):
            st.session_state.page = "intro"
            st.rerun()

    with col2:
        st.markdown(
            "<h2 style='color:#FFD700;'>주식주신PRO 분석실</h2>",
            unsafe_allow_html=True
        )

    st.write("---")

    search_input = st.text_input(
        "🔍 종목명 또는 종목코드 입력",
        placeholder="예: 삼성전자 또는 005930"
    )

    analyze_button = st.button("🚀 실시간 분석")

    # ==========================================
    # 분석 실행
    # ==========================================
    if analyze_button and search_input:

        # 종목명 → 코드 변환
        stock_code = STOCK_MAP.get(
            search_input,
            search_input
        )

        # 코드 검증
        if len(stock_code) != 6:
            st.error("올바른 종목코드를 입력하세요.")
            st.stop()

        # 데이터 가져오기
        try:
            with st.spinner("실시간 데이터를 불러오는 중입니다..."):
                df = get_stock_data(stock_code)

            if df is None:
                st.error("데이터를 불러오지 못했습니다.")
                st.stop()

            result = calculate_signal(df)

        except Exception:
            st.error("실시간 데이터 처리 중 오류가 발생했습니다.")
            st.stop()

        # ==========================================
        # 상단 정보
        # ==========================================
        st.markdown(
            f"### 📈 [{stock_code}] 실시간 분석 결과"
        )

        price_col, position_col = st.columns([2,1])

        with price_col:

            delta_text = (
                f"{result['change']:,} "
                f"({result['change_percent']}%)"
            )

            st.metric(
                label="현재 주가",
                value=f"{result['current_price']:,} 원",
                delta=delta_text
            )

        with position_col:

            st.markdown(
                f"""
                <div style="
                    background-color:{result['pos_color']}33;
                    border:2px solid {result['pos_color']};
                    border-radius:15px;
                    padding:15px;
                    text-align:center;
                    margin-top:10px;
                ">
                    <h3 style="
                        color:{result['pos_color']};
                        margin:0;
                    ">
                        {result['position']}
                    </h3>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("")

        # ==========================================
        # 핵심 분석 지표
        # ==========================================
        st.markdown("#### 📊 핵심 분석 지표")

        analysis_data = {
            "분석 항목": [
                "오늘 최고가",
                "오늘 최저가",
                "거래량",
                "거래량 집중도",
                "상승 가능성"
            ],
            "실시간 결과": [
                f"{result['high_price']:,} 원",
                f"{result['low_price']:,} 원",
                f"{result['volume']:,} 주",
                f"{result['volume_score']} %",
                f"{result['up_score']} %"
            ]
        }

        table_df = pd.DataFrame(analysis_data)

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True
        )

        st.write("")

        # ==========================================
        # 차트
        # ==========================================
        st.markdown("#### 📉 최근 주가 흐름")

        chart_df = df[["Close"]].rename(
            columns={"Close":"종가"}
        )

        st.line_chart(chart_df)

        st.write("")

        # ==========================================
        # AI 코멘트
        # ==========================================
        st.markdown("#### 💡 AI 분석 코멘트")

        st.info(result["ai_advice"])

        st.write("")

        # ==========================================
        # 뉴스 섹션
        # ==========================================
        st.markdown("#### 📰 시장 체크 포인트")

        st.markdown(
            f"• [{stock_code}] 최근 거래량 변동성 확대 여부 확인"
        )

        st.markdown(
            f"• 단기 지지선: {result['low_price']:,} 원"
        )

        st.markdown(
            f"• 단기 저항선: {result['high_price']:,} 원"
        )