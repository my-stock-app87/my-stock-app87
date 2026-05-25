from news_ai.news_collector import collect_news

from news_ai.keyword_analyzer import analyze_keywords

from news_ai.news_score import calculate_news_scores

from theme_ai.theme_score import apply_theme_score


def apply_news_theme(df):

    # =========================
    # 뉴스 수집
    # =========================

    news_list = collect_news()

    # =========================
    # 키워드 분석
    # =========================

    keyword_count = analyze_keywords(news_list)

    # =========================
    # 뉴스 점수 계산
    # =========================

    news_scores = calculate_news_scores(
        keyword_count
    )

    # =========================
    # 테마 점수 적용
    # =========================

    df = apply_theme_score(
        df,
        news_scores
    )

    return df