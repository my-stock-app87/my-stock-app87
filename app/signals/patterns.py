def detect_patterns(df):

    df["accumulation"] = (
        (df["volume_ratio"] > 2) &
        (df["volatility"] < 0.03) &
        (df["price_change"].abs() < 0.02)
    ).astype(int)

    df["breakout"] = (
        (df["volume_ratio"] > 3) &
        (df["price_change"] > 0.05)
    ).astype(int)

    df["shakeout"] = (
        (df["volume_ratio"] > 2) &
        (df["price_change"] < -0.05) &
        (df["volatility"] > 0.04)
    ).astype(int)

    df["distribution"] = (
        (df["volume_ratio"] > 3) &
        (df["price_change"] < 0)
    ).astype(int)

    return df