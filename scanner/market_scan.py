import FinanceDataReader as fdr
import pandas as pd


# =========================
# 가격대 분류
# =========================
def price_zone(price):

    if price <= 10000:
        return "1만원 이하"

    elif price <= 30000:
        return "3만원 이하"

    else:
        return "5만원 이상"


# =========================
# 전체 시장 랜덤 스캔
# =========================
def market_scan(sample_size=100):

    try:
        
        krx = pd.read_csv(
            "data/stock_list.csv",
            dtype=str
        )        

    except Exception as e:
        
        print("csv 오류:", e)
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

        except Exception as e:
            print("에러종목:", code, name)
            print("에러내용:", e)
            continue

            if df.empty:
                continue

            if len(df) < 20:
                continue

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            close = int(latest["Close"])
            prev_close = int(prev["Close"])
            volume = int(latest["Volume"])

            avg_volume = df["Volume"].tail(20).mean()

            if avg_volume <= 0:
                avg_volume = 1

            change_pct = ((close - prev_close) / prev_close) * 100

            ma5 = df["Close"].rolling(5).mean().iloc[-1]
            ma20 = df["Close"].rolling(20).mean().iloc[-1]

            volume_ratio = volume / avg_volume
            trading_value = close * volume

            score = 50          
          
            if volume_ratio >= 3:
                score += 25

            elif volume_ratio >= 2:
                score += 15

            elif volume_ratio >= 1.2:
                score += 10

            if close > ma5:
                score += 10

            if close > ma20:
                score += 10

            if 0 <= change_pct <= 5:
                score += 20

            elif 5 <= change_pct <= 10:
                score += 10

            elif change_pct >= 20:
                score -= 20

            if close <= 5000:
                score += 10

            elif close <= 10000:
                score += 5

            # =========================
            # 거래대금 점수
            # =========================
            if trading_value >= 10000000000:
                score += 20

            elif trading_value >= 5000000000:
                score += 10

            signal = "관망"

            if volume_ratio >= 3:
                signal = "거래량폭발"

            elif volume_ratio >= 1.5 and abs(change_pct) <= 3:
                signal = "세력매집중"

            elif close > ma5 and close > ma20 and 1 <= change_pct <= 8:
                signal = "돌파직전"

            elif close > ma20 and -3 <= change_pct <= 1:
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

            # =========================
            # 수정된 매수가 / 매도가
            # =========================
            buy_price = int(close * 0.98)
            sell_price = int(close * 1.040)
            stop_loss = int(buy_price * 0.97)

            result.append({

                "종목코드": code,

                "종목명": name,

                "현재가": close,

                "등락률(%)": round(change_pct, 2),

                "거래량": volume,

                "거래량배수": round(volume_ratio, 2),

                "거래대금(억)": round(trading_value / 100000000, 1),

                "매수가": buy_price,

                "매도가": sell_price,

                "손절가": stop_loss,

                "가격대": price_zone(close),

                "AI점수": round(score, 2),

                "신호": signal,

                "판단": action
            })

        except Exception as e:
            print(code, name, e)
            continue

    result_df = pd.DataFrame(result)

    result_df = pd.DataFrame(result)

print("최종결과:", len(result_df))

if result_df.empty:
    return pd.DataFrame()

    if result_df.empty:
        return pd.DataFrame()

    result_df = result_df.sort_values(
        ["AI점수", "거래량배수"],
        ascending=False
    )

    return result_df.reset_index(drop=True)
