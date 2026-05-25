def detect_breakout(df):
    df["돌파"] = (
        (df["거래량비율"] > 1.2) &
        (df["등락률"] > 5)
    )
    return df