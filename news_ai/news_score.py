def calculate_news_scores(keyword_count):

    scores = {}

    for keyword, count in keyword_count.items():

        # =========================
        # 테스트용 강화
        # =========================

        if count >= 1:

            score = 50

        else:

            score = 0

        scores[keyword] = score

    return scores