# =====================================================
# 🧠 종합분석 (안전성 및 가독성 극대화 버전)
# =====================================================
st.markdown("## 🧠 종합분석")

if len(names) == 0:
    st.error("종목 데이터 로딩 실패. 네트워크 상태를 확인하세요.")
    st.stop()

# 1. 안전한 종목 선택 기능
name = st.selectbox("종목 선택", names)

# 2. 종목 코드를 정확한 6자리 문자열로 변환 (핵심 수정)
try:
    raw_code = df_stock[df_stock["Name"] == name]["Code"].values[0]
    c = str(raw_code).zfill(6) # 005930 처럼 앞자리 0이 안 잘리도록 처리
except Exception as e:
    st.error(f"종목 코드 추출 실패: {e}")
    st.stop()

# 3. 데이터 로드 및 지표 계산
with st.spinner("📊 데이터를 분석하는 중입니다..."):
    raw_data = get_price(c)
    df = ind(raw_data)

# 4. 데이터 검증 및 화면 출력
if not df.empty and len(df) >= 2:
    l = df.iloc[-1]   # 오늘(최근) 데이터
    p = df.iloc[-2]   # 어제(직전) 데이터

    # 데이터 추출
    price = int(l["Close"])
    pct = ((price - p["Close"]) / (p["Close"] + 1e-10)) * 100

    buy_price = int(price * 0.98)
    sell_price = int(price * 1.04)

    whale = float(l["Whale"])
    vol_pct = ((l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10)) * 100
    up_prob = np.clip(whale * 0.7, 0, 95)

    # 상태 및 색상 결정
    if whale >= 65 and vol_pct > 0:
        status = "🟥 매수구간"
        color = "#ff4d4d"
    elif whale < 35:
        status = "🟦 매도구간"
        color = "#4d79ff"
    else:
        status = "⚪ 관망"
        color = "#888888"

    # =====================================================
    # 🔥 HTS 스타일 테이블 (UI 배치 완벽 수정)
    # =====================================================
    st.markdown(f"""
    <div style="background-color:#ffffff; padding:18px; border-radius:12px; border:1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.03); margin-bottom: 20px;">
        <!-- 현재가 행 -->
        <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:2px solid #f0f0f0;">
            <span style="font-weight:bold; color:#333333; font-size: 16px;">현재가</span>
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="font-weight:bold; font-size: 16px; color:#222222;">{price:,}원 ({pct:+.2f}%)</span>
                <span style="background-color:{color}15; color:{color}; padding:3px 8px; border-radius:6px; font-weight:900; font-size:14px; border: 1px solid {color}30;">{status}</span>
            </div>
        </div>
        <!-- 매수추천가 행 -->
        <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #f9f9f9;">
            <span style="color:#ff4d4d; font-weight:bold;">매수추천가 (🔻2%)</span>
            <span style="font-weight:bold; color:#ff4d4d; font-size: 15px;">{buy_price:,}원</span>
        </div>
        <!-- 매도추천가 행 -->
        <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #f9f9f9;">
            <span style="color:#4d79ff; font-weight:bold;">매도추천가 (🔺4%)</span>
            <span style="font-weight:bold; color:#4d79ff; font-size: 15px;">{sell_price:,}원</span>
        </div>
        <!-- 세력점수 행 -->
        <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #f9f9f9;">
            <span style="font-weight:bold; color:#555555;">세력유입도</span>
            <span style="font-weight:bold; color:#222222;">{whale:.1f}%</span>
        </div>
        <!-- 상승예측 행 -->
        <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0;">
            <span style="font-weight:bold; color:#555555;">단기 상승 확률</span>
            <span style="font-weight:bold; color:#e67e22; font-size: 15px;">{up_prob:.1f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # 🤖 AI 전략 진단
    # =====================================================
    st.markdown("### 🤖 AI 투자 전략")
    if whale >= 70:
        ai = "🚀 **세력 강하게 유입된 구간**\n\n* 단기 급등 가능성이 매우 높습니다.\n* 철저히 눌림목 매수 전략이 유효합니다.\n* 다만 추격 매수 시 급락 리스크가 있으니 단타 중심으로 짧게 대응하세요."
    elif whale >= 60:
        ai = "📊 **세력 유입 초기 구간**\n\n* 거래량이 살아나고 있으나 방향성이 아직 확실하지 않습니다.\n* 섣부른 추격 매수보다는 분할 매수로 접근하는 것이 좋습니다.\n* 주요 지지선 지지 여부를 먼저 확인하세요."
    elif whale < 35:
        ai = "📉 **약세 흐름 및 매도 우세 구간**\n\n* 시장의 매도 압력이 강하며 하방 압력을 받고 있습니다.\n* 현재 뚜렷한 반등 신호가 부족하므로 무리한 물타기는 금물입니다.\n* 철저한 손절가 준수 및 비중 축소를 권장합니다."
    else:
        ai = "⚪ **지루한 횡보 구간**\n\n* 주가 변동성이 낮고 뚜렷한 매수/매도 주체가 없습니다.\n* 이 구간에서는 거래량이 갑자기 터지는 돌파 시점이 중요합니다.\n* 무리하게 진입하기보다는 관망하며 타이밍을 노리세요."

    st.info(ai)

else:
    # 예외 상황 안내 메세지 세분화
    if raw_data.empty:
        st.warning(f"⚠️ '{name}' 종목의 주가 데이터를 불러오지 못했습니다. (거래정지 또는 코드 오류)")
    elif len(df) < 2:
        st.warning(f"⚠️ 분석에 필요한 최소 데이터(영업일 기준 20일 이상)가 부족합니다.")
