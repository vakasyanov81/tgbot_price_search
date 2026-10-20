"""Сбор логов для выгрузки в Telegram: журнал сервиса, bot.log и логи priceformation в один zip."""

import asyncio
import datetime
import tempfile
import zipfile
from asyncio.subprocess import PIPE, STDOUT
from collections import deque
from pathlib import Path

from autosnab_bot.services.priceformation_cli import PRICEFORMATION_DIR
from autosnab_bot.services.system_update import REPO_DIR, SERVICE_NAME

JOURNAL_COMMAND: tuple[str, ...] = ('journalctl', '--user', '-u', SERVICE_NAME, '--no-pager')
BOT_LOG = REPO_DIR / 'bot.log'
PRICEFORMATION_LOG_DIR = PRICEFORMATION_DIR / 'logs'
# Сколько последних строк брать из каждого текстового лога: файлы растут, а Telegram принимает до 50 МБ.
LOG_LINES = 5000


async def _journal() -> str:
    process = await asyncio.create_subprocess_exec(*JOURNAL_COMMAND, stdout=PIPE, stderr=STDOUT)
    stdout, _ = await process.communicate()
    return stdout.decode(errors='replace')


def _tail(path: Path) -> str:
    with path.open(encoding='utf-8', errors='replace') as log_file:
        return ''.join(deque(log_file, maxlen=LOG_LINES))


def _priceformation_logs() -> list[Path]:
    if not PRICEFORMATION_LOG_DIR.is_dir():
        return []
    return sorted(path for path in PRICEFORMATION_LOG_DIR.rglob('*') if path.is_file())


def _new_archive_path() -> Path:
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    with tempfile.NamedTemporaryFile(prefix=f'autosnab-logs-{stamp}-', suffix='.zip', delete=False) as archive_file:
        return Path(archive_file.name)


def _fill_archive(archive: zipfile.ZipFile, journal: str) -> None:
    archive.writestr('service-journal.log', journal)
    if BOT_LOG.is_file():
        archive.writestr('bot.log', _tail(BOT_LOG))
    for log_file in _priceformation_logs():
        arcname = log_file.relative_to(PRICEFORMATION_LOG_DIR).as_posix()
        archive.writestr(f'priceformation/{arcname}', _tail(log_file))


def _write_archive(journal: str) -> Path:
    path = _new_archive_path()
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        _fill_archive(archive, journal)
    return path


async def build_logs_archive() -> Path:
    journal = await _journal()
    return await asyncio.to_thread(_write_archive, journal)
