def apply_filters(df):

    filtered_rows = []

    for _, row in df.iterrows():

        keep = True

        # =========================
        # 너무 급등한 종목 제외
        # =========================

        if row["등락률"] > 20:

            keep = False

        # =========================
        # 변동성 과도 제외
        # =========================

        if row["변동성"] > 18:

            keep = False

        # =========================
        # 거래량 너무 없음 제외
        # =========================

        if row["거래량비율"] < 0.5:

            keep = False

        # =========================
        # AI 점수 낮음 제외
        # =========================

        if row["AI_SCORE"] < 60:

            keep = False

        if keep:

            filtered_rows.append(row)

    return df.__class__(filtered_rows)