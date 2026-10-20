import asyncio
import importlib
from typing import Any

import pytest
from telegram.error import BadRequest

from autosnab_bot.services.search_replies import SEARCH_REPLIES
from autosnab_bot.services.type_menu import USER_TYPE_FILTER
from tests.fakes import FakeBot, keyboard_labels, make_context, make_update

# handlers/__init__ экспортирует функцию search, она перекрывает одноимённый модуль.
search_module = importlib.import_module('autosnab_bot.handlers.search')
QUERY_ID = 10
FIRST_REPLY = 101
SECOND_REPLY = 102


@pytest.fixture(autouse=True)
def _fake_reply(monkeypatch: pytest.MonkeyPatch) -> list[str | None]:
    filters: list[str | None] = []

    async def fake_reply(_source: object, product_type: str | None, text: str) -> str:
        filters.append(product_type)
        return f'результат: {text}'

    monkeypatch.setattr(search_module, 'search_reply', fake_reply)
    return filters


def run(update: Any, context: Any) -> None:
    asyncio.run(search_module.search(update, context))


def test_edited_query_replaces_previous_reply() -> None:
    context = make_context()
    run(make_update('185 65', message_id=QUERY_ID), context)
    run(make_update('185 70', edited=True, message_id=QUERY_ID), context)
    assert context.bot.texts == ['результат: 185 65', 'результат: 185 70']
    assert context.bot.deleted == [FIRST_REPLY]
    assert all(message['reply_markup'] is not None for message in context.bot.sent)


def test_edited_query_without_known_reply_sends_new() -> None:
    context = make_context()
    run(make_update('185 70', edited=True), context)
    assert context.bot.texts == ['результат: 185 70']
    assert context.bot.deleted == []


def test_unchanged_result_is_not_resent() -> None:
    context = make_context()
    run(make_update('kama'), context)
    run(make_update('kama', edited=True), context)
    assert context.bot.texts == ['результат: kama']


def test_undeletable_reply_still_gets_new_one() -> None:
    context = make_context(bot=FakeBot(delete_error=BadRequest("Message can't be deleted")))
    run(make_update('kama', message_id=QUERY_ID), context)
    run(make_update('nokian', edited=True, message_id=QUERY_ID), context)
    assert context.bot.texts == ['результат: kama', 'результат: nokian']
    assert context.chat_data[SEARCH_REPLIES][QUERY_ID][0] == SECOND_REPLY


def test_search_uses_type_filter(_fake_reply: list[str | None]) -> None:
    context = make_context({USER_TYPE_FILTER: 'Диск'})
    run(make_update('r15'), context)
    assert _fake_reply == ['Диск']
    assert '✅ Диск' in keyboard_labels(context.bot.sent[-1])


def test_edited_chip_text_is_a_query() -> None:
    context = make_context()
    run(make_update('Диск', edited=True), context)
    assert context.user_data == {}
    assert context.bot.texts == ['результат: Диск']


def test_message_without_text_is_ignored() -> None:
    context = make_context()
    run(make_update(), context)
    assert context.bot.sent == []
