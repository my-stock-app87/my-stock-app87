def flow_features(df):
    df["foreign_strength"] = df["외인순매수"]
    df["institution_strength"] = df["기관순매수"]

    # 수급 쏠림
    df["flow_bias"] = ((df["foreign_strength"] > 0) | (df["institution_strength"] > 0)).astype(int)

    return df