KEYWORDS = [
    "AI",
    "반도체",
    "그래핀",
    "전력망",
    "스마트그리드",
    "2차전지",
    "로봇",
    "원전",
    "조선",
    "방산",
]


def analyze_keywords(news_list):
    result = {}

    for keyword in KEYWORDS:
        count = 0

        for news in news_list:
            title = news["title"]

            if keyword in title:
                count += 1

        result[keyword] = count

    return result