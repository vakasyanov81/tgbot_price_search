from pathlib import Path

import pytest

from autosnab_bot.services.price_sources import DEFAULT_SOURCE, SOURCES_BY_KEY, get_source

RESULT_FILES = (
    'price_2026-10-19.xlsx',
    'price_2026-10-20.xlsx',
    'price_drom_2026-10-19.xlsx',
    'price_drom_2026-10-20.xlsx',
    'doubles_2026-10-20.xlsx',
    'price_drom_2026-10-21.xlsx.part',
)


@pytest.fixture
def result_dir(tmp_path: Path) -> Path:
    for name in RESULT_FILES:
        (tmp_path / name).write_bytes(b'')
    (tmp_path / 'price_drom_2026-10-22.xlsx').mkdir()
    return tmp_path


@pytest.mark.parametrize(
    ('key', 'expected'),
    [('drom', 'price_drom_2026-10-20.xlsx'), ('inner', 'price_2026-10-20.xlsx'), ('full', None)],
)
def test_latest_file_per_source(result_dir: Path, key: str, expected: str | None) -> None:
    latest = SOURCES_BY_KEY[key].latest_file(result_dir)
    assert getattr(latest, 'name', None) == expected


def test_latest_file_without_result_dir(tmp_path: Path) -> None:
    assert DEFAULT_SOURCE.latest_file(tmp_path / 'missing') is None


def test_get_source_defaults_to_drom() -> None:
    assert DEFAULT_SOURCE.key == 'drom'
    assert get_source(None) is DEFAULT_SOURCE
    assert get_source('unknown') is DEFAULT_SOURCE
    assert get_source('inner').key == 'inner'
