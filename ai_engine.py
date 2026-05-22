import pandas as pd
from collectors.kr_collector import collect_korean_market_data


# =========================
# 1. 점수 계산 엔진
# =========================
def calculate_scores(df):

    # 거래량 변화
    vol_score = min(
        100,
        df["Volume"].pct_change().fillna(0).abs().mean() * 1200
    )

    # 상승 강도
    up_score = max(
        0,
        df["Close"].pct_change().mean() * 1200 + 50
    )

    # 수급 강도 (단순화)
    force_score = (vol_score + up_score) / 2

    # 변동성 (낮을수록 매집 가능성)
    volatility_score = df["Close"].pct_change().std() * 1000

    # 최종 점수 (핵심)
    final_score = (
        vol_score * 0.4 +
        up_score * 0.3 +
        force_score * 0.3
    )

    return {
        "vol_score": round(vol_score, 2),
        "up_score": round(up_score, 2),
        "force_score": round(force_score, 2),
        "volatility_score": round(volatility_score, 2),
        "final_score": round(final_score, 2)
    }


# =========================
# 2. 해석 엔진 (핵심 개선)
# =========================
def explain(scores):

    score = scores["final_score"]
    volatility = scores["volatility_score"]

    reasons = []

    # 📊 조건 해석
    if scores["vol_score"] > 60:
        reasons.append("거래량 급증 → 세력 개입 가능성")

    if scores["force_score"] > 50:
        reasons.append("수급 강세 → 기관/외국인 유입")

    if volatility < 30:
        reasons.append("변동성 낮음 → 매집 구간 가능성")

    if score > 70:
        position = "🟢 매수 후보 (강세)"
        ai = "상승 가능성 높음"
        color = "#00C853"

    elif score > 40:
        position = "🟡 관찰 구간"
        ai = "추세 확인 필요"
        color = "#FFD600"

    else:
        position = "🔴 회피 구간"
        ai = "하락 압력 강함"
        color = "#D50000"

    return position, ai, color, reasons


# =========================
# 3. 메인 분석 함수
# =========================
def run_analysis(code):

    df = collect_korean_market_data(code)

    if df.empty:
        return {"error": "데이터 없음"}

    scores = calculate_scores(df)
    position, ai, color, reasons = explain(scores)

    last_price = df["Close"].iloc[-1]

    return {
        "종목": code,
        "현재가": int(last_price),

        # 점수
        **scores,

        # 판단
        "position": position,
        "ai": ai,
        "color": color,

        # 설명
        "reasons": reasons
    }
