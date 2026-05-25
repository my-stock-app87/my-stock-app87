import pandas as pd

from datetime import datetime

import os


def save_recommendations(df):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    save_df = df.copy()

    save_df["추천일"] = today

    file_path = "logs/recommendations.csv"

    # =========================
    # 기존 파일 있으면 추가 저장
    # =========================

    if os.path.exists(file_path):

        old_df = pd.read_csv(file_path)

        save_df = pd.concat(
            [old_df, save_df],
            ignore_index=True
        )

    save_df.to_csv(
        file_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"추천 저장 완료: {file_path}"
    )