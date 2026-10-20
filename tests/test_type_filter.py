import asyncio
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from autosnab_bot.handlers import type_filter
from autosnab_bot.services import product_types, type_menu, validate_user
from autosnab_bot.services.price_list import PriceInfo
from autosnab_bot.services.price_search import PriceListSearch

search_module = importlib.import_module("autosnab_bot.handlers.search")
TYPES = ["Легковая шина", "Грузовая шина", "Диск"]


class Loader:
    def __init__(self, items):
        self.items = items

    def load_price(self):
        return True

    def get_price_list(self):
        return self.items


class FakeBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, **kwargs):
        self.sent.append(kwargs)
        return SimpleNamespace(message_id=len(self.sent))


@pytest.fixture(autouse=True)
def _setup(monkeypatch):
    monkeypatch.setattr(validate_user, "ALLOWED_USER_IDS", frozenset({1}))

    async def fake_types():
        return TYPES

    monkeypatch.setattr(type_filter, "get_product_types", fake_types)
    monkeypatch.setattr(type_menu, "get_product_types", fake_types)


def make_context(user_data=None):
    return SimpleNamespace(bot=FakeBot(), user_data={} if user_data is None else user_data, chat_data={})


def make_update(text, edited=False):
    message = SimpleNamespace(text=text, message_id=10)
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=1),
        effective_chat=SimpleNamespace(id=1),
        message=None if edited else message,
        edited_message=message if edited else None,
    )


def keyboard_labels(sent):
    return [button.text for row in sent["reply_markup"].keyboard for button in row]


def test_search_filters_by_product_type():
    search = PriceListSearch(
        Loader(
            {
                "kama 185/65r15": [PriceInfo("1", "", "1", 1, product_type="Легковая шина")],
                "kama 185/65r15 диск": [PriceInfo("2", "", "1", 2, product_type="Диск")],
            }
        )
    )
    assert list(search.search("kama")) == ["kama 185/65r15", "kama 185/65r15 диск"]
    assert list(search.search("kama", product_type="Диск")) == ["kama 185/65r15 диск"]
    assert list(search.search("kama 185", product_type="Грузовая шина")) == []


def test_keyboard_marks_active_type():
    keyboard = asyncio.run(type_menu.type_keyboard(make_context({type_menu.USER_TYPE_FILTER: "Диск"})))
    assert [[button.text for button in row] for row in keyboard.keyboard] == [
        ["Все", "Легковая шина"],
        ["Грузовая шина", "✅ Диск"],
    ]
    assert keyboard.resize_keyboard is True


def test_chip_sets_and_clears_filter():
    context = make_context()
    asyncio.run(search_module.search(make_update("Легковая шина"), context))  # type: ignore[arg-type]
    assert context.user_data == {type_menu.USER_TYPE_FILTER: "Легковая шина"}
    assert "✅ Легковая шина" in keyboard_labels(context.bot.sent[-1])

    asyncio.run(search_module.search(make_update("✅ Легковая шина"), context))  # type: ignore[arg-type]
    assert context.user_data == {type_menu.USER_TYPE_FILTER: "Легковая шина"}

    asyncio.run(search_module.search(make_update("Все"), context))  # type: ignore[arg-type]
    assert context.user_data == {}
    assert "✅ Все" in keyboard_labels(context.bot.sent[-1])


def test_search_uses_type_filter(monkeypatch):
    seen = {}

    async def fake_response(context, text):
        seen["type"] = type_menu.user_type_filter(context)
        return f"результат: {text}"

    monkeypatch.setattr(search_module, "search_response", fake_response)
    context = make_context({type_menu.USER_TYPE_FILTER: "Диск"})
    asyncio.run(search_module.search(make_update("r15"), context))  # type: ignore[arg-type]
    assert seen == {"type": "Диск"}
    assert context.bot.sent[-1]["text"] == "результат: r15"


def test_edited_message_with_chip_text_is_a_query(monkeypatch):
    async def fake_response(_context, text):
        return f"результат: {text}"

    monkeypatch.setattr(search_module, "search_response", fake_response)
    context = make_context()
    asyncio.run(search_module.search(make_update("Диск", edited=True), context))  # type: ignore[arg-type]
    assert context.user_data == {}
    assert context.bot.sent[-1]["text"] == "результат: Диск"


def test_product_types_cache_keeps_last_list_on_error(monkeypatch):
    calls = []

    async def ok():
        calls.append("ok")
        return ["Диск"]

    async def fail():
        raise RuntimeError("cli down")

    monkeypatch.setattr(product_types, "_types", [])
    monkeypatch.setattr(product_types.priceformation, "get_product_types", ok)
    assert asyncio.run(product_types.get_product_types()) == ["Диск"]
    assert asyncio.run(product_types.get_product_types()) == ["Диск"]
    assert calls == ["ok"]

    monkeypatch.setattr(product_types, "_loaded_at", 0.0)
    monkeypatch.setattr(product_types.priceformation, "get_product_types", fail)
    assert asyncio.run(product_types.get_product_types()) == ["Диск"]


def test_every_plain_reply_carries_menu(monkeypatch):
    async def fake_response(_context, text):
        return f"результат: {text}"

    monkeypatch.setattr(search_module, "search_response", fake_response)
    context = make_context({type_menu.USER_TYPE_FILTER: "Диск"})
    asyncio.run(search_module.search(make_update("r15"), context))  # type: ignore[arg-type]
    assert "✅ Диск" in keyboard_labels(context.bot.sent[-1])


def test_access_denied_has_no_menu(monkeypatch):
    monkeypatch.setattr(validate_user, "ALLOWED_USER_IDS", frozenset({2}))
    context = make_context()
    asyncio.run(search_module.search(make_update("r15"), context))  # type: ignore[arg-type]
    assert "нет доступа" in context.bot.sent[-1]["text"]
    assert context.bot.sent[-1]["reply_markup"] is None


def test_long_result_fits_telegram_limit(monkeypatch):
    long_title = "диск " + "x" * 150
    items = {f"{long_title} {i}": [PriceInfo("1000", "", "4", i, product_type="Диск")] for i in range(50)}
    search = PriceListSearch(Loader(items))
    monkeypatch.setattr(search_module, "get_search_instance", lambda _key, _path: search)
    monkeypatch.setattr(search_module.PriceSource, "latest_file", lambda _self: Path("price_drom_2026-10-20.xlsx"))
    context = make_context({type_menu.USER_TYPE_FILTER: "Диск"})

    text = asyncio.run(search_module.search_response(context, "диск"))  # type: ignore[arg-type]

    assert len(text) <= search_module.MESSAGE_LIMIT
    assert "Найдено 50 позиций (показаны первые " in text
    shown = int(text.split("показаны первые ")[1].split(",")[0])
    assert 0 < shown < 50
    assert text.count("\n") == 2 + shown  # источник, тип, найдено + строки


def test_short_result_is_not_marked_truncated():
    lines = ["1. a", "2. b"]
    assert search_module._lines_that_fit("header", lines) == 2
