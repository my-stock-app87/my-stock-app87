def calculate_ai_score(df):

    ai_scores = []

    for _, row in df.iterrows():

        score = 0

        score += row["유사도"]
        score += row["거래량비율"] * 5

        if row["등락률"] > 0:
            score += row["등락률"] * 2

        score += row["뉴스점수"] * 0.2
        score += row["테마점수"] * 0.3

        if row["세력신호"]:
            score += 50

        if row["급등직전"]:
            score += 40

        # 5만원 이상 안정주 보정
        if row["현재가"] >= 50000:
            score += 20

        # 저가주 거래량 보정
        if row["현재가"] <= 30000 and row["거래량비율"] >= 1.2:
            score += 25

        if row["변동성"] > 18:
            score -= 20

        ai_scores.append(round(score, 2))

    df["AI_SCORE"] = ai_scores

    return df