def calculate_risk(volatility):

    if volatility >= 15:
        return "매우높음"

    elif volatility >= 10:
        return "높음"

    elif volatility >= 5:
        return "중간"

    else:
        return "낮음"