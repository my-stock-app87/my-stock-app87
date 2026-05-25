def is_valid_stock(name, close, avg_volume):
    if close <= 0:
        return False

    if avg_volume < 50000:
        return False

    bad_words = ["스팩", "리츠", "ETN", "ETF", "우선주"]
    for word in bad_words:
        if word in str(name):
            return False

    return True


def price_zone(close):
    if close <= 10000:
        return "1만원 이하"
    elif close <= 30000:
        return "3만원 이하"
    elif close >= 50000:
        return "5만원 이상"
    else:
        return "중간가격대"