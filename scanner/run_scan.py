import pandas as pd
from scanner.market_scan import market_scan


def empty_result():

    return {
        "top10": pd.DataFrame(),
        "under_10000": pd.DataFrame(),
        "under_30000": pd.DataFrame(),
        "under_50000": pd.DataFrame(),
        "over_50000": pd.DataFrame(),
        "tomorrow_surge": pd.DataFrame(),
    }


def run_ai_scan():

    # =========================
    # 시장 스캔
    # =========================

    scan_df = market_scan(sample_size=200)

    if scan_df.empty:
        return empty_result()

    # =========================
    # V2 전략
    # AI70 + 관망/눌림목
    # =========================

    v1_df = scan_df[

        (scan_df["AI점수"] >= 70)

        &

        (scan_df["신호"].isin([
            "관망",
            "눌림목"
        ]))

        &

        (scan_df["등락률(%)"] >= 0)

        &

        (scan_df["등락률(%)"] <= 8)

    ]

    # =========================
    # 후보 부족 시
    # AI70 전체
    # =========================

    if len(v1_df) < 5:

        v1_df = scan_df[

            (scan_df["AI점수"] >= 70)

            &

            (scan_df["등락률(%)"] >= 0)

            &

            (scan_df["등락률(%)"] <= 8)

        ]

    # =========================
    # AI 추천
    # =========================

    top10_df = v1_df.sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(10)

    # =========================
    # 가격대별 추천
    # =========================

    under_10000_df = scan_df[
        scan_df["현재가"] <= 10000
    ].sort_values(
        ["AI점수", "거래량배수"],
        ascending=False
    ).head(5)

    under_30000_df = scan_df[
        (scan_df["현재가"] > 10000)
        &
        (scan_df["현재가"] <= 30000)
    ].sort_values(
        ["AI점수", "거래량배수"],
        ascending=False
    ).head(5)

    under_50000_df = scan_df[
        (scan_df["현재가"] > 30000)
        &
        (scan_df["현재가"] <= 50000)
    ].sort_values(
        ["AI점수", "거래량배수"],
        ascending=False
    ).head(5)

    over_50000_df = scan_df[
        scan_df["현재가"] > 50000
    ].sort_values(
        ["AI점수", "거래량배수"],
        ascending=False
    ).head(5)

    # =========================
    # 내일 급등 예상
    # =========================

    tomorrow_surge_df = v1_df.sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(10)

    return {

        "top10": top10_df,

        "under_10000": under_10000_df,

        "under_30000": under_30000_df,

        "under_50000": under_50000_df,

        "over_50000": over_50000_df,

        "tomorrow_surge": tomorrow_surge_df,
    }
