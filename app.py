    # =====================================================
    # 🔥 안정형 UI (div 방식) - HTML 문법 오류 수정본
    # =====================================================
    st.markdown(f"""
    <div style="
        width:100%;
        background:white;
        border-radius:16px;
        border:1px solid #ddd;
        padding:12px;
    ">

    <!-- 현재가 -->
    <div style="
        display:flex;
        justify-content:space-between;
        padding:10px 0;
        border-bottom:1px solid #eee;
    ">
        <div style="font-weight:800;">현재가</div>
        <div>{price:,}원 ({pct:+.2f}%)</div>
        <div style="font-weight:900; color:{status_color};">
            {status}
        </div>
    </div>

    <!-- 매수 -->
    <div style="
        display:flex;
        justify-content:space-between;
        padding:10px 0;
        border-bottom:1px solid #eee;
    ">
        <div style="font-weight:800;">매수추천</div>
        <div style="color:#ff4d4d; font-weight:800;">
            {buy_price:,}원
        </div>
    </div>

    <!-- 매도 -->
    <div style="
        display:flex;
        justify-content:space-between;
        padding:10px 0;
        border-bottom:1px solid #eee;
    ">
        <div style="font-weight:800;">매도추천</div>
        <div style="color:#4d79ff; font-weight:800;">
            {sell_price:,}원
        </div>
    </div>

    <!-- 세력 -->
    <div style="
        display:flex;
        justify-content:space-between;
        padding:10px 0;
        border-bottom:1px solid #eee;
    ">
        <div style="font-weight:800;">세력</div>
        <div>{whale:.1f}%</div>
    </div>

    <!-- 거래량 -->
    <div style="
        display:flex;
        justify-content:space-between;
        padding:10px 0;
        border-bottom:1px solid #eee;
    ">
        <div style="font-weight:800;">거래량 변화</div>
        <div>{vol_pct:+.1f}%</div>
    </div>

    <!-- 예측 -->
    <div style="
        display:flex;
        justify-content:space-between;
        padding:10px 0;
    ">
        <div style="font-weight:800;">예측확률</div>
        <div>{up_prob:.1f}%</div>
    </div>

    </div>
    """, unsafe_allow_html=True)
