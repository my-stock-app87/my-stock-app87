def volume_features(df):
    df["volume_ma20"] = df["거래량"].rolling(20).mean()
    df["volume_ratio"] = df["거래량"] / df["volume_ma20"]

    # 거래량 폭발 여부
    df["volume_spike"] = (df["volume_ratio"] > 3).astype(int)

    return df