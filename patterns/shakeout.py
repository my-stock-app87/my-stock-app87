def detect_shakeout(df):

    df["흔들기"] = (
        (df["거래량비율"] > 2) &
        (df["등락률"] < -3)
    )

    return df