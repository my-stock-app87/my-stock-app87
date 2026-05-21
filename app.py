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
    # 🔥 HTS 테이블 UI (마크다운 충돌 방지를 위해 들여쓰기 공백 완전 제거)
    # =====================================================
    table_html = f"""<table style="width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden; border:1px solid #ddd;">
<tr style="background:#f7f7f7;">
<td style="padding:10px; font-weight:800;">현재가</td>
<td style="padding:10px; text-align:right;">{price:,}원 ({pct:+.2f}%)</td>
<td style="text-align:right; font-weight:900; color:{status_color}; padding-right:10px;">{status}</td>
</tr>
<tr>
<td style="padding:10px; font-weight:800;">매수추천</td>
<td colspan="2" style="padding:10px; text-align:right; color:#ff4d4d; font-weight:800;">{buy_price:,}원</td>
</tr>
<tr style="background:#f7f7f7;">
<td style="padding:10px; font-weight:800;">매도추천</td>
<td colspan="2" style="padding:10px; text-align:right; color:#4d79ff; font-weight:800;">{sell_price:,}원</td>
</tr>
<tr>
<td style="padding:10px; font-weight:800;">세력</td>
<td colspan="2" style="padding:10px; text-align:right;">{whale:.1f}%</td>
</tr>
<tr style="background:#f7f7f7;">
<td style="padding:10px; font-weight:800;">거래량 변화</td>
<td colspan="2" style="padding:10px; text-align:right;">{vol_pct:+.1f}%</td>
</tr>
<tr>
<td style="padding:10px; font-weight:800;">예측확률</td>
<td colspan="2" style="padding:10px; text-align:right;">{up_prob:.1f}%</td>
</tr>
</table>"""

    st.markdown(table_html, unsafe_allow_html=True)

    # =====================================================
    # 🤖 AI 전략 (개선: 더 읽기 쉽게 5줄 고정)
    # =====================================================
    st.markdown("### 🤖 AI 전략")

    if whale >= 70 and vol_pct > 10:
        ai = """🚀 강한 세력 + 거래량 동반 상승 흐름입니다.
단기 급등 가능성이 높아 추세 대응이 중요합니다.
눌림 구간에서는 분할 매수가 유리합니다.
하지만 급등 이후 급락 리스크도 존재합니다.
단타 중심으로 빠른 대응이 필요합니다."""
    
    elif whale >= 60:
        ai = """📊 세력 유입이 진행 중인 초기 구간입니다.
방향성이 아직 확실하지 않아 확인이 필요합니다.
추격 매수보다는 지지 확인 후 진입이 안전합니다.
거래량 변화가 핵심 판단 기준입니다.
단기 관망 + 준비 전략이 유리합니다."""

    elif whale < 35:
        ai = """📉 약세 흐름이 지속되는 구간입니다.
매도 압력이 강하고 반등 신호가 부족합니다.
손실 관리 및 비중 축소가 우선입니다.
무리한 진입은 리스크가 큽니다.
보수적 대응이 필요합니다."""

    else:
        ai = """⚪ 뚜렷한 방향성이 없는 횡보 구간입니다.
세력과 거래량 모두 불확실한 상태입니다.
단기 트레이딩은 위험도가 높습니다.
돌파 여부 확인이 중요합니다.
현재는 관망이 가장 안전합니다."""

    ai_html = f"""<div style="background:white; padding:16px; border-radius:16px; border:1px solid #eee; line-height:1.7; font-size:14px; white-space:pre-line;">{ai}</div>"""

    st.markdown(ai_html, unsafe_allow_html=True)
