import FinanceDataReader as fdr
import pandas as pd
from scanner.filters import is_valid_stock, price_zone


# =========================
# 종목 가져오기
# =========================
def get_stock_list():

    try:

        krx = fdr.StockListing("KRX")

        return krx[
            ["Code", "Name"]
        ].dropna()

    except Exception:

        return pd.DataFrame({

            "Code": [
                "005930",
                "000660",
                "035420",
                "035720",
                "005380",
                "051910",
                "006400",
                "373220",
                "207940",
                "068270",
                "051900",
                "066570",
                "005490",
                "012330",
                "028260",
            ],

            "Name": [
                "삼성전자",
                "SK하이닉스",
                "NAVER",
                "카카오",
                "현대차",
                "LG화학",
                "삼성SDI",
                "LG에너지솔루션",
                "삼성바이오로직스",
                "셀트리온",
                "LG생활건강",
                "LG전자",
                "POSCO홀딩스",
                "현대모비스",
                "삼성물산",
            ]
        })


# =========================
# 전체 시장 스캔
# =========================
def market_scan(sample_size=1000):

    krx = get_stock_list()

    if krx.empty:
        return pd.DataFrame()

    if len(krx) > sample_size:

        sample = krx.sample(
            sample_size,
            random_state=None
        )

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

            prev_close = int(
                df["Close"].iloc[-2]
            )

            volume = int(
                df["Volume"].iloc[-1]
            )

            avg_volume = (
                df["Volume"]
                .tail(20)
                .mean()
            )

            if prev_close <= 0:
                continue

            if avg_volume <= 0:
                continue

            if not is_valid_stock(
                name,
                close,
                avg_volume
            ):
                continue

            change_pct = (
                (close - prev_close)
                / prev_close
            ) * 100

            ma5 = (
                df["Close"]
                .rolling(5)
                .mean()
                .iloc[-1]
            )

            ma20 = (
                df["Close"]
                .rolling(20)
                .mean()
                .iloc[-1]
            )

            volume_ratio = (
                volume / avg_volume
            )

            score = 0

            if volume_ratio >= 3:
                score += 30

            elif volume_ratio >= 2:
                score += 20

            elif volume_ratio >= 1.5:
                score += 10

            if close > ma5:
                score += 10

            if close > ma20:
                score += 10

            if 0 <= change_pct <= 5:
                score += 25

            elif 5 <= change_pct <= 10:
                score += 15

            elif change_pct >= 20:
                score -= 30

            if close <= 5000:
                score += 20

            elif close <= 10000:
                score += 10

            if volume >= 300000:
                score += 10

            signal = "관망"

            if volume_ratio >= 3:

                signal = "거래량폭발"

            elif (
                volume_ratio >= 1.5
                and abs(change_pct) <= 3
            ):

                signal = "세력매집중"

            elif (
                close > ma5
                and close > ma20
                and 1 <= change_pct <= 8
            ):

                signal = "돌파직전"

            elif (
                close > ma20
                and -3 <= change_pct <= 1
            ):

                signal = "눌림목"

            action = "지켜본다"

            if score >= 90:
                action = "강력관심"

            elif score >= 75:
                action = "매수관심"

            elif score >= 60:
                action = "분할매수"

            elif score < 40:
                action = "제외"

            if signal == "거래량폭발" and change_pct >= 15:

                action = "추격주의"

            buy_price = int(close * 0.97)

            sell_price = int(close * 1.05)

            stop_loss = int(close * 0.94)

            result.append({

                "종목코드": code,
                "종목명": name,
                "현재가": close,

                "등락률(%)": round(
                    change_pct,
                    2
                ),

                "거래량": volume,

                "거래량배수": round(
                    volume_ratio,
                    2
                ),

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

    result_df = result_df.sort_values(
        "AI점수",
        ascending=False
    )

    return result_df.reset_index(drop=True)