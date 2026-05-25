from theme_ai.theme_mapper import get_theme


def apply_theme_score(df, news_scores):

    themes = []

    news_score_list = []

    theme_score_list = []

    for _, row in df.iterrows():

        stock_name = row["종목명"]

        theme = get_theme(stock_name)

        news_score = news_scores.get(
            theme,
            0
        )

        theme_score = 0

        # =========================
        # 테마 존재
        # =========================

        if theme != "기타":

            theme_score += 30

        # =========================
        # 뉴스 반영
        # =========================

        if news_score > 0:

            theme_score += 50

        themes.append(theme)

        news_score_list.append(news_score)

        theme_score_list.append(theme_score)

    df["테마"] = themes

    df["뉴스점수"] = news_score_list

    df["테마점수"] = theme_score_list

    return df