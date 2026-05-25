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

    # =========================
    # 랜덤 시장 스캔
    # =========================
    scan_df = market_scan(sample_size=100)

    if scan_df.empty:
        return empty_result()

    # =========================
    # AI 추천 종목
    # =========================
    top10_df = scan_df.sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(10)

    # =========================
    # 가격대별 추천
    # =========================
    under_10000_df = scan_df[

        (scan_df["현재가"] <= 10000)

    ].sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(5)

    under_30000_df = scan_df[

        (scan_df["현재가"] <= 30000)

    ].sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(5)

    over_50000_df = scan_df[

        (scan_df["현재가"] >= 50000)

    ].sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(5)

    # =========================
    # 내일 급등 예상
    # =========================
    tomorrow_surge_df = scan_df[

        (
            scan_df["신호"].isin([
                "세력매집중",
                "돌파직전",
                "눌림목",
                "거래량폭발"
            ])
        )

        &

        (
            scan_df["거래량배수"] >= 1.2
        )

    ].sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(7)

    # =========================
    # 비어있으면 대체
    # =========================
    if tomorrow_surge_df.empty:

        tomorrow_surge_df = scan_df.sort_values(

            ["AI점수", "거래량배수"],

            ascending=False

        ).head(7)

    return {

        "top10": top10_df,

        "under_10000": under_10000_df,

        "under_30000": under_30000_df,

        "over_50000": over_50000_df,

        "tomorrow_surge": tomorrow_surge_df,
    }