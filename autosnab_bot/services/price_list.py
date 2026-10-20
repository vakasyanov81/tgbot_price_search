from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

from python_calamine import CalamineWorkbook

SHEET_NAME = 'price'
# Колонки ищутся по заголовку: у шаблонов priceformation (Дром, общий, полный) разный набор и порядок колонок.
TITLE_HEADER = 'Номенклатура'
PRICE_SELLING_HEADER = 'Цена'
PRICE_PURCHASE_HEADER = 'Цена закуп.'
REST_HEADER = 'Остаток'
SUPPLIER_HEADER = 'Поставщик'
PRODUCT_TYPE_HEADER = 'Тип товара'
# priceformation помечает звёздочкой тип, исправленный по названию: «Легкогрузовая шина*».
CORRECTED_TYPE_MARK = '*'


class PriceInfo(NamedTuple):
    price: str
    price_purchase: str
    rest: str
    row_id: int
    supplier: str = ''
    product_type: str = ''
    # Название как в прайсе; ключ словаря — оно же в нижнем регистре, для поиска без учёта регистра.
    title: str = ''


price_data = dict[str, list[PriceInfo]]


class _Columns:
    """Номера колонок по заголовку (первое вхождение)."""

    def __init__(self, header: Sequence[object]) -> None:
        self._positions: dict[str, int] = {}
        for position, name in enumerate(header):
            self._positions.setdefault(str(name).strip(), position)

    def has(self, name: str) -> bool:
        return name in self._positions

    def cell(self, row: Sequence[object], name: str) -> str:
        position = self._positions.get(name)
        if position is None or position >= len(row):
            return ''
        return str(row[position])


class PriceListDataLoader:
    def __init__(self, path: Path) -> None:
        self.price_list: price_data = {}
        self.path = path

    def load_price(self) -> bool:
        rows = self._read_rows()
        if not rows:
            return False
        columns = _Columns(rows[0])
        if not columns.has(TITLE_HEADER):
            return False
        for row_id, row in enumerate(rows[1:], start=1):
            self._add_row(columns, row, row_id)
        return True

    def get_price_list(self) -> price_data:
        return self.price_list

    def _read_rows(self) -> Sequence[Sequence[object]]:
        if not self.path.exists():
            return []
        workbook = CalamineWorkbook.from_path(str(self.path))
        rows: Sequence[Sequence[object]] = workbook.get_sheet_by_name(SHEET_NAME).to_python()
        return rows

    def _add_row(self, columns: _Columns, row: Sequence[object], row_id: int) -> None:
        title = columns.cell(row, TITLE_HEADER).strip()
        if not title:
            return
        product_type = columns.cell(row, PRODUCT_TYPE_HEADER).strip()
        price_info = PriceInfo(
            price=columns.cell(row, PRICE_SELLING_HEADER),
            price_purchase=columns.cell(row, PRICE_PURCHASE_HEADER),
            rest=columns.cell(row, REST_HEADER),
            row_id=row_id,
            supplier=columns.cell(row, SUPPLIER_HEADER),
            product_type=product_type.removesuffix(CORRECTED_TYPE_MARK),
            title=title,
        )
        self.price_list.setdefault(title.lower(), []).append(price_info)
