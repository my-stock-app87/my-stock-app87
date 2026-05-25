import pandas as pd
from scanner.market_scan import market_scan


def empty_result():
    return {
        "top10": pd.DataFrame(),
        "under_10000": pd.DataFrame(),
        "under_30000": pd.DataFrame(),
        "over_50000": pd.DataFrame(),
        "tomorrow_surge": pd.DataFrame(),
    }


def run_ai_scan():
    scan_df = market_scan(sample_size=100)

    if scan_df.empty:
        return empty_result()

    top10_df = scan_df.head(10)

    under_10000_df = scan_df[scan_df["가격대"] == "1만원 이하"].head(5)
    under_30000_df = scan_df[scan_df["가격대"] == "3만원 이하"].head(5)
    over_50000_df = scan_df[scan_df["가격대"] == "5만원 이상"].head(5)

    # =========================
    # 내일 급등 예상 조건
    # =========================
    strong_signals = [
        "거래량폭발",
        "돌파직전",
        "VI근접",
        "상한가패턴",
        "세력매집중",
        "눌림목",
    ]

    tomorrow_surge_df = scan_df[
        (scan_df["신호"].isin(strong_signals)) &
        (scan_df["AI점수"] >= 50) &
        (scan_df["판단"] != "제외")
    ].sort_values("AI점수", ascending=False).head(5)

    # 만약 조건이 너무 빡세서 안 나오면 AI점수 높은 종목으로 대체
    if tomorrow_surge_df.empty:
        tomorrow_surge_df = scan_df[
            (scan_df["AI점수"] >= 45) &
            (scan_df["판단"] != "제외")
        ].sort_values("AI점수", ascending=False).head(5)

    return {
        "top10": top10_df,
        "under_10000": under_10000_df,
        "under_30000": under_30000_df,
        "over_50000": over_50000_df,
        "tomorrow_surge": tomorrow_surge_df,
    }