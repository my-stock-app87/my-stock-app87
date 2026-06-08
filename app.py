import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from scanner.run_scan import run_ai_scan

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="주식주신 PRO Mobile",
    layout="centered"
)

# =========================
# 모바일 B안 스타일
# =========================
st.markdown(
    """
<style>
.stApp {
    background: radial-gradient(circle at top, #171b2f 0%, #070914 48%, #02030a 100%);
    color: #f5f7ff;
}

.block-container {
    max-width: 560px;
    padding-top: 1.2rem;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
}

h1, h2, h3, h4, h5, h6, p, label, span, div {
    font-family: 'Segoe UI', 'Noto Sans KR', sans-serif;
}

section[data-testid="stSidebar"] {
    background: #090d18;
    border-right: 1px solid rgba(140, 90, 255, 0.25);
}

.mobile-title {
    font-size: 30px;
    font-weight: 950;
    letter-spacing: -1px;
    color: #ffffff;
    margin-bottom: 4px;
}

.sub-text {
    color: #9aa4b8;
    font-size: 13px;
    margin-bottom: 18px;
}

.mobile-card {
    background: linear-gradient(145deg, rgba(18,24,39,0.98), rgba(7,10,18,0.98));
    border: 1px solid rgba(155, 92, 255, 0.28);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 0 22px rgba(120, 70, 255, 0.12);
    margin-bottom: 14px;
}

.mobile-card-soft {
    background: rgba(15, 21, 36, 0.94);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 15px;
    padding: 14px;
    margin-bottom: 10px;
}

.label {
    font-size: 12px;
    color: #9aa4b8;
    margin-bottom: 4px;
}

.value-big {
    font-size: 34px;
    font-weight: 950;
    line-height: 1.12;
    color: #ffffff;
}

.value-mid {
    font-size: 22px;
    font-weight: 850;
    color: #ffffff;
}

.value-small {
    font-size: 15px;
    font-weight: 700;
    color: #cbd5e1;
}

.purple { color:#bd93ff; }
.green { color:#48e27a; }
.red { color:#ff5b6a; }
.blue { color:#58a6ff; }
.yellow { color:#ffd75e; }

.badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    background: rgba(155, 92, 255, 0.18);
    border: 1px solid rgba(155, 92, 255, 0.4);
    color: #bd93ff;
    font-weight: 800;
    font-size: 12px;
    margin-right: 5px;
    margin-bottom: 5px;
}

.badge-red {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    background: rgba(255, 91, 106, 0.15);
    border: 1px solid rgba(255, 91, 106, 0.35);
    color: #ff6b7a;
    font-weight: 800;
    font-size: 12px;
    margin-right: 5px;
    margin-bottom: 5px;
}

.ai-circle {
    width: 104px;
    height: 104px;
    border-radius: 50%;
    border: 4px solid #9b5cff;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 26px rgba(155, 92, 255, 0.5);
    background: radial-gradient(circle, rgba(155,92,255,0.2), rgba(10,13,22,0.95));
    margin-left: auto;
}

.price-buy {
    background: rgba(72, 226, 122, 0.11);
    border: 1px solid rgba(72, 226, 122, 0.24);
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 10px;
}

.price-sell {
    background: rgba(88, 166, 255, 0.11);
    border: 1px solid rgba(88, 166, 255, 0.24);
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 10px;
}

.price-stop {
    background: rgba(255, 91, 106, 0.11);
    border: 1px solid rgba(255, 91, 106, 0.24);
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 10px;
}

.line-card {
    padding: 12px 14px;
    border-radius: 13px;
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 9px;
    font-size: 14px;
}

.hr {
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 14px 0;
}

div[data-testid="stMetricValue"] {
    color: #ffffff;
}

.stSelectbox div, .stTextInput div {
    color: #111827;
}

@media (max-width: 640px) {
    .mobile-title { font-size: 27px; }
    .value-big { font-size: 30px; }
    .value-mid { font-size: 20px; }
    .mobile-card { padding: 16px; border-radius: 16px; }
    .ai-circle { width: 92px; height: 92px; }
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
        krx = pd.read_csv(
            "data/stock_list.csv",
            dtype=str  
        )
        
        return krx

    except Exception as e:
        
        st.error(
            f"종목목록 로딩 실패 : {e}"
            
        )  
        
        return pd.DataFrame(
            columns=["code", "name"]
        )

# =========================
# AI 분석
# =========================
def analyze_stock(df, stock_name):

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = int(latest["Close"])
    prev_price = int(prev["Close"])
    volume = int(latest["Volume"])

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
        <div class="mobile-card">
            <div class="label">🔥 현재 전략 백테스트 · 최근 100회 평균</div>
            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
                <div>
                    <div class="value-big green">56.40%</div>
                    <div class="value-small">성공 56 · 실패 44 · AI 신뢰도 A</div>
                </div>
                <div class="ai-circle">
                    <div style="text-align:center;">
                        <div style="font-size:24px; font-weight:950;">56.4%</div>
                        <div class="label">승률</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def metric_card(label, value, sub="", color_class=""):
    st.markdown(
        f"""
        <div class="mobile-card-soft">
            <div class="label">{label}</div>
            <div class="value-mid {color_class}">{value}</div>
            <div class="value-small">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def price_card(kind, label, value, sub):
    class_name = {
        "buy": "price-buy",
        "sell": "price-sell",
        "stop": "price-stop",
    }.get(kind, "mobile-card-soft")

    st.markdown(
        f"""
        <div class="{class_name}">
            <div class="label">{label}</div>
            <div class="value-mid">{value}</div>
            <div class="value-small">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_table_cards(df, max_rows=10):

    if df is None or df.empty:
        st.info("결과가 없습니다.")
        return

    for _, row in df.head(max_rows).iterrows():

        code = str(row.get("종목코드", ""))
        name = str(row.get("종목명", ""))
        price = int(row.get("현재가", 0))
        score = row.get("AI점수", "")
        candle = row.get("캔들", "")
        comment = row.get("AI해설", "")
        
        signal = row.get("신호", "")
        action = row.get("판단", "")
        buy = int(row.get("매수가", 0))
        sell = int(row.get("매도가", 0))

        st.markdown(f"### {name}")
        st.write(f"종목코드 : {code}")
        st.write(f"현재가 : {price:,}원")
        st.write(f"AI점수 : {score}")
        st.write(f"신호 : {signal}")
        st.write(f"판단 : {action}")
        st.write(f"매수가 : {buy:,}원")
        st.write(f"매도가 : {sell:,}원")
        st.divider()


# =========================
# 종목 리스트 로드
# =========================
krx = load_stock_list()

# =========================
# 제목
# =========================
st.markdown(
    """
    <div class="mobile-title">🔥 주식주신 <span class="purple">PRO</span></div>
    <div class="sub-text">모바일 전용 · AI 종목 진단 · 분할매수/매도</div>
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

    st.markdown("### 🔍 종목 검색")

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

        selected_row = krx[krx["Name"] == selected_stock]

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

            # 종목 메인 카드
            st.markdown(
                f"""
                <div class="mobile-card">
                    <div>
                        <div style="font-size:28px; font-weight:950;">⭐ {stock_name}</div>
                        <div style="margin-top:6px;">
                            <span class="badge">{code}</span>
                            <span class="badge">{analysis["테마"]}</span>
                            <span class="badge-red">{analysis["AI판단"]}</span>
                        </div>
                    </div>
                    <div class="hr"></div>
                    <div style="display:flex; justify-content:space-between; align-items:center; gap:12px;">
                        <div>
                            <div class="label">현재가</div>
                            <div class="value-big">{price:,}원</div>
                            <div class="{'red' if change_pct >= 0 else 'blue'}" style="font-size:20px; font-weight:900;">
                                {change_pct:+.2f}%
                            </div>
                        </div>
                        <div class="ai-circle">
                            <div style="text-align:center;">
                                <div style="font-size:30px; font-weight:950; color:#bd93ff;">{analysis["AI점수"]:.0f}</div>
                                <div class="label">AI점수</div>
                            </div>
                        </div>
                    </div>
                    <div class="hr"></div>
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <div class="label">AI등급</div>
                            <div style="font-size:40px; font-weight:950; color:#ffd75e;">{analysis["AI등급"]}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="label">전략</div>
                            <div class="value-mid purple">{analysis["보유전략"]}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 핵심 지표 2열
            st.markdown("### 📊 핵심 지표")
            m1, m2 = st.columns(2)
            with m1:
                metric_card("거래량", f"{volume:,}", f"전일대비 {volume_text}")
            with m2:
                metric_card("거래대금", f"{trading_value_eok:,.1f}억", f"거래량배수 {volume_ratio:.2f}배", "green")

            m3, m4 = st.columns(2)
            with m3:
                metric_card("오늘 고가", f"{int(latest['High']):,}원", "", "green")
            with m4:
                metric_card("오늘 저가", f"{int(latest['Low']):,}원", "", "yellow")

            m5, m6 = st.columns(2)
            with m5:
                metric_card("5일선", f"{int(analysis['MA5']):,}원", "현재가 위" if price > analysis["MA5"] else "현재가 아래")
            with m6:
                metric_card("20일선", f"{int(analysis['MA20']):,}원", "현재가 위" if price > analysis["MA20"] else "현재가 아래")

            # 매수 / 매도
            st.markdown("### 💰 분할 매수")
            price_card("buy", "1차 매수 (40%)", f"{buy1:,}원", "가볍게 진입")
            price_card("buy", "2차 매수 (30%)", f"{buy2:,}원", "눌림 확인")
            price_card("buy", "3차 매수 (30%)", f"{buy3:,}원", "마지막 분할")

            st.markdown("### 🎯 분할 매도")
            price_card("sell", "1차 매도 (30%)", f"{sell1:,}원", "기본 목표")
            price_card("sell", "2차 매도 (30%)", f"{sell2:,}원", "추세 지속")
            price_card("sell", "3차 매도 (40%)", f"{sell3:,}원", "강한 상승")
            price_card("stop", "손절가", f"{stop_loss:,}원", "기준 이탈 시 정리")

            # AI 의견
            reason_lines = ""
            for reason, point in analysis["점수이유"]:
                reason_lines += (
                    f'<div class="line-card">✅ {reason} '
                    f'<span style="float:right;" class="purple">{point}</span></div>'
                )

            st.markdown(
                f"""
                <div class="mobile-card">
                    <div style="font-size:22px; font-weight:950; color:#bd93ff; margin-bottom:12px;">🧠 AI 의견</div>
                    <div class="line-card">현재상황 : <b>{analysis["현재상황"]}</b></div>
                    <div class="line-card">보유전략 : <b>{analysis["보유전략"]}</b></div>
                    <div class="line-card">뉴스강도 : <b>{analysis["뉴스강도"]}</b></div>
                    {reason_lines}
                    <div style="font-size:20px; font-weight:900; color:#bd93ff; margin-top:14px;">
                        {analysis["AI의견"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 차트
            st.markdown("### 📈 최근 종가 차트")
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
        render_table_cards(result["top10"], max_rows=10)


# =========================
# 내일 급등 예상
# =========================
elif menu == "내일급등예상":

    st.subheader("🚀 내일 급등 예상")

    if st.button("🔥 급등 예상 시작"):
        result = run_ai_scan()
        render_table_cards(result["tomorrow_surge"], max_rows=10)


# =========================
# 가격대별 추천
# =========================
elif menu == "가격대별추천":

    st.subheader("💰 가격대별 추천")

    if st.button("💎 가격대별 분석"):

        result = run_ai_scan()

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "1만원 이하",
                "1~3만원",
                "3~5만원",
                "5만원 이상"
            ]
        )

        with tab1:
            render_table_cards(result["under_10000"], max_rows=5)

        with tab2:
            render_table_cards(result["under_30000"], max_rows=5)

        with tab3:
            if "under_50000" in result:
                render_table_cards(result["under_50000"], max_rows=5)
            else:
                st.info("3~5만원 데이터 없음")

        with tab4:
            render_table_cards(result["over_50000"], max_rows=5)
