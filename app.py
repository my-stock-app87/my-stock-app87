import streamlit as st
import pandas as pd
from ai_engine import run_analysis

st.title("📊 주식 분석실 PRO")

user_input = st.text_input("종목명 / 코드 입력")

btn = st.button("🚀 분석하기")

if btn:

    if not user_input:
        st.error("종목을 입력하세요")
        st.stop()

    # 🔥 AI 브레인 호출
    output = run_analysis(user_input)

    if "error" in output:
        st.error("데이터 없음")
        st.stop()

    result = output["result"]
    df = output["df"]

    st.metric(
        "현재가",
        f"{result['current']:,}원",
        f"{result['change']:,} ({result['change_pct']}%)"
    )

    st.markdown(
        f"<div style='color:{result['color']}; font-size:20px;'>"
        f"{result['position']}</div>",
        unsafe_allow_html=True
    )

    st.subheader("📊 핵심 분석")

    st.write(result)

    st.subheader("📈 최근 5일")
    st.line_chart(df["Close"].tail(5))

    st.subheader("💡 AI 판단")
    st.info(result["ai"])