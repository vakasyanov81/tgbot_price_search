import asyncio
import importlib
from types import SimpleNamespace

import pytest
from telegram.error import BadRequest

from autosnab_bot.handlers import type_filter
from autosnab_bot.services import validate_user

# handlers/__init__ экспортирует функцию search, она перекрывает одноимённый модуль.
search_module = importlib.import_module("autosnab_bot.handlers.search")


class FakeBot:
    def __init__(self, delete_error=None):
        self.sent = []
        self.deleted = []
        self.delete_error = delete_error

    async def send_message(self, **kwargs):
        self.sent.append(kwargs)
        return SimpleNamespace(message_id=100 + len(self.sent))

    async def delete_message(self, chat_id, message_id):
        if self.delete_error:
            raise self.delete_error
        self.deleted.append(message_id)


@pytest.fixture(autouse=True)
def _setup(monkeypatch):
    monkeypatch.setattr(validate_user, "ALLOWED_USER_IDS", frozenset({1}))

    async def fake_response(_context, text):
        return f"результат: {text}"

    monkeypatch.setattr(search_module, "search_response", fake_response)

    async def fake_types():
        return ["Легковая шина", "Диск"]

    monkeypatch.setattr(type_filter, "get_product_types", fake_types)


def make_update(text, message_id=10, edited=False):
    message = SimpleNamespace(text=text, message_id=message_id)
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=1),
        effective_chat=SimpleNamespace(id=1),
        message=None if edited else message,
        edited_message=message if edited else None,
    )


def make_context(bot=None):
    return SimpleNamespace(bot=bot or FakeBot(), chat_data={}, user_data={})


def run(update, context):
    asyncio.run(search_module.search(update, context))  # type: ignore[arg-type]


def texts(bot):
    return [kwargs["text"] for kwargs in bot.sent]


def test_edited_query_replaces_previous_reply():
    context = make_context()
    run(make_update("185 65"), context)
    run(make_update("185 70", edited=True), context)

    assert texts(context.bot) == ["результат: 185 65", "результат: 185 70"]
    assert context.bot.deleted == [101]
    assert context.chat_data[search_module.SEARCH_REPLIES][10][0] == 102


def test_every_reply_carries_menu():
    context = make_context()
    run(make_update("185 65"), context)
    run(make_update("185 70", edited=True), context)

    assert all(kwargs["reply_markup"] is not None for kwargs in context.bot.sent)


def test_edited_query_without_known_reply_sends_new():
    context = make_context()
    run(make_update("185 70", edited=True), context)

    assert texts(context.bot) == ["результат: 185 70"]
    assert context.bot.deleted == []


def test_unchanged_result_is_not_resent():
    context = make_context()
    run(make_update("kama"), context)
    run(make_update("kama", edited=True), context)

    assert texts(context.bot) == ["результат: kama"]
    assert context.bot.deleted == []


def test_undeletable_reply_still_gets_new_one():
    context = make_context(FakeBot(delete_error=BadRequest("Message can't be deleted")))
    run(make_update("kama"), context)
    run(make_update("nokian", edited=True), context)

    assert texts(context.bot) == ["результат: kama", "результат: nokian"]
    assert context.chat_data[search_module.SEARCH_REPLIES][10][0] == 102


def test_legacy_reply_record_is_replaced():
    context = make_context()
    context.chat_data[search_module.SEARCH_REPLIES] = {10: 55}
    run(make_update("nokian", edited=True), context)

    assert context.bot.deleted == [55]
    assert context.chat_data[search_module.SEARCH_REPLIES][10][0] == 101


def test_replies_map_is_bounded(monkeypatch):
    monkeypatch.setattr(search_module, "MAX_SEARCH_REPLIES", 2)
    context = make_context()
    for message_id in (1, 2, 3):
        run(make_update("q", message_id=message_id), context)

    assert list(context.chat_data[search_module.SEARCH_REPLIES]) == [2, 3]
