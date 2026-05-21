    # =====================================================
    # 🔥 [수정] HTML 소스코드가 아닌 실제 표로 렌더링되도록 수정
    # =====================================================
    st.markdown(f"""
    <table style="width:100%; border-collapse:collapse; background-color:#ffffff; border-radius:12px; border:1px solid #ddd; overflow:hidden;">
        <tr style="background-color:#f7f7f7; border-bottom:1px solid #eee;">
            <td style="padding:12px 10px; font-weight:800; color:#333;">현재가</td>
            <td style="padding:12px 10px; text-align:right; font-weight:bold;">
                {price:,}원 ({pct:+.2f}%)
            </td>
            <td style="padding:12px 10px; text-align:right; font-weight:900; color:{color};">
                {status}
            </td>
        </tr>
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:12px 10px; font-weight:800; color:#333;">매수추천가</td>
            <td colspan="2" style="padding:12px 10px; text-align:right; color:#ff4d4d; font-weight:bold;">
                {buy_price:,}원
            </td>
        </tr>
        <tr style="background-color:#f7f7f7; border-bottom:1px solid #eee;">
            <td style="padding:12px 10px; font-weight:800; color:#333;">매도추천가</td>
            <td colspan="2" style="padding:12px 10px; text-align:right; color:#4d79ff; font-weight:bold;">
                {sell_price:,}원
            </td>
        </tr>
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:12px 10px; font-weight:800; color:#333;">세력유입도</td>
            <td colspan="2" style="padding:12px 10px; text-align:right; font-weight:bold; color:#222;">
                {whale:.1f}%
            </td>
        </tr>
        <tr>
            <td style="padding:12px 10px; font-weight:800; color:#333;">상승예측</td>
            <td colspan="2" style="padding:12px 10px; text-align:right; font-weight:bold; color:#e67e22;">
                {up_prob:.1f}%
            </td>
        </tr>
    </table>
    <br>
    """, unsafe_allow_html=True)
