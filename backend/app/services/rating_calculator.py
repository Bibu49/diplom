import pandas as pd


class RatingCalculator:

    def build(self, ul_result, fl_result, iku_result):

        df_ul = pd.DataFrame(ul_result)
        df_fl = pd.DataFrame(fl_result)
        df_iku = pd.DataFrame(iku_result)

        merged = df_ul.merge(df_fl, on='branch')
        merged = merged.merge(df_iku, on='branch')

        merged['total_score'] = (
            merged['score_ul'] +
            merged['score_fl'] +
            merged['score_iku']
        )

        merged = merged.sort_values(
            'total_score',
            ascending=False
        )

        merged['rank'] = range(1, len(merged) + 1)

        return merged