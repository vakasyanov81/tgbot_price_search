from typing import NamedTuple

from python_calamine import CalamineWorkbook

from autosnab_bot import config

SHEET_NAME = "price"
TITLE_COLUMN = 2
PRICE_PURCHASE_COLUMN = 5
PRICE_SELLING_COLUMN = 6
REST_COLUMN = 9


class PriceInfo(NamedTuple):
    price: str
    price_purchase: str
    rest: str
    row_id: int


price_data = dict[str, list[PriceInfo]]


class PriceListDataLoader:
    def __init__(self, file_name: str) -> None:
        self.price_list: price_data = {}
        self.file_name = file_name

    def load_price(self) -> bool:
        path = config.UPLOAD_DIR / self.file_name
        if not path.exists():
            return False

        wb = CalamineWorkbook.from_path(str(path))
        data = wb.get_sheet_by_name(SHEET_NAME).to_python()

        for i, row in enumerate(data):
            # skip header
            if i == 0:
                continue
            title = str(row[TITLE_COLUMN]).lower()
            price = str(row[PRICE_SELLING_COLUMN])
            price_purchase = str(row[PRICE_PURCHASE_COLUMN])
            rest = str(row[REST_COLUMN])

            self.price_list.setdefault(title, []).append(PriceInfo(price, price_purchase, rest, i))
        return True

    def get_price_list(self) -> price_data:
        return self.price_list
