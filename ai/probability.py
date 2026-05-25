def calculate_probability(score):

    if score >= 180:
        return 90

    elif score >= 140:
        return 80

    elif score >= 100:
        return 70

    elif score >= 70:
        return 60

    else:
        return 50