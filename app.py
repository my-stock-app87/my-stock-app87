import streamlit as st
from ai_engine import run_analysis

st.title("📊 주식분석실 PRO")

code = st.text_input("종목 코드 입력", value="")

if st.button("분석하기"):

    if code is None or code.strip() == "":
        st.warning("종목 코드를 입력하세요 (예: 005930)")
    else:
        result = run_analysis(code.strip())
        st.write(result)