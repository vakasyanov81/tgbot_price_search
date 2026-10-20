import os
from pathlib import Path

import pytest

from autosnab_bot.services import price_search_cache
from tests.price_helpers import DROM_HEADER, write_price

LATER = 10


def row(title: str) -> list[object]:
    return ['Шина', '', title, '', '', 1, 1, '']


def test_cache_reloads_changed_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(price_search_cache, '_cache', {})
    path = write_price(tmp_path / 'price_drom_2026-10-20.xlsx', [DROM_HEADER, row('Kama')])
    first = price_search_cache.get_search_instance('drom', path)
    assert price_search_cache.get_search_instance('drom', path) is first

    write_price(path, [DROM_HEADER, row('Nokian')])
    changed_at = path.stat().st_mtime + LATER
    os.utime(path, (changed_at, changed_at))
    second = price_search_cache.get_search_instance('drom', path)
    assert second is not first
    assert 'nokian' in second.search('nokian')
