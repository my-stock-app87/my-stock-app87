import streamlit as st
import pandas as pd
from ai_engine import run_analysis

st.title("📊 주식분석실 PRO")

# 1️⃣ 종목 입력
code = st.text_input("종목 코드 입력 (예: 005930)")

# 2️⃣ 버튼
if st.button("분석하기"):
    if code == "":
        st.warning("종목 코드를 입력하세요")
    else:
        result = run_analysis(code)

        st.subheader("📌 분석 결과")

        # dict or dataframe 둘 다 대응
        if isinstance(result, pd.DataFrame):
            st.dataframe(result)
        else:
            st.write(result)