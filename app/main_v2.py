import datetime

from app.collectors.global_collector import collect_global_macro
from app.collectors.kr_collector import collect_korean_stock


def run_brain():

    today = datetime.date.today().strftime("%Y%m%d")

    print("\n==============================")
    print("🚀 AI STOCK BRAIN START")
    print("==============================\n")

    # 1. 글로벌 데이터
    print("🌐 글로벌 데이터 수집 중...")
    global_df = collect_global_macro(today)

    # 2. 한국 데이터
    print("\n🇰🇷 한국 데이터 수집 중...")
    kr_df = collect_korean_stock(today)

    # 3. 결과 확인
    print("\n==============================")
    print("📊 결과 확인")
    print("==============================\n")

    print("\n🌐 글로벌 (상위 5개)")
    print(global_df.head())

    print("\n🇰🇷 한국 (상위 5개)")
    print(kr_df.head())

    print("\n==============================")
    print("✅ 브레인 실행 완료")
    print("==============================\n")


if __name__ == "__main__":
    run_brain()