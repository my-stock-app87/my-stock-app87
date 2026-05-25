def detect_whale_signal(df):

    whale_signals = []

    for _, row in df.iterrows():

        signal = False

        # =========================
        # 거래량 증가
        # =========================

        if row["거래량비율"] > 1.5:

            # =========================
            # 변동성 낮음
            # =========================

            if row["변동성"] < 8:

                # =========================
                # 상승 시작
                # =========================

                if row["등락률"] > 1:

                    signal = True

        whale_signals.append(signal)

    df["세력신호"] = whale_signals

    return df