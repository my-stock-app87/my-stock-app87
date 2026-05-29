import FinanceDataReader as fdr
import pandas as pd


# =========================
# 가격대 분류
# =========================
def price_zone(price):

    if price <= 10000:
        return "1만원 이하"

    elif price <= 30000:
        return "1~3만원"

    elif price <= 50000:
        return "3~5만원"

    else:
        return "5만원 이상"


# =========================
# 전체 시장 랜덤 스캔
# =========================
def market_scan(sample_size=100):

    try:
        krx = fdr.StockListing("KRX")
        krx = krx[["Code", "Name"]].dropna()

    except Exception as e:
        print("KRX 오류:", e)
        return pd.DataFrame()

    sample = krx.sample(
        min(sample_size, len(krx)),
        random_state=None
    )

    result = []

    for _, row in sample.iterrows():

        code = str(row["Code"])
        name = row["Name"]

        try:
            df = fdr.DataReader(code).tail(60)

            if df.empty or len(df) < 20:
                continue

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            close = int(latest["Close"])
            prev_close = int(prev["Close"])
            volume = int(latest["Volume"])

            avg_volume = df["Volume"].tail(20).mean()

            if avg_volume <= 0:
                avg_volume = 1

            # 거래량 너무 적은 종목 제거
            if avg_volume < 100000:
                continue

            change_pct = ((close - prev_close) / prev_close) * 100

            ma5 = df["Close"].rolling(5).mean().iloc[-1]
            ma20 = df["Close"].rolling(20).mean().iloc[-1]

            volume_ratio = volume / avg_volume

            # =========================
            # AI 점수 + 추천 이유
            # =========================
            score = 50
            reason = []

            if volume_ratio >= 3:
                score += 25
                reason.append("거래량폭발")

            elif volume_ratio >= 2:
                score += 15
                reason.append("거래량증가")

            elif volume_ratio >= 1.2:
                score += 10
                reason.append("거래량양호")

            if close > ma5:
                score += 10
                reason.append("MA5돌파")

            if close > ma20:
                score += 10
                reason.append("MA20상향")

            if 0 <= change_pct <= 5:
                score += 20
                reason.append("급등직전")

            elif 5 < change_pct <= 10:
                score += 10
                reason.append("상승추세")

            elif change_pct >= 20:
                score -= 20
                reason.append("과열주의")

            if close <= 5000:
                score += 20
                reason.append("저가주")

            elif close <= 10000:
                score += 10
                reason.append("중저가주")

            # =========================
            # 추세강도
            # =========================
            trend = 0

            if close > ma5:
                trend += 30

            if close > ma20:
                trend += 30

            if volume_ratio >= 2:
                trend += 20

            if 0 <= change_pct <= 10:
                trend += 20

            trend = min(trend, 100)

            # =========================
            # 신호
            # =========================
            signal = "관망"

            if volume_ratio >= 3:
                signal = "거래량폭발"

            elif volume_ratio >= 1.5 and abs(change_pct) <= 3:
                signal = "세력매집중"

            elif close > ma5 and close > ma20 and 1 <= change_pct <= 8:
                signal = "돌파직전"

            elif close > ma20 and -3 <= change_pct <= 1:
                signal = "눌림목"

            # =========================
            # 판단
            # =========================
            action = "지켜본다"

            if score >= 95 and trend >= 90:
                action = "강력관심"

            elif score >= 80:
                action = "매수관심"

            elif score >= 65:
                action = "분할매수"

            elif score < 50:
                action = "제외"

            # =========================
            # 분할매수
            # =========================
            buy1 = close
            buy2 = int(close * 0.97)
            buy3 = int(close * 0.94)

            avg_buy_price = int(
                (buy1 * 0.4) +
                (buy2 * 0.3) +
                (buy3 * 0.3)
            )

            # =========================
            # 분할매도
            # =========================
            if trend >= 90:
                sell1 = int(close * 1.07)
                sell2 = int(close * 1.15)
                sell3 = int(close * 1.25)

            elif trend >= 75:
                sell1 = int(close * 1.05)
                sell2 = int(close * 1.10)
                sell3 = int(close * 1.15)

            else:
                sell1 = int(close * 1.04)
                sell2 = int(close * 1.08)
                sell3 = int(close * 1.12)

            stop_loss = int(buy3 * 0.97)

            # =========================
            # 저장
            # =========================
            result.append({

                "종목코드": code,
                "종목명": name,
                "현재가": close,

                "등락률(%)": round(change_pct, 2),

                "거래량": volume,
                "거래량배수": round(volume_ratio, 2),

                "AI점수": round(score, 2),
                "추세강도": trend,

                "추천이유": ", ".join(reason),

                "1차매수(40%)": buy1,
                "2차매수(30%)": buy2,
                "3차매수(30%)": buy3,
                "예상평균단가": avg_buy_price,

                "1차매도(20%)": sell1,
                "2차매도(30%)": sell2,
                "3차매도(50%)": sell3,

                "손절가": stop_loss,

                "가격대": price_zone(close),
                "신호": signal,
                "판단": action
            })

        except Exception as e:
            print(code, name, e)
            continue

    result_df = pd.DataFrame(result)

    if result_df.empty:
        return pd.DataFrame()

    result_df = result_df.sort_values(
        ["AI점수", "추세강도", "거래량배수"],
        ascending=False
    )

    return result_df.reset_index(drop=True)
