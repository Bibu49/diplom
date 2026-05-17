import pandas as pd


class ExcelParser:

    def __init__(self, excel_file):
        self.excel = excel_file

    def load_ul(self):
        return pd.read_excel(self.excel, 'ЮЛ25')

    def load_fl(self):
        return pd.read_excel(self.excel, 'ФЛ25')

    def load_iku(self):
        return pd.read_excel(self.excel, 'ИКУ25')

    def load_norms(self):
        return pd.read_excel(self.excel, 'норм25')

    def load_coefficients(self):
        return pd.read_excel(self.excel, 'коэф')