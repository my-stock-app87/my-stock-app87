import streamlit as st

from ui.chart_view import show_chart


def show_stock_card(report):

    with st.container(border=True):

        st.subheader(
            f"📌 {report['종목명']} "
            f"({report['종목코드']})"
        )

        # =========================
        # 실시간 신호
        # =========================

        if report.get("실시간신호"):

            st.error(
                report["실시간신호"]
            )

        # =========================
        # 상단 점수
        # =========================

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "현재가",
                report["현재가"]
            )

        with col2:

            st.metric(
                "AI SCORE",
                report["AI_SCORE"]
            )

        with col3:

            st.metric(
                "상승확률",
                f"{report['확률']}%"
            )

        with col4:

            st.metric(
                "위험도",
                report["위험도"]
            )

        st.divider()

        # =========================
        # 뉴스 테마
        # =========================

        col5, col6, col7 = st.columns(3)

        with col5:

            st.metric(
                "테마",
                report["테마"]
            )

        with col6:

            st.metric(
                "뉴스점수",
                report["뉴스점수"]
            )

        with col7:

            st.metric(
                "테마점수",
                report["테마점수"]
            )

        st.divider()

        # =========================
        # 유사 패턴
        # =========================

        st.info(
            f"과거 유사 패턴: "
            f"{report['유사패턴']}"
        )

        st.divider()

        # =========================
        # 추천 이유
        # =========================

        st.write("### 📊 추천 이유")

        for reason in report["추천이유"]:

            st.write(f"- {reason}")

        st.divider()

        # =========================
        # 예상 가격
        # =========================

        buy_col, sell_col = st.columns(2)

        with buy_col:

            st.success(
                f"예상 매수가: "
                f"{report['예상매수가']}"
            )

        with sell_col:

            st.warning(
                f"예상 매도가: "
                f"{report['예상매도가']}"
            )

        st.divider()

        # =========================
        # 차트 보기
        # =========================

        with st.expander("📈 차트 보기"):

            show_chart(
                report["종목코드"],
                report["종목명"]
            )

        st.markdown("---")