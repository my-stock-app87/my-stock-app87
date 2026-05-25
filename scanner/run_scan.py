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

    scan_df = market_scan()

    if scan_df.empty:
        return empty_result()

    # =========================
    # 제외 제거
    # =========================
    valid_df = scan_df[
        scan_df["판단"] != "제외"
    ].copy()

    # =========================
    # AI 추천 종목
    # =========================
    top10_df = valid_df.sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(10)

    # =========================
    # 가격대별 추천
    # =========================

    under_10000_df = valid_df[

        (valid_df["현재가"] <= 10000) &
        (valid_df["AI점수"] >= 55)

    ].sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(5)

    under_30000_df = valid_df[

        (valid_df["현재가"] <= 30000) &
        (valid_df["AI점수"] >= 55)

    ].sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(5)

    over_50000_df = valid_df[

        (valid_df["현재가"] >= 50000) &
        (valid_df["AI점수"] >= 55)

    ].sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(5)

    # =========================
    # 내일 급등 예상
    # =========================

    tomorrow_surge_df = valid_df[

        (
            valid_df["신호"].isin([
                "세력매집중",
                "돌파직전",
                "눌림목"
            ])
        )

        &

        (
            valid_df["등락률(%)"] >= -2
        )

        &

        (
            valid_df["등락률(%)"] <= 7
        )

        &

        (
            valid_df["거래량배수"] >= 1.3
        )

        &

        (
            valid_df["AI점수"] >= 60
        )

    ].sort_values(

        ["AI점수", "거래량배수"],

        ascending=False

    ).head(5)

    # =========================
    # 없으면 예비 후보
    # =========================

    if tomorrow_surge_df.empty:

        tomorrow_surge_df = valid_df[

            (
                valid_df["AI점수"] >= 65
            )

            &

            (
                valid_df["거래량배수"] >= 1.2
            )

        ].sort_values(

            ["AI점수", "거래량배수"],

            ascending=False

        ).head(5)

    return {

        "top10": top10_df,

        "under_10000": under_10000_df,

        "under_30000": under_30000_df,

        "over_50000": over_50000_df,

        "tomorrow_surge": tomorrow_surge_df,
    }