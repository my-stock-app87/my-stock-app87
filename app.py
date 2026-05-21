import streamlit as st
import pandas as pd

st.set_page_config(page_title="Stock App", layout="wide")
st.title("📊 한국 주식 리스트")

@st.cache_data
def load_data():
    try:
        from pykrx.stock import get_market_ticker_list, get_market_ticker_name

        kospi = get_market_ticker_list("KOSPI")
        kosdaq = get_market_ticker_list("KOSDAQ")

        tickers = kospi + kosdaq

        df = pd.DataFrame({
            "Code": tickers,
            "Name": [get_market_ticker_name(t) for t in tickers]
        })

        return df

    except Exception as e:
        return None


df = load_data()

if df is None or df.empty:
    st.error("데이터 로딩 실패")
    st.stop()

st.success(f"총 {len(df)}개 종목")

search = st.text_input("종목 검색")

if search:
    df = df[df["Name"].str.contains(search, case=False, na=False)]

st.dataframe(df, use_container_width=True)