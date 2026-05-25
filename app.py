import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from scanner.run_scan import run_ai_scan

st.set_page_config(page_title="주식주신 AI", layout="wide")

st.title("🔥 주식주신 AI")
st.caption("AI 기반 종목 분석 · 급등주 탐지 · 가격대별 추천")


@st.cache_data(ttl=3600)
def load_stock_list():
    krx = fdr.StockListing("KRX")
    return krx[["Code", "Name"]].dropna()


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

    high_20 = df["High"].tail(20).max()
    low_20 = df["Low"].tail(20).min()

    position_score = 0 if high_20 == low_20 else ((price - low_20) / (high_20 - low_20)) * 100

    theme = "일반테마"
    if any(word in stock_name for word in ["국일", "상보", "크리스탈"]):
        theme = "그래핀 / 신소재"
    elif any(word in stock_name for word in ["LS", "대한전선", "일진", "광명"]):
        theme = "전력인프라 / 전선"
    elif any(word in stock_name for word in ["기가", "RF", "텔레", "오이"]):
        theme = "통신장비 / 반도체"
    elif any(word in stock_name for word in ["에코", "포스코", "금양"]):
        theme = "2차전지"
    elif any(word in stock_name for word in ["로봇", "두산"]):
        theme = "로봇 / 자동화"

    if volume_ratio >= 3:
        news_power = "강함"
    elif volume_ratio >= 1.5:
        news_power = "보통"
    else:
        news_power = "약함"

    if volume_ratio >= 3 and change_pct > 5:
        situation = "거래량 폭발 + 단기 급등 흐름"
        strategy = "단기"
        opinion = "이미 많이 움직였을 수 있어 추격매수는 조심. 눌림 확인이 좋음."
    elif price > ma5 and price > ma20 and 2 <= change_pct <= 8:
        situation = "이동평균선 위에서 상승 흐름 유지"
        strategy = "단기"
        opinion = "단기 스윙 관점으로 볼 수 있음. 매수가는 현재가보다 낮게 잡는 게 안전."
    elif volume_ratio >= 1.5 and abs(change_pct) <= 3:
        situation = "거래량 증가 + 세력 매집 가능성"
        strategy = "중기"
        opinion = "급등 전 준비 구간일 수 있음. 분할매수 관점으로 지켜볼 만함."
    elif price > ma20 and -3 <= change_pct <= 1:
        situation = "20일선 위 눌림목 구간"
        strategy = "중기"
        opinion = "무리한 추격보다 눌림 후 반등 확인이 중요."
    elif price < ma20:
        situation = "중기 흐름 약함"
        strategy = "관망"
        opinion = "아직 방향성이 약함. 20일선 회복 전까지는 지켜보는 구간."
    else:
        situation = "특별한 강한 신호는 부족"
        strategy = "관망"
        opinion = "거래량과 뉴스가 더 붙는지 확인 필요."

    if position_score <= 30 and price > ma20:
        strategy = "장기"
        opinion = "저점권에서 버티는 모습이면 장기 관찰 가능. 단, 거래량 확인 필요."

    return {
        "테마": theme,
        "뉴스강도": news_power,
        "현재상황": situation,
        "보유전략": strategy,
        "AI의견": opinion,
        "거래량배수": round(volume_ratio, 2),
        "20일 위치": round(position_score, 2)
    }


krx = load_stock_list()

st.sidebar.title("📌 메뉴")
menu = st.sidebar.radio(
    "선택",
    ["종목검색", "AI추천종목", "내일급등예상", "가격대별추천"]
)


if menu == "종목검색":
    st.subheader("🔍 종목 검색")

    selected_stock = st.selectbox("종목을 선택하세요", krx["Name"].tolist())
    selected_row = krx[krx["Name"] == selected_stock]

    if not selected_row.empty:
        code = str(selected_row.iloc[0]["Code"])

        try:
            df = fdr.DataReader(code).tail(120)

            if df.empty or len(df) < 25:
                st.warning("데이터를 불러오지 못했습니다.")
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

                buy_price = int(price * 0.97)
                sell_price = int(price * 1.05)
                stop_loss = int(price * 0.94)

                st.metric(
                    label=f"{selected_stock} 현재가",
                    value=f"{price:,}원",
                    delta=f"{change_pct:.2f}%"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.info(
                        f"""
거래량: {volume:,}

전일대비: {volume_text}

거래량배수: {volume_ratio:.2f}배
"""
                    )

                with col2:
                    st.success(f"오늘 고가: {int(latest['High']):,}원")

                with col3:
                    st.warning(f"오늘 저가: {int(latest['Low']):,}원")

                with col4:
                    st.error(f"손절가: {stop_loss:,}원")

                col5, col6 = st.columns(2)

                with col5:
                    st.success(f"추천 매수가: {buy_price:,}원")

                with col6:
                    st.info(f"추천 매도가: {sell_price:,}원")

                st.subheader("📈 최근 종가 차트")
                st.line_chart(df["Close"])

                st.subheader("📊 최근 데이터")

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

                analysis = analyze_stock(df, selected_stock)

                st.subheader("🧠 AI 종합 분석")

                a1, a2, a3, a4 = st.columns(4)

                with a1:
                    st.info(f"테마: {analysis['테마']}")

                with a2:
                    st.warning(f"뉴스강도: {analysis['뉴스강도']}")

                with a3:
                    st.success(f"보유전략: {analysis['보유전략']}")

                with a4:
                    st.metric("거래량배수", analysis["거래량배수"])

                st.markdown(f"""
                ### 📌 현재상황
                {analysis["현재상황"]}

                ### 💬 AI 의견
                {analysis["AI의견"]}
                """)

        except Exception as e:
            st.error(f"종목 데이터를 불러오는 중 오류 발생: {e}")


elif menu == "AI추천종목":
    st.subheader("🤖 AI 추천 종목 TOP 10")
    st.write("버튼을 누르면 AI가 조건에 맞는 종목을 스캔합니다.")

    if st.button("🚀 AI 스캔 시작"):
        with st.spinner("AI가 종목을 스캔 중입니다..."):
            result = run_ai_scan()

        if result["top10"].empty:
            st.warning("추천 종목이 없습니다.")
        else:
            st.dataframe(result["top10"], use_container_width=True)


elif menu == "내일급등예상":
    st.subheader("🚀 내일 급등 예상 종목")

    if st.button("🔥 급등 예상 스캔 시작"):
        with st.spinner("급등 직전 패턴을 찾는 중입니다..."):
            result = run_ai_scan()

        if result["tomorrow_surge"].empty:
            st.warning("급등 예상 조건에 맞는 종목이 없습니다.")
        else:
            st.dataframe(result["tomorrow_surge"], use_container_width=True)


elif menu == "가격대별추천":
    st.subheader("💰 가격대별 추천 종목")

    if st.button("💎 가격대별 스캔 시작"):
        with st.spinner("가격대별 종목을 분석 중입니다..."):
            result = run_ai_scan()

        tab1, tab2, tab3 = st.tabs(["1만원 이하", "3만원 이하", "5만원 이상"])

        with tab1:
            st.dataframe(result["under_10000"], use_container_width=True)

        with tab2:
            st.dataframe(result["under_30000"], use_container_width=True)

        with tab3:
            st.dataframe(result["over_50000"], use_container_width=True)