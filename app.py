# =====================================================
# 🛠️ [긴급 수리] FDR 버그 우회 및 필수 종목 빌트인
# =====================================================
# fdr.StockListing("KRX")가 빈 값을 반환하는 버그를 우회하기 위한 수동 매핑 리스트입니다.
# 자주 쓰시는 종목들을 이 딕셔너리에 추가하시면 즉시 정상 작동합니다.
BUILTIN_STOCKS = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "삼성바이오로직스": "207940",
    "현대차": "005380",
    "기아": "000270",
    "셀트리온": "068270",
    "카카오": "035720",
    "NAVER": "035420",
    "에코프로비엠": "247540"
}

# fdr이 살아있으면 크롤링 데이터를 쓰고, 터졌으면 빌트인 리스트로 자동 전환합니다.
if df_stock.empty:
    names = list(BUILTIN_STOCKS.keys())
    def code(name):
        return BUILTIN_STOCKS.get(name, None)
else:
    names = df_stock["Name"].dropna().tolist()
    def code(name):
        try:
            val = df_stock[df_stock["Name"] == name]["Code"].values[0]
            return str(val).zfill(6)
        except:
            return None

# =====================================================
# 🧠 종합분석 (에러 추적용 디버깅 모드)
# =====================================================
st.markdown("## 🧠 종합분석")

if not names:
    st.error("🚨 종목 데이터 소스를 불러올 수 없습니다.")
    st.stop()

name = st.selectbox("종목 선택", names)
c = code(name)

if not c:
    st.error(f"❌ '{name}'에 해당하는 종목 코드를 찾을 수 없습니다.")
    st.stop()

# 1. 원본 주가 데이터 호출 및 확인
raw_price = get_price(c)

if raw_price.empty:
    st.error(f"❌ [데이터 로드 실패] '{name}({c})'의 최근 주가 데이터를 Yahoo/Naver 금융에서 가져오지 못했습니다. fdr.DataReader 작동 여부를 확인하세요.")
else:
    # 2. 보조지표 계산 함수 대입
    df = ind(raw_price)
    
    if df.empty or len(df) < 2:
        st.warning(f"⚠️ [분석 불가] 보조지표 계산 결과 데이터가 너무 적습니다. (현재 가용 데이터: {len(raw_price)}거래일)")
        st.info("💡 `ind()` 함수 내부의 rolling(20) 연산을 채우기 위한 데이터가 부족할 수 있습니다.")
    else:
        # 정상적인 데이터 추출 및 UI 바인딩
        l = df.iloc[-1]
        p = df.iloc[-2]

        price = int(l["Close"])
        pct = ((price - p["Close"]) / (p["Close"] + 1e-10)) * 100

        buy_price = int(price * 0.98)
        sell_price = int(price * 1.04)

        whale = float(l["Whale"])
        vol_pct = ((l["Volume"] - p["Volume"]) / (p["Volume"] + 1e-10)) * 100
        up_prob = np.clip(whale * 0.7, 0, 95)

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
        # 🔥 HTS 스타일 테이블 UI 출력
        # =====================================================
        st.markdown(f"""
        <div style="background-color:#ffffff; padding:18px; border-radius:12px; border:1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.03); margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:2px solid #f0f0f0;">
                <span style="font-weight:bold; color:#333333; font-size: 16px;">현재가</span>
                <div style="display:flex; align-items:center; gap:12px;">
                    <span style="font-weight:bold; font-size: 16px; color:#222222;">{price:,}원 ({pct:+.2f}%)</span>
                    <span style="background-color:{color}15; color:{color}; padding:3px 8px; border-radius:6px; font-weight:900; font-size:14px; border: 1px solid {color}30;">{status}</span>
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #f9f9f9;">
                <span style="color:#ff4d4d; font-weight:bold;">매수추천가</span>
                <span style="font-weight:bold; color:#ff4d4d; font-size: 15px;">{buy_price:,}원</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #f9f9f9;">
                <span style="color:#4d79ff; font-weight:bold;">매도추천가</span>
                <span style="font-weight:bold; color:#4d79ff; font-size: 15px;">{sell_price:,}원</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #f9f9f9;">
                <span style="font-weight:bold; color:#555555;">세력유입도</span>
                <span style="font-weight:bold; color:#222222;">{whale:.1f}%</span>
            </div>
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
