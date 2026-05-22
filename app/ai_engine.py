import pandas as pd
from app.collectors.kr_collector import collect_korean_market_data


# -------------------------
# 점수 계산
# -------------------------
def calculate_scores(df):

    vol_score = min(100, df["Volume"].pct_change().fillna(0).abs().mean() * 1000)
    up_score = max(0, df["Close"].pct_change().mean() * 1000 + 50)
    force_score = (vol_score + up_score) / 2

    volatility_score = df["Close"].pct_change().std() * 1000
    final_score = (vol_score * 0.4 + up_score * 0.3 + force_score * 0.3)

    return {
        "vol_score": round(vol_score, 2),
        "up_score": round(up_score, 2),
        "force_score": round(force_score, 2),
        "volatility_score": round(volatility_score, 2),
        "final_score": round(final_score, 2)
    }


# -------------------------
# 해석 레이어
# -------------------------
def explain(scores):

    reasons = []

    if scores["vol_score"] > 60:
        reasons.append("거래량 급증 → 세력 유입 가능성")

    if scores["force_score"] > 50:
        reasons.append("수급 강세 패턴")

    if scores["volatility_score"] < 30:
        reasons.append("매집 구간 가능성")

    if scores["final_score"] > 70:
        position = "🚀 급등 가능성"
    elif scores["final_score"] > 40:
        position = "⚠️ 관찰 구간"
    else:
        position = "🔻 약세"

    return position, reasons


# -------------------------
# 메인 분석 함수
# -------------------------
def run_analysis(code):

    df = collect_korean_market_data(code)

    if df.empty:
        return {"error": "데이터 없음"}

    scores = calculate_scores(df)
    position, reasons = explain(scores)

    last_price = df["Close"].iloc[-1]

    return {
        "종목": code,
        "현재가": int(last_price),
        **scores,
        "position": position,
        "reasons": reasons,
        "ai": position
    }