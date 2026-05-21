
st.markdown("## 🧠 종합분석")

try:

    name = st.selectbox("종목 선택", names)
    c = code(name)

    df_raw = get_price(c)

    if df_raw is None or len(df_raw) < 10:
        st.warning("데이터 부족")
        st.stop()

    df = ind(df_raw)

    if df is None or df.empty:
        st.warning("지표 계산 실패")
        st.stop()

    l = df.iloc[-1]
    p = df.iloc[-2]

    price = int(l["Close"])
    pct = (price - p["Close"]) / (p["Close"] + 1e-10) * 100

    buy_price = int(price * 0.98)
    sell_price = int(price * 1.04)

    whale = float(l.get("Whale", 0))
    vol_pct = (l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10) * 100

    up_prob = np.clip(whale * 0.7, 0, 95)

    if whale >= 65 and vol_pct > 0:
        status = "🟥 매수구간"
        status_color = "#ff4d4d"
    elif whale < 35:
        status = "🟦 매도구간"
        status_color = "#4d79ff"
    else:
        status = "⚪ 관망"
        status_color = "#999"

    st.markdown(f"""
    <div style="
        width:100%;
        background:white;
        border-radius:16px;
        border:1px solid #ddd;
        padding:12px;
    ">

    <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #eee;">
        <div style="font-weight:800;">현재가</div>
        <div>{price:,}원 ({pct:+.2f}%)</div>
        <div style="color:{status_color}; font-weight:900;">{status}</div>
    </div>

    <div style="display:flex; justify-content:space-between; padding:10px 0;">
        <div style="font-weight:800;">매수</div>
        <div style="color:#ff4d4d; font-weight:800;">{buy_price:,}원</div>
    </div>

    <div style="display:flex; justify-content:space-between; padding:10px 0;">
        <div style="font-weight:800;">매도</div>
        <div style="color:#4d79ff; font-weight:800;">{sell_price:,}원</div>
    </div>

    <div style="display:flex; justify-content:space-between; padding:10px 0;">
        <div style="font-weight:800;">세력</div>
        <div>{whale:.1f}%</div>
    </div>

    <div style="display:flex; justify-content:space-between; padding:10px 0;">
        <div style="font-weight:800;">예측</div>
        <div>{up_prob:.1f}%</div>
    </div>

    </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"에러 발생: {e}")