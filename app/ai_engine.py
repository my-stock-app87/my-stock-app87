import pandas as pd

def calculate_ai_score(df):
    """
    features + signals를 종합해서
    작전주 확률 점수를 계산하는 엔진
    """

    # --------------------------
    # 1. 기본 점수 (거래량)
    # --------------------------
    df["score"] = df["volume_ratio"] * 20

    # --------------------------
    # 2. 패턴 점수 (signals)
    # --------------------------
    df["score"] += df["accumulation"] * 25
    df["score"] += df["breakout"] * 35
    df["score"] += df["shakeout"] * 20
    df["score"] += df["distribution"] * -30  # 위험 패턴은 감점

    # --------------------------
    # 3. 수급 점수
    # --------------------------
    df["score"] += df["flow_bias"] * 15

    # --------------------------
    # 4. 공매도 (숏스퀴즈)
    # --------------------------
    df["score"] += df["short_pressure"] * 15

    # --------------------------
    # 5. 점수 정규화
    # --------------------------
    df["score"] = df["score"].clip(0, 100)

    # --------------------------
    # 6. 최종 라벨링
    # --------------------------
    def label(row):
        if row["score"] >= 75:
            return "🔥 작전/급등 의심"
        elif row["score"] >= 50:
            return "⚠️ 관찰 필요"
        else:
            return "❄️ 일반"

    df["label"] = df.apply(label, axis=1)

    # --------------------------
    # 7. 위험도 계산
    # --------------------------
    df["risk"] = (
        df["distribution"] * 40 +
        df["shakeout"] * 30
    )

    return df