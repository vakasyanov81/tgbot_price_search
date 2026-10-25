"""Обновление бота: git pull с субмодулями и перезапуск systemd-сервиса (как `just service-restart`)."""

import asyncio
from asyncio.subprocess import PIPE, STDOUT
from dataclasses import dataclass

from autosnab_bot import config

REPO_DIR = config.BASE_DIR.parent
SERVICE_NAME = 'autosnab-bot.service'
GIT_PULL: tuple[str, ...] = ('git', 'pull', '--ff-only')
GIT_SUBMODULES: tuple[str, ...] = ('git', 'submodule', 'update', '--init', '--recursive')
# systemd-run выносит перезапуск в отдельный юнит: иначе systemctl наследует cgroup бота и гибнет вместе с ним
RESTART_COMMAND: tuple[str, ...] = (
    'systemd-run',
    '--user',
    '--collect',
    '--unit=autosnab-bot-restart',
    'systemctl',
    '--user',
    'restart',
    SERVICE_NAME,
)


@dataclass(frozen=True)
class StepResult:
    command: str
    ok: bool
    output: str


async def _run(command: tuple[str, ...]) -> StepResult:
    process = await asyncio.create_subprocess_exec(*command, cwd=REPO_DIR, stdout=PIPE, stderr=STDOUT)
    stdout, _ = await process.communicate()
    output = stdout.decode(errors='replace').strip()
    return StepResult(' '.join(command), process.returncode == 0, output)


async def update_code() -> list[StepResult]:
    pull = await _run(GIT_PULL)
    if not pull.ok:
        return [pull]
    return [pull, await _run(GIT_SUBMODULES)]


async def restart_service() -> StepResult:
    return await _run(RESTART_COMMAND)
