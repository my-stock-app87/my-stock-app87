import datetime
import pandas as pd
from pykrx import stock


# =========================
# 1. 날짜 처리
# =========================
def get_today():
    return datetime.date.today().strftime("%Y%m%d")


# =========================
# 2. 한국 전체 시장 데이터 수집
# =========================
def collect_korean_stock(target_date: str = None):

    if target_date is None:
        target_date = get_today()

    print(f"🇰🇷 한국 데이터 수집 시작: {target_date}")

    try:
        # =========================
        # 1. KOSPI + KOSDAQ OHLCV
        # =========================
        df_kospi = stock.get_market_ohlcv_by_ticker(target_date, market="KOSPI")
        df_kosdaq = stock.get_market_ohlcv_by_ticker(target_date, market="KOSDAQ")

        df_price = pd.concat([df_kospi, df_kosdaq])

        # =========================
        # 2. 투자자별 수급 데이터
        # =========================
        df_flow = stock.get_market_trading_value_by_investor(
            target_date,
            target_date,
            market="ALL"
        )

        # =========================
        # 3. 종목 기본 정보
        # =========================
        tickers = stock.get_market_ticker_list(target_date)

        info_list = []

        for ticker in tickers:
            try:
                name = stock.get_market_ticker_name(ticker)

                if ticker in df_price.index:
                    row = df_price.loc[ticker]

                    info_list.append({
                        "date": target_date,
                        "ticker": ticker,
                        "name": name,

                        "open": float(row["시가"]),
                        "high": float(row["고가"]),
                        "low": float(row["저가"]),
                        "close": float(row["종가"]),
                        "volume": float(row["거래량"]),
                        "change_rate": float(row["등락률"])
                    })

            except Exception:
                continue

        df_result = pd.DataFrame(info_list)

        # =========================
        # 4. 수급 데이터 병합 (간단 버전)
        # =========================
        if not df_flow.empty:
            df_flow = df_flow.reset_index()

            # 컬럼 구조 맞추기 (기관/외국인/개인)
            df_flow = df_flow.rename(columns={
                "기관합계": "institution",
                "외국인합계": "foreign",
                "개인": "individual"
            })

            df_result = df_result.merge(
                df_flow[["티커", "institution", "foreign", "individual"]],
                left_on="ticker",
                right_on="티커",
                how="left"
            )

            df_result.drop(columns=["티커"], inplace=True)

        print(f"✅ 한국 데이터 완료: {len(df_result)}개 종목")

        return df_result

    except Exception as e:
        print(f"❌ 한국 데이터 수집 실패: {e}")
        return pd.DataFrame()


# =========================
# 3. 테스트 실행
# =========================
if __name__ == "__main__":
    df = collect_korean_stock()
    print(df.head())