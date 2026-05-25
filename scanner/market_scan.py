import FinanceDataReader as fdr
import pandas as pd
from scanner.filters import is_valid_stock, price_zone


# =========================
# 종목 리스트
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
                "078130",
                "027580",
                "900250",
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
                "국일제지",
                "상보",
                "크리스탈신소재",
            ]
        })


# =========================
# 메인 스캔
# =========================
def market_scan(sample_size=100):

    krx = get_stock_list()

    if krx.empty:
        return pd.DataFrame()

    # 랜덤 샘플
    if len(krx) > sample_size:

        sample = krx.sample(
            sample_size,
            random_state=42
        )

    else:
        sample = krx

    result = []

    # =========================
    # 종목 루프
    # =========================
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

            avg_volume = (
                df["Volume"]
                .tail(20)
                .mean()
            )

            if prev_close <= 0:
                continue

            if avg_volume <= 0:
                continue

            # =========================
            # 기본 필터
            # =========================
            if not is_valid_stock(
                name,
                close,
                avg_volume
            ):
                continue

            # =========================
            # 변화율
            # =========================
            change_pct = (
                (close - prev_close)
                / prev_close
            ) * 100

            # =========================
            # 이동평균선
            # =========================
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

            # =========================
            # 거래량 배수
            # =========================
            if avg_volume > 0:
                volume_ratio = volume / avg_volume
            else:
                volume_ratio = 0

            # =========================
            # 20일 위치
            # =========================
            high_20 = (
                df["High"]
                .tail(20)
                .max()
            )

            low_20 = (
                df["Low"]
                .tail(20)
                .min()
            )

            if high_20 == low_20:

                position_score = 0

            else:

                position_score = (
                    (close - low_20)
                    / (high_20 - low_20)
                ) * 100

            # =========================
            # AI 점수
            # =========================
            score = 0

            # 거래량 보정
            if volume_ratio >= 3:
                score += 30

            elif volume_ratio >= 2:
                score += 20

            elif volume_ratio >= 1.5:
                score += 10

            # 추세
            if close > ma5:
                score += 10

            if close > ma20:
                score += 10

            # 상승률
            if 1 <= change_pct <= 8:
                score += 20

            elif 8 <= change_pct <= 15:
                score += 10

            elif change_pct > 20:
                score -= 10

            # =========================
            # 테마 보정
            # =========================
            if any(word in name for word in [

                "국일",
                "상보",
                "크리스탈",
                "그래핀",
                "신소재"

            ]):
                score += 20

            # =========================
            # 저가주 보정
            # =========================
            if close <= 5000:
                score += 15

            elif close <= 10000:
                score += 10

            # =========================
            # 거래량 자체 보정
            # =========================
            if volume >= 300000:
                score += 10

            elif volume >= 100000:
                score += 5

            # =========================
            # 세력 보정
            # =========================
            if (
                volume_ratio >= 1.2
                and -3 <= change_pct <= 5
            ):
                score += 15

            # =========================
            # 위치 보정
            # =========================
            if 35 <= position_score <= 75:
                score += 10

            # =========================
            # 거래량 너무 적으면 감점
            # =========================
            if volume < 30000:
                score -= 30

            # =========================
            # 신호
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

            if 8 <= change_pct <= 14:

                signal = "VI근접"

            if (
                close > ma20
                and -3 <= change_pct <= 1
                and volume_ratio >= 1
            ):

                signal = "눌림목"

            # =========================
            # 판단
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

            # 위험 경고
            if signal in [
                "거래량폭발",
                "상한가패턴",
                "VI근접"
            ]:
                action = "추격주의"

            # =========================
            # 추천 가격
            # =========================
            buy_price = int(close * 0.97)

            sell_price = int(close * 1.05)

            stop_loss = int(close * 0.94)

            # =========================
            # 결과 저장
            # =========================
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

    # =========================
    # 데이터프레임
    # =========================
    result_df = pd.DataFrame(result)

    if result_df.empty:
        return pd.DataFrame()

    # AI 점수순 정렬
    result_df = result_df.sort_values(
        "AI점수",
        ascending=False
    )

    return result_df.reset_index(drop=True)