import streamlit as st
from ai_engine import run_analysis

st.set_page_config(page_title="주식분석실 PRO", layout="wide")

st.title("📊 주식분석실 PRO")

code = st.text_input("종목 코드 입력 (예: 005930)")

if st.button("분석하기"):

    if not code:
        st.warning("종목 코드를 입력하세요")
    else:
        result = run_analysis(code)

        st.subheader("📌 분석 결과")

        st.json(result)