import datetime
import pandas as pd
import yfinance as yf
import FinanceDataReader as fdr


# =========================
# 1. 날짜 처리
# =========================
def get_date_range(target_date):
    """
    yfinance는 end_date가 포함되지 않기 때문에 +1일 처리 필요
    """
    start = datetime.datetime.strptime(target_date, "%Y%m%d")
    end = start + datetime.timedelta(days=1)

    return (
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d")
    )


# =========================
# 2. 글로벌 매크로 수집
# =========================
def collect_global_macro(target_date: str):
    print(f"🌐 글로벌 데이터 수집 시작: {target_date}")

    start_date, end_date = get_date_range(target_date)

    macro_tickers = {
        "^IXIC": "NASDAQ",
        "^GSPC": "S&P500",
        "^DJI": "DOW",
        "^VIX": "VIX",
        "CL=F": "WTI_OIL",
        "GC=F": "GOLD",
        "BTC-USD": "BTC",
        "KRW=X": "USDKRW"
    }

    results = []

    # =========================
    # 2-1. yfinance 데이터
    # =========================
    for ticker, name in macro_tickers.items():
        try:
            df = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False
            )

            if df.empty:
                continue

            close = float(df["Close"].iloc[-1])

            results.append({
                "date": target_date,
                "indicator": name,
                "value": close
            })

        except Exception as e:
            print(f"⚠️ {name} 수집 실패: {e}")

    # =========================
    # 2-2. 미국 10년물 금리
    # =========================
    try:
        df_bond = fdr.DataReader("US10Y", start_date, end_date)

        if not df_bond.empty:
            results.append({
                "date": target_date,
                "indicator": "US10Y",
                "value": float(df_bond["Close"].iloc[-1])
            })

    except Exception as e:
        print(f"⚠️ US10Y 수집 실패: {e}")

    # =========================
    # 3. DataFrame 변환
    # =========================
    df_result = pd.DataFrame(results)

    if not df_result.empty:
        df_result["date"] = pd.to_datetime(df_result["date"])

    print(f"✅ 글로벌 데이터 완료: {len(df_result)}개")
    return df_result


# =========================
# 4. 테스트 실행
# =========================
if __name__ == "__main__":
    today = datetime.date.today().strftime("%Y%m%d")

    df = collect_global_macro(today)
    print(df)