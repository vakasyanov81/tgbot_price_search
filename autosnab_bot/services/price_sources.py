"""Прайсы для поиска: файлы, которые priceformation пишет в file_prices/result."""

import dataclasses
import re
from pathlib import Path

from autosnab_bot.services.priceformation import RESULT_DIR


@dataclasses.dataclass(frozen=True)
class PriceSource:
    key: str
    title: str
    # Имя файла шаблона priceformation с датой формирования: price_drom_2026-10-20.xlsx.
    file_pattern: re.Pattern[str]
    # Как получить прайс, если его ещё нет (HTML).
    how_to_make: str

    def latest_file(self, folder: Path | None = None) -> Path | None:
        """Самый свежий файл этого прайса (по дате в имени)."""
        folder = folder or RESULT_DIR
        if not folder.is_dir():
            return None
        files = [path for path in folder.iterdir() if path.is_file() and self.file_pattern.fullmatch(path.name)]
        return max(files, key=lambda path: path.name, default=None)


_DATE = r"\d{4}-\d{2}-\d{2}"
_VIA_PF = "Сформируйте его через /pf → «Сформировать общий прайс»"

SOURCES = (
    PriceSource("drom", "Прайс для Дрома", re.compile(rf"price_drom_{_DATE}\.xlsx"), _VIA_PF),
    PriceSource("inner", "Общий прайс", re.compile(rf"price_{_DATE}\.xlsx"), _VIA_PF),
    PriceSource(
        "full",
        "Полный прайс",
        re.compile(rf"price_full_{_DATE}\.xlsx"),
        "Бот его не формирует: запустите в priceformation <code>uv run pf parse --result-template for_full</code>",
    ),
)
SOURCES_BY_KEY = {source.key: source for source in SOURCES}
DEFAULT_SOURCE = SOURCES_BY_KEY["drom"]


def get_source(key: str | None) -> PriceSource:
    return SOURCES_BY_KEY.get(key or "", DEFAULT_SOURCE)
