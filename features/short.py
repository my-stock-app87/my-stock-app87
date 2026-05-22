def short_features(df):
    df["short_ratio"] = df["공매도비중"]

    # 숏스퀴즈 후보
    df["short_pressure"] = (df["short_ratio"] > 0.05).astype(int)

    return df