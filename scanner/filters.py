# =========================
# 종목 필터
# =========================

def is_valid_stock(

    name,
    close,
    avg_volume

):

    # 거래정지 제외
    if "스팩" in name:
        return False

    if "우" in name:
        return False

    # 너무 거래량 적은 종목 제외
    if avg_volume < 50000:
        return False

    return True


# =========================
# 가격대 분류
# =========================
def price_zone(price):

    if price <= 10000:
        return "1만원 이하"

    elif price <= 30000:
        return "3만원 이하"

    else:
        return "5만원 이상"