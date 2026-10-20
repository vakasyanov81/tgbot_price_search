import asyncio
import zipfile
from pathlib import Path

import pytest

from autosnab_bot.services import log_export

JOURNAL = 'журнал сервиса\n'


@pytest.fixture
def log_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    bot_log = tmp_path / 'bot.log'
    pf_logs = tmp_path / 'priceformation' / 'logs'
    pf_logs.mkdir(parents=True)
    monkeypatch.setattr(log_export, 'BOT_LOG', bot_log)
    monkeypatch.setattr(log_export, 'PRICEFORMATION_LOG_DIR', pf_logs)

    async def journal() -> str:
        return JOURNAL

    monkeypatch.setattr(log_export, '_journal', journal)
    return bot_log, pf_logs


def _names(archive: Path) -> list[str]:
    with zipfile.ZipFile(archive) as zipped:
        return sorted(zipped.namelist())


def _read(archive: Path, name: str) -> str:
    with zipfile.ZipFile(archive) as zipped:
        return zipped.read(name).decode()


def test_archive_contains_journal_bot_log_and_priceformation_logs(log_paths: tuple[Path, Path]) -> None:
    bot_log, pf_logs = log_paths
    bot_log.write_text('бот\n', encoding='utf-8')
    (pf_logs / 'parse.log').write_text('парсинг\n', encoding='utf-8')
    (pf_logs / 'mail').mkdir()
    (pf_logs / 'mail' / 'fetch.log').write_text('почта\n', encoding='utf-8')

    archive = asyncio.run(log_export.build_logs_archive())
    try:
        assert _names(archive) == [
            'bot.log',
            'priceformation/mail/fetch.log',
            'priceformation/parse.log',
            'service-journal.log',
        ]
        assert _read(archive, 'service-journal.log') == JOURNAL
        assert _read(archive, 'priceformation/mail/fetch.log') == 'почта\n'
    finally:
        archive.unlink()


def test_archive_keeps_only_last_lines_of_each_log(
    log_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    bot_log, _ = log_paths
    monkeypatch.setattr(log_export, 'LOG_LINES', 2)
    bot_log.write_text('первая\nвторая\nтретья\n', encoding='utf-8')

    archive = asyncio.run(log_export.build_logs_archive())
    try:
        assert _read(archive, 'bot.log') == 'вторая\nтретья\n'
    finally:
        archive.unlink()


def test_archive_without_bot_log_and_priceformation_logs(
    log_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(log_export, 'PRICEFORMATION_LOG_DIR', tmp_path / 'missing')

    archive = asyncio.run(log_export.build_logs_archive())
    try:
        assert _names(archive) == ['service-journal.log']
    finally:
        archive.unlink()


def test_journal_returns_command_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(log_export, 'JOURNAL_COMMAND', ('echo', 'журнал'))
    assert asyncio.run(log_export._journal()) == 'журнал\n'
