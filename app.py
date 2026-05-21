import streamlit as st
import pandas as pd

st.set_page_config(page_title="Stock App", layout="wide")
st.title("📊 주식 앱 (안정 버전)")

# -------------------------
# 샘플 데이터 (무조건 표시)
# -------------------------
data = {
    "Code": ["all"],
    "Name": [""]
}

df = pd.DataFrame(data)

st.success("샘플 데이터 로딩 완료 (안정 모드)")

search = st.text_input("종목 검색")

if search:
    df = df[df["Name"].str.contains(search, case=False)]

st.dataframe(df, use_container_width=True)