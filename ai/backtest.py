import pandas as pd


def run_backtest(df):

    results = []

    for _, row in df.iterrows():

        score = row["AI_SCORE"]

        # =========================
        # 가상 성공 확률
        # =========================

        success = False

        expected_return = 0

        if score >= 180:

            success = True

            expected_return = 12

        elif score >= 140:

            success = True

            expected_return = 8

        elif score >= 100:

            success = True

            expected_return = 5

        elif score >= 70:

            success = False

            expected_return = 2

        else:

            success = False

            expected_return = -3

        results.append({

            "종목명": row["종목명"],

            "AI_SCORE": score,

            "예상수익률": expected_return,

            "성공여부": success
        })

    return pd.DataFrame(results)