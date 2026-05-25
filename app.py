if menu == "종목검색":

    st.subheader("🔍 종목 검색")

    search_mode = st.radio(
        "검색 방식",
        ["종목명 선택", "종목코드 직접입력"],
        horizontal=True
    )

    if search_mode == "종목명 선택":
        selected_stock = st.selectbox(
            "종목을 선택하세요",
            krx["Name"].tolist()
        )

        selected_row = krx[krx["Name"] == selected_stock]

        if selected_row.empty:
            st.warning("종목을 찾지 못했습니다.")
            st.stop()

        code = str(selected_row.iloc[0]["Code"])
        stock_name = selected_stock

    else:
        code = st.text_input(
            "종목코드 6자리를 입력하세요",
            placeholder="예: 005930"
        )

        stock_name = code

        if not code:
            st.info("종목코드를 입력하세요.")
            st.stop()

        code = code.strip()

        if len(code) != 6:
            st.warning("종목코드는 6자리로 입력하세요.")
            st.stop()

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
                label=f"{stock_name} 현재가",
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

            analysis = analyze_stock(df, stock_name)

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