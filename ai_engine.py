import pandas as pd
import numpy as np
import datetime
import FinanceDataReader as fdr

# ==========================================
# 1. 데이터
# ==========================================

def get_stock_data(code):
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=30)

    df = fdr.DataReader(code, start, end)

    return df if not df.empty else None


# ==========================================
# 2. 핵심 분석 엔진 (너의 analyze() 이동)
# ==========================================

def analyze(df):

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    current = int(latest["Close"])
    prev_close = int(prev["Close"])

    high = int(latest["High"])
    low = int(latest["Low"])
    volume = int(latest["Volume"])

    change = current - prev_close
    change_pct = round((change / prev_close) * 100, 2)

    avg_vol = df["Volume"].tail(5).mean()

    vol_trend = "📈 증가" if volume > df.iloc[-2]["Volume"] else "📉 감소"

    vol_score = min(max(int(volume / avg_vol * 50), 10), 95)

    price_pos = (current - low) / max(high - low, 1) * 100

    up_score = min(max(int(price_pos * 0.7 + change_pct * 5), 5), 98)

    volume_ratio = volume / avg_vol

    force_score = (
        min(volume_ratio * 40, 60) +
        min(max(change_pct * 2, 0), 40)
    )

    force_score = round(min(max(force_score, 0), 100), 1)

    if up_score >= 70:
        position = "🔥 상승 우세"
        color = "#FF4B4B"
        ai = "거래량 증가 + 상승 흐름"
    elif up_score <= 35:
        position = "⚠ 약세"
        color = "#1F77B4"
        ai = "하락 압력"
    else:
        position = "👀 관망"
        color = "#FFA500"
        ai = "횡보 구간"

    return {
        "current": current,
        "change": change,
        "change_pct": change_pct,
        "high": high,
        "low": low,
        "volume": volume,
        "vol_trend": vol_trend,
        "vol_score": vol_score,
        "up_score": up_score,
        "force_score": force_score,
        "position": position,
        "color": color,
        "ai": ai,
        "buy": int(low * 1.003),
        "sell": int(high * 0.997),
        "estimated_target": int(current * (1 + up_score / 100 * 0.05))
    }


# ==========================================
# 3. 메인 함수 (app.py가 호출)
# ==========================================

def run_analysis(code):

    df = get_stock_data(code)

    if df is None or len(df) < 5:
        return {"error": "no data"}

    result = analyze(df)

    return {
        "df": df,
        "result": result
    }