import asyncio
import datetime
import os
import time
from pathlib import Path
from typing import Any

import pytest

from autosnab_bot.services import priceformation_cli

TAIL_LIMIT = 30
LINES = 100
OLD = 100


class FakeProcess:
    def __init__(self, stdout: bytes, returncode: int | None = 0, hangs: bool = False) -> None:
        self.returncode = returncode
        self.killed = False
        self._stdout = stdout
        self._hangs = hangs

    async def communicate(self) -> tuple[bytes, None]:
        if self._hangs:
            await asyncio.sleep(1)
        return self._stdout, None

    def kill(self) -> None:
        self.killed = True

    async def wait(self) -> int:
        return -1


def fake_exec(monkeypatch: pytest.MonkeyPatch, process: FakeProcess) -> dict[str, Any]:
    call: dict[str, Any] = {}

    async def create_subprocess_exec(*args: str, **kwargs: Any) -> FakeProcess:
        call.update(args=args, **kwargs)
        return process

    monkeypatch.setattr(asyncio, 'create_subprocess_exec', create_subprocess_exec)
    return call


def test_run_command_strips_ansi_and_hides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'secret')
    call = fake_exec(monkeypatch, FakeProcess(b'\x1b[91m[ERROR]\x1b[0m: no prices', returncode=1))
    outcome = asyncio.run(priceformation_cli.run_command('parse'))
    assert outcome == priceformation_cli.CommandResult(1, '[ERROR]: no prices')
    assert call['args'][-2:] == ('priceformation', 'parse')
    assert 'TELEGRAM_BOT_TOKEN' not in call['env']


def test_run_command_timeout_kills_process(monkeypatch: pytest.MonkeyPatch) -> None:
    process = FakeProcess(b'', hangs=True)
    fake_exec(monkeypatch, process)
    monkeypatch.setattr(priceformation_cli, 'COMMAND_TIMEOUT', datetime.timedelta(0))
    outcome = asyncio.run(priceformation_cli.run_command('parse'))
    assert process.killed
    assert not outcome.ok


def test_command_result_json_skips_uv_warnings() -> None:
    outcome = priceformation_cli.CommandResult(0, 'warning: something\n{"1": {"sup_title": "Пошк"}}\n')
    assert outcome.json() == {'1': {'sup_title': 'Пошк'}}


def test_strip_ansi() -> None:
    assert priceformation_cli.strip_ansi('\x1b[91m[ERROR]\x1b[0m: нет прайсов') == '[ERROR]: нет прайсов'


def test_tail_keeps_short_text() -> None:
    assert priceformation_cli.tail('  строка 1\nстрока 2\n', LINES) == 'строка 1\nстрока 2'


def test_tail_cuts_by_whole_lines() -> None:
    text = '\n'.join(f'line {index}' for index in range(LINES))
    cut = priceformation_cli.tail(text, TAIL_LIMIT)
    last = LINES - 1
    assert cut.startswith('…\n')
    assert cut.endswith(f'line {last}')
    kept = cut.splitlines()[1:]
    assert all(line.startswith('line ') for line in kept)


def test_tail_of_single_long_line() -> None:
    assert priceformation_cli.tail('x' * LINES, TAIL_LIMIT) == '…\n' + 'x' * TAIL_LIMIT


def test_result_files_since(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(priceformation_cli, 'RESULT_DIR', tmp_path)
    old = tmp_path / 'old.xlsx'
    old.write_text('')
    old_time = time.time() - OLD
    os.utime(old, (old_time, old_time))
    started = time.time() - 1
    new = tmp_path / 'for_drom.xlsx'
    new.write_text('')
    (tmp_path / 'subdir').mkdir()
    assert priceformation_cli.result_files_since(started) == [new]


def test_result_files_since_without_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(priceformation_cli, 'RESULT_DIR', tmp_path / 'missing')
    assert priceformation_cli.result_files_since(0) == []


def test_is_available(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(priceformation_cli, 'PRICEFORMATION_DIR', tmp_path)
    assert not priceformation_cli.is_available()
    (tmp_path / 'pyproject.toml').write_text('')
    assert priceformation_cli.is_available()
