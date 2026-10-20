import pytest

from autosnab_bot.services import type_menu

TEST_PRODUCT_TYPES = ["Легковая шина", "Грузовая шина", "Диск"]


@pytest.fixture(autouse=True)
def _product_types(monkeypatch):
    """Меню типов прикрепляется к каждому сообщению: в тестах — без запуска CLI priceformation."""

    async def fake_types():
        return TEST_PRODUCT_TYPES

    monkeypatch.setattr(type_menu, "get_product_types", fake_types)
