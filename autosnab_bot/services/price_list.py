from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import NamedTuple

from python_calamine import CalamineWorkbook

# Колонки ищутся по заголовку: у шаблонов priceformation (Дром, общий, полный) разный набор и порядок колонок.
TITLE_HEADER = 'Номенклатура'
PRICE_SELLING_HEADER = 'Цена'
PRICE_PURCHASE_HEADER = 'Цена закуп.'
REST_HEADER = 'Остаток'
SUPPLIER_HEADER = 'Поставщик'
PRODUCT_TYPE_HEADER = 'Тип товара'
# priceformation помечает звёздочкой тип, исправленный по названию: «Легкогрузовая шина*».
CORRECTED_TYPE_MARK = '*'
HEADER_ALIASES = {
    'Название': TITLE_HEADER,
    'Цена продажи': PRICE_SELLING_HEADER,
    'Закупочная цена': PRICE_PURCHASE_HEADER,
}


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
type SheetRows = Sequence[Sequence[object]]


class _Columns:
    """Номера колонок по заголовку (первое вхождение)."""

    def __init__(self, header: Sequence[object]) -> None:
        self._positions: dict[str, int] = {}
        for position, name in enumerate(header):
            normalized = str(name).strip()
            self._positions.setdefault(HEADER_ALIASES.get(normalized, normalized), position)

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
        loaded = False
        for sheet_name, rows in self._read_sheets():
            loaded = self._load_sheet(sheet_name, rows) or loaded
        return loaded

    def get_price_list(self) -> price_data:
        return self.price_list

    def _load_sheet(self, sheet_name: str, rows: Sequence[Sequence[object]]) -> bool:
        if not rows:
            return False
        columns = _Columns(rows[0])
        if not columns.has(TITLE_HEADER):
            return False
        default_type = 'Аккумулятор' if sheet_name == 'Аккумуляторы' else ''
        for row_id, row in enumerate(rows[1:], start=1):
            self._add_row(columns, row, row_id, default_type)
        return True

    def _read_sheets(self) -> Iterator[tuple[str, SheetRows]]:
        if not self.path.exists():
            return
        workbook = CalamineWorkbook.from_path(str(self.path))
        for name in workbook.sheet_names:
            yield name, workbook.get_sheet_by_name(name).to_python()

    def _add_row(self, columns: _Columns, row: Sequence[object], row_id: int, default_type: str) -> None:
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
            product_type=product_type.removesuffix(CORRECTED_TYPE_MARK) or default_type,
            title=title,
        )
        self.price_list.setdefault(title.lower(), []).append(price_info)
