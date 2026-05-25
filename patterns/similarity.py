import pandas as pd


def calculate_similarity(df):

    historical = pd.read_csv(
        "data/historical_patterns.csv"
    )

    similarities = []

    similar_patterns = []

    for _, row in df.iterrows():

        best_score = 0

        best_pattern = "없음"

        for _, past in historical.iterrows():

            score = 0

            # =========================
            # 거래량 비교
            # =========================

            volume_diff = abs(
                row["거래량비율"]
                - past["거래량비율"]
            )

            if volume_diff <= 0.5:
                score += 30

            elif volume_diff <= 1:
                score += 15

            # =========================
            # 등락률 비교
            # =========================

            change_diff = abs(
                row["등락률"]
                - past["등락률"]
            )

            if change_diff <= 3:
                score += 30

            elif change_diff <= 5:
                score += 15

            # =========================
            # 변동성 비교
            # =========================

            volatility_diff = abs(
                row["변동성"]
                - past["변동성"]
            )

            if volatility_diff <= 3:
                score += 20

            elif volatility_diff <= 5:
                score += 10

            # =========================
            # 패턴 반영
            # =========================

            if row["돌파"]:
                score += 20

            if row["매집"]:
                score += 10

            if row["흔들기"]:
                score += 10

            # =========================
            # 최고 유사 패턴 저장
            # =========================

            if score > best_score:

                best_score = score

                best_pattern = (
                    f"{past['종목명']} "
                    f"({past['패턴']})"
                )

        similarities.append(best_score)

        similar_patterns.append(best_pattern)

    df["유사도"] = similarities

    df["유사패턴"] = similar_patterns

    return df