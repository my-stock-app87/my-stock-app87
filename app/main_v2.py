import pandas as pd

# collectors
from app.collectors.kr_collector import collect_korean_market_data

# features
from app.features.volume import volume_features
from app.features.price import price_features
from app.features.flow import flow_features
from app.features.short import short_features

# signals
from app.signals.patterns import detect_patterns

# engine
from app.ai_engine import calculate_ai_score


def run_pipeline(target_date):
    print(f"\n🚀 AI 작전주 분석 시작: {target_date}")

    # 1️⃣ 데이터 수집
    df = collect_korean_market_data(target_date)

    if df.empty:
        print("❌ 데이터 없음 (휴장일 또는 오류)")
        return

    # 2️⃣ FEATURES 적용
    df = volume_features(df)
    df = price_features(df)
    df = flow_features(df)
    df = short_features(df)

    # 3️⃣ SIGNALS 적용
    df = detect_patterns(df)

    # 4️⃣ AI ENGINE (최종 점수)
    df = calculate_ai_score(df)

    # 5️⃣ 결과 정렬
    df = df.sort_values(by="score", ascending=False)

    # 6️⃣ TOP 20 출력
    print("\n🔥🔥 오늘의 작전/급등 의심 TOP 20 🔥🔥\n")

    cols = [
        "종목코드",
        "종가",
        "volume_ratio",
        "score",
        "label"
    ]

    print(df[cols].head(20).to_string(index=False))

    # 7️⃣ 저장 (선택)
    df.to_csv(f"result_{target_date}.csv", index=False, encoding="utf-8-sig")

    print(f"\n✅ 완료: result_{target_date}.csv 저장됨")


# 실행
if __name__ == "__main__":
    import datetime

    today = datetime.date.today().strftime("%Y%m%d")
    run_pipeline(today)