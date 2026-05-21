
elif st.session_state.page == "analysis":

    if st.button("⬅️ 메인으로"):
        st.session_state.page = ""

    st.markdown("## 🧠 AI 종합분석")

    name = st.selectbox("종목 선택", names)

    c = code(name)

    df = ind(get_price(c))

    if not df.empty:

        l = df.iloc[-1]
        p = df.iloc[-2]

        # =====================================================
        # 현재가
        # =====================================================
        price = int(l["Close"])
        diff = price - int(p["Close"])
        pct = (diff / int(p["Close"])) * 100

        # =====================================================
        # 추천 매수 / 매도
        # =====================================================
        buy_price = int(l["Close"] * 0.98)
        sell_price = int(l["Close"] * 1.04)

        # =====================================================
        # 세력 점수
        # =====================================================
        whale = round(l["Whale"], 1)

        # =====================================================
        # 거래량 변화 (%)
        # =====================================================
        today_volume = int(l["Volume"])
        yesterday_volume = int(p["Volume"])

        volume_pct = (
            (today_volume - yesterday_volume)
            / (yesterday_volume + 1e-10)
        ) * 100

        if volume_pct > 10:
            volume_text = "🔥 거래량 급증 (세력 유입)"
            volume_color = "red"

        elif volume_pct > 0:
            volume_text = "📈 거래량 증가"
            volume_color = "red"

        elif volume_pct < -10:
            volume_text = "⚠️ 거래량 급감"
            volume_color = "blue"

        else:
            volume_text = "📉 거래량 감소"
            volume_color = "blue"

        # =====================================================
        # 상승/하락 확률
        # =====================================================
        up_prob = np.clip(
            (
                l["Whale"] * 0.5 +
                l["Strength"] * 0.3 +
                l["Pred"] * 2
            ),
            0,
            95
        )

        down_prob = 100 - up_prob

        risk = np.clip(down_prob, 5, 95)

        if up_prob >= 55:
            today_predict = "📈 상승 예상"
            predict_color = "red"
            predict_prob = up_prob
        else:
            today_predict = "📉 하락 예상"
            predict_color = "blue"
            predict_prob = down_prob

        # =====================================================
        # AI 분석 멘트
        # =====================================================
        if whale >= 75:
            ai_text = "🚀 강한 세력 매집 (단기 급등 가능성)"
        elif whale >= 55:
            ai_text = "📊 세력 유입 진행 (방향성 확인)"
        elif l["RSI"] < 30:
            ai_text = "🎯 과매도 구간 (반등 가능성)"
        else:
            ai_text = "⚠️ 뚜렷한 방향 없음"

        # =====================================================
        # 현재가
        # =====================================================
        st.metric(
            "현재가",
            f"{price:,}원",
            f"{pct:+.2f}%"
        )

        # =====================================================
        # 핵심 정보 카드
        # =====================================================
        st.markdown(f"""
        <div class='card'>

        📈 오늘 최고가 :
        <b style='color:red;'>{int(l['High']):,}원</b>

        <br><br>

        📉 오늘 최저가 :
        <b style='color:blue;'>{int(l['Low']):,}원</b>

        <br><br>

        🟢 추천 매수가 :
        <b>{buy_price:,}원</b>

        <br><br>

        🔴 추천 매도가 :
        <b>{sell_price:,}원</b>

        <br><br>

        🐳 세력 점수 :
        <b>{whale:.1f}%</b>

        <br><br>

        📊 거래량 :
        <b>{today_volume:,}주</b>

        <br>

        <b style='color:{volume_color};'>
        {volume_text} ({volume_pct:+.1f}%)
        </b>

        <br><br>

        📊 상승/하락 판단 :
        <b style='color:{predict_color}; font-size:18px;'>
        {today_predict} ({predict_prob:.1f}%)
        </b>

        <br><br>

        ⚠️ 리스크 :
        <b>{risk:.1f}%</b>

        </div>
        """, unsafe_allow_html=True)

        # =====================================================
        # 매수 / 매도 판단
        # =====================================================
        if whale >= 65 and l["RSI"] < 65:
            st.success("🟥 지금 매수해")

        elif l["RSI"] > 75 or whale < 35:
            st.error("🟦 지금 매도해")

        else:
            st.info("⚪ 관망 구간")

        # =====================================================
        # AI 분석
        # =====================================================
        st.markdown("### 🤖 AI 분석")

        st.markdown(f"""
        <div class='card'>

        {ai_text}

        <br><br>

        🔥 변동성 :
        <b>{l['Pred']:.1f}%</b>

        <br><br>

        📊 RSI :
        <b>{l['RSI']:.1f}</b>

        </div>
        """, unsafe_allow_html=True)

        # =====================================================
        # 뉴스
        # =====================================================
        st.markdown("### 📰 뉴스")

        news = get_news(name)

        for n in news:
            st.markdown(f"• [{n['title']}]({n['link']})")