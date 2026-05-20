st.subheader("📊 종목 선택")

selected = st.selectbox("종목", names)

target = code(selected)

if target:
    raw = get_raw_price(target)
    df = ind(raw)

    if not df.empty:

        last = df.iloc[-1]

        # =========================
        # 📱 모바일 카드 UI
        # =========================
        st.markdown("### 📊 현재 상태")

        col1, col2, col3 = st.columns(3)
        col1.metric("현재가", f"{int(last['Close']):,}원")
        col2.metric("RSI", round(last["RSI"], 1))
        col3.metric("세력점수", power(df))

        st.markdown("---")

        # =========================
        # 📈 1주 요약
        # =========================
        week = week_high_low(df)

        st.markdown("### 📈 1주 요약")
        st.metric("최고가", f"{week['1주 최고가']:,}")
        st.metric("최저가", f"{week['1주 최저가']:,}")
        st.write(f"변동폭: {week['변동폭(%)']}%")

        st.markdown("---")

        # =========================
        # 📊 5일치 데이터 (펼치기)
        # =========================
        with st.expander("📊 최근 5일 시세 보기"):
            st.dataframe(df.tail(5)[["Close", "Volume", "RSI"]], use_container_width=True)

        # =========================
        # 🧠 AI 해석
        # =========================
        with st.expander("🧠 AI 분석 해석"):
            st.write(f"""
- 전략: {buy_price(df)[1]}
- 추천 매수가: {buy_price(df)[0]:,}원
- 목표가: {sell_price(df):,}원
            """)

        # =========================
        # 🚀 버튼형 기능
        # =========================
        st.markdown("### 🚀 추가 기능")

        if st.button("🔥 급등주 TOP 10"):
            st.dataframe(scan_market().head(10), use_container_width=True)

        if st.button("📊 테마주 보기"):
            st.dataframe(theme_stocks(), use_container_width=True)