def run_analysis(code, df):

    if df is None or df.empty:
        return {"error": "데이터 없음"}

    try:
        features = build_features(df)
        scores = score(features)

        s = scores["final_score"]

        if s > 70:
            position = "🟢 급등 가능 구간"
            ai = "진입 타이밍 가능성 높음"
            color = "#00C853"
        elif s > 45:
            position = "🟡 관찰 구간"
            ai = "움직임 준비 중"
            color = "#FFD600"
        else:
            position = "🔴 비활성 구간"
            ai = "아직 에너지 부족"
            color = "#D50000"

        return {
            "종목": code,
            "현재가": features["price"],
            **features,
            **scores,
            "position": position,
            "ai": ai,
            "color": color
        }

    except Exception as e:
        return {"error": str(e)}
