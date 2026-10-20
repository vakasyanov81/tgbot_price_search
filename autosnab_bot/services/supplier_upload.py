"""Загрузка файлов поставщика: собранные файлы, проверка файла и тексты ответов."""

import dataclasses
import html
from collections.abc import Iterable
from pathlib import Path

from telegram import Document
from telegram.constants import FileSizeLimit

from autosnab_bot.services import priceformation
from autosnab_bot.services.priceformation_cli import CommandResult
from autosnab_bot.services.priceformation_output import error_text, placed_names

# Bot API отдаёт ботам файлы не больше 20 МБ.
MAX_FILE_SIZE = FileSizeLimit.FILESIZE_DOWNLOAD


@dataclasses.dataclass
class PendingUpload:
    supplier_id: str
    title: str
    # (file_id, имя файла) в порядке получения.
    files: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    status_message_id: int | None = None

    def add(self, document: Document) -> None:
        name = Path(document.file_name or '').name
        self.files.append((document.file_id, name))

    def targets(self, folder: Path) -> list[tuple[str, Path]]:
        """(file_id, куда скачать) — каждый файл в свою папку, чтобы одинаковые имена не затёрлись."""
        targets: list[tuple[str, Path]] = []
        for index, (file_id, name) in enumerate(self.files):
            targets.append((file_id, folder / str(index) / name))
        return targets

    def collected_text(self) -> str:
        names = bullet_list(name for _, name in self.files)
        return f'Поставщик «{html.escape(self.title)}», файлов: {len(self.files)}\n{names}'


def bullet_list(names: Iterable[str]) -> str:
    return '\n'.join(f'• {html.escape(name)}' for name in names)


def rejection(document: Document) -> str:
    """Почему файл не подходит для загрузки; пустая строка — подходит."""
    if not priceformation.is_supplier_file(document.file_name):
        return 'Неверный формат файла. Подходят xls, xlsx, json или zip-архив с ними'
    if document.file_size and document.file_size > MAX_FILE_SIZE:
        name = html.escape(document.file_name or '')
        return f'Файл {name} больше 20 МБ, бот не может его скачать'
    return ''


def upload_report(title: str, outcome: CommandResult) -> str:
    supplier = html.escape(title)
    if not outcome.ok:
        reason = html.escape(error_text(outcome.output))
        return f'Не удалось загрузить файлы поставщика «{supplier}»: {reason}'
    placed = bullet_list(placed_names(outcome))
    return f'Файлы поставщика «{supplier}» загружены:\n{placed}'
