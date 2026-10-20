"""Запуск CLI priceformation (git-сабмодуль) отдельным процессом и разбор его вывода."""

import asyncio
import dataclasses
import datetime
import json
import os
import re
from pathlib import Path

from autosnab_bot import config

PRICEFORMATION_DIR = config.BASE_DIR.parent / 'priceformation'
RESULT_DIR = PRICEFORMATION_DIR / 'file_prices' / 'result'
README_FILE = PRICEFORMATION_DIR / 'README.md'

COMMAND_TIMEOUT = datetime.timedelta(hours=0.5)
# Сколько последних символов вывода показывать, когда CLI не ответил JSON.
ERROR_TAIL = 300

# VIRTUAL_ENV бота сбивает uv с окружения сабмодуля, а токен бота priceformation не нужен.
_HIDDEN_ENV = frozenset(('VIRTUAL_ENV', 'TELEGRAM_BOT_TOKEN'))
_ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')


@dataclasses.dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def json(self) -> object:
        """JSON-ответ CLI: последняя строка вывода (выше могут быть предупреждения uv)."""
        last_line = self.output.strip().rsplit('\n', 1)[-1]
        return json.loads(last_line)


def is_available() -> bool:
    return (PRICEFORMATION_DIR / 'pyproject.toml').is_file()


async def run_command(*args: str) -> CommandResult:
    """Запустить `priceformation <args>` в окружении сабмодуля, stdout и stderr вместе."""
    process = await asyncio.create_subprocess_exec(
        'uv',
        'run',
        '--project',
        str(PRICEFORMATION_DIR),
        'priceformation',
        *args,
        cwd=PRICEFORMATION_DIR,
        env=_command_env(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    timeout = COMMAND_TIMEOUT.total_seconds()
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except TimeoutError:
        process.kill()
        await process.wait()
        return CommandResult(-1, f'Команда не завершилась за {COMMAND_TIMEOUT} и была остановлена')
    return CommandResult(process.returncode or 0, strip_ansi(stdout.decode(errors='replace')))


def result_files_since(started: float) -> list[Path]:
    """Файлы результата, записанные не раньше started (время из time.time())."""
    if not RESULT_DIR.is_dir():
        return []
    written = (path for path in RESULT_DIR.iterdir() if path.is_file())
    return sorted(path for path in written if path.stat().st_mtime >= started)


def strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub('', text)


def tail(text: str, limit: int) -> str:
    """Последние строки текста, не длиннее limit символов."""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[-limit:]
    newline = cut.find('\n')
    whole_lines = cut if newline == -1 else cut[newline + 1 :]
    return f'…\n{whole_lines}'


def _command_env() -> dict[str, str]:
    return {name: env_value for name, env_value in os.environ.items() if name not in _HIDDEN_ENV}
