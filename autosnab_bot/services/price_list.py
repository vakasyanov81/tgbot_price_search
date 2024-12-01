import os
from collections import OrderedDict
from pathlib import Path
from typing import NamedTuple

from python_calamine import CalamineWorkbook

from autosnab_bot import config


class PriceInfo(NamedTuple):
    price: str
    price_purchase: str
    rest: str
    row_id: int


price_data = dict[str, list[PriceInfo]]


class PriceListDataLoader:
    def __init__(self, file_name):
        self.price_list: price_data = OrderedDict()
        self.file_name = file_name

    def load_price(self):
        title_index = 2
        price_selling_index = 6
        price_purchase_index = 5
        rest_count_index = 9
        _file = str(config.UPLOAD_DIR) + os.sep + self.file_name
        if not Path(_file).exists():
            return False

        wb = CalamineWorkbook.from_path(_file)

        data = wb.get_sheet_by_name("price").to_python()

        for i, data_ in enumerate(data):
            # skip header
            if i == 0:
                continue
            title = str(data_[title_index]).lower()
            price = str(data_[price_selling_index])
            price_purchase = str(data_[price_purchase_index])
            rest = str(data_[rest_count_index])

            if title not in self.price_list:
                self.price_list[title] = []
            self.price_list[title].append(PriceInfo(price, price_purchase, rest, i))

    def get_price_list(self) -> price_data:
        return self.price_list
