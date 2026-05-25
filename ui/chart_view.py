import streamlit as st

import FinanceDataReader as fdr

import mplfinance as mpf

import matplotlib.pyplot as plt


def show_chart(stock_code, stock_name):

    try:

        df = fdr.DataReader(stock_code)

        df = df.tail(60)

        # =========================
        # 이동평균선
        # =========================

        mav = (5, 20)

        # =========================
        # 스타일
        # =========================

        style = mpf.make_mpf_style(

            base_mpf_style="charles",

            gridstyle="-"
        )

        # =========================
        # 차트 생성
        # =========================

        fig, axlist = mpf.plot(

            df,

            type="candle",

            volume=True,

            mav=mav,

            style=style,

            figsize=(10, 6),

            returnfig=True
        )

        st.write(
            f"### 📈 {stock_name} 캔들 차트"
        )

        st.pyplot(fig)

    except Exception as e:

        st.error(
            f"차트 오류: {e}"
        )