import asyncio
from typing import Any

import pytest

from autosnab_bot import __main__ as bot_main
from autosnab_bot import config, handlers

ALL_USERS = frozenset((1,))
NO_USERS: frozenset[int] = frozenset()


class FakeApplication:
    def __init__(self) -> None:
        self.handlers: list[Any] = []
        self.error_handlers: list[Any] = []
        self.polling = False

    def add_handler(self, bot_handler: Any) -> None:
        self.handlers.append(bot_handler)

    def add_error_handler(self, callback: Any) -> None:
        self.error_handlers.append(callback)

    def run_polling(self) -> None:
        self.polling = True


class FakeBuilder:
    application = FakeApplication()

    def token(self, _token: str) -> FakeBuilder:
        return self

    def persistence(self, _persistence: Any) -> FakeBuilder:
        return self

    def post_init(self, _callback: Any) -> FakeBuilder:
        return self

    def build(self) -> FakeApplication:
        return self.application


def test_main_registers_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, 'TELEGRAM_BOT_TOKEN', 'token')
    monkeypatch.setattr(bot_main, 'ApplicationBuilder', FakeBuilder)
    monkeypatch.setattr(bot_main, 'ALLOWED_USER_IDS', ALL_USERS)
    bot_main.main()
    application = FakeBuilder.application
    assert application.polling
    assert len(application.handlers) == len(bot_main.COMMAND_HANDLERS) + 5
    assert application.error_handlers == [handlers.on_error]


@pytest.mark.parametrize(('token', 'users'), [('', ALL_USERS), ('token', NO_USERS)])
def test_check_config_requires_token_and_users(
    monkeypatch: pytest.MonkeyPatch, token: str, users: frozenset[int]
) -> None:
    monkeypatch.setattr(config, 'TELEGRAM_BOT_TOKEN', token)
    monkeypatch.setattr(bot_main, 'ALLOWED_USER_IDS', users)
    with pytest.raises(ValueError, match=r'in \.env'):
        bot_main.check_config()


def test_warm_up_loads_product_types(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def get_product_types() -> list[str]:
        calls.append('types')
        return []

    monkeypatch.setattr(bot_main, 'get_product_types', get_product_types)
    asyncio.run(bot_main._warm_up(object()))
    assert calls == ['types']
