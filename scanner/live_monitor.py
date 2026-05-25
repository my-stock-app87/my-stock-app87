import pandas as pd


def detect_live_changes(df):

    alerts = []

    for _, row in df.iterrows():

        message = ""

        # =========================
        # 거래량 급증
        # =========================

        if row["거래량비율"] >= 2:

            message += "🔥 거래량 급증 "

        # =========================
        # AI 고득점
        # =========================

        if row["AI_SCORE"] >= 180:

            message += "🚀 AI 고득점 "

        # =========================
        # 세력 신호
        # =========================

        if row["세력신호"]:

            message += "🐋 세력 포착 "

        # =========================
        # 급등 직전
        # =========================

        if row["급등직전"]:

            message += "⚡ 급등 직전 "

        alerts.append(message)

    df["실시간신호"] = alerts

    return df