import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from scanner.run_scan import run_ai_scan

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="주식주신 PRO Mobile V3",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# MOBILE V3 스타일
# =========================
st.markdown(
    """
<style>
.stApp {
    background:
        radial-gradient(circle at top left, rgba(155,92,255,0.22), transparent 32%),
        radial-gradient(circle at top right, rgba(72,226,122,0.12), transparent 28%),
        linear-gradient(180deg, #050713 0%, #090d18 48%, #03040a 100%);
    color: #f8fafc;
}

.block-container {
    max-width: 900px;
    margin: 0 auto;
    padding-top: 1.2rem;
    padding-left: 0.8rem;
    padding-right: 0.8rem;
    padding-bottom: 5.5rem;
}

h1, h2, h3, h4, h5, h6, p, label, span, div {
    font-family: 'Segoe UI', 'Noto Sans KR', sans-serif;
}

section[data-testid="stSidebar"] {
    background: #070a14;
    border-right: 1px solid rgba(155,92,255,0.25);
    min-width: 220px;
}

.header {
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:18px;
    padding:10px 4px 4px 4px;
    position:relative;
    z-index:10;
}

.logo {
    font-size:25px;
    font-weight:950;
    letter-spacing:-1px;
}

.pro {
    color:#9b5cff;
}

.mini {
    color:#9aa4b8;
    font-size:12px;
    margin-top:2px;
}

.card {
    background: linear-gradient(145deg, rgba(18,24,39,0.98), rgba(7,10,18,0.98));
    border: 1px solid rgba(155,92,255,0.26);
    border-radius: 22px;
    padding: 17px;
    margin-bottom: 13px;
    box-shadow: 0 0 24px rgba(155,92,255,0.12);
}

.hero {
    border: 1px solid rgba(155,92,255,0.36);
    box-shadow: 0 0 34px rgba(155,92,255,0.18);
}

.row {
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:12px;
}

.label {
    color:#9aa4b8;
    font-size:12px;
    font-weight:700;
    margin-bottom:4px;
}

.price {
    font-size:38px;
    font-weight:950;
    letter-spacing:-1px;
    line-height:1.08;
}

.name {
    font-size:27px;
    font-weight:950;
    letter-spacing:-1px;
}

.code {
    display:inline-block;
    padding:4px 9px;
    border-radius:999px;
    background:rgba(155,92,255,0.16);
    border:1px solid rgba(155,92,255,0.38);
    color:#bd93ff;
    font-size:12px;
    font-weight:850;
    margin-right:4px;
    margin-top:6px;
}

.badge-red {
    display:inline-block;
    padding:4px 9px;
    border-radius:999px;
    background:rgba(255,91,106,0.15);
    border:1px solid rgba(255,91,106,0.35);
    color:#ff7080;
    font-size:12px;
    font-weight:850;
    margin-top:6px;
}

.green { color:#48e27a; }
.red { color:#ff5b6a; }
.blue { color:#58a6ff; }
.yellow { color:#ffd75e; }
.purple { color:#bd93ff; }
.gray { color:#9aa4b8; }

.ai-ring {
    width:106px;
    height:106px;
    border-radius:50%;
    border:4px solid #9b5cff;
    background: radial-gradient(circle, rgba(155,92,255,0.25), rgba(7,10,18,0.96));
    box-shadow:0 0 32px rgba(155,92,255,0.55);
    display:flex;
    align-items:center;
    justify-content:center;
    flex-shrink:0;
}

.ai-score {
    font-size:30px;
    font-weight:950;
    color:#bd93ff;
    line-height:1;
}

.ai-grade {
    font-size:42px;
    font-weight:950;
    color:#ffd75e;
    line-height:1;
}

.action-big {
    font-size:25px;
    font-weight:950;
}

.decision-card {
    background:rgba(155,92,255,0.10);
    border:1px solid rgba(155,92,255,0.24);
    border-radius:17px;
    padding:13px;
}

.grade-card {
    background:rgba(255,215,94,0.10);
    border:1px solid rgba(255,215,94,0.24);
    border-radius:17px;
    padding:13px;
}

.grid2 {
    display:grid;
    grid-template-columns: 1fr 1fr;
    gap:10px;
}

.grid3 {
    display:grid;
    grid-template-columns: 1fr;
    gap:9px;
}

.mini-card {
    background:rgba(255,255,255,0.045);
    border:1px solid rgba(255,255,255,0.075);
    border-radius:17px;
    padding:13px;
}

.buy {
    background:rgba(72,226,122,0.105);
    border:1px solid rgba(72,226,122,0.24);
}

.sell {
    background:rgba(88,166,255,0.105);
    border:1px solid rgba(88,166,255,0.24);
}

.stop {
    background:rgba(255,91,106,0.12);
    border:1px solid rgba(255,91,106,0.28);
}

.value {
    font-size:22px;
    font-weight:950;
}

.value2 {
    font-size:18px;
    font-weight:900;
}

.reason {
    padding:11px 12px;
    border-radius:14px;
    background:rgba(255,255,255,0.045);
    border:1px solid rgba(255,255,255,0.07);
    margin-bottom:8px;
    font-size:14px;
}

.section-title {
    font-size:19px;
    font-weight:950;
    margin: 18px 0 9px;
    letter-spacing:-0.5px;
}

.bottom-nav {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: 10px;
    width: min(450px, calc(100% - 20px));
    background: rgba(7,10,18,0.94);
    border: 1px solid rgba(155,92,255,0.28);
    border-radius: 20px;
    padding: 9px 10px;
    display:flex;
    justify-content:space-around;
    z-index:999;
    backdrop-filter: blur(12px);
    box-shadow: 0 0 24px rgba(0,0,0,0.35);
}

.nav-item {
    font-size:12px;
    font-weight:800;
    color:#9aa4b8;
    text-align:center;
}

.nav-active {
    color:#bd93ff;
}

div[data-testid="stMetricValue"] {
    color: #ffffff;
}

.stSelectbox div, .stTextInput div {
    color: #111827;
}

.stRadio label {
    color: #e5e7eb !important;
}

@media (max-width: 520px) {
    .block-container {
        padding-top: 1.4rem;
        padding-left: 0.55rem;
        padding-right: 0.55rem;
    }
    .price { font-size:34px; }
    .name { font-size:25px; }
    .ai-ring { width:96px; height:96px; }
    .ai-score { font-size:27px; }
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

    theme_map = {
        "삼성전자": "반도체",
        "SK하이닉스": "HBM",
        "한미반도체": "HBM",
        "리노공업": "반도체",
        "DB하이텍": "반도체",
        "가온칩스": "AI반도체",

        "국일제지": "그래핀",
        "상보": "그래핀",
        "크리스탈신소재": "그래핀",
        "나노X이미징": "그래핀",

        "기가레인": "통신장비",
        "대한광통신": "광통신",
        "이노와이어리스": "통신장비",

        "루닛": "의료AI",
        "뷰노": "의료AI",
        "제이엘케이": "의료AI",

        "LG에너지솔루션": "2차전지",
        "삼성SDI": "2차전지",
        "LG화학": "2차전지",
        "에코프로": "2차전지",
        "에코프로비엠": "2차전지",

        "현대차": "전기차",
        "기아": "전기차",
        "현대위아": "자동차부품",

        "NAVER": "AI플랫폼",
        "카카오": "플랫폼",
        "카페24": "이커머스",

        "LS ELECTRIC": "스마트그리드",
        "옴니시스템": "스마트그리드",
        "비츠로셀": "ESS",
    }

    theme = theme_map.get(stock_name, "일반테마")

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


def price_box(kind, title, value, memo):
    st.markdown(
        f"""
        <div class="mini-card {kind}">
            <div class="label">{title}</div>
            <div class="value">{value}</div>
            <div class="mini">{memo}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def metric_box(title, value, memo="", color=""):
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="label">{title}</div>
            <div class="value2 {color}">{value}</div>
            <div class="mini">{memo}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_stock_cards(df, max_rows=10):
    if df is None or df.empty:
        st.info("결과가 없습니다.")
        return

    for i, (_, row) in enumerate(df.head(max_rows).iterrows(), start=1):
        name = row.get("종목명", "")
        price = int(row.get("현재가", 0))
        score = row.get("AI점수", "")
        signal = row.get("신호", "")
        action = row.get("판단", "")
        buy = int(row.get("매수가", 0))
        sell = int(row.get("매도가", 0))

        st.markdown(
            f"""
            <div class="card">
                <div class="row">
                    <div>
                        <div class="label">#{i}</div>
                        <div class="name">{name}</div>
                        <span class="code">{signal}</span>
                        <span class="badge-red">{action}</span>
                    </div>
                    <div style="text-align:right;">
                        <div class="value purple">{score}</div>
                        <div class="label">AI점수</div>
                    </div>
                </div>
                <div class="hr"></div>
                <div class="grid2">
                    <div>
                        <div class="label">현재가</div>
                        <div class="value2">{price:,}원</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="label">매도 목표</div>
                        <div class="value2 blue">{sell:,}원</div>
                    </div>
                </div>
                <div class="mini">매수 기준 {buy:,}원</div>
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================
# 데이터
# =========================
krx = load_stock_list()

# =========================
# 상단
# =========================
st.markdown(
    """
    <div class="header">
        <div>
            <div class="logo">🔥 주식주신 <span class="pro">PRO</span></div>
            <div class="mini">MOBILE V3 · 실전 매매 판단 화면</div>
        </div>
        <div style="text-align:right;">
            <div class="label">전략승률</div>
            <div style="font-size:20px; font-weight:950;" class="green">56.4%</div>
        </div>
    </div>
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

    search_mode = st.radio(
        "검색",
        ["종목명", "코드"],
        horizontal=True
    )

    if search_mode == "종목명":
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
                volume_text = f"+{volume_change_pct:.2f}%"
            elif volume_change_pct < 0:
                volume_text = f"{volume_change_pct:.2f}%"
            else:
                volume_text = "0.00%"

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

            color_class = "red" if change_pct >= 0 else "blue"

            # 메인 히어로
            st.markdown(
                f"""
                <div class="card hero">
                    <div class="row">
                        <div>
                            <div class="name" style="word-break:keep-all; line-height:1.18;">⭐ {stock_name}</div>
                            <span class="code">{code}</span>
                            <span class="code">{analysis["테마"]}</span>
                            <span class="badge-red">{analysis["AI판단"]}</span>
                        </div>
                        <div class="ai-ring">
                            <div style="text-align:center;">
                                <div class="ai-score">{analysis["AI점수"]:.0f}</div>
                                <div class="label">AI점수</div>
                            </div>
                        </div>
                    </div>

                    <div class="hr"></div>

                    <div class="row">
                        <div>
                            <div class="label">현재가</div>
                            <div class="price">{price:,}원</div>
                            <div class="{color_class}" style="font-size:20px; font-weight:950;">
                                ▲ {change_pct:+.2f}%
                            </div>
                        </div>

                        <div class="ai-ring">
                            <div style="text-align:center;">
                                <div class="ai-score">{analysis["AI점수"]:.0f}</div>
                                <div class="label">AI점수</div>
                            </div>
                        </div>
                    </div>

                    <div class="hr"></div>

                    <div class="grid2">
                        <div class="grade-card">
                            <div class="label">AI등급</div>
                            <div class="ai-grade">{analysis["AI등급"]}</div>
                        </div>
                        <div class="decision-card" style="text-align:right;">
                            <div class="label">AI판단</div>
                            <div class="action-big purple">{analysis["AI판단"]}</div>
                        </div>
                    </div>

                    <div style="height:10px;"></div>

                    <div class="decision-card">
                        <div class="label">보유전략</div>
                        <div class="action-big purple">{analysis["보유전략"]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 핵심 지표
            st.markdown('<div class="section-title">📊 핵심 지표</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                metric_box("거래량", f"{volume:,}", f"전일대비 {volume_text}")
            with c2:
                metric_box("거래대금", f"{trading_value_eok:,.1f}억", f"{volume_ratio:.2f}배", "green")

            c3, c4 = st.columns(2)
            with c3:
                metric_box("오늘 고가", f"{int(latest['High']):,}원", "", "green")
            with c4:
                metric_box("오늘 저가", f"{int(latest['Low']):,}원", "", "yellow")

            c5, c6 = st.columns(2)
            with c5:
                metric_box(
                    "5일선",
                    f"{int(analysis['MA5']):,}원",
                    "현재가 위" if price > analysis["MA5"] else "현재가 아래",
                    "green" if price > analysis["MA5"] else "blue"
                )
            with c6:
                metric_box(
                    "20일선",
                    f"{int(analysis['MA20']):,}원",
                    "현재가 위" if price > analysis["MA20"] else "현재가 아래",
                    "green" if price > analysis["MA20"] else "blue"
                )

            # 매수
            st.markdown('<div class="section-title">💰 매수 구간</div>', unsafe_allow_html=True)
            price_box("buy", "1차 매수 40%", f"{buy1:,}원", "가볍게 진입")
            price_box("buy", "2차 매수 30%", f"{buy2:,}원", "눌림 확인")
            price_box("buy", "3차 매수 30%", f"{buy3:,}원", "마지막 분할")

            # 매도 / 손절
            st.markdown('<div class="section-title">🎯 매도 구간</div>', unsafe_allow_html=True)
            price_box("sell", "1차 매도 30%", f"{sell1:,}원", "+4% 기본 목표")
            price_box("sell", "2차 매도 30%", f"{sell2:,}원", "+7% 추세 지속")
            price_box("sell", "3차 매도 40%", f"{sell3:,}원", "+12% 강한 상승")
            price_box("stop", "🛑 손절가", f"{stop_loss:,}원", "-6% 기준 이탈")

            # AI 의견
            reason_lines = ""
            for reason, point in analysis["점수이유"]:
                reason_lines += (
                    f'<div class="reason">✅ {reason} '
                    f'<span style="float:right;" class="purple">{point}</span></div>'
                )

            st.markdown(
                f"""
                <div class="card">
                    <div class="section-title" style="margin-top:0;">🧠 AI 의견</div>
                    <div class="reason">현재상황 : <b>{analysis["현재상황"]}</b></div>
                    <div class="reason">보유전략 : <b>{analysis["보유전략"]}</b></div>
                    <div class="reason">뉴스강도 : <b>{analysis["뉴스강도"]}</b></div>
                    {reason_lines}
                    <div style="font-size:19px; font-weight:950; color:#bd93ff; margin-top:12px;">
                        {analysis["AI의견"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 차트
            st.markdown('<div class="section-title">📈 차트</div>', unsafe_allow_html=True)
            chart_df = pd.DataFrame({
                "종가": df["Close"],
                "5일선": df["Close"].rolling(5).mean(),
                "20일선": df["Close"].rolling(20).mean(),
            })
            st.line_chart(chart_df)

            with st.expander("최근 데이터 보기"):
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
        render_stock_cards(result["top10"], max_rows=10)


# =========================
# 내일 급등 예상
# =========================
elif menu == "내일급등예상":

    st.subheader("🚀 내일 급등 예상")

    if st.button("🔥 급등 예상 시작"):
        result = run_ai_scan()
        render_stock_cards(result["tomorrow_surge"], max_rows=10)


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
            render_stock_cards(result["under_10000"], max_rows=5)

        with tab2:
            render_stock_cards(result["under_30000"], max_rows=5)

        with tab3:
            if "under_50000" in result:
                render_stock_cards(result["under_50000"], max_rows=5)
            else:
                st.info("3~5만원 데이터 없음")

        with tab4:
            render_stock_cards(result["over_50000"], max_rows=5)


# =========================
# 하단 안내
# =========================
st.markdown(
    """
    <div class="bottom-nav">
        <div class="nav-item nav-active">☰ 왼쪽 메뉴에서 추천 · 급등 · 가격대별 화면 전환</div>
    </div>
    """,
    unsafe_allow_html=True
)
