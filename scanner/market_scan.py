import FinanceDataReader as fdr
import pandas as pd
from scanner.filters import is_valid_stock, price_zone


def market_scan(sample_size=100):
    krx = fdr.StockListing("KRX")
    krx = krx[["Code", "Name"]].dropna()

    if len(krx) > sample_size:
        sample = krx.sample(sample_size, random_state=42)
    else:
        sample = krx

    result = []

    for _, row in sample.iterrows():
        code = str(row["Code"])
        name = row["Name"]

        try:
            df = fdr.DataReader(code).tail(60)

            if df.empty or len(df) < 25:
                continue

            close = int(df["Close"].iloc[-1])
            prev_close = int(df["Close"].iloc[-2])
            volume = int(df["Volume"].iloc[-1])

            avg_volume = df["Volume"].tail(20).mean()

            if prev_close <= 0 or avg_volume <= 0:
                continue

            if not is_valid_stock(name, close, avg_volume):
                continue

            change_pct = ((close - prev_close) / prev_close) * 100

            ma5 = df["Close"].rolling(5).mean().iloc[-1]
            ma20 = df["Close"].rolling(20).mean().iloc[-1]

            volume_ratio = volume / avg_volume if avg_volume > 0 else 0

            high_20 = df["High"].tail(20).max()
            low_20 = df["Low"].tail(20).min()

            if high_20 == low_20:
                position_score = 0
            else:
                position_score = ((close - low_20) / (high_20 - low_20)) * 100

            # =========================
            # AI 점수
            # =========================
            score = 0

            if volume_ratio >= 2:
                score += 25
            elif volume_ratio >= 1.5:
                score += 15

            if close > ma5:
                score += 15

            if close > ma20:
                score += 10

            if 1 <= change_pct <= 8:
                score += 20
            elif change_pct > 12:
                score -= 20

            if close <= 10000:
                score += 10
            elif close <= 30000:
                score += 5

            if 35 <= position_score <= 75:
                score += 15

            if volume < 30000:
                score -= 30

            # =========================
            # 신호 분석
            # =========================
            signal = "관망"

            if volume_ratio >= 3:
                signal = "거래량폭발"

            if (
                volume_ratio >= 1.5
                and abs(change_pct) <= 3
                and close > ma5
            ):
                signal = "세력매집중"

            if (
                close > ma5
                and close > ma20
                and 3 <= change_pct <= 8
            ):
                signal = "돌파직전"

            if (
                change_pct >= 20
                and volume_ratio >= 2
            ):
                signal = "상한가패턴"

            if (
                8 <= change_pct <= 14
            ):
                signal = "VI근접"

            if (
                close > ma20
                and -3 <= change_pct <= 1
                and volume_ratio >= 1
            ):
                signal = "눌림목"

            # =========================
            # 판단 시스템
            # =========================
            action = "지켜본다"

            if score >= 90:
                action = "강력관심"

            elif score >= 75:
                action = "매수관심"

            elif score >= 60:
                action = "분할매수"

            elif score < 40:
                action = "제외"

            if signal == "거래량폭발":
                action = "추격주의"

            if signal == "상한가패턴":
                action = "추격주의"

            # =========================
            # 가격 계산
            # =========================
            buy_price = int(close * 0.97)
            sell_price = int(close * 1.05)
            stop_loss = int(close * 0.94)

            result.append({
                "종목코드": code,
                "종목명": name,
                "현재가": close,
                "등락률(%)": round(change_pct, 2),
                "거래량": volume,
                "거래량배수": round(volume_ratio, 2),
                "매수가": buy_price,
                "매도가": sell_price,
                "손절가": stop_loss,
                "가격대": price_zone(close),
                "AI점수": round(score, 2),
                "신호": signal,
                "판단": action
            })

        except Exception:
            continue

    result_df = pd.DataFrame(result)

    if result_df.empty:
        return pd.DataFrame()

    result_df = result_df.sort_values("AI점수", ascending=False)

    return result_df.reset_index(drop=True)