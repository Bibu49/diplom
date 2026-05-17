from pathlib import Path
import pandas as pd
import xml.etree.ElementTree as ET


class FileLoader:

    @staticmethod
    def load(path: str):
        ext = Path(path).suffix.lower()

        if ext == '.xlsx':
            return pd.ExcelFile(path)

        if ext == '.csv':
            return pd.read_csv(path, sep=';', encoding='utf-8')

        if ext == '.xml':
            root = ET.parse(path).getroot()

            rows = []

            for row in root:
                rows.append({
                    child.tag: child.text
                    for child in row
                })

            return pd.DataFrame(rows)

        raise ValueError('Unsupported file format')