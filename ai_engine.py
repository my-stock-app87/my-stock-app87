import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import datetime

# ==========================================
# 1. 데이터 로딩
# ==========================================

def get_stock_data(code):
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=60)

    df = fdr.DataReader(code, start, end)

    if df.empty or len(df) < 10:
        return None

    return df


# ==========================================
# 2. Feature 계산
# ==========================================

def analyze(df):

    df = df.copy()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    current = float(latest["Close"])
    prev_close = float(prev["Close"])

    high = float(latest["High"])
    low = float(latest["Low"])
    volume = float(latest["Volume"])

    # ==========================================
    # 1. 기본 변화율
    # ==========================================
    change_pct = ((current - prev_close) / prev_close) * 100

    # ==========================================
    # 2. 거래량 분석
    # ==========================================
    avg_vol = df["Volume"].tail(5).mean()

    vol_ratio = volume / (avg_vol + 1e-9)

    if vol_ratio >= 2:
        vol_score = 95
    elif vol_ratio >= 1.5:
        vol_score = 80
    elif vol_ratio >= 1:
        vol_score = 60
    else:
        vol_score = 40

    # ==========================================
    # 3. 가격 위치 (추세 강도)
    # ==========================================
    price_pos = (current - low) / (high - low + 1e-9)

    up_score = price_pos * 100

    # ==========================================
    # 4. 수급 추정 (단순 강화)
    # ==========================================
    force_score = (
        vol_score * 0.6 +
        max(change_pct * 5, 0)
    )

    force_score = min(max(force_score, 0), 100)

    # ==========================================
    # 5. 변동성 리스크
    # ==========================================
    volatility = df["Close"].pct_change().rolling(5).std().iloc[-1]
    volatility_score = min(volatility * 500, 100)

    # ==========================================
    # 6. 통합 점수 (핵심)
    # ==========================================
    final_score = (
        up_score * 0.30 +
        force_score * 0.35 +
        vol_score * 0.25 +
        change_pct * 2
    )

    # ==========================================
    # 7. 시장 상태 보정
    # ==========================================

    if change_pct > 7:
        final_score += 5

    if vol_score > 80:
        final_score += 3

    if force_score > 70:
        final_score += 5

    if volatility_score > 60:
        final_score -= 5

    # ==========================================
    # 8. 최종 판단
    # ==========================================

    if final_score >= 80:
        position = "🚀 강한 상승 (추세 확장)"
        ai = "강한 매수 흐름 + 수급 유입"
        color = "#FF4B4B"

    elif final_score >= 65:
        position = "📈 상승 우세"
        ai = "상승 흐름 유지"
        color = "#FF7A00"

    elif final_score >= 50:
        position = "👀 관망"
        ai = "방향성 불확실"
        color = "#FFA500"

    elif final_score >= 35:
        position = "⚠ 약세"
        ai = "하락 압력 증가"
        color = "#1F77B4"

    else:
        position = "🔻 하락"
        ai = "매도 압력 강함"
        color = "#0000FF"

    # ==========================================
    # 9. 결과 반환
    # ==========================================

    return {
        "current": int(current),
        "change_pct": round(change_pct, 2),

        "up_score": round(up_score, 2),
        "vol_score": round(vol_score, 2),
        "force_score": round(force_score, 2),

        "volatility_score": round(volatility_score, 2),

        "final_score": round(final_score, 2),

        "position": position,
        "ai": ai,
        "color": color,

        "buy": int(low * 1.003),
        "sell": int(high * 0.997),
        "target": int(current * (1 + final_score / 100 * 0.05))
    }


# ==========================================
# 3. 메인 함수
# ==========================================

def run_analysis(code):

    df = get_stock_data(code)

    if df is None:
        return {"error": "no data"}

    result = analyze(df)

    return {
        "df": df,
        "result": result
    }