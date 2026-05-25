def detect_pre_breakout(df):

    signals = []

    for _, row in df.iterrows():

        signal = False

        # =========================
        # 거래량 서서히 증가
        # =========================

        if row["거래량비율"] > 1.2:

            # =========================
            # 아직 크게 안오름
            # =========================

            if row["등락률"] < 5:

                # =========================
                # 변동성 낮음
                # =========================

                if row["변동성"] < 7:

                    signal = True

        signals.append(signal)

    df["급등직전"] = signals

    return df