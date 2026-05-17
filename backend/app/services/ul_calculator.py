from app.services.formula_engine import FormulaEngine


class ULCalculator:

    def calculate(self, df, norm):

        result = []

        grouped = df.groupby('Филиал')

        for branch, data in grouped:

            accrued = data['Начислено'].sum()
            paid = data['Оплачено'].sum()

            performance = FormulaEngine.performance(
                accrued,
                paid
            )

            delta = FormulaEngine.delta(
                performance,
                norm
            )

            score = FormulaEngine.score(delta)

            result.append({
                'branch': branch,
                'accrued': accrued,
                'paid': paid,
                'performance': performance,
                'score_ul': score
            })

        return result