"""Помощники тестов прайса: позиция, загрузчик-заглушка и запись xlsx."""

from collections.abc import Callable, Sequence
from pathlib import Path

from openpyxl import Workbook

from autosnab_bot.services.price_list import PriceInfo, price_data

DROM_HEADER = ('Тип товара', 'Бренд', 'Номенклатура', 'Сезон', 'Шип', 'Цена', 'Остаток', 'Наличие')
INNER_HEADER = ('Тип товара', 'Номенклатура', 'Цена закуп.', 'Цена', 'Остаток', 'Поставщик')


class StubLoader:
    def __init__(self, titles_prices: price_data, loaded: bool = True) -> None:
        self._titles_prices = titles_prices
        self._loaded = loaded

    def load_price(self) -> bool:
        return self._loaded

    def get_price_list(self) -> price_data:
        return self._titles_prices


def price_info(price: str, row_id: int = 1, supplier: str = '', product_type: str = '') -> PriceInfo:
    return PriceInfo(price, '', '1', row_id, supplier=supplier, product_type=product_type)


def numbered_prices(prefix: str, count: int, price_of: Callable[[int], int]) -> price_data:
    """Позиции «prefix 0» … «prefix count-1» с ценой price_of(номер)."""
    titles_prices: price_data = {}
    for index in range(count):
        price = str(price_of(index))
        titles_prices[f'{prefix} {index}'] = [price_info(price, index)]
    return titles_prices


def write_price(path: Path, rows: Sequence[Sequence[object]], sheet: str = 'price') -> Path:
    workbook = Workbook()
    worksheet = workbook.active
    assert worksheet is not None
    worksheet.title = sheet
    for row in rows:
        worksheet.append(list(row))
    workbook.save(path)
    return path
