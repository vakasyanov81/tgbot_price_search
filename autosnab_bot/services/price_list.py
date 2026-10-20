from pathlib import Path
from typing import NamedTuple

from python_calamine import CalamineWorkbook

SHEET_NAME = "price"
# Колонки ищутся по заголовку: у шаблонов priceformation (Дром, общий, полный) разный набор и порядок колонок.
TITLE_HEADER = "Номенклатура"
PRICE_SELLING_HEADER = "Цена"
PRICE_PURCHASE_HEADER = "Цена закуп."
REST_HEADER = "Остаток"
SUPPLIER_HEADER = "Поставщик"
PRODUCT_TYPE_HEADER = "Тип товара"
# priceformation помечает звёздочкой тип, исправленный по названию: «Легкогрузовая шина*».
CORRECTED_TYPE_MARK = "*"


class PriceInfo(NamedTuple):
    price: str
    price_purchase: str
    rest: str
    row_id: int
    supplier: str = ""
    product_type: str = ""
    # Название как в прайсе; ключ словаря — оно же в нижнем регистре, для поиска без учёта регистра.
    title: str = ""


price_data = dict[str, list[PriceInfo]]


class PriceListDataLoader:
    def __init__(self, path: Path) -> None:
        self.price_list: price_data = {}
        self.path = path

    def load_price(self) -> bool:
        if not self.path.exists():
            return False

        wb = CalamineWorkbook.from_path(str(self.path))
        data = wb.get_sheet_by_name(SHEET_NAME).to_python()
        if not data:
            return False

        header = [str(cell).strip() for cell in data[0]]
        if TITLE_HEADER not in header:
            return False
        columns = {name: header.index(name) for name in header}

        def cell(row: list, name: str) -> str:
            index = columns.get(name)
            return str(row[index]) if index is not None and index < len(row) else ""

        for i, row in enumerate(data[1:], start=1):
            title = cell(row, TITLE_HEADER).strip()
            if not title:
                continue
            info = PriceInfo(
                price=cell(row, PRICE_SELLING_HEADER),
                price_purchase=cell(row, PRICE_PURCHASE_HEADER),
                rest=cell(row, REST_HEADER),
                row_id=i,
                supplier=cell(row, SUPPLIER_HEADER),
                product_type=cell(row, PRODUCT_TYPE_HEADER).strip().removesuffix(CORRECTED_TYPE_MARK),
                title=title,
            )
            self.price_list.setdefault(title.lower(), []).append(info)
        return True

    def get_price_list(self) -> price_data:
        return self.price_list
