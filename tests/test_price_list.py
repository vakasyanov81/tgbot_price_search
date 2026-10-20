from pathlib import Path

from autosnab_bot.services.price_list import PriceInfo, PriceListDataLoader
from autosnab_bot.services.price_search import PriceListSearch
from autosnab_bot.services.search_format import prepare_search_result
from tests.price_helpers import DROM_HEADER, INNER_HEADER, write_price

KAMA_TITLE = 'Kama 185/65R15'
KAMA_KEY = 'kama 185/65r15'
TIRE = 'Шина'
POSHK = 'Пошк'


def drom_row(title: str) -> list[object]:
    return [TIRE, 'Kama', title, 'Лето', '', 5000, 4, '']


def test_reads_columns_by_header_drom(tmp_path: Path) -> None:
    path = write_price(tmp_path / 'drom.xlsx', [DROM_HEADER, drom_row(KAMA_TITLE)])
    loader = PriceListDataLoader(path)
    assert loader.load_price() is True
    expected = PriceInfo('5000.0', '', '4.0', 1, '', TIRE, KAMA_TITLE)
    assert loader.get_price_list() == {KAMA_KEY: [expected]}


def test_reads_supplier_and_purchase_inner(tmp_path: Path) -> None:
    priced = (TIRE, KAMA_TITLE, 4000, 5000, 4, POSHK)
    rows = [INNER_HEADER, priced, (TIRE, None, 1, 2, 3, POSHK)]
    loader = PriceListDataLoader(write_price(tmp_path / 'inner.xlsx', rows))
    assert loader.load_price() is True
    expected = PriceInfo('5000.0', '4000.0', '4.0', 1, POSHK, TIRE, KAMA_TITLE)
    assert loader.get_price_list() == {KAMA_KEY: [expected]}


def test_strips_corrected_type_mark(tmp_path: Path) -> None:
    rows = [INNER_HEADER, ('Легкогрузовая шина*', 'Kama 185R14C', 1, 2, 3, POSHK)]
    loader = PriceListDataLoader(write_price(tmp_path / 'inner.xlsx', rows))
    loader.load_price()
    assert loader.get_price_list()['kama 185r14c'][0].product_type == 'Легкогрузовая шина'


def test_short_row_gives_empty_cells(tmp_path: Path) -> None:
    path = write_price(tmp_path / 'short.xlsx', [DROM_HEADER, (TIRE, 'Kama', KAMA_TITLE)])
    loader = PriceListDataLoader(path)
    loader.load_price()
    assert loader.get_price_list()[KAMA_KEY][0].price == ''


def test_rejects_file_without_title_column(tmp_path: Path) -> None:
    path = write_price(tmp_path / 'bad.xlsx', [('Цена', 'Остаток'), (1, 2)])
    assert PriceListDataLoader(path).load_price() is False


def test_rejects_empty_sheet_and_missing_file(tmp_path: Path) -> None:
    assert PriceListDataLoader(write_price(tmp_path / 'empty.xlsx', [])).load_price() is False
    assert PriceListDataLoader(tmp_path / 'missing.xlsx').load_price() is False


def test_result_keeps_original_case(tmp_path: Path) -> None:
    title = 'Kama 185/65R15 Breeze 88T'
    path = write_price(tmp_path / 'drom.xlsx', [DROM_HEADER, drom_row(title)])
    found = PriceListSearch(PriceListDataLoader(path)).search('KAMA 185/65r15')
    assert list(found) == [title.lower()]
    assert prepare_search_result(found) == f'1. {title} - 5000Руб. 4 шт.'
