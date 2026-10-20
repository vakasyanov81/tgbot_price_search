import os

import pytest
from openpyxl import Workbook

from autosnab_bot.services import price_search_cache
from autosnab_bot.services.price_list import PriceInfo, PriceListDataLoader
from autosnab_bot.services.price_search import prepare_search_result
from autosnab_bot.services.price_sources import DEFAULT_SOURCE, SOURCES_BY_KEY, get_source

DROM_HEADER = ["Тип товара", "Бренд", "Номенклатура", "Сезон", "Шип", "Цена", "Остаток", "Наличие"]
INNER_HEADER = ["Тип товара", "Номенклатура", "Цена закуп.", "Цена", "Остаток", "Поставщик"]


def write_price(path, rows, sheet="price"):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    for row in rows:
        ws.append(row)
    wb.save(path)
    return path


@pytest.fixture
def result_dir(tmp_path):
    for name in (
        "price_2026-10-19.xlsx",
        "price_2026-10-20.xlsx",
        "price_drom_2026-10-19.xlsx",
        "price_drom_2026-10-20.xlsx",
        "doubles_2026-10-20.xlsx",
        "price_drom_2026-10-21.xlsx.part",
    ):
        (tmp_path / name).write_bytes(b"")
    return tmp_path


@pytest.mark.parametrize(
    ("key", "expected"),
    [("drom", "price_drom_2026-10-20.xlsx"), ("inner", "price_2026-10-20.xlsx"), ("full", None)],
)
def test_latest_file_per_source(result_dir, key, expected):
    latest = SOURCES_BY_KEY[key].latest_file(result_dir)
    assert (latest.name if latest else None) == expected


def test_latest_file_without_result_dir(tmp_path):
    assert DEFAULT_SOURCE.latest_file(tmp_path / "missing") is None


def test_get_source_defaults_to_drom():
    assert DEFAULT_SOURCE.key == "drom"
    assert get_source(None) is DEFAULT_SOURCE
    assert get_source("unknown") is DEFAULT_SOURCE
    assert get_source("inner").key == "inner"


def test_loader_reads_columns_by_header_drom(tmp_path):
    path = write_price(
        tmp_path / "drom.xlsx",
        [DROM_HEADER, ["Шина", "Kama", "Kama 185/65R15", "Лето", "", 5000, 4, "В наличии"]],
    )
    loader = PriceListDataLoader(path)
    assert loader.load_price() is True
    assert loader.get_price_list() == {"kama 185/65r15": [PriceInfo("5000.0", "", "4.0", 1, "")]}


def test_loader_reads_supplier_and_purchase_inner(tmp_path):
    path = write_price(
        tmp_path / "inner.xlsx",
        [INNER_HEADER, ["Шина", "Kama 185/65R15", 4000, 5000, 4, "Пошк"], ["Шина", None, 1, 2, 3, "Пошк"]],
    )
    loader = PriceListDataLoader(path)
    assert loader.load_price() is True
    assert loader.get_price_list() == {"kama 185/65r15": [PriceInfo("5000.0", "4000.0", "4.0", 1, "Пошк")]}


def test_loader_rejects_file_without_title_column(tmp_path):
    path = write_price(tmp_path / "bad.xlsx", [["Цена", "Остаток"], [1, 2]])
    assert PriceListDataLoader(path).load_price() is False


def test_prepare_search_result_shows_supplier():
    result = {"kama": [PriceInfo("5000.0", "4000", "4.0", 1, "Пошк")], "nokian": [PriceInfo("7000", "", "2", 2)]}
    assert prepare_search_result(result) == "1. kama - 5000Руб. 4 шт. (Пошк)\n2. nokian - 7000Руб. 2 шт."


def test_cache_reloads_changed_file(tmp_path, monkeypatch):
    monkeypatch.setattr(price_search_cache, "_cache", {})
    path = write_price(tmp_path / "price_drom_2026-10-20.xlsx", [DROM_HEADER, ["Шина", "", "Kama", "", "", 1, 1, ""]])
    first = price_search_cache.get_search_instance("drom", path)
    assert price_search_cache.get_search_instance("drom", path) is first

    write_price(path, [DROM_HEADER, ["Шина", "", "Nokian", "", "", 1, 1, ""]])
    os.utime(path, (path.stat().st_atime, path.stat().st_mtime + 10))
    second = price_search_cache.get_search_instance("drom", path)
    assert second is not first
    assert "nokian" in second.search("nokian")
