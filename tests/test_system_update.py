import asyncio

import pytest

from autosnab_bot.services import system_update


def test_run_captures_output_and_exit_status() -> None:
    ok = asyncio.run(system_update._run(('echo', 'hello')))
    failed = asyncio.run(system_update._run(('false',)))

    assert ok == system_update.StepResult('echo hello', True, 'hello')
    assert failed.ok is False


def test_update_code_stops_at_failed_pull(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[tuple[str, ...]] = []

    async def fake_run(command: tuple[str, ...]) -> system_update.StepResult:
        commands.append(command)
        return system_update.StepResult(' '.join(command), ok=False, output='conflict')

    monkeypatch.setattr(system_update, '_run', fake_run)
    outcomes = asyncio.run(system_update.update_code())

    assert commands == [system_update.GIT_PULL]
    assert [outcome.ok for outcome in outcomes] == [False]


def test_update_code_runs_pull_then_submodules(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[tuple[str, ...]] = []

    async def fake_run(command: tuple[str, ...]) -> system_update.StepResult:
        commands.append(command)
        return system_update.StepResult(' '.join(command), ok=True, output='')

    monkeypatch.setattr(system_update, '_run', fake_run)
    outcomes = asyncio.run(system_update.update_code())

    assert commands == [system_update.GIT_PULL, system_update.GIT_SUBMODULES]
    assert all(outcome.ok for outcome in outcomes)


def test_restart_service_uses_user_systemd_unit(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[tuple[str, ...]] = []

    async def fake_run(command: tuple[str, ...]) -> system_update.StepResult:
        commands.append(command)
        return system_update.StepResult(' '.join(command), ok=True, output='')

    monkeypatch.setattr(system_update, '_run', fake_run)
    asyncio.run(system_update.restart_service())

    assert commands == [('systemctl', '--user', 'restart', 'autosnab-bot.service')]
