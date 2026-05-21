st.markdown(f"""
<div style="
    width:100%;
    background:white;
    border-radius:16px;
    overflow:hidden;
    border:1px solid #ddd;
">

<table style="
    width:100%;
    border-collapse:collapse;
    font-size:14px;
">

<!-- 현재가 + 상태 -->
<tr style="background:#f7f7f7; border-bottom:1px solid #eee;">
    <td style="padding:12px; font-weight:800;">현재가</td>
    <td style="padding:12px; text-align:right;">
        {price:,}원 ({pct:+.2f}%)
    </td>
    <td style="padding:12px; text-align:right; font-weight:900; color:{color};">
        {status}
    </td>
</tr>

<!-- 매수 -->
<tr style="border-bottom:1px solid #eee;">
    <td style="padding:12px; font-weight:800;">매수추천</td>
    <td colspan="2" style="padding:12px; text-align:right; color:#ff4d4d; font-weight:800;">
        {buy_price:,}원
    </td>
</tr>

<!-- 매도 -->
<tr style="background:#f7f7f7; border-bottom:1px solid #eee;">
    <td style="padding:12px; font-weight:800;">매도추천</td>
    <td colspan="2" style="padding:12px; text-align:right; color:#4d79ff; font-weight:800;">
        {sell_price:,}원
    </td>
</tr>

<!-- 세력 -->
<tr style="border-bottom:1px solid #eee;">
    <td style="padding:12px; font-weight:800;">세력</td>
    <td colspan="2" style="padding:12px; text-align:right;">
        {whale:.1f}%
    </td>
</tr>

<!-- 거래량 -->
<tr style="background:#f7f7f7; border-bottom:1px solid #eee;">
    <td style="padding:12px; font-weight:800;">거래량 변화</td>
    <td colspan="2" style="padding:12px; text-align:right;">
        {vol_pct:+.1f}%
    </td>
</tr>

<!-- 예측 -->
<tr>
    <td style="padding:12px; font-weight:800;">예측확률</td>
    <td colspan="2" style="padding:12px; text-align:right;">
        {up_prob:.1f}%
    </td>
</tr>

</table>

</div>
""", unsafe_allow_html=True)