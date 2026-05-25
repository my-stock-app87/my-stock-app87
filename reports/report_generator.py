from ai.probability import calculate_probability

from ai.risk_manager import calculate_risk


def calculate_buy_price(current_price):

    low = int(current_price * 0.97)

    high = int(current_price)

    return f"{low:,}원 ~ {high:,}원"


def calculate_sell_price(current_price):

    low = int(current_price * 1.05)

    high = int(current_price * 1.10)

    return f"{low:,}원 ~ {high:,}원"


def generate_report(df):

    reports = []

    for _, row in df.iterrows():

        reasons = []

        if row["매집"]:
            reasons.append("세력 매집 패턴 감지")

        if row["돌파"]:
            reasons.append("거래량 돌파 발생")

        if row["흔들기"]:
            reasons.append("흔들기 패턴 감지")

        if row["뉴스점수"] > 0:
            reasons.append("뉴스 흐름 감지")

        if row["테마점수"] > 0:
            reasons.append(
                f"{row['테마']} 테마 강세"
            )

        probability = calculate_probability(
            row["AI_SCORE"]
        )

        risk = calculate_risk(
            row["변동성"]
        )

        report = {

            "종목코드": row["종목코드"],

            "종목명": row["종목명"],

            "현재가": f"{int(row['현재가']):,}원",

            "AI_SCORE": row["AI_SCORE"],

            "유사도": row["유사도"],

            "유사패턴": row["유사패턴"],

            "확률": probability,

            "위험도": risk,

            "테마": row["테마"],

            "뉴스점수": row["뉴스점수"],

            "테마점수": row["테마점수"],

            "추천이유": reasons,

            "예상매수가": calculate_buy_price(
                row["현재가"]
            ),

            "예상매도가": calculate_sell_price(
                row["현재가"]
            )
        }

        reports.append(report)

    return reports