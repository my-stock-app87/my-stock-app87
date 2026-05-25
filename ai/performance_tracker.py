import pandas as pd

import os


def calculate_performance():

    file_path = "logs/recommendations.csv"

    # =========================
    # 파일 없으면 종료
    # =========================

    if not os.path.exists(file_path):

        return {

            "총추천수": 0,

            "성공수": 0,

            "실패수": 0,

            "성공률": 0
        }

    df = pd.read_csv(file_path)

    if len(df) == 0:

        return {

            "총추천수": 0,

            "성공수": 0,

            "실패수": 0,

            "성공률": 0
        }

    # =========================
    # 현재는 AI_SCORE 기준 가상 판정
    # =========================

    success_count = len(
        df[df["AI_SCORE"] >= 120]
    )

    fail_count = len(df) - success_count

    success_rate = round(

        (success_count / len(df)) * 100,

        2
    )

    return {

        "총추천수": len(df),

        "성공수": success_count,

        "실패수": fail_count,

        "성공률": success_rate
    }