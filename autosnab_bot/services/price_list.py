import os
from collections import OrderedDict
from pathlib import Path
from typing import NamedTuple, Type

import prettytable as pt
from python_calamine import CalamineWorkbook

from autosnab_bot import config


class PriceInfo(NamedTuple):
    price: str
    price_purchase: str
    rest: str
    row_id: int


price_data = dict[str, list[PriceInfo]]


class PriceSearchInterface:
    def __init__(self, price_list: price_data):
        self.price_list = price_list

    def search(self, search_string: str, search_limit: int):
        raise NotImplementedError


class PriceListSimple:
    def __init__(
        self, search_driver: Type["PriceSearchInterface"], price_list: price_data
    ):
        self.search_driver = search_driver
        self.price_list = price_list

    def search(self, search_string: str, search_limit=10):
        return self.search_driver(self.price_list).search(search_string, search_limit)


class PriceList:
    _is_loaded = False

    def __init__(self, search_driver: Type["PriceSearchInterface"], file_name):
        self.price_list: price_data = OrderedDict()
        self.file_name = file_name
        self.search_driver = search_driver

    def search(self, search_string: str, search_limit=10):
        return self.search_driver(self.price_list).search(search_string, search_limit)

    def load_price(self):
        _file = str(config.UPLOAD_DIR) + os.sep + self.file_name
        if not Path(_file).exists():
            return False

        wb = CalamineWorkbook.from_path(_file)

        data = wb.get_sheet_by_name("price").to_python()

        for i, data_ in enumerate(data):
            # skip header
            if i == 0:
                continue
            title = str(data_[2]).lower()
            price = str(data_[6])  # цена продажи
            price_purchase = str(data_[5])  # цена закупочная
            rest = str(data_[9])
            if title not in self.price_list:
                self.price_list[title] = []
            self.price_list[title].append(PriceInfo(price, price_purchase, rest, i))

        self._is_loaded = True

    def clear(self):
        self.price_list = OrderedDict()

    def price_is_loaded(self):
        return self._is_loaded


class PriceListSearch(PriceSearchInterface):
    def search(self, search_string: str, search_limit=10):
        """Поиск по названию позиции в прайсе"""
        result = self.strict_search(
            search_string, search_limit
        ) or self.no_accurate_search(search_string, search_limit)
        return result

    def strict_search(self, search_string: str, search_limit=10):
        """Строгий поиск по точному вхождению"""
        result = dict()
        search_string = search_string.lower()
        search_count = 0

        for title, prices in self.price_list.items():
            if search_string in title:
                result[title] = prices
                search_count += 1
            if search_count >= search_limit:
                break
        return result

    def no_accurate_search(self, search_string: str, search_limit=10):
        """Не строгий поиск"""
        result = dict()
        search_string = search_string.lower()
        search_count = 0
        search_chunks = [s.strip() for s in search_string.split() if len(s.strip())]
        search_chunks_len = len(search_chunks)
        if search_chunks_len == 1:
            return result

        for title, prices in self.price_list.items():
            searched_chunk_count = 0
            for search_chunk in search_chunks:
                if search_chunk in title:
                    searched_chunk_count += 1
            if searched_chunk_count == search_chunks_len:
                result[title] = prices
                search_count += 1
            if search_count >= search_limit:
                break
        return result


def prepare_search_result(result):
    # print(result)
    table = pt.PrettyTable(["название", "цена", "остаток"])
    table.align["название"] = "l"
    table.align["цена"] = "r"
    table.align["остаток"] = "r"
    for title, prices in result.items():
        table.add_row(
            (title, f"{prices[0].price_purchase}/{prices[0].price}", prices[0].rest)
        )
    # response_txt = ''  # find_nomenclature(message.text)
    response_txt = f"```{table}```"
    # print(f"response: {response_txt}")
    return response_txt


def get_instance_price_list(
    price_driver: str, search_driver: str = "PriceListSearch", *args
):
    price_driver_instances = {
        "PriceList": PriceList,
        "PriceListSimple": PriceListSimple,
    }
    search_driver_instance = {"PriceListSearch": PriceListSearch}

    instance = price_driver_instances[price_driver]

    return instance(search_driver_instance.get(search_driver), *args)


price_list_instance = get_instance_price_list(
    "PriceList", "PriceListSearch", "price.xlsx"
)
price_list_instance.load_price()
