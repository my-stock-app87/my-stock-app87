import feedparser


def collect_news():
    urls = [
        "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
    ]

    news_list = []

    for url in urls:
        feed = feedparser.parse(url)

        for entry in feed.entries:
            news_list.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", "")
            })

    return news_list