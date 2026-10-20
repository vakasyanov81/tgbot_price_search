import pytest

from autosnab_bot.handlers import type_filter
from autosnab_bot.services import type_menu, validate_user
from tests.fakes import ALLOWED_USER

TEST_PRODUCT_TYPES = ('Легковая шина', 'Грузовая шина', 'Диск')


@pytest.fixture(autouse=True)
def _allowed_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_user, 'ALLOWED_USER_IDS', frozenset((ALLOWED_USER,)))


@pytest.fixture(autouse=True)
def _product_types(monkeypatch: pytest.MonkeyPatch) -> None:
    """Меню типов прикрепляется к каждому сообщению: в тестах — без запуска CLI priceformation."""

    async def fake_types() -> list[str]:
        return list(TEST_PRODUCT_TYPES)

    monkeypatch.setattr(type_menu, 'get_product_types', fake_types)
    monkeypatch.setattr(type_filter, 'get_product_types', fake_types)
