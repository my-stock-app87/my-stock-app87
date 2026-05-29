import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from scanner.run_scan import run_ai_scan

st.set_page_config(page_title="주식주신 AI", layout="wide")

st.title("🔥 주식주신 AI V2")
st.caption("AI 추천 · 추세강도 · 분할매수 · 분할매도 · 가격대별 추천")


@st.cache_data(ttl=3600)
def load_stock_list():
    try:
        krx = fdr.StockListing("KRX")
        return krx[["Code", "Name"]].dropna()
    except Exception:
        return pd.DataFrame({
            "Code": ["005930", "000660", "035420", "035720", "005380", "078130", "049080"],
            "Name": ["삼성전자", "SK하이닉스", "NAVER", "카카오", "현대차", "국일제지", "기가레인"]
        })


def show_ai_card(row):
    st.markdown("---")
    st.subheader(f"{row['종목명']} ({row['현재가']:,}원)")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("AI점수", row["AI점수"])

    with c2:
        st.metric("추세강도", row["추세강도"])

    with c3:
        st.metric("거래량배수", row["거래량배수"])

    st.success(f"추천이유 : {row['추천이유']}")
    st.info(f"신호 : {row['신호']} | 판단 : {row['판단']}")

    c4, c5 = st.columns(2)

    with c4:
        st.write("### 🛒 분할매수")
        st.write(f"1차매수 40% : {row['1차매수(40%)']:,}원")
        st.write(f"2차매수 30% : {row['2차매수(30%)']:,}원")
        st.write(f"3차매수 30% : {row['3차매수(30%)']:,}원")
        st.write(f"예상평균단가 : {row['예상평균단가']:,}원")

    with c5:
        st.write("### 💰 분할매도")
        st.write(f"1차매도 20% : {row['1차매도(20%)']:,}원")
        st.write(f"2차매도 30% : {row['2차매도(30%)']:,}원")
        st.write(f"3차매도 50% : {row['3차매도(50%)']:,}원")
        st.write(f"손절가 : {row['손절가']:,}원")


krx = load_stock_list()

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


if menu == "종목검색":

    st.subheader("🔍 종목 검색")

    search_mode = st.radio(
        "검색 방식",
        ["종목명 선택", "종목코드 입력"],
        horizontal=True
    )

    if search_mode == "종목명 선택":
        selected_stock = st.selectbox("종목 선택", krx["Name"].tolist())
        selected_row = krx[krx["Name"] == selected_stock]

        if selected_row.empty:
            st.warning("종목 없음")
            st.stop()

        code = str(selected_row.iloc[0]["Code"])
        stock_name = selected_stock

    else:
        code = st.text_input("종목코드 입력", placeholder="예: 005930")

        if not code:
            st.stop()

        stock_name = code

    try:
        df = fdr.DataReader(code).tail(120)

        if df.empty or len(df) < 25:
            st.warning("데이터 없음")
            st.stop()

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

        trend = 0

        if price > ma5:
            trend += 30

        if price > ma20:
            trend += 30

        if volume_ratio >= 2:
            trend += 20

        if 0 <= change_pct <= 10:
            trend += 20

        trend = min(trend, 100)

        buy1 = price
        buy2 = int(price * 0.97)
        buy3 = int(price * 0.94)

        avg_buy = int((buy1 * 0.4) + (buy2 * 0.3) + (buy3 * 0.3))

        if trend >= 90:
            sell1 = int(price * 1.07)
            sell2 = int(price * 1.15)
            sell3 = int(price * 1.25)

        elif trend >= 75:
            sell1 = int(price * 1.05)
            sell2 = int(price * 1.10)
            sell3 = int(price * 1.15)

        else:
            sell1 = int(price * 1.04)
            sell2 = int(price * 1.08)
            sell3 = int(price * 1.12)

        stop_loss = int(buy3 * 0.97)

        st.metric(
            label=f"{stock_name} 현재가",
            value=f"{price:,}원",
            delta=f"{change_pct:.2f}%"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.info(f"거래량: {volume:,}\n\n거래량배수: {volume_ratio:.2f}배")

        with col2:
            st.success(f"오늘 고가: {int(latest['High']):,}원")

        with col3:
            st.warning(f"오늘 저가: {int(latest['Low']):,}원")

        with col4:
            st.error(f"손절가: {stop_loss:,}원")

        st.subheader("🔥 추세강도")
        st.progress(trend / 100)
        st.write(f"추세강도 : {trend}점")

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("🛒 분할매수")
            st.write(f"1차매수 40% : {buy1:,}원")
            st.write(f"2차매수 30% : {buy2:,}원")
            st.write(f"3차매수 30% : {buy3:,}원")
            st.write(f"예상평균단가 : {avg_buy:,}원")

        with c2:
            st.subheader("💰 분할매도")
            st.write(f"1차매도 20% : {sell1:,}원")
            st.write(f"2차매도 30% : {sell2:,}원")
            st.write(f"3차매도 50% : {sell3:,}원")
            st.write(f"손절가 : {stop_loss:,}원")

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

    except Exception as e:
        st.error(f"종목 데이터를 불러오는 중 오류 발생: {e}")


elif menu == "AI추천종목":

    st.subheader("🤖 AI 추천 종목")

    if st.button("🚀 AI 스캔 시작"):

        result = run_ai_scan()

        if result["top10"].empty:
            st.warning("추천 종목이 없습니다.")
        else:
            for _, row in result["top10"].iterrows():
                show_ai_card(row)


elif menu == "내일급등예상":

    st.subheader("🚀 내일 급등 예상")

    if st.button("🔥 급등 예상 시작"):

        result = run_ai_scan()

        if result["tomorrow_surge"].empty:
            st.warning("내일 급등 예상 종목이 없습니다.")
        else:
            for _, row in result["tomorrow_surge"].iterrows():
                show_ai_card(row)


elif menu == "가격대별추천":

    st.subheader("💰 가격대별 추천")

    if st.button("💎 가격대별 분석"):

        result = run_ai_scan()

        tab1, tab2, tab3, tab4 = st.tabs([
            "1만원 이하",
            "1~3만원",
            "3~5만원",
            "5만원 이상"
        ])

        with tab1:
            st.dataframe(result["under_10000"], use_container_width=True)

        with tab2:
            st.dataframe(result["under_30000"], use_container_width=True)

        with tab3:
            st.dataframe(result["under_50000"], use_container_width=True)

        with tab4:
            st.dataframe(result["over_50000"], use_container_width=True)
