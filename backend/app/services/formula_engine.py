import math


class FormulaEngine:

    @staticmethod
    def performance(accrued, paid):
        if accrued == 0:
            return 0

        return paid / accrued

    @staticmethod
    def delta(fact, norm):
        return fact - norm

    @staticmethod
    def score(delta_percent, max_score=30):
        score = (1 + 0.3 * (delta_percent / 0.01)) * max_score

        return max(score, 0)

    @staticmethod
    def bonus(percent, coef, max_bonus):
        value = (
            (1 + coef * ((percent - 0.01) / 0.01))
            * max_bonus
        )

        return math.floor(value * 100) / 100