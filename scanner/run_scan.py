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
    # 랜덤 시장 스캔
    # =========================
    scan_df = market_scan(sample_size=500)

    if scan_df.empty:
        return empty_result()

    # =========================
    # AI 추천 종목
    # =========================
    top10_df = scan_df.sort_values(

        ["AI점수", "추세강도", "거래량배수"],

        ascending=False

    ).head(10)

    # =========================
    # 가격대별 추천
    # =========================

    # 1만원 이하
    under_10000_df = scan_df[

        scan_df["현재가"] <= 10000

    ].sort_values(

        ["AI점수", "추세강도"],

        ascending=False

    ).head(5)

    # 1만원 ~ 3만원
    under_30000_df = scan_df[

        (scan_df["현재가"] > 10000)

        &

        (scan_df["현재가"] <= 30000)

    ].sort_values(

        ["AI점수", "추세강도"],

        ascending=False

    ).head(5)

    # 3만원 ~ 5만원
    under_50000_df = scan_df[

        (scan_df["현재가"] > 30000)

        &

        (scan_df["현재가"] <= 50000)

    ].sort_values(

        ["AI점수", "추세강도"],

        ascending=False

    ).head(5)

    # 5만원 이상
    over_50000_df = scan_df[

        scan_df["현재가"] > 50000

    ].sort_values(

        ["AI점수", "추세강도"],

        ascending=False

    ).head(5)

    # =========================
    # 내일 급등 예상
    # =========================
    tomorrow_surge_df = scan_df[

        (

            scan_df["신호"].isin([

                "거래량폭발",

                "세력매집중",

                "돌파직전",

                "눌림목"

            ])

        )

        &

        (scan_df["거래량배수"] >= 1.5)

        &

        (scan_df["AI점수"] >= 80)

        &

        (scan_df["추세강도"] >= 70)

    ].sort_values(

        ["AI점수", "추세강도", "거래량배수"],

        ascending=False

    ).head(10)

    # =========================
    # 급등 후보 부족 시
    # =========================
    if len(tomorrow_surge_df) < 5:

        tomorrow_surge_df = scan_df.sort_values(

            ["AI점수", "추세강도", "거래량배수"],

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
