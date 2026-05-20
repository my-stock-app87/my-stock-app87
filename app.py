# 📱 탭 명칭 직관화 및 스마트폰 가로 폭 스크롤 최적화
tab1, tab2 = st.tabs(["1. 종목분석", "2. 단기 급등추천"])

with tab1:
    df_visual = df_processed.tail(period).copy()
    df_visual.index = pd.to_datetime(df_visual.index).strftime('%m월 %d일')
    
    # 🟢 [최근 5일 압축 요약 뷰] 무한 스크롤 방지용 콤팩트 가로 차트
    df_recent_5 = df_visual.tail(5)
    st.line_chart(df_recent_5[["Close", "Target_Buy", "Target_Sell"]], height=220)
    st.bar_chart(df_recent_5["Volume"], height=130)

    # 🟢 [원터치 전체 보기 토글]: 누르면 숨겨진 이전 장기 데이터가 시원하게 열림
    with st.expander("🔍 터치하여 전체 기간 데이터 더보기", expanded=False):
        st.line_chart(df_visual[["Close", "Target_Buy", "Target_Sell"]])
        st.bar_chart(df_visual["Volume"])
        st.line_chart(df_visual["RSI"])

with tab2:
    st.markdown("### 🚀 내일 급등 수급 유력주")
    rec_data = get_short_term_recommendations(df_stock)
    st.dataframe(rec_data, use_container_width=True, hide_index=True)
