def price_features(df):
    df["price_change"] = (df["종가"] - df["시가"]) / df["시가"]
    df["volatility"] = (df["고가"] - df["저가"]) / df["종가"]

    # 급등/급락 신호
    df["price_momentum"] = (df["price_change"] > 0.05).astype(int)

    return df