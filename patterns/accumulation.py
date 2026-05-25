def detect_accumulation(df):
    df["매집"] = (
        (df["거래량비율"] > 1.0) &
        (df["등락률"].abs() < 3)
    )
    return df