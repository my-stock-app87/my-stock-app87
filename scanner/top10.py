def get_top10(df):

    df = df.sort_values(
        by="AI_SCORE",
        ascending=False
    )

    return df.head(10)