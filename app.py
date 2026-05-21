
st.markdown("## 🧠 종합분석")

name = st.selectbox("종목 선택", names)
c = code(name)

df = ind(get_price(c))

if not df.empty:

    l = df.iloc[-1]
    p = df.iloc[-2]

    price = int(l["Close"])
    pct = (price - p["Close"]) / p["Close"] * 100

    buy_price = int(price * 0.98)
    sell_price = int(price * 1.04)

    whale = l["Whale"]

    vol_pct = (l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10) * 100

    up_prob = np.clip(whale * 0.7, 0, 95)

    # =====================================================
    # 상태
    # =====================================================
    if whale >= 65 and vol_pct > 0:
        status = "🟥 매수구간"
        status_color = "#ff4d4d"
    elif whale < 35:
        status = "🟦 매도구간"
        status_color = "#4d79ff"
    else:
        status = "⚪ 관망"
        status_color = "#999"

    # =====================================================
    # 🔥 안정형 UI (div 방식)
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

    # =====================================================
    # AI 전략 (3~5줄 이상)
    # =====================================================
    st.markdown("### 🤖 AI 전략")

    if whale >= 70 and vol_pct > 10:
        ai = """
✔ 세력 강한 유입 구간  
✔ 거래량 상승 동반  
✔ 단기 급등 가능성 높음  
✔ 눌림 시 분할 매수 유효  
✔ 단타 중심 대응 필요
"""
    elif whale >= 60:
        ai = """
✔ 세력 유입 초기 단계  
✔ 방향성 아직 불확실  
✔ 추격 매수 위험 존재  
✔ 지지 확인 후 진입 필요  
✔ 관망 + 대기 전략
"""
    elif whale < 35:
        ai = """
✔ 약세 흐름 진행  
✔ 매도 압력 우세  
✔ 반등 신호 부족  
✔ 리스크 관리 필요  
✔ 비중 축소 권장
"""
    else:
        ai = """
✔ 횡보 구간 진행  
✔ 방향성 없음  
✔ 돌파 여부 중요  
✔ 단기 대응 금지  
✔ 관망 유지
"""

    st.markdown(f"""
    <div style="
        background:white;
        padding:16px;
        border-radius:16px;
        border:1px solid #eee;
        white-space:pre-line;
        line-height:1.7;
        font-size:14px;
    ">
    {ai}
    </div>
    """, unsafe_allow_html=True)