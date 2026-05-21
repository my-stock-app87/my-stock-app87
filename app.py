        # =====================================================
        # 🔥 [최종 패치] 공백 버그를 원천 차단하는 st.html 방식
        # =====================================================
        # 문자열 맨 앞의 들여쓰기 공백을 전부 지우고 변수에 담아 st.html로 전달합니다.
        html_table = f"""
<table style="width:100%; border-collapse:collapse; background-color:#ffffff; border-radius:12px; border:1px solid #ddd; overflow:hidden; font-family:sans-serif;">
    <tr style="background-color:#f7f7f7; border-bottom:1px solid #eee;">
        <td style="padding:12px 10px; font-weight:800; color:#333; width:30%;">현재가</td>
        <td style="padding:12px 10px; text-align:right; font-weight:bold; width:45%;">
            {price:,}원 ({pct:+.2f}%)
        </td>
        <td style="padding:12px 10px; text-align:right; font-weight:900; color:{color}; width:25%;">
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
"""
        # unsafe_allow_html 없이 작동하며 문자열 인덴트 오류를 완벽하게 우회합니다.
        st.html(html_table)
