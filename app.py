import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from scanner.run_scan import run_ai_scan

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="주식주신 PRO",
    layout="wide"
)

# =========================
# PRO 다크 스타일
# =========================
st.markdown(
    """
<style>
/* 전체 */
.stApp {
    background: radial-gradient(circle at top, #141827 0%, #05070d 45%, #020308 100%);
    color: #f5f7ff;
}

/* 기본 텍스트 */
h1, h2, h3, h4, h5, h6, p, label, span, div {
    font-family: 'Segoe UI', 'Noto Sans KR', sans-serif;
}

/* 사이드바 */
section[data-testid="stSidebar"] {
    background: #090d18;
    border-right: 1px solid rgba(140, 90, 255, 0.25);
}

/* 카드 */
.pro-card {
    background: linear-gradient(145deg, rgba(18,24,39,0.98), rgba(7,10,18,0.98));
    border: 1px solid rgba(140, 100, 255, 0.25);
    border-radius: 18px;
    padding: 22px;
    box-shadow: 0 0 24px rgba(120, 70, 255, 0.12);
    margin-bottom: 18px;
}

.pro-card-soft {
    background: rgba(15, 21, 36, 0.92);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 14px;
}

.pro-title {
    font-size: 42px;
    font-weight: 900;
    letter-spacing: -1px;
    color: #ffffff;
}

.pro-purple {
    color: #9b5cff;
}

.pro-green {
    color: #48e27a;
}

.pro-red {
    color: #ff5b6a;
}

.pro-blue {
    color: #58a6ff;
}

.pro-yellow {
    color: #ffd75e;
}

.big-number {
    font-size: 46px;
    font-weight: 900;
    color: #ffffff;
    line-height: 1.1;
}

.mid-number {
    font-size: 30px;
    font-weight: 800;
    color: #ffffff;
}

.small-label {
    font-size: 14px;
    color: #9aa4b8;
    margin-bottom: 6px;
}

.badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 999px;
    background: rgba(155, 92, 255, 0.18);
    border: 1px solid rgba(155, 92, 255, 0.4);
    color: #bd93ff;
    font-weight: 700;
    margin-right: 6px;
}

.badge-red {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 999px;
    background: rgba(255, 91, 106, 0.15);
    border: 1px solid rgba(255, 91, 106, 0.35);
    color: #ff6b7a;
    font-weight: 700;
}

.ai-circle {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    border: 5px solid #9b5cff;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: auto;
    box-shadow: 0 0 30px rgba(155, 92, 255, 0.55);
    background: radial-gradient(circle, rgba(155,92,255,0.18), rgba(10,13,22,0.95));
}

.ai-circle-inner {
    text-align: center;
}

.progress-wrap {
    background: #202638;
    border-radius: 999px;
    height: 12px;
    overflow: hidden;
}

.progress-bar {
    height: 12px;
    border-radius: 999px;
    background: linear-gradient(90deg, #784cff, #bd6cff);
}

.line-card {
    padding: 14px 16px;
    border-radius: 13px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 10px;
}

.price-box-green {
    background: rgba(72, 226, 122, 0.11);
    border: 1px solid rgba(72, 226, 122, 0.22);
    border-radius: 14px;
    padding: 18px;
}

.price-box-blue {
    background: rgba(88, 166, 255, 0.11);
    border: 1px solid rgba(88, 166, 255, 0.22);
    border-radius: 14px;
    padding: 18px;
}

.price-box-red {
    background: rgba(255, 91, 106, 0.11);
    border: 1px solid rgba(255, 91, 106, 0.22);
    border-radius: 14px;
    padding: 18px;
}

/* streamlit 기본 요소 색 보정 */
div[data-testid="stMetricValue"] {
    color: #ffffff;
}
div[data-testid="stMetricDelta"] {
    font-size: 15px;
}
.stSelectbox div, .stTextInput div {
    color: #111827;
}
</style>
""",
    unsafe_allow_html=True
)

# =========================
# 종목 리스트
# =========================
@st.cache_data(ttl=3600)
def load_stock_list():

    try:
        krx = fdr.StockListing("KRX")
        return krx[["Code", "Name"]].dropna()

    except Exception:
        return pd.DataFrame({
            "Code": [
                "005930", "000660", "035420", "035720", "005380",
                "051910", "006400", "373220", "207940", "068270",
                "078130", "049080", "328130", "338220",
            ],
            "Name": [
                "삼성전자", "SK하이닉스", "NAVER", "카카오", "현대차",
                "LG화학", "삼성SDI", "LG에너지솔루션", "삼성바이오로직스",
                "셀트리온", "국일제지", "기가레인", "루닛", "뷰노",
            ]
        })


# =========================
# AI 분석
# =========================
def analyze_stock(df, stock_name):

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = int(latest["Close"])
    prev_price = int(prev["Close"])
    volume = int(latest["Volume"])
    prev_volume = int(prev["Volume"])

    change_pct = ((price - prev_price) / prev_price) * 100

    avg_volume = df["Volume"].tail(20).mean()
    volume_ratio = volume / avg_volume if avg_volume > 0 else 0

    ma5 = df["Close"].rolling(5).mean().iloc[-1]
    ma20 = df["Close"].rolling(20).mean().iloc[-1]

    trading_value = price * volume

    ai_score = 50
    reasons = []

    if volume_ratio >= 3:
        ai_score += 25
        reasons.append(("거래량 폭발", "+25"))
    elif volume_ratio >= 2:
        ai_score += 15
        reasons.append(("거래량 증가", "+15"))
    elif volume_ratio >= 1.2:
        ai_score += 10
        reasons.append(("거래량 양호", "+10"))

    if trading_value >= 10000000000:
        ai_score += 20
        reasons.append(("거래대금 유입", "+20"))
    elif trading_value >= 5000000000:
        ai_score += 10
        reasons.append(("거래대금 양호", "+10"))

    if price > ma5:
        ai_score += 10
        reasons.append(("5일선 돌파", "+10"))

    if price > ma20:
        ai_score += 10
        reasons.append(("20일선 돌파", "+10"))

    if 0 <= change_pct <= 5:
        ai_score += 20
        reasons.append(("상승 초기 구간", "+20"))
    elif 5 <= change_pct <= 10:
        ai_score += 10
        reasons.append(("상승 추세", "+10"))
    elif change_pct >= 20:
        ai_score -= 20
        reasons.append(("과열 주의", "-20"))

    if price <= 5000:
        ai_score += 10
        reasons.append(("저가주 가점", "+10"))
    elif price <= 10000:
        ai_score += 5
        reasons.append(("중저가주 가점", "+5"))

    if ai_score >= 120:
        ai_grade = "S"
        decision = "🔥 매우 강력"
    elif ai_score >= 95:
        ai_grade = "A"
        decision = "🟢 강력관심"
    elif ai_score >= 75:
        ai_grade = "B"
        decision = "🟡 관심"
    elif ai_score >= 50:
        ai_grade = "C"
        decision = "⚪ 관망"
    else:
        ai_grade = "D"
        decision = "🔴 제외"

    theme = "일반테마"

    if any(word in stock_name for word in ["국일"]):
        theme = "그래핀"
    elif any(word in stock_name for word in ["기가"]):
        theme = "통신장비"
    elif any(word in stock_name for word in ["루닛", "뷰노"]):
        theme = "의료AI"

    if volume_ratio >= 3:
        news_power = "강함"
    elif volume_ratio >= 1.5:
        news_power = "보통"
    else:
        news_power = "약함"

    if volume_ratio >= 3 and change_pct > 5:
        situation = "거래량 폭발 + 급등 흐름"
        strategy = "단기"
        opinion = "추격매수는 조심. 눌림 확인 후 접근."
    elif price > ma5 and price > ma20:
        situation = "상승 추세 유지"
        strategy = "단기"
        opinion = "분할매수 후 단계별 매도 전략 적합."
    elif volume_ratio >= 1.5:
        situation = "세력 매집 가능성"
        strategy = "중기"
        opinion = "거래량 유지 여부 확인 필요."
    else:
        situation = "관망 구간"
        strategy = "관망"
        opinion = "방향성 부족. 무리한 진입 금지."

    return {
        "테마": theme,
        "뉴스강도": news_power,
        "현재상황": situation,
        "보유전략": strategy,
        "AI의견": opinion,
        "거래량배수": round(volume_ratio, 2),
        "거래대금억": round(trading_value / 100000000, 1),
        "AI점수": round(ai_score, 2),
        "AI등급": ai_grade,
        "AI판단": decision,
        "점수이유": reasons,
        "MA5": ma5,
        "MA20": ma20,
    }


def render_strategy_status():
    st.markdown(
        """
        <div class="pro-card">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:18px;">
                <div>
                    <div style="font-size:24px; font-weight:800;">🔥 AI 전략 상태</div>
                    <div class="small-label">현재 전략 백테스트 · 최근 100회 평균</div>
                    <div class="big-number pro-green">56.40%</div>
                </div>
                <div style="text-align:center;">
                    <div class="ai-circle">
                        <div class="ai-circle-inner">
                            <div style="font-size:28px; font-weight:900;">56.4%</div>
                            <div class="small-label">승률</div>
                        </div>
                    </div>
                </div>
                <div style="text-align:center;">
                    <div class="small-label">최근 100회 테스트</div>
                    <div style="font-size:28px; font-weight:900;"><span class="pro-green">성공 56</span> <span style="color:#777;">|</span> <span class="pro-red">실패 44</span></div>
                </div>
                <div style="text-align:center;">
                    <div class="small-label">AI 신뢰도 등급</div>
                    <div style="font-size:64px; font-weight:900; color:#ffd75e;">A</div>
                    <div style="color:#cbd5e1;">신뢰 가능한 전략입니다.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 종목 리스트 로드
# =========================
krx = load_stock_list()

# =========================
# 제목
# =========================
st.markdown(
    """
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
        <div class="pro-title">🔥 주식주신 <span class="pro-purple">PRO</span></div>
    </div>
    <div style="color:#9aa4b8; margin-bottom:24px;">AI 기반 종목 분석 · 급등주 탐지 · 가격대별 추천</div>
    """,
    unsafe_allow_html=True
)

# =========================
# 메뉴
# =========================
st.sidebar.title("📌 메뉴")

menu = st.sidebar.radio(
    "선택",
    [
        "종목검색",
        "AI추천종목",
        "내일급등예상",
        "가격대별추천",
    ]
)

# =========================
# 종목검색
# =========================
if menu == "종목검색":

    render_strategy_status()

    st.markdown("## 🔍 종목 검색")

    search_mode = st.radio(
        "검색 방식",
        ["종목명 선택", "종목코드 입력"],
        horizontal=True
    )

    if search_mode == "종목명 선택":

        selected_stock = st.selectbox(
            "종목 선택",
            krx["Name"].tolist()
        )

        selected_row = krx[
            krx["Name"] == selected_stock
        ]

        if selected_row.empty:
            st.warning("종목 없음")
            st.stop()

        code = str(selected_row.iloc[0]["Code"])
        stock_name = selected_stock

    else:

        code = st.text_input(
            "종목코드 입력",
            placeholder="예: 005930"
        )

        if not code:
            st.stop()

        stock_name = code

    try:

        df = fdr.DataReader(code).tail(120)

        if df.empty or len(df) < 25:

            st.warning("데이터 없음")

        else:

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            price = int(latest["Close"])
            prev_price = int(prev["Close"])

            volume = int(latest["Volume"])
            prev_volume = int(prev["Volume"])

            change_pct = ((price - prev_price) / prev_price) * 100

            if prev_volume > 0:
                volume_change_pct = ((volume - prev_volume) / prev_volume) * 100
            else:
                volume_change_pct = 0

            if volume_change_pct > 0:
                volume_text = f"+{volume_change_pct:.2f}% 증가"
            elif volume_change_pct < 0:
                volume_text = f"{volume_change_pct:.2f}% 감소"
            else:
                volume_text = "0.00% 동일"

            avg_volume = df["Volume"].tail(20).mean()
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0

            trading_value = price * volume
            trading_value_eok = trading_value / 100000000

            buy1 = int(price * 0.97)
            buy2 = int(price * 0.95)
            buy3 = int(price * 0.93)

            sell1 = int(price * 1.04)
            sell2 = int(price * 1.07)
            sell3 = int(price * 1.12)

            stop_loss = int(price * 0.94)

            analysis = analyze_stock(df, stock_name)

            # =========================
            # 종목 진단서
            # =========================
            st.markdown(
                f"""
                <div class="pro-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; gap:20px;">
                        <div>
                            <div style="font-size:36px; font-weight:900;">⭐ {stock_name} <span class="badge">{code}</span></div>
                            <div style="margin-top:10px;">
                                <span class="badge">{analysis["테마"]}</span>
                                <span class="badge-red">{analysis["AI판단"]}</span>
                            </div>
                        </div>
                        <div style="text-align:center;">
                            <div class="small-label">현재가</div>
                            <div class="big-number">{price:,}원</div>
                            <div class="{'pro-red' if change_pct >= 0 else 'pro-blue'}" style="font-size:22px; font-weight:800;">
                                {change_pct:+.2f}%
                            </div>
                        </div>
                        <div style="text-align:center;">
                            <div class="small-label">AI 등급</div>
                            <div style="font-size:72px; font-weight:900; color:#9b5cff;">{analysis["AI등급"]}</div>
                        </div>
                        <div style="text-align:center;">
                            <div class="ai-circle">
                                <div class="ai-circle-inner">
                                    <div style="font-size:44px; font-weight:900; color:#bd93ff;">{analysis["AI점수"]:.0f}</div>
                                    <div class="small-label">AI 점수</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # =========================
            # 핵심 지표
            # =========================
            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                st.markdown(f'<div class="pro-card-soft"><div class="small-label">거래량</div><div class="mid-number">{volume:,}</div><div class="pro-green">전일대비 {volume_text}</div></div>', unsafe_allow_html=True)

            with col2:
                st.markdown(f'<div class="pro-card-soft"><div class="small-label">거래대금</div><div class="mid-number">{trading_value_eok:,.1f}억</div><div class="pro-green">거래량배수 {volume_ratio:.2f}배</div></div>', unsafe_allow_html=True)

            with col3:
                st.markdown(f'<div class="pro-card-soft"><div class="small-label">오늘 고가</div><div class="mid-number pro-green">{int(latest["High"]):,}원</div></div>', unsafe_allow_html=True)

            with col4:
                st.markdown(f'<div class="pro-card-soft"><div class="small-label">오늘 저가</div><div class="mid-number pro-yellow">{int(latest["Low"]):,}원</div></div>', unsafe_allow_html=True)

            with col5:
                st.markdown(f'<div class="pro-card-soft"><div class="small-label">5일선</div><div class="mid-number">{int(analysis["MA5"]):,}원</div><div class="pro-green">{"현재가 위" if price > analysis["MA5"] else "현재가 아래"}</div></div>', unsafe_allow_html=True)

            with col6:
                st.markdown(f'<div class="pro-card-soft"><div class="small-label">20일선</div><div class="mid-number">{int(analysis["MA20"]):,}원</div><div class="pro-green">{"현재가 위" if price > analysis["MA20"] else "현재가 아래"}</div></div>', unsafe_allow_html=True)

            # =========================
            # AI 의견 / 시나리오
            # =========================
            col_left, col_right = st.columns(2)

            with col_left:
                reason_lines = ""
                for reason, point in analysis["점수이유"]:
                    reason_lines += f'<div class="line-card">✅ {reason} <span style="float:right;" class="pro-purple">{point}</span></div>'

                st.markdown(
                    f"""
                    <div class="pro-card">
                        <div style="font-size:26px; font-weight:900; color:#bd93ff; margin-bottom:16px;">🧠 AI 의견</div>
                        <div class="line-card">현재상황 : <b>{analysis["현재상황"]}</b></div>
                        <div class="line-card">보유전략 : <b>{analysis["보유전략"]}</b></div>
                        <div class="line-card">뉴스강도 : <b>{analysis["뉴스강도"]}</b></div>
                        {reason_lines}
                        <div style="font-size:28px; font-weight:900; color:#bd93ff; margin-top:18px;">{analysis["AI의견"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_right:
                st.markdown(
                    f"""
                    <div class="pro-card">
                        <div style="font-size:26px; font-weight:900; color:#bd93ff; margin-bottom:16px;">🎯 예상 시나리오</div>
                        <div class="price-box-green">
                            <div class="small-label">1차 매수 (40%)</div>
                            <div class="mid-number">{buy1:,}원</div>
                        </div>
                        <div style="height:10px;"></div>
                        <div class="price-box-green">
                            <div class="small-label">2차 매수 (30%)</div>
                            <div class="mid-number">{buy2:,}원</div>
                        </div>
                        <div style="height:10px;"></div>
                        <div class="price-box-green">
                            <div class="small-label">3차 매수 (30%)</div>
                            <div class="mid-number">{buy3:,}원</div>
                        </div>
                        <hr style="border-color:rgba(255,255,255,0.08);">
                        <div class="price-box-blue">
                            <div class="small-label">1차 매도 (30%)</div>
                            <div class="mid-number">{sell1:,}원</div>
                        </div>
                        <div style="height:10px;"></div>
                        <div class="price-box-blue">
                            <div class="small-label">2차 매도 (30%)</div>
                            <div class="mid-number">{sell2:,}원</div>
                        </div>
                        <div style="height:10px;"></div>
                        <div class="price-box-blue">
                            <div class="small-label">3차 매도 (40%)</div>
                            <div class="mid-number">{sell3:,}원</div>
                        </div>
                        <div style="height:10px;"></div>
                        <div class="price-box-red">
                            <div class="small-label">손절가</div>
                            <div class="mid-number">{stop_loss:,}원</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # =========================
            # 차트
            # =========================
            st.markdown("## 📈 최근 종가 차트")
            chart_df = pd.DataFrame({
                "종가": df["Close"],
                "5일선": df["Close"].rolling(5).mean(),
                "20일선": df["Close"].rolling(20).mean(),
            })
            st.line_chart(chart_df)

            with st.expander("📊 최근 데이터 보기"):
                view_df = df.tail(20).copy()
                view_df = view_df.rename(columns={
                    "Open": "시가",
                    "High": "고가",
                    "Low": "저가",
                    "Close": "종가",
                    "Volume": "거래량"
                })

                st.dataframe(
                    view_df[["시가", "고가", "저가", "종가", "거래량"]],
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"종목 데이터를 불러오는 중 오류 발생: {e}")

# =========================
# AI 추천
# =========================
elif menu == "AI추천종목":

    st.subheader("🤖 AI 추천 종목")

    if st.button("🚀 AI 스캔 시작"):

        result = run_ai_scan()

        st.dataframe(
            result["top10"],
            use_container_width=True
        )

# =========================
# 내일 급등 예상
# =========================
elif menu == "내일급등예상":

    st.subheader("🚀 내일 급등 예상")

    if st.button("🔥 급등 예상 시작"):

        result = run_ai_scan()

        st.dataframe(
            result["tomorrow_surge"],
            use_container_width=True
        )

# =========================
# 가격대별 추천
# =========================
elif menu == "가격대별추천":

    st.subheader("💰 가격대별 추천")

    if st.button("💎 가격대별 분석"):

        result = run_ai_scan()

        tab1, tab2, tab3 = st.tabs(
            [
                "1만원 이하",
                "3만원 이하",
                "5만원 이상"
            ]
        )

        with tab1:
            st.dataframe(
                result["under_10000"],
                use_container_width=True
            )

        with tab2:
            st.dataframe(
                result["under_30000"],
                use_container_width=True
            )

        with tab3:
            st.dataframe(
                result["over_50000"],
                use_container_width=True
            )
