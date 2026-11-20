"""Прайсы для поиска: файлы, которые priceformation пишет в file_prices/result."""

import dataclasses
import hashlib
import re
from pathlib import Path

from python_calamine import CalamineWorkbook

from autosnab_bot.services import priceformation_reference as reference
from autosnab_bot.services.priceformation_cli import RESULT_DIR


@dataclasses.dataclass(frozen=True)
class PriceSource:
    key: str
    title: str
    # Имя файла шаблона priceformation с датой формирования: price_drom_akb_2026-11-17.xlsx.
    file_pattern: re.Pattern[str]
    # Как получить прайс, если его ещё нет (HTML).
    how_to_make: str
    sheet_name: str | None = None
    product_groups: tuple[str, ...] = (reference.TIRE,)

    def latest_file(self, folder: Path | None = None) -> Path | None:
        """Самый свежий файл этого прайса (по дате в имени)."""
        folder = folder or RESULT_DIR
        if not folder.is_dir():
            return None
        files = [path for path in folder.iterdir() if self._matches(path)]
        return max(files, key=lambda path: path.name, default=None)

    def _matches(self, path: Path) -> bool:
        return path.is_file() and self.file_pattern.fullmatch(path.name) is not None


SHEET_KEY_LENGTH = 16
_DATE = r'\d{4}-\d{2}-\d{2}'
_VIA_PF = 'Сформируйте его через /pf → «Сформировать общий прайс»'

SOURCES = (
    PriceSource(
        'drom',
        'Прайс для Дрома (АКБ)',
        re.compile(rf'price_drom_akb_{_DATE}\.xlsx'),
        _VIA_PF,
        product_groups=(reference.AKB,),
    ),
    PriceSource('drom_tire', 'Прайс для Дрома (шины)', re.compile(rf'price_drom_tire_{_DATE}\.xlsx'), _VIA_PF),
    PriceSource(
        'inner',
        'Общий прайс',
        re.compile(rf'price_{_DATE}\.xlsx'),
        _VIA_PF,
        product_groups=reference.PRODUCT_GROUPS,
    ),
    PriceSource(
        'full',
        'Полный прайс',
        re.compile(rf'price_full_{_DATE}\.xlsx'),
        'Бот его не формирует: запустите в priceformation <code>uv run pf parse --result-template for_full</code>',
    ),
)
_SHEET_GROUPS = {'Аккумуляторы': (reference.AKB,), 'Шины и диски': (reference.TIRE,)}
SOURCES_BY_KEY = {source.key: source for source in SOURCES}
DEFAULT_SOURCE = SOURCES_BY_KEY['drom']


def get_source(key: str | None) -> PriceSource:
    source = SOURCES_BY_KEY.get(key or '')
    if source is not None:
        return source
    if key is None or not key.startswith('inner:'):
        return DEFAULT_SOURCE
    return next((source for source in get_sources() if source.key == key), DEFAULT_SOURCE)


def get_sources() -> tuple[PriceSource, ...]:
    """Файловые источники и вкладки самого свежего общего прайса."""
    common = SOURCES_BY_KEY['inner']
    path = common.latest_file()
    if path is None:
        return SOURCES
    workbook = CalamineWorkbook.from_path(str(path))
    sheets = tuple(_sheet_source(common, name) for name in workbook.sheet_names)
    return (*SOURCES, *sheets)


def _sheet_source(common: PriceSource, name: str) -> PriceSource:
    # Хеш удерживает callback_data в пределах 64 байт Telegram даже при длинном имени листа.
    suffix = hashlib.sha256(name.encode()).hexdigest()[:SHEET_KEY_LENGTH]
    groups = _SHEET_GROUPS.get(name, common.product_groups)
    return dataclasses.replace(
        common, key=f'inner:{suffix}', title=f'Общий прайс — {name}', sheet_name=name, product_groups=groups
    )
